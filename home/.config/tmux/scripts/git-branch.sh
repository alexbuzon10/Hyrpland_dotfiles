#!/usr/bin/env bash

dir="${1:-$PWD}"

git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

branch="$(git -C "$dir" branch --show-current 2>/dev/null)"
if [[ -z "$branch" ]]; then
    branch="$(git -C "$dir" rev-parse --short HEAD 2>/dev/null)"
fi

[[ -n "$branch" ]] && printf ' %s #[fg=#62666F]│ #[fg=#d5d5d5]' "$branch"
