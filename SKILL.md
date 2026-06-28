---
name: kailatex
description: 把 txt / 截图整理成"简洁美观、可直接打印"的中文考试资料 PDF 的标准流程与排版规范（tectonic + ctex + Python 转换器 + PyMuPDF 预览）。适用于：教材练习题、判断题、作业题、开卷资料、押题题库、章节测验等"题目+答案"型资料。
---

# kailatex — 中文资料 LaTeX → PDF 标准流程与排版规范

> 这是把"乱七八糟的 txt / 手机截图"整理成**一目了然、可直接打印**的中文 PDF 的固定打法。
> 已用它做过：金融风险管理教材练习题、章节练习题、判断题、作业题；国际金融开卷资料、押题题库。
> 配套：`template_convert.py`（转换器骨架，复制即用）、`preview.py`（PyMuPDF 预览/截图/拼图）。
> 相关机器配置见 memory `windows-latex-pdf-toolchain`。

---

## 0. 何时用这套

输入是"题目 / 资料"，要输出**排版工整、能打印或考场照抄**的中文 PDF。典型成品结构：
**封面 → 目录（考场/复习快速定位）→ 正文（按章/讲分节）→（可选）末尾统一参考答案**。

不适用：要做 Word（用 docx skill）、要做图表（用 kaiplot）。

---

## 1. 工具链（这台 Windows 已就绪）

| 用途 | 工具 | 说明 |
|---|---|---|
| 编译引擎 | **tectonic 便携版** | `C:\Users\21033\Desktop\金融风险管理\课件\_tex\tectonic.exe`（单 exe、免管理员、首次编译自动联网下载宏包；XeTeX 内核，支持 ctex/xeCJK）。换机用 GitHub release 重新下一个即可。 |
| Python | `py` | `C:\Users\21033\AppData\Local\Programs\Python\Python311`（真 Python，不是 Store 桩）。已装 Pillow、PyMuPDF。 |
| 预览 PDF | **PyMuPDF**（`import fitz`） | 本机无 poppler，Read 工具不能直接渲染 PDF → 用 fitz 把页转 PNG 再看。 |
| 中文字体 | tectonic 自带 **Fandol** | 环境读不到系统字体（会打印 `Fontconfig error` —**可忽略**），ctex 自动回退 Fandol，打印没问题。 |

**坑**：脚本目录里别放与 stdlib 同名的文件（如 `inspect.py`）→ 会 shadow，`import fitz` 失败。

---

## 2. 标准流水线（5 步）

```
源(txt/截图)  →①获取文本  →②结构化 JSON  →③Python 转换器  →④tectonic 编译  →⑤PyMuPDF 预览核验→改
```

1. **获取文本**
   - **txt 源**：直接 Python 正则解析（保真、零改写，最适合"标准答案照抄"类）。先**剥离聊天残留**（`Used a tool`、`下面发…`、`接下来发…`、`第X章…题完。`）。
   - **截图源**：先 `Image.resize(×3, LANCZOS)` 放大（原图常 ~560px 太糊），再用 **Workflow 工作流**一图一 agent 转录（`transcribe → verify` 两遍），结构化输出；**剔除非考试内容**（Web Exercise、推荐网址、页眉页码）。
   - **要算的计算题必须交叉验证**：每题派 3 个独立 agent 各自重算，一致才采用（亲测能抓出人/单 agent 的错）。
2. **结构化 JSON**：统一成 `[{num,title,sections:[{key,name,items:[{label,q,a}]}]}]` 之类。**打印每章每节题数核对**（如 简答15/计算6/论述12），数目对了再继续。
3. **转换器**（`template_convert.py`）：JSON → `.tex`。核心是 `render_inline`（保护数学、转义特殊符、CJK/货币安全）+ `render_md`（逐行：标题/列表/表格/公式）。
4. **编译**：`tectonic.exe --outdir <dir> <file.tex>`。
5. **预览核验**：PyMuPDF 转 PNG → Read 看。**整页会被缩小看不清公式 → 切上下两半（zoom 3）再看**；先做一张缩略图拼图确认整体结构无空页/无破版，再放大核验公式/表格/目录。

> 大任务用 **Workflow** 并行（OCR 一图一 agent、解题一题多 agent 交叉验证、逐章 tidy）；ultracode 下尤其如此。

---

## 3. LaTeX 模板（preamble，直接抄）

