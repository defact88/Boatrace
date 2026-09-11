# -*- coding: utf-8 -*-
# C:\boatrace\UI\odds_window.pyw

import argparse, threading, time, sys, os, sqlite3, logging, json
import tkinter as tk
from tkinter                import ttk, font as tkfont
from datetime               import timedelta, timezone, date, datetime as dt
from Helpers.Custum_func    import cFr, cLbl, cBtn, cEnt, cCvs
from Helpers.scraper_odds   import fetch_all_odds
from Helpers.selenium_buyer import SeleniumBuyer, PurchaseError, LoginError
import tkinter as tk

DB            = r"C:\boatrace\boatrace.db"
ODDS_CTL_PATH = r"C:\boatrace\tmp\json\odds_ctl.json"

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

VENUES = [ "", "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖",  "蒲郡", "常滑",
                 "津", "三国", "びわこ", "住之江",   "尼崎",   "鳴門",  "丸亀", "児島",
               "宮島", "徳山",   "下関",   "若松",   "芦屋",   "福岡",  "唐津", "大村", ]

FRM_BG = {1:"#FFFFFF",2:"#333333",3:"#D40000",4:"#0066CC",5:"#FFD400",6:"#008A2E"}
FRM_FG = {1:"#000000",2:"#FFFFFF",3:"#FFFFFF",4:"#FFFFFF",5:"#000000",6:"#FFFFFF"}

HIL_BG     = "#FFD700"
INCLUDE_BG = "#cce8ff"
CUT_BG     = "#CCCCCC"
CUT_FG     = "#AAAAAA"
NORM_BG    = "#FFFFFF"
HDR_BG     = "#2B4A7A"
HDR_FG     = "#FFFFFF"
PANEL_BG   = "#F0F4FA"
TBL_BG     = "#FFFFFF"
ALT_BG     = "#F0F0FF"
SEP_C      = "#CCCCDD"

HIGH_THRESH = { "3T":1000.0, "3F":100.0, "2T":100.0, "2F":1000.0,
                "TT":1000.0, "FF":100.0, "KK":100.0,              }

ROW_H    = 30
CELL_H   = 26
HDR_H    = 24

#-----------------------------
def parse_odds_min(odds_str:str) -> float:

    if not odds_str: return 0.0

    s = odds_str.replace(" ", "")
    parts = s.split("-")
    try: return float(parts[0])
    except: return 0.0
# ─── 合成オッズ計算 ───
def synthetic_odds(odd_list:list[float]) -> float:
    s = sum(1.0/o for o in odd_list if o > 0)
    return round(1.0/s, 2) if s > 0 else 0.0

