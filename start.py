import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")


def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, shell=True)


print("==> Installing backend dependencies...")
run(f'"{sys.executable}" -m pip install -r requirements.txt -q', BACKEND)

print("==> Installing frontend dependencies...")
run("npm install --silent", FRONTEND)

# Clean up Next.js cache to prevent Windows EINVAL errors
next_cache = os.path.join(FRONTEND, ".next")
if os.path.exists(next_cache):
    print("==> Cleaning up frontend cache...")
    try:
        import shutil
        def on_error(func, path, exc_info):
            import stat
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
            func(path)
        shutil.rmtree(next_cache, onerror=on_error)
        print("    [Done] Cache cleared.")
    except:
        print("    [Note] Could not fully clean .next folder, continuing...")

print("==> Starting backend on http://localhost:8000 ...")
backend_proc = subprocess.Popen(
    "uvicorn main:app --reload --port 8000",
    cwd=BACKEND, shell=True,
)

print("==> Starting frontend on http://localhost:3000 ...")
frontend_proc = subprocess.Popen(
    "npm run dev",
    cwd=FRONTEND, shell=True,
)

print("\n  BuyWise is running!")
print("  Frontend : http://localhost:3000")
print("  Backend  : http://localhost:8000")
print("  Press Ctrl+C to stop both servers.\n")

try:
    backend_proc.wait()
    frontend_proc.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    backend_proc.terminate()
    frontend_proc.terminate()
