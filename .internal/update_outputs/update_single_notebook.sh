#!/bin/bash

# usage: update_single_notebook.sh <notebook path> [--links-only]
# exits with non-zero if the notebook failed to execute, or if its links failed to update

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
PATCH_DIR="$SCRIPT_DIR/patch_notebook"
source "$SCRIPT_DIR/utils/common.sh"
source "$SCRIPT_DIR/utils/jupyter_utils.sh"

parse_args() {
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

# usage: finalize_notebook <exit code of the execution>
# returns non-zero if the execution failed, or if the links failed to update
finalize_notebook() {
  local status=$1

  "$PATCH_DIR/injected_cells.py" remove "$executed_notebook_path"

  if [[ "$is_links_only" == true ]]; then
    if [[ $status -eq 0 ]]; then
      "$PATCH_DIR/update_links.py" "$notebook_path" "$executed_notebook_path" || status=$?
    else
      echo "NOT updating links for ${notebook_path} since 'jupyter nbconvert' failed with exit code ${status}"
    fi

    rm "$executed_notebook_path"
  fi

  return $status
}

main() {
  parse_args "$@"
  assert_python3_kernel_exists || exit 1
  export_notebook_execution_env

  prepare_notebook || exit 1
  time_it "\"$notebook_path\"" execute_notebook_inplace "$executed_notebook_path"
  finalize_notebook $?
}

main "$@"
