import json, asyncio, os, re, httpx
import tkinter as tk
from tkinter            import filedialog, messagebox, ttk
from datetime           import datetime
from async_tkinter_loop import async_handler, async_mainloop
from markdown_it        import MarkdownIt
from tkinterweb         import HtmlFrame
from tkinter            import scrolledtext
from mdit_py_plugins.front_matter import front_matter_plugin

GUI, MUI, HNH, CBR = "Yu Gothic UI", "Meiryo UI", "Helvetica Neue Heavy", "Cambria"
GR, SD, RD, RA, BD = "groove", "solid", "ridge", "raised", "bold"
ALL, CT            = "nsew", "center"

# --- 設定 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

LOGS_DIR     = r"C:\boatrace\Management\API_GUI\logs"
PROMPTS_JSON = r"C:\boatrace\Management\API_GUI\prompts.json"
PROMPTS_TEXT = r"C:\boatrace\Management\API_GUI\prompts.txt"
PROFILE_JSON = r"C:\boatrace\Management\API_GUI\profile.json" 
MAX_CONTEXT  = 200

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

DEFAULT_PROMPTS = {"標準": "あなたは有能なAIアシスタントです。",}

#-------------------------------------------------
def load_system_prompts():

    prompt = DEFAULT_PROMPTS.copy() 
    try:
        with open(PROMPTS_JSON, "r", encoding="utf-8") as f:
            prompt = prompt | json.load(f)
    except Exception: pass
    try:
        with open(PROMPTS_TEXT, "r", encoding="utf-8") as f:
            prompt = prompt | {"GPT-4o":f.read()}
    except Exception: pass

    return prompt

