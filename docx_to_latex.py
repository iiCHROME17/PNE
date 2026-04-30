"""
docx_to_latex.py  —  Convert Dissertation Draft 5.docx → LaTeX project
"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document
from docx.oxml.ns import qn

DOCX    = r"Dissertation\Literature Material\Drafts\Compiled\Dissertation Draft 5.docx"
OUT_DIR = r"Dissertation\LaTeX"
MEDIA   = os.path.join(OUT_DIR, "media")
os.makedirs(MEDIA, exist_ok=True)

doc   = Document(DOCX)
paras = doc.paragraphs
body  = doc.element.body

# ─────────────────────────────────────────────────────────────────────────────
# 1. EXTRACT IMAGES
# ─────────────────────────────────────────────────────────────────────────────
rid_to_file = {}
for rId, rel in doc.part.rels.items():
    if 'image' in rel.reltype:
        try:
            part = rel.target_part
            ext  = part.partname.split('.')[-1].lower()
            fname = f"img_{rId}.{ext}"
            with open(os.path.join(MEDIA, fname), 'wb') as f:
                f.write(part.blob)
            rid_to_file[rId] = fname
        except Exception as e:
            print(f"  Warning: {rId}: {e}", file=sys.stderr)

print(f"Extracted {len(rid_to_file)} images")

# ─────────────────────────────────────────────────────────────────────────────
# 2. HELPERS
# ─────────────────────────────────────────────────────────────────────────────
_UMAP = {
    '—': '---', '–': '--',
    '’': "'",   '‘': '`',
    '“': '``',  '”': "''",
    '→': r'$\rightarrow$',
    '≤': r'$\leq$', '≥': r'$\geq$',
    'é': r"\'e", 'è': r'\`e',
    'ü': r'\"u', 'ä': r'\"a',
    '…': r'\ldots{}',
    ' ': '~',
    '°': r'\textdegree{}',
    'ą': r'\k{a}',  # ą
    'ł': r'\l{}',   # ł
    'ó': r"\'o",    # ó
    'ś': r"\'s",    # ś
    'ż': r'\.z',    # ż
    '−': '$-$',           # U+2212 minus sign
    '×': r'$\times$',     # U+00D7 multiplication
    'ç': r'\c{c}',         # U+00E7 cedilla (Façade)
    'Δ': r'$\Delta$',      # U+0394 delta
    '★': r'$\bigstar$',    # U+2605 star
    '✗': r'$\times$',      # U+2717 cross/fail mark
    '§': r'\S{}',          # U+00A7 section sign
    '✓': r'$\checkmark$',  # U+2713 check mark (preemptive)
    'α': r'$\alpha$',      # U+03B1 alpha
    'β': r'$\beta$',       # U+03B2 beta
    'γ': r'$\gamma$',      # U+03B3 gamma
    'π': r'$\pi$',         # U+03C0 pi
}

def esc(text):
    if not text:
        return ''
    out = []
    for ch in text:
        if   ch == '\\': out.append(r'\textbackslash{}')
        elif ch == '&':  out.append(r'\&')
        elif ch == '%':  out.append(r'\%')
        elif ch == '$':  out.append(r'\$')
        elif ch == '#':  out.append(r'\#')
        elif ch == '{':  out.append(r'\{')
        elif ch == '}':  out.append(r'\}')
        elif ch == '^':  out.append(r'\^{}')
        elif ch == '_':  out.append(r'\_')
        elif ch == '~':  out.append(r'\textasciitilde{}')
        elif ch in _UMAP: out.append(_UMAP[ch])
        else:            out.append(ch)
    return ''.join(out)

def runs_to_latex(para):
    result = ''
    for run in para.runs:
        t = esc(run.text)
        if not t:
            continue
        b, i = run.bold, run.italic
        if b and i:
            t = f'\\textbf{{\\textit{{{t}}}}}'
        elif b:
            t = f'\\textbf{{{t}}}'
        elif i:
            t = f'\\textit{{{t}}}'
        result += t
    return result or esc(para.text)

def para_images(para):
    rids = []
    for blip in para._p.findall('.//' + qn('a:blip')):
        rid = blip.get(qn('r:embed'))
        if rid and rid in rid_to_file:
            rids.append(rid)
    return rids

# ─────────────────────────────────────────────────────────────────────────────
# 3. TABLE → longtable
# ─────────────────────────────────────────────────────────────────────────────
def table_to_latex(tbl, caption=''):
    rows  = tbl.rows
    if not rows:
        return ''
    ncols = max(len(r.cells) for r in rows)
    cw    = 15.2 / ncols

    def cell_text(cell, bold=False):
        parts = []
        for p in cell.paragraphs:
            t_parts = []
            for run in p.runs:
                t = esc(run.text)
                if not t:
                    continue
                # Only apply run-level bold/italic when NOT forcing bold at cell level
                if not bold:
                    if run.bold and run.italic:
                        t = f'\\textbf{{\\textit{{{t}}}}}'
                    elif run.bold:
                        t = f'\\textbf{{{t}}}'
                    elif run.italic:
                        t = f'\\textit{{{t}}}'
                t_parts.append(t)
            pt = ''.join(t_parts) or esc(p.text)
            if pt.strip():
                parts.append(pt.strip())
        result = ' '.join(parts)
        return f'\\textbf{{{result}}}' if bold and result else result

    col_spec = '|' + '|'.join([f'p{{{cw:.1f}cm}}'] * ncols) + '|'
    L = []
    font = r'{\footnotesize' if ncols >= 4 else ''
    if font: L.append(font)

    L.append(f'\\begin{{longtable}}{{{col_spec}}}')
    if caption:
        L.append(f'\\caption{{{esc(caption)}}}\\\\')
    L.append(r'\hline')

    header_row = None
    for r_idx, row in enumerate(rows):
        is_hdr = (r_idx == 0)
        cells  = [cell_text(c, bold=is_hdr) for c in row.cells]

        if is_hdr:
            header_row = cells
            L.append(' & '.join(cells) + r' \\')
            L.append(r'\hline')
            L.append(r'\endfirsthead')
            L.append(r'\hline')
            L.append(' & '.join(cells) + r' \\')
            L.append(r'\hline')
            L.append(r'\endhead')
            L.append(r'\hline')
            L.append(r'\endfoot')
        else:
            L.append(' & '.join(cells) + r' \\')
            L.append(r'\hline')

    L.append(r'\end{longtable}')
    if font: L.append('}')
    return '\n'.join(L)

# ─────────────────────────────────────────────────────────────────────────────
# 4. HEADING CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────
HEADING_STYLES = {'Heading 1', 'Heading 2', 'Heading 3',
                  'heading 1', 'heading 2', 'heading 3'}

def classify(para):
    """Return (level, clean_title).
    level: 1=chapter, 2=section, 3=subsection,
           0=body,  -1=title-page, -2=abstract-head, -3=refs-head,
           -4=appendices-marker
    """
    style = para.style.name
    text  = para.text.strip()

    # Body paragraphs masquerading as headings — detect by length/punctuation
    if style in HEADING_STYLES:
        is_sentence = (
            len(text) > 90 or
            (text.endswith('.') and len(text) > 55) or
            (text and text[0].islower())
        )
        if is_sentence:
            return 0, text

    if style == 'Heading 1':
        m = re.match(r'^Chapter\s+\d+:\s*(.*)', text)
        if m:
            return 1, m.group(1).strip()
        if text in ('References', 'Bibliography'):
            return -3, text
        if text in ('Appendices', 'Appendix'):
            return -4, text
        return -1, text  # title-page element

    if style == 'Heading 2':
        if text == 'Abstract':
            return -2, text
        if text in ('References', 'Bibliography'):
            return -3, text
        if text in ('Appendices', 'Appendix'):
            return -4, text
        title = re.sub(r'^\d+(?:\.\d+)*\s+', '', text).strip()
        return 2, title

    if style == 'Heading 3':
        title = re.sub(r'^\d+(?:\.\d+)*\s+', '', text).strip()
        return 3, title

    return 0, text  # Normal

# ─────────────────────────────────────────────────────────────────────────────
# 5. PRE-SCAN: collect abstract text (paras between "Abstract" H2 and first section H2)
# ─────────────────────────────────────────────────────────────────────────────
refs_start = next(i for i,p in enumerate(paras) if p.text.strip()=='References')
app_marker = next(i for i,p in enumerate(paras)
                  if p.text.strip() in ('Appendices','Appendix'))

abstract_paras = []
in_abs = False
for i, p in enumerate(paras):
    lvl, _ = classify(p)
    if lvl == -2:
        in_abs = True
        continue
    if in_abs:
        if lvl in (1, 2, 3):   # any heading ends the abstract
            break
        if p.text.strip():
            abstract_paras.append(runs_to_latex(p) if p.runs else esc(p.text))

abstract_tex = '\n\n'.join(abstract_paras)

ABSTRACT_PARA_RANGE = set()
in_abs = False
for i, p in enumerate(paras):
    lvl, _ = classify(p)
    if lvl == -2:
        in_abs = True
        ABSTRACT_PARA_RANGE.add(i)
        continue
    if in_abs:
        if lvl in (1, 2, 3):
            break
        ABSTRACT_PARA_RANGE.add(i)

# Title-page para indices (0-4 area)
TITLE_PAGE_RANGE = set()
for i in range(min(5, len(paras))):
    lvl, _ = classify(paras[i])
    if lvl in (-1, 2):
        TITLE_PAGE_RANGE.add(i)

# ─────────────────────────────────────────────────────────────────────────────
# 6. PREAMBLE
# ─────────────────────────────────────────────────────────────────────────────
PREAMBLE = r"""\documentclass[12pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[a4paper, margin=2.5cm, top=3cm, bottom=3cm]{geometry}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
\usepackage{setspace}
\usepackage{parskip}
\usepackage{caption}
\usepackage[titletoc,title]{appendix}
\usepackage{microtype}
\usepackage{array}
\usepackage{enumitem}
\usepackage{lmodern}
\usepackage{csquotes}
\usepackage{emptypage}

\onehalfspacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}

