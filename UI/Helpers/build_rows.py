# -*- coding: utf-8 -*-
# "C:\boatrace\UI\Helpers\build_row.py

from __future__      import annotations
from Helpers.queries import Query
from datetime        import datetime as dt, date, timedelta
import Dal as dal

#================== entry:make_rows ============================
def make_rows(self):

    lineup        = query_players(self.date, self.venue_id, self.race_no)
    date_to       = date.fromisoformat(self.date)
    date_frm      = date_to -timedelta(days=int(self.range_d))
    date_frm_v    = date_to -timedelta(days=int(self.range_v))
    entry_rows    = [None] * 7
    data_rows     = [None] * 7

    for row in lineup:
        frn    = row["frame_no"]
        pid    = row["player_id"]
        query1 = Query(date_frm, date_to, query1=True, query2=True, player_id=pid)
        ave    = query1._pack(by_course=True)
        rate   = query1._pack(for_graph=True)
        RATE   = rate["own"][0]["rate"]
        dist   = query1._pack(for_distribute=True)
        query2 = Query(date_frm_v, date_to, query1=True, player_id=pid, venue_id=self.venue_id)
        v_ave  = query2._pack(by_course=True)

        entry_rows[frn] = { "frno": row["frame_no"],
                             "pid": row["player_id"],
                            "name": row["name"],
                            "rgns": row["regions"],
                             "age": f"{row['age']} 歳",
                            "clss": row["class_now"],
                            "regp": f"{row['regist_period']} 期",
                            "flyg": row['flying_st'],
                            "late": row['late_st'],
                            "heig": f"{row['heig']}cm",
                             "wkg": f"{row['weight_tdy']}kg",
                           "mo_no": row["motor_no"],
                           "bo_no": row["boat_no"],
                           "mo_av": f"{row["motor_ave"]:.1f}",
                           "bo_av": f"{row["boat_ave"]:.1f}",
                            "scav": ave[0]["sc_ave"],
                            "stav": ave[0]["st_ave"],
                             "cnt": {c:ave[c]["cnt"] for c in range(1,7)},
                           "v_ave": v_ave[0]["sc_ave"],
                           "v_cnt": v_ave[0]["cnt"],
                            "absn": row["absn"], 
                           "rate1": RATE[1],
                           "rate2": RATE[1]+RATE[2],
                           "rate3": RATE[1]+RATE[2]+RATE[3],                }

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
    rows = {"dspl":{}, "rslt":{},}

    for frn in range(1, 7):

        disp  = query_display_run(frn, self.date, self.venue_id, self.race_no)
        rslt  = query_result(frn, self.date, self.venue_id, self.race_no)
        rpr   = disp.get("repr", "") if disp.get('repr') else  ""
        parts = ([s.strip() for s in rpr.split(",") if s] + [""] * 9)[:9]
        d_cou = 6 if disp.get("absn", None) and not disp.get("cour", frn) else disp.get("cour", frn) or frn
        tilt  = disp.get('tilt') if disp.get('tilt') != 0 else "0"
        exhi  = f"{ disp.get('exhi'):.2f}" if disp.get('exhi') else ""
        adj_d = disp.get('s_adj', None)
        adj_r = rslt.get('s_adj', None)
        r_cou = 6 if rslt.get("f_code", "") == "K" else rslt.get("cour", frn)
        if not rslt.get("f_rank", None):
            fin = rslt.get("f_code", None) if rslt.get("f_code", None) else ""
        else: fin = rslt.get("f_rank")

        rows["dspl"][frn] = { "cour":d_cou,
                              "exhi":exhi,
                             "s_adj":adj_d,
                              "tilt":tilt if tilt else "" ,
                              "rpr1":"  ".join(parts[2:5]),
                              "rpr2":"  ".join(parts[0:2]),
                              "rpr3":"  ".join(parts[5:9]),
                              "absn":disp.get("absn", None) }

        rows["rslt"][frn] = {   "cour":r_cou,
                              "finish":fin,
                              "f_code":rslt.get("f_code", None),
                               "s_adj":adj_r,
                              "w_move":rslt.get("w_move", None),
                                "absn":disp.get("absn",   None)  }

        if frn == 1:
            rows["dspl"][0] = { "wdir":disp.get("wdir",  None),
                                "wthr":disp.get("wthr",  None),
                                "wspd":disp.get("wspd",  ""  ),
                                "wave":disp.get("wave",  ""  ),
                                "stab":disp.get("stab",  ""  ),
                                "shlp":disp.get("shlp",  ""  )  }

            rows["rslt"][0] = { "wdir":rslt.get("wdir", None),
                                "wthr":rslt.get("wthr", None),
                                "wspd":rslt.get("wspd", ""  ),
                                "wave":rslt.get("wave", ""  )  }

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
        """,  (self.date, self.venue_id, self.race_no))

    row = { k: (dt.fromisoformat(row[k]) if k == 'deadline' and row[k] else row[k]) 
            for k in row.keys() } if row else {}

    return row
# ======================= 選手基本ﾃﾞｰﾀ取得 ===========================
def query_players(date: str, venue_id: int, race_no: int):

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
    return dal.fetch_all(sql, (date, venue_id, race_no))

# ======================== 展示ﾃﾞｰﾀ取得 ==============================
def query_display_run(fr_no:int, date:str, venue_id:int, race_no:int):

    row = dal.fetch_one(
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

          FROM Display_run
         WHERE date     =?
           AND venue_id =?
           AND frame_no =?
           AND race_no  =?
      ORDER BY frame_no
         LIMIT 1
        """,
        (date, venue_id, fr_no, race_no) )

    row = {k:row[k] for k in row.keys()} if row else {}

    return row

# ====================================================================
def query_result(fn:int, d:date, v:int, r:int):

    row1 = dal.fetch_one(
        """
        SELECT weather      AS wthr,
               wind_dir     AS wdir,
               wind_spd     AS wspd,
               wave_hgt     AS wave
          FROM Races
         WHERE     date= ?
           AND venue_id= ?
           AND  race_no= ?
        """,
        (d, v, r)                    )

    row2 = dal.fetch_one(
        """
        SELECT frame_no    AS frame_no,
               course      AS cour,
               finish_rank AS f_rank,
               fault_code  AS f_code,
               slit_ADJ    AS s_adj,
               win_move    AS w_move
          FROM Race_entries
         WHERE      date= ?
           AND venue_id = ?
           AND   race_no= ?
           AND  frame_no= ?
      ORDER BY frame_no
        """,
        (d, v, r, fn)                    )

    row1 = {k: row1[k] for k in row1.keys()} if row1 else {}
    row2 = {k: row2[k] for k in row2.keys()} if row2 else {}
    row1.update(row2) 

    return row1
# --------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
