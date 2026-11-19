#!/bin/bash

# all this script does is wrap the line:
# 	find . -type f -name "*.ipynb" | xargs -P3 -I{} jupyter nbconvert --to notebook --execute --inplace {}

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
source "$SCRIPT_DIR/utils/common.sh"

MAX_THREADS=${UPDATER_MAX_THREADS:-3} # note: there's a max of 3 running jobs per user, so we limit the threads to 3
MODE=${UPDATER_MODE:-}
FOLDER=${UPDATER_FOLDER:-}

print_help() {
  cat <<EOF
usage: $0
  plus, there are some environment variables which you can set
    UPDATER_FOLDER      - can be set to a folder, on which we run 'find <that folder>'
    UPDATER_MODE        - can be set to 'test_small', 'test_algorithms', 'test_all'
    UPDATER_MAX_THREADS - any number (recommending 1, 2, or 3). default: 3
    UPDATER_LINKS_ONLY  - only update the platform links, keeping the rest of the outputs. default: true
    UPDATER_TRACK_TIME  - print when each notebook starts and ends. default: true
    UPDATER_SILENCE_GIT - silence 'git pull'. default: false
    UPDATER_SILENCE_PIP - silence 'pip install'. default: false
  booleans can be set to '1' / 'true' or '0' / 'false' (case-insensitive)

example usage:
UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_FOLDER=algorithms/algebraic .internal/update_outputs/update_notebooks.sh

UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=true UPDATER_TRACK_TIME=false UPDATER_MODE=test_small .internal/update_outputs/update_notebooks.sh

UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_LINKS_ONLY=0 UPDATER_FOLDER=algorithms/algebraic .internal/update_outputs/update_notebooks.sh
EOF
}

print_section() {
  echo
  echo
  echo "======= $1 ======="
}

#
# 1) Initialization - validations, `git pull` + create-new-branch, update pip
#
assert_inside_venv() {
  # `sys.prefix` differs from `sys.base_prefix` only inside a venv (`python -m venv` / `uv venv`)
  if ! python -c "import sys; sys.exit(sys.prefix == sys.base_prefix)"; then
    echo "Please enter venv" >&2
    return 1
  fi
}

# sets `search_root` and `name_pattern`, by which we `find` the notebooks to update
resolve_notebooks_scope() {
  if [[ -n "$FOLDER" ]]; then
    search_root="$FOLDER"
    name_pattern="*.ipynb"
    return 0
  fi

  case "$MODE" in
    test_small)
      search_root="."
      name_pattern="*bernstein*.ipynb"
      ;;
    test_algorithms)
      search_root="algorithms/"
      name_pattern="*.ipynb"
      ;;
    test_all)
      search_root="."
      name_pattern="*.ipynb"
      ;;
    *)
      echo "Error: Either UPDATER_FOLDER must be set or UPDATER_MODE must be one of: test_small, test_algorithms, test_all." >&2
      return 1
      ;;
  esac
}

create_branch() {
  local out_git=/dev/stdout
  is_true "$UPDATER_SILENCE_GIT" false && out_git=/dev/null

  git checkout main
  git pull >>"$out_git"

  echo
  git checkout -b "updating_notebooks_$(date '+%Y.%m.%d_%H.%M')"
  echo
}

update_requirements() {
  local out_pip=/dev/stdout
  is_true "$UPDATER_SILENCE_PIP" false && out_pip=/dev/null

  echo "[*] Updating pip"
  local start end
  start=$(date +%s)

  python -m pip install -U -r requirements.txt -r requirements_notebooks.txt >>"$out_pip"

  end=$(date +%s)
  printf "[*] Updating pip - done : took %s\n" "$(format_duration $((end - start)))"
}

#
# 2) Update the notebooks
#
list_notebooks() {
  find "$search_root" -type f -name "$name_pattern"
}

update_notebooks() {
  local links_only_flag=""
  is_true "$UPDATER_LINKS_ONLY" true && links_only_flag="--links-only"

  # a failing notebook is recorded (`|| echo`), rather than failing xargs, so that the rest keep running
  # shellcheck disable=SC2016  # the single-quoted `$N` are expanded by the inner `bash -c`
  list_notebooks | xargs -P"$MAX_THREADS" -I{} \
    bash -c '"$0" "$1" "$2" || echo "$1" >>"$3"' \
    "$SCRIPT_DIR/update_single_notebook.sh" {} "$links_only_flag" "$FAILED_NOTEBOOKS_FILE"
}

print_failed_notebooks() {
  if [[ -s "$FAILED_NOTEBOOKS_FILE" ]]; then
    echo
    echo "[!] Failed to update $(wc -l <"$FAILED_NOTEBOOKS_FILE") notebook(s):"
    sort "$FAILED_NOTEBOOKS_FILE" | sed 's/^/    /'
  fi
}

#
# 3) Commit the changes + open PR
#
commit_notebooks() {
  find . -name "*.ipynb" -exec git add {} +
  git commit -m "Updating notebooks output"
}

commit_and_open_pr() {
  # discard the changes to the .synthesis_options.json files
  find . -name "*.synthesis_options.json" -exec git restore {} +

  # if pre-commit edited the files, the first commit fails, and the second one includes those edits
  commit_notebooks || commit_notebooks

  gh pr create --fill --label "Updating output"
  gh pr view --web
}

main() {
  if has_flag --help "$@"; then
    print_help
    exit 0
  fi

  print_section "Init"
  cd "$(git rev-parse --show-toplevel)" || exit 1
  # validate before making any changes
  assert_inside_venv || exit 1
  resolve_notebooks_scope || exit 1
  create_branch
  update_requirements

  print_section "Updating notebooks"
  FAILED_NOTEBOOKS_FILE="$(mktemp)"
  trap 'rm -f "$FAILED_NOTEBOOKS_FILE"' EXIT
  update_notebooks

  print_section "Creating PR"
  commit_and_open_pr

  print_failed_notebooks
}

main "$@"
