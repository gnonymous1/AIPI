# AI Model Manager

A self-contained Windows desktop app (Python + Tkinter) to manage your AI
model providers: **base URL, API key, and models** — with live **connection
status**, **model browsing**, and a built-in **model tester**.

No extra installs needed (uses Python stdlib + `requests`, which is already
installed).

## Launch
Double-click **`Start AI Model Manager.bat`** (there is also an **"AI Model Manager"**
desktop shortcut), or run `python ai_model_manager.py` from this folder.

## Features
- **Providers tab** — add / edit / delete providers with:
  - Display name
  - Base URL (e.g. `http://127.0.0.1:11434`)
  - API key (masked, with a *Show* toggle while editing)
  - API format: `auto` (tries both), `openai`, or `anthropic`
  - Default model + notes
  - **Test Selected / Test All** live connection checks. Green ✔ = connected,
    red ✘ = failed (shows HTTP status / error), ⏳ while testing.
- **Models tab** — fetch the model list from a provider (`/v1/models`),
  browse, and copy any model to the clipboard.
- **Model Tester tab** — pick a provider + model (auto-load from cached/fetched
  list or type any model id), set max tokens & temperature, send a prompt, and
  see the response plus **latency** and **token usage**. Optional **Stream tokens**
  mode shows the answer token-by-token, and **Compare…** runs the same prompt on
  two models side-by-side.
- **Benchmark tab** — run a prompt across **all** of a provider's models and get a
  ranked table (fastest first) with latency + token usage. Every run is saved.
- **Stats & History tab** — aggregates of all test/benchmark runs (counts,
  OK/failed, avg/min/max latency, total tokens) plus a scrollable recent-runs table.
- **Claude Profiles tab** — shows **all models already configured in Claude Code**
  (reads `~/.claude/profiles`), highlights the currently active one, and can
  **install a full custom Claude profile** from any provider. You can **Set as
  Active** (writes into `~/.claude/settings.json`), **Import settings**, add
  **notes**, **rename**, delete, copy a model id, or open the profiles folder.
- **Tray & hotkey** — closing minimizes to a floating tray bar; **Ctrl+Alt+M**
  opens a quick model switcher.
- **"Pass to" CLI** — right at the Model Tester, a **Pass to ▾** menu sends the
  current provider+model to a CLI tool (Claude, Cline, OpenCode, kilo, Hermes, or
  any custom tool you add) — it opens a new console pre-configured with that
  provider's URL/key/model via env vars. "Pass to Claude" also installs & activates
  a Claude Code profile automatically.
- **Omniroute service** — toolbar **Omniroute** button checks status, launches, or
  runs a fix; plus a standalone **Omniroute Launch & Fix** desktop script.
- **Provider presets** — one-click templates for OpenRouter / Together / SambaNova.
- **Portable export/import** — save the whole setup as JSON and restore it later.
- **Auto-test** — all providers are connection-tested automatically on launch.
- **Logs tab** — timestamped activity / errors.
- Config is persisted to **`config.json`** (auto-saved). A toolbar lets you
  Save, Reload, or open the config folder.

## Endpoints used
| Format   | Models              | Chat                       |
|----------|---------------------|----------------------------|
| openai   | `GET /v1/models`    | `POST /v1/chat/completions`|
| anthropic| `GET /v1/models`    | `POST /v1/messages`        |

## Files
- `ai_model_manager.py` — the GUI (Tkinter).
- `api_client.py` — networking (connection test, model list, chat).
- `config.json` — your saved providers (created/edited by the app).
- `Start AI Model Manager.bat` — one-click launcher.
