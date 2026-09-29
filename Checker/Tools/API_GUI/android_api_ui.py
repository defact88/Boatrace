import flet as ft
import json
import os
import httpx
from datetime import datetime

# --- APIキーの設定 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- 保存先ディレクトリの設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
LOGS_DIR = os.path.join(BASE_DIR, "logs")
PROMPTS_JSON = os.path.join(BASE_DIR, "prompts.json")
MAX_CONTEXT = 20

os.makedirs(LOGS_DIR, exist_ok=True)

DEFAULT_PROMPTS = {"標準": "あなたは有能なアシスタントです。回答は常に最新の情報を考慮してください。"}

def load_system_prompts():
    prompts = DEFAULT_PROMPTS.copy()
    if os.path.exists(PROMPTS_JSON):
        try:
            with open(PROMPTS_JSON, "r", encoding="utf-8") as f:
                prompts.update(json.load(f))
        except Exception:
            pass
    return prompts

async def main(page: ft.Page):
    page.title = "Multi-LLM App"
    page.theme_mode = ft.ThemeMode.DARK
    
    # ウィンドウサイズの指定
    page.window.width = 400
    page.window.height = 800

    # 状態管理
    state = {
        "current_thread_file": None,
        "history": [],
        "system_prompts": load_system_prompts()
    }
    
    client = httpx.AsyncClient(http2=True, timeout=120.0)

    # --- UIコンポーネント ---
    chat_log = ft.ListView(expand=True, spacing=15, auto_scroll=True, padding=10)
    txt_input = ft.TextField(hint_text="メッセージを入力", expand=True, multiline=True, min_lines=1, max_lines=4)
    btn_send = ft.IconButton(icon=ft.Icons.SEND, icon_color="#0078d7")

    model_dropdown = ft.Dropdown(
        label="Select Model",
        options=[
            ft.dropdown.Option("gemini-3.1-flash-lite"),
            ft.dropdown.Option("gemini-3.1-pro"),
            ft.dropdown.Option("gpt-4o"),
            ft.dropdown.Option("gpt-4o-mini"),
        ],
        value="gemini-3.1-flash-lite",
    )
    
    prompt_dropdown = ft.Dropdown(
        label="System Instruction",
        options=[ft.dropdown.Option(k) for k in state["system_prompts"].keys()],
        value="標準",
    )

    thread_list_ui = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, expand=True)

    # --- ドロワーの開閉関数（同期関数で定義し、drawer.update() を実行） ---
