# ------------------------------------------------------------------------------
# ============================  DBクエリ画面 ===================================

from __future__ import annotations
from tkinter    import ttk, messagebox
import tkinter as tk
import sqlite3

VENUES   = ["桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",
            "津",   "三国", "びわこ", "住之江", "尼崎",   "鳴門",   "丸亀", "児島",
            "宮島", "徳山", "下関",   "若松",   "芦屋",   "福岡",   "唐津", "大村", ]

GRADE    = ["SG", "PG1", "G1", "G2", "G3", "一般"]
GRADE_N  = {"SG":5, "PG1":4, "G1":3, "G2":2, "G3":1, "一般":0}

REGIONS  = ["", "群馬", "埼玉", "東京", "静岡", "愛知", "三重", "福井", "滋賀", "大阪",
                "兵庫", "岡山", "広島", "徳島", "香川", "山口", "福岡", "長崎", "佐賀"  ]
NUM1TO6  = ["", 1, 2, 3, 4, 5, 6]
WINMOVE  = ["", "逃げ", "差し", "まくり", "まくり差し", "抜き", "恵まれ"]
TABLES   = ["Players", "Season_result", "Races", "Race_entries", "Venues"]
FINAL    = ["", "0", "1"]

# ==============================================================================
class DBQueryScreen(ttk.Frame):

    def __init__(self, parent, app:App, db_path:str):
        super().__init__(parent)

        self.app     = app
        self.db_path = db_path

        root  = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        left  = ttk.Frame(root) ; root.add( left, weight= 1)
        right = ttk.Frame(root) ; root.add(right, weight=20)

        root.pack(fill=tk.BOTH, expand=True)

        # =============== 条件パネル =============
        cond = ttk.Frame(left) ; cond.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ① 期間
        sec1 = ttk.LabelFrame(cond, text="① 期間") ; sec1.pack(fill=tk.X, pady=(0,8))

        self.var_en_date = tk.BooleanVar(value=False)
        ttk.Checkbutton(sec1, variable=self.var_en_date).grid(row=0, column=0, padx=8)

        years  = [""] + [str(y) for y in [2026 - i for i in range(20)]]
        months = [""] + [str(m) for m in range(1, 13)]
        days   = [""] + [str(d) for d in range(1, 32)]

        ttk.Label(sec1, text="年").grid(row=0, column= 2, sticky="w")
        ttk.Label(sec1, text="月").grid(row=0, column= 4, sticky="w")
        ttk.Label(sec1, text="日").grid(row=0, column= 6, sticky="w")
        ttk.Label(sec1, text="～").grid(row=0, column= 7, sticky="w", padx=5)
        ttk.Label(sec1, text="年").grid(row=0, column= 9, sticky="w")
        ttk.Label(sec1, text="月").grid(row=0, column=11, sticky="w")
        ttk.Label(sec1, text="日").grid(row=0, column=13, sticky="w")

        self.cbo_f_y = ttk.Combobox(sec1, values=years,  state="readonly", width=6)
        self.cbo_f_m = ttk.Combobox(sec1, values=months, state="readonly", width=3)
        self.cbo_f_d = ttk.Combobox(sec1, values=days,   state="readonly", width=3)
        self.cbo_t_y = ttk.Combobox(sec1, values=years,  state="readonly", width=6)
        self.cbo_t_m = ttk.Combobox(sec1, values=months, state="readonly", width=3)
        self.cbo_t_d = ttk.Combobox(sec1, values=days,   state="readonly", width=3)

        self.cbo_f_y.grid(row=0, column= 1, sticky="w", padx=(2,0))
        self.cbo_f_m.grid(row=0, column= 3, sticky="w", padx=(2,0))
        self.cbo_f_d.grid(row=0, column= 5, sticky="w", padx=(2,0))
        self.cbo_t_y.grid(row=0, column= 8, sticky="w", padx=(2,0))
        self.cbo_t_m.grid(row=0, column=10, sticky="w", padx=(2,0))
        self.cbo_t_d.grid(row=0, column=12, sticky="w", padx=(2,0))

        # ② レース条件（Races）
        sec2 = ttk.LabelFrame(cond, text="② レース条件")
        sec2.pack(fill=tk.X, pady=(0,8))

        r1 = ttk.Frame(sec2) ; r1.grid(row=0, column=1, sticky="w")

        self.var_en_race = tk.BooleanVar(value=False)
        ttk.Checkbutton( sec2, variable=self.var_en_race).grid(row=0, column=0,
                                                    sticky="w", padx=8, pady=5 )

        ttk.Label(r1, text="開催場").grid(row=0, column=0, sticky="w", padx=5, pady=6)
        ttk.Label(r1, text="ｸﾞﾚｰﾄﾞ").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Label(r1, text="優勝戦").grid(row=0, column=4, sticky="w", padx=(15, 5))

        self.cbo_venue = ttk.Combobox(r1, values=VENUES, state="readonly", width=8)
        self.cbo_grade = ttk.Combobox(r1, values=GRADE,  state="readonly", width=8)
        self.cbo_final = ttk.Combobox(r1, values=FINAL,  state="readonly", width=6)

        self.cbo_venue.grid(row=0, column=1, sticky="w", padx=(0, 5))
        self.cbo_grade.grid(row=0, column=3, sticky="w", padx=(0, 5))
        self.cbo_final.grid(row=0, column=5, sticky="w")
        self.cbo_final.current(0)

        r2 = ttk.Frame(sec2) ; r2.grid(row=1, column=1, sticky="w")

        ttk.Label(r2, text="風速"  ).grid(row=1, column=0, sticky="w",padx=5, pady=6)
        ttk.Label(r2, text="m  ～ ").grid(row=1, column=2, sticky="w")
        ttk.Label(r2, text="m"     ).grid(row=1, column=4, sticky="w")

        self.ent_wind_min = ttk.Entry(r2, width=6)
        self.ent_wind_max = ttk.Entry(r2, width=6)

        self.ent_wind_min.grid(row=1, column=1, sticky="w")
        self.ent_wind_max.grid(row=1, column=3, sticky="w")

        # ③ 対象（Players）
        self._regions = REGIONS
        sel_types     = ["登録番号", "選手名", "所属支部", "登録期"]

        sec3 = ttk.LabelFrame(cond) ; sec3.pack(fill=tk.X)

        boxA = ttk.LabelFrame(sec3, text="③ 対象A")
        boxB = ttk.LabelFrame(sec3, text="対象B")

        boxA.grid(row=0, column=0, sticky="nsew", padx=6)
        boxB.grid(row=0, column=1, sticky="nsew", padx=6)

        self.var_selA = tk.StringVar(value="登録番号")
        self.var_selB = tk.StringVar(value="登録番号")

        self._build_target_box(boxA, "A", self.var_selA, sel_types, self._regions)
        self._build_target_box(boxB, "B", self.var_selB, sel_types, self._regions, off=1)

        self.var_enableB = tk.BooleanVar(value=False)

        ttk.Checkbutton(boxB, variable=self.var_enableB).grid(row=0, column=0, padx=6)

        sec3.grid_columnconfigure(0, weight=1) ; sec3.grid_columnconfigure(1, weight=1)

        # ④ レース詳細（Race_entries）
        detA = ttk.LabelFrame(sec3, text="④ 条件A")
        detB = ttk.LabelFrame(sec3, text="条件B")
        detA.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        detB.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

        frA1 = ttk.Frame(detA) ; frA1.grid(row=0, column=0, sticky="nsew")
        frA2 = ttk.Frame(detA) ; frA2.grid(row=1, column=0, sticky="nsew")
        frB1 = ttk.Frame(detB) ; frB1.grid(row=0, column=0, sticky="nsew")
        frB2 = ttk.Frame(detB) ; frB2.grid(row=1, column=0, sticky="nsew")

        self.entA_course = self._labeled_entry(frA1, "ｺｰｽ   ", 0, 0, NUM1TO6, px=0, w=4)
        self.entA_frank  = self._labeled_entry(frA1, "着",     0, 2, NUM1TO6, px=0, w=4)
        self.entA_wmove  = self._labeled_entry(frA2, "決り手", 1, 1, WINMOVE, x=-1, w=10)
        self.entB_course = self._labeled_entry(frB1, "ｺｰｽ   ", 0, 0, NUM1TO6, px=0, w=4)
        self.entB_frank  = self._labeled_entry(frB1, "着",     0, 2, NUM1TO6, px=0, w=4)
        self.entB_wmove  = self._labeled_entry(frB2, "決り手", 1, 1, WINMOVE, x=-1, w=10)

        sec5 = ttk.LabelFrame(cond, text="⑤ 出力選択")
        sec5.pack(fill=tk.X, padx=0, pady=(0,8))

        self._out_vars = {} ; self._chkB_widgets = []
        # --------------------
        def make_chk(row, col, key, text, default=True, isB=False):

            var = tk.BooleanVar(value=default)
            chk = ttk.Checkbutton(sec5, text=text, variable=var)
            chk.grid(row=row, column=col, sticky="w", padx=6, pady=2)

            self._out_vars[key] = var
            if isB: self._chkB_widgets.append(chk)
        # --------------------
        make_chk(1,0,"venue_id",      "開催場",     False)
        make_chk(1,1,"grade",         "グレード",   False)
        make_chk(1,2,"is_final",      "優勝戦",     False)
        make_chk(1,3,"wind_spd",      "風速",       False)

        make_chk(2,0,"A_regions",     "A 所属支部", False)
        make_chk(2,1,"A_name",        "A 選手名",   True)
        make_chk(2,2,"A_course",      "A コース",   True)
        make_chk(2,3,"A_finish_rank", "A 着順",     True)
        make_chk(2,4,"A_win_move",    "A 決まり手", False)
        make_chk(3,0,"B_regions",     "B 所属支部", False,True)
        make_chk(3,1,"B_name",        "B 選手名",   True, True)
        make_chk(3,2,"B_course",      "B コース",   True, True)
        make_chk(3,3,"B_finish_rank", "B 着順",     True, True)
        make_chk(3,4,"B_win_move",    "B 決まり手", False, True)

        #make_chk(2,0,"A_player_id",   "A 登録番号", False)
        #make_chk(3,0,"B_player_id",   "B 登録番号", False,True)
        # --------------------
        def on_toggle_B(*_):
            state = ("!disabled" if self.var_enableB.get() else "disabled")
            for w in self._chkB_widgets: w.state([state])
        # --------------------
        self.var_enableB.trace_add("write", on_toggle_B); on_toggle_B()

        bar = ttk.Frame(cond) ; bar.pack(fill=tk.X, padx=0, pady=(0,8))
        self.var_output = tk.StringVar(value="list")

        ttk.Radiobutton( bar, text= "レコード一覧", value="list",
                          variable= self.var_output       ).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton( bar, text= "レコード数",   value="count",
                          variable= self.var_output       ).pack(side=tk.LEFT, padx=6)
        ttk.Button(      bar, text= "実行",
                           command= self._run             ).pack(side=tk.LEFT, padx=10)
        ttk.Button(      bar, text= "条件クリア",
                           command= self._clear_conditions).pack(side=tk.LEFT, padx=6)
        ttk.Button(      bar, text= "出力クリア",
                           command= self._clear_output    ).pack(side=tk.LEFT, padx=6)

        # ============== 出力パネル ==============
        out_top = ttk.Frame(right); out_top.pack(fill=tk.X, padx=8, pady=4)

        self.lbl_info = ttk.Label(out_top, text="")
        self.tree     = ttk.Treeview(right, show="headings")

        self.lbl_info.pack(side=tk.LEFT, padx=4)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,4))

        ysb = ttk.Scrollbar(right, orient=tk.VERTICAL,   command=self.tree.yview)
        xsb = ttk.Scrollbar(right, orient=tk.HORIZONTAL, command=self.tree.xview)

        ysb.pack(fill=tk.Y, side=tk.RIGHT) ; xsb.pack(fill=tk.X, side=tk.BOTTOM)

        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self._col_widths = { "日付":95, "開催場":70, "ｸﾞﾚｰﾄﾞ":65, "優勝戦":65, "風速":50,
                             "A 支部":70, "A 選手名":130, "A ｺｰｽ":50, "A 着順":55,
                             "A 決り手":70,
                             "B 支部":70, "B 選手名":130, "B ｺｰｽ":55, "B 着順":55,
                             "B 決り手":70,                                            }
    # ==========================================================================
    # ----- 共通UIヘルパ -----
    def _labeled_entry(self, parent, text, r, c, val, x=1, px=5,  w:int=12):

        ttk.Label(parent, text=text).grid(row=r, column=c+x, sticky="w", padx=px, pady=5)
        comb = ttk.Combobox(parent, values=val, state="readonly", width=w)
        comb.grid(row=r, column=c, sticky="w", padx=5, pady=5)

        return comb
    # ---- ユーティリティ ----
    def _ymd(self, ycb:ttk.Combobox, mcb:ttk.Combobox, dcb:ttk.Combobox):
        y = ycb.get().strip(); m = mcb.get().strip(); d = dcb.get().strip()
        if y and m and d:
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

        return ""
    # -------- DB ------------
    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=30)
        con.execute("PRAGMA foreign_keys=ON;")

        return con
    #-------------------------------------------------------
    def _build_target_box(self, parent, tag, var_sel, sel_types, regions, off:int=0):

        c     = off
        cbo   = ttk.Combobox( parent, values=sel_types, state="readonly",
                                           width=11, textvariable=var_sel )
        ent   = ttk.Entry(parent, width=12)
        btn   = ttk.Button(parent, text="検索", width=7, command=lambda:self._player_pick(tag))
        cbo_r = ttk.Combobox(parent, values=regions, state="readonly", width=10)

        cbo.grid(  row=0, column=c,   sticky="w", padx=(5,10), pady=0)
        ent.grid(  row=1, column=c,   sticky="w", padx=5,      pady=5)
        btn.grid(  row=0, column=c+1, sticky="e")
        cbo_r.grid(row=2, column=c,   sticky="w", padx=5,      pady=5)

        ttk.Label(parent, text="支部").grid(row=2, column=c+1, sticky="w")

        if tag == "A":
            self.cboA_type, self.entA_val, self.cboA_regions = cbo, ent, cbo_r
        else:
            self.cboB_type, self.entB_val, self.cboB_regions = cbo, ent, cbo_r
        # ----------
        def on_type_changed(*_):
            sel     = var_sel.get()
            is_text = (sel in ("登録番号", "選手名", "登録期"))

            if tag == "A":
                self.entA_val.configure(state="normal" if is_text else "disabled")
                self.cboA_regions.configure( state="readonly"
                                             if sel == "所属支部" else "disabled" )
            else:
                self.entB_val.configure(state="normal" if is_text else "disabled")
                self.cboB_regions.configure( state="readonly"
                                             if sel == "所属支部" else "disabled" )
        # ----------
        cbo.bind("<<ComboboxSelected>>", on_type_changed)
        on_type_changed()

    # ------------------ 選手ピッカー ----------------------
    def _player_pick(self, tag:str):
        # ----------
        def parse_group(text:str):
            if "?" in text:
                a,b = text.split("?",1)
                try: return int(a), int(b)
                except ValueError: return None
            return None
        # ----------
        def do_search(*_):
            load(ent_kw.get().strip(), cbo_grp.get().strip(), cbo_reg.get().strip())
        # ----------
        def apply_selection():
            sel = tree.selection()
            if not sel: win.destroy(); return
            pid = tree.item(sel[0], "values")[0]
            if tag == "A":
                self.cboA_type.set("登録番号")
                self.entA_val.delete(0, tk.END); self.entA_val.insert(0, pid)
            else:
                self.cboB_type.set("登録番号")
                self.entB_val.delete(0, tk.END); self.entB_val.insert(0, pid)
            win.destroy()
        # ----------
        win = tk.Toplevel(self)
        win.title("選手選択")
        win.geometry("500x500+730+320")
        win.transient(self.winfo_toplevel())
        win.grab_set()
        groups = [""] + [f"{i:04d}" for i in range(0, 6000, 1000)]

        bar     = ttk.Frame(   win)
        row1    = ttk.Frame(   bar)
        row2    = ttk.Frame(   bar)
        row3    = ttk.Frame(   bar)
        ent_kw  = ttk.Entry(   row1, width=16)
        cbo_grp = ttk.Combobox(row2, values=groups, state="readonly", width=10)
        cbo_reg = ttk.Combobox(row3, values=[""] + REGIONS, state="readonly", width=8)
        btns    = ttk.Frame(   bar)

        bar.pack(fill=tk.BOTH, side =tk.RIGHT, padx=8, pady=6)
        row1.grid(  row= 0, column=0, sticky="nswe", padx=5, pady=10)
        row2.grid(  row= 1, column=0, sticky="nswe", padx=5, pady=10)
        row3.grid(  row= 2, column=0, sticky="nswe", padx=5, pady=10)
        ent_kw.grid(row= 0, column=1, sticky="w",    padx=4         )
        btns.grid(  row=12, column=0, sticky="nswe", padx=5, pady=10)
        cbo_grp.grid(row=0, column=1, sticky="w",    padx=(4,10)    )
        cbo_reg.grid(row=0, column=1, sticky="w",    padx=(4,6)     )

        ent_kw.bind("<Return>", do_search)

        bar.grid_rowconfigure(12, weight=1)

        ttk.Label(row1, text="氏名").grid(row=0, column=0, sticky="nswe")
        ttk.Label(row2, text="登番").grid(row=0, column=0, sticky="w"   )
        ttk.Label(row3, text="支部").grid(row=0, column=0, sticky="w"   )

        ttk.Button( bar, text="検索", command=do_search
                   ).grid(row=3, column=0, sticky="w", padx=5, pady=10)
        ttk.Button(btns, text="OK", command=apply_selection).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="キャンセル", command=win.destroy).pack(side=tk.RIGHT)

        cols = ("登番","名前","支部")
        tree = ttk.Treeview(win, columns=cols, show="headings")

        for c,w in zip(cols, (60,140,50)):
            tree.heading(c, text=c) ; tree.column(c, width=w, anchor=tk.W)

        ysb = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=ysb.set)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(8,0), pady=(0,8))
        ysb.pack(fill=tk.Y, side=tk.LEFT, padx=(0,8), pady=(0,8))

        tree.bind("<Double-1>", lambda e: apply_selection())
        # ----------
        def load(keyword:str, group_text:str, region_text:str):

            sql    = ( "SELECT player_id, name, COALESCE(regions,'') FROM Players WHERE 1=1 " )
            params = []

            if keyword:
                sql    += "AND (player_id = ? OR name LIKE ?) "
                params += [keyword, f"%{keyword}%"]

            if group_text:
                sql    += "AND CAST(player_id AS INTEGER) BETWEEN ? AND ? "
                params += group_text, int(group_text) + 999

            if region_text:
                sql    += "AND regions = ? "
                params += [region_text]

            sql += "ORDER BY CAST(player_id AS INTEGER) LIMIT 1000;"

            try:
                with self._connect() as con:
                    rows = con.execute(sql, params).fetchall()
            except Exception as e:
                messagebox.showerror("読み込みエラー", f"{e}", parent=win); return

            tree.delete(*tree.get_children())
            for r in rows: tree.insert("", tk.END, values=r)
        #-----------
        load("", "", "")
        ent_kw.focus_set()

    # ----------------------- 実行 -------------------------
    def _run(self):

        try:
            sql, params, columns = self._build_query()
        except ValueError as e:
            messagebox.showwarning("条件エラー", str(e)); return

        is_count = (self.var_output.get() == "count")
        q = f"SELECT COUNT(1) FROM ({sql}) AS q;" if is_count else (sql + " LIMIT 500")
        try:
            with self._connect() as con:
                cur  = con.execute(q, params)
                rows = cur.fetchall()
                cols = ( ["count"] if is_count else ( columns
                                   if  columns else [ d[0] for d in cur.description ] ) )
        except Exception as e:
            messagebox.showerror("クエリ実行エラー", f"{e}") ; return

        if is_count:
            self._reset_tree(["count"])
            self.tree.insert("", tk.END, values=[rows[0][0] if rows else 0])
            self.lbl_info.config(text=f"件数: {rows[0][0] if rows else 0}")
        else:
            if "開催場" in cols:
                vidx       = cols.index("開催場")
                cols[vidx] = "開催場"
                #-------------
                def vid_to_name(v):
                    try:
                        vi = int(v)
                        return VENUES[vi-1] if 1 <= vi <= len(VENUES) else v
                    except Exception: return v
                #-------------
                rows = [ tuple( vid_to_name(v) if i==vidx else v for i, v in enumerate(r)
                               ) for r in rows ]

            self._reset_tree(cols)
            for r in rows:
                self.tree.insert("", tk.END, values=r)

            self.lbl_info.config(text=f"{len(rows)} 行（上限500件）")

    # ------------------------------------------------------
    def _reset_tree(self, columns):

        for c in self.tree["columns"]: self.tree.heading(c, text="")

        self.tree["columns"] = columns

        for c in columns:
            self.tree.heading(c, text=c)
            w = self._col_widths.get(c, 120)
            self.tree.column(c, width=w, anchor="center", stretch=False)

        for i in self.tree.get_children(): self.tree.delete(i)
    #-------------------------------------------------------
    def _sql(self, r, c):
        return f"(SELECT {c} FROM Players WHERE player_id = re{r}.player_id) AS {r}_{c}"
    #-------------------------------------------------------
    def _selected_output_cols(self, use_B:bool):

        select_exprs = ["r.date AS date"] ; headers = ["日付"]

        mapping_common = { "venue_id":("r.venue_id", "開催場"),
                              "grade":("r.grade",    "ｸﾞﾚｰﾄﾞ"),
                           "is_final":("r.is_final", "優勝戦"),
                           "wind_spd":("r.wind_spd", "風速"  )  }

        mapping_A = {     "A_regions":(f"{self._sql("A", "regions")}",     "A 支部"  ),
                             "A_name":(f"{self._sql("A", "name")}",        "A 選手名"),
                        "A_player_id":("reA.player_id AS A_player_id",     "A 登番"  ),
                           "A_course":("reA.course AS A_course",           "A ｺｰｽ"   ),
                      "A_finish_rank":("reA.finish_rank AS A_finish_rank", "A 着順"  ),
                         "A_win_move":("reA.win_move AS A_win_move",       "A 決り手"), }

        mapping_B = {     "B_regions":(f"{self._sql("B", "regions")}",       "B 支部"),
                             "B_name":(f"{self._sql("B", "name")}",        "B 選手名"),
                        "B_player_id":("reB.player_id AS B_player_id",     "B 登番"  ),
                           "B_course":("reB.course AS B_course",           "B ｺｰｽ"   ),
                      "B_finish_rank":("reB.finish_rank AS B_finish_rank", "B 着順"  ),
                         "B_win_move":("reB.win_move AS B_win_move",       "B 決り手"), }
        #-----------
        def add(mapping):

            for k,(expr,hdr) in mapping.items():
                v=self._out_vars.get(k); 
                if v and v.get(): select_exprs.append(expr); headers.append(hdr)
        #-----------
        add(mapping_common)
        add(mapping_A)
        if use_B: add(mapping_B)

        return select_exprs, headers

    # ------------------------- クエリ構築 ---------------------------
    def _build_query(self):

        use_B = self.var_enableB.get()
        typA  = self.cboA_type.get()
        valA  = ( self.cboA_regions.get() if self.cboA_type.get()=="所属支部"
                                             else self.entA_val.get().strip() )
        typB  = self.cboB_type.get()
        valB  = ( self.cboB_regions.get() if self.cboB_type.get()=="所属支部"
                                             else self.entB_val.get().strip() )

        if not typA:
            raise ValueError("対象Aの識別カラムを選択してください。")
        if typA in ("登録番号","選手名","登録期") and valA == "":
            raise ValueError("対象Aの値を入力してください。")
        if typA == "所属支部" and valA == "":
            raise ValueError("対象Aの地域を選択してください。")
        if use_B:
            if typA != typB: raise ValueError("A/Bは同種カラムの組合せのみ有効です。")
            if typB in ("登録番号","選手名","登録期") and (valB.strip() == ""):
                raise ValueError("対象Bの値を入力してください。")
            if typB == "所属支部" and valB == "":
                raise ValueError("対象Bの地域を選択してください。")

        detA = {      "course":self.entA_course.get().strip(),
                 "finish_rank":self.entA_frank.get().strip(),
                    "win_move":self.entA_wmove.get().strip()  }

        detB = {      "course":self.entB_course.get().strip(),
                 "finish_rank":self.entB_frank.get().strip(),
                    "win_move":self.entB_wmove.get().strip()   }

        use_date  = self.var_en_date.get()
        from_s    = self._ymd(self.cbo_f_y, self.cbo_f_m, self.cbo_f_d)
        to_s      = self._ymd(self.cbo_t_y, self.cbo_t_m, self.cbo_t_d)

        use_races = self.var_en_race.get()
        venue_txt = self.cbo_venue.get()
        grade_txt = self.cbo_grade.get()
        v_final   = self.cbo_final.get().strip()
        v_wmin    = self.ent_wind_min.get().strip()
        v_wmax    = self.ent_wind_max.get().strip()
        v_venue   = VENUES.index(venue_txt)+1 if venue_txt else None
        v_grade   = GRADE_N[grade_txt] if grade_txt else None

        params  = []
        where_r = [] ; whereA_e = [] ; whereB_e = [] ; whereA_p = [] ; whereB_p = []
        #-----------
        def build_player_where(alias, typ, val, out):

            if   typ == "登録番号":
                out.append(f"{alias}.player_id = ?")     ; params.append(val)
            elif typ ==   "選手名":
                out.append(f"{alias}.name LIKE ?")       ; params.append(f"%{val}%")
            elif typ == "所属支部":
                out.append(f"{alias}.regions = ?")       ; params.append(val)
            elif typ ==   "登録期":
                out.append(f"{alias}.regist_period = ?") ; params.append(val)
        #-----------
        def add_entry_details(alias, det, out):
            if det["course"]:
                out.append(f"{alias}.course = ?");      params.append(det["course"])
            if det["finish_rank"]:
                out.append(f"{alias}.finish_rank = ?"); params.append(det["finish_rank"])
            if det["win_move"]:
                out.append(f"{alias}.win_move = ?");     params.append(det["win_move"])
        #-----------
        build_player_where("pA", typA, valA, whereA_p)
        if use_B: build_player_where("pB", typB, valB, whereB_p)

        add_entry_details("reA", detA, whereA_e)

        if use_B: add_entry_details("reB", detB, whereB_e)

        if use_races:
            if v_venue: where_r.append("r.venue_id = ?") ; params.append(v_venue)
            if v_grade: where_r.append("r.grade = ?")    ; params.append(v_grade)
            if v_final in ("0","1"): 
                where_r.append("r.is_final = ?")
                params.append(int(v_final))
            if v_wmin and v_wmax:
                where_r.append("r.wind_spd BETWEEN ? AND ?")
                params.extend([v_wmin, v_wmax])
            elif v_wmin:
                where_r.append("r.wind_spd >= ?")
                params.append(v_wmin)
            elif v_wmax:
                where_r.append("r.wind_spd <= ?")
                params.append(v_wmax)

        if use_date and (from_s or to_s):
            col = "r.date"
            if from_s and to_s:
                where_r.append(f"{col} BETWEEN ? AND ?"); params.extend([from_s, to_s])
            elif from_s:
                where_r.append(f"{col} >= ?"); params.append(from_s)
            elif to_s:
                where_r.append(f"{col} <= ?"); params.append(to_s)

        select_exprs, headers = self._selected_output_cols(use_B)

        if use_B:
            sql = f"""
                SELECT {", ".join(select_exprs)}
                  FROM Race_entries reA
                  JOIN Players pA
                    ON pA.player_id = reA.player_id
                  JOIN Race_entries reB
                    ON reB.race_id  = reA.race_id
                  JOIN Players pB
                    ON pB.player_id = reB.player_id
                  JOIN Races r
                    ON r.race_id    = reA.race_id
                """
            where_all = []
            if whereA_p: where_all += whereA_p
            if whereB_p: where_all += whereB_p
            if whereA_e: where_all += whereA_e
            if whereB_e: where_all += whereB_e
            if where_r : where_all += where_r
            if where_all:      sql += " WHERE " + " AND ".join(where_all)

            columns = headers

        else:
            sql = f"""
                SELECT {", ".join([e for e in select_exprs if not e.startswith("reB.")])}
                  FROM Race_entries reA
                  JOIN Players pA
                    ON pA.player_id = reA.player_id
                  JOIN Races r
                    ON r.race_id    = reA.race_id
                """

            where_all = []
            if  whereA_p: where_all += whereA_p
            if  whereA_e: where_all += whereA_e
            if   where_r: where_all += where_r
            if where_all:       sql += " WHERE " + " AND ".join(where_all)

            columns = [h for h in headers if not h.startswith("B_")]

        return sql.strip(), params, columns

    # ------------------------- クリア -------------------------------
    def _clear_conditions(self):

        self.var_en_date.set(False)
        for cb in ( self.cbo_f_y, self.cbo_f_m, self.cbo_f_d,
                    self.cbo_t_y, self.cbo_t_m, self.cbo_t_d  ): cb.set("")

        self.var_en_race.set(False        )
        self.cbo_venue.delete(   0, tk.END)
        self.cbo_grade.delete(   0, tk.END)
        self.cbo_final.current(  0        )
        self.ent_wind_min.delete(0, tk.END)
        self.ent_wind_max.delete(0, tk.END)
        self.var_selA.set("登録番号"      )
        self.entA_val.delete(    0, tk.END)
        self.cboA_regions.set(  ""        )
        self.var_enableB.set(False        )
        self.var_selB.set("登録番号"      )
        self.entB_val.delete(    0, tk.END)
        self.cboB_regions.set(  ""        )

        for w in (self.entA_course, self.entA_frank, self.entA_wmove,
                  self.entB_course, self.entB_frank, self.entB_wmove): w.delete(0,tk.END)
        for var in self._out_vars.values(): var.set(True)
    #---------------
    def _clear_output(self):
        self.lbl_info.config(text=""); self._reset_tree([])
    #---------------
    def _clear(self):
        self._clear_conditions(); self._clear_output()
    #---------------
