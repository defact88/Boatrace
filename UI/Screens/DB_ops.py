# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\DB_ops.py

from tkinter             import ttk, messagebox
from datetime            import datetime, timedelta, timezone, date
from pathlib             import Path
from Helpers.Custum_func import cFr, cLbl
import threading, subprocess, sys, sqlite3, tkinter as tk

VENUES   = [ "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",
             "津",   "三国", "びわこ", "住之江", "尼崎",   "鳴門",   "丸亀", "児島",
             "宮島", "徳山", "下関",   "若松",   "芦屋",   "福岡",   "唐津", "大村", ]
VENUE_ID = {name: i+1 for i, name in enumerate(VENUES)}

IMPORT_B = r"C:\boatrace\import_B_txt.py"

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

BG_COLOR = "#F0F4FA"

#=====================================================================
class DBOpsScreen(ttk.Frame):

    def __init__(self, parent, app, db_path):
        super().__init__(parent)

        self.app            = app
        self.db_path        = db_path
        self._tables_cache  = []
        self.cols1          = []
        self.cols2          = []

        self.app.option_add("*TCombobox*Listbox*Font", (MUI,9)) 

        fnt   = dict(font=(GUI,10), bg=BG_COLOR)

        style = ttk.Style()

        style.configure("TLabelframe", background=BG_COLOR, font=(GUI,9,BD))
        style.configure( "r.Treeview", background="#222222", 
                                       foreground="white", 
                                  fieldbackground="black"  )

        # ================= UI 構成 =================
        main_frame = cFr(self, bg=BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ops = cFr(main_frame, bg=BG_COLOR)
        ops.pack(fill=tk.X, padx=20, pady=(6,6))

        # --- 検索設定エリア (左側) ---
        ops_L = cFr(ops, bg=BG_COLOR)
        ops_L.grid(row=0, column=0, sticky="nw")

        # T1 FROM
        cLbl(ops_L, text="FROM", **fnt).grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.cbo_table1 = ttk.Combobox(ops_L, values=[], width=15, state="readonly", justify='center', font=(GUI,10))
        self.cbo_table1.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        self.cbo_table1.bind("<<ComboboxSelected>>", self._on_t1_changed)

        # T1 WHERE / STATE (6列分)
        cLbl(ops_L, text="WHERE",   **fnt).grid(row=1, column=0, sticky="w", padx=4, pady=4)
        cLbl(ops_L, text="(STATE)", **fnt).grid(row=2, column=0, sticky="w", padx=4, pady=4)
        
        self.cbo_t1_cols   = []
        self.ent_t1_states = []

        for c in range(6):
            cbo = ttk.Combobox(ops_L, values=[], width=15, state="readonly", justify='center', font=(GUI,10))
            cbo.grid(row=1, column=1+c, sticky="w", padx=4, pady=4)
            self.cbo_t1_cols.append(cbo)
            ent = ttk.Entry(ops_L, width=15)
            ent.grid(row=2, column=1+c, sticky="w", padx=4)
            self.ent_t1_states.append(ent)

        # T2 JOIN ON
        cLbl(ops_L, text="JOIN ON", **fnt).grid(row=3, column=0, sticky="w", padx=4, pady=4)
        self.cbo_table2 = ttk.Combobox(ops_L, values=[], width=15, state="readonly", justify='center', font=(GUI,10))
        self.cbo_table2.grid(row=3, column=1, sticky="w", padx=4, pady=4)
        self.cbo_table2.bind("<<ComboboxSelected>>", self._on_t2_changed)

        self.lbl_join_t1 = tk.Label(ops_L, text="T1", width=15, bg="#FFE4B5", relief="solid", bd=1, font=(GUI,9), padx=4, pady=4)
        self.lbl_join_t1.grid(row=3, column=2, padx=2, pady=2)

        self.cbo_join_t1 = ttk.Combobox(ops_L, values=[], width=15, state="disabled", justify='center', font=(GUI,10))
        self.cbo_join_t1.grid(row=3, column=3, sticky="w", padx=4, pady=4)
        self.cbo_join_t1.bind("<<ComboboxSelected>>", self._eval_join_state)

        fr_eq = cFr(ops_L, bg=BG_COLOR)
        fr_eq.grid(row=3, column=4, sticky="w", padx=4)
        cLbl(fr_eq, text="=", **fnt).pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_join_t2 = tk.Label(fr_eq, text="", width=15, bg="#DDEEFF", relief="solid", bd=1, font=(GUI,9), padx=4, pady=4)
        self.lbl_join_t2.pack(side=tk.LEFT)

        self.cbo_join_t2 = ttk.Combobox(ops_L, values=[], width=15, state="disabled", justify='center', font=(GUI,10))
        self.cbo_join_t2.grid(row=3, column=5, sticky="w", padx=4, pady=4)
        self.cbo_join_t2.bind("<<ComboboxSelected>>", self._eval_join_state)

        # T2 WHERE / STATE (6列分)
        cLbl(ops_L, text="WHERE",   **fnt).grid(row=4, column=0, sticky="w", padx=4, pady=4)
        cLbl(ops_L, text="(STATE)", **fnt).grid(row=5, column=0, sticky="w", padx=4, pady=4)
        
        self.cbo_t2_cols   = []
        self.ent_t2_states = []

        for c in range(6):
            cbo = ttk.Combobox(ops_L, values=[], width=15, state="disabled", justify='center', font=(GUI,10))
            cbo.grid(row=4, column=1+c, sticky="w", padx=4, pady=4)
            self.cbo_t2_cols.append(cbo)

            ent = ttk.Entry(ops_L, width=15, state="disabled")
            ent.grid(row=5, column=1+c, sticky="w", padx=4)
            self.ent_t2_states.append(ent)

        # --- 日付・操作エリア (右側) ---
        ops.columnconfigure(1, weight=1)

        ops_R = cFr(ops, bg=BG_COLOR)
        ops_R.grid(row=0, column=1, sticky="ew", padx=(30, 0))

        # ボタン群
        btn_fr = cFr(ops_R, bg=BG_COLOR)
        btn_fr.pack(anchor="e", fill="x", pady=(0, 15))
        btn_fr.columnconfigure(1, weight=1)
  
        btn_preview = ttk.Button(btn_fr, text="プレビュー", command=self._preview, style="r.TButton")
        btn_preview.grid(row=0, column=0, padx=(0, 20), sticky="ns")

        btn_main   = ttk.Button(btn_fr, text="メイン画面", style="r.TButton", command=lambda: app.show_screen("Main"))
        btn_update = ttk.Button(btn_fr, text="更新",       style="r.TButton", command=self._refresh_tables)
        btn_main.grid(  row=0, column=1, pady=2, sticky="e")
        btn_update.grid(row=1, column=1, pady=2, sticky="e")

        # 日付指定群
        date_fr = cFr(ops_R, bg=BG_COLOR)
        date_fr.pack(anchor="e", fill="x")

        cLbl(date_fr, text="DATE ( FROM )", **fnt)._grid(R=0, C=1, Cspan=3, Stk="we", padx=(0, 0)) 
        cLbl(date_fr, text="DATE ( TO )",   **fnt)._grid(R=0, C=5, Cspan=3, Stk="we", padx=(10,0))
        cLbl(date_fr, text=" ～ ",          **fnt)._grid(R=1, C=4,          Stk="we", padx=5)

        ttk.Button(date_fr, text="本日", style="r.TButton", command=self._today_only,   width=6).grid(row=0, column=0, sticky="e", padx=(0,10))
        ttk.Button(date_fr, text="単日", style="r.TButton", command=self._from_to_from, width=6).grid(row=1, column=0, sticky="e", padx=(0,10))

        years  = [""] + [str(y) for y in reversed(range(2000, date.today().year + 1))]
        months = [""] + [f"{m:02d}" for m in range(1, 13)]
        days   = [""] + [f"{d:02d}" for d in range(1, 32)]

        self.df_y = ttk.Combobox(date_fr, values=years,  width=6, state="disabled")
        self.df_m = ttk.Combobox(date_fr, values=months, width=4, state="disabled")
        self.df_d = ttk.Combobox(date_fr, values=days,   width=4, state="disabled")
        self.df_y.grid(row=1, column=1, sticky="w", padx=2, pady=4)
        self.df_m.grid(row=1, column=2, sticky="w", padx=2, pady=4)
        self.df_d.grid(row=1, column=3, sticky="w", padx=2, pady=4)

        self.dt_y = ttk.Combobox(date_fr, values=years,  width=6, state="disabled")
        self.dt_m = ttk.Combobox(date_fr, values=months, width=4, state="disabled")
        self.dt_d = ttk.Combobox(date_fr, values=days,   width=4, state="disabled")
        self.dt_y.grid(row=1, column=5, sticky="w", padx=2, pady=4)
        self.dt_m.grid(row=1, column=6, sticky="w", padx=2, pady=4)
        self.dt_d.grid(row=1, column=7, sticky="w", padx=2, pady=4)

        self.lbl_count = ttk.Label(date_fr, text="", background=BG_COLOR)
        self.lbl_count.grid(row=2, column=7, sticky="e", pady=(5,0))

        # --- SELECT指定エリア (下段 10列) ---
        ops_Sel = cFr(ops, bg=BG_COLOR)
        ops_Sel.grid(row=1, column=0, columnspan=2, sticky="w", pady=(15,0))

        cLbl(ops_Sel, text="SELECT", **fnt).grid(row=0, column=0, rowspan=2, sticky="w", padx=4)

        self.cbo_sel_tbls = []
        self.cbo_sel_cols = []
        for i in range(10):
            c_tbl = ttk.Combobox(ops_Sel, values=[], width=14, state="readonly", justify='center', font=(GUI,10))
            c_tbl.grid(row=0, column=1+i, padx=4, pady=2)
            c_tbl.bind("<<ComboboxSelected>>", self._on_sel_tbl_changed)
            self.cbo_sel_tbls.append(c_tbl)

            c_col = ttk.Combobox(ops_Sel, values=[], width=14, state="disabled", justify='center', font=(GUI,10))
            c_col.grid(row=1, column=1+i, padx=4, pady=2)
            self.cbo_sel_cols.append(c_col)

        # ================= Treeview エリア =================
        result = cFr(main_frame, bg=BG_COLOR)
        result.pack(fill=tk.BOTH, padx=10, pady=(0,6), expand=True)

        self.tree = ttk.Treeview(result, columns=(), style="r.Treeview", show="headings", height=12)
        vsb       = ttk.Scrollbar(result, orient="vertical",   command=self.tree.yview)
        hsb       = ttk.Scrollbar(result, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(      row=0, column=1, sticky="ns")
        hsb.grid(      row=1, column=0, sticky="ew")

        result.grid_rowconfigure(0, weight=1)
        result.grid_columnconfigure(0, weight=1)

        # ================= ログエリア =================
        logf         = ttk.LabelFrame(main_frame, text="CMDｺﾝｿｰﾙ ｴｺｰ出力")
        self.txt_log = tk.Text(logf, height=6, bg="black", fg="white", font=("Consolas",10))
        log_vsb      = ttk.Scrollbar(logf, orient="vertical", command=self.txt_log.yview)

        self.txt_log.configure(yscrollcommand=log_vsb.set)

        logf.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0,10))
        log_vsb.grid(row=0, column=1, sticky="ns")
        self.txt_log.grid(row=0, column=0, sticky="nsew")

        logf.grid_rowconfigure(0, weight=1)
        logf.grid_columnconfigure(0, weight=1)

        self._refresh_tables()

    # --------------------------------------------
    def _from_to_from(self):

        self.dt_y.set(self.df_y.get().strip())
        self.dt_m.set(self.df_m.get().strip())
        self.dt_d.set(self.df_d.get().strip())

    # --------------------------------------------
    def _today_only(self):

        def jst_today():
            JST = timezone(timedelta(hours=9))
            return datetime.now(JST).date()

        self.df_y.set(jst_today().strftime("%Y"))
        self.df_m.set(jst_today().strftime("%m"))
        self.df_d.set(jst_today().strftime("%d"))
        self.dt_y.set(jst_today().strftime("%Y"))
        self.dt_m.set(jst_today().strftime("%m"))
        self.dt_d.set(jst_today().strftime("%d"))

    # --------------------------------------------
    def _get_table_cols(self, tbl_name):

        if not tbl_name: return []
        try:
            with sqlite3.connect(self.db_path, timeout=30) as c:
                rows = c.execute(f"PRAGMA table_info({tbl_name})").fetchall()
            return [""] + [r[1] for r in rows]
        except Exception as e:
            self._echo(f"[ERR] pragma table_info: {e}")
            return []

    # --------------------------------------------
    def _refresh_tables(self):

        try:
            with sqlite3.connect(self.db_path, timeout=30) as c:
                rows = c.execute("""
                    SELECT name
                      FROM sqlite_master
                     WHERE type='table'
                  ORDER BY name
                """).fetchall()
            names = [r[0] for r in rows]
        except Exception as e:
            names = []
            self._echo(f"[ERR] list tables: {e}")

        self._tables_cache = names
        self.cbo_table1["values"] = names
        self.cbo_table2["values"] = [""] + names 

        if names:
            self.cbo_table1.current(0)
            self._on_t1_changed()
            self.cbo_table2.current(0)
            self._on_t2_changed()

    # --------------------------------------------
    def _on_t1_changed(self, *_):

        tbl = self.cbo_table1.get().strip()
        self.lbl_join_t1.config(text=tbl)
        
        cols = self._get_table_cols(tbl)
        self.cols1 = cols

        for cbo in self.cbo_t1_cols:
            cbo["values"] = cols
            if cols: cbo.current(0)
            
        self.cbo_join_t1["values"] = cols

        has_date = any((str(c).lower() == "date") for c in cols)
        widgets  = (self.df_y, self.df_m, self.df_d, self.dt_y, self.dt_m, self.dt_d)
        
        state = "readonly" if has_date else "disabled"
        for w in widgets:
            if not has_date: w.set("")
            w.configure(state=state)

        self._update_select_tbl_choices()
        self._eval_join_state()

    # --------------------------------------------
    def _on_t2_changed(self, *_):

        tbl = self.cbo_table2.get().strip()

        if not tbl:
            self.cols2 = []
            self.cbo_join_t1.set("")
            self.cbo_join_t1.config(state="disabled")
            self.cbo_join_t2.set("")
            self.cbo_join_t2["values"] = []
            self.cbo_join_t2.config(state="disabled")
            self.lbl_join_t2.config(text="")
        else:
            self.lbl_join_t2.config(text=tbl)
            cols = self._get_table_cols(tbl)
            self.cols2 = cols

            self.cbo_join_t1.config(state="readonly")
            self.cbo_join_t2["values"] = cols
            self.cbo_join_t2.config(state="readonly")
            
            for cbo in self.cbo_t2_cols:
                cbo["values"] = cols
                if cols: cbo.current(0)

        self._update_select_tbl_choices()
        self._eval_join_state()

    # --------------------------------------------
    def _eval_join_state(self, *_):

        t2 = self.cbo_table2.get().strip()
        j1 = self.cbo_join_t1.get().strip()
        j2 = self.cbo_join_t2.get().strip()

        if t2 and j1 and j2:
            cbo_st = "readonly"
            ent_st = "normal"
        else:
            cbo_st = "disabled"
            ent_st = "disabled"

        for cbo in self.cbo_t2_cols:
            cbo.config(state=cbo_st)
        for ent in self.ent_t2_states:
            ent.config(state=ent_st)

    # --------------------------------------------
    def _update_select_tbl_choices(self):

        t1 = self.cbo_table1.get().strip()
        t2 = self.cbo_table2.get().strip()

        vals = []
        if t1: vals.append(t1)
        if t2: vals.append(t2)

        for i, c_tbl in enumerate(self.cbo_sel_tbls):
            cur = c_tbl.get().strip()
            c_tbl["values"] = vals
            if cur not in vals:
                c_tbl.set("")

            self._on_sel_tbl_changed(c_tbl)

    # --------------------------------------------
    def _on_sel_tbl_changed(self, event_or_widget):

        w = event_or_widget.widget if hasattr(event_or_widget, 'widget') else event_or_widget
        idx = self.cbo_sel_tbls.index(w)
        
        tbl_name = w.get().strip()
        c_col = self.cbo_sel_cols[idx]

        t1 = self.cbo_table1.get().strip()
        t2 = self.cbo_table2.get().strip()

        if tbl_name and tbl_name == t1:
            c_col["values"] = self.cols1
            c_col.config(state="readonly")

        elif tbl_name and tbl_name == t2:
            c_col["values"] = self.cols2
            c_col.config(state="readonly")

        else:
            c_col.set("")
            c_col["values"] = []
            c_col.config(state="disabled")

    # --------------------------------------------
    def _preview(self):

        T1 = self.cbo_table1.get().strip()
        T2 = self.cbo_table2.get().strip()
        j1 = self.cbo_join_t1.get().strip()
        j2 = self.cbo_join_t2.get().strip()

        if not T1:
            self._echo("[ERR] テーブル①が選択されていません。")
            return

        if T2 and (not j1 or not j2):
            messagebox.showerror("結合条件エラー", "テーブル②が指定されていますが、結合条件が設定されていません。")
            return

        # ---------------- SELECT 構築 ----------------
        sel_cols = []
        for i in range(10):
            t = self.cbo_sel_tbls[i].get().strip()
            c = self.cbo_sel_cols[i].get().strip()
            if t and c:
                sel_cols.append(f"{t}.{c} AS '{t}.{c}'")

        if not sel_cols:
            sel_cols.append(f"{T1}.*")

        select_clause = "SELECT " + ", ".join(sel_cols)

        # ---------------- FROM/JOIN 構築 ----------------
        from_clause = f"FROM {T1}"
        if T2 and j1 and j2:
            from_clause += f" INNER JOIN {T2} ON {T1}.{j1} = {T2}.{j2}"

        # ---------------- WHERE 構築 ----------------
        conds = []

        try:
            df_y, df_m, df_d = self.df_y.get().strip(), self.df_m.get().strip(), self.df_d.get().strip()
            dt_y, dt_m, dt_d = self.dt_y.get().strip(), self.dt_m.get().strip(), self.dt_d.get().strip()
        except Exception:
            df_y = df_m = df_d = dt_y = dt_m = dt_d = ""

        # 日付検索
        if all([df_y, df_m, df_d, dt_y, dt_m, dt_d]):
            date_from = f"{df_y}-{df_m}-{df_d}"
            date_to   = f"{dt_y}-{dt_m}-{dt_d}"
            conds.append(f"{T1}.date BETWEEN '{date_from}' AND '{date_to}'")

        # T1 WHERE
        for i in range(6):
            c1 = self.cbo_t1_cols[i].get().strip()
            s1 = self.ent_t1_states[i].get().strip()
            if c1 and s1:
                conds.append(f"{T1}.{c1} {s1}")

        # T2 WHERE
        if T2 and j1 and j2:
            for i in range(6):
                c2 = self.cbo_t2_cols[i].get().strip()
                s2 = self.ent_t2_states[i].get().strip()
                if c2 and s2:
                    conds.append(f"{T2}.{c2} {s2}")

        where_clause = ""
        if conds:
            where_clause = "WHERE " + " AND ".join(conds)

        sql = f"{select_clause} \n{from_clause} \n{where_clause} \nLIMIT 5000;"
        self._echo(f"[EXEC] {sql}")

        try:
            with sqlite3.connect(self.db_path, timeout=30) as c:
                c.row_factory = sqlite3.Row
                cursor        = c.execute(sql)
                rows          = cursor.fetchall()
                fetched_cols  = [desc[0] for desc in cursor.description]

        except Exception as e:
            self._echo(f"[ERR] preview: {e}")
            return

        self._render_rows(fetched_cols, rows)
        self.lbl_count.config(text=f"{len(rows)} rows")

    # --------------------------------------------
    def _render_rows(self, col_names, rows):

        self.tree.configure(columns=col_names)

        for c in self.tree["columns"]:

            base_col = c.split(".")[-1] if "." in c else c

            self.tree.heading(c, text=base_col)

            width = COLUMNS.get(base_col, 80)
            self.tree.column(c, width=width, anchor='center', stretch=False)

        for it in self.tree.get_children():
            self.tree.delete(it)

        for r in rows:
            self.tree.insert("", "end", values=[r[c] for c in col_names])

    # --------------------------------------------
    def _echo(self, msg: str):

        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")

COLUMNS = { "player_id":75, "name":140, "name_kana":95, "sex":50, "age":50,
            "regist_period":105, "regions":60, "height_cm":80, "weight_kg":70, "class_now":85, 
            "bloodtype":75, "birthday":100, "score_ave":90, "comment":120, "overall_rating":110,
            "day_no":60, "race_no":70,
            "series_title":300, "race_title":100, "is_final":60, "is_prefinal":90, "grade":50,
            "status":55, "weather":70, "distance":70, "wind_dir":60, "lap_reduct":90,
            "venue_id":75, "course":55,
            "boat_no":70, "motor_ave":90, "deadline_vote":110,
            "slit_ADJ":70, "frame_no":80, "violation":60, "finish_rank":90, "racec_time":85,
            "fault_code":85, "fault_level":85, "win_move":85, "race_time":85, 
            "program_id":110, "race_id":105, "entry_id":115, "date":105 }