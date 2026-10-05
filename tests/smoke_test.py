"""Smoke test for a RUNNING adapter. Standard library only.

    python tests/smoke_test.py                      # against http://127.0.0.1:8765
    python tests/smoke_test.py --token demo --model sonnet
    python tests/smoke_test.py --stub               # extra assertions for the maintainer's offline stub (not in this release)
    python tests/smoke_test.py --check-only         # status + model list only: no model request, no usage

Against the real CLI this sends a handful of tiny prompts, i.e. it spends a little subscription usage.
"""
import argparse
import base64
import http.client
import json
import struct
import sys
import zlib
from urllib.parse import urlparse


def png_data_url(w, h, rgb):
    """Solid-colour PNG as a data: URL, built by hand so the test needs no Pillow."""
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()

if __name__ != "__main__":
    raise ImportError("smoke_test.py is a script, not a module: importing it would run the tests")

ap = argparse.ArgumentParser()
ap.add_argument("--base-url", default="http://127.0.0.1:8765")
ap.add_argument("--token", default="demo")
ap.add_argument("--model", default="sonnet")
ap.add_argument("--stub", action="store_true")
ap.add_argument("--check-only", action="store_true", help="status and model list only; sends no prompt")
args = ap.parse_args()
base = urlparse(args.base_url)
failures = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def call(method, path, body=None, headers=None, auth=True):
    conn = http.client.HTTPConnection(base.hostname, base.port, timeout=300)
    hdrs = {"Content-Type": "application/json", **({"Authorization": f"Bearer {args.token}"} if auth else {}),
            **(headers or {})}
    conn.request(method, path, json.dumps(body) if body is not None else None, hdrs)
    resp = conn.getresponse()
    return resp.status, resp.getheader("content-type", ""), resp.read().decode("utf-8")


def stub_report(text):
    return json.loads(text.split("STUB-CLI-REPORT ", 1)[1].split("\n", 1)[0])


print("GET /status")
status, _, raw = call("GET", "/status")
info = json.loads(raw)
print("  ", raw)
check("status is 200 and logged in", status == 200 and info.get("ok") is True, raw)
check("status does not expose account identity", "@" not in raw)
status, _, raw = call("GET", "/status", auth=False)
check("status answers without the API key (diagnostics only)", status == 200, f"{status} {raw[:120]}")

print("GET /v1/models and /models")
for path in ("/v1/models", "/models"):
    status, _, raw = call("GET", path)
    ids = [m["id"] for m in json.loads(raw).get("data", [])]
    check(f"{path} lists sonnet", status == 200 and "sonnet" in ids, raw)

if args.check_only:
    print()
    print("CHECK-ONLY: adapter reachable, CLI logged in, no prompt sent." if not failures else f"{len(failures)} FAILED: {failures}")
    sys.exit(1 if failures else 0)

print("POST /v1/chat/completions  (stream=false)")
status, _, raw = call("POST", "/v1/chat/completions", {
    "model": args.model, "max_tokens": 64, "temperature": 0,
    "messages": [{"role": "user", "content": "Reply with exactly the word: pong"}]})
obj = json.loads(raw)
check("status 200", status == 200, raw[:300])
text = (obj.get("choices") or [{}])[0].get("message", {}).get("content", "")
print("   reply:", text[:160].replace("\n", " "))
check("object is chat.completion with content", obj.get("object") == "chat.completion" and bool(text))
check("finish_reason is stop", (obj.get("choices") or [{}])[0].get("finish_reason") == "stop")
usage = obj.get("usage") or {}
check("usage is populated", usage.get("prompt_tokens", 0) > 0 and usage.get("completion_tokens", 0) > 0
      and usage.get("total_tokens") == usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0), str(usage))
if args.stub:
    rep = stub_report(text)
    check("stub: tools disabled, max-turns 1, safe mode, never --bare",
          rep["tools_disabled"] and rep["max_turns"] == "1" and rep["safe_mode"] and not rep["bare"], str(rep))
    # Set by the adapter on purpose, or kept on purpose when the user has them set (adapter.KEEP_ENV).
    deliberate = {"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_GIT_BASH_PATH"}
    check("stub: no ANTHROPIC_/CLAUDE_CODE_/ADAPTER_ env reaches the CLI (except the deliberate ones)",
          set(rep["leaked_env"]) <= deliberate, str(rep["leaked_env"]))
    check("stub: cwd is empty", rep["cwd_entries"] == 0, str(rep))
    check("stub: default system prompt + adapter note used",
          rep["system_head"].startswith("You are an assistant embedded in COMSOL") and rep["system_has_adapter_note"])
    check("stub: cache tokens folded into prompt_tokens", usage.get("prompt_tokens") == 1212, str(usage))


def stream(path, body):
    status, ctype, raw = call("POST", path, body)
    events = [line[6:] for line in raw.split("\n") if line.startswith("data: ")]
    chunks = [json.loads(e) for e in events if e != "[DONE]"]
    return status, ctype, events, chunks


