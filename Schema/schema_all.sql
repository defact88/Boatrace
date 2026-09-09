
/*-------------------------------------------------------------------------------------*/
CREATE TABLE Players(

  player_id     INTEGER PRIMARY KEY,
  name          TEXT    NOT NULL,
  name_kana     TEXT    NOT NULL,
  sex           TEXT    NOT NULL,
  age           INTEGER,
  regist_period INTEGER NOT NULL,
  regions       TEXT,
  height        INTEGER NOT NULL,
  weight        INTEGER NOT NULL,
  blood_type    TEXT    NOT NULL,
  birthday      DATE    NOT NULL,
  birthplace    TEXT,
  flying_st     INTEGER NOT NULL DEFAULT 0,
  late_st       INTEGER NOT NULL DEFAULT 0,
  class_now     TEXT,
  penalty_now   TEXT,
  penalty_hist  TEXT,
  comment       TEXT,

  CHECK(sex IN ('男','女'))
);

CREATE INDEX IF NOT EXISTS idx_Players_1
                        ON Players(player_id, name, age, regions, flying_st, late_st, class_now);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Season_result(

  player_id      INTEGER NOT NULL REFERENCES Players(player_id),
  year           INTEGER NOT NULL,
  season         INTEGER NOT NULL,
  class_in       TEXT    NOT NULL,
  score_ave      INTEGER,
  top2_ave       INTEGER,
  ST_ave         INTEGER,
  overall_rating INTEGER,

  PRIMARY KEY(player_id, year, season),

  CHECK(season IN (1,2))
);

CREATE INDEX IF NOT EXISTS idx_season_result_search 
                        ON Season_result(year, season, player_id);
/*-------------------------------------------------------------------------------------*/
CREATE TABLE Venues(

  venue_id        INTEGER PRIMARY KEY,
  venue_name      TEXT    NOT NULL,
  upd_motor       INTEGER NOT NULL,
  upd_boat        INTEGER NOT NULL,
  home_region     TEXT    NOT NULL,
  water_type      TEXT,
  direction       TEXT
);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Races(

  race_id      INTEGER PRIMARY KEY,
  date         DATE    NOT NULL,
  venue_id     INTEGER NOT NULL REFERENCES Venues(venue_id),
  series_title TEXT    NOT NULL,
  grade        INTEGER,
  day_no       INTEGER NOT NULL,
  race_no      INTEGER NOT NULL,
  race_title   TEXT,
  is_prefinal  INTEGER DEFAULT 0,
  is_final     INTEGER DEFAULT 0,
  all_ladies   INTEGER DEFAULT 0,
  distance     INTEGER,
  stabilizer   INTEGER NOT NULL DEFAULT 0,
  weather      TEXT,
  wind_dir     TEXT,
  wind_spd     INTEGER,
  wave_hgt     INTEGER,
  status       TEXT    NOT NULL DEFAULT 'held',

  CHECK(race_no BETWEEN 1 AND 12)
);

CREATE INDEX IF NOT EXISTS idx_races_1
                        ON Races(date, venue_id, grade, series_title, status, is_final);

CREATE INDEX IF NOT EXISTS idx_races_venue_date_status
                        ON Races(venue_id, date, status, is_final);

CREATE INDEX IF NOT EXISTS idx_races_race_id ON Races(race_id);

CREATE INDEX IF NOT EXISTS idx_races_date_status ON Races(date, status, is_final);

