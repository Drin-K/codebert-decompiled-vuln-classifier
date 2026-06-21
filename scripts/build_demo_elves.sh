#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/data/demo_src"
output_dir="$repo_root/data/demo"

mkdir -p "$output_dir"

demos=(
  demo_mixed_01
  demo_mixed_02
  demo_mixed_03
  demo_buffer_overflow_only
  demo_format_string_only
  demo_integer_overflow_only
)

for demo in "${demos[@]}"; do
  gcc -O0 -g -fno-stack-protector -no-pie "$source_dir/$demo.c" -o "$output_dir/$demo"
  file "$output_dir/$demo"
done