print("POST /chat/completions  (stream=true, multi-turn, system message, undecodable image part, no /v1 prefix)")
status, ctype, events, chunks = stream("/chat/completions", {
    "model": "", "stream": True,
    "messages": [
        {"role": "system", "content": "You are terse. SYSTEM-MARKER"},
        {"role": "user", "content": "My favourite solver is PARDISO."},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": [
            {"type": "text", "text": "Which solver did I say I like? One word."},
            {"type": "image_url", "image_url": {"url": "https://example.com/not-a-data-url.png"}}]}]})
text = "".join((c["choices"][0]["delta"].get("content") or "") for c in chunks if c.get("choices"))
print("   reply:", text[:160].replace("\n", " "))
check("status 200 text/event-stream", status == 200 and ctype.startswith("text/event-stream"), f"{status} {ctype}")
check("first chunk carries role=assistant", chunks and chunks[0]["choices"][0]["delta"].get("role") == "assistant")
check("all chunks are chat.completion.chunk", all(c.get("object") == "chat.completion.chunk" for c in chunks))
check("content arrived in more than one delta" if args.stub else "content arrived",
      sum(1 for c in chunks if c.get("choices") and c["choices"][0]["delta"].get("content")) > (1 if args.stub else 0))
check("a chunk has finish_reason=stop", any(c.get("choices") and c["choices"][0].get("finish_reason") == "stop" for c in chunks))
check("usage on the finish chunk (no stream_options sent)",
      any(c.get("usage") and c.get("choices") for c in chunks), str(chunks[-1:] if chunks else ""))
check("stream ends with [DONE]", bool(events) and events[-1] == "[DONE]")
if args.stub:
    rep = stub_report(text)
    check("stub: empty model id mapped to the default", rep["model"] == "sonnet", str(rep["model"]))
    check("stub: system message forwarded", rep["system_head"].startswith("You are terse. SYSTEM-MARKER"))
    check("stub: prompt ends with reply instruction", rep["prompt_tail"].endswith("Reply only as the assistant to the current user message."))
    check("stub: undecodable image -> placeholder, plain-text stdin", rep["input_mode"] == "text" and rep["images"] == [], str(rep))
else:
    check("model used the flattened history", "pardiso" in text.lower(), text[:200])

print("POST /v1/chat/completions  (stream=true, real image: 16x16 red PNG as data: URL)")
status, _, events, chunks = stream("/v1/chat/completions", {
    "model": args.model, "stream": True,
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "What is the dominant colour of this image? Answer with one word."},
        {"type": "image_url", "image_url": {"url": png_data_url(16, 16, (220, 30, 30))}}]}]})
text = "".join((c["choices"][0]["delta"].get("content") or "") for c in chunks if c.get("choices"))
print("   reply:", text[:120].replace("\n", " "))
check("status 200 with content", status == 200 and bool(text), f"{status} {text[:120]}")
if args.stub:
    rep = stub_report(text)
    check("stub: image delivered as a stream-json image block",
          rep["input_mode"] == "stream-json" and len(rep["images"]) == 1 and rep["images"][0]["dims"] == [16, 16], str(rep["images"]))
else:
    check("model saw the image (says red)", "red" in text.lower(), text[:120])

if args.stub:
    print("POST /v1/chat/completions  (image downscaling: 2400x120 PNG in conversation history)")
    status, _, events, chunks = stream("/v1/chat/completions", {
        "model": "sonnet", "stream": True,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "Here is a plot."},
                                         {"type": "image_url", "image_url": {"url": png_data_url(2400, 120, (0, 90, 200))}}]},
            {"role": "assistant", "content": "I see it."},
            {"role": "user", "content": "What was the colour?"}]})
    text = "".join((c["choices"][0]["delta"].get("content") or "") for c in chunks if c.get("choices"))
    rep = stub_report(text)
    check("stub: history image kept in place and downscaled to 1568 px",
          status == 200 and len(rep["images"]) == 1 and rep["images"][0]["dims"] == [1568, 78], str(rep["images"]))
    check("stub: history text still wraps the image", rep["prompt_head"].startswith("<conversation_history>")
          and rep["prompt_tail"].endswith("Reply only as the assistant to the current user message."), str(rep))

print("POST /v1/chat/completions  (stream=true, stream_options.include_usage)")
status, _, events, chunks = stream("/v1/chat/completions", {
    "model": args.model, "stream": True, "stream_options": {"include_usage": True},
    "messages": [{"role": "user", "content": "Say hi in three words."}]})
check("usage rides a final chunk with empty choices (OpenAI spec)",
      status == 200 and len(chunks) >= 2 and chunks[-1].get("choices") == [] and chunks[-1].get("usage", {}).get("total_tokens", 0) > 0,
      str(chunks[-1:] if chunks else ""))

