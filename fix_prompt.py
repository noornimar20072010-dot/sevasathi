import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the rewrite prompt
old_rewrite_prompt = """            rewrite_prompt = (
                "Given the following conversation history and the user's latest question, "
                "rewrite the latest question to be a standalone question in English that includes all relevant context "
                "(like specific scheme names) mentioned previously. If it's already standalone, just output the original question in English. "
                "If the question is in Hindi or Punjabi, translate it to a standalone English question.\\n\\n"
                f"Conversation History:\\n{history_text}\\n\\n"
                f"Latest Question: {request.question}\\n\\n"
                "Standalone Question (in English):"
            )"""

new_rewrite_prompt = """            rewrite_prompt = (
                "You are an expert translator and query rewriter.\\n\\n"
                "Translate the following question into English if it is in Hindi or Punjabi. "
                "Also, make it a standalone question using the provided conversation history. "
                "If the conversation history is empty, just translate the question.\\n\\n"
                f"Conversation History:\\n{history_text}\\n\\n"
                f"Latest Question: {request.question}\\n\\n"
                "Output ONLY the standalone English question and nothing else.\\n"
                "Standalone Question (in English):"
            )"""

code = code.replace(old_rewrite_prompt, new_rewrite_prompt)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated main.py")

