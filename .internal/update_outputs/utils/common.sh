#!/bin/bash

# helpers shared by the update_outputs scripts (sourced, not executed)

UTILS_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

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

# usage: format_duration <seconds>  ->  hh:mm:ss
format_duration() {
  local elapsed=$1
  printf "%02d:%02d:%02d" $((elapsed / 3600)) $((elapsed % 3600 / 60)) $((elapsed % 60))
}

# environment for executing notebooks unattended
export_notebook_execution_env() {
  # disable popping browser for `show(qprog)`
  export BROWSER="$UTILS_DIR/fake_browser.sh"

  # trigger circuit creation in backend
  export OPENVSCODE="some-dummy-value"
}
