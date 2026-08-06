"""
ai_model_manager.py - Desktop GUI to manage AI providers (base URL / API key /
models), test connections, browse models, and run a live model tester.

Requires only Python 3 stdlib + requests.
"""
import json
import os
import queue
import shutil
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from api_client import (
    APIError,
    test_connection,
    list_models,
    chat,
    chat_stream,
    resolve_format,
    normalize_base,
)
import claude_profiles as cp
import history as hist
import omniroute_service as omni
import gateway_server as gw

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

FORMATS = ["auto", "openai", "anthropic"]

DEFAULT_CONFIG = {
    "providers": [
        {
            "name": "Ollama (Local)",
            "format": "openai",
            "base_url": "http://127.0.0.1:11434",
            "api_key": "",
            "default_model": "",
            "notes": "Local Ollama server (OpenAI-compatible).",
        },
        {
            "name": "Claude Code Router",
            "format": "auto",
            "base_url": "http://127.0.0.1:3456",
            "api_key": "ccr-dummy",
            "default_model": "",
            "notes": "claude-code-router local proxy.",
        },
        {
            "name": "Omniroute (Claude)",
            "format": "anthropic",
            "base_url": "http://localhost:20128",
            "api_key": "omniroute-proxy",
            "default_model": "antigravity/claude-sonnet-4-6",
            "notes": "Omniroute proxy (Anthropic-compatible).",
        },
    ]
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


class Worker:
    """Run network calls in a background thread and deliver results to the UI."""

    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self._poll()

    def _poll(self):
        try:
            while True:
                callback, result, error = self.queue.get_nowait()
                try:
                    callback(result, error)
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def submit(self, fn, on_done, *args, **kwargs):
        """Run fn(*args, **kwargs) off-thread; call on_done(result, error) on the UI thread."""
        def _run():
            try:
                result = fn(*args, **kwargs)
                self.queue.put((on_done, result, None))
            except Exception as e:
                self.queue.put((on_done, None, e))
        threading.Thread(target=_run, daemon=True).start()



class ModelTestDialog(tk.Toplevel):
    """Dedicated window to test a specific model with a custom prompt."""

    def __init__(self, parent, base, key, fmt, model):
        super().__init__(parent)
        self.title("Test Model: %s" % model)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.geometry("620x520")
        self.minsize(500, 400)

        self.base = base
        self.key = key
        self.fmt = fmt
        self.model = model

        # Info bar (read-only)
        info = ttk.Frame(self, padding=(12, 10, 12, 6))
        info.pack(fill="x")
        ttk.Label(info, text="Provider: %s" % base, foreground="gray").pack(anchor="w")
        ttk.Label(info, text="Model: %s" % model, font=("", 9, "bold")).pack(anchor="w")
        ttk.Label(info, text="Format: %s" % fmt, foreground="gray").pack(anchor="w")

        # Prompt input
        mid = ttk.Frame(self, padding=(12, 6, 12, 6))
        mid.pack(fill="both", expand=True)
        ttk.Label(mid, text="Enter text to test:").pack(anchor="w")
        self.prompt_text = scrolledtext.ScrolledText(mid, height=8, wrap="word")
        self.prompt_text.pack(fill="both", expand=True, pady=4)
        self.prompt_text.insert("1.0", "Hello! Please introduce yourself in one sentence.")

        # Controls
        ctrl = ttk.Frame(self, padding=(12, 6, 12, 6))
        ctrl.pack(fill="x")
        ttk.Label(ctrl, text="Max tokens:").pack(side="left")
        self.var_max = tk.StringVar(value="128")
        ttk.Spinbox(ctrl, from_=1, to=4096, increment=32,
                    textvariable=self.var_max, width=8).pack(side="left", padx=4)
        ttk.Button(ctrl, text="Run Test", command=self._run_test).pack(side="left", padx=8)
        self.status = tk.StringVar(value="")
        ttk.Label(ctrl, textvariable=self.status, foreground="gray").pack(side="left", padx=12)

        # Response
        bottom = ttk.Frame(self, padding=(12, 6, 12, 12))
        bottom.pack(fill="both", expand=True)
        ttk.Label(bottom, text="Response:").pack(anchor="w")
        self.response = scrolledtext.ScrolledText(bottom, height=10, wrap="word")
        self.response.pack(fill="both", expand=True)

    def _run_test(self):
        prompt = self.prompt_text.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Empty", "Enter a prompt first.", parent=self)
            return
        try:
            max_tokens = int(self.var_max.get())
        except ValueError:
            messagebox.showerror("Bad value", "Max tokens must be a number.", parent=self)
            return

        self.status.set("Running…")
        self.response.delete("1.0", "end")
        self.response.insert("1.0", "Thinking…")
        self.update_idletasks()

        def _job():
            try:
                return chat({"name": "test", "format": self.fmt,
                             "base_url": self.base, "api_key": self.key},
                            self.model, prompt, max_tokens, 0.7, 60)
            except Exception as e:
                return None, str(e)

        def _done(result, error):
            self.response.delete("1.0", "end")
            if error:
                self.status.set("✘ Failed")
                self.response.insert("1.0", "Error:\n%s" % str(error)[:500])
                return
            text, raw, usage, latency, fmt_used = result
            self.status.set("✔ OK · %.2fs · %s" % (latency, fmt_used))
            self.response.insert("1.0", text or "(no response)")
            usage_str = ""
            if usage:
                tin = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
                tout = usage.get("output_tokens") or usage.get("completion_tokens") or 0
                usage_str = "\n\n[Tokens: %d in / %d out]" % (tin, tout)
            self.response.insert("end", usage_str)

        import threading
        def _run():
            res, err = _job()
            self.after(0, lambda: _done(res, err))

        threading.Thread(target=_run, daemon=True).start()


class ProviderDialog(tk.Toplevel):
    """Modal dialog to add or edit a provider."""

    def __init__(self, parent, provider=None, title="Provider"):
        super().__init__(parent)
        self.title(title)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.result = None

        self.var_format = tk.StringVar(value="auto")
        self.var_name = tk.StringVar()
        self.var_base = tk.StringVar()
        self.var_key = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_notes = tk.StringVar()
        self.var_temp = tk.StringVar(value="0.7")
        self.var_max = tk.StringVar(value="1024")
        self._fetched_models = []
        self._test_result = None

        if provider:
            self.var_name.set(provider.get("name", ""))
            self.var_base.set(provider.get("base_url", ""))
            self.var_key.set(provider.get("api_key", ""))
            self.var_model.set(provider.get("default_model", ""))
            self.var_notes.set(provider.get("notes", ""))
            self.var_format.set(provider.get("format", "auto"))
            if provider.get("default_temperature"):
                self.var_temp.set(str(provider["default_temperature"]))
            if provider.get("default_max_tokens"):
                self.var_max.set(str(provider["default_max_tokens"]))

        # Fixed-size buttons at bottom (always visible)
        btns = ttk.Frame(self, padding=(12, 8, 12, 12))
        btns.pack(fill="x", side="bottom")
        ttk.Button(btns, text="Save", command=self._save, default="active").pack(side="right", padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right", padx=6)
        ttk.Button(btns, text="Test Connection", command=self._test_connection).pack(side="left", padx=6)
        self.test_status = tk.StringVar(value="")
        ttk.Label(btns, textvariable=self.test_status, foreground="gray").pack(side="left", padx=12)

        # Scrollable fields
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, side="top")

        canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = ttk.Frame(canvas, padding=12)
        canvas_window = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_body_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=e.width)

        body.bind("<Configure>", _on_body_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        pad = {"padx": 6, "pady": 4, "sticky": "w"}
        row = 0

        ttk.Label(body, text="Display name:").grid(row=row, column=0, **pad)
        ttk.Entry(body, textvariable=self.var_name, width=44).grid(row=row, column=1, **pad)
        row += 1

        ttk.Label(body, text="API format:").grid(row=row, column=0, **pad)
        ttk.Combobox(body, textvariable=self.var_format, values=FORMATS,
                     state="readonly", width=42).grid(row=row, column=1, **pad)
        ttk.Label(body, text="(auto = try both)", foreground="gray").grid(row=row, column=2, **pad)
        row += 1

        ttk.Label(body, text="Base URL:").grid(row=row, column=0, **pad)
        ttk.Entry(body, textvariable=self.var_base, width=44).grid(row=row, column=1, **pad)
        ttk.Label(body, text="e.g. http://127.0.0.1:11434", foreground="gray").grid(row=row, column=2, **pad)
        row += 1

        ttk.Label(body, text="API key:").grid(row=row, column=0, **pad)
        self.key_entry = ttk.Entry(body, textvariable=self.var_key, width=44, show="*")
        self.key_entry.grid(row=row, column=1, **pad)
        self._key_visible = False
        ttk.Button(body, text="Show", command=self._toggle_key).grid(row=row, column=2, **pad)
        row += 1

        ttk.Label(body, text="Default chat model:").grid(row=row, column=0, **pad)
        model_row = ttk.Frame(body)
        model_row.grid(row=row, column=1, sticky="w")
        self.model_cb = ttk.Combobox(model_row, textvariable=self.var_model,
                                     state="normal", width=34)
        self.model_cb.pack(side="left")
        ttk.Button(model_row, text="Fetch", command=self._fetch_models_for_dialog).pack(side="left", padx=4)
        ttk.Button(model_row, text="Test Model", command=self._open_model_test_window).pack(side="left", padx=4)
        row += 1

        ttk.Label(body, text="(used for chat / completions)",
                  foreground="gray").grid(row=row, column=0, columnspan=3, sticky="w", padx=6)
        row += 1

        ttk.Label(body, text="Default temperature:").grid(row=row, column=0, **pad)
        ttk.Spinbox(body, from_=0.0, to=2.0, increment=0.1,
                    textvariable=self.var_temp, width=8).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(body, text="Default max tokens:").grid(row=row, column=0, **pad)
        ttk.Spinbox(body, from_=1, to=128000, increment=256,
                    textvariable=self.var_max, width=10).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        ttk.Label(body, text="Notes:").grid(row=row, column=0, **pad)
        ttk.Entry(body, textvariable=self.var_notes, width=44).grid(row=row, column=1, **pad)
        row += 1

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

        # Set proper initial size
        self.update_idletasks()
        self.minsize(520, 480)
        self.geometry("560x520")

    def _toggle_key(self):
        self._key_visible = not self._key_visible
        self.key_entry.config(show="" if self._key_visible else "*")

    def _open_model_test_window(self):
        base = self.var_base.get().strip()
        key = self.var_key.get().strip()
        fmt = self.var_format.get()
        model = self.var_model.get().strip()
        if not base or not model:
            messagebox.showwarning("Missing info",
                                   "Enter Base URL and select a model first.", parent=self)
            return
        ModelTestDialog(self, base, key, fmt, model)

    def _fetch_models_for_dialog(self):
        base = self.var_base.get().strip()
        key = self.var_key.get().strip()
        fmt = self.var_format.get()
        if not base:
            messagebox.showwarning("Missing URL", "Enter a Base URL first.", parent=self)
            return
        self.model_cb.set("Fetching…")
        self.update_idletasks()

        def _job():
            try:
                return list_models(base, key, fmt), None
            except Exception as e:
                return None, e

        def _done(result, error):
            if error:
                self.model_cb.set("")
                messagebox.showerror("Fetch failed", str(error), parent=self)
                return
            models = result or []
            self._fetched_models = models
            self.model_cb["values"] = models
            if models:
                self.model_cb.set(models[0])
            else:
                self.model_cb.set("(no models returned)")

        import threading
        def _run():
            res, err = _job()
            # Schedule UI update on main thread
            self.after(0, lambda: _done(res, err))

        threading.Thread(target=_run, daemon=True).start()

    def _test_connection(self):
        base = self.var_base.get().strip()
        key = self.var_key.get().strip()
        fmt = self.var_format.get()
        if not base:
            messagebox.showwarning("Missing URL", "Enter a Base URL first.", parent=self)
            return
        self.test_status.set("Testing connection…")
        self.update_idletasks()

        def _job():
            try:
                return test_connection(base, key, fmt)
            except Exception as e:
                return None, str(e)

        def _done(result, error):
            if error:
                self.test_status.set("✘ Failed")
                messagebox.showerror("Connection failed", str(error), parent=self)
                return
            ok, fmt, models, err = result
            if ok:
                self.test_status.set("✔ Connected (%s, %d models)" % (fmt, len(models)))
                messagebox.showinfo("Connection OK",
                                    "Connected successfully!\n\nFormat: %s\nModels: %d"
                                    % (fmt, len(models)), parent=self)
            else:
                self.test_status.set("✘ Failed")
                messagebox.showerror("Connection failed", err or "unknown error", parent=self)

        import threading
        def _run():
            res, err = _job()
            self.after(0, lambda: _done(res, err))

        threading.Thread(target=_run, daemon=True).start()

    def _test_selected_model(self):
        base = self.var_base.get().strip()
        key = self.var_key.get().strip()
        fmt = self.var_format.get()
        model = self.var_model.get().strip()
        if not base:
            messagebox.showwarning("Missing URL", "Enter a Base URL first.", parent=self)
            return
        if not model:
            messagebox.showwarning("No model", "Select or enter a model first.", parent=self)
            return
        self.test_status.set("Testing model '%s'…" % model)
        self.update_idletasks()

        def _job():
            try:
                text, raw, usage, latency, fmt_used = chat(
                    {"name": "test", "format": fmt, "base_url": base, "api_key": key},
                    model, "Hi, please reply with just 'OK'.", 16, 0.7, 30)
                return (text, raw, usage, latency, fmt_used), None
            except Exception as e:
                return None, str(e)

        def _done(result, error):
            if error:
                self.test_status.set("✘ Model test failed")
                # Provide actionable hints for common errors
                hint = ""
                err_lower = (error or "").lower()
                if "403" in err_lower or "permission" in err_lower:
                    hint = ("\n\nPossible fixes:\n"
                            "• Check that the API key is valid and not expired\n"
                            "• Check that the model name is correct (use Fetch to see available models)\n"
                            "• The model may require a different API key or subscription\n"
                            "• Try 'Fetch' to get the exact model ID from the provider")
                elif "404" in err_lower or "not found" in err_lower:
                    hint = ("\n\nPossible fixes:\n"
                            "• Model name may be incorrect or has been renamed\n"
                            "• Use 'Fetch' to see the exact available models\n"
                            "• Check the provider's documentation for the correct model ID")
                elif "401" in err_lower or "unauthorized" in err_lower:
                    hint = ("\n\nPossible fixes:\n"
                            "• API key is invalid or expired\n"
                            "• Check the API key in the provider settings")
                messagebox.showerror("Model test failed",
                                     "%s%s" % (str(error)[:300], hint), parent=self)
                return
            text, raw, usage, latency, fmt_used = result
            self.test_status.set("✔ Model OK (%.2fs)" % latency)
            messagebox.showinfo("Model test OK",
                                "Model '%s' responded in %.2fs\n\nResponse:\n%s"
                                % (model, latency, text[:200]), parent=self)

        import threading
        def _run():
            res, err = _job()
            self.after(0, lambda: _done(res, err))

        threading.Thread(target=_run, daemon=True).start()

    def _save(self):
        name = self.var_name.get().strip()
        base = self.var_base.get().strip()
        if not name or not base:
            messagebox.showerror("Missing info",
                                 "Display name and Base URL are required.", parent=self)
            return
        self.result = {
            "name": name,
            "format": self.var_format.get(),
            "base_url": base,
            "api_key": self.var_key.get().strip(),
            "default_model": self.var_model.get().strip(),
            "default_temperature": self.var_temp.get().strip(),
            "default_max_tokens": self.var_max.get().strip(),
            "notes": self.var_notes.get().strip(),
        }
        self.destroy()


class App:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.worker = Worker(root)
        self.model_cache = {}   # provider name -> list of models
        self.status_cache = {}  # provider name -> ("ok"|"fail", detail)
        self._busy = set()
        self._tray_win = None
        self._stream_job = None

        root.title("AI Model Manager")
        root.geometry("980x720")
        root.minsize(860, 580)

        self._build_toolbar()
        self._build_notebook()
        self._refresh_provider_tree()
        self._refresh_tester_combos()
        self._refresh_claude_tab()
        self._refresh_stats()
        self._log("Ready. Add a provider or test an existing connection.")

        root.protocol("WM_DELETE_WINDOW", self._on_close)
        for seq in ("<Control-Alt-m>", "<Control-Alt-M>"):
            root.bind(seq, lambda e: self._open_quick_switcher())

        # 1) Auto-test all providers shortly after launch (feature #1).
        root.after(900, self._auto_test_launch)

    def _auto_test_launch(self):
        if not self.config.get("providers"):
            return
        self._log("Auto-testing %d provider(s) on launch…" % len(self.config["providers"]))
        for p in list(self.config["providers"]):
            self._test(p)

    # ---------- UI construction ----------
    def _build_toolbar(self):
        bar = ttk.Frame(self.root, padding=(8, 6))
        bar.pack(fill="x")
        ttk.Button(bar, text="+ Add Provider", command=self._add_provider).pack(side="left", padx=3)
        ttk.Button(bar, text="Edit Provider", command=self._edit_provider).pack(side="left", padx=3)
        ttk.Button(bar, text="Delete Provider", command=self._delete_provider).pack(side="left", padx=3)
        ttk.Button(bar, text="Test Selected", command=self._test_selected).pack(side="left", padx=3)
        ttk.Button(bar, text="Test All", command=self._test_all).pack(side="left", padx=3)
        ttk.Button(bar, text="Fetch Models", command=self._fetch_models).pack(side="left", padx=3)
        ttk.Button(bar, text="Save Config", command=self._save).pack(side="left", padx=3)
        ttk.Button(bar, text="Quick Switch", command=self._open_quick_switcher).pack(side="left", padx=3)
        ttk.Button(bar, text="Omniroute", command=self._open_omniroute).pack(side="left", padx=3)
        ttk.Button(bar, text="Presets", command=self._open_presets).pack(side="left", padx=3)
        ttk.Button(bar, text="Gateway", command=self._open_gateway).pack(side="left", padx=3)
        ttk.Button(bar, text="Import", command=self._import_config).pack(side="left", padx=3)
        ttk.Button(bar, text="Export", command=self._export_config).pack(side="left", padx=3)
        ttk.Button(bar, text="Reload Config", command=self._reload).pack(side="left", padx=3)
        ttk.Button(bar, text="Reset All", command=self._reset_all).pack(side="left", padx=3)
        ttk.Button(bar, text="Config Folder", command=self._open_folder).pack(side="right", padx=3)

    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self._build_providers_tab()
        self._build_models_tab()
        self._build_tester_tab()
        self._build_logs_tab()
        self._build_claude_tab()
        self._build_stats_tab()
        self._build_bench_tab()
        self._build_gateway_tab()

    def _build_providers_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Providers")

        cols = ("name", "format", "base", "key", "models", "status")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse")
        headers = {"name": "Name", "format": "Format", "base": "Base URL",
                   "key": "API Key", "models": "Models", "status": "Status"}
        widths = {"name": 170, "format": 90, "base": 240, "key": 150,
                  "models": 90, "status": 190}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.tag_configure("ok", foreground="#0a7d33")
        self.tree.tag_configure("fail", foreground="#c00")
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        bot = ttk.Frame(tab)
        bot.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(bot, text="Tip: select a provider then use the toolbar. "
                            "Green ✔ = connected, red ✘ = failed.",
                  foreground="gray").pack(side="left")
        self.prov_pass_btn = ttk.Menubutton(bot, text="Pass to ▾")
        self.prov_pass_menu = tk.Menu(self.prov_pass_btn, tearoff=0)
        self.prov_pass_btn["menu"] = self.prov_pass_menu
        self.prov_pass_btn.pack(side="right", padx=4)
        self._rebuild_prov_pass_menu()

    def _build_models_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Models")

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Provider:").pack(side="left")
        self.models_provider = ttk.Combobox(top, state="readonly", width=40)
        self.models_provider.pack(side="left", padx=6)
        ttk.Button(top, text="Fetch", command=self._fetch_models_from_tab).pack(side="left", padx=4)
        ttk.Button(top, text="Copy Selected", command=self._copy_selected_model).pack(side="left", padx=4)

        self.models_list = ttk.Treeview(tab, columns=("m",), show="headings")
        self.models_list.heading("m", text="Available Models")
        self.models_list.column("m", width=600)
        self.models_list.pack(fill="both", expand=True, padx=6, pady=6)
        self.models_list.bind("<Double-1>", lambda e: self._copy_selected_model())

    def _build_tester_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Model Tester")

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Provider:").pack(side="left")
        self.tester_provider = ttk.Combobox(top, state="readonly", width=34)
        self.tester_provider.pack(side="left", padx=4)
        ttk.Label(top, text="Model:").pack(side="left", padx=(10, 0))
        self.tester_model = ttk.Combobox(top, state="normal", width=40)
        self.tester_model.pack(side="left", padx=4)
        ttk.Button(top, text="Edit", command=self._edit_tester_model).pack(side="left", padx=2)
        ttk.Button(top, text="Load models", command=self._load_models_for_tester).pack(side="left", padx=4)
        self.tester_provider.bind("<<ComboboxSelected>>", lambda e: self._load_models_for_tester())

        mid = ttk.Frame(tab)
        mid.pack(fill="x", padx=6, pady=2)
        ttk.Label(mid, text="Max tokens:").pack(side="left")
        self.var_max_tokens = tk.StringVar(value="1024")
        ttk.Spinbox(mid, from_=1, to=128000, textvariable=self.var_max_tokens, width=8).pack(side="left", padx=4)
        ttk.Label(mid, text="Temperature:").pack(side="left", padx=(10, 0))
        self.var_temp = tk.StringVar(value="0.7")
        ttk.Spinbox(mid, from_=0.0, to=2.0, increment=0.1, textvariable=self.var_temp, width=6).pack(side="left", padx=4)

        self.prompt = scrolledtext.ScrolledText(tab, height=7, wrap="word")
        self.prompt.pack(fill="x", padx=6, pady=6)
        self.prompt.insert("1.0",
            "Hello! Please introduce yourself in a few sentences: tell me which AI "
            "model you are, who made you, and one line of your favorite poetry.")
        ttk.Label(tab, text="Prompt above, response below", foreground="gray").pack(anchor="w", padx=8)

        self.ctrl = ttk.Frame(tab)
        self.ctrl.pack(fill="x", padx=6, pady=4)
        self.run_btn = ttk.Button(self.ctrl, text="Run Test", command=self._run_test)
        self.run_btn.pack(side="left", padx=2)
        self.var_stream = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.ctrl, text="Stream tokens", variable=self.var_stream
                        ).pack(side="left", padx=10)
        ttk.Button(self.ctrl, text="Compare…", command=self._open_compare).pack(side="left", padx=2)

        self.pass_btn = ttk.Menubutton(self.ctrl, text="Pass to ▾")
        self.pass_menu = tk.Menu(self.pass_btn, tearoff=0)
        self.pass_btn["menu"] = self.pass_menu
        self._rebuild_pass_menu()
        self.pass_btn.pack(side="left", padx=6)

        self.response = scrolledtext.ScrolledText(tab, height=18, wrap="word")
        self.response.pack(fill="both", expand=True, padx=6, pady=6)

        self.metrics = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.metrics, foreground="#0a7d33",
                  anchor="w").pack(fill="x", padx=8, pady=(0, 6))

    def _build_logs_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Logs")
        self.log_text = scrolledtext.ScrolledText(tab, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)
        self.log_text.tag_configure("err", foreground="red")
        self.log_text.tag_configure("ok", foreground="green")

    def _build_claude_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Claude Profiles")

        self.claude_dir_var = tk.StringVar(value=cp.profiles_dir())
        ttk.Label(tab, textvariable=self.claude_dir_var,
                  foreground="gray").pack(anchor="w", padx=8, pady=(6, 0))

        btns = ttk.Frame(tab)
        btns.pack(fill="x", padx=6, pady=4)
        ttk.Button(btns, text="Refresh", command=self._refresh_claude_tab).pack(side="left", padx=3)
        ttk.Button(btns, text="+ Create from provider…", command=self._create_claude_profile).pack(side="left", padx=3)
        ttk.Button(btns, text="Import settings…", command=self._import_settings_wizard).pack(side="left", padx=3)
        ttk.Button(btns, text="Set as Active", command=self._set_active_profile).pack(side="left", padx=3)
        ttk.Button(btns, text="Edit notes", command=self._edit_profile_notes).pack(side="left", padx=3)
        ttk.Button(btns, text="Rename", command=self._rename_profile).pack(side="left", padx=3)
        ttk.Button(btns, text="Delete selected", command=self._delete_claude_profile).pack(side="left", padx=3)
        ttk.Button(btns, text="Copy model", command=self._copy_claude_model).pack(side="left", padx=3)
        ttk.Button(btns, text="Open folder", command=self._open_claude_folder).pack(side="left", padx=3)

        cols = ("name", "model", "base", "key", "notes")
        self.claude_tree = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse")
        headers = {"name": "Profile", "model": "Model", "base": "Base URL",
                   "key": "API Key", "notes": "Notes / Purpose"}
        widths = {"name": 170, "model": 240, "base": 200, "key": 150, "notes": 220}
        for c in cols:
            self.claude_tree.heading(c, text=headers[c])
            self.claude_tree.column(c, width=widths[c], anchor="w")
        self.claude_tree.pack(fill="both", expand=True, padx=6, pady=6)

        self.claude_status = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.claude_status, foreground="gray"
                  ).pack(anchor="w", padx=8, pady=(0, 6))

        self.claude_active = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.claude_active, foreground="#0a7d33",
                  font=("", 9, "bold")).pack(anchor="w", padx=8, pady=(0, 6))

        self._refresh_claude_tab()

    def _refresh_claude_tab(self):
        for i in self.claude_tree.get_children():
            self.claude_tree.delete(i)
        try:
            profiles = cp.list_profiles()
            active_model = cp.get_active_model()
        except Exception as e:
            self._log("Claude profiles read failed: %s" % e, err=True)
            self.claude_status.set("Could not read profiles: %s" % e)
            return
        self.claude_tree.tag_configure("active", foreground="#0a7d33",
                                       font=("", 9, "bold"))
        for p in profiles:
            key = p.get("api_key") or ""
            key_disp = ("••••" + key[-4:]) if key else ""
            tags = ("active",) if (p.get("model") == active_model) else ()
            self.claude_tree.insert("", "end", values=(
                p["name"], p.get("model", ""), p.get("base_url", ""),
                key_disp, (p.get("notes") or "")[:60]), tags=tags)
        self.claude_status.set("%d profile(s) configured in Claude Code." % len(profiles))
        if active_model:
            self.claude_active.set("ACTIVE MODEL: %s   (from ~/.claude/settings.json)" % active_model)
        else:
            self.claude_active.set("No active model set yet.")
        self._log("Claude Profiles: %d profile(s); active=%s" %
                  (len(profiles), active_model or "(none)"))

    def _set_active_profile(self):
        name = self._selected_claude_profile()
        if not name:
            return
        if not messagebox.askyesno("Set Active",
                                   "Make profile '%s' the active Claude Code model?" % name):
            return
        try:
            model = cp.set_active_profile(name)
        except (ValueError, OSError) as e:
            self._log("Set active failed: %s" % e, err=True)
            messagebox.showerror("Set active failed", str(e))
            return
        self._log("Set active Claude model to '%s' -> %s" % (name, model), ok=True)
        self._refresh_claude_tab()
        messagebox.showinfo("Active model set",
                            "Claude Code will now use:\n%s\n\n(also written to "
                            "%s)" % (model, cp.user_settings_path()))

    def _edit_profile_notes(self):
        name = self._selected_claude_profile()
        if not name:
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Notes for %s" % name)
        dlg.transient(self.root)
        dlg.grab_set()
        txt = tk.Text(dlg, width=56, height=8, wrap="word")
        txt.pack(padx=10, pady=10)
        txt.insert("1.0", cp.profile_notes(name) or "")
        btns = ttk.Frame(dlg)
        btns.pack(pady=(0, 10))

        def save():
            cp.set_profile_notes(name, txt.get("1.0", "end").strip())
            self._log("Updated notes for profile '%s'." % name)
            self._refresh_claude_tab()
            dlg.destroy()

        ttk.Button(btns, text="Save", command=save).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=6)

    def _rename_profile(self):
        name = self._selected_claude_profile()
        if not name:
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Rename profile")
        dlg.transient(self.root)
        dlg.grab_set()
        ttk.Label(dlg, text="New folder name:").pack(padx=10, pady=(10, 0))
        var = tk.StringVar(value=name)
        ent = ttk.Entry(dlg, textvariable=var, width=40)
        ent.pack(padx=10, pady=5)
        btns = ttk.Frame(dlg)
        btns.pack(pady=(0, 10))

        def do_rename():
            new = var.get().strip()
            try:
                res = cp.rename_profile(name, new)
            except ValueError as e:
                messagebox.showerror("Rename failed", str(e), parent=dlg)
                return
            if res:
                self._log("Renamed profile '%s' -> '%s'." % (name, res))
                self._refresh_claude_tab()
            dlg.destroy()

        ttk.Button(btns, text="Rename", command=do_rename).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=6)

    def _import_settings_wizard(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Import a Claude settings.json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            info = cp.parse_settings_file(path)
        except Exception as e:
            self._log("Import parse failed: %s" % e, err=True)
            messagebox.showerror("Import failed", str(e))
            return
        dlg = tk.Toplevel(self.root)
        dlg.title("Import profile")
        dlg.transient(self.root)
        dlg.grab_set()
        var_name = tk.StringVar(value=info["name"])
        var_model = tk.StringVar(value=info["model"])
        var_base = tk.StringVar(value=info["base_url"])
        var_key = tk.StringVar(value=info["api_key"])
        body = ttk.Frame(dlg, padding=12)
        body.pack(fill="both", expand=True)
        rows = [("Folder name", var_name), ("Model", var_model),
                ("Base URL", var_base), ("API key", var_key)]
        for i, (label, var) in enumerate(rows):
            ttk.Label(body, text=label + ":").grid(row=i, column=0, padx=6, pady=4, sticky="w")
            ttk.Entry(body, textvariable=var, width=48).grid(row=i, column=1, padx=6, pady=4)
        btns = ttk.Frame(body)
        btns.grid(row=len(rows), column=0, columnspan=2, pady=10)

        def do_import():
            try:
                cp.create_profile(var_name.get(), var_model.get(), var_base.get(),
                                  var_key.get(), "Imported")
            except (ValueError, OSError) as e:
                messagebox.showerror("Import failed", str(e), parent=dlg)
                return
            self._log("Imported Claude profile '%s'." % var_name.get(), ok=True)
            self._refresh_claude_tab()
            dlg.destroy()

        ttk.Button(btns, text="Import", command=do_import).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=6)

    # ---------- Quick switcher + tray / hotkey (feature #4) ----------
    def _open_quick_switcher(self):
        from tkinter import simpledialog
        names = [p["name"] for p in cp.list_profiles()]
        if not names:
            messagebox.showinfo("No profiles", "No Claude profiles found yet.")
            return
        active = cp.get_active_model()
        choice = simpledialog.askstring(
            "Quick Switch (Ctrl+Alt+M)",
            ("Pick a Claude profile to set active:\n\n%s\n\nCurrent active: %s\n\n"
             "Type the profile name:") % ("\n".join(names), active or "(none)"))
        if not choice:
            return
        choice = choice.strip()
        if choice not in names:
            messagebox.showwarning("Not found", "No profile named '%s'." % choice)
            return
        try:
            model = cp.set_active_profile(choice)
        except (ValueError, OSError) as e:
            messagebox.showerror("Failed", str(e))
            return
        self._log("Hotkey switch -> active model '%s'." % model, ok=True)
        self._refresh_claude_tab()
        messagebox.showinfo("Active model set", "Now active:\n%s" % model)

    def _on_close(self):
        if self._tray_win is None:
            self._minimize_to_tray()
        else:
            self._restore_from_tray()

    def _minimize_to_tray(self):
        self.root.withdraw()
        win = tk.Toplevel(self.root)
        win.title("AI Model Manager")
        win.attributes("-topmost", True)
        win.geometry("+10+600")
        f = ttk.Frame(win, padding=8)
        f.pack()
        ttk.Label(f, text="AI Model Manager (minimized)").pack(side="left", padx=4)
        ttk.Button(f, text="Open", command=self._restore_from_tray).pack(side="left", padx=4)
        ttk.Button(f, text="Quick Switch", command=self._restore_then_switch).pack(side="left", padx=4)
        ttk.Button(f, text="Exit", command=self._quit_app).pack(side="left", padx=4)
        win.protocol("WM_DELETE_WINDOW", self._quit_app)
        self._tray_win = win
        self._log("Minimized to tray (press Ctrl+Alt+M to quick switch).")

    def _restore_from_tray(self):
        if self._tray_win is not None:
            self._tray_win.destroy()
            self._tray_win = None
        self.root.deiconify()
        self.root.lift()

    def _restore_then_switch(self):
        self._restore_from_tray()
        self._open_quick_switcher()

    def _quit_app(self):
        if self._tray_win is not None:
            self._tray_win.destroy()
        self.root.quit()

    # ---------- Cloud provider presets (feature #6) ----------
    PRESETS = [
        {"name": "OpenRouter", "format": "auto", "base_url": "https://openrouter.ai/api/v1",
         "api_key": "", "default_model": "", "notes": "OpenRouter (OpenAI-compatible)."},
        {"name": "Together", "format": "auto", "base_url": "https://api.together.xyz/v1",
         "api_key": "", "default_model": "", "notes": "Together AI (OpenAI-compatible)."},
        {"name": "SambaNova", "format": "auto", "base_url": "https://api.sambanova.ai/v1",
         "api_key": "", "default_model": "", "notes": "SambaNova Cloud (OpenAI-compatible)."},
    ]

    # CLI tools you can "pass" the current provider+model to.
    TOOLS = [
        ("Claude", "claude"),
        ("Cline", "cline"),
        ("OpenCode", "opencode"),
        ("kilo", "kilo"),
        ("Hermes", "hermes"),
        ("OTHER…", "__other__"),
    ]

    def _open_presets(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Cloud Provider Preset")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        ttk.Label(dlg, text="Choose a provider template to add:", padding=(10, 8)
                  ).pack(anchor="w")
        body = ttk.Frame(dlg, padding=10)
        body.pack(fill="both", expand=True)
        for p in self.PRESETS:
            ttk.Button(body, text="+ %s" % p["name"], width=32,
                       command=lambda pp=p: self._add_preset(pp, dlg)).pack(
                pady=2, fill="x")
        ttk.Label(body, text="API key is left blank — set it after adding.",
                  foreground="gray", wraplength=280).pack(anchor="w", pady=(8, 0))
        ttk.Button(body, text="Close", command=dlg.destroy).pack(pady=6)

    def _add_preset(self, preset, dlg):
        dlg.destroy()
        self.config["providers"].append(dict(preset))
        self._save(quiet=True)
        self._refresh_provider_tree()
        self._refresh_tester_combos()
        self._log("Added provider preset '%s'." % preset["name"], ok=True)

    # ---------- Export / import config (feature #10) ----------
    def _export_config(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Export setup", defaultextension=".json",
            initialfile="ai-model-manager-setup.json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except OSError as e:
            self._log("Export failed: %s" % e, err=True)
            messagebox.showerror("Export failed", str(e))
            return
        self._log("Exported setup to %s" % path, ok=True)

    def _import_config(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Import setup JSON",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self._log("Import failed: %s" % e, err=True)
            messagebox.showerror("Import failed", str(e))
            return
        if not isinstance(data, dict) or "providers" not in data:
            messagebox.showerror("Bad file", "Not a valid setup file (missing 'providers').")
            return
        if not messagebox.askyesno(
                "Import",
                "Replace current %d provider(s) with the %d imported provider(s)?"
                % (len(self.config.get("providers", [])), len(data.get("providers", [])))):
            return
        self.config = data
        self._save(quiet=True)
        self._refresh_provider_tree()
        self._refresh_tester_combos()
        self._log("Imported %d provider(s) from %s."
                  % (len(data.get("providers", [])), path))

    # ---------- "Pass to" CLI tool ----------
    def _custom_tools(self):
        return [t for t in self.config.get("tools", [])
                if isinstance(t, dict) and t.get("name") and t.get("command")]

    def _rebuild_pass_menu(self):
        m = self.pass_menu
        m.delete(0, "end")
        for label, cmd in self.TOOLS:
            m.add_command(label=label,
                          command=lambda c=cmd, l=label: self._pass_to(c, l))
        for t in self._custom_tools():
            m.add_command(label="%s  (%s)" % (t["name"], t["command"]),
                          command=lambda c=t["command"], l=t["name"]: self._pass_to(c, l))
        m.add_separator()
        m.add_command(label="Add custom CLI tool…", command=self._add_custom_tool)

    def _rebuild_prov_pass_menu(self):
        m = self.prov_pass_menu
        m.delete(0, "end")
        for label, cmd in self.TOOLS:
            m.add_command(label=label,
                          command=lambda c=cmd, l=label: self._pass_from_providers_tab(c, l))
        for t in self._custom_tools():
            m.add_command(label="%s  (%s)" % (t["name"], t["command"]),
                          command=lambda c=t["command"], l=t["name"]: self._pass_from_providers_tab(c, l))
        m.add_separator()
        m.add_command(label="Add custom CLI tool…", command=self._add_custom_tool)

    def _selected_provider(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No provider", "Select a provider in the Providers tab first.")
            return None
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return None
        name = vals[0]
        return self._provider_by_name(name)

    def _pass_from_providers_tab(self, command, label):
        prov = self._selected_provider()
        if not prov:
            return
        model = prov.get("default_model", "").strip()
        if not model:
            # Prompt for a model name since the provider has no default.
            from tkinter import simpledialog
            model = simpledialog.askstring(
                "Model to pass",
                "Provider '%s' has no default model.\n\nEnter a model name to pass:"
                % prov["name"])
            if not model:
                return
        if command in ("__other__", "OTHER…"):
            self._add_custom_tool()
            return
        if label == "Claude":
            self._pass_to_claude(prov, model)
            return
        self._launch_tool(command, prov, model)

    def _current_provider_model(self):
        name = self.tester_provider.get()
        prov = self._provider_by_name(name)
        model = self.tester_model.get().strip()
        if not prov:
            messagebox.showwarning("No provider", "Pick a provider first (Model Tester).")
            return None, None
        if not model:
            model = prov.get("default_model", "")
        if not model:
            messagebox.showwarning("No model", "Pick a model to pass.")
            return None, None
        return prov, model

    def _tool_env(self, prov, model):
        fmt = resolve_format(prov)
        base = normalize_base(prov.get("base_url", ""))
        openai_base = base + "/v1" if not base.endswith("/v1") else base
        key = prov.get("api_key", "")
        return {
            "OPENAI_BASE_URL": openai_base,
            "OPENAI_API_KEY": key,
            "OPENAI_MODEL": model,
            "ANTHROPIC_BASE_URL": base,
            "ANTHROPIC_API_KEY": key,
            "ANTHROPIC_MODEL": model,
            "CLAUDE_CODE_MODEL": model,
            "LLM_BASE_URL": base,
            "LLM_API_KEY": key,
            "LLM_MODEL": model,
        }

    def _launch_tool(self, command, prov, model):
        if command == "cline":
            base = normalize_base(prov.get("base_url", "")) + "/v1"
            key = prov.get("api_key", "(none)")
            settings_block = (
                "Provider: OpenAI-compatible\n"
                "Base URL: %s\n"
                "API Key: %s\n"
                "Model: %s" % (base, key, model))
            messagebox.showinfo(
                "Cline: credits cannot be bypassed",
                "Cline is a VS Code extension with its own billing.\n"
                "Our app cannot bypass 'Cline Credits depleted'.\n\n"
                "TWO OPTIONS:\n\n"
                "A) Use ClinePass (no per-credit billing):\n"
                "   https://app.cline.bot/dashboard/subscription?personal=true\n"
                "   Then in VS Code: /settings -> Provider: ClinePass\n\n"
                "B) Use a different CLI tool (no credit system):\n"
                "   - OpenCode  (already on your PATH)\n"
                "   - kilo       (already on your PATH)\n"
                "   - Hermes     (already on your PATH)\n"
                "   - Claude CLI (installed, uses Anthropic API)\n\n"
                "--- Paste these into Cline settings if you still want Cline ---\n"
                "%s\n"
                "------------------------------------------------------------------"
                % settings_block)
            self._log("Cline credit notice for %s / %s (no bypass possible)."
                      % (prov["name"], model))
            return
        resolved = shutil.which(command)
        if not resolved:
            messagebox.showerror("Tool not found",
                                 ("'%s' is not on your PATH.\n\n"
                                  "Install it, or use 'Pass to ▾ -> Add custom "
                                  "CLI tool…' with a full path.\n\n"
                                  "Checked via: where %s" % (command, command)))
            return
        import subprocess
        env = dict(os.environ)
        env.update(self._tool_env(prov, model))
        # Windows .cmd/.bat files need shell=True or the full path with extension.
        use_shell = resolved.lower().endswith((".cmd", ".bat", ".ps1"))
        try:
            subprocess.Popen([resolved] if not use_shell else resolved,
                             env=env, cwd=os.path.expanduser("~"),
                             creationflags=subprocess.CREATE_NEW_CONSOLE,
                             shell=use_shell)
        except Exception as e:
            messagebox.showerror("Launch failed", str(e))
            return
        self._log("Passed %s / %s to CLI tool '%s' (opened new console)."
                  % (prov["name"], model, command), ok=True)

    def _pass_to(self, command, label):
        prov, model = self._current_provider_model()
        if not prov or not model:
            return
        if command in ("__other__", "OTHER…"):
            self._add_custom_tool()
            return
        if label == "Claude":
            self._pass_to_claude(prov, model)
            return
        self._launch_tool(command, prov, model)

    def _pass_to_claude(self, prov, model):
        # Claude Code only understands Claude/Anthropic model IDs.
        # If the current model looks like a non-Claude model (e.g. moonshotai/kimi-k3-free),
        # prompt the user for a valid Claude model name before creating the profile.
        claude_model = model
        lower = model.lower()
        if not any(h in lower for h in ("claude", "sonnet", "haiku", "opus", "anthropic")):
            from tkinter import simpledialog
            claude_model = simpledialog.askstring(
                "Pick a Claude model",
                ("The current model '%s' is not a Claude model.\n"
                 "Claude Code needs a Claude/Anthropic model ID.\n\n"
                 "Examples:\n"
                 "  claude-sonnet-4-20250514\n"
                 "  claude-3-5-haiku-20241022\n"
                 "  claude-3-opus-20240229\n\n"
                 "Enter the Claude model to use:")
                % model)
            if not claude_model:
                return
            claude_model = claude_model.strip()
        try:
            profile_name = "pass-" + cp.sanitize_name(claude_model)
            cp.create_profile(profile_name, claude_model, prov.get("base_url", ""),
                              prov.get("api_key", ""),
                              "Auto-created by Pass to Claude for %s" % claude_model)
            cp.set_active_profile(profile_name)
        except Exception as e:
            messagebox.showerror("Claude pass failed", str(e))
            return
        self._refresh_claude_tab()
        self._log("Installed & activated Claude profile '%s' for %s."
                  % (profile_name, claude_model), ok=True)
        self._launch_tool("claude", prov, claude_model)
        messagebox.showinfo("Passed to Claude",
                            "Profile '%s' is active and Claude is launching.\n%s"
                            % (profile_name, claude_model))

    def _edit_tester_model(self):
        """Let the user type any model name into the Model Tester combobox."""
        current = self.tester_model.get().strip()
        from tkinter import simpledialog
        new_model = simpledialog.askstring(
            "Edit model",
            "Enter the model ID to use for testing:\n\n"
            "Tip: you can type any model name here, even if it is not\n"
            "in the dropdown list.",
            initialvalue=current)
        if new_model is None:
            return
        new_model = new_model.strip()
        if not new_model:
            messagebox.showwarning("Empty", "Model name cannot be empty.", parent=self.root)
            return
        self.tester_model.set(new_model)
        self._log("Model Tester model set to: %s" % new_model)

    def _add_custom_tool(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add custom CLI tool")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        body = ttk.Frame(dlg, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Tool name:").pack(anchor="w")
        var_name = tk.StringVar()
        ttk.Entry(body, textvariable=var_name, width=46).pack(pady=2)
        ttk.Label(body, text="Command (on PATH or full path):").pack(anchor="w", pady=(6, 0))
        var_cmd = tk.StringVar()
        ttk.Entry(body, textvariable=var_cmd, width=46).pack(pady=2)
        ttk.Label(body, text="Example: opencode, kilo, hermes, C:\\tools\\ai.exe",
                  foreground="gray").pack(anchor="w", pady=(2, 0))

        def save():
            n = var_name.get().strip()
            c = var_cmd.get().strip()
            if not n or not c:
                messagebox.showerror("Missing", "Both name and command are required.",
                                     parent=dlg)
                return
            self.config.setdefault("tools", []).append({"name": n, "command": c})
            self._save(quiet=True)
            self._rebuild_pass_menu()
            dlg.destroy()
            self._log("Added custom tool '%s' (%s)." % (n, c))

        btns = ttk.Frame(body)
        btns.pack(pady=(10, 0))
        ttk.Button(btns, text="Add", command=save).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=6)

    # ---------- Omniroute service (launch / fix) ----------
    def _open_omniroute(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Omniroute Service")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        body = ttk.Frame(dlg, padding=12)
        body.pack(fill="both", expand=True)
        status = tk.StringVar(value="Checking…")
        ttk.Label(body, textvariable=status, wraplength=470,
                  justify="left").pack(anchor="w", pady=(0, 8))

        def refresh_status():
            running, detail = omni.status()
            status.set(("GREEN - " if running else "RED - ") + detail)
            dlg.update_idletasks()

        def do_start():
            status.set("Launching Omniroute…")
            dlg.update_idletasks()
            ok, detail = omni.start()
            status.set(("GREEN - " if ok else "RED - ") + detail)

        def do_fix():
            status.set("Running fix…")
            dlg.update_idletasks()
            ok, detail = omni.fix()
            status.set(("GREEN - " if ok else "RED - ") + detail)

        def open_dash():
            import webbrowser
            webbrowser.open(omni.BASE + "/dashboard/api-manager")

        btns = ttk.Frame(body)
        btns.pack(anchor="w")
        ttk.Button(btns, text="Check Status", command=refresh_status).pack(side="left", padx=3)
        ttk.Button(btns, text="Launch", command=do_start).pack(side="left", padx=3)
        ttk.Button(btns, text="Fix", command=do_fix).pack(side="left", padx=3)
        ttk.Button(btns, text="Open Dashboard", command=open_dash).pack(side="left", padx=3)
        ttk.Button(btns, text="Close", command=dlg.destroy).pack(side="left", padx=3)
        refresh_status()






    def _create_claude_profile(self):
        providers = self.config["providers"]
        if not providers:
            messagebox.showerror("No providers", "Add a provider first (Providers tab).",
                                 parent=self.root)
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Create Claude Code Profile")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        var_prov = tk.StringVar(value=providers[0]["name"])
        var_name = tk.StringVar()
        var_model = tk.StringVar()
        var_api = tk.StringVar()
        base_var = tk.StringVar()

        model_box = ttk.Combobox(dlg, textvariable=var_model, state="normal", width=44)
        key_entry = ttk.Entry(dlg, textvariable=var_api, width=44, show="*")
        prov_box = ttk.Combobox(dlg, textvariable=var_prov, state="readonly",
                                values=[p["name"] for p in providers], width=44)
        base_entry = ttk.Entry(dlg, textvariable=base_var, width=44)

        def on_provider_change(*_a):
            prov = self._provider_by_name(var_prov.get())
            if not prov:
                return
            var_api.set(prov.get("api_key", ""))
            base_var.set(prov.get("base_url", ""))
            models = self.model_cache.get(prov["name"], [])
            model_box["values"] = models
            chosen = prov.get("default_model", "")
            if not chosen and models:
                chosen = models[0]
            if chosen:
                var_model.set(chosen)

        prov_box.bind("<<ComboboxSelected>>", on_provider_change)
        on_provider_change()

        pad = {"padx": 8, "pady": 4, "sticky": "w"}
        body = ttk.Frame(dlg, padding=12)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="Provider:").grid(row=0, column=0, **pad)
        prov_box.grid(row=0, column=1, **pad)

        ttk.Label(body, text="Profile name:").grid(row=1, column=0, **pad)
        ttk.Entry(body, textvariable=var_name, width=44).grid(row=1, column=1, **pad)
        ttk.Label(body, text="(folder name for Claude)", foreground="gray").grid(row=1, column=2, **pad)

        ttk.Label(body, text="Model:").grid(row=2, column=0, **pad)
        model_box.grid(row=2, column=1, **pad)
        ttk.Label(body, text="e.g. antigravity/claude-sonnet-4-6", foreground="gray").grid(row=2, column=2, **pad)

        ttk.Label(body, text="API key:").grid(row=3, column=0, **pad)
        key_entry.grid(row=3, column=1, **pad)
        ttk.Button(body, text="Show",
                   command=lambda: key_entry.config(show="")).grid(row=3, column=2, **pad)

        ttk.Label(body, text="Base URL:").grid(row=4, column=0, **pad)
        base_entry.grid(row=4, column=1, **pad)
        ttk.Label(body, text="(from provider)", foreground="gray").grid(row=4, column=2, **pad)

        info = ("Creates a folder in your Claude Code profiles so you can switch to this "
                "model with /profile inside Claude.")
        ttk.Label(body, text=info, foreground="gray", wraplength=520).grid(
            row=5, column=0, columnspan=3, padx=8, pady=(8, 0), sticky="w")

        btns = ttk.Frame(body)
        btns.grid(row=6, column=0, columnspan=3, pady=(12, 0))

        def do_create():
            model = var_model.get().strip()
            name = var_name.get().strip() or cp.sanitize_name(model)
            base = base_var.get().strip()
            try:
                path = cp.create_profile(name, model, base, var_api.get().strip())
            except (ValueError, OSError) as e:
                messagebox.showerror("Create failed", str(e), parent=dlg)
                return
            self._log("Created Claude profile '%s' -> %s" % (name, path), ok=True)
            messagebox.showinfo("Created",
                                "Claude profile installed:\n%s\n\nUse /profile in "
                                "Claude Code to select it." % path, parent=dlg)
            self._refresh_claude_tab()
            dlg.destroy()

        ttk.Button(btns, text="Create Profile", command=do_create).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left", padx=6)

    def _selected_claude_profile(self):
        sel = self.claude_tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a Claude profile first.")
            return None
        return self.claude_tree.item(sel[0], "values")[0]

    def _delete_claude_profile(self):
        name = self._selected_claude_profile()
        if not name:
            return
        if not messagebox.askyesno("Delete", "Delete Claude profile '%s'?" % name):
            return
        try:
            ok = cp.delete_profile(name)
        except Exception as e:
            self._log("Delete failed: %s" % e, err=True)
            messagebox.showerror("Delete failed", str(e))
            return
        if ok:
            self._log("Deleted Claude profile '%s'." % name)
        self._refresh_claude_tab()

    def _copy_claude_model(self):
        name = self._selected_claude_profile()
        if not name:
            return
        row = None
        for i in self.claude_tree.get_children():
            if self.claude_tree.item(i, "values")[0] == name:
                row = self.claude_tree.item(i, "values")
                break
        if not row:
            return
        copy_to_clipboard(self.root, row[1])
        self._log("Copied model to clipboard: %s" % row[1])

    def _open_claude_folder(self):
        import subprocess
        subprocess.Popen(["explorer", cp.profiles_dir()])

    # ---------- Stats & History tab (feature #2) ----------
    def _build_stats_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Stats & History")

        self.stats_text = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.stats_text, font=("", 10, "bold"),
                  justify="left").pack(anchor="w", padx=10, pady=(8, 4))

        ttk.Label(tab, text="Recent runs (latest first):", foreground="gray"
                  ).pack(anchor="w", padx=10, pady=(4, 0))

        cols = ("ts", "provider", "model", "latency", "usage", "ok")
        self.hist_tree = ttk.Treeview(tab, columns=cols, show="headings", height=14)
        heads = {"ts": "Time", "provider": "Provider", "model": "Model",
                 "latency": "Latency", "usage": "Tokens", "ok": "Result"}
        widths = {"ts": 150, "provider": 130, "model": 200, "latency": 80,
                  "usage": 120, "ok": 60}
        for c in cols:
            self.hist_tree.heading(c, text=heads[c])
            self.hist_tree.column(c, width=widths[c], anchor="w")
        self.hist_tree.tag_configure("ok", foreground="#0a7d33")
        self.hist_tree.tag_configure("fail", foreground="#c00")
        self.hist_tree.pack(fill="both", expand=True, padx=8, pady=6)

        btns = ttk.Frame(tab)
        btns.pack(anchor="w", padx=8, pady=(0, 6))
        ttk.Button(btns, text="Refresh", command=self._refresh_stats).pack(side="left", padx=3)
        ttk.Button(btns, text="Clear history", command=self._clear_history).pack(side="left", padx=3)
        ttk.Button(btns, text="Open history.json", command=self._open_history_file).pack(side="left", padx=3)

    def _refresh_stats(self):
        entries = hist.load()
        s = hist.stats(entries)
        lines = [
            "Runs: %d   OK: %d   Failed: %d" % (s["total"], s["ok"], s["failed"]),
            "Avg latency: %.2fs   Min: %.2fs   Max: %.2fs" %
            (s["avg_latency"], s["min_latency"], s["max_latency"]),
            "Tokens in: %d   Tokens out: %d" % (s["input_tokens"], s["output_tokens"]),
        ]
        self.stats_text.set("\n".join(lines))
        for i in self.hist_tree.get_children():
            self.hist_tree.delete(i)
        for e in reversed(entries[-500:]):
            lat = e.get("latency")
            lat_txt = ("%.2fs" % lat) if isinstance(lat, (int, float)) else "-"
            u = e.get("usage") or {}
            tok = u.get("input_tokens") or u.get("prompt_tokens") or 0
            tout = u.get("output_tokens") or u.get("completion_tokens") or 0
            usage_txt = ("%d/%d" % (tok, tout)) if (tok or tout) else "-"
            ok = e.get("ok")
            self.hist_tree.insert("", "end", values=(
                e.get("time_str", ""), e.get("provider", ""), e.get("model", ""),
                lat_txt, usage_txt, "OK" if ok else "FAIL"),
                tags=("ok" if ok else "fail",))

    def _clear_history(self):
        if not messagebox.askyesno("Clear", "Delete all recorded test history?"):
            return
        hist.save([])
        self._refresh_stats()
        self._log("Cleared test history.")

    def _open_history_file(self):
        import subprocess
        subprocess.Popen(["explorer", "/select,", hist.HISTORY_PATH])

    # ---------- Benchmark tab (feature #3) ----------
    def _build_bench_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Benchmark")

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Provider:").pack(side="left")
        self.bench_provider = ttk.Combobox(top, state="readonly", width=40)
        self.bench_provider.pack(side="left", padx=6)
        ttk.Button(top, text="Run on all models", command=self._run_benchmark).pack(side="left", padx=4)
        ttk.Button(top, text="Load models", command=self._bench_load_models).pack(side="left", padx=4)

        self.bench_status = tk.StringVar(value="Pick a provider, then run.")

        cols = ("rank", "model", "latency", "tokens", "status")
        self.bench_tree = ttk.Treeview(tab, columns=cols, show="headings")
        heads = {"rank": "#", "model": "Model", "latency": "Latency",
                 "tokens": "Tokens", "status": "Status"}
        widths = {"rank": 40, "model": 420, "latency": 90, "tokens": 120, "status": 160}
        for c in cols:
            self.bench_tree.heading(c, text=heads[c])
            self.bench_tree.column(c, width=widths[c], anchor="w")
        self.bench_tree.tag_configure("ok", foreground="#0a7d33")
        self.bench_tree.tag_configure("fail", foreground="#c00")

        head = ttk.Frame(tab)
        head.pack(fill="both", expand=True, padx=6, pady=4)
        self.bench_status_label = ttk.Label(head, textvariable=self.bench_status,
                                            foreground="#0a7d33")
        self.bench_status_label.pack(anchor="w")
        self.bench_tree.pack(fill="both", expand=True, padx=6, pady=4)
        ttk.Label(tab, text="Uses the prompt from the Model Tester tab, max_tokens=256, "
                            "temp=0.2, and records results to history.",
                  foreground="gray").pack(anchor="w", padx=8, pady=(0, 6))

        if self.config.get("providers"):
            self.bench_provider["values"] = [p["name"] for p in self.config["providers"]]
            self.bench_provider.set(self.config["providers"][0]["name"])

    # ---------- Gateway tab (local API server) ----------
    def _build_gateway_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Gateway")

        # Header
        hdr = ttk.Frame(tab)
        hdr.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(hdr, text="Standard Professional API Gateway", font=("", 12, "bold")).pack(side="left")
        self.gateway_status_var = tk.StringVar(value="Stopped")
        self.gateway_status_lbl = ttk.Label(hdr, textvariable=self.gateway_status_var,
                                            foreground="#c00", font=("", 10, "bold"))
        self.gateway_status_lbl.pack(side="right")

        # Info
        info = ttk.Label(tab,
            text="Run a local OpenAI & Anthropic compatible API server and Browser Web Dashboard on localhost.\n"
                 "Other software (Claude Code, Cursor, Windsurf, LangChain) can use your providers via this gateway.\n"
                 "Provider selection: ?provider=ProviderName in query string.",
            foreground="gray", justify="left")
        info.pack(anchor="w", padx=10, pady=(0, 8))

        # URL display
        url_frame = ttk.Frame(tab)
        url_frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(url_frame, text="Endpoint:").pack(side="left")
        self.gateway_url_var = tk.StringVar(value="http://127.0.0.1:11434/v1/chat/completions")
        url_entry = ttk.Entry(url_frame, textvariable=self.gateway_url_var, width=50, state="readonly")
        url_entry.pack(side="left", padx=6, fill="x", expand=True)

        # Port + Force Port + provider
        ctrl = ttk.Frame(tab)
        ctrl.pack(fill="x", padx=10, pady=6)
        ttk.Label(ctrl, text="Port:").pack(side="left")
        self.gateway_port_var = tk.StringVar(value="11434")
        ttk.Entry(ctrl, textvariable=self.gateway_port_var, width=8).pack(side="left", padx=4)

        # Force Port toggle
        self.gateway_force_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, text="Force Port (Kill conflicting PID if busy)", variable=self.gateway_force_var).pack(side="left", padx=(8, 4))

        ttk.Label(ctrl, text="Provider:").pack(side="left", padx=(10, 0))
        self.gateway_provider_var = tk.StringVar(value="")
        providers = [p["name"] for p in self.config.get("providers", [])]
        self.gateway_provider_cb = ttk.Combobox(ctrl, textvariable=self.gateway_provider_var,
                                                 values=providers, state="readonly", width=24)
        self.gateway_provider_cb.pack(side="left", padx=4)

        # Buttons
        btns = ttk.Frame(tab)
        btns.pack(fill="x", padx=10, pady=6)
        self.gateway_start_btn = ttk.Button(btns, text="Start Gateway", command=self._gateway_start)
        self.gateway_start_btn.pack(side="left", padx=4)
        ttk.Button(btns, text="Stop Gateway", command=self._gateway_stop).pack(side="left", padx=4)
        ttk.Button(btns, text="Check Status", command=self._gateway_status).pack(side="left", padx=4)
        ttk.Button(btns, text="Copy URL", command=self._gateway_copy_url).pack(side="left", padx=4)
        ttk.Button(btns, text="Open Browser Dashboard 🌐", command=self._gateway_open_dashboard).pack(side="left", padx=4)

        # Port scanner - show free / locked ports to debug conflicts
        ps = ttk.LabelFrame(tab, text="Port status & Force Conflict Resolution")
        ps.pack(fill="x", padx=10, pady=(4, 4))
        prow = ttk.Frame(ps)
        prow.pack(fill="x", padx=6, pady=4)
        ttk.Label(prow, text="Ports:").pack(side="left")
        self.gateway_ports_var = tk.StringVar(value="11430-11440")
        ttk.Entry(prow, textvariable=self.gateway_ports_var, width=18).pack(side="left", padx=4)
        ttk.Button(prow, text="Scan", command=self._gateway_scan_ports).pack(side="left", padx=4)
        ttk.Button(prow, text="⚡ Force Free Selected Port", command=self._gateway_force_free_selected).pack(side="left", padx=4)
        ttk.Label(prow, text="(Select a row and click Force Free to terminate PID holding port)",
                  foreground="gray").pack(side="left", padx=6)

        self.port_tree = ttk.Treeview(ps, columns=("port", "status", "pid", "process"),
                                      show="headings", height=5)
        for c, h, w in (("port", "Port", 70), ("status", "Status", 90),
                        ("pid", "PID", 90), ("process", "Process (owns the port)", 260)):
            self.port_tree.heading(c, text=h)
            self.port_tree.column(c, width=w, anchor="w")
        self.port_tree.tag_configure("free", foreground="#0a7d33")
        self.port_tree.tag_configure("locked", foreground="#c00")
        self.port_tree.pack(fill="x", padx=6, pady=(0, 6))
        self.gateway_scan_note = tk.StringVar(value="Click Scan to check port availability.")
        ttk.Label(ps, textvariable=self.gateway_scan_note, foreground="gray").pack(anchor="w", padx=6, pady=(0, 4))

        # Standard Endpoints summary
        ex = ttk.LabelFrame(tab, text="Standard Professional API Endpoints")
        ex.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        example_text = (
            "Base URL:       http://127.0.0.1:11434/v1\n"
            "Chat Endpoint:  http://127.0.0.1:11434/v1/chat/completions  (OpenAI spec)\n"
            "Claude Endpoint:http://127.0.0.1:11434/v1/messages          (Anthropic spec)\n"
            "Models Endpoint:http://127.0.0.1:11434/v1/models            (List models)\n"
            "Health Check:   http://127.0.0.1:11434/v1/health            (Gateway Status)\n"
            "OpenAPI Spec:   http://127.0.0.1:11434/v1/openapi.json       (Swagger UI JSON)\n\n"
            "Browser Web Dashboard: http://127.0.0.1:11434/ (Loaded with full dark theme & controls)"
        )
        ex_lbl = tk.Label(ex, text=example_text, justify="left", foreground="#333",
                          font=("Consolas", 9))
        ex_lbl.pack(fill="both", expand=True, padx=8, pady=6)

        self._gateway_status()

    def _gateway_start(self):
        try:
            port = int(self.gateway_port_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be a number (e.g. 11434).")
            return
        force = self.gateway_force_var.get()
        ok, detail = gw.start_gateway(port, force=force)
        if ok:
            self.gateway_url_var.set("http://127.0.0.1:%d/v1/chat/completions" % port)
            self.gateway_status_var.set("Running")
            self.gateway_status_lbl.config(foreground="#0a7d33")
            self._log("Gateway started: %s" % detail, ok=True)
            messagebox.showinfo("Gateway Started", detail)
            # Auto-open dashboard in browser after short delay
            import webbrowser
            self.root.after(800, lambda: webbrowser.open("http://127.0.0.1:%d/" % port))
        else:
            self._log("Gateway start failed: %s" % detail, err=True)
            messagebox.showerror("Gateway Error", detail)

    def _gateway_stop(self):
        ok, detail = gw.stop_gateway()
        if ok:
            self.gateway_status_var.set("Stopped")
            self.gateway_status_lbl.config(foreground="#c00")
            self._log("Gateway stopped.", ok=True)
            messagebox.showinfo("Gateway", "Gateway stopped.")
        else:
            messagebox.showinfo("Gateway", detail or "Gateway is not running.")

    def _gateway_status(self):
        if gw.is_gateway_running():
            self.gateway_status_var.set("Running")
            self.gateway_status_lbl.config(foreground="#0a7d33")
            self.gateway_start_btn.config(state="disabled")
        else:
            self.gateway_status_var.set("Stopped")
            self.gateway_status_lbl.config(foreground="#c00")
            self.gateway_start_btn.config(state="normal")

    def _gateway_scan_ports(self):
        spec = self.gateway_ports_var.get().strip()
        ports = gw.expand_port_spec(spec)
        self.port_tree.delete(*self.port_tree.get_children())
        entries = gw.scan_ports(ports)
        free = locked = 0
        for e in entries:
            tag = "free" if not e["in_use"] else "locked"
            status = "Free" if not e["in_use"] else "LOCKED"
            if not e["in_use"]:
                free += 1
            else:
                locked += 1
            self.port_tree.insert("", "end", values=(e["port"], status, e["pid"], e["process"]), tags=(tag,))
        self.gateway_scan_note.set("%d free, %d locked (%s)"
                                   % (free, locked, "used ports show the process that holds them" if locked else "all clear"))

    def _gateway_force_free_selected(self):
        sel = self.port_tree.selection()
        if not sel:
            messagebox.showinfo("Force Free Port", "Please select a locked port row from the list first.")
            return
        item = self.port_tree.item(sel[0])
        vals = item.get("values", [])
        if not vals:
            return
        port = int(vals[0])
        status = vals[1]
        pid = vals[2]
        if status == "Free":
            messagebox.showinfo("Force Free Port", "Port %d is already free!" % port)
            return
        if messagebox.askyesno("Force Free Port", f"Are you sure you want to terminate PID {pid} holding port {port}?"):
            ok, msg = gw.kill_port_listener(port)
            if ok:
                messagebox.showinfo("Force Free Port", msg)
                self._gateway_scan_ports()
            else:
                messagebox.showerror("Error", msg)

    def _gateway_copy_url(self):
        url = self.gateway_url_var.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self._log("Copied gateway URL: %s" % url)

    def _gateway_open_dashboard(self):
        import webbrowser
        port_str = self.gateway_port_var.get().strip()
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Gateway", "Invalid port: %s" % port_str)
            return

        url = "http://127.0.0.1:%d/" % port

        if not gw.is_gateway_running():
            if messagebox.askyesno("Gateway not running",
                                   "Gateway is not running on port %d.\n\nStart it now?" % port):
                self._gateway_start()
                self.root.after(1000, lambda: self._do_open_dashboard(url))
            return

        self._do_open_dashboard(url)

    def _do_open_dashboard(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
            self._log("Opened dashboard: %s" % url)
        except Exception as e:
            messagebox.showerror("Browser error",
                                 "Could not open browser.\n\nURL: %s\nError: %s" % (url, e))


    def _open_gateway(self):
        self.nb.select(self._gateway_tab_index())

    def _gateway_tab_index(self):
        try:
            return self.nb.index("current")
        except Exception:
            for i in range(self.nb.index("end")):
                if "Gateway" in self.nb.tab(i, "text"):
                    return i
        return 0

    def _bench_load_models(self):
        self._load_models_for_bench(self.bench_provider.get())

    def _load_models_for_bench(self, name):
        prov = self._provider_by_name(name)
        if not prov:
            return
        if not self.model_cache.get(name):
            self._fetch_for_provider(prov, lambda r, e: self._bench_models_loaded(name))
        else:
            self._bench_models_loaded(name)

    def _bench_models_loaded(self, name):
        models = self.model_cache.get(name, [])
        self.bench_status.set("%d model(s) ready to benchmark for %s." % (len(models), name))
        self._log("Benchmark: %d model(s) ready for %s." % (len(models), name))

    def _run_benchmark(self):
        name = self.bench_provider.get()
        prov = self._provider_by_name(name)
        if not prov:
            messagebox.showwarning("No provider", "Pick a provider first.")
            return
        models = self.model_cache.get(name, [])
        if not models:
            self._fetch_for_provider(prov, lambda r, e: self._benchmark_after_load(name, e))
            return
        self._benchmark_go(prov, models)

    def _benchmark_after_load(self, name, error):
        if error:
            messagebox.showerror("Fetch failed", str(error))
            return
        prov = self._provider_by_name(name)
        models = self.model_cache.get(name, [])
        if prov and models:
            self._benchmark_go(prov, models)

    def _benchmark_go(self, prov, models):
        name = prov["name"]
        prompt = self.prompt.get("1.0", "end").strip() or "Hello."
        for i in self.bench_tree.get_children():
            self.bench_tree.delete(i)
        self.bench_status.set("Benchmarking %d model(s)…" % len(models))
        self.bench_btn_disable(True)
        prov_snap = dict(prov)

        def _push(progress):
            self.worker.queue.put((self._bench_progress, progress, None))

        def _job():
            results = []
            total = len(models)
            for i, m in enumerate(models):
                _push((i, total, m, "testing"))
                start = time.time()
                try:
                    text, raw, usage, lat, fmt = chat(prov_snap, m, prompt, 256, 0.2, 90)
                    results.append({"model": m, "ok": True, "latency": lat,
                                    "usage": usage, "format": fmt})
                    _push((i + 1, total, m, ("ok", lat)))
                except Exception as e:
                    results.append({"model": m, "ok": False, "latency": None,
                                    "error": str(e)})
                    _push((i + 1, total, m, ("err", str(e)[:30])))
            return results

        def _done(result, error):
            self.bench_btn_disable(False)
            if error:
                self.bench_status.set("Benchmark error: %s" % error)
                self._log("Benchmark failed: %s" % error, err=True)
                return
            ok_results = [r for r in result if r.get("ok")]
            ok_results.sort(key=lambda r: r["latency"])
            for rank, r in enumerate(ok_results, start=1):
                u = r.get("usage") or {}
                tin = u.get("input_tokens") or u.get("prompt_tokens") or 0
                tout = u.get("output_tokens") or u.get("completion_tokens") or 0
                self.bench_tree.insert("", "end", values=(
                    rank, r["model"], "%.2fs" % r["latency"],
                    ("%d/%d" % (tin, tout)) if (tin or tout) else "-",
                    "OK · %s" % r.get("format", "")), tags=("ok",))
                hist.add(name, r["model"], prompt, r["latency"], r.get("usage", {}),
                         r.get("format", ""), ok=True, source="benchmark")
            for r in [x for x in result if not x.get("ok")]:
                self.bench_tree.insert("", "end", values=(
                    "-", r["model"], "-", "-", "ERR: %s" % r.get("error", "")[:40]),
                    tags=("fail",))
                hist.add(name, r["model"], prompt, None, {}, "", ok=False,
                         error=r.get("error"), source="benchmark")
            self.bench_status.set("Done. %d OK, %d failed. Fastest: %.2fs" % (
                len(ok_results), len(result) - len(ok_results),
                ok_results[0]["latency"] if ok_results else 0))
            self._log("Benchmark %s: %d OK, %d failed." %
                      (name, len(ok_results), len(result) - len(ok_results)))
            self._refresh_stats()

        self.worker.submit(_job, _done)

    def bench_btn_disable(self, disabled):
        # Reuse the tester run button to indicate an active job.
        for w in (self.run_btn,):
            try:
                w.config(state="disabled" if disabled else "normal")
            except Exception:
                pass

    def _bench_progress(self, result, error):
        cur, total, model, detail = result
        if detail == "testing":
            self.bench_status.set("Testing %d/%d: %s" % (cur + 1, total, model))
        else:
            tag, val = detail
            if tag == "ok":
                self.bench_status.set("Done %d/%d: %s (%.2fs)" % (cur, total, model, val))
            else:
                self.bench_status.set("Done %d/%d: %s (ERR)" % (cur, total, model))







    # ---------- Provider CRUD ----------
    def _selected_provider(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a provider in the Providers tab.")
            return None
        name = self.tree.item(sel[0], "values")[0]
        for p in self.config["providers"]:
            if p["name"] == name:
                return p
        return None

    def _add_provider(self):
        dlg = ProviderDialog(self.root, provider=None, title="Add Provider")
        self.root.wait_window(dlg)
        if dlg.result:
            for p in self.config["providers"]:
                if p["name"].lower() == dlg.result["name"].lower():
                    messagebox.showwarning("Duplicate",
                                           "A provider with that name already exists.")
                    return
            self.config["providers"].append(dlg.result)
            self._save(quiet=True)
            self._refresh_provider_tree()
            self._refresh_tester_combos()
            self._log("Added provider: %s" % dlg.result["name"])

    def _edit_provider(self):
        prov = self._selected_provider()
        if not prov:
            return
        dlg = ProviderDialog(self.root, provider=prov, title="Edit Provider")
        self.root.wait_window(dlg)
        if dlg.result:
            idx = self.config["providers"].index(prov)
            self.config["providers"][idx] = dlg.result
            self._save(quiet=True)
            self._refresh_provider_tree()
            self._refresh_tester_combos()
            self._log("Edited provider: %s" % dlg.result["name"])

    def _delete_provider(self):
        prov = self._selected_provider()
        if not prov:
            return
        if messagebox.askyesno("Delete", "Delete provider '%s'?" % prov["name"]):
            self.config["providers"].remove(prov)
            self.status_cache.pop(prov["name"], None)
            self.model_cache.pop(prov["name"], None)
            self._save(quiet=True)
            self._refresh_provider_tree()
            self._refresh_tester_combos()
            self._log("Deleted provider: %s" % prov["name"])

    def _provider_by_name(self, name):
        for p in self.config["providers"]:
            if p["name"] == name:
                return p
        return None

    # ---------- Connection testing ----------
    def _mark_busy(self, name, busy):
        if busy:
            self._busy.add(name)
        else:
            self._busy.discard(name)
        self._refresh_provider_tree()

    def _test(self, provider):
        name = provider["name"]
        self.status_cache[name] = ("test", "Testing…")
        self._mark_busy(name, True)

        def _job():
            return test_connection(
                provider.get("base_url", ""),
                provider.get("api_key", ""),
                provider.get("format", "auto"))

        def _done(result, error):
            self._mark_busy(name, False)
            if error:
                self.status_cache[name] = ("fail", str(error))
                self._log("Test FAILED for %s: %s" % (name, error), err=True)
                self._refresh_provider_tree()
                return
            ok, fmt, models, err = result
            if ok:
                count = len(models)
                self.status_cache[name] = ("ok", "%s · %d model(s)" % (fmt, count))
                if models:
                    self.model_cache[name] = models
                self._log("Test OK for %s (%s, %d models): %s"
                          % (name, fmt, count, ", ".join(models[:5])), ok=True)
            else:
                self.status_cache[name] = ("fail", err or "unknown error")
                self._log("Test FAILED for %s: %s" % (name, err), err=True)
            self._refresh_provider_tree()

        self.worker.submit(_job, _done)

    def _test_all(self):
        for p in list(self.config["providers"]):
            self._test(p)

    def _test_selected(self):
        prov = self._selected_provider()
        if prov:
            self._test(prov)

    # ---------- Models ----------
    def _fetch_for_provider(self, provider, done):
        name = provider["name"]
        self.status_cache[name] = ("test", "Fetching models…")
        self._mark_busy(name, True)

        def _job():
            return list_models(provider.get("base_url", ""),
                               provider.get("api_key", ""),
                               provider.get("format", "auto"))

        def _on_done(result, error):
            self._mark_busy(name, False)
            if error:
                self.status_cache[name] = ("fail", str(error))
                self._log("Fetch models FAILED for %s: %s" % (name, error), err=True)
                self._refresh_provider_tree()
                if done:
                    done(result, error)
                return
            self.model_cache[name] = result
            self.status_cache[name] = ("ok", "connected · %d model(s)" % len(result))
            self._log("Fetched %d model(s) for %s: %s"
                      % (len(result), name, ", ".join(result[:5])))
            self._refresh_provider_tree()
            if done:
                done(result, error)
            if self.tester_provider.get() == name:
                self._populate_model_combo(name)

        self.worker.submit(_job, _on_done)

    def _fetch_models(self):
        prov = self._selected_provider()
        if prov:
            self._fetch_for_provider(prov, None)

    def _fetch_models_from_tab(self):
        name = self.models_provider.get()
        prov = self._provider_by_name(name)
        if prov:
            self._fetch_for_provider(prov, self._refresh_models_list)

    def _refresh_models_list(self, result=None, error=None):
        for i in self.models_list.get_children():
            self.models_list.delete(i)
        name = self.models_provider.get()
        models = self.model_cache.get(name, [])
        for m in models:
            self.models_list.insert("", "end", values=(m,))
        self._log("Models list refreshed for %s (%d entries)" % (name, len(models)))

    def _copy_selected_model(self):
        sel = self.models_list.selection()
        if not sel:
            return
        model = self.models_list.item(sel[0], "values")[0]
        copy_to_clipboard(self.root, model)
        self._log("Copied model to clipboard: %s" % model)

    # ---------- Model tester ----------
    def _refresh_tester_combos(self):
        names = [p["name"] for p in self.config["providers"]]
        self.tester_provider["values"] = names
        self.models_provider["values"] = names
        if names:
            if not self.tester_provider.get():
                self.tester_provider.set(names[0])
            if not self.models_provider.get():
                self.models_provider.set(names[0])
        self._populate_model_combo(self.tester_provider.get())

    def _populate_model_combo(self, name):
        models = self.model_cache.get(name, [])
        self.tester_model["values"] = models
        prov = self._provider_by_name(name)
        if models and not self.tester_model.get():
            self.tester_model.set(models[0])
        elif prov and prov.get("default_model"):
            self.tester_model.set(prov["default_model"])
        # Apply provider-specific defaults for temperature / max_tokens
        if prov:
            if prov.get("default_temperature"):
                try:
                    self.var_temp.set(str(float(prov["default_temperature"])))
                except (ValueError, TypeError):
                    pass
            if prov.get("default_max_tokens"):
                try:
                    self.var_max_tokens.set(str(int(prov["default_max_tokens"])))
                except (ValueError, TypeError):
                    pass

    def _load_models_for_tester(self):
        name = self.tester_provider.get()
        prov = self._provider_by_name(name)
        if prov:
            if self.model_cache.get(name):
                self._populate_model_combo(name)
                self._log("Loaded %d cached model(s) for %s" % (len(self.model_cache[name]), name))
            else:
                self._fetch_for_provider(prov, lambda r, e: self._populate_model_combo(name))

    def _run_test(self):
        name = self.tester_provider.get()
        prov = self._provider_by_name(name)
        if not prov:
            messagebox.showwarning("No provider", "Add a provider first.")
            return
        model = self.tester_model.get().strip()
        if not model:
            messagebox.showwarning("No model", "Please choose / type a model to test.")
            return
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("No prompt", "Please enter a prompt.")
            return
        try:
            max_tokens = int(self.var_max_tokens.get())
            temperature = float(self.var_temp.get())
        except ValueError:
            messagebox.showerror("Bad value", "Max tokens and temperature must be numbers.")
            return

        self.run_btn.config(state="disabled", text="Running…")
        self.response.delete("1.0", "end")
        self.metrics.set("")
        provider_snapshot = dict(prov)
        prompt_for_history = prompt

        if self.var_stream.get():
            self._run_test_stream(prov, model, prompt, max_tokens, temperature)
            return

        def _job():
            return chat(provider_snapshot, model, prompt, max_tokens, temperature)

        def _done(result, error):
            self.run_btn.config(state="normal", text="Run Test")
            if error:
                self.metrics.set("ERROR")
                self.response.insert("end", "Test failed:\n%s" % error)
                self._log("Model test failed (%s / %s): %s" % (name, model, error), err=True)
                hist.add(name, model, prompt_for_history, None, {}, "", ok=False, error=str(error))
                self._refresh_stats()
                return
            text, raw, usage, latency, fmt = result
            self.response.delete("1.0", "end")
            self.response.insert("end", text)
            usage_str = self._format_usage(usage)
            self.metrics.set("OK · %s · format=%s · %s"
                             % (self._fmt_secs(latency), fmt, usage_str))
            self._log("Model test OK (%s / %s), latency %.2fs, %s"
                      % (name, model, latency, usage_str), ok=True)
            hist.add(name, model, prompt_for_history, latency, usage, fmt, ok=True)
            self._refresh_stats()

        self.worker.submit(_job, _done)

    def _run_test_stream(self, prov, model, prompt, max_tokens, temperature):
        name = prov["name"]
        prov_snap = dict(prov)

        def job():
            text = ""
            usage = {}
            fmt = ""
            start = time.time()
            try:
                for kind, val in chat_stream(prov_snap, model, prompt,
                                             max_tokens, temperature):
                    if kind == "fmt":
                        fmt = val
                    elif kind == "text":
                        text += val
                        self.worker.queue.put((self._stream_delta, val, None))
                    elif kind == "usage":
                        usage = val or {}
                latency = time.time() - start
                self.worker.queue.put((self._stream_finished,
                                       (text, usage, latency, fmt), None))
            except Exception as e:
                self.worker.queue.put((self._stream_finished, None, e))

        threading.Thread(target=job, daemon=True).start()
        self._log("Streaming test started (%s / %s)." % (name, model))

    def _stream_delta(self, result, error):
        self.response.insert("end", result)
        self.response.see("end")

    def _stream_finished(self, result, error):
        self.run_btn.config(state="normal", text="Run Test")
        if error:
            self.metrics.set("ERROR")
            self.response.insert("end", "\n\n[stream failed: %s]" % error)
            self._log("Stream test failed: %s" % error, err=True)
            return
        text, usage, latency, fmt = result
        usage_str = self._format_usage(usage)
        self.metrics.set("OK · %s · format=%s · %s"
                         % (self._fmt_secs(latency), fmt, usage_str))
        self._log("Stream test OK (%s), latency %.2fs, %s"
                  % (fmt, latency, usage_str), ok=True)
        name = self.tester_provider.get()
        model = self.tester_model.get().strip()
        prompt = self.prompt.get("1.0", "end").strip()
        hist.add(name, model, prompt, latency, usage, fmt, ok=True)
        self._refresh_stats()

    # ---------- Side-by-side compare (feature #8) ----------
    def _open_compare(self):
        name = self.tester_provider.get()
        prov = self._provider_by_name(name)
        if not prov:
            messagebox.showwarning("No provider", "Pick a provider first.")
            return
        model_a = self.tester_model.get().strip()
        if not model_a:
            messagebox.showwarning("No model", "Pick a model first.")
            return
        model_b = tk.StringVar()
        dlg = tk.Toplevel(self.root)
        dlg.title("Compare models")
        dlg.transient(self.root)
        dlg.grab_set()
        body = ttk.Frame(dlg, padding=12)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Model A (current): %s" % model_a).pack(anchor="w", pady=2)
        ttk.Label(body, text="Model B:").pack(anchor="w", pady=(8, 2))
        cb = ttk.Combobox(body, textvariable=model_b, state="normal", width=48)
        cb.pack(anchor="w")
        models = self.model_cache.get(name, [])
        cb["values"] = models
        if models and len(models) > 1:
            model_b.set(models[1] if models[0] != model_a else models[0])
        elif models:
            model_b.set(models[0])
        ttk.Label(body, text="Uses the same prompt from the Model Tester tab.",
                  foreground="gray").pack(anchor="w", pady=(8, 0))
        status = tk.StringVar(value="")
        st = ttk.Label(body, textvariable=status, foreground="#0a7d33")
        st.pack(anchor="w", pady=(6, 0))

        def do_compare():
            mb = model_b.get().strip()
            if not mb:
                messagebox.showwarning("No model B", "Pick a second model.")
                return
            if mb == model_a:
                messagebox.showwarning("Same model", "Pick a different model for B.")
                return
            prompt = self.prompt.get("1.0", "end").strip() or "Hello."
            try:
                max_tokens = int(self.var_max_tokens.get())
                temperature = float(self.var_temp.get())
            except ValueError:
                messagebox.showerror("Bad value", "Invalid numbers.")
                return
            status.set("Running both models…")
            dlg.update_idletasks()
            pa, pb = dict(prov), dict(prov)

            def job():
                ra = ("error", "n/a", str(RuntimeError("no result")))
                try:
                    ta, _, ua, la, fa = chat(pa, model_a, prompt, max_tokens, temperature)
                    ra = (ta, ("%.2fs" % la), ua)
                except Exception as e:
                    ra = ("error", "n/a", str(e))
                rb = ("error", "n/a", str(RuntimeError("no result")))
                try:
                    tb, _, ub, lb, fb = chat(pb, mb, prompt, max_tokens, temperature)
                    rb = (tb, ("%.2fs" % lb), ub)
                except Exception as e:
                    rb = ("error", "n/a", str(e))
                self.worker.queue.put((lambda res, err: self._show_compare(
                    model_a, model_b, prompt, res, prov, max_tokens, temperature),
                    (ra, rb), None))

            threading.Thread(target=job, daemon=True).start()
            dlg.destroy()

        ttk.Button(body, text="Compare", command=do_compare).pack(pady=(10, 0))

    def _show_compare(self, model_name_b, model_b_var, prompt, res, prov,
                      max_tokens, temperature):
        # No-op body (results handled by _compare_result_builder).
        self._compare_result(model_name_b, prompt, res, prov)

    def _compare_result(self, model_a, prompt, res, prov):
        (ta, la, ua), (tb, lb, ub) = res
        win = tk.Toplevel(self.root)
        win.title("Compare: %s vs %s" % (model_a, res and ""))
        win.geometry("1000x600")
        win.transient(self.root)
        tf = ttk.Frame(win)
        tf.pack(fill="both", expand=True, padx=6, pady=6)
        for i, (title, txt, lat) in enumerate([("Model A", ta, la), ("Model B", tb, lb)]):
            f = ttk.Frame(tf)
            f.pack(side="left", fill="both", expand=True, padx=4)
            ttk.Label(f, text="%s   [%s]" % (title, lat), font=("", 9, "bold")).pack(anchor="w")
            box = scrolledtext.ScrolledText(f, wrap="word")
            box.pack(fill="both", expand=True)
            box.insert("1.0", "ERROR" if txt == "error" else txt)


    @staticmethod
    def _fmt_secs(s):
        if s < 60:
            return "%.2fs" % s
        return "%dm %02ds" % (int(s // 60), int(s % 60))

    @staticmethod
    def _format_usage(usage):
        if not usage:
            return "usage n/a"
        parts = []
        for k in ("input_tokens", "prompt_tokens", "output_tokens", "completion_tokens",
                  "total_tokens"):
            if usage.get(k) is not None:
                parts.append("%s=%s" % (k, usage[k]))
        return "usage: " + ", ".join(parts) if parts else "usage n/a"

    # ---------- Provider tree refresh ----------
    def _refresh_provider_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in self.config["providers"]:
            name = p["name"]
            status = self.status_cache.get(name)
            if status and status[0] == "ok":
                status_txt, tag = "✔ " + status[1], "ok"
            elif status and status[0] == "fail":
                status_txt, tag = "✘ " + status[1], "fail"
            elif status and status[0] == "test":
                status_txt, tag = "⏳ " + status[1], ""
            else:
                status_txt, tag = "— not tested", ""
            nmodels = len(self.model_cache.get(name, []))
            key = p.get("api_key") or ""
            key_disp = ("••••" + key[-4:]) if key else "(none)"
            self.tree.insert("", "end", values=(
                name, p.get("format", "auto"), p.get("base_url", ""),
                key_disp, nmodels, status_txt), tags=(tag,))
        try:
            self._rebuild_prov_pass_menu()
        except Exception:
            pass

    # ---------- Logs / save / reload / folder ----------
    def _log(self, msg, err=False, ok=False):
        ts = time.strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        tag = "err" if err else ("ok" if ok else "")
        self.log_text.insert("end", "[%s] " % ts, tag)
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _save(self, quiet=False):
        save_config(self.config)
        if not quiet:
            self._log("Config saved to %s" % CONFIG_PATH)

    def _reload(self):
        self.config = load_config()
        self.status_cache.clear()
        self.model_cache.clear()
        self._refresh_provider_tree()
        self._refresh_tester_combos()
        self._log("Config reloaded from disk.")

    def _reset_all(self):
        if not messagebox.askyesno(
                "Reset All",
                "This will reset:\n"
                "  • Providers to built-in defaults\n"
                "  • Claude Code profiles (delete all custom profiles)\n"
                "  • Test history\n"
                "  • Cached models / status\n\n"
                "Continue?"):
            return
        # Reset config to defaults
        self.config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.status_cache.clear()
        self.model_cache.clear()
        # Reset Claude profiles
        try:
            import shutil
            profiles_dir = cp.profiles_dir()
            if os.path.isdir(profiles_dir):
                for entry in os.listdir(profiles_dir):
                    full = os.path.join(profiles_dir, entry)
                    if os.path.isdir(full):
                        shutil.rmtree(full, ignore_errors=True)
                # Reset settings.json active model
                settings_path = cp.user_settings_path()
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except Exception:
                            data = {}
                    data.pop("activeModel", None)
                    with open(settings_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
        except Exception as e:
            self._log("Claude reset failed: %s" % e, err=True)
        # Clear history
        try:
            hist.save([])
        except Exception:
            pass
        self._save(quiet=True)
        self._refresh_provider_tree()
        self._refresh_tester_combos()
        self._refresh_claude_tab()
        self._refresh_stats()
        self._log("Reset all to defaults.", ok=True)
        messagebox.showinfo("Reset Complete",
                            "Providers, Claude profiles, and history have been reset.")

    def _open_folder(self):
        import subprocess
        subprocess.Popen(["explorer", APP_DIR])


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()





