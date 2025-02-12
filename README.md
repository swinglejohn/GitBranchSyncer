# Git Branch Syncer

A command line utility that automatically keeps your local branches in sync with remote changes. Particularly useful when working with AI bots (like Mentat) that are contributing to your branches while you're testing locally.

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

## Usage Modes

### Interactive Mode (Default)
Runs in your terminal, showing real-time output:
```bash
# Monitor current branch
git-branch-syncer

# Monitor specific branch
git-branch-syncer branch-name
```

### Daemon Mode
Runs in the background, logging to file:
```bash
# Monitor current branch as daemon
git-branch-syncer --daemon

# Monitor specific branch as daemon
git-branch-syncer --daemon branch-name
```

## About the tool

- Monitors a branch and pulls new commits
- Checks for updates every 5 seconds
- Fast-forward only pulls to prevent conflicts (stops on failure to pull)
- Hooks are terminated and rerun when new changes arrive
- Can run either interactively or as a daemon process

## Managing Daemons

Stop monitoring:
```bash
# Stop monitoring current branch
git-branch-syncer stop

# Stop monitoring specific branch
git-branch-syncer stop branch-name

# Stop all running daemons
git-branch-syncer stop all
```

List daemons:
```bash
# List all running daemons across all repositories
git-branch-syncer list
```

## Hooks

You can create a hooks script that will be executed after successfully pulling new changes. This is useful for automatically rebuilding and restarting your project when changes are pulled.

To use hooks:
1. Create a file named `.git-branch-syncer-hooks.sh` in your repository root
2. Make it executable (`chmod +x .git-branch-syncer-hooks.sh`)
3. Add "#!/bin/bash" at the top of the file
4. Add any and all commands to rebuild/restart your project

Example hooks script:
```bash
#!/bin/bash

# Rebuild and restart after new changes (these commands are just examples)
npm install
npm run build
pm2 restart myapp
```

The hooks script:
- Is optional - syncing works without it
- Runs from the repository root directory
- Will be terminated and rerun when new changes arrive
- Output is visible in interactive mode
- Output is logged to file in daemon mode

## Log File (Daemon Mode)

When running in daemon mode, all activities are logged to:
```
~/.gitbranchsyncer/logs/gitbranchsyncer.log
```

## Requirements

- Python 3.6 or higher
- GitPython library (installed automatically)
- Unix-like operating system (Linux, macOS)
