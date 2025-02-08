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

## Usage

The tool can be used in two ways:

1. Monitor current branch:
```bash
git-branch-syncer
```

2. Monitor a specific branch:
```bash
git-branch-syncer branch-name
```

The tool will:
- Run in the background while keeping your terminal interactive
- Continuously monitor for new remote commits
- Automatically pull changes as soon as they're detected
- Provide timestamped feedback when changes are pulled
- Can be stopped at any time with Ctrl+C

## Features

- Runs in background while keeping terminal interactive
- Automatically detects and pulls new commits
- Checks for updates every 5 seconds
- Shows timestamp with notifications
- Graceful shutdown with Ctrl+C
- Handles common error cases (merge conflicts, network issues)
- Provides clear feedback about sync status

## Requirements

- Python 3.6 or higher
- GitPython library (installed automatically)
