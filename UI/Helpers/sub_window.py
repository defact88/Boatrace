# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\sub_window.py

import tkinter as tk
from tkinter    import ttk, messagebox
import Dal as dal

def open_player_picker(self):

    win = tk.Toplevel(self)
    win.title("選手選択")
    win.geometry("500x500+730+320")
    win.transient(self)
    win.grab_set()

    # 右：フィルタバー
    bar = ttk.Frame(win); bar.pack(fill=tk.BOTH, side=tk.RIGHT, padx=8, pady=6)
    bar.grid_rowconfigure(12, weight=1)

    # 検索キーワード
    row1 = ttk.Frame(bar); row1.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
    ttk.Label(row1, text="検索").grid(row=0, column=0, sticky="nswe")
    ent_kw = ttk.Entry(row1, width=16); ent_kw.grid(row=0, column=1, sticky="w", padx=4)

    # 1000番グループ
    row2 = ttk.Frame(bar); row2.grid(row=1, column=0, sticky="nswe", padx=5, pady=10)
    ttk.Label(row2, text="登番").grid(row=0, column=0, sticky="w")
    groups = [""] + [f"{i:04d}" for i in range(0, 6000, 1000)]
    cbo_grp = ttk.Combobox(row2, values=groups, state="readonly", width=10)
    cbo_grp.grid(row=0, column=1, sticky="w", padx=(4,10))

    # 支部プルダウン（DBからDistinct取得）
    row3 = ttk.Frame(bar); row3.grid(row=2, column=0, sticky="nswe", padx=5, pady=10)
    ttk.Label(row3, text="支部").grid(row=0, column=0, sticky="w")
    reg_vals = [""]
    try:
        rows = dal.fetch_all("SELECT DISTINCT regions AS r FROM Players "
                             "WHERE r IS NOT NULL AND TRIM(r)<>'' ORDER BY r")
        reg_vals += [r["r"] for r in rows]
    except Exception:
        pass
    cbo_reg = ttk.Combobox(row3, values=reg_vals, state="readonly", width=8)
    cbo_reg.grid(row=0, column=1, sticky="w", padx=(4,6))

    # 検索ボタン
    def do_search(*_):
        load(ent_kw.get().strip(), cbo_grp.get().strip(), cbo_reg.get().strip())
    ttk.Button(bar, text="検索", command=do_search).grid(row=3, column=0, sticky="w", padx=5, pady=10)

    # 決定/閉じる
    btns = ttk.Frame(bar); btns.grid(row=12, column=0, sticky="nswe", padx=5, pady=10)
    def apply_selection():
        sel = tree.selection()
        if not sel:
            win.destroy(); return
        pid = tree.item(sel[0], "values")[0]
        try: pid = int(pid)
        except Exception: pass
        self.open_p_analys(pid)
        win.destroy()
    ttk.Button(btns, text="決 定", command=apply_selection).grid(row=0, column=0, sticky="we", padx=4, pady=4)
    ttk.Button(btns, text="閉じる", command=win.destroy).grid(row=1, column=0, sticky="we", padx=4, pady=4)

    # 左：結果ツリー
    cols = ("player_id", "name", "regions")
    tree = ttk.Treeview(win, columns=cols, show="headings")
    for c, w in zip(cols, (60, 140, 50)):
        tree.heading(c, text=c); tree.column(c, width=w, anchor=tk.W)
    ysb = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=ysb.set)
    tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(8,0), pady=(0,8))
    ysb.pack(fill=tk.Y, side=tk.LEFT, padx=(0,8), pady=(0,8))
    tree.bind("<Double-1>", lambda e: apply_selection())
    ent_kw.bind("<Return>", do_search)

    # ロード処理
    def load(keyword: str, group_text: str, region_text: str):
        sql = ("SELECT player_id, name, COALESCE(regions,'') AS regions "
               "FROM Players WHERE 1=1 ")
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

    load("", "", "")
