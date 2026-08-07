# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\capture_betconf.py
#
# 購入確認画面（betconf）のHTML構造を解析するスクリプト。
# 「投票する」ボタンと投票用PWフィールドのセレクタを確定する。
#
# 使い方:
#   1. 実行すると Brave が起動して投票画面まで自動で進む
#   2. 「手動操作してください」と表示されたら:
#      - 賭式を1つ選んで舟番を選んで金額を入れて
#        「ベットリストに追加」→「投票入力完了」を押す
#   3. betconf画面に遷移したら Enter を押す
#   4. C:\boatrace\tmp\betconf.html と betconf_analysis.json が保存される

from __future__ import annotations
import os, re, time, logging, concurrent.futures, json
import undetected_chromedriver as uc
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC
from selenium.common.exceptions    import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

TOP_PAGE     = "https://www.boatrace.jp"
OUTPUT_HTML  = r"C:\boatrace\tmp\log\betconf.html"
OUTPUT_JSON  = r"C:\boatrace\tmp\log\betconf_analysis.json"

kanyusha_no = os.environ.get("MBRACE_KANYUSHA", "")
ansyo_no    = os.environ.get("MBRACE_ANSYO",    "")
auth_pw     = os.environ.get("MBRACE_AUTHPW",   "")

def main():
    opts = uc.ChromeOptions()
    opts.binary_location = (r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
    opts.add_argument(r"--user-data-dir=C:\boatrace\tmp\Brave_profile\User Data")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-session-crashed-bubble")

    user_data  = r"C:\boatrace\tmp\Brave_profile\User Data"
    prefs_path = os.path.join(user_data, "Default", "Preferences")

    if os.path.exists(prefs_path):
        try:
            with open(prefs_path, encoding="utf-8") as f:
                prefs = json.load(f)

            prefs.setdefault("profile", {})["exit_type"] = "normal"
            prefs.setdefault("profile", {})["exited_cleanly"] = True

            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(prefs, f)
            print("Braveのセッション復元フラグをリセットしました")
        except Exception as e:
            print(f"Preferences の書き換えに失敗: {e}")

    driver = uc.Chrome(options=opts, version_main=147, use_subprocess=True)

    handles = driver.window_handles
    if len(handles) > 1:
        print(f"不要なウィンドウが {len(handles)-1} 件見つかりました。削除します。")
        main = handles[0]
        for h in handles[1:]:
            try:
                driver.switch_to.window(h)
                driver.close()
            except Exception:
                pass
        driver.switch_to.window(main)

    try:
        driver.get(TOP_PAGE)
        time.sleep(2)

        handles_before = set(driver.window_handles)
        try:
            WebDriverWait(driver, 5).until( EC.element_to_be_clickable((By.ID, "commonHead"))
                                           ).click()
        except Exception:
            pass

        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "in_KanyusyaNo")) )

            for fid, val in [("in_KanyusyaNo", kanyusha_no),
                             ("in_AnsyoNo",    ansyo_no),
                             ("in_PassWord",   auth_pw)]:
                el = driver.find_element(By.ID, fid)
                el.click(); time.sleep(0.2)
                el.send_keys(val)
            handles_before = set(driver.window_handles)
            btn = driver.find_element(By.NAME, "TENTP017A_2")
            ActionChains(driver).move_to_element(btn).click().perform()
        except TimeoutException:
            pass

        try:
            WebDriverWait(driver, 10).until(
                lambda d: set(d.window_handles) != handles_before )
            new_handle = (set(driver.window_handles) - handles_before).pop()
            driver.switch_to.window(new_handle)
        except TimeoutException:
            pass

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "todayForm")))
        print("[nav] 場選択画面 確認完了")

        els = driver.find_elements(By.CSS_SELECTOR, f"#jyo03 a")
        if els:
            els[0].click()
            print(f"[nav] jyo03 クリック")

        WebDriverWait(driver, 15).until(
            lambda d: "betcom" in d.current_url or "nextrace" in d.current_url )
        time.sleep(2)
        print(f"[nav] 投票画面到達: {driver.current_url}")

        print()
        print("=" * 60)
        print(" 【手動操作してください】")
        print("  1. 賭式ボタンを選択（例: 3連複）")
        print("  2. 舟番を選択（例: 1, 3, 4）")
        print("  3. 金額を入力（例: 1）")
        print("  4. 「ベットリストに追加」をクリック")
        print("  5. 「投票入力完了」をクリック")
        print("  6. betconf画面（投票内容確認）が表示されたら Enter")
        print("  ※「投票する」は押さないでください")
        print("=" * 60)
        input("  → betconf 画面が表示されたら Enter を押してください: ")

        src = driver.page_source
        os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"[saved] {OUTPUT_HTML}")


        analysis = { "current_url": driver.current_url,
                     "cookies"    : driver.get_cookies(), }

        analysis["forms"] = re.findall(
            r'<form[^>]*>', src, re.IGNORECASE)[:10]

        analysis["elements"] = re.findall(
            r'<(?:input|button|a)[^>]*>(?:[^<]{0,30})?',
            src, re.IGNORECASE)[:60]

        for kw in [ "投票する", "voteBtn", "executeVote", "btnVote",
                    "inputPass", "betPassword", "betpw"             ]:
            idx = src.find(kw)
            if idx >= 0:
                analysis[f"context_{kw}"] = src[max(0,idx-200):idx+300]

        pws = re.findall(
            r'<input[^>]+type=["\']password["\'][^>]*>',
            src, re.IGNORECASE)
        analysis["password_fields"] = pws

        btns = re.findall(
            r'<(?:button|input)[^>]+(?:type=["\']submit["\']|class="[^"]*btn[^"]*")[^>]*>'
            r'(?:[^<]{0,30})?',
            src, re.IGNORECASE)
        analysis["buttons"] = btns[:20]

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"[saved] {OUTPUT_JSON}")

        print()
        print("=== PW フィールド ===")
        for p in analysis["password_fields"]:
            print(f"  {p[:120]}")

        print()
        print("=== ボタン ===")
        for b in analysis["buttons"]:
            print(f"  {b[:120]}")

        print()
        print("=== 「投票する」周辺 ===")
        ctx = analysis.get("context_投票する", "")
        if ctx:
            print(ctx[:500])
        else:
            print("「投票する」テキストが見つかりません")
            print("voteBtn:", bool(analysis.get("context_voteBtn")))
            print("executeVote:", bool(analysis.get("context_executeVote")))

    finally:
        time.sleep(2)
        driver.quit()
        print("[end] 完了")

if __name__ == "__main__":
    main()
