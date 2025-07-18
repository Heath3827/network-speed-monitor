# 🌐 Network Speed Monitor

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](https://github.com)

A powerful CLI tool to **track internet speed over time** with smart alerts, beautiful reports, and comprehensive monitoring capabilities.

## ✨ Features

- 🔄 **Continuous Monitoring** - Track speed at configurable intervals (5m, 30m, 1h, etc.)
- 🚨 **Smart Alerts** - Get notified when speed drops below your threshold
- 📊 **Beautiful Reports** - Generate charts and export data (PNG, CSV, JSON)
- 💾 **Historical Data** - SQLite database stores all your speed test history
- 🌐 **Server Selection** - Test against closest or fastest servers
- 🎨 **Rich CLI** - Colored output with formatted tables
- 🐍 **Virtual Environment** - Isolated dependencies for clean installation
- ⚡ **Easy Alias** - Simple `speed-monitor` command after installation

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/LinuxCTRL/network-speed-monitor.git
cd network-speed-monitor

# Install with virtual environment (recommended)
chmod +x install_venv.sh
./install_venv.sh

# Restart terminal or reload shell
source ~/.bashrc
```

### Basic Usage

```bash
# Test your installation
speed-monitor --help

# Run a quick speed test
speed-monitor test --quick

# Start continuous monitoring (every 30 minutes, alert below 50 Mbps)
speed-monitor start --interval 30m --alert-threshold 50Mbps

# Generate a weekly report with chart
speed-monitor report --last-week --export png

# View recent history
speed-monitor history --limit 10
```

## 📋 Commands

### Core Commands

| Command  | Description                    | Example                                                       |
| -------- | ------------------------------ | ------------------------------------------------------------- |
| `start`  | Begin continuous monitoring    | `speed-monitor start --interval 15m --alert-threshold 25Mbps` |
| `stop`   | Stop monitoring process        | `speed-monitor stop`                                          |
| `status` | Show current monitoring status | `speed-monitor status`                                        |
| `test`   | Run single speed test          | `speed-monitor test --quick`                                  |

### Reporting Commands

| Command   | Description                    | Example                                         |
| --------- | ------------------------------ | ----------------------------------------------- |
| `report`  | Generate comprehensive reports | `speed-monitor report --last-week --export png` |
| `history` | Show recent test history       | `speed-monitor history --limit 20`              |
| `cleanup` | Remove old data                | `speed-monitor cleanup --days 30`               |

### Advanced Options

```bash
# Monitoring with custom settings
speed-monitor start --interval 5m --alert-threshold 100Mbps --email user@example.com

# Detailed reports
speed-monitor report --stats                    # Show statistics
speed-monitor report --today --export csv       # Today's data as CSV
speed-monitor report --last-month --export json # Monthly data as JSON

# Server selection
speed-monitor test --servers closest            # Use closest servers
speed-monitor test --servers fastest            # Use fastest servers
```

## 📊 Sample Output

### Speed Test Results

```
┌─────────────────┬─────────────────┐
│ Metric          │ Value           │
├─────────────────┼─────────────────┤
│ Download Speed  │ 85.4 Mbps       │
│ Upload Speed    │ 12.3 Mbps       │
│ Ping            │ 23.1 ms         │
│ Server          │ New York, US    │
│ ISP             │ Verizon         │
│ Timestamp       │ 2024-01-15 14:30│
└─────────────────┴─────────────────┘
```

### Monitoring Output

```
🚀 Starting speed monitoring...
📊 Interval: 900s (15m)
🚨 Alert threshold: 50.0 Mbps
💾 Database: /home/user/.local/share/speed-monitor/speeds.db
Press Ctrl+C to stop

🔄 Running speed test...

┌─────────────────┬─────────────────┐
│ Metric          │ Value           │
├─────────────────┼─────────────────┤
│ Download Speed  │ 45.2 Mbps       │
│ Upload Speed    │ 8.7 Mbps        │
│ Ping            │ 28.3 ms         │
│ Server          │ Chicago, US     │
│ Status          │ ALERT           │
│ Timestamp       │ 14:32:15        │
└─────────────────┴─────────────────┘

🚨 SPEED ALERT: Download speed (45.2 Mbps) is below threshold (50.0 Mbps)
⏰ Next test in 15 minutes...
```

## 📈 Reports & Charts

The tool generates beautiful charts showing your internet speed over time:

- **PNG Charts** - Visual speed trends with download/upload lines
- **CSV Export** - Raw data for spreadsheet analysis
- **JSON Export** - Structured data for programmatic use
- **Statistics** - Min, max, average speeds and alert counts

## ⚙️ Configuration

Configuration is stored at `~/.config/speed-monitor/config.json`:

```json
{
  "default_interval": "15m",
  "default_threshold": "10Mbps",
  "database_path": "~/.local/share/speed-monitor/speeds.db",
  "alert_email": null,
  "preferred_servers": ["closest"],
  "log_level": "INFO"
}
```

## 🔧 Requirements

- **Python 3.7+**
- **speedtest-cli** (automatically installed)
- **Virtual environment** (automatically created)

### Dependencies

```
speedtest-cli>=2.1.3    # Speed testing
matplotlib>=3.5.0       # Chart generation
click>=8.0.0           # CLI interface
tabulate>=0.9.0        # Table formatting
colorama>=0.4.4        # Colored output
requests>=2.25.0       # HTTP requests
```

## 🗂️ Data Storage

- **Database**: `~/.local/share/speed-monitor/speeds.db` (SQLite)
- **Config**: `~/.config/speed-monitor/config.json`
- **Logs**: `~/.local/share/speed-monitor/alerts.log`

All data is stored locally for privacy and security.

## 🛠️ Development

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python3 speed_monitor_complete.py --help
```

### Project Structure

```
network-speed-monitor/
├── speed_monitor_complete.py   # Main application
├── install_venv.sh            # Installation script
├── run.sh                     # Runner script
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── demo.py                    # Demo script
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [speedtest-cli](https://github.com/sivel/speedtest-cli) for the speed testing functionality
- [Click](https://click.palletsprojects.com/) for the excellent CLI framework
- [matplotlib](https://matplotlib.org/) for chart generation

## 📞 Support

- 🐛 **Bug Reports**: [Open an issue](https://github.com/LinuxCTRL/network-speed-monitor/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/LinuxCTRL/network-speed-monitor/discussions)
- 📧 **Contact**: sofalcons@outlook.com

---

⭐ **Star this repo** if you find it helpful!

Made with ❤️ for network monitoring enthusiasts
