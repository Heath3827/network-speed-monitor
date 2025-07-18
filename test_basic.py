#!/usr/bin/env python3
"""
Basic test script for Network Speed Monitor
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"

def test_help():
    """Test help command"""
    print("Testing help command...")
    code, stdout, stderr = run_command("python3 speed_monitor.py --help")
    if code == 0 and "Network Speed Monitor" in stdout:
        print("✅ Help command works")
        return True
    else:
        print(f"❌ Help command failed: {stderr}")
        return False

def test_status():
    """Test status command"""
    print("Testing status command...")
    code, stdout, stderr = run_command("python3 speed_monitor.py status")
    if code == 0:
        print("✅ Status command works")
        print(f"Output: {stdout.strip()}")
        return True
    else:
        print(f"❌ Status command failed: {stderr}")
        return False

def test_config_creation():
    """Test if config and data directories are created"""
    print("Testing configuration setup...")
    
    # Run status to trigger config creation
    run_command("python3 speed_monitor.py status")
    
    config_dir = os.path.expanduser("~/.config/speed-monitor")
    data_dir = os.path.expanduser("~/.local/share/speed-monitor")
    config_file = os.path.join(config_dir, "config.json")
    
    if os.path.exists(config_dir) and os.path.exists(data_dir) and os.path.exists(config_file):
        print("✅ Configuration directories and files created")
        return True
    else:
        print("❌ Configuration setup failed")
        return False

def main():
    """Run basic tests"""
    print("🧪 Running basic tests for Network Speed Monitor\n")
    
    tests = [
        test_help,
        test_status,
        test_config_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("\nYou can now try:")
        print("  python3 speed_monitor.py test --quick")
        print("  python3 speed_monitor.py start --interval 5m --alert-threshold 50Mbps")
    else:
        print("❌ Some tests failed. Please check the setup.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())