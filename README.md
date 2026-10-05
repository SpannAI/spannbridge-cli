# SpannBridge

Connects the Chatbot window in COMSOL Multiphysics® software to Claude Code, using your Claude subscription instead of an API key.

An open-source tech demo published by Spann Engineering Consulting LLC, whose website is [spann.ai](https://spann.ai).  Spann Engineering Consulting LLC helps clients solve their toughest R&D challenges and continue to get value from delivered simulations through AI automation.

Release 1.0 · October 2026 · MIT License · Windows · COMSOL Multiphysics® 6.4

**This GitHub repository is neither developed by nor endorsed by COMSOL AB**, nor by Anthropic PBC.  See [Publisher, trademarks, and affiliation](#publisher-trademarks-and-affiliation).

SpannBridge comes as two separate editions.  **This one runs Claude Code on a Claude Pro or Max subscription.**  For OpenAI Codex on a ChatGPT plan, see [SpannAI/spannbridge-appserver](https://github.com/SpannAI/spannbridge-appserver).

**This repository is for Windows only, because the Chatbot window in COMSOL Multiphysics® 6.4 runs only on Windows.**

> **Follow your organization's rules before you send work data.**  Everything you type or attach in the Chatbot leaves your PC and goes to Anthropic, a third-party AI company.  This includes questions, model code, Model Builder nodes, Graphics snapshots, and results.  Many organizations restrict or forbid sending confidential, client, proprietary, or export-controlled information to outside AI services.  Check your organization's policy first.  SpannBridge does not filter, redact, or block anything.  Spann Engineering Consulting LLC also recommends that you turn off model training in your Claude privacy settings.  See [Your data and your organization's rules](#your-data-and-your-organizations-rules).

> SpannBridge is a **single-user tool for your own PC and your own Claude subscription**.  Anthropic decides whether it permits this use and how it bills it.  Anthropic changed or proposed to change those rules more than once in 2026.  Read [Is this allowed?  Check before you run it](#is-this-allowed-check-before-you-run-it) as well, especially if you are reading this long after October 2026.

> **Your work is yours.**  You may use SpannBridge free of charge, including for paid engineering work.  Spann Engineering Consulting LLC claims no ownership of anything you create with it and accepts no liability for it.  Using SpannBridge requires no credit or acknowledgment.  See [What the MIT License means for you](#what-the-mit-license-means-for-you).

> **Get SpannBridge only from its official sources.**  Spann Engineering Consulting LLC publishes SpannBridge and its other products only on [spann.ai](https://spann.ai) and on GitHub under [SpannAI](https://github.com/SpannAI).  SpannBridge has no separate domain name.  Its announcement page is [spann.ai/spannbridge](https://spann.ai/spannbridge), and its contact address is [spannbridge@spann.ai](mailto:spannbridge@spann.ai).  Spann Engineering Consulting LLC does not operate any other site that claims to be the SpannBridge website, so do not download anything from such a site.  SpannBridge is not published on PyPI, npm, or any other package registry.  The MIT License allows others to publish copies and modified versions, but Spann Engineering Consulting LLC has not reviewed them.
>
> **SpannBridge is free.**  It never asks for payment, passwords, or personal information.  The only sign-in is `claude auth login`, which opens Anthropic's sign-in page.  Your Claude subscription is a separate purchase from Anthropic.
>
> **You can read every line before you run it.**  SpannBridge is distributed as Python scripts and other plain-text files.  It is never distributed as a compiled program such as an `.exe` file.  You, or an AI assistant you trust, can read the code to check that it does what this README says.

Is there a feature you'd like to add?  Developers and AI coding assistants who want to change SpannBridge should start with [DEEP-DIVE.md](DEEP-DIVE.md).  If you want to adapt SpannBridge to another AI provider, I've left some notes at [Other AI providers](#other-ai-providers).

## Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Your data and your organization's rules](#your-data-and-your-organizations-rules)
- [Is this allowed?  Check before you run it](#is-this-allowed-check-before-you-run-it)
- [Requirements](#requirements)
- [What's in this repository](#whats-in-this-repository)
- [Quick start (Windows)](#quick-start-windows)
- [Using it](#using-it)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [If you are reading this in the future](#if-you-are-reading-this-in-the-future)
- [Reporting a problem and contact](#reporting-a-problem-and-contact)
- [Using the Claude API directly instead](#using-the-claude-api-directly-instead)
- [Other AI providers](#other-ai-providers)
- [What the MIT License means for you](#what-the-mit-license-means-for-you)
- [Publisher, trademarks, and affiliation](#publisher-trademarks-and-affiliation)

## What it does

COMSOL Multiphysics® 6.4 simulation software has a built-in Chatbot window.  The Chatbot can connect to any AI service that accepts requests in the format of OpenAI's chat API (an "OpenAI-compatible" service).  SpannBridge is a small program that runs on your PC and acts as that service.  It passes each question to **Claude Code**, Anthropic's official command-line program, which is signed in with your own Claude account.

- **Chat with Claude inside COMSOL Multiphysics®.**  Replies appear in the Chatbot window as Claude writes them.  The Chatbot's token counters also update.
- **Write COMSOL® API for Java code that runs.**  SpannBridge tells Claude the rules of the **Java Shell**, the window in COMSOL Multiphysics® that runs Java statements.  The rules are: plain statements on the open `model`, no class or `main` method, checked exceptions caught inline, and a plot after solving.  As a result, **Send to Java Shell → Run** builds the model in your Model Builder.  If the Java Shell reports an error, select it, click **Send to Chatbot**, ask for a fix, and run the code again.
- **Understand your model.**  Right-click a Model Builder node and choose **Send to Chatbot → Node**.  The node arrives as its Java code, and Claude can explain or fix it.
- **See your results.**  Graphics-window snapshots and PNG, JPEG, or GIF files that you send to the Chatbot reach Claude as images.
- **Choose the model and how long it thinks** for each conversation, in the Chatbot's *Model id* setting.  Examples are `default`, `sonnet`, and `fable:low`.
- **See what each reply would cost on the paid API.**  The SpannBridge window shows the token counts of each reply and its API-equivalent cost, as Claude Code reports them.  Anthropic does not charge you that amount, because your plan's usage limits apply instead.  See [Reading the SpannBridge window](#reading-the-spannbridge-window).

SpannBridge never operates COMSOL Multiphysics® by itself.  Nothing in your model changes until you click **Send to Java Shell** and **Run**.  SpannBridge does **not** support the Chatbot's *Tool calling* option, which is its built-in documentation search.  SpannBridge is also not a server for other people.  See [Limitations](#limitations).

## How it works

```
 COMSOL Multiphysics® 6.4 (Chatbot window)
        │  OpenAI-compatible HTTP:  POST /v1/chat/completions  (streamed reply)
        ▼
 SpannBridge (adapter.py, listening on 127.0.0.1:8765, this PC only)
        │  one Claude Code process per message:  claude -p ...
        │  prompt in on stdin, stream-json events (one JSON object per line) out on stdout
        ▼
 Claude Code (the official claude program, installed and run unmodified)
        │  signed in with your account through Anthropic's own "claude auth login"
        │  Claude Code stores and renews the sign-in.  SpannBridge never touches it.
        ▼
 Anthropic (use counts against your Claude Pro or Max plan's usage limits)
```

These steps happen for each message you send in the Chatbot window:

1. **The Chatbot window sends the whole conversation so far** to SpannBridge, in OpenAI's chat format.  The conversation includes the Chatbot's system prompt (its standing instructions to the AI), your messages, Claude's earlier replies, and any attachments.
2. **SpannBridge turns the conversation into one prompt.**  The prompt contains the Chatbot's system prompt plus a short note about the Java Shell, the earlier turns inside a `<conversation_history>` block, and your newest message last.  Images are passed to Claude as images, not converted to text.
3. **SpannBridge starts `claude -p`** with every Claude Code tool turned off, a limit of one turn, and an empty working folder.  It also uses safe mode, so none of your own Claude Code settings, memory files, hooks, plugins, or MCP servers (add-on tool connections) load.  Safe mode needs a recent version of Claude Code.  With an older version, SpannBridge prints a warning at startup, and your own settings can load.  With these settings, Claude Code behaves as a plain chat model, not as a coding agent.
4. **SpannBridge converts the reply.**  Claude Code streams its answer in pieces.  SpannBridge converts each piece into OpenAI's streaming format, so the reply appears in the Chatbot window as Claude writes it.  The last piece includes the token counts.
5. **The Claude Code process exits** when the answer is complete.  SpannBridge keeps nothing between messages.  The next message starts a fresh `claude -p` with the full conversation again, which the Chatbot resends anyway.

SpannBridge **never** does any of these things:

- read, copy, store, or forward your Claude credentials
- call Anthropic's servers itself
- accept connections from other computers or from web pages
- log your messages, or save them to disk unless you turn on its debugging option
- send anything to Spann Engineering Consulting LLC

## Your data and your organization's rules

**Check that your organization allows it before you use SpannBridge for work.**  Everything in a Chatbot conversation goes to Anthropic, a third-party AI company.  That includes your questions, the Chatbot's own prompt, Model Builder nodes (as Java code), Graphics snapshots, attached files, and Claude's earlier replies in the conversation.

- **Your organization's rules come first.**  Many employers and clients restrict or forbid sending confidential, proprietary, client-owned, personal, or export-controlled information to outside AI services.  Export-controlled information includes, for example, technical data under the US ITAR and EAR export-control regulations.  Some organizations allow only approved tools and accounts.  SpannBridge does not change those rules.  You are responsible for following them.
- **A personal Claude subscription is not automatically an approved tool for work data.**  If your organization has an approved way to use Claude, use that way and follow its rules.
- **SpannBridge sends exactly what the Chatbot sends.**  It does not filter, redact, or block anything.  If something must not leave your PC, do not type it, attach it, or send it to the Chatbot.
- **Nothing goes to Spann Engineering Consulting LLC.**  SpannBridge has neither telemetry, usage statistics, nor an update check.  SpannBridge makes no network connections except on 127.0.0.1 (your own PC).  Your data goes only from the official Claude Code program to Anthropic.  Spann Engineering Consulting LLC receives information from you only if you contact it yourself, for example by email.
- **Your Claude account's terms and privacy settings govern how Anthropic handles the data,** as with any Claude chat.  Claude sees only what the Chatbot sends, not your other Claude chats.
- **Turn off model training.**  Spann Engineering Consulting LLC recommends this to everyone who uses SpannBridge.  On Pro and Max plans, Anthropic trains new models on your chats and Claude Code sessions while its model-improvement setting is on.  That includes the Claude Code sessions that SpannBridge starts.  To turn the setting off, open [claude.ai/settings/data-privacy-controls](https://claude.ai/settings/data-privacy-controls) and switch off **Help improve Claude**.  With the setting off, Anthropic keeps the data for 30 days instead of 5 years, according to its [data usage page](https://code.claude.com/docs/en/data-usage) on 3 October 2026.

Claude Code also tells the model some facts about the PC it runs on: SpannBridge's working folder, your operating system, today's date, and **your Claude account's email address**.  These facts cannot be switched off without also turning off subscription sign-in.  SpannBridge tells Claude to ignore them.  SpannBridge also turns off the nonessential data that Claude Code would otherwise send to Anthropic and to other services: usage metrics, error reports, and feedback surveys.

On your PC, SpannBridge writes nothing to disk except one temporary prompt file per request, which it deletes afterwards.  It runs Claude Code with session saving turned off, so these chats do not appear in your Claude Code history.  SpannBridge logs sizes and counts, never message content.  The one exception to both statements is the debugging option `ADAPTER_DUMP_STDIN`.  When it is on, SpannBridge saves a copy of each full prompt, including your messages and attachments, and keeps it until you next start SpannBridge without the option.

## Is this allowed? Check before you run it

**Short answer as of 3 October 2026.**  Anthropic's published rules allow a person to sign in to the *unmodified* Claude Code program with *their own* Claude subscription.  Claude Code has a non-interactive mode (`claude -p`, also called headless mode).  Use of that mode counts against the subscription's normal usage limits.  SpannBridge is built to stay inside those rules.  It runs the official `claude` program as published, and sign-in happens only through Anthropic's own process.  SpannBridge never handles your credentials.  It serves only you, on your own PC.

**What Anthropic does not allow.**  Do not use SpannBridge for any of these:

- offering Claude sign-in inside someone else's product
- routing other people's requests through a Free, Pro, or Max login
- collecting, storing, or passing on Claude credentials or session tokens

Anthropic also states that its advertised Pro and Max usage limits assume ordinary, individual use.  Anthropic may enforce these rules without notice.  So do not make SpannBridge reachable from a network, do not share it with colleagues through your login, and do not use it for heavy automated workloads.

This section is the author's reading of Anthropic's public documents.  It is not legal advice and not an Anthropic endorsement.  A successful sign-in or reply does not prove that a use is permitted.  You are responsible for your own compliance.

### How to check the current rules

Anthropic changed its policies and billing for this kind of use several times in 2026.  Check these pages before you rely on SpannBridge.  Check them again whenever you update Claude Code or return to SpannBridge after a while.

| Question | Where to look | What to look for |
|---|---|---|
| Is signing in with a subscription still allowed for this kind of use? | [Claude Code: Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance), section *Authentication and credential use* | Confirm that subscription sign-in still covers ordinary use of Claude Code.  Confirm that an end user may still sign in to the unmodified program with their own subscription.  Look for any new limit on headless or programmatic use. |
| How does Anthropic bill `claude -p` on a subscription? | [Use the Claude Agent SDK with your Claude plan](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan).  If the article has moved, search [support.claude.com](https://support.claude.com) for "claude -p". | Check whether `claude -p` still counts against your plan's usage limits, uses a separate credit, or is excluded.  On 3 Oct 2026 the article, dated 16 June 2026, said that Anthropic had paused a planned change and that nothing had changed. |
| Does headless mode still exist? | [Claude Code: Run Claude Code programmatically](https://code.claude.com/docs/en/headless) | Confirm that the `-p` (`--print`) mode and `--output-format stream-json` are still documented. |
| What do the general terms for Pro and Max say? | [Consumer Terms](https://www.anthropic.com/legal/consumer-terms) and [Usage Policy](https://www.anthropic.com/legal/aup) | Look for anything new about automated or programmatic access. |

If any of these pages says that this use is not allowed, or bills it in a way that you do not want, **stop using SpannBridge**.  Use [the Claude API directly](#using-the-claude-api-directly-instead) instead.  If your seat is on a **Team or Enterprise** plan, your organization's agreement and admin settings apply.  Ask your admin first in that case.  If you are unsure, Anthropic's compliance page links to a contact page for questions about permitted sign-in methods.

## Requirements

- **Windows 10 or 11.**  The Chatbot window in COMSOL Multiphysics® 6.4 is Windows-only.  For Mac and Linux, see [Mac and Linux](#mac-and-linux).
- **COMSOL Multiphysics® 6.4 simulation software** with the Chatbot window.  Version 6.4 installs the Chatbot by default.
- **A Claude Pro or Max subscription.**  The Free plan does not include Claude Code.
- **Claude Code**, Anthropic's command-line program.  Step 1 below installs it.  The copy inside the Claude desktop app does not work for this purpose.
- **Python 3.10 or newer**, from [python.org](https://www.python.org/downloads/) or the Microsoft Store.
- No administrator rights, no API key, and no Node.js.

**Tested with** (October 2026): Windows 11 Pro, COMSOL Multiphysics® 6.4, Claude Code 2.1.280, Python 3.10.11 (Microsoft Store), FastAPI 0.97.0, uvicorn 0.22.0, Pillow 9.5.0, and a Claude Pro or Max subscription.  The Model ids `sonnet` and `fable` were tested in the Chatbot window.

## What's in this repository

Three files are needed to run SpannBridge.  Everything else is optional or documentation.

| File | What it is | Needed to run SpannBridge? |
|---|---|---|
| `adapter.py` | SpannBridge itself: the local server that the Chatbot connects to. | **Yes** |
| `Start-SpannBridge.py` | The launcher.  It checks the prerequisites, then starts `adapter.py`. | **Yes** (or start `adapter.py` directly) |
| `requirements.txt` | The list of Python packages to install. | **Yes**, once, during setup |
| `tests/smoke_test.py` | A check of a running SpannBridge.  It sends a few tiny requests, or none with `--check-only`. | No, but step 6 uses it |
| `README.md` | This guide. | No, documentation only |
| `DEEP-DIVE.md` | Technical notes for developers and AI coding assistants.  It lists the problems solved in this release and explains how to adapt SpannBridge to other AI providers. | No, documentation only |
| `LICENSE` | The MIT License, the legal text.  See [What the MIT License means for you](#what-the-mit-license-means-for-you). | No, but keep it with the code if you share the code |
| `.gitignore` | Tells git which generated files to skip. | No |

## Quick start (Windows)

**After the first time, running SpannBridge is one command.**  Once you've set up SpannBridge the first time, all you need to do is open a PowerShell window in the SpannBridge folder and type `python Start-SpannBridge.py`.  Leave that window open while you use the Chatbot.  The other steps below are one-time setup and checks.  COMSOL Multiphysics® keeps the same Chatbot settings.  If you start SpannBridge with custom options such as `--token`, use the same options each time.  If SpannBridge reports that Claude Code is not signed in, repeat step 2.

Use a normal **PowerShell** window, not an Administrator window.

### 1. Install Claude Code

```powershell
irm https://claude.ai/install.ps1 | iex
```

Close the window, open a **new** one, and check the installation:

```powershell
claude --version
```

If the reply is *"not recognized"* but `C:\Users\<you>\.local\bin\claude.exe` exists, the installer did not add that folder to your PATH.  Add it once with this command, then open another new window:

```powershell
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User").TrimEnd(";") + ";$env:USERPROFILE\.local\bin", "User")
```

**Which installer to use.**  The command above is Anthropic's recommended **native installer**.  It installs a signed `claude.exe` that needs no Node.js and updates itself.  `winget install Anthropic.ClaudeCode` installs the same program but does not update it automatically.  The npm package `@anthropic-ai/claude-code` also works but is not needed.  Packages with similar names under any other npm scope are not Anthropic's.  Anthropic's current instructions are at [code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup).

### 2. Sign in with your Claude subscription

```powershell
claude auth login
```

In the browser, sign in with the Claude account that has your **Pro or Max subscription**, not with a Claude Console account.  A Console account is for paid API use, billed per token.  Then confirm that the output shows `"loggedIn": true`:

```powershell
claude auth status
```

If `ANTHROPIC_API_KEY` is set on your PC, Claude Code bills that API key instead of your subscription.  SpannBridge hides the key from Claude Code automatically.  For the check in step 3, clear it in this window:

```powershell
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
```

### 3. Check that Claude Code works on its own

```powershell
"say hi" | claude -p --output-format json
```

This command sends one tiny request, which counts against your plan.  The output should be JSON that contains `"is_error": false` and a short reply.  Fix any problem here before you go on, because SpannBridge needs a working Claude Code installation.

### 4. Get SpannBridge and its Python packages

Get SpannBridge in one of two ways.  You can put it in any folder, and spaces in the path are fine.

**Download the ZIP.**  On the repository's GitHub page, click **Code → Download ZIP**, and extract the ZIP.  Windows often extracts the ZIP into a folder inside a folder of the same name, so use the inner one if you see only one folder.

**Or clone the repository with git.**  Git is not part of Windows, so use this way only if you have git installed.  Open PowerShell in the folder where you want to put SpannBridge, and run these commands:

```powershell
git clone https://github.com/SpannAI/spannbridge-cli.git
cd spannbridge-cli
```

To get a newer version later, run `git pull` in the `spannbridge-cli` folder.

Review the source before you run it.  Then open PowerShell in the folder that contains `Start-SpannBridge.py`, if it is not already open there.  To do that, open the folder in File Explorer, type `powershell` in the address bar, and press Enter.  Check that Python works:

```powershell
python --version
```

It should print Python 3.10 or newer.  If Windows opens the Microsoft Store instead, or says that `python` is not recognized, install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH**, or install it from the Microsoft Store.  Then open a new PowerShell window in the same folder.  Then install the packages:

```powershell
python -m pip install -r requirements.txt
```

### 5. Check, then start SpannBridge

First run a check that starts nothing and sends nothing:

```powershell
python Start-SpannBridge.py --check-only
```

The check ends with `PASS: ready to start` or tells you what to fix.  Then start SpannBridge:

```powershell
python Start-SpannBridge.py
```

The launcher repeats the checks, prints the values to enter in the Chatbot preferences, and starts SpannBridge.  **Leave that window open** while you use the Chatbot.  Press Ctrl+C to stop SpannBridge.  Start it with the command, not by double-clicking the file, because a double-clicked window closes before you can read an error.

To choose options, add them after the file name:

```powershell
python Start-SpannBridge.py --token YOUR-TOKEN --thinking-off
```

Replace `YOUR-TOKEN` with a word of your choice that other people cannot guess.  SpannBridge then requires that word from the Chatbot, which sends it from its *API key* field.  No other program on your PC can then use your subscription through SpannBridge.  `--thinking-off` makes replies start sooner on models where thinking is optional, such as Sonnet 5 (see [Choosing a model and effort](#choosing-a-model-and-effort)).  [Configuration](#configuration) lists all options.

SpannBridge has no PowerShell scripts.  The PowerShell script setting (the execution policy) therefore does not apply.  You do not need to bypass or change it.

A good start looks like this.  Check that the `login` line says `"ok": true`:

```
COMSOL Preferences -> Chatbot:  Base URL http://127.0.0.1:8765/v1   Model id default   Context length 128000   API key demo   Tool calling off
20:51:43 SpannBridge 1.0 (runs Claude Code)   http://127.0.0.1:8765
20:51:44    claude : C:\Users\<you>\.local\bin\claude.EXE  (2.1.280 (Claude Code))
20:51:44    flags  : --disable-slash-commands --effort --no-session-persistence --permission-prompts --safe-mode --strict-mcp-config --tools
20:51:44    login  : {"ok": true, "exit_code": 0, "loggedIn": true, "authMethod": "claude.ai", ...}
20:51:44    token  : required (ADAPTER_TOKEN)   timeout: 180s   default model: sonnet   effort: medium   concurrency: 2
20:51:44    thinking: off (MAX_THINKING_TOKENS=0 is passed through to claude)
20:51:44    COMSOL : Base URL = http://127.0.0.1:8765/v1   Model id = default (or e.g. sonnet, fable:low)   Context length = 128000   Tool calling = off
```

### 6. Test SpannBridge before you open COMSOL Multiphysics®

Open a second PowerShell window in the same folder.  First run a check that uses **none** of your plan.  It confirms that SpannBridge answers and that Claude Code is signed in:

```powershell
python tests\smoke_test.py --check-only
```

Then run the full check.  It sends a handful of tiny prompts:

```powershell
python tests\smoke_test.py
```

If you started SpannBridge with `--token`, add the same `--token YOUR-TOKEN` to both commands.  The output should end with `ALL PASSED`.

### 7. Point the Chatbot at SpannBridge

In COMSOL Multiphysics®, choose **File → Preferences → Chatbot**, tick **Enable Chatbot**, and enter these settings:

| Setting | Value |
|---|---|
| Provider | **OpenAI API compatible** |
| Base URL | `http://127.0.0.1:8765/v1` |
| Model id | `default`.  For other choices, see [Choosing a model and effort](#choosing-a-model-and-effort). |
| Context length (tokens) | `128000`, the COMSOL® default |
| Tool calling | **Cleared** (off) |
| API key | Leave it blank.  If you started SpannBridge with `--token`, enter that word. |

Click **OK**.  Open the Chatbot from the **Home** toolbar with **Windows → Chatbot**.

These settings are the same for both SpannBridge editions, so you can switch between them without changing the Chatbot preferences.  The context length is the limit that the Chatbot applies to the input and output of each request.  On 3 October 2026, 128,000 tokens fit within the context window of every model in either edition, with room left for what each command-line program adds to the prompt.

Both SpannBridge editions use port **8765**, which is easy to remember because it counts down.  Only one of them can run at a time.  To run both, start one with `--port 8766` and point the Chatbot's Base URL at that port.

### 8. Try a first conversation

1. Choose **File → New → Blank Model**, so the generated code has a clean model to build in.
2. In the Chatbot window, set the subject (top left) to **Programming**.  The Chatbot then sends its own Java-programming instructions, which produced better code in our tests.
3. Ask, for example:
   > Write COMSOL® API for Java code to create a 2D heat transfer model of a 10 cm square steel plate,
   > 20 °C on the left edge, 100 °C on the right, insulated top and bottom, and solve it.
4. On the reply, click **Send to Java Shell**, then **Run**.  The nodes appear in the Model Builder, and the study solves.
5. If the Java Shell shows an error, select the error, right-click, choose **Send to Chatbot**, ask "fix this", and repeat.  If no plot appears, ask "add a temperature surface plot and run it".

## Using it

### Choosing a model and effort

The Chatbot's **Model id** setting tells SpannBridge which model to request from Claude Code:

| Model id | Meaning |
|---|---|
| `default` | The recommended setting: the model that Claude Code recommends for your plan.  On 3 October 2026, Claude Code 2.1.280 selected Opus 5.5 with a 1-million-token context window (`claude-opus-5-5[1m]`).  With the example prompt from step 8, the first visible text appeared after 8 s and the whole answer after 21 s (measured once, without the Chatbot's *Programming* prompt).  Opus models use your plan's limits faster than Sonnet, and Opus 5.5 always thinks.  To shorten its thinking, add a lower effort, such as `default:low`. |
| `sonnet`, `opus`, `haiku`, or `fable` | The newest model of that family **that your installed copy of Claude Code knows about**.  See [Model names](#model-names). |
| A full ID, for example `claude-sonnet-5-5` | Exactly that model version. |
| Empty | SpannBridge's default model (`--model`, normally `sonnet`).  This is not the same as `default`. |
| Anything else | SpannBridge refuses the request with an error that lists the valid choices.  It does not answer with a different model than the one you named. |

**Why `sonnet` is SpannBridge's own default.**  When the Model id is empty, SpannBridge uses `sonnet`.  It was chosen so that replies start quickly when you test SpannBridge for the first time.  The choice is about the wait before the first visible text only.  It is not an endorsement of Sonnet's engineering ability, and Spann Engineering Consulting LLC has not compared the engineering answers of the different models.  For demanding modeling work, compare models such as `default`, `opus`, and `fable`, and judge the answers yourself.

*Effort* is the Claude Code setting for how much the model thinks before it answers.  The Chatbot has no effort setting, so SpannBridge reads an optional **suffix** on the Model id.  The suffix applies to that conversation only:

| Suffix | Effect |
|---|---|
| `:low`, `:medium`, `:high`, `:xhigh`, or `:max` | Sets the effort level, for example `fable:low` or `opus:high`.  SpannBridge ignores a misspelled suffix and prints a warning in its window. |
| `:off` | Turns thinking off (`MAX_THINKING_TOKENS=0`).  This works only on models where thinking is optional, such as Sonnet 5, which `sonnet` selects in Claude Code 2.1.280.  Models whose thinking is always on (Fable 5.1, Opus 5.5, and Sonnet 5.5) ignore it. |
| *(none)* | Uses SpannBridge's default effort, `medium`.  Change the default with `--effort`. |

**Effort sets how long the Chatbot shows nothing before the reply starts.**  With the Claude Code default effort (`high`), the example prompt in step 8 produced no visible text for over a minute.  These times were measured once, on 22 Sept 2026, with `claude-sonnet-5`.  Your times will differ with other models and future versions.

| Setting | First visible text | Whole answer | Output tokens |
|---|---|---|---|
| Claude Code default (`high`) | 67 s | 83 s | about 9,200 |
| `medium` (SpannBridge default) | 9 s | 31 s | about 3,500 |
| `low` | 5 s | 27 s | about 2,800 |
| thinking off (`:off` or `--thinking-off`) | 2 s | 30 s | about 3,300 |

All four settings produced complete answers of similar length.  The output-token count in the Chatbot includes the model's thinking, so it can be much larger than the visible reply.  Larger models (Opus and Fable) use up your plan's limits faster than Sonnet.

While Claude is still thinking, SpannBridge sends a small keep-alive signal every 15 seconds so that the connection stays open.  The reply then streams normally.

### Attachments and images

- **Model Builder nodes** arrive as Java code inside your message.
- **Graphics snapshots and image files** reach Claude as images.  SpannBridge shrinks images larger than 1568 pixels first, because Claude would shrink them anyway.
- **The Chatbot resends the entire conversation with every message, including every earlier image.**  A conversation with several snapshots therefore uses much more of your plan per message.  Start a new Chatbot conversation when you no longer need the old images.

### Reading the SpannBridge window

```
-> POST /v1/chat/completions  model='sonnet'->sonnet stream=True msgs=3 {'system': 1, 'user': 2} chars=5321 system_chars=4226 images=0 (0 KB) tools=no ...
   spawn: claude -p --output-format stream-json ... --tools "" ... --safe-mode   (prompt: 5321 chars on stdin)
   first token after 2.1s
<- 200 /v1/chat/completions  9.4s  in=1874 out=512 tokens  2210 chars  api-equivalent cost $0.0131
```

- `model='x'->y` shows what the Chatbot asked for and what SpannBridge passed to Claude Code.
- `api-equivalent cost` is what the request *would* cost on the paid API.  On a subscription, Anthropic does not charge per request.  Your plan's usage limits apply instead.  To see your limits, type `/usage` in an interactive `claude` session.
- SpannBridge logs only sizes and counts, **never message content**, unless you turn on `ADAPTER_DUMP_STDIN`, which saves full prompts to disk.
- `(no such endpoint …)` means that the Chatbot called an address that SpannBridge does not serve.  This message helps if a future version of COMSOL Multiphysics® changes its requests.

### Check the engineering

Claude can be wrong, including when it sounds certain.  Check generated code and results before you rely on them, as you would check a colleague's first draft.  Check in particular the units, material data, boundary conditions, mesh, and solver settings.  SpannBridge does not certify answers or replace engineering judgment.

Before you send anything from a work project, read [Your data and your organization's rules](#your-data-and-your-organizations-rules).

## Configuration

**Launcher options.**  Add any of these after `python Start-SpannBridge.py`:

| Option | Default | Meaning |
|---|---|---|
| `--check-only` | off | Checks Python, the packages, Claude Code, sign-in, and the port, then stops.  It starts nothing and sends nothing. |
| `--port` | `8765` | The port that SpannBridge listens on, always on 127.0.0.1 (this PC only).  If you change it, change the Base URL in the Chatbot preferences to match. |
| `--token` | *(none)* | The API key that the Chatbot must send.  If it is empty, SpannBridge accepts any key, including a blank one.  Spaces before and after the word are ignored. |
| `--model` | `sonnet` | The model to use when the Chatbot's Model id is empty.  It may include a suffix, such as `fable:low`. |
| `--effort` | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, or `default` (the model's own default). |
| `--thinking-off` | off | Turns thinking off for all requests, on models with optional thinking only. |
| `--timeout-seconds` | `180` | Stops a request that takes longer.  Raise it for very long code generations. |
| `--keepalive-seconds` | `15` | The keep-alive interval while Claude thinks.  `0` turns keep-alives off.  The Chatbot then receives nothing until Claude starts to answer or the request times out. |

**Environment variables.**  These apply when you start `python adapter.py` yourself.  The launcher sets the first group for you.

| Variable | Default | Meaning |
|---|---|---|
| `ADAPTER_PORT`, `ADAPTER_TOKEN`, `ADAPTER_DEFAULT_MODEL`, `ADAPTER_EFFORT`, `ADAPTER_TIMEOUT`, and `ADAPTER_KEEPALIVE_S` | as above | Same as the launcher options.  `ADAPTER_EFFORT=default` means the model's own default.  SpannBridge refuses to start, with a message, if a value is not valid. |
| `MAX_THINKING_TOKENS` | *(unset)* | A Claude Code setting that SpannBridge passes through.  `0` turns thinking off. |
| `CLAUDE_BIN` | *(found on PATH)* | The full path to `claude.exe`, if it is not on your PATH. |
| `ADAPTER_MAX_CONCURRENCY` | `2` | How many Claude Code processes may run at once.  Extra requests wait. |
| `ADAPTER_MAX_IMAGE_PX` | `1568` | SpannBridge shrinks larger images to this size.  This requires Pillow. |
| `ADAPTER_WORK_DIR` | `%USERPROFILE%\.spannbridge-cli` | The scratch folder: an always-empty working folder plus temporary prompt files, in a separate subfolder for each port.  Keep it outside `AppData` if you use Microsoft Store Python. |
| `ADAPTER_SAFE_MODE` | `1` | `0` lets your personal Claude Code settings load.  Use it for troubleshooting only. |
| `ADAPTER_DUMP_STDIN` | *(unset)* | `1` (or any value other than `0`) saves each exact prompt to the scratch folder for debugging.  These files contain your messages.  SpannBridge deletes them when it next starts without this option. |

`http://127.0.0.1:8765/status` shows the SpannBridge and Claude Code versions, the sign-in state (without your email address), and the settings in use.  It answers without the API key, so you can use it to check whether SpannBridge is running.  It cannot send anything to Claude.

## Troubleshooting

Start with `python Start-SpannBridge.py --check-only`.  It finds most setup problems without sending anything.

| Symptom | Fix |
|---|---|
| `claude` is "not recognized", or the check says `Claude Code not found` | Install Claude Code (step 1), fix PATH if needed, and open a **new** window.  Or set `CLAUDE_BIN` to the full path of `claude.exe`. |
| `not logged in`, or the check says `Signed in   : NO` | Run `claude auth login`, then retry.  You do not need to restart SpannBridge. |
| PowerShell says "running scripts is disabled on this system" | This is the Windows default setting.  SpannBridge does not need scripts.  Run `python Start-SpannBridge.py`.  Anthropic's installer in step 1 is a typed command, which that setting allows. |
| `can't open file … Start-SpannBridge.py` (or `adapter.py`) | You are in the wrong folder.  Open PowerShell in the folder that contains `Start-SpannBridge.py`. |
| `Port 8765 … is already in use` | SpannBridge is already running.  Look for its window.  Or start with `--port 8766` and change the Base URL in the Chatbot preferences. |
| Nothing appears in the SpannBridge window when you chat | The Base URL or port in the Chatbot preferences is wrong, or SpannBridge is not running.  Test with `curl.exe http://127.0.0.1:8765/status`. |
| `Unknown Model id` | The *Model id* in the Chatbot preferences is not a name that SpannBridge knows.  Use `default`, `sonnet`, `opus`, `haiku`, `fable`, or a full `claude-*` ID.  See [Choosing a model and effort](#choosing-a-model-and-effort). |
| HTTP 401, or `<- 401 bad or missing bearer token` in the SpannBridge window | The API key in the Chatbot preferences must equal the `--token` that you started SpannBridge with.  A blank API key gets this error whenever SpannBridge was started with `--token`. |
| Long silence before a reply | Claude is thinking.  Use a suffix such as `sonnet:low` or `sonnet:off`, or start with `--effort low` or `--thinking-off`. |
| `timed out after 180 s` | Raise `--timeout-seconds`, or lower the effort. |
| A reply ends with `[adapter error] …` | Claude Code reported a problem partway through the reply, often a usage limit.  SpannBridge keeps the partial reply.  Usage limits reset over time.  Type `/usage` in an interactive `claude` session to see them. |
| Usage appears on an API bill, not on your plan | `ANTHROPIC_API_KEY` or a Console login is in use.  `claude auth status` should show your Claude subscription.  If it does not, sign out and sign in again. |
| Java Shell code runs, but nothing happens | Claude wrote the code as a Java class, which the Java Shell compiles but never runs.  Ask for "plain Java Shell statements on `model`, no class".  Start from a blank model so that names such as `comp1` are free. |
| The Java Shell shows `unreported exception java.io.IOException` | A file operation needs a `try`/`catch` block in the Java Shell.  Send the error to the Chatbot and ask for a fix. |
| Claude says it cannot see an image | If SpannBridge skipped the image, its window says why (`image part skipped: …`).  SpannBridge does not support web links or very large files. |
| Answers mention your own projects or Claude Code settings | Your copy of Claude Code is too old for safe mode.  Run `claude update`. |
| `WinError 2` when SpannBridge starts Claude Code | `ADAPTER_WORK_DIR` points into `AppData` while you use Microsoft Store Python.  Use the default. |
| `This event loop cannot spawn subprocesses` | Start with `python Start-SpannBridge.py` or `python adapter.py`, not with `uvicorn --reload`. |

## Limitations

- **Tool calling must stay off.**  The Chatbot's documentation search needs the chat *client* to run the search tool.  Claude Code cannot return a tool call to the Chatbot.  If the Chatbot sends tools, SpannBridge ignores them and answers as plain chat.
- **One user, one PC.**  SpannBridge listens only on 127.0.0.1 and refuses requests from web pages.  Do not make it reachable from a network, and do not share it.  See [Is this allowed?](#is-this-allowed-check-before-you-run-it).  Without `--token`, other programs on your PC could use your plan through SpannBridge.
- **Claude Code runs with your own Windows permissions.**  SpannBridge turns off every Claude Code tool through Claude Code's own options, and Claude Code then reports an empty tool list (verified on 3 October 2026).  SpannBridge does not run Claude Code in an operating-system sandbox, so this protection depends on those options working as documented.
- **Every message starts Claude Code again,** which adds about 0.8 s (measured on 22 September 2026), and resends the whole conversation.  Long conversations with many images therefore become slower and use more of your plan.
- SpannBridge ignores the Chatbot's `temperature` and maximum-token settings, because Claude Code has no equivalent.
- SpannBridge does not fetch images sent as web links.  Only attached images work.
- SpannBridge makes no automatic retries.  If Claude Code fails, you see the error and decide whether to resend.
- SpannBridge was tested on Windows only.

## If you are reading this in the future

SpannBridge connects three products that change on their own schedules: Claude Code, Anthropic's models and policies, and COMSOL Multiphysics® software.  This section lists what is likely to change and how to check it.

### Anthropic's rules and billing

These rules are the most likely to change.  A change can make SpannBridge unusable for you.  Use the checklist in [How to check the current rules](#how-to-check-the-current-rules) before you rely on SpannBridge.

### Model names

- **Aliases follow your installed copy of Claude Code, not Anthropic's website.**  `sonnet` means the newest Sonnet model that *your copy* of Claude Code knows.  For example, on 3 Oct 2026 Anthropic's models page already listed Claude Sonnet 5.5 (`claude-sonnet-5-5`).  Claude Code 2.1.280 still mapped `sonnet` to `claude-sonnet-5`.  Updating Claude Code (`claude update`) moves the aliases forward.  Until then, the full ID works.  Claude Code prints an `unrecognized_model` warning but runs the model.
- **To see which model an alias selects,** run this command.  It uses one tiny request:

  ```powershell
  ("hi" | claude -p --model sonnet --output-format json | ConvertFrom-Json).modelUsage.PSObject.Properties.Name
  ```

- **Current models, IDs, and retirement dates** are on Anthropic's [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) and [model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations) pages.  A full ID stops working when Anthropic retires that model.  Aliases avoid this problem.  The model families themselves (`sonnet`, `opus`, `haiku`, and `fable`) may also change.
- The model list at `/v1/models` is for information only and may be out of date.  The Chatbot does not use it.

### Effort and thinking

The effort levels, each model's default, and whether thinking can be turned off differ by model and change over time.  For example, thinking is always on for Fable 5.1, Opus 5.5, and Sonnet 5.5, so `:off` has no effect there.  When `claude update` moves `sonnet` to Sonnet 5.5, `:off` and `--thinking-off` will no longer have an effect on `sonnet` either.  Current details are on the Claude Code [model configuration](https://code.claude.com/docs/en/model-config) page.  The timing table above comes from one model on one day.  Measure again with your own setup.

### Claude Code itself

Claude Code updates itself.  Its command-line options (flags) can change.

- At startup, SpannBridge prints which optional flags your copy of Claude Code supports (the `flags` line).  It uses only those.  If a *required* flag disappears, requests fail with a message that usually contains `unknown option`.
- **After any Claude Code update, run** `python tests\smoke_test.py`.  If replies start to arrive all at once at the end instead of streaming, Claude Code has changed its streaming format.  SpannBridge still delivers the full answer.
- If an update breaks SpannBridge, you can return to the tested version (2.1.280) with `& ([scriptblock]::Create((irm https://claude.ai/install.ps1))) 2.1.280`.  Then stop automatic updates as described on Anthropic's [setup page](https://code.claude.com/docs/en/setup).  Treat this as a temporary measure only, because you also miss security fixes.
- Installation commands and download addresses may move.  Anthropic's [setup page](https://code.claude.com/docs/en/setup) has the current ones.

### COMSOL Multiphysics® software

Later versions of COMSOL Multiphysics® may change the Chatbot preferences, add providers, handle tool calling differently, or run the Chatbot on Mac and Linux.  They may also change how attachments and the Java Shell work.  SpannBridge was tested only with version 6.4.  Check *Chatbot Preference Settings* in the COMSOL® documentation for your version.  SpannBridge accepts any address that ends in `chat/completions`, so it keeps working if the form of the Base URL changes.  The SpannBridge window logs every request, so it is the first place to look when something changes.

On 16 September 2026, COMSOL AB announced COMSOL Multiphysics® version 2027 for release in fall 2026 ([press release](https://www.comsol.com/press-release/system-level-modeling-and-agentic-ai-take-the-spotlight-in-comsol-multiphysics-version-2027-14722)).  It adds the COMSOL® MCP Server.  The server uses the Model Context Protocol (MCP), a standard way for AI agents to use outside tools, so that external AI agents can work with COMSOL Multiphysics® directly through its API.  This is a different route from SpannBridge, which connects an AI service to the Chatbot window.

### Python packages

`requirements.txt` lists minimum versions.  If a future FastAPI or uvicorn release breaks SpannBridge, install the newest versions that passed the offline tests on 3 October 2026:

```powershell
python -m pip install "fastapi==0.142.2" "uvicorn==0.54.0" "Pillow==12.3.0"
```

The older versions in the *Tested with* list (FastAPI 0.97.0, uvicorn 0.22.0, and Pillow 9.5.0) may not install on newer Python.  Pillow 9.5.0 needs Python 3.10 or 3.11.

### Mac and Linux

The Chatbot in COMSOL Multiphysics® 6.4 is Windows-only, so this release targets Windows.  A later version of COMSOL Multiphysics® may bring the Chatbot to other platforms.  In that case, these points apply:

- `adapter.py` and `Start-SpannBridge.py` are mostly portable but are untested on Mac and Linux.  Run the launcher with `python3 Start-SpannBridge.py`.
- On timeout, SpannBridge would need to stop the whole Claude Code process group rather than one process.
- Install Claude Code with `curl -fsSL https://claude.ai/install.sh | bash`.

Developers who adapt SpannBridge should read [DEEP-DIVE.md](DEEP-DIVE.md) first.

## Reporting a problem and contact

To report a bug, open an issue on GitHub, so that other users can see the problem and its fix.  Include this information:

- the SpannBridge version (the first line of its window)
- the output of `claude --version`
- your COMSOL Multiphysics® version
- the Model id
- the lines in the SpannBridge window around the problem

Before you post, remove your email address, any API key or `--token` value, paths that contain your user name, and any confidential model content.

For a security problem, or for anything else that should not be public, email [spannbridge@spann.ai](mailto:spannbridge@spann.ai).  Use the same address for other questions about SpannBridge.  Do not send passwords, API keys, or confidential model files.  SpannBridge is a free tech demo with no support agreement, so a reply or a fix is not guaranteed.

## Using the Claude API directly instead

The Chatbot can also use Anthropic's own OpenAI-compatible service directly, with **no SpannBridge**.  This route bills per token to a Claude Console API key.  It is the supported route for work use and for anything beyond personal experiments.  It is also the route to use if Anthropic stops allowing subscription use.

| Setting | Value |
|---|---|
| Provider | OpenAI API compatible |
| Base URL | `https://api.anthropic.com/v1` |
| Model id | A current model ID, for example `claude-sonnet-5-5`.  See the [models overview](https://platform.claude.com/docs/en/about-claude/models/overview). |
| Context length | `200000` |
| Tool calling | On.  The Chatbot's documentation search works on this route. |
| API key | A key from [platform.claude.com](https://platform.claude.com/).  Set a spending limit. |

Details are on Anthropic's [OpenAI SDK compatibility](https://platform.claude.com/docs/en/api/openai-sdk) page.

## Other AI providers

**Grok Build and Muse Code.**  To the best of our knowledge, SpannBridge could be adapted to two other official command-line programs that you sign in to with a subscription: Grok Build (`grok`) from xAI and Muse Code (`muse`) from Meta.  Both programs have a headless mode, which another program can start in the same way that SpannBridge starts Claude Code.  Spann Engineering Consulting LLC has not tested either adaptation.  It is also not confirmed that their headless modes use the subscription rather than a separately billed API key.  Section 8 of [DEEP-DIVE.md](DEEP-DIVE.md) has notes on both programs and a checklist for the adaptation.  If an AI coding assistant helps you, have it read DEEP-DIVE.md first, because the file was written for that use.  Read each vendor's current terms and billing rules before you start.

**Google Gemini.**  Do not adapt SpannBridge to a Google AI subscription because Google's current terms prohibit this structure.  On 18 June 2026, Gemini CLI stopped accepting sign-in with a Google AI Pro or Ultra subscription ([Google's notice](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals)).  Those subscriptions now work with Google's Antigravity products.  The [Antigravity terms](https://antigravity.google/terms) state that the use of third-party software, tools, or services to access the service is a breach of the agreement.  An adapted SpannBridge would be such third-party software.  In February 2026, Google suspended the accounts of subscribers who used such tools ([Google's post](https://github.com/google-gemini/gemini-cli/discussions/20632)).

**The paid APIs.**  xAI, Meta, and Google also sell API access through OpenAI-compatible addresses.  The Chatbot can use those addresses directly without SpannBridge.

This section describes the vendors' public pages as read on 3 October 2026.  It is not legal advice.

## What the MIT License means for you

SpannBridge is free, open-source software.  Its copyright holder is Spann Engineering Consulting LLC.  It is released under the [MIT License](LICENSE), a short and widely used license that allows almost any use of the code.  In plain terms:

- **You can use it for anything,** including paid engineering and consulting work, without paying or asking permission.
- **Your work is yours.**  Spann Engineering Consulting LLC claims no ownership of, rights in, or credit for anything you create while you use SpannBridge.  This includes models, code, Chatbot answers, calculations, reports, and designs.
- **Using SpannBridge requires no acknowledgment.**  You do not need to mention SpannBridge or Spann Engineering Consulting LLC anywhere when you use it to get Chatbot answers for an engineering project.
- **The license's only condition concerns redistribution of SpannBridge's own code.**  If you copy, share, or publish SpannBridge's source files, changed or unchanged, keep the copyright notice and the license text with them.
- **No warranty and no liability.**  SpannBridge is provided "as is".  Spann Engineering Consulting LLC accepts no liability for SpannBridge or for anything produced with it.  You are responsible for checking results.  See [Check the engineering](#check-the-engineering).
- **Other companies' terms still apply.**  The MIT License covers SpannBridge only.  It does not grant you access to Anthropic's services or change their terms.  Your agreements with Anthropic and COMSOL AB govern your use of Claude, Claude Code, and COMSOL Multiphysics® software.

This summary is for convenience.  The [LICENSE](LICENSE) file is the legal text.

## Publisher, trademarks, and affiliation

**Publisher.**  Spann Engineering Consulting LLC publishes SpannBridge and holds its copyright.  Andrew Spann, the founder and owner of Spann Engineering Consulting LLC, created SpannBridge.  Spann Engineering Consulting LLC is the company's legal name.  *Spann.AI* is its brand name.  The website [spann.ai](https://spann.ai) belongs to the same company.  In this repository, "Spann.AI" and "Spann Engineering Consulting LLC" both refer to that one company.  The contact address for SpannBridge is [spannbridge@spann.ai](mailto:spannbridge@spann.ai).

**COMSOL AB.**  **This GitHub repository is neither developed by nor endorsed by COMSOL AB.**  This repository and its software are not affiliated with COMSOL AB.  COMSOL AB has not authorized, sponsored, or approved them and is not otherwise connected to them.  Spann Engineering Consulting LLC is a COMSOL® Certified Consultant.  That certification does not mean that COMSOL AB authorized, sponsored, or approved this project.

**Anthropic PBC.**  This repository is not developed, endorsed, or sponsored by Anthropic PBC.

**Trademarks.**  COMSOL and COMSOL Multiphysics are registered trademarks of COMSOL AB.  Anthropic, Claude, and Claude Code are trademarks of Anthropic PBC.  Other names in this repository, such as OpenAI, ChatGPT, Codex, xAI, Grok, Meta, Muse, Google, Gemini, and Antigravity, are trademarks of their respective owners.  This repository uses these names only to identify those companies and their products.  Your agreement with Anthropic governs your use of Claude and Claude Code.  Your license agreement with COMSOL AB governs your use of COMSOL Multiphysics® software.  See [the trademark guidelines of COMSOL AB](https://www.comsol.com/trademarks).
