# -*- coding: utf-8 -*-
# C:\boatrace\Inport\import_Fan.py

import argparse, glob, re, sqlite3, shutil, subprocess
from dataclasses import dataclass
from datetime    import date
from pathlib     import Path
from typing      import Dict, List, Tuple, Optional

DB_PATH    = r"C:\boatrace\boatrace.db"
INBOX_DIR  = Path(r"C:\boatrace\INBOX\Fan")
ARC_DIR    = Path(r"C:\boatrace\Archive\FAN\FAN_TXT")
LAYOUT_TXT = r"C:\boatrace\tmp\fan_data_layout.txt"

# =========================== ユーティリティ =========================
def conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA foreign_keys=ON;")
    return c
#---------------------------------------------------------------------
def load_layout():

    names, offs = [], []
    pos         = 0

    with open(LAYOUT_TXT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "\t" not in line: continue

            name, wtxt = line.split("\t", 1)

            try: w = int(wtxt.strip())
            except ValueError: continue

            names.append(name.strip())
            offs.append((pos, w))

            pos += w

    if not names: raise RuntimeError("layout 読み込み失敗（空）")

    return names, offs

#---------------------------------------------------------------------
def decode_line(line_bytes:bytes, names:List[str], offs: List[Tuple[int,int]]):

    out:Dict[str, str] = {}

    for name, (pos, w) in zip(names, offs):
        raw       = line_bytes[pos:pos+w]
        out[name] = raw.decode("cp932", errors="ignore")

    return out

class RequiredFieldError(Exception): pass
#---------------------------------------------------------------------
def req_str(field:str, v:Optional[str]):

    if v is None: raise RequiredFieldError(f"{field} required")
    s = v.strip()
    if s == "":   raise RequiredFieldError(f"{field} empty")

    return s
#---------------------------------------------------------------------
def req_int(field:str, v:Optional[str]):

    if v is None: raise RequiredFieldError(f"{field} required")
    s = v.strip()
    if s == "" or not re.fullmatch(r"-?\d+", s):
        raise RequiredFieldError(f"{field} not-int: {v!r}")

    return int(s)
#---------------------------------------------------------------------
def normalize_sex(v:str):

    v = v.strip()
    if v in ("1", "男"): return "男"
    if v in ("2", "女"): return "女"

    raise RequiredFieldError(f"sex invalid: {v!r}")
#---------------------------------------------------------------------
def parse_birthday(era_letter:str, yymmdd:str):

    e = era_letter.strip().upper()

    if not re.fullmatch(r"[SHR]", e):
        raise RequiredFieldError(f"era invalid: {era_letter!r}")
    if not re.fullmatch(r"\d{6}", yymmdd or ""):
        raise RequiredFieldError(f"birthday invalid: {yymmdd!r}")

    yy = int(yymmdd[0:2])
    mm = int(yymmdd[2:4])
    dd = int(yymmdd[4:6])

    if    e == "S": yyyy = 1925 + yy
    elif  e == "H": yyyy = 1988 + yy
    else          : yyyy = 2018 + yy

    return f"{yyyy:04d}-{mm:02d}-{dd:02d}"

#---------------------------------------------------------------------
def compute_age(birthday_iso:str, asof:Optional[date]=None):

    y, m, d = map(int, birthday_iso.split("-"))
    bd      = date(y, m, d)
    today   = asof or date.today()
    a       = today.year -bd.year -((today.month, today.day) < (bd.month, bd.day))

    return max(a, 0)
# ---------------------モード ----------------------------------------
@dataclass(frozen=True)
class Mode:
    overwrite: bool = False
    @classmethod
    def from_args(cls, args) -> "Mode":
        return cls(overwrite=args.overwrite)
# =================== SQL (Players / Season_result) ==================
# 変動5項目のみ差分更新（最新ファイル時の通常モード）

PLAYER_UPDATE_DIFF_SQL = """
    UPDATE Players
       SET  age = CASE WHEN COALESCE( age, -1) 
                     IS NOT COALESCE(:age, -1)
                       THEN :age
                       ELSE  age       END,
        regions = CASE WHEN :regions
                     IS NOT NULL
                        AND COALESCE(regions,'') <> :regions
                       THEN :regions
                       ELSE  regions   END,
         height = CASE WHEN COALESCE(height, -1)
                     IS NOT :height
                       THEN :height
                       ELSE  height    END,
         weight = CASE WHEN COALESCE(weight, -1)
                     IS NOT :weight
                       THEN :weight
                       ELSE  weight    END,
      class_now = CASE WHEN :class_now
                     IS NOT NULL
                        AND COALESCE(class_now,'') <> :class_now
                       THEN :class_now
                       ELSE  class_now END
     WHERE player_id = :player_id
       AND (COALESCE(age, -1) IS NOT COALESCE(:age, -1)
        OR (:regions   IS NOT NULL AND COALESCE(regions,'')   <> :regions)
        OR  COALESCE(height, -1) IS NOT :height
        OR  COALESCE(weight, -1) IS NOT :weight
        OR (:class_now IS NOT NULL AND COALESCE(class_now,'') <> :class_now) )
    """

# 過去ファイル時の通常モード：現値が NULL の場合のみ上書き

PLAYER_UPDATE_PAST_NULLZERO_SQL = """
    UPDATE Players
       SET age       = CASE WHEN (age       IS NULL )
                            THEN :age
                            ELSE  age       END,
           regions   = CASE WHEN (regions   IS NULL )
                            THEN :regions
                            ELSE  regions   END,
           height    = CASE WHEN (height IS NULL )
                            THEN :height
                            ELSE  height    END,
           weight    = CASE WHEN (weight IS NULL )
                            THEN :weight
                            ELSE  weight    END,
           class_now = CASE WHEN (class_now IS NULL )
                            THEN :class_now
                            ELSE  class_now END
     WHERE player_id = :player_id
       AND ( (age       IS NULL OR       age= 0 )
        OR   (regions   IS NULL OR   regions='0')
        OR   (height    IS NULL OR    height= 0 )
        OR   (weight    IS NULL OR    weight= 0 )
        OR   (class_now IS NULL OR class_now='0') )
    """

PLAYER_UPDATE_ALL_SQL = """
    UPDATE Players
       SET name          = :name,
           name_kana     = :name_kana,
           sex           = :sex,
           age           = :age,
           regist_period = :regist_period,
           regions       = COALESCE(:regions, regions),
           height        = :height,
           weight        = :weight,
           blood_type    = :blood_type,
           birthday      = :birthday,
           birthplace    = COALESCE(:birthplace, birthplace),
           class_now     = :class_now,
           comment       = NULL
     WHERE player_id     = :player_id
    """

PLAYER_INSERT_SQL = """
    INSERT INTO Players( player_id,     name,       name_kana, sex,    age,
                         regist_period, regions,    height,    weight, blood_type,
                         birthday,      birthplace, class_now                         )

         VALUES( :player_id,     :name,       :name_kana, :sex,    :age, 
                 :regist_period, :regions,    :height,    :weight, :blood_type, 
                 :birthday,      :birthplace, :class_now                           )
    """

SEASON_UPSERT_SQL = """
    INSERT INTO Season_result( player_id, year,   season, class_in, score_ave,
                               top2_ave,  ST_ave, overall_rating               )
         VALUES( :player_id, :year,   :season, :class_in, :score_ave,
                 :top2_ave,  :ST_ave, :overall_rating                 )
    ON CONFLICT(player_id, year, season)
  DO UPDATE SET class_in       = excluded.class_in,
                score_ave      = excluded.score_ave,
                top2_ave       = excluded.top2_ave,
                ST_ave         = excluded.ST_ave,
                overall_rating = excluded.overall_rating
    """

@dataclass
class Summary:
    before_players:     int = 0
    after_players:      int = 0
    inserted_players:   int = 0
    updated_players:    int = 0
    inserted_season:    int = 0
    updated_season:     int = 0
    skipped_players_pk: int = 0
    warnings:     List[str] = None

    def __post_init__(self):
        if self.warnings is None: self.warnings = []
#---------------------------------------------------------------------
def count_players(c:sqlite3.Connection):
    return c.execute("SELECT COUNT(*) FROM Players").fetchone()[0]
#---------------------------------------------------------------------
def select_player(c:sqlite3.Connection, player_id:int):
    c.row_factory = sqlite3.Row
    return c.execute("SELECT * FROM Players WHERE player_id=?",(player_id,)).fetchone()
#---------------------------------------------------------------------
def ensure_dirs():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ARC_DIR.mkdir(  parents=True, exist_ok=True)
#---------------------------------------------------------------------
def archive_files(paths: List[Path]):

    ARC_DIR.mkdir(parents=True, exist_ok=True)
    for src in paths:
        if not src.exists(): continue
        dst = ARC_DIR / src.name
        if dst.exists(): continue

        shutil.move(str(src), str(dst))
# ======================= パース関数 =================================
def parse_player_row(obj: Dict[str,str], is_old: bool=False):

    player_id     = req_int("player_id",     obj.get("登番"))
    name          = req_str("name",          obj.get("氏名漢字"))
    name_kana     = req_str("name_kana",     obj.get("氏名カナ"))
    sex           = normalize_sex(req_str("sex", obj.get("性別")))
    regist_period = req_int("regist_period", obj.get("登録期") )
    height        = req_int("height",        obj.get("身長")   )
    weight        = req_int("weight",        obj.get("体重")   )
    blood_type    = req_str("blood_type",    obj.get("血液型") )
    birthday      = parse_birthday(          req_str("年号", obj.get("年号")),
                    req_str("birthday",      obj.get("生年月日")))
    age_val       = compute_age(birthday)
    class_now     = req_str("class_in",     (obj.get("級")     or "B2"))

    if is_old:
        regions    = None
        birthplace = None
    else:
        regions    = req_str("regions",      obj.get("支部"))
        birthplace = req_str("birth_place", (obj.get("出身地") or ""))

    return {
        "player_id"     :player_id,
        "name"          :name,
        "name_kana"     :name_kana,
        "sex"           :sex,
        "age"           :age_val,
        "regist_period" :regist_period,
        "regions"       :regions,
        "height"        :height,
        "weight"        :weight,
        "blood_type"    :blood_type,
        "birthday"      :birthday,
        "birthplace"    :birthplace,
        "class_now"     :class_now,     }

#---------------------------------------------------------------------
def parse_season_row(obj: Dict[str,str]):

    player_id = req_int("player_id",      obj.get("登番"))
    class_in  = req_str("class_in",      (obj.get("級") or "").strip() or None)
    year      = req_int("year",           obj.get("年"))
    season    = req_int("season",         obj.get("期"))
    score     = req_int("score_ave",      obj.get("勝率"))
    top2      = req_int("top2_ave",       obj.get("複勝率"))
    st        = req_str("ST_ave",        (obj.get("平均ST") or "").strip() or None)
    overall   = req_int("overall_rating", obj.get("今期能力指数"))

    return {
        "player_id"     :player_id,
        "year"          :year,
        "season"        :season,
        "class_in"      :class_in,
        "score_ave"     :score,
        "top2_ave"      :top2,
        "ST_ave"        :st,
        "overall_rating":overall    }

# ------------------------ 最新／過去 判定 ---------------------------
def get_latest_season_in_summary(c:sqlite3.Connection):

    row = c.execute("""
        SELECT year, season
          FROM Summary_players
         WHERE year   IS NOT NULL
           AND season IS NOT NULL
      ORDER BY year DESC, season DESC
         LIMIT 1
    """).fetchone()

    return (int(row[0]), int(row[1])) if row else None
#---------------------------------------------------------------------
def parse_year_season_from_filename(path:Path):

    m = re.search(r"fan(\d{2})(\d{2})", path.name, re.I)
    if not m: return None, None

    yy, tt = m.groups()
    year   = 2000 + int(yy)
    season = 1 if tt == "04" else 2

    return year, season
#---------------------------------------------------------------------
@dataclass
class FileContext:
    path:          Path
    is_old_layout: bool
    is_latest:     bool
#---------------------------------------------------------------------
def upsert_players_and_terms(paths: List[Path], mode: Mode):

    names, offs = load_layout()
    summ        = Summary()

    with conn() as c:
        summ.before_players  = count_players(c)
        c.execute("BEGIN IMMEDIATE;")
        inserted  = 0
        latest_ys = get_latest_season_in_summary(c)

        for p in paths:
            year_num, term = parse_year_season_from_filename(p)
            is_old    = (year_num  is not None and (year_num % 100) <= 13)
            is_latest = (latest_ys is None)     or (year_num, term) == latest_ys

            with open(p, "rb") as f:
                p_cnt , m_cnt, f_cnt = 0, 0, 0
                for line in f:
                    line = line.rstrip(b"\r\n")
                    if not line: continue

                    obj    = decode_line(line, names, offs)
                    p_cnt += 1
                    try:        # --- Players ---
                        pd = parse_player_row(obj, is_old)
                        if   pd["sex"] == "男": m_cnt += 1
                        elif pd["sex"] == "女": f_cnt += 1
                    except RequiredFieldError:
                        c.rollback(); raise

                    exists = select_player(c, pd["player_id"])
                    if not exists:
                        c.execute(PLAYER_INSERT_SQL, pd)
                        summ.inserted_players += 1
                        inserted              += 1
                    else:
                        if mode.overwrite:
                            c.execute(PLAYER_UPDATE_ALL_SQL, pd)
                            summ.updated_players += 1
                        else:
                            if is_latest:
                                rc = c.execute(PLAYER_UPDATE_DIFF_SQL, pd)
                                if rc.rowcount > 0: summ.updated_players += rc.rowcount
                            else:
                                rc = c.execute(PLAYER_UPDATE_PAST_NULLZERO_SQL, pd)
                                if rc.rowcount > 0: summ.updated_players += rc.rowcount

                    try: sd = parse_season_row(obj) # --- Season_result ---
                    except RequiredFieldError: continue

                    cur = c.execute(SEASON_UPSERT_SQL, sd)
                    if cur.rowcount == 1: summ.updated_season += 1

                file_name  = p.name
                if year_num is not None and term is not None:
                    year   = year_num
                    season = term
                else: 
                    year   = None
                    season = None

                c.execute("""
                    INSERT
                      INTO Summary_players( file_name, year, season,
                                                 players,   male, female )
                    VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(file_name)
             DO UPDATE SET year    = excluded.year,
                           season  = excluded.season,
                           players = excluded.players,
                           male    = excluded.male,
                           female  = excluded.female
                    """,
                    (file_name, year, season, p_cnt, m_cnt, f_cnt))

        if inserted >= 40:
            summ.warnings.append(f"[Players] 新規登録 {inserted} 件（閾値>=40）")

        summ.after_players = count_players(c)
        c.commit()

    return summ

#================================== CLI ========================================
def resolve_targets_by_tag(tag:Optional[str]):

    ensure_dirs()
    if tag:
        if not re.fullmatch(r"\d{4}", tag):
            raise SystemExit(f"tag は 4桁数値を指定してください: {tag!r}")

        cand_arc =   ARC_DIR / f"fan{tag}.txt"
        cand_inb = INBOX_DIR / f"fan{tag}.txt"

        if cand_arc.exists(): return [cand_arc]
        if cand_inb.exists(): return [cand_inb]

        raise SystemExit(f"対象ファイルが見つかりません: {cand_arc} / {cand_inb}")

    return [Path(p) for p in glob.glob(str(INBOX_DIR / "fan*.txt"))]

#-------------------------------------------------------------------------------
def main():

    ap = argparse.ArgumentParser(description="FAN(選手/期別ﾃﾞｰﾀ)取込")
    ap.add_argument("tag",          nargs="?",         help="対象ﾌｧｲﾙ(yy04/10)")
    ap.add_argument("--overwrite", action="store_true",help="上書きﾓｰﾄﾞ")
    args = ap.parse_args()

    paths = resolve_targets_by_tag(args.tag)
    mode  = Mode.from_args(args)

    print(f"mode: overwrite={mode.overwrite}")
    print("targets:")

    for p in paths: print(f" - {p}")

    summ = upsert_players_and_terms(paths, mode)

    print("---- summary ----")
    print(f"Players(before)   : {summ.before_players}")
    print(f"Players(after)    : {summ.after_players}")
    print(f"Players(insert)   : {summ.inserted_players}")
    print(f"Players(update)   : {summ.updated_players}")
    print(f"Season_rslt(insert) : {summ.inserted_season}")
    print(f"Season_rslt(update) : {summ.updated_season}")

    if summ.warnings:
        print("-- WARNINGS --")
        for w in summ.warnings: print(w)

    if not summ.warnings: archive_files(paths)
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main()

    try: subprocess.run( ["python", r"C:\boatrace\Import\DL_player_img.py"],
                                                                      check=True )
    except Exception as e:
        print(f"[WARN] download_player_images.py 呼び出し失敗: {e}")
