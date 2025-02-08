This file contains extra context that may be useful for AIs developing the project.

The goal of not putting this in the main README is to keep it concise for human users of the tool.

This file doesn't need to repeat information already present in the main README and AIs should read them together.


## Error Handling

The daemon will automatically stop if:
- A merge conflict occurs
- The branch is not tracking a remote branch
- The branch is deleted
- Any other git error occurs

This prevents error message spam and allows the user to resolve issues manually.

## Other

When stopping a specific daemon, if it's not running, the tool will show all running daemons across repositories to help you find the one you want to stop.
