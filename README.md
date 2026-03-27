# Nico Job Agent Skills

AI agent skill for adding job postings as proposed jobs to [Nico Job Agent](https://github.com/nico-jobagent) via its API.

## Compatible Agents

Works with any agent that supports the [AgentSkills](https://agentskills.org) standard:

- **Claude Code** (Anthropic)
- **OpenClaw**
- **Cursor**
- **GitHub Copilot**
- Any agent that can read `SKILL.md` and run shell commands

## Prerequisites

- **python3** (uses only stdlib — no pip install needed)
- A **Nico API key** (`NICO_API_KEY`)

## Quick Setup

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

## Manual Installation

### Claude Code

**Option A — Plugin mode** (recommended):
```bash
claude --plugin-dir /path/to/nico-skills
```

**Option B — User skill**:
```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.claude/skills/nico-jobagent
```

### OpenClaw

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

### Cursor

**Option A — Remote rule**: Settings > Rules > Add Rule > Remote Rule (GitHub) > enter repo URL

**Option B — User skill**:
```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.cursor/skills/nico-jobagent
```

### GitHub Copilot

```bash
ln -s /path/to/nico-skills/skills/nico-jobagent ~/.copilot/skills/nico-jobagent
```

Or copy into your repo:
```bash
cp -r /path/to/nico-skills/skills/nico-jobagent .github/skills/nico-jobagent
```

### Any Other Agent

Point your agent at:
- **Instructions**: `skills/nico-jobagent/SKILL.md`
- **CLI tool**: `skills/nico-jobagent/scripts/nico_client.py`

## Configuration

Set these environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NICO_API_KEY` | Yes | — | Your Nico API authentication key |
| `NICO_API_URL` | No | `https://staging.nico-jobagent.com` | Nico API base URL |

Add to your shell profile or agent's environment settings.

## CLI Reference

The skill uses `scripts/nico_client.py`, a zero-dependency Python CLI:

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
