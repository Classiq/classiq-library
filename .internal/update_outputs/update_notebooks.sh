#!/bin/bash

# all this script does is wrap the line:
# 	find . -type f -name "*.ipynb" | xargs -P3 -I{} jupyter nbconvert --to notebook --execute --inplace {}


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


# note: there's a max of 3 running jobs per user, so we limit the threads to 3
# # test all bernstein-vazirani notebooks
find . -type f -name "*bernstein*.ipynb" | xargs -P2 -I{} "$current_folder/update_single_notebook_links.sh" {}
# test all algorithms
# find algorithms/ -type f -name "*.ipynb" | xargs -P3 -I{} "$current_folder/update_single_notebook_links.sh" {}
# # test 3 notebooks
# find . -type f -name "*.ipynb" | head -n 3 | xargs -P3 -I{} "$current_folder/update_single_notebook_links.sh" {}
# # test all notebooks
# find algorithms applications tutorials -type f -name "*.ipynb" | xargs -P3 -I{} "$current_folder/update_single_notebook_links.sh" {}

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


gh pr create --fill
gh pr view --web
