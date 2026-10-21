# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\build_series_idx.py

from typing      import List, Dict, Optional
from tkinter     import ttk
from datetime    import datetime as dt, date, timedelta, timezone
from collections import defaultdict
import re, tkinter as tk

from Helpers.Custum_func import cFr, cLbl, cBtn
from widgets import apply_absent_bg
import Dal as dal

RE_FINAL = re.compile(    r"(?<!準)"
                          r"(?!進出|進)"
                          r"(?:優勝戦|優\s*勝\s*戦|決勝戦|(?<=.{4})優勝"
                                                       r"|(?<=.{5})優)"
                       r"|(?:王将位決定戦|初優勝決定戦"
                          r"|賞金女王決定|賞金王決定戦"
                          r"|是政女王決定|是政王子決定|是政名人決定|是政プリンス"
                          r"|海の王者決定|波乗り王決定|ヘビー級王決"
                          r"|オオムラＧＰ|Ｇ・Ａ決定戦"
                          r"|関ヶ原決戦|王座決定戦|団体・優勝"
                          r"|澤乃井ファイ|ファイナル\s*$)",re.I )

FRAME_COLORS   = { 0: dict(bg="white",   fg="#000000"),
                   1: dict(bg="#FFFFFF", fg="#000000"),
                   2: dict(bg="#000000", fg="#FFFFFF"),
                   3: dict(bg="#D40000", fg="#FFFFFF"),
                   4: dict(bg="#0066CC", fg="#FFFFFF"),
                   5: dict(bg="#FFD400", fg="#000000"),
                   6: dict(bg="#008A2E", fg="#FFFFFF"), }

RNK_BY_C_POINT = { 1:{1:0, 2:-1, 3:-2, 4:-3, 5:-3, 6:-4},
                   2:{1:2, 2: 0, 3: 0, 4:-1, 5:-2, 6:-3},
                   3:{1:2, 2: 0, 3: 0, 4:-1, 5:-2, 6:-3},
                   4:{1:3, 2: 1, 3: 0, 4: 0, 5:-1, 6:-2},
                   5:{1:4, 2: 3, 3: 1, 4: 0, 5: 0, 6:-1},
                   6:{1:5, 2: 3, 3: 2, 4: 1, 5: 0, 6:-1}, }

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"
"#E9F1F2"

BG_COL   = "#F0F4FA"
HL_BLU   = "#D0E3FF"
BLUE2    = "#0D7DDA"
WHITE    = "#FFFFFF"
BLACK    = "#000000"
HDR_BG   = "#2B4A7A"
BTN_BG   = "#4A6A9A"
R_N_OPT = dict(bg="#bacae2", fg="BLACK", Bd=(1,GR))

HDR_B    = dict(bg=HDR_BG)
HDR_BF   = dict(bg=HDR_BG, fg=WHITE)
BTN_BF   = dict(bg=BTN_BG, fg=WHITE)
BTN_OPT  = dict(bg=BTN_BG, fg=WHITE, Bd=(1,RA), Csr="hand2")

TODAY = dict(fg=WHITE, bg="#006cc5", Bd=(1,RD))
OTHER = dict(fg=WHITE, bg=HDR_BG,    Bd=(1,GR))

# ------------------
def today_iso() -> str:

    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date().strftime("%Y-%m-%d")

# ------------------
def to_str(x) -> str:

    if isinstance(x,  str): return x
    if isinstance(x, date): return x.strftime("%Y-%m-%d")

    raise ValueError("str conv error")

# ------------------
def to_date(x) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return date.fromisoformat(x)

    raise ValueError("date conv error")

#-----------------------------
def days_ago(d:str, range:int):

    d = to_date(d)

    return to_str(d -timedelta(days=range))

# ------------------
def w_txt(s:str) -> str:

    hair = "\u200A"

    return hair.join(list(s))

