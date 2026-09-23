#!/usr/bin/env bash

./setuptests.sh
./prebuild.sh
if [ "$1" = '' ]; then
    uv run main.py
else 
    uv run main.py .testenv/wikis/$1/wiki.pwi
fi