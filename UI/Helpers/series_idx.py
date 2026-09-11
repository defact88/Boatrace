# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\series_idx.py

from typing      import List, Dict, Optional
from tkinter     import ttk
from datetime    import datetime as dt, date, timedelta, timezone
from collections import defaultdict
from Helpers.Custum_func    import cFr, cLbl, cBtn
import re, tkinter as tk
import Dal as dal

RE_FINAL = re.compile(
    r"(?:"
    r"(?<!準)(?<!準々)優勝戦"
    r"|(?<!準)(?<!準々)決勝戦"
    r"|(?<!初)(?<!準)(?<!準々)優\s*勝"
    r"|王将位決定戦"
    r"|賞金女王決定"
    r"|王座決定戦"
    r"|ファイナル\s*$"
    r"|海の王者決定"
    r"|是政名人決定"
    r"|波乗り王決定"
    r"|関ヶ原決戦"
    r"|団体・優勝"
    r"|オオムラＧＰ"
    r"|(?<=.{4})優勝"
    r"|(?<=.{5})優"
    r"|ヘビー級王決"
    r"|初優勝決定戦"
    r")"                                 )

FRAME_COLORS = { 1: dict(bg="#FFFFFF", fg="#000000"),
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

HDR_COLOR  = "#d0e3ff"
BG_COLOR   = "#e9f1f2"

# ------------------
def jst_today() -> date:
    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date()
# ------------------
def today_iso() -> str:
    return jst_today().strftime("%Y-%m-%d")
# ------------------
def wid_txt(s:str) -> str:
    hair = "\u200A"
    return hair.join(list(s))
# --------------------------------------------------------------------
def build_day_lbl(on_day:str, venue_id:int):

    row = dal.fetch_one(
        """
        SELECT series_title
          FROM Race_programs
         WHERE date     = ?
           AND venue_id = ?
         LIMIT 1
        """,
        (on_day, venue_id))

    series_title = row[0]
    max_d = (date.fromisoformat(on_day) - timedelta(days=10)).strftime("%Y-%m-%d")

    dates = dal.fetch_all(
        """
        SELECT DISTINCT date
          FROM Race_programs
         WHERE venue_id     = ?
           AND series_title = ?
           AND date BETWEEN ? AND ?
      ORDER BY date ASC
        """,
        (venue_id, series_title, max_d, on_day))

    candidates = [r[0] for r in dates]
    if not candidates: return [], []

    placeholders = ",".join("?" * len(candidates))
    held_rows = dal.fetch_all(
        f"""
        SELECT date, COUNT(1) AS cnt
          FROM Races
         WHERE venue_id = ?
           AND status   = 'held'
           AND date IN ({placeholders})
         GROUP BY date
        """,
        (venue_id, *candidates))

    held_dates = {r[0]: int(r[1]) for r in held_rows}
    meta       = []

    for d in candidates:
        held_race  = held_dates.get(d, 0)
        digested   = (held_race >= 6)
        visible    = True if d == on_day else (held_race > 0)
        meta.append( {
            "date"      : d,
            "held_race" : held_race,
            "digested"  : digested,
            "visible"   : visible,
            "final_day" : False,           } )

    label_no      = 0
    prev_digested = False

    for i, item in enumerate(meta):
        if i == 0: label_no = 1
        else:
            if prev_digested: label_no += 1
        item["label_no"] = label_no
        prev_digested    = item["digested"]

    if meta:
        last      = meta[-1]
        last_date = last["date"]

        rows = dal.fetch_all(
            """
            SELECT DISTINCT race_title
              FROM Race_programs
             WHERE date     = ?
               AND venue_id = ?
            """,
            (last_date, venue_id))

        last["final_day"] = any(RE_FINAL.search(r[0] or "") for r in rows)

        visible = [item for item in meta if item.get("visible", True)]
        if len(visible) > 7: visible = visible[-7:]

        slots:list[dict] = visible[:]

        while len(slots) < 7:
            slots.insert(7, None)

    return meta, slots

# ==========================================================
def get_lineup(entry_rows):

    lineup = {}
    for f in range(1, 7):
        lane = entry_rows[f]
        if not lane:
            lineup[f] = None
            continue
        lineup[f] = lane.get("pid")

    return lineup

# ==========================================================
def get_results(_date:str, base_day:str, race_no:int, venue_id:int, player_id:int):

    is_base_day = (_date == base_day)

    if is_base_day:
        rows = dal.fetch_all(
            """
            SELECT r.race_no,  e.frame_no,    e.course,
                   e.slit_ADJ, e.finish_rank, e.fault_code
              FROM Races r
              JOIN Race_entries e
                ON e.race_id   = r.race_id
             WHERE r.date      = ?
               AND r.venue_id  = ?
               AND e.player_id = ?
               AND r.race_no   < ?
          ORDER BY r.race_no ASC
            """,
            (_date, venue_id, player_id, race_no)) or []
    else:
        rows = dal.fetch_all(
            """
            SELECT r.race_no,  e.frame_no,    e.course,
                   e.slit_ADJ, e.finish_rank, e.fault_code
              FROM Races r
              JOIN Race_entries e
                ON e.race_id   = r.race_id
             WHERE r.date      = ?
               AND r.venue_id  = ?
               AND e.player_id = ?
          ORDER BY r.race_no ASC
            """,
            (_date, venue_id, player_id)) or []

    rows = rows[:2]
    # --------------
    def conv_one(row_tuple):
        if not row_tuple:
            return ("", "", "", "", "")
        race_no_, fn, course, slit_adj, fin_rank, fault = row_tuple
        A = race_no_                          if race_no_  is not None else ""
        B = course                            if course    is not None else ""
        C = (f"{slit_adj:.2f}").strip('-')    if slit_adj  is not None else ""
        D = fin_rank                          if fin_rank  is not None else (fault or "")
        F = fn                                if fn                    else None
        return (A, B, C, D, F)
    # --------------
    left  = conv_one(rows[0]) if len(rows) >= 1 else ("", "", "", "", None)
    right = conv_one(rows[1]) if len(rows) >= 2 else ("", "", "", "", None)

    return left, right

# ==========================================================
def get_other_race(date_: date, venue_id: int, player_id: int, race_no: int):

    rows = dal.fetch_all(
        """
        SELECT race_no, frame_no
          FROM Race_programs
         WHERE date      = ?
           AND venue_id  = ?
           AND player_id = ?
      ORDER BY Race_programs.race_no ASC
        """,
        (date_, venue_id, player_id)) or []

    cand = [0, 0]
    if len(rows) < 2: return cand

    r1, r2 = rows[0], rows[1]
    cand   = r2 if race_no == r1[0] else (r1 if race_no == r2[0] else r2)

    return cand

# ================ Right: 日程ヘッダ表示/更新 ==============
def update_series_idx(self, date: str, v_id: int, r_no: int):

    self.date     = date
    self.venue_id = v_id
    self.race_no  = r_no
    self.lineup   = get_lineup(self.entry_rows)
    _, self.slots = build_day_lbl(self.date, self.venue_id)
    today_idx     = sum(1 for n in range(7) if self.slots[n]) -1

    for lane in range(1, 7):
        cells = self._widgets_main[lane]["R_hdr"]

        for i in range(7):
            cell = cells[i]
            info = self.slots[i]
            if not info: continue

            dn   = info.get("label_no", 0)
            text = "初  日" if dn == 1 else f"{dn}日目"
            text = "最終日" if info["final_day"] else text
            bg = {"bg":"#b3ffd4"} if i == today_idx else {"bg":HDR_COLOR}

            tk.Label( cell, text=text, anchor="center", font=(MUI,8), **bg, justify="center"
                     ).pack(expand=True, fill="both")

    _assign_series_idx(self)
    _assign_other_run(self)

# =================== Right: 節間成績 表示/更新 ==================
def _assign_series_idx(self):

    slots  = self.slots
    lineup = self.lineup
    pids   = []
    dates  = []

    for lane in range(1, 7):
        f_no = self.frame_order[lane - 1]
        pid  = lineup.get(f_no)
        if pid is not None: pids.append(pid)

    for info in slots:
        if info: dates.append(info["date"])

    pids  = list(dict.fromkeys(pids))
    dates = list(dict.fromkeys(dates))

    if not pids or not dates: return

    p_ph = ",".join("?" * len(pids))
    d_ph = ",".join("?" * len(dates))

    rows = dal.fetch_all(
        f"""
        SELECT r.date,
               e.player_id,
               r.race_no,
               e.frame_no,
               e.course,
               e.slit_ADJ,
               e.finish_rank,
               e.fault_code
          FROM Races r
          JOIN Race_entries e
            ON e.race_id   = r.race_id
         WHERE e.player_id IN ({p_ph})
           AND r.date      IN ({d_ph})
           AND r.venue_id   = ?
      ORDER BY e.player_id, r.date, r.race_no ASC
        """,
        (*pids, *dates, self.venue_id))

    result_map: dict[tuple, list] = defaultdict(list)
    for row in rows:
        key = (row["player_id"], row["date"])
        result_map[key].append(row)

    base_date = self.date
    # --------------
    def _filter_rows(pid, d, raw_rows):
        if d == base_date:
            return [r for r in raw_rows if r["race_no"] < self.race_no]
        return raw_rows
    # --------------
    def _conv_one(row):

        if row is None: return ("", "", "", "", None)
        race_no_ = row["race_no"]
        fn       = row["frame_no"]
        course   = row["course"]
        slit_adj = row["slit_ADJ"]
        fin_rank = row["finish_rank"]
        fault    = row["fault_code"]
        A = race_no_                          if race_no_  is not None else ""
        B = course                            if course    is not None else ""
        C = (f"{slit_adj:.2f}").strip('-')    if slit_adj  is not None else ""
        D = fin_rank                          if fin_rank  is not None else (fault or "")
        E = fn                                if fn                    else None

        return (A, B, C, D, E)
    # --------------
    for lane in range(1, 7):
        f_no  = self.frame_order[lane - 1]
        pid   = lineup.get(f_no)
        cells = self._widgets_main.get(lane).get("R_bdy")

        for i in range(7):
            info  = slots[i]
            col_L = i * 2
            col_R = col_L + 1
            if not info: continue

            _date = info.get("date")
            raw   = _filter_rows(pid, _date, result_map.get((pid, _date), []))
            raw   = raw[:2]
            L     = _conv_one(raw[0]) if len(raw) >= 1 else ("", "", "", "", None)
            R     = _conv_one(raw[1]) if len(raw) >= 2 else ("", "", "", "", None)

            _paint_abcd(self, cells[col_L], L[0], L[1], L[2], L[3], _date, f_no=L[4])
            _paint_abcd(self, cells[col_R], R[0], R[1], R[2], R[3], _date, f_no=R[4])

# --------------------------------------
def _paint_abcd(self, cells:list[tk.Frame], r_no, cour, s_adj, fin, date, f_no:int|None):

    if not r_no or "": return

    col   = FRAME_COLORS[f_no]
    s_adj = s_adj[1:] if s_adj else ""

    if fin in ("F", "L", "S", "K"):
        fg_CD = "red" 

    else: 
        fg_CD = "black"

    lbl = tk.Label(cells[0], text=f"{r_no}R", bg="white", anchor=CT, font=(MUI,8), cursor="hand2")
    lbl.bind("<Button-1>", lambda e, d=date: self._reload_for(d, self.venue_id, r_no, R=1))
    lbl.pack(expand=True, fill="both")

    cLbl( cells[1], text=cour,           fg=col["fg"], bg=col["bg"], Anc=CT, font=(MUI,8,BD)
         )._pack(expand=True, fill="both", px=1)
    cLbl( cells[2], text=wid_txt(s_adj), fg=fg_CD, bg="white", Anc=CT, font=(MUI,8)
         )._pack(expand=True, fill="both")
    cLbl( cells[3], text=fin, fg=fg_CD, bg="white", Anc=CT, font=(GUI,10,BD)
         )._pack(expand=True, fill="both")

# ================= Right: 2走インデックス 表示/更新 ==================
def _assign_other_run(self):

    lineup = self.lineup

    for lane in range(1, 7):
        target = self.frame_order[lane - 1]
        pid    = lineup.get(target)
        widgt  = self._widgets_main.get(lane)
        cells  = widgt["R_idx"]
        other  = get_other_race(self.date, self.venue_id, pid, self.race_no)
        if other[0] == 0: continue
        colors = FRAME_COLORS[other[1]]

        tk.Label( cells[0], text=f"{other[0]}R", anchor="center", font=(GUI,10,BD), bg=BG_COLOR,
                 ).pack(pady=(25, 0))

        frno_lbl = tk.Label( cells[1], height=2, text=other[1], anchor="center",
                             bg=colors["bg"], fg=colors["fg"], font=(GUI,10,BD) )
        frno_lbl.pack(fill="x", pady=(10, 10))

        def _go(date_iso=self.date, venue_id=self.venue_id, race_no=other[0]):
            self._reload_for(date_iso, venue_id, race_no)

        ttk.Button(cells[2], text=">", style="Thin.TButton", command=_go).pack(pady=(0, 5))