# ----------------------------------------------------------
def build_day_lbl(d_iso:str, venue_id:int):

    row = dal.fetch_one(
        """
        SELECT series_title
          FROM Race_programs
         WHERE date     = ?
           AND venue_id = ?
         LIMIT 1
        """,
        (d_iso, venue_id) )

    series_title = row[0]
    max_date     = days_ago(d_iso, 10)

    dates = dal.fetch_all("""
        SELECT DISTINCT date
          FROM Race_programs
         WHERE venue_id     = ?
           AND series_title = ?
           AND date BETWEEN ? AND ?
      ORDER BY date ASC
        """,
        (venue_id, series_title, max_date, d_iso) )

    candidates = [r[0] for r in dates]
    if not candidates: return [], []

    placeholders = ",".join("?" * len(candidates))

    held_rows = dal.fetch_all(f"""
                    SELECT date,
                           COUNT(1) AS cnt
                      FROM Races
                     WHERE venue_id = ?
                       AND status   = 'held'
                       AND date IN ({placeholders})
                  GROUP BY date
                    """,
                    (venue_id, *candidates))

    held_dates = {r[0]:int(r[1]) for r in held_rows}
    meta       = []

    for d in candidates:
        held_race   = held_dates.get(d, 0)
        carried_out = (held_race >= 6)
        visible     = True if d == d_iso else (held_race > 0)

        meta.append( {        "date":d,
                         "held_race":held_race,
                       "carried_out":carried_out,
                           "visible":visible,
                         "final_day":False,       } )

    day_no           = 1
    prev_carried_out = False

    for item in meta:
        if prev_carried_out: day_no += 1

        item["day_no"]   = day_no
        prev_carried_out = item["carried_out"]

    if meta:
        last      = meta[-1]
        last_date = last["date"]

        rows = dal.fetch_all("""
            SELECT DISTINCT race_title
              FROM Race_programs
             WHERE date     = ?
               AND venue_id = ?
            """,
            (last_date, venue_id))

        last["final_day"] = any(RE_FINAL.search(title[0] or "") for title in rows)
        visible           = [item for item in meta if item.get("visible", True)]

        if len(visible) > 7:
            visible = visible[-7:]

        slots:list[dict] = visible[:]

        while len(slots) < 7:
            slots.insert(7, None)

    return meta, slots

# ----------------------------------------------------------
def get_lineup(rows):

    lineup = {fn:rows[fn]["pid"] for fn in range(1,7)}

    return lineup

# ----------------------------------------------------------
def get_other_race(d_iso:str, venue_id:int, player_id:int, race_no:int):

    rows = dal.fetch_all(
        """
        SELECT race_no, frame_no
          FROM Race_programs
         WHERE date      = ?
           AND venue_id  = ?
           AND player_id = ?
      ORDER BY Race_programs.race_no ASC
        """,
        (d_iso, venue_id, player_id)) or []

    if len(rows) < 2: return [0, 0]

    race1 = rows[0]
    race2 = rows[1]

    return race2 if race_no == race1["race_no"] else race1

# ----------------- 日程ヘッダ 表示/更新 -------------------
def update_series_idx(self, d_iso:str, venue_id:int, race_no:int):

    lineup    = get_lineup(self.entry_rows)
    _, slots  = build_day_lbl(d_iso, venue_id)
    today_idx = sum(1 for n in range(7) if slots[n]) -1

    for lane in range(1, 7):
        cells = self.widgets_idx[lane]["R_hdr"]
        for i in range(7):
            hedr = cells[i]
            info = slots[i]
            hedr.config(text="", bg=BG_COL)
            if info:
                dn   = info.get("day_no")
                text = "初  日" if dn == 1           else f"{dn}日目"
                text = "最終日" if info["final_day"] else text
                hedr._config(text=text, **TODAY if i == today_idx else OTHER, Anc="n", py=5)

    _assign_series_idx(self, slots, lineup)
    _assign_other_run(self, lineup)

