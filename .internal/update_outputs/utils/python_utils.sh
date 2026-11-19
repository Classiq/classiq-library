#!/bin/bash

# python helpers for the update_outputs scripts (sourced, not executed)

assert_inside_venv() {
  # `sys.prefix` differs from `sys.base_prefix` only inside a venv (`python -m venv` / `uv venv`)
  if ! python -c "import sys; sys.exit(sys.prefix == sys.base_prefix)"; then
    echo "Error: not inside a venv. please activate one (e.g. 'source .venv/bin/activate'), and run again" >&2
    return 1
  fi
}

# usage: pip_install_requirements <requirements file...>
pip_install_requirements() {
  local args=() requirements_file
  for requirements_file in "$@"; do
    args+=(-r "$requirements_file")
  done

  python -m pip install -U "${args[@]}"
}
