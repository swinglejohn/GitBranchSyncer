# Git Branch Syncer

A command line utility that automatically keeps your local branches in sync with remote changes by running in the background. Particularly useful when working with AI bots (like Mentat) that are contributing to your branches while you're testing locally.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/swinglejohn/GitBranchSyncer.git
cd GitBranchSyncer
```

2. Install using pip:
```bash
pip install .
```


## Common Commands:
```bash
# Monitor current branch (in current directory/ repo)
git-branch-syncer

# Stop monitoring current branch (in current directory/ repo)
git-branch-syncer stop

# List all running daemons across all repositories
git-branch-syncer list

# Stop all running daemons across all repositories
git-branch-syncer stop all
```

## About the tool

- Runs as a daemon process in the background
- Monitors a branch and pulls new commits
- Checks for updates every 5 seconds
- Allows for multiple instances running at once (managed by PID)
- Fast-forward only pulls to prevent conflicts (stops on failure to pull)
- Log all activities to ~/.gitbranchsyncer/logs/gitbranchsyncer.log

## All Commands 

Start monitoring:
```bash
# Monitor current branch
git-branch-syncer

# Monitor specific branch
git-branch-syncer branch-name
```

Stop monitoring:
```bash
# Stop monitoring current branch
git-branch-syncer stop

# Stop monitoring specific branch
git-branch-syncer stop branch-name

# Stop all running daemons
git-branch-syncer stop all
```

Manage daemons:
```bash
# List all running daemons across all repositories
git-branch-syncer list

# Example output:
Running Git Branch Syncer daemons:

project1:
  - Branch 'main' (PID: 1234)
  - Branch 'feature-1' (PID: 5678)

project2:
  - Branch 'develop' (PID: 9012)
```

## Log File

All sync activities are logged to:
```
~/.gitbranchsyncer/logs/gitbranchsyncer.log
```

## Requirements

- Python 3.6 or higher
- GitPython library (installed automatically)
- Unix-like operating system (Linux, macOS)
