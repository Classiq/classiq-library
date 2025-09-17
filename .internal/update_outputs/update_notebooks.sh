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
  echo "UPDATER_MAX_THREADS=1 UPDATER_SILENCE_PIP=1 UPDATER_MODE=test_small .internal/update_outputs/update_notebooks.sh"
  exit 0
fi




#
# 1) Initialization - `git pull` + create-new-branch
#
echo "======= Init ======="
cd "$(git rev-parse --show-toplevel)"

git checkout main
git pull

echo
git checkout -b "updating_notebooks_$(date '+%Y.%m.%d_%H.%M')"
echo

echo "Updating pip"
if [ "$UPDATER_SILENCE_PIP" = "true" ] || [ "$UPDATER_SILENCE_PIP" = "1" ]; then
    out="/dev/null"
else
    out="&1"
fi
python -m pip install -U -r requirements.txt -r requirements_tests.txt >"$out"
echo "Updating pip - done"

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

# Execute the command
eval "$FIND_CMD" | xargs -P"$MAX_THREADS" -I{} "$current_folder/update_single_notebook_links.sh" "{}"

#
# 3) Commit the changes + open PR
#
echo
echo
echo "======= Creating PR ======="
# 1. Add all .py files recursively
find . -name "*.ipynb" -exec git add {} +
# 2. Restore all .txt files to discard their changes
find . -name "*.synthesis_options.json" -exec git restore {} +
# 3. Commit the staged .py files
git commit -m "Updating notebooks output"

# running twice so that we'd include the pre-commit updates
find . -name "*.ipynb" -exec git add {} +
git commit -m "Updating notebooks output"


gh pr create --fill --label "Updating output"
gh pr view --web
