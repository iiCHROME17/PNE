import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document

doc   = Document(r"Dissertation\Literature Material\Drafts\Compiled\Dissertation Draft 5.docx")
paras = doc.paragraphs

refs_start = next(i for i,p in enumerate(paras) if p.text.strip()=='References')
app_start  = next(i for i,p in enumerate(paras) if p.text.strip() in ('Appendices','Appendix'))

print("=== STYLE INVENTORY (body, first occurrence of each) ===")
seen = {}
for i in range(len(paras)):
    s = paras[i].style.name
    t = paras[i].text.strip()
    if s not in seen and t:
        seen[s] = (i, t[:80])

for style, (idx, sample) in sorted(seen.items()):
    loc = 'body' if idx < refs_start else ('refs' if idx < app_start else 'app')
    print(f"  [{loc}] '{style}': {sample}")

print("\n=== HEADING STYLES IN BODY (all) ===")
for i in range(refs_start):
    s = paras[i].style.name
    t = paras[i].text.strip()
    if 'Heading' in s or 'heading' in s:
        print(f"  [{i}] '{s}': {t[:80]}")

print("\n=== FIRST 20 BODY PARAGRAPHS (to see structure) ===")
for i in range(min(25, refs_start)):
    t = paras[i].text.strip()
    s = paras[i].style.name
    if t:
        print(f"  [{i}] ({s}): {t[:80]}")

print("\n=== ABSTRACT / TITLE area ===")
for i in range(min(10, refs_start)):
    t = paras[i].text.strip()
    s = paras[i].style.name
    print(f"  [{i}] ({s}): {t[:120]}")

print("\n=== CHAPTER HEADINGS (pattern match) ===")
for i in range(refs_start):
    t = paras[i].text.strip()
    if re.match(r'^Chapter\s+\d', t, re.IGNORECASE) or re.match(r'^\d+\s+[A-Z]', t):
        print(f"  [{i}] ({paras[i].style.name}): {t[:80]}")
