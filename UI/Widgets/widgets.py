# -*- coding: utf-8 -*-
# c:\boatrace\UI\Widgets\widgets.py

from __future__ import annotations
import os, math
import tkinter as tk
from pathlib import Path
from PIL     import Image, ImageTk

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"
HDR_COLOR          = "#e9f1f2"

WEATHER_DIR     = r"C:\boatrace\tmp\weather_icon"
H_TYPE_ICON_DIR = r"C:\boatrace\tmp\held_type_icon"
PLAYER_IMG_DIR  = Path(r"C:\boatrace\tmp\assets\players")
ICON_CACHE      = {}
PLAYER_IMG_CACHE:dict[tuple[int,int,int], "ImageTk.PhotoImage"] = {}
IMG_CACHE:       dict[tuple[int,int,int], "ImageTk.PhotoImage"] = {}

# ==============================================================================
# ----------------------------
def _wid(s: str) -> str:
    hair = "\u200A" 
    return hair.join(list(s))

#  ============================== グラフ表示 ===================================
# ==============================================================================
def framing_graph( self, frame:tk.Frame, frame_order, rows1, rows2=None, s_lane=0,
                                                     W=248, H=266):
    #---------------
    def nz(v):
        try:    return float(v)
        except: return 0.0
    #---------------
    for w in frame.winfo_children(): w.destroy()

    Colr1    = "#FFF4AA" ;ColrA    = "#E5EAD5"
    Colr2    = "#33EE33" ;ColrB    = "#CCF8CC"
    Colr3    = "#2A62FF" ;ColrC    = "#92ADFF"
    EDGE1    = "#000010" ;EDGE2    = "#689d9b"
    lane_col = "#9ee7ff" ;subj_col = "#8ddde9"

    cv     = tk.Canvas(frame, width=W, height=H) ;cv.place(x=-2, y=-2)
    lane_H = H // 6
    s_frno = frame_order[s_lane -1]

    for lane in range(1, 7):
        frno  = frame_order[lane -1]
        data  = rows1[frno]["own"] if rows1[frno].get("own", None) else rows1
        s_row = rows1[s_frno] if s_lane else None

        sL   = (lane -1) *lane_H +2;eL = sL +lane_H
        s1   = sL +15              ;e1 = s1 +10       # ｸﾞﾗﾌ1 始端/終端(Y)
        s2   = e1 +2               ;e2 = s2 +5        # ｸﾞﾗﾌ2 始端/終端(Y)

        cv.create_rectangle(0, sL, W, eL, fill=(subj_col if lane == s_lane else lane_col))

        cv.create_line(   1, sL,  W+1, sL, fill="#a4b7cb", width=1) # lane区切り 
        cv.create_line(   1, sL,    1, eL, fill="#a8a8a8", width=1) # 始端線
        cv.create_line(W//2, sL, W//2, eL, fill="#00ceff", width=1) # 中央線

        if rows1[frno].get("absn", None): continue

        if s_lane in [0, lane]:
            rate1  = nz(data[lane]["rate"][1])
            rate2  = nz(data[lane]["rate"][2])
            rate3  = nz(data[lane]["rate"][3])
        else:
            rate1 = nz(s_row["oth"][s_lane][lane][1])
            rate2 = nz(s_row["oth"][s_lane][lane][2])
            rate3 = nz(s_row["oth"][s_lane][lane][3])

        seg1 =        int(W * rate1)
        seg2 = seg1 + int(W * rate2)
        seg3 = seg2 + int(W * rate3)

        cv.create_rectangle(       0, s1, seg1, e1, fill=Colr3, outline=EDGE1, width=1)
        if seg2 != seg1:
            cv.create_rectangle(seg1, s1, seg2, e1, fill=Colr2, outline=EDGE1, width=1)
        if seg3 != seg2:
            cv.create_rectangle(seg2, s1, seg3, e1, fill=Colr1, outline=EDGE1, width=1)

        if rows2:
            rateA = nz(rows2[lane]["rate"][1]) ;segA =        int(W * rateA)
            rateB = nz(rows2[lane]["rate"][2]) ;segB = segA + int(W * rateB)
            rateC = nz(rows2[lane]["rate"][3]) ;segC = segB + int(W * rateC)
            cv.create_rectangle(       0, s2, segA, e2, fill=ColrC, outline=EDGE2, width=1)
            if segB != segA:
                cv.create_rectangle(segA, s2, segB, e2, fill=ColrB, outline=EDGE2, width=1)
            if segC != segB:
                cv.create_rectangle(segB, s2, segC, e2, fill=ColrA, outline=EDGE2, width=1)

# =========================== スリット図表示 ===================================
# ==============================================================================
def framing_figure(self, fig_frame:tk.Frame, frame_order:list, A:dict=None, B:dict=None):

    # --------------
    def load_scaled_boat(lane:int, target_w):

        key      = (lane, target_w)
        if key in fig_boat_imgs: return fig_boat_imgs[key]

        fname    = f"boat{lane}.png"
        fpath    = os.path.join(base_dir, fname)
        img      = tk.PhotoImage(file=fpath)
        base_w   = img.width()
        img      = Image.open(fpath).convert("RGBA")
        w0, h0   = img.size
        target_h = max(1, int(h0 * (target_w / w0))) -4
        pil      = img.resize((target_w, target_h), Image.LANCZOS)
        tkimg    = ImageTk.PhotoImage(pil)

        fig_boat_imgs[key] = tkimg

        return tkimg
    # --------------
    for w in fig_frame.winfo_children(): w.destroy()

    adW          = 24 if B else 0
    W, H, row_h  = 256, 264, 44
    cv           = tk.Canvas(fig_frame, width=W + adW, height=H) ; cv.place(x=-2, y=-1)

    if not hasattr(fig_frame, "_img_refs"    ): fig_frame._img_refs     = []
    if not hasattr(fig_frame, "fig_boat_imgs"): fig_frame.fig_boat_imgs = {} 

    base_dir      = r"C:\boatrace\tmp\slit_figure"
    bg_path       = os.path.join(base_dir, "bg.jpg")
    img           = Image.open(bg_path).convert("RGB")
    img           = img.resize((W+adW, H), Image.LANCZOS)
    bg_img        = ImageTk.PhotoImage(img)
    fig_boat_imgs = fig_frame.fig_boat_imgs

    fig_frame._img_refs.append(bg_img) 
    cv.create_image(0, 0, image=bg_img, anchor="nw")

    sec_range  = [ -6, -5, -4, -3, -2, -1, 0, 1, 1.5]
    px_per_sec = W / 0.75
    zero_x     = px_per_sec * 0.6 +adW
    target_w   = int(px_per_sec * 0.15)

    cv.create_line(zero_x, 0, zero_x, H, fill="#d58b36", width=1) # ｽﾘｯﾄﾗｲﾝ

    for k in sec_range:
        x = zero_x + (k * 0.1 * px_per_sec)
        if x == zero_x: continue
        cv.create_line(x, 0, x, H, fill="#00ceff", width=1)       # 0.1秒線

    for lane in range(1, 7):

        frno = frame_order[lane-1]
        v    = A[frno]["st"] if A else B[frno]["st"]

        if v == None: continue

        st       = float(v) if v != "" else 0.47
        right_x  = zero_x - (st * px_per_sec) +5
        boat_img = load_scaled_boat(frno, target_w)
        cy       = (lane - 1) * row_h + row_h // 2 +3

        fig_frame._img_refs.append(boat_img) 
        cv.create_image(right_x, cy, image=boat_img, anchor="e")

        if v == "":
            txt = " ー"
        else: 
            tx  = f"{st:.2f}"
            txt = f"{tx[1:]}" if st >= 0 else f"{tx[2:]}"

        t_col = "red" if st < 0 else "black"
        cv.create_text(234+adW, (lane-1)*44+22, text=_wid(list(txt)), fill=t_col, font=(GUI,10,BD))

        if B and B[frno]["opt"]:
            opt = B[frno]["opt"]
            cv.create_text(15, (lane-1)*44+22, anchor="w", **opt)

# ========================= 天気・風向アイコン表示 =============================
# ==============================================================================
def framing_weather(self, fr_wthr:tk.Frame, fr_wdir:tk.Frame, rows:dict):

    # --------------
    def _center_fit_rgba(pil_img: Image.Image, size=(43, 43)):

        w0, h0 = pil_img.size
        W, H   = size
        scale  = min(W / max(1, w0), H / max(1, h0))
        nw, nh = max(1, int(w0 * scale)), max(1, int(h0 * scale))
        img    = pil_img.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        canvas.paste(img, ((W - nw) // 2, (H - nh) // 2), img)

        return canvas
    # --------------
    def _photo_cached(path:str, angle:float|None, size=(45, 45)):

        key = (path, round(angle or 0.0, 2), size[0], size[1])
        if key in ICON_CACHE: return ICON_CACHE[key]

        basename = os.path.basename(path).lower()
        if "arrow" in basename and angle is not None:
            arrow_px = 32
            base     = Image.open(path).convert("RGBA").resize((arrow_px, arrow_px),
                                                               Image.LANCZOS)
            pad      = int(arrow_px * 2.2)
            tmp      = Image.new("RGBA", (pad, pad), (0, 0, 0, 0))
            tmp.paste(base, ((pad -arrow_px) // 2, (pad -arrow_px) // 2), base)

            rot      = tmp.rotate(angle, resample=Image.BICUBIC, expand=True)
            W, H     = size
            cx, cy   = rot.size[0] / 2, rot.size[1] / 2
            left     = max(0, cx - W / 2) ; top = max(0, cy - H / 2)
            crop     = rot.crop((left, top, left + W, top + H))
            tkimg    = ImageTk.PhotoImage(crop)
            ICON_CACHE[key] = tkimg

            return tkimg

        im    = Image.open(path).convert("RGBA")
        if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)

        im              = _center_fit_rgba(im, size)
        tkimg           = ImageTk.PhotoImage(im)
        ICON_CACHE[key] = tkimg

        return tkimg
    # --------------
    for frame in [fr_wdir, fr_wthr]:
        if not hasattr(frame, "_img_refs"): frame._img_refs = []

        for w in frame.winfo_children(): w.destroy()

    data = rows[0] if rows[0] else []
    wdir = int(data["wdir"]) if data["wdir"] else None
    wthr = str(data.get("wthr", "") or "")
    wmap = {   "晴": "extracted_sunny_45.png",
             "曇り": "extracted_cloudy_45.png",
               "雨": "extracted_rain_45.png",
               "雪": "extracted_snow_45.png",   }
    # ------------- 天気 ---------------
    icon_path = os.path.join(WEATHER_DIR, wmap[wthr]) if wthr in wmap else None

    if icon_path:
        tkimg = _photo_cached(icon_path, angle=None, size=(43, 43))
        fr_wthr._img_refs.append(tkimg)
        tk.Label(fr_wthr, image=tkimg, bg=HDR_COLOR).grid(sticky="nsew")
    else:
        tk.Label(fr_wthr, text="", bg=HDR_COLOR).grid(sticky="nsew")

    # -------------- 風向 --------------
    arrow_path = os.path.join(WEATHER_DIR, "extracted_arrow_45.png")

    if  wdir and 1 <= wdir <= 16:
        step  = (wdir -1) %16
        angle = -22.5 *step
        tkimg = _photo_cached(arrow_path, angle=angle, size=(45,45))
        fr_wdir._img_refs.append(tkimg)
        tk.Label(fr_wdir, image=tkimg, bg=HDR_COLOR).grid(sticky="nsew" )
    else:
        tk.Label(fr_wdir, text="", bg=HDR_COLOR).grid(sticky="nsew")

# ============================= 選手画像更新 ===================================
# ==============================================================================
def set_player_image(label:tk.Label, player_id:int, size:tuple[int, int]):

    w, h = int(size[0]), int(size[1])
    key  = (int(player_id), w, h)

    if not key in PLAYER_IMG_CACHE:
        p = PLAYER_IMG_DIR / f"{int(player_id)}.jpg"

        if not p.exists(): return
        try:
            im     = Image.open(p).convert("RGB")
            iw, ih = im.size
            if iw <= 0 or ih <= 0: return
    
            scale = min(w / iw, h / ih)
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))
            im    = im.resize((new_w, new_h), Image.LANCZOS)
            img   = ImageTk.PhotoImage(im)
            PLAYER_IMG_CACHE[key] = img

        except Exception: return
    else: img = PLAYER_IMG_CACHE[key]

    label.configure(image=img, text="")
    label._player_photo_ref = img

# ============================ 欠場ﾌﾚｰﾑ ﾏｽｸ処理 ================================
# ==============================================================================
def apply_absent_bg(lane_frame:tk.Misc, gray:str = "#cfcfcf"):

    def _walk(root):
        yield root
        for ch in getattr(root, "winfo_children", lambda: [])():
            yield from _walk(ch)

    for w in _walk(lane_frame):
        try:
            w.configure(background=gray)
            w.configure(fill=gray)
        except: pass
            
#============================ ウィジェット初期化 ===============================
# ==============================================================================
def clear_all_lanes(self):

    for lane in range(1, 7):
        m = self._widgets_main.get(lane, {})
        s = self._widgets_sub.get( lane, {})

        for key in ("regp", "pid",  "rgns", "name", "age", "wkg", "clss", "scav",
                    "late", "flyg", "stav", "mo_av", "mo_pr", "ve_av", "ve_ac"):
            if key in m: m[key].config(text="")

        for key in ("frno", "name",  "flyg", "tilt", "exib", "cnt", "repr"):
            if key in s: s[key].config(text="")
        #-----------
        def _walk(w):
            yield w
            for ch in w.winfo_children(): yield from _walk(ch)
        #-----------
        if self.is_absent:
            for w in _walk(m["Lane"]):
                try: w.configure(bg="white")
                except Exception: pass

        for cell in m.get("R_hdr"):
            for ch in cell.winfo_children(): ch.destroy()
        for cels in m.get("R_bdy"):
            for cell in cels:
                for ch in cell.winfo_children(): ch.destroy()
        for cell in m.get("R_idx"):
            for ch in cell.winfo_children(): ch.destroy()

# ============================ 開催種アイコン表示 ==============================
# ==============================================================================
def framing_held_type_icon(self, lbl: tk.Label, h_type: int):

    if not h_type:
        lbl.configure(image="", text="")
        setattr(lbl, "_held_img", None)
        return

    base_map = {1: "morning", 2: "summertime", 3: "nighter", 4: "midnight"}
    base     = base_map.get(h_type)
    path     = os.path.join(H_TYPE_ICON_DIR, f"{base}.png")
    img      = tk.PhotoImage(file=path)
    lbl.configure(image=img)
    setattr(lbl, "_held_img", img)
