# -*- coding: utf-8 -*-
"""
kailatex 预览工具 —— 用 PyMuPDF 把 PDF 转 PNG 供 Read 核验（本机无 poppler，Read 不能直接渲染 PDF）。
用法：
  py preview.py <pdf>                 # 整书缩略拼图 _prev\_montage.png（看结构/空页/破版）
  py preview.py <pdf> full 1 7 12     # 指定页整页放大 _prev\full{n}.png
  py preview.py <pdf> half 8          # 把某页切上下两半（zoom 3）_prev\p8_1/2.png（核验公式细节）
核验顺序：先 montage 看整体 → 再 full/half 放大看 公式/表格/目录/计算步骤。
整页在对话里会被缩小看不清 → 公式一定用 half 切半看。
"""
import sys, os, fitz
from PIL import Image, ImageDraw

pdf_path = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'montage'
od = os.path.join(os.path.dirname(pdf_path), '_prev')
os.makedirs(od, exist_ok=True)
d = fitz.open(pdf_path)
N = d.page_count

def render(pno, zoom):
    pix = d[pno-1].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.frombytes('RGB', [pix.width, pix.height], pix.samples)

if mode == 'montage':
    ims = [render(i+1, 0.45) for i in range(N)]
    tw, th = ims[0].size; cols = 8; rows = (N+cols-1)//cols; pad = 4
    sh = Image.new('RGB', (cols*tw+(cols+1)*pad, rows*th+(rows+1)*pad), 'white')
    dr = ImageDraw.Draw(sh)
    for i, im in enumerate(ims):
        r, c = divmod(i, cols); x = pad+c*(tw+pad); y = pad+r*(th+pad)
        sh.paste(im, (x, y)); dr.rectangle([x-1, y-1, x+tw, y+th], outline='#bbb'); dr.text((x+2, y+1), str(i+1), fill='red')
    sh.save(os.path.join(od, '_montage.png'))
    print('wrote', os.path.join(od, '_montage.png'), '| pages', N)
elif mode == 'full':
    for p in map(int, sys.argv[3:]):
        render(p, 2.3).save(os.path.join(od, f'full{p}.png')); print('full', p)
elif mode == 'half':
    for p in map(int, sys.argv[3:]):
        img = render(p, 3.0); W, H = img.size
        for k in (0, 1):
            img.crop((0, int(H*k/2), W, int(H*(k+1)/2))).save(os.path.join(od, f'p{p}_{k+1}.png'))
        print('half', p)
