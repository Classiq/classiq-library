#!/bin/bash

# usage: update_single_notebook.sh <notebook path> [--links-only]
# exits with non-zero if the notebook failed to execute, or if its links failed to update

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
PATCH_DIR="$SCRIPT_DIR/patch_notebook"
source "$SCRIPT_DIR/utils/common.sh"

parse_args() {
  notebook_path="$(realpath "$1")"
  notebook_dir="$(dirname "$notebook_path")"

  is_links_only=false
  has_flag --links-only "$@" && is_links_only=true
}

assert_python3_kernel_exists() {
  if ! jupyter kernelspec list | tail -n +2 | awk '{print $1}' | grep -xq "python3"; then
    echo "Kernel python3 not found" >&2
    return 1
  fi
}

# in links-only mode, we execute a temporary copy, and later take only the links from it
prepare_notebook() {
  if [[ "$is_links_only" == true ]]; then
    executed_notebook_path="$notebook_path.temp.ipynb"
    cp "$notebook_path" "$executed_notebook_path"
  else
    executed_notebook_path="$notebook_path"
  fi

  "$PATCH_DIR/injected_cells.py" add "$executed_notebook_path"
}

# returns the exit code of `jupyter nbconvert`
execute_notebook() {
  local out=/dev/stdout
  is_true "$UPDATER_TRACK_TIME" true || out=/dev/null

  local start end status
  start=$(date +%s)
  printf "[*] Starting at %s : \"%s\"\n" "$(date)" "$notebook_path" >>"$out"

  (
    cd "$notebook_dir" &&
      jupyter nbconvert --to notebook --execute --inplace "$(basename "$executed_notebook_path")" --ExecutePreprocessor.kernel_name=python3
  )
  status=$?

  end=$(date +%s)
  printf "[*] Ended    at %s : \"%s\" : took %s\n" "$(date)" "$notebook_path" "$(format_duration $((end - start)))" >>"$out"

  return $status
}

# usage: finalize_notebook <exit code of execute_notebook>
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

  prepare_notebook
  execute_notebook
  finalize_notebook $?
}

main "$@"
