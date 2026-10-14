# -*- coding: utf-8 -*-
# C:\boatrace\UI\Window\race_window.py

import tkinter as tk
import subprocess, sys, json
from tkinter  import ttk, messagebox
from datetime import datetime as dt, date, time, timedelta, timezone
from pathlib  import Path

import Dal as dal

from Helpers.build_rows       import query_program, make_rows, make_sub_rows
from Helpers.queries          import Query
from Helpers.build_series_idx import update_series_idx, build_day_lbl
from Helpers.sub_window       import open_player_picker
from Helpers.Custum_func      import cFr, cLbl, cBtn
from Widgets.center_widgets   import framing_center_widgets
from Widgets.placeholder      import build_main_placeholder, build_sub_placeholder
from Widgets.widgets          import ( framing_graph, framing_figure, framing_weather,
                                       clear_widgets, apply_absent_bg, set_player_image, )

# ====================================================================
APP_TITLE = ""

ODDS_WINDOW    = r"C:\boatrace\UI\odds_window.py"
RESULTS_WINDOW = r"C:\boatrace\UI\results_window.py"

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"

MAIN_BG   = "#F0F4FA"  #"SystemButtonFace"

VENUES    = [ "桐生",  "戸田",  "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",  "津",
              "三国", "びわこ", "住之江",  "尼崎",   "鳴門",   "丸亀",  "児島", "宮島", "徳山",
              "下関",  "若松",   "芦屋",   "福岡",   "唐津",   "大村",                         ]
VENUE_ID  = { name: i+1 for i, name in enumerate(VENUES) }

GRADE_IDX = { 0:"一般", 1:"G3", 2:"G2", 3:"G1", 4:"PG1", 5:"SG" }

FRM_COLOR = { 1: dict(bg="#FFFFFF", fg="#000000"),
              2: dict(bg="#000000", fg="#FFFFFF"),
              3: dict(bg="#D40000", fg="#FFFFFF"),
              4: dict(bg="#0066CC", fg="#FFFFFF"),
              5: dict(bg="#FFD400", fg="#000000"),
              6: dict(bg="#008A2E", fg="#FFFFFF"), }

CLS_COLOR = { "A1": dict(fill="#74b7ff"),
              "A2": dict(fill="#afffaf"),
              "B1": dict(fill="#dedede"),
              "B2": dict(fill="#ffbfbf"), }

RATE_OPT  = { 0:{"font":(MUI,8,BD), "fg":"black"},
              1:{"font":(MUI,8,BD), "fg":"blue" },
              2:{"font":(MUI,8,BD), "fg":"red"  }  }

ST_OPT    = { 0:{"font":(MUI,8,BD), "fg":"black"},
              1:{"font":(MUI,8,BD), "fg":"blue" },
              2:{"font":(MUI,8,BD), "fg":"red"  }  }

FAULT_OPT = { 0:{"font":(MUI, 8   ),"fg":"black"},
              1:{"font":(MUI, 9,BD),"fg":"red"  }, 
              2:{"font":(MUI, 9,BD),"fg":"red"  }, 
              3:{"font":(MUI, 9,BD),"fg":"red"  }, } 

# ===========  共通ヘルパー  ===========
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
def days_ago(d:str, range:int)-> str:

    d = to_date(d)

    return to_str(d -timedelta(days=range))

# ----------------------------
def wid_txt(s:str) -> str:

    hair = "\u200A" 
    return hair.join(list(s))