/*------------------------------------------------------------------------------------*/
CREATE TABLE Race_entries(

  race_id     INTEGER NOT NULL REFERENCES Races(race_id),
  entry_id    INTEGER PRIMARY KEY,
  race_no     INTEGER NOT NULL,
  venue_id    INTEGER NOT NULL REFERENCES Venues(venue_id),
  date        DATE    NOT NULL,
  frame_no    INTEGER NOT NULL,
  player_id   INTEGER NOT NULL REFERENCES Players(player_id),
  course      INTEGER,
  win_move    TEXT, 
  finish_rank INTEGER,
  fault_code  TEXT    NOT NULL DEFAULT 'N',
  fault_level INTEGER,
  motor_no    INTEGER NOT NULL,
  boat_no     INTEGER NOT NULL,
  slit_ADJ    INTEGER,
  race_time   TEXT,
  violation   TEXT NOT NULL DEFAULT 0,

  CHECK(frame_no    BETWEEN 1 AND 6),
  CHECK(fault_code  IN ('N','F','L','S','K')),
  CHECK(fault_level IN (0,1,2)),
  CHECK(violation   IN ('0','T','R','TR'))
);

CREATE INDEX IF NOT EXISTS idx_entries_1
                        ON Race_entries( date,       frame_no,    player_id,  finish_rank,
                                         fault_code, fault_level, course,     slit_ADJ,
                                         win_move,   venue_id,    race_id                  );

CREATE INDEX IF NOT EXISTS idx_entries_pid_date
                        ON Race_entries(player_id, date, race_id);

CREATE INDEX IF NOT EXISTS idx_entries_race_id ON Race_entries(race_id);

