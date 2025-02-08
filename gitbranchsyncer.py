#!/usr/bin/env python3
import sys
import os
import git
import time
import signal
import atexit
import logging
import glob
from pathlib import Path
from datetime import datetime

class GitBranchSyncer:
    def __init__(self, repo_path=None, branch_name=None):
        self.repo_path = repo_path or Path.cwd()
        self.branch_name = branch_name
        self.running = True
        self.log_file = None
        
        # Set up logging
        self.setup_logging()
        
        # Get repository
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
            self.repo_path = Path(self.repo.working_dir)
        except git.InvalidGitRepositoryError:
            self.logger.error("Error: Not in a git repository")
            sys.exit(1)
            
        # Get branch name if not specified
        if not self.branch_name:
            self.branch_name = self.repo.active_branch.name
            
        # Set branch name in environment for process tracking
        os.environ['BRANCH_NAME'] = self.branch_name
        
    def setup_logging(self):
        """Set up logging configuration."""
        log_dir = Path.home() / ".gitbranchsyncer" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / "gitbranchsyncer.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('GitBranchSyncer')
        
    def daemonize(self):
        """Daemonize the process."""
        # First fork (detaches from parent)
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process exits
                sys.exit(0)
        except OSError as err:
            self.logger.error(f'Fork #1 failed: {err}')
            sys.exit(1)
            
        # Decouple from parent environment
        os.chdir(str(self.repo_path))  # Stay in repo directory
        os.umask(0)
        os.setsid()
        
        # Second fork (relinquish session leadership)
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process exits
                sys.exit(0)
        except OSError as err:
            self.logger.error(f'Fork #2 failed: {err}')
            sys.exit(1)
            
        # Flush standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        pid = os.getpid()
        self.logger.info(f"Daemon started with PID {pid}")
        self.logger.info(f"Logs available at: {self.log_file}")
        print(f"Git Branch Syncer daemon started for branch: {self.branch_name}")
        print(f"PID: {pid}")
        print(f"Logs: {self.log_file}")
            
    def check_and_sync_branch(self):
        """Check for and sync new commits for the branch."""
        try:
            # Fetch latest changes
            self.repo.remotes.origin.fetch()
            
            # Get the branch
            branch = self.repo.heads[self.branch_name]
            
            # Get tracking branch
            tracking_branch = branch.tracking_branch()
            if not tracking_branch:
                self.logger.error(f"Branch '{self.branch_name}' is not tracking a remote branch")
                self.running = False
                return False
            
            # Check if we need to pull
            commits_behind = list(self.repo.iter_commits(f'{self.branch_name}..{tracking_branch.name}'))
            if not commits_behind:
                return False
            
            # Pull changes
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.logger.info(f"Found {len(commits_behind)} new commit(s). Pulling changes...")
            self.repo.git.pull('--ff-only')  # Only fast-forward pulls to avoid conflicts
            self.logger.info("Successfully synced with remote!")
            return True
            
        except git.GitCommandError as e:
            self.logger.error(f"Git error occurred: {e}")
            self.logger.info("Shutting down daemon due to git error")
            self.running = False
            return False
        except KeyError:
            self.logger.error(f"Error: Branch '{self.branch_name}' not found")
            self.logger.info("Shutting down daemon due to missing branch")
            self.running = False
            return False
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            self.logger.info("Shutting down daemon due to error")
            self.running = False
            return False
            
    def signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        self.running = False
        self.logger.info("Shutting down Git Branch Syncer...")
        
    def run(self):
        """Main loop to monitor branch."""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.logger.info(f"Starting Git Branch Syncer for branch: {self.branch_name}")
        
        check_interval = 5  # seconds between checks
        
        while self.running:
            self.check_and_sync_branch()
            if not self.running:  # Check if we should exit due to error
                break
            time.sleep(check_interval)

