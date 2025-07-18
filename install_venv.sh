#!/bin/bash

# Network Speed Monitor Installation Script with Virtual Environment

set -e

echo "Network Speed Monitor Installation with Virtual Environment"
echo "=========================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is required but not installed."
    echo "Please install pip3 and try again."
    exit 1
fi

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Make scripts executable
chmod +x speed_monitor_complete.py
chmod +x run.sh

# Create config directory
CONFIG_DIR="$HOME/.config/speed-monitor"
DATA_DIR="$HOME/.local/share/speed-monitor"

mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"

# Create default config if it doesn't exist
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default configuration..."
    cat > "$CONFIG_FILE" << EOF
{
    "default_interval": "15m",
    "default_threshold": "10Mbps",
    "database_path": "$DATA_DIR/speeds.db",
    "alert_email": null,
    "preferred_servers": ["closest"],
    "log_level": "INFO"
}
EOF
fi

# Create alias for easy access
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALIAS_COMMAND="alias speed-monitor='$SCRIPT_DIR/run.sh'"

# Add alias to shell configuration files
for shell_config in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile"; do
    if [ -f "$shell_config" ]; then
        # Check if alias already exists
        if ! grep -q "alias speed-monitor=" "$shell_config"; then
            echo "" >> "$shell_config"
            echo "# Network Speed Monitor alias" >> "$shell_config"
            echo "$ALIAS_COMMAND" >> "$shell_config"
            echo "Alias added to $shell_config"
        else
            echo "Alias already exists in $shell_config"
        fi
    fi
done

echo ""
echo "Installation completed successfully!"
echo ""
echo "USAGE OPTIONS:"
echo ""
echo "Option 1 - Use alias (recommended, restart terminal or run 'source ~/.bashrc'):"
echo "  speed-monitor --help"
echo "  speed-monitor start --interval 30m --alert-threshold 50Mbps"
echo "  speed-monitor test --quick"
echo "  speed-monitor report --last-week --export png"
echo ""
echo "Option 2 - Use runner script directly:"
echo "  ./run.sh --help"
echo "  ./run.sh start --interval 30m"
echo ""
echo "Option 3 - Manual virtual environment:"
echo "  source venv/bin/activate"
echo "  python3 speed_monitor_complete.py --help"
echo "  deactivate"
echo ""
echo "NEXT STEPS:"
echo "1. Restart your terminal or run: source ~/.bashrc"
echo "2. Test installation: speed-monitor --help"
echo "3. Run your first test: speed-monitor test --quick"
echo ""
echo "The virtual environment keeps all dependencies isolated and secure!"