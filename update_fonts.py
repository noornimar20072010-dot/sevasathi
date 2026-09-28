import re

with open('frontend/src/App.css', 'r', encoding='utf-8') as f:
    css = f.read()

css = css.replace("font-family: 'Mukta', 'Noto Sans', system-ui, sans-serif;", "font-family: 'Mukta', 'Mukta Mahee', 'Noto Sans', system-ui, sans-serif;")
css = css.replace("font-family: 'Mukta', sans-serif;", "font-family: 'Mukta', 'Mukta Mahee', sans-serif;")
css = css.replace("font-family: 'Fraunces', Georgia, serif;", "font-family: 'Fraunces', 'Noto Serif Devanagari', 'Noto Serif Gurmukhi', Georgia, serif;")

with open('frontend/src/App.css', 'w', encoding='utf-8') as f:
    f.write(css)
print('Fonts updated in App.css')

