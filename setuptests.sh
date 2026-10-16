#!/usr/bin/env bash

rm -rf .testenv
mkdir .testenv
mkdir .testenv/wikis
uv run tools.py convert-endtest-wikis .testenv/wikis
#uv run tools/gen_endtest.py