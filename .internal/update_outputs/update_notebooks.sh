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
python -m pip install -U -r requirements.txt -r requirements_tests.txt

#
# 2) Update the notebooks
#
echo
echo
echo "======= Updating notebooks ======="

current_folder="$(realpath "$(dirname "$0")")"


# note: there's a max of 3 running jobs per user, so we limit the threads to 3
# # test all bernstein-vazirani notebooks
find . -type f -name "*bernstein*.ipynb" | xargs -P2 -I{} "$current_folder/update_single_notebook.sh" {}
# test all algorithms
# find algorithms/ -type f -name "*.ipynb" | xargs -P3 -I{} "$current_folder/update_single_notebook.sh" {}
# # test 3 notebooks
# find . -type f -name "*.ipynb" | head -n 3 | xargs -P3 -I{} "$current_folder/update_single_notebook.sh" {}
# # test all notebooks
# find algorithms applications tutorials -type f -name "*.ipynb" | xargs -P3 -I{} "$current_folder/update_single_notebook.sh" {}

#
# 3) Commit the changes + open PR
#
echo
echo
echo "======= Creating PR ======="
# running twice so that we'd include the pre-commit updates
git commit -a -m "Updating notebooks output" || git commit -a -m "Updating notebooks output"
# # running once, so that failure on pre-commit would fail this script
# git commit -a -m "Updating notebooks output" || { echo "pre-commit failed. please fix manually"; exit 1; }

gh pr create --fill
gh pr view --web
