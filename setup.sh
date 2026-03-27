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
SKILL_DIR="$SCRIPT_DIR/skills/nico-jobagent"

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
    if [ -L "$target_dir/nico-jobagent" ] || [ -d "$target_dir/nico-jobagent" ]; then
        echo "  Skill already exists at $target_dir/nico-jobagent — skipping."
    else
        ln -s "$SKILL_DIR" "$target_dir/nico-jobagent"
        echo "  Installed for $agent_name: $target_dir/nico-jobagent -> $SKILL_DIR"
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

# Detect shell profile
if [ -f "$HOME/.zshrc" ]; then
    shell_profile="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    shell_profile="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    shell_profile="$HOME/.bash_profile"
else
    shell_profile=""
fi

if [ -n "$shell_profile" ]; then
    echo ""
    read -rp "Add NICO_API_KEY and NICO_API_URL to $shell_profile? [Y/n] " yn
    if [[ "$yn" != "n" && "$yn" != "N" ]]; then
        # Remove existing entries to avoid duplicates
        if grep -q "^export NICO_API_KEY=" "$shell_profile" 2>/dev/null; then
            sed -i.bak '/^export NICO_API_KEY=/d' "$shell_profile"
            sed -i.bak '/^export NICO_API_URL=/d' "$shell_profile"
            rm -f "${shell_profile}.bak"
        fi
        echo "" >> "$shell_profile"
        echo "# Nico Job Agent" >> "$shell_profile"
        echo "export NICO_API_KEY=\"$api_key\"" >> "$shell_profile"
        echo "export NICO_API_URL=\"$api_url\"" >> "$shell_profile"
        echo "  Added to $shell_profile"
        echo ""
        echo "  Run 'source $shell_profile' or open a new terminal to activate."
    fi
else
    echo ""
    echo "  Could not detect shell profile. Add these to your shell config manually:"
    echo ""
    echo "    export NICO_API_KEY=\"$api_key\""
    echo "    export NICO_API_URL=\"$api_url\""
fi

echo ""
echo "Setup complete!"
