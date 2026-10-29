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

DATE_KEYS = [("fy","%Y"), ("fm","%m"), ("fd","%d"), ("ty","%Y"), ("tm","%m"), ("td","%d")]

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
                  "next_race":("出走予定",693), }

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK = "groove", "solid", "ridge", "raised", "sunken"
ALL, CT ,BD        = "nsew", "center", "bold"

SEL_BG  = "#2F6DB3"###?

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
BTN     = dict(bg=BTN_BG, fg=WHITE, font=(MUI, 9), Bd=(2,RA))
D_LABEL = dict(bg=HDR_BG, fg=WHITE, font=(MUI, 8), Bd=(1,RD))
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
    return f"{to_date(df).strftime('%m/%d')}～{to_date(df).strftime('%m/%d')}"
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
        self.date_vars  = {}
        self.ven_vars   = {}
        self.grd_vars   = {}
        self.rnk_vars   = {}
        self.wm_vars    = {}
        self.wm_cbs     = []
        self.othr_c_cbs = []
        self.self_c_var = tk.IntVar(value=1)
        self.othr_c_var = tk.IntVar(value=None)
        self.num_var    = tk.IntVar(value=10)
        self.run_var    = tk.IntVar(value=25)
        self.best       = tk.BooleanVar(value=True)
        self.other      = False

        self._current_rows      = []
        self.selected_row       = None
        self.selected_player_id = None

        style = ttk.Style()
        style.configure("fpw.TCheckbutton", font=(MUI,10,BD),    background=MAIN_BG)
        style.configure("fpw.TRadiobutton", font=(MUI,10,BD), background=MAIN_BG)

        fr_main = cFr(self, W=1220, H=1400, **BG, px=10, py=15) ;fr_main.Pgate()
        fr_main._grid(R=0, C=0, Stk=ALL)

        fr_top = cFr(fr_main, W=1220, H=600, **BG) ;fr_top._grid(R=0, C=0, py=(0,20)) ;fr_top.Pgate()
        fr_btm = cFr(fr_main, W=1220, H=750, **BG) ;fr_btm._grid(R=1, C=0, px=5)      ;fr_btm.Pgate()

        cntrl  = cFr(fr_top, W= 490, H=600, **BG)  ;cntrl._grid(R=0, C=0, px=5) ;cntrl.Pgate()
        result = cFr(fr_top, W= 680, H=600, **BG) ;result._grid(R=0, C=1, px=5) ;result.Pgate()

        fr_date  = cFr(cntrl, W=490, H= 60, **BG, py= 5)  ;fr_date._grid(R=0, C=0) ;fr_date.Pgate()
        fr_dbtn  = cFr(cntrl, W=490, H= 40, **BG, py= 5)  ;fr_dbtn._grid(R=1, C=0) ;fr_dbtn.Pgate()
        fr_venue = cFr(cntrl, W=490, H=165, **BG, py= 5) ;fr_venue._grid(R=2, C=0) ;fr_venue.Pgate()
        fr_grade = cFr(cntrl, W=490, H= 50, **BG, py=10) ;fr_grade._grid(R=3, C=0) ;fr_grade.Pgate()
        fr_self  = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_self._grid(R=4, C=0) ;fr_self.Pgate()
        fr_othr  = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_othr._grid(R=5, C=0) ;fr_othr.Pgate()
        fr_rank  = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_rank._grid(R=6, C=0) ;fr_rank.Pgate()
        fr_wmvs  = cFr(cntrl, W=490, H= 45, **BG, py=10)  ;fr_wmvs._grid(R=7, C=0) ;fr_wmvs.Pgate()
        fr_param = cFr(cntrl, W=490, H= 45, **BG, py=10) ;fr_param._grid(R=8, C=0) ;fr_param.Pgate()
        fr_sbtn  = cFr(cntrl, W=490, H= 50, **BG, py=10)  ;fr_sbtn._grid(R=9, C=0) ;fr_sbtn.Pgate()

        cLbl(fr_date, text="DATE ( FROM )", **D_LABEL)._grid(R=0, C=0, Cspan=6, Stk=ALL) 
        cLbl(fr_date, text=" DATE ( TO ) ", **D_LABEL)._grid(R=0, C=8, Cspan=6, Stk=ALL)
        cLbl(fr_date, text=" ～ ",            **BGFNT)._grid(R=1, C=6,    px=3, Stk=ALL)

        opts1 = [dict(W=5, Frm=2000, To=2030), dict(W=3, Frm=1, To=12), dict(W=3, Frm=1, To=31)]
        opts2 = dict(Inc=1, font=(MUI,10), Jst="right")
        texts = ["年 ","月 ","日 "]
        for (c, n), keys in zip(enumerate([0,1,2,0,1,2]), DATE_KEYS):
            col = (c if c < 3 else c +1)*2
            var = tk.IntVar(value=None)
            cSpbx(fr_date, **opts1[n], **opts2, Txtv=var)._grid(R=1, C=col, px=2, py=4, ipady=1)
            cLbl(fr_date, text=texts[n], **BGFNT)._grid(R=1, C=col+1, Stk=ALL) 
            self.date_vars[keys[0]] = var

        cBtn( fr_dbtn, W=8, text="直近 1年", **BTN, Com=lambda:self._past_days(365)
             )._grid(R=0, C=0, Stk=ALL, px=5, py=(0,10))
        cBtn( fr_dbtn, W=8, text="直近 半年", **BTN, Com=lambda:self._past_days(182)
             )._grid(R=0, C=1, Stk=ALL, px=5, py=(0,10))

        for c in range(6):
            for r in range(4):
                key = c + (6 * r)
                txt = VENUES[key]
                var = tk.BooleanVar(value=False if key == 2 else True)
                ttk.Checkbutton(fr_venue, text=f"{txt:7}", variable=var, style="fpw.TCheckbutton"
                                ).grid(row=r, column=c, sticky="w", padx=(4,0), pady=4)
                self.ven_vars[key] = var

        cBtn( fr_venue, W=7, text="全 選択", **BTN, Com=self._select_all, px=3
             )._grid(R=4, C=0, py=(8,0))
        cBtn( fr_venue, W=7, text="全 解除", **BTN, Com=self._reset_all,  px=3
             )._grid(R=4, C=1, py=(8,0))

        for c in range(4):
            var = tk.BooleanVar(value=True)
            px  = (30,15) if c == 0 else 15
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

        cBtn(fr_sbtn, W=11, text="登 録", **BTN, Com=self._register_favorite)._grid(R=0, C=0, px=(270,0))
        cBtn(fr_sbtn, W=11, text="検 索", **BTN, Com=self._on_search)._grid(R=0, C=1, px=(20,0))

        self._init_result_table(result)
        self._init_regist_table(fr_btm)
        self._past_days(365)
    # --------------------------------------------
    def _init_result_table(self, parent):

        parent.Rconf(0, Min=28)  ;parent.Cconf(0, Min=650)
        parent.Rconf(1, Min=572)

        self.fr_hdr = cFr(parent,  W=650, H= 28, **HDR_B, Bd=(1,RD))
        self.canvas = cCvs(parent, W=650, H=572, bg=BLACK1)
        self.inner  = cFr(self.canvas, Bd=(1,SD))
        scr_bar     = cSrb(parent, orient="vertical", Com=self.canvas.yview)
        self.canvas.config(yscrollcommand=scr_bar.set)

        self.fr_hdr._grid( R=0, C=0)           ;self.fr_hdr.Pgate()
        self.canvas._grid( R=1, C=0, Stk=ALL)
        scr_bar._grid(     R=1, C=1, Stk="ns")

        self.window = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
       #-----------
        def _mw(e):
            self.canvas.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_conf(event=None):
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfig(self.window, width=self.canvas.winfo_width())
        #-----------
        self.canvas.bind("<Enter>", lambda e:self.canvas.bind_all("<MouseWheel>", _mw))
        self.canvas.bind("<Leave>", lambda e:self.canvas.unbind_all("<MouseWheel>"))
        self.inner.bind("<Configure>", _on_conf)
        self.canvas.bind("<Configure>", _on_conf)

    # --------------------------------------------
    def _init_regist_table(self, parent):

        table1 = cFr(parent, W=1190, H=390) ;table1._grid(R=0, C=0) ;table1.Pgate()
        pannel = cFr(parent, W=1190, H=350) ;pannel._grid(R=1, C=0) ;pannel.Pgate()

        table1.Rconf(0, Min=28)  ;table1.Cconf(0, Min=1160)
        table1.Rconf(1, Min=362)
        pannel.Rconf(0, Min=350) ;pannel.Cconf(0, Min=1160)

        self._regist_cells = {}

        self.fr_hdr2 = cFr(table1,  W=1160, H= 28, **HDR_B, Bd=(1,RD))
        self.canvas2 = cCvs(table1, W=1155, H=362, bg=BLACK1)
        self.inner2  = cFr(self.canvas2, Bd=(1,SD))
        scr_bar2     = cSrb(table1, orient="vertical", Com=self.canvas2.yview)
        self.canvas2.config(yscrollcommand=scr_bar2.set)

        self.fr_hdr2._grid( R=0, C=0)           ;self.fr_hdr2.Pgate()
        self.canvas2._grid( R=1, C=0, Stk=ALL)
        scr_bar2._grid(     R=1, C=1, Stk="ns")

        self.window2 = self.canvas2.create_window((0,0), window=self.inner2, anchor="nw")
       #-----------
        def _mw2(e):
            self.canvas2.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_conf2(event=None):
            self.canvas2.config(scrollregion=self.canvas2.bbox("all"))
            self.canvas2.itemconfig(self.window2, width=self.canvas2.winfo_width())
        #-----------
        self.canvas2.bind("<Enter>", lambda e:self.canvas2.bind_all("<MouseWheel>", _mw2))
        self.canvas2.bind("<Leave>", lambda e:self.canvas2.unbind_all("<MouseWheel>"))
        self.inner2.bind("<Configure>", _on_conf2)
        self.canvas2.bind("<Configure>", _on_conf2)

        cntrl  = cFr(pannel, W=500, H=350)  ;cntrl._grid(R=0, C=0)  ;cntrl.Pgate()
        table2 = cFr(pannel, W=690, H=350) ;table2._grid(R=0, C=1) ;table2.Pgate()

        self._load_regist_list()

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
        for n, (k, v) in enumerate(DATE_KEYS):
            if n < 3: self.date_vars[k].set(int(_past(d).strftime(v)))
            else:     self.date_vars[k].set(int(_today().strftime(v))) 
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
            self.inner.Cconf(c, Min=v[1], W=1)
            hdr = cLbl(self.fr_hdr, text=v[0], **HDR) ;hdr._grid(R=0, C=c, Stk=ALL)
            self._cells[c] = hdr
            for r, data in enumerate(rows):
                self.inner.Rconf(r, Min=30, W=1)
                fg  = "yellow" if k == "rate" else "white"
                lbl = cLbl(self.inner, text=data[k], **CELL_B, fg=fg) ;lbl._grid(R=r, C=c, Stk=ALL)
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
            d, title, grade, venue, rno1, frn1, rno2, frn2 = schedule_today.split(",")
            r1    = f"{rno1}R"
            r2    = f"{rno2}R" if int(rno2) else None
            r1c   = f"{frn1} 号艇"
            r2c   = f"{frn2} 号艇" if int(rno2) else None
            race  = f"[{r1}]  {r1c} / [{r2}]  {r2c}" if int(rno2) else f"[{r1}]  {r1c}"
            return f"[本日]   {VENUES[int(venue)-1]}  {G_LIST[int(grade)]}  {title}  {race}"

        if schedule_1:
            d_from, d_to, title, grade, venue = schedule_1.split(",")
            vname = VENUES[int(venue)-1].strip() if venue else ""
            return f"[{to_range(d_from, d_to)}]   {vname}  {G_LIST[int(grade)]}  {title}"

        return "予定なし"

    # --------------------------------------------
    def _load_regist_list(self):

        for widget in self._regist_cells.values():
            widget.destroy()
        self._regist_cells.clear()

        self.fr_hdr2.Rconf(0, Min=28)
        for c, (k, v) in enumerate(REG_CELLS.items()):
            self.fr_hdr2.Cconf(c, Min=v[1], W=1)
            self.inner2.Cconf( c, Min=v[1], W=1)
            hdr = cLbl(self.fr_hdr2, text=v[0], **HDR) ;hdr._grid(R=0, C=c, Stk=ALL)
            self._regist_cells[c] = hdr

        ids = self._load_favorite_ids()
        if not ids: return

        ph   = ",".join("?" * len(ids))
        rows = dal.fetch_all(
                  f"""
                    SELECT player_id, name, age, class_now, regions,
                           regist_period, flying_st, late_st,
                           schedule_today AS schdl_t,
                           schedule_1     AS schdl_1
                      FROM Players
                     WHERE player_id IN ({ph})
                  """,
                  ids )

        for r, row in enumerate(rows):
            self.inner2.Rconf(r, Min=30, W=1)
            data = dict(row)
            data["next_race"] = self._format_next_race(data["schdl_t"], data["schdl_1"])
            for c, k in enumerate(REG_CELLS.keys()):
                val = data.get(k)
                lbl = cLbl(self.inner2, text="" if val is None else val, **CELL_B, fg="white")
                lbl._grid(R=r, C=c, Stk=ALL)
                self._regist_cells[(r, c)] = lbl

    # --------------------------------------------
    def _search_players(self):

        d_from = f"{self.date_vars["fy"].get()}-{self.date_vars["fm"].get()}-{self.date_vars["fd"].get()}"
        d_to   = f"{self.date_vars["ty"].get()}-{self.date_vars["tm"].get()}-{self.date_vars["td"].get()}"

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