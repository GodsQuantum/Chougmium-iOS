#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
binary="$(mktemp "${TMPDIR:-/tmp}/venetium-compat-test.XXXXXXXX")"
trap 'rm -f "$binary"' EXIT
cc -std=c11 -DVENETIUM_UNIT_TEST -Wall -Wextra -Werror -Itests/include src/coordinate_space.c tests/test_coordinate_space.c -o "$binary"
"$binary"

