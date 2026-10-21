# -*- coding: utf-8 -*-
# C:\boatrace\UI\boatrace_gui.py

import tkinter as tk
import threading, subprocess, sys, sqlite3, signal, traceback, json, os, queue
from tkinter             import ttk, messagebox
from datetime            import datetime as dt, date, time, timedelta, timezone
from pathlib             import Path
from collections         import deque

import Dal as dal
from Helpers.Custum_func import cFr, cLbl, cBtn
from Screens             import DBOpsScreen, DBSchemScreen, DBQueryScreen
from Screens             import PlayerAnalysisScreen, VenueAnalysisScreen, MotorAnalysisScreen
from Window              import RaceSelectWindow, RaceWindow

# ====================================================================
APP_TITLE = ""

GUI, MUI, HNH, CBR     = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, SK, BD = "groove", "solid", "ridge", "raised", "sunken", "bold"
ALL, CT                = "nsew", "center"

MAIN_BG = "#F0F4FA"
HDR_BG  = "#2B4A7A"
BTN_BG  = "#4A6A9A"
WHITE   = "#FFFFFF"
YELLOW1 = "#FFD700"
YELLOW2 = "#F1EE62"
GRAY1   = "#ECECEC"
GRAY2   = "#CFCFCF"
BLACK1  = "#000000"
BLACK2  = "#222222"
BLUE    = "#ff7474"
LIT_RED = "#ff5b5b"

HDR_B   = dict(bg=HDR_BG)
HDR_BF  = dict(bg=HDR_BG,  fg=WHITE)
BTN_BF  = dict(bg=BTN_BG,  fg=WHITE)
BTN_OFF = dict(bg=BTN_BG,  fg=WHITE,  Bd=(3,RA))
BTN_OPT = dict(bg=BTN_BG,  fg=WHITE,  Bd=(3,RA), font=(MUI,9,BD))
GRY_OFF = dict(bg=GRAY1,   fg=BLACK1, Bd=(1,RA))
YEL1_ON = dict(bg=YELLOW1, fg=BLACK2, Bd=(1,GR))
YEL2_ON = dict(bg=YELLOW2, fg=BLACK2, Bd=(1,SK))

DB_PATH       = r"C:\boatrace\boatrace.db"
DAILY_INSERT  = r"C:\boatrace\Import\Updata\daily_insert.py"
SUMMARIZ      = r"C:\boatrace\UI\summarize_today.py"

ON_LAUNCH     = {"ensure_prg":True, "summarrizer":True}

# ===========  共通ヘルパー  ===========
def today_iso() -> str:

    JST = timezone(timedelta(hours=9))
    return dt.now(JST).date().strftime("%Y-%m-%d")

# ------------------
def to_str(x) -> str:

    if isinstance(x,  str): return x
    if isinstance(x, date): return x.strftime("%Y-%m-%d")

    raise ValueError("str conv error")

# ------------------
def to_date(x) -> date:

    if isinstance(x, date): return x
    if isinstance(x,  str): return date.fromisoformat(x)

    raise ValueError("date conv error")

#-----------------------------
def days_ago(d:str, range:int)-> str:

    d = to_date(d)

    return to_str(d -timedelta(days=range))

