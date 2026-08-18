import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import json
import requests
import threading
import os
import time
import re
from datetime import datetime
from pathlib  import Path

# --- 設定 ---
# ※実際の運用では環境変数や別ファイルからの読み込みを推奨
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-flash-lite"
LOGS_DIR = path("C:\Users\Yuji\Desktop\Gemini_API\logs")
PROMPTS_FILE = path("C:\Users\Yuji\Desktop\Gemini_API\prompts.json")
MAX_CONTEXT = 10 # 履歴保持数

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

DEFAULT_PROMPTS = {
    "標準": "あなたは有能なアシスタントです。回答は常に最新の情報を考慮してください。",
    "Python 3.13 エキスパート": "あなたはPython 3.13に精通したシニアエンジニアです。最新の文法（Type Hinting, f-strings等）を駆使した、クリーンで効率的なコードを提案してください。",
    "競艇データ解析官": "あなたは競艇（ボートレース）の統計分析スペシャリストです。SQLiteでのクエリ最適化やデータマイニングの視点から助言してください。"
}

def load_system_prompts():
    if not os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_PROMPTS, f, ensure_ascii=False, indent=2)
        return DEFAULT_PROMPTS
    try:
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_PROMPTS

class GeminiWin11App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Thread Manager Ultra - Windows 11 Edition")
        self.root.geometry("1100x850")
        
        self.current_thread_file = None
        self.selected_file_path = None
        self.last_answer = ""
        
        self.system_prompts = load_system_prompts()
        self.selected_system_key = tk.StringVar(value="標準")

        self.setup_ui()
        self.refresh_thread_list()

    def setup_ui(self):
        # メインの左右分割
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg="#cccccc")
        self.paned.pack(fill=tk.BOTH, expand=True)

        # --- サイドバー ---
        self.side_frame = tk.Frame(self.paned, width=280, bg="#f0f0f0")
        self.paned.add(self.side_frame)
        
        tk.Label(self.side_frame, text="[ System Instruction ]", bg="#f0f0f0", font=("Segoe UI", 10, "bold")).pack(pady=10)
        self.prompt_menu = ttk.OptionMenu(self.side_frame, self.selected_system_key, *self.system_prompts.keys())
        self.prompt_menu.pack(padx=15, fill=tk.X)
        
        tk.Button(self.side_frame, text="指示内容を編集", command=self.edit_system_prompts, relief=tk.FLAT, bg="#e1e1e1").pack(pady=5)

        tk.Label(self.side_frame, text="[ Threads ]", bg="#f0f0f0", font=("Segoe UI", 10, "bold")).pack(pady=15)
        tk.Button(self.side_frame, text="+ New Chat", command=self.new_chat, bg="#0078d7", fg="white", font=("Segoe UI", 9, "bold")).pack(pady=5, padx=20, fill=tk.X)
        
        self.thread_listbox = tk.Listbox(self.side_frame, font=("Segoe UI", 9), borderwidth=0, highlightthickness=0)
        self.thread_listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.thread_listbox.bind("<<ListboxSelect>>", self.on_thread_select)
        
        tk.Button(self.side_frame, text="Delete Thread", command=self.delete_thread, fg="#d13438", relief=tk.FLAT).pack(pady=10)

        # --- メインエリア ---
        self.main_frame = tk.Frame(self.paned, bg="white")
        self.paned.add(self.main_frame)

        # ログ表示エリア
        self.txt_log = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, font=("Consolas", 11), bg="#ffffff", borderwidth=0)
        self.txt_log.pack(padx=20, pady=(20, 10), fill=tk.BOTH, expand=True)
        self.txt_log.config(state=tk.DISABLED)

        # 下部ツールバーと入力
        self.bottom_frame = tk.Frame(self.main_frame, bg="white")
        self.bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.toolbar = tk.Frame(self.bottom_frame, bg="white")
        self.toolbar.pack(fill=tk.X)
        
        self.lbl_file_status = tk.Label(self.toolbar, text="No attachment", fg="#666666", bg="white", font=("Segoe UI", 9))
        self.lbl_file_status.pack(side=tk.LEFT)
        tk.Button(self.toolbar, text="Attach File", command=self.select_file, bg="#f3f3f3", relief=tk.GROOVE).pack(side=tk.LEFT, padx=10)
        
        self.btn_save_code = tk.Button(self.toolbar, text="Extract Last Code", command=self.save_last_code, bg="#dff6dd", relief=tk.GROOVE)
        self.btn_save_code.pack(side=tk.RIGHT)

        self.txt_input = scrolledtext.ScrolledText(self.bottom_frame, wrap=tk.WORD, font=("Segoe UI", 11), height=5, borderwidth=1, relief=tk.SOLID)
        self.txt_input.pack(fill=tk.X, pady=10)
        self.txt_input.bind("<Control-Return>", lambda e: self.start_thread())
        
        self.btn_send = tk.Button(self.bottom_frame, text="Send (Ctrl+Enter)", command=self.start_thread, bg="#0078d7", fg="white", font=("Segoe UI", 10, "bold"), height=2)
        self.btn_send.pack(fill=tk.X)

    # --- ロジック層 ---

    def edit_system_prompts(self):
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit System Instructions")
        txt_edit = scrolledtext.ScrolledText(edit_win, width=60, height=20, font=("Consolas", 10))
        txt_edit.pack(padx=20, pady=20)
        txt_edit.insert(tk.END, json.dumps(self.system_prompts, ensure_ascii=False, indent=2))
        
        def save():
            try:
                self.system_prompts = json.loads(txt_edit.get("1.0", tk.END))
                with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.system_prompts, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Success", "Saved successfully.")
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid JSON format: {e}")
        tk.Button(edit_win, text="Save JSON", command=save).pack(pady=10)

    def save_last_code(self):
        if not self.last_answer: return
        codes = re.findall(r"'''(.*?)'''", self.last_answer, re.DOTALL)
        if not codes:
            messagebox.showinfo("Info", "No code blocks found.")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("\n\n# --- New Snippet ---\n\n".join(codes))
            messagebox.showinfo("Success", "Code saved.")

    def start_thread(self):
        if not self.current_thread_file: self.new_chat()
        prompt = self.txt_input.get("1.0", tk.END).strip()
        if not prompt and not self.selected_file_path: return
        
        actual_p = prompt
        display_p = prompt
        if self.selected_file_path:
            try:
                with open(self.selected_file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                actual_p = f"{prompt}\n\n[FILE: {os.path.basename(self.selected_file_path)}]\n{content}"
                display_p = f"{prompt}\n(Attached: {os.path.basename(self.selected_file_path)})"
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return

        self.txt_input.delete("1.0", tk.END)
        self.update_log(f"\n[YOU]\n{display_p}\n\n[GEMINI] Thinking...")
        self.clear_file_selection()
        
        threading.Thread(target=self.get_response, args=(actual_p, display_p), daemon=True).start()

    def get_response(self, actual_p, display_p):
        try:
            with open(self.current_thread_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            history = data.get("history", [])
            
            # API送信用データの構築（履歴のダイエット）
            contents = []
            for item in history[-MAX_CONTEXT:]:
                contents.append({"role": item["role"], "parts": item["parts"]})
            
            # 今回の入力を追加
            contents.append({"role": "user", "parts": [{"text": actual_p}]})
            
            # システム指示の構築（日付注入）
            base_sys = self.system_prompts.get(self.selected_system_key.get(), "")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_system = f"{base_sys}\n\n[System Context: Current Time is {now_str}]"
            
            payload = {
                "system_instruction": {"parts": [{"text": full_system}]},
                "contents": contents
                # 一旦 tools をコメントアウト、または削除
            }
            
            url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={API_KEY.strip()}"
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            res_json = response.json()
            answer = res_json['candidates'][0]['content']['parts'][0]['text']
            
            # 表示用加工
            clean_answer = answer.replace("```", "'''")
            self.last_answer = clean_answer
            
            # --- 履歴の保存ロジック（ここが重要：巨大なファイル内容は履歴から削る） ---
            # 1. ユーザー入力の保存
            user_entry = {"role": "user", "parts": [{"text": actual_p}], "display_text": display_p}
            # ファイルが含まれる場合は、保存用のテキストを「軽量版」に差し替え
            if "[FILE:" in actual_p:
                summary = f"(Previous File Attachment: {display_p.splitlines()[-1]})"
                user_entry["parts"] = [{"text": f"{prompt}\n{summary}"}]
            
            history.append(user_entry)
            history.append({"role": "model", "parts": [{"text": clean_answer}]})
            
            data["history"] = history
            if len(history) <= 2:
                data["title"] = display_p.replace("\n"," ")[:20] + "..."
            
            with open(self.current_thread_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.root.after(0, self.finish_res, clean_answer)
            
        except Exception as e:
            self.root.after(0, self.update_log, f"\n[ERROR] {str(e)}")

    def finish_res(self, answer):
        # ログの「Thinking...」を消して回答を表示
        self.txt_log.config(state=tk.NORMAL)
        # 簡易的な末尾削除ロジック（実際はもっと精密に制御可能）
        self.txt_log.delete("end-14c", tk.END) 
        self.txt_log.insert(tk.END, f"\n{answer}\n\n" + "-"*50 + "\n")
        self.txt_log.config(state=tk.DISABLED)
        self.txt_log.see(tk.END)
        self.refresh_thread_list()

    # --- ヘルパーメソッド ---
    def update_log(self, text):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, text)
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def select_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.selected_file_path = p
            self.lbl_file_status.config(text=f"Ready: {os.path.basename(p)}", fg="#d13438")

    def clear_file_selection(self):
        self.selected_file_path = None
        self.lbl_file_status.config(text="No attachment", fg="#666666")

    def refresh_thread_list(self):
        self.thread_listbox.delete(0, tk.END)
        logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True)
        for f in logs:
            try:
                with open(os.path.join(LOGS_DIR, f), 'r', encoding='utf-8') as j:
                    self.thread_listbox.insert(tk.END, json.load(j).get("title", f))
            except: self.thread_listbox.insert(tk.END, f)

    def new_chat(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_thread_file = os.path.join(LOGS_DIR, f"chat_{ts}.json")
        with open(self.current_thread_file, 'w', encoding='utf-8') as f:
            json.dump({"title": f"New Chat {ts}", "history": []}, f)
        self.refresh_thread_list()
        self.thread_listbox.selection_set(0)
        self.load_thread_to_log()

    def on_thread_select(self, event):
        sel = self.thread_listbox.curselection()
        if not sel: return
        logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True)
        self.current_thread_file = os.path.join(LOGS_DIR, logs[sel[0]])
        self.load_thread_to_log()

    def load_thread_to_log(self):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete(1.0, tk.END)
        if self.current_thread_file:
            try:
                with open(self.current_thread_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get("history", []):
                        role = "[YOU]" if item['role'] == "user" else "[GEMINI]"
                        content = item.get("display_text", item['parts'][0]['text'])
                        self.txt_log.insert(tk.END, f"{role}\n{content}\n\n")
            except: pass
        self.txt_log.config(state=tk.DISABLED)
        self.txt_log.see(tk.END)

    def delete_thread(self):
        sel = self.thread_listbox.curselection()
        if not sel: return
        if messagebox.askyesno("Confirm", "Delete this thread?"):
            logs = sorted([f for f in os.listdir(LOGS_DIR) if f.endswith(".json")], reverse=True)
            os.remove(os.path.join(LOGS_DIR, logs[sel[0]]))
            self.current_thread_file = None
            self.refresh_thread_list()
            self.load_thread_to_log()

if __name__ == "__main__":
    root = tk.Tk()
    app = GeminiWin11App(root)
    root.mainloop()