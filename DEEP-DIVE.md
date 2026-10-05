# SpannBridge deep dive for developers

**Audience.**  This file is for a developer, or an AI coding assistant, who is about to modify SpannBridge or adapt it to another AI provider, for example xAI Grok or Meta Muse.  End users should read `README.md` instead.

**Status.**  Written for release 1.0 of `spannbridge-cli`, October 2026.  Items marked *verified* were observed on Windows 11 with COMSOL Multiphysics® 6.4 and Claude Code 2.1.275 to 2.1.280.  Items marked *unverified* come from documentation or research and were not run.  This file lists the problems that were solved and the notes for adapting SpannBridge.  The design rationale, the full verification log, and the offline test suite are not part of this release.

This repository is neither developed by nor endorsed by COMSOL AB or Anthropic PBC.  See *Publisher, trademarks, and affiliation* in README.md.  COMSOL and COMSOL Multiphysics are registered trademarks of COMSOL AB.  Anthropic, Claude, and Claude Code are trademarks of Anthropic PBC.  Other names in this file, such as OpenAI, Codex, xAI, Grok, Meta, Muse, Google, Gemini, and Antigravity, are trademarks of their respective owners.

Most items follow the order symptom, cause, fix.  Read section 1 before you write any code.

## 0. Two integration patterns

| | Pattern A.  One command-line run per request (this repository) | Pattern B.  One long-running session server (`spannbridge-appserver`) |
|---|---|---|
| Upstream | `claude -p` reads the prompt on stdin, writes JSON events on stdout (one per line), and exits. | `codex app-server` speaks JSON-RPC over stdin and stdout.  Each request uses one temporary thread. |
| State | None.  The client resends the whole conversation every time. | One server process for the adapter's lifetime. |
| Cost per request | Process start, about 0.8 s for Claude Code (measured). | Calls to start and end the thread. |
| Effect of a crash | One request fails. | Every request in progress fails if the server stops. |
| Candidates | Grok Build `grok -p`, Muse Code `muse exec` | Muse Code `muse serve` with `@muse-code/sdk` |

Pattern A is simpler to make reliable.  Pattern B allows finer control over approvals, answer phases, and model catalogs, but it needs a protocol state machine.  Both patterns use the same OpenAI-compatible HTTP front end.  Most client-side traps are in that front end (section 4).

## 1. Compliance rules that determine the design

These rules are design inputs.  Check them on each vendor's site again before you adapt SpannBridge.

- **Run only the vendor's official, unmodified program, signed in through the vendor's own process.**  Never read, copy, forward, or store the program's credential files or tokens.  Anthropic's Claude Code compliance page forbids third parties from collecting or passing on Claude credentials.  Meta states that the Muse Code subscription credential is "for use with Muse Code only".  xAI's subscription sign-in service rejects clients that are not on its allowlist with HTTP 403.  Running the vendor's program is therefore the only design that both works and follows the rules.
- **One user, one machine.**  Bind to `127.0.0.1` only, and do not make that setting configurable.  Refuse peers that are not on the local machine and `Host` headers that are not local.  Refuse any request that has an `Origin` header.  Otherwise a web page in the user's browser can send a request to localhost and spend the user's subscription.  An optional bearer token stops other local programs.  Compare it with `hmac.compare_digest`.
- **Remove API-key environment variables from the child process.**  If `ANTHROPIC_API_KEY` reaches Claude Code, billing moves from the subscription to the API key without any warning.  The equivalent variables for other vendors are `XAI_API_KEY`, `META_API_KEY`, and `OPENAI_API_KEY`.  Remove variables by prefix and keep an allowlist (section 3).
- **Names.**  Product and repository names must not contain vendor marks or COMSOL® marks.  The guidelines of COMSOL AB, Anthropic, and OpenAI all forbid this.  Name the vendor in a descriptive subtitle in which SpannBridge is the subject ("Connects the Chatbot window in COMSOL Multiphysics® software to Claude Code…").  The COMSOL AB guidelines also require ® on each use and a generic noun ("COMSOL Multiphysics® simulation software").  They forbid possessive, plural, hyphenated, and abbreviated forms.  Check the documentation for the possessive form before each release.

## 2. The COMSOL Multiphysics® 6.4 Chatbot as a client

