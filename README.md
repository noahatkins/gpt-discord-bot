# Discord OpenAI Bot

A lightweight Discord bot powered by OpenAI’s Chat Completions API. It exposes a `/ask` slash command that creates a dedicated thread for each request, keeps the entire thread history in memory, and replies inside that thread so everyone can follow the conversation.

> **Status:** Actively developed proof-of-concept. Great for personal servers; adapt before running at larger scale or with persistent storage.

## Features

- `/ask` slash command with per-thread OpenAI context
- Automatic thread creation and cleanup when threads are archived/deleted
- In-memory conversation history for quick experimentation
- Configurable OpenAI model via `OPENAI_MODEL`

## Prerequisites

- Python 3.11+
- Discord application & bot token with the **Message Content Intent** enabled
- OpenAI API key with access to the model you configure (default `gpt-4o-mini`)

## Quick Start

1. Clone and install deps:
   ```bash
   git clone https://github.com/noahatkins/python-bot.git
   cd python-bot
   python -m venv .venv
   .\.venv\Scripts\activate  # source .venv/bin/activate on macOS/Linux
   pip install -r requirements.txt
   ```
2. Copy `env.example` → `.env` and fill in:
   - `DISCORD_TOKEN`
   - `OPENAI_API_KEY`
   - optional `OPENAI_MODEL`
3. Run the bot:
   ```bash
   python bot.py
   ```
4. Invite the bot with scopes `bot applications.commands`. Grant **Send Messages**, **Create Public Threads**, **Send Messages in Threads**, **Manage Threads**, **Read Message History**, and **Use Slash Commands**.

## `/ask` Workflow

```
1. /ask prompt:"Could you outline the steps to deploy this Discord bot to a Raspberry Pi?"
2. Bot replies in the channel, creates a thread, asks OpenAI, and posts the first answer inside the new thread.
3. Keep chatting in that thread; every new user message becomes part of the OpenAI context so responses stay on topic.
```

The bot ignores messages outside those threads and skips replies to other bots by default.

## Configuration

| Variable         | Description                                    | Required |
|------------------|------------------------------------------------|----------|
| `DISCORD_TOKEN`  | Token from the Discord developer portal        | ✅       |
| `OPENAI_API_KEY` | OpenAI API key with chat-completions access    | ✅       |
| `OPENAI_MODEL`   | Override default model (`gpt-4o-mini`)         | ❌       |

Secrets are loaded via `.env` thanks to `python-dotenv`. Never commit `.env`; use `env.example` when sharing config.

### Secret Hygiene

- `.env` is already gitignored; keep your real keys there.
- Rotate Discord/OpenAI keys immediately if they leak (Discord dev portal → *Regenerate Token*, OpenAI dashboard → *View API keys*).
- When opening PRs, redact logs that might contain prompt contents or server names.

## Development

- Formatting/linting: `python -m py_compile bot.py services/openai_client.py`
- Run locally with `python bot.py`
- Tests are manual for now; add your own harness or mocks before shipping to production servers.

## Troubleshooting

- **Slash command not visible**: restart the bot so `bot.tree.sync()` runs, and ensure the invite included `applications.commands`.
- **Thread creation fails**: verify the bot has the thread permissions listed above and that you run `/ask` in a guild text channel (not DMs).
- **OpenAI errors**: check that `OPENAI_API_KEY` is valid and the model name exists in your account. The bot logs failures to the console.

## License

MIT © noahatkins

