# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\brouse_race_replay.py"

import webbrowser, argparse, sys, subprocess, ctypes, time
from datetime   import datetime as dt, date, timedelta, timezone

#=====================================================================
def brouse_race_replay(date_str, jo_code, race_no, v_name):
    """
    jo_code: 開催場コード (例: "15")
    stadium_name: ローマ字場名 (例: "marugame")
    date_str: 日付 (例: "20260824")
    race_no: レース番号 (例: 1 -> "01")
    """
    firefox_path      = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    stadium_param     = f"{jo_code}{v_name}"
    race_number_param = f"{int(race_no):02d}"

    url = ( f"https://front.player.boatrace-cdn.jp/player/vod?"
            f"service=boatcast&stadium={stadium_param}&raceType=race&"
            f"raceDate={date_str}&raceNumber={race_number_param}&autoplay=1&bitrate=high" )

    subprocess.Popen([firefox_path, "-new-window", url], shell=False)
    time.sleep(0.8)

    user32 = ctypes.windll.user32
    hwnd   = user32.GetForegroundWindow()

    user32.MoveWindow(hwnd, 1500, 100, 1000, 800, True)

#=====================================================================
def main():

    p = argparse.ArgumentParser()
    p.add_argument("--date",     required=True,  help="対象日(YYYY-MM-DD)")
    p.add_argument("--venue_id", required=True,  help="場コード")
    p.add_argument("--race_no",  required=True,  help="レースNo")
    p.add_argument("--v_name",   required=True,  help="場名")
    args  = p.parse_args()

    brouse_race_replay(args.date, args.venue_id, args.race_no, args.v_name)

#=====================================================================
if __name__ == "__main__":
    sys.exit(main())