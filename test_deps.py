"""
Simple test script to verify that all required packages are installed.
"""
import subprocess
import sys

def test_dependencies():
    """Test that all required packages are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "jinja2",
        "python-multipart",
        "openai",
        "langchain",
        "langchain-openai",
        "python-docx",
        "markdown",
        "requests",
        "beautifulsoup4",
        "selenium",
        "webdriver-manager",
        "python-dotenv",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Use pip to check if package is installed
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {package} is installed")
            else:
                missing_packages.append(package)
                print(f"❌ {package} is NOT installed")
        except Exception as e:
            print(f"Error checking {package}: {e}")
    
    if missing_packages:
        print("\n❌ The following packages are missing:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n✅ All required packages are installed!")
        return True

if __name__ == "__main__":
    success = test_dependencies()
    sys.exit(0 if success else 1) 