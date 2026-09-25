# -*- coding: utf-8 -*-
# summarize_today_info.py

from __future__  import annotations
from dataclasses import dataclass, field
from datetime    import datetime, timedelta, timezone, date
from typing      import Dict, List, Optional, Tuple
from Helpers.scraper_odds import fetch_all_odds
from Helpers.ev_scanner   import evaluate_ev, insert_odds_snapshot, ProbabilityProvider

import sqlite3, subprocess, threading, time, sys, os, signal, argparse, re, json, ctypes
import Dal as dal

VENUES = [ "桐   生",  "戸   田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲   郡", "常   滑",
           "   津   ", "三   国", "び わ こ", "住之江", "尼   崎", "鳴   門", "丸   亀", "児   島",
           "宮   島",  "徳   山", "下   関", "若   松", "芦   屋", "福   岡", "唐   津", "大   村", ]
# ---- 環境設定 ----------------------------------
# パス
BASE_DIR       = r"C:\boatrace"
DB_PATH        = os.path.join(BASE_DIR, "boatrace.db")
SP_DIR         = os.path.join(BASE_DIR, r"UI\Subprocess")
SP_INFO        = os.path.join(SP_DIR, "get_today_info.py")
SP_BEFORE      = os.path.join(SP_DIR, "get_Before_info.py")
SP_RESULT      = os.path.join(SP_DIR, "import_result_today.py")
LOCK_PATH      = os.path.join(BASE_DIR, r"tmp\json\summarizer.lock")
# 定数
CHANGE_INTERVAL = 300  #   変更: n秒 間隔で巡回
CANCEL_INTERVAL = 15   #   中止: n分 間隔で巡回
OFFSET_DISPLAY  = 12   #   展示:   前レース締切から n分後 に実行
OFFSET_RESULT   = 20   #   結果: 当該レース締切から n分後 に実行
RETRY_DIS       = 60   #   展示: 未反映なら n秒後に再試行
RETRY_RES       = 180  #   結果: 未反映なら n秒後に再試行
RETRY_NUM       = 10   #   展示/結果: リトライ回数
ODDS_SET_SIZE   = 212  #   オッズ総数(3T:120 + 3F:20 + 2T:30 + 2F:15 + KK:15 + TT:6 + FF:6)
JST             = timezone(timedelta(hours=9))

# ---- タスク定義 --------------------------------
@dataclass
class Task:
    kind:        str
    run_at:      datetime
    d:           date
    venue_id:    int
    race_no:     int
    tries:       int                = 0
    last_error:  Optional[str]      = None
    next_try_at: Optional[datetime] = None                        # 次回再試行時刻
    disabled:    bool               = False                       # RETRY_NUM 回連続失敗で無効化
    inflight:    bool               = False                       # 起動中
    meta:        Dict               = field(default_factory=dict) # 内部用メモ