All rows are *verified* from real requests, except where marked.

| Behavior | Consequence |
|---|---|
| The Chatbot appends `/chat/completions` to the Base URL.  Users type the Base URL with or without `/v1`. | Serve any path that ends in `chat/completions`.  The path `/v1/v1/chat/completions` occurs. |
| The Chatbot never calls `/models`. | The model list is for information only.  It can be static. |
| The Chatbot always sends `stream: true` and `temperature: 0.3`. | Streaming must be reliable.  A command-line program cannot apply the temperature, so the adapter only logs it. |
| The Chatbot sends its own system prompt.  It is about 300 characters long under the subject *General* and about 4,200 under *Programming*. | The *Programming* subject produced much better Java in tests.  The adapter appends its own note to whatever system prompt arrives. |
| The Chatbot resends the **entire** history every turn, including **every earlier image**. | A stateless adapter needs no extra work.  Token use grows with each image: three snapshots made each later turn about 7,800 input tokens (measured). |
| A Model Builder node attachment is COMSOL® API for Java code as plain text inside the user message.  A typical node was about 6.6 KB. | No special handling is needed. |
| A Graphics snapshot is an `image_url` part with `data:image/png;base64,…`.  Snapshots were about 1300 pixels wide and 40 to 220 KB. | Decode the image, downscale it if needed, and pass it as a native image block. |
| With *Tool calling* on, the Chatbot sends OpenAI `tools`.  Its documentation search needs the client to run the tool. | A command-line program with its own agent loop cannot return a tool call to the client.  Either ignore `tools` (this repository) or return HTTP 400 (the sibling repository). |
| *Unverified:* whether the Chatbot shows HTTP error bodies (`{"error": {"message": …}}`), and whether it shows an `{"error": …}` object inside an SSE stream. | Delay the HTTP status line until the first event arrives from upstream, so that fast failures become real HTTP errors.  After streaming starts, write errors as **reply text**, which the Chatbot always shows. |
| The token counters read `usage` from the stream. | Put `usage` on the final chunk even when `stream_options.include_usage` is absent. |
| The *Context length* setting limits input plus output for each request.  Its default is 128,000 tokens (COMSOL® documentation).  The Chatbot cannot count the input that the command-line program adds. | Keep the default in both editions, so that their Chatbot preferences are identical.  It leaves room for the program's own input: about 400 tokens for Claude Code (measured) and 9,000 to 11,500 for Codex (reported by the sibling repository). |
| The **Java Shell** compiles snippets against a predefined `model` variable, which is the open model. | A `class … main()` block compiles and never runs.  `model.save()` fails on an uncaught checked `IOException`.  A solve with no plot group shows nothing.  The adapter's prompt note covers all three cases.  The user should start from a blank model. |

## 3. Windows and process pitfalls