# ------------------ 節間成績 表示/更新 --------------------
def _assign_series_idx(self, slots, lineup):

    p_ids = {lineup[self.frame_order[ln -1]]:0 for ln in range(1,7)}
    dates = {i["date"]:0 for i in slots if i}

    p_ph = ",".join("?" * len(p_ids))
    d_ph = ",".join("?" * len(dates))

    rows = dal.fetch_all(f"""
        SELECT r.date,
               e.player_id,
               r.race_no,
               e.frame_no,
               e.course,
               e.slit_ADJ,
               e.finish_rank,
               e.fault_code
          FROM        Races r
          JOIN Race_entries e ON e.race_id = r.race_id

         WHERE e.player_id IN ({p_ph})
           AND r.date      IN ({d_ph})
           AND r.venue_id  = ?

      ORDER BY e.player_id, r.date, r.race_no ASC
        """,
        (*p_ids, *dates, self.venue_id))

    result_map:dict[tuple,list] = defaultdict(list)

    for row in rows:
        key = (row["player_id"], row["date"])
        result_map[key].append(row)

    base_date = self.date
    # --------------
    def _filter_rows(d_iso, rows):
        if d_iso == base_date:
            return [r for r in rows if r["race_no"] < self.race_no]
        return rows
    # --------------
    def _conv_one(row):

        slit = row["slit_ADJ"]
        A    = row["race_no"]
        B    = row["course"]
        C    = ((f"{slit:.2f}").strip('-'))[1:] if slit else ""
        D    = row["finish_rank"] or row["fault_code"]
        E    = row["frame_no"]

        return (A, B, C, D, E)
    # --------------
    for lane in range(1, 7):
        p_id  = lineup[self.frame_order[lane -1]]
        cells = self.widgets_idx[lane]["R_bdy"]

        for col_cells in cells:
            col_cells[0].unbind("<Button-1>")
            for r in range(4):
                col_cells[r]._config(text="", bg=BG_COL, Bd=(1,GR), fg="black", Csr="")

        for i in range(7):
            info  = slots[i]
            if not info: continue
            d_iso = info.get("date")
            row   = _filter_rows(d_iso, result_map.get((p_id, d_iso), []))[:2]
            if d_iso < self.date and len(row) >= 1:
                cells[i*2 +1][0]._config(text="", **R_N_OPT)

            L     = _conv_one(row[0]) if len(row) >= 1 else None
            R     = _conv_one(row[1]) if len(row) >= 2 else None

            if L: _paint_abcd(self, cells[i*2   ], L[0], L[1], L[2], L[3], L[4], d_iso)
            if R: _paint_abcd(self, cells[i*2 +1], R[0], R[1], R[2], R[3], R[4], d_iso)

# ----------------------------------------------------------
def _paint_abcd(self, cells:list, r_no:int, course:int, st:str, rank:str, f_no:int, d:str):

    col = FRAME_COLORS[f_no]
    fg  = "red" if rank in ("F", "L", "S", "K") else "black"

    cells[0]._config(text=w_txt(f"{r_no}R"), font=(GUI,8,BD), **R_N_OPT, Csr="hand2", Anc="n", py=5)
    cells[1]._config(text=course,            font=(GUI,9,BD), **col, Bd=(3,GR))
    cells[2]._config(text=st,                font=(MUI,8),    fg=fg, bg=WHITE, Bd=(1,GR))
    cells[3]._config(text=rank,              font=(GUI,9,BD), fg=fg, bg=WHITE, Bd=(1,GR))
    cells[0].bind("<Button-1>", lambda e:self._reload_for(d, self.venue_id, r_no, result=True))

# --------------- 2走インデックス 表示/更新 ----------------
def _assign_other_run(self, lineup):

    for lane in range(1, 7):
        cells = self.widgets_idx[lane]["R_idx"]
        cells[2].unbind("<Button-1>")
        for i in range(3):
            cells[i]._config(text="", bg=HDR_BG, Bd=(1,"flat"))

        p_id  = lineup[self.frame_order[lane -1]]
        other = get_other_race(self.date, self.venue_id, p_id, self.race_no)
        if other[0] == 0: continue

        opts1 = dict(font=(GUI,10,BD), bg=HDR_BG)
        opts2 = FRAME_COLORS[other[1]] | dict(font=(MUI,8,BD), Bd=(1,RD))
        #-----------
        def _go(rno):
            self._reload_for(self.date, self.venue_id, rno, result=True)
        #-----------
        cells[0]._config(text=f"{other[0]}R", **opts1)
        cells[1]._config(text=other[1],       **opts2)
        cells[2]._config(text=">",     font=(MUI,9,BD), **BTN_OPT, py=8)
        cells[2].bind("<Button-1>", lambda e, rno=other[0]:_go(rno))

# ----------------------------------------------------------
