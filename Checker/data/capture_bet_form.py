# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\capture_bet_form.py
#
# 投票画面のフォーム構造を解析するスクリプト。
# 「ベットリストに追加」ボタン周辺の HTML を保存して
# フィールド名・ボタン構造を確定する。
#
# 使い方:
#   1. 実行すると Brave が起動して投票画面まで自動で進む
#   2. 「続行してください」と表示されたら何もしなくてよい
#   3. 自動で HTML が保存されて終了する

import os, time, json, re, concurrent.futures
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC
from selenium.common.exceptions    import TimeoutException

TOP_PAGE    = "https://www.boatrace.jp"
OUTPUT_HTML  = r"C:\boatrace\tmp\log\bet_form.html"
OUTPUT_JSON  = r"C:\boatrace\tmp\log\bet_form_analysis.json"

kanyusha_no = os.environ.get("MBRACE_KANYUSHA", "")
ansyo_no    = os.environ.get("MBRACE_ANSYO",    "")
auth_pw     = os.environ.get("MBRACE_AUTHPW",   "")

#-----------------------------
def _force_kill_leftovers():

    targets = ["chromedriver.exe", "undetected_chromedriver.exe"]
    for target in targets:
        try:
            subprocess.run(['taskkill', '/IM', target, '/T'], capture_output=True, shell=True)
        except Exception:
            pass
#=====================================================================
def main():
    opts = uc.ChromeOptions()
    opts.binary_location = (r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
    opts.add_argument(r"--user-data-dir=C:\boatrace\tmp\Brave_profile\User Data")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")

    driver = uc.Chrome(options=opts, version_main=147, use_subprocess=True)
    print("[start] Brave 起動完了")

    time.sleep(2)
    handles = driver.window_handles
    if len(handles) > 1:
        print(f"不要なウィンドウが {len(handles)-1} 件。削除します。")
        for handle in handles[1:]:
            driver.switch_to.window(handle)
            driver.close()
        driver.switch_to.window(handles[0])
        time.sleep(1)

    try:
        # トップ → 投票ボタン → ログイン → 場選択画面
        driver.get(TOP_PAGE)
        time.sleep(2)

        handles_before = set(driver.window_handles)
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "commonHead"))
            ).click()
        except Exception:
            pass

        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "in_KanyusyaNo"))
            )
            for fid, val in [("in_KanyusyaNo", kanyusha_no),
                             ("in_AnsyoNo",    ansyo_no),
                             ("in_PassWord",   auth_pw)]:
                el = driver.find_element(By.ID, fid)
                el.click(); time.sleep(0.2)
                el.send_keys(val)
            handles_before = set(driver.window_handles)
            driver.find_element(By.NAME, "TENTP017A_2").click()
        except TimeoutException:
            pass

        try:
            WebDriverWait(driver, 8).until(
                lambda d: set(d.window_handles) != handles_before
            )
            new_handle = (set(driver.window_handles) - handles_before).pop()
            driver.switch_to.window(new_handle)
        except TimeoutException:
            pass

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "todayForm"))
        )
        print("[nav] 場選択画面 確認完了")

        els = driver.find_elements(By.CSS_SELECTOR, f"#jyo07 a")
        jyo_el = els[0]
        print(f"[nav] 場を検出: jyo07")

        if jyo_el is None:
            print("[warn] 場が見つかりません")
            return

        jyo_el.click()
        WebDriverWait(driver, 15).until(
            lambda d: "betcom" in d.current_url or "nextrace" in d.current_url
        )
        time.sleep(2)
        print(f"[nav] 投票画面へ遷移完了: {driver.current_url}")

        # ── 投票画面の HTML を保存 ──
        src = driver.page_source

        os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"[saved] HTML: {OUTPUT_HTML}")

        # ── フォーム構造の解析 ──
        analysis = {}

        # 全フォームの action と method
        forms = re.findall(
            r'<form[^>]+(?:action|method|id|name)[^>]*>',
            src, re.IGNORECASE
        )
        analysis["forms"] = forms[:20]

        # input/select/button 要素
        inputs = re.findall(
            r'<(?:input|select|button|textarea)[^>]*>',
            src, re.IGNORECASE
        )
        analysis["form_elements"] = inputs[:60]

        # 「ベットリストに追加」ボタン周辺
        idx = src.find("ベットリストに追加")
        if idx < 0:
            idx = src.find("betlist")
        if idx >= 0:
            analysis["bet_add_button_context"] = src[max(0, idx-500):idx+500]
        else:
            analysis["bet_add_button_context"] = "NOT FOUND"

        # 購入金額フィールド周辺
        idx2 = src.find("購入金額")
        if idx2 >= 0:
            analysis["amount_field_context"] = src[max(0, idx2-200):idx2+400]

        # 勝式（賭式）ボタン周辺
        idx3 = src.find("3連単")
        if idx3 >= 0:
            analysis["kachishiki_context"] = src[max(0, idx3-100):idx3+400]

        # JSESSIONID Cookie 確認
        analysis["cookies"] = driver.get_cookies()
        analysis["current_url"] = driver.current_url

        # page_source から meta/hidden 要素を全て抽出
        metas   = re.findall(r'<meta[^>]+>', src, re.IGNORECASE)
        hiddens = re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', src, re.IGNORECASE)
        analysis["meta_tags"]     = metas[:20]
        analysis["hidden_inputs"] = hiddens[:20]

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"[saved] 解析結果: {OUTPUT_JSON}")

        # コンソールにサマリを表示
        print()
        print("=== フォーム ===")
        for fm in forms[:5]:
            print(f"  {fm[:120]}")

        print()
        print("=== フォーム要素（先頭30件）===")
        for el in inputs[:30]:
            print(f"  {el[:120]}")

        print()
        print("=== ベットリストに追加 周辺 ===")
        ctx = analysis.get("bet_add_button_context", "")
        print(ctx[:600] if ctx else "見つかりません")

        print()
        print("=== Cookie ===")
        for ck in analysis["cookies"]:
            print(f"  {ck['name']:30s} = {ck['value'][:50]}")

    finally:
        time.sleep(2)
        driver.quit()
        print("[end] 完了")

if __name__ == "__main__":
    main()