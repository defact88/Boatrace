# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\selenium_buyer.py

from __future__       import annotations
from typing           import List, Optional, Tuple, Dict
from logging          import getLogger, FileHandler, Formatter, INFO
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC
from selenium.common.exceptions    import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
import os, re, time, concurrent.futures, json

logger = getLogger(__name__)
logger.setLevel(INFO)

OUTPUT_JSON  = r"C:\boatrace\tmp\log\bet_log.json"
LOG_DIR      = r"C:\boatrace\tmp\log"
log_path     = os.path.join(LOG_DIR, "selenium.log")

fh = FileHandler(log_path, encoding='utf-8')
fh.setLevel(INFO)

formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

TOP_PAGE     = "https://www.boatrace.jp"
LOGIN_URL    = f"{TOP_PAGE}/owpc/pc/login?authAfterUrl=/%3FvoteTagId%3DcommonHead"
BASE_BET     = "https://ib.mbrace.or.jp/tohyo-ap-pctohyo-web"

KACHISHIKI_SEL = { "TT":"#betkati1 a",
                   "FF":"#betkati2 a",
                   "2T":"#betkati3 a",
                   "2F":"#betkati4 a",
                   "KK":"#betkati5 a",
                   "3T":"#betkati6 a",
                   "3F":"#betkati7 a", }

KACHISHIKI_COLS = { "TT": 1,
                    "FF": 1,
                    "2T": 2,
                    "2F": 2,
                    "KK": 2,
                    "3T": 3,
                    "3F": 3, }

SEL_AMOUNT      = "#amount"
SEL_ADD_BTN     = "#regAmountBtn a"
SEL_COMP_BTN    = ".btnSubmit a"
SEL_CONF_AMT    = "#distamoTotal"
SEL_CONF_PW     = "#transferBetPassword"

#=====================================================================
class PurchaseError(Exception):  pass
class LoginError(PurchaseError): pass
class BetError(PurchaseError):   pass

