#!/usr/bin/env python3
import sys
import git
import time
import signal
from pathlib import Path
from datetime import datetime

# Global flag for graceful shutdown
running = True

def get_repo():
    """Get git repository from current directory."""
    try:
        return git.Repo(Path.cwd(), search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        print("Error: Not in a git repository")
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle Ctrl+C to gracefully shutdown."""
    global running
    print("\nShutting down Git Branch Syncer...")
    running = False

def check_and_sync_branch(repo, branch_name):
    """
    Check for and sync new commits for the specified branch.
    Returns True if changes were pulled, False otherwise.
    """
    try:
        # Fetch latest changes
        repo.remotes.origin.fetch()
        
        # Get the branch
        branch = repo.heads[branch_name]
        
        # Get tracking branch
        tracking_branch = branch.tracking_branch()
        if not tracking_branch:
            print(f"Error: Branch '{branch_name}' is not tracking a remote branch")
            return False
        
        # Check if we need to pull
        commits_behind = list(repo.iter_commits(f'{branch_name}..{tracking_branch.name}'))
        if not commits_behind:
            return False
        
        # Pull changes
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] Found {len(commits_behind)} new commit(s). Pulling changes...")
        repo.remotes.origin.pull()
        print(f"[{timestamp}] Successfully synced with remote!")
        return True
        
    except git.GitCommandError as e:
        print(f"\nGit error occurred: {e}")
        return False
    except KeyError:
        print(f"\nError: Branch '{branch_name}' not found")
        return False
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return False

def monitor_branch(branch_name=None):
    """
    Continuously monitor the specified branch (or current branch if none specified)
    for new commits and pull them automatically.
    """
    repo = get_repo()
    
    # Get current branch if none specified
    if not branch_name:
        branch_name = repo.active_branch.name
    
    print(f"Starting Git Branch Syncer for branch: {branch_name}")
    print("Monitoring for new commits (Press Ctrl+C to stop)...")
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    check_interval = 5  # seconds between checks
    
    while running:
        check_and_sync_branch(repo, branch_name)
        # Sleep in small intervals to allow for quicker shutdown response
        for _ in range(check_interval):
            if not running:
                break
            time.sleep(1)

def main():
    """Main entry point for the script."""
    # Get branch name from command line args if provided
    branch_name = sys.argv[1] if len(sys.argv) > 1 else None
    monitor_branch(branch_name)

if __name__ == "__main__":
    main()
