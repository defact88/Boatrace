# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\sub_window.py

import tkinter as tk
from tkinter      import ttk, messagebox
from Custum_func  import cFr, cLbl, cBtn, cEnt
import Dal as dal

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
BLUE    = "#ff7474"
LIT_RED = "#ff5b5b"

HDR_B   = dict(bg=HDR_BG)
HDR_BF  = dict(bg=HDR_BG, fg=WHITE)
BTN_BF  = dict(bg=BTN_BG, fg=WHITE)
BTN_OPT = dict(bg=BTN_BG, fg=WHITE,  Bd=(1,RA), font=(MUI,9,BD))
BTN_OFF = dict(bg=BTN_BG, fg=WHITE,  Bd=(1,RA))
GRY_OFF = dict(bg=GRAY1,  fg=BLACK1, Bd=(1,RA))
YEL1_ON = dict(bg=YELL1,  fg=BLACK2, Bd=(1,GR))
YEL2_ON = dict(bg=YELL2,  fg=BLACK2, Bd=(1,SK))

REGIONS = [ "",     "群馬", "埼玉", "東京", "静岡", "愛知", "三国", "三重", "滋賀", "大阪",
            "兵庫", "広島", "徳島", "香川", "岡山", "山口", "福岡", "佐賀", "長崎"          ]
#=====================================================================
def open_player_picker(self):

    win = tk.Toplevel(self, bg=MAIN_BG)
    win.title("選手選択")
    win.geometry("600x600+550+200")
    win.transient(self)
    win.grab_set()

    groups = [""] + [f"{i:04d}" for i in range(1000, 7000, 1000)]

    pannel = cFr(win, bg=MAIN_BG) ;pannel.pack(fill="both", side="right", padx=8, pady=6)

    row1 = cFr(pannel) ;row1._grid(R=0, C=0, Stk=ALL, px=5, py=10)
    row2 = cFr(pannel) ;row2._grid(R=1, C=0, Stk=ALL, px=5, py=10)
    row3 = cFr(pannel) ;row3._grid(R=2, C=0, Stk=ALL, px=5, py=10)
    btns = cFr(pannel) ;btns._grid(R=12, C=0, Stk=ALL, px=5, py=10)
    cLbl(row1, text="検索", font=(MUI,10))._grid(R=0, C=0, Stk=ALL)
    cLbl(row2, text="登番", font=(MUI,10))._grid(R=0, C=0, Stk="w")
    cLbl(row3, text="支部", font=(MUI,10))._grid(R=0, C=0, Stk="w")

    ent_kw  = cEnt(row1, W=15, font=(MUI,11))
    cbo_grp = ttk.Combobox(row2, values=groups,  state="readonly", width=10, font=(MUI,10))
    cbo_reg = ttk.Combobox(row3, values=REGIONS, state="readonly", width=10, font=(MUI,10))

    ent_kw._grid(row=0, column=1, sticky="w", padx=4)
    cbo_grp.grid(row=0, column=1, sticky="w", padx=(4,10))
    cbo_reg.grid(row=0, column=1, sticky="w", padx=(4, 6))

    #-----┐
    def do_search(*_):
        load(ent_kw.get().strip(), cbo_grp.get().strip(), cbo_reg.get().strip())
    #-----┘
    #-----┐
    def apply_selection():
        sel = tree.selection()
        if not sel:
            win.destroy(); return
        pid = tree.item(sel[0], "values")[0]
        try:
            pid = int(pid)
        except Exception: pass

        self.open_p_analys(pid)
        win.destroy()
    #-----┘
    cBtn(pannel, text="検索",   Com=do_search,       **BTN_OPT)._grid(R=3, C=0, Stk=ALL, py=20)
    cBtn(btns, W=10,   text="決 定",  Com=apply_selection, **BTN_OPT)._grid(R=0, C=0, Stk=ALL, px=5, py=5)
    cBtn(btns,   text="閉じる", Com=win.destroy,     **BTN_OPT)._grid(R=1, C=0, Stk=ALL, px=5, py=5)

    # 結果ツリー
    cols = ("登番", "選手名", "所属支部")
    tree = ttk.Treeview(win, columns=cols, show="headings")

    for c, w in zip(cols, (50, 130, 60)):
        tree.heading(c, text=c)
        tree.column(c, width=w, anchor=CT)

    ysb = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=ysb.set)
    tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(8,0), pady=(0,8))
    ysb.pack(fill=tk.Y, side=tk.LEFT, padx=(0,8), pady=(0,8))
    tree.bind("<Double-1>", lambda e: apply_selection())
    ent_kw.bind("<Return>", do_search)
    #-----┐
    def load(keyword: str, group_text: str, region_text: str):

        sql = ("""
                  SELECT player_id,
                         name,
                         COALESCE(regions,'') AS regions
                    FROM Players
                    WHERE 1=1
               """)

        params = []

        if keyword:
            sql += "AND (player_id = ? OR name LIKE ?) "
            params += [keyword, f"%{keyword}%"]
        if group_text:
            sql += "AND CAST(player_id AS INTEGER) BETWEEN ? AND ? "
            params += [int(group_text), int(group_text) + 999]
        if region_text:
            sql += "AND regions = ? "
            params += [region_text]

        sql += "ORDER BY CAST(player_id AS INTEGER) LIMIT 1000;"

        try:
            rows = dal.fetch_all(sql, tuple(params)) if dal else []
        except Exception as e:
            messagebox.showerror("検索エラー", f"{e}"); rows = []

        tree.delete(*tree.get_children())

        for r in rows:
            tree.insert("", tk.END, values=[r["player_id"], r["name"], r["regions"]])
    #-----┘
    load("", "", "")
#=====================================================================
