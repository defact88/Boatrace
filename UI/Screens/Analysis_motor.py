# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\Analysis_motor.py

from tkinter                import ttk
from datetime               import datetime as dt, date, time, timedelta
from Helpers.Custum_func    import cFr, cLbl, cBtn
from dateutil.relativedelta import relativedelta
import Dal as dal, tkinter as tk

P_GEN_PRE  = [0, 10,  8, 6, 4, 2, 1]
P_GEN_FIN  = [0, 11,  9, 7, 6, 4, 3]
P_G12_PRE  = [0, 11,  9, 7, 5, 3, 2]
P_G12_FIN  = [0, 12, 10, 8, 7, 5, 4]
P_SG_PRE   = [0, 12, 10, 8, 6, 4, 3]
P_SG_FIN   = [0, 13, 11, 9, 8, 6, 5]

BT_KEY = "ファン感謝３Ｄａｙｓボートレースバトルトーナメント"

GUI, MUI       = "Yu Gothic UI", "Meiryo UI"
BD             = "bold"
GR, SD, RA, RD = "groove", "solid", "raised", "ridge"
ALL, CT        = "nsew", "center"

HDR_C          = "#e0e1f4"
HL_COL         = "#cce8ff"
PREFIN         = "#e2ffe1"
PLAYER         = "#fffcec"
INFO           = "#f2fdff"

FRM  = { 0: dict(bg="SystemButtonFace", fg=  "black", font=(MUI,8,BD), Anc=CT),
         1: dict(bg="#FFFFFF",          fg="#000000", font=(MUI,8,BD), Anc=CT),
         2: dict(bg="#000000",          fg="#FFFFFF", font=(MUI,8,BD), Anc=CT),
         3: dict(bg="#D40000",          fg="#FFFFFF", font=(MUI,8,BD), Anc=CT),
         4: dict(bg="#0066CC",          fg="#FFFFFF", font=(MUI,8,BD), Anc=CT),
         5: dict(bg="#FFD400",          fg="#000000", font=(MUI,8,BD), Anc=CT),
         6: dict(bg="#008A2E",          fg="#FFFFFF", font=(MUI,8,BD), Anc=CT), }

GOPT = { 0: dict(text="一般戦",          bg=INFO, font=(MUI,9    )),
         1: dict(text="G3",              bg=INFO, font=(MUI,9    )),
         2: dict(text="G2",  fg="green", bg=INFO, font=(MUI,10,BD)),
         3: dict(text="G1",  fg="blue",  bg=INFO, font=(MUI,10,BD)),
         4: dict(text="PG1", fg="blue",  bg=INFO, font=(MUI,10,BD)),
         5: dict(text="SG",  fg="red",   bg=INFO, font=(MUI,10,BD))  }

CLS  = { "A1": dict(text="A1", fg="blue",    bg=PLAYER, font=(GUI,10,BD), Anc=CT),
         "A2": dict(text="A2", fg="#006625", bg=PLAYER, font=(GUI,10,BD), Anc=CT),
         "B1": dict(text="B1", fg="black",   bg=PLAYER, font=(GUI,10,BD), Anc=CT),
         "B2": dict(text="B2", fg="red",     bg=PLAYER, font=(GUI,10,BD), Anc=CT)  }

FINAL = { 1:"①", 2:"②", 3:"③", 4:"④", 5:"⑤", 6:"⑥",
          "F":"(F)", "L":"(L)", "S":"(S)", "K":"(K)"       }

NAME =  dict(font=(GUI,10,BD), bg=PLAYER,  Anc=CT)
TERM =  dict(font=(GUI,10   ), bg=INFO,    Anc=CT)
FIN  = [dict(font=(MUI, 8,BD), bg="white", Anc=CT),
        dict(font=(MUI, 8,BD), bg=PREFIN,  Anc=CT),
        dict(font=(MUI,11,BD), bg=HL_COL,  Anc=CT), ]
SLIT =  dict(font=(MUI, 7   ), bg="white", Anc=CT)

