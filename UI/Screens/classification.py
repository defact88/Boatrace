# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\same_period_player.py

from tkinter                 import ttk, messagebox
from PIL                     import Image, ImageTk
from typing                  import Dict, Optional
from itertools               import product
from dateutil.relativedelta  import relativedelta
from collections             import defaultdict
from datetime                import datetime as dt, date, time, timedelta
from Helpers.Custum_func     import cFr, cLbl, cBtn, cCvs, cSrb
from Helpers.queries         import Query
from Widgets.widgets         import set_player_image
import os, tkinter as tk, Dal as dal

GUI, MUI       = "Yu Gothic UI", "Meiryo UI"
BD             = "bold"
GR, SD, RA, RD = "groove", "solid", "raised", "ridge"
ALL, CT        = "nsew", "center"

BDFNT          = dict(font=(MUI,9,BD))
NMFNT          = dict(font=(MUI,9   ))

COLS           = [ ("player_id", "登番"     ),
                   ("name",      "氏名"     ),
                   ("age",       "年齢"     ),
                   ("regions",   "所属支部" ),
                   ("class_now", "現適用級" ),
                   ("score_ave", "適用勝率" ),
                   ("sc_now",    "今期勝率" ),
                   ("to_final",  "優 出"    ),
                   ("victory",   "優 勝"    ),
                   ("win_G2",    "G2 優勝"  ),
                   ("win_G1",    "G1 優勝"  ),
                   ("win_SG",    "SG 優勝"  ), ]

HL_COL    = "#cce8ff"
HDR_COLOR = "#e0e1f4"
NML_COL   = "SystemButtonFace"

CEL_W = 70
CEL_H = 30
CELLS = [70, 120, 60, 70, 70, 70, 70, 60, 60, 60, 60, 60]

P_GEN_PRE  = [0, 10,  8, 6, 4, 2, 1]
P_GEN_FIN  = [0, 11,  9, 7, 6, 4, 3]
P_G12_PRE  = [0, 11,  9, 7, 5, 3, 2]
P_G12_FIN  = [0, 12, 10, 8, 7, 5, 4]
P_SG_PRE   = [0, 12, 10, 8, 6, 4, 3]
P_SG_FIN   = [0, 13, 11, 9, 8, 6, 5]

BT_KEY = "ファン感謝３Ｄａｙｓボートレースバトルトーナメント"
#---------------------------------------
def _point_for(grade:int, final:int, rank:int, s_name:str):

    if s_name.strip() in BT_KEY: tbl = P_G12_FIN if final else P_G12_PRE
    elif grade in (2, 3, 4):     tbl = P_G12_FIN if final else P_G12_PRE
    elif grade ==  5:            tbl = P_SG_FIN  if final else  P_SG_PRE
    else:                        tbl = P_GEN_FIN if final else P_GEN_PRE

    return tbl[rank or 0]
#---------------------------------------
def _this_season_start(today:date) -> date:

    if 5 <= today.month <= 10: return date(today.year,  5, 1)
    if      today.month >= 11: return date(today.year, 11, 1)

    return date(today.year-1, 11, 1)
