#!/usr/bin/env python
"""Deterministic, ZERO-CREDIT overlay tool for spec deliverables.
Two modes — both composite precise vector-style callouts onto a clean render so you
never pay an image model to (badly) type dimension text or labels.

  dims     : drafting-convention dimension lines auto-placed from the detected
             silhouette. Auto-assigns the larger/smaller value to taller/shorter sides.
  annotate : leader-line callouts naming features, labels parked in the margins.

Requires: pillow, numpy  (pip install pillow numpy)

Usage:
  python overlay.py dims     <in.png> <out.png> <dims.json>
  python overlay.py annotate <in.png> <out.png> <annos.json>

dims.json   : {"bg_thresh":38,"title":"...","callouts":[
                {"type":"width","value":"W 210 cm"},
                {"type":"height","side":"auto","pair":["110 cm","86 cm"]},   # taller→1st
                {"type":"height","side":"full_right","value":"155 cm"},
                {"type":"note","text":"Depth (D) 80 cm"}]}
annos.json  : {"title":"ADDITIONS vs original","banner":"#26303f",
               "callouts":[{"x":0.5,"y":0.10,"side":"L","text":"Illuminated header sign"}]}

`banner` is any CSS hex and defaults to a neutral slate. Callout `x`/`y` are fractions of
image width/height, so coordinates stay valid when you re-render at another resolution.
"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MODE, INP, OUT, CFG = sys.argv[1], sys.argv[2], sys.argv[3], json.load(open(sys.argv[4], encoding="utf-8"))
im = Image.open(INP).convert("RGB"); W, H = im.size
draw = ImageDraw.Draw(im); INK = (40, 40, 46)

def font(sz, bold=True):
    for p in ([f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()

def label(cx, cy, txt, F):
    tb = draw.textbbox((0,0), txt, font=F); tw, thh = tb[2]-tb[0], tb[3]-tb[1]; pad=12
    draw.rectangle([cx-tw/2-pad, cy-thh/2-pad, cx+tw/2+pad, cy+thh/2+pad], fill=(255,255,255), outline=INK, width=3)
    draw.text((cx-tw/2, cy-thh/2-tb[1]), txt, fill=INK, font=F)

def arrow(p, q):
    import math
    draw.line([p, q], fill=INK, width=4); a = math.atan2(q[1]-p[1], q[0]-p[0])
    for s in (-0.5, 0.5):
        draw.line([q, (q[0]-26*math.cos(a+s), q[1]-26*math.sin(a+s))], fill=INK, width=4)

def silhouette():
    a = np.asarray(im).astype(int)
    corners = np.concatenate([a[:40,:40].reshape(-1,3), a[:40,-40:].reshape(-1,3),
                              a[-40:,:40].reshape(-1,3), a[-40:,-40:].reshape(-1,3)])
    bg = np.median(corners, axis=0)
    mask = np.sqrt(((a-bg)**2).sum(axis=2)) > CFG.get("bg_thresh", 38)
    xs = np.where(mask.sum(axis=0) > H*0.02)[0]; ys = np.where(mask.sum(axis=1) > W*0.02)[0]
    return mask, int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())

if MODE == "dims":
    mask, left, right, top, bottom = silhouette(); bw = right-left
    def counter_top(x0, x1):
        start = top + int(0.42*(bottom-top)); tops=[]
        for x in range(x0, x1):
            nz = np.where(mask[start:bottom, x])[0]
            if len(nz): tops.append(start+int(nz.min()))
        return int(np.median(tops)) if tops else start
    lct = counter_top(left+int(0.08*bw), left+int(0.25*bw))
    rct = counter_top(right-int(0.25*bw), right-int(0.08*bw))
    F = font(46)
    for c in CFG.get("callouts", []):
        t = c["type"]
        if t == "width":
            y = min(bottom+70, H-60)
            draw.line([(left,bottom),(left,y+18)], fill=INK, width=2); draw.line([(right,bottom),(right,y+18)], fill=INK, width=2)
            mid=(left+right)//2; arrow((mid,y),(left,y)); arrow((mid,y),(right,y)); label(mid,y,c["value"],F)
        elif t == "height" and c.get("side") == "full_right":
            x = min(right+230, W-70); m=(top+bottom)//2
            draw.line([(right,top),(x+14,top)],fill=INK,width=2); draw.line([(right,bottom),(x+14,bottom)],fill=INK,width=2)
            arrow((x,m),(x,top)); arrow((x,m),(x,bottom)); label(x,m,c["value"],F)
        elif t == "height":  # auto pair → taller side gets pair[0]
            tall_y, low_y = (lct, rct) if lct<=rct else (rct, lct)
            tall_left = lct <= rct
            xL=max(left-95,70); xR=min(right+95,W-70)
            def vd(x, ytop, txt, ext):
                m=(ytop+bottom)//2; draw.line([(ext,ytop),(x+14,ytop)],fill=INK,width=2)
                draw.line([(ext,bottom),(x+14,bottom)],fill=INK,width=2); arrow((x,m),(x,ytop)); arrow((x,m),(x,bottom)); label(x,m,txt,F)
            if tall_left: vd(xL, tall_y, c["pair"][0], left); vd(xR, low_y, c["pair"][1], right)
            else:         vd(xL, low_y, c["pair"][1], left); vd(xR, tall_y, c["pair"][0], right)
        elif t == "note":
            Fn=font(38); tb=draw.textbbox((0,0),c["text"],font=Fn)
            draw.rectangle([60,40,60+(tb[2]-tb[0])+28,40+(tb[3]-tb[1])+24], fill=(255,255,255), outline=INK, width=3)
            draw.text((74,50), c["text"], fill=INK, font=Fn)

elif MODE == "annotate":
    F = font(34); TITLE = font(40)
    title = CFG.get("title")
    if title:
        tb = draw.textbbox((0,0), title, font=TITLE)
        from PIL import ImageColor
        bc = ImageColor.getrgb(CFG.get("banner", "#26303f"))
        draw.rectangle([0,0,W,tb[3]-tb[1]+34], fill=bc); draw.text((30,16), title, fill=(244,244,247), font=TITLE)
    for c in CFG.get("callouts", []):
        ax, ay = int(c["x"]*W), int(c["y"]*H); lines = c["text"].split("\n")
        tw = max(draw.textbbox((0,0), ln, font=F)[2] for ln in lines)
        lh = draw.textbbox((0,0), "Ag", font=F)[3]+6; bh = lh*len(lines); pad=14
        bx = 40 if c.get("side","L")=="L" else W-40-tw-2*pad
        by = max(70, min(ay-bh//2, H-bh-40))
        draw.rectangle([bx,by,bx+tw+2*pad,by+bh+2*pad], fill=(255,255,255), outline=INK, width=3)
        for i, ln in enumerate(lines): draw.text((bx+pad, by+pad+i*lh), ln, fill=INK, font=F)
        sx = bx+tw+2*pad if c.get("side","L")=="L" else bx; sy = by+(bh+2*pad)//2
        draw.line([(sx,sy),(ax,ay)], fill=INK, width=3)
        from PIL import ImageColor as _IC
        draw.ellipse([ax-9,ay-9,ax+9,ay+9], fill=_IC.getrgb(CFG.get("accent", "#c98a2e")), outline=INK, width=3)
else:
    sys.exit("mode must be 'dims' or 'annotate'")

im.save(OUT); print(f"{MODE} -> {OUT}")
