import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'print(f"Original Question: {request.question}")', 
    'print(f"Original Question: {request.question.encode(\'cp1252\', \'replace\').decode(\'cp1252\')}")'
)
code = code.replace(
    'print(f"Rewritten Question: {actual_question}")', 
    'print(f"Rewritten Question: {actual_question.encode(\'cp1252\', \'replace\').decode(\'cp1252\')}")'
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed prints')