# --- ドロワーの開閉関数 ---
    def open_drawer(e):
        page.open(drawer)

    def close_drawer():
        page.close(drawer)

    def refresh_thread_list():
        thread_list_ui.controls.clear()
        logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True)
        for f in logs:
            filepath = os.path.join(LOGS_DIR, f)
            title = f
            try:
                with open(filepath, "r", encoding="utf-8") as j:
                    title = json.load(j).get("title", f)
            except:
                pass
            
            thread_list_ui.controls.append(
                ft.ListTile(
                    title=ft.Text(title, size=14, max_lines=1),
                    on_click=lambda e, fp=filepath: page.run_task(load_thread, fp)
                )
            )
        page.update()

    async def start_new_thread(e=None):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        state["current_thread_file"] = os.path.join(LOGS_DIR, f"chat_{ts}.json")
        state["history"] = []
        initial_data = {
            "title": f"New Chat {ts}",
            "model": model_dropdown.value,
            "system_key": prompt_dropdown.value,
            "history": []
        }
        with open(state["current_thread_file"], "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        
        chat_log.controls.clear()
        refresh_thread_list()
        close_drawer()

    async def load_thread(filepath):
        state["current_thread_file"] = filepath
        chat_log.controls.clear()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if data.get("model"): model_dropdown.value = data["model"]
            if data.get("system_key"): prompt_dropdown.value = data["system_key"]
            state["history"] = data.get("history", [])
            
            for item in state["history"]:
                role = "YOU" if item["role"] == "user" else item.get("model", "ASSISTANT")
                bgcolor = "#1e3a5f" if role == "YOU" else "#252526"
                text = item["parts"][0]["text"]
                
                chat_log.controls.append(
                    ft.Container(
                        content=ft.Markdown(f"**[{role}]**\n\n{text}", selectable=True),
                        bgcolor=bgcolor, padding=15, border_radius=10
                    )
                )
        except Exception as ex:
            chat_log.controls.append(ft.Text(f"Load Error: {ex}"))
            
        page.update()
        close_drawer()

    async def delete_thread(e):
        if state["current_thread_file"] and os.path.exists(state["current_thread_file"]):
            os.remove(state["current_thread_file"])
            state["current_thread_file"] = None
            chat_log.controls.clear()
            refresh_thread_list()
        close_drawer()

    async def send_message(e):
        prompt = txt_input.value.strip()
        if not prompt: return
        
        if not state["current_thread_file"]:
            await start_new_thread()
            
        txt_input.value = ""
        btn_send.disabled = True
        
        chat_log.controls.append(
            ft.Container(
                content=ft.Markdown(f"**[YOU]**\n\n{prompt}"),
                bgcolor="#1e3a5f", padding=15, border_radius=10
            )
        )
        page.update()
        
        current_model = model_dropdown.value
        sys_prompt = state["system_prompts"].get(prompt_dropdown.value, "")
        is_openai = current_model.startswith("gpt")
        
        assistant_md = ft.Markdown(f"**[{current_model}]**\n\n", selectable=True)
        chat_log.controls.append(
            ft.Container(
                content=assistant_md,
                bgcolor="#252526", padding=15, border_radius=10
            )
        )
        page.update()
        
        state["history"].append({"role": "user", "parts": [{"text": prompt}]})
        response_text = ""
        
        try:
            if is_openai:
                messages = []
                if sys_prompt: messages.append({"role": "system", "content": sys_prompt})
                for h in state["history"][-MAX_CONTEXT:]:
                    role = "user" if h["role"] == "user" else "assistant"
                    messages.append({"role": role, "content": h["parts"][0]["text"]})
                    
                payload = {"model": current_model, "messages": messages, "stream": True, "temperature": 0.7}
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
                
                async with client.stream("POST", "https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            d = line[6:].strip()
                            if d == "[DONE]": break
                            try:
                                delta = json.loads(d)["choices"][0]["delta"]
                                if "content" in delta:
                                    response_text += delta["content"]
                                    assistant_md.value = f"**[{current_model}]**\n\n{response_text}"
                                    page.update()
                            except: pass
            else:
                contents = []
                for h in state["history"][-MAX_CONTEXT:]:
                    contents.append({"role": h["role"], "parts": [{"text": h["parts"][0]["text"]}]})
                    
                payload = {"contents": contents, "generationConfig": {"temperature": 0.7}}
                if sys_prompt: payload["system_instruction"] = {"parts": [{"text": sys_prompt}]}
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:streamGenerateContent?key={GEMINI_API_KEY}"
                
                async with client.stream("POST", url, json=payload) as resp:
                    buffer = ""
                    async for chunk in resp.aiter_bytes():
                        buffer += chunk.decode("utf-8", errors="replace")
                        while True:
                            buffer = buffer.lstrip(" \n\r,[")
                            if not buffer: break
                            depth, end_idx, in_str, escape = 0, -1, False, False
                            for i, ch in enumerate(buffer):
                                if escape: escape = False; continue
                                if ch == "\\" and in_str: escape = True; continue
                                if ch == '"': in_str = not in_str; continue
                                if in_str: continue
                                if ch == "{": depth += 1
                                elif ch == "}":
                                    depth -= 1
                                    if depth == 0:
                                        end_idx = i; break
                            if end_idx == -1: break
                            
                            json_str = buffer[: end_idx + 1]
                            buffer = buffer[end_idx + 1:]
                            try:
                                chunk_data = json.loads(json_str)
                                text_chunk = chunk_data["candidates"][0]["content"]["parts"][0]["text"]
                                response_text += text_chunk
                                assistant_md.value = f"**[{current_model}]**\n\n{response_text}"
                                page.update()
                            except: pass

            state["history"].append({"role": "model", "model": current_model, "parts": [{"text": response_text}]})
            
            with open(state["current_thread_file"], "r", encoding="utf-8") as f:
                data = json.load(f)
            data["history"] = state["history"]
            data["model"] = current_model
            data["system_key"] = prompt_dropdown.value
            if len(state["history"]) <= 2:
                data["title"] = prompt[:20] + "..."
                
            with open(state["current_thread_file"], "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as ex:
            assistant_md.value += f"\n\n**[Error]** {str(ex)}"
            page.update()
            
        btn_send.disabled = False
        refresh_thread_list()
        page.update()

    btn_send.on_click = send_message

    # --- ドロワー（引き出しメニュー）の構築 ---
    drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Text("Settings", weight=ft.FontWeight.BOLD),
                    model_dropdown,
                    prompt_dropdown,
                    ft.Divider(),
                    ft.Button("+ New Chat", on_click=start_new_thread, bgcolor="#0078d7", color="white"),
                    ft.Button("Delete Thread", on_click=delete_thread, bgcolor="#8b0000", color="white"),
                    ft.Divider(),
                    ft.Text("Threads", weight=ft.FontWeight.BOLD),
                    ft.Container(content=thread_list_ui, height=300),
                ], spacing=15)
            )
        ]
    )
    
    # ページにドロワーをセット

    # --- アプリの基本レイアウト ---
    page.appbar = ft.AppBar(
        title=ft.Text("Multi-LLM App", size=18),
        leading=ft.IconButton(ft.Icons.MENU, on_click=open_drawer),
        bgcolor="#252526"
    )

    page.add(
        ft.Column([
            chat_log,
            ft.Row([txt_input, btn_send], alignment=ft.MainAxisAlignment.END)
        ], expand=True)
    )

    # 初期化処理
    refresh_thread_list()

if __name__ == "__main__":
    ft.run(main, host="0.0.0.0", port=8550, view=ft.AppView.WEB_BROWSER)