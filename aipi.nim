# ═══════════════════════════════════════════════════════════════
#   AIPI — Native Nim Package Launcher
#   Compiles to ultra-compact binary (~150KB): aipi.exe
#   Developed by gnonymous
# ═══════════════════════════════════════════════════════════════

import os, osproc, strutils, browsers

const PORT = "11434"
const APP_NAME = "AIPI — AI Protocol Interface"

proc findPython(): string =
  for cmd in ["python", "python3", "py"]:
    if execCmdEx(cmd & " --version").exitCode == 0:
      return cmd
  return ""

proc main() =
  echo "=========================================================="
  echo "  🌐 " & APP_NAME & " Native Launcher"
  echo "  Universal AI Gateway & Model Router"
  echo "=========================================================="

  let py = findPython()
  if py == "":
    echo "❌ Error: Python 3.8+ is required. Please install Python to run AIPI."
    quit(1)

  let appDir = getAppDir()
  let serverScript = appDir / "gateway_server.py"

  if not fileExists(serverScript):
    echo "❌ Error: gateway_server.py not found in " & appDir
    quit(1)

  echo "🚀 Launching AIPI Gateway Server on port " & PORT & "..."
  
  # Launch gateway process in background
  let p = startProcess(py, appDir, [serverScript, "run", PORT], nil, {poParentStreams, poUsePath})

  # Open web UI in default browser
  sleep(1500)
  openDefaultBrowser("http://localhost:" & PORT)

  discard p.waitForExit()

when isMainModule:
  main()
