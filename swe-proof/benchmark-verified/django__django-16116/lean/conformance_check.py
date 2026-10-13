#!/usr/bin/env python3
r"""G-CONF — differential test of the R/I shadow of
implementation_processChanges against the patch.diff behaviour (the patched
control flow of makemigrations Command.handle's "changes" arm).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: with no detected changes, emit nothing and finish;
otherwise, in verification-only mode, request a non-zero exit BEFORE emitting any
output; otherwise emit exactly one form of migration output (merge into the
latest migration when requested, else a fresh migration file) and finish.

We diff that against an INDEPENDENT oracle that executes the EXACT patched Python
control flow as a sequence of recorded effects (mirroring the gold patch's
hoisted `if check_changes: sys.exit(1)` ahead of the writers), observing which
writer ran and what exit status was requested. The observed
`(wrote_to_last, wrote_new, exit_code)` triple is compared to the shadow's
`(wroteToLast, wroteNew, exitCode)`.

Zero disagreements required over >=10^5 fuzzed inputs (all 8 Boolean
combinations). stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16116          # pinned in mapping.md
N = 130_000           # >= 10^5


def shadow(has_changes: bool, check_only: bool, merge_into_last: bool):
    """R/I shadow of implementation_processChanges (op-for-op).

    Returns (wrote_to_last: bool, wrote_new: bool, exit_code: int|None)."""
    wrote_to_last = False
    wrote_new = False
    exit_code = None
    if not has_changes:
        return (wrote_to_last, wrote_new, exit_code)
    if check_only:
        exit_code = 1
        return (wrote_to_last, wrote_new, exit_code)
    if merge_into_last:
        wrote_to_last = True
    else:
        wrote_new = True
    return (wrote_to_last, wrote_new, exit_code)


def oracle(has_changes: bool, check_only: bool, merge_into_last: bool):
    """Run the EXACT patched control flow as recorded effects.

    Mirrors makemigrations.handle's `else:` (changes-detected) arm after the gold
    patch:

        else:
            if check_changes:
                sys.exit(1)
            if self.update:
                self.write_to_last_migration_files(changes)
            else:
                self.write_migration_files(changes)

    Returns (wrote_to_last: bool, wrote_new: bool, exit_code: int|None)."""
    effects = {"wrote_to_last": False, "wrote_new": False, "exit_code": None}

    class _Exit(Exception):
        def __init__(self, code):
            self.code = code

    def sys_exit(code):
        raise _Exit(code)

    def write_to_last_migration_files():
        effects["wrote_to_last"] = True

    def write_migration_files():
        effects["wrote_new"] = True

    try:
        if not has_changes:
            pass                                  # "No changes detected" branch
        else:
            if check_only:                        # if check_changes:
                sys_exit(1)                        #     sys.exit(1)
            if merge_into_last:                   # if self.update:
                write_to_last_migration_files()
            else:                                 # else:
                write_migration_files()
    except _Exit as e:
        effects["exit_code"] = e.code

    return (effects["wrote_to_last"], effects["wrote_new"], effects["exit_code"])


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # All 8 Boolean combinations exhaustively first.
    fixed = [(h, c, m)
             for h in (False, True)
             for c in (False, True)
             for m in (False, True)]
    cases = list(fixed)
    for _ in range(N):
        cases.append((rng.choice([False, True]),
                      rng.choice([False, True]),
                      rng.choice([False, True])))

    for h, c, m in cases:
        got = shadow(h, c, m)
        want = oracle(h, c, m)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((h, c, m, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for h, c, m, g, w in examples:
            print(f"  has_changes={h} check_only={c} merge={m} shadow={g} oracle={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
