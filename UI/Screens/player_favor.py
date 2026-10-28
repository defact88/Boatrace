# -*- coding: utf-8 -*-
#C:\boatrace\UI\Screens\player_favor.py

import argparse, sys, sqlite3, json
import tkinter as tk
from tkinter  import ttk, messagebox
from datetime import datetime as dt, date, timedelta, timezone
from pathlib  import Path

from Custum_func import cFr, cLbl, cBtn, cCvs, cSrb, cEnt, cSpbx
import Dal as dal

FAVORITE_JSON = Path(r"C:\boatrace\tmp\json\favorite_players.json")

SEL_BG = "#2F6DB3"

VENUES  = [ " 桐生 ", " 戸田 ", "江戸川", "平和島", "多摩川", "浜名湖", " 蒲郡 ", " 常滑 ",
            "  津  ", " 三国 ", "びわこ", "住之江", " 尼崎 ", " 鳴門 ", " 丸亀 ", " 児島 ",
            " 宮島 ", " 徳山 ", " 下関 ", " 若松 ", " 芦屋 ", " 福岡 ", " 唐津 ", " 大村 ", ]

GRADES  = [ ["SG",(5,)], ["G1",(4,3)] ,["G2",(2,)], ["一般",(0,1)] ]
G_LIST  = ["一般", "G3", "G2", "G1", "PG1", "SG"]


W_MOVES = ['逃げ', '差し', 'まくり', 'まくり差し', '抜き', '恵まれ']

CELLS1 = {    "rank":("順位",    45),
              "name":("選手名", 160),
               "cls":("級",      50),
            "course":("コース",  50),
              "rate":("指定着率",70),
          "all_over":("全体平均",70),
              "diff":("差"      ,65),
               "cnt":("指定着数",70),
             "total":("出走数",  70),  }

CELLS2 = {    "rank":("順位",    45),
              "name":("選手名", 145),
               "cls":("級",      45),
            "self_c":("自ｺｰｽ",   50),
            "othr_c":("対象ｺｰｽ", 50),
              "rate":("指定着率",65),
          "all_over":("全体平均",65),
              "diff":("差"      ,65),
               "cnt":("指定着数",60),
             "total":("出走数",  60),  }

REG_CELLS = {     "player_id":("登番",     60),
                       "name":("選手名",  140),
                        "age":("年齢",     45),
                  "class_now":("級",       45),
                    "regions":("支部",     55),
              "regist_period":("期",       60),
                  "flying_st":("F",        30),
                    "late_st":("L",        30),
                  "next_race":("出走予定",443),
                 "conditions":("設定条件",250), }

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

BG      = dict(bg=MAIN_BG)
BGFNT   = dict(bg=MAIN_BG, font=(MUI,10))
HDR     = dict(bg=HDR_BG, fg=WHITE, font=(MUI,10), Bd=(1,RD))
BTN     = dict(bg=BTN_BG, fg=WHITE, font=(MUI,10),  Bd=(2,RA))
CELL_B  = dict(bg=BLACK1          , font=(MUI,11), Bd=(1,GR))

# ===========  共通ヘルパー  ===========
def _today() -> date:
    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date()
