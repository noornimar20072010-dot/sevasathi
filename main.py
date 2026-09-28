import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Scheme Assistant API")

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize ChromaDB client (using the same path and collection as ingest.py)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="schemes")

# Fetch all unique scheme_name values from ChromaDB on startup
try:
    all_items = collection.get(include=["metadatas"])
    unique_scheme_names = list({
        meta.get("scheme_name") 
        for meta in all_items.get("metadatas", []) 
        if meta and meta.get("scheme_name")
    })
    print(f"Loaded {len(unique_scheme_names)} unique scheme names on startup.")
except Exception as e:
    print(f"Warning: Could not load initial scheme names: {e}")
    unique_scheme_names = []

# Helper to extract significant words for matching
def get_significant_words(text: str) -> set:
    words = set(re.findall(r'\b[a-z0-9]+\b', text.lower()))
    stop_words = {"the", "a", "an", "scheme", "yojana", "for", "and", "of", "in", "to", "on", "with"}
    return words - stop_words

# Initialize Groq client
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key)

class HistoryItem(BaseModel):
    question: str
    answer: str

class AskRequest(BaseModel):
    question: str
    history: list[HistoryItem] = []
    language: str = "en"

class AskResponse(BaseModel):
    answer: str
    sources: list[str]

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    if not groq_client.api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured.")

    try:
        # 1. Rewrite the question using conversation history (if any) into a standalone question
        actual_question = request.question
        if request.history or request.language in ["hi", "pa"]:
            recent_history = request.history[-2:] if request.history else []
            history_text = "\n".join([f"User: {h.question}\nAssistant: {h.answer}" for h in recent_history])
            
            rewrite_prompt = (
                "You are an expert translator and query rewriter.\n\n"
                "Translate the following question into English if it is in Hindi or Punjabi. "
                "Also, make it a standalone question using the provided conversation history. "
                "If the conversation history is empty, just translate the question.\n\n"
                f"Conversation History:\n{history_text}\n\n"
                f"Latest Question: {request.question}\n\n"
                "Output ONLY the standalone English question and nothing else.\n"
                "Standalone Question (in English):"
            )
            
            rewrite_response = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": rewrite_prompt}],
                max_tokens=100,
                temperature=0
            )
            actual_question = rewrite_response.choices[0].message.content.strip()
            if actual_question.startswith('"') and actual_question.endswith('"'):
                actual_question = actual_question[1:-1]
            print(f"Original Question: {request.question.encode('cp1252', 'replace').decode('cp1252')}")
            print(f"Rewritten Question: {actual_question.encode('cp1252', 'replace').decode('cp1252')}")

        q_lower = actual_question.lower()
        needs_docs = any(w in q_lower for w in ["document", "documents", "papers", "required"])
        needs_elig = any(w in q_lower for w in ["eligible", "eligibility", "who", "can apply", "age"])

        # 2. Try scheme-name matching
        question_words = get_significant_words(actual_question)
        matched_schemes_with_scores = []
        
        for s_name in unique_scheme_names:
            s_words = get_significant_words(s_name)
            overlap = len(question_words.intersection(s_words))
            # Match requires at least 2 significant words
            if overlap >= 2:
                matched_schemes_with_scores.append((overlap, s_name))
                
        # Sort by overlap score descending
        matched_schemes_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        is_name_match = len(matched_schemes_with_scores) > 0
        
        final_docs = []
        final_metas = []
        response_mode = "normal"
        
        if is_name_match:
            print("Path used: NAME-MATCH.")
            # If exactly 1-2 schemes match strongly, fetch ALL their chunks
            top_matches = [name for score, name in matched_schemes_with_scores[:2]]
            
            docs_pool = []
            metas_pool = []
            for match in top_matches:
                match_results = collection.get(where={"scheme_name": match})
                if match_results and match_results.get("documents"):
                    docs_pool.extend(match_results["documents"])
                    metas_pool.extend(match_results["metadatas"])
            
            # Prioritize matching keywords, cap at 16000 chars (~4000 tokens)
            prioritized_indices = []
            other_indices = []
            for i, meta in enumerate(metas_pool):
                section = meta.get("section", "")
                if (needs_docs and section == "documents_required") or (needs_elig and section == "eligibility"):
                    prioritized_indices.append(i)
                else:
                    other_indices.append(i)
                    
            current_len = 0
            for i in prioritized_indices + other_indices:
                doc = docs_pool[i]
                meta = metas_pool[i]
                if current_len + len(doc) <= 16000:
                    final_docs.append(doc)
                    final_metas.append(meta)
                    current_len += len(doc)
                else:
                    break
            
            response_mode = "normal"
            # SKIP steps 3 and 4 entirely and go straight to step 5.
            
        else:
            # 3. If no strong name match, run semantic search
            print("Path used: SEMANTIC SEARCH.")
            
            # Query top 10 chunks by embedding similarity
            results = collection.query(
                query_texts=[actual_question],
                n_results=10,
                include=["documents", "metadatas", "distances"]
            )
            
            res_docs = results["documents"][0] if results["documents"] else []
            res_metas = results["metadatas"][0] if results["metadatas"] else []
            res_dists = results.get("distances", [[]])[0] if results.get("distances") else []
            
            # Deduplicate to at most 5 DISTINCT scheme_names (keep best-scoring chunk per scheme)
            seen_schemes = set()
            docs_pool = []
            metas_pool = []
            best_distance = float('inf')
            
            for doc, meta, dist in zip(res_docs, res_metas, res_dists):
                if dist < best_distance:
                    best_distance = dist
                s_name = meta.get("scheme_name", "")
                if s_name not in seen_schemes:
                    seen_schemes.add(s_name)
                    docs_pool.append(doc)
                    metas_pool.append(meta)
                if len(seen_schemes) >= 5:
                    break
                    
            # Cap combined context at 3000 tokens (~12000 characters)
            current_len = 0
            for doc, meta in zip(docs_pool, metas_pool):
                if current_len + len(doc) <= 12000:
                    final_docs.append(doc)
                    final_metas.append(meta)
                    current_len += len(doc)
                else:
                    break
            
            # 4. Decide response mode based on step 3 results
            if best_distance < 0.5:
                # Treat as a confident single-scheme answer
                response_mode = "normal"
            else:
                # No chunk is a strong match AND there are multiple distinct schemes
                if len(seen_schemes) > 1:
                    response_mode = "list"
                else:
                    response_mode = "normal"

        
        if len(question_words) == 0:
            if request.language == "hi":
                return AskResponse(answer="मुझे यकीन नहीं है कि आप क्या जानना चाहते हैं। कृपया किसी सरकारी योजना के बारे में पूछें।", sources=[])
            elif request.language == "pa":
                return AskResponse(answer="ਮੈਨੂੰ ਯਕੀਨ ਨਹੀਂ ਹੈ ਕਿ ਤੁਸੀਂ ਕੀ ਜਾਣਨਾ ਚਾਹੁੰਦੇ ਹੋ। ਕਿਰਪਾ ਕਰਕੇ ਕਿਸੇ ਸਰਕਾਰੀ ਸਕੀਮ ਬਾਰੇ ਪੁੱਛੋ।", sources=[])
            else:
                return AskResponse(answer="I'm not sure what you'd like to know. Please ask about a government scheme.", sources=[])
                
        if len(final_docs) == 0:
            if request.language == "hi":
                return AskResponse(answer="उस योजना के बारे में कोई जानकारी नहीं मिली।", sources=[])
            elif request.language == "pa":
                return AskResponse(answer="ਉਸ ਸਕੀਮ ਬਾਰੇ ਕੋਈ ਜਾਣਕਾਰੀ ਨਹੀਂ ਮਿਲੀ।", sources=[])
            else:
                return AskResponse(answer="No information found for that scheme.", sources=[])

        # 5. Send the finalized context to Groq
        context = "\n\n---\n\n".join(final_docs)
        
        
        lang_instruction = ""
        if request.language == "hi":
            lang_instruction = "\nWrite the entire answer in Hindi. Use simple everyday words for an elderly reader. Keep scheme names, numbers and rupee amounts exactly as in the source."
        elif request.language == "pa":
            lang_instruction = "\nWrite the entire answer in Punjabi (Gurmukhi script). Use simple everyday words for an elderly reader. Keep scheme names, numbers and rupee amounts exactly as in the source."
        else:
            lang_instruction = "\nWrite the entire answer in English. Use simple everyday words for an elderly reader. Keep scheme names, numbers and rupee amounts exactly as in the source."

        if response_mode == "normal":
            system_prompt = (
                "You are a helpful, warm, and patient assistant for elderly, first-time internet users. "
                "Your goal is to answer their questions about government schemes based ONLY on the provided context. "
                "Use simple, plain language. Avoid all technical jargon. Keep sentences short and easy to understand. "
                "IMPORTANT FORMATTING RULES: "
                "1) DO NOT generate Markdown tables. Tables are hard for elderly users to read. "
                "2) Use bold text and numbered lists where helpful to make the information clear. "
                "3) Provide a specific, detailed answer based on the scheme(s) in the context. "
                "If the answer is not in the context, gently let them know."
            ) + lang_instruction
        else:
            system_prompt = (
                "You are a helpful, warm, and patient assistant for elderly, first-time internet users. "
                "Your goal is to answer their questions about government schemes based ONLY on the provided context. "
                "Use simple, plain language. Avoid all technical jargon. Keep sentences short and easy to understand. "
                "IMPORTANT FORMATTING RULES: "
                "1) Start with a short, friendly intro sentence. "
                "2) Present each distinct scheme as a numbered list. "
                "3) Put each scheme's name in **bold**, followed by 1-2 plain sentences about who it's for and what it offers. "
                "4) DO NOT generate Markdown tables. "
                "5) End your answer by inviting the user to ask for more details, for example: 'Would you like more details on any of these?' "
                "If the answer is not in the context, gently let them know."
            ) + lang_instruction
        
        prompt_with_context = f"Here is some information about government schemes:\n\n{context}\n\nUser Question: {actual_question}"
        
        messages = [{"role": "system", "content": system_prompt}]
        if request.history or request.language in ["hi", "pa"]:
            for h in request.history[-2:]:
                messages.append({"role": "user", "content": h.question})
                messages.append({"role": "assistant", "content": h.answer})
        messages.append({"role": "user", "content": prompt_with_context})
        
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages
        )
        
        answer = response.choices[0].message.content
        
        # 6. Return the answer along with accurate source scheme_name(s)
        sources = list({meta.get("scheme_name") for meta in final_metas if meta.get("scheme_name")})
        
        return AskResponse(answer=answer, sources=sources)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