- **Microsoft Store Python redirects `AppData`.**  A temporary folder that Store Python creates under `%TEMP%` does not exist for a separate program such as `claude.exe`.  Using it as the working folder causes `WinError 2`.  Fix: put the scratch folder under the home folder (`~/.spannbridge-cli`).
- **Two running copies shared one temporary folder.**  Each copy deleted leftover prompt files when it started.  A second copy, for example the offline tests on another port, could therefore delete a prompt file that the first copy still needed.  The sibling repository reported the same problem in its own design.  Fix: one temporary subfolder per port, because two running copies can never share a port.  *Verified* with the stub on 2026-10-03.
- **The command-line program bundled with the Claude desktop app cannot be used from outside the app.**  It sits in a versioned, redirected folder that moves with every app update.  Fix: require the standalone installation.
- **The native Claude Code installer did not add `~/.local/bin` to PATH** on the test machine.  Fix: document the PATH command, and also look for `~/.local/bin/claude.exe` directly.
- **asyncio subprocesses need the Proactor event loop on Windows.**  `uvicorn --reload` and `--workers` select a loop that cannot start processes.  Fix: run `python adapter.py`, and refuse to start with any other loop.
- **Killing the parent process left the real worker running.**  With an npm `claude.cmd` shim, the work runs in a grandchild process.  `proc.kill()` stopped only the parent.  The grandchild kept spending tokens and kept stdout open, so the timeout never fired.  Fix: run `taskkill /T /F` on the parent first and wait for it, then call `kill()`.  The event reader also has its own read deadline, because a killed process does not guarantee end-of-file on its output.
- **Running `taskkill` after every request stalled the server.**  `taskkill` runs synchronously, and the program had usually not exited yet when the request ended.  With a stub (a small program that imitates Claude Code), `taskkill` ran at the end of 5 of 5 normal requests and took about 0.2 s each time (measured).  The whole server waited during that time, including other open replies.  Fix: after a normal result, wait up to 2 s for the program to exit by itself.  Kill the tree only if it does not exit, or if the request ended early.  Do the kill in a `finally` block, so that it still runs when the waiting task is cancelled.
- **Windows limits a command line to 32,767 characters.**  Fix: pass the system prompt with `--system-prompt-file`, never with `--system-prompt`.
- **`.cmd` shims must run through cmd.exe** (`create_subprocess_shell` with `list2cmdline`).  cmd.exe special characters such as `%`, `&`, and `^` in arguments or paths are a latent risk.  Mitigation: validate every argument.  The model name must match a strict pattern so that it can never become a flag.  One known gap remains: `list2cmdline` quotes only arguments that contain spaces, so a user folder name that contains `&` would break the system prompt path through cmd.exe.  The native `claude.exe` does not go through cmd.exe and is not affected.  A better approach (used in the sibling repository) resolves an npm shim to `node.exe` plus the package's JavaScript entry point.
- **The host application's environment reaches the child process.**  A terminal opened inside the Claude desktop app has `ANTHROPIC_BASE_URL` and about 20 `CLAUDE_CODE_*` variables (counted on the development machine).  These variables redirect the child program.  Fix: remove `ANTHROPIC_*`, `CLAUDE_*`, `CLAUDECODE*`, and `ADAPTER_*`.  Keep only `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_OAUTH_TOKEN`, and `CLAUDE_CODE_GIT_BASH_PATH`.  Add `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, which stops update checks and similar background traffic on every request.
- **PowerShell 5.1 turns a native program's stderr into a terminating error** when output is redirected.  Fix: the adapter logs to stdout.
- **Windows blocks `.ps1` scripts by default** (execution policy `Restricted`).  Security software also flags an execution-policy bypass flag.  Fix: the launcher is `Start-SpannBridge.py`, run with `python`.  No PowerShell script is needed.  This was *verified* under the `Restricted` execution policy.  The sibling repository uses a Node.js launcher (`Start-SpannBridge.mjs`) for the same reason.
- **A file named `Start Adapter.cmd`, typed without quotes, runs cmd.exe's built-in `start` command.**  That command tries to open `Adapter.cmd` and shows a Windows error dialog.  Never begin a launcher name with a cmd.exe built-in command followed by a space.
- **File Explorer hides file extensions by default.**  `Start-SpannBridge.py` next to `Start-SpannBridge.cmd` looks like two identical files.  Ship one launcher.
- **Microsoft Store Python does not register `.py` files.**  Double-clicking a `.py` file shows "How do you want to open this file?".  Document `python <file>`, not a double-click.
- **Console encoding.**  A cp1252 console made logging fail on characters such as ® and →.  Fix: `sys.stdout.reconfigure(errors="replace")`.
- **A port that is already in use** produced a uvicorn traceback.  Fix: test the port first and print one plain sentence.

## 4. HTTP and streaming pitfalls

