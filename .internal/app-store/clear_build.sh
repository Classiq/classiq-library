#!/bin/bash

# Use this script to cleanup the docs directory after locally building the app store

cd "$(dirname "$0")"

DIRS=(
  "algorithms"
  "applications"
  "community"
  "tutorials"
)

for dir in "${DIRS[@]}"; do
  to_delete="$(pwd)/docs/$dir"
  keep_file="$to_delete/index.md"
  echo "Deleting build artifacts from $to_delete"
  find "$to_delete" -mindepth 1 ! -path "$keep_file" -exec rm -rf {} +
done

echo "Deleting built site at site/"
rm -rf site
