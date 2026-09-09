# -*- coding: utf-8 -*-
# C:\boatrace\UI\boatrace_gui.py

import tkinter as tk
import threading, subprocess, sys, sqlite3, signal, traceback, json, os, queue
from tkinter                import ttk, messagebox
from datetime               import datetime as dt, date, time, timedelta, timezone
from pathlib                import Path
from collections            import deque

import Dal as dal
from Screens                import( DBOpsScreen, DBSchemScreen, DBQueryScreen, RaceSelectScreen,
                                    PlayerAnalysisScreen, VenuesAnalysisScreen,
                                     PlayerSamePeriodScreen, MotorAnalysisScreen )
from Helpers.build_rows     import query_program, make_rows, make_sub_rows
from Helpers.queries        import Query
from Helpers.series_idx     import update_series_idx, build_day_lbl
from Helpers.sub_window     import open_player_picker
from Helpers.Custum_func    import cFr, cLbl, cBtn
from Widgets.center_widgets import framing_center_widgets
from Widgets.placeholder    import build_main_placeholder, build_sub_placeholder
from Widgets.widgets        import ( framing_graph, framing_figure, framing_weather,
                                     clear_all_lanes, apply_absent_bg, set_player_image, )

# ====================================================================
APP_TITLE = ""

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

SCOL     = "#a5e6ff"
BG_COLOR = "#e9f1f2"
MAIN_BG  = "#F0F4FA"

VENUES = [ "桐生","戸田",  "江戸川","平和島","多摩川","浜名湖","蒲郡","常滑", "津",
           "三国","びわこ","住之江","尼崎",  "鳴門",  "丸亀",  "児島","宮島", "徳山",
           "下関","若松",  "芦屋",  "福岡",  "唐津",  "大村",                         ]
VENUE_ID = { name: i+1 for i, name in enumerate(VENUES) }

GRADE_IDX = { 0:"一般", 1:"G3", 2:"G2", 3:"G1", 4:"PG1", 5:"SG" }

FRM_COLOR = { 1: dict(bg="#FFFFFF", fg="#000000"),
              2: dict(bg="#000000", fg="#FFFFFF"),
              3: dict(bg="#D40000", fg="#FFFFFF"),
              4: dict(bg="#0066CC", fg="#FFFFFF"),
              5: dict(bg="#FFD400", fg="#000000"),
              6: dict(bg="#008A2E", fg="#FFFFFF"), }

CLS_COLOR = { "A1": dict(fill="#74b7ff"),
              "A2": dict(fill="#afffaf"),
              "B1": dict(fill="#dedede"),
              "B2": dict(fill="#ffbfbf"), }

RATE_OPT  = { 0:{"font":(MUI,8,BD), "fg":"black"},
              1:{"font":(MUI,8,BD), "fg":"blue" },
              2:{"font":(MUI,8,BD), "fg":"red"  }  }

ST_OPT    = { 0:{"font":(MUI,8,BD), "fg":"black"},
              1:{"font":(MUI,8,BD), "fg":"blue" },
              2:{"font":(MUI,8,BD), "fg":"red"  }  }

FAULT_OPT = { 0:{"font":(MUI, 8   ),"fg":"black"},
              1:{"font":(MUI, 9,BD),"fg":"red"  }, 
              2:{"font":(MUI, 9,BD),"fg":"red"  }, 
              3:{"font":(MUI, 9,BD),"fg":"red"  }, } 

ON_LAUNCH     = {"ensure_prg":True, "summarrizer":True}

DB_PATH       = r"C:\boatrace\boatrace.db"
DAILY_INSERT  = r"C:\boatrace\Import\daily_insert.py"
IMPORT_B      = r"C:\boatrace\Import\import_B_txt.py"
SUMMARIZ      = r"C:\boatrace\UI\summarize_today.py"
CTL_PATH      = r"C:\boatrace\tmp\json\ctl.json"
ODDS_CTL_PATH = r"C:\boatrace\tmp\json\odds_ctl.json"
ODDS_WINDOW   = r"C:\boatrace\UI\odds_window.py"

# ===========  共通ヘルパー  ===========
def jst_today() -> date:

    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date()

#-----------------------------
def today_iso() -> str:

    return jst_today().strftime("%Y-%m-%d")

#-----------------------------
def wid_txt(s:str) -> str:

    hair = "\u200A" 
    return hair.join(list(s))

#-----------------------------
def d_range(d:str, range:int):

    d_t = date.fromisoformat(d)
    return (d_t -timedelta(days=range), d_t)

# -- サマライザ制御：フラグI/O
def ctl_read():

    try:
        with open(CTL_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
            if not isinstance(d, dict): d = {}
    except Exception:
        d = {}

    return {"stop":bool(d.get("stop", False)), "mute":bool(d.get("mute", False))}

# ----------------------------
def ctl_write(*, stop=None, mute=None):

    d = ctl_read()
    if stop is not None: d["stop"] = bool(stop)
    if mute is not None: d["mute"] = bool(mute)

    os.makedirs(os.path.dirname(CTL_PATH), exist_ok=True)
    with open(CTL_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)

# ====================  モーダル進行ダイアログ  ======================
# --------------------------------------------------------------------
class ProgressDialog(tk.Toplevel):

    def __init__(self, parent, title="処理中", message="しばらくお待ちください..."):
        super().__init__(parent)

        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._disable_close)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=message, font=(GUI,11)).pack(pady=(2, 8))
        self.pb = ttk.Progressbar(frm, mode="indeterminate", length=280)
        self.pb.pack(pady=6)
        self.pb.start(50)
        self.update_idletasks()
        self.update()

        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2

        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # ----------------------------------
    def _disable_close(self): pass