```latex
\documentclass[11pt]{ctexart}
\usepackage{amsmath,amssymb}
\usepackage{array}
\usepackage{geometry}
\geometry{a4paper,top=1.9cm,bottom=1.9cm,left=2.1cm,right=2.1cm}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{xeCJK}
\usepackage{textcomp}
\providecommand{\euro}{\texteuro}
\xeCJKDeclareCharClass{CJK}{"2460 -> "2473}   % ①..⑳ 圈码当中文渲染（否则缺字）
\xeCJKDeclareCharClass{CJK}{"2160 -> "216B}   % Ⅰ..Ⅻ 罗马数字
\setlength{\parindent}{0pt}
\setlength{\parskip}{2.5pt}
\linespread{1.12}
\emergencystretch=4em      % 吸收轻微 Overfull
\hbadness=10000            % 静音 underfull 警告
\titleformat{\section}{\centering\Large\bfseries}{}{0pt}{}
\titlespacing{\section}{0pt}{4pt}{6pt}
\titleformat{\subsection}{\large\bfseries}{}{0pt}{}
\titlespacing{\subsection}{0pt}{8pt}{4pt}
\pagestyle{fancy}\fancyhf{}
\fancyfoot[C]{\small 第 \thepage{} 页}    % 只留页码；页眉留空
\renewcommand{\headrulewidth}{0pt}
\begin{document}
% 封面：
\begin{center}
{\huge\bfseries 《标题》}\\[6pt]
{\small 一句说明（题型/口径/〔补充〕含义等）}
\end{center}
\vspace{4pt}\hrule\vspace{8pt}
```

---

## 4. 转换器核心（`render_inline` 思路）

完整可用版见 `template_convert.py`。要点：

- **占位符用 `chr(1)/chr(2)/chr(6)`，不要在源码里写真控制字符**（否则以后没法用 Edit 改）。
- 处理顺序：`\$`→哨兵 → 抽 `$$..$$` → 抽 `$..$`（**含中文且无反斜杠的 `$..$` 判为"货币$符号"不当公式**）→ 保护已有 `\命令` → 转义 `& % # _ $ { } ~ ^` → 替换 `USYM` 裸符号 → 还原命令 → 还原数学（数学内 `£→\mbox{\pounds}`、`€→\mbox{\euro}`、哨兵→`\$`）→ `**粗**→\textbf`。
- **USYM**（裸 unicode 数学符号 → LaTeX，必须有，否则缺字）：
  `× → $\times$`、`÷ ± ≈ ≤ ≥ ≠ ∑ ∏ ∈ ≡`、`→ ⇒ ⇔ ↔ ↑ ↓`、`− → -`、`² ³`、下标 `₀..₉ → $_{n}$`、上标 `⁰..⁹ → $^{n}$`、`£ → \pounds{}`、`€ → \euro{}`。
- **答案按 ①②③ 列点时**：渲染前 `re.sub(r'[ \t　]*([①-⑳])', '\n\\1', a)` 把每个圈码顶到行首 → 每点独占一行（"考试就是这样答题的"）。
- **填空/答题括号**：`（\s*）→（\hspace{2.6em}）`（空白试卷可写）。
- **Markdown 表格** `| a | b |` → `tabular`（`|c|c|`+`\hline`）。
- **多行 `$$..$$`**：必须在**逐行处理之前**整体抽出，否则按行切会把公式打碎。

---

## 5. 排版风格规范（我们约定的"那种"）

1. **简洁美观、一目了然**：A4、上下 1.9cm 左右 2.1cm、`linespread 1.12`；正文 11pt。
2. **封面**：大标题 + 一行小字说明；下面一条 `\hrule`。**不要页眉跑题文字**，页脚只放"第 N 页"。
3. **目录（考场快速定位）**：用 `{\small ... \linespread{1.04}\selectfont}` 收紧；**每道题独占一行**、按【简答/计算/论述/名词解释】分组缩进；计算题列"（分值）标题"，简答/论述列题干，名词列术语。**绝不把多题堆在一行**。
4. **正文分节**：`一、二、三、四` 或 `第N章/讲`；**题目在前、答案紧随**，方便照抄/对照。
5. **题目加粗、答案正常**；计算题分【题目】【答案】两段。
6. **保留原列点序号**（①②③ / （1）（2） / 1.2.3.），**不要擅自改写或合并**——尤其"标准答案照抄"型，忠实第一。
7. **公式 100% 正确**是硬指标：逐页放大核验；计算结果要么用原文、要么交叉验证后才改。
8. **两种作答形态**（按需选）：
   - **空白试卷型**（可手写）：只出题、答题括号留宽、简答/计算题下留空白；答案另放末尾"参考答案"分隔页。
   - **答案版/照抄型**：题目后紧跟标准答案，①②③ 每点一行。
