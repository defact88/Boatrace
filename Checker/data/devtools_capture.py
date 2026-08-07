# -*- coding: utf-8 -*-
# C:\boatrace\UI\Helpers\devtools_capture.py

# 使い方:
#   1. このスクリプトを単独で実行する
#   2. Brave が起動して場選択画面まで自動で進む
#   3. 「続行してください」と表示されたら手動で操作する
#      - 場ボタンをクリック → 投票画面へ遷移
#      - 賭式ボタンを選択 → 舟番を選択 → 金額入力
#      - 「ベットリストに追加」ボタンをクリック（※実際に購入はしない）
#   4. ボタンを押した瞬間のリクエストが captured_requests.json に保存される
#   5. Brave が自動で閉じる

import json, os, time, re, threading
import undetected_chromedriver as uc
from selenium.webdriver.common.by   import By
from selenium.webdriver.support.ui  import WebDriverWait
from selenium.webdriver.support     import expected_conditions as EC
from selenium.common.exceptions     import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

TOP_PAGE  = "https://www.boatrace.jp"
LOGIN_URL = f"{TOP_PAGE}/owpc/pc/login?authAfterUrl=/%3FvoteTagId%3DcommonHead"
BASE_BET  = "https://ib.mbrace.or.jp/tohyo-ap-pctohyo-web"

TARGET_URLS = ["betadd", "betcomp", "betcom", "service/bet"]

OUTPUT_FILE = r"C:\boatrace\tmp\log\captured_requests.json"

kanyusha_no = os.environ.get("MBRACE_KANYUSHA", "")
ansyo_no    = os.environ.get("MBRACE_ANSYO",    "")
auth_pw     = os.environ.get("MBRACE_AUTHPW",   "")

# ── CDP ネットワーク監視 ──────────────────────────────────────────────────────

captured = []
#------------------------------
def enable_cdp_network(driver):

    driver.execute_cdp_cmd("Network.enable", {})
#------------------------------
def start_capture(driver):

    js_intercept = """
    window.__captured = window.__captured || [];

    const _origFetch = window.fetch;
    window.fetch = async function(input, init) {
        const url    = (typeof input === 'string') ? input : input.url;
        const method = (init && init.method) ? init.method : 'GET';
        const body   = (init && init.body)   ? init.body   : null;
        const heads  = (init && init.headers) ? JSON.stringify(init.headers) : null;
        const result = await _origFetch(input, init);
        const clone  = result.clone();
        let respText = '';
        try { respText = await clone.text(); } catch(e) {}

        window.__captured.push({
            type    : 'fetch',
            url     : url,
            method  : method,
            body    : body,
            headers : heads,
            status  : result.status,
            response: respText.substring(0, 2000),
            cookies : document.cookie,
            ts      : new Date().toISOString()
        });

        return result;
    };

    const _origOpen = XMLHttpRequest.prototype.open;
    const _origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
        this._url    = url;
        this._method = method;
        return _origOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        const xhr = this;
        xhr.addEventListener('load', function() {
            window.__captured.push({
                type    : 'xhr',
                url     : xhr._url,
                method  : xhr._method,
                body    : (typeof body === 'string') ? body : null,
                status  : xhr.status,
                response: xhr.responseText.substring(0, 2000),
                cookies : document.cookie,
                ts      : new Date().toISOString()
            });
        });
        return _origSend.apply(this, arguments);
    };

    console.log('[devtools_capture] インターセプト設定完了');
    """
    driver.execute_script(js_intercept)
    print("[capture] fetch/XHR インターセプト設定完了")

#=====================================================================
def poll_captured(driver, stop_event, interval=1.0):

    while not stop_event.is_set():
        try:
            items = driver.execute_script(
                "return (window.__captured || []).splice(0);"
            )
            if items:
                for item in items:
                    url = item.get("url", "")
                    if any(t in url for t in TARGET_URLS):
                        captured.append(item)
                        print(f"\n[CAPTURED] {item['method']} {url}")
                        print(f"  status : {item.get('status')}")
                        print(f"  body   : {item.get('body', '')[:300]}")
                        print(f"  cookies: {item.get('cookies', '')[:200]}")
                        print(f"  resp   : {item.get('response', '')[:300]}")
        except Exception:
            pass
        time.sleep(interval)

