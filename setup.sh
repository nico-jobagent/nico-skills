#!/bin/bash
set -e

echo "Nico Job Agent Skills - Setup"
echo "=============================="
echo ""

# Check python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found on PATH."
    echo "Install it from https://www.python.org/downloads/ or via your package manager."
    exit 1
fi
echo "python3 found: $(python3 --version)"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/skills/nico-job-search"

# Prompt for API key
echo ""
read -rp "Enter your NICO_API_KEY: " api_key
if [ -z "$api_key" ]; then
    echo "Error: API key is required."
    exit 1
fi

# Prompt for API URL
read -rp "Enter your NICO_API_URL [https://staging.nico-jobagent.com]: " api_url
api_url="${api_url:-https://staging.nico-jobagent.com}"

# Detect installed agents
echo ""
echo "Detecting AI agents..."

agents_found=()
if command -v claude &> /dev/null; then
    agents_found+=("claude")
    echo "  Found: Claude Code"
fi
if command -v openclaw &> /dev/null; then
    agents_found+=("openclaw")
    echo "  Found: OpenClaw"
fi
if [ -d "$HOME/.cursor" ]; then
    agents_found+=("cursor")
    echo "  Found: Cursor"
fi
if [ -d "$HOME/.copilot" ] || command -v gh &> /dev/null; then
    agents_found+=("copilot")
    echo "  Found: GitHub Copilot"
fi

if [ ${#agents_found[@]} -eq 0 ]; then
    echo "  No AI agents detected automatically."
fi

# Install skill for detected agents
echo ""
echo "Install options:"
echo ""

install_skill() {
    local target_dir="$1"
    local agent_name="$2"

    mkdir -p "$target_dir"
    if [ -L "$target_dir/nico-job-search" ] || [ -d "$target_dir/nico-job-search" ]; then
        echo "  Skill already exists at $target_dir/nico-job-search — skipping."
    else
        ln -s "$SKILL_DIR" "$target_dir/nico-job-search"
        echo "  Installed for $agent_name: $target_dir/nico-job-search -> $SKILL_DIR"
    fi
}

for agent in "${agents_found[@]}"; do
    case "$agent" in
        claude)
            read -rp "Install for Claude Code (~/.claude/skills/)? [Y/n] " yn
            if [[ "$yn" != "n" && "$yn" != "N" ]]; then
                install_skill "$HOME/.claude/skills" "Claude Code"
            fi
            ;;
        openclaw)
            read -rp "Install for OpenClaw (~/.openclaw/skills/)? [Y/n] " yn
            if [[ "$yn" != "n" && "$yn" != "N" ]]; then
                install_skill "$HOME/.openclaw/skills" "OpenClaw"
            fi
            ;;
        cursor)
            read -rp "Install for Cursor (~/.cursor/skills/)? [Y/n] " yn
            if [[ "$yn" != "n" && "$yn" != "N" ]]; then
                install_skill "$HOME/.cursor/skills" "Cursor"
            fi
            ;;
        copilot)
            read -rp "Install for GitHub Copilot (~/.copilot/skills/)? [Y/n] " yn
            if [[ "$yn" != "n" && "$yn" != "N" ]]; then
                install_skill "$HOME/.copilot/skills" "GitHub Copilot"
            fi
            ;;
    esac
done

# Environment variable configuration
echo ""
echo "Environment Configuration"
echo "========================="
echo ""
echo "Set these environment variables for your agent:"
echo ""
echo "  export NICO_API_KEY=\"$api_key\""
echo "  export NICO_API_URL=\"$api_url\""
echo ""
echo "Add them to your shell profile (~/.bashrc, ~/.zshrc) or configure"
echo "them in your agent's settings:"
echo ""
echo "  Claude Code:  Add to settings.json env section"
echo "  OpenClaw:     Add to ~/.openclaw/openclaw.json skills.entries"
echo "  Cursor:       Add to workspace environment"
echo "  Copilot:      Add to shell profile"
echo ""
echo "Setup complete!"