- **When to send the HTTP status line.**  If the adapter waits for the first upstream event before sending HTTP 200, fast failures (not signed in, crash) become real 4xx and 5xx errors.  A model that thinks for a minute then leaves the connection silent.  Fix: on streaming requests, wait at most 5 s, then send 200 and an SSE comment (`: keep-alive`) every 15 s until the first token.  The stream generator must keep using the read that is still pending.  It must not start a new one.
- **An error after partial output was lost.**  For example, a usage limit reached halfway through a reply ended the reply as if it were complete.  Fix: keep the partial text and append `[adapter error] …`, in both streaming and non-streaming modes.
- **Token usage mapping.**  `prompt_tokens` is input plus cache-read plus cache-creation tokens.  `completion_tokens` is the output, which includes thinking, so it can be much larger than the visible reply.  With `include_usage`, send usage on a final chunk whose `choices` list is empty, as the OpenAI specification requires.  Without it, attach usage to the finish chunk anyway so that the Chatbot's counters update.
- **The body-size limit could be bypassed.**  A check that reads only `Content-Length` let a chunked upload (one without a length header) through.  Fix: refuse on the header, and also count the bytes actually read.  Do not rely on counting alone.  A client that declares 30 MB and sends 14 bytes would make the read wait forever.
- **The diagnostic page required the token.**  `/status` required the bearer token, so the troubleshooting advice "curl /status" returned 401.  Fix: `/status` skips the token check, because it cannot spend anything.  It keeps the local-only and `Origin` checks.
- **Abandoned requests.**  If the client disconnects before streaming starts, nothing reads the output.  Fix: use a deadline timer that does not depend on the reader.  `close()` can run more than once safely.  After a client disconnect, Starlette cancels every `await` inside `close()` again, so the kill, the release of the concurrency slot, and the file cleanup all sit in `finally` blocks.  The callers cancel the pending read task.
- **The line-length limit.**  asyncio's default limit for `readline` is 64 KB.  One stream-json line can contain a whole message with base64 images.  Fix: set `limit` to 64 MB on the subprocess pipes.

## 5. Claude Code pitfalls (most apply to any agent command-line program)

- **Headless mode still loads the user's own customizations:** CLAUDE.md files, hooks, plugins, skills, and MCP servers.  An empty working folder does not prevent this.  Fix: `--safe-mode`.  `--strict-mcp-config` does **not** remove claude.ai connectors (for example "Claude Docs", which adds tool schemas and instructions).  Set `ENABLE_CLAUDEAI_MCP_SERVERS=false` for that.  Also use `--no-session-persistence`, so that Chatbot conversations do not appear in `claude --resume`.  *Verified* on 2026-10-03: a CLAUDE.md file in the working folder that asked for a marker word reached the model without `--safe-mode`, and the marker did not appear with it.
- **Measure the input overhead that the program adds.**  With `--system-prompt-file` and safe mode, a five-word prompt used 384 input tokens (measured on 2026-10-03).  For tiny prompts through Codex, the sibling repository reported about 9,000 to 11,500 input tokens.  The overhead affects the plan's usage limits and the API-equivalent cost.
- **`--bare` turns off subscription sign-in** and allows only an API key.  Never pass it.
- **Removing tools.**  `--tools ""` makes the `system/init` event report `"tools": []`.  Confirm this from that event rather than by assumption.  A `--disallowedTools` list is the fallback for old versions.  Removing tools is a program option, not an operating-system sandbox.  The program still runs with the user's own permissions, so say so in the documentation.
- **Required flags that `--help` does not list.**  `--max-turns` and `--system-prompt-file` work but do not appear in the help text.  Probe `--help` only for *optional* flags.  Never make a required flag depend on the help text.
- **The program adds context even with a custom system prompt.**  It tells the model the working folder, the operating system, the date, the model name, and the **signed-in account's email address**.  The model once wrote the user's home folder path into `model.modelPath(...)`.  Fix: the prompt note tells the model to ignore these facts and to use bare file names.  The README tells the user about the email address.
- **Errors look like successes.**  An authentication or usage failure arrives as `{"type":"result","subtype":"success","is_error":true,"result":"<message>"}` with exit code 1.  An authentication failure also produces an `assistant` event with `"error":"authentication_failed"`.  Check `is_error`, not `subtype`.
- **Model aliases depend on the installed version.**  On 2026-10-03, version 2.1.280 resolved `sonnet` to `claude-sonnet-5`, although `claude-sonnet-5-5` was already released.  The full ID worked and printed an `unrecognized_model` warning on stderr.  Claude Code also has a `default` alias for the model that it recommends for the account.  On the same day, 2.1.280 resolved `default` to `claude-opus-5-5[1m]` (measured).  This is the closest equivalent to the plan default model in Codex.
- **The default effort can mean a minute of silence.**  At the default effort (`high`), Sonnet 5 took 66.6 s to show the first visible token for the example prompt (measured).  With `medium` it took 9.4 s, with `low` 4.6 s, and with thinking off 2.3 s.  `MAX_THINKING_TOKENS=0` has no effect on models whose thinking is always on (Fable 5.1, Opus 5.5, and Sonnet 5.5).  For those models, effort is the only control.  The Chatbot has no effort setting, so the adapter reads a suffix on the Model id (`fable:low`, `sonnet:off`).  The default model, `sonnet`, was chosen for the same reason as the default effort: a short wait before the first token during a user's first test.  It is not a judgment of Sonnet's engineering ability.
- **Images need stream-json input.**  Send one JSON line, `{"type":"user","message":{"role":"user","content":[…blocks…]}}`, with `--input-format stream-json`.  Then close stdin.  The program exits after the turn.
- **The model sometimes denied seeing images.**  With a "you have no tools" note in the system prompt, the model claimed that it could not see attached images in about one run in three.  Fix: when images are present, add a sentence that says the images are attached and visible.  After this change, 5 of 5 runs described the image.
- **Use only top-level text.**  Read only `stream_event` lines whose `parent_tool_use_id` is null.