#===============================================================================
class PlayerClassificationScreen(tk.Toplevel):

    def __init__( self, master, regist_period:int=None, region:str=None):
        super().__init__(master)

        self.title("")
        self.geometry("866x970+1145+200")
        self.resizable(False, False)
        self.regist_period = regist_period
        self.region        = region
        self.key = regist_period if regist_period else region
        self.build_ui()
        self._refresh_players_data()

    def build_ui(self):

        fr_main = cFr(self, W=866, H=970, px=9, py=5)
        fr_main._grid(R=0, C=0) ;fr_main.Pgate()

        fr_info      = cFr(fr_main,  W=848, H= 50)
        fr_hdr       = cFr(fr_main,  W=832, H= 30, Bd=(1,SD))
        self.canvas       = cCvs(fr_main, W=832, H=870)
        self.fr_body = cFr(self.canvas,   W=832, Bd=(1,SD))
        scr_bar      = cSrb(fr_main, orient="vertical", Com=self.canvas.yview)
        self.canvas.config(yscrollcommand=scr_bar.set)

        fr_info._grid(R=0, C=0, Cspan=2) ;fr_info.Pgate()
        fr_hdr._grid( R=1, C=0)           ;fr_hdr.Pgate()
        self.canvas._grid( R=2, C=0, Stk="nsew")
        scr_bar._grid(R=2, C=1, Stk=  "ns")

        self.canvas.create_window((0, 0), window=self.fr_body, anchor="nw")
        self.fr_body.bind("<Configure>", lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        for c in range(0, len(COLS)):
            fr_hdr.Cconf(c, minsize=CELLS[c])
        fr_hdr.Rconf(0, minsize=CEL_H)

        if isinstance(self.key, int):
            ttk.Button( fr_info, text="＜", command=self._preview
                       ).grid(row=0, column=0, padx=(260,0))
            self.lb_info = cLbl(fr_info, font=(MUI,11), text=f"   {self.key} 期  ")
            self.lb_info._grid(R=0, C=1, Stk=ALL)
            ttk.Button(fr_info, text="＞", command=self._next).grid(row=0, column=2)
        else:
            cLbl(fr_info, font=(MUI,11), text=f"   {self.key} 支部  ", Anc=CT)._grid(R=0, C=0, Stk=ALL)

        self._cells:Dict[tuple[int,int], tk.Label] = {}
        # ----------
        def make_cell(r:int, c:int, text:str, f:str):
            lbl = cLbl(fr_body, text=text, font=f, Anc=CT, Bd=(1,GR))
            lbl._grid(R=r, C=c, Stk=ALL)
            self._cells[(r,c)] = lbl
        #-----------
        for c, cap in enumerate(COLS):      # ヘッダ
            cLbl(fr_hdr, text=cap[1], font=(MUI,10), bg=HDR_COLOR, Bd=(1,RD))._grid(R=0, C=c, Stk=ALL)
        #-----------
        def _mw(e):
            self.canvas.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_close():
           self.destroy()
        #-----------
        self.canvas.bind("<Enter>", lambda e:self.canvas.bind_all("<MouseWheel>", _mw))
        self.canvas.bind("<Leave>", lambda e:self.canvas.unbind_all("<MouseWheel>"))
        self.protocol("WM_DELETE_WINDOW", _on_close)

    #-------------------------------------------------------
    def _preview(self):

        self.key -= 1
        self.lb_info.config(text=f"   {self.key} 期  ")
        self._refresh_players_data()
    #-------------------------------------------------------
    def _next(self):

        self.key += 1
        self.lb_info.config(text=f"   {self.key} 期  ")
        self._refresh_players_data()
    #-------------------------------------------------------
    def _refresh_players_data(self):

        for widget in self._cells.values():
            widget.destroy()
        self._cells.clear()

        sql_1 = """
            WITH TargetPlayers AS( SELECT p.player_id,
                                          p.name,
                                          p.age,
                                          p.regions,
                                          p.class_now,
                                          sr.score_ave
                                     FROM Players p JOIN Season_result sr
                                       ON p.player_id = sr.player_id
                                    WHERE p.regist_period = ?
                                      AND sr.year         = ?
                                      AND sr.season       = ?              ),
                """
        sql_2 = """
            WITH TargetPlayers AS( SELECT p.player_id,
                                          p.name,
                                          p.age,
                                          p.regions,
                                          p.class_now,
                                          sr.score_ave
                                     FROM Players p JOIN Season_result sr
                                       ON p.player_id = sr.player_id
                                    WHERE p.regions  = ?
                                      AND sr.year    = ?
                                      AND sr.season  = ?                   ),
                """

        main_query = """
             CurrentSeason AS( SELECT e.player_id,
                                COUNT(*) as run_cnt,
                                  SUM( CASE WHEN r.series_title LIKE ?
                                              OR r.grade IN (2, 3, 4)
                                            THEN( CASE WHEN r.is_final = 1 
                                                       THEN( CASE e.finish_rank WHEN 1 THEN 12
                                                                                WHEN 2 THEN 10
                                                                                WHEN 3 THEN  8
                                                                                WHEN 4 THEN  7
                                                                                WHEN 5 THEN  5
                                                                                WHEN 6 THEN  4
                                                                                ELSE 0 END     )
                                                       ELSE( CASE e.finish_rank WHEN 1 THEN 11
                                                                                WHEN 2 THEN  9
                                                                                WHEN 3 THEN  7
                                                                                WHEN 4 THEN  5
                                                                                WHEN 5 THEN  3
                                                                                WHEN 6 THEN  2
                                                                                ELSE 0 END     )
                                                        END                                      )

                                            WHEN r.grade = 5
                                            THEN( CASE WHEN r.is_final = 1
                                                       THEN( CASE e.finish_rank WHEN 1 THEN 13
                                                                                WHEN 2 THEN 11
                                                                                WHEN 3 THEN  9
                                                                                WHEN 4 THEN  8
                                                                                WHEN 5 THEN  6
                                                                                WHEN 6 THEN  5
                                                                                ELSE 0 END     )
                                                       ELSE( CASE e.finish_rank WHEN 1 THEN 12
                                                                                WHEN 2 THEN 10
                                                                                WHEN 3 THEN  8
                                                                                WHEN 4 THEN  6
                                                                                WHEN 5 THEN  4
                                                                                WHEN 6 THEN  3
                                                                                ELSE 0 END     )
                                                        END                                      )

                                           ELSE( CASE WHEN r.is_final = 1 
                                                      THEN( CASE e.finish_rank WHEN 1 THEN 11
                                                                               WHEN 2 THEN  9
                                                                               WHEN 3 THEN  7
                                                                               WHEN 4 THEN  6
                                                                               WHEN 5 THEN  4
                                                                               WHEN 6 THEN  3
                                                                               ELSE 0 END     )
                                                      ELSE( CASE e.finish_rank WHEN 1 THEN 10
                                                                               WHEN 2 THEN  8
                                                                               WHEN 3 THEN  6
                                                                               WHEN 4 THEN  4
                                                                               WHEN 5 THEN  2
                                                                               WHEN 6 THEN  1
                                                                               ELSE 0 END     )
                                                       END                                      )
                                            END ) as total_pts

                                  FROM Race_entries e JOIN Races r
                                    ON e.race_id = r.race_id
                                 WHERE r.date BETWEEN ? AND ?
                                   AND r.status  = 'held'
                                   AND e.finish_rank != 0
                               AND NOT(e.fault_code IN ('F','L','S','K') AND e.fault_level != 0)
                              GROUP BY e.player_id ),

             CareerSummary AS ( SELECT e.player_id,
                                   SUM(CASE WHEN    r.is_final = 1 THEN 1 ELSE 0 END) AS to_final,
                                   SUM(CASE WHEN    r.is_final = 1
                                             AND e.finish_rank = 1 THEN 1 ELSE 0 END) AS victory,
                                   SUM(CASE WHEN       r.grade = 2
                                             AND    r.is_final = 1
                                             AND e.finish_rank = 1 THEN 1 ELSE 0 END) AS win_G2,
                                   SUM(CASE WHEN       r.grade IN (3,4)
                                             AND    r.is_final = 1
                                             AND e.finish_rank = 1 THEN 1 ELSE 0 END) AS win_G1,
                                   SUM(CASE WHEN       r.grade = 5
                                             AND    r.is_final = 1
                                             AND e.finish_rank = 1 THEN 1 ELSE 0 END) AS win_SG
                                  FROM Race_entries e
                                  JOIN Races r ON e.race_id = r.race_id
                                 WHERE r.is_final = 1
                              GROUP BY e.player_id )

            SELECT tp.player_id, tp.name, tp.age, tp.regions, tp.class_now, 
                   printf('%.2f', CAST(tp.score_ave AS FLOAT) / 100),
                   printf('%.2f', CAST(cs.total_pts AS FLOAT) / NULLIF(cs.run_cnt, 0)),
                   IFNULL(ca.to_final, 0),
                   IFNULL(ca.victory,  0),
                   IFNULL(ca.win_G2,   0),
                   IFNULL(ca.win_G1,   0),
                   IFNULL(ca.win_SG,   0)
              FROM TargetPlayers tp
         LEFT JOIN CurrentSeason cs ON tp.player_id = cs.player_id
         LEFT JOIN CareerSummary ca ON tp.player_id = ca.player_id
          ORDER BY tp.player_id;
        """

        date_to    = date.today()
        date_from  = _this_season_start(date_to)

        if 1 <= date.today().month <=  6: _year = date.today().year ;season = 1
        if 7 <= date.today().month <= 12: _year = date.today().year ;season = 2

        params   = ( self.key, _year, season, 'ファン感謝３Ｄａｙｓボートレースバトルトーナメント',
                     date_from.isoformat(), date_to.isoformat() )
        sql      = sql_1 if isinstance(self.key, int) else sql_2
        all_rows = dal.fetch_all(sql + main_query, params)

        for r, data in enumerate(all_rows):
            self.fr_body.Rconf(r, minsize=CEL_H)
            has_major_win = (data[10] >= 1 or data[11] >= 1)
            bg            = HL_COL if has_major_win else "white"

            for c, val in enumerate(data):
                self.fr_body.Cconf(c, minsize=CELLS[c])
                f   =(MUI,10,BD) if c >= 10 and val >=1 else (MUI,10)
                lbl = cLbl(self.fr_body, text=str(val), font=f, Anc=CT, Bd=(1,GR), bg=bg)
                lbl._grid(R=r, C=c, Stk=ALL)
                self._cells[(r, c)] = lbl

                if c == 0:
                    pid = val
                if c == 1:
                    self._cells[(r, c)].config(text=str(val), cursor="hand2", bg=bg, font=f)
                    self._cells[(r, c)].bind("<Button-1>",lambda e, p=pid:self._player_screen(p))
                else:
                    self._cells[(r, c)].config(text=str(val), bg=bg, font=f)

        self.fr_body.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    #-------------------------------------------------------
    def _player_screen(self, pid):

        from Screens import PlayerAnalysisScreen
        PlayerAnalysisScreen(self, pid, cou=1)