# =====================   出走表ウィンドウ  ==========================
# --------------------------------------------------------------------
class RaceWindow(tk.Toplevel):

    def __init__(self, master, app, d_iso:str, venue_id:int, range_d:int=270, sub_window:bool=False):
        super().__init__(master)

        self.geometry("1220x1400+75+0")
        self.resizable(False, False)

        self.app         = app
        self.date        = d_iso
        self.venue_id    = venue_id
        self.race_no     = 1
        self.date_to     = d_iso
        self.date_from   = days_ago(d_iso, range_d)
        self.vrange_d    = 1100
        self.last_date   = None
        self.last_race   = None
        self.wdgt_no     = 1
        self.sub_window  = [sub_window, 0]
        self.frame_order = [1,2,3,4,5,6]
        self.entry_rows  = []
        self.entry_prg   = {}
        self.clock_id    = None
        self.is_absent   = []

        self.flying      = False
        self.not_flying  = False
        self.exclude_edo = True if venue_id != 3 else False
        self.on_mark     = True
        self.limited_grade = False
        self.s_lane      = 0
        self.disp_oriten = False
        self.disp_parts  = True
        self.figB_result = False

        self.lane_managers = {}

        self._odds_proc    = None
        self._results_proc = None

        self.protocol("WM_DELETE_WINDOW", self._on_rw_close)

        self.overall = self._from_json(self.date, excld=self.exclude_edo)

        root = cFr(self, width=1220, height=1400, padx=10,)
        root._grid(R=0, C=0) ;root.Pgate()

        if sub_window: self._start_odds_proc()

        # Header =======================
        hdr1   = cFr(root,  W=1130, H=30, px=10) ;hdr1._grid(  R=0, C=0,          Stk="w") ;hdr1.Pgate()
        hdr2   = cFr(root,  W=1130, H=30, px=10) ;hdr2._grid(  R=1, C=0,          Stk="w") ;hdr2.Pgate()
        btns   = cFr(root,  W= 70,  H=60)        ;btns._grid(  R=0, C=1, Rspan=2, Stk="e") ;btns.Pgate()

        hdr1L  = cFr(hdr1,  W=400,  H=30)        ;hdr1L._grid( R=0, C=0)  ;hdr1L.Pgate()
        hdr1R  = cFr(hdr1,  W=810,  H=30)        ;hdr1R._grid (R=0, C=1)  ;hdr1R.Pgate()
        hdr2L  = cFr(hdr2,  W=400,  H=30)        ;hdr2L._grid( R=0, C=0)  ;hdr2L.Pgate()
        hdr2R  = cFr(hdr2,  W=810,  H=30)        ;hdr2R._grid( R=0, C=1)  ;hdr2R.Pgate()
        hdr1LA = cFr(hdr1L, W=45,   H=30)        ;hdr1LA._grid(R=0, C=0) ;hdr1LA.Pgate()
        hdr1LB = cFr(hdr1L, W=300,  H=30)        ;hdr1LB._grid(R=0, C=1) ;hdr1LB.Pgate()
        hdr1LC = cFr(hdr1L, W=55,   H=30)        ;hdr1LC._grid(R=0, C=2) ;hdr1LC.Pgate()
        hdr2LA = cFr(hdr2L, W=70,   H=30)        ;hdr2LA._grid(R=0, C=0) ;hdr2LA.Pgate()
        hdr2LB = cFr(hdr2L, W=60,   H=30)        ;hdr2LB._grid(R=0, C=1) ;hdr2LB.Pgate()
        hdr2LC = cFr(hdr2L, W=50,   H=30)        ;hdr2LC._grid(R=0, C=2) ;hdr2LC.Pgate()
        hdr2LD = cFr(hdr2L, W=120,  H=30)        ;hdr2LD._grid(R=0, C=3) ;hdr2LD.Pgate()
        hdr2LE = cFr(hdr2L, W=100,  H=30)        ;hdr2LE._grid(R=0, C=4) ;hdr2LE.Pgate()

        self.lb_1LA = cLbl(hdr1LA, Anc=CT, font=(MUI,10,BD)); self.lb_1LA._grid(Stk=ALL)
        self.lb_1LB = cLbl(hdr1LB,         font=(MUI,10,BD)); self.lb_1LB._grid(Stk=ALL)
        self.lb_1LC = cLbl(hdr1LC, Anc=CT, font=(MUI, 9,BD)); self.lb_1LC._grid(Stk=ALL)
        self.lb_2LA = cLbl(hdr2LA,         font=(MUI,10))   ; self.lb_2LA._grid(Stk=ALL)
        self.lb_2LB = cLbl(hdr2LB,         font=(MUI,10,BD)); self.lb_2LB._grid(Stk=ALL)
        self.lb_2LC = cLbl(hdr2LC,         font=(MUI,10,BD)); self.lb_2LC._grid(Stk=ALL)
        self.lb_2LD = cLbl(hdr2LD,         font=(MUI,10))   ; self.lb_2LD._grid(Stk=ALL)
        self.lb_2LE = cLbl(hdr2LE,         font=(MUI, 9,BD)); self.lb_2LE._grid(Stk=ALL)

        self._mk_day_buttons (hdr1R)
        self._mk_race_buttons(hdr2R)

        bg  = "#F1EE62" if self.sub_window[0] else "#ececec"
        rel = SK        if self.sub_window[0] else RA

        self.bt_change_sub = cBtn( btns, text=" SUB 切替 ",     W=8,  font=(MUI,8), Rel=RA,
                                   bg="#e1f2ff", px=3,
                                   Com=lambda:self._change_sub_window() )
        self.bt_toggle_sub = cBtn( btns, text=wid_txt(" ODDS "), W=8, font=(MUI,8), Rel=rel,
                                   bg=bg, px=3,
                                   Com=lambda:self._toggle_sub_window(d_iso, venue_id, 1) )

        self.bt_change_sub._grid(R=0, C=0, py=(0,3), Stk="e")
        self.bt_toggle_sub._grid(R=1, C=0, py=(2,0), Stk="e")

        # Body(Main/Sub) ===============
        body = cFr(root, W=1200, H=1340); body._grid(R=2, C=0, Cspan=2); body.Pgate()

        self.frm_main = cFr(body, W=1200, H=1002)
        self.frm_sub  = cFr(body, W=1200, H= 318)

        self.frm_main._grid(R=0, C=0, pady=(2, 0)) ;self.frm_main.Pgate()
        self.frm_sub._grid (R=1, C=0, pady=(8,10)) ;self.frm_sub.Pgate()

        self.widgets_main: dict[int, dict[str, tk.Widget]] = {}
        self.widgets_sub:  dict[int, dict[str, tk.Widget]] = {}

        build_main_placeholder(self, self.frm_main)
        build_sub_placeholder (self, self.frm_sub)

        # 初期表示更新 ********
        self._reload_for(self.date, self.venue_id, self.race_no)
        self.app.bind_all("<Button-4>", self._assaign_button)

    #----------------- 日程切替 ボタン ---------------------
    def _mk_day_buttons(self, parent:tk.Frame):

        for child in parent.winfo_children(): child.destroy()

        self._day_btns = {}
        labels, _ = build_day_lbl(self.date, self.venue_id)

        for col, info in enumerate(labels):
            if not info["visible"]: continue

            d = info["date"]
            if   info["day_no"] == 1: txt = "初 日"
            elif info["final_day"]:   txt = "最終日"
            else:                     txt = f"{info['day_no']}日目"

            btn  = ttk.Button( parent, text=txt, width=8, style="hdr.TButton",
                               command=lambda d=d:self._reload_for(d, self.venue_id, 1) )
            btn.grid(row=0, column=col, padx=2)

            self._day_btns[d] = btn

            if col >= 9: break

        self._highright_D_btn(d)

    #----------------- レース切替ボタン --------------------
    def _mk_race_buttons(self, parent:ttk.Frame):

        for child in parent.winfo_children(): child.destroy()

        self._race_btns = []

        for r in range(1,13):
            btn = ttk.Button( parent, text=f"{r}Ｒ", style="hdr.TButton", width=6,
                              command=lambda r=r:self._reload_for(self.date, self.venue_id, r) )
            btn.grid(row=0, column=r-1, padx=1, pady=0)

            self._race_btns.append(btn)

        self._highright_R_btn(1)
    # ----------------------------------
    def _highright_D_btn(self, d_iso:str):

        for key, btn in self._day_btns.items():
            if key == d_iso : btn.state(['pressed'])
            else:             btn.state(['!pressed'])
    # ----------------------------------
    def _highright_R_btn(self, on:int):
    
        for idx, btn in enumerate(self._race_btns, start=1):
            if on == idx: btn.state(['pressed'])
            else:         btn.state(['!pressed'])
    # ----------------------------------
    def _assaign_button(self, event):

        self._reload_for(self.last_date, self.venue_id, self.last_race)

    #------------- サブ画面表示/非表示 ボタン --------------
    def _toggle_sub_window(self, d_iso:str, venue_id:int, race_no:int):

        if self.sub_window[0] == False:
            # ------ 表示 ON ------
            self.sub_window[0] = True
            self.bt_toggle_sub.config(bg="#F1EE62", relief=SK)

            if self.sub_window[1] == 0:
                if self._odds_proc and self._odds_proc.poll() is None:
                    self._send_odds_command({ "state":"deiconify",
                                               "date":d_iso,
                                              "venue":venue_id,
                                               "race":race_no     })
                else: self._start_odds_proc()

            else:
                if self._results_proc and self._results_proc.poll() is None:
                    self._send_results_command({ "state":"deiconify",
                                                   "date":d_iso,
                                                  "venue":venue_id     })
                else: self._start_results_proc()

        else:
            # ------ 表示 OFF ------
            self.sub_window[0] = False
            self.bt_toggle_sub.config(bg="#ececec", relief=RA)

            if self.sub_window[1] == 0:
                if self._odds_proc and self._odds_proc.poll() is None:
                    self._send_odds_command({"state":"withdraw"})
            else:
                if self._results_proc and self._results_proc.poll() is None:
                    self._send_results_command({"state":"withdraw"})

    #---------------- odds subprocess 起動 -----------------
    def _start_odds_proc(self):

        try:
            self._odds_proc = subprocess.Popen(
                [ sys.executable, ODDS_WINDOW, "--date", self.date,
                                              "--venue", str(self.venue_id),
                                               "--race", str(self.race_no),  ],
                          stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                           text=True,
                        bufsize=1,
                  creationflags=0x00000200,                                    )

            self._send_odds_command( {   "date":self.date,
                                        "venue":self.venue_id,
                                         "race":self.race_no,
                                        "state":"deiconify"        } )

        except Exception as e:
            messagebox.showerror("odds_window 起動エラー", str(e))
            self.sub_window[0] = False
            self.bt_toggle_sub.config(bg="#ececec", relief=RA)
            return

    #--------------- 標準入力へコマンド送信 ----------------
    def _send_odds_command(self, cmd:dict):

        if self._odds_proc and self._odds_proc.poll() is None:
            try:
                if self._odds_proc.stdin:
                    self._odds_proc.stdin.write(json.dumps(cmd, ensure_ascii=False) + "\n")
                    self._odds_proc.stdin.flush()

            except Exception as e:
                print(f"[WARN] _send_odds_command: {e}")

    #--------------- results subprocess 起動 ---------------
    def _start_results_proc(self):

        try:
            self._results_proc = subprocess.Popen(
                [ sys.executable, RESULTS_WINDOW, "--date",  self.date,
                                                  "--venue", str(self.venue_id), ],
                          stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                           text=True,
                        bufsize=1,
                  creationflags=0x00000200,                                    )

            self._send_results_command( {   "date":self.date,
                                           "venue":self.venue_id,
                                           "state":"deiconify"         } )

        except Exception as e:
            messagebox.showerror("results_window 起動エラー", str(e))
            self.sub_window[0] = False
            self.bt_toggle_sub.config(bg="#ececec", relief=RA)
            return

    #-------------- 標準入力へコマンド送信 -----------------
    def _send_results_command(self, cmd:dict):

        if self._results_proc and self._results_proc.poll() is None:
            try:
                if self._results_proc.stdin:
                    self._results_proc.stdin.write(json.dumps(cmd, ensure_ascii=False) + "\n")
                    self._results_proc.stdin.flush()

            except Exception as e:
                print(f"[WARN] _send_results_command: {e}")

    #--------------- オッズ/結果 切替ボタン ----------------
    def _change_sub_window(self):

        if self.sub_window[1] == 0:
            self.sub_window[1] = 1
            self.bt_toggle_sub.config(text=" Ｒesults ")
            if self.sub_window[0]:
                self._stop_odds_proc()
                self._start_results_proc()
        else:
            self.sub_window[1] = 0
            self.bt_toggle_sub.config(text=" ОＤＤＳ ")
            if self.sub_window[0]:
                self._stop_results_proc()
                self._start_odds_proc()

    #-------------------- 並び変更API ----------------------
    def _frame_at_lane(self, lane:int, frame_no:int, update:bool=True):

        if lane not in (1,2,3,4,5,6) or frame_no not in (1,2,3,4,5,6): return

        src_idx = self.frame_order.index(frame_no)
        dst_idx = lane -1
        self.frame_order.pop(src_idx)
        self.frame_order.insert(dst_idx, frame_no)

        if update: 
            self._update_main_entries()
            update_series_idx(self, self.date, self.venue_id, self.race_no)
            self._update_sub_entries()

    #--------------- 表示/更新 エントリー ------------------
    def _reload_for(self, d_iso:str, venue_id:int, race_no:int, result:bool=False):

        self._highright_D_btn(d_iso)
        self._highright_R_btn(race_no)
        self.last_date                  = self.date
        self.last_race                  = self.race_no
        self.date                       = d_iso
        self.race_no                    = race_no
        self.venue_id                   = venue_id
        self.frame_order                = [1, 2, 3, 4, 5, 6]
        self.is_absent                  = []

        for ln, m in self.lane_managers.items(): m.reset_state(ln)

        if (self._odds_proc) and (self._odds_proc.poll() is None) and (not result):
            self._send_odds_command({"date":d_iso, "venue":venue_id, "race":race_no})
        if (self._results_proc) and (self._results_proc.poll() is None):
            self._send_results_command({"date":d_iso, "venue":venue_id})

        self._update_header()
        self._update_main_entries()
        update_series_idx(self, self.date, self.venue_id, self.race_no)
        self._update_sub_entries(result=result)

    #----------------- Header 表示/更新 --------------------
    def _update_header(self):

        self.entry_prg = query_program(self)
        prg            = self.entry_prg
        d              = to_date(prg['date'])

        self.lb_1LA.config(text=f" {GRADE_IDX[prg['grade']]}" if prg["grade"] != 0 else "")
        self.lb_1LB.config(text=f"{prg['series_title']}")
        self.lb_1LC.config(text=f"{prg['day_no']}日目")
        self.lb_2LA.config(text=f"{d.month} 月 {d.day} 日")
        self.lb_2LB.config(text=f"  {prg['vname']}")
        self.lb_2LC.config(text=f"{self.race_no}R")
        self.lb_2LD.config(text=f"{prg['race_title'].strip()}")
        self.lb_2LE.config(text=f"締切  {prg['deadline'].strftime('%H：%M')}")

    #-------------- widgets_Main 表示/更新 -----------------
    def _update_main_entries(self):

        clear_widgets(self, main=True, center_wdg=True)
        self.entry_rows, self.data_rows = make_rows(self)

        for lane in range(1, 7):

            if self.entry_rows[self.frame_order[lane-1]]["absn"]:
                self._frame_at_lane(6 -len(self.is_absent), frn, update=False)
                self.is_absent.append(frn)

            wdg_m = self.widgets_main[lane]
            wdg_s = self.widgets_sub[lane]
            frn   = self.frame_order[lane-1]
            row   = self.entry_rows[frn]
            d_row = self.data_rows[frn]

            home     = bool(self.entry_prg['h_reg'] == row['rgns'])
            regn_opt = dict(font=(MUI,9,BD), fill="blue") if home else dict(font=(MUI,9))
            flyg_opt = FAULT_OPT[row['flyg']]
            late_opt = FAULT_OPT[row['late']]
            vcnt_opt = dict(fill="red", font=(GUI,8)) if row['v_cnt'] < 10 else dict(fill="black", font=(GUI,8,BD))

            if         row["stav"]  == ""  : stav_opt = ST_OPT[0]
            elif float(row["stav"]) >= 0.2 : stav_opt = ST_OPT[2]
            elif float(row["stav"]) <= 0.12: stav_opt = ST_OPT[1]
            else:                            stav_opt = ST_OPT[0]

            if   row["rate1"] >= 33.3:      rate1_opt = RATE_OPT[1]
            elif row["rate1"] <= 10:        rate1_opt = RATE_OPT[2]
            else:                           rate1_opt = RATE_OPT[0]
            if   row["rate2"] >= 55:        rate2_opt = RATE_OPT[1]
            elif row["rate2"] <= 20:        rate2_opt = RATE_OPT[2]
            else:                           rate2_opt = RATE_OPT[0]
            if   row["rate3"] >= 70:        rate3_opt = RATE_OPT[1]
            elif row["rate3"] <= 30:        rate3_opt = RATE_OPT[2]
            else:                           rate3_opt = RATE_OPT[0]

            wdg_m["frno" ].config(text= str(frn),             **FRM_COLOR[frn])
            wdg_m["name" ].config(text= f"{row['name']}"                      )
            wdg_m["rate1"].config(text= f"{row['rate1']:.1f}",     **rate1_opt)
            wdg_m["rate2"].config(text= f"{row['rate2']:.1f}",     **rate2_opt)
            wdg_m["rate3"].config(text= f"{row['rate3']:.1f}",     **rate3_opt)
            wdg_m["late" ].config(text= f"L{row['late']}",         **late_opt )
            wdg_m["flyg" ].config(text= f"F{row['flyg']}",         **flyg_opt )
            wdg_m["stav" ].config(text= f"{wid_txt(row['stav'])}", **stav_opt )
            wdg_m["mo_av"].config(text= f"{wid_txt(row['mo_av'])}"            )
            wdg_m["bo_av"].config(text= f"{wid_txt(row['bo_av'])}"            )
            set_player_image(wdg_m["photo"], row.get("pid"), (112, 160))
            wdg_m["photo"].bind( "<Button-1>",lambda e, p=row["pid"], c=lane:
                                 self.app.open_p_analys(p, self.venue_id, self.date, c) )

            wdg_m["mo_av"].bind( "<Button-1>",lambda e, m=row["mo_no"], um=self.entry_prg["upd_m"]: 
                                 self.app.open_m_analys(m, self.venue_id, um)                      )

            wdg_m["cv1"].delete("all") ;wdg_m["cv2"].delete("all") ;wdg_m["cv3"].delete("all")

            for x, y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
               wdg_m["cv1"].create_text(23+x, 13+y, text=row["clss"], font=(CBR,12,BD), fill="white")

            wdg_m["cv1"].create_rectangle(8, 12, 42, 18, width=0, **CLS_COLOR[row["clss"]])
            wdg_m["cv1"].create_text( 23, 13, text=row["clss" ], font=(CBR,12,BD), fill="Black")
            wdg_m["cv1"].create_text( 72, 14, text=row["scav" ], font=(MUI, 9,BD), fill="Black")
            wdg_m["cv1"].create_text(132, 15, text=row["v_ave"], font=(MUI, 8,BD), fill="Black")
            wdg_m["cv1"].create_text(161, 15, text=f"/ {row["v_cnt"]}",              **vcnt_opt)
            wdg_m["cv2"].create_text( 23, 18, text=row["regp" ], font=(MUI, 9),    fill="Black")
            wdg_m["cv2"].create_text( 92, 17, text=row["pid"  ], font=(MUI, 9),    fill="Black")
            wdg_m["cv2"].create_text(160, 16, text=row["rgns" ],                      **regn_opt)
            wdg_m["cv3"].create_text( 23, 20, text=row["age"  ], font=(MUI, 9),    fill="Black")
            wdg_m["cv3"].create_text( 88, 20, text=row["heig" ], font=(MUI, 8),    fill="Black")
            wdg_m["cv3"].create_text(151, 20, text=row["wkg"  ], font=(MUI, 8),    fill="Black")

            f_l     = int(row["flyg"] or 0) + int(row["late"] or 0)
            cnt_opt = dict(fg="red" if row["cnt"][lane] < 10 else "black")

            wdg_s["frno"].config(text= str(frn), **FRM_COLOR[frn]        )
            wdg_s["name"].config(text= f"{row.get('name')}"              )
            wdg_s["flyg"].config(text= f"{f_l}" if f_l else ""           )
            wdg_s["cnt" ].config(text= f" / {row['cnt'][lane]}", **cnt_opt)

            framing_center_widgets(self, wdg_m["fr_Ctr"], lane, d_row, wdgt_no=self.wdgt_no)

            if bool(row["absn"]): apply_absent_bg(wdg_m["Lane"])

    #--------------- widgets_Sub 表示/更新 -----------------
    def _update_sub_entries(self, figA:bool=True, graph:bool=True, P_O:bool=True, figB:bool=True,
                             result:bool=False):

        clear_widgets(self, figA=figA, graph=graph, figB=figB)

        self.sub_rows = make_sub_rows(self)
        row           = self.sub_rows["befr"]
        ortn          = self.sub_rows["ortn"]
        prg           = self.entry_prg
        rowA          = {f:{"st":None} for f in range(1,7)}

        trn_list = [ (ortn[r]["accel"] or 0) + (ortn[r]["turn"] or 0) for r in range(1,7) ] 
        lap_list = [ ortn[r]["lap"] for r in range(1,7) if ortn[r]["lap"] ] 
        e_list   = [ row[r]["exhi"] for r in range(1,7) if row[r]["exhi"] ]
        min_trn  = min(trn_list) if trn_list else 0
        min_lap  = min(lap_list) if lap_list else 0
        fast_ex  = (sum(e_list) / len(e_list)) if e_list else 0

        for lane in range(1,7):

            frn             = self.frame_order[lane-1]
            rowA[frn]["st"] = self.data_rows[frn]["own"][lane]["st_ave"]
            cv              = self.widgets_sub[lane]["cnvs"] ;cv.delete("all")
            tilt            = row[frn]["tilt"] if row[frn]["tilt"] != -0.5 else "-"
            exhi            = f"{row[frn]['exhi']:.2f}" if row[frn]['exhi'] else ""

            if   float(row[frn]["exhi"] or 0) <= fast_ex -0.08: e_color="#0000ff"
            elif float(row[frn]["exhi"] or 0) >= fast_ex +0.10: e_color="red" 
            else:                                               e_color="black"

            self.widgets_sub[lane]["tilt"].config(text=f"{tilt}")
            self.widgets_sub[lane]["exhi"].config(text=wid_txt(exhi), fg=e_color)

            g_p = ("プロペラ","キャリボ","シャフト")
            if self.disp_parts:
                for n, p in enumerate(row[frn]["repr"]):
                    p_opt = dict(fill="red" if p in g_p else "black")
                    x     = 35 if n % 2 == 0 else 95

                    if   n < 2: cv.create_text(x, 21, text=f"{p}", font=(MUI,8), **p_opt)
                    elif n < 4: cv.create_text(x,  7, text=f"{p}", font=(MUI,8), **p_opt)
                    elif n < 6: cv.create_text(x, 35, text=f"{p}", font=(MUI,8), **p_opt)
            else:
                #-------------
                def get_grid_color(diff, max_d, worse):

                    if diff < 0:     diff = 0
                    if diff > max_d: diff = max_d

                    rg = int(0 + 255 *(diff / max_d))
                    bg = f"#{rg:02x}{rg:02x}ff"
                    fg = "red" if diff >= worse else "white" if rg < 130 else "black"

                    return bg, fg
                #-------------
                lap_val        = ortn[frn]["lap"] or 0
                trn_val        = (ortn[frn]["accel"] or 0) + (ortn[frn]["turn"] or 0)
                trn            = f"{trn_val:.2f}" if trn_val else None
                lap            = f"{lap_val:.2f}" if lap_val else None
                lap_bg, lap_fg = get_grid_color(lap_val -min_lap, 0.40, 1.00)
                trn_bg, trn_fg = get_grid_color(trn_val -min_trn, 0.25, 0.50)

                if exhi: cv.create_rectangle( 2, 1,  42, 41, fill="#f6f6f6", outline="")
                if lap:  cv.create_rectangle(45, 1,  94, 41, fill=lap_bg,    outline="")
                if trn:  cv.create_rectangle(97, 1, 143, 41, fill=trn_bg,    outline="")

                cv.create_text( 19, 21, text=exhi, font=(MUI,8,BD), fill=e_color)
                cv.create_text( 69, 21, text=lap,  font=(MUI,8,BD), fill=lap_fg )
                cv.create_text(118, 21, text=trn,  font=(MUI,8,BD), fill=trn_fg )
                
                cv.create_line(43, 0, 43, 44, fill="black", width=1)
                cv.create_line(95, 0, 95, 44, fill="black", width=1)

        wdg_hdr = self.widgets_sub[0]
        wspd    = row[0]["wspd"] or 0
        wave    = row[0]["wave"] or 0
        stab    = row[0]["stab"]
        lap     = row[0]["shlp"]
        m_pas   = ( to_date(self.date).month -int(prg["upd_m"]) )%12
        b_pas   = ( to_date(self.date).month -int(prg["upd_b"]) )%12
        vname   = "　 ".join(prg["vname"]) if len(prg["vname"]) < 3 else  prg["vname"]

        wdg_hdr["vname"].config(text=f"BR  {vname}" )
        wdg_hdr["w_typ"].config(text=f"{'　'.join(prg['w_typ'])} ")
        wdg_hdr["upd_m"].config(text=f" {m_pas}  ヶ月 ")
        wdg_hdr["upd_b"].config(text=f" {b_pas}  ヶ月 ")
        wdg_hdr["wspd" ].config(text=f"風 速  {wspd}  m", fg="red" if wspd >=5 else "black")
        wdg_hdr["wave" ].config(text=f"波 高  {wave} cm")
        wdg_hdr["stab" ].config(text="安 定 版 装着" if stab else "", bg="yellow" if stab else "white")
        wdg_hdr["shlp" ].config(text="周回短縮 1200m" if  lap else "", bg="yellow" if  lap else "white")
        wdg_hdr["deadl"].config(text=f"  {prg['deadline'].strftime('%H：%M')}  ")
        # --------------
        def _update_clock():

            if self.clock_id is not None:
                self.widgets_sub[0]["now"].after_cancel(self.clock_id)
                self.widgets_sub[0]["last"].config(font=(MUI,10,BD))

            _now = dt.now().strftime("%H : %M")
            last = int( (prg["deadline"] - dt.now()).total_seconds() )

            self.widgets_sub[0]["now"].config(text=f"  {_now}  ")

            if  300 <  last <= 1800:
                self.widgets_sub[0]["last"].config(text=f"{int(last / 60)} 分", fg="black")
            elif 60 <  last <=  300:
                self.widgets_sub[0]["last"].config(text=f"{int(last / 60)} 分", fg="red")                
            elif  0 <= last <=   60:
                self.widgets_sub[0]["last"].config(text=f"{int(last)     } 秒", fg="red")
            elif  0 >= last:
                self.widgets_sub[0]["last" ].config(text="投票 締切", fg="black", font=(MUI,8))
            else: self.widgets_sub[0]["last"].config(text="")

            self.clock_id = self.widgets_sub[0]["now"].after(1000, _update_clock)
        # --------------
        _update_clock()

        if graph: framing_graph( self, wdg_hdr["Graph"], self.frame_order, self.data_rows)
        if figA:  framing_figure(self, wdg_hdr["Fig_A"], self.frame_order, rowA=rowA)
        if figB:  self._update_figB(result)

    #-------------------------------------------------------
    def _update_figB(self, result:bool):

            row   = self.sub_rows["rslt"] if self.figB_result or result else self.sub_rows["befr"]
            order = [1,2,3,4,5,6]
            rowB = {f:{"st":None, "opt":{}, "wm":None} for f in range(1,7)}

            for frn in range(1, 7):
                rowB[frn]["st"] = row[frn]["s_adj"]
                cour            = row[frn]["cour"] or 6
                order[cour-1]   = frn

                if self.figB_result:
                    rank = row[frn]["finish"]
                    if isinstance(rank, int):
                        if rank == 1:
                            rank = row[frn].get("w_move", "")
                            rowB[frn]["opt"] = dict(text=rank, font=(HNH,10,BD), fill="blue")
                        else:
                            rowB[frn]["opt"] = dict(text=rank, font=(HNH,10,BD), fill="black")
                    else:   rowB[frn]["opt"] = dict(text=rank, font=(HNH,10,BD), fill="red")

            framing_figure(self, self.widgets_sub[0]["Fig_B"], order, rowB=rowB)
            framing_weather(self, self.widgets_sub[0]["wthr"], self.widgets_sub[0]["wdir"], row)

    # --------------- ウィンドウ終了処理 -------------------
    def _on_rw_close(self):

        self._stop_odds_proc()
        self._stop_results_proc()
        try: self.destroy()
        except Exception: pass

    # ------ odds subprocess 終了 ------
    def _stop_odds_proc(self):

        if self._odds_proc and self._odds_proc.poll() is None:
            try:
                self._send_odds_command({"state":"stop"})
                self._odds_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._odds_proc.terminate()
            except Exception:
                pass
            finally:
                self._odds_proc = None

    # ------ results subprocess 終了 ------
    def _stop_results_proc(self):

        if self._results_proc and self._results_proc.poll() is None:
            try:
                self._send_results_command({"state":"stop"})
                self._results_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._results_proc.terminate()
            except Exception:
                pass
            finally:
                self._results_proc = None

    #-----------------------------------
    def _from_json(self, d_iso:str, excld:bool=False):
        #---------------
        def convert_keys_to_int(d:dict):
            return {int(k) if k.isdigit() else k:v for k, v in d.items()}
        #---------------
        col = "excld_edo" if excld else "all_venue"

        row = dal.fetch_one(f"""
                      SELECT {col}
                        FROM Daily_Overall
                       WHERE date = ?
                      """,
                      (d_iso,) )

        if row:
            json_txt = row[0]
            try:
                return json.loads(json_txt, object_hook=convert_keys_to_int)
            except json.JSONDecodeError as e:
                print(f"JSON復元エラー: {e}")
                return {}
        else:
            return {}

# -----------------------------------------------------------------------------