# -*- coding: utf-8 -*-
# C:\boatrace\Management\Mmanagement_gui.pyw

from tkinter     import messagebox
from pathlib     import Path
from PIL         import Image, ImageTk
from Custum_func import cFr, cLbl, cBtn
import subprocess, shutil, os, csv, datetime, time, ctypes, win32com.client, sys
import tkinter as tk
#-------------------------------------------------
BASE_DIR     = Path(r"C:\boatrace\Management")
CSV_FILEMAP  = BASE_DIR / "file_map.csv"
CSV_ARGSTBL  = BASE_DIR / "args_table.csv"
ICON_PATH    = BASE_DIR / r"Icon\GUI.ico"
TERAPAD_PATH = r"C:\Program Files (x86)\TeraPad\TeraPad.exe"
BACKUP_ROOT  = Path(r"C:\boatrace\BACKUP")
UPLOAD_DIR   = Path(r"C:\boatrace\Management\UPLOAD")
GUI_POS_X    = 1750
GUI_POS_Y    = 5
SELCOL       = "#b1dbcc"

GUI, MUI, HNH      = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

#===============================================================================
class FileManagementGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Management GUI [ver.4.6]")
        self.geometry(f"800x380+{GUI_POS_X}+{GUI_POS_Y}")
        self.configure(bg= "#222222")
        self.resizable(False, False)
        try: self.iconbitmap(ICON_PATH)
        except Exception: pass

        self.option_add("*Font", (MUI,12))
        self.option_add("*Foreground", "#FFFFFF")
        self.option_add("*Background", "#222222")

        self.file_map             = self.load_file_map()
        self.args_table           = self.load_args_table()
        self.active_category      = None
        self.active_subcat        = None
        self.active_file          = None
        self.arg_widgets          = []
        self.current_file_records = []
        self.active_record        = None
        self.create_widgets()
        self.populate_first_layer()

    #-------------------------
    def populate_first_layer(self):
        self.on_select_category("UI")

    #-------------------------------------------------------
    def load_file_map(self):

        rows = []
        if not CSV_FILEMAP.exists():
            self.show_msg("Error", f"{CSV_FILEMAP} が見つかりません")
            return rows

        try:
            with open(CSV_FILEMAP, "r", encoding= "utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    norm = {(k or "").strip():(v or "").strip() for k, v in r.items()}
                    rows.append(norm)
        except Exception as e:
            self.show_msg("Error", f"file_map.csv の読み込みに失敗:\n{e}")

        return rows

    #-------------------------------------------------------
    def load_args_table(self):

        args = {}
        if not CSV_ARGSTBL.exists(): return args

        with open(CSV_ARGSTBL, "r", encoding= "utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3: row += [""] * (3 - len(row))
                fn, arg, req = row
                req_bool     = "True" in (req or "")
                args.setdefault(fn.strip(), []).append(((arg or "").strip(), req_bool))

        return args

    #-------------------------------------------------------
    def create_widgets(self):

        self.frame_left   = tk.Frame(self, bg= "#222222", width=120, height=400)
        self.frame_center = tk.Frame(self, bg= "#222222", width=280, height=400)
        self.frame_right  = tk.Frame(self, bg= "#252525", width=400, height=400,
                                     highlightbackground="#555555", highlightthickness=2)

        self.frame_left.pack(  side= "left",  fill= "both", padx= (3,6), pady=6)
        self.frame_center.pack(side= "left",  fill= "both", padx= (6,3), pady=6)
        self.frame_right.pack( side= "right", fill= "both", padx= (3,6), pady=6)

        self.frame_left.pack_propagate(False)
        self.frame_center.pack_propagate(False)
        self.frame_right.pack_propagate(False)

        #====== 左カラム =====

        MNG_PATH     = r"C:\boatrace\Management\Management_gui.pyw"
        MNG_DIR      = r"C:\boatrace\Management"
        BR_GUI_PATH  = Path(r"C:\boatrace\UI\boatrace_gui.py")
        BR_GUI_DIR   = r"C:\boatrace\UI"
        SCHEMA_PATH  = r"C:\boatrace\Schema\schema_all.sql"
        SCHEMA_DIR   = r"C:\boatrace\Schema"
        FILEMAP_PATH = r"C:\boatrace\Management\file_map.csv"
        ARGLIST_PATH = r"C:\boatrace\Management\args_table.csv"
        MAIN_DIR     = r"C:\boatrace"
        BACKUP_DIR   = r"C:\boatrace\Backup"

        BAT_COMMIT   = Path(r"C:\boatrace\BR\Gitcommit.bat")
        DAILY_PATH   = Path(r"C:\boatrace\Import\daily_insert.py")

        base_size    = (1760, 950, 800, 500)

        # ----------
        def open_file(f_path:Path):
            subprocess.Popen([TERAPAD_PATH, str(f_path)], shell=True)
        # ----------
        icon_img_F = Image.open(BASE_DIR / r"Icon\X_fol.ico" ).resize((40, 40))
        icon_img_A = Image.open(BASE_DIR / r"Icon\Finder.ico").resize((40, 40))
        icon_img_B = Image.open(BASE_DIR / r"Icon\GUI.ico"   ).resize((40, 40))
        icon_img_C = Image.open(BASE_DIR / r"Icon\Matrix.ico").resize((40, 40))
        icon_img_M = Image.open(BASE_DIR / r"Icon\Memo.ico"  ).resize((40, 40))

        fr_icons = tk.Frame(self.frame_left, bg= "#222222")
        fr_icons.place(x=5, y=5, width=110, height=355)

        self.Fol  = ImageTk.PhotoImage(icon_img_F)
        self.txt  = ImageTk.PhotoImage(icon_img_M)
        self.A_D  = ImageTk.PhotoImage(icon_img_A)
        self.B_D  = ImageTk.PhotoImage(icon_img_B)
        self.C_D  = ImageTk.PhotoImage(icon_img_C)

        icon_A_F = cBtn(fr_icons, Img=self.A_D, bd=0, Com=lambda p=MNG_PATH:open_file(p))
        icon_A_D = cBtn(fr_icons, Img=self.Fol, bd=0, Com=lambda:open_explr(MNG_DIR, *base_size))
        icon_B_F = cBtn(fr_icons, Img=self.B_D, bd=0, Com=lambda p=BR_GUI_PATH:open_file(p))
        icon_B_D = cBtn(fr_icons, Img=self.Fol, bd=0, Com=lambda:open_explr(BR_GUI_DIR, *base_size) )
        icon_C_F = cBtn(fr_icons, Img=self.C_D, bd=0, Com=lambda p=SCHEMA_PATH: open_file(p))
        icon_C_D = cBtn(fr_icons, Img=self.Fol, bd=0, Com=lambda:open_explr(SCHEMA_DIR, *base_size))
        icon_Main= cBtn(fr_icons, Img=self.Fol, bd=0, Com=lambda:open_explr(MAIN_DIR, *base_size))
        icon_Sub = cBtn(fr_icons, Img=self.Fol, bd=0, Com=lambda:open_explr(BACKUP_DIR, *base_size))
        icon_Fmp = cBtn(fr_icons, Img=self.txt, bd=0, Com=lambda p=FILEMAP_PATH:open_file(p))
        icon_Arg = cBtn(fr_icons, Img=self.txt, bd=0, Com=lambda p=ARGLIST_PATH:open_file(p))

        lb_row1  = tk.Label(fr_icons,text="Management",   font=(MUI,9), anchor=CT)
        lb_row2  = tk.Label(fr_icons,text="Boatrace_gui", font=(MUI,9), anchor=CT)
        lb_row3  = tk.Label(fr_icons,text="DB_Schema",    font=(MUI,9), anchor=CT)
        lb_row4a = tk.Label(fr_icons,text="Filemap",      font=(MUI,9), anchor=CT)
        lb_row4b = tk.Label(fr_icons,text="Arglist",      font=(MUI,9), anchor=CT)
        lb_row5a = tk.Label(fr_icons,text="Maiin",        font=(MUI,9), anchor=CT)
        lb_row5b = tk.Label(fr_icons,text="Backup",       font=(MUI,9), anchor=CT)

        icon_A_F.grid( row=0, column=0, padx= (3, 10), pady=(5, 0), sticky= "w")
        icon_A_D.grid( row=0, column=1, padx= (10, 3), pady=(5, 0), sticky= "w")
        lb_row1.grid(  row=1, column=0, columnspan=2,               sticky="ns")
        icon_B_F.grid( row=2, column=0, padx= (3, 10), pady=(8, 0), sticky= "w")
        icon_B_D.grid( row=2, column=1, padx= (10, 3), pady=(8, 0), sticky= "w")
        lb_row2.grid(  row=3, column=0, columnspan=2,               sticky="ns")
        icon_C_F.grid( row=4, column=0, padx= (3, 10), pady=(8, 0), sticky= "w")
        icon_C_D.grid( row=4, column=1, padx= (10, 3), pady=(8, 0), sticky= "w")
        lb_row3.grid(  row=5, column=0, columnspan=2,               sticky="ns")
        icon_Fmp.grid( row=6, column=0, padx= (3, 10), pady=(8, 0), sticky= "w")
        icon_Arg.grid( row=6, column=1, padx= (10, 3), pady=(8, 0), sticky= "w")
        lb_row4a.grid( row=7, column=0,                             sticky="ns")
        lb_row4b.grid( row=7, column=1,                             sticky="ns")
        icon_Main.grid(row=8, column=0, padx= (3, 10), pady=(8, 0), sticky= "w")
        icon_Sub.grid( row=8, column=1, padx= (10, 3), pady=(8, 0), sticky= "w")
        lb_row5a.grid( row=9, column=0,                             sticky="ns")
        lb_row5b.grid( row=9, column=1,                             sticky="ns")

        #====== 中カラム =====

        self.lbl_active  =   tk.Label( self.frame_center, text="", relief="groove", font=(MUI,11),
                                        bg="#333333", fg="#66CCFF", anchor="w", padx=15  )
        self.list_files  = tk.Listbox( self.frame_center, height=9, relief="flat", font=(MUI,11),
                                        bg="#333333", fg="#FFFFFF", activestyle="none",
                                        selectbackground= SELCOL, exportselection= False  )
        self.list_subcat = tk.Listbox( self.frame_center, height=6, relief="flat", font=(MUI,11),
                                        bg="#333333", fg="#FFFFFF", activestyle="none",
                                        selectbackground=SELCOL, exportselection=False  )

        self.lbl_active.pack(  fill="x",                          pady=(0, 5))
        self.list_files.pack(  fill="both", expand=False, padx=2, pady=(5, 5))
        self.list_subcat.pack(fill="x",    expand=False, padx=2, pady=(5, 0))
        self.list_files.bind( "<<ListboxSelect>>", self.on_select_file)
        self.list_subcat.bind("<<ListboxSelect>>", self.on_select_subcat)

        #====== 右カラム =====

        # 引数表示エリア
        self.fr_args    = tk.Frame(self.frame_right, bg="#333333",relief="ridge", bd=1)
        self.fr_arglist = tk.Frame(self.fr_args,     bg="#333333")
        self.fr_args.place(x=10, y=10, width=350, height=250)
        self.fr_arglist.pack(fill= "both", expand= False, padx=8, pady=4)

        # 第1階層ボタン
        self.frame_cat = tk.Frame(self.frame_right, bg= "#222222")
        self.frame_cat.place(x=10, y=270, width=360, height=35)

        for i in range(4): self.frame_cat.grid_columnconfigure(i, weight=0)

        btn_opt = dict(bg="#444444", fg="#FFFFFF",font=(MUI,10), width=8)

        self.icon_gui    = ImageTk.PhotoImage(Image.open(ICON_PATH).resize((40, 40)))

        self.btn_ui      = tk.Button( self.frame_cat, text="ＵＩ",    **btn_opt,
                                      command=lambda: self.on_select_category("UI")      )
        self.btn_import  = tk.Button( self.frame_cat, text="Import",  **btn_opt,
                                      command=lambda: self.on_select_category("Import")  )
        self.btn_checker = tk.Button( self.frame_cat, text="Checker", **btn_opt,
                                      command=lambda: self.on_select_category("Checker") )
        self.boot_gui    = tk.Button( self.frame_cat, image=self.icon_gui, relief="flat",
                                      command=lambda: self.on_launch(BR_GUI_PATH)        )

        self.btn_ui.grid(     row=0, column=0, padx=(0,5),  sticky="w")
        self.btn_import.grid( row=0, column=1, padx=(0,5),  sticky="w")
        self.btn_checker.grid(row=0, column=2, padx=(0,5),  sticky="w")
        self.boot_gui.grid(   row=0, column=3, padx=(0,0),  sticky="w")

        # アクションボタン
        self.frame_act = tk.Frame(self.frame_right, bg="#222222")
        self.frame_act.place(x=10, y=320, width=360, height=35)

        btn_opt2 = dict(font=(MUI,10), width=7)
        btn_opt3 = dict(font=(MUI, 8), padx=5, pady=5, width=7)

        self.btn_edit = tk.Button( self.frame_act, text="編 集",  **btn_opt2,
                                   bg="#555555", fg="#FFFFFF", command=self.on_edit )
        self.btn_bkup = tk.Button( self.frame_act, text="BackUp", **btn_opt2,
                                   bg="#555555", fg="#FFFFFF", command=self.on_backup )
        self.btn_exec = tk.Button( self.frame_act, text="実 行",  **btn_opt2,
                                   bg="#AACCFF", fg="#000000", command=self.on_execute )
        self.btn_upd  = tk.Button( self.frame_act, text="日時 更新",**btn_opt3,
                                   bg="#66CC99", fg="#000000",
                                   command=lambda:self.on_launch(DAILY_PATH, aug=" --all", cmd=True) )
        self.btn_cmt  = tk.Button( self.frame_act, text="Commit",  **btn_opt2,
                                   bg="#66CC99", fg="#000000",
                                   command=lambda:self.on_launch(BAT_COMMIT, cmd=True) )

        self.btn_edit.grid(row=0, column=0, padx=2)
        self.btn_bkup.grid(row=0, column=1, padx=2)
        self.btn_exec.grid(row=0, column=2, padx=2)
        self.btn_upd.grid( row=0, column=3, padx=2)
        self.btn_cmt.grid( row=0, column=4, padx=2)

        self.cat_buttons = {"Checker":self.btn_checker, "Import":self.btn_import, "UI":self.btn_ui}
        self.cat_normal_color = "#444444"
        self.cat_active_color = SELCOL

    #-------------------------------------------------------
    def on_select_category(self, cat):

        self.active_category = cat
        for key, btn in self.cat_buttons.items():
            if key == cat:
                btn.config(bg= self.cat_active_color, fg="#000000")
            else:
                btn.config(bg= self.cat_normal_color, fg="#FFFFFF")

        subcats = sorted({r["サブカテゴリ"] for r in self.file_map if r["カテゴリ"] == cat})
        self.list_subcat.delete(0, "end")

        for s in subcats:
            self.list_subcat.insert("end", f"  {s}")

        self.list_files.delete(0, "end")
        self.lbl_active.config(text= "")
        self.active_subcat        = None
        self.active_file          = None
        self.current_file_records = []
        self.active_record        = None
        self.clear_args()

    #-------------------------------------------------------
    def on_select_subcat(self, event=None):

        if not self.active_category: return

        sel = self.list_subcat.curselection()

        if not sel: return

        subcat_text        = self.list_subcat.get(sel[0]).strip()
        self.active_subcat = subcat_text
        files = [ r for r in self.file_map if r["カテゴリ"]     == self.active_category
                                          and r["サブカテゴリ"] == subcat_text          ]

        self.current_file_records = files
        self.list_files.delete(0, "end")

        for rec in files: self.list_files.insert("end",f"  {rec['ファイル名']}")

        self.lbl_active.config(text=  "")
        self.active_file   = None
        self.active_record = None 
        self.clear_args()

    #-------------------------------------------------------
    def on_select_file(self, event=None):

        sel = self.list_files.curselection()
        if not sel: return

        idx = sel[0]
        if not (0 <= idx < len(self.current_file_records)): return

        record             = self.current_file_records[idx]
        fname              = record["ファイル名"].strip()
        self.active_record = record
        self.active_file   = fname

        self.lbl_active.config(text= fname)
        self.display_args(fname)

    #-------------------------------------------------------
    def clear_args(self):

        for w in self.fr_arglist.winfo_children(): w.destroy()
        self.arg_widgets.clear()

    #-------------------------------------------------------
    def display_args(self, filename):

        self.clear_args()
        args = self.args_table.get(filename, [])
        if not args:
            lbl = tk.Label(self.fr_arglist, text= "(no arguments)", bg= "#333333", fg= "#888888")
            lbl.pack(anchor= "w", padx=4, pady=2)
            return

        for arg, required in args:
            rowf = tk.Frame(self.fr_arglist, bg= "#333333")
            rowf.pack(fill= "x", pady=2)
            rowf.grid_columnconfigure(0, minsize= 40)
            rowf.grid_columnconfigure(1, minsize=150)
            rowf.grid_columnconfigure(2, minsize=150)

            var_chk = None
            if arg.startswith("--"):
                var_chk = tk.BooleanVar(value= bool(required))
                chk     = tk.Checkbutton( rowf,   variable= var_chk,
                                                        bg= "#333333",
                                          activebackground= "#333333",
                                               selectcolor= "#333333"  )
                chk.grid(row=0, column=0, sticky= "w")
            else:
                tk.Label(rowf, text= "", bg= "#333333", width=2).grid(row=0, column=0)

            lbl = tk.Label( rowf, text= arg or "(positional)", anchor= "w",
                            font=(MUI,11), bg= "#333333", fg= "#FFFFFF"     )
            ent = tk.Entry( rowf, insertbackground= "#FFFFFF", width=14,
                            bg= "#222222", fg= "#FFFFFF",                  )
            if required: lbl.config(fg= "#FF6666")

            lbl.grid(row=0, column=1, sticky= "w", padx=(4, 6))
            ent.grid(row=0, column=2, sticky= "w", padx=(4, 0))

            self.arg_widgets.append({
                "type":"option" if arg.startswith("--") else "positional",
                "name":arg, "required":required, "var":var_chk, "entry":ent } )

    #-------------------------------------------------------
    def on_launch(self, path:str, aug:str="", cmd:bool=False):

        if not path.exists():
            self.show_msg("Error", f"{path} が存在しません。")
            return
        if str(path)[-3:] == ".py":
            subprocess.Popen(["cmd.exe", "/c", "python", str(path) + aug])
            return
        if cmd:
            subprocess.Popen(["cmd.exe", "/c", str(path) + aug])
        else:
            subprocess.Popen([sys.executable, str(path) + aug], shell=True)

    #-------------------------------------------------------
    def on_execute(self):

        if not self.active_record:
            self.show_msg("Info", "ファイルが選択されていません。"); return

        script_path = Path(self.active_record["実行パス"]) 
        if not script_path.exists():
            self.show_msg("Error", f"{script_path} が存在しません。"); return

        args = []
        for w in self.arg_widgets:
            val = w["entry"].get().strip()
            if w["type"] == "option":
                if w["var"] and w["var"].get():
                    args.append(w["name"])
                    if val: args.append(val)
            else: 
                if val: args.append(val)

        cmdline = [ "start", f'"{self.active_file}"', "cmd", "/K", "python",
                    f'"{script_path}"'                                       ] + args

        try: subprocess.Popen(" ".join(cmdline), shell= True)
        except Exception as e:
            self.show_msg("Error", f"実行に失敗しました:\n{e}")
    #-------------------------------------------------------
    def on_edit(self):

        if not self.active_record:
            self.show_msg("Info", "ファイルが選択されていません。"); return

        path = Path(self.active_record["実行パス"])
        if not path.exists():
            self.show_msg("Error", f"{path} が存在しません。"); return
        if not Path(TERAPAD_PATH).exists():
            self.show_msg("Error", "TeraPad が見つかりません。"); return

        subprocess.Popen([TERAPAD_PATH, str(path)], shell= True)

    #-------------------------------------------------------
    def on_backup(self):

        if not self.active_record:
            self.show_msg("Info", "バックアップ対象が選択されていません。"); return
        src = Path(self.active_record["実行パス"])
        if not src.exists():
            self.show_msg("Error", f"ソースが存在しません:\n{src}"); return

        category = self.active_category or record.get("カテゴリ") or "Unknown"
        subcat   = self.active_subcat or record.get("サブカテゴリ") or "Unknown" 
        today    = datetime.datetime.now().strftime("%Y%m%d")
        dst_dir  = BACKUP_ROOT / category / subcat / src.stem
        dst_dir.mkdir(parents= True, exist_ok= True)

        base_name = f"{today}{src.name}"
        dst_file  = dst_dir / base_name
        counter   = 2

        while dst_file.exists():
            stem, ext = os.path.splitext(base_name)
            dst_file  = dst_dir / f"{stem}({counter}){ext}"
            counter  += 1

        try:
            shutil.copy2(src, dst_file)
            self.show_msg("完了", f"バックアップ完了:\n{dst_file}")
        except Exception as e:
            self.show_msg("Error", f"バックアップ失敗:\n{e}")

    #-------------------------------------------------------
    def _is_true(self, v:str) -> bool:

        s = (v or "").strip().lower()
        return s in {"1","true","t","yes","y","on","?","?"}

    #-------------------------------------------------------
    def on_uploads(self):

        try: UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.show_msg("Error", f"UPLOAD_DIR作成に失敗:\n{UPLOAD_DIR}\n{e}")
            return

        copied  = 0
        skipped = []
        errors  = []

        for r in self.file_map:
            flag = r.get("アップロード")
            if not self._is_true(flag): continue

            src = Path((r.get("実行パス") or "").strip())
            if not src or not src.exists() or src.is_dir():
                skipped.append(r.get("ファイル名") or str(src))
                continue

            dst = UPLOAD_DIR / src.name
            try:
                if dst.exists():
                    try             : dst.unlink()
                    except Exception: pass

                shutil.copy2(src, dst)
                copied += 1
            except Exception as e: errors.append(f"{src.name}: {e}")

        msg = f"集約完了：{copied} 件コピー"
        if skipped:
            msg += f"\nスキップ：{len(skipped)} 件（存在しない/ディレクトリ）"
        if errors:
            msg += f"\nエラー：{len(errors)} 件"
        self.show_msg("Info", msg)

        if errors:
            self.show_msg("warn", "エラー詳細：\n" + "\n".join(errors[:10]),
                          title="一部失敗", width=520)

        try:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.show_msg("Error", f"UPLOAD_DIR作成に失敗:\n{UPLOAD_DIR}\n{e}")
            return

        open_explr(str(UPLOAD_DIR), 1760, 647, 800, 700)

    # ---------------- 固定位置ユーザーダイアログ --------------------
    def show_msg( self, kind:str, text:str, title:str= "",
                      x_ofs:int=60, y_ofs:int=60, width:int=420 ):

        self.update_idletasks()
        x = self.winfo_rootx() + int(x_ofs)
        y = self.winfo_rooty() + int(y_ofs)

        if kind == "error":
            ttl = title or "Error"
            fg  = "#FF6666"
        elif kind == "warn":
            ttl = title or "Warning"
            fg  = "#FFCC66"
        else:
            ttl = title or "Info"
            fg  = "#AACCFF"

        dlg = tk.Toplevel(self)
        dlg.title(ttl)
        dlg.configure(bg="#333333")
        dlg.geometry(f"+{x}+{y}")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.attributes("-topmost", True)
        dlg.grab_set()

        wrap = max(200, int(width))
        frm  = tk.Frame(dlg, bg="#333333")
        frm.pack(padx=16, pady=14)

        lbl_t = tk.Label( frm, text=ttl,  bg="#333333", fg=fg, anchor="w", font= (MUI, 13, BD) )
        lbl_m = tk.Label( frm, text=text, bg="#333333", fg="#FFFFFF", anchor="w",
                          font=(MUI, 12), justify="left", wraplength=wrap         )
        btn = tk.Button(  frm, text="OK", width=9, bg="#555555", fg="#FFFFFF",
                                                           command=dlg.destroy )

        lbl_t.pack(fill="x", pady=(0,  6))
        lbl_m.pack(fill="x", pady=(0, 10))
        btn.pack(anchor= "e")
        btn.focus_set()

        dlg.bind("<Return>", lambda e: dlg.destroy())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        dlg.wait_window(dlg)

# ==============================================================================
def open_explr(path: str, left=50, top=50, width=1000, height=700):

    target_path = os.path.abspath(path).lower()
    shell       = win32com.client.Dispatch("Shell.Application")
    
    os.startfile(target_path)

    hwnd = 0

    for _ in range(40):
        time.sleep(0.01)
        for window in shell.Windows():
            try:
                folder_path = window.Document.Folder.Self.Path.lower()
                if folder_path == target_path:
                    hwnd = window.HWND
                    break
            except Exception:
                continue
        if hwnd:
            break

    if hwnd:
        user32 = ctypes.windll.user32
        user32.SetWindowPos(hwnd, 0, left, top, width, height, 0x0014)
        user32.ShowWindow(hwnd, 1)

# ==============================================================================
if __name__ == "__main__":
    app = FileManagementGUI()
    app.mainloop()
