#!/usr/bin/env python3
"""
Demo script for Network Speed Monitor
"""

import sys
import os

# Add current directory to path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_functionality():
    """Demonstrate the speed monitor functionality"""
    print("🌐 Network Speed Monitor Demo")
    print("=" * 40)
    
    try:
        # Import our speed monitor
        from speed_monitor_complete import SpeedMonitor, cli
        
        print("✅ Speed Monitor module loaded successfully!")
        print()
        
        # Create monitor instance
        monitor = SpeedMonitor()
        print("✅ Monitor instance created")
        print(f"📁 Config directory: {monitor.config_dir}")
        print(f"📁 Data directory: {monitor.data_dir}")
        print(f"🗄️ Database path: {monitor.db_path}")
        print()
        
        # Test configuration
        print("⚙️ Configuration:")
        for key, value in monitor.config.items():
            print(f"  {key}: {value}")
        print()
        
        # Test parsing functions
        print("🧪 Testing utility functions:")
        
        # Test interval parsing
        intervals = ['30m', '1h', '5s', '2d']
        for interval in intervals:
            seconds = monitor.parse_interval(interval)
            print(f"  {interval} = {seconds} seconds")
        
        print()
        
        # Test speed parsing
        speeds = ['50Mbps', '1Gbps', '500Kbps', '100']
        for speed in speeds:
            mbps = monitor.parse_speed(speed)
            print(f"  {speed} = {mbps} Mbps")
        
        print()
        print("🎉 All basic functionality working!")
        print()
        print("📋 Available Commands:")
        print("  python3 speed_monitor_complete.py --help")
        print("  python3 speed_monitor_complete.py status")
        print("  python3 speed_monitor_complete.py test --quick")
        print("  python3 speed_monitor_complete.py start --interval 30m --alert-threshold 50Mbps")
        print("  python3 speed_monitor_complete.py report --stats")
        print("  python3 speed_monitor_complete.py history --limit 10")
        print()
        print("⚠️  Note: For actual speed tests, you need 'speedtest-cli' installed:")
        print("  pip install speedtest-cli")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_functionality()