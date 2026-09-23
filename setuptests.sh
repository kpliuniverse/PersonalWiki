#!/usr/bin/env bash

rm -rf .testenv
mkdir .testenv
cp -r end-tests/. .testenv
#uv run tools/gen_endtest.py