#===============================================================================
class MultiLLMWin11App:
    def __init__(self, root):

        self.root = root
        self.root.title("Multi-LLM Thread Manager (Gemini / ChatGPT)")
        self.root.geometry("1300x1300")

        self.current_thread_file = None
        self.selected_file_path  = None
        self.last_answer         = ""
        self.full_log_md         = ""
        self.client              = httpx.AsyncClient(http2=True, timeout=120.0)
        self.system_prompts      = load_system_prompts()
        self.selected_system_key = tk.StringVar(value="標準")
        self.selected_model      = tk.StringVar(value="gemini-3.1-flash-lite")
        self.models              = [ "gemini-3.1-flash-lite",
                                     "gemini-3.1-pro",
                                     "gemini-3-flash",
                                     "gpt-4o",
                                     "gpt-4o-mini",
                                     "o3-mini",                ]

        self.md = MarkdownIt( "commonmark", {        "html":True,
                                              "typographer":False,
                                                   "breaks":True,
                                                 "xhtmlOut":False, }, ).enable("table")

        # CSS設定
        self.base_css = """
        body        { font-family: "メイリオ", "Yu Gothic UI", "sans-serif"; line-height: 1.6;
                      color: #e0e0e0; padding: 15px; background-color: #1e1e1e; font-size: 1.1em; }
        b, strong   { font-weight: bold; color: #67b9ff; }
        h1, h2, h3  { color: #dba400; border-bottom: 1px solid #333; }
        code        { background-color: #101010; color: #f2f2f2; padding: 2px 4px;
                      border-radius: 4px; font-family: 'Consolas', monospace; font-size: 1.1em; }
        pre         { background-color: #101010; border: 1px solid #3c3c3c; padding: 12px;
                      border-radius: 8px; overflow-x: auto; color: #cccccc; }
        table       { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td      { border: 1px solid #3c3c3c; padding: 8px; text-align: left; }
        th          { background-color: #333333; }
        .user-box   { color: #0078d7; font-weight: bold; margin-top: 20px;
                      border-left: 5px solid #0078d7; padding-left: 10px; }
        .assistant-box { color: #c586c0; font-weight: bold; margin-top: 20px;
                         border-left: 5px solid #c586c0; padding-left: 10px;  }
        hr          { border: 0; border-top: 1px solid #333; margin: 20px 0; }
        h3          { margin-top: 25px; padding-left: 10px; }
        """

        self.setup_ui()
        self.refresh_thread_list()

    #---------------------------------------------
    def setup_ui(self):

        # メインの左右分割
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg="#121212")
        self.paned.pack(fill=tk.BOTH, expand=True)

        # --- サイドバー ---
        self.side_frame = tk.Frame(self.paned, width=280, bg="#252526")
        self.paned.add(self.side_frame)

        tk.Label( self.side_frame,
                  text="[ Select Model ]",
                    bg="#353536",
                    fg="#ffffff",
                  font=("Segoe UI", 10, "bold"),).pack(pady=(10, 0))

        self.model_menu = ttk.OptionMenu( self.side_frame,
                                          self.selected_model,
                                          self.selected_model.get(),
                                          *self.models,              )
        self.model_menu.pack(padx=15, pady=5, fill=tk.X)

        tk.Label( self.side_frame,
                  text= "[ System Instruction ]",
                    bg= "#252526",
                    fg= "#ffffff",
                  font= ("Segoe UI", 10, "bold"), ).pack(pady=10)

        self.prompt_menu = ttk.OptionMenu( self.side_frame,
                                           self.selected_system_key,
                                           self.selected_system_key.get(),
                                          *self.system_prompts.keys(),     )
        self.prompt_menu.pack(padx=15, fill=tk.X)

        tk.Button( self.side_frame,
                      text= "Prompt 編集",
                   command= self.edit_system_prompts,
                    relief= "raised",
                        bg= "#3c3c3c",
                        fg= "#ffffff",
                   activebackground="#505050",
                   activeforeground="#ffffff", ).pack(pady=(10, 5))
                   
        # 共通プロファイル 編集ボタン
        tk.Button( self.side_frame,
                      text= "共通指示･ﾌﾟﾛﾌｧｲﾙ 編集",
                   command= self.edit_user_profile,
                    relief= "raised",
                        bg= "#2d4a2e",
                        fg= "#ffffff",
                   activebackground="#3e6b3f",
                   activeforeground="#ffffff", ).pack(pady=(0, 15))

        tk.Label( self.side_frame,
                  text= "[ Threads ]",
                    bg= "#252526",
                    fg= "#ffffff",
                  font= ("Segoe UI", 10, "bold"), ).pack(pady=15)

        tk.Button( self.side_frame,
                      text= "+ New Chat",
                   command= self.new_chat,
                        bg= "#0078d7",
                        fg= "white",
                      font= ("Segoe UI", 9, "bold"),
                    relief= "raised",              ).pack(pady=5, padx=20, fill=tk.X)

        self.thread_listbox = tk.Listbox( self.side_frame,
                                          font= ("Meiryo UI", 11),
                                            bg= "black",
                                            fg= "#cccccc",
                                                 borderwidth= 0,
                                          highlightthickness= 0,
                                            selectbackground= "#37373d", )
        self.thread_listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.thread_listbox.bind("<<ListboxSelect>>", self.on_thread_select)

        tk.Button( self.side_frame,
                      text= "Delete Thread",
                   command= self.delete_thread,
                        fg= "#f1707b",
                        bg= "#252526",
                    relief= "raised",
                   activebackground="#3c3c3c", ).pack(pady=10)

        # --- メインエリア ---
        self.main_frame = tk.Frame(self.paned, bg="#1e1e1e")
        self.paned.add(self.main_frame)

        # ログ表示エリア
        self.html_view = HtmlFrame(self.main_frame)
        self.html_view.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=True)
        self.render_html("Multi-LLM GUI Ready.")

        self.bottom_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # 下部ツールバー
        self.toolbar = tk.Frame(self.bottom_frame, bg="#1e1e1e")
        self.toolbar.pack(fill=tk.X)

        self.lbl_file_status = tk.Label( self.toolbar,
                                         text= "No attachment",
                                           fg= "#aaaaaa",
                                           bg= "#1e1e1e",
                                         font= ("Segoe UI", 9), )
        self.lbl_file_status.pack(side=tk.LEFT)

        tk.Button( self.toolbar,
                      text= "Attach File",
                   command= self.select_file,
                        bg= "#ffb325",
                    relief= "raised",
                   borderwidth=1,             ).pack(side=tk.LEFT, padx=10)

        self.btn_save_code = tk.Button( self.toolbar,
                                               text="Extract Last Code",
                                            command=self.save_last_code,
                                                 bg="#2d4a2e",
                                                 fg="#ffffff",
                                             relief="raised",
                                        borderwidth=1,                   )
        self.btn_save_code.pack(side=tk.RIGHT)

        # テキスト入力エリア
        self.txt_input = tk.Text( self.bottom_frame,
                                              wrap=tk.WORD,
                                              font=("Meiryo UI", 12),
                                                bg="#2d2d2d",
                                                fg="#ffffff",
                                            height=8,
                                            relief=tk.SOLID,
                                       borderwidth=1,
                                  insertbackground="white",           )
        self.txt_input.pack(fill=tk.X, pady=10)
        self.txt_input.bind("<Control-Return>", lambda e:self.send_message())

        self.btn_send = tk.Button( self.bottom_frame,
                                      text= "Send (Ctrl+Enter)",
                                   command= self.send_message,
                                        bg= "#0078d7",
                                        fg= "white",
                                      font= ("Segoe UI", 10, "bold"),
                                    height= 2,
                                    relief= "raised",                 )
        self.btn_send.pack(fill=tk.X)

    #---------------------------------------------
    def preprocess_markdown(self, text:str) -> str:

        return text.replace("'''", "```")

    #---------------------------------------------
    def render_html(self, md_text=None):

        if md_text is None:
            md_text = self.full_log_md

        preprocessed = self.preprocess_markdown(md_text)
        html_body    = self.md.render(preprocessed)
        full_html    = f"<html><style>{self.base_css}</style><body>{html_body}</body></html>"

        with open(r"C:\boatrace\Management\debug_output.html", "w", encoding="utf-8") as f:
            f.write(full_html)

        self.html_view.load_html(full_html)
        self.root.after(50, lambda: self.html_view.yview_moveto(1.0))

    #---------------------------------------------
    async def _stream_gemini(self, current_model, payload, actual_p, prompt, history, data):

        if not GEMINI_API_KEY:
            messagebox.showerror("Error", "環境変数 GEMINI_API_KEY が設定されていません。")
            return

        url = ( f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}"
               f":streamGenerateContent?key={GEMINI_API_KEY}"                              )
        current_res_md = ""

        async with self.client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                self.full_log_md += f"*[API Error {response.status_code}]: {error_body.decode()}*\n"
                self.render_html()
                return

            buffer = ""
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode("utf-8", errors="replace")
                while True:
                    buffer = buffer.lstrip(" \n\r,[")
                    if not buffer:
                        break
                    depth, end_idx, in_str, escape = 0, -1, False, False
                    for i, ch in enumerate(buffer):
                        if escape:
                            escape = False
                            continue
                        if ch == "\\" and in_str:
                            escape = True
                            continue
                        if ch == '"':
                            in_str = not in_str
                            continue
                        if in_str:
                            continue
                        if ch == "{":
                            depth += 1
                        elif ch == "}":
                            depth -= 1
                            if depth == 0:
                                end_idx = i
                                break
                    if end_idx == -1:
                        break

                    json_str = buffer[: end_idx + 1]
                    buffer   = buffer[end_idx + 1 :]

                    try:
                        chunk_data = json.loads(json_str)
                        text_chunk = chunk_data["candidates"][0]["content"]["parts"][0]["text"]
                        current_res_md += text_chunk
                    except (KeyError, IndexError, json.JSONDecodeError):
                        continue

        self._finish_response(current_res_md, actual_p, prompt, history, data, current_model)

    #---------------------------------------------
    async def _stream_openai(self, current_model, payload, actual_p, prompt, history, data):

        if not OPENAI_API_KEY:
            messagebox.showerror("Error", "環境変数 OPENAI_API_KEY が設定されていません。")
            return

        url            = "https://api.openai.com/v1/chat/completions"
        headers        = { "Authorization":f"Bearer {OPENAI_API_KEY}",
                            "Content-Type":"application/json",         }
        current_res_md = ""

        async with self.client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                self.full_log_md += f"*[API Error {response.status_code}]:{error_body.decode()}*\n"
                self.render_html()
                return

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data_str)
                    delta      = chunk_data["choices"][0]["delta"]
                    if "content" in delta and delta["content"]:
                        current_res_md += delta["content"]
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

        self._finish_response(current_res_md, actual_p, prompt, history, data, current_model)

    #---------------------------------------------
    def _finish_response(self, current_res_md, actual_p, prompt, history, data, current_model):

        self.last_answer = current_res_md.replace("```", "'''")
        self.full_log_md += current_res_md + "\n\n<hr>\n"

        user_entry = {
                    "role":"user",
                   "parts":[{"text":actual_p}],
            "display_text":f"{prompt}\n\n*(Attached:{os.path.basename(self.selected_file_path)})*"
                           if self.selected_file_path else prompt,                                 }

        if "[FILE:" in actual_p:
            user_entry["parts"] = [
                {
                    "text": (
                        f"{prompt}\n(Previous File Attachment:"
                        f" {os.path.basename(self.selected_file_path) if self.selected_file_path else 'File'})"
                    )
                }
            ]

        history.append(user_entry)
        history.append({"role":"model", "parts":[{"text":current_res_md}]})
        
        data["history"] = history
        if len(history) <= 2:
            data["title"] = prompt[:20] + "..." if prompt else "File Thread..."

        data["model"]      = current_model
        data["system_key"] = self.selected_system_key.get()

        with open(self.current_thread_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # -------------メイン送信ロジック ------------
    @async_handler
    async def send_message(self):

        if not self.current_thread_file:
            self.new_chat()

        prompt = self.txt_input.get("1.0", tk.END).strip()
        if not prompt and not self.selected_file_path:
            return

        actual_p  = prompt
        display_p = prompt

        if self.selected_file_path:
            try:
                with open(self.selected_file_path, "r", encoding="utf-8", errors="replace",) as f:
                    content = f.read()

                actual_p  = ( f"{prompt}\n\n[FILE:"
                              f" {os.path.basename(self.selected_file_path)}]\n{content}" )
                display_p = f"{prompt}\n\n*(Attached: {os.path.basename(self.selected_file_path)})*"

            except Exception as e:
                messagebox.showerror("Error", str(e))
                return

        self.txt_input.delete("1.0", tk.END)
        self.btn_send.config(state=tk.DISABLED)

        user_md = f"\n<div class='user-box'>[YOU]</div>\n\n{display_p}\n\n"

        self.full_log_md += user_md
        self.render_html()

        current_model = self.selected_model.get()

        with open(self.current_thread_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        history        = data.get("history", [])
        base_sys       = self.system_prompts.get(self.selected_system_key.get(), "").strip()
        common_profile = ""

        if os.path.exists(PROFILE_JSON):
            try:
                with open(PROFILE_JSON, "r", encoding="utf-8") as f:
                    p_data         = json.load(f)
                    common_profile = p_data.get("common_profile", "").strip()
            except:
                pass

        if common_profile:
            base_sys = f"【共通指示・ユーザープロファイル】\n{common_profile}\n\n【個別ロール設定】\n{base_sys}"

        is_openai   = current_model.startswith(("gpt-", "o1-", "o3-"))
        model_label = (f"[GPT:{current_model}]" if is_openai else f"[GEMINI:{current_model}]")

        self.full_log_md += (f"<div class='assistant-box'>{model_label}</div>\n\n")
        self.clear_file_selection()

        try:
            if is_openai:
                messages = []
                if base_sys:
                    messages.append({"role":"system", "content":base_sys})
                for item in history[-MAX_CONTEXT:]:
                    role = ("user" if item["role"] == "user" else "assistant")
                    text = item["parts"][0]["text"]
                    messages.append({"role":role, "content":text})

                messages.append({"role":"user", "content":actual_p})

                payload = {       "model":current_model,
                               "messages":messages,
                                 "stream":True,
                            "temperature":0.7,           }

                await self._stream_openai(current_model, payload, actual_p, prompt, history, data)

            else:
                contents = []
                for item in history[-MAX_CONTEXT:]:
                    contents.append( {  "role":item["role"],
                                       "parts":[{"text":item["parts"][0]["text"]}], } )

                contents.append({"role":"user", "parts":[{"text":actual_p}]})

                payload = {         "contents":contents,
                            "generationConfig":{     "temperature":0.7,
                                                 "maxOutputTokens":8192, }, }
                if base_sys:
                    payload["system_instruction"] = {"parts":[{"text":base_sys}]}

                await self._stream_gemini(current_model, payload, actual_p, prompt, history, data)

        except Exception as e:
            self.full_log_md += f"\n\n*[System Error: {str(e)}]*\n"

        finally:
            self.render_html()
            self.btn_send.config(state=tk.NORMAL)
            self.refresh_thread_list()

    #---------------------------------------------
    def edit_system_prompts(self):

        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit System Instructions (JSON)")
        edit_win.configure(bg="#1e1e1e")

        txt_edit = scrolledtext.ScrolledText( edit_win,
                                                        width= 60,
                                                        height= 20,
                                                          font= ("Consolas", 10),
                                                            bg= "#2d2d2d",
                                                            fg= "#ffffff",
                                              insertbackground="white",           )
        txt_edit.pack(padx=20, pady=20)
        txt_edit.insert(tk.END, json.dumps(self.system_prompts, ensure_ascii=False, indent=2))
        #-----------
        def save():
            try:
                self.system_prompts = json.loads(txt_edit.get("1.0", tk.END))
                with open(PROMPTS_JSON, "w", encoding="utf-8") as f:
                    json.dump(self.system_prompts, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("Success", "Saved.")
                edit_win.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"JSON Error: {e}")
        #-----------
        tk.Button( edit_win,
                      text= "Save JSON",
                   command= save,
                        bg= "#0078d7",
                        fg= "white",
                    relief= tk.FLAT,     ).pack(pady=10)

    #---------------------------------------------
    def edit_user_profile(self):
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Common Instructions & Profile")
        edit_win.configure(bg="#1e1e1e")

        tk.Label( edit_win,
                  text="すべてのチャット（システムプロンプトの先頭）に自動追加される自由記述欄です。",
                  bg="#1e1e1e", fg="#aaaaaa", font=(MUI,9) ).pack(pady=(15,0))

        txt_edit = scrolledtext.ScrolledText( edit_win,
                                                         width= 70,
                                                        height= 15,
                                                          font= (MUI, 11),
                                                            bg= "#2d2d2d",
                                                            fg= "#ffffff",
                                              insertbackground="white",    )
        txt_edit.pack(padx=20, pady=10)

        current_text = ""
        if os.path.exists(PROFILE_JSON):
            try:
                with open(PROFILE_JSON, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                    current_text = p_data.get("common_profile", "")
            except Exception:
                pass

        txt_edit.insert(tk.END, current_text)

        def save_profile():
            text = txt_edit.get("1.0", tk.END).strip()
            try:
                with open(PROFILE_JSON, "w", encoding="utf-8") as f:
                    json.dump({"common_profile": text}, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("Success", "共通プロファイルを保存しました。")
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Save Error: {e}")

        tk.Button( edit_win,
                      text= "Save Profile",
                   command= save_profile,
                        bg= "#2d4a2e",
                        fg= "white",
                    relief= tk.FLAT,
                    height= 2, width= 15    ).pack(pady=(0, 15))

    #---------------------------------------------
    def save_last_code(self):

        if not self.last_answer:
            return

        codes = re.findall(r"'''(.*?)'''", self.last_answer, re.DOTALL)
        if not codes:
            codes = re.findall(r"```(.*?)```", self.last_answer, re.DOTALL)

        if not codes:
            messagebox.showinfo("Info", "No code blocks found.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")], )

        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n\n# --- Extracted Code ---\n\n".join(codes))
            messagebox.showinfo("Success", "Saved.")

    # --------------- スレッド管理 ---------------
    def select_file(self):

        p = filedialog.askopenfilename()
        if p:
            self.selected_file_path = p
            self.lbl_file_status.config(text=f"Ready: {os.path.basename(p)}", fg="#f1707b")

    #---------------------------------------------
    def clear_file_selection(self):

        self.selected_file_path = None
        self.lbl_file_status.config(text="No attachment", fg="#aaaaaa")

    #---------------------------------------------
    def refresh_thread_list(self):

        self.thread_listbox.delete(0, tk.END)
        logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True,)

        for f in logs:
            try:
                with open(os.path.join(LOGS_DIR, f), "r", encoding="utf-8") as j:
                    self.thread_listbox.insert(tk.END, json.load(j).get("title", f))
            except:
                self.thread_listbox.insert(tk.END, f)

    #---------------------------------------------
    def new_chat(self):

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_thread_file = os.path.join(LOGS_DIR, f"chat_{ts}.json")

        initial_data = {
            "title": f"New Chat {ts}",
            "model": self.selected_model.get(),
            "system_key": self.selected_system_key.get(),
            "history": []
        }
        
        with open(self.current_thread_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
        self.refresh_thread_list()
        self.full_log_md = ""
        self.render_html("New Thread Started.")

    #---------------------------------------------
    def on_thread_select(self, event):

        sel = self.thread_listbox.curselection()
        if not sel:
            return

        logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True,)
        self.current_thread_file = os.path.join(LOGS_DIR, logs[sel[0]])
        self.load_thread_to_log()

    #---------------------------------------------
    def load_thread_to_log(self):

        self.full_log_md = ""
        if self.current_thread_file:
            try:
                with open(self.current_thread_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    saved_model = data.get("model")
                    if saved_model and saved_model in self.models:
                        self.selected_model.set(saved_model)
                        
                    saved_sys_key = data.get("system_key")
                    if saved_sys_key and saved_sys_key in self.system_prompts.keys():
                        self.selected_system_key.set(saved_sys_key)

                    for item in data.get("history", []):
                        role_label = (   "[YOU]" if item["role"] == "user" else "[ASSISTANT]")
                        role_class = ("user-box" if item["role"] == "user" else "assistant-box")
                        content    = item.get("display_text", item["parts"][0]["text"])
                        self.full_log_md += f"<div class='{role_class}'>{role_label}</div>\n\n{content}\n\n"
                        if item["role"] != "user":
                            self.full_log_md += "<hr>\n"
            except:
                pass

        self.render_html()

    #---------------------------------------------
    def delete_thread(self):

        sel = self.thread_listbox.curselection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete this thread?"):
            logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True,)
            os.remove(os.path.join(LOGS_DIR, logs[sel[0]]))
            self.current_thread_file = None
            self.refresh_thread_list()
            self.full_log_md = ""
            self.render_html("Thread Deleted.")

#===============================================================================
if __name__ == "__main__":

    root = tk.Tk()
    root.configure(bg="#1e1e1e")
    app = MultiLLMWin11App(root)
    async_mainloop(root)