#=====================================================================
class SeleniumBuyer:
    def __init__( self, kanyusha_no :Optional[str] = None,
                        ansyo_no    :Optional[str] = None,
                        auth_pw     :Optional[str] = None,
                        bet_pw      :Optional[str] = None,
                        headless    :bool          = False,
                        timeout     :int           = 5      ):

        self.kanyusha_no = kanyusha_no or os.environ.get("MBRACE_KANYUSHA", "")
        self.ansyo_no    = ansyo_no    or os.environ.get("MBRACE_ANSYO",    "")
        self.auth_pw     = auth_pw     or os.environ.get("MBRACE_AUTHPW",   "")
        self.bet_pw      = bet_pw      or os.environ.get("MBRACE_BETPW",    "")
        self.timeout     = timeout
        self._driver     = None

        missing = [ n for n, v in [ ("加入者番号", self.kanyusha_no),
                                    ("暗証番号",   self.ansyo_no),
                                    ("認証用PW",   self.auth_pw),
                                    ("購入用PW",   self.bet_pw)       ] if not v ]
        if missing:
            raise ValueError(f"未設定の認証情報: {', '.join(missing)}")

        self._force_kill_leftovers()
        self._reset_brave_session()

        time.sleep(1)

        opts = uc.ChromeOptions()
        opts.binary_location = (r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")

        if headless:
            opts.add_argument("--headless=new")

        opts.add_argument(r"--user-data-dir=C:\boatrace\tmp\Brave_profile\User Data")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-session-crashed-bubble")

        self._driver = uc.Chrome(options=opts, version_main=150, use_subprocess=True)
        logger.info("Brave 起動完了")

    #-----------------------------------------------------------------
    def login(self, venue_id:int):

        self._close_extra_windows()
        time.sleep(0.5)
        self._navigate_to_bet_window()
        self._navigate_to_venue(venue_id)
        logger.info(f"ログイン・場遷移完了 venue_id={venue_id}")

    #-----------------------------------------------------------------
    def _navigate_to_bet_window(self):

        self._driver.set_window_size(1000, 700)
        self._driver.set_window_position(1000, 300)
        logger.info(f"トップページへアクセス →")
        self._driver.get(TOP_PAGE)
        time.sleep(0.1)

        handles_before = set(self._driver.window_handles)

        try:
            self._wait(3).until(EC.element_to_be_clickable((By.ID,"commonHead"))).click()
            logger.info("「投票」ボタン クリック →")
        except TimeoutException:
            logger.warning("「投票」ボタンが見つかりません")
        time.sleep(0.3)

        try:
            self._wait(5).until(EC.presence_of_element_located((By.ID,"in_KanyusyaNo")))

            logger.info("ログインフォーム検出: OK → 入力開始")
            for fid, val in [ ("in_KanyusyaNo", self.kanyusha_no),
                              ("in_AnsyoNo",    self.ansyo_no),
                              ("in_PassWord",   self.auth_pw)     ]:
                el = self._driver.find_element(By.ID, fid)
                el.send_keys(val)
                time.sleep(0.1)

            handles_before = set(self._driver.window_handles)
            btn            = self._driver.find_element(By.NAME, "TENTP017A_2")
            ActionChains(self._driver).move_to_element(btn).click().perform()
            logger.info("ログインボタン クリック")

        except TimeoutException:
            logger.info("ログインフォームなし (ログイン済み)")

        try:
            self._wait(3).until(lambda d:set(d.window_handles) != handles_before)
            new_handle = (set(self._driver.window_handles) - handles_before).pop()
            self._driver.switch_to.window(new_handle)
            logger.info(f"投票画面へ切り替え: OK")

        except TimeoutException:
            raise LoginError("投票ウィンドウが開きませんでした")

        logger.info("場選択画面 遷移確認 →")

        try:
            self._wait(3).until(EC.presence_of_element_located((By.ID,"todayForm")))
            logger.info("場選択画面 遷移: OK")
        except TimeoutException:
            raise LoginError(f"場選択画面が開きません: {self._driver.current_url}")

    #-----------------------------------------------------------------
    def _navigate_to_venue(self, venue_id:int):

        self._driver.set_window_size(1000, 700)
        self._driver.set_window_position(800, 300)
        jyo_id   = f"jyo{venue_id:02d}"
        selector = f"#{jyo_id} a"
        logger.info(f"場選択を実行: jyoCode={venue_id} →")

        try:
            btn = self._wait(3).until( EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            btn.click()

        except TimeoutException:
            li_exists = bool(self._driver.find_elements(By.ID, jyo_id))
            a_exists  = bool(self._driver.find_elements(By.CSS_SELECTOR, selector))
            raise LoginError( f"場選択ボタンが見つかりません\n"
                              f"  selector='{selector}'\n"
                              f"  li#{jyo_id}: {li_exists} / {selector}: {a_exists}\n"
                              f"  URL: {self._driver.current_url}\n"
                              f"  → 指定会場が開催中か確認してください"                 )

        try:
            self._wait(3).until(lambda d:"betcom" in d.current_url or "nextrace" in d.current_url)
            time.sleep(0.2)
            logger.info(f"投票画面への遷移: OK")
        except TimeoutException:
            raise LoginError(f"投票画面へ遷移できませんでした: {self._driver.current_url}")

    #-----------------------------------------------------------------
    def _select_race(self, race_no:int):

        selectors = [ f"a[data-race='{race_no}']",
                      f"a[data-raceno='{race_no}']",
                      f"li.raceTab:nth-child({race_no}) a",
                      f"//a[contains(text(),'{race_no}R')]", ]

        for sel in selectors:
            try:
                if sel.startswith("//"):
                    el = self._driver.find_element(By.XPATH, sel)
                else:
                    el = self._driver.find_element(By.CSS_SELECTOR, sel)
                el.click()
                time.sleep(0.1)
                logger.info(f"レース選択({race_no}R): OK")
                return
            except NoSuchElementException:
                continue

        logger.warning(f"レースタブが見つかりません({race_no}R)。")

    #-----------------------------------------------------------------
    def purchase_all( self, selected:List[Tuple], date_str:str, venue_id:int, race_no:int,
                                                                      dry_run:bool = True ):

        result = {"success": [], "failed": [], "skipped": []}
        bets   = []

        for item in selected:
            bt, key, label = item[0], item[1], item[2]
            alloc_str = item[3] if len(item) > 3 else ""
            if not alloc_str or not alloc_str.strip():
                result["skipped"].append(label); continue
            try:
                lot = int(alloc_str.replace(",", ""))
            except ValueError:
                result["skipped"].append(label); continue
            bets.append((bt, key, label, lot))

        if not bets:
            logger.warning("購入対象 0 件（金額未入力）")
            return result

        try:
            self._select_race(race_no)
        except Exception as e:
            logger.warning(f"レース選択失敗（続行）: {e}")

        total = 0
        for (bt, key, label, lot) in bets:
            try:
                self._add_one_bet(bt, key, lot)
                result["success"].append(f"{label}   {lot}00円")
                logger.info(f"ベット登録完了: {label} / {lot}口")
                total += lot
            except BetError as e:
                result["failed"].append(label)
                logger.error(f"ベット登録失敗: {label} → {e}")

        if not result["success"]:
            logger.warning("登録成功件数 0 件。購入を中止します。")
            return result
        else:
            result["success"].append(f"合計   {total}00円")
        try:
            self._click_comp_btn()
        except BetError as e:
            logger.error(f"投票入力完了ボタン失敗: {e}")
            result["failed"] += result["success"]
            result["success"] = []
            return result

        if dry_run:
            logger.info("[DRY RUN] 投票入力完了まで完了。確認画面へは進みません。")
            return result

        try:
            self._confirm_and_vote(f"{total*100}")
            logger.info("購入完了")
        except BetError as e:
            logger.error(f"購入確定失敗: {e}")
            result["failed"] += result["success"]
            result["success"] = []

        return result

    #-----------------------------------------------------------------
    def _add_one_bet(self, bet_type:str, key:tuple, lot:int):

        wait      = self._wait(5)
        kachi_sel = KACHISHIKI_SEL.get(bet_type)

        if not kachi_sel:
            raise BetError(f"未対応の賭式: {bet_type}")

        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, kachi_sel))).click()
            time.sleep(0.1)
            logger.info(f"賭式選択: {bet_type} ({kachi_sel})")
        except TimeoutException:
            raise BetError(f"賭式ボタンが見つかりません: {kachi_sel}")

        n_cols = KACHISHIKI_COLS.get(bet_type, 1)
        boats  = list(key)

        if n_cols == 1:
            for boat in boats:
                sel = f"#regbtn_{boat}_1 a"
                try:
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
                    logger.info(f"舟番クリック: {boat}号艇 (列1)")
                except TimeoutException:
                    try:
                        self._driver.find_element(By.ID, f"regbtn_{boat}_1").click()
                    except NoSuchElementException:
                        raise BetError(f"舟番ボタンが見つかりません: {sel}")
        else:
            for col, boat in enumerate(boats[:n_cols], start=1):
                sel = f"#regbtn_{boat}_{col} a"
                try:
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
                    logger.info(f"舟番クリック: {boat}号艇 ({col}着列)")
                except TimeoutException:
                    try:
                        self._driver.find_element(By.ID, f"regbtn_{boat}_{col}").click()
                    except NoSuchElementException:
                        raise BetError(f"舟番ボタンが見つかりません: {sel}")

        try:
            amt_el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_AMOUNT)))
            amt_el.clear()
            amt_el.send_keys(str(lot))
            logger.info(f"金額入力: {lot}（={lot*100}円）")
        except TimeoutException:
            raise BetError("金額フィールドが見つかりません")

        try:
            self._wait(5).until( lambda d:
                                     "off" not in ( d.find_element( By.ID, "regAmountBtn"
                                                   ).get_attribute("class") or "" ) )
        except TimeoutException:
            raise BetError( "「ベットリストに追加」ボタンが有効になりません。\n"
                            "舟番が正しく選択されているか確認してください。"     )

        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_ADD_BTN))).click()
            time.sleep(0.1)
            logger.info("ベットリストに追加 クリック完了")
        except TimeoutException:
            raise BetError("「ベットリストに追加」ボタンが押せません")

    #-----------------------------------------------------------------
    def _click_comp_btn(self):

        try:
            self._wait(5).until( lambda d: 
                                    "off" not in ( d.find_element( By.CSS_SELECTOR, ".btnSubmit"
                                                                  ).get_attribute("class") or "" ))
        except TimeoutException:
            raise BetError("「投票入力完了」ボタンが有効になりません（ベット登録件数を確認）")

        try:
            self._wait(5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_COMP_BTN))).click()
            logger.info("「投票入力完了」クリック → 確認画面を待機中")
        except TimeoutException:
            raise BetError("「投票入力完了」が押せません")

        try:
            self._wait(5).until(lambda d: "betconf" in d.current_url)
            time.sleep(0.1)
            logger.info(f"購入確認画面へ遷移: OK")
        except TimeoutException:
            raise BetError(f"購入確認画面への遷移タイムアウト: {self._driver.current_url}")

    #-----------------------------------------------------------------
    def _confirm_and_vote(self, total_yen:int):

        wait = WebDriverWait(self._driver, 10)

        try:
            amt_el = wait.until(EC.element_to_be_clickable((By.ID, "amount")))
            amt_el.send_keys(str(total_yen))
            time.sleep(0.1)
            logger.info(f"確認画面 購入金額入力: {total_yen}円")
        except TimeoutException:
            raise BetError("確認画面の購入金額フィールド(#amount)が見つかりません")

        try:
            pw_el = wait.until(EC.element_to_be_clickable((By.ID, "pass")))
            pw_el.send_keys(self.bet_pw)
            time.sleep(0.1)
            logger.info("確認画面 投票用パスワード入力完了")
        except TimeoutException:
            raise BetError("確認画面の投票用PWフィールド(#pass)が見つかりません")

        try:
            vote_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#submitBet a")))
            vote_btn.click()
            logger.info("「投票する」ボタンクリック完了")
            time.sleep(0.1)
        except TimeoutException:
            raise BetError("「投票する」ボタン(#submitBet a)が見つかりません")

        ok_clicked = False
        ok_selectors = [ (By.XPATH,        "//a[normalize-space()='OK']"),
                         (By.XPATH,        "//button[normalize-space()='OK']"),
                         (By.CSS_SELECTOR, "#btnOK a"),
                         (By.CSS_SELECTOR, ".btnOk a"),
                         (By.CSS_SELECTOR, ".popupBtn a"),                      ]
        time.sleep(0.2)
        for by, sel in ok_selectors:
            try:
                ok_el = WebDriverWait(self._driver, 3).until(EC.element_to_be_clickable((by, sel)))
                ok_el.click()
                ok_clicked = True
                logger.info(f"最終確認 OKクリック: {sel}")
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not ok_clicked:
            try:
                WebDriverWait(self._driver, 3).until(EC.alert_is_present())
                self._driver.switch_to.alert().accept()
                ok_clicked = True
                logger.info("JS confirm ダイアログ OKクリック")
            except (TimeoutException, NoAlertPresentException):
                pass

        if not ok_clicked:
            logger.warning("最終確認OKボタンが見つかりませんでした。手動確認してください。")

        time.sleep(0.5)
        logger.info(f"購入処理完了")

    #-----------------------------------------------------------------
    def _force_kill_leftovers(self):

        targets = ["chromedriver.exe", "undetected_chromedriver.exe"]
        for target in targets:
            try:
                subprocess.run(['taskkill', '/IM', target, '/T'], capture_output=True, shell=True)
            except Exception:
                pass

    #-----------------------------------------------------------------
    def shutdown(self):
        if hasattr(self, '_driver') and self._driver:
            try:
                self._driver.quit()
            except Exception as e:
                logger.warning(f"Seleniumの終了中にエラー: {e}")
            finally:
                self._driver = None

        self._reset_brave_session()
        logger.info("すべての終了処理が完了しました。")

    #-----------------------------------------------------------------
    def _reset_brave_session(self):

        user_data    = r"C:\boatrace\tmp\Brave_profile\User Data"
        default_dir  = os.path.join(user_data, "Default")
        prefs_path   = os.path.join(default_dir, "Preferences")

        for fname in ["Last Session", "Last Tabs", "Current Session", "Current Tabs"]:
            fpath = os.path.join(default_dir, fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    logger.info(f"セッションファイル削除: {fname}")
                except Exception as e:
                    logger.warning(f"削除失敗: {fname} ({e})")

        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, encoding="utf-8") as f:
                    prefs = json.load(f)

                prefs.setdefault("profile", {})["exit_type"] = "normal"
                prefs.setdefault("profile", {})["exited_cleanly"] = True
                prefs.setdefault("profile", {})["restore_on_startup"] = 1 

                sessions = prefs.get("profile", {}).get("sessions", {})
                if sessions:
                    prefs["profile"]["sessions"] = {}

                with open(prefs_path, "w", encoding="utf-8") as f:
                    json.dump(prefs, f)
                logger.info("Braveのセッション復元フラグをリセットしました")

            except Exception as e:
                logger.warning(f"Preferences の書き換えに失敗: {e}")

    #-----------------------------------------------------------------
    def _close_extra_windows(self):

        handles = self._driver.window_handles
        if len(handles) > 1:
            logger.info(f"不要なウィンドウが {len(handles)-1} 件見つかりました。削除します。")
            main = handles[0]
            for h in handles[1:]:
                try:
                    self._driver.switch_to.window(h)
                    self._driver.close()
                except Exception:
                    pass
            self._driver.switch_to.window(main)
    #-----------------------------------------------------------------
    def _wait(self, time:int):
        return WebDriverWait(self._driver, time)