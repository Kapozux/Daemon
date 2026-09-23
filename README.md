# Daemon

A ~400-line from-scratch SWE agent that autonomously resolves GitHub issues. Scored 60.3% on the full SWE-bench Lite benchmark (181/300).

## Features

- Three-stage loop: routing → planning → execution with self-correction
- Multi-model switching (DeepSeek / Kimi) via natural language
- Multi-agent coordination (spawn sub-agents for parallel tasks)
- File tools (read/write/search) alongside bash execution
- Exit-verified self-correction loop
- Context compression with original task preservation
- Rich terminal UI (spinner, streaming output)
- Dangerous command confirmation
- Headless mode for benchmarking (reads task file, outputs git diff)
- DAEMON.md project-specific preloading

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

## Headless Mode (SWE-bench)

```bash
python My_agent.py task.txt
# Reads task from file, runs autonomously, outputs patch.txt
```

## SWE-bench Results

| Run | Model | Instances | Score |
|-----|-------|-----------|-------|
| Baseline | Kimi K2.7 Code | 10 | 30% |
| v2 | DeepSeek V4 Flash | 30 (4 runs) | 67% mean |
| Full | DeepSeek V4 Flash | 300 | 60.3% |

## Architecture

My_agent.py — Main loop (routing → plan → execution)
llm.py — LLM clients, streaming, compression
actions.py — Action parsing, file tools, bash execution
chat_export.py — Chat history export
system_prompt.txt — Agent instructions
DAEMON.md — Project-specific context (optional)
## License

MIT