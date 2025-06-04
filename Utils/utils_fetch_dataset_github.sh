#!/usr/bin/env bash

gh search repos --language=html --topic=static-site --sort=stars --created '>2024-07-01' --limit 100 --json fullName --jq '.[].fullName' |

while IFS= read -r repo; do
  echo "Bearbeite $repo …"

  branch="$(gh repo view "$repo" --json defaultBranchRef -q .defaultBranchRef.name)"

  tree_json=$(gh api "repos/$repo/git/trees/$branch?recursive=1")

  html_paths=$(echo "$tree_json" |
    jq -r '.tree[]
          | select(.path | test("\\.html?$"))   # <- nur Dateiendung zählt
          | .path')

  echo "Starte mit $repo ($branch)"
  echo "HTML-Paths gefunden:"
  echo "$html_paths"

  sleep 1
done
