import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update AskRequest
code = code.replace(
    "class AskRequest(BaseModel):\n    question: str\n    history: list[HistoryItem] = []",
    "class AskRequest(BaseModel):\n    question: str\n    history: list[HistoryItem] = []\n    language: str = \"en\""
)

# 2. Update rewrite_prompt
old_rewrite_prompt = """            rewrite_prompt = (
                "Given the following conversation history and the user's latest question, "
                "rewrite the latest question to be a standalone question that includes all relevant context "
                "(like specific scheme names) mentioned previously. If it's already standalone, just output the original question.\\n\\n"
                f"Conversation History:\\n{history_text}\\n\\n"
                f"Latest Question: {request.question}\\n\\n"
                "Standalone Question:"
            )"""

new_rewrite_prompt = """            rewrite_prompt = (
                "Given the following conversation history and the user's latest question, "
                "rewrite the latest question to be a standalone question in English that includes all relevant context "
                "(like specific scheme names) mentioned previously. If it's already standalone, just output the original question in English. "
                "If the question is in Hindi or Punjabi, translate it to a standalone English question.\\n\\n"
                f"Conversation History:\\n{history_text}\\n\\n"
                f"Latest Question: {request.question}\\n\\n"
                "Standalone Question (in English):"
            )"""

code = code.replace(old_rewrite_prompt, new_rewrite_prompt)

# Also need to run rewrite if the language is hi or pa, even if there is no history
# Actually, the user says: "In the existing step that rewrites the question using conversation history, also translate the question into English if it is in Hindi or Punjabi."
# I will change `if request.history:` to `if request.history or request.language in ["hi", "pa"]:`
code = code.replace("if request.history:", "if request.history or request.language in [\"hi\", \"pa\"]:")
code = code.replace("recent_history = request.history[-2:]", "recent_history = request.history[-2:] if request.history else []")

# 3. Add fallback messages handling before sending to Groq, or replace them if they exist
# Wait, they might have fallback logic: 
# Let's add lang_instruction
lang_code = """
        lang_instruction = ""
        if request.language == "hi":
            lang_instruction = "\\nWrite the entire answer in Hindi. Use simple everyday words for an elderly reader. Keep scheme names, numbers and rupee amounts exactly as in the source."
        elif request.language == "pa":
            lang_instruction = "\\nWrite the entire answer in Punjabi (Gurmukhi script). Use simple everyday words for an elderly reader. Keep scheme names, numbers and rupee amounts exactly as in the source."
        else:
            lang_instruction = "\\nWrite the entire answer in English. Use simple everyday words for an elderly reader. Keep scheme names, numbers and rupee amounts exactly as in the source."
"""

code = code.replace(
    "if response_mode == \"normal\":",
    lang_code + "\n        if response_mode == \"normal\":"
)

# Append lang_instruction to system prompts
code = code.replace(
    "\"If the answer is not in the context, gently let them know.\"\n            )",
    "\"If the answer is not in the context, gently let them know.\"\n            ) + lang_instruction"
)

# 4. Fallback messages - maybe the user wants me to add a quick check for len(question_words) < 1
# And if len(final_docs) == 0.
# Let's add an explicit check before sending to Groq.
fallback_logic = """
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
"""

# Let's insert fallback logic right before `# 5. Send the finalized context to Groq`
code = code.replace(
    "# 5. Send the finalized context to Groq",
    fallback_logic + "\n        # 5. Send the finalized context to Groq"
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated main.py")

