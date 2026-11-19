#!/bin/bash

# jupyter helpers for the update_outputs scripts (sourced, not executed)

UTILS_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

# environment for executing notebooks unattended
export_notebook_execution_env() {
  # disable popping browser for `show(qprog)`
  export BROWSER="$UTILS_DIR/fake_browser.sh"

  # trigger circuit creation in backend
  export OPENVSCODE="some-dummy-value"
}

assert_python3_kernel_exists() {
  if ! jupyter kernelspec list | tail -n +2 | awk '{print $1}' | grep -xq "python3"; then
    echo "Kernel python3 not found" >&2
    return 1
  fi
}

# usage: is_notebook <path>  - jupyter's checkpoints aren't counted as notebooks
is_notebook() {
  [[ "$1" == *.ipynb && "$1" != *.ipynb_checkpoints/* ]]
}

# usage: find_notebooks <folder> [name pattern, default: *.ipynb]  ->  prints the notebooks, NUL-separated
# skips jupyter's checkpoints
find_notebooks() {
  find "$1" -name .ipynb_checkpoints -prune -o -type f -name "${2:-*.ipynb}" -print0
}

# usage: copy_notebook <notebook path>  ->  prints the path of the copy (next to the original)
copy_notebook() {
  local copy_path="$1.temp.ipynb"
  cp "$1" "$copy_path" && echo "$copy_path"
}

# usage: execute_notebook_inplace <notebook path>
# nbconvert runs the kernel in the notebook's folder, so relative paths in the notebook work from anywhere
execute_notebook_inplace() {
  jupyter nbconvert --to notebook --execute --inplace "$1" \
    --ExecutePreprocessor.kernel_name=python3
}