# ========================= 本体クラス ===============================
class SummarizeTodayInfo:
    def __init__(self, db_path:str=DB_PATH, monitor:bool=True):

        self.db_path           = db_path
        self.monitor           = monitor
        self.conn              = sqlite3.connect(self.db_path)
        self.conn.row_factory  = sqlite3.Row
        self._stop             = False
        self._lock             = threading.Lock()
        self.running           = {"before":0, "result":0, "change":0, "cancel":0, "odds":0}
        self.run_limit         = {"before":3, "result":3, "change":3, "cancel":1, "odds":3}
        self._threads          = set()
        self._ctl_prev_mute    = None
        self.tasks:      List[Task] = []
        self.late_tasks: List[Task] = []
        self.prob_provider = ProbabilityProvider()  # 予想ロジック実装後差し替え

        th = threading.Thread(target=self._stdin_watch, daemon=True)
        th.start()
        self._threads.add(th)

    # ---------------------- 公開 API ----------------------
    def build_schedule_for_date(self, d:date):

        now  = self._now()
        cur  = self.conn.cursor()
        rows = cur.execute( """
                            SELECT venue_id, race_no,
                                   MIN(deadline_vote) AS dl, 
                                   MIN(series_title)  AS series_title,
                                   MIN(grade)         AS grade,
                                   MIN(day_no)        AS day_no,
                                   MIN(race_title)    AS race_title
                              FROM Race_programs
                             WHERE date =?
                          GROUP BY venue_id, race_no
                          ORDER BY venue_id, race_no
                            """, 
                            (d.strftime("%Y-%m-%d"),)                  ).fetchall()

        by_v = {}

        for v_id, rno, dl, _st, _gr, _dn, _rt in rows:
            by_v.setdefault(v_id, []).append({"race_no":int(rno), "deadline":dl})

        new_tasks:List[Task]  = []
        late_tasks:List[Task] = []

        for v_id, lst in by_v.items():
            lst_sorted    = sorted(lst, key=lambda x:x["race_no"])
            prev_deadline = None

            for rec in lst_sorted:
                rno      = rec["race_no"]
                deadline = self._parse_deadline(rec["deadline"])
                remain   = (deadline -now).total_seconds()

                #-------------
                if not self._exists_before(d, v_id, rno):
                    if now > deadline:
                        late_tasks.append( Task( kind="before", run_at=now, d=d,
                                                 venue_id=v_id, race_no=rno, meta={"prio":0} ) )
                    else:
                        if rno == 1: run_d =      deadline -timedelta(minutes=15)
                        else:        run_d = prev_deadline +timedelta(minutes=OFFSET_DISPLAY)
                        new_tasks.append( Task( kind="before", run_at=run_d, d=d,
                                                venue_id=v_id, race_no=rno, meta={"prio":1} ) )
                #-------------
                if not self._exists_result(d, v_id, rno):
                    if now > deadline +timedelta(minutes=40):
                        late_tasks.append( Task( kind="result", run_at=now, d=d,
                                                 venue_id=v_id, race_no=rno, meta={"prio":0} ) )
                    else:
                        run_r = deadline +timedelta(minutes=OFFSET_RESULT)
                        new_tasks.append( Task( kind="result", run_at=run_r, d=d,
                                                venue_id=v_id, race_no=rno, meta={"prio":1} ) )
                #-------------
                if not self._exists_odds(d, v_id, rno):
                    if remain <= 0:
                        late_tasks.append( Task( kind="odds", run_at=now, d=d, venue_id=v_id,
                                                 race_no=rno, meta={"deadline":deadline, "prio":0} ) )
                    else:
                        if remain > 1200: run_o = deadline -timedelta(minutes=20)
                        else:             run_o =      now +timedelta(seconds=10)
                        new_tasks.append( Task( kind="odds", run_at=run_o, d=d, venue_id=v_id,
                                                race_no=rno, meta={"deadline":deadline, "prio":1} ) )
                #-------------

                prev_deadline = deadline

            lst_valid = [x for x in lst_sorted if x["deadline"]]

            if lst_valid:
                first_deadline = self._parse_deadline(lst_valid[ 0]["deadline"])
                last_deadline  = self._parse_deadline(lst_valid[-1]["deadline"])

                if first_deadline and last_deadline and now < last_deadline:
                    new_tasks.append( Task( kind="change", run_at=first_deadline, d=d, race_no=1,
                                            venue_id=v_id, meta={"last_deadline":last_deadline}  ) )

        new_tasks.append( Task( kind="cancel", run_at=now, d=d, venue_id=0, race_no=0,
                                meta={"interval_min":CANCEL_INTERVAL}                  ) )

        with self._lock: 
            self.tasks.extend(new_tasks)
            self.late_tasks.extend(late_tasks)

        if self.monitor:
            bc = sum(1 for t in new_tasks if t.kind == "before")
            rc = sum(1 for t in new_tasks if t.kind == "result")
            cc = sum(1 for t in new_tasks if t.kind == "change")
            kc = sum(1 for t in new_tasks if t.kind == "cancel")
            oc = sum(1 for t in new_tasks if t.kind == "odds")

            print( f" Total tasks={len(new_tasks)}:\n"
                   f" before={bc} / result={rc} / change={cc} / cancel={kc} / odds={oc}" )

    # ------------------------------------------------------
    def _rebuild_schedule_for_venue(self, d:date, v_id:int):

        now  = self._now()
        cur  = self.conn.cursor()
        rows = cur.execute( """
                            SELECT race_no, MIN(deadline_vote) AS dl
                              FROM Race_programs
                             WHERE     date =?
                               AND venue_id =?
                          GROUP BY race_no
                          ORDER BY race_no
                            """,
                            (d.strftime("%Y-%m-%d"), v_id)            ).fetchall()

        if not rows: return

        with self._lock:
            self.tasks = [ t for t in self.tasks
                           if not ( t.d==d and     t.venue_id ==  v_id
                                           and     t.kind     in ("before","result","odds")
                                           and not t.inflight
                                           and not t.disabled                                ) ]

        lst_sorted            = [ {"race_no":int(r), "deadline":dl} for (r, dl) in rows ]
        new_tasks: List[Task] = []
        late_tasks:List[Task] = []
        prev_deadline         = None

        for rec in lst_sorted:
            rno      = rec["race_no"]
            deadline = self._parse_deadline(rec["deadline"])
            remain   = (deadline -now).total_seconds()

            #-----------------
            if not self._exists_before(d, v_id, rno) and not self._has_task("before", d, v_id, rno ):

                if now > prev_deadline +timedelta(minutes=OFFSET_DISPLAY):
                    late_tasks.append( Task( kind="before", run_at=now, d=d,
                                             venue_id=v_id, race_no=rno, meta={"prio":0} ) )
                else:
                    if rno == 1: run_d =      deadline -timedelta(minutes=15)
                    else:        run_d = prev_deadline +timedelta(minutes=OFFSET_DISPLAY)
                    new_tasks.append( Task( kind="before", run_at=run_d, d=d,
                                            venue_id=v_id, race_no=rno, meta={"prio":1} ) )
            #-----------------
            if not self._exists_result(d, v_id, rno) and not self._has_task("result", d, v_id, rno):

                if now > prev_deadline +timedelta(minutes=OFFSET_RESULT):
                    late_tasks.append( Task( kind="result", run_at=now, d=d,
                                             venue_id=v_id, race_no=rno, meta={"prio":0} ) )
                else:
                    run_r = deadline +timedelta(minutes=OFFSET_RESULT)
                    new_tasks.append( Task( kind="result", run_at=run_r, d=d,
                                            venue_id=v_id, race_no=rno, meta={"prio":1} ) )
            #-----------------
            if not self._exists_odds(d, v_id, rno) and not self._has_task("odds", d, v_id, rno):

                if remain <= 0:
                    late_tasks.append( Task( kind="odds", run_at=now, d=d, venue_id=v_id,
                                             race_no=rno, meta={"deadline":deadline, "prio":0} ) )
                else:
                    if remain > 1200: run_o = deadline -timedelta(minutes=20)
                    else:             run_o =      now +timedelta(seconds=10)
                    new_tasks.append( Task( kind="odds", run_at=run_o, d=d, venue_id=v_id,
                                           race_no=rno, meta={"deadline":deadline, "prio":1} ) )
            #-----------------

            prev_deadline = deadline

        if new_tasks:
            with self._lock: self.tasks.extend(new_tasks)
        if late_tasks:
            with self._lock: self.late_tasks.extend(late_tasks)

            if self.monitor:
                bc = sum(1 for t in new_tasks if t.kind=="before")
                rc = sum(1 for t in new_tasks if t.kind=="result")
                oc = sum(1 for t in new_tasks if t.kind=="odds")
                self._log(f"[rebuild] {d} jcd={v_id} before={bc} result={rc} odds={oc}")

    # ------------------------------------------------------
    def run_forever(self, tick_sec:int =10):

        if self.monitor: self._log("[SummarizeTodayInfo loop] start")
        try:
            while not self._stop:
                now     = self._now()
                due     = self._collect_due(now)
                started = {"before":0, "result":0, "change":0, "cancel":0, "odds":0}

                for t in due:
                    k = t.kind

                    with self._lock:
                        if self.running[k] >= self.run_limit[k]:
                            continue
                        if started[k] >= max(1, self.run_limit[k] - self.running[k]):
                            continue

                        t.inflight       = True
                        self.running[k] += 1
                        started[k]      += 1

                    th = threading.Thread(target=self._run_task_body, args=(t, now), daemon=True)
                    th.start()
                    self._threads.add(th)

                if sum(started.values()) == 0:
                    with self._lock:
                        idle = ( sum(self.running.values()) == 0 )

                    if idle:
                        lt = self._collect_one_late(now)
                        if lt is not None:
                            k = lt.kind

                            with self._lock:
                                if self.running[k] < self.run_limit[k]:
                                    lt.inflight      = True
                                    self.running[k] += 1
                                else:
                                    lt = None

                            if lt is not None:
                                th = threading.Thread(target=self._run_task_body, args=(lt, now),
                                                      daemon=True)
                                th.start()
                                self._threads.add(th)

                dead = {th for th in self._threads if not th.is_alive()}
                self._threads -= dead

                time.sleep(tick_sec)

        finally:
            for th in list(self._threads):
                try: th.join(timeout=5.0)
                except: pass

            self.conn.close()
            if self.monitor: self._log("[SummarizeTodayInfo loop] is stopped")

    # ------------------------------------------------------
    def _collect_due(self, now:datetime) -> List[Task]:

        due:List[Task] = []

        with self._lock:
            for t in self.tasks:
                if t.disabled: continue
                if t.inflight: continue
                if      ( t.next_try_at and (now >= t.next_try_at) ) or (
                      not t.next_try_at and (now >= t.run_at     ) ):
                    due.append(t)
        # ----------
        def _eff_time(x):
            return x.next_try_at or x.run_at or now
        # ----------
        due.sort(key=lambda x:(x.meta.get("prio", 0), _eff_time(x)))

        return due

    # ------------------------------------------------------
    def _collect_one_late(self, now:datetime) -> Optional[Task]:

        late_due:List[Task] = []

        with self._lock:
            self.late_tasks = [t for t in self.late_tasks if not (t.disabled and not t.inflight)]

            for t in self.late_tasks:
                if t.disabled: continue
                if t.inflight: continue

                if ( t.next_try_at and now >= t.next_try_at
                    ) or (not t.next_try_at and now >= t.run_at):
                    late_due.append(t)

        if not late_due: return None

        def _eff_time(x):
            return x.next_try_at or x.run_at or now

        late_due.sort(key=lambda x:(x.meta.get("prio", 0), _eff_time(x)))

        return late_due[0]

    # ------------------------------------------------------
    def _run_task_body(self, t:Task, now:datetime):

        try:
            if self._stop:
                t.disabled = True
                self._log( f"[    info    ] 【{t.kind}】[{VENUES[t.venue_id-1]}"
                           f" {t.race_no}R] stop requested; skip"               )
                return

            ok  = False
            err = None

            try:
                #-------------
                if t.kind   == "before":
                    if self._is_cancelled(t.d, t.venue_id, t.race_no):
                        t.disabled = True
                        self._log( f"[    info    ] 【before 】[{VENUES[t.venue_id-1]}"
                                   f" {t.race_no:02}R]  is cancelled (skip)"              )
                        return
                    ok = self._exec_before(t)
                    if not ok:
                        t.next_try_at = now + timedelta(seconds=RETRY_DIS)
                        print( f"[    info    ] 【before 】[{VENUES[t.venue_id-1]} {t.race_no:02}R]"
                               f"  retry at [{t.next_try_at.strftime('%H:%M:%S')}]"                   )
                #-------------
                elif t.kind == "result":
                    if self._is_cancelled(t.d, t.venue_id, t.race_no):
                        t.disabled = True
                        self._log( f"[    info    ] 【result】{VENUES[t.venue_id-1]}"
                                   f" {t.race_no:02}R]  is cancelled (skip)"          )
                        return
                    ok = self._exec_result(t)
                    if not ok: 
                        t.next_try_at = now + timedelta(seconds=RETRY_RES)
                        print( f"[    info    ] 【result】[{VENUES[t.venue_id-1]}{t.race_no:02}R]"
                               f"  retry at [{t.next_try_at.strftime('%H:%M:%S')}]"                )
                #-------------
                elif t.kind == "odds":
                    if self._is_cancelled(t.d, t.venue_id, t.race_no):
                        t.disabled = True
                        print( f"[    info    ] 【  odds  】[{VENUES[t.venue_id-1]}"
                               f" {t.race_no:02}R]  is cancelled (skip)")
                        return
                    ok = self._exec_odds(t)
                    if not ok:
                        interval = self._calc_odds_interval(t, now)
                        t.next_try_at = now + timedelta(seconds=interval)
                        print( f"[    info    ] 【  odds  】[{VENUES[t.venue_id-1]}"
                               f" {t.race_no:02}R] retry at [{t.next_try_at.strftime('%H:%M:%S')}]" )
                #-------------
                elif t.kind == "change":
                    if self._venue_finished(t.d, t.venue_id, now):
                        t.disabled = True
                        return
                    ok            = self._exec_change(t)
                    t.next_try_at = now +timedelta(seconds=CHANGE_INTERVAL)
                #-------------
                elif t.kind == "cancel":
                    ok            = self._exec_cancel(t)
                    interval      = t.meta.get("interval_min", CANCEL_INTERVAL)
                    t.next_try_at = self._now() +timedelta(minutes=interval)
                #-------------

            except Exception as e:
                ok  = False
                err = str(e)
                self._log(f"【{t.kind}】[{VENUES[t.venue_id-1]} {t.race_no:02}R]  内部エラー:{err}")

            t.tries += 1

            if err: t.last_error = err
            if ok and t.kind in ("before", "result", "odds"):
                t.disabled = True
            elif t.tries >= RETRY_NUM and t.kind in ("before","result"): 
                t.disabled = True
                self._log(f"【{t.kind}】 リトライオーバー (タスク破棄)")

        finally:
            with self._lock:
                t.inflight = False
                if self.running.get(t.kind, 0) > 0:self.running[t.kind] -= 1

    # ------------------------------------------------------
    def _cancel_tasks_from(self, d:date, venue_id:int, from_rno:int):

        with self._lock:
            n = 0
            for t in self.tasks:
                if t.disabled or t.inflight:                           continue
                if t.d != d   or t.venue_id != venue_id:               continue
                if t.kind not in ("before","result","change","odds"): continue
                if t.race_no is None or t.race_no < from_rno:          continue

                t.disabled = True
                n += 1

        self._log(f"[cancel] {d} {VENUES[t.venue_id-1]} r>={from_rno} disabled={n}")

    # ------------------------------------------------------
    def _calc_odds_interval(self, t:Task, now:datetime) -> int:

        remain = (t.meta["deadline"] -now).total_seconds()

        if remain <= 0:    return 60   # 締切後      ：1分感覚
        if remain <= 600:  return 120  # 締切10分前～：2分間隔
        if remain <= 1200: return 300  # 締切20分前～：5分間隔

        return 600

    # -------------------- 個別実行 ------------------------
    def _call_py(self, path:str, args:List[str]) -> Tuple[int, str, str]:

        cmd = [sys.executable, path] + args
        p   = subprocess.Popen( cmd, creationflags=0x08000000,
                                             stdin=subprocess.DEVNULL,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                              text=True             )

        try:
            while True:
                try:
                    out, err = p.communicate(timeout=1.0)
                    return p.returncode, out, err
                except subprocess.TimeoutExpired:
                    if self._stop:
                        p.terminate()
                        p.wait(timeout=3)
                        return 1, "", "Terminated by stop request"
        except Exception as e:
            return 1, "", str(e)

    # ------------------------------------------------------
    def _exec_before(self, t:Task) -> bool:

        task_name = f"【before 】[{VENUES[t.venue_id-1]} {t.race_no:02}R] "
        self._log(f"{task_name} start")

        rc, out, err = self._call_py( SP_BEFORE, [  "--date", t.d.strftime("%Y-%m-%d"),
                                                    "--venue", str(t.venue_id),
                                                     "--race", str(t.race_no),           ] )

        if rc != 0:
            self._log(f"{task_name} {err.strip() or out.strip() or f'ExitCode={rc}'}")
            return False

        ok = self._exists_before(t.d, t.venue_id, t.race_no)
        if ok: self._log(f"{task_name} Done update.")
        else:  self._log(f"{task_name} Not updated yet.")

        return ok

    # ------------------------------------------------------
    def _exec_result(self, t:Task) -> bool:

        task_name = f"【 result  】[{VENUES[t.venue_id-1]} {t.race_no:02}R] "
        self._log(f"{task_name} start")

        rc, out, err = self._call_py( SP_RESULT, [  "--date", t.d.strftime("%Y-%m-%d"),
                                                   "--venue", str(t.venue_id),
                                                    "--race", str(t.race_no),           ] )

        if rc != 0:
            self._log(f"{task_name} {err.strip() or out.strip() or f'ExitCode={rc}'}")
            return False

        ok = self._exists_result(t.d, t.venue_id, t.race_no)
        if ok: self._log(f"{task_name} Done update.")
        else:  self._log(f"{task_name} Not updated yet.")

        return ok
    # ------------------------------------------------------
    def _exec_change(self, t:Task) -> bool:

        task_name = f"【change】[{VENUES[t.venue_id-1]}       ] "
        self._log(f"{task_name} start")

        _args = ["A", "--date", t.d.strftime("%Y-%m-%d"), "--venue", str(t.venue_id)]

        if not t.meta.get("first_done"):
            _args.append("--first")

        rc, out, err = self._call_py(SP_INFO, _args)

        if rc != 0:
            self._log(f"{task_name} DB update fail")
            self._log(f"{task_name} {(err.strip() or out.strip() or f'ExitCode={rc}')}")
            return False

        t.meta["first_done"] = True
        found_deadline       = False
        found_absent         = False

        for ln in out.splitlines():
            s = ln.strip()

            if s.startswith("[OK] deadlines_updated:"):
                nums = s.split(":",1)[1].strip()
                if nums: found_deadline = True
            elif s.startswith("[OK] absents_updated:"):
                nums = s.split(":",1)[1].strip()
                if nums: found_absent = True

        if found_deadline:
            self._log(f"{task_name} find deadline chenged")
            self._rebuild_schedule_for_venue(t.d, t.venue_id)
        if found_absent:
            self._log(f"{task_name} find absent")
        if not found_deadline and not found_absent:
            self._log(f"{task_name} no changes")

        return True

    # ------------------------------------------------------
    def _exec_cancel(self, t:Task):

        task_name = f"【cancel 】[    {t.d.strftime('%m-%d')}    ] "
        self._log(f"{task_name} start")
        rc, out, err = self._call_py( SP_INFO, ["B", "--date", t.d.strftime("%Y-%m-%d"),] )
        if rc != 0:
            self._log(f"{task_name} DB update fail")
            self._log(f"{task_name} {(err.strip() or out.strip() or f'ExitCode={rc}')}")
            return False

        updated = False
        for ln in out.splitlines():
            s = ln.strip()

            if s.startswith("[OK] Insert cancelled:"):
                try:
                    m1 = re.search(r"jcd=(\d+)",  s)
                    m2 = re.search(r"rno>=(\d+)", s)
                    if m1 and m2:
                        jcd = int(m1.group(1))
                        frm = int(m2.group(1))
                        self._cancel_tasks_from(t.d, jcd, frm)
                        updated = True
                except Exception: pass

        if updated: self._log(f"{task_name} Find cancelled and done update.")
        else:       self._log(f"{task_name} no cancellations.")

        return True

    # ------------------------------------------------------
    def _exec_odds(self, t:Task) -> bool:

        task_name = f"【  odds  】[{VENUES[t.venue_id-1]} {t.race_no:02}R] "
        self._log(f"{task_name} called")

        try:
            data = fetch_all_odds( t.d.strftime("%Y%m%d"), t.venue_id, t.race_no,
                                     pages=("3T","3F","2T_2F","KK","TT_FF")       )
        except Exception as e:
            self._log(f"{task_name} fetch_odds error: {e}")
            return False

        if data.get("error"):
            self._log(f"{task_name} scraper partial error: {data['error']}")

        hits = evaluate_ev(data, t.d, t.venue_id, t.race_no, self.prob_provider)

        if hits: self._log(f"{task_name} EV hit: {len(hits)} 件")

        if data.get("final"):
            result = insert_odds_snapshot(data, t.d, t.venue_id, t.race_no, hits=hits)
            if result == 0:
                self._log(f"{task_name} fetch data error")
                return False
            if result == 1:
                self._log(f"{task_name} Done insert.")
                return True
            if result == 2:
                self._log(f"[WARN]] {task_name} insert but count !== 212")
            return True

        else: return False

    # -------------------- 反映確認 ------------------------
    def _exists_before(self, d:date, venue_id:int, race_no:int) -> bool:

        if self._is_cancelled(d, venue_id, race_no):
            return True

        d_iso = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)

        with sqlite3.connect(str(DB_PATH), timeout=30) as conn:
            row = conn.execute("""
                SELECT SUM( CASE WHEN dr.entry_id   IS     NULL THEN 1
                                 WHEN dr.is_absent   =        1 THEN 0
                                 WHEN dr.course     IS NOT NULL
                                  AND dr.exhibition IS NOT NULL
                                  AND dr.slit_ADJ   IS NOT NULL THEN 0
                                 ELSE 1
                            END                                         ) AS ng_count
                  FROM Race_programs rp
             LEFT JOIN Before_info   dr
                    ON dr.entry_id = rp.program_id
                 WHERE     rp.date= ?
                   AND rp.venue_id= ?
                   AND  rp.race_no= ?
                """,
               (d_iso, venue_id, race_no)).fetchone()

        ng = int((row[0] if row else 0) or 0)

        return (ng == 0)

    # ------------------------------------------------------
    def _exists_result(self, d:date, venue_id:int, race_no:int) -> bool:

        if self._is_cancelled(d, venue_id, race_no):
            return True

        sql = """
            SELECT COUNT(*)
              FROM Race_entries
             WHERE date=? AND venue_id=? AND race_no=?
               AND (finish_rank IS NOT NULL OR fault_code IN ('F', 'L', 'S', 'K'))
            """
        with self._connect_ro() as conn:
            cur = conn.cursor()
            cur.execute(sql, (d.strftime("%Y-%m-%d"), venue_id, race_no))
            row = cur.fetchone()

        return 1 if row[0] == 6 else 0

    # ------------------------------------------------------
    def _exists_odds(self, d:date, venue_id:int, race_no:int) -> dict:

        d_iso = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)

        with self._connect_ro() as conn:
            rows = conn.execute("""
                SELECT captured_at,
                       COUNT(*) AS cnt
                  FROM Odds
                 WHERE date=? AND venue_id=? AND race_no=?
              GROUP BY captured_at
                """,
               (d_iso, venue_id, race_no)).fetchall()

        set_count = 0

        if not rows: return False

        for r in rows:
            if r["cnt"] == 212:
                set_count += 1

        if set_count == 0: return False
        if set_count != 0: return True

    # ユーティリティ ---------------------------------------
    def _connect_ro(self) -> sqlite3.Connection:

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        return conn

    # ------------------------------------------------------
    def _parse_deadline(self, s:Optional[str]) -> Optional[datetime]:

        if not s: return None
        try:
            d_t = datetime.strptime(s, "%Y-%m-%d %H:%M")
            return d_t.replace(tzinfo=JST)

        except Exception:
            return None
    # ------------------------------------------------------
    def _is_cancelled(self, d:date, venue_id:int, race_no:int) -> bool:

        d_iso = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
        sql = """
            SELECT 1
              FROM Races
             WHERE date=? AND venue_id=? AND race_no=?
               AND status='cancelled'
             LIMIT 1
        """
        with self._connect_ro() as conn:
            cur = conn.execute(sql, (d_iso, venue_id, race_no))

            return cur.fetchone() is not None

    # ------------------------------------------------------
    def _venue_finished(self, d:date, venue_id:int, now:datetime) -> bool:

        sql = """
              SELECT MAX(deadline_vote)
                FROM Race_programs
               WHERE     date= ?
                 AND venue_id= ?
              """

        with self._connect_ro() as conn:
            cur = conn.execute(sql, (d.strftime("%Y-%m-%d"), venue_id))
            s   = cur.fetchone()[0]
        last = self._parse_deadline(s) if s else None

        return bool(last and now >= last)

    # ------------------------------------------------------
    def _has_task(self, kind:str, d:date, vid:int, rno:int) -> bool:

        with self._lock:
            for t in self.tasks:
                if ( t.kind == kind and t.d == d and t.venue_id == vid and
                                       t.race_no == rno and not t.disabled ):
                    return True

        return False

    # ------------------------------------------------------
    def _now(self) -> datetime:

        jst = timezone(timedelta(hours=9), name="JST")

        if getattr(self, "_sim_date", None) is not None:
            t = datetime.now(jst).time()
            return datetime.combine(self._sim_date, t).replace(tzinfo=jst)

        return datetime.now(jst)

    # ----------------------- ログ -------------------------
    def _log(self, s:str, mute:bool=False):

        if not self.monitor and not mute: return
        try:              t = datetime.now(JST).strftime("%H:%M:%S")
        except Exception: t = "--:--:--"

        print(f"[{t}] {s}", flush=True)

    # ------------------------------------------------------
    def _stdin_watch(self):

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                    if isinstance(cmd, dict):
                        if "stop" in cmd:
                            self._stop = bool(cmd["stop"])
                            if self._stop:
                                self._log("[control] stop requested", mute=True)
                        if "mute" in cmd:
                            new_monitor = not bool(cmd["mute"])
                            if new_monitor != self.monitor:
                                self.monitor = new_monitor
                                self._log(f"[monitor] {'ON' if self.monitor else 'OFF'}", mute=True)
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    self._log(f"[WARN] _stdin_watch error: {e}", mute=True)
        except Exception:
            pass
    # ------------------------------------------------------
    def stop(self):

        self._stop = True

