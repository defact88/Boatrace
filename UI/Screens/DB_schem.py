# -*- coding: utf-8 -*-
# C:\boatrace\UI\Screens\DB_schem.py

import tkinter as tk
import sqlite3, os, shutil, re, datetime
from tkinter             import ttk, messagebox
from Helpers.Custum_func import cFr, cLbl, cBtn

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

class DBSchemScreen(ttk.Frame):
    def __init__(self, parent, app, db_path):
        super().__init__(parent)

        self.app     = app
        self.db_path = db_path
        self.configure(width=1300, height=900)
        self.grid_propagate(False)

        style = ttk.Style()
        style.configure("SelectedRow.TFrame", background="#2F6DB3")

        self.selected_table_row = None
        self._tbl_edit_index    = None
        self._tbl_edit_entry    = None
        self._tbl_new_index     = None
        self._new_table_mode    = False
        self._col_new_index     = None
        self._active_tbl_cb     = None
        self._active_col_cb     = None
        self._active_chk_cb     = None
        self._active_uni_cb     = None
        self._active_pk_cb      = None

        # 上段
        top  = ttk.Frame(self, height=80)
        mid  = ttk.Frame(self, height=600)
        top.pack(fill=tk.X)                  ;top.pack_propagate(False)
        mid.pack(fill=tk.X, padx=10, pady=0) ;mid.pack_propagate(False)

        row1 = ttk.Frame(top) ;row1.pack(anchor="w", pady=(0,10))
        row2 = ttk.Frame(top) ;row2.pack(anchor="w", padx=20)

        ttk.Button( row1, text="MAIN", width=8,
                    command=lambda: app.show_screen("Main")).pack(side=tk.LEFT, padx=10 )
        ttk.Button(row1, text="DATA", width=10).pack(side=tk.LEFT)

        self.cbo_kind = ttk.Combobox( row2, width=10, state="readonly",
                                       values=["TABLE", "VIEW", "INDEX"] )
        self.cbo_kind.set("TABLE") ;self.cbo_kind.pack(side=tk.LEFT)

        ttk.Frame(row2, width=80).pack(side=tk.LEFT)
        ttk.Button( row2, text="CREATE", width=10,
                    command=self._on_create).pack(side=tk.LEFT, padx=5 )

        ttk.Button(row2, text="DELETE", width=10, command=self._on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="RENAME", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="UPDATE", width=10).pack(side=tk.LEFT, padx=5)

        mid.columnconfigure(0, weight=0)
        mid.columnconfigure(1, weight=0)
        mid.columnconfigure(2, weight=1)

        # Block A : テーブル一覧
        frm_tables = ttk.Frame(mid, width=190, height=600, relief="solid", borderwidth=1)
        frm_tables.grid(row=0, column=0, sticky=ALL); frm_tables.grid_propagate(False)

        self.frm_tbl_list = ttk.Frame(frm_tables, width=190, height=560)
        self.frm_tbl_list.pack(fill=tk.BOTH, padx=2, pady=(20, 5))
        self.frm_tbl_list.pack_propagate(False)

        self.tbl_rows = []
        for i in range(20):
            r = ttk.Frame(self.frm_tbl_list, height=28)
            r.pack(fill=tk.X)
            r.pack_propagate(False)

            var = tk.BooleanVar()
            chk = ttk.Checkbutton( r, variable=var,
                                       command=lambda idx=i: self._set_single_cb("tbl", idx) )
            lbl = ttk.Label(r, text="", anchor="w", font=(MUI, 10))

            chk.pack(side=tk.LEFT, padx=0)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            r.bind(  "<Button-1>", lambda e, idx=i: self._on_table_click(idx))
            lbl.bind("<Button-1>", lambda e, idx=i: self._on_table_click(idx))

            self.tbl_rows.append({"row":r, "var":var, "chk":chk, "lbl":lbl})

        # Block B : カラム一覧
        frm_cols = ttk.Frame(mid, width=170, height=600, relief="groove", borderwidth=1)
        frm_cols.grid(row=0, column=1, sticky=ALL, padx=(10,0))
        frm_cols.grid_propagate(False)

        self.frm_col_list = ttk.Frame(frm_cols, width=170, height=560)
        self.frm_col_list.pack(fill=tk.BOTH, expand=False, padx=(0,10), pady=(20,5))
        self.frm_col_list.pack_propagate(False)

        self.col_rows = []
        for i in range(20):
            r = ttk.Frame(self.frm_col_list, height=26)
            r.pack(fill=tk.X, pady=1) ;r.pack_propagate(False)

            var = tk.BooleanVar()
            chk = ttk.Checkbutton( r,variable=var,
                                      command=lambda idx=i: self._set_single_cb("col", idx) )
            ent = ttk.Entry(r, font=(MUI,10))

            chk.pack(side=tk.LEFT, padx=0)
            ent.pack(fill=tk.X, expand=True)

            self.col_rows.append({"var": var, "chk": chk, "ent": ent})

        # Block C : パラメータ
        frm_param = ttk.Frame(mid, width=780, height=600, relief="solid", borderwidth=1)
        frm_param.grid(row=0, column=2, sticky=ALL, padx=(10,0))
        frm_param.grid_propagate(False)

        hdr = ttk.Frame(frm_param, height=20) ;hdr.pack(fill=tk.X) ;hdr.pack_propagate(False)

        col_names = [ "TYPE", "NOT NULL", "UNIQUE", "PRIMARY KEY",
                      "DEFAULT", "(other param)", "REFERENCES", "ON DEL CSCD" ]
        widths    = [90, 80, 60, 100, 90, 130, 170, 80]

        for name, w in zip(col_names, widths):
            ttk.Label( hdr, text   = name,
                            width  = int(w / 6),
                            anchor = "center",
                            font   = (GUI, 8)    ).pack(side=tk.LEFT, padx=4)

        self.frm_param_grid = ttk.Frame(frm_param, width=780, height=560)
        self.frm_param_grid.pack(fill=tk.BOTH, expand=False, padx=4, pady=(0,4))
        self.frm_param_grid.pack_propagate(False)

        self.param_rows = []
        for i in range(20):
            row = ttk.Frame(self.frm_param_grid, height=26)
            row.pack(fill=tk.X, pady=1)
            row.pack_propagate(False)

            widgets = {}
            for name, w in zip(col_names, widths):
                e = ttk.Entry(row, width=int(w / 8), font=(MUI,10))
                e.pack(side=tk.LEFT, padx=(4,2))
                widgets[name] = e
            self.param_rows.append(widgets)

        # 下段（CHECK / UNIQUE / PRIMARY KEY）
        bottom = ttk.Frame(self, height=216, width=1290)
        bottom.pack(fill=tk.X, padx=5, pady=(10, 5))
        bottom.pack_propagate(False)
        bottom.grid_propagate(False)

        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=1)

        # ---------- CHECK ----------
        frm_chk = ttk.Frame(bottom, height=216, width=430, relief="solid", borderwidth=1)
        frm_chk.grid(row=0, column=0, sticky=ALL, padx=(0, 2)) ;frm_chk.pack_propagate(False)

        ttk.Label(frm_chk, text="CHECK（テーブルレベル）", font=(GUI,10,BD)).pack(anchor="w", padx=6)

        self.chk_rows_frame = ttk.Frame(frm_chk)
        self.chk_rows_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0,4))
        self.chk_rows       = []
        self.chk_cb_vars    = []
        self._active_chk_cb = None

        # ---------- UNIQUE ----------
        frm_uni = ttk.Frame(bottom, height=216, width=430, relief="solid", borderwidth=1)
        frm_uni.grid(row=0, column=1, sticky=ALL, padx=2)
        frm_uni.pack_propagate(False)

        ttk.Label(frm_uni, text="UNIQUE（複合）", font=(GUI,10,BD)).pack(anchor="w", padx=6)

        self.uni_rows_frame = ttk.Frame(frm_uni)
        self.uni_rows_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.uni_rows       = []
        self.uni_cb_vars    = []
        self._active_uni_cb = None

        # ---------- PRIMARY KEY ----------
        frm_pk = ttk.Frame(bottom, height=216, width=430, relief="solid", borderwidth=1)
        frm_pk.grid(row=0, column=2, sticky=ALL, padx=(2,0))
        frm_pk.pack_propagate(False)

        ttk.Label(frm_pk, text="PRIMARY KEY（複合）", font=(GUI, 10, "bold")).pack(anchor="w", padx=6)

        self.pk_rows_frame = ttk.Frame(frm_pk)
        self.pk_rows_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.pk_rows       = []
        self.pk_cb_vars    = []
        self._active_pk_cb = None

        self._load_tables()
        self._bottom_max_rows = 8

    # TABLE 一覧読込--------------------------------------------------
    def _load_tables(self):

        kind = self.cbo_kind.get().strip().lower()
        if kind not in ("table", "view", "index"): kind = "table"

        sql  = "SELECT name FROM sqlite_master WHERE type=? ORDER BY name"

        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                rows = con.execute(sql, (kind,)).fetchall()
        except Exception as e:
            print("[ERR] load_tables:", e)
            rows = []

        names          = [r[0] for r in rows]
        exclude        = {"sqlite_sequence", "sqlite_stat1", "sqlite_stat4"}
        names          = [n for n in names if n not in exclude]
        max_rows       = len(self.tbl_rows)
        existing_count = min(len(names), max_rows - 1)

        self._tbl_new_index  = existing_count if existing_count < max_rows else None
        self._cancel_table_edit()
        self._new_table_mode = False

        for i, item in enumerate(self.tbl_rows):
            if i < existing_count:
                item["lbl"].config(text=names[i])
                item["chk"].config(state="normal")
                item["var"].set(False)
            elif self._tbl_new_index is not None and i == self._tbl_new_index:
                item["lbl"].config(text="")
                item["chk"].config(state="normal")
                item["var"].set(False)
            else:
                item["lbl"].config(text="")
                item["chk"].config(state="disabled")
                item["var"].set(False)

        if existing_count > 0:                self._select_table_row(0)
        elif self._tbl_new_index is not None: self._select_table_row(self._tbl_new_index)
        else:                                 self.selected_table_row = None

    # TABLE 行クリック（選択 or 編集開始）----------------------------
    def _on_table_click(self, idx):

        max_idx = -1
        if self._tbl_new_index is not None:
            max_idx = self._tbl_new_index
        else:
            for i, item in enumerate(self.tbl_rows):
                if item["chk"].cget("state") == "normal": max_idx = i

        if idx < 0 or idx > max_idx: return

        if self.selected_table_row == idx and self._tbl_edit_entry is None:
            self._start_table_edit(idx)
        else:
            self._select_table_row(idx)

    # TABLE名 編集開始------------------------------------------------
    def _start_table_edit(self, idx):

        rowinfo = self.tbl_rows[idx]
        lbl     = rowinfo["lbl"]
        self._cancel_table_edit()
        text    = lbl.cget("text")
        lbl.pack_forget()

        ent = ttk.Entry(rowinfo["row"], font=(MUI, 10))
        ent.insert(0, text)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ent.focus_set()
        ent.select_range(0, tk.END)

        ent.bind("<Return>",   lambda e, i=idx: self._finish_table_edit(i))
        ent.bind("<FocusOut>", lambda e, i=idx: self._finish_table_edit(i))

        self._tbl_edit_index = idx
        self._tbl_edit_entry = ent

    # TABLE名 編集終了------------------------------------------------
    def _finish_table_edit(self, idx):

        if self._tbl_edit_entry is None: return

        ent      = self._tbl_edit_entry
        new_name = ent.get().strip()
        ent.destroy()
        rowinfo  = self.tbl_rows[idx]
        lbl      = rowinfo["lbl"]
        lbl.config(text=new_name)
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._tbl_edit_entry = None
        self._tbl_edit_index = None

    # ----------------------------------------------------------------
    def _cancel_table_edit(self):
        if self._tbl_edit_entry is not None and self._tbl_edit_index is not None:
            self._finish_table_edit(self._tbl_edit_index)

    # TABLE 行選択----------------------------------------------------
    def _select_table_row(self, idx):

        if self.selected_table_row is not None:
            old = self.tbl_rows[self.selected_table_row]["row"]
            old.configure(style="")

        row = self.tbl_rows[idx]["row"]
        row.configure(style="SelectedRow.TFrame")
        self.selected_table_row = idx

        name = self.tbl_rows[idx]["lbl"].cget("text").strip()
        if self._tbl_new_index is not None and idx == self._tbl_new_index and not name:
            self._load_new_table_template()
        elif name:
            self._new_table_mode = False
            self._load_columns(name)

    # 新規テーブル用テンプレート--------------------------------------
    def _load_new_table_template(self):

        self._new_table_mode = True
        for col in self.col_rows:
            col["ent"].config(state="normal")  
            col["ent"].delete(0, tk.END)
            col["var"].set(False)

            if col["chk"].winfo_manager(): col["chk"].pack_forget()

        for row in self.param_rows:
            for w in row.values():
                w.config(state="normal") 
                w.delete(0, tk.END)

        for w in self.chk_rows_frame.winfo_children(): w.destroy()
        for w in self.uni_rows_frame.winfo_children(): w.destroy()
        for w in self.pk_rows_frame.winfo_children():  w.destroy()
        self.chk_rows.clear();      self.uni_rows.clear();      self.pk_rows.clear()
        self.chk_cb_vars.clear();   self.uni_cb_vars.clear();   self.pk_cb_vars.clear()
        self._active_chk_cb = None; self._active_uni_cb = None; self._active_pk_cb = None

        self.chk_cb_vars.clear()
        self.uni_cb_vars.clear()
        self.pk_cb_vars.clear()

        self._tbl_checks  = []
        self._tbl_uniques = []
        self._tbl_pkeys   = []
        self._refresh_lower_blocks()

    # 既存テーブルのカラム読み込み------------------------------------
    def _load_columns(self, table_name):

        self._new_table_mode = False
        for col in self.col_rows: 
            row = col["ent"].master
            for w in row.winfo_children(): w.pack_forget()
            col["chk"].pack(side=tk.LEFT, padx=0)
            col["ent"].pack(fill=tk.X, expand=True)

        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                rows = con.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        except Exception as e:
            print("[ERR] load_columns:", e)
            rows = []

        sql                 = self._get_create_sql(table_name)
        col_defs, tbl_checks, tbl_uniques, tbl_pkeys = self._parse_create_sql(sql)
        self._tbl_checks    = tbl_checks
        self._tbl_uniques   = tbl_uniques
        self._tbl_pkeys     = tbl_pkeys
        max_rows            = len(self.col_rows)
        existing_count      = min(len(rows), max_rows - 1)
        self._col_new_index = existing_count if existing_count < max_rows else None

        for i, col in enumerate(self.col_rows):
            ent = col["ent"]
            chk = col["chk"]

            if i < existing_count:
                col_name = rows[i][1]
                ent.config(state="normal")
                ent.delete(0, tk.END)
                ent.insert(0, col_name)
                chk.config(state="normal")
                col["var"].set(False)

            elif self._col_new_index is not None and i == self._col_new_index:
                ent.config(state="normal")
                ent.delete(0, tk.END)
                chk.config(state="normal")
                col["var"].set(False)

            else:
                ent.delete(0, tk.END)
                ent.config(state="disabled")
                chk.config(state="disabled")
                col["var"].set(False)

            param = self.param_rows[i]
            if i < existing_count:
                for w in param.values(): w.config(state="normal")
            elif self._col_new_index is not None and i == self._col_new_index:
                for w in param.values(): w.config(state="normal")
            else:
                for w in param.values():
                    w.delete(0, tk.END)
                    w.config(state="disabled")

        self._fill_params(col_defs)
        self._colinfo_cache = rows
        self._refresh_lower_blocks()

    #-----------------------------------------------------------------
    def _refresh_lower_blocks(self):

        for w in self.chk_rows_frame.winfo_children(): w.destroy()
        for w in self.uni_rows_frame.winfo_children(): w.destroy()
        for w in self.pk_rows_frame.winfo_children():  w.destroy()

        self.chk_rows.clear();      self.uni_rows.clear();      self.pk_rows.clear()
        self.chk_cb_vars.clear();   self.uni_cb_vars.clear();   self.pk_cb_vars.clear()
        self._active_chk_cb = None; self._active_uni_cb = None; self._active_pk_cb = None

        chk_vals = list(getattr(self, "_tbl_checks",  []))
        uni_vals = list(getattr(self, "_tbl_uniques", []))
        pk_vals  = list(getattr(self, "_tbl_pkeys",   []))

        self._build_row_block("chk",self.chk_rows_frame,self.chk_rows,self.chk_cb_vars,chk_vals)
        self._build_row_block("uni",self.uni_rows_frame,self.uni_rows,self.uni_cb_vars,uni_vals)
        self._build_row_block("pk", self.pk_rows_frame, self.pk_rows, self.pk_cb_vars, pk_vals)

    # ----------------------------------------------------------------
    def _build_row_block(self, block, parent_frame, rows_list, vars_list, values: list):

        if getattr(self, "_new_table_mode", False): total = getattr(self, "_bottom_max_rows", 8)
        else: total = len(values) + 1

        row_h = 24

        for i in range(total):
            row = ttk.Frame(parent_frame, height=row_h)
            row.pack(fill=tk.X, padx=0, pady=0)
            row.pack_propagate(False)

            if getattr(self, "_new_table_mode", False):
                cb = None
                var = None
                ttk.Frame(row, width=22).pack(side=tk.LEFT)
            else:
                var = tk.BooleanVar()
                cb  = ttk.Checkbutton(row, variable=var,
                                      command=lambda idx=i, blk=block: self._set_single_cb(blk, idx))
                cb.pack(side=tk.LEFT, padx=2)

            ent = ttk.Entry(row, font=(GUI, 10))
            ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

            if i < len(values):
                ent.insert(0, values[i])

            rows_list.append({"frm": row, "cb": cb, "var": var, "ent": ent})
            #vars_list.append(var)
            if var is not None: vars_list.append(var)

    # ----------------------------------------------------------------
    def _get_create_sql(self, table_name):

        sql = None
        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                row = con.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)  ).fetchone()
            if row:  sql = row[0]

        except Exception as e: print("[ERR] get_create_sql:", e)

        return sql

    # ----------------------------------------------------------------
    def _parse_create_sql(self, sql):

        col_defs, tbl_checks, tbl_uniques, tbl_pkeys = [], [], [], []
        if not sql: return col_defs, tbl_checks, tbl_uniques, tbl_pkeys
 
        s = sql.strip()
        try:
            l = s.index('('); r = s.rindex(')')
            inner = s[l+1:r]
        except ValueError:
            return col_defs, tbl_checks, tbl_uniques, tbl_pkeys

        #-----------
        def split_top(body: str): # トップレベルのカンマでだけ分割
            items, buf = [], []
            depth = 0; in_s = False; in_d = False; esc = False
            for ch in body:
                if esc: buf.append(ch); esc = False; continue
                if ch == '\\': buf.append(ch); esc = True; continue
                if not in_d and ch == "'": in_s = not in_s; buf.append(ch); continue
                if not in_s and ch == '"': in_d = not in_d; buf.append(ch); continue
                if not in_s and not in_d:
                    if ch == '(': depth += 1; buf.append(ch); continue
                    if ch == ')': depth -= 1; buf.append(ch); continue
                    if ch == ',' and depth == 0:
                        t = ''.join(buf).strip()
                        if t: items.append(t)
                        buf = []
                        continue
                buf.append(ch)
            tail = ''.join(buf).strip()
            if tail: items.append(tail)
            return items
        #-----------
        def strip_col_checks(col_def: str): # 列定義から列内CHECK を抜いて下段へ
            s          = col_def.strip()
            out_checks = []
            cleaned    = []
            i = 0; L = len(s)
            #-----------
            def match_word(src, pos, word):
                w = len(word)
                return src[pos:pos+w].upper() == word and (pos+w == len(src) or src[pos+w].isspace() or src[pos+w] == '(')
            #-----------
            while i < L:
                if match_word(s, i, "CHECK"):
                    j = i + 5
                    while j < L and j < L and s[j].isspace(): j += 1
                    if j >= L or s[j] != '(':
                        cleaned.append(s[i]); i += 1; continue
                    depth = 0; k = j
                    while k < L:
                        ch = s[k]
                        if ch == '(': depth += 1
                        elif ch == ')':
                            depth -= 1
                            if depth == 0:
                                k += 1
                                break
                        k += 1
                    expr = s[j:k].strip()
                    out_checks.append("CHECK " + expr)
                    i = k
                else:
                    cleaned.append(s[i]); i += 1

            cleaned_s = ' '.join(''.join(cleaned).strip().split()).rstrip(',')
            return cleaned_s, out_checks
        #-----------
        for part in split_top(inner):
            t = part.strip().rstrip(',')
            if not t: continue
            up = t.upper()

            if up.startswith("UNIQUE"):      tbl_uniques.append(t); continue
            if up.startswith("CHECK"):       tbl_checks.append(t);  continue
            if up.startswith("PRIMARY KEY"): tbl_pkeys.append(t);   continue

            cleaned, checks = strip_col_checks(t)
            if cleaned: col_defs.append(cleaned)
            if checks:  tbl_checks.extend(checks)

        return col_defs, tbl_checks, tbl_uniques, tbl_pkeys

    # ----------------------------------------------------------------
    def _fill_params(self, col_defs):

        for row in self.param_rows:
            for w in row.values(): w.delete(0, tk.END)

        STOP = r'(?:\bNOT\b|\bUNIQUE\b|\bPRIMARY\b|\bDEFAULT\b|\bREFERENCES\b|\bON\b|\bCHECK\b|,|$)'

        for i, line in enumerate(col_defs):
            if i >= len(self.param_rows): break

            row      = self.param_rows[i]
            s        = line.strip()
            u        = s.upper()
            #------------
            def put(key, val):
                w = row[key]
                prev = w.cget("state")
                if prev == "disabled":  w.config(state="normal")
                w.delete(0, tk.END)
                if val: w.insert(0, val)
                if prev == "disabled": w.config(state="disabled")
            #------------
            m        = re.match(r'^\s*\S+\s+([^\s,]+)', s)
            type_val = m.group(1) if m else ""
            put("TYPE", type_val)

            row["NOT NULL"].insert(0, "NOT NULL" if " NOT NULL" in u or u.startswith("NOT NULL") else "")
            row["UNIQUE"].insert(0, "UNIQUE" if re.search(r'\bUNIQUE\b(?!\s*\()', u) else "")
            row["PRIMARY KEY"].insert(0, "PRIMARY KEY" if "PRIMARY KEY" in u else "")

            def_val = ""
            m = re.search(r'\bDEFAULT\b\s+(.*?)\s*(?=' + STOP + r')', s,flags=re.IGNORECASE)
            if m: def_val = m.group(1).strip().rstrip(',')
            row["DEFAULT"].insert(0, def_val)

            ref_val = ""
            m       = re.search(r'\bREFERENCES\b\s+(.+?\))', s, flags=re.IGNORECASE)
            if m:
                tmp = m.group(1)
                cut = re.split(r'\bON\b|\bUNIQUE\b|\bPRIMARY\b|\bCHECK\b|,', tmp, flags=re.IGNORECASE)[0]
                ref_val = cut.strip()

            row["REFERENCES"].insert(0, ref_val)
            row["ON DEL CSCD"].insert(0, "TRUE" if "ON DELETE CASCADE" in u else "")

            other_on = ""
            m = re.search(r'\bON\s+UPDATE\b\s+(.*?)\s*(?=' + STOP + r')', s, flags=re.IGNORECASE)
            if m: other_on = m.group(1).strip().rstrip(',')

            row["(other param)"].insert(0, other_on)

    # CREATE TABLE 実行コア-------------------------------------------
    def _exec_create_table( self, table_name, col_defs,
                           check_lines=None, unique_lines=None, pkey_lines=None ):

        check_lines  = check_lines  or []
        unique_lines = unique_lines or []
        pkey_lines   = pkey_lines   or []
        table_name   = table_name.strip()

        if not table_name:
            messagebox.showwarning("エラー", "テーブル名が空です。")
            return
        if not col_defs:
            messagebox.showwarning("エラー", "カラムが 1 件もありません。")
            return

        defs = []
        for line in col_defs:
            s = line.strip().rstrip(',')
            if s: defs.append(s)

        for seq in (check_lines, unique_lines, pkey_lines):
            for line in seq:
                s = line.strip().rstrip(',')
                if s: defs.append(s)

        inner = ", ".join(defs)
        ddl   = f"CREATE TABLE {table_name} ({inner});"
        msg   = "以下の SQL を実行します。\n\n" + ddl

        if not messagebox.askokcancel("CREATE 確認", msg): return

        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                con.execute(f"DROP TABLE IF EXISTS {table_name}__tmp__create_guard")
                con.execute(ddl)
            self._load_tables() 
            messagebox.showinfo("成功", f"CREATE TABLE 完了：{table_name}")
        except Exception as e:
            messagebox.showerror("エラー", f"CREATE TABLE 失敗：{e}")

    # CREATEボタン処理）----------------------------------------------
    def _on_create(self):

        self._cancel_table_edit()
        block, idx = self._get_active_cb()
        if block is None:
            messagebox.showwarning("エラー", "CREATE 対象が選択されていません。")
            return

        if block == "tbl" and self._tbl_new_index is not None and idx == self._tbl_new_index:
            self._create_new_table_from_inputs()
            return

        if (block == "col"
                and self._col_new_index is not None
                and idx == self._col_new_index
                and not self._new_table_mode):

            tbl_info   = self.tbl_rows[self.selected_table_row]
            table_name = tbl_info["lbl"].cget("text").strip()
            if not table_name:
                messagebox.showwarning("エラー", "テーブル名を取得できません。")
                return

            self._create_new_column_in_existing_table(table_name, idx)
            return

        messagebox.showwarning( "エラー",
            "CREATE 対象は「新規テーブル行」または「新規カラム行」のみ有効です。" )

    # 新規テーブル用 CREATE 本体--------------------------------------
    def _create_new_table_from_inputs(self):

        tbl_info   = self.tbl_rows[self._tbl_new_index]
        table_name = tbl_info["lbl"].cget("text").strip()
        if not table_name:
            messagebox.showwarning("エラー", "テーブル名が空です。")
            return

        col_names = []
        for row in self.col_rows:
            name = row["ent"].get().strip()
            if name: col_names.append(name)

        col_defs = []
        for i, pr in enumerate(self.param_rows):
            name = self.col_rows[i]["ent"].get().strip()
            if not name: continue

            parts = [name]
            for k in ["TYPE", "NOT NULL", "UNIQUE", "PRIMARY KEY", "DEFAULT", "(other param)", "REFERENCES", "ON DEL CSCD"]:
                v = pr[k].get().strip()
                if v: parts.append(v)

            col_def = ' '.join(parts).strip().rstrip(',')
            if col_def: col_defs.append(col_def) 
        #---------------
        def _collect_from_rows(rows):
            out = []
            for r in rows:
                v = r["ent"].get().strip()
                if v: out.append(v)
            return out
        #---------------
        check_lines  = _collect_from_rows(self.chk_rows)
        unique_lines = _collect_from_rows(self.uni_rows)
        pkey_lines   = _collect_from_rows(self.pk_rows)

        self._exec_create_table(table_name, col_defs, check_lines, unique_lines, pkey_lines)

    # 既存テーブルに新規カラム追加-----------------------------------
    def _create_new_column_in_existing_table(self, table_name, col_index):

        table_name = table_name.strip()
        if not table_name:
            messagebox.showwarning("エラー", "テーブル名が空で----す。")
            return
        if self._col_new_index is None or col_index != self._col_new_index:
            messagebox.showwarning("エラー", "CREATE 対象は新規カラム行のみです。")
            return

        name = self.col_rows[col_index]["ent"].get().strip()
        if not name:
            messagebox.showwarning("エラー", "カラム名が空です。")
            return

        pr    = self.param_rows[col_index]
        parts = [name]
        for k in ["TYPE", "NOT NULL", "UNIQUE", "PRIMARY KEY", "DEFAULT", "(other param)", "REFERENCES", "ON DEL CSCD"]:
            v = pr[k].get().strip()
            if v:
                if k is "DEFAULT":    v = f"DEFAULT {v}"
                if k is "REFERENCES": v = f"REFERENCES {v}"
                parts.append(v)

        col_def = ' '.join(parts).strip().rstrip(',')
        ddl     = f"ALTER TABLE {table_name} ADD COLUMN {col_def};"
        msg     = "以下の SQL を実行します。\n\n" + ddl

        if not messagebox.askokcancel("CREATE 確認", msg): return

        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                con.execute(ddl)
            self._load_columns(table_name) 
            messagebox.showinfo("成功", f"ADD COLUMN 完了：{name}")
        except Exception as e:
            messagebox.showerror("エラー", f"ADD COLUMN 失敗：{e}")

    # DELETE -----------------------------------------------------------
    def _on_delete(self):

        block, idx = self._get_active_cb()
        if block is None:
            messagebox.showwarning("エラー", "DELETE 対象が選択されていません。")
            return

        self._backup_before_change();

        if block == "tbl": self._delete_table(idx);  return
        if block == "col": self._delete_column(idx); return
        if block == "chk": self._delete_check(idx);  return
        if block == "uni": self._delete_unique(idx); return
        if block == "pk":  self._delete_pkey(idx);   return

        messagebox.showwarning("エラー", "DELETE 対象が不明です。")

    # テーブル削除 ---------------------------------------------------
    def _delete_table(self, idx):

        lbl        = self.tbl_rows[idx]["lbl"]
        table_name = lbl.cget("text").strip()

        if not table_name:
            messagebox.showwarning("エラー", "テーブル名を取得できません。")
            return

        sql = f"DROP TABLE {table_name};"
        msg = f"以下の SQL を実行します。\n\n{sql}"

        if not messagebox.askokcancel("DELETE 確認", msg): return

        try:
            con = sqlite3.connect(self.db_path, timeout=30)
            with con:
                con.execute(sql)
                con.execute("PRAGMA optimize;")
        except Exception as e:
            messagebox.showerror("DELETE 失敗",
                                 f"DROP TABLE 実行に失敗 \n\n{e}")
            return

        self._load_tables()
        messagebox.showinfo("完了", f"TABLE: {table_name} を削除")

    # カラム削除 -----------------------------------------------------
    def _delete_column(self, idx):

        if self.selected_table_row is None:
            messagebox.showwarning("エラー", "テーブルが選択されていません。")
            return

        tbl_info   = self.tbl_rows[self.selected_table_row]
        table_name = tbl_info["lbl"].cget("text").strip()
        if not table_name:
            messagebox.showwarning("エラー", "テーブル名を取得できません。")
            return

        colname = self.col_rows[idx]["ent"].get().strip()
        if not colname:
            messagebox.showwarning("エラー", "カラム名を取得できません。")
            return

        sql = f"ALTER TABLE {table_name} DROP COLUMN {colname};"
        msg = f"以下の SQL を実行します。\n\n{sql}"
        if not messagebox.askokcancel("DELETE 確認", msg):
            return

        try:
            con = sqlite3.connect(self.db_path, timeout=30)
            with con:
                con.execute(sql)
                con.execute("PRAGMA optimize;")
        except Exception as e:
            messagebox.showerror("DELETE 失敗", f"DROP COLUMN 実行に失敗しました。\n\n{e}")
            return

        self._load_columns(table_name)
        messagebox.showinfo("完了", f"TABLE: {table_name} からCOLUMN: {colname} を削除")

    # バックアップ ----------------------------------------------------
    def _backup_before_change(self):

        base = r"C:\boatrace\BACKUP\DB"
        os.makedirs(base, exist_ok=True)

        today = datetime.datetime.now().strftime("%Y%m%d")
        name  = f"{today}boatrace.db"
        dst   = os.path.join(base, name)
        cnt   = 1

        while os.path.exists(dst):
            dst  = os.path.join(base, f"{today}boatrace({cnt}).db")
            cnt += 1

        shutil.copy2(self.db_path, dst)

        files = sorted( [os.path.join(base, f) for f in os.listdir(base)],
                         key=lambda p: os.path.getmtime(p)                 )
        if len(files) > 30:
            for old in files[:-30]:
                try: os.remove(old)
                except: pass

    # 現在 TRUE の C/B を探す-----------------------------------------
    def _get_active_cb(self):

        for i, item in enumerate(self.tbl_rows):
            if item["var"].get(): return "tbl", i

        for i, item in enumerate(self.col_rows):
            if item["var"].get(): return "col", i

        for i, var in enumerate(self.chk_cb_vars):
            if var.get():         return "chk", i

        for i, var in enumerate(self.uni_cb_vars):
            if var.get():         return "uni", i

        for i, var in enumerate(self.pk_cb_vars):
            if var.get():          return "pk", i

        return None, None

    # C/B=TRUE(0or1) + 再ｸﾘｯｸでﾄｸﾞﾙ ----------------------------------
    def _set_single_cb(self, block, idx):

        if block == "tbl":
            if not (0 <= idx < len(self.tbl_rows)): return
            active = self._active_tbl_cb
        elif block == "col":
            if not (0 <= idx < len(self.col_rows)): return
            active = self._active_col_cb
        elif block == "chk":
            if not (0 <= idx < len(self.chk_cb_vars)): return
            active = self._active_chk_cb
        elif block == "uni":
            if not (0 <= idx < len(self.uni_cb_vars)): return
            active = self._active_uni_cb
        elif block == "pk":
            if not (0 <= idx < len(self.pk_cb_vars)): return
            active = self._active_pk_cb
        else: return

        if active == idx:
            new_tbl = None if block == "tbl" else self._active_tbl_cb
            new_col = None if block == "col" else self._active_col_cb
            new_chk = None if block == "chk" else self._active_chk_cb
            new_uni = None if block == "uni" else self._active_uni_cb
            new_pk  = None if block == "pk"  else self._active_pk_cb
        else:
            new_tbl = idx if block == "tbl" else None
            new_col = idx if block == "col" else None
            new_chk = idx if block == "chk" else None
            new_uni = idx if block == "uni" else None
            new_pk  = idx if block == "pk"  else None

        self._active_tbl_cb = new_tbl
        self._active_col_cb = new_col
        self._active_chk_cb = new_chk
        self._active_uni_cb = new_uni
        self._active_pk_cb  = new_pk

        for item in self.tbl_rows: item["var"].set(False)
        for item in self.col_rows: item["var"].set(False)
        for v in self.chk_cb_vars: v.set(False)
        for v in self.uni_cb_vars: v.set(False)
        for v in self.pk_cb_vars:  v.set(False)

        if self._active_tbl_cb is not None:
            self.tbl_rows[self._active_tbl_cb]["var"].set(True)
        if self._active_col_cb is not None:
            self.col_rows[self._active_col_cb]["var"].set(True)
        if self._active_chk_cb is not None and 0 <= self._active_chk_cb < len(self.chk_cb_vars):
            self.chk_cb_vars[self._active_chk_cb].set(True)
        if self._active_uni_cb is not None and 0 <= self._active_uni_cb < len(self.uni_cb_vars):
            self.uni_cb_vars[self._active_uni_cb].set(True)
        if self._active_pk_cb is not None and 0 <= self._active_pk_cb < len(self.pk_cb_vars):
            self.pk_cb_vars[self._active_pk_cb].set(True)

    # 依存オブジェクト取得 -------------------------------------------
    def _list_indexes(self, table_name: str):

        out = []
        if not table_name: return out
        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                cur = con.cursor()
                cur.execute(f"PRAGMA index_list({table_name})")
                for seq, idx_name, unique, origin, partial in cur.fetchall():

                    cur.execute(f"PRAGMA index_info({idx_name})")
                    cols = [r[2] for r in cur.fetchall()]
                    cur.execute(
                        "SELECT sql FROM sqlite_master WHERE type='index' AND name=?",
                        (idx_name,)                                                   )

                    row = cur.fetchone()
                    sql = row[0] if row and row[0] else ""
                    out.append( {     "name": idx_name,
                                    "unique": bool(unique),
                                    "origin": origin,
                                   "partial": bool(partial),
                                   "columns": cols,
                                       "sql": sql,           })

        except Exception: pass

        return out

    # 依存オブジェクト取得 -------------------------------------------
    def _list_views_referencing(self, table_name:str, column_name:str = None):

        out = []
        if not table_name: return out

        tbl_pat = re.compile(rf'\b{re.escape(table_name)}\b',  re.IGNORECASE)
        col_pat = re.compile(rf'\b{re.escape(column_name)}\b', re.IGNORECASE) if column_name else None

        try:
            with sqlite3.connect(self.db_path, timeout=30) as con:
                cur = con.cursor()
                cur.execute("SELECT name, sql FROM sqlite_master WHERE type='view' AND sql IS NOT NULL")
                for name, sql in cur.fetchall():
                    s = sql or ""
                    if not tbl_pat.search(s): continue
                    if col_pat and not col_pat.search(s): continue
                    out.append({"name": name, "sql": s})
        except Exception: pass

        return out
