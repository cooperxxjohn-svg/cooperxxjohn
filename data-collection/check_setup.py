"""
Setup Checker
Verifies environment is ready for data collection
Run: python check_setup.py
"""

import sys
import subprocess

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} (need 3.7+)")
        return False

def check_package(package_name, import_name=None):
    """Check if package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} (not installed)")
        return False

def check_chrome():
    """Check if Chrome/Chromium is installed"""
    try:
        result = subprocess.run(
            ["google-chrome", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Google Chrome ({version})")
            return True
    except:
        pass

    # Try chromium
    try:
        result = subprocess.run(
            ["chromium-browser", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Chromium ({version})")
            return True
    except:
        pass

    print("❌ Chrome/Chromium (not found)")
    print("   Install: sudo apt-get install chromium-browser")
    return False

def main():
    print("\n" + "="*70)
    print("DATA COLLECTION SETUP CHECKER")
    print("="*70 + "\n")

    all_good = True

    # Check Python
    print("1. Python Version:")
    all_good &= check_python_version()

    # Check packages
    print("\n2. Required Packages:")
    all_good &= check_package("selenium")
    all_good &= check_package("requests")
    all_good &= check_package("PIL", "PIL")
    all_good &= check_package("imagehash")
    all_good &= check_package("webdriver_manager", "webdriver_manager")

    # Check Chrome
    print("\n3. Chrome Browser:")
    all_good &= check_chrome()

    # Summary
    print("\n" + "="*70)
    if all_good:
        print("✅ ALL CHECKS PASSED - Ready to collect data!")
        print("\nRun: python collect_all.py")
    else:
        print("❌ SOME CHECKS FAILED - Install missing dependencies")
        print("\nFix:")
        print("  pip install -r requirements.txt")
        print("  sudo apt-get install chromium-browser  # Linux")
        print("  brew install --cask google-chrome       # macOS")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
