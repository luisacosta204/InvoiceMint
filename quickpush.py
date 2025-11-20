#!/usr/bin/env python3
"""
quickpush.py — one-command: status → add → commit → push

Usage:
  python quickpush.py "Your commit message"
  # macOS/Linux (after chmod +x):
  ./quickpush.py "Your commit message"

If you omit the message, it defaults to "Quick update".
Works on Windows and macOS/Linux.
"""
import sys, subprocess, shlex

def run(cmd, check=True):
    # Accept string or list; print the command for visibility
    if isinstance(cmd, str):
        print(f"$ {cmd}")
        result = subprocess.run(cmd, shell=True, text=True)
    else:
        print(f"$ {' '.join(shlex.quote(x) for x in cmd)}")
        result = subprocess.run(cmd, text=True)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

def has_git():
    try:
        run(["git", "--version"])
        return True
    except Exception:
        return False

def inside_repo():
    try:
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip() == "true"
    except Exception:
        return False

def upstream_set():
    try:
        subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                       capture_output=True, text=True, check=True)
        return True
    except Exception:
        return False

def current_branch():
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "main"

def main():
    if not has_git():
        print("Error: git not found in PATH.")
        sys.exit(1)
    if not inside_repo():
        print("Error: not inside a Git repository (no .git directory here).")
        sys.exit(1)

    message = " ".join(sys.argv[1:]).strip() or "Quick update"

    # Show status
    run(["git", "status"], check=False)

    # Add all changes
    run(["git", "add", "-A"])

    # Commit (if there are staged changes)
    # If nothing to commit, continue to push.
    try:
        run(["git", "commit", "-m", message])
    except subprocess.CalledProcessError:
        print("Nothing to commit (working tree clean). Continuing to push...")

    # Push (set upstream automatically if missing)
    branch = current_branch()
    if upstream_set():
        run(["git", "push"])
    else:
        print(f"No upstream set for '{branch}'. Setting upstream to origin/{branch}...")
        run(["git", "push", "-u", "origin", branch])

    print("\n✅ Done! Changes pushed successfully.")

if __name__ == "__main__":
    main()
