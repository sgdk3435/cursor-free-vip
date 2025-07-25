import warnings
import os
import platform
import subprocess
import time
import threading
import shutil
from logo import print_logo
from dotenv import load_dotenv

# Ignore specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

class LoadingAnimation:
    def __init__(self):
        self.is_running = False
        self.animation_thread = None

    def start(self, message="Building"):
        self.is_running = True
        self.animation_thread = threading.Thread(target=self._animate, args=(message,))
        self.animation_thread.start()

    def stop(self):
        self.is_running = False
        if self.animation_thread:
            self.animation_thread.join()
        print("\r" + " " * 70 + "\r", end="", flush=True)

    def _animate(self, message):
        animation = "|/-\\"
        idx = 0
        while self.is_running:
            print(f"\r{message} {animation[idx % len(animation)]}", end="", flush=True)
            idx += 1
            time.sleep(0.1)

def progress_bar(progress, total, prefix="", length=50):
    filled = int(length * progress // total)
    bar = "█" * filled + "░" * (length - filled)
    percent = f"{100 * progress / total:.1f}"
    print(f"\r{prefix} |{bar}| {percent}% Complete", end="", flush=True)
    if progress == total:
        print()

def simulate_progress(message, duration=1.0, steps=20):
    print(f"\033[94m{message}\033[0m")
    for i in range(steps + 1):
        time.sleep(duration / steps)
        progress_bar(i, steps, prefix="Progress:", length=40)

def build():
    # Clean screen
    os.system("cls" if platform.system().lower() == "windows" else "clear")
    
    # Display logo
    print_logo()    # Clean PyInstaller cache and dist directory
    print("\033[93m🧹 Cleaning build cache and dist directory...\033[0m")
    
    def safe_remove_tree(path):
        """Safely remove directory tree with retry logic"""
        if not os.path.exists(path):
            return True
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                shutil.rmtree(path)
                return True
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"\033[93m⚠️ Permission error removing {path}, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})\033[0m")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"\033[91m❌ Failed to remove {path}: {str(e)}\033[0m")
                    print(f"\033[93m💡 Tip: Please close any running executables from the dist folder and try again.\033[0m")
                    return False
            except Exception as e:
                print(f"\033[91m❌ Error removing {path}: {str(e)}\033[0m")
                return False
        
        return False
    
    # Clean build directory
    if not safe_remove_tree('build'):
        return False
    
    # Clean dist directory
    if not safe_remove_tree('dist'):
        return False
    
    # Reload environment variables to ensure getting the latest version
    load_dotenv(override=True)
    version = os.getenv('VERSION', '1.0.0')
    print(f"\033[93m📦 Building version: v{version}\033[0m")

    try:
        simulate_progress("Preparing build environment...", 0.5)
        
        loading = LoadingAnimation()
        loading.start("Building in progress")
        
        # Set output name based on system type
        system = platform.system().lower()
        if system == "windows":
            os_type = "windows"
            ext = ".exe"
        elif system == "linux":
            os_type = "linux"
            ext = ""
        else:  # Darwin
            os_type = "mac"
            ext = ""
            
        output_name = f"CursorFreeVIP_{version}_{os_type}"
        
        # Build command
        build_command = f'pyinstaller --clean --noconfirm build.spec'
        output_path = os.path.join('dist', f'{output_name}{ext}')
        
        os.system(build_command)
        
        loading.stop()

        if os.path.exists(output_path):
            print(f"\n\033[92m✅ Build completed!")
            print(f"📦 Executable file located: {output_path}\033[0m")
        else:
            print("\n\033[91m❌ Build failed: Output file not found\033[0m")
            return False

    except Exception as e:
        if loading:
            loading.stop()
        print(f"\n\033[91m❌ Build process error: {str(e)}\033[0m")
        return False

    return True

if __name__ == "__main__":
    build() 