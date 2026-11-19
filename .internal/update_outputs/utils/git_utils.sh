#!/bin/bash

# git helpers for the update_outputs scripts (sourced, not executed)

# usage: create_branch_from_main <branch name>
create_branch_from_main() {
  git checkout main &&
    git pull &&
    git checkout -b "$1"
}

# usage: commit_files <pathspec> <message>
# in a pathspec, `*` matches across folders, and gitignored files (like .ipynb_checkpoints) are skipped
# if pre-commit edited the files, the first commit fails, and the second one includes those edits
commit_files() {
  local pathspec=$1 message=$2

  git add -- "$pathspec"
  if ! git commit -m "$message"; then
    git add -- "$pathspec"
    git commit -m "$message"
  fi
}

# usage: open_pr <label>
open_pr() {
  gh pr create --fill --label "$1"
  gh pr view --web
}