## 6. Testing pitfalls

- **Record the real event stream before you write a stub.**  There are two free ways to probe.  Run the real program with `CLAUDE_CONFIG_DIR` set to an empty folder.  It is then not signed in, and it prints `system/init` and a failed `result`.  Or, while signed in, request a model ID that does not exist.  The program prints `system/init` and bills zero tokens.  The stub for this release's offline tests reproduced the recorded stream.  It also had failure modes: not signed in, crash, hang, slow, no partial messages, an error after partial output, a crash after partial output, and a hang after partial output.
- **A probe that imported the adapter skipped flag detection at startup.**  The probes therefore ran with weaker flags than the server and showed about 12,000 extra input tokens (measured) that the server never used.  Fix: `detect_flags()` now runs on first use.
- **Importing `tests/smoke_test.py` ran the whole test suite against the live adapter.**  Fix: the module refuses to be imported.
- **Test with the same cleaned environment as the adapter.**  A shell started by an AI coding assistant contains that assistant's environment variables.
- **Problems with the AI assistant's shell during this build.**  A Bash heredoc turned `\b` into a backspace character inside a generated file.  A Git Bash layer changed `nul` to `/dev/null` inside a generated `.cmd` file.  `cmd //c "Start Adapter.cmd"` lost its quotes.  Write files with a file-writing tool, not with shell `echo` or `printf`.  Test `.cmd` files from PowerShell with full paths.  When a script must contain backslashes, build Windows paths with `chr(92)`.
- **Measure latency.**  The default effort was chosen from the measured time to the first token on the real example prompt, not from documentation.

## 7. Release checks

- Package an explicit list of files, not a whole working folder.  Before you publish, check every file for email addresses other than the contact address, paths to a personal user folder, and possessive forms of the COMSOL® mark.  Check the SHA-256 hash of every packaged file against its source.
- Keep plan names out of documentation and sample output.  Write "Pro or Max subscription", not a specific plan.
- Do not redistribute COMSOL® example model files.

## 8. Adapting SpannBridge to other providers

*Unverified.*  The notes on Grok and Muse come from public documentation and secondary sources read on 2026-09-30.  The note on Google Gemini comes from Google's own pages, read on 2026-10-03.  Check every point again.

**Google Gemini.**  Do not adapt SpannBridge to a Google AI subscription, because Google's current terms prohibit this structure.

