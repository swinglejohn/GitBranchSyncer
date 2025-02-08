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

## Usage

Start monitoring a branch:

1. Monitor current branch:
```bash
git-branch-syncer
```

2. Monitor a specific branch:
```bash
git-branch-syncer branch-name
```

Stop monitoring:
```bash
# Stop monitoring current branch
git-branch-syncer stop

# Stop monitoring specific branch
git-branch-syncer stop branch-name
```

The tool will:
- Run as a daemon process in the background
- Keep your terminal completely free for other commands
- Continuously monitor for new remote commits
- Automatically pull changes as soon as they're detected
- Log all activities to ~/.gitbranchsyncer/logs/gitbranchsyncer.log

## Features

- True background daemon process
- Terminal remains completely free for other commands
- Automatically detects and pulls new commits
- Checks for updates every 5 seconds
- Proper process management with PID files
- Detailed logging of all activities
- Graceful shutdown support
- Handles common error cases (merge conflicts, network issues)

## Log File

All sync activities are logged to:
```
~/.gitbranchsyncer/logs/gitbranchsyncer.log
```

## Requirements

- Python 3.6 or higher
- GitPython library (installed automatically)
- Unix-like operating system (Linux, macOS)
