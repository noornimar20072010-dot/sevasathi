import json

data = json.load(open('schemes_final_clean.json', encoding='utf-8'))
names = [s['scheme_name'].lower() for s in data]

checks = [
    'ayushman', 'pm kisan', 'pm-kisan', 'ujjwala', 'jan dhan',
    'atal pension', 'pmjay', 'national social assistance',
    'pradhan mantri awas', 'sukanya samriddhi', 'mgnrega',
    'indira gandhi national old age', 'national family benefit',
]

for c in checks:
    found = [n for n in names if c in n]
    if found:
        print(f"{c}: FOUND - {found[0]}")
    else:
        print(f"{c}: MISSING")
