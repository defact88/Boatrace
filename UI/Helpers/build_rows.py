# -*- coding: utf-8 -*-
# "C:\boatrace\UI\Helpers\build_row.py

from __future__      import annotations
from Helpers.queries import Query
from datetime        import datetime as dt, date, timedelta
import Dal as dal

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

#================== entry:make_rows ============================
def make_rows(self):

    date_to    = to_str(self.date_to)
    date_from  = to_str(self.date_from)
    lineup     = query_players(self.date, self.venue_id, self.race_no)
    date_frm_v = self.date -timedelta(days=int(self.range_v))
    entry_rows = [None] *7
    data_rows  = [None] *7

    for row in lineup:
        frn       = row["frame_no"]
        pid       = row["player_id"]
        query_opt = {}

        if row['flying_st'] or row['late_st']:
            if self.flying:
                query_opt = dict(flying=True)
                date_from = self.date_to -timedelta(days=730)  
        elif self.not_flying:
            query_opt |= dict(not_flying=True)
        if self.exclude_edo:
            query_opt |= dict(exclude_venue=3)
        if self.limited_grade:
            query_opt |= dict(grade=[5, 4, 3, 2])

        query    = Query( date_from, date_to,  query_results=True, query_self_others=True,
                          player_id=pid, **query_opt                                       )
        query_v  = Query( date_frm_v, date_to, query_results=True,
                          player_id=pid, venue_id=self.venue_id        )
        ave      = query._pack(by_course=True)
        rate     = query._pack(for_graph=True)
        dist     = query._pack(for_distribute=True)
        v_ave    = query_v._pack(by_course=True)
        own_rate = rate["own"][0]["rate"]

        entry_rows[frn] = { "frno":row["frame_no"],
                             "pid":row["player_id"],
                            "name":row["name"],
                            "rgns":row["regions"],
                             "age":f"{row['age']} 歳",
                            "clss":row["class_now"],
                            "regp":f"{row['regist_period']} 期",
                            "flyg":row['flying_st'],
                            "late":row['late_st'],
                            "heig":f"{row['heig']}cm",
                             "wkg":f"{row['weight_tdy']}kg",
                           "mo_no":row["motor_no"],
                           "bo_no":row["boat_no"],
                           "mo_av":f"{row["motor_ave"]:.1f}",
                           "bo_av":f"{row["boat_ave"]:.1f}",
                            "scav":ave[0]["sc_ave"],
                            "stav":ave[0]["st_ave"],
                             "cnt":{c:ave[c]["cnt"] for c in range(1,7)},
                           "v_ave":v_ave[0]["sc_ave"],
                           "v_cnt":v_ave[0]["cnt"],
                            "absn":row["absn"], 
                           "rate1":own_rate[1],
                           "rate2":own_rate[1]+own_rate[2],
                           "rate3":own_rate[1]+own_rate[2]+own_rate[3],   }

        data_rows[frn] = {   "own":rate["own"],
                             "oth":rate["oth"],
                             "all":None,
                            "absn":row["absn"],
                         "own_cnt":dist["own_cnt"],
                         "oth_cnt":dist["oth_cnt"],
                        "oth_by_r":dist["oth_by_r"],
                        "win_move":dist["win_move"],
                         "subj_wm":dist["subj_wm"],
                          "starts":dist["starts"],    }

    return entry_rows, data_rows

# ====================================================================
def make_sub_rows(self):

    prg  = self.entry_prg
    rows = {"befr":{}, "rslt":{},}

    for frn in range(1, 7):

        befr  = query_before_info(frn, self.date, self.venue_id, self.race_no)
        rslt  = query_result(     frn, self.date, self.venue_id, self.race_no)
        repr  = [s.strip() for s in (befr["repr"] or "").split(",") if s]
        d_cou = 6 if befr["absn"] and not bef["cour"] else befr["cour"] or frn
        tilt  = befr["tilt"] if befr["tilt"] != 0 else "0"
        exhi  = f"{befr['exhi']:.2f}" if befr["exhi"] else ""
        adj_d = befr["s_adj"]
        adj_r = rslt["s_adj"]
        r_cou = 6 if rslt["f_code"] == "K" else rslt["cour"]
        if not rslt["f_rank"]:
            fin = rslt["f_code"] if rslt["f_code"] else ""
        else: 
            fin = rslt["f_rank"]

        rows["befr"][frn] = {   "cour":d_cou,
                                "exhi":exhi,
                               "s_adj":adj_d,
                                "tilt":tilt if tilt else "",
                                "repr":repr,
                                "absn":befr["absn"],         }

        rows["rslt"][frn] = {   "cour":r_cou,
                              "finish":fin,
                              "f_code":rslt["f_code"],
                               "s_adj":adj_r,
                              "w_move":rslt["w_move"],
                                "absn":befr["absn"],         }

        if frn == 1:
            rows["befr"][0] = { "wdir":befr["wdir"],
                                "wthr":befr["wthr"],
                                "wspd":befr["wspd"] or "",
                                "wave":befr["wave"] or "",
                                "stab":befr["stab"] or "",
                                "shlp":befr["shlp"] or "",   }

            rows["rslt"][0] = { "wdir":rslt["wdir"],
                                "wthr":rslt["wthr"],
                                "wspd":rslt["wspd"] or "",
                                "wave":rslt["wave"] or "",   }

    return rows