#=========================== メイン処理 ==============================

def main():

    opts = uc.ChromeOptions()
    opts.binary_location = (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    )
    opts.add_argument(r"--user-data-dir=C:\boatrace\tmp\Brave_profile\User Data")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-session-crashed-bubble")

    driver = uc.Chrome(options=opts, , version_main=147, use_subprocess=True)
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
        driver.get(TOP_PAGE)
        time.sleep(2)

        handles_before = set(driver.window_handles)
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "commonHead"))
            )
            btn.click()
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
            print("[login] ログインフォーム送信")
        except TimeoutException:
            print("[login] ログインフォームなし（ログイン済み）")

        try:
            WebDriverWait(driver, 10).until(
                lambda d: set(d.window_handles) != handles_before
            )
            new_handle = (set(driver.window_handles) - handles_before).pop()
            driver.switch_to.window(new_handle)
            print(f"[nav] 投票ウィンドウへ切り替え: {driver.current_url}")
        except TimeoutException:
            pass

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "todayForm"))
        )
        print("[nav] 場選択画面 確認完了")

        # ── インターセプト開始 ──
        start_capture(driver)
        stop_event = threading.Event()
        poll_thread = threading.Thread(
            target=poll_captured, args=(driver, stop_event), daemon=True
        )
        poll_thread.start()

        # ── 手動操作の案内 ──
        print()
        print("=" * 60)
        print(" 【手動操作してください】")
        print("  1. 場選択画面で場ボタンをクリック")
        print("  2. 賭式ボタンを選択（例: 3連複）")
        print("  3. 舟番をクリック（例: 1, 3, 4）")
        print("  4. 金額を入力（例: 1）")
        print("  5. 「ベットリストに追加」ボタンをクリック ← ここが重要")
        print("  ※ 実際の購入確定ボタンは押さないでください")
        print()
        print(" 「ベットリストに追加」を押したら Enter キーを入力してください")
        print("=" * 60)
        input("  → 操作が完了したら Enter を押してください: ")

        # 追加で3秒待機して非同期リクエストを拾う
        time.sleep(3)
        stop_event.set()

        # ── 結果を出力 ──
        print()
        print(f"[result] キャプチャ件数: {len(captured)}")

        # Cookie もまとめて記録
        cookies = driver.get_cookies()
        all_data = {
            "captured_requests": captured,
            "browser_cookies"  : cookies,
            "current_url"      : driver.current_url,
            "page_csrf"        : "",
        }
        # page_source から CSRF を取得
        src = driver.page_source
        import re as re_
        m = re_.search(r'<meta[^>]+name="_csrf_token"[^>]+content="([^"]+)"', src)
        if m:
            all_data["page_csrf"] = m.group(1)

        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"[saved] {OUTPUT_FILE}")
        print()

        # サマリを表示
        if captured:
            print("=== キャプチャしたリクエスト ===")
            for c in captured:
                print(f"  {c['method']} {c['url']}")
                print(f"    status : {c.get('status')}")
                print(f"    body   : {c.get('body','')[:200]}")
                print(f"    cookies: {c.get('cookies','')[:150]}")
                print(f"    resp   : {c.get('response','')[:200]}")
                print()
        else:
            print("[warn] betadd/betcomp のリクエストがキャプチャできませんでした")
            print("  → fetch でも XHR でもない通信方式の可能性があります")
            print("  → captured_requests.json の browser_cookies を確認してください")

        print(f"\n[cookie] Brave のCookie: {len(cookies)} 件")
        for ck in cookies:
            print(f"  {ck['name']:30s} = {ck['value'][:40]}  (domain={ck.get('domain','')})")

    finally:
        time.sleep(2)
        driver.quit()
        print("[end] Brave 終了")

if __name__ == "__main__":
    main()