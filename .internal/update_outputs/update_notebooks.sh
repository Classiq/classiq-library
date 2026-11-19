#!/bin/bash

# all this script does is wrap the line:
# 	find . -type f -name "*.ipynb" | xargs -P3 -I{} jupyter nbconvert --to notebook --execute --inplace {}

SCRIPT_DIR="$(realpath "$(dirname "$0")")"
source "$SCRIPT_DIR/utils/common.sh"
source "$SCRIPT_DIR/utils/git_utils.sh"
source "$SCRIPT_DIR/utils/jupyter_utils.sh"
source "$SCRIPT_DIR/utils/python_utils.sh"

# the configuration - taken from the environment variables, and overridden by the arguments (see `parse_args`)
PATHS=()               # absolute paths of the notebooks / folders to update. FOLDER / MODE are converted into it
ARE_PATHS_GIVEN=false  # true even if all the given paths were skipped, so that we won't fall back to FOLDER / MODE
FOLDER=${UPDATER_FOLDER:-}
MODE=${UPDATER_MODE:-}
SHOULD_CREATE_BRANCH=$(as_bool is_true "$UPDATER_CREATE_BRANCH" true)
SHOULD_UPDATE_PIP=$(as_bool is_true "$UPDATER_UPDATE_PIP" true)
SHOULD_CREATE_PR=$(as_bool is_true "$UPDATER_CREATE_PR" true)
MAX_THREADS=${UPDATER_MAX_THREADS:-3} # note: there's a max of 3 running jobs per user, so we limit the threads to 3
IS_LINKS_ONLY=$(as_bool is_true "$UPDATER_LINKS_ONLY" true)
SHOULD_TRACK_TIME=$(as_bool is_true "$UPDATER_TRACK_TIME" true)
SHOULD_SILENCE_GIT=$(as_bool is_true "$UPDATER_SILENCE_GIT" false)
SHOULD_SILENCE_PIP=$(as_bool is_true "$UPDATER_SILENCE_PIP" false)

print_help() {
  cat <<EOF
usage: $0 [options] [paths...]

executes notebooks, and opens a PR with their updated outputs

which notebooks (one is required):
  [paths...]                                       notebooks and folders, relative to the current folder. '-' reads them from stdin (one per line).
                                                   files that aren't notebooks are skipped. takes precedence over --folder and --mode
  --folder <dir>          [UPDATER_FOLDER]         all the notebooks under <dir> (relative to the repo root)
  --mode <mode>           [UPDATER_MODE]           'test_small' / 'test_algorithms' / 'test_all'

steps (all on by default. turn them off to update the notebooks locally, without git / pip):
  --[no-]create-branch    [UPDATER_CREATE_BRANCH]  checkout main, pull, and create a new branch
  --[no-]update-pip       [UPDATER_UPDATE_PIP]     'pip install -U' the requirements
  --[no-]create-pr        [UPDATER_CREATE_PR]      commit the notebooks, and open a PR

options:
  -j, --max-threads <n>   [UPDATER_MAX_THREADS]    how many notebooks to execute in parallel. default: 3
  --[no-]links-only       [UPDATER_LINKS_ONLY]     only update the platform links, keeping the rest of the outputs. default: on
  --[no-]track-time       [UPDATER_TRACK_TIME]     print when 'pip install' and each notebook start and end. default: on
  --[no-]silence-git      [UPDATER_SILENCE_GIT]    silence git while creating the branch. default: off
  --[no-]silence-pip      [UPDATER_SILENCE_PIP]    silence 'pip install'. default: off
  -h, --help

boolean flags also accept a value, e.g. '--links-only=false'.
each option can also be set by its environment variable (in brackets), and the arguments take precedence.
boolean environment variables can be set to '1' / 'true' or '0' / 'false' (case-insensitive).

examples:
  git diff --name-only main | $0 -  # from the repo root, since git prints paths relative to it
  find . -type f -name "*grover*" | $0 - --no-create-branch --no-update-pip --no-create-pr
  $0 algorithms/foundational/ -j 1 --silence-pip
  $0 --mode test_small --no-track-time
  UPDATER_SILENCE_PIP=1 UPDATER_FOLDER=algorithms/algebraic $0 --links-only=false
EOF
}

# usage: add_paths <path...>  - adds the paths (relative to the current folder) to PATHS, skipping the missing ones
add_paths() {
  ARE_PATHS_GIVEN=true

  local path
  for path in "$@"; do
    if [[ -e "$path" ]]; then
      PATHS+=("$(realpath "$path")")
    elif [[ -n "$path" ]]; then
      echo "Warning: skipping '$path', which doesn't exist" >&2
    fi
  done
}