- On 18 June 2026, Gemini CLI stopped accepting sign-in with a Google AI Pro or Ultra subscription ([Google's notice](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals)).  Those subscriptions now work with Google's Antigravity products.
- Section 6 of the [Antigravity terms](https://antigravity.google/terms) states that the use of third-party software, tools, or services to access the service is a breach of the agreement.  An adapter like SpannBridge is such third-party software.
- In February 2026, Google suspended the accounts of subscribers who used such tools ([Google's post](https://github.com/google-gemini/gemini-cli/discussions/20632)).
- Gemini models remain available through Google's paid API, which has an OpenAI-compatible address that the Chatbot can use directly.

**xAI Grok, through the "Grok Build" command-line program (`grok`).**  This fits pattern A.

- Headless options: `-p` or `--single <PROMPT>`, `--output-format plain|json|streaming-json|streaming-messages-json`, and `--json-schema`.
- Sign-in: browser sign-in on a SuperGrok or X Premium+ subscription, or `XAI_API_KEY`.  The API key is billed separately through the xAI API.  It is unknown whether `-p` uses the stored subscription sign-in or needs the key.
- Third-party clients that used the xAI subscription sign-in service directly were rejected with HTTP 403.  Run the official program instead.  Remove `XAI_API_KEY` from the child environment.
- Unknown: the streaming event format, flags that turn off tools or replace the system prompt, image input, and the context that the program adds.  Record the event stream first (section 6).

**Meta Muse, through the "Muse Code" command-line program (`muse`).**  This fits pattern A with `muse exec`, or pattern B with `muse serve`.

- Installation on Windows: `irm https://dev.meta.ai/install.ps1 | iex`.  Meta's documentation says native Windows is supported.  One third-party guide wrongly says that Windows needs WSL.
- Headless options: `muse exec "<prompt>"`, with `--json` for one JSON event per line, `--disable-web-tools`, and `--disable-write`.  No flag that replaces the system prompt is documented.
- Programmatic use: `muse serve` uses a versioned session protocol.  The TypeScript package `@muse-code/sdk` wraps that protocol.  This is the closest equivalent to the Codex App Server.
- Billing: Muse Code plans apply to "Muse Code CLI only while signed in".  Additional API keys are billed per use.  The documentation says that non-interactive environments need `META_API_KEY`.  Confirm which billing path `exec` and `serve` use **before** you claim subscription use.  The plans for the consumer Muse app are a different product.
- Never read the stored credential (keychain service `ai.meta.dev.credentials`).

**Checklist for adapting SpannBridge to another provider**

1. Read the vendor's policy pages.  Record the date and what they say.
2. Find the headless or server mode and its machine-readable output format.
3. Record a real event stream with a free or signed-out probe.  Write a stub from it.
4. Map the events.  Text pieces become OpenAI chunks.  The final result becomes the finish chunk with usage.  Error results become HTTP errors before streaming starts, and reply text after.
5. Turn off agent behavior: tools, user configuration, MCP servers, and connectors.  Use a sandbox and a single turn.  Confirm each setting from the program's own startup or status output.
6. Find the context that the program adds to the model's input, and tell the model to ignore it.
7. Remove the vendor's API-key variables from the child environment, so that billing cannot move without warning.
8. Measure the time to the first token for each effort setting, with a real prompt from the Chatbot.
9. Find the program's image input.  Test it with a generated PNG and with a real Graphics snapshot.
10. Test in COMSOL Multiphysics® itself: the *Programming* subject, **Send to Java Shell**, the error loop, a node attachment, and a Graphics snapshot.
11. Name the project without vendor marks or COMSOL® marks.  Check the release files for personal data before you publish them.

## 9. Lessons from the sibling repository `spannbridge-appserver` (pattern B)

These points come from that repository's review notes.  They apply to `muse serve` and to any JSON-RPC session server.

- Model catalogs arrive in pages.  Follow the cursors, and stop if a cursor repeats.
- A catalog entry can have a picker `id` that differs from its `model` value.  Accept both, and send `model`.
- A turn can fail before the call that starts it returns.  Attach a rejection handler early.  Otherwise the failure becomes an unhandled promise rejection.
- On cancellation or timeout, interrupt the turn.  Then unsubscribe from the temporary thread so that the server can unload it.
- Decline every approval, permission, elicitation, and user-input request that the server sends.
- If the server process stops, fail all pending calls at once with HTTP 503.  Do not wait for each call to time out.
- Keep *commentary* separate from the *final answer*.  Do not present commentary as the reply.
- Create temporary files inside the cleanup scope.  Reject malformed inputs with an explicit error.

## 10. Open items

- A bridge for the Chatbot's tool calling, so that its documentation search works.
- Persistent sessions, so that earlier images are not sent again with every message.
- Run an npm `claude.cmd` shim through the native program instead of cmd.exe.
- On Mac and Linux: stop the child's whole process group on timeout, and adjust the launcher and the stub.
- Check how the Chatbot window shows HTTP errors: 400 for an unknown Model id, 401 for a wrong API key, and 500 when Claude Code is not signed in.  These errors were tested only over HTTP, not in COMSOL Multiphysics® itself.
