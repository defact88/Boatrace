# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\DB_ops.py

from tkinter             import ttk, messagebox
from datetime            import datetime, timedelta, timezone, date
from pathlib             import Path
from Helpers.Custum_func import cFr, cLbl
import threading, subprocess, sys ,sqlite3, tkinter as tk

VENUES   = [ "桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑",
             "津",   "三国", "びわこ", "住之江", "尼崎",   "鳴門",   "丸亀", "児島",
             "宮島", "徳山", "下関",   "若松",   "芦屋",   "福岡",   "唐津", "大村", ]
VENUE_ID = {name: i+1 for i, name in enumerate(VENUES)}

IMPORT_B = r"C:\boatrace\import_B_txt.py"

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

#=====================================================================
class DBOpsScreen(ttk.Frame):
    def __init__(self, parent, app, db_path):
        super().__init__(parent)

        self.app            = app
        self.db_path        = db_path
        self._tables_cache  = []
        self._columns_cache = {}

        topbar = ttk.Frame(self) ;topbar.pack(fill=tk.X,             pady=6 )
        ops    = ttk.Frame(self)    ;ops.pack(fill=tk.X,    padx=10, pady=(0,6))
        result = ttk.Frame(self) ;result.pack(fill=tk.BOTH, padx=10, pady=(0,6), expand=True)

        ttk.Button( topbar, text="メイン画面", command=lambda: app.show_screen("Main") 
                   ).pack(side=tk.RIGHT, padx=10)
        ttk.Button( topbar, text="プレビュー", command=self._preview
                   ).pack(side=tk.LEFT, padx=20)
        ttk.Button( ops, text="更新", command=self._refresh_tables
                   ).grid(row=0, column=15, sticky="e", padx=(155,0))


        cLbl(ops, text="FROM"         )._grid(R=0, C= 0,          Stk="w",  padx=4, pady=4)
        cLbl(ops, text="WHERE"        )._grid(R=1, C= 0,          Stk="w",  padx=4, pady=4)
        cLbl(ops, text="(STATE)"      )._grid(R=2, C= 0,          Stk="w",  padx=4)
        cLbl(ops, text="DATE ( FROM )")._grid(R=1, C= 7, Cspan=3, Stk="we", padx=(50, 0)) 
        cLbl(ops, text="DATE ( TO )"  )._grid(R=1, C=11, Cspan=3, Stk="we", padx=(10, 0))
        cLbl(ops, text=" ～ "         )._grid(R=2, C=10,          Stk="we", padx=5)

        self.cbo_table = ttk.Combobox( ops, values=[], width=15, state="readonly",
                                                  justify='center', font=(GUI,10) )
        self.cbo_table.grid(row=0, column=1, sticky="w", padx=4, pady=4)
        self.cbo_table.bind("<<ComboboxSelected>>", self._on_table_changed)

        self.cbo_cols  = []
        self.entries   = []
        for c in range(4):
            cbo_col = ttk.Combobox( ops, values=[], width=15, state="readonly",
                                              justify='center', font=(GUI,10) )
            cbo_col.grid(row=1, column=1+c, sticky="w", padx=4, pady=4)
            self.cbo_cols.append(cbo_col)

            ent_state = ttk.Entry(ops, width=15)
            ent_state.grid(row=2, column=1+c, sticky="w", padx=4)
            self.entries.append(ent_state)

        years  = [""] + [str(y) for y in reversed(range(2000, date.today().year + 1))]
        months = [""] + [f"{m:02d}" for m in range(1, 13)]
        days   = [""] + [f"{d:02d}" for d in range(1, 32)]

        self.df_y = ttk.Combobox(ops, values=years,  width=6, state="disabled")
        self.df_m = ttk.Combobox(ops, values=months, width=4, state="disabled")
        self.df_d = ttk.Combobox(ops, values=days,   width=4, state="disabled")
        self.df_y.grid(row=2, column=7, sticky="w", padx=(20, 2), pady=4)
        self.df_m.grid(row=2, column=8, sticky="w", padx=2,       pady=4)
        self.df_d.grid(row=2, column=9, sticky="w", padx=2,       pady=4)

        self.dt_y = ttk.Combobox(ops, values=years,  width=6, state="disabled")
        self.dt_m = ttk.Combobox(ops, values=months, width=4, state="disabled")
        self.dt_d = ttk.Combobox(ops, values=days,   width=4, state="disabled")
        self.dt_y.grid(row=2, column=11, sticky="w", padx=2, pady=4)
        self.dt_m.grid(row=2, column=12, sticky="w", padx=2, pady=4)
        self.dt_d.grid(row=2, column=13, sticky="w", padx=2, pady=4)

        self.lbl_count = ttk.Label(ops, text="")
        self.lbl_count.grid(row=2, column=14, sticky="se", padx=(0,0))

        ttk.Button( ops, text="本日", command=lambda:self._today_only(),
                   ).grid(row=1, column=5, sticky="e", padx=(10,10))
        ttk.Button( ops, text="単日", command=lambda:self._from_to_from(),
                   ).grid(row=2, column=5, sticky="e", padx=(10,10))

        self.tree = ttk.Treeview(result, columns=(), show="headings", height=12)
        vsb       = ttk.Scrollbar(result, orient="vertical",   command=self.tree.yview)
        hsb       = ttk.Scrollbar(result, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(      row=0, column=1, sticky="ns")
        hsb.grid(      row=1, column=0, sticky="ew")

        result.grid_rowconfigure(0, weight=1)
        result.grid_columnconfigure(0, weight=1)

        logf         = ttk.LabelFrame(self, text="CMDｺﾝｿｰﾙ ｴｺｰ出力")
        self.txt_log = tk.Text(logf, height=8, font=("Consolas", 10))
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

        self._tables_cache       = names
        self.cbo_table["values"] = names

        if names:
            self.cbo_table.current(0)
            self._on_table_changed()

    # --------------------------------------------
    def _on_table_changed(self, *_):

        tbl = self.cbo_table.get()
        cols = []

        try:
            with sqlite3.connect(self.db_path, timeout=30) as c:
                rows = c.execute(f"PRAGMA table_info({tbl})").fetchall()
            cols = [""] + [r[1] for r in rows]
        except Exception as e:
            self._echo(f"[ERR] pragma table_info: {e}")

        for c in range(4):
            self.cbo_cols[c]["values"] = cols
            if cols: self.cbo_cols[c].current(0)

        has_date = any((str(c).lower() == "date") for c in cols)
        widgets  = ( getattr(self, "df_y", None), getattr(self, "df_m", None),
                     getattr(self, "df_d", None), getattr(self, "dt_y", None),
                     getattr(self, "dt_m", None), getattr(self, "dt_d", None) )

        for w in widgets:
            if w is None: continue
            if has_date:
                w.configure(state="readonly")
            else:
                w.set("")
                w.configure(state="disabled")

    # --------------------------------------------
    def _preview(self):

        tbl   = self.cbo_table.get().strip()
        if not tbl: return
        sql   = f"SELECT * FROM {tbl}"
        conds = []

        try:
            df_y = self.df_y.get().strip()
            df_m = self.df_m.get().strip()
            df_d = self.df_d.get().strip()
            dt_y = self.dt_y.get().strip()
            dt_m = self.dt_m.get().strip()
            dt_d = self.dt_d.get().strip()
        except Exception:
            df_y = df_m = df_d = dt_y = dt_m = dt_d = ""

        if all([df_y, df_m, df_d, dt_y, dt_m, dt_d]):
            date_from = f"{df_y}-{df_m}-{df_d}"
            date_to   = f"{dt_y}-{dt_m}-{dt_d}"
            conds.append(f"date BETWEEN '{date_from}' AND '{date_to}'")

        for c in range(4):
            col   = self.cbo_cols[c].get().strip()
            state = self.entries[c].get().strip()
            if not state: continue
            conds.append(f"{col} {state}")

        if conds: sql += " WHERE " + " AND ".join(conds)

        sql += " LIMIT 5000"

        try:
            with sqlite3.connect(self.db_path, timeout=30) as c:
                c.row_factory = sqlite3.Row
                rows = c.execute(sql).fetchall()
        except Exception as e:
            self._echo(f"[ERR] preview: {e}")
            return

        self._render_rows(rows)
        self.lbl_count.config(text=f"{len(rows)} rows")

    # --------------------------------------------
    def _render_rows(self, rows):

        cols = rows[0].keys() if rows else []
        self.tree.configure(columns=cols)

        for c in self.tree["columns"]:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=COLUMNS.get(c, 70), anchor='center',
                                                                      stretch=False )
        for it in self.tree.get_children():
            self.tree.delete(it)
        for r in rows:
            self.tree.insert("", "end", values=[r[c] for c in cols])
    # --------------------------------------------
    def _echo(self, msg: str):
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")

COLUMNS = { "player_id":70, "name":120, "name_kana":80, "sex":50, "age":50,
            "regist_period":100, "regions":60, "height_cm":80, "weight_kg":70,
            "bloodtype":75, "birthday":100, "comment":120, "day_no":55, "race_no":55,
            "series_title":275, "race_title":100, "is_final":50, "grade":50, "status":55, "weather":60,
            "distance":60, "wind_dir":60, "venue_id":65, "course":50, "boat_no":60,
            "slit_ADJ":55, "frame_no":65, "violation":60, "finish_rank":75,
            "player_id":65, "program_id":110, 
            "race_id":90, "entry_id":110, "date":90, "name":130}