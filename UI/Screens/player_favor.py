# -*- coding: utf-8 -*-
#C:\boatrace\UI\Screens\player_favor.py

import argparse, sys, sqlite3, json
import tkinter as tk
from tkinter  import ttk, messagebox
from datetime import datetime as dt, date, timedelta, timezone

from Custum_func import cFr, cLbl, cBtn, cCvs, cSrb, cEnt
import Dal as dal

VENUES  = [ "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",
             "津",  "三国", "びわこ", "住之江",  "尼崎",   "鳴門",  "丸亀", "児島",
            "宮島", "徳山",  "下関",   "若松",   "芦屋",   "福岡",  "唐津", "大村", ]

W_MOVES = ['逃げ', '差し', 'まくり', 'まくり差し', '抜き', '恵まれ']

CELLS1 = {    "rank":("順位",    50),
              "name":("選手名", 200),
               "cls":("級",      50),
            "course":("コース",  50),
              "rate":("指定着率",90),
               "cnt":("指定着数",80),
             "total":("出走数",  80),  }

CELLS2 = {    "rank":("順位",    40),
              "name":("選手名", 140),
               "cls":("級",      40),
            "self_c":("自艇ｺｰｽ", 45),
            "othr_c":("他艇ｺｰｽ", 45),
              "rate":("指定着率",60),
          "all_over":("全体平均",60),
              "diff":("差"      ,60),
               "cnt":("指定着数",55),
             "total":("出走数",  55),  }


GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK = "groove", "solid", "ridge", "raised", "sunken"
ALL, CT ,BD        = "nsew", "center", "bold"

MAIN_BG = "#F0F4FA"
HDR_BG  = "#2B4A7A"
BTN_BG  = "#4A6A9A"
WHITE   = "#FFFFFF"
YELL1   = "#FFD700"
YELL2   = "#F1EE62"
GRAY1   = "#ECECEC"
GRAY2   = "#CFCFCF"
BLACK1  = "#000000"
BLACK2  = "#222222"
BLUE    = "#0001da"
LIT_RED = "#ff5b5b"

HDR_B   = dict(bg=HDR_BG)
HDR_BF  = dict(bg=HDR_BG, fg=WHITE)
BTN_BF  = dict(bg=BTN_BG, fg=WHITE)
BTN_OFF = dict(bg=BTN_BG, fg=WHITE,  Bd=(1,RA))
GRY_OFF = dict(bg=GRAY1,  fg=BLACK1, Bd=(1,RA))
YEL1_ON = dict(bg=YELL1,  fg=BLACK2, Bd=(1,GR))
YEL2_ON = dict(bg=YELL2,  fg=BLACK2, Bd=(1,SK))

BG       = dict(bg=MAIN_BG)
FONT     = dict(font=(MUI,10), bg=MAIN_BG)
HDR      = dict(bg=HDR_BG, fg=WHITE, font=(MUI,10), Bd=(1,RD))
BTN      = dict(bg=HDR_BG, fg=WHITE, font=(MUI,9),  Bd=(2,RA))
CELL_BF  = dict(bg=BLACK1, fg=WHITE, font=(MUI,11), Bd=(1,GR))

# ===========  共通ヘルパー  ===========
def _today() -> str:
    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date()
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
# ------------------
def days_ago(d:str, range:int)-> str:
    d = to_date(d)
    return to_str(d -timedelta(days=range))

