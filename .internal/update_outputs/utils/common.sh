#!/bin/bash

# general helpers for the update_outputs scripts (sourced, not executed)

# usage: is_true <value> <default: true|false>
# "true" / "1" are true, "false" / "0" are false (case-insensitive), anything else (including empty) falls back to <default>
is_true() {
  case "${1,,}" in
    true | 1) return 0 ;;
    false | 0) return 1 ;;
    *) [[ "$2" == true ]] ;;
  esac
}

# usage: has_flag <flag> <args...>
has_flag() {
  local flag=$1
  shift

  local arg
  for arg in "$@"; do
    if [[ "$arg" == "$flag" ]]; then
      return 0
    fi
  done
  return 1
}

# usage: variable=$(as_bool <command...>)
# prints "true" if the command succeeds, and "false" otherwise
# e.g. `is_links_only=$(as_bool has_flag --links-only "$@")`
as_bool() {
  if "$@"; then
    echo true
  else
    echo false
  fi
}

# usage: silence_if <true|false> <command...>
# runs the command, discarding its stdout if true
silence_if() {
  local should_silence=$1
  shift

  if [[ "$should_silence" == true ]]; then
    "$@" >/dev/null
  else
    "$@"
  fi
}

# usage: format_duration <seconds>  ->  hh:mm:ss
format_duration() {
  local elapsed=$1
  printf "%02d:%02d:%02d" $((elapsed / 3600)) $((elapsed % 3600 / 60)) $((elapsed % 60))
}

# usage: time_it <label> <command...>
# runs the command, printing when it starts and ends (unless UPDATER_TRACK_TIME is false)
# returns the exit code of the command
time_it() {
  local label=$1
  shift

  if ! is_true "$UPDATER_TRACK_TIME" true; then
    "$@"
    return
  fi

  local start end status
  start=$(date +%s)
  printf "[*] Starting at %s : %s\n" "$(date)" "$label"

  "$@"
  status=$?

  end=$(date +%s)
  printf "[*] Ended    at %s : %s : took %s\n" "$(date)" "$label" "$(format_duration $((end - start)))"

  return $status
}

print_section() {
  echo
  echo
  echo "======= $1 ======="
}
