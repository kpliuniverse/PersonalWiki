#usr/bin/env bash

git stash export --to-ref "refs/stashes/$1"
git push origin "refs/stashes/$1"