9. **〔补充〕标记**：凡整理者自己补充/完善的内容，显式标注，便于区分原文。
10. **目录/正文里中文标点照抄**；不要把全角（　＝＋％）误转义（它们是 CJK，安全）。

---

## 6. 目录 / 文件夹约定

```
<课程>\<主题>_整理\
   ├─ <主题>.pdf      # 交付：成品
   ├─ <主题>.tex      # 交付：源码
   ├─ <主题>.txt      # 交付：纯文本备用（可由 PDF get_text 导出）
   └─ _build\          # 脚本 + 中间 JSON（parse_*.py / convert_*.py / *.json / *workflow*.js）
```
收尾：删临时 `_prev/_crop/_big/__pycache__`、`*.aux/*.log`；转换器读 JSON 用 `os.path.dirname(__file__)`（数据放 `_build`，成品写父目录），这样文件夹干净又能随时重生成。

---

## 7. 常见坑与修复（踩过的，重要）

| 现象 | 原因 | 修复 |
|---|---|---|
| `Missing character ① / ②`（U+2460+） | 圈码被当拉丁字母 | preamble 加 `\xeCJKDeclareCharClass{CJK}{"2460 -> "2473}` |
| `Missing character Ⅰ/Ⅱ`（U+2160+） | 罗马数字同上 | 加 `{"2160 -> "216B}`，或映射成 ASCII `I/II/III` |
| 下标 `₁₂`、`↔` 等缺字 | 裸 unicode 不在数学字体 | 全部并入 `USYM` 映射 |
| `Missing $ inserted` | `$` 当美元号用（`$1.5/£`），被误配成数学定界 | 规则：`$..$` 内**含中文且无 `\`** 才判为货币、按字面；真公式必有 `\`。`\$` 先换哨兵 |
| 中文跑进数学模式、`Missing 某/银/…` | `$$..$$` 里夹了裸中文，或多行 `$$` 被按行切碎 | 多行 `$$` **整体预抽**；display 内裸中文用 `\text{…}` 包；`£/€` 用 `\mbox{\pounds}/\mbox{\euro}` |
| 一行排不下、`Overfull \hbox 184pt` | 超长不可断串（如 40 个数列） | 把纯数字列在逗号处拆成多段 `$..$`；并 `\emergencystretch=4em` |
| `Fontconfig error: Cannot load default config` | tectonic 无系统字体 | **忽略**，ctex 自动用 Fandol |
| `import fitz` 失败 | 脚本目录有 `inspect.py` 等与 stdlib 同名 | 改名/删除 |
| Edit 改不动转换器 | 源码里有真控制字符 | 占位符一律用 `chr(1)` 等函数写，别写字面控制字符 |
| 表格变成一堆 `|` 转义 | 没做表格解析 | markdown 表格走 `parse_table` → `tabular` |

---

## 8. 编译与预览命令

**编译**（PowerShell，UTF-8）：
```powershell
$env:PYTHONIOENCODING="utf-8"
$base = "<...>_整理"
$tect = "C:\Users\21033\Desktop\金融风险管理\课件\_tex\tectonic.exe"
py "$base\_build\convert_xxx.py"
& $tect --outdir $base "$base\xxx.tex" 2>&1 |
  Select-String -Pattern "^error|Missing \$|Fatal|Missing character|Undefined control|Overfull" | Select-Object -First 12
Write-Output "exit: $LASTEXITCODE"
Remove-Item -Force "$base\xxx.aux","$base\xxx.log" -ErrorAction SilentlyContinue
py -c "import fitz; print(fitz.open(r'$base\xxx.pdf').page_count)"
```

**预览**：见 `preview.py`（全页 PNG / 整书拼图 / 单页切上下两半放大）。核验顺序：先拼图看结构 → 再放大看公式、表格、目录、计算步骤。

---

## 9. 一句话 SOP

> 放大/解析源 → 结构化 JSON 并核对题数 →（计算题交叉验证）→ `template_convert.py` 出 tex → tectonic 编译（清零 Missing/Overfull）→ PyMuPDF 切半放大逐页核验 → 清理临时文件、导 txt 备用。
