#!/usr/bin/env python3
"""Recolor the TOC (slide 2) raster decorations from cyan to the app's indigo.
Hue-rotates cyan-range pixels -> indigo, preserves white card interiors + alpha."""
import zipfile, shutil, io, os
import numpy as np
from PIL import Image

SRC = "/opt/ai-anti-spam-shield-crm/edit-slide-defense/ai-scam-shield.-draft_0.0.3.pptx"
TARGETS = [f"ppt/media/image{n}.png" for n in [25,26,27,28,29,30,31,32,33,34]]

TARGET_HUE = 245/360.0   # indigo (#818CF8 ~245deg)

def recolor_bytes(data):
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    arr = np.asarray(im).astype(np.float32)/255.0
    r,g,b,a = arr[...,0],arr[...,1],arr[...,2],arr[...,3]
    mx = np.max(arr[...,:3],axis=-1); mn = np.min(arr[...,:3],axis=-1)
    df = mx-mn
    # hue (0..1)
    hue = np.zeros_like(mx)
    mask = df>1e-6
    # compute hue
    rc = ((mx-r)/np.where(mask,df,1))
    gc = ((mx-g)/np.where(mask,df,1))
    bc = ((mx-b)/np.where(mask,df,1))
    h = np.where(mx==r, bc-gc, np.where(mx==g, 2.0+rc-bc, 4.0+gc-rc))
    hue = (h/6.0) % 1.0
    sat = np.where(mx>0, df/np.where(mx>0,mx,1), 0)
    val = mx
    # cyan-range pixels (hue ~150..210deg = .416..583) with enough saturation
    cyan = (hue>0.40)&(hue<0.60)&(sat>0.12)
    new_hue = np.where(cyan, TARGET_HUE, hue)
    # HSV -> RGB (vectorized)
    i = np.floor(new_hue*6).astype(int)%6
    f = new_hue*6 - np.floor(new_hue*6)
    pp = val*(1-sat); qq = val*(1-f*sat); tt = val*(1-(1-f)*sat)
    rr = np.select([i==0,i==1,i==2,i==3,i==4,i==5],[val,qq,pp,pp,tt,val])
    gg = np.select([i==0,i==1,i==2,i==3,i==4,i==5],[tt,val,val,qq,pp,pp])
    bb = np.select([i==0,i==1,i==2,i==3,i==4,i==5],[pp,pp,tt,val,val,qq])
    out = np.stack([rr,gg,bb,a],axis=-1)
    out = np.clip(out*255,0,255).astype(np.uint8)
    res = Image.fromarray(out,"RGBA")
    buf=io.BytesIO(); res.save(buf,"PNG"); return buf.getvalue()

zin=zipfile.ZipFile(SRC,'r'); tmp=SRC+".tmp"
zout=zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data=zin.read(item.filename)
    if item.filename in TARGETS:
        data=recolor_bytes(data); print("recolored", item.filename)
    zout.writestr(item,data)
zout.close(); zin.close()
shutil.move(tmp,SRC)
print("saved")
