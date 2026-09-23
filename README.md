# Daemon

A ~400-line, from-scratch Python SWE agent — no LangChain, no agent framework, just
the OpenAI SDK and a bash-action loop. It reads a GitHub issue, edits the repo in
place, and verifies its own fix by running tests before exiting.

**SWE-bench Lite, pass@1: 173/300 (57.7%)** — see [Results](#results) for the full
breakdown and for why this differs from an earlier 60.3% headline number.

## Architecture

The agent is one file (`My_agent.py`) plus three small modules it imports
(`actions.py`, `llm.py`, `chat_export.py`) and a system prompt
(`system_prompt.txt`). No retrieval, no repo map, no framework — every turn is:
build the message list, call the model, parse one action out of its reply, run it,
feed the output back.

**Three-stage loop.**
1. **Routing** — a throwaway classification call decides `plan-needed` vs
   `plan-unwanted` for the user's instruction.
2. **Planning** (only if routed there) — the model proposes a plan in plain text and
   iterates on it with the user until it emits a `plan-finish` marker, capped at 20
   rounds.
3. **Execution** — the model emits one action per turn, wrapped as
   ` ```bash-action\n<command>\n``` `. Capped at 50 rounds; the loop also gives up
   after 3 consecutive turns with no parseable action.

**Action space.** `read file.py 10-20`, `write file.py 15 <content>` and
`search keyword ./dir` are handled directly in Python (line-based file I/O, not real
`sed`/`grep`), so the model always sees exact line numbers to edit against. Anything
else is a real shell command via `subprocess.run`, with a 120s timeout per call and a
short list of destructive patterns (`rm -rf`, `git push --force`, editing the agent's
own source, `.env`, ...) gated behind an interactive `y/n` confirmation.

**Self-correction.** The model isn't allowed to just say "done": emitting `exit`
gets pushed back with "run the tests first"; only `exit-verified` actually ends the
loop. The system prompt encodes a fixed bug-fixing recipe (reproduce → fix →
rerun repro → run existing tests → grep for the same mistake elsewhere →
`exit-verified`).

**Context compression.** Once a turn's reported token usage passes 50k, the agent
stops and asks the model to compress its own transcript — condense tool output
heavily, keep the human's original wording, keep the model's own reasoning — and
restarts the message list from that summary plus the original task, so a long
session doesn't lose the actual goal.

**Sub-agents.** The system prompt tells the model it can delegate: write a task
file and run `python My_Agent.py task.txt`, which recurses into the same headless
mode described below and hands back a `patch.txt`. There's no coordination beyond
that — a sub-agent is just another instance of the same loop.

**Backends.** `llm.py` streams from either DeepSeek (`deepseek-chat`) or Kimi
(`kimi-k2.7-code`) through the OpenAI SDK's chat-completions interface, switchable
mid-session by typing the model's name. `query_lm` retries up to 5 times on any
API exception (this is also where a DeepSeek-specific bug lived: DeepSeek's stream
emits a `usage` field that Moonshot's doesn't, and reading it unconditionally used
to crash every call the moment the backend was switched to DeepSeek — fixed by
guarding on `hasattr(chunk, "usage")`).

## Headless mode (how the benchmark runs it)

```bash
python My_agent.py task.txt
```

reads the issue text from `task.txt`, runs the normal execution loop non-interactively
(no planning stage, no `input()` prompts), and on exit runs `git diff` into
`patch.txt`. For SWE-bench, an external harness drops the four agent files
unmodified into each instance's official container, runs this command against
`/testbed`, and collects the resulting patch — the agent code itself has no
SWE-bench-specific logic.

## Results

**300/300 SWE-bench Lite instances, DeepSeek V4 Flash (`deepseek-chat`), pass@1** —
one attempt per instance, no reroll, no test-suite knowledge, no web browsing:

**173 / 300 resolved — 57.7%**

| Repo | Resolved | Empty patch |
| --- | --- | --- |
| django | 81 / 114 (71.1%) | 6 |
| sympy | 37 / 77 (48.1%) | 12 |
| scikit-learn | 14 / 23 (60.9%) | 1 |
| matplotlib | 12 / 23 (52.2%) | 1 |
| pytest-dev | 10 / 17 (58.8%) | 0 |
| sphinx-doc | 7 / 16 (43.8%) | 1 |
| psf (requests) | 2 / 6 (33.3%) | 0 |
| astropy | 3 / 6 (50.0%) | 0 |
| pylint-dev | 2 / 6 (33.3%) | 0 |
| pydata (xarray) | 2 / 5 (40.0%) | 1 |
| mwaskom (seaborn) | 2 / 4 (50.0%) | 1 |
| pallets (flask) | 1 / 3 (33.3%) | 0 |

23 instances (7.7%) got an empty patch — the model gave up, hit the retry cap on a
transient API error, or ran out of turns without ever emitting a diff.

**A note on measuring this correctly.** All 6 `psf/requests` instances came back
unresolved on the first evaluation pass (4 instances in parallel at a time). Its
tests hit real `httpbin`-backed network calls, which time out under concurrent load
independently of whether the patch is correct. Re-running the same, unchanged
patches one at a time flipped 2 of them to resolved — that's the number in the table
above. This is a real property of SWE-bench Lite's `psf__requests` tests, not
something specific to this agent; anyone benchmarking against it at high concurrency
should expect to see the same undercount.

**Why 57%, not 60.3%.** An earlier internal run allowed the agent to reroll once on
an empty diff (`--attempts 2` in the eval harness) and scored 181/300 (60.3%). That
number is *not* a valid pass@1 figure — the SWE-bench leaderboard requires exactly
one attempt per instance — so it isn't what's submitted. It's kept here only as a
best@2 data point: rerolling turned 19 of 23 first-try empty patches into a real
patch, and 9 of those (~3 points) went on to resolve, which is the actual measured
effect of giving the agent a second shot at instances where it produced nothing the
first time.

**Earlier, smaller runs** (kept for context, not comparable at this sample size):
10 instances on Kimi K2.7 Code scored 3/10; four repeated 30-instance samples on
DeepSeek V4 Flash after a module split scored 19–23/30 (mean 20.2, sd 1.9) —
a spread wide enough that no single 30-instance run should be trusted on its own.

## Known limitations

- **The dangerous-command confirmation blocks in headless mode.** If the model's
  action matches one of the destructive patterns, `execute_action` calls Python's
  `input()` — which has nothing to read from inside a non-interactive container and
  will hang until the harness's timeout kills the run. This has not been observed
  in the SWE-bench Lite run above, but it's a real failure mode for any task that
  legitimately needs e.g. `git push --force`.
- **120s per shell command.** Long-running test suites or builds that exceed this
  get killed and reported back as a timeout, not a real result.
- **Single-pass context compression.** When a session exceeds the token threshold,
  the transcript is summarized exactly once by asking the model to compress itself
  — there's no iterative or structured summarization, so very long sessions can
  still lose detail the compression pass judged unimportant at the time.
- **No repo map or retrieval.** Navigation is `search` (a plain substring grep) plus
  manual `read`/`write` by line number. This tracks with the per-repo results above:
  django, with its consistent app-per-directory layout, resolves well above average,
  while sympy — where the relevant code is harder to locate by keyword alone, and
  where 12 of 77 attempts produced no patch at all — resolves well below it.

## Leaderboard compliance

No web-browsing tool exists in the action space (`read`/`write`/`search`/shell only).
The harness feeds the agent only the issue's `problem_statement` — never
`hints_text`, `PASS_TO_PASS`, or `FAIL_TO_PASS` — so the model has no access to test
outcomes or hints while solving the task.

## Quickstart

```bash
# Clone
git clone https://github.com/Kapozux/Daemon.git
cd Daemon

# Setup
python -m venv .venv
source .venv/bin/activate
pip install openai python-dotenv rich

# Configure
cp .env.example .env
# Add your DEEPSEEK_API_KEY and MOONSHOT_API_KEY

# Run
python My_agent.py
```

## Files

- `My_agent.py` — main loop (routing → plan → execution)
- `llm.py` — LLM clients, streaming, compression
- `actions.py` — action parsing, file tools, bash execution
- `chat_export.py` — chat history export
- `system_prompt.txt` — agent instructions
- `DAEMON.md` — optional project-specific context, preloaded if present

## License

MIT
