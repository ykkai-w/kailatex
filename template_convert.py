# -*- coding: utf-8 -*-
"""
kailatex 转换器骨架 —— 复制到 <主题>_整理/_build/convert_xxx.py 后改 load 与 assembly 即可。
依赖：py(Python3.11) + tectonic。读结构化 JSON → 写 .tex。
核心是 render_inline / render_md / parse_table，已处理：数学保护、特殊符转义、
CJK/货币安全、裸 unicode 符号映射、markdown 表格、多行 $$ 显示公式、①②③ 圈码。
"""
import json, re, html, os

# ---------- 裸 unicode 数学符号 -> LaTeX（缺一个就缺字，按需补） ----------
USYM = {'×':r'$\times$','÷':r'$\div$','→':r'$\to$','⇒':r'$\Rightarrow$','⇔':r'$\Leftrightarrow$',
        '↔':r'$\leftrightarrow$','⇌':r'$\rightleftharpoons$','↑':r'$\uparrow$','↓':r'$\downarrow$',
        '≈':r'$\approx$','≤':r'$\le$','≥':r'$\ge$','≠':r'$\neq$','≡':r'$\equiv$','√':r'$\surd$',
        '∞':r'$\infty$','∑':r'$\sum$','∏':r'$\prod$','∈':r'$\in$','∩':r'$\cap$','∪':r'$\cup$',
        '−':'-','²':r'$^{2}$','³':r'$^{3}$','±':r'$\pm$','≜':r'$\triangleq$','∝':r'$\propto$',
        '∴':r'$\therefore$','∵':r'$\because$','‰':r'\textperthousand{}','€':r'\euro{}','£':r'\pounds{}',
        '＞':'>','＜':'<'}
for _i, _c in enumerate('₀₁₂₃₄₅₆₇₈₉'): USYM[_c] = '$_{%d}$' % _i
for _i, _c in enumerate('⁰¹²³⁴⁵⁶⁷⁸⁹'): USYM[_c] = '$^{%d}$' % _i

S1, S2, S6 = chr(1), chr(2), chr(6)              # 占位哨兵（勿用字面控制字符）
_CJK = re.compile(r'[　-〿一-鿿＀-￯]')           # CJK + 全角区

def _fix_math(s):                                 # 货币符号在数学模式内安全化
    return s.replace('£', r'\mbox{\pounds}').replace('€', r'\mbox{\euro}').replace(S6, r'\$')

def render_inline(text):
    text = text.replace('\\$', S6)                # 转义美元 \$ -> 哨兵（任何模式都安全）
    math = []
    def pmd(m):
        math.append(m.group(0)); return f"{S1}{len(math)-1}{S1}"
    text = re.sub(r'\$\$.*?\$\$', pmd, text, flags=re.S)
    def pmi(m):                                   # 含中文且无反斜杠的 $..$ 判为"货币$"，按字面
        inner = m.group(1)
        if _CJK.search(inner) and '\\' not in inner and S6 not in inner:
            return m.group(0)
        math.append(m.group(0)); return f"{S1}{len(math)-1}{S1}"
    text = re.sub(r'\$([^$]*)\$', pmi, text)
    cmds = []
    def pc(m):
        cmds.append(m.group(0)); return f"{S2}{len(cmds)-1}{S2}"
    text = re.sub(r'\\[A-Za-z]+\*?|\\[%$&_#{}~^]', pc, text)   # 保护已有 \命令 与 \转义符
    text = text.replace('\\', r'\textbackslash{}')
    for a, b in [('&', r'\&'), ('%', r'\%'), ('#', r'\#'), ('_', r'\_'), ('$', r'\$'),
                 ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')]:
        text = text.replace(a, b)
    for a, b in USYM.items():
        text = text.replace(a, b)
    text = re.sub(S2 + r'(\d+)' + S2, lambda m: cmds[int(m.group(1))], text)
    def restore(m):
        s = _fix_math(math[int(m.group(1))])
        return '\\[' + s[2:-2] + '\\]' if s.startswith('$$') else s
    text = re.sub(S1 + r'(\d+)' + S1, restore, text)
    text = text.replace(S6, r'\$')
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)     # **粗** -> \textbf
    text = re.sub(r'（[\s　]*）', r'（\\hspace{2.6em}）', text)  # 答题空括号留宽（空白卷用）
    return text

def is_tbl(l): return l.strip().startswith('|')
def parse_table(rows):
    def cells(r): return [c.strip() for c in r.strip().strip('|').split('|')]
    data = [cells(r) for r in rows if not re.match(r'^\s*\|[\s:\-\|]+\|?\s*$', r)]
    if not data: return ''
    nc = max(len(r) for r in data); data = [r + ['']*(nc-len(r)) for r in data]
    out = ['\\begin{center}\\small', '\\renewcommand{\\arraystretch}{1.25}',
           '\\begin{tabular}{|' + '|'.join(['c']*nc) + '|}', '\\hline']
    for r in data: out.append(' & '.join(render_inline(c) for c in r) + ' \\\\ \\hline')
    out += ['\\end{tabular}', '\\end{center}']
    return '\n'.join(out)

