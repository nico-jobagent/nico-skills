# Nico Job Agent Skills

AI agent skill for searching Nico Job Agent's job index and adding job postings as proposed jobs to [Nico Job Agent](https://nico-jobagent.com) via its API.

## Contents

- [Compatible Agents](#compatible-agents)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Quick Setup](#quick-setup)
  - [Manual Installation](#manual-installation)
  - [Configuration](#configuration)
- [CLI Manual](#cli-manual)
  - [`posting` — job posting search](#posting--job-posting-search)
  - [`application` — job application management](#application--job-application-management)
- [License](#license)

## Compatible Agents

Works with any agent that supports skills via `SKILL.md`:

- **Claude Code** (Anthropic)
- **OpenClaw**
- **Cursor**
- **GitHub Copilot**
- Any agent that can read `SKILL.md` and run shell commands

## Installation

### Prerequisites

- **python3** (uses only stdlib — no pip install needed)
- A **Nico API key** (`NICO_API_KEY`)

### Quick Setup

```bash
git clone https://github.com/nico-jobagent/nico-skills.git
cd nico-skills
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Check that python3 is available
2. Prompt for your API credentials (`NICO_API_KEY`, `NICO_API_URL`)
3. Detect installed AI agents (Claude Code, OpenClaw, Cursor, GitHub Copilot)
4. Symlink the skill into each agent's skill directory
5. Write the env vars to your shell profile (`~/.zshrc` or `~/.bashrc`)

After setup, reload your shell config:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Manual Installation

#### Claude Code

**Option A — Plugin mode** (recommended):
```bash
claude --plugin-dir /path/to/nico-skills
```

**Option B — User skill**:
```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.claude/skills/nico-jobagent
```

#### OpenClaw

```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.openclaw/skills/nico-jobagent
```

Or configure in `~/.openclaw/openclaw.json`:
```json5
{
  skills: {
    load: {
      extraDirs: ["/path/to/nico-skills/skills"]
    }
  }
}
```

#### Cursor

**Option A — Remote rule**: Settings > Rules > Add Rule > Remote Rule (GitHub) > enter repo URL

**Option B — User skill**:
```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.cursor/skills/nico-jobagent
```

#### GitHub Copilot

```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.copilot/skills/nico-jobagent
```

Or copy into your repo:
```bash
cp -r /path/to/nico-skills/skills/nico-jobagent .github/skills/nico-jobagent
```

#### Any Other Agent

Point your agent at:
- **Instructions**: `skills/nico-jobagent/SKILL.md`
- **CLI tool**: `skills/nico-jobagent/scripts/nico_client.py`

### Configuration

Set these environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NICO_API_KEY` | Yes | — | Your Nico API authentication key |
| `NICO_API_URL` | No | `api.nico-jobagent.com` | Nico API base URL (scheme optional — `https://` is added if omitted) |

Add to your shell profile or agent's environment settings.

## CLI Manual

The skill uses `scripts/nico_client.py`, a zero-dependency Python CLI. All commands
print JSON to stdout. Commands come in two groups:

| Group | Purpose |
|---|---|
| `posting` | **Job posting search** — discover openings in Nico's index (read-only) |
| `application` | **Job application management** — your tracked applications |

Run `python3 scripts/nico_client.py --help` for the full command list.

### `posting` — job posting search

```bash
# Search — in a specific state
python3 scripts/nico_client.py posting search --title "backend engineer" --country US --region California

# Search — remote roles (don't pair --region with --work-mode remote — remote
# postings aren't pinned to a state, so that combination returns nothing)
python3 scripts/nico_client.py posting search --title "backend engineer" --country US --work-mode remote

# Get one posting's full detail (application url + description) by id
python3 scripts/nico_client.py posting get --id "019e5132-627d-799e-963e-3c24f72a9dd5"
```

`posting search` accepts employer/city **names** (resolved for you); `--country` is required;
results are compact (no url/description — that's what `posting get` is for).
Requires job search enabled for the account.

### `application` — job application management

```bash
# Check for duplicates (by URL or company name)
python3 scripts/nico_client.py application search --url "https://company.com/jobs/123"
python3 scripts/nico_client.py application search --company-name "Acme Inc"

# List your applications
python3 scripts/nico_client.py application list --status draft

# Fetch one application's full detail (incl. notes and interviews)
python3 scripts/nico_client.py application get --id "<application_id>"

# Parse a job URL to extract details
python3 scripts/nico_client.py application parse-url --url "https://company.com/jobs/123"

# Create a proposed application
python3 scripts/nico_client.py application create \
  --title "Software Engineer" \
  --company "Acme Inc" \
  --url "https://company.com/jobs/123" \
  --location "Berlin, Germany" \
  --work-mode "remote"

# Add a note
python3 scripts/nico_client.py application add-note --id "<application_id>" --body "Recruiter replied"
```

Work modes (create): `remote`, `remote-optional`, `hybrid`, `on-site`.
Status filters (list): `draft`, `applied`, `interviewing`, `offer`, `finished`, `active`.

## License

MIT