# ----------------------------
def wid_txt(s:str) -> str:

    hair = "\u200A" 
    return hair.join(list(s))

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
        self.configure(bg=MAIN_BG)

        style = ttk.Style()
        style.configure("TButton",     font=(MUI,10), anchor="center")
        style.configure("MS.TButton",  font=(MUI,9),  anchor="center")
        style.configure("hdr.TButton", font=(MUI,9),  anchor="center")
        style.configure("RW.TButton",  font=(MUI,9), backgroud="blue", anchor="center")

        self._summ_proc   = None
        self._ext_text    = None
        self._ext_visible = False
        self._log_buf     = deque(maxlen=5000)
        self.current      = None
        self.contanr      = cFr(self, bg=MAIN_BG) ;self.contanr.pack(fill=tk.BOTH, expand=True)
        self.screens      = { "Main":       MainScreen(parent=self.contanr, app=self),
                               "DBO":      DBOpsScreen(parent=self.contanr, app=self),
                               "DBS":    DBSchemScreen(parent=self.contanr, app=self),
                               "DBQ":    DBQueryScreen(parent=self.contanr, app=self),
                               "RSW": RaceSelectWindow(parent=self.contanr, app=self), }

        self.show_screen("Main")

        if ON_LAUNCH["ensure_prg"]:  self.after(0,   self._ensure_programs_on_launch)
        if ON_LAUNCH["summarrizer"]: self.after(500, self._start_summarizer_on_launch)

    # --------------------------------------------
    def show_screen(self, name:str):

        if self.current is not None: self.current.pack_forget()

        scr = self.screens[name] ;scr.pack(fill=tk.BOTH, expand=True)
        self.current = scr

        if   name == "DBO": self.geometry("1800x1200")
        elif name == "DBS": self.geometry("1300x900")
        elif name == "DBQ": self.geometry("1350x900")
        elif name == "RSW": self.geometry( "800x650+350+300")
        else:               self.geometry( "600x500+90+0")

        if hasattr(scr, "on_show"):
            try: scr.on_show()
            except Exception as e: print("[WARN] on_show failed:", e)

    # =========  出走表ウィンドウを開く ==========
    def open_race_window(self, d_iso:str, venue_id:int, range_d:int, sub_window:bool):

        try:
            win = RaceWindow(self.contanr, self, d_iso, venue_id, range_d, sub_window)
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
            win = VenueAnalysisScreen(self, venue_id)
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

    # =============  日時更新 起動  ==============
    def _ensure_programs_on_launch(self):

        d_iso = today_iso()
        try:
            row = dal.fetch_one("""
                      SELECT COUNT(1)
                        FROM Race_programs
                       WHERE date=?
                      """,
                      (d_iso,) )
            cnt = int(row[0]) if row else 0

        except Exception as e:
            messagebox.showerror("DB接続エラー", f"Race_programs 確認時にエラー: {e}")
            return

        if cnt > 0: return

        dlg      = ProgressDialog(self, title="Loading...", message=f"{d_iso} の日時更新中")
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

            if finished["done"]:
                dlg.destroy()
                if not finished["ok"]:
                    messagebox.showerror( "当日データ取得エラー", finished["err"] )
                return

            self.after(100, poll)
        # ----------
        th = threading.Thread(target=worker, daemon=True)
        th.start()

        self.after(200, poll)

    # ============  サマライザー起動  ============
    def _start_summarizer_on_launch(self):

        try:
            self._summ_stop = False
            self._summ_mute = False
            self._summ_proc = subprocess.Popen( [(sys.executable or "python"), SUMMARIZ],
                                                 cwd           = str(Path(SUMMARIZ).parent),
                                                 stdin         = subprocess.PIPE,
                                                 stdout        = subprocess.PIPE,
                                                 stderr        = subprocess.STDOUT,
                                                 text          = True,
                                                 bufsize       = 1,
                                                 creationflags = 0x00000200                  )

            self._send_summarizer_command({"stop":False, "mute":False})

            th = threading.Thread(target=self._reader_summarizer, daemon=True)
            th.start()

        except Exception as e:
            print("[WARN] summarize_today launch failed:", e)

    # --------------------------------------------
    def _send_summarizer_command(self, cmd:dict):

        if self._summ_proc and self._summ_proc.poll() is None:
            try:
                if self._summ_proc.stdin:
                    self._summ_proc.stdin.write(json.dumps(cmd, ensure_ascii=False) + "\n")
                    self._summ_proc.stdin.flush()
            except Exception as e:
                print(f"[WARN] _send_summarizer_command: {e}")

    # --------------------------------------------
    def _reader_summarizer(self):

        try:
            if not self._summ_proc or not self._summ_proc.stdout:
                return
            for line in iter(self._summ_proc.stdout.readline, ''):
                cleaned = line.rstrip("\n")
                self._log_buf.append(cleaned)
                if self._ext_visible:
                    self.after(0, lambda line=cleaned:self._append_ext_log(line))
        except Exception:
            pass

        finally:
            try:
                if self._summ_proc and self._summ_proc.stdout:
                    self._summ_proc.stdout.close()
            except Exception:
                pass

    # --------------------------------------------
    def _append_ext_log(self, line:str):

        if self._ext_text is not None and self._ext_visible:
            try:
                self._ext_text.insert("end", line + "\n")
                self._ext_text.see("end")
            except Exception:
                pass

    # --------------------------------------------
    def _on_close(self):

        self._summ_stop = True
        self._send_summarizer_command({"stop":True})

        try:              self.destroy()
        except Exception: pass