# ==========================  App ルータ =============================
# --------------------------------------------------------------------
class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.title(APP_TITLE)
        self.geometry("700x600+500+250")
        self.minsize(500, 400)

        style = ttk.Style()
        style.configure("r.TButton", font=(MUI,9   ), anchor="center")
        style.configure("y.TButton", font=(MUI,8,BD), anchor="center")
        style.configure("m.TButton", font=(MUI,9   ), anchor="center")

        self._summ_proc   = None
        self._ext_text    = None
        self._ext_visible = False
        self._log_queue   = queue.Queue()
        self._log_buf     = deque(maxlen=5000)
        self.after(100, self._drain_log_queue)

        self.current = None
        contanr      = cFr(self, bg=MAIN_BG) ;contanr.pack(fill=tk.BOTH, expand=True)
        self.contanr = contanr
        self.screens = { "Main":       MainScreen(parent=contanr, app=self),
                          "DBO":      DBOpsScreen(parent=contanr, app=self, db_path=DB_PATH),
                          "DBS":    DBSchemScreen(parent=contanr, app=self, db_path=DB_PATH),
                          "DBQ":    DBQueryScreen(parent=contanr, app=self, db_path=DB_PATH),
                          "RSS": RaceSelectScreen(parent=contanr, app=self, db_path=DB_PATH)  }

        self.show_screen("Main")
        if ON_LAUNCH["ensure_prg"]:  self.after(0, self._ensure_programs_on_launch)
        if ON_LAUNCH["summarrizer"]: self.after(0, self._start_summarizer_on_launch)

    # --------------------------------------------
    def show_screen(self, name:str):

        if self.current is not None: self.current.pack_forget()

        scr = self.screens[name] ;scr.pack(fill=tk.BOTH, expand=True)
        self.current = scr

        if   name == "DBO": self.geometry("1500x900")
        elif name == "DBS": self.geometry("1300x900")
        elif name == "DBQ": self.geometry("1350x900")
        elif name == "RSS": self.geometry( "740x600+500+400")
        else:               self.geometry( "600x500+300+150")

        if hasattr(scr, "on_show"):
            try: scr.on_show()
            except Exception as e: print("[WARN] on_show failed:", e)

    # =========  出走表ウィンドウを開く ==========
    def open_race_window(self, date:str, venue_id:int, range_d:int, sub_window:bool):

        try:
            win = RaceWindow(self, date, venue_id, range_d, sub_window)
            win.grab_set()
        except Exception as e:
            messagebox.showerror("ウィンドウ生成エラー", f"{e}\n\n{traceback.format_exc()}")

    # ========  選手詳細ウィンドウを開く =========
    def open_p_analys(self, p_id:int, v:int=None, d:str=None, c:int=None):

        try:
            win = PlayerAnalysisScreen(self, p_id, v_id=v, d_iso=d, cou=c if c else 1)
            win.grab_set()
        except Exception as e:
            messagebox.showerror("ウィンドウ生成エラー", f"{e}\n\n{traceback.format_exc()}")

    # =======  開催場詳細ウィンドウを開く ========
    def open_v_analys(self, venue_id):

        try:
            win = VenuesAnalysisScreen(self, venue_id)
            win.grab_set()
        except Exception as e:
            messagebox.showerror("ウィンドウ生成エラー", f"{e}\n\n{traceback.format_exc()}")

    # ======  モーター詳細ウィンドウを開く =======
    def open_m_analys(self, m_no, v_id, upd_m):

        try:
            win = MotorAnalysisScreen(self, m_no, v_id, upd_m)
            win.grab_set()
        except Exception as e:
            messagebox.showerror("ウィンドウ生成エラー", f"{e}\n\n{traceback.format_exc()}")

    # ======  起動直後：当日分 Bデータ更新  =====
    def _ensure_programs_on_launch(self):

        d_iso = today_iso()
        try:
            with sqlite3.connect(DB_PATH, timeout=30) as c:
                c.execute("PRAGMA foreign_keys=ON;")
                row = c.execute(
                    "SELECT COUNT(1) FROM Race_programs WHERE date=?",
                    (d_iso,)).fetchone()
                cnt = int(row[0]) if row else 0
        except Exception as e:
            messagebox.showerror("DB接続エラー", f"Race_programs 確認時にエラー: {e}")
            return

        if cnt > 0: return

        dlg = ProgressDialog(self, title="Loading...",message=f"{d_iso} の日時更新中")
        finished = {"done":False, "ok":False, "err":None}
        # ----------
        def worker():
            try:
                py   = sys.executable or "python"
                cmd  = [py, DAILY_INSERT, "--overwrite", "--background"]
                proc = subprocess.run( cmd,
                                       stdout = subprocess.DEVNULL,
                                       stderr = subprocess.DEVNULL,
                                       stdin  = subprocess.DEVNULL,
                                       check  = False,
                                       cwd    = str(Path(DAILY_INSERT).parent), )
                finished["ok"] = (proc.returncode == 0)
                if not finished["ok"]:
                    finished["err"] = f"daily_insert.py [{proc.returncode}]"

            except Exception as e:
                finished["ok"]  = False
                finished["err"] = str(e)

            finally: finished["done"] = True
        # ----------
        def poll():

            if not finished["done"]: self.after(30, poll) ;return

            try:              dlg.destroy()
            except Exception: pass

            if not finished["ok"]:
                messagebox.showerror( "当日データ取得エラー", finished["err"] )
                return
        # ----------
        th = threading.Thread(target=worker, daemon=True)
        th.start()

        self.after(200, poll)

    # ============  サマライザー起動  ============
    def _start_summarizer_on_launch(self):

        try:
            ctl_write(stop=False, mute=False)
            self._summ_proc = subprocess.Popen( [(sys.executable or "python"), SUMMARIZ],
                                                 cwd           = str(Path(SUMMARIZ).parent),
                                                 stdin         = subprocess.DEVNULL,
                                                 stdout        = subprocess.PIPE,
                                                 stderr        = subprocess.STDOUT,
                                                 text          = True,
                                                 bufsize       = 1,
                                                 creationflags = 0x00000200                  )

            th = threading.Thread(target=self._reader_summarizer, daemon=True)
            th.start()

        except Exception as e: print("[WARN] summarize_today launch failed:", e)

    # --------------------------------------------
    def _reader_summarizer(self):

        try:
            if not self._summ_proc or not self._summ_proc.stdout:
                return
            for line in iter(self._summ_proc.stdout.readline, ''):
                self._log_queue.put(line.rstrip("\r\n"))
        except Exception: pass

        finally:
            try:
                if self._summ_proc and self._summ_proc.stdout:
                    self._summ_proc.stdout.close()
            except Exception: pass

    # --------------------------------------------
    def _drain_log_queue(self):

        try:
            while True:
                line = self._log_queue.get_nowait()
                self._log_buf.append(line)
                if self._ext_text is not None and self._ext_visible:
                    try:
                        self._ext_text.insert("end", line + "\n")
                        self._ext_text.see("end")
                    except Exception: pass
        except queue.Empty: pass

        self.after(100, self._drain_log_queue)

    # --------------------------------------------
    def _on_close(self):

        proc = getattr(self, "_summ_proc", None)

        if proc and proc.poll() is None:
            try:
                if hasattr(signal, "CTRL_BREAK_EVENT"):
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else: proc.terminate()
                proc.wait(timeout=5)

            except Exception:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    try: proc.kill()
                    except Exception: pass

        try:              self.destroy()
        except Exception: pass