#===============================================================================
class OddsWindow(tk.Tk):

    def __init__(self, date:str, venue_id:int, race_no:int, interval_min:int=1, players:dict={}):
        super().__init__()

        self.title("")
        self.geometry("1150x1400+1295+0")  #1220 1400
        self.resizable(False, False)
        self.configure(bg=PANEL_BG)

        self.date           = date
        self.venue_id       = venue_id
        self.race_no        = race_no
        self.players        = {}
        self.interval       = interval_min * 60
        self.fetch_state    = True
        self.var_int        = tk.IntVar(value=1)
        self.odds_data      = {}
        self.selected       = []
        self.cell_refs      = {}
        self.after_id       = None
        self.loading        = False
        self.tbl_rows       = []
        self.grid_items     = {}
        self.formation_vars = {}
        self.formation_chks = {}
        self.mustin_vars    = {}
        self.mustin_chks    = {}

        self.formation      = self._new_formation_state()
        self.mustin         = self._new_mustin_state()
        self.deadline       = self._fetch_deadline(self.date, self.venue_id, self.race_no)[0]
        self._buyer:"SeleniumBuyer|None" = None

        self.update_idletasks()

        self._COL_DEF       = [ ("×",           25, CT),
                                ("賭式",         90, CT),
                                ("組合せ",       80, CT),
                                ("オッズ   ",   100, CT),
                                ("ベット",       70, CT),
                                ("",             30, CT),
                                ("  予想配当",  180, CT ), ]

        self._update_Players(self.date, self.venue_id, self.race_no)
        self._build_ui()

        th = threading.Thread(target=self._read_stdin_loop, daemon=True)
        th.start()

        self.after(200, self._start_fetch)
        self.protocol("WM_DELETE_WINDOW", self._on_ow_close)

    #-------------------------
    def _new_formation_state(self):

        return {n:{1:False, 2:False, 3:False} for n in range(1,8)}
    #-------------------------
    def _new_mustin_state(self):

        return {n:{1:False, 2:False} for n in range(1,7)}

    # -------- 標準入力待受スレッドループ --------
    def _read_stdin_loop(self):

        try:
            for line in iter(sys.stdin.readline, ''):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                self.after(0, lambda d=data: self._handle_command(d))
        except Exception:
            pass

    # ----------- 受信コマンド処理 ---------------
    def _handle_command(self, d: dict):

        state = d.get("state")
        if state == "stop":
            self._on_ow_close()
            return

        if state == "withdraw":
            self.withdraw()
        elif state in ("deiconify", "normal"):
            self.deiconify()

        new_date  = d.get("date", self.date)
        new_venue = d.get("venue", self.venue_id)
        new_race  = d.get("race", self.race_no)

        changed = (new_date != self.date or int(new_venue) != self.venue_id or int(new_race) != self.race_no)

        if changed and not self.loading:
            self.date     = new_date
            self.venue_id = int(new_venue)
            self._switch_race(int(new_race))

    # ----------- ウィンドウ終了処理 -------------
    def _on_ow_close(self):

        if self.after_id is not None:
            try: self.after_id.after_cancel(self.after_id)
            except Exception: pass
            self.after_id = None

        try: self.destroy()
        except Exception: pass

    #====================== UI 構築 ========================
    def _build_ui(self):

        # ヘッダー
        tb_L = cFr(self, bg=HDR_BG, height=36) ;tb_L._pack(fill="x", side="top")
        tb_R = cFr(tb_L, bg=HDR_BG)            ;tb_R._pack(side="right", px=8)

        d     = dt.fromisoformat(self.date).strftime("%Y 年 %#m 月 %#d 日")
        venue = VENUES[self.venue_id]

        self.lbl_title1 = cLbl(tb_L, text=f" {d}    {venue}   ",
                                   bg=HDR_BG, fg=HDR_FG, font=(MUI,10))
        self.lbl_title1._pack(side="left", py=4, Anc="w")
        self.lbl_title2 = cLbl( tb_L, text=f"{self.race_no} R    ",
                                   bg=HDR_BG, fg=HDR_FG, font=(MUI,10))
        self.lbl_title2._pack(side="left", py=4,Anc="e")

        self._race_btns = {}
        for rno in range(1, 13):
            btn = cBtn(tb_L, text=f"{rno} R", width=5, command=lambda r=rno: self._switch_race(r))
            btn._pack(side="left", px=2, py=6)
            self._race_btns[rno] = btn
        self._update_race_btn_style()

        cBtn( tb_R, text=" 更   新 ", command=self._start_fetch, bg="#4A7ACC", fg="white",
                   font=(GUI,9,BD), Rel=RA, px=5 )._pack(side="right", px=(10,5), py=3)
        cLbl(tb_R, text="分", bg=HDR_BG, fg=HDR_FG, font=(MUI,8))._pack(side="right", px=5)
        tk.Spinbox( tb_R, from_=1, to=10, width=3, textvariable=self.var_int, font=(GUI,9)
                   ).pack(side="right", padx=(8,0), pady=3)
        cLbl(tb_R, text="   更新間隔", fg=HDR_FG, font=(MUI,8), bg=HDR_BG)._pack(side="right")
        self.lbl_next = cLbl(tb_R, text="", bg=HDR_BG, fg="#AADDFF", font=(MUI,9))
        self.lbl_next._pack(side="right",  px=(0,8))

        pane = tk.PanedWindow(self, orient="vertical", bg=PANEL_BG, sashwidth=5, sashrelief="raised")
        pane.pack(fill="both", expand=True)

        # オッズグリッド
        top_frame = cFr(pane, bg=PANEL_BG)
        pane.add(top_frame, minsize=1035, stretch="always")

        self.canvas_top = cCvs(top_frame, bg=PANEL_BG, highlightthickness=0)
        self.grid_frame = cFr(self.canvas_top, bg=PANEL_BG)
        self.canvas_top._pack(fill="both", expand=True)
        self.canvas_top.create_window((0,0), window=self.grid_frame, anchor="nw")

        # 下部パネル
        bot_frame = cFr(pane, bg="#ECEEF5")
        pane.add(bot_frame, minsize=360, stretch="never")

        tbl_outer = cFr(bot_frame, bg="#ECEEF5", Bd=(1,SD))
        ctrl_fr   = cFr(bot_frame, bg=HDR_BG,    Bd=(1,GR), padx=5)
        filter_fr = cFr(bot_frame, bg="#883333")

        tbl_outer._pack(side="left", Exp=True, fill="both", Anc="w", px=1, py=2)
        filter_fr._pack(side="left", Exp=True, fill="y",    Anc="w", px=1, py=2)
        ctrl_fr._pack(  side="left", Exp=True, fill="both", Anc="w", px=0, py=2)

        fr_hdr  = cFr(filter_fr, bg=HDR_BG,    Bd=(1,GR))
        fr_fmt  = cFr(filter_fr, bg="#2A6632", Bd=(1,GR), px=3)
        fr_must = cFr(filter_fr, bg="#883333", Bd=(1,GR), px=5)

        fr_hdr._pack( side="top",  fill="x",              Anc=CT)
        fr_fmt._pack( side="left", fill="both", Exp=True, Anc="w")
        fr_must._pack(side="left", fill="both", Exp=True, Anc="w")

        cLbl( fr_hdr,  text="FILTER", py=2, font=(MUI,9),   fg="white", bg=HDR_BG,    Anc=CT
             )._pack(side="top", fill="both", Anc=CT)

        cLbl( fr_fmt,  text="FORMATION",   font=(MUI,9,BD), fg=HDR_FG,  bg="#2A6632", Anc=CT,
             )._grid(R=0, C=0, Cspan=3, Stk=ALL)

        cLbl( fr_must, text="  MUST IN  ", font=(MUI,9,BD), fg="white", bg="#883333", Anc=CT,
             )._grid(R=0, C=0, Cspan=2, py=2)

        # FORMATION
        for i in range(1,4):
            cLbl( fr_fmt, text=f"{i}着", font=(MUI,9), fg=HDR_FG, bg="#2A6632", padx=10, Anc=CT
                 )._grid(R=1, C=i-1, Stk=ALL, py=2)
            for n in range(1, 8):
                var = tk.BooleanVar(value=self.formation.get(n, {}).get(i, False))
                chk = tk.Checkbutton( fr_fmt, text=str(n) if n <=6 else "全", font=(GUI,9,BD),
                                      selectcolor="#f8ff71", variable=var, indicatoron=0,
                                      bg="white" if n <=6 else "#ffd877", fg="black",
                                      pady=4, padx=2, command=lambda no=n, p=i, v=var:
                                      self._on_formation_change(no, p, v.get())                 )
                chk.grid(row=n+1, column=i-1, padx=2, pady=2, sticky=ALL)
                self.formation_vars[(n, i)] = var
                self.formation_chks[(n, i)] = chk

        # MUST IN
        for i in range(1,3):
            cLbl( fr_must, text="AND" if i ==1 else " OR " , font=(MUI,8,BD), fg="white", bg="#883333",
                   padx=1, Anc=CT )._grid(R=1, C=i-1, Stk=ALL, py=(0,2))
            for n in range(1, 7):
                var = tk.BooleanVar(value=self.mustin.get(n, {}).get(i, False))
                chk = tk.Checkbutton( fr_must, text=str(n), font=(GUI,9,BD), fg="black",
                                      selectcolor="#f8ff71", bg="white" if n <=6 else "#2A6632",
                                      variable=var, indicatoron=0, pady=4, padx=4,
                                      command=lambda no=n, p=i, v=var:
                                      self._on_mustin_change(no, p, v.get())                    )
                chk.grid(row=n+1, column=i-1, padx=2, pady=2, sticky=ALL)
                self.mustin_vars[(n, i)] = var
                self.mustin_chks[(n, i)] = chk

        cBtn( fr_must, text="全 クリア", bg="#666688", fg="white", font=(MUI,10), px=8, Rel=RA, Com=self._clear_all_filters, 
             )._grid(R=8, C=0, Cspan=2, py=2)

        # CTRLパネル
        opt1 = dict(bg=HDR_BG,    fg=HDR_FG)
        opt2 = dict(bg=HDR_BG,    fg="#FFD700")
        opt3 = dict(bg="#E06020", fg="white")
        default = "ーー.ー"
        self.lbl_count     = cLbl(ctrl_fr, text="0 点",  **opt1, font=(MUI,11), Anc="e")
        self.lbl_synth     = cLbl(ctrl_fr, text=default, **opt1, font=(MUI,11))
        self.ent_equal_bet = cEnt(ctrl_fr, W=8, Jst="right",     font=(MUI,11))
        self.ent_equal_div = cEnt(ctrl_fr, W=8, Jst="right",     font=(MUI,11))
        self.low_divid     = cLbl(ctrl_fr, text="",      **opt1, font=(MUI,10))
        self.high_divid    = cLbl(ctrl_fr, text="",      **opt1, font=(MUI,10))
        self.low_marjin    = cLbl(ctrl_fr, text="",      **opt1, font=(MUI,10))
        self.high_marjin   = cLbl(ctrl_fr, text="",      **opt1, font=(MUI,10))
        self.total_bet     = cLbl(ctrl_fr, text="",      **opt1, font=(MUI,11))
        self.ent_equal_div.insert(1, "")

        cBtn( ctrl_fr, text="クリア", bg="#666688", fg="white", font=(MUI,8), px=10, Rel=RA, Com=self._clear_alloc
             )._grid(R=0, C=0, px=10, py=10)
        cBtn( ctrl_fr, text="  購  入  ", bg="yellow", fg="black", font=(MUI,10,BD), Rel=RA, Com=self._open_purchase_dialog
             )._grid(R=0, C=5, px=(0,5), py=10)

        cLbl(ctrl_fr, text="一律配分",  **opt1, font=(MUI,10))._grid(R=1, C=0, px=2)
        self.ent_equal_bet._grid(                           Cspan=2, R=1, C=1, px=(10,0))
        cLbl(ctrl_fr,  text="00 円",    **opt1, font=(MUI,10), Anc="s")._grid(R=1, C=3)
        cBtn( ctrl_fr, text="配分実行", **opt3, font=(MUI,10), px=10, Rel=RA, Com=self._exec_equal_bet
             )._grid(                                       Cspan=2, R=1, C=4,  px=(40,10), py=5)

        cLbl(ctrl_fr, text="均等配分",  **opt1, font=(MUI,10))._grid(R=2, C=0, px=2)
        self.ent_equal_div._grid(                           Cspan=2, R=2, C=1, px=(10,0))
        cLbl(ctrl_fr,  text="00 円",    **opt1, font=(MUI,10), Anc="s")._grid(R=2, C=3)
        cBtn( ctrl_fr, text="配分実行", **opt3, font=(MUI,10), px=10, Rel=RA, Com=self._exec_equal_divide
             )._grid(                                       Cspan=2, R=2, C=4, px=(40,10), py=5)

        cLbl(ctrl_fr, text="ベッド 計 :",  **opt2, font=(MUI,10), Anc="w")._grid(R=3, C=0, py=10)
        self.lbl_count._grid(R=3, C=1, Stk="w", px=(8, 0), py=10)
        cLbl(ctrl_fr, text="合成オッズ :", **opt2, font=(MUI,10), Anc="w")._grid(R=3, C=2, Stk="w", Cspan=3, py=10)
        self.lbl_synth._grid(R=3, C=5, px=(0, 10), py=10)

        cLbl(ctrl_fr, text="期待配当 :", **opt1, font=(MUI,10), Anc="w")._grid(R=4, C=0, py=10)
        self.low_divid._grid( R=4, C=1, Cspan=2, py=10)
        cLbl( ctrl_fr, text="～",        **opt1, font=(MUI,10), Anc="w")._grid(R=4, C=3, py=10)
        self.high_divid._grid(R=4, C=4, Cspan=2, Stk="we", py=10)

        cLbl(ctrl_fr, text="      差額 :", **opt1, font=(MUI,10), Anc="w")._grid(R=5, C=0, py=10)
        self.low_marjin._grid( R=5, C=1, Cspan=2, py=10)
        cLbl( ctrl_fr, text="～",        **opt1, font=(MUI,10), Anc="w")._grid(R=5, C=3, py=10)
        self.high_marjin._grid(R=5, C=4, Cspan=2, Stk="we", py=10)

        cLbl(ctrl_fr, text="ベット総額", **opt1, font=(MUI,10))._grid(R=6, C=0, px=5)
        self.total_bet._grid(R=6, C=1, Cspan=3, px=5, py=20)

        # 選択ベット一覧テーブル
        hdr_row = cFr(tbl_outer, bg=HDR_BG, height=HDR_H)
        hdr_row._pack(fill="x", side="top")
        hdr_row.pack_propagate(False)

        w0 = self._COL_DEF[0][1]
        cBtn( hdr_row, text="x", bg="#884444", fg="white", font=(GUI,8,BD), relief="flat",
                   command=self._clear_all_sel )._grid(R=0, C=0, Cspan=1, Stk="nsew", ipadx=2)

        for ci, (txt, w, anc) in enumerate(self._COL_DEF):
            hdr_row.grid_columnconfigure(ci, minsize=w)
            if ci == 0: continue 
            cLbl( hdr_row, text=txt, bg=HDR_BG, fg=HDR_FG, font=(GUI,8,BD), Anc=anc
                 )._grid(R=0, C=ci, sticky=ALL)

        scrl_fr = cFr(tbl_outer, bg="#ECEEF5")           ;scrl_fr._pack(fill="both", expand=True)
        vsb2    = ttk.Scrollbar(scrl_fr, orient="vertical") ;vsb2.pack(side="right", fill="y")

        self._tbl_canvas = tk.Canvas( scrl_fr, bg=TBL_BG, yscrollcommand=vsb2.set)
        self._tbl_canvas.pack(side="left", fill="both", expand=True)
        vsb2.config(command=self._tbl_canvas.yview)

        self._tbl_inner = tk.Frame(self._tbl_canvas, bg=TBL_BG)
        self._tbl_win  = self._tbl_canvas.create_window((0, 0), window=self._tbl_inner, anchor="nw")
        #-----------
        def _on_inner_cfg(e):
            self._tbl_canvas.configure(scrollregion=self._tbl_canvas.bbox("all"))
        #-----------
        def _on_canvas_cfg(e):
            self._tbl_canvas.itemconfig(self._tbl_win, width=e.width)
        #-----------
        def _on_wheel(e):
            self._tbl_canvas.yview_scroll(int(-1*(e.delta / 120)), "units")
        #-----------
        self._tbl_inner.bind("<Configure>", _on_inner_cfg)
        self._tbl_canvas.bind("<Configure>", _on_canvas_cfg)
        self._tbl_canvas.bind("<MouseWheel>", _on_wheel)
        self._tbl_inner.bind("<MouseWheel>",  _on_wheel)
        self.tbl_rows = []

    #----------- ボタン動作 ------------
    #------------ MUST IN --------------
    def _on_mustin_change(self, boat_no:int, position:int, val:bool):

        if boat_no not in self.mustin: self.mustin[boat_no] = {}
        self.mustin[boat_no][position] = bool(val)
        self._refresh_grid_cells()
    #----------- FORMATION -------------
    def _on_formation_change(self, boat_no:int, position:int, val:bool):

        if boat_no == 7:
            for no in range(1, 7):
                self.formation[no][position] = bool(val)
                self._set_check_var(self.formation_vars, (no, position), bool(val))
            self.formation[7][position] = bool(val)
            self._set_check_var(self.formation_vars, (7, position), bool(val))
        else:
            if boat_no not in self.formation: self.formation[boat_no] = {}
            self.formation[boat_no][position] = bool(val)
            all_on = all(self.formation[n][position] for n in range(1, 7))
            self.formation[7][position] = all_on
            self._set_check_var(self.formation_vars, (7, position), all_on)

        self._refresh_grid_cells()
    #------------ 一律配分 -------------
    def _exec_equal_bet(self):

        if not self.tbl_rows: return
        try: unit = int(self.ent_equal_bet.get()) *100
        except: return
        if unit <= 0: return

        unit_str = f"{(unit//100):,}"
        for alloc_var, ret_lbl, bt, key, odds_str in self.tbl_rows:
            alloc_var.set(unit_str)
            ret = round(unit * parse_odds_min(odds_str))
            ret_lbl.config(text=f"{ret:,} 円")
        self._update_total_bet()
    #------------ 均等配分 -------------
    def _exec_equal_divide(self):

        if not self.selected: return
        try: budget = int(self.ent_equal_div.get()) *100
        except: return

        odds_vals = []
        for alloc_var, ret_lbl, bt, key, odds_str in self.tbl_rows:
            odds_vals.append(parse_odds_min(odds_str))

        inv_sum = sum(1.0/o for o in odds_vals if o > 0)
        if inv_sum == 0: return

        for i, (alloc_var, ret_lbl, bt, key, odds_str) in enumerate(self.tbl_rows):
            o = odds_vals[i]
            if o <= 0:
                alloc_var.set("")
                ret_lbl.config(text="")
                continue

            raw   = budget * (1.0 / o) / inv_sum
            unit  = max(100, int(raw // 100) * 100)
            alloc_var.set(f"{(unit//100):,}")
            ret_lbl.config(text=f"{round(unit * o):,} 円")
    #-----------------------------------
    def _clear_alloc(self):

        for alloc_var, ret_lbl, bt, key, odds_str in self.tbl_rows:
            alloc_var.set("")
            ret_lbl.config(text="")

        self.selected = [ (s[0], s[1], s[2], "") for s in self.selected ]
        self._update_total_bet()
    #-----------------------------------
    def _delete_row(self, bt:str, key:tuple):

        existing = [(i,s) for i,s in enumerate(self.selected) if s[0]==bt and s[1]==key]
        if existing:
            self.selected.pop(existing[0][0])
            if (bt, key) in self.cell_refs:
                cell, labl, _ = self.cell_refs[(bt, key)]
                cell.config(bg=NORM_BG)
                labl.config(bg=NORM_BG)
        self._refresh_tree()
    #-----------------------------------
    def _clear_all_sel(self):

        self.selected.clear()
        self._refresh_grid_cells()
        self._refresh_tree()
    #-----------------------------------
    def _clear_all_filters(self):

        for b in self.formation:
            for pos in self.formation[b]:
                self.formation[b][pos] = False
        for b in self.mustin:
            for type_key in self.mustin[b]:
                self.mustin[b][type_key] = False

        self._sync_filter_widgets()
        self._refresh_grid_cells()
    #-----------------------------------
    def _set_check_var(self, var_dict:dict, key:tuple, value:bool):

        var = var_dict.get(key)
        if var is not None:
            var.set(bool(value))
    #-----------------------------------
    def _sync_filter_widgets(self):

        for pos in (1, 2, 3):
            for boat_no in range(1, 8):
                self._set_check_var( self.formation_vars, (boat_no, pos),
                                     self.formation.get(boat_no,{}).get(pos, False) )
        for pos in (1, 2):
            for boat_no in range(1, 7):
                self._set_check_var( self.mustin_vars, (boat_no, pos),
                                     self.mustin.get(boat_no,{}).get(pos, False) )

    #==================== レース切替 =======================
    def _switch_race(self, race_no:int):

        if self.loading: return
        self.race_no = race_no
        # レース切替時はフレームを再生成するため grid_items をクリア
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.cell_refs.clear()
        self.grid_items.clear()
        d  = dt.fromisoformat(self.date).strftime("%Y 年 %#m 月 %#d 日")

        self.lbl_title1.config(text=f" {d}    {VENUES[self.venue_id]}   ")
        self.lbl_title2.config(text=f"{self.race_no} R    ")
        self._update_race_btn_style()
        self._update_Players(self.date, self.venue_id, self.race_no)
        self.selected.clear()
        self.deadline  = self._fetch_deadline(self.date, self.venue_id, self.race_no)[0]
        self.mustin    = self._new_mustin_state()
        self.formation = self._new_formation_state()
        self._sync_filter_widgets()
        self._refresh_tree()
        if self.after_id is not None:
            try: self.after_cancel(self.after_id)
            except Exception: pass
            self.after_id = None
        self.fetch_state = True
        self._start_fetch()

    #-----------------------------------
    def _update_race_btn_style(self):

        for rno, btn in self._race_btns.items():
            if rno == self.race_no:
                btn.config(bg="#FFD700", fg="#222222", font=(MUI,8,BD), relief=GR)
            else:
                btn.config(bg="#4A6A9A", fg="#FFFFFF", font=(MUI,8,BD), relief=RA)

    #================ フェッチ & タイマー ==================
    def _start_fetch(self):

        if self.loading: return
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.loading = True
        self.title("取得中...")

        threading.Thread(target=self._fetch_worker, daemon=True).start()
    #-----------------------------------
    def _fetch_worker(self):
        #-----------
        def on_prog(key):
            self.after(0, lambda k=key: self.title(f"{k} 完了"))
        #-----------
        try:
            data = fetch_all_odds( self.date.replace("-", ""), self.venue_id, self.race_no,
                                                                       on_progress=on_prog  )
        except Exception as e:
            self.after(0, lambda: self.title(f"取得失敗: {e}"))
            self.loading = False
            return
        self.after(0, lambda d=data: self._on_fetched(d))
    #-----------------------------------
    def _on_fetched(self, data:dict):

        self.odds_data = data
        self.loading   = False
        err = data.get("error")
        self.title(f" {err}" if err else "更新完了")
        self._rebuild_grids()
        self._refresh_tree()
        self._schedule_next()
    #-----------------------------------
    def _schedule_next(self): 

        if (dt.fromisoformat(self.deadline) +timedelta(minutes=5)) <= dt.now():
            self.lbl_next.config(text=f"更新停止")
            self.fetch_state = False
        if dt.now() +timedelta(minutes=1) >= dt.fromisoformat(self.deadline):
            self.interval = 15
        else:
            self.interval = self.var_int.get() * 60
        self._tick_remaining = self.interval

        if self.after_id is not None:
            try: self.after_cancel(self.after_id)
            except Exception: pass

        self.after_id = self.after(1000, self._tick)
    #-----------------------------------
    def _tick(self):

        if self.fetch_state:
            if self._tick_remaining <= 0:
                self.lbl_next.config(text="")
                self._start_fetch()
                return
            self.lbl_next.config(text=f"次回更新 {self._tick_remaining} 秒")
            self._tick_remaining -= 1

        self.after_id = self.after(1000, self._tick)

    #================= オッズグリッド更新 ==================
    def _rebuild_grids(self):

        if not self.grid_items:
            self._build_all_grids()
        else:
            self._refresh_grid_cells()

    #-----------------------------------
    def _build_all_grids(self):

        d = self.odds_data

        # 3連単
        blk1 = cFr(self.grid_frame, bg=PANEL_BG, Rel=GR, bd=1)
        blk1._grid(R=0, C=0, Stk="nw", px=(23,4), py=(4,6))
        self._build_3T(blk1, d.get("3T",{}))

        # 3連複, 拡連複
        blk2 = cFr(self.grid_frame, bg=PANEL_BG, Rel=GR, bd=1)
        blk2._grid(R=1, C=0, Stk="nw", px=4, py=0)
        self._build_3F_KK(blk2, d.get("3F",{}), d.get("KK",{}))

        # 2連単
        blk3 = cFr(self.grid_frame, bg=PANEL_BG, Rel=GR, bd=1)
        blk3._grid(R=0, C=1, Rspan=2, Stk="nw", px=(20,0), py=10)
        self._build_2T(blk3, d.get("2T",{}))

        # 2連複
        blk4 = cFr(self.grid_frame, bg=PANEL_BG, Rel=GR, bd=1)
        blk4._grid(R=0, C=2, Rspan=2, Stk="nw", px=(20,0), py=10)
        self._build_2F(blk4, d.get("2F",{}))

        # 単勝/複勝
        self._build_others(blk4, "単勝", "TT", d.get("TT",{}))
        self._build_others(blk4, "複勝", "FF", d.get("FF",{}))

        self._refresh_grid_cells()

    #------ ブロック共通フレーム -------
    def _block_header(self, parent, title:str) -> cFr:

        hdr = cFr(parent, bg=HDR_BG, py=1) ;hdr._pack(fill="x")
        cLbl(hdr, text=title, bg=HDR_BG, fg=HDR_FG, font=(MUI,8), py=1)._pack(side="top")

        return parent
    #------------- 3連単 ---------------
    def _build_3T(self, parent, data: dict):

        self._block_header(parent, "3連単")
        fr = cFr(parent, bg=PANEL_BG) ;fr._pack(px=0, py=1, anchor="nw")

        names = getattr(self, 'players', {})
        boats = [1, 2, 3, 4, 5, 6]
        for col, num1 in enumerate(boats):
            bg = FRM_BG[num1]
            fg = FRM_FG[num1]

            hf0 = cFr(fr, bg=bg, W=100, H=18) ;hf0.pack_propagate(False)
            hf1 = cFr(fr, bg=bg, W=100, H=22) ;hf1.pack_propagate(False)
            hf0._grid(R=0, C=col*3, Cspan=3, Stk="nsew")
            hf1._grid(R=1, C=col*3, Cspan=3, Stk="nsew")

            cLbl(hf0, text=str(num1),           bg=bg, fg=fg, font=(MUI,9,BD))._pack(expand=True)
            cLbl(hf1, text=names.get(num1, ""), bg=bg, fg=fg, font=(MUI,10), Anc="n")._pack(Exp=True)

            row     = 2
            boats_2 = [r for r in boats if r != num1]

            for num2 in boats_2:
                fr2 = cFr(fr, W=20, H=120, bg=FRM_BG[num2], Rel=GR, bd=1)
                fr2.pack_propagate(False)
                fr2._grid(R=row, C=col*3, Rspan=4, Stk="nsew")
                cLbl( fr2, text=str(num2), bg=FRM_BG[num2], fg=FRM_FG[num2], font=(MUI,9,BD)
                     )._pack(expand=True)

                boats_3 = [r for r in boats_2 if r != num2]

                for num3 in boats_3:
                    fr3 = cFr(fr, W=20, H=ROW_H, bg=FRM_BG[num3], Rel=GR, bd=1)
                    fr3.pack_propagate(False)
                    fr3._grid(R=row, C=col*3 +1, Stk="nsew")
                    cLbl( fr3, text=str(num3), bg=FRM_BG[num3], fg=FRM_FG[num3], font=(MUI,9,BD)
                         )._pack(expand=True)

                    key   = (num1, num2, num3)
                    label = f"３連単 {num1}ー{num2}ー{num3}"
                    self._grid_data_cell(fr, "3T", 90, ROW_H, row, col*3+2, data, key, label, 1)

                    row += 1

    #-------------- 3連複 --------------
    def _build_3F_KK(self, parent, data:dict, kk:dict):

        boats_2 = [2, 3, 4, 5]
        boats_3 = [3, 4, 5, 6]

        self._block_header(parent, "3連複 / 拡連複")
        fr = cFr(parent, bg=PANEL_BG) ;fr._pack(px=0, py=1)

        ii  = 4
        b_2 = boats_2[:]
        for col, num1 in enumerate(range(1, 5)):
            bg = FRM_BG[num1]
            fg = FRM_FG[num1]

            hf = cFr(fr, bg=bg, W=100, H=27, Bd=(1, GR)) ;hf.pack_propagate(False)
            hf._grid(R=0, C=col*3, Cspan=3, Stk="nsew")
            cLbl(hf, text=str(num1), bg=bg, fg=fg, font=(MUI,9,BD))._pack(expand=True)

            i   = ii
            row = 1
            b_3 = boats_3[:]
            for num2 in b_2:
                fr2 = cFr(fr, W=20, H=ROW_H*i, bg=FRM_BG[num2], Rel=GR, bd=1)
                fr2.pack_propagate(False)
                fr2._grid(R=row, C=col*3, Rspan=i, Stk="nsew")
                cLbl( fr2, text=str(num2), bg=FRM_BG[num2], fg=FRM_FG[num2], font=(MUI,9,BD)
                     )._pack(expand=True)

                for num3 in b_3:
                    fr3 = cFr(fr, W=20, H=ROW_H, bg=FRM_BG[num3], Rel=GR, bd=1)
                    fr3.pack_propagate(False)
                    fr3._grid(R=row, C=col*3 +1, Stk="nsew")
                    cLbl( fr3, text=str(num3), bg=FRM_BG[num3], fg=FRM_FG[num3], font=(MUI,9,BD)
                         )._pack(expand=True)

                    key      = (num1, num2, num3)
                    label = f"３連複 {num1}={num2}={num3}"
                    self._grid_data_cell(fr, "3F", 90, ROW_H, row, col*3+2, data, key, label, 1)

                    row += 1
                del b_3[0]
                i -= 1
            del b_2[0]
            del boats_3[0]
            ii -= 1
        del boats_2[0]

        #----------- 拡連複 ------------
        boats_4 = [5, 4, 3, 2, 1]
        boats_5 = [2, 3, 4, 5, 6]
        out     = [5, 4, 3, 2]

        for i, num1 in enumerate(boats_4):
            row = 9 -i
            hf  = cFr(fr, W=100, H=ROW_H, bg=FRM_BG[num1], Bd=(1, GR)) ;hf.pack_propagate(False)
            hf._grid(R=row, C=i*3 +4, Cspan=3, Stk="nsew")
            cLbl(hf, text=str(num1), bg=FRM_BG[num1], fg=FRM_FG[num1], font=(MUI,9,BD))._pack(expand=True)

            b_2 = [r for r in boats_5 if r not in out]
            for i2, num2 in enumerate(b_2, 1):
                fr2 = cFr(fr, W=20, H=ROW_H, bg=FRM_BG[num2], Rel=GR, bd=1)
                fr2.pack_propagate(False)
                fr2._grid(R=row +i2, C=i*3 +4, Stk="nsew")
                cLbl( fr2, text=str(num2), bg=FRM_BG[num2], fg=FRM_FG[num2], font=(MUI,9,BD)
                     )._pack(expand=True)

                key   = (num1, num2)
                label = f"拡連複 {num1} ≡ {num2} "
                self._grid_data_cell(fr, "KK", 110, ROW_H, row+i2, i*3+5, kk, key, label, 2)

            try: del out[0]
            except: pass

    #------------- 2連単 ---------------
    def _build_2T(self, parent, data:dict):

        self._block_header(parent, "2連単")
        fr = cFr(parent, bg=PANEL_BG) ;fr._pack(px=0, py=1)

        for row, num1 in enumerate(range(1, 7)):
            fr1 = cFr(fr, W=20, H=120, bg=FRM_BG[num1], Rel=GR, bd=1)
            fr1.pack_propagate(False)
            fr1._grid(R=row *5, C=0, Rspan=5, Stk="nsew")
            cLbl( fr1, text=str(num1), bg=FRM_BG[num1], fg=FRM_FG[num1], font=(MUI,9,BD)
                 )._pack(expand=True)

            for row2,  num2 in enumerate([r for r in range(1, 7) if r != num1]):
                fr2 = cFr(fr, W=20, H=30, bg=FRM_BG[num2], Rel=GR, bd=1)
                fr2.pack_propagate(False)
                fr2._grid(R=row *5 +row2, C=1, Stk="nsew")
                cLbl( fr2, text=str(num2), bg=FRM_BG[num2], fg=FRM_FG[num2], font=(MUI,9,BD)
                     )._pack(expand=True)

                key   = (num1, num2)
                label = f"２連単  {num1} ー {num2} "
                self._grid_data_cell(fr, "2T", 80, ROW_H, row*5+row2, 2, data, key, label)

    #-------------- 2連複 --------------
    def _build_2F(self, parent, data:dict):

        self._block_header(parent, "2連複")
        fr = cFr(parent, bg=PANEL_BG) ;fr._pack(px=0, py=1)

        boats = [2, 3, 4, 5, 6]
        row   = 0
        for i, num1 in enumerate(range(1, 6)):
            fr1 = cFr(fr, W=20, H=30*(5 -i), bg=FRM_BG[num1], Rel=GR, bd=1)
            fr1.pack_propagate(False)
            fr1._grid(R=row, C=0, Rspan=5 -i, Stk="nsew")
            cLbl( fr1, text=str(num1), bg=FRM_BG[num1], fg=FRM_FG[num1], font=(MUI,9,BD)
                 )._pack(expand=True)

            for num2 in boats:
                fr2 = cFr(fr, W=20, H=30, bg=FRM_BG[num2], Rel=GR, bd=1)
                fr2.pack_propagate(False)
                fr2._grid(R=row, C=1, Stk="nsew")
                cLbl( fr2, text=str(num2), bg=FRM_BG[num2], fg=FRM_FG[num2], font=(MUI,9,BD)
                     )._pack(expand=True)

                key   = (num1, num2)
                label = f"２連複 {num1} ＝ {num2} "
                self._grid_data_cell(fr, "2F", 80, ROW_H, row, 2, data, key, label)

                row += 1

            try: del boats[0]
            except: pass

    #----------- 単勝/複勝 -------------
    def _build_others(self, parent, title, bet_type, data):

        self._block_header(parent, title)
        fr = cFr(parent, bg=PANEL_BG) ;fr._pack(px=4, py=10)

        for row, num1 in enumerate(range(1, 7)):
            fr1 = cFr(fr, W=20, H=30, bg=FRM_BG[num1], Rel=GR, bd=1)
            fr1._grid(R=row, C=0, Stk="nsew") ;fr1.pack_propagate(False)
            cLbl(fr1, text=num1, bg=FRM_BG[num1], fg=FRM_FG[num1], font=(MUI,9,BD))._pack(Exp=True)

            key   = (num1,)
            label = f"{title}        {num1}    "
            self._grid_data_cell(fr, bet_type, 80, ROW_H, row, 1, data,  key, label)

    #-----------------------------------
    def _grid_data_cell(self, fr, bet_type, W, H, row, col, data, key, label, span=1):

        odds = data.get(key, "").replace("-", " - ")
        cut  = self._is_cut(key, bet_type)
        high = bool(odds) and parse_odds_min(odds) >= HIGH_THRESH[bet_type]

        if odds == "欠場": cell_bg, cell_fg = CUT_BG, "black"
        elif cut:          cell_bg, cell_fg = CUT_BG, CUT_FG
        else:              cell_bg, cell_fg = NORM_BG, "#CC0000" if high else "#222222"

        cell = cFr(fr, bg=cell_bg, W=W, H=H, Bd=(1,GR))
        cell.pack_propagate(False)
        cell._grid(R=row, C=col, Cspan=span, Stk="nsew")
        lb = cLbl( cell, text=odds, bg=cell_bg, fg=cell_fg, font=(MUI,10),
                    Anc="e", cursor="hand2" if (odds and not cut) else ""  )
        lb._pack(fill="both", expand=True, px=3)

        self._register_grid_item(bet_type, key, label, cell, lb)

    #-----------------------------------
    def _is_cut(self, combo_key:tuple, bet_type:str) -> bool:

            allowed = {}
            for pos in (1, 2, 3):
                if self.formation.get(7, {}).get(pos):
                    pos_allowed = list(range(1, 7))
                else:
                    pos_allowed = [b for b in range(1, 7) if self.formation.get(b, {}).get(pos)]
                allowed[pos] = pos_allowed if pos_allowed else list(range(1, 7))
            is_formation_ok = False

            if   bet_type == "3T":
                r1, r2, r3 = combo_key
                is_formation_ok = (r1 in allowed[1] and r2 in allowed[2] and r3 in allowed[3])
            elif bet_type == "2T":
                r1, r2 = combo_key
                is_formation_ok = (r1 in allowed[1] and r2 in allowed[2])
            elif bet_type == "TT":
                is_formation_ok = (combo_key[0] in allowed[1])
            elif bet_type == "3F":
                from itertools import permutations
                is_formation_ok = any(p[0] in allowed[1] and p[1] in allowed[2] and p[2] in allowed[3] 
                                     for p in permutations(combo_key))
            elif bet_type == "2F":
                r1, r2 = combo_key
                is_formation_ok = (r1 in allowed[1] and r2 in allowed[2]) or (r2 in allowed[1] and r1 in allowed[2])
            elif bet_type == "KK":
                r1, r2 = combo_key
                patterns = [(1,2), (2,1), (1,3), (3,1), (2,3), (3,2)]
                is_formation_ok = any(r1 in allowed[p[0]] and r2 in allowed[p[1]] for p in patterns)
            elif bet_type == "FF":
                r1 = combo_key[0]
                is_formation_ok = (r1 in allowed[1] or r1 in allowed[2] or r1 in allowed[3])

            if not is_formation_ok: return True

            combo_set       = set(combo_key)
            remaining_slots = 3 -len(combo_set)

            must_and_targets = {b for b in range(1, 7) if self.mustin.get(b, {}).get(1)}
            needed_and       = must_and_targets - combo_set
            if len(needed_and) > remaining_slots:
                return True

            must_or_targets = {b for b in range(1, 7) if self.mustin.get(b, {}).get(2)}
            if must_or_targets and not (must_or_targets & combo_set):
                return True

            return False

    #================= ベットテーブル更新 ==================
    def _refresh_tree(self):

        for w in self._tbl_inner.winfo_children(): w.destroy()
        self.tbl_rows.clear()

        valid_odds = []

        for ri, row_data in enumerate(self.selected):
            bt, key, label = row_data[0], row_data[1], row_data[2]
            alloc_str      = row_data[3] if len(row_data) > 3 else ""
            odds_str       = self._current_odds_str(bt, key)

            v = parse_odds_min(odds_str)
            if v > 0: valid_odds.append(v)

            row_bg = TBL_BG if ri % 2 == 0 else ALT_BG

            sep = cFr(self._tbl_inner, bg=SEP_C, H=1)
            sep._grid(R=ri*2, C=0, Cspan=6, Stk="ew")

            row_fr = cFr(self._tbl_inner, bg=row_bg, H=CELL_H)
            row_fr._grid(R=ri*2+1, C=0, Stk="ew") ;row_fr.grid_propagate(False)

            for ci, (_, w, _) in enumerate(self._COL_DEF):
                row_fr.Cconf(ci, minsize=w, W=0)

            cBtn( row_fr, text="×", font=(GUI,8,BD), fg="#CC2222", bg=row_bg, Rel=GR, bd=1,
                  command=lambda bt_=bt, key_=key:self._delete_row(bt_, key_) 
                 )._grid(R=0, C=0, Stk=ALL)

            cLbl( row_fr, text=self._type_label(bt), bg=row_bg, font=(MUI,9), Anc=CT
                 )._grid(R=0, C=1, Stk=ALL)

            combo_txt = label.split(" ",1)[1] if " " in label else label
            cLbl( row_fr, text=combo_txt, bg=row_bg, font=(MUI,9), Anc=CT
                 )._grid(R=0, C=2, Stk=ALL)

            cLbl( row_fr, text=f"{odds_str}      x", bg=row_bg, font=(MUI,10), Anc=CT, px=4
                 )._grid(R=0, C=3, Stk="e")

            alloc_var = tk.StringVar(value=alloc_str)
            ent       = tk.Entry( row_fr, width=1, textvariable=alloc_var, font=(MUI,10),
                                  justify="right", relief=GR, bd=1, bg="#FFFEF0"     )
            ent.grid(row=0, column=4, sticky=ALL, padx=(3,0), pady=2)

            cLbl( row_fr, text="00 円  =", bg=row_bg, font=(MUI,9), Anc="sw")._grid(R=0, C=5, Stk=ALL)

            ret_lbl = cLbl(row_fr, text="", bg=row_bg, font=(MUI,10), Anc=CT)
            ret_lbl._grid(R=0, C=6, Stk=ALL, px=(0.10))

            if alloc_str:
                try:
                    amt = int(alloc_str) *100
                    ret_lbl.config(text=f"{round(amt * parse_odds_min(odds_str)):,} 円   ")
                except: pass
            #-----------------
            def _on_alloc_change(*a, idx_=ri, av=alloc_var, os_=odds_str, rl=ret_lbl):
                raw = av.get()
                try:
                    amt = int(raw) *100
                    rl.config(text=f"{round(amt * parse_odds_min(os_)):,} 円   ")
                except:
                    rl.config(text="")

                if idx_ < len(self.selected):
                    old_ = self.selected[idx_]
                    self.selected[idx_] = (old_[0], old_[1], old_[2], av.get())
                self._update_total_bet()
            #-----------------
            alloc_var.trace_add("write", _on_alloc_change)

            self.tbl_rows.append((alloc_var, ret_lbl, bt, key, odds_str))

        if self.selected:
            cFr( self._tbl_inner, bg=SEP_C, H=1
                )._grid(row=len(self.selected)*2, C=0, Cspan=6, Stk="ew")

        self._tbl_inner.grid_columnconfigure(0, minsize=sum(w for _, w, _ in self._COL_DEF))

        self.lbl_count.config(text=f"{len(self.selected)} 点")
        self._update_total_bet()

        if valid_odds:
            sv = synthetic_odds(valid_odds)
            color = "red" if sv <= 1.0 else ("#FFD700" if sv <= 1.5 else "#00DD88")
            self.lbl_synth.config(text=f"{sv:.1f}", fg=color, font=(MUI,11))
        else:
            self.lbl_synth.config(text="ーー.ー", fg="white", font=(MUI,10))

    #-----------------------------------
    def _type_label(self, bt:str) -> str:

        return {  "TT":"単勝",  "FF":"複勝", "KK":"拡連複",
                  "2T":"2連単", "2F":"2連複",
                  "3F":"3連複", "3T":"3連単"                }.get(bt, bt)
    #-----------------------------------
    def _update_total_bet(self):

        total  = 0
        divids = []

        for alloc_var, ret_lbl, bt, key, odds_str in self.tbl_rows:
            raw = alloc_var.get()
            try:
                amt = int(raw) *100
                total += amt
                ret_val = round(amt * parse_odds_min(odds_str))
                divids.append(ret_val)
            except: pass

        self.total_bet.config(text=f"{total:,} 円" if total else "")

        if divids:
            hi = max(divids)
            lo = min(divids)
            self.high_divid.config(text=f"{hi:,} 円")
            self.low_divid.config( text=f"{lo:,} 円")
            hi_m = hi - total
            lo_m = lo - total
            hi_fg = "#00DD88" if hi_m >= 0 else "#FF6666"
            lo_fg = "#00DD88" if lo_m >= 0 else "#FF6666"
            self.high_marjin.config(text=f"{hi_m:+,} 円", fg=hi_fg)
            self.low_marjin.config( text=f"{lo_m:+,} 円", fg=lo_fg)
        else:
            self.high_divid.config( text="")
            self.low_divid.config(  text="")
            self.high_marjin.config(text="", fg=HDR_FG)
            self.low_marjin.config( text="", fg=HDR_FG)

    #==================== 選択トグル =======================
    def _refresh_grid_cells(self):

        self.cell_refs.clear()

        for ref_key, meta in self.grid_items.items():
            bt      = meta["bet_type"]
            key     = meta["key"]
            cell    = meta["cell"]
            lb      = meta["label"]
            odds_str = self._current_odds_str(bt, key)
            cut      = self._is_cut(key, bt)

            if odds_str == "欠場":
                cell_bg, cell_fg = CUT_BG, "black"
            elif cut:
                cell_bg, cell_fg = CUT_BG, CUT_FG
            else:
                high    = bool(odds_str) and parse_odds_min(odds_str) >= HIGH_THRESH[bt]
                cell_bg = NORM_BG
                cell_fg = "#CC0000" if high else "#222222"

            if any(s[0] == bt and s[1] == key for s in self.selected):
                cell_bg = HIL_BG
            elif self._is_linked_3T_from_3F(bt, key):
                cell_bg = INCLUDE_BG

            cell.config(bg=cell_bg)
            lb.config( bg=cell_bg, fg=cell_fg, text=odds_str,
                       cursor=("hand2" if (odds_str and not cut) else "") )
            self._bind_grid_item(bt, key, meta["title"], cell, lb, bool(odds_str and not cut))
    #-----------------------------------
    def _bind_grid_item(self, bet_type:str, key:tuple, label:str, cell, lb, active:bool):

        ref_key = (bet_type, key)
        cell.unbind("<Button-1>")
        lb.unbind("<Button-1>")

        if active:
            self.cell_refs[ref_key] = (cell, lb, NORM_BG)
            #------------
            def _on_click(e, bt=bet_type, k=key, lbl=label):
                self._toggle_select(bt, k, lbl)
            #------------
            cell.bind("<Button-1>", _on_click)
            lb.bind("<Button-1>", _on_click)
    #-----------------------------------
    def _toggle_select(self, bet_type:str, key:tuple, label:str):

        existing = [ (i, s) for i, s in enumerate(self.selected)
                     if s[0] == bet_type and s[1] == key ]

        if existing:
            idx, _ = existing[0]
            self.selected.pop(idx)
        else:
            self.selected.append((bet_type, key, label, ""))

        self._refresh_grid_cells()
        self._refresh_tree()
    #-----------------------------------
    def _normalize_key(self, bet_type:str, key:tuple):

        if bet_type in ("2F", "3F", "KK"):
            return tuple(sorted(key))

        return tuple(key)
    #-----------------------------------
    def _current_odds_str(self, bet_type:str, key:tuple) -> str:

        key_n = self._normalize_key(bet_type, key)

        if bet_type in ("TT", "FF"):
            v = self.odds_data.get(bet_type, {}).get(key_n[0], "")
            return v.replace("-", " - ") if isinstance(v, str) else ""

        src = self.odds_data.get(bet_type, {})
        if key in src:                    v = src.get(key, "")
        elif key_n in src:                v = src.get(key_n, "")
        elif tuple(reversed(key)) in src: v = src.get(tuple(reversed(key)), "")
        else:                             v = ""

        return v if isinstance(v, str) else ""
    #-----------------------------------
    def _is_linked_3T_from_3F(self, bet_type:str, key:tuple) -> bool:

        if bet_type != "3T" or len(key) != 3:
            return False

        key_set = set(key)

        for s in self.selected:
            if s[0] == "3F" and len(s[1]) == 3 and set(s[1]) == key_set:
                return True

        return False
    #-----------------------------------
    def _register_grid_item(self, bet_type:str, key:tuple, label:str, cell, lb):

        self.grid_items[(bet_type, key)] = { "cell":cell, "label":lb, "bet_type":bet_type,
                                              "key":key,  "title":label                    }

    # ----------------------------------
    def _update_Players(self, date:str, venue_id:int, race_no:int):

        c             = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row

        sql = """
            SELECT rp.frame_no      AS fr_no,
                   p.name           AS name
              FROM players p
              JOIN Race_programs rp ON p.player_id = rp.player_id
             WHERE rp.date     =?
               AND rp.venue_id =? 
               AND rp.race_no  =?
          ORDER BY frame_no
             """
        rows         = c.execute(sql, (date, venue_id, race_no)).fetchall()
        self.players = {i:p for i, p in rows} if rows else {}

        c.close()
    # ----------------------------------
    def _fetch_deadline(self, date:str, venue_id:int, race_no:int):

        c             = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row

        sql = """
            SELECT deadline_vote AS dline
              FROM Race_programs
             WHERE date     =?
               AND venue_id =? 
               AND race_no  =?
             """
        out = c.execute(sql, (date, venue_id, race_no)).fetchone()
        c.close()

        return out

    # ======================== 購入ダイアログ ========================
    def _open_purchase_dialog(self):

        if not self.selected:
            tk.messagebox.showwarning("購入", "購入対象が選択されていません。")
            return

        no_amount = [s[2] for s in self.selected
                     if not (len(s) > 3 and s[3].strip())]
        if no_amount:
            msg = "金額未入力の組み合わせがあります:\n"
            msg += "\n".join(no_amount[:5])
            if len(no_amount) > 5:
                msg += f"\n…他 {len(no_amount)-5} 件"
            tk.messagebox.showwarning("金額未入力", msg)
            return

        dlg = tk.Toplevel(self)
        dlg.title("自動購入 設定")
        dlg.geometry("430x360+2100+700")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(bg="#f5f5f5")

        cLbl( dlg, text="テレボート 自動購入", font=(GUI,13,BD), bg="#1a5276", fg="white"
             ).pack(fill="x", ipady=8)

        frm = cFr(dlg, bg="#f5f5f5", px=24, py=16) ;frm.pack(fill="both", expand=True)
        #-----------
        def make_row(row, label, show=""):
            cLbl( frm, text=label, font=(MUI,10), bg="#f5f5f5", anchor="w", width=16
                 ).grid(row=row, column=0, sticky="w", pady=5)
            ent = tk.Entry(frm, width=22, font=(MUI,10), show=show, relief=SD, bd=1)
            ent.grid(row=row, column=1, sticky="w", padx=4)
            return ent
        #-----------
        ent_kanyusha = make_row(0, "加入者番号")
        ent_ansyo    = make_row(1, "暗証番号",         show="●")
        ent_authpw   = make_row(2, "認証用パスワード", show="●")
        ent_betpw    = make_row(3, "購入用パスワード", show="●")

        ent_kanyusha.insert(0, os.environ.get("MBRACE_KANYUSHA", ""))
        ent_ansyo.insert(   0, os.environ.get("MBRACE_ANSYO",    ""))
        ent_authpw.insert(  0, os.environ.get("MBRACE_AUTHPW",   ""))
        ent_betpw.insert(   0, os.environ.get("MBRACE_BETPW",    ""))

        # オプション
        opt_frm = tk.Frame(frm, bg="#f5f5f5")
        opt_frm.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 4))

        dry_var      = tk.BooleanVar(value=True)
        headless_var = tk.BooleanVar(value=False)

        tk.Checkbutton( opt_frm, text="ドライラン（確認まで・購入なし）",
                             variable=dry_var, bg="#f5f5f5", font=(MUI,9) ).pack(anchor="w")

        tk.Checkbutton( opt_frm, text="ヘッドレス（ブラウザ非表示）",
                        variable=headless_var, bg="#f5f5f5", font=(MUI,9) ).pack(anchor="w")

        # 件数・金額サマリ
        n_bets    = sum(1 for s in self.selected if len(s) > 3 and s[3].strip())
        total_yen = 0

        for s in self.selected:
            try:
                total_yen += int(s[3].replace(",", "")) * 100
            except Exception:
                pass

        cLbl( frm, text=f"購入対象  {n_bets} 件   合計  {total_yen:,} 円",
              font=(MUI,10,BD), bg="#f5f5f5", fg="#1a5276" )._grid(R=5, C=0, Cspan=2, py=(6, 4))

        # ボタン
        btn_frm = cFr(frm, bg="#f5f5f5") ;btn_frm._grid(R=6, C=0, Cspan=2, py=8)
        #-----------
        def _start():
            k  = ent_kanyusha.get().strip()
            a  = ent_ansyo.get().strip()
            ap = ent_authpw.get().strip()
            bp = ent_betpw.get().strip()
            if not all([k, a, ap, bp]):
                tk.messagebox.showwarning("入力不足", "全項目を入力してください。", parent=dlg)
                return
            dlg.destroy()
            self._run_purchase(k, a, ap, bp, dry_run=dry_var.get(), headless=headless_var.get())
        #-----------
        cBtn( btn_frm, text="購入開始", width=14, bg="#1a5276", fg="white", font=(MUI,10,BD),
                          relief="flat", cursor="hand2", Com=_start ).pack(side="left", padx=6)

        cBtn( btn_frm, text="キャンセル", width=10, font=(MUI,10),
                    relief="flat", cursor="hand2", Com=dlg.destroy ).pack(side="left", padx=6)

    #-----------------------------------
    def _run_purchase( self, kanyu_no:str, ansyo_no:str, auth_pw:str, bet_pw:str,
                                                      dry_run:bool, headless:bool ):

        prog = tk.Toplevel(self)
        prog.title("購入処理中...")
        prog.geometry("280x80+2000+600")
        prog.resizable(False, False)
        prog.grab_set()
        cLbl(prog, text="ログイン・購入処理中...", font=(MUI,10), py=16).pack()

        def _worker():
            buyer = None
            try:
                buyer = SeleniumBuyer( kanyusha_no = kanyu_no,
                                       ansyo_no    = ansyo_no,
                                       auth_pw     = auth_pw,
                                       bet_pw      = bet_pw,
                                       headless    = headless,
                                       timeout     = 10,          )

                buyer.login(venue_id=self.venue_id)

                result = buyer.purchase_all( selected = self.selected,
                                             date_str = self.date,
                                             venue_id = self.venue_id,
                                             race_no  = self.race_no,
                                             dry_run  = dry_run,        )

                self.after(0, lambda r=result: self._show_purchase_result(r, prog))

            except LoginError as e:
                self.after(0, lambda e=e: ( prog.destroy(),
                                            tk.messagebox.showerror("ログインエラー", str(e) ) ))
            except ValueError as e:
                self.after(0, lambda e=e: ( prog.destroy(),
                                            tk.messagebox.showerror("設定エラー", str(e) ) )) 
            except Exception as e:
                self.after(0, lambda e=e: ( prog.destroy(),
                                            tk.messagebox.showerror(
                                                         "エラー", f"{type(e).__name__}: {e}" ) ))
            finally:
                if buyer: buyer.shutdown()

        th = threading.Thread(target=_worker, daemon=True)
        th.start()

    #-----------------------------------
    def _show_purchase_result(self, result:dict, prog_dlg=None):

        if prog_dlg:
            try:              prog_dlg.destroy()
            except Exception: pass

        s = result["success"]
        f = result["failed"]
        k = result["skipped"]

        lines = []
        if s:
            lines.append(f"購入 成功  {len(s)} 件")
            lines += [f"   {x}" for x in s]
        if f:
            lines.append(f"購入 失敗  {len(f)} 件")
            lines += [f"   {x}" for x in f]
        if k:
            lines.append(f"購入 スキップ  {len(k)} 件（金額未入力）")

        msg = "\n".join(lines) if lines else "処理対象がありませんでした。"

        if f:
            tk.messagebox.showwarning("購入結果（一部失敗）", msg)
        else:
            tk.messagebox.showinfo("購入結果", msg)

#=================== エントリポイント ======================
def main():

    parser = argparse.ArgumentParser(description="ボートレース オッズウィンドウ")
    parser.add_argument("--date",  required=True,           help="YYYY-MM-DD")
    parser.add_argument("--venue", required=True, type=int, help="会場ID 1-24")
    parser.add_argument("--race",  required=True, type=int, help="レース番号 1-12")
    parser.add_argument("--interval", default=1,  type=int, help="更新間隔(分)")
    args = parser.parse_args()

    app = OddsWindow( date         = args.date,
                      venue_id     = args.venue,
                      race_no      = args.race,
                      interval_min = args.interval, )
    app.mainloop()

if __name__ == "__main__":
    main()