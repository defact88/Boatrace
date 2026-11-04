# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\brouse.py"

import webbrowser, argparse, sys, subprocess, ctypes, time
from datetime   import datetime as dt, date, timedelta, timezone


V_NAME  = [ "kiryu",       "toda",      "edogawa",  "heiwajima", "tamagawa", "hamanako",
            "gamagori",    "tokoname",  "tsu",      "mikuni",    "biwako",   "suminoe",
            "amagasaki",   "naruto",    "marugame", "kojima",    "miyajima", "tokuyama",
            "shimonoseki", "wakamatsu", "ashiya",   "fukuoka",   "karatsu",  "omura",    ]

#-----------------------------
def _str_date(d:str):

    d = date.fromisoformat(d)

    return d.strftime("%Y%m%d")

#=====================================================================
def brouse_race_replay(date_iso, v_id, race_no):

    date_str     = _str_date(date_iso)
    firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    stadium      = f"{v_id}{V_NAME[v_id-1]}"
    race_number  = f"{int(race_no):02d}"

    url = ( f"https://front.player.boatrace-cdn.jp/player/vod?"
            f"service=boatcast&stadium={stadium}&raceType=race&"
            f"raceDate={date_str}&raceNumber={race_number}&autoplay=1&bitrate=high" )

    subprocess.Popen([firefox_path, "-new-window", url], shell=False)
    time.sleep(0.8)

    user32 = ctypes.windll.user32
    hwnd   = user32.GetForegroundWindow()

    user32.MoveWindow(hwnd, 1500, 100, 1000, 800, True)

#=====================================================================
def main():

    p = argparse.ArgumentParser()
    p.add_argument("--date",     type=str, required=True,  help="対象日(YYYY-MM-DD)")
    p.add_argument("--venue_id", type=int, required=True,  help="場コード")
    p.add_argument("--race_no",  type=int, required=True,  help="レースNo")
    args  = p.parse_args()

    brouse_race_replay(args.date, args.venue_id, args.race_no)

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())