# ------------------
def _past(d) -> date:
    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date() -timedelta(days=d)
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
def to_range(df, dt) -> date:
    return f"{to_date(df).strftime('%m/%d')} ～ {to_date(df).strftime('%m/%d')}"
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

        self._cells     = {}
        self.ven_vars   = {}
        self.grd_vars   = {}
        self.rnk_vars   = {}
        self.wm_vars    = {}
        self.wm_cbs     = []
        self.othr_c_cbs = []
        self.self_c_var = tk.IntVar(value=1)
        self.othr_c_var = tk.IntVar(value=None)
        self.num_var    = tk.IntVar(value=10)
        self.run_var    = tk.IntVar(value=30)
        self.best       = tk.BooleanVar(value=True)
        self.other      = False

        self._current_rows      = []
        self.selected_row       = None
        self.selected_player_id = None

        style = ttk.Style()
        style.configure("fpw.TCheckbutton", font=(MUI,10), background=MAIN_BG)
        style.configure("fpw.TRadiobutton", font=(MUI,10,BD), background=MAIN_BG)

        fr_main = cFr(self, W=1220, H=1400, bg=MAIN_BG, px=10, py=15) ;fr_main.Pgate()
        fr_main._grid(R=0, C=0, Stk=ALL)

        cntrl  = cFr(fr_main, W= 490, H=600, **BG)  ;cntrl._grid(R=0, C=0, px=5) ;cntrl.Pgate()
        result = cFr(fr_main, W= 680, H=600, **BG) ;result._grid(R=0, C=1, px=5, py=(0,20)) ;result.Pgate()
        regist = cFr(fr_main, W=1190, H=750, **BG) ;regist._grid(R=1, C=0, Cspan=2) ;regist.Pgate()

        fr_date = cFr(cntrl, W=490, H=60, **BG, py=5) ;fr_date._grid(R=0, C=0) ;fr_date.Pgate()

        cLbl(fr_date, text="DATE ( FROM )", **HDR)._grid(R=0, C=1, Cspan=3, Stk=ALL) 
        cLbl(fr_date, text=" DATE ( TO ) ", **HDR)._grid(R=0, C=5, Cspan=3, Stk=ALL)
        cLbl(fr_date, text="  ～  ",      **BGFNT)._grid(R=1, C=4,          Stk=ALL, px=5)

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

        fr_dbtn   = cFr(cntrl, W=490, H=45,  **BG, py= 5)  ;fr_dbtn._grid(R=1, C=0) ;fr_dbtn.Pgate()
        fr_venue  = cFr(cntrl, W=490, H=135, **BG, py= 5) ;fr_venue._grid(R=2, C=0) ;fr_venue.Pgate()
        fr_grade  = cFr(cntrl, W=490, H= 50, **BG, py=10) ;fr_grade._grid(R=3, C=0) ;fr_grade.Pgate()
        fr_self   = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_self._grid(R=4, C=0) ;fr_self.Pgate()
        fr_othr   = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_othr._grid(R=5, C=0) ;fr_othr.Pgate()
        fr_rank   = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_rank._grid(R=6, C=0) ;fr_rank.Pgate()
        fr_wmvs   = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_wmvs._grid(R=7, C=0) ;fr_wmvs.Pgate()
        fr_param  = cFr(cntrl, W=490, H= 45, **BG, py=10) ;fr_param._grid(R=8, C=0) ;fr_param.Pgate()
        fr_sbtn   = cFr(cntrl, W=490, H= 50, **BG, py=10)  ;fr_sbtn._grid(R=9, C=0) ;fr_sbtn.Pgate()

        cBtn( fr_dbtn, W=7, text="  本日  ", **BTN, Com=self._today_only
             )._grid(R=0, C=0, Stk=ALL, px=5, py=(0,20))
        cBtn( fr_dbtn, W=8, text="直近 1年", **BTN, Com=lambda:self._past_days(365)
             )._grid(R=0, C=1, Stk=ALL, px=5, py=(0,20))
        cBtn( fr_dbtn, W=8, text="直近 半年", **BTN, Com=lambda:self._past_days(182)
             )._grid(R=0, C=3, Stk=ALL, px=5, py=(0,20))

        cBtn( fr_venue, W=2, text="全\n選\n択", **BTN, Com=self._select_all, px=3
             )._grid(R=0, C=0, Rspan=2, px=(0,17))
        cBtn( fr_venue, W=2, text="全\n解\n除", **BTN, Com=self._reset_all, px=3
             )._grid(R=2, C=0, Rspan=2, px=(0,17))

        for c in range(1,7):
            for r in range(4):
                key = c + (6 * r)-1
                txt = VENUES[key]
                var = tk.BooleanVar(value=False) if key == 2 else tk.BooleanVar(value=True)
                ttk.Checkbutton(fr_venue, text=f"{txt:6}", variable=var, style="fpw.TCheckbutton"
                                ).grid(row=r, column=c, sticky="w", padx=(4,0), pady=4)
                self.ven_vars[key] = var

        for c in range(4):
            var = tk.BooleanVar(value=True)
            px  = (50,10) if c == 0 else 18
            ttk.Checkbutton( fr_grade, text=f"{GRADES[c][0]}", variable=var, style="fpw.TRadiobutton"
                            ).grid(row=0, column=c, sticky="w", padx=px, pady=2)
            self.grd_vars[(GRADES[c][1])] = var

        cLbl(fr_self, text="自", **HDR, px=4, py=4)._grid(R=0, C=0)
        self.bt_othr = cBtn(fr_othr, text="他", **BTN, Com=self._toggle_other)
        self.bt_othr._grid(R=0, C=0)

        for c in range(1,7):
            ttk.Radiobutton( fr_self, text=f"{c} ｺｰｽ  ", variable=self.self_c_var, value=c,
                             style="fpw.TRadiobutton"
                            ).grid(row=0, column=c, sticky="w", padx=6, pady=2)

        for c in range(1,7):
            cb = ttk.Radiobutton( fr_othr, text=f"{c} ｺｰｽ  ", variable=self.othr_c_var, value=c,
                              state=tk.DISABLED, style="fpw.TRadiobutton")
            cb.grid(row=0, column=c, sticky="w", padx=6, pady=2)
            self.othr_c_cbs.append(cb)

        for r in range(1,7):
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton( fr_rank, text=f"{r} 着    ", variable=var, style="fpw.TCheckbutton",
                             command=lambda v=var, r=r:self._on_rank_changed(v,r)
                            ).grid(row=0, column=r-1, sticky="w", padx=6, pady=2)
            self.rnk_vars[r] = var

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

        cLbl(fr_param, text="上位 ", **BGFNT, px=2)._grid(R=0, C=2, px=(20,0))
        cSpbx(fr_param, W=4, Frm=1, To=50, Inc=10, font=(MUI,11), Txtv=self.num_var)._grid(R=0, C=3)
        cLbl(fr_param, text="出走数", **BGFNT, px=5)._grid(R=0, C=4, px=(20,0))
        cSpbx(fr_param, W=4, Frm=1, To=50, Inc=10, font=(MUI,11), Txtv=self.run_var)._grid(R=0, C=5)
        cLbl(fr_param, text="以上", **BGFNT)._grid(R=0, C=6)

        cBtn(fr_sbtn, W=11, text="検索 実行", **BTN, Com=self._on_search)._grid(R=0, C=1, px=(130,0))
        cBtn(fr_sbtn, W=11, text="選手 登録", **BTN, Com=self._register_favorite)._grid(R=0, C=0, px=(60,0))

        self._init_result_table(result)
        self._init_regist_table(regist)

    # --------------------------------------------
    def _init_result_table(self, parent):

        parent.Rconf(0, Min=28)  ;parent.Cconf(0, Min=650)
        parent.Rconf(1, Min=572)

        self.fr_hdr  = cFr(parent,  W=650, H= 28, **HDR_B, Bd=(1,RD))
        self.canvas  = cCvs(parent, W=650, H=572, bg=BLACK1)
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
    def _init_regist_table(self, parent):

        table = cFr(parent, W=1190, H=490) ;table._grid(R=0, C=0) ;table.Pgate()
        cntrl = cFr(parent, W=1190, H=250) ;cntrl._grid(R=1, C=0) ;cntrl.Pgate()

        table.Rconf(0, Min=28)  ;table.Cconf(0, Min=1160)
        table.Rconf(1, Min=462)
        table.Rconf(2, Min=250)

        self._regist_cells = {}

        self.fr_hdr2  = cFr(table,  W=1160, H= 28, **HDR_B, Bd=(1,RD))
        self.canvas2  = cCvs(table, W=1155, H=462, bg=BLACK1)
        self.fr_body2 = cFr(self.canvas2, Bd=(1,SD))
        scr_bar2      = cSrb(table, orient="vertical", Com=self.canvas2.yview)
        self.canvas2.config(yscrollcommand=scr_bar2.set)

        self.fr_hdr2._grid( R=0, C=0)           ;self.fr_hdr2.Pgate()
        self.canvas2._grid( R=1, C=0, Stk=ALL)
        scr_bar2._grid(     R=1, C=1, Stk="ns")

        self.window2 = self.canvas2.create_window((0, 0), window=self.fr_body2, anchor="nw")
        #-----------
        def _mw2(e):
            self.canvas2.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_conf2(event=None):
            self.canvas2._config(Scrgn=self.canvas2.bbox("all"))
            self.canvas2.itemconfig(self.window2, width=self.canvas2.winfo_width())
        #-----------
        self.canvas2.bind("<Enter>", lambda e:self.canvas2.bind_all("<MouseWheel>", _mw2))
        self.canvas2.bind("<Leave>", lambda e:self.canvas2.unbind_all("<MouseWheel>"))
        self.fr_body2.bind("<Configure>", _on_conf2)
        self.canvas2.bind("<Configure>", _on_conf2)

        self._load_regist_list()

    # --------------------------------------------
    def _on_rank_changed(self, var, key):

        active = sum(1 for var in self.rnk_vars.values() if var.get())
        if active == 0:
           var.set(True)

        self._update_wm_state()

    # --------------------------------------------
    def _update_wm_state(self):

        selected_r = [k for k, v in self.rnk_vars.items() if v.get()]
        is_only_r1 = (selected_r == [1])
        state      = tk.NORMAL if (not self.other and is_only_r1) else tk.DISABLED

        for cb in self.wm_cbs:
            cb.configure(state=state)

    # --------------------------------------------
    def _toggle_other(self):

        self.other = not self.other
        if self.other:
            self.bt_othr._config(**YEL2_ON)
            for cb in self.othr_c_cbs:
                cb.config(state=tk.NORMAL)
        else:
            self.bt_othr._config(**BTN)
            for cb in self.othr_c_cbs:
                cb.config(state=tk.DISABLED)

        self._update_wm_state()

    # --------------------------------------------
    def _select_all(self):
        for var in self.ven_vars.values():
            var.set(True)
    # --------------------------------------------
    def _reset_all(self):
        for var in self.ven_vars.values():
            var.set(False)
    # --------------------------------------------
    def _past_days(self, d):
        self.df_y.set(_past(d).strftime("%Y")) ;self.dt_y.set(_today().strftime("%Y"))
        self.df_m.set(_past(d).strftime("%m")) ;self.dt_m.set(_today().strftime("%m"))
        self.df_d.set(_past(d).strftime("%d")) ;self.dt_d.set(_today().strftime("%d"))
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

        self._current_rows      = rows
        self.selected_row       = None
        self.selected_player_id = None

        cells = CELLS2 if self.other else CELLS1
        self.fr_hdr.Rconf(0, Min=28)

        for c, (k, v) in enumerate(cells.items()):
            self.fr_hdr.Cconf( c, Min=v[1], W=1)
            self.fr_body.Cconf(c, Min=v[1], W=1)
            hdr = cLbl(self.fr_hdr, text=v[0], **HDR) ;hdr._grid(R=0, C=c, Stk=ALL)
            self._cells[c] = hdr
            for r, data in enumerate(rows):
                self.fr_body.Rconf(r, Min=30, W=1)
                fg  = "yellow" if k == "rate" else "white"
                lbl = cLbl(self.fr_body, text=data[k], **CELL_B, fg=fg) ;lbl._grid(R=r, C=c, Stk=ALL)
                lbl.bind("<Button-1>", lambda e, idx=r:self._select_row(idx))
                self._cells[(r, c)] = lbl

    # --------------------------------------------
    def _select_row(self, idx):

        cells   = CELLS2 if self.other else CELLS1
        n_cols  = len(cells)

        if self.selected_row is not None:
            for c in range(n_cols):
                w = self._cells.get((self.selected_row, c))
                if w: w._config(bg=CELL_B["bg"])

        for c in range(n_cols):
            w = self._cells.get((idx, c))
            if w: w._config(bg=SEL_BG)

        self.selected_row       = idx
        self.selected_player_id = self._current_rows[idx]["pid"]

    # --------------------------------------------
    def _register_favorite(self):

        if self.selected_player_id is None:
            messagebox.showwarning("注目選手登録", "選手を選択してください。")
            return

        ids = self._load_favorite_ids()
        if self.selected_player_id in ids:
            messagebox.showinfo("注目選手登録", "既に登録済みです。")
            return

        ids.append(self.selected_player_id)
        self._save_favorite_ids(ids)
        self._load_regist_list()

    # --------------------------------------------
    def _load_favorite_ids(self) -> list[int]:

        if not FAVORITE_JSON.exists(): return []

        try:
            return json.loads(FAVORITE_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    # --------------------------------------------
    def _save_favorite_ids(self, ids:list[int]):

        FAVORITE_JSON.parent.mkdir(parents=True, exist_ok=True)
        FAVORITE_JSON.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")

    # --------------------------------------------
    def _format_next_race(self, schedule_today, schedule_1) -> str:

        if schedule_today:
            d, title, grade, venue, rno = schedule_today.split(",")
            vname = VENUES[int(venue)-1].strip() if venue else ""
            return f"本日 {vname}  {G_LIST[int(grade)]}  {title}  {rno}R"

        if schedule_1:
            d_from, d_to, title, grade, venue = schedule_1.split(",")
            vname = VENUES[int(venue)-1].strip() if venue else ""
            return f"{to_range(d_from, d_to)}  {vname}  {G_LIST[int(grade)]}  {title}"

        return "予定なし"

    # --------------------------------------------
    def _load_regist_list(self):

        for widget in self._regist_cells.values():
            widget.destroy()
        self._regist_cells.clear()

        self.fr_hdr2.Rconf(0, Min=28)

        for c, (k, v) in enumerate(REG_CELLS.items()):
            self.fr_hdr2.Cconf( c, Min=v[1], W=1)
            self.fr_body2.Cconf(c, Min=v[1], W=1)
            hdr = cLbl(self.fr_hdr2, text=v[0], **HDR) ;hdr._grid(R=0, C=c, Stk=ALL)
            self._regist_cells[c] = hdr

        ids = self._load_favorite_ids()
        if not ids: return

        ph   = ",".join("?" * len(ids))
        rows = dal.fetch_all(
                  f"""
                    SELECT player_id, name, age, class_now, regions,
                           regist_period, flying_st, late_st,
                           schedule_today, schedule_1
                      FROM Players
                     WHERE player_id IN ({ph})
                  """,
                  ids )

        for r, row in enumerate(rows):
            self.fr_body2.Rconf(r, Min=30, W=1)
            data              = dict(row)
            data["next_race"] = self._format_next_race(data["schedule_today"], data["schedule_1"])

            for c, k in enumerate(REG_CELLS.keys()):
                val = data.get(k)
                lbl = cLbl(self.fr_body2, text="" if val is None else val, **CELL_B, fg="white")
                lbl._grid(R=r, C=c, Stk=ALL)
                self._regist_cells[(r, c)] = lbl

    # --------------------------------------------
    def _search_players(self):

        f_y, f_m, f_d = self.df_y.get().strip(), self.df_m.get().strip(), self.df_d.get().strip()
        t_y, t_m, t_d = self.dt_y.get().strip(), self.dt_m.get().strip(), self.dt_d.get().strip()
        d_from = f"{f_y}-{f_m}-{f_d}"
        d_to   = f"{t_y}-{t_m}-{t_d}"

        venues   = [k for k, v in self.ven_vars.items() if v.get()]
        venues   = [v for v in range(1,25)] if not venues else venues
        grades   = [g for k, v in self.grd_vars.items() if v.get() for g in k]
        grades   = [5,4,3,2,1,0] if not grades else grades
        f_ranks  = [k for k, v in self.rnk_vars.items() if v.get()]
        w_moves  = [k for k, v in self.wm_vars.items()  if v.get()]
        s_course = self.self_c_var.get()
        o_course = self.othr_c_var.get()
        num      = int(self.num_var.get()) or 10
        run      = int(self.run_var.get()) or 30
        order    = "DESC" if self.best.get() else "ASC"

        ph1 = ",".join("?" * len(venues))
        ph2 = ",".join("?" * len(f_ranks))
        ph3 = ",".join("?" * len(grades))

        if self.other:
            sql = f"""
                WITH Stats AS (SELECT p.player_id                              AS pid,
                                      p.name,
                                      p.class_now                              AS cls,
                                      e1.course                                AS self_c,
                                      e2.course                                AS othr_c,
                                      COUNT(DISTINCT e1.race_id)               AS total,
                                      SUM(CASE WHEN e2.finish_rank IN ({ph2})
                                               THEN 1 ELSE 0 END             ) AS cnt
                                 FROM Race_entries e1
                                 JOIN Race_entries e2 ON  e1.race_id  =  e2.race_id AND
                                                          e1.entry_id <> e2.entry_id
                                 JOIN      Players p  ON p.player_id  = e1.player_id
                                 JOIN        Races r  ON   r.race_id  = e1.race_id
                                WHERE e1.date BETWEEN ? AND ?
                                  AND e1.course = ?
                                  AND e2.course = ?
                                  AND e1.venue_id IN ({ph1})
                                  AND r.grade     IN ({ph3})
                                GROUP BY p.player_id, p.name, p.class_now
                               HAVING COUNT(DISTINCT e1.race_id) >= ?                     )

              SELECT ROW_NUMBER() OVER (ORDER BY (100.0*cnt / total) DESC) AS rank,
                     pid,
                     name,
                     cls,
                     self_c,
                     othr_c,
                     ROUND(100.0 * cnt / total, 1) AS rate,
                     cnt,
                     total
                FROM Stats
               ORDER BY rate {order}
               LIMIT {num};
            """
            params = (*f_ranks, d_from, d_to, s_course, o_course, *venues, *grades, run)
            rows   = dal.fetch_all(sql, params)

        else:
            ph4  = ",".join("?" * len(w_moves))
            ph   = f" AND e.win_move IN ({ph4})" if w_moves else ""

            sql = f"""
                WITH Stats AS (SELECT e.course,
                                      e.player_id                             AS pid,
                                      COUNT(*)                                AS total,
                                      SUM(CASE WHEN(e.finish_rank IN ({ph2})
                                                    {ph})
                                               THEN 1 ELSE 0 END            ) AS cnt

                                 FROM Race_entries e
                                 JOIN        Races r ON r.race_id = e.race_id
                                WHERE e.date BETWEEN ? AND ?
                                  AND e.course = ?
                                  AND e.venue_id IN ({ph1})
                                  AND r.grade    IN ({ph3})

                                GROUP BY e.player_id
                               HAVING COUNT(*) >= {run}                                  )

              SELECT ROW_NUMBER() OVER (ORDER BY (100.0*cnt / total) DESC) AS rank,
                     p.player_id                   AS pid,
                     p.name,
                     p.class_now                   AS cls,
                     course,
                     ROUND(100.0 * cnt / total, 1) AS rate,
                     cnt,
                     total
                FROM Stats s
                JOIN Players p ON p.player_id = s.pid
               ORDER BY rate {order}
               LIMIT {num};
                """
            if w_moves: params = (*f_ranks, *w_moves, d_from, d_to, s_course, *venues, *grades)
            else:       params = (*f_ranks, d_from, d_to, s_course, *venues, *grades)

            rows = dal.fetch_all(sql, params)

        if not rows: return []

        couese    = o_course if self.other else s_course
        json_data = self._from_json()
        avrg_rate = sum(json_data[couese]["rate"][r] for r in f_ranks) *100.0
        out_rows  = []

        for row in rows:
            prow  = dict(row)
            prow |= {"all_over":round(avrg_rate,1), "diff":round(row["rate"] -avrg_rate,1)}
            out_rows.append(prow)

        return out_rows

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