# overrides the configuration by the arguments
# prints an error for each unknown argument, and returns non-zero if there were any
parse_args() {
  local is_valid=true
  local options_with_value="--folder|--mode|-j|--max-threads"
  local stdin_paths

  while [[ $# -gt 0 ]]; do
    # normalize `--option=value` into `--option value`
    if [[ "$1" =~ ^($options_with_value)=(.*)$ ]]; then
      set -- "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${@:2}"
    fi

    if [[ "$1" =~ ^($options_with_value)$ && $# -lt 2 ]]; then
      echo "Error: '$1' requires a value (see --help)" >&2
      is_valid=false
      break
    fi

    case "$1" in
      -h | --help)
        print_help
        exit 0
        ;;
      --folder) FOLDER=$2; shift ;;
      --mode) MODE=$2; shift ;;
      -j | --max-threads) MAX_THREADS=$2; shift ;;
      -j?*) MAX_THREADS=${1#-j} ;;
      # boolean flags - `--flag`, `--no-flag`, or `--flag=<bool>`
      --create-branch | --no-create-branch | --create-branch=*) SHOULD_CREATE_BRANCH=$(parse_boolean_flag "$1") || is_valid=false ;;
      --update-pip | --no-update-pip | --update-pip=*) SHOULD_UPDATE_PIP=$(parse_boolean_flag "$1") || is_valid=false ;;
      --create-pr | --no-create-pr | --create-pr=*) SHOULD_CREATE_PR=$(parse_boolean_flag "$1") || is_valid=false ;;
      --links-only | --no-links-only | --links-only=*) IS_LINKS_ONLY=$(parse_boolean_flag "$1") || is_valid=false ;;
      --track-time | --no-track-time | --track-time=*) SHOULD_TRACK_TIME=$(parse_boolean_flag "$1") || is_valid=false ;;
      --silence-git | --no-silence-git | --silence-git=*) SHOULD_SILENCE_GIT=$(parse_boolean_flag "$1") || is_valid=false ;;
      --silence-pip | --no-silence-pip | --silence-pip=*) SHOULD_SILENCE_PIP=$(parse_boolean_flag "$1") || is_valid=false ;;
      # paths
      -)
        mapfile -t stdin_paths
        add_paths "${stdin_paths[@]}"
        ;;
      -?*)
        echo "Error: unknown argument '$1' (see --help)" >&2
        is_valid=false
        ;;
      *) add_paths "$1" ;;
    esac
    shift
  done

  [[ "$is_valid" == true ]]
}

# converts FOLDER / MODE into PATHS (relative to the repo root)
# prints an error if neither is valid, and returns non-zero
add_folder_or_mode_paths() {
  if [[ -n "$FOLDER" ]]; then
    if [[ ! -d "$FOLDER" ]]; then
      echo "Error: folder '$FOLDER' doesn't exist (note: it's relative to the repo root)" >&2
      return 1
    fi
    add_paths "$FOLDER"
    return
  fi

  local paths
  case "$MODE" in
    test_small) mapfile -d '' paths < <(find_notebooks . "*bernstein*.ipynb") ;;
    test_algorithms) paths=(algorithms) ;;
    test_all) paths=(.) ;;
    "")
      echo "Error: either paths, --folder, or --mode must be given (see --help)" >&2
      return 1
      ;;
    *)
      echo "Error: invalid mode '$MODE'. it must be one of: test_small, test_algorithms, test_all" >&2
      return 1
      ;;
  esac
  add_paths "${paths[@]}"
}

# prints an error for each invalid option, and returns non-zero if there were any
validate_config() {
  local is_valid=true

  if [[ ! "$MAX_THREADS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: max threads must be a positive number, but got '$MAX_THREADS'" >&2
    is_valid=false
  fi

  if [[ "$ARE_PATHS_GIVEN" != true ]]; then
    add_folder_or_mode_paths || is_valid=false
  fi

  local path
  for path in "${PATHS[@]}"; do
    if [[ "$path" != "$PWD" && "$path" != "$PWD"/* ]]; then
      echo "Error: '$path' is outside of the repo ('$PWD')" >&2
      is_valid=false
    fi
  done

  if [[ "$is_valid" == true && -z "$(list_notebooks | tr -d '\0')" ]]; then
    echo "Error: there are no notebooks to update" >&2
    is_valid=false
  fi

  [[ "$is_valid" == true ]]
}

# prints the notebooks to update, NUL-separated, relative to the repo root
list_notebooks() {
  local path
  for path in "${PATHS[@]}"; do
    path="$(relative_to_cwd "$path")"
    if [[ -d "$path" ]]; then
      find_notebooks "$path"
    elif is_notebook "$path"; then
      printf '%s\0' "$path"
    fi
  done
}

update_notebooks() {
  local links_only_flag
  if [[ "$IS_LINKS_ONLY" == true ]]; then
    links_only_flag="--links-only"
  else
    links_only_flag=""
  fi

  local notebooks
  mapfile -d '' notebooks < <(list_notebooks | sort -zu)
  echo "[*] Updating ${#notebooks[@]} notebook(s)"

  # a failing notebook is recorded (`|| echo`), rather than failing xargs, so that the rest keep running
  # shellcheck disable=SC2016  # the single-quoted `$N` are expanded by the inner `bash -c`
  printf '%s\0' "${notebooks[@]}" | xargs -0 -P"$MAX_THREADS" -I{} \
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
  local is_valid=true
  parse_args "$@" || is_valid=false

  #
  # 1) Initialization - validations, `git pull` + create-new-branch, update pip
  #
  print_section "Init"
  cd "$(git rev-parse --show-toplevel)" || exit 1
  # validate before making any changes, reporting all the errors at once
  validate_config || is_valid=false
  assert_inside_venv || is_valid=false
  assert_python3_kernel_exists || is_valid=false
  if [[ "$is_valid" != true ]]; then
    exit 1
  fi

  # read by `time_it`, both here and in update_single_notebook.sh
  export UPDATER_TRACK_TIME="$SHOULD_TRACK_TIME"

  if [[ "$SHOULD_CREATE_BRANCH" == true ]]; then
    silence_if "$SHOULD_SILENCE_GIT" create_branch_from_main "updating_notebooks_$(date '+%Y.%m.%d_%H.%M')" || exit 1
  fi
  if [[ "$SHOULD_UPDATE_PIP" == true ]]; then
    time_it "Updating pip" silence_if "$SHOULD_SILENCE_PIP" pip_install_requirements requirements.txt requirements_notebooks.txt
  fi

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
  if [[ "$SHOULD_CREATE_PR" == true ]]; then
    print_section "Creating PR"
    # discard the changes to the .synthesis_options.json files
    git restore -- "*.synthesis_options.json"
    commit_files "*.ipynb" "Updating notebooks output" && open_pr "Updating output"
  fi

  print_failed_notebooks
}

main "$@"