CREATE INDEX IF NOT EXISTS idx_entries_performance 
                        ON Race_entries(player_id, finish_rank, fault_code);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Race_programs(

  program_id    INTEGER  PRIMARY KEY,
  date          DATE     NOT NULL,
  venue_id      INTEGER  NOT NULL,
  held_type     INTEGER,
  series_title  TEXT     NOT NULL,
  grade         INTEGER,
  day_no        INTEGER  NOT NULL,
  race_no       INTEGER  NOT NULL,
  race_title    TEXT     NOT NULL,
  all_ladies    INTEGER           DEFAULT 0,
  deadline_vote DATETIME NOT NULL,

  frame_no      INTEGER  NOT NULL,
  player_id     INTEGER  NOT NULL REFERENCES Players(player_id),
  weight_tdy    REAL     NOT NULL,
  motor_no      INTEGER  NOT NULL,
  boat_no       INTEGER  NOT NULL,
  motor_ave     REAL     NOT NULL,
  boat_ave      REAL     NOT NULL,
  is_absent     INTEGER  NOT NULL DEFAULT 0,

  UNIQUE(program_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_programs_1 
                        ON Race_programs( date, frame_no, player_id, venue_id,
                                          day_no, race_no, series_title        );
CREATE INDEX IF NOT EXISTS idx_programs_venue_series_date
                        ON Race_programs (venue_id, series_title, date);
CREATE INDEX IF NOT EXISTS idx_programs_date_venue_pid
                        ON Race_programs (date, venue_id, player_id, race_no);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Display_run(

  race_id     INTEGER,
  entry_id    INTEGER PRIMARY KEY,
  venue_id    INTEGER NOT NULL REFERENCES Venues(venue_id),
  date        DATE    NOT NULL,
  race_no     INTEGER NOT NULL,
  lap_reduct  INTEGER NOT NULL DEFAULT 0,
  stabilizer  INTEGER NOT NULL DEFAULT 0,
  weather     TEXT,
  wind_dir    TEXT,
  wind_spd    INTEGER,
  wave_hgt    INTEGER,

  player_id   INTEGER NOT NULL REFERENCES Players(player_id),
  frame_no    INTEGER NOT NULL,
  is_absent   INTEGER NOT NULL DEFAULT 0,
  course      INTEGER,

  exhibition  REAL,
  slit_ADJ    REAL,
  tilt        REAL,
  rep_parts   TEXT,

  CHECK(frame_no BETWEEN 1 AND 6),
  CHECK(course   BETWEEN 1 AND 6)
);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Odds_snapshots(

  snapshot_id  INTEGER PRIMARY KEY AUTOINCREMENT,

  race_id      INTEGER NOT NULL,
  date         DATE    NOT NULL,
  venue_id     INTEGER NOT NULL,
  race_no      INTEGER NOT NULL,

  bet_type     TEXT    NOT NULL,
  boat1        INTEGER NOT NULL,
  boat2        INTEGER,
  boat3        INTEGER,

  odds         REAL,
  raw_odds     TEXT,
  is_absent    INTEGER NOT NULL DEFAULT 0,

  captured_at  DATETIME NOT NULL,
  is_final     INTEGER NOT NULL DEFAULT 0,

  CHECK(bet_type IN ('3T','3F','2T','2F','KK','TT','FF')),
  CHECK(boat1 BETWEEN 1 AND 6),
  CHECK(boat2 IS NULL OR boat2 BETWEEN 1 AND 6),
  CHECK(boat3 IS NULL OR boat3 BETWEEN 1 AND 6)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_odds_snapshot
    ON Odds_snapshots(date, venue_id, race_no, bet_type, boat1, boat2, boat3, captured_at);

CREATE INDEX IF NOT EXISTS idx_odds_race
    ON Odds_snapshots(date, venue_id, race_no, bet_type);

CREATE INDEX IF NOT EXISTS idx_odds_final
    ON Odds_snapshots(date, venue_id, race_no, bet_type, is_final);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Summary_ETL(

  summary_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  run_started_at   TEXT    NOT NULL,
  run_finished_at  TEXT    NOT NULL,
  date_from        DATE,
  date_to          DATE,
  files_found      INTEGER DEFAULT 0,
  files_imported   INTEGER DEFAULT 0,
  races_expected   INTEGER DEFAULT 0,
  races_inserted   INTEGER DEFAULT 0,
  races_cancelled  INTEGER DEFAULT 0,
  entries_expected INTEGER DEFAULT 0,
  entries_inserted INTEGER DEFAULT 0,
  entries_missing  INTEGER DEFAULT 0,
  warnings_count   INTEGER DEFAULT 0,
  warnings_json    TEXT
);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Summary_races(

  file_name  TEXT PRIMARY KEY,
  date       DATE NOT NULL UNIQUE,
  venues     INTEGER,
  races      INTEGER,
  cnt_SG     INTEGER,
  cnt_PG1    INTEGER,
  cnt_G1     INTEGER,
  cnt_G2     INTEGER,
  held       INTEGER,
  cancelled  INTEGER
);

CREATE UNIQUE INDEX idx_summary_races_date ON Summary_races(date);

/*-------------------------------------------------------------------------------------*/
CREATE TABLE Summary_Players(

  file_name  TEXT    PRIMARY KEY,
  year       DATE    NOT NULL,
  season     INTEGER NOT NULL,
  players    INTEGER NOT NULL,
  male       INTEGER NOT NULL,
  female     INTEGER NOT NULL
);

/*-------------------------------------------------------------------------------------*/
CREATE VIEW V_daily_schedule

  AS SELECT date,
            venue_id,
            MIN(series_title)  AS series_title,
            MIN(day_no)        AS day_no,
            MIN(grade)         AS grade,
            MIN(held_type)     AS held_type

       FROM Race_programs
   GROUP BY date, venue_id;

/*-------------------------------------------------------------------------------------*/
CREATE VIEW V_race_finish

  AS SELECT e.race_id,
            e.date,
            MAX(CASE WHEN e.course = 1 THEN e.finish_rank END) AS c1,
            MAX(CASE WHEN e.course = 2 THEN e.finish_rank END) AS c2,
            MAX(CASE WHEN e.course = 3 THEN e.finish_rank END) AS c3,
            MAX(CASE WHEN e.course = 4 THEN e.finish_rank END) AS c4,
            MAX(CASE WHEN e.course = 5 THEN e.finish_rank END) AS c5,
            MAX(CASE WHEN e.course = 6 THEN e.finish_rank END) AS c6

       FROM Race_entries e
      WHERE e.fault_code NOT IN ('F','L','K')
        AND(e.finish_rank IS NULL OR e.finish_rank != 0)
    AND NOT(e.fault_code   = 'S' AND e.fault_level  = 0)
   GROUP BY e.race_id, e.date;

/*-------------------------------------------------------------------------------------*/
