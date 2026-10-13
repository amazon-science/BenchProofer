#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15987 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md
              bijection. `detectCollision` computes a membership test that looks
              only at each entry's canonical textual rendering (`Entry.text`),
              independent of whether the entry is stored as a plain text value
              or as a structured value (`Entry.wrapped`). There are no axioms in
              this bundle; the impl region is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour, transliterated verbatim from the patched
              hunk: `app_dir in [str(d) for d in fixture_dirs]`. The real repo
              values are arbitrary path-like entries — plain `str` or `pathlib`
              `Path` instances (the type the issue is about) — and `app_dir` is
              a `str` produced by `os.path.join`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys
from pathlib import Path, PurePosixPath

SEED = 15987
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean detectCollision, transliterated -----------
# An Entry is modeled as (text, wrapped). matchesText compares only `text`:
#   matchesText target entries = any(e.text == target for e in entries)
# The `wrapped` flag is immaterial to the result (the fix's behaviour).
def shadow_detect(target_text, entries):
    """detectCollision (target, entries): text-only membership.
    `entries` is a list of (text, wrapped) pairs; `target_text` is a str.
    The backward `while` fold of detectCollision computes exactly the
    left-to-right disjunction of (e.text == target_text)."""
    found = False
    for text, _wrapped in entries:
        found = (text == target_text) or found
    return found


# --- the oracle: patch.diff's behaviour, transliterated ----------------------
def oracle_detect(target_text, raw_entries):
    """The patched hunk, verbatim: `app_dir in [str(d) for d in fixture_dirs]`.
    `raw_entries` is a list of real path-like values (str or Path); `target_text`
    is the `app_dir` str."""
    return target_text in [str(d) for d in raw_entries]


def _rand_path_text(rng):
    """A canonical path-like string (POSIX). os.path.join / str(Path) leave such
    strings unchanged, so it is the canonical textual rendering of both forms."""
    parts = [rng.choice(["app", "fixtures", "data", "x", "abc", "dir1", "dir2"])
             for _ in range(rng.randint(1, 4))]
    return "/" + "/".join(parts)


def _build_case(rng):
    """Build (target_text, entries_for_shadow, raw_entries_for_oracle).

    raw_entries mixes plain `str` and `Path`-wrapped entries; the shadow entry
    carries the SAME canonical text (str(value)) and a `wrapped` flag recording
    whether the oracle value is a Path. The target is drawn so that collisions
    with both plain and wrapped entries occur frequently."""
    n = rng.randint(0, 6)
    raw = []
    shadow = []
    texts = [_rand_path_text(rng) for _ in range(max(1, n))]
    for k in range(n):
        text = rng.choice(texts)
        wrapped = rng.random() < 0.5
        value = Path(text) if wrapped else text
        raw.append(value)
        # mapping.md bijection: shadow text = str(value) (the canonical render).
        shadow.append((str(value), wrapped))
    # target: sometimes matches an existing entry's text, sometimes fresh.
    if texts and rng.random() < 0.7:
        target = rng.choice(texts)
    else:
        target = _rand_path_text(rng)
    # `app_dir` in the repo is produced by os.path.join (a str); model it so.
    target = os.path.join(*([p for p in target.split("/") if p] or ["x"]))
    target = "/" + target if not target.startswith("/") else target
    # keep shadow texts aligned with str(value) for the SAME target normalization
    return target, shadow, raw


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # boundary cases first (plan §4.1 step 4)
    boundary = []
    # empty collection
    boundary.append(("/app/fixtures", [], []))
    # single plain-str match
    boundary.append(("/app/fixtures", [("/app/fixtures", False)], ["/app/fixtures"]))
    # single Path-wrapped match (the issue: a Path duplicate must be detected)
    boundary.append(("/app/fixtures", [("/app/fixtures", True)], [Path("/app/fixtures")]))
    # Path-wrapped non-match
    boundary.append(("/app/fixtures", [("/other/fixtures", True)], [Path("/other/fixtures")]))
    # mix: plain non-match + Path match
    boundary.append(("/app/fixtures",
                     [("/x", False), ("/app/fixtures", True)],
                     ["/x", Path("/app/fixtures")]))
    # duplicate texts, one plain one wrapped
    boundary.append(("/d", [("/d", False), ("/d", True)], ["/d", Path("/d")]))

    for target, shadow, raw in boundary:
        count += 1
        s = bool(shadow_detect(target, shadow))
        o = bool(oracle_detect(target, raw))
        if s != o:
            disagreements.append((target, shadow, raw, s, o))

    for _ in range(N_FUZZ):
        count += 1
        target, shadow, raw = _build_case(rng)
        s = bool(shadow_detect(target, shadow))
        o = bool(oracle_detect(target, raw))
        if s != o:
            disagreements.append((target, shadow, raw, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for target, shadow, raw, s, o in disagreements:
            print("  target=%r shadow_entries=%r raw=%r shadow=%r oracle=%r"
                  % (target, shadow, raw, s, o))
        return 1
    print("G-CONF OK: R/I shadow of detectCollision agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
