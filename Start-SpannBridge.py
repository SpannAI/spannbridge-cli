"""Start SpannBridge after checking its prerequisites.

    python Start-SpannBridge.py --check-only          check everything; start nothing, send nothing
    python Start-SpannBridge.py                       defaults: port 8765, model sonnet, effort medium
    python Start-SpannBridge.py --token demo --thinking-off
    python Start-SpannBridge.py --model fable --effort low --timeout-seconds 300

The launcher is Python rather than a PowerShell script on purpose: Windows' PowerShell
execution policy doesn't apply, so nothing has to be bypassed or changed.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EFFORTS = ("low", "medium", "high", "xhigh", "max", "default")


def main() -> int:
    ap = argparse.ArgumentParser(description="Check prerequisites, then start SpannBridge.")
    ap.add_argument("--check-only", action="store_true", help="check prerequisites only; start nothing")
    ap.add_argument("--port", type=int, default=8765, help="port on 127.0.0.1 (default 8765)")
    ap.add_argument("--token", default="", help="API key the Chatbot must send (default: accept any)")
    ap.add_argument("--model", default="sonnet", help="model to use when the Chatbot's Model id is empty")
    ap.add_argument("--effort", choices=EFFORTS, default="medium", help="default effort (default medium)")
    ap.add_argument("--thinking-off", action="store_true", help="turn thinking off (MAX_THINKING_TOKENS=0)")
    ap.add_argument("--timeout-seconds", type=int, default=180, help="per-request limit (default 180)")
    ap.add_argument("--keepalive-seconds", type=float, default=15, help="keep-alive interval; 0 = off")
    a = ap.parse_args()
    if not 1 <= a.port <= 65535 or not 10 <= a.timeout_seconds <= 3600 or not 0 <= a.keepalive_seconds <= 600:
        ap.error("--port 1-65535, --timeout-seconds 10-3600, --keepalive-seconds 0-600")

    if sys.version_info < (3, 10):
        print(f"Python 3.10 or newer is required; this is {sys.version.split()[0]}.")
        return 1
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        print("Python packages are missing. Run:  python -m pip install -r requirements.txt")
        return 1

    sys.path.insert(0, str(HERE))
    import adapter  # same Claude Code discovery and environment scrubbing as the adapter itself

    adapter.CWD_DIR.mkdir(parents=True, exist_ok=True)
    binary = adapter.find_claude()
    if not binary:
        print("Claude Code not found. Install it:  irm https://claude.ai/install.ps1 | iex\n"
              "then open a new window (README step 1), or set CLAUDE_BIN to the full path of claude.exe.")
        return 1
    adapter.STATE["bin"] = binary
    try:
        version = adapter.run_cli_sync(["--version"]).stdout.strip() or "?"
    except Exception as e:  # noqa: BLE001
        print(f"Claude Code was found at {binary} but could not run: {e}")
        return 1
    signed_in = bool(adapter.auth_status().get("ok"))
    with socket.socket() as probe:
        port_busy = probe.connect_ex(("127.0.0.1", a.port)) == 0
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("Note: ANTHROPIC_API_KEY is set; SpannBridge withholds it from Claude Code so your subscription is used.")

    if a.check_only:
        print(f"Python      : {sys.version.split()[0]}")
        print(f"Claude Code : {version}  ({binary})")
        print(f"Signed in   : {'yes' if signed_in else 'NO - run: claude auth login'}")
        print(f"Port {a.port:<6} : {'IN USE - is SpannBridge already running? Use --port' if port_busy else 'free'}")
        if signed_in and not port_busy:
            print("PASS: ready to start. Nothing was started and no request was sent.")
            return 0
        print("Fix the item(s) above, then run this check again.")
        return 1

    if not signed_in:
        print("WARNING: Claude Code is not signed in. Run:  claude auth login   "
              "(SpannBridge starts, but requests fail until then)")
    env = dict(os.environ)
    env.update(ADAPTER_PORT=str(a.port), ADAPTER_DEFAULT_MODEL=a.model, ADAPTER_TIMEOUT=str(a.timeout_seconds),
               ADAPTER_KEEPALIVE_S=str(a.keepalive_seconds), ADAPTER_EFFORT=a.effort)
    env["CLAUDE_BIN"] = binary
    token = a.token.strip()
    for name, value in (("ADAPTER_TOKEN", token), ("MAX_THINKING_TOKENS", "0" if a.thinking_off else "")):
        if value:
            env[name] = value
        else:
            env.pop(name, None)
    print(f"COMSOL Preferences -> Chatbot:  Base URL http://127.0.0.1:{a.port}/v1   Model id default   "
          f"Context length 128000   API key {token or '(leave blank)'}   Tool calling off", flush=True)
    try:
        return subprocess.call([sys.executable, str(HERE / "adapter.py")], env=env, cwd=str(HERE))
    except KeyboardInterrupt:  # Ctrl+C reaches the adapter too; just exit quietly
        return 0


if __name__ == "__main__":
    sys.exit(main())