# ======================== Headerﾃﾞｰﾀ取得 ============================
def query_program(self):

    row = dal.fetch_one( 
        """
        SELECT rp.date,
               rp.venue_id,
               v.venue_name  AS vname,
               v.upd_motor   AS upd_m,
               v.upd_boat    AS upd_b,
               v.water_type  AS w_typ,
               v.home_region AS h_reg,
               rp.series_title,
               rp.day_no,
               rp.race_no,
               rp.race_title,
               rp.grade,
               rp.deadline_vote AS deadline

          FROM Race_programs rp
          JOIN Venues v ON v.venue_id = rp.venue_id
         WHERE rp.date     =? 
           AND rp.venue_id =? 
           AND rp.race_no  =?
         LIMIT 1
        """,
       (to_str(self.date), self.venue_id, self.race_no))

    row = { k:(dt.fromisoformat(row[k]) if k == 'deadline' and row[k] else row[k]) 
            for k in row.keys() } if row else {}

    return row

# ======================= 選手基本ﾃﾞｰﾀ取得 ===========================
def query_players(_date:date, venue_id:int, race_no:int):

    sql = """
        SELECT rp.frame_no,
               rp.player_id,

               p.name          AS name,
               p.regions       AS regions,
               p.age           AS age,
               p.height        AS heig,
               p.class_now     AS class_now,
               p.regist_period AS regist_period,
               p.flying_st     AS flying_st,
               p.late_st       AS late_st,
   
               rp.weight_tdy   AS weight_tdy,
               rp.motor_no     AS motor_no,
               rp.motor_ave    AS motor_ave,
               rp.boat_no      AS boat_no,
               rp.boat_ave     AS boat_ave,
               rp.is_absent    AS absn

          FROM Race_programs rp
    INNER JOIN Players p ON p.player_id = rp.player_id
         WHERE rp.date     =?
           AND rp.venue_id =? 
           AND rp.race_no  =?
      ORDER BY rp.frame_no
         """
    return dal.fetch_all(sql, (to_str(_date), venue_id, race_no))

# ======================== 展示ﾃﾞｰﾀ取得 ==============================
def query_before_info(fr_no:int, _date:date, venue_id:int, race_no:int):

    cur = dal._cursor()
    row = cur.execute(
        """
        SELECT weather     AS wthr,
               wind_dir    AS wdir,
               wind_spd    AS wspd,
               wave_hgt    AS wave,
               player_id   AS pid,
               is_absent   AS absn,
               course      AS cour,
               exhibition  AS exhi,
               slit_ADJ    AS s_adj,
               tilt        AS tilt,
               rep_parts   AS repr,
               lap_reduct  AS shlp,
               stabilizer  AS stab

          FROM Before_info
         WHERE date     =?
           AND venue_id =?
           AND frame_no =?
           AND race_no  =?
      ORDER BY frame_no
         LIMIT 1
        """,
        (to_str(_date), venue_id, fr_no, race_no) ).fetchone()

    row = dict(row) if row else dict.fromkeys([d[0] for d in cur.description]) 

    return row

# ====================================================================
def query_result(fn:int, d:date, v:int, r:int):

    cur = dal._cursor()
    row = cur.execute("""
        SELECT r.weather      AS wthr,
               r.wind_dir     AS wdir,
               r.wind_spd     AS wspd,
               r.wave_hgt     AS wave,

               e.frame_no    AS frame_no,
               e.course      AS cour,
               e.finish_rank AS f_rank,
               e.fault_code  AS f_code,
               e.slit_ADJ    AS s_adj,
               e.win_move    AS w_move

          FROM Race_entries e
          JOIN Races r ON e.race_id = r.race_id
         WHERE     e.date = ?
           AND e.venue_id = ?
           AND  e.race_no = ?
           AND e.frame_no = ?
      ORDER BY frame_no
        """,
        (to_str(d), v, r, fn) ).fetchone()

    row = dict(row) if row else dict.fromkeys([d[0] for d in cur.description])

    return row
# --------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