# ========================== メイン画面 ==============================
# --------------------------------------------------------------------
class MainScreen(tk.Frame):

    def __init__(self, parent, app:App):
        super().__init__(parent)

        self.app = app
        fr_main  = cFr(self,    W=600, H=500)

        fr_titl  = cFr(fr_main, W=580, H= 30, **HDR_B)
        fr_panl  = cFr(fr_main, W=580, H=150, Bd=(1,GR))
        fr_body  = cFr(fr_main, W=580, H=260)
        fr_bar1  = cFr(fr_panl, W=580, H= 40)
        fr_bar2  = cFr(fr_panl, W=580, H= 40)

        fr_main._grid(R=0, C=0                       ) ;fr_main.Pgate()
        fr_titl._grid(R=0, C=0, padx=10, py=20       ) ;fr_titl.Pgate()
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

        cLbl(fr_titl,  text="  BoatRace GUI", font=(MUI,12,BD), **HDR_BF)._grid(R=0, C=0, Stk=ALL)
        cLbl(fr_titl,  text="MAIN MENU    ",  font=(GUI,11,BD), **HDR_BF)._grid(R=0, C=1, Stk=ALL)
        cLbl( fr_panl, text="ー Realtime summarizer ー",font=(GUI,10,BD), Anc="n"
             )._grid(R=0, C=0, Cspan=2, Stk="n", pady=(0,10))

        stat_opt = {"bg":"white", "fg":"black", "font":(MUI,9)}

        self.bt_boot = cBtn(fr_bar1, W=8, text=" 停  止 ",  **BTN_OPT, Com=self._toggle_boot, Csr="hand2")
        btn_mute     = cBtn(fr_bar2, W=8, text="ﾓﾆﾀ-出力",  **BTN_OPT, Com=self._toggle_mute, Csr="hand2")
        self.bt_extn = cBtn(fr_bar1, text="拡張ﾓﾆﾀ  表示 ", **BTN_OPT, Com=self._toggle_ext_monitor, Csr="hand2")
        lb_stat1 = cLbl(fr_bar1, W=18, text="--", Bd=(3,SK), py=4, **stat_opt)
        lb_stat2 = cLbl(fr_bar2, W=18, text="--", Bd=(3,SK), py=4, **stat_opt)

        self.bt_boot._grid(R=0, C=0, sticky="w", px= 20, ipady=2)
        btn_mute._grid(    R=1, C=0, sticky="w", px= 20, ipady=2)
        lb_stat1._grid(    R=0, C=1, sticky="w", px=(0,144))
        lb_stat2._grid(    R=1, C=1, sticky="w", px=(0,275))
        self.bt_extn._grid(R=0, C=2, sticky="w", px= 0, ipady=6, ipadx=4)

        btn_dbo = cBtn(fr_body, text="Ｄ Ｂ  参 照", Com=lambda:app.show_screen("DBO"), Csr="hand2")
        btn_dbs = cBtn(fr_body, text="SCHEMA 編 集", Com=lambda:app.show_screen("DBS"), Csr="hand2")
        btn_dbq = cBtn(fr_body, text="対 戦  履 歴", Com=lambda:app.show_screen("DBQ"), Csr="hand2")
        btn_rac = cBtn(fr_body, text="レース 選 択", Com=lambda:app.show_screen("RSW"), Csr="hand2")
        btn_plr = cBtn(fr_body, text="選 手  詳 細", Com=lambda a=self.app: open_player_picker(a))
        btn_fav = cBtn(fr_body, text="注 目  選 手", Com=lambda:app.show_screen("FPL"), Csr="hand2")

        btn_dbo._grid(R=0, C=0, ipady=15) ; btn_dbo._config(W=20, **BTN_OFF)
        btn_dbs._grid(R=1, C=0, ipady=15) ; btn_dbs._config(W=20, **BTN_OFF)
        btn_dbq._grid(R=2, C=0, ipady=15) ; btn_dbq._config(W=20, **BTN_OFF)
        btn_rac._grid(R=0, C=1, ipady=15) ; btn_rac._config(W=20, **BTN_OFF)
        btn_plr._grid(R=1, C=1, ipady=15) ; btn_plr._config(W=20, **BTN_OFF)
        btn_fav._grid(R=2, C=1, ipady=15) ; btn_fav._config(W=20, **BTN_OFF)

        self._lbl_monitor = [lb_stat1, lb_stat2]
        self.after(1000, self._update_monitor_state)

    #---------- 拡張 moni 表示/非表示 ------------
    def _toggle_ext_monitor(self):

        if getattr(self, "_ext_container", None) and self.app._ext_visible:
            self._hide_ext_monitor()
            self.bt_extn.config(text="拡張ﾓﾆﾀ   表示 ") 
        else:
            self._show_ext_monitor()
            self.bt_extn.config(text="拡張ﾓﾆﾀ 非表示") 

    #---------- moni 出力ON/OFF(mute) ------------
    def _toggle_mute(self):

        self.app._summ_mute = not getattr(self.app, "_summ_mute", False)
        self.app._send_summarizer_command({"mute": self.app._summ_mute})
        self._update_monitor_state()

    #----------  サマライザ 起動/停止 ------------
    def _toggle_boot(self):

        proc = getattr(self.app, "_summ_proc", None)

        if (proc is not None) and (proc.poll() is None):
            self.app._summ_stop = True
            self.app._send_summarizer_command({"stop": True})
        else:
            self.app._summ_stop = False
            self.app._summ_mute = False
            self.app._start_summarizer_on_launch()

        self._poll_monitor_state()

    # --------------------------------------------
    def _poll_monitor_state(self):

        self._update_monitor_state()

        proc       = getattr(self.app, "_summ_proc", None)
        is_running = (proc is not None) and (proc.poll() is None)

        if self.app._summ_stop and is_running:
            self.after(1000, self._poll_monitor_state)

    # --------------------------------------------
    def _update_monitor_state(self):

        try:
            proc        = getattr(self.app, "_summ_proc", None)
            is_running  = (proc is not None) and (proc.poll() is None)
            is_stop_req = getattr(self.app, "_summ_stop", False)
            is_mute     = getattr(self.app, "_summ_mute", False)

            if is_running:
                txt1 = "停止要求中" if is_stop_req else "稼働中"
                opt1 = dict(bg="yellow") if is_stop_req else dict(bg="#ceffd3")
                self.bt_boot.config(text="停 止")
            else:
                txt1 = "停止中"
                opt1 = dict(bg="#dedede", fg="black")
                self.bt_boot.config(text="起 動")

            txt2 = "ON" if (not is_mute) else "OFF"
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

# --------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()