%% longtable default font
\setlength{\LTcapwidth}{\linewidth}

\begin{document}

%%──────────────────────────────────────────────────────────────────
%%  TITLE PAGE
%%──────────────────────────────────────────────────────────────────
\begin{titlepage}
  \centering
  \vspace*{2.5cm}
  {\Huge\bfseries Psychological Narrative Engine\par}
  \vspace{1.2cm}
  {\LARGE CS3IP Individual Project Dissertation\par}
  \vspace{0.8cm}
  {\Large Jerome Bawa\par}
  \vfill
  {\large \today\par}
\end{titlepage}

%%──────────────────────────────────────────────────────────────────
%%  ABSTRACT
%%──────────────────────────────────────────────────────────────────
\begin{abstract}
\addcontentsline{toc}{chapter}{Abstract}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 7. MAIN WALK
# ─────────────────────────────────────────────────────────────────────────────
output = [PREAMBLE, abstract_tex, '\n\\end{abstract}\n\\newpage\n']
output.append('\\tableofcontents\n\\listoftables\n\\listoffigures\n\\newpage\n')

para_idx  = 0
table_idx = 0

in_refs     = False
in_appendix = False
fig_count   = 0

# Track figure captions from the immediately-preceding paragraph
pending_caption = None

for child in body:
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

    # ── TABLE ──
    if tag == 'tbl':
        tbl = doc.tables[table_idx]
        table_idx += 1

        if in_refs:
            pass  # skip reference-section tables (shouldn't exist)
        else:
            # Try to use pending_caption as table caption
            cap = pending_caption or ''
            pending_caption = None
            output.append('\n' + table_to_latex(tbl, caption=cap) + '\n')
        continue

    if tag != 'p':
        continue

    # ── PARAGRAPH ──
    para = doc.paragraphs[para_idx]
    para_idx += 1
    text = para.text.strip()
    lvl, title = classify(para)

    # Skip title-page and abstract paras (handled above)
    if para_idx - 1 in TITLE_PAGE_RANGE or para_idx - 1 in ABSTRACT_PARA_RANGE:
        continue

    # Empty paragraph
    if not text and not para_images(para):
        continue

    # ── Caption-line detection (applies everywhere: body + appendices) ──
    # A "Heading 1"-styled table/figure label or a Normal caption line
    img_rids_early = para_images(para)
    is_caption_line = (
        not img_rids_early and
        bool(re.match(r'^(Figure|Table)\s+[\w\.]+\s*[—–\-]', text, re.IGNORECASE))
    )
    if is_caption_line:
        pending_caption = text
        continue  # will be consumed by the next table/figure element

    # ── Transitions ──
    if lvl == -3 or text == 'References':
        in_refs = True
        in_appendix = False
        output.append('\n\\chapter*{References}\n\\addcontentsline{toc}{chapter}{References}\n')
        continue

    if lvl == -4 or text in ('Appendices', 'Appendix'):
        in_appendix = True
        in_refs = False
        output.append('\n\\begin{appendices}\n')
        continue

    # ── REFERENCES section ──
    if in_refs:
        if text and len(text) > 5:
            output.append(f'\\noindent\\hangindent=0.7cm {esc(text)}\n\n')
        continue

    # ── APPENDICES ──
    if in_appendix:
        m_app = re.match(r'^Appendix\s+[A-L]\s*[—–-]+\s*(.*)', text)
        if m_app:
            output.append(f'\n\\chapter{{{esc(m_app.group(1).strip())}}}\n')
            continue
        if lvl == 2:
            output.append(f'\n\\section{{{esc(title)}}}\n')
            continue
        if lvl == 3:
            output.append(f'\n\\subsection{{{esc(title)}}}\n')
            continue
        # Normal appendix paragraph
        img_rids = para_images(para)
        if img_rids:
            for rid in img_rids:
                fname = rid_to_file.get(rid, '')
                fig_count += 1
                cap_tex = esc(text) if text else f'Figure {fig_count}'
                output.append(
                    f'\n\\begin{{figure}}[htbp]\n'
                    f'\\centering\n'
                    f'\\includegraphics[width=0.85\\textwidth]{{media/{fname}}}\n'
                    f'\\caption{{{cap_tex}}}\n'
                    f'\\end{{figure}}\n'
                )
            continue
        if text:
            output.append(esc(text) + '\n\n')
        continue

    # ── MAIN BODY ──
    if lvl == 1:   # \chapter
        output.append(f'\n\\chapter{{{esc(title)}}}\n')
        pending_caption = None
        continue

    if lvl == 2:   # \section
        output.append(f'\n\\section{{{esc(title)}}}\n')
        pending_caption = None
        continue

    if lvl == 3:   # \subsection
        output.append(f'\n\\subsection{{{esc(title)}}}\n')
        pending_caption = None
        continue

    # lvl == 0 : body paragraph
    img_rids = para_images(para)

    if img_rids:
        for rid in img_rids:
            fname = rid_to_file.get(rid, '')
            if not fname:
                continue
            fig_count += 1
            cap_tex = esc(text) if text else pending_caption or f'Figure {fig_count}'
            pending_caption = None
            output.append(
                f'\n\\begin{{figure}}[htbp]\n'
                f'\\centering\n'
                f'\\includegraphics[width=0.85\\textwidth]{{media/{fname}}}\n'
                f'\\caption{{{cap_tex}}}\n'
                f'\\label{{fig:{fig_count}}}\n'
                f'\\end{{figure}}\n'
            )
        continue

    # Check if this is a figure/table caption line (label for the next element)
    is_caption = bool(re.match(
        r'^(Figure|Table)\s+[\w\.]+\s*[—–-]', text, re.IGNORECASE
    ))
    if is_caption:
        pending_caption = text
        # Don't output as paragraph; it will be attached to the next table/figure
        continue

    # Regular text paragraph
    body_tex = runs_to_latex(para)
    if body_tex.strip():
        output.append(body_tex + '\n\n')
    pending_caption = None

# Close out
if in_appendix:
    output.append('\n\\end{appendices}\n')
output.append('\n\\end{document}\n')

# ─────────────────────────────────────────────────────────────────────────────
# 8. WRITE FILE
# ─────────────────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT_DIR, 'main.tex')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(''.join(output))

print(f"\nWritten:   {out_path}")
print(f"Images:    {len(rid_to_file)}")
print(f"Tables:    {table_idx}")
print(f"Figures:   {fig_count}")
print(f"Paras:     {para_idx}")
lines = ''.join(output).count('\n')
print(f"TeX lines: {lines:,}")
