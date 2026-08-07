# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\querries.py

from typing                 import Dict, Optional
from dateutil.relativedelta import relativedelta
from datetime               import datetime as dt, date, timedelta, timezone
from collections            import defaultdict
import Dal as dal
import os

P_GEN_PRE  = [0, 10,  8, 6, 4, 2, 1]
P_GEN_FIN  = [0, 11,  9, 7, 6, 4, 3]
P_G12_PRE  = [0, 11,  9, 7, 5, 3, 2]
P_G12_FIN  = [0, 12, 10, 8, 7, 5, 4]
P_SG_PRE   = [0, 12, 10, 8, 6, 4, 3]
P_SG_FIN   = [0, 13, 11, 9, 8, 6, 5]

BT_KEY = "ファン感謝３Ｄａｙｓボートレースバトルトーナメント"
# ====================================================================
class Query():
    def __init__(self, date_from, date_to, query1:bool=False, query2:bool=False,
                           grade:Optional[list] = None,
                       player_id:Optional[int]  = None,
                        venue_id:Optional[int]  = None,
                      all_ladies:Optional[int]  = None,
                      stabilizer:Optional[int]  = None,
                         weather:Optional[str]  = None,
                        wind_spd:Optional[int]  = None,
                        wind_dir:Optional[int]  = None,
                        wave_hgt:Optional[int]  = None,
                          course:Optional[int]  = None,
                     finish_rank:Optional[int]  = None,
                      fault_code:Optional[str]  = None,
                     fault_level:Optional[int]  = None,
                        slit_ADJ:Optional[int]  = None,
                      water_type:Optional[int]  = None,
                          flying:Optional[str]  = None,

                  exclude_rookie:list= [False, False]                   ):

        super().__init__()

        self.date_from      = date_from
        self.date_to        = date_to
        self.player_id      = player_id
        self.option         = {k:v for k, v in locals().items() if v is not None} or {}
        self.exclude_rookie = exclude_rookie

        self.parts = {   "player_id":(" AND e.player_id   = ?", lambda s:[player_id]),
                             "grade":(" AND r.grade IN (%s)" % ",".join("?"*len(grade))
                                                              if grade else None, grade ),
                          "wind_dir":(" AND r.wind_dir IN (%s)" % ",".join("?"*len(wind_dir))
                                                              if wind_dir else None, wind_dir ),
                        "water_type":(" AND v.water_type  = ?", lambda s:[water_type]),
                          "venue_id":(" AND r.venue_id    = ?", lambda s:[venue_id]),
                        "all_ladies":(" AND r.all_ladies  = ?", lambda s:[all_ladies]),
                        "stabilizer":(" AND r.stabilizer  = ?", lambda s:[stabilizer]),
                           "weather":(" AND r.weather     = ?", lambda s:[weather]),
                          "wind_spd":(" AND r.wind_spd   >= ?", lambda s:[wind_spd]),
                          "wave_hgt":(" AND r.wave_hgt   >= ?", lambda s:[wave_hgt]),
                            "course":(" AND e.course      = ?", lambda s:[course]),
                       "finish_rank":(" AND e.finish_rank = ?", lambda s:[finish_rank]),
                        "fault_code":(" AND e.fault_code  = ?", lambda s:[fault_code]),
                       "fault_level":(" AND e.fault_level = ?", lambda s:[fault_level]),
                          "slit_ADJ":(" AND e.slit_ADJ    = ?", lambda s:[slit_ADJ]),

                            "flying":("__DYN_FLYING__"        , None),                            }

        if query1: self.rows1 = self._query_results()
        if query2: self.rows2 = self._query_self_others()

    # ------------------------------------------------------
    def _pack( self,  by_grade:bool=False,
                     by_course:bool=False,
                     by_series:bool=False,
                     for_trend:bool=False,
                     for_index:bool=False,
                     for_graph:bool=False,
                for_distribute:bool=False   ):

        if   by_grade:
            out = self._packing_by_grade(self.rows1)
        elif by_course:
            out = self._packing_by_course(self.rows1)
        elif by_series:
            rows_by_series = self._packing_by_series(self.rows1)
            if   for_trend:
                out = self._repacking_trend(rows_by_series)
            elif for_index:
                out = self._repacking_index(rows_by_series)

        elif for_distribute:
            out = self._packing_distribute(self.rows2[1])
        elif for_graph:
            out = self._packing_graph(*self.rows2)

        return out

    # ------------------------------------------------------
    def _query_results(self):

        sql = """
            SELECT r.date,
                   r.series_title,
                   r.grade,
                   r.is_final,
                   e.frame_no,
                   e.course,
                   e.slit_adj,
                   e.finish_rank,
                   e.fault_code,
                   e.fault_level

              FROM Race_entries e
              JOIN Races r
                ON e.race_id  = r.race_id
              JOIN Venues v
                ON e.venue_id = v.venue_id
             WHERE e.date BETWEEN ? AND ?
               AND r.status  = 'held'
              """

        params  = [self.date_from, self.date_to]
        exec_r  = self.exclude_rookie[0]
        add_sql, add_param = self._build_filter_clause(exec_r)
        sql    += add_sql
        sql    += " ORDER BY e.date ASC, e.race_no ASC"
        params += add_param
        rows    = dal.fetch_all(sql, tuple(params)) or []

        return rows

    # ------------------------------------------------------
    def _query_self_others(self):

        sql_own1 = """
                  WITH base AS (  SELECT e.course,
                                         e.slit_adj,
                                         e.finish_rank,
                                         e.fault_code,
                                         e.fault_level
                                    FROM Race_entries e
                                    JOIN Races r
                                      ON e.race_id = r.race_id
                                    JOIN Venues v
                                      ON e.venue_id = v.venue_id
                                   WHERE e.date BETWEEN ? AND ?
                                     AND r.status       = 'held'
                                     AND e.finish_rank != 0
                                 AND NOT e.fault_code  IN ('F','L','K')
                                 AND NOT (     e.fault_code  = 'S'
                                           AND e.fault_level =  0 )
                   """
 
        sql_own2 = """
              ) SELECT course,
                 COUNT(*) AS starts,
                   SUM(CASE WHEN finish_rank = 1 THEN 1 ELSE 0 END) AS win1,
                   SUM(CASE WHEN finish_rank = 2 THEN 1 ELSE 0 END) AS win2,
                   SUM(CASE WHEN finish_rank = 3 THEN 1 ELSE 0 END) AS win3,
                   SUM(CASE WHEN finish_rank = 4 THEN 1 ELSE 0 END) AS win4,
                   SUM(CASE WHEN finish_rank = 5 THEN 1 ELSE 0 END) AS win5,
                   SUM(CASE WHEN finish_rank = 6 THEN 1 ELSE 0 END) AS win6,
                   SUM(slit_adj)                                    AS st_sum
                  FROM base
              GROUP BY course
                  """

        sql_othr1 = """
                   WITH my_races AS ( SELECT e.race_id,
                                             e.finish_rank,
                                             e.fault_code,
                                             e.fault_level
                                        FROM Race_entries e
                                        JOIN Races r
                                          ON e.race_id = r.race_id
                                        JOIN Venues v
                                          ON e.venue_id = v.venue_id
                                       WHERE e.date BETWEEN ? AND ?
                                         AND r.status       = 'held'
                                         AND e.finish_rank != 0
                                     AND NOT e.fault_code  IN ('F','L','K')
                                     AND NOT (     e.fault_code  = 'S'
                                               AND e.fault_level =  0 )
                   """

        sql_othr2 = """
               ) SELECT e.race_id,
                        e.player_id,
                        e.course,
                        e.finish_rank,
                        e.fault_code,
                        e.fault_level,
                        e.win_move
                   FROM Race_entries e
                   JOIN my_races mr
                     ON mr.race_id = e.race_id
                    """
        sql_othr3 = " ORDER BY e.race_id, e.course"

        add_sql, add_param = self._build_filter_clause(0)
        sql_own            = (sql_own1 + add_sql + sql_own2)

        rookie_sql, rookie_param = ("", [])
        if self.exclude_rookie[1]:
            rookie_sql, rookie_param = self._build_exclude_rookie_clause()

        sql_othr = sql_othr1 + add_sql + sql_othr2 + rookie_sql + sql_othr3

        params      = [self.date_from, self.date_to] + add_param
        params_othr = params + rookie_param

        rows1  = dal.fetch_all(sql_own, tuple(params))
        rows2  = dal.fetch_all(sql_othr, tuple(params_othr))

        return (rows1, rows2)

    # ------------------------------------------------------
    def _packing_by_grade(self, rows):  # 選手成績一覧

        out = { g:{   "starts":0,  "series":0,
                    "to_final":0, "victory":0,
                      "sc_ave":0,  "st_ave":0,
                         "F_L":0,     "S_K":0,
                          "r1":0, "r2":0, "r3":0,
                          "r4":0, "r5":0, "r6":0  } for g in ["ALL","SG","G1","G2","G0"] }

        cnt = { g:{ "sc_sum":0, "st_sum":0,
                    "sc_cnt":0, "st_cnt":0, "series":set() } for g in ["ALL","SG","G1","G2","G0"] }

        for _, s_title, grade, is_final, _, _, s_adj, rank, fcode, flevel in rows:

            if   grade ==    5 : targets = ["ALL", "SG"]
            elif grade in (4,3): targets = ["ALL", "G1"]
            elif grade ==    2 : targets = ["ALL", "G2"]
            elif grade in (1,0): targets = ["ALL", "G0"]

            for gr in targets:
                o = out[gr]
                c = cnt[gr]

                c["series"].add(s_title)
                o["starts"] += 1

                if s_adj and (fcode not in ('F', 'L')):
                    c["st_sum"] += s_adj
                    c["st_cnt"] += 1

                if flevel != 0 or rank != 0:
                    p = self._point_for(grade, is_final, rank, s_title)
                    c["sc_sum"] += p
                    c["sc_cnt"] += 1

                if fcode  in ('F','L')  : o["F_L"]      += 1
                if fcode  in ('S','K')  : o["S_K"]      += 1
                if rank in (1,2,3,4,5,6): o[f"r{rank}"] += 1
                if is_final:
                    o["to_final"] += 1
                    if rank == 1: o["victory"] += 1

        for c, o in zip(cnt.values(), out.values()):
            o["series"] = len(c["series"]) if c["series"] else 0

            if c["sc_cnt"] > 0: o["sc_ave"] = c["sc_sum"] / c["sc_cnt"]
            if c["st_cnt"] > 0: o["st_ave"] = c["st_sum"] / c["st_cnt"]

        return out

    # ------------------------------------------------------
    def _packing_by_course(self, rows):

        out = {c:{ "cnt":0, "st_ave":0, "sc_ave":0, "F_L":0,
                    "rate":{rnk:0 for rnk in range(1,7)}     } for c in range(0,7) }

        cnt = {c:{"st_sum":0, "st_cnt":0,
                       "rate":{rnk:0 for rnk in range(1,7)} } for c in range(0,7) }

        sc_sum, sc_cnt = 0, 0

        for _, s_title, grade, is_final, _, course, s_adj, rank, f_code, f_level in rows:

            if f_level != 0 and rank != 0:
                p = self._point_for(grade, is_final, rank, s_title)
                sc_cnt += 1
                sc_sum += p

            if course and f_code in ["F", "L"]: out[course]["F_L"] += 1
            if f_code in ["F", "L", "K"]: continue

            out[course]["cnt"]    += 1
            cnt[course]["st_sum"] += s_adj if s_adj else 0
            cnt[course]["st_cnt"] += 1
            out[0]["cnt"]         += 1
            cnt[0]["st_sum"]      += s_adj if s_adj else 0
            cnt[0]["st_cnt"]      += 1

            if rank in range(1,7):
                cnt[course]["rate"][rank] += 1

        out[0]["sc_ave"] = f"{(sc_sum / sc_cnt):.2f}" if sc_cnt else ""

        for c in range(0,7):
            out[c]["st_ave"] = f"{(cnt[c]['st_sum'] / cnt[c]['st_cnt']):.2f}" if cnt[c]['st_cnt'] else ""
            for r in range(1,7):
                out[c]["rate"][r] = (cnt[c]["rate"][r] / out[c]["cnt"]) if cnt[c]["rate"][r] else 0.0

        return dict(out)

    # ------------------------------------------------------
    def _packing_by_series(self, rows):

        out = {}
        for _date, s_title, grade, is_final, frno, cour, s_adj, rank, fcode, flevel in rows:

            year = dt.fromisoformat(_date).year

            if year not in out: out[year] = {}
            if s_title not in out[year]:
                out[year][s_title] = { "start":_date, "end":_date, "title":s_title, "grade":grade,
                                       "results":[], "slots":[], "d_pack":{},                     }

            if _date < out[year][s_title]["start"]: out[year][s_title]["start"] = _date
            if _date > out[year][s_title]["end"]:   out[year][s_title]["end"]   = _date

            out[year][s_title]["results"].append([grade, is_final, s_adj, rank, fcode, flevel])

            if _date not in out[year][s_title]["d_pack"]: out[year][s_title]["d_pack"][_date] = []

            out[year][s_title]["d_pack"][_date].append({ "date":_date,
                                                       "is_fnl":is_final,
                                                       "fr_no" :frno,
                                                       "cour"  :cour if cour  else "",
                                                       "s_adj" :float(abs(s_adj)) if s_adj else "",
                                                       "finish":rank if rank else fcode } )

        return out

    # ------------------------------------------------------
    def _repacking_index(self, rows):

        out = {}
        for year in rows.values():
            for seri in year.keys():
                for day in year[seri]["d_pack"].keys(): 
                    for items in year[seri]["d_pack"][day]:
                        year[seri]['slots'].append(items)
                        if len(year[seri]["d_pack"][day]) == 1:
                            year[seri]["slots"].append( { "date":"", "is_fnl":0, "fr_no":0,
                                                          "cour":"", "s_adj":"", "finish":"" } )

                while len(year[seri]["slots"]) < 14:
                    year[seri]["slots"].append( { "date":"", "is_fnl":0, "fr_no":0,
                                                  "cour":"", "s_adj":"", "finish":"" } )
 
                year[seri].pop("d_pack", None)

        return rows

    # ------------------------------------------------------
    def _repacking_trend(self, rows):

        sc_cumltv_cnt = 0
        st_cumltv_cnt = 0
        sc_cumltv_sum = 0
        st_cumltv_sum = 0
        out           = []

        for idx, year in enumerate(rows.values()):
            for seri in year.keys():
                sc_single_cnt = 0
                st_single_cnt = 0
                sc_single_sum = 0
                st_single_sum = 0
                has_F         = False

                for grade, is_final, s_adj, rank, fcode, flevel in year[seri]["results"]:

                    gr = grade
                    if fcode == 'F': has_F = True

                    if flevel != 0 and rank != 0:
                        pts            = self._point_for(grade, is_final, rank, seri)
                        sc_single_cnt += 1
                        sc_single_sum += pts

                    if s_adj and (fcode not in ('F', 'L', 'K')):
                        st_single_cnt += 1
                        st_single_sum += s_adj

                sc_cumltv_cnt += sc_single_cnt ;sc_cumltv_sum += sc_single_sum
                st_cumltv_cnt += st_single_cnt ;st_cumltv_sum += st_single_sum

                sr_single = (sc_single_sum / sc_single_cnt) if sc_single_cnt > 0 else 0
                sr_cumltv = (sc_cumltv_sum / sc_cumltv_cnt) if sc_cumltv_cnt > 0 else 0
                st_single = (st_single_sum / st_single_cnt) if st_single_cnt > 0 else None
                st_cumltv = (st_cumltv_sum / st_cumltv_cnt) if st_cumltv_cnt > 0 else None

                out.append( { "sr_cumltv": sr_cumltv,  "sr_single": sr_single,
                              "st_cumltv": st_cumltv,  "st_single": st_single,
                                  "label": str(idx),       "has_F": has_F,      
                                  "grade": gr                                  } )

        return out

    # ------------------------------------------------------
    def _packing_distribute(self, rows):

        own_cnt  = {c:{rnk:0 for rnk in range(1,7)} for c in range(1,7)}
        oth_cnt  = {mc:{oc:{rnk:0 for rnk in range(1,7)}
                              for oc in range(1,7)} for mc in range(1,7)}
        oth_by_r = {mc:{mrk:{oc:{rnk:0 for rnk in range(1,7)} 
                              for oc in range(1,7)} for mrk in range(1,7)} for mc in range(1,7)}
        win_move = defaultdict(lambda:{c:defaultdict(int) for c in range(1,7)})
        subj_wm  = {sc:{sr:{c:{} for c in range(1,7)} for sr in range(1,7)} for sc in range(1,7)}
        starts   = {c:0 for c in range(1,7)} 

        by_race  = defaultdict(list)

        for r in rows:
            rid = r["race_id"]
            by_race[rid].append(r)

        for rid, entries in by_race.items():
            subj = None
            for ent in entries:
                if ent["player_id"] == self.player_id:
                    subj = ent
                    break
            if subj is None: continue

            subj_c = subj["course"]      or 0
            subj_r = subj["finish_rank"] or 0

            if subj_c not in range(1,7): continue
            if subj_r not in range(1,7): continue

            starts[subj_c]          += 1
            own_cnt[subj_c][subj_r] += 1

            for ent in entries:
                if ent["finish_rank"] == 1:
                    c  = ent["course"] or 0
                    wm = ent["win_move"]
                    if c in range(1, 7) and wm not in (None, ""):
                        win_move[subj_c][c][wm] += 1
                        subj_wm[subj_c][subj_r][c][wm] = subj_wm[subj_c][subj_r][c].get(wm, 0) +1
                    break

            for ent in entries:
                cou = ent["course"]      or 0
                rk  = ent["finish_rank"] or 0

                if cou not in range(1, 7): continue
                if rk  not in range(1, 7): continue
                if cou ==     subj_c:      continue

                oth_cnt[subj_c][cou][rk]          += 1
                oth_by_r[subj_c][subj_r][cou][rk] += 1

        return {  "own_cnt": dict(own_cnt),
                  "oth_cnt": dict(oth_cnt),
                 "oth_by_r": dict(oth_by_r),
                 "win_move": dict(win_move),
                  "subj_wm": dict(subj_wm),
                  "starts": dict(starts),    }

    # ------------------------------------------------------
    def _packing_graph(self, rows1, rows2):

        own = {c:{   "rate":{rnk:0 for rnk in range(1,4)},
                   "st_ave":None,
                   "starts":0,                             } for c in range(0,7)}
        oth = {mc:{oc:{rnk:0 for rnk in range(1,4)} for oc in range(1,7)} for mc in range(1, 7)}
        cnt = {mc:{oc:{rnk:0 for rnk in range(1,4)} for oc in range(1,7)} for mc in range(1, 7)}
        cnt_st = {mc:{oc:0  for oc in range(1,7)} for mc in range(1,7)}

        for r in rows1:
            c  = r["course"] or 0
            s  = r["starts"] or 0
            st = r["st_sum"] or 0

            own[c]["rate"][1] = (r["win1"] / s) if s else 0.0 ; own[0]["rate"][1] += r["win1"]
            own[c]["rate"][2] = (r["win2"] / s) if s else 0.0 ; own[0]["rate"][2] += r["win2"]
            own[c]["rate"][3] = (r["win3"] / s) if s else 0.0 ; own[0]["rate"][3] += r["win3"]
            own[c]["starts"]  = s                             ; own[0]["starts"]  += s
            own[c]["st_ave"]  = (st        / s) if s else None

        own[0]["rate"][1] = own[0]["rate"][1] / own[0]["starts"] *100 if own[0]["rate"][1] else 0
        own[0]["rate"][2] = own[0]["rate"][2] / own[0]["starts"] *100 if own[0]["rate"][2] else 0
        own[0]["rate"][3] = own[0]["rate"][3] / own[0]["starts"] *100 if own[0]["rate"][3] else 0

        races = defaultdict(list)
        for rec in rows2:
            r_id = rec["race_id"]
            races[r_id].append(rec)

        for lst in races.values():
            mc = None
            for p in lst:
                if p["player_id"] == self.player_id:
                    mc = p["course"]
                    break
            if not mc or not (1 <= mc <= 6): continue

            for p in lst:
                if p["player_id"] == self.player_id: continue

                rank = p["finish_rank"]
                oc   = p["course"]
                if rank is None: continue

                cnt_st[mc][oc] += 1
                if rank == 1: cnt[mc][oc][1] += 1
                if rank == 2: cnt[mc][oc][2] += 1
                if rank == 3: cnt[mc][oc][3] += 1

        for mc in range(1,7):
            for oc in range(1,7):
                if mc == oc: continue
                s = cnt_st[mc][oc]

                oth[mc][oc][1] = (cnt[mc][oc][1] / s) if s else 0.0
                oth[mc][oc][2] = (cnt[mc][oc][2] / s) if s else 0.0
                oth[mc][oc][3] = (cnt[mc][oc][3] / s) if s else 0.0

        return {"own":dict(own), "oth":dict(oth)}

    # --------------- ｵﾌﾟｼｮﾝSQL, params作成 ----------------
    def _build_filter_clause(self, exclude_rookie):

        sql, params = [], []

        for key in self.option.keys():
            if key == "flying":
                parts, param = self._build_flying_clause()
                if parts:
                    sql.append(parts)
                    params.extend(param)
                continue

            tpl = self.parts.get(key)
            if not tpl: continue
            parts, param = tpl
            sql.append(parts)

            if   callable(param):                  params.extend(param(self))
            elif isinstance(param, (list, tuple)): params.extend(param)
            elif param is not None:                params.append(param)

        if self.exclude_rookie and exclude_rookie:
            frag, prm = self._build_exclude_rookie_clause()
            sql.append(frag)
            params.extend(prm)

        return "".join(sql), params

    # ----------------- ﾌﾗｲﾝｸﾞﾌｨﾙﾀSQL作成 ------------------
    def _build_flying_clause(self):

        rows = dal.fetch_all(
            """
            SELECT date
              FROM Race_entries
             WHERE player_id  = ?
               AND fault_code ='F'
               AND date BETWEEN ? AND ?
            """,
            (self.player_id, self.date_from, self.date_to) ) or []

        wins = []
        for (d_str,) in rows:
            f_date           = self._to_date(d_str)
            _start, term_end = self._calc_term_bounds_for_date(f_date)
            start            = max(  f_date, self._to_date(self.date_from))
            end              = min(term_end, self._to_date(self.date_to  ))
            if start <= end: wins.append((start, end))

        if not wins: return " AND 1=0", []
        wins.sort(key=lambda x: x[0])

        merged = []
        for start, end in wins:
            if not merged or start > merged[-1][1]: merged.append([start, end])
            else:                                   merged[-1][1] = max(merged[-1][1], end)

        frag   = " AND (" +" OR ".join(["(r.date BETWEEN ? AND ?)"] *len(merged)) +")"
        params = []
        for start, end in merged: params.extend([start.isoformat(), end.isoformat()])

        return frag, params
    # --------------------------------------------
    def _build_exclude_rookie_clause(self):

        frag = """
            AND e.player_id IN
            ( SELECT p.player_id
                FROM Players p
               WHERE julianday(?) - julianday(
                         date('1957-11-01', '+' || ((p.regist_period - 1) * 6) || ' months')
                              ) >= 365 )
               """
        return frag, [self.date_to]
    # --------------------------------------------
    def _calc_term_bounds_for_date(self, d:date):

        y, m = d.year, d.month
        if 5 <= m <= 10: return (date(y, 5, 1), date(y,10,31))
        if      m >= 11: return (date(y,11, 1), date(y+1,4,30))

        return (date(y-1,11, 1), date(y, 4,30))
    # --------------------------------------------
    def _to_date(self, x) -> date:

        if isinstance(x, date): return x
        if isinstance(x,  str): return date.fromisoformat(x)

        raise ValueError("date conv error")
    # --------------------------------------------
    def _point_for(self, grade:int|None, final:int|None, rank:int|None, s_name:str):

        if s_name.strip() in BT_KEY: tbl = P_G12_FIN if final else P_G12_PRE
        elif grade in (2, 3, 4):     tbl = P_G12_FIN if final else P_G12_PRE
        elif grade ==  5:            tbl = P_SG_FIN  if final else  P_SG_PRE
        else:                        tbl = P_GEN_FIN if final else P_GEN_PRE

        return tbl[rank or 0]