#=====================================================================
class PlayerFavorScreen(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app  = app
        self.app.geometry("1220x1400+75+0")
        #self.app.protocol("WM_DELETE_WINDOW", self._on_close)

        self._cells  = {}
        self.v_vars  = {}
        self.wm_vars = {}
        self.r_vars  = {}
        self.sc_var  = tk.StringVar(value=1)
        self.oc_var  = tk.StringVar(value=1)
        self.num_var = tk.IntVar(value=10)
        self.run_var = tk.IntVar(value=30)
        self.wm_cbs  = []
        self.oc_cbs  = []
        self.other_course = False
        self.best    = tk.BooleanVar(value=True)

        style = ttk.Style()
        style.configure("fpw.TCheckbutton", font=(MUI,10), background=MAIN_BG)
        style.configure("fpw.TRadiobutton", font=(MUI,10), background=MAIN_BG)

        fr_main = cFr(self, W=1220, H=1400, bg=MAIN_BG, px=10, py=15) ;fr_main.Pgate()
        fr_main._grid(R=0, C=0, Stk=ALL)

        cntrl  = cFr(fr_main, W=550, H=600, **BG)  ;cntrl._grid(R=0, C=0, px=5) ;cntrl.Pgate()
        result = cFr(fr_main, W=630, H=600, **BG) ;result._grid(R=0, C=1, px=5) ;result.Pgate()

        fr_date = cFr(cntrl, W=550, H=80, **BG, py=5) ;fr_date._grid(R=0, C=0) ;fr_date.Pgate()

        cLbl(fr_date, text="DATE ( FROM )", **HDR)._grid(R=0, C=1, Cspan=3, Stk="we", px=(0, 0)) 
        cLbl(fr_date, text="DATE ( TO )",   **HDR)._grid(R=0, C=5, Cspan=3, Stk="we", px=(10,0))
        cLbl(fr_date, text=" ～ ",         **FONT)._grid(R=1, C=4,          Stk="we", px=5)

        cBtn(fr_date, text="本日", **BTN, Com=self._today_only,   W=6)._grid(R=0, C=0, Stk=ALL, px=(0,10), py=2)
        cBtn(fr_date, text="単日", **BTN, Com=self._from_to_from, W=6)._grid(R=1, C=0, Stk=ALL, px=(0,10), py=2)

        years  = [str(y) for y in reversed(range(2000, date.today().year +1))]
        months = [f"{m:02d}" for m in range(1,13)]
        days   = [f"{d:02d}" for d in range(1,32)]

        self.df_y = ttk.Combobox(fr_date, values=years,  width=6, font=(MUI,10))
        self.df_m = ttk.Combobox(fr_date, values=months, width=4, font=(MUI,10))
        self.df_d = ttk.Combobox(fr_date, values=days,   width=4, font=(MUI,10))
        self.dt_y = ttk.Combobox(fr_date, values=years,  width=6, font=(MUI,10))
        self.dt_m = ttk.Combobox(fr_date, values=months, width=4, font=(MUI,10))
        self.dt_d = ttk.Combobox(fr_date, values=days,   width=4, font=(MUI,10))
        self.df_y.grid(row=1, column=1, sticky="w", padx=2, pady=4)
        self.df_m.grid(row=1, column=2, sticky="w", padx=2, pady=4)
        self.df_d.grid(row=1, column=3, sticky="w", padx=2, pady=4)
        self.dt_y.grid(row=1, column=5, sticky="w", padx=2, pady=4)
        self.dt_m.grid(row=1, column=6, sticky="w", padx=2, pady=4)
        self.dt_d.grid(row=1, column=7, sticky="w", padx=2, pady=4)

        fr_venue = cFr(cntrl, W=550, H=120, **BG, py= 5) ;fr_venue._grid(R=1, C=0) ;fr_venue.Pgate()
        fr_btns  = cFr(cntrl, W=550, H= 50, **BG, py=10)  ;fr_btns._grid(R=2, C=0) ;fr_btns.Pgate()
        fr_self  = cFr(cntrl, W=550, H= 45, **BG, py=10)  ;fr_self._grid(R=3, C=0) ;fr_self.Pgate()
        fr_othr  = cFr(cntrl, W=550, H= 45, **BG, py=10)  ;fr_othr._grid(R=4, C=0) ;fr_othr.Pgate()
        fr_rank  = cFr(cntrl, W=550, H= 45, **BG, py=10)  ;fr_rank._grid(R=5, C=0) ;fr_rank.Pgate()
        fr_wmvs  = cFr(cntrl, W=550, H= 45, **BG, py=10)  ;fr_wmvs._grid(R=6, C=0) ;fr_wmvs.Pgate()
        fr_param = cFr(cntrl, W=550, H= 45, **BG, py=10) ;fr_param._grid(R=7, C=0) ;fr_param.Pgate()

        fr_sbtn  = cFr(cntrl, W=550, H= 50, **BG, py=10)  ;fr_sbtn._grid(R=8, C=0) ;fr_sbtn.Pgate()

        for c in range(6):
            for r in range(4):
                key = c + (6 * r)
                txt = VENUES[key]
                var = tk.BooleanVar(value=True)
                ttk.Checkbutton(fr_venue, text=f"{txt:6}", variable=var, style="fpw.TCheckbutton"
                                ).grid(row=r, column=c, sticky="w", padx=6, pady=2)
                self.v_vars[key] = var

        cBtn(fr_btns, text="全選択", **BTN, Com=self._select_all, W= 7)._grid(R=0, C=0, px=5)
        cBtn(fr_btns, text="全解除", **BTN, Com=self._reset_all,  W= 7)._grid(R=0, C=1, px=5)

        cLbl(fr_self, text="自", **HDR, px=4, py=4)._grid(R=0, C=0)
        self.bt_othr = cBtn(fr_othr, text="他", **HDR, Com=self._toggle_other)
        self.bt_othr._grid(R=0, C=0)

        for c in range(1,7):
            ttk.Radiobutton( fr_self, text=f"{c} ｺｰｽ  ", variable=self.sc_var, value=c,
                                  style="fpw.TRadiobutton"
                            ).grid(row=0, column=c, sticky="w", padx=6, pady=2)

        for c in range(1,7):
            cb = ttk.Radiobutton( fr_othr, text=f"{c} ｺｰｽ  ", variable=self.oc_var, value=c,
                              state=tk.DISABLED, style="fpw.TRadiobutton")
            cb.grid(row=0, column=c, sticky="w", padx=6, pady=2)
            self.oc_cbs.append(cb)

        for r in range(1,7):
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton( fr_rank, text=f"{r} 着    ", variable=var, style="fpw.TCheckbutton",
                             command=lambda v=var, r=r:self._on_rank_changed(v,r)
                            ).grid(row=0, column=r-1, sticky="w", padx=6, pady=2)
            self.r_vars[r] = var

        for c in range(6):
            txt = W_MOVES[c]
            var = tk.BooleanVar(value=False)
            cb  = ttk.Checkbutton( fr_wmvs, text=f"{txt:6}", variable=var, style="fpw.TCheckbutton",
                                    command=self._update_wm_state,
                                  ) ;cb.grid(row=0, column=c, sticky="w", padx=6, pady=2)
            self.wm_vars[W_MOVES[c]] = var
            self.wm_cbs.append(cb)

        ttk.Radiobutton( fr_param, text=f"Best", variable=self.best, value=True,
                                  style="fpw.TRadiobutton"
                            ).grid(row=0, column=0, sticky="w", padx=6, pady=2)
        ttk.Radiobutton( fr_param, text=f"Worst", variable=self.best, value=False,
                                  style="fpw.TRadiobutton"
                            ).grid(row=0, column=1, sticky="w", padx=6, pady=2)

        cLbl(fr_sbtn, text="上位 ", **FONT, px=2)._grid(R=0, C=0)
        tk.Spinbox( fr_sbtn, from_=1, to=50, width=4, font=(MUI,10), textvariable=self.num_var
                   ).grid(row=0, column=1)
        cLbl(fr_sbtn, text="出走数", **FONT, px=5)._grid(R=0, C=2, px=(20,0))
        tk.Spinbox( fr_sbtn, from_=1, to=50, width=4, font=(MUI,10), textvariable=self.run_var
                   ).grid(row=0, column=3)
        cLbl(fr_sbtn, text="以上", **FONT)._grid(R=0, C=4)

        cBtn(fr_sbtn, text="検索実行", **HDR, Com=self._on_search, W=12)._grid(R=0, C=5, px=(150,0))

        self._init_result_table(result)

    # --------------------------------------------
    def _init_result_table(self, parent):

        parent.Rconf(0, Min=28)  ;parent.Cconf(0, Min=600)
        parent.Rconf(1, Min=572)

        self.fr_hdr  = cFr(parent,  W=600, H= 28, **HDR_B, Bd=(1,RD))
        self.canvas  = cCvs(parent, W=600, H=572, bg=BLACK1)
        self.fr_body = cFr(self.canvas, Bd=(1,SD))
        scr_bar      = cSrb(parent, orient="vertical", Com=self.canvas.yview)
        self.canvas.config(yscrollcommand=scr_bar.set)

        self.fr_hdr._grid( R=0, C=0)           ;self.fr_hdr.Pgate()
        self.canvas._grid( R=1, C=0, Stk=ALL)
        scr_bar._grid(     R=1, C=1, Stk="ns")

        self.window = self.canvas.create_window((0, 0), window=self.fr_body, anchor="nw")
        #-----------
        def _mw(e):
            self.canvas.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_conf(event=None):
            self.canvas._config(Scrgn=self.canvas.bbox("all"))
            self.canvas.itemconfig(self.window, width=self.canvas.winfo_width())
        #-----------
        self.canvas.bind("<Enter>", lambda e:self.canvas.bind_all("<MouseWheel>", _mw))
        self.canvas.bind("<Leave>", lambda e:self.canvas.unbind_all("<MouseWheel>"))
        self.fr_body.bind("<Configure>", _on_conf)
        self.canvas.bind("<Configure>", _on_conf)

    # --------------------------------------------
    def _on_rank_changed(self, var, key):

        active = sum(1 for var in self.r_vars.values() if var.get())
        if active == 0:
           var.set(True)

        self._update_wm_state()

    # --------------------------------------------
    def _update_wm_state(self):

        selected_r = [k for k, v in self.r_vars.items() if v.get()]
        is_only_r1 = (selected_r == [1])
        state      = tk.NORMAL if (not self.other_course and is_only_r1) else tk.DISABLED

        for cb in self.wm_cbs:
            cb.configure(state=state)

    # --------------------------------------------
    def _toggle_other(self):

        self.other_course = not self.other_course
        if self.other_course:
            self.bt_othr._config(**YEL2_ON)
            for cb in self.oc_cbs:
                cb.config(state=tk.NORMAL)
        else:
            self.bt_othr._config(**HDR)
            for cb in self.oc_cbs:
                cb.config(state=tk.DISABLED)

        self._update_wm_state()

    # --------------------------------------------
    def _select_all(self):
        for var in self.v_vars.values():
            var.set(True)
    # --------------------------------------------
    def _reset_all(self):
        for var in self.v_vars.values():
            var.set(False)
    # --------------------------------------------
    def _from_to_from(self):
        self.dt_y.set(self.df_y.get().strip())
        self.dt_m.set(self.df_m.get().strip())
        self.dt_d.set(self.df_d.get().strip())
    # --------------------------------------------
    def _today_only(self):
        self.df_y.set(_today().strftime("%Y")) ;self.dt_y.set(_today().strftime("%Y"))
        self.df_m.set(_today().strftime("%m")) ;self.dt_m.set(_today().strftime("%m"))
        self.df_d.set(_today().strftime("%d")) ;self.dt_d.set(_today().strftime("%d"))
    # --------------------------------------------
    def _on_search(self):

        rows = self._search_players()
        if not rows: return

        for widget in self._cells.values():
            widget.destroy()
        self._cells.clear()

        cells = CELLS1 if not self.other_course else CELLS2

        self.fr_hdr.Rconf(0, Min=28)
        for c, v in enumerate(cells.values()):
            self.fr_hdr.Cconf(c, Min=v[1], W=1)
            cLbl(self.fr_hdr, text=v[0], **HDR)._grid(R=0, C=c, Stk=ALL)

        for r, data in enumerate(rows):
            self.fr_body.Rconf(r, Min=30, W=1)
            for c, (key, val) in enumerate(data.items()):
                self.fr_body.Cconf(c, Min=cells[key][1], W=1)
                lbl = cLbl(self.fr_body, text=val, **CELL_BF)
                lbl._grid(R=r, C=c, Stk=ALL)
                self._cells[(r, c)] = lbl

    # --------------------------------------------
    def _search_players(self):

        f_y, f_m, f_d = self.df_y.get().strip(), self.df_m.get().strip(), self.df_d.get().strip()
        t_y, t_m, t_d = self.dt_y.get().strip(), self.dt_m.get().strip(), self.dt_d.get().strip()
        d_from = f"{f_y}-{f_m}-{f_d}"
        d_to   = f"{t_y}-{t_m}-{t_d}"

        venues   = [k for k, v in self.v_vars.items()  if v.get()]
        f_ranks  = [k for k, v in self.r_vars.items()  if v.get()]
        w_moves  = [k for k, v in self.wm_vars.items() if v.get()]
        s_course = self.sc_var.get()
        o_course = self.oc_var.get()
        num      = int(self.num_var.get()) or 10
        run      = int(self.run_var.get()) or 30
        sort_desc = self.best.get()

        ph1 = ",".join("?" * len(venues))
        ph2 = ",".join("?" * len(f_ranks))

        if not venues:
            messagebox.showwarning("error", "select venues")
            return []
        if not f_ranks:
            messagebox.showwarning("error", "select finish ranks")
            return []

        if self.other_course:

            sql = f"""
                SELECT p.player_id AS pid,
                       p.name,
                       p.class_now AS cls,
                       COUNT(DISTINCT e1.race_id) AS total,
                       SUM(CASE WHEN e2.finish_rank IN ({ph2}) THEN 1 ELSE 0 END) AS cnt
                  FROM Race_entries e1
                  JOIN Race_entries e2 ON e1.race_id = e2.race_id AND e1.entry_id <> e2.entry_id
                  JOIN Players p ON p.player_id = e1.player_id
                 WHERE e1.date BETWEEN ? AND ?
                   AND e1.course = ?
                   AND e2.course = ?
                   AND e1.venue_id IN ({ph1})
                 GROUP BY p.player_id, p.name, p.class_now
                HAVING COUNT(DISTINCT e1.race_id) >= ?
            """
            params = (*f_ranks, d_from, d_to, s_course, o_course, *venues, run)
            rows = dal.fetch_all(sql, params)
            if not rows:
                return []

            json_data = self._from_json()
            avg_rates = 0.0
            for r in f_ranks:
                avg_rates += json_data[int(o_course)]["rate"][r] * 100.0

            processed_rows = []
            for row in rows:
                total = row['total']
                cnt   = row['cnt']
                rate  = 100.0 * cnt / total
                diff  = rate - avg_rates
                processed_rows.append({
                    'rank': 0,
                    'name': row['name'],
                    'cls': row['cls'],
                    'self_c': s_course,
                    'othr_c': o_course,
                    'rate': round(rate, 1),
                    'all_over': round(avg_rates, 1),
                    'diff': round(diff, 1),
                    'cnt': cnt,
                    'total': total,
                })

            processed_rows.sort(key=lambda x: x['rate'], reverse=sort_desc)
            top_rows = processed_rows[:num]

            for idx, r in enumerate(top_rows, start=1):
                r['rank'] = idx

            return top_rows

        else:

            ph3 = ",".join("?" * len(w_moves))
            ph = f" AND e.win_move IN ({ph3})" if w_moves else ""
            sort = "DESC" if self.best.get() else "ASC"

            sql = f"""
                WITH Stats AS (SELECT e.course,
                                      e.player_id                             AS pid,
                                      COUNT(*)                                AS total,
                                      SUM(CASE WHEN(e.finish_rank IN ({ph2})
                                                    {ph}                   )
                                               THEN 1
                                               ELSE 0
                                                END                          ) AS cnt

                                 FROM Race_entries e
                                WHERE     e.date BETWEEN ? AND ?
                                      AND e.course = ?
                                      AND e.venue_id IN ({ph1})
                                GROUP BY e.player_id
                               HAVING COUNT(*) >= {run} )

                SELECT ROW_NUMBER() OVER (ORDER BY (100.0*cnt / total) DESC) AS rank,
                       p.name,
                       p.class_now AS cls,
                       course,
                       ROUND(100.0 * cnt / total, 1) AS rate,
                       cnt,
                       total
                  FROM Stats s
                  JOIN Players p ON p.player_id = s.pid
                 ORDER BY rate {sort}
                 LIMIT {num};
                """
            if w_moves: params = (*f_ranks, *w_moves, d_from, d_to, s_course, *venues)
            else:       params = (*f_ranks, d_from, d_to, s_course, *venues)

            rows = dal.fetch_all(sql, params)

            return [dict(row) for row in rows if rows]

    #-----------------------------------
    def _from_json(self):
        #---------------
        def convert_keys_to_int(d:dict):
            return {int(k) if k.isdigit() else k:v for k, v in d.items()}
        #---------------

        row = dal.fetch_one(f"""
                      SELECT all_venue
                        FROM Daily_Overall
                       WHERE date = ?
                      """,
                      (today_iso(),) )

        if row:
            json_txt = row[0]
            try:
                return json.loads(json_txt, object_hook=convert_keys_to_int)
            except json.JSONDecodeError as e:
                print(f"JSON復元エラー: {e}")
                return {}
        else:
            return {}

    #-------------------------------------------------------
    def _on_close(self):

        self.app.show_screen("Main")
    #-------------------------------------------------------