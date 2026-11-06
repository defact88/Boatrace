# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\brouse_play.py"

import webbrowser, argparse, sys, subprocess, ctypes, time, pyautogui
import pygetwindow as gw
from datetime   import datetime as dt, date, timedelta, timezone


V_NAME  = [ "kiryu",       "toda",      "edogawa",  "heiwajima", "tamagawa", "hamanako",
            "gamagori",    "tokoname",  "tsu",      "mikuni",    "biwako",   "suminoe",
            "amagasaki",   "naruto",    "marugame", "kojima",    "miyajima", "tokuyama",
            "shimonoseki", "wakamatsu", "ashiya",   "fukuoka",   "karatsu",  "omura",    ]

Y_SET   = [ -20, 20, -5,-50,-45, 60,
             38,-20, 10, 15,-25, 20, 
             20,  0, 20, 50, 20,-10,
            -20, 10,-35,-60, 20, 20, ]

Y_SET2  = [   5, 20,-10,  0, 20, 28,
             28, 18,  0, 35, 15, 28, 
             28, 25,-20, 50, 20, 35,
             28, 25, 15, 15, 28, 25, ]

#-----------------------------
def _str_date(d:str):

    d = date.fromisoformat(d)

    return d.strftime("%Y%m%d")

#=====================================================================
def brouse_live(date_iso:str, v_id:int):

    try:
        old_windows = gw.getWindowsWithTitle('Player')
        for w in old_windows:
            w.close()
        if old_windows:
            time.sleep(0.4)
    except Exception:
        pass

    date_str     = _str_date(date_iso)
    firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    stadium      = f"{v_id:02d}{V_NAME[v_id-1]}"

    url = ( f"https://front.player.boatrace-cdn.jp/player/live?"
            f"service=boatcast&stadium={stadium}&sourceType=mix&"
            f"dvr=1&audioMode=0&autoplay=1&bitrate=high"           )

    cmd = [firefox_path, "-P", "boatrace",
                         "-no-remote",
                         "-new-window", url]

    subprocess.Popen(cmd, shell=False)
    time.sleep(0.9)

    user32 = ctypes.windll.user32
    hwnd   = user32.GetForegroundWindow()
    user32.MoveWindow(hwnd, 1296, 0, 1271, 748, True)

    windows = gw.getWindowsWithTitle('Player')
    if windows:
        x, y = pyautogui.position()
        win = windows[0]
        win.activate()
        time.sleep(0.5)

        bar_x = win.left +int(win.width * 0.38) +Y_SET[v_id-1]
        bar_y = win.bottom - 55 
        
        pyautogui.click(bar_x, bar_y)
        time.sleep(1.0)
        time.sleep(0.3)
        pyautogui.click(win.left+100, win.bottom-35)
        pyautogui.click(win.left+116, win.bottom-35)
        pyautogui.moveTo(x, y)

#=====================================================================
def brouse_replay(date_iso:str, v_id:int, race_no:int):

    try:
        old_windows = gw.getWindowsWithTitle('Player')
        for w in old_windows:
            w.close()
        if old_windows:
            time.sleep(0.4)
    except Exception:
        pass

    date_str     = _str_date(date_iso)
    firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    stadium      = f"{v_id:02d}{V_NAME[v_id-1]}"
    race_number  = f"{int(race_no):02d}"

    url = ( f"https://front.player.boatrace-cdn.jp/player/vod?"
            f"service=boatcast&stadium={stadium}&raceType=race&"
            f"raceDate={date_str}&raceNumber={race_number}&autoplay=1&bitrate=high" )

    cmd = [firefox_path, "-P", "boatrace",
                         "-no-remote",
                         "-new-window", url]

    subprocess.Popen(cmd, shell=False)
    time.sleep(0.9)

    user32 = ctypes.windll.user32
    hwnd   = user32.GetForegroundWindow()
    user32.MoveWindow(hwnd, 1296, 0, 1271, 748, True)

    windows = gw.getWindowsWithTitle('Player')
    if windows:
        x, y = pyautogui.position()
        win = windows[0]
        win.activate()
        time.sleep(0.5)

        bar_x = win.left +int(win.width * 0.38) +Y_SET[v_id-1]
        bar_y = win.bottom - 55 
        
        pyautogui.click(bar_x, bar_y)
        time.sleep(1.0)
        pyautogui.click(bar_x, bar_y)
        time.sleep(0.3)
        pyautogui.click(win.left+100, win.bottom-35)
        pyautogui.click(win.left+116, win.bottom-35)
        pyautogui.moveTo(x, y)

#=====================================================================
def brouse_tenji(date_iso:str, v_id:int, race_no:int):

    try:
        old_windows = gw.getWindowsWithTitle('Player')
        for w in old_windows:
            w.close()
        if old_windows:
            time.sleep(0.4)
    except Exception:
        pass

    date_str     = _str_date(date_iso)
    firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    stadium      = f"{v_id:02d}{V_NAME[v_id-1]}"
    race_number  = f"{int(race_no):02d}"

    url = ( f"https://front.player.boatrace-cdn.jp/player/vod?"
            f"service=boatcast&stadium={stadium}&raceType=exhibition&"
            f"raceDate={date_str}&raceNumber={race_number}&autoplay=1&bitrate=high" )

    cmd = [firefox_path, "-P", "boatrace",
                         "-no-remote",
                         "-new-window", url]

    subprocess.Popen(cmd, shell=False)
    time.sleep(0.9)

    user32 = ctypes.windll.user32
    hwnd   = user32.GetForegroundWindow()
    user32.MoveWindow(hwnd, 1296, 0, 1271, 748, True)

    windows = gw.getWindowsWithTitle('Player')
    if windows:
        x, y = pyautogui.position()
        win = windows[0]
        win.activate()
        time.sleep(0.5)

        bar_x = win.left +int(win.width * 0.28) +Y_SET2[v_id-1]
        bar_y = win.bottom - 55 
        
        pyautogui.click(bar_x, bar_y)
        time.sleep(1.0)
        pyautogui.click(bar_x, bar_y)
        time.sleep(0.3)
        pyautogui.click(win.left+100, win.bottom-35)
        pyautogui.click(win.left+116, win.bottom-35)
        pyautogui.moveTo(x, y)

#=====================================================================
def main():

    p = argparse.ArgumentParser()
    p.add_argument("--date",     type=str, required=True,  help="対象日(YYYY-MM-DD)")
    p.add_argument("--venue_id", type=int, required=True,  help="場コード")
    p.add_argument("--race_no",  type=int, required=True,  help="レースNo")
    args  = p.parse_args()

    brouse_race(args.date, args.venue_id, args.race_no)

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())