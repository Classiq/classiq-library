#!/bin/bash

#
# Parse arguments
#
is_links_only=false
for arg in "$@"; do
  if [[ "$arg" == "--links-only" ]]; then
    is_links_only=true
    break
  fi
done

#
# Parse file paths
#
notebook_relative_path="$1"
notebook_path="$(realpath "$notebook_relative_path")"

notebook_dir=$(dirname "$notebook_path")
notebook_name=$(basename "$notebook_path")


current_folder="$(realpath "$(dirname "$0")")"


#
# Preparations before executing notebook
#

# disable popping browser for `show(qprog)`
export BROWSER="$current_folder/fake_browser.sh"

# trigger circuit creation in backend
export OPENVSCODE="some-dummy-value"

# validations, before starting copy
if ! jupyter kernelspec list | tail -n +2 | awk '{print $1}' | grep -xq "python3"; then
  echo "Kernel python3 not found" >&2
  exit 1
fi

#
# Editing notebook before execution
#

# (maybe) make a copy
if [[ "$is_links_only" == true ]]; then
	notebook_copy_path="$notebook_path.temp.ipynb"
	notebook_copy_name=$(basename "$notebook_copy_path")
	cp "$notebook_path" "$notebook_copy_path"
else
	notebook_copy_path="$notebook_path"
fi

# hook edit notebook
"$current_folder/hook_add_random_seed.py" "$notebook_copy_path"

#
# Executing
#

# (maybe) track timing
if [ "$UPDATER_TRACK_TIME" = "false" ] || [ "$UPDATER_TRACK_TIME" = "0" ]; then
  out="/dev/null"
else
  out="/dev/stdout"
fi

# record start time
start=$(date +%s)
printf "[*] Starting at %s : \"%s\"\n" "$(date)" "$notebook_path" >"$out"

# execute
pushd "$notebook_dir" > /dev/null
jupyter nbconvert --to notebook --execute --inplace "$notebook_copy_name" --ExecutePreprocessor.kernel_name=python3
status=$?
popd > /dev/null

# record end time
end=$(date +%s)
elapsed=$((end - start))

# format hh:mm:ss
printf -v duration "%02d:%02d:%02d" $((elapsed/3600)) $((elapsed%3600/60)) $((elapsed%60))
printf "[*] Ended    at %s : \"%s\" : took %s\n" "$(date)" "$notebook_path" "$duration" >"$out"

#
# Post execution
#

"$current_folder/hook_remove_random_seed.py" "$notebook_copy_path"

#
# if links-only - then merge the diff
#
if [[ "$is_links_only" == true ]]; then
	if [ $status -eq 0 ]; then
		"$current_folder/update_links.py" "$notebook_path" "$notebook_copy_path"
	else
		echo "NOT updating links for ${notebook_path} since 'jupyter nbconvert' failes with exit code ${status}"
	fi

	rm "$notebook_copy_path"
fi
