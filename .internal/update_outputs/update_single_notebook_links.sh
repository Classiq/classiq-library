#!/bin/bash

notebook_relative_path="$1"
notebook_path="$(realpath "$notebook_relative_path")"

notebook_dir=$(dirname "$notebook_path")
notebook_name=$(basename "$notebook_path")


current_folder="$(realpath "$(dirname "$0")")"

# disable popping browser for `show(qprog)`
export BROWSER="$current_folder/fake_browser.sh"

# make a copy
notebook_copy_path="$notebook_path.temp.ipynb"
notebook_copy_name=$(basename "$notebook_copy_path")
cp "$notebook_path" "$notebook_copy_path"

"$current_folder/hook_add_random_seed.py" "$notebook_copy_path"

pushd "$notebook_dir" > /dev/null
jupyter nbconvert --to notebook --execute --inplace "$notebook_copy_name"
popd > /dev/null

"$current_folder/hook_remove_random_seed.py" "$notebook_copy_path"

"$current_folder/update_links.py" "$notebook_path" "$notebook_copy_path"

rm "$notebook_copy_path"
