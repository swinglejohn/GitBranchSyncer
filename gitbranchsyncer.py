#!/usr/bin/env python3
import sys
import git
from pathlib import Path

def get_repo():
    """Get git repository from current directory."""
    try:
        return git.Repo(Path.cwd(), search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        print("Error: Not in a git repository")
        sys.exit(1)

def sync_branch(branch_name=None):
    """
    Sync the specified branch (or current branch if none specified) with remote.
    """
    repo = get_repo()
    
    # Get current branch if none specified
    if not branch_name:
        branch_name = repo.active_branch.name
    
    try:
        # Fetch latest changes
        print(f"Fetching latest changes from remote...")
        repo.remotes.origin.fetch()
        
        # Get the branch
        branch = repo.heads[branch_name]
        
        # Get tracking branch
        tracking_branch = branch.tracking_branch()
        if not tracking_branch:
            print(f"Error: Branch '{branch_name}' is not tracking a remote branch")
            sys.exit(1)
        
        # Check if we need to pull
        commits_behind = list(repo.iter_commits(f'{branch_name}..{tracking_branch.name}'))
        if not commits_behind:
            print("Already up to date!")
            return
        
        # Pull changes
        print(f"Found {len(commits_behind)} new commit(s). Pulling changes...")
        repo.remotes.origin.pull()
        print("Successfully synced with remote!")
        
    except git.GitCommandError as e:
        print(f"Git error occurred: {e}")
        sys.exit(1)
    except KeyError:
        print(f"Error: Branch '{branch_name}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def main():
    """Main entry point for the script."""
    # Get branch name from command line args if provided
    branch_name = sys.argv[1] if len(sys.argv) > 1 else None
    sync_branch(branch_name)

if __name__ == "__main__":
    main()