# ========================== メイン画面 ==============================
# --------------------------------------------------------------------
class MainScreen(tk.Frame):

    def __init__(self, parent, app:App):
        super().__init__(parent)

        self.app = app
        fr_main  = cFr(self,    W=600, H=500)

        fr_titl  = cFr(fr_main, W=580, H= 70)
        fr_panl  = cFr(fr_main, W=580, H=150, Bd=(1, GR))
        fr_body  = cFr(fr_main, W=580, H=260)
        fr_bar1  = cFr(fr_panl, W=580, H= 40)
        fr_bar2  = cFr(fr_panl, W=580, H= 40)

        fr_main._grid(R=0, C=0                       ) ;fr_main.Pgate()
        fr_titl._grid(R=0, C=0, padx=10              ) ;fr_titl.Pgate()
        fr_panl._grid(R=1, C=0                       ) ;fr_panl.Pgate()
        fr_body._grid(R=2, C=0,          pady=(10, 0)) ;fr_body.Pgate()
        fr_bar1._grid(R=1, C=0                       ) ;fr_bar1.Pgate()
        fr_bar2._grid(R=2, C=0                       ) ;fr_bar2.Pgate()

        fr_titl.Cconf(0, W=1) ; fr_titl.Rconf(0, W=1)
        fr_titl.Cconf(1, W=1)

        fr_bar1.Cconf(0, W=1) ; fr_bar1.Rconf(0, W=1)
        fr_bar1.Cconf(1, W=1)
        fr_bar1.Cconf(2, W=1)
        fr_bar2.Cconf(0, W=1) ; fr_bar2.Rconf(0, W=1)
        fr_bar2.Cconf(1, W=1)

        fr_body.Rconf(0, W=1) ; fr_body.Cconf(0, W=1)
        fr_body.Rconf(1, W=1) ; fr_body.Cconf(1, W=1)
        fr_body.Rconf(2, W=1)

        cLbl(fr_titl, text="Boat Race GUI", font=(MUI,16,BD))._grid(R=0, C=0, Stk=ALL)
        cLbl(fr_titl, text="MAIN MENU    ", font=(GUI,12,BD))._grid(R=0, C=1, Stk=ALL)
        cLbl( fr_panl, text="リアルタイム  サマライザ",font=(GUI,10,BD), Anc="n"
             )._grid(R=0, C=0, Cspan=2, Stk="n", pady=(0, 10))

        stat_opt = {"bg":"white", "fg":"black"}

        self.btn_boot = ttk.Button(fr_bar1, text="停 止",  command=self._toggle_boot)
        btn_mute = ttk.Button(fr_bar2, text="ﾓﾆﾀ-出力",    command=self._toggle_mute)
        btn_extn = ttk.Button(fr_bar1, text="拡張ﾓﾆﾀ表示", command=self._toggle_ext_monitor)
        lb_stat1 = cLbl(fr_bar1, text=" -- ", W=18, H=1, Bd=(3,GR), pady=3, **stat_opt)
        lb_stat2 = cLbl(fr_bar2, text=" -- ", W=18, H=1, Bd=(3,GR), pady=3, **stat_opt)

        self.btn_boot.grid(row=0, column=0, sticky="w", padx= 20, ipady=2)
        btn_mute.grid(row=1, column=0, sticky="w", padx= 20, ipady=2)
        lb_stat1.grid(row=0, column=1, sticky="w", padx=(0, 140))
        lb_stat2.grid(row=1, column=1, sticky="w", padx=(0, 265))
        btn_extn.grid(row=0, column=2, sticky="w", padx= 0, ipady=2)

        btn_dbo = ttk.Button(fr_body, text="Ｄ Ｂ  参 照", command=lambda:app.show_screen("DBO"))
        btn_dbs = ttk.Button(fr_body, text="SCHEMA 編 集", command=lambda:app.show_screen("DBS"))
        btn_dbq = ttk.Button(fr_body, text="データ 比 較", command=lambda:app.show_screen("DBQ"))
        btn_rac = ttk.Button(fr_body, text="レース 選 択", command=lambda:app.show_screen("RSS"))
        btn_plr = ttk.Button(fr_body, text="選 手  詳 細", command=lambda a=self.app:
                                                                          open_player_picker(a) )

        btn_dbo.grid(row=0, column=0, ipady=18) ; btn_dbo.config(width=20)
        btn_dbs.grid(row=1, column=0, ipady=18) ; btn_dbs.config(width=20)
        btn_rac.grid(row=0, column=1, ipady=18) ; btn_rac.config(width=20)
        btn_plr.grid(row=1, column=1, ipady=18) ; btn_plr.config(width=20)
        btn_dbq.grid(row=2, column=1, ipady=18) ; btn_dbq.config(width=20)

        self._lbl_monitor = [lb_stat1, lb_stat2]
        self.after(500, self._poll_monitor_state)

    # ------ 拡張 moni 表示/非表示 ハンドラ ------
    def _toggle_ext_monitor(self):

        if getattr(self, "_ext_container", None) and self.app._ext_visible:
            self._hide_ext_monitor()
        else:
            self._show_ext_monitor()

    # --------------------------------------------
    def _toggle_mute(self):

        d = ctl_read()
        ctl_write(mute=not d["mute"])
        self._update_monitor_state()

    # --------------------------------------------
    def _toggle_boot(self):

        proc       = getattr(self.app, "_summ_proc", None)
        is_running = proc is not None and proc.poll() is None

        if is_running:
            ctl_write(stop=True)
        else:
            ctl_write(stop=False)
            self.app._start_summarizer_on_launch()

        self._poll_monitor_state()

    # --------------------------------------------
    def _poll_monitor_state(self):

        self._update_monitor_state()

        data       = ctl_read()
        proc       = getattr(self.app, "_summ_proc", None)
        is_running = (proc is not None) and (proc.poll() is None)

        if data["stop"] and is_running:
            self.after(1000, self._poll_monitor_state)
        elif not data["stop"] and not is_running:
            self.after(1000, self._poll_monitor_state)
        else:
            pass

    # --------------------------------------------
    def _update_monitor_state(self):

        try:
            data       = ctl_read()
            proc       = getattr(self.app, "_summ_proc", None)
            is_running = (proc is not None) and (proc.poll() is None)

            if is_running:
                txt1 = "停止要求中" if data["stop"] else "稼働中"
                opt1 = dict(bg="yellow") if data["stop"] else dict(bg="#ceffd3")
                self.btn_boot.config(text="停 止")
            else:
                txt1 = "停止中"
                opt1 = dict(bg="#dedede", fg="black")
                self.btn_boot.config(text="起 動")

            txt2 = "ON" if (not data["mute"]) else "OFF"
            opt2 = dict(bg="yellow") if txt2 == "OFF" else dict(bg="#ceffd3")

            self._lbl_monitor[0].config(text=f"{txt1}", **opt1, font=(MUI,9))
            self._lbl_monitor[1].config(text=f"{txt2}", **opt2, font=(MUI,9))

        except Exception as e:
            print("[WARN] monitor label update:", e)

    # --------------------------------------------
    def _show_ext_monitor(self):

        if not getattr(self, "_ext_container", None):
            self._ext_container = cFr(self, W=550, H=500)
            self._ext_container._grid(R=0, C=1)
            self._ext_container.Pgate()

            frm = cFr(self._ext_container, W=530, H=480)
            sb  = ttk.Scrollbar(frm, orient="vertical")
            tx  = tk.Text(frm, wrap="none",font=(MUI,11), fg="white", bg="black")

            frm._grid(R=0, C=0, Stk=ALL, padx=(0, 10), pady=(0, 5)) ; frm.Pgate()
            tx.grid(row=0, column=0, sticky=ALL)
            sb.grid(row=0, column=1, sticky="ns")
            frm.Rconf(0, weight=1) ; frm.Cconf(0, weight=1)
            tx.configure(state="normal")
            tx.config(yscrollcommand=sb.set)
            sb.config(command=tx.yview)
            self.app._ext_text = tx

            try:
                if self.app._log_buf:
                    tx.insert("end", "\n".join(self.app._log_buf) + "\n")
                    tx.see("end")
            except Exception: pass

        else:
            self._ext_container._grid(R=0, C=1)
            self._ext_container.Pgate()

        self.app._ext_visible = True

        try:
            h = max(self.app.winfo_height(), 500)
            self.app.geometry(f"1150x{h}")
        except Exception: pass

    # --------------------------------------------
    def _hide_ext_monitor(self):

        if getattr(self, "_ext_container", None):
            try:              self._ext_container.pack_forget()
            except Exception: pass

        self.app._ext_visible = False

        try:
            h = max(self.app.winfo_height(), 500)
            self.app.geometry(f"600x{h}")
        except Exception: pass

