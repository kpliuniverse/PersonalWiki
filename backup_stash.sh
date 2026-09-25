#usr/bin/env bash

git stash export --to-ref "ref/stashes/$1"
git push origin "refs/stashes/$1"


