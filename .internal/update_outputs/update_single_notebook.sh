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
    echo "NOT updating links for ${notebook_path} since 'jupyter nbconvert' failed with exit code ${status}"
    return "$status"
  fi

  "$PATCH_DIR/update_links.py" "$notebook_path" "$executed_notebook_path"
}

main() {
  parse_args "$@" || exit 1
  assert_python3_kernel_exists || exit 1
  export_notebook_execution_env

  prepare_notebook || exit 1
  trap cleanup_notebook EXIT

  time_it "\"$notebook_path\"" execute_notebook_inplace "$executed_notebook_path"
  local status=$?
  "$PATCH_DIR/injected_cells.py" remove "$executed_notebook_path"

  if [[ "$is_links_only" == true ]]; then
    take_links_from_copy $status
    status=$?
  fi

  return $status
}

main "$@"
