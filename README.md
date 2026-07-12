# Nico Job Agent Skills

AI agent skill for searching Nico Job Agent's global job index and adding job postings as proposed jobs to [Nico Job Agent](https://nico-jobagent.com) via its API.

## Contents

- [Compatible Agents](#compatible-agents)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Quick Setup](#quick-setup)
  - [Manual Installation](#manual-installation)
  - [Configuration](#configuration)
- [CLI Manual](#cli-manual)
  - [Search Nico's global job index](#search-nicos-global-job-index-discover-openings)
  - [Parse a job URL](#parse-a-job-url)
  - [Check for duplicates](#check-for-duplicates)
  - [Create a proposed job](#create-a-proposed-job)
  - [List jobs](#list-jobs)
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
print JSON to stdout. Run `python3 scripts/nico_client.py --help` for the full command list.

### Search Nico's global job index (discover openings)

```bash
python3 scripts/nico_client.py search-postings \
  --title "backend engineer" --country US --region California --work-mode remote
```

Accepts employer/city **names** (resolved for you) — exact parity with Nico's MCP
`search_job_postings` tool. `--country` is required. Requires job search enabled for the account.

### Parse a job URL

```bash
python3 scripts/nico_client.py parse-url --url "https://company.com/jobs/123"
```

### Check for duplicates

```bash
# By URL
python3 scripts/nico_client.py search --url "https://company.com/jobs/123"

# By company name
python3 scripts/nico_client.py search --company-name "Acme Inc"
```

### Create a proposed job

```bash
python3 scripts/nico_client.py create \
  --title "Software Engineer" \
  --company "Acme Inc" \
  --url "https://company.com/jobs/123" \
  --location "Berlin, Germany" \
  --work-mode "remote"
```

Work modes: `remote`, `remote-optional`, `hybrid`, `on-site`

### List jobs

```bash
python3 scripts/nico_client.py list --status draft
```

Status filters: `draft`, `applied`, `interviewing`, `offer`, `finished`, `active`

## License

MIT
