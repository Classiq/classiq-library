#!/bin/bash

# all this script does is wrap the line:
# 	find . -type f -name "*.ipynb" | xargs -P3 -I{} jupyter nbconvert --to notebook --execute --inplace {}

if [[ " $* " == *" --help "* ]]; then
  echo "usage: $0"
  echo "  plus, there are some environment variables which you can set"
  echo "    UPDATER_SILENCE_PIP - can be set to '1' or 'true'"
  echo "    UPDATER_MAX_THREADS - any number (recommending 1, 2, or 3)"
  echo "    UPDATER_MODE        - can be set to 'test_small', 'test_algorithms', 'test_all'"
  echo "    UPDATER_FOLDER      - can be set to a folder, on which we run 'find <that folder>."
  echo
  echo "example usage:"
  echo "UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_FOLDER=algorithms/algebraic .internal/update_outputs/update_notebooks.sh"
  echo
  echo "UPDATER_MAX_THREADS=true UPDATER_SILENCE_PIP=true UPDATER_TRACK_TIME=false UPDATER_MODE=test_small .internal/update_outputs/update_notebooks.sh"
  echo
  echo "UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_LINKS_ONLY=0 UPDATER_FOLDER=algorithms/algebraic .internal/update_outputs/update_notebooks.sh"
  exit 0
fi

#
# 1) Initialization - `git pull` + create-new-branch
#
echo "======= Init ======="
cd "$(git rev-parse --show-toplevel)"

if [ "$UPDATER_SILENCE_GIT" = "true" ] || [ "$UPDATER_SILENCE_GIT" = "1" ]; then
    out_git="/dev/null"
else
    out_git="/dev/stdout"
fi

git checkout main
git pull >"$out_git"

echo
git checkout -b "updating_notebooks_$(date '+%Y.%m.%d_%H.%M')"
echo

# is outside venv; return 0 = outside venv; return 1 = inside venv
python -c "import sys; sys.exit(not hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))"
if [ $? -eq 0 ]; then
  echo "Please enter venv"
  exit 1
fi


echo "[*] Updating pip"
if [ "$UPDATER_SILENCE_PIP" = "true" ] || [ "$UPDATER_SILENCE_PIP" = "1" ]; then
    out_pip="/dev/null"
else
    out_pip="/dev/stdout"
fi
start=$(date +%s)

python -m pip install -U -r requirements.txt -r requirements_tests.txt >"$out_pip"

end=$(date +%s)
elapsed=$((end - start))
# format hh:mm:ss
printf -v duration "%02d:%02d:%02d" $((elapsed/3600)) $((elapsed%3600/60)) $((elapsed%60))
printf "[*] Updating pip - done : took %s\n" "$duration"

#
# 2) Update the notebooks
#
echo
echo
echo "======= Updating notebooks ======="

current_folder="$(realpath "$(dirname "$0")")"

# Set default values
MAX_THREADS=${UPDATER_MAX_THREADS:-3}  # note: there's a max of 3 running jobs per user, so we limit the threads to 3
MODE=${UPDATER_MODE:-}
FOLDER=${UPDATER_FOLDER:-}

# Determine the list of files to process
if [[ -n "$FOLDER" ]]; then
  FIND_CMD="find \"$FOLDER\" -type f -name \"*.ipynb\""
else
  case "$MODE" in
    test_small)
      FIND_CMD='find . -type f -name "*bernstein*.ipynb"'
      ;;
    test_algorithms)
      FIND_CMD='find algorithms/ -type f -name "*.ipynb"'
      ;;
    test_all)
      FIND_CMD='find . -type f -name "*.ipynb"'
      ;;
    *)
      echo "Error: Either UPDATER_FOLDER must be set or UPDATER_MODE must be one of: test_small, test_algorithms, test_all."
      exit 1
      ;;
  esac
fi

if [ "$UPDATER_LINKS_ONLY" = "false" ] || [ "$UPDATER_LINKS_ONLY" = "0" ]; then
    links_only_flag=""
else
    links_only_flag="--links-only"
fi

# Execute the command
eval "$FIND_CMD" | xargs -P"$MAX_THREADS" -I{} "$current_folder/update_single_notebook.sh" "{}" "$links_only_flag"

#
# 3) Commit the changes + open PR
#
echo
echo
echo "======= Creating PR ======="
# 1. Restore all .synthesis_options.json files to discard their changes
find . -name "*.synthesis_options.json" -exec git restore {} +
# 2. Add all .ipynb files recursively
find . -name "*.ipynb" -exec git add {} +
# 3. Commit the staged .ipynb files
git commit -m "Updating notebooks output"

if [ $? -ne 0 ]; then
	# running twice so that we'd include the pre-commit updates
	find . -name "*.ipynb" -exec git add {} +
	git commit -m "Updating notebooks output"
fi


gh pr create --fill --label "Updating output"
gh pr view --web