def get_running_daemons():
    """Get list of all running daemons using pgrep."""
    running_daemons = []
    
    try:
        # Run pgrep to find all git-branch-syncer processes
        import subprocess
        result = subprocess.run(['pgrep', '-fl', 'git-branch-sync'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0 and result.returncode != 1:  # 1 means no processes found
            return running_daemons
            
        # Parse each process
        for line in result.stdout.splitlines():
            try:
                # Split line into PID and command
                pid, *cmd_parts = line.strip().split()
                pid = int(pid)
                
                # Read process environment
                try:
                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        env = f.read().decode('utf-8', errors='ignore')
                except (FileNotFoundError, PermissionError):
                    # Process might have died or we don't have permission
                    continue
                
                # Find PWD in environment
                repo_path = None
                branch_name = None
                for var in env.split('\0'):
                    if var.startswith('PWD='):
                        repo_path = Path(var[4:])
                    elif var.startswith('BRANCH_NAME='):
                        branch_name = var[12:]
                
                if not branch_name:
                    # Try to get branch name from git if not in environment
                    try:
                        repo = git.Repo(repo_path, search_parent_directories=True)
                        branch_name = repo.active_branch.name
                    except (git.InvalidGitRepositoryError, AttributeError):
                        branch_name = "unknown"
                
                if repo_path:
                    running_daemons.append((repo_path, branch_name, pid))
                else:
                    # Include PID even if we couldn't get the repo path
                    running_daemons.append((Path("unknown"), "unknown", pid))
                    
            except (ValueError, IndexError):
                continue
                
    except FileNotFoundError:
        # pgrep not available
        print("Warning: pgrep command not found")
        
    return running_daemons

def check_daemon_running(repo_path, branch_name):
    """Check if a daemon is already running for the given branch."""
    daemons = get_running_daemons()
    repo_path = Path(repo_path).resolve()
    
    for daemon_repo, daemon_branch, _ in daemons:
        if daemon_repo == repo_path and daemon_branch == branch_name:
            return True
    return False

def stop_daemon(pid):
    """Stop a daemon process by PID."""
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        return False

def stop_all_daemons():
    """Stop all running daemons."""
    daemons = get_running_daemons()
    if not daemons:
        print("No Git Branch Syncer daemons are running")
        return
        
    for repo_path, branch_name, pid in daemons:
        repo_name = repo_path.name if repo_path != Path("unknown") else "unknown"
        if stop_daemon(pid):
            print(f"Stopped daemon for '{repo_name}/{branch_name}' (PID: {pid})")

def list_daemons():
    """List all running daemons."""
    daemons = get_running_daemons()
    if daemons:
        print("Running Git Branch Syncer daemons:")
        current_repo = None
        for repo_path, branch_name, pid in sorted(daemons, key=lambda x: (x[0], x[1])):
            if repo_path != current_repo:
                repo_name = repo_path.name if repo_path != Path("unknown") else "unknown"
                print(f"\n{repo_name}:")
                current_repo = repo_path
            print(f"  - Branch '{branch_name}' (PID: {pid})")
    else:
        print("No Git Branch Syncer daemons are running")

def main():
    """Main entry point for the script."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "stop":
            if len(sys.argv) > 2 and sys.argv[2] == "all":
                # Stop all daemons
                stop_all_daemons()
            else:
                try:
                    # Stop specific branch daemon
                    repo = git.Repo(Path.cwd(), search_parent_directories=True)
                    repo_path = Path(repo.working_dir).resolve()
                    branch_name = sys.argv[2] if len(sys.argv) > 2 else repo.active_branch.name
                    
                    # Find matching daemon
                    daemons = get_running_daemons()
                    found = False
                    for daemon_repo, daemon_branch, pid in daemons:
                        if daemon_repo == repo_path and daemon_branch == branch_name:
                            if stop_daemon(pid):
                                print(f"Stopped daemon for '{repo_path.name}/{branch_name}' (PID: {pid})")
                                found = True
                                break
                    
                    if not found:
                        print(f"No daemon is running for branch '{branch_name}'")
                        # Show running daemons
                        if daemons:
                            print("\nOther running daemons:")
                            current_repo = None
                            for other_repo, other_branch, pid in sorted(daemons, key=lambda x: (x[0], x[1])):
                                if other_repo != current_repo:
                                    repo_name = other_repo.name if other_repo != Path("unknown") else "unknown"
                                    print(f"\n{repo_name}:")
                                    current_repo = other_repo
                                print(f"  - Branch '{other_branch}' (PID: {pid})")
                            print("\nTo stop all daemons, use: git-branch-syncer stop all")
                except git.InvalidGitRepositoryError:
                    print("Error: Not in a git repository")
                    sys.exit(1)
        elif command == "list":
            # List all running daemons
            list_daemons()
        else:
            # Start daemon for specific branch
            try:
                repo = git.Repo(Path.cwd(), search_parent_directories=True)
                repo_path = Path(repo.working_dir)
                branch_name = command if command != "start" else repo.active_branch.name
                
                # Check if daemon is already running
                if check_daemon_running(repo_path, branch_name):
                    print(f"Error: A daemon is already running for branch '{branch_name}'")
                    sys.exit(1)
                
                syncer = GitBranchSyncer(branch_name=branch_name)
                syncer.daemonize()
                syncer.run()
            except git.InvalidGitRepositoryError:
                print("Error: Not in a git repository")
                sys.exit(1)
    else:
        # Start daemon for current branch
        try:
            repo = git.Repo(Path.cwd(), search_parent_directories=True)
            repo_path = Path(repo.working_dir)
            branch_name = repo.active_branch.name
            
            # Check if daemon is already running
            if check_daemon_running(repo_path, branch_name):
                print(f"Error: A daemon is already running for branch '{branch_name}'")
                sys.exit(1)
            
            syncer = GitBranchSyncer()
            syncer.daemonize()
            syncer.run()
        except git.InvalidGitRepositoryError:
            print("Error: Not in a git repository")
            sys.exit(1)

if __name__ == "__main__":
    main()