SET_PARTS = {'ピストン×２', 'リング×４', 'シリンダーケース'}

# --------
def w_txt(s:str) -> str:
    hair = "\u200A" 
    return hair.join(list(s))
#=====================================================================
class MotorAnalysisScreen(tk.Toplevel):
    def __init__(self, master, motor_no:int, venue_id:int, upd_m:int):
        super().__init__(master)

        self.title("")
        self.geometry("606x700+600+150")

        self.motor_no = motor_no
        self.venue_id = venue_id

        y = dt.now().year if upd_m <= dt.now().month else dt.now().year -1
        self.date_from = f"{y}-{upd_m:02d}-01"
        self.date_to   = dt.now().strftime("%Y-%m-%d")

        self._build_ui()
        self._refresh_data()

    #---------------------------------------------
    def _build_ui(self):

        headers = [ "モーター", "使用 節数", "使用レース",
                    " 1着 率 ", "2連対率",   "3連対率",
                    "優出 回数", "優勝 回数", "プロペラ交換",
                    "セット交換"]

        self.stat_labels = {}

        self.main = cFr(self, W=606, H=700, px=10, py=10)
        self.main._grid(R=0, C=0, Stk=ALL) ;self.main.Pgate()

        # --- 左部
        fr_stats = cFr(self.main, W=200, H=680, Bd=(1,SD))
        fr_stats._grid(R=0, C=0, padx=(0,20), Stk=ALL) ;fr_stats.Pgate()

        for r, text in zip(range(10), headers):
            fr1 = cFr(fr_stats, W=99, H=30)
            fr2 = cFr(fr_stats, W=99, H=30)
            fr1.Cconf(0, W=1) ;fr1.Rconf(0, W=1)
            fr2.Cconf(0, W=1) ;fr2.Rconf(0, W=1)
            fr1._grid(R=r, C=0, Stk=ALL) ;fr1.Pgate()
            fr2._grid(R=r, C=1, Stk=ALL) ;fr2.Pgate()

            cLbl(fr1, text=text, bg="#e0e1f4", font=(MUI,10), Bd=(1,GR))._grid(R=0, C=0, Stk=ALL)
            lb = cLbl(fr2, text="-", bg="white", font=(MUI,10), Bd=(1,GR))
            lb._grid(R=0, C=0, Stk=ALL)
            self.stat_labels[r] = lb

        # --- 下部
        fr_cvs = cFr(self.main, W=366, H=680, Bd=(1,SD)) ;fr_cvs._grid(R=0, C=1, Stk=ALL) ;fr_cvs.Pgate()

        fr_hdr = cFr(fr_cvs, W=364, H=30, Bd=(1,GR), bg="#e0e1f4")
        fr_hdr._grid(R=0, C=0, Cspan=2, Stk=ALL); fr_hdr.Pgate()
        fr_hdr.Rconf(0, W=1) ;fr_hdr.Cconf(0, W=1)

        cLbl(fr_hdr, text="使用 履歴", font=(MUI,10), bg="#e0e1f4",Anc=CT)._grid(R=0, C=0, Stk=ALL)

        self.canvas  = tk.Canvas(fr_cvs, width=337, height=648)
        self.scr_bar = ttk.Scrollbar(fr_cvs, orient="vertical", command=self.canvas.yview)
        self.fr_body = cFr(self.canvas, width=337, height=648)

        self.canvas.configure(yscrollcommand=self.scr_bar.set)

        self.canvas.grid( row=1, column=0, sticky=ALL) ;self.canvas.grid_propagate(False)
        self.scr_bar.grid(row=1, column=1, sticky="ns") ;self.scr_bar.grid_propagate(False)

        self.window  = self.canvas.create_window((0, 0), window=self.fr_body, anchor="nw")
        #-----------
        def _mw(e):
            self.canvas.yview_scroll(int(-1 *(e.delta / 120)), "units")
        #-----------
        def _on_close():
           self.unbind_all("<MouseWheel>")
           self._mw_handler = None
           self.destroy()
        #-----------
        def _on_conf(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfigure(self.window, width=self.canvas.winfo_width())
        #-----------
        self.fr_body.bind( "<Configure>", _on_conf)
        self.canvas.bind(  "<Configure>", _on_conf)
        self.canvas.bind_all("<MouseWheel>", _mw)
        self.protocol("WM_DELETE_WINDOW", _on_close)

    #-------------------------------------------------------
    def _refresh_data(self):

        for widget in self.fr_body.winfo_children(): widget.destroy()

        rows1 = dal.fetch_one(
            """
            SELECT COUNT(DISTINCT r.series_title) as series_cnt,
                   COUNT(         e.race_id     ) as race_cnt,
                     SUM(CASE WHEN e.finish_rank  = 1 THEN 1 ELSE 0 END) as win1,
                     SUM(CASE WHEN e.finish_rank <= 2 THEN 1 ELSE 0 END) as win2,
                     SUM(CASE WHEN e.finish_rank <= 3 THEN 1 ELSE 0 END) as win3,
                     SUM(CASE WHEN r.is_final     = 1 THEN 1 ELSE 0 END) as fin,
                     SUM(CASE WHEN r.is_final = 1 AND e.finish_rank = 1 THEN 1 ELSE 0 END) as victry
              FROM Race_entries e
              JOIN Races r ON e.race_id = r.race_id
             WHERE e.motor_no = ?
               AND r.venue_id = ?
               AND r.date    >= ?
               AND e.finish_rank in (1,2,3,4,5,6)
            """,
            (self.motor_no, self.venue_id, self.date_from))

        if rows1 and rows1['race_cnt'] > 0:
            rc = rows1['race_cnt']
            self.stat_labels[0].config(text=str(self.motor_no))
            self.stat_labels[1].config(text=f"{rows1['series_cnt']} 節")
            self.stat_labels[2].config(text=f"{rc} 回")
            self.stat_labels[3].config(text=f"{(rows1['win1']/rc*100):.1f}%")
            self.stat_labels[4].config(text=f"{(rows1['win2']/rc*100):.1f}%")
            self.stat_labels[5].config(text=f"{(rows1['win3']/rc*100):.1f}%")
            self.stat_labels[6].config(text=f"{rows1['fin']}")
            self.stat_labels[7].config(text=f"{rows1['victry']}")

        rows2 = dal.fetch_all(
            """
            SELECT r.date         as date,
                   r.series_title as title,
                   r.grade        as grade,
                   r.is_final     as final,
                   r.is_prefinal  as prefinal,
                   p.player_id    as p_id,
                   p.name         as name,
                   p.class_now    as _class,
                   e.boat_no      as b_no,
                   e.frame_no     as fr_no,
                   e.course       as cour,
                   e.slit_ADJ     as slit,
                   e.finish_rank  as rank,
                   e.fault_code   as fault,
                   e.fault_level  as f_lvl,
                   d.rep_parts    as parts
              FROM Race_entries e
              JOIN Races r       ON   e.race_id  = r.race_id
              JOIN Players p     ON e.player_id  = p.player_id
              JOIN Display_run d ON d.entry_id   = e.entry_id
             WHERE e.motor_no = ?
               AND r.venue_id = ?
               AND r.date    >= ?
          ORDER BY r.date DESC, r.race_no DESC
            """,
            (self.motor_no, self.venue_id, self.date_from))

        series_groups = []
        if rows2:
            current_group = []
            last_date  = dt.strptime(rows2[0]['date'], '%Y-%m-%d')
            last_title = rows2[0]['title']

            for r in rows2:
                this_date = dt.strptime(r['date'], '%Y-%m-%d')

                if r['title'] == last_title and abs((last_date - this_date).days) <= 9:
                    current_group.append(r)
                else:
                    series_groups.append(current_group)
                    current_group = [r]

                last_date = this_date
                last_title = r['title']

            if current_group:
                series_groups.append(current_group)

        propeller = 0
        set_parts = 0
        for r, rows in enumerate(series_groups):

            fr_block = cFr(self.fr_body, W=337, H=140, Bd=(1,SD))
            fr_block._grid(R=r, C=0, py=(0,20)) ;fr_block.Pgate()

            fr_head  = cFr(fr_block, W=335, H=54)
            fr_data  = cFr(fr_block, W=335, H=84, Bd=(1,GR))
            fr_head._grid(R=0, C=0) ;fr_head.Pgate()
            fr_data._grid(R=1, C=0) ;fr_data.Pgate()

            fr_head1  = cFr(fr_head, W=335, H=24)
            fr_head2  = cFr(fr_head, W=335, H=30)
            fr_head1._grid(R=0, C=0) ;fr_head1.Pgate()
            fr_head2._grid(R=1, C=0) ;fr_head2.Pgate()

            fr_term  = cFr(fr_head1, W=285, H=30, bg=INFO,    Bd=(1,GR)) ;fr_term.Pgate()
            fr_grad  = cFr(fr_head1, W= 50, H=30, bg=INFO,    Bd=(1,GR)) ;fr_grad.Pgate()
            fr_name  = cFr(fr_head2, W=135, H=30, bg=PLAYER,  Bd=(1,GR)) ;fr_name.Pgate()
            fr_clas  = cFr(fr_head2, W= 40, H=30, bg=PLAYER,  Bd=(1,GR)) ;fr_clas.Pgate()
            fr_sc_p  = cFr(fr_head2, W= 80, H=30, bg=PLAYER,  Bd=(1,GR)) ;fr_sc_p.Pgate()
            fr_sc_m  = cFr(fr_head2, W= 80, H=30, bg="white", Bd=(1,GR)) ;fr_sc_m.Pgate()

            fr_term._grid(R=0, C=0) ;fr_term.Rconf(0, W=1) ;fr_term.Cconf(0, W=1)
            fr_grad._grid(R=0, C=1) ;fr_grad.Rconf(0, W=1) ;fr_grad.Cconf(0, W=1)
            fr_name._grid(R=1, C=0) ;fr_name.Rconf(0, W=1) ;fr_name.Cconf(0, W=1)
            fr_clas._grid(R=1, C=1) ;fr_clas.Rconf(0, W=1) ;fr_clas.Cconf(0, W=1)
            fr_sc_p._grid(R=1, C=2) ;fr_sc_p.Rconf(0, W=1) ;fr_sc_p.Cconf(0, W=1)
            fr_sc_m._grid(R=1, C=3) ;fr_sc_m.Rconf(0, W=1) ;fr_sc_m.Cconf(0, W=1)

            head = rows[0]

            txt1 = f"{head['name']}"
            txt2 = f"{self._date(rows[-1]['date'])}  ～  {self._date(rows[0]['date'], md=True)}"

            cLbl(fr_term, text=txt2, **TERM,     px=0, py=0)._grid(R=0, C=0, Stk="n")
            cLbl(fr_name, text=txt1, **NAME,     px=0, py=0)._grid(R=0, C=0, Stk=ALL)
            cLbl(fr_clas, **CLS[head['_class']], px=0, py=0)._grid(R=0, C=0, Stk=ALL)
            cLbl(fr_grad, **GOPT[head['grade']], px=0, py=0)._grid(R=0, C=0, Stk=ALL)

            sc_sum    = 0
            sc_cnt    = 0
            pid       = None
            rep_parts = []

            for c, row in enumerate(reversed(rows)):

                fr_A = cFr(fr_data, W=26, H=28, Bd=(1,GR)) ;fr_A._grid(R=0, C=c) ;fr_A.Pgate()
                fr_B = cFr(fr_data, W=26, H=28, Bd=(1,GR)) ;fr_B._grid(R=1, C=c) ;fr_B.Pgate()
                fr_C = cFr(fr_data, W=26, H=28, Bd=(1,GR)) ;fr_C._grid(R=2, C=c) ;fr_C.Pgate()
                fr_A.Rconf(0, W=1) ;fr_A.Cconf(0, W=1)
                fr_B.Rconf(0, W=1) ;fr_B.Cconf(0, W=1)
                fr_C.Rconf(0, W=1) ;fr_C.Cconf(0, W=1)

                opt  = FRM[row["fr_no"]]
                if row["fault"] != "F" : slit = f"{row['slit']:.2f}"[1:] if row['slit'] else ""
                else: slit = f"{row['slit']:.2f}"[2:]
                fin  = row["rank"] if row["rank"] else row["fault"]
                fg   = "red" if fin in ("F","L","S","K") else "black"
                txt  = FINAL[fin] if row["final"] else fin

                i = row["prefinal"]
                if row["final"]: i = 2

                cLbl(fr_A, text=row["cour"], **opt    )._grid(R=0, C=0, Stk=ALL)
                cLbl(fr_B, text=slit, **SLIT          )._grid(R=0, C=0, Stk=ALL)
                cLbl(fr_C, text=txt, **FIN[i], fg=fg  )._grid(R=0, C=0, Stk=ALL)

                if row["parts"]:
                    rep_parts.extend([s.strip() for s in row["parts"].split(",")])
                    set_parts += 1 if SET_PARTS.issubset(rep_parts) else 0

                pid = row["p_id"]

                if row["f_lvl"] != 0 or row["rank"] != 0:
                    p = self._point_for(row["grade"], row["final"], row["rank"], row["title"])
                    sc_cnt += 1
                    sc_sum += p
            sc_m = f"{(sc_sum / sc_cnt):.2f}"
            sc_p = self._query_sc(pid)

            cLbl(fr_sc_p, text=w_txt(sc_p), font=(GUI,10,BD), bg=PLAYER)._grid(R=0, C=0, Stk=ALL)
            cLbl(fr_sc_m, text=w_txt(sc_m), font=(GUI,10,BD), bg="#fffdbb")._grid(R=0, C=0, Stk=ALL)

            propeller += rep_parts.count("プロペラ")
        self.stat_labels[8].config(text=f"{propeller}")
        self.stat_labels[9].config(text=f"{set_parts}")
    #-----------------------------------
    @staticmethod
    def _to_date(x) -> date:

        if isinstance(x, date): return x
        if isinstance(x,  str): return dt.fromisoformat(x)

        raise ValueError("date conv error")
    #-----------------------------------
    def _date(self, d:dt, md:bool=False) -> str:

        d = self._to_date(d)
        if md: return f"{d.month}月 {d.day}日"
        else:  return f"{d.year}年    {d.month}月 {d.day}日"
    # --------------------------------------------
    def _point_for(self, grade:int|None, final:int|None, rank:int|None, s_name:str):

        if s_name.strip() in BT_KEY: tbl = P_G12_FIN if final else P_G12_PRE
        elif grade in (2, 3, 4):     tbl = P_G12_FIN if final else P_G12_PRE
        elif grade ==  5:            tbl = P_SG_FIN  if final else  P_SG_PRE
        else:                        tbl = P_GEN_FIN if final else P_GEN_PRE

        return tbl[rank or 0]
    # --------------------------------------------
    def _query_sc(self, pid):

        _date = (dt.now() - relativedelta(months=6)).isoformat()
        rows = dal.fetch_all(
            """
            SELECT r.series_title as title,
                   r.grade        as grade,
                   r.is_final     as final,
                   e.finish_rank  as rank,
                   e.fault_code   as fault,
                   e.fault_level  as f_lvl
              FROM Race_entries e
              JOIN Races r ON e.race_id = r.race_id
               AND e.player_id = ?
               AND r.date     >= ?
          GROUP BY e.entry_id
            """,
            (pid, _date))

        if rows:
            sc_sum = 0
            sc_cnt = 0

            for  title, grade, final, rank, fault, f_lvl in rows:
               if f_lvl != 0 or rank != 0:
                    p = self._point_for(grade, final, rank, title)
                    sc_cnt += 1
                    sc_sum += p

        return  f"{(sc_sum / sc_cnt):.2f}"

        