def render_md(md):
    md = html.unescape(md)
    disp = []                                     # 先整体抽出多行 $$..$$ 显示公式
    def grab(m):
        disp.append(m.group(1).strip()); return f"\n{S1}D{len(disp)-1}{S1}\n"
    md = re.sub(r'\$\$(.+?)\$\$', grab, md, flags=re.S)
    lines = md.split('\n'); out = []; i = 0; n = len(lines)
    while i < n:
        l = lines[i]; s = l.strip()
        dm = re.match(S1 + r'D(\d+)' + S1 + r'$', s)
        if dm:
            inner = _fix_math(disp[int(dm.group(1))].replace('\\$', S6))
            inner = re.sub(r'([　-〿一-鿿＀-￯]+)', r'\\text{\1}', inner)  # 数学里裸中文包 \text
            out.append('\\[' + inner + '\\]'); i += 1; continue
        if is_tbl(l):
            blk = []
            while i < n and is_tbl(lines[i]): blk.append(lines[i]); i += 1
            out.append(parse_table(blk)); continue
        if not s: i += 1; continue
        s = re.sub(r'^\s*#{1,6}\s*', '', s)        # 去 markdown ## 标题记号
        if re.match(r'^[-*+]\s+', s):
            out.append('\\noindent\\hspace{1em}$\\bullet$\\,' + render_inline(re.sub(r'^[-*+]\s+', '', s)) + ' \\par')
        else:
            out.append('\\noindent ' + render_inline(s) + ' \\par')
        i += 1
    return '\n'.join(out)

def break_points(a):                              # 答案按 ①②③ 每点独占一行
    return re.sub(r'[ \t　]*([①-⑳])', r'\n\1', html.unescape(a))

PRE = r'''\documentclass[11pt]{ctexart}
\usepackage{amsmath,amssymb}\usepackage{array}\usepackage{geometry}
\geometry{a4paper,top=1.9cm,bottom=1.9cm,left=2.1cm,right=2.1cm}
\usepackage{fancyhdr}\usepackage{titlesec}\usepackage{xeCJK}\usepackage{textcomp}
\providecommand{\euro}{\texteuro}
\xeCJKDeclareCharClass{CJK}{"2460 -> "2473}
\xeCJKDeclareCharClass{CJK}{"2160 -> "216B}
\setlength{\parindent}{0pt}\setlength{\parskip}{2.5pt}\linespread{1.12}
\emergencystretch=4em \hbadness=10000
\titleformat{\section}{\centering\Large\bfseries}{}{0pt}{}\titlespacing{\section}{0pt}{4pt}{6pt}
\titleformat{\subsection}{\large\bfseries}{}{0pt}{}\titlespacing{\subsection}{0pt}{8pt}{4pt}
\pagestyle{fancy}\fancyhf{}\fancyfoot[C]{\small 第 \thepage{} 页}\renewcommand{\headrulewidth}{0pt}
\begin{document}
'''

# ---------------- 示例：把通用 JSON 拼成 tex ----------------
if __name__ == '__main__':
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    HERE = os.path.dirname(os.path.abspath(__file__))
    data = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))  # 改成你的 JSON
    tex = [PRE]
    tex.append(r'\begin{center}{\huge\bfseries 《标题》}\\[6pt]{\small 说明}\end{center}\vspace{4pt}\hrule\vspace{8pt}')
    # 目录：每题独占一行（{\small ...}收紧）
    tex.append(r'\section*{目\quad 录（快速定位）}')
    tex.append(r'{\small\setlength{\parskip}{1.2pt}\linespread{1.04}\selectfont')
    for c in data:                                       # c = {num,title,sections:[{name,items:[{label,q,a,...}]}]}
        tex.append('\\subsection*{第%s章　%s}' % (c['num'], render_inline(c['title'])))
        for sec in c['sections']:
            tex.append('\\smallskip\\noindent\\textbf{【%s（%d题）】}\\par' % (sec['name'], len(sec['items'])))
            for it in sec['items']:
                topic = it.get('title') or re.sub(r'\s+', '', it['q'])[:60]
                tex.append('\\noindent\\hspace{1.2em}' + it['label'] + '.\\,' + render_inline(topic) + '\\par')
    tex.append('}\\clearpage')
    # 正文：题在前、答紧随；答案 ①②③ 每点一行
    for c in data:
        tex.append('\\section*{第%s章　%s}' % (c['num'], render_inline(c['title'])))
        for si, sec in enumerate(c['sections']):
            tex.append('\\subsection*{%s、%s}' % ('一二三四五'[si], sec['name']))
            for it in sec['items']:
                tex.append('\\smallskip\\noindent\\textbf{%s．%s}\\par' % (it['label'], render_inline(it['q'])))
                tex.append(render_md(break_points(it['a'])))
                tex.append('\\vspace{3pt}')
        tex.append('\\clearpage')
    tex.append(r'\end{document}')
    open(os.path.join(BASE, '成品.tex'), 'w', encoding='utf-8').write('\n'.join(tex))
    print('wrote 成品.tex')
