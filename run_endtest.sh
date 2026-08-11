#!/usr/bin/env bash
sh ./setuptests.sh

if [$1 = ""]; then
    uv run main.py
else 
    uv run main.py .testenv/wikis/$1/wiki.pwi
fi