# =====================   出走表ウィンドウ  ==========================
# --------------------------------------------------------------------
class RaceWindow(tk.Toplevel):
    def __init__(self, app:App, date:str, venue_id:int, range_d:int=270, sub_window:bool=False):
        super().__init__(app)

        self.geometry("1220x1400+75+0")
        self.resizable(False, False)
        self.app         = app
        self.date        = date
        self.date_to     = dt.fromisoformat(date)
        self.date_frm    = self.date_to -timedelta(days=int(range_d))
        self.venue_id    = venue_id
        self.race_no     = 1
        self.wno         = 1
        self.last_date   = None
        self.last_race   = None
        self.range_d     = range_d
        self.range_v     = 1100
        self.sub_window  = [sub_window, 0]
        self.frame_order = [1,2,3,4,5,6]
        self.s_lane      = 0
        self.entry_rows  = []
        self.entry_prg   = {}
        self.clock_id    = None
        self.is_absent   = []
        self._odds_proc  = None

        self.protocol("WM_DELETE_WINDOW", self._on_rw_close)

        self.overall = Query( self.date_frm, self.date_to, query1=True, exclude_rookie=[True,False]
                             )._pack(by_course=True)

        root = cFr(self, width=1220, height=1400, padx=10,)
        root._grid(R=0, C=0) ;root.Pgate()

        if sub_window: self._start_odds_proc()

        #==================== Header =======================
        hdr1   = cFr(root,  W=1130, H=30, px=10) ;hdr1._grid(R=0, C=0, Stk="w")   ;hdr1.Pgate()
        hdr2   = cFr(root,  W=1130, H=30, px=10) ;hdr2._grid(R=1, C=0, Stk="w")   ;hdr2.Pgate()
        btns   = cFr(root,  W= 70,  H=60)        ;btns._grid(R=0, C=1, Rspan=2, Stk="e") ;btns.Pgate()
        hdr1L  = cFr(hdr1,  W=400,  H=30)        ;hdr1L._grid(R=0, C=0)  ;hdr1L.Pgate()
        hdr1R  = cFr(hdr1,  W=810,  H=30)        ;hdr1R._grid(R=0, C=1)  ;hdr1R.Pgate()
        hdr2L  = cFr(hdr2,  W=400,  H=30)        ;hdr2L._grid(R=0, C=0)  ;hdr2L.Pgate()
        hdr2R  = cFr(hdr2,  W=810,  H=30)        ;hdr2R._grid(R=0, C=1)  ;hdr2R.Pgate()
        hdr1LA = cFr(hdr1L, W=45,   H=30)        ;hdr1LA._grid(R=0, C=0) ;hdr1LA.Pgate()
        hdr1LB = cFr(hdr1L, W=300,  H=30)        ;hdr1LB._grid(R=0, C=1) ;hdr1LB.Pgate()
        hdr1LC = cFr(hdr1L, W=55,   H=30)        ;hdr1LC._grid(R=0, C=2) ;hdr1LC.Pgate()
        hdr2LA = cFr(hdr2L, W=70,   H=30)        ;hdr2LA._grid(R=0, C=0) ;hdr2LA.Pgate()
        hdr2LB = cFr(hdr2L, W=60,   H=30)        ;hdr2LB._grid(R=0, C=1) ;hdr2LB.Pgate()
        hdr2LC = cFr(hdr2L, W=50,   H=30)        ;hdr2LC._grid(R=0, C=2) ;hdr2LC.Pgate()
        hdr2LD = cFr(hdr2L, W=120,  H=30)        ;hdr2LD._grid(R=0, C=3) ;hdr2LD.Pgate()
        hdr2LE = cFr(hdr2L, W=100,  H=30)        ;hdr2LE._grid(R=0, C=4) ;hdr2LE.Pgate()

        self.lb_1LA = cLbl(hdr1LA, Anc=CT, font=(MUI,10,BD)); self.lb_1LA._grid(Stk=ALL)
        self.lb_1LB = cLbl(hdr1LB,         font=(MUI,10,BD)); self.lb_1LB._grid(Stk=ALL)
        self.lb_1LC = cLbl(hdr1LC, Anc=CT, font=(MUI, 9,BD)); self.lb_1LC._grid(Stk=ALL)
        self.lb_2LA = cLbl(hdr2LA,         font=(MUI,10))   ; self.lb_2LA._grid(Stk=ALL)
        self.lb_2LB = cLbl(hdr2LB,         font=(MUI,10,BD)); self.lb_2LB._grid(Stk=ALL)
        self.lb_2LC = cLbl(hdr2LC,         font=(MUI,10,BD)); self.lb_2LC._grid(Stk=ALL)
        self.lb_2LD = cLbl(hdr2LD,         font=(MUI,10))   ; self.lb_2LD._grid(Stk=ALL)
        self.lb_2LE = cLbl(hdr2LE,         font=(MUI, 9,BD)); self.lb_2LE._grid(Stk=ALL)

        self._mk_day_buttons (hdr1R)
        self._mk_race_buttons(hdr2R)

        bg  = "#F1EE62" if self.sub_window[0] else "#ececec"
        rel = GR if self.sub_window[0] else RA

        self.bt_change_sub = cBtn( btns, text=" SUB 切替 ", font=(MUI,8), Rel=RA, bg="#e9f1f2", px=2,
                             Com=lambda d=date, v=venue_id, r=1: self._change_sub_window(d, v, r))
        self.bt_toggle_sub = cBtn( btns, text=" ОＤＤＳ ", font=(MUI,8), Rel=rel, bg=bg, px=5,
                             Com=lambda d=date, v=venue_id, r=1: self._toggle_sub_window(d, v, r))

        self.bt_change_sub._grid(R=0, C=0, py=(0,3), Stk="e")
        self.bt_toggle_sub._grid(R=1, C=0, py=(2,0), Stk="e")

        #================ Body(Main/Sub) ===================
        body = cFr(root, W=1200, H=1340); body._grid(R=2, C=0, Cspan=2); body.Pgate()

        self.frm_main = cFr(body, W=1200, H=1002)
        self.frm_sub  = cFr(body, W=1200, H= 318)

        self.frm_main._grid(R=0, C=0, pady=(2, 0)) ;self.frm_main.Pgate()
        self.frm_sub._grid (R=1, C=0, pady=(8,10)) ;self.frm_sub.Pgate()

        self._widgets_main: dict[int, dict[str, tk.Widget]] = {}
        self._widgets_sub:  dict[int, dict[str, tk.Widget]] = {}

        build_main_placeholder(self, self.frm_main)
        build_sub_placeholder (self, self.frm_sub)

        # 初期表示更新 ********
        self._reload_for(self.date, self.venue_id, self.race_no)

        self.app.bind_all("<Button-4>", self._assaign_button)

    #================== 日程 ボタン ========================
    def _mk_day_buttons(self, parent:tk.Frame):

        for child in parent.winfo_children(): child.destroy()

        self._day_btns = {}
        labels, no_use = build_day_lbl(self.date, self.venue_id)

        for col, info in enumerate(labels):
            if not info["visible"]: continue
            dn   = info["label_no"]
            d    = info["date"]
            txt  = "初 日"  if dn == 1          else f"{dn}日目"
            txt  = "最終日" if info["final_day"] else txt
            btn  = ttk.Button( parent, text=txt, width=8, style="m.TButton", command=lambda
                               d=d:self._reload_for(d, self.venue_id, 1) )
            btn.grid(row=0, column=col, padx=2)
            self._day_btns[d] = btn

            if col >= 9: break

        self._highright_D_btn(d)

    # ================== レースボタン ======================
    def _mk_race_buttons(self, parent:ttk.Frame):

        self._race_btns = []
        for r in range(1, 13):
            btn = ttk.Button( parent, text=f"{r}Ｒ", style="m.TButton", width=6, command=lambda
                              r=r:self._reload_for(self.date, self.venue_id, r)               )
            btn.grid(row=0, column=r-1, padx=1, pady=0)
            self._race_btns.append(btn)

        self._highright_R_btn(1)

    # ============== サブ表示/非表示 ボタン ================
    def _toggle_sub_window(self, date, venue_id, race_no):

        if self.sub_window[0] == False:
            # ------ 表示 ON ------
            self.sub_window[0] = True
            self.bt_toggle_sub.config(bg="#F1EE62", relief=GR)

            if self.sub_window[1] == 0:
                if self._odds_proc and self._odds_proc.poll() is None:
                    self._odds_ctl_write(state="deiconify")
                else: self._start_odds_proc()
            else:
                pass   # result_window は後で実装

        else:
            # ------ 表示 OFF ------
            self.sub_window[0] = False
            self.bt_toggle_sub.config(bg="#ececec", relief=RA)

            if self.sub_window[1] == 0:
                if self._odds_proc and self._odds_proc.poll() is None:
                    self._odds_ctl_write(state="iconify")
            else:
                pass   # result_window は後で実装

    # --------------- odds subprocess 起動 -----------------
    def _start_odds_proc(self):

        self._odds_ctl_write(date=self.date, venue=self.venue_id, race=self.race_no, state="normal")

        try:
            self._odds_proc = subprocess.Popen(
                [ sys.executable, ODDS_WINDOW, "--date", self.date,
                                              "--venue", str(self.venue_id),
                                               "--race", str(self.race_no), ],
                  creationflags=0x00000200,                                    )

        except Exception as e:
            messagebox.showerror("odds_window 起動エラー", str(e))
            self.sub_window[0] = False
            self.bt_toggle_sub.config(bg="#ececec", relief=RA)
            return

    # --------------- odds_ctl.json 書き込み ---------------
    def _odds_ctl_write(self, *, date=None, venue=None, race=None, state=None):

        try:
            try:
                with open(ODDS_CTL_PATH, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if not isinstance(d, dict): d = {}
            except Exception:
                d = {}

            if date  is not None: d["date"]   = date
            if venue is not None: d["venue"]  = venue
            if race  is not None: d["race"]   = race
            if state is not None: d["state"]  = state

            os.makedirs(os.path.dirname(ODDS_CTL_PATH), exist_ok=True)
            with open(ODDS_CTL_PATH, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] odds_ctl_write: {e}")

    # ============== オッズ/結果 切替ボタン ================
    def _change_sub_window(self, date, venue_id, race_no):

        if self.sub_window[1] == 0:
            self.sub_window[1] = 1
            self.bt_toggle_sub.config(text=" Ｒesults ")
            if self.sub_window[0]:
                self._minimize_odds_proc()
                # result_window は後で実装
        else:
            self.sub_window[1] = 0
            self.bt_toggle_sub.config(text=" ОＤＤＳ ")
            if self.sub_window[0]:
                # result_window を終了して odds を起動
                self._start_odds_proc()

    # ==================== 表示/更新 エントリー ======================
    def _reload_for(self, date:str, venue_id:int, race_no:int, R:int=0):

        self._highright_D_btn(date)
        self._highright_R_btn(race_no)
        self.last_date                  = self.date
        self.last_race                  = self.race_no
        self.date                       = date
        self.race_no                    = race_no
        self.venue_id                   = venue_id
        self.frame_order                = [1, 2, 3, 4, 5, 6]
        self.entry_prg                  = query_program(self)
        self.entry_rows, self.data_rows = make_rows(self)

        if self._odds_proc and self._odds_proc.poll() is None:
            self._odds_ctl_write(date=date, venue=venue_id, race=race_no)

        self._update(R)
    # ---------------------------------
    def _update(self, R):

        clear_all_lanes(self)

        self.is_absent   = []
        self._set_absent()
        self._update_header()
        self._update_main_entries()
        self._update_sub_entries(R)
        framing_graph(self, self._widgets_sub[0]["Graph"], self.frame_order, self.data_rows,
                                                                          rows2=self.overall )
        update_series_idx(self, self.date, self.venue_id, self.race_no)

        for lane in range(1,7):
            frn    = self.frame_order[lane-1]
            is_abs = bool(self.entry_rows[frn]["absn"])
            if is_abs: apply_absent_bg(self._widgets_main[lane]["Lane"])

    # ---------------------------------
    def _set_absent(self):

        for frn in reversed(range(1, 7)):
             if self.entry_rows[frn]["absn"]:
                 self._frame_at_lane(6-len(self.is_absent), frn, upd=False)
                 self.is_absent.append(frn)

    # 並び変更API ----------------------
    def _frame_at_lane(self, lane:int, frame_no:int, upd:bool=True):

        if lane not in (1,2,3,4,5,6) or frame_no not in (1,2,3,4,5,6): return

        src_idx = self.frame_order.index(frame_no)
        dst_idx = lane - 1
        self.frame_order.pop(src_idx)
        self.frame_order.insert(dst_idx, frame_no)

        if upd: self._update(0)

    # ----------------------------------
    def _highright_D_btn(self, on_date:str):

        for key, btn in self._day_btns.items():
            if key == on_date : btn.state(['pressed'])
            else:               btn.state(['!pressed'])
    # ----------------------------------
    def _highright_R_btn(self, on:int):
    
        for idx, btn in enumerate(self._race_btns, start=1):
            if on == idx: btn.state(['pressed'])
            else:       btn.state(['!pressed'])
    # ----------------------------------
    def _assaign_button(self, event):

        self._reload_for(self.last_date, self.venue_id, self.last_race)

    #===================== Header: 表示/更新 =========================
    def _update_header(self):

        prg   = self.entry_prg
        _date = date.fromisoformat(prg['date'])

        self.lb_1LA.config(text= f" {GRADE_IDX.get(prg["grade"])}" if prg["grade"] or not 1 else "")
        self.lb_1LB.config(text= f"{prg['series_title']}")
        self.lb_1LC.config(text= f"{prg['day_no']}日目")
        self.lb_2LA.config(text= f"{_date.month} 月 {_date.day} 日")
        self.lb_2LB.config(text= f"  {prg['vname']}")
        self.lb_2LC.config(text= f"{self.race_no}R")
        self.lb_2LD.config(text= f"{prg['race_title'].strip()}")
        self.lb_2LE.config(text= f"締切  {prg['deadline'].strftime('%H：%M')}")

    #==================== widgets_Main: 表示/更新 ====================
    def _update_main_entries(self):

        for lane in range(1, 7):
            wdg_m = self._widgets_main.get(lane)
            wdg_s = self._widgets_sub.get( lane)
            frn   = self.frame_order[lane-1]
            row   = self.entry_rows[frn]
            d_row = self.data_rows[frn]

            home  = 1 if self.entry_prg['h_reg'] == row['rgns'] else 0
            r_opt = {"font":(MUI,9,BD),"fill":"blue"} if home else {"font":(MUI,10),"fill":"black"}
            flyg_opt = FAULT_OPT[row['flyg']]
            late_opt = FAULT_OPT[row['late']]
            if   float(row.get('stav')) >= 0.2 : stav_opt = ST_OPT[2]
            elif float(row.get('stav')) <= 0.12: stav_opt = ST_OPT[1]
            else:                                stav_opt = ST_OPT[0]

            if   row.get('rate1') >= 33.3: rate1_opt = RATE_OPT[1]
            elif row.get('rate1') <= 10:   rate1_opt = RATE_OPT[2]
            else:                          rate1_opt = RATE_OPT[0]
            if   row.get('rate2') >= 55:   rate2_opt = RATE_OPT[1]
            elif row.get('rate2') <= 20:   rate2_opt = RATE_OPT[2]
            else:                          rate2_opt = RATE_OPT[0]
            if   row.get('rate3') >= 70:   rate3_opt = RATE_OPT[1]
            elif row.get('rate3') <= 30:   rate3_opt = RATE_OPT[2]
            else:                          rate3_opt = RATE_OPT[0]

            wdg_m["frno"].config( text= str(frn),   **FRM_COLOR[frn]  )
            wdg_m["name"].config( text= f"{row.get('name')}"          )
            wdg_m["rate1"].config(text= f"{row.get('rate1'):.1f}",      **rate1_opt)
            wdg_m["rate2"].config(text= f"{row.get('rate2'):.1f}",      **rate2_opt)
            wdg_m["rate3"].config(text= f"{row.get('rate3'):.1f}",      **rate3_opt)
            wdg_m["late"].config( text= f"L{row.get('late')}",          **late_opt)
            wdg_m["flyg"].config( text= f"F{row.get('flyg')}",          **flyg_opt)
            wdg_m["stav"].config( text= f"{wid_txt(row.get('stav')) }", **stav_opt)
            wdg_m["mo_av"].config(text= f"{wid_txt(row.get('mo_av'))}")
            wdg_m["bo_av"].config(text= f"{wid_txt(row.get('bo_av'))}")

            set_player_image(wdg_m["photo"], row.get("pid"), (112, 160))
            wdg_m["photo"].bind( "<Button-1>",lambda e, p=row.get("pid"), c=lane, v=self.venue_id:
                                                self.app.open_p_analys(p, v=v, d=self.date, c=c) )
            wdg_m["mo_av"].bind( "<Button-1>",lambda e, m=row["mo_no"], v=self.venue_id:
                                      self.app.open_m_analys(m, v, self.entry_prg["upd_m"]) )

            wdg_m['cv1'].delete("all") ;wdg_m['cv2'].delete("all") ;wdg_m['cv3'].delete("all")

            for x, y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
               wdg_m['cv1'].create_text(23+x, 13+y, text=row['clss'], font=(CBR,12,BD), fill="white")
            wdg_m['cv1'].create_rectangle(8, 12, 42, 18, width=0, **CLS_COLOR[row['clss']])
            wdg_m['cv1'].create_text(23,  13, text=row['clss'],  font=(CBR,12,BD), fill="Black")
            wdg_m['cv1'].create_text(72,  14, text=row['scav'],  font=(MUI,9,BD), fill="Black")
            wdg_m['cv1'].create_text(132, 15, text=row['v_ave'], font=(MUI,8,BD), fill="Black")
            wdg_m['cv1'].create_text(161, 15, text=f"/ {row['v_cnt']}", font=(GUI,8), fill="Black")
            wdg_m['cv2'].create_text(23,  18, text=row['regp'],  font=(MUI,9), fill="Black")
            wdg_m['cv2'].create_text(92,  17, text=row['pid'],   font=(MUI,9), fill="Black")
            wdg_m['cv2'].create_text(160, 16, text=row['rgns'], **r_opt)
            wdg_m['cv3'].create_text(23,  20, text=row['age'],   font=(MUI,9), fill="Black")
            wdg_m['cv3'].create_text(88,  20, text=row['heig'],  font=(MUI,8), fill="Black")
            wdg_m['cv3'].create_text(151, 20, text=row['wkg'],   font=(MUI,8), fill="Black")

            f_l   = int(row['flyg'] or 0) + int(row['late'] or 0)
            c_opt = dict(fg="red") if row["cnt"][lane] < 10 else dict(fg="black")

            wdg_s["frno"].config(text= str(frn), **FRM_COLOR[frn]              )
            wdg_s["name"].config(text= f"{row.get('name')}"                    )
            wdg_s["flyg"].config(text= f"{f_l}" if f_l else ""                 )
            wdg_s["cnt" ].config(text= f"/ {row["cnt"][lane]}", **c_opt)

            framing_center_widgets(self, wdg_m["fr_Ctr"], lane, d_row, wdgt_no=self.wno)

    #==================== widgets_Sub: 表示/更新 =====================
    def _update_sub_entries(self, switch):

        self.sub_rows = make_sub_rows(self)
        row           = self.sub_rows["dspl"]
        prg           = self.entry_prg
        e_list        = []
        fig_row       = {f:{"st":None} for f in range(1,7)}

        for r in range(1,7):
            if row[r]["exhi"]: e_list.append(float(row[r]["exhi"]))
        fast_ex = ((sum(e_list)-max(e_list)-min(e_list)) / (len(e_list)-2))-0.05 if e_list else 0

        for lane in range(1,7):

            frn  = self.frame_order[lane-1]
            wdg  = self._widgets_sub.get(lane, {})
            tilt = row[frn]['tilt'] if row[frn]['tilt'] != -0.5 else "-"

            if   float(row[frn].get('exhi', 0) or 0) <= fast_ex:       e_opt={"fg":"blue"}
            elif float(row[frn].get('exhi', 0) or 0) >= fast_ex +0.15: e_opt={"fg":"red"} 
            else: e_opt={"fg":"black"}

            wdg["tilt"].config(text= f"{tilt}"                 )
            wdg["exhi"].config(text= wid_txt(f"{row[frn].get('exhi', "")}"), **e_opt)
            wdg["rpr1"].config(text= f"{row[frn].get('rpr1')}" )
            wdg["rpr2"].config(text= f"{row[frn].get('rpr2')}" )
            wdg["rpr3"].config(text= f"{row[frn].get('rpr3')}" )

            absn               = row[frn]["absn"] or 0
            st_ave             = self.data_rows[frn]["own"][lane]["st_ave"]
            fig_row[frn]["st"] = st_ave if not absn else None 

        framing_figure(self, self._widgets_sub[0]["Fig_A"], self.frame_order, A=fig_row)

        wspd  = row[0]['wspd']
        wave  = row[0]['wave']
        stab  = row[0]['stab']
        lap   = row[0]['shlp']
        m_pas = (date.fromisoformat(self.date).month - int(prg["upd_m"]))%12
        b_pas = (date.fromisoformat(self.date).month - int(prg["upd_b"]))%12
        vname = "　 ".join(prg["vname"]) if len(prg["vname"]) < 3 else  prg["vname"]

        self._widgets_sub[0]["vname"].config(text= f"BR  {vname}" )
        self._widgets_sub[0]["w_typ"].config(text= f"{'　'.join(prg['w_typ'])} " )
        self._widgets_sub[0]["upd_m"].config(text= f" {m_pas}  ヶ月 ")
        self._widgets_sub[0]["upd_b"].config(text= f" {b_pas}  ヶ月 ")
        self._widgets_sub[0]["wspd" ].config(text= f"風 速  {wspd}  m" )
        self._widgets_sub[0]["wave" ].config(text= f"波 高  {wave} cm" )
        self._widgets_sub[0]["stab" ].config(text= "安 定 版 装 着" if stab else "",
                                               bg="yellow" if stab else "white"     )
        self._widgets_sub[0]["shlp" ].config(text= "周 回 短 縮 1200 m" if lap else "",
                                               bg="yellow" if lap else "white"      )
        self._widgets_sub[0]["deadl"].config(text= f"  {prg['deadline'].strftime('%H：%M')}  ")
        # --------------
        def _update_clock():

            if self.clock_id is not None:
                self._widgets_sub[0]["now"].after_cancel(self.clock_id)
                self._widgets_sub[0]["last"].config(font=(MUI,10,BD))
            _now = dt.now().strftime("%H : %M")
            last = int( (prg['deadline'] - dt.now()).total_seconds() )

            self._widgets_sub[0]["now"].config(text=f"  {_now}  ")

            if  300 <  last <= 1800:
                self._widgets_sub[0]["last"].config(text=f"{int(last / 60)} 分", fg="black")
            elif 60 <  last <=  300:
                self._widgets_sub[0]["last"].config(text=f"{int(last / 60)} 分", fg="red")                
            elif  0 <= last <=   60:
                self._widgets_sub[0]["last"].config(text=f"{int(last)     } 秒", fg="red")
            elif  0 >= last:
                self._widgets_sub[0]["last" ].config(text="投票 締切", fg="black", font=(MUI,8))
            else: self._widgets_sub[0]["last"].config(text="")

            self.clock_id = self._widgets_sub[0]["now"].after(1000, _update_clock)
        # --------------
        _update_clock()
        self._update_figure(switch)

    #=================================================================
    def _update_figure(self, switch):

            row       = self.sub_rows["rslt"] if switch else self.sub_rows["dspl"]
            fig_order = [1,2,3,4,5,6]
            c_dict    = {}
            fig_row   = {f:{"st":None, "opt":{}, "wm":None} for f in range(1,7)}

            for frn in range(1, 7):

                fig_row[frn]["st"] = row[frn]["s_adj"]
                absn               = row[frn]["absn"] or 0
                cour               = row[frn]["cour"] or 6
                fig_order[cour-1]  = frn

                if switch:
                    rank = row[frn]["finish"]
                    if isinstance(rank, int):
                        if rank == 1:
                            rank = row[frn].get("w_move", "")
                            fig_row[frn]["opt"] = dict(text=rank, font=(HNH,10,BD), fill="blue")
                        else:
                            fig_row[frn]["opt"] = dict(text=rank, font=(HNH,10,BD), fill="black")
                    else: fig_row[frn]["opt"] = dict(text=rank, font=(HNH,10,BD), fill="red")

            if switch:
                self._widgets_sub[0]["bt_fig1"].config(relief=RA, bg="#E1E1E1")
                self._widgets_sub[0]["bt_fig2"].config(relief=RD, bg="#F1EE62")
            else:
                self._widgets_sub[0]["bt_fig1"].config(relief=RD, bg="#F1EE62")
                self._widgets_sub[0]["bt_fig2"].config(relief=RA, bg="#E1E1E1")

            framing_figure(self, self._widgets_sub[0]["Fig_B"], fig_order, B=fig_row)
            framing_weather(self, self._widgets_sub[0]["wthr"], self._widgets_sub[0]["wdir"], row)

    # ==================== ウィンドウ終了処理 =====================
    def _on_rw_close(self):

        self._stop_odds_proc()
        try: self.destroy()
        except Exception: pass
    # ------ odds subprocess 終了 ------
    def _stop_odds_proc(self):

        if self._odds_proc and self._odds_proc.poll() is None:
            try:
                self._odds_ctl_write(state="stop")
                self._odds_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._odds_proc.terminate()
            except Exception:
                pass
            finally:
                self._odds_proc = None
        self._odds_ctl_write(state="normal")
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
