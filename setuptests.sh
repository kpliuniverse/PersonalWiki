#!/usr/bin/env bash

rm -rf .testenv
mkdir .testenv
uv run tools/gen_endtest.py