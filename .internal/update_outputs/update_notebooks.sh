#!/bin/bash

# all this script does is wrap the line:
# 	find . -type f -name "*.ipynb" | xargs -P3 -I{} jupyter nbconvert --to notebook --execute --inplace {}

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
source "$SCRIPT_DIR/utils/common.sh"
source "$SCRIPT_DIR/utils/git_utils.sh"
source "$SCRIPT_DIR/utils/python_utils.sh"

MAX_THREADS=${UPDATER_MAX_THREADS:-3} # note: there's a max of 3 running jobs per user, so we limit the threads to 3
MODE=${UPDATER_MODE:-}
FOLDER=${UPDATER_FOLDER:-}
IS_LINKS_ONLY=$(as_bool is_true "$UPDATER_LINKS_ONLY" true)
SHOULD_SILENCE_GIT=$(as_bool is_true "$UPDATER_SILENCE_GIT" false)
SHOULD_SILENCE_PIP=$(as_bool is_true "$UPDATER_SILENCE_PIP" false)

print_help() {
  cat <<EOF
usage: $0
  plus, there are some environment variables which you can set
    UPDATER_FOLDER      - can be set to a folder, on which we run 'find <that folder>'
    UPDATER_MODE        - can be set to 'test_small', 'test_algorithms', 'test_all'
    UPDATER_MAX_THREADS - any number (recommending 1, 2, or 3). default: 3
    UPDATER_LINKS_ONLY  - only update the platform links, keeping the rest of the outputs. default: true
    UPDATER_TRACK_TIME  - print when 'pip install' and each notebook start and end. default: true
    UPDATER_SILENCE_GIT - silence git while creating the branch. default: false
    UPDATER_SILENCE_PIP - silence 'pip install'. default: false
  booleans can be set to '1' / 'true' or '0' / 'false' (case-insensitive)

example usage:
UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_FOLDER=algorithms/algebraic .internal/update_outputs/update_notebooks.sh

UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=true UPDATER_TRACK_TIME=false UPDATER_MODE=test_small .internal/update_outputs/update_notebooks.sh

UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_LINKS_ONLY=0 UPDATER_FOLDER=algorithms/algebraic .internal/update_outputs/update_notebooks.sh
EOF
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

list_notebooks() {
  find "$search_root" -type f -name "$name_pattern"
}

update_notebooks() {
  local links_only_flag
  if [[ "$IS_LINKS_ONLY" == true ]]; then
    links_only_flag="--links-only"
  else
    links_only_flag=""
  fi

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

main() {
  if has_flag --help "$@"; then
    print_help
    exit 0
  fi

  #
  # 1) Initialization - validations, `git pull` + create-new-branch, update pip
  #
  print_section "Init"
  cd "$(git rev-parse --show-toplevel)" || exit 1
  # validate before making any changes
  assert_inside_venv || exit 1
  resolve_notebooks_scope || exit 1

  silence_if "$SHOULD_SILENCE_GIT" create_branch_from_main "updating_notebooks_$(date '+%Y.%m.%d_%H.%M')" || exit 1
  time_it "Updating pip" silence_if "$SHOULD_SILENCE_PIP" pip_install_requirements requirements.txt requirements_notebooks.txt

  #
  # 2) Update the notebooks
  #
  print_section "Updating notebooks"
  FAILED_NOTEBOOKS_FILE="$(mktemp)"
  trap 'rm -f "$FAILED_NOTEBOOKS_FILE"' EXIT
  update_notebooks

  #
  # 3) Commit the changes + open PR
  #
  print_section "Creating PR"
  # discard the changes to the .synthesis_options.json files
  git_restore_by_name "*.synthesis_options.json"
  commit_by_name "*.ipynb" "Updating notebooks output"
  open_pr "Updating output"

  print_failed_notebooks
}

main "$@"
