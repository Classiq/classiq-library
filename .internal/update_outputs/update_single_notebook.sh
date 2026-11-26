#!/bin/bash

# usage: update_single_notebook.sh <notebook path> [--links-only]
# exits with non-zero if the notebook failed to execute, or if its links failed to update

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
PATCH_DIR="$SCRIPT_DIR/patch_notebook"
source "$SCRIPT_DIR/utils/common.sh"
source "$SCRIPT_DIR/utils/jupyter_utils.sh"

parse_args() {
  if [[ ! -f "$1" ]]; then
    echo "Error: notebook '$1' doesn't exist. usage: $0 <notebook path> [--links-only]" >&2
    return 1
  fi

  notebook_path="$(realpath "$1")"
  notebook_label="\"$1\"" # for the logs - the path as it was given, which is usually shorter
  is_links_only=$(as_bool has_flag --links-only "$@")
}

# in links-only mode, we execute a temporary copy, and later take only the links from it
prepare_notebook() {
  if [[ "$is_links_only" == true ]]; then
    executed_notebook_path="$(copy_notebook "$notebook_path")" || return 1
  else
    executed_notebook_path="$notebook_path"
  fi

  "$PATCH_DIR/injected_cells.py" add "$executed_notebook_path"
}

# runs on exit, even if interrupted (e.g. by ctrl-c), so that no injected cells or temporary copy is left behind
cleanup_notebook() {
  if [[ "$is_links_only" == true ]]; then
    rm -f "$executed_notebook_path"
  else
    "$PATCH_DIR/injected_cells.py" remove "$executed_notebook_path"
  fi
}

# usage: take_links_from_copy <exit code of the execution>
take_links_from_copy() {
  local status=$1

  if [[ $status -ne 0 ]]; then
    echo "[!] Not updating the links of $notebook_label, since its execution failed (exit code $status)" >&2
    return "$status"
  fi

  if ! "$PATCH_DIR/update_links.py" "$notebook_path" "$executed_notebook_path"; then
    echo "[!] Couldn't update the links of $notebook_label. you may update all of its outputs instead (not links-only)" >&2
    return 1
  fi
}

main() {
  parse_args "$@" || exit 1
  assert_python3_kernel_exists || exit 1
  export_notebook_execution_env

  prepare_notebook || exit 1
  trap cleanup_notebook EXIT

  time_it "$notebook_label" execute_notebook_inplace "$executed_notebook_path"
  local status=$?
  "$PATCH_DIR/injected_cells.py" remove "$executed_notebook_path"

  if [[ "$is_links_only" == true ]]; then
    take_links_from_copy $status
    status=$?
  fi

  return $status
}

main "$@"
