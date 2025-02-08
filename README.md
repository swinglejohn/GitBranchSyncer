# Git Branch Syncer

A command line utility that helps you stay in sync with remote branches, particularly useful when working with AI bots (like Mentat) that are contributing to your branches while you're testing locally.

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

1. Sync current branch:
```bash
git-branch-syncer
```

2. Sync a specific branch:
```bash
git-branch-syncer branch-name
```

The tool will:
- Fetch the latest changes from remote
- Check if your local branch is behind the remote
- Pull any new changes if needed
- Provide feedback about the sync status

## Features

- Automatically detects current branch if none specified
- Fetches latest changes from remote
- Shows number of new commits being pulled
- Handles common error cases (merge conflicts, network issues)
- Provides clear feedback about what's happening

## Requirements

- Python 3.6 or higher
- GitPython library (installed automatically)