if args.stub:
    print("Per-request effort: Model id suffix and reasoning_effort field")
    for model_id, body_extra, want_effort, want_off, label in (
            ("sonnet:low", {}, "low", False, "sonnet:low -> --effort low"),
            ("fable:off", {}, "medium", True, "fable:off -> MAX_THINKING_TOKENS=0, default effort kept"),
            ("sonnet", {"reasoning_effort": "high"}, "high", False, "reasoning_effort field -> --effort high"),
            ("sonnet:bogus", {}, "medium", False, "unknown suffix ignored")):
        status, _, raw = call("POST", "/v1/chat/completions",
                              {"model": model_id, "messages": [{"role": "user", "content": "x"}], **body_extra})
        rep = stub_report(json.loads(raw)["choices"][0]["message"]["content"])
        # thinking_off is only asserted for ":off": the adapter's own environment may already carry
        # MAX_THINKING_TOKENS=0, which legitimately passes through to every request.
        check(f"stub: {label}", status == 200 and rep["effort"] == want_effort and (rep["thinking_off"] or not want_off),
              f"effort={rep['effort']} thinking_off={rep['thinking_off']}")
        if model_id == "fable:off":
            check("stub: model part of the suffix form is honoured", rep["model"] == "fable", rep["model"])
    status, _, raw = call("POST", "/v1/chat/completions",
                          {"model": "Default:low", "messages": [{"role": "user", "content": "x"}]})
    rep = stub_report(json.loads(raw)["choices"][0]["message"]["content"]) if status == 200 else {}
    check("stub: Default:low -> Claude Code's own default model, effort low",
          rep.get("model") == "default" and rep.get("effort") == "low", f"{status} {rep or raw[:120]}")

print("Guard rails")
conn = http.client.HTTPConnection(base.hostname, base.port, timeout=30)
conn.putrequest("POST", "/v1/chat/completions")
conn.putheader("Authorization", f"Bearer {args.token}")
conn.putheader("Content-Type", "application/json")
conn.putheader("Content-Length", str(30 * 1024 * 1024))  # claims 30 MB; the adapter must refuse before reading it
conn.endheaders()
try:
    conn.send(b'{"messages": [')
    resp = conn.getresponse()
    status, raw = resp.status, resp.read().decode("utf-8", "replace")
except OSError as e:  # the server may close the socket right after answering
    status, raw = -1, str(e)
check("oversized body -> 413 before it is read", status == 413, f"{status} {raw[:120]}")


def chunked_body(total, size=64 * 1024):  # no Content-Length: the adapter has to count real bytes
    sent = 0
    while sent < total:
        piece = min(size, total - sent)
        sent += piece
        yield b" " * piece


conn = http.client.HTTPConnection(base.hostname, base.port, timeout=60)
try:
    conn.request("POST", "/v1/chat/completions", body=chunked_body(25 * 1024 * 1024 + 64 * 1024),
                 headers={"Authorization": f"Bearer {args.token}", "Content-Type": "application/json",
                          "Transfer-Encoding": "chunked"}, encode_chunked=True)
    resp = conn.getresponse()
    status, raw = resp.status, resp.read().decode("utf-8", "replace")
except OSError as e:
    status, raw = -1, str(e)
check("oversized chunked body (no Content-Length) -> 413", status == 413, f"{status} {raw[:120]}")
status, _, raw = call("POST", "/v1/chat/completions", {"model": "sonnet", "messages": [{"role": "user", "content": "x"}]},
                      headers={"Origin": "https://evil.example"})
check("browser-origin request refused with 403 before any spend", status == 403, f"{status} {raw[:120]}")
status, _, raw = call("POST", "/v1/chat/completions", {"model": "sonnet"})
check("missing messages -> 400 OpenAI-style error", status == 400 and "error" in json.loads(raw), raw[:120])
status, _, raw = call("POST", "/v1/chat/completions", {"model": "opus5", "messages": [{"role": "user", "content": "x"}]})
check("unknown Model id -> 400 naming the valid choices, before any spend",
      status == 400 and "Unknown Model id" in raw and "sonnet" in raw, f"{status} {raw[:160]}")
status, _, raw = call("POST", "/v1/chat/completions", {"model": "sonnet", "stream_options": "yes", "messages": []})
check("non-object stream_options does not crash the request", status == 400, f"{status} {raw[:120]}")
if args.stub:  # skipped against the real CLI only to avoid one more paid prompt
    status, _, raw = call("POST", "/v1/v1/chat/completions", {"model": "sonnet", "messages": [{"role": "user", "content": "x"}]})
    check("doubled prefix /v1/v1/chat/completions is still served", status == 200, f"{status} {raw[:120]}")
status, _, raw = call("GET", "/v1/embeddings")
check("unknown path -> 404 OpenAI-style error", status == 404 and "error" in json.loads(raw), raw[:120])

print()
print("ALL PASSED" if not failures else f"{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
