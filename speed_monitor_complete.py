#!/usr/bin/env python3
"""
Network Speed Monitor - Track internet speed over time with alerts
"""

import os
import sys
import json
import sqlite3
import time
import subprocess
import threading
import signal
from datetime import datetime, timedelta
from pathlib import Path
import click
import requests
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init()

class SpeedMonitor:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'speed-monitor'
        self.data_dir = Path.home() / '.local' / 'share' / 'speed-monitor'
        self.config_file = self.config_dir / 'config.json'
        self.db_path = self.data_dir / 'speeds.db'
        self.pid_file = self.data_dir / 'monitor.pid'

        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self.load_config()

        # Initialize database
        self.init_database()

    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            "default_interval": "15m",
            "default_threshold": "10Mbps",
            "database_path": str(self.db_path),
            "alert_email": None,
            "preferred_servers": ["closest"],
            "log_level": "INFO"
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except (json.JSONDecodeError, IOError):
                pass

        # Create default config file
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=4)

        return default_config

    def init_database(self):
        """Initialize SQLite database for storing speed test results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS speed_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                download_speed REAL,
                upload_speed REAL,
                ping REAL,
                server_name TEXT,
                server_location TEXT,
                isp TEXT,
                alert_triggered BOOLEAN DEFAULT FALSE
            )
        ''')

        conn.commit()
        conn.close()

    def parse_interval(self, interval_str):
        """Parse interval string like '30m', '1h', '5s' to seconds"""
        if not interval_str:
            return 900  # Default 15 minutes

        unit = interval_str[-1].lower()
        try:
            value = int(interval_str[:-1])
        except ValueError:
            return 900

        multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }

        return value * multipliers.get(unit, 60)  # Default to minutes

    def parse_speed(self, speed_str):
        """Parse speed string like '50Mbps', '1Gbps' to Mbps"""
        if not speed_str:
            return 10.0  # Default threshold

        speed_str = speed_str.lower().replace(' ', '')

        if speed_str.endswith('gbps'):
            return float(speed_str[:-4]) * 1000
        elif speed_str.endswith('mbps'):
            return float(speed_str[:-4])
        elif speed_str.endswith('kbps'):
            return float(speed_str[:-4]) / 1000
        else:
            # Assume Mbps if no unit
            try:
                return float(speed_str)
            except ValueError:
                return 10.0

    def run_speedtest(self):
        """Run speedtest and return results"""
        try:
            # Check if speedtest-cli is installed
            result = subprocess.run(['speedtest-cli', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise FileNotFoundError("speedtest-cli not found")

            # Run speed test with JSON output
            result = subprocess.run([
                'speedtest-cli',
                '--json',
                '--timeout', '60'
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, 'speedtest-cli')

            data = json.loads(result.stdout)

            return {
                'download_speed': round(data['download'] / 1_000_000, 2),  # Convert to Mbps
                'upload_speed': round(data['upload'] / 1_000_000, 2),      # Convert to Mbps
                'ping': round(data['ping'], 2),
                'server_name': data['server']['name'],
                'server_location': f"{data['server']['country']}, {data['server']['name']}",
                'isp': data['client']['isp'],
                'timestamp': datetime.now()
            }

        except FileNotFoundError:
            click.echo(f"{Fore.RED}ERROR: speedtest-cli is not installed. Please install it first:{Style.RESET_ALL}")
            click.echo("pip install speedtest-cli")
            return None
        except subprocess.TimeoutExpired:
            click.echo(f"{Fore.YELLOW}WARNING: Speed test timed out{Style.RESET_ALL}")
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            click.echo(f"{Fore.RED}ERROR: Speed test failed: {e}{Style.RESET_ALL}")
            return None

    def save_result(self, result, alert_triggered=False):
        """Save speed test result to database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO speed_tests
            (timestamp, download_speed, upload_speed, ping, server_name, server_location, isp, alert_triggered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['timestamp'].isoformat(),  # <-- Convert to ISO 8601 string to avoid errors in python 3.12+
            result['download_speed'],
            result['upload_speed'],
            result['ping'],
            result['server_name'],
            result['server_location'],
            result['isp'],
            alert_triggered
        ))

        conn.commit()
        conn.close()

    def check_alert(self, result, threshold):
        """Check if speed is below threshold and trigger alert"""
        if result['download_speed'] < threshold:
            self.trigger_alert(result, threshold)
            return True
        return False

    def trigger_alert(self, result, threshold):
        """Trigger alert for low speed"""
        message = (f"SPEED ALERT: Download speed ({result['download_speed']} Mbps) "
                  f"is below threshold ({threshold} Mbps)")

        click.echo(f"{Fore.RED}{message}{Style.RESET_ALL}")

        # Log to file
        log_file = self.data_dir / 'alerts.log'
        with open(log_file, 'a') as f:
            f.write(f"{result['timestamp']}: {message}\n")

        # TODO: Add email notification if configured
        if self.config.get('alert_email'):
            # Email notification would be implemented here
            pass

    def is_monitoring(self):
        """Check if monitoring is currently running"""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is still running
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            # Process not running, clean up pid file
            self.pid_file.unlink(missing_ok=True)
            return False

    def start_monitoring(self, interval, threshold):
        """Start continuous monitoring"""
        if self.is_monitoring():
            click.echo(f"{Fore.YELLOW}WARNING: Monitoring is already running{Style.RESET_ALL}")
            return

        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

        click.echo(f"{Fore.GREEN}Starting speed monitoring...{Style.RESET_ALL}")
        click.echo(f"Interval: {interval}s ({interval//60}m)")
        click.echo(f"Alert threshold: {threshold} Mbps")
        click.echo(f"Database: {self.db_path}")
        click.echo(f"{Fore.CYAN}Press Ctrl+C to stop{Style.RESET_ALL}")

        def signal_handler(signum, frame):
            click.echo(f"\n{Fore.YELLOW}Stopping monitoring...{Style.RESET_ALL}")
            self.pid_file.unlink(missing_ok=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while True:
                click.echo(f"\n{Fore.BLUE}Running speed test...{Style.RESET_ALL}")
                result = self.run_speedtest()

                if result:
                    alert_triggered = self.check_alert(result, threshold)
                    self.save_result(result, alert_triggered)

                    # Display result in a nice table format
                    status_icon = "ALERT" if alert_triggered else "OK"
                    status_color = Fore.RED if alert_triggered else Fore.GREEN
                    
                    result_table = [
                        ["Download Speed", f"{result['download_speed']} Mbps"],
                        ["Upload Speed", f"{result['upload_speed']} Mbps"],
                        ["Ping", f"{result['ping']} ms"],
                        ["Server", result['server_location']],
                        ["Status", f"{status_color}{status_icon}{Style.RESET_ALL}"],
                        ["Timestamp", result['timestamp'].strftime('%H:%M:%S')]
                    ]
                    
                    click.echo(f"\n{Fore.CYAN}Speed Test Result:{Style.RESET_ALL}")
                    click.echo(tabulate(result_table, headers=["Metric", "Value"], tablefmt="grid"))

                click.echo(f"Next test in {interval//60} minutes...")
                time.sleep(interval)

        except KeyboardInterrupt:
            click.echo(f"\n{Fore.YELLOW}Monitoring stopped{Style.RESET_ALL}")
        finally:
            self.pid_file.unlink(missing_ok=True)

# Initialize the monitor instance
monitor = SpeedMonitor()

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Network Speed Monitor - Track internet speed over time with alerts"""
    pass

@cli.command()
@click.option('--interval', default='15m', help='Monitoring interval (e.g., 30m, 1h, 5s)')
@click.option('--alert-threshold', default='10Mbps', help='Alert threshold (e.g., 50Mbps, 1Gbps)')
@click.option('--email', help='Email address for alerts')
def start(interval, alert_threshold, email):
    """Start continuous speed monitoring"""
    interval_seconds = monitor.parse_interval(interval)
    threshold_mbps = monitor.parse_speed(alert_threshold)

    if email:
        monitor.config['alert_email'] = email
        with open(monitor.config_file, 'w') as f:
            json.dump(monitor.config, f, indent=4)

    monitor.start_monitoring(interval_seconds, threshold_mbps)

@cli.command()
def stop():
    """Stop speed monitoring"""
    if not monitor.is_monitoring():
        click.echo(f"{Fore.YELLOW}WARNING: No monitoring process is running{Style.RESET_ALL}")
        return

    try:
        with open(monitor.pid_file, 'r') as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        monitor.pid_file.unlink(missing_ok=True)
        click.echo(f"{Fore.GREEN}Monitoring stopped{Style.RESET_ALL}")
    except (OSError, ValueError):
        click.echo(f"{Fore.RED}Failed to stop monitoring{Style.RESET_ALL}")

@cli.command()
def status():
    """Show monitoring status"""
    if monitor.is_monitoring():
        click.echo(f"{Fore.GREEN}Monitoring is running{Style.RESET_ALL}")

        # Show last result
        conn = sqlite3.connect(monitor.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, download_speed, upload_speed, ping, server_location
            FROM speed_tests
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()

        if result:
            status_table = [
                ["Last Test", result[0]],
                ["Download Speed", f"{result[1]} Mbps"],
                ["Upload Speed", f"{result[2]} Mbps"],
                ["Ping", f"{result[3]} ms"],
                ["Server", result[4]]
            ]
            click.echo(f"\n{Fore.CYAN}Last Speed Test:{Style.RESET_ALL}")
            click.echo(tabulate(status_table, headers=["Metric", "Value"], tablefmt="grid"))
    else:
        click.echo(f"{Fore.YELLOW}Monitoring is not running{Style.RESET_ALL}")

@cli.command()
@click.option('--servers', default='closest', help='Server selection (closest, fastest, or server name)')
@click.option('--quick', is_flag=True, help='Quick test without saving to database')
def test(servers, quick):
    """Run a single speed test"""
    click.echo(f"{Fore.BLUE}Running speed test...{Style.RESET_ALL}")

    result = monitor.run_speedtest()

    if result:
        if not quick:
            monitor.save_result(result)
            click.echo(f"{Fore.GREEN}Result saved to database{Style.RESET_ALL}")

        # Display results in a nice table
        table_data = [
            ["Download Speed", f"{result['download_speed']} Mbps"],
            ["Upload Speed", f"{result['upload_speed']} Mbps"],
            ["Ping", f"{result['ping']} ms"],
            ["Server", result['server_location']],
            ["ISP", result['isp']],
            ["Timestamp", result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')]
        ]

        click.echo(f"\n{Fore.CYAN}Speed Test Results:{Style.RESET_ALL}")
        click.echo(tabulate(table_data, headers=["Metric", "Value"], tablefmt="grid"))
    else:
        click.echo(f"{Fore.RED}Speed test failed{Style.RESET_ALL}")

@cli.command()
@click.option('--last-week', is_flag=True, help='Show last week data')
@click.option('--last-month', is_flag=True, help='Show last month data')
@click.option('--today', is_flag=True, help='Show today data')
@click.option('--stats', is_flag=True, help='Show statistics summary')
@click.option('--export', type=click.Choice(['csv', 'json', 'png']), help='Export format')
@click.option('--limit', default=50, help='Limit number of results')
def report(last_week, last_month, today, stats, export, limit):
    """Generate speed test reports"""
    conn = sqlite3.connect(monitor.db_path)
    cursor = conn.cursor()

    # Determine date filter
    where_clause = ""
    if today:
        where_clause = "WHERE DATE(timestamp) = DATE('now')"
    elif last_week:
        where_clause = "WHERE timestamp >= datetime('now', '-7 days')"
    elif last_month:
        where_clause = "WHERE timestamp >= datetime('now', '-30 days')"

    if stats:
        # Show statistics
        cursor.execute(f'''
            SELECT
                COUNT(*) as total_tests,
                AVG(download_speed) as avg_download,
                MIN(download_speed) as min_download,
                MAX(download_speed) as max_download,
                AVG(upload_speed) as avg_upload,
                AVG(ping) as avg_ping,
                COUNT(CASE WHEN alert_triggered = 1 THEN 1 END) as alerts
            FROM speed_tests
            {where_clause}
        ''')

        stats_data = cursor.fetchone()
        if stats_data and stats_data[0] > 0:
            stats_table = [
                ["Total Tests", stats_data[0]],
                ["Average Download", f"{stats_data[1]:.2f} Mbps"],
                ["Min Download", f"{stats_data[2]:.2f} Mbps"],
                ["Max Download", f"{stats_data[3]:.2f} Mbps"],
                ["Average Upload", f"{stats_data[4]:.2f} Mbps"],
                ["Average Ping", f"{stats_data[5]:.2f} ms"],
                ["Alerts Triggered", stats_data[6]]
            ]

            click.echo(f"{Fore.CYAN}Speed Test Statistics:{Style.RESET_ALL}")
            click.echo(tabulate(stats_table, headers=["Metric", "Value"], tablefmt="grid"))
        else:
            click.echo(f"{Fore.YELLOW}No data available for the selected period{Style.RESET_ALL}")

    else:
        # Show detailed results
        cursor.execute(f'''
            SELECT timestamp, download_speed, upload_speed, ping, server_location, alert_triggered
            FROM speed_tests
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        results = cursor.fetchall()

        if results:
            # Format data for table
            table_data = []
            for row in results:
                alert_icon = "ALERT" if row[5] else "OK"
                table_data.append([
                    row[0][:19],  # Timestamp (without microseconds)
                    f"{row[1]:.1f}",  # Download
                    f"{row[2]:.1f}",  # Upload
                    f"{row[3]:.1f}",  # Ping
                    row[4][:30],  # Server (truncated)
                    alert_icon
                ])

            headers = ["Timestamp", "Down (Mbps)", "Up (Mbps)", "Ping (ms)", "Server", "Status"]
            click.echo(f"{Fore.CYAN}Speed Test History:{Style.RESET_ALL}")
            click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

            # Export functionality
            if export:
                export_file = monitor.data_dir / f"speed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export}"

                if export == 'csv':
                    import csv
                    with open(export_file, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(headers[:-1] + ['Alert Triggered'])  # Replace icon with boolean
                        for i, row in enumerate(results):
                            writer.writerow([row[0], row[1], row[2], row[3], row[4], bool(row[5])])

                elif export == 'json':
                    export_data = []
                    for row in results:
                        export_data.append({
                            'timestamp': row[0],
                            'download_speed': row[1],
                            'upload_speed': row[2],
                            'ping': row[3],
                            'server_location': row[4],
                            'alert_triggered': bool(row[5])
                        })

                    with open(export_file, 'w') as jsonfile:
                        json.dump(export_data, jsonfile, indent=2)

                elif export == 'png':
                    try:
                        import matplotlib.pyplot as plt
                        import matplotlib.dates as mdates
                        from datetime import datetime as dt

                        # Parse timestamps and speeds
                        #timestamps = [dt.strptime(row[0], '%Y-%m-%d %H:%M:%S') for row in results]    # old line caused date-time errors in output when using Python 3.12+
                        timestamps = [dt.fromisoformat(row[0]) for row in results]    # edited to stop errors in Python 3.12+
                        download_speeds = [row[1] for row in results]
                        upload_speeds = [row[2] for row in results]
                        ping_rate = [row[3] for row in results]

                        # Reverse for chronological order
                        timestamps.reverse()
                        download_speeds.reverse()
                        upload_speeds.reverse()
                        ping_rate.reverse()

                        # Convert datetime objects to matplotlib date numbers
                        timestamps_num = mdates.date2num(timestamps)

                        # Create the plot
                        fig, ax = plt.subplots(figsize=(12, 6))
                        ax.plot(timestamps_num, download_speeds, label='Download', color='blue', linewidth=2)
                        ax.plot(timestamps_num, upload_speeds, label='Upload', color='red', linewidth=2)
                        ax.plot(timestamps_num, ping_rate, label='Latency (Ping)', color='green', linewidth=2)    # added ping worm to the chart
                        
                        ax.set_xlabel('Time')
                        ax.set_ylabel('Speed (Mbps)')
                        ax.set_title('Internet Speed Over Time')
                        ax.set_ylim(0,500)    #set speed scale limits for better and consistent chart display
                        ax_ping_rate = ax.twinx()    # added ping worm to the chart
                        ax_ping_rate.set_ylabel('Latency (Sec)')    # added ping worm to the chart
                        ax_ping_rate.set_ylim(0,1)    #set ping scale limits for better chart display
                        ax.legend()
                        ax.grid(True, alpha=0.3)

                        # Format x-axis
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                        ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(timestamps_num)//10)))
                        plt.xticks(rotation=45)

                        plt.tight_layout()
                        plt.savefig(export_file, dpi=300, bbox_inches='tight')
                        plt.close()

                    except ImportError:
                        click.echo(f"{Fore.RED}matplotlib is required for PNG export{Style.RESET_ALL}")
                        return

                click.echo(f"{Fore.GREEN}Report exported to: {export_file}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}No data available for the selected period{Style.RESET_ALL}")

    conn.close()

@cli.command()
@click.option('--limit', default=20, help='Number of recent results to show')
def history(limit):
    """Show recent speed test history"""
    conn = sqlite3.connect(monitor.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT timestamp, download_speed, upload_speed, ping, server_location, alert_triggered
        FROM speed_tests
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()
    conn.close()

    if results:
        table_data = []
        for row in results:
            alert_icon = "ALERT" if row[5] else "OK"
            table_data.append([
                row[0][:19],
                f"{row[1]:.1f}",
                f"{row[2]:.1f}",
                f"{row[3]:.1f}",
                row[4][:25],
                alert_icon
            ])

        headers = ["Timestamp", "Down (Mbps)", "Up (Mbps)", "Ping (ms)", "Server", "Status"]
        click.echo(f"{Fore.CYAN}Recent Speed Tests:{Style.RESET_ALL}")
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        click.echo(f"{Fore.YELLOW}No speed test data found{Style.RESET_ALL}")

@cli.command()
@click.option('--days', default=30, help='Remove data older than N days')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def cleanup(days, confirm):
    """Clean up old speed test data"""
    conn = sqlite3.connect(monitor.db_path)
    cursor = conn.cursor()

    # Count records to be deleted
    cursor.execute('''
        SELECT COUNT(*) FROM speed_tests
        WHERE timestamp < datetime('now', '-{} days')
    '''.format(days))

    count = cursor.fetchone()[0]

    if count == 0:
        click.echo(f"{Fore.GREEN}No data older than {days} days found{Style.RESET_ALL}")
        conn.close()
        return

    if not confirm:
        if not click.confirm(f"Delete {count} records older than {days} days?"):
            click.echo("Cleanup cancelled")
            conn.close()
            return

    # Delete old records
    cursor.execute('''
        DELETE FROM speed_tests
        WHERE timestamp < datetime('now', '-{} days')
    '''.format(days))

    conn.commit()
    conn.close()

    click.echo(f"{Fore.GREEN}Deleted {count} old records{Style.RESET_ALL}")

if __name__ == '__main__':
    cli()
