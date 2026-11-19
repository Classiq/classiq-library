#!/bin/bash

# git helpers for the update_outputs scripts (sourced, not executed)

# usage: create_branch_from_main <branch name>
create_branch_from_main() {
  git checkout main &&
    git pull &&
    git checkout -b "$1"
}

# usage: git_restore_by_name <file name pattern>
git_restore_by_name() {
  find . -name "$1" -exec git restore {} +
}

# usage: git_add_by_name <file name pattern>
git_add_by_name() {
  find . -name "$1" -exec git add {} +
}

# usage: commit_by_name <file name pattern> <message>
# if pre-commit edited the files, the first commit fails, and the second one includes those edits
commit_by_name() {
  local pattern=$1 message=$2

  git_add_by_name "$pattern"
  if ! git commit -m "$message"; then
    git_add_by_name "$pattern"
    git commit -m "$message"
  fi
}

# usage: open_pr <label>
open_pr() {
  gh pr create --fill --label "$1"
  gh pr view --web
}
