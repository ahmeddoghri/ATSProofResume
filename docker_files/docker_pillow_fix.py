"""
Quick fix script to install Pillow in the Docker container.
"""
import os
import sys
import subprocess

def fix_pillow_dependency():
    """Install Pillow package if missing."""
    try:
        # Try importing PIL to check if it's installed
        import PIL
        print("PIL is already installed.")
        return True
    except ImportError:
        print("PIL not found. Installing Pillow...")
        try:
            # Install Pillow
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            print("Pillow installed successfully.")
            
            # Verify installation
            try:
                import PIL
                print(f"PIL version {PIL.__version__} is now installed.")
                return True
            except ImportError:
                print("Failed to import PIL after installation.")
                return False
        except Exception as e:
            print(f"Error installing Pillow: {e}")
            return False

if __name__ == "__main__":
    success = fix_pillow_dependency()
    sys.exit(0 if success else 1) 