# ====================================================================
def main():

    if not _acquire_singleton_lock():
        print("[INFO] Another instance is already running. Exiting.")
        return
    try:
        ap = argparse.ArgumentParser()
        ap.add_argument("--date", help="YYYY-MM-DD 仮想日付")
        args = ap.parse_args()

        app = SummarizeTodayInfo(DB_PATH, monitor=True)

        if args.date:
            d = datetime.strptime(args.date, "%Y-%m-%d").date()
            app._sim_date = d
        else:
            d = datetime.now(JST).date()

        print(f"[init] schedule date {d}")

        app.build_schedule_for_date(d)
        app.run_forever(tick_sec=5)

    finally:
        _release_singleton_lock()

#-----------------------------------------------------------
def _acquire_singleton_lock() -> bool:

    while True:
        if os.path.exists(LOCK_PATH):
            try:
                with open(LOCK_PATH, "r") as f:
                    old_pid = int(f.read().strip())

                h = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x00100000, False, old_pid)
                if h:
                    print("[INFO] Another instance is already running. Wait...")

                    res = ctypes.windll.kernel32.WaitForSingleObject(h, 3000) 
                    ctypes.windll.kernel32.CloseHandle(h)
                    if res == 0x00000000:
                        print(f"[info] Success to close old instance")
                    else:
                        continue

            except Exception as e:
                print(f"[error] Reading error: {e}")
                return False
        else:
            os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)

        with open(LOCK_PATH, "w") as f:
            f.write(str(os.getpid()))

        return True

# ----------------------------
def _release_singleton_lock():

    try:              os.remove(LOCK_PATH)
    except Exception: pass

#-----------------------------------------------------------
def _install_signal_handlers(app:"SummarizeTodayInfo"):

    #-----
    def _stop(_sig, _frm):
        try:              app.stop()
        except Exception: pass
    #-----
    for sig in (getattr(signal, "SIGBREAK", None), signal.SIGINT, signal.SIGTERM):
        if sig: 
            try:              signal.signal(sig, _stop)
            except Exception: pass

#=====================================================================
if __name__ == "__main__":
    main()
