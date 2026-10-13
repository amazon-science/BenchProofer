#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Sanitize the repo checkout's .git in an eval container so the agent CANNOT recover the
# gold fix from git history (SWE-bench issue #465: refs, reflog, packed-refs,
# tags expose solution commits even with HEAD at base_commit). Afterwards only
# base_commit and its ancestors survive; future objects are physically pruned.
#
# Usage:  sanitize_repo.sh <base_commit> <repo_dir>
# repo_dir is REQUIRED: it is the benchmark's checkout directory (/testbed on
# SWE-bench_Verified, /app on SWE-bench Pro) and the caller knows it from the
# registry. Defaulting it here would silently sanitize the wrong directory --
# and a 'sanitized' container whose .git was never touched is the leak this
# script exists to close.
# Exit 0 on success; prints a one-line VERIFY result the caller can assert on.
set -uo pipefail

BASE="${1:?usage: sanitize_repo.sh <base_commit> <repo_dir>}"
REPO="${2:?usage: sanitize_repo.sh <base_commit> <repo_dir> (no default: see above)}"
cd "$REPO" || { echo "SANITIZE-FAIL: no $REPO"; exit 1; }
git config --global --add safe.directory "$REPO" 2>/dev/null || true

# 0a) LOCATE the git dir, and refuse anything that is not this checkout's own
# root. `[ -d .git ]` is not that test: in a worktree or submodule layout .git is
# a FILE, and a checkout nested inside a larger repo has no .git of its own at
# all while `git` commands here still resolve the PARENT's. Both used to take a
# "nothing to strip" branch that printed SANITIZE-OK and exited 0 before the
# VERIFY step below could run, so a container with the gold fix one `git log
# --all` away was stamped sanitized -- and the caller reads that stamp as licence
# to demote every git-history flag in the trajectory audit from HIGH to INFO.
# Failing loud instead is right even for a checkout with no history at all: the
# submission is extracted as `git diff __base`, so no __base means an empty patch
# and a silently unresolved instance.
GITDIR=$(git rev-parse --git-dir 2>/dev/null || true)
TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$GITDIR" ] || [ -z "$TOPLEVEL" ]; then
  echo "SANITIZE-FAIL: $REPO is not a git checkout (no git dir); the agent's" \
       "submission is extracted as 'git diff __base', so this cannot proceed"
  exit 1
fi
GITDIR=$(cd "$GITDIR" && pwd -P)
if [ "$(cd "$TOPLEVEL" && pwd -P)" != "$(pwd -P)" ]; then
  echo "SANITIZE-FAIL: $REPO is not the root of its own checkout" \
       "(git toplevel is $TOPLEVEL); refusing to sanitize a repository the" \
       "benchmark did not name"
  exit 1
fi

# 0b) working tree exactly at base_commit on a single local branch
git checkout -q -f -B __base "$BASE" 2>/dev/null || git reset -q --hard "$BASE"

# 1) drop EVERY ref except refs/heads/__base (git log --all walks them all)
git for-each-ref --format='%(refname)' \
  | grep -vx 'refs/heads/__base' \
  | while read -r ref; do git update-ref -d "$ref" 2>/dev/null || true; done

# 2) remove remotes (branch names can hint the fix; fetch could repull)
for r in $(git remote 2>/dev/null); do git remote remove "$r" 2>/dev/null || true; done

# 3) remove leftover tags (belt-and-suspenders)
git tag -l | xargs -r git tag -d >/dev/null 2>&1 || true

# 4) nuke the reflog (@{1} can resurrect future commits). $GITDIR, not .git: in a
# worktree layout the two are different directories and only one holds the logs.
rm -rf "$GITDIR/logs"
git reflog expire --expire=now --all >/dev/null 2>&1 || true

# 5) drop packed future refs + FETCH_HEAD/ORIG_HEAD/MERGE_HEAD pointers
rm -f "$GITDIR/packed-refs" "$GITDIR/FETCH_HEAD" "$GITDIR/ORIG_HEAD" \
      "$GITDIR/MERGE_HEAD" 2>/dev/null || true
git pack-refs --all 2>/dev/null || true

# 6) physically remove unreachable objects (even `git cat-file` cannot recover)
git gc --prune=now --quiet 2>/dev/null || git gc --prune=now 2>/dev/null || true

# 7) VERIFY: nothing but __base's ancestors is reachable
n_refs=$(git for-each-ref --format='%(refname)' | grep -vx 'refs/heads/__base' | wc -l | tr -d ' ')
n_remotes=$(git remote | wc -l | tr -d ' ')
n_tags=$(git tag -l | wc -l | tr -d ' ')
has_reflog=0; [ -d "$GITDIR/logs" ] && has_reflog=1
# `git log --all` must equal `git log __base`
all_count=$(git log --all --oneline 2>/dev/null | wc -l | tr -d ' ')
base_count=$(git log __base --oneline 2>/dev/null | wc -l | tr -d ' ')

if [ "$n_refs" = "0" ] && [ "$n_remotes" = "0" ] && [ "$n_tags" = "0" ] \
   && [ "$has_reflog" = "0" ] && [ "$all_count" = "$base_count" ]; then
  echo "SANITIZE-OK: only __base remains ($base_count commits, --all==base, no remotes/tags/reflog)"
  exit 0
fi
echo "SANITIZE-FAIL: refs=$n_refs remotes=$n_remotes tags=$n_tags reflog=$has_reflog all=$all_count base=$base_count"
exit 1
