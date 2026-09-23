# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\sub_window.py

import tkinter as tk
from tkinter             import ttk, messagebox
from Helpers.Custum_func import cFr, cLbl, cBtn
import Dal as dal

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

MAIN_BG = "#F0F4FA"

REGIONS = [ "",     "群馬", "埼玉", "東京", "静岡", "愛知", "三国", "三重", "滋賀", "大阪",
            "兵庫", "広島", "徳島", "香川", "岡山", "山口", "福岡", "佐賀", "長崎"          ]
#=====================================================================
def open_player_picker(self):

    style = ttk.Style()
    style.configure( "PP.TButton", font=(MUI,9), anchor="center")
    style.configure("PP.Treeview", font=(MUI,10))
    style.configure("PP.Treeview.Heading", font=(MUI,10))
    style.configure("PP.TCombobox", font=(MUI,10))

    fnt = dict(font=(MUI,9))

    win = tk.Toplevel(self, bg=MAIN_BG)
    win.title("選手選択")
    win.geometry("500x500+730+320")
    win.transient(self)
    win.grab_set()

    # 右：フィルタバー
    bar = cFr(win, bg=MAIN_BG); bar.pack(fill=tk.BOTH, side=tk.RIGHT, padx=8, pady=6)
    bar.Rconf(12, W=1)

    # キーワード
    row1 = cFr(bar);          row1._grid(R=0, C=0, Stk="nswe", px=5, py=10)
    cLbl(row1, text="検索", **fnt)._grid(R=0, C=0, Stk="nswe")
    ent_kw = ttk.Entry(row1, width=16, font=(MUI,11)); ent_kw.grid(row=0, column=1, sticky="w", padx=4)

    # 登番
    row2 = cFr(bar); row2._grid(R=1, C=0, Stk="nswe", px=5, py=10)
    cLbl(row2, text="登番", **fnt)._grid(R=0, C=0, Stk="w")
    groups = [""] + [f"{i:04d}" for i in range(0, 6000, 1000)]
    cbo_grp = ttk.Combobox(row2, values=groups, state="readonly", width=10, font=(MUI,10))
    cbo_grp.grid(row=0, column=1, sticky="w", padx=(4,10))

    # 支部
    row3 = cFr(bar); row3._grid(R=2, C=0, Stk="nswe", px=5, py=10)
    cLbl(row3, text="支部", **fnt)._grid(R=0, C=0, Stk="w")
    cbo_reg = ttk.Combobox(row3, values=REGIONS, state="readonly", width=8, font=(MUI,10))
    cbo_reg.grid(row=0, column=1, sticky="w", padx=(4,6))

    #-----┐
    def do_search(*_):
        load(ent_kw.get().strip(), cbo_grp.get().strip(), cbo_reg.get().strip())
    #-----┘
    ttk.Button( bar, text="検索", command=do_search, style="PP.TButton"
               ).grid(row=3, column=0, sticky="nswe", padx=(0,0), pady=(20,0))
    btns = cFr(bar); btns._grid(R=12, C=0, Stk="nswe", px=5, py=10)
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
    ttk.Button( btns, text="決 定", command=apply_selection, style="PP.TButton",
               ).grid(row=0, column=0, sticky="we", padx=4, pady=4)
    ttk.Button( btns, text="閉じる", command=win.destroy, style="PP.TButton",
               ).grid(row=1, column=0, sticky="we", padx=4, pady=4)

    # 結果ツリー
    cols = ("登番", "選手名", "所属支部")
    tree = ttk.Treeview(win, columns=cols, show="headings", style="PP.Treeview")

    for c, w in zip(cols, (50, 130, 60)):
        tree.heading(c, text=c)
        tree.column(c, width=w, anchor="center")

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
