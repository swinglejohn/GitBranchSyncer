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
        self.pid_file = None
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
            
        # Set up PID file path
        self.pid_file = self.repo_path / ".git" / f"branch-syncer-{self.branch_name}.pid"
        
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
        os.chdir('/')
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
        
        # Write pidfile
        pid = str(os.getpid())
        self.pid_file.write_text(pid)
        
        # Register cleanup function
        atexit.register(self.cleanup)
        
        self.logger.info(f"Daemon started with PID {pid}")
        self.logger.info(f"Logs available at: {self.log_file}")
        print(f"Git Branch Syncer daemon started for branch: {self.branch_name}")
        print(f"PID: {pid}")
        print(f"Logs: {self.log_file}")
        
    def cleanup(self):
        """Cleanup function to remove PID file."""
        if self.pid_file and self.pid_file.exists():
            self.pid_file.unlink()
            
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

def get_running_daemons(repo_path):
    """Get list of branches with running daemons."""
    git_dir = Path(repo_path) / ".git"
    running_daemons = []
    
    # Find all PID files
    for pid_file in git_dir.glob("branch-syncer-*.pid"):
        branch_name = pid_file.name.replace("branch-syncer-", "").replace(".pid", "")
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process is running
            os.kill(pid, 0)  # This will raise an error if process is not running
            running_daemons.append((branch_name, pid))
        except (ProcessLookupError, ValueError, FileNotFoundError):
            # Clean up stale PID file
            try:
                pid_file.unlink()
            except FileNotFoundError:
                pass
            
    return running_daemons

def stop_daemon(pid_file, branch_name):
    """Stop the daemon process."""
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped Git Branch Syncer daemon for branch '{branch_name}' (PID: {pid})")
    except FileNotFoundError:
        return False
    except ProcessLookupError:
        if os.path.exists(pid_file):
            os.unlink(pid_file)
        return False
    return True

def stop_all_daemons(repo_path):
    """Stop all running daemons."""
    daemons = get_running_daemons(repo_path)
    if not daemons:
        print("No Git Branch Syncer daemons are running")
        return
        
    for branch_name, _ in daemons:
        pid_file = Path(repo_path) / ".git" / f"branch-syncer-{branch_name}.pid"
        stop_daemon(pid_file, branch_name)

def list_daemons(repo_path):
    """List all running daemons."""
    daemons = get_running_daemons(repo_path)
    if daemons:
        print("Running Git Branch Syncer daemons:")
        for branch_name, pid in daemons:
            print(f"  - Branch '{branch_name}' (PID: {pid})")
    else:
        print("No Git Branch Syncer daemons are running")

def main():
    """Main entry point for the script."""
    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
        repo_path = repo.working_dir
    except git.InvalidGitRepositoryError:
        print("Error: Not in a git repository")
        sys.exit(1)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "stop":
            if len(sys.argv) > 2 and sys.argv[2] == "all":
                # Stop all daemons
                stop_all_daemons(repo_path)
            else:
                # Stop specific branch daemon
                branch_name = sys.argv[2] if len(sys.argv) > 2 else repo.active_branch.name
                pid_file = Path(repo_path) / ".git" / f"branch-syncer-{branch_name}.pid"
                if not stop_daemon(pid_file, branch_name):
                    print(f"No daemon is running for branch '{branch_name}'")
                    # Show running daemons
                    daemons = get_running_daemons(repo_path)
                    if daemons:
                        print("\nOther running daemons:")
                        for other_branch, pid in daemons:
                            print(f"  - Branch '{other_branch}' (PID: {pid})")
                        print("\nTo stop all daemons, use: git-branch-syncer stop all")
        elif command == "list":
            # List running daemons
            list_daemons(repo_path)
        else:
            # Start daemon for specific branch
            syncer = GitBranchSyncer(branch_name=command)
            syncer.daemonize()
            syncer.run()
    else:
        # Start daemon for current branch
        syncer = GitBranchSyncer()
        syncer.daemonize()
        syncer.run()

if __name__ == "__main__":
    main()
