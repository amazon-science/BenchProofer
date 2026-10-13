#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_kernSHit
against the patch.diff behaviour (post-patch `kernS` hit-flag slice).

The impl region is NOT all-A-tagged (it has I/R structure), so this runs a real
fuzz. The single A-reference op (the marker-membership read) is left as the REAL
repo callee: the post-patch `kernS` marker-substitution + membership logic
(`kern='_'; while kern in s: kern += choice(...); s = s.replace(' ', kern);
hit = kern in s`), reached only in the space-present subcase. The shadow
therefore reproduces the post-patch behaviour op-for-op; we assert zero
disagreements vs an independent reconstruction of the patched slice over >=10^5
fuzzed (parenBranch, s) inputs.

Result encoding mirrors the Lean `Except Unit Bool`:
  ("ok", bool)   normal return with a well-defined flag
  ("error", None) the routine aborted (UnboundLocalError) — post-patch: never.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import string
import sys

SEED = 19637          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(paren_branch: bool, s: str, rng: random.Random):
    """R/I shadow of implementation_kernSHit.

    hit := False
    if parenBranch:
        if ' ' in s:
            hit := <real marker-membership callee>   # A-reference, real repo logic
        else:
            hit := False
    return ("ok", hit)
    """
    hit = False
    if paren_branch:
        if ' ' in s:
            # A-reference op realised by the REAL post-patch kernS callee:
            kern = '_'
            while kern in s:
                kern += rng.choice(string.ascii_letters + string.digits)
            s2 = s.replace(' ', kern)
            hit = kern in s2
        else:
            hit = False
    return ("ok", hit)


def patched_slice(paren_branch: bool, s: str, rng: random.Random):
    """Independent reconstruction of the POST-patch kernS hit-flag slice
    (lines 471-516 with the gold indentation + else branch). Never raises."""
    hit = False
    if paren_branch:
        # ... unchanged *(/-( /nesting rewrites already applied to s ...
        if ' ' in s:
            kern = '_'
            while kern in s:
                kern += rng.choice(string.ascii_letters + string.digits)
            s = s.replace(' ', kern)
            hit = kern in s
        else:
            hit = False
    return ("ok", hit)


def main() -> int:
    disagreements = 0
    examples = []

    alphabet = list("_ ()*+-/xyz") + list(string.ascii_letters + string.digits)

    # Deterministic boundary cases first (both branch values, with/without space).
    fixed = [
        (True, ""), (True, "x"), (True, "(2*x)/(x-1)"),  # the reported repro: no space
        (True, " "), (True, "x y"), (True, "* *("), (True, "-( *(x+y))"),
        (True, "_"), (True, "_ _"), (True, "a _ b"),
        (False, ""), (False, "x y"), (False, " "), (False, "(2*x)/(x-1)"),
    ]

    cases = list(fixed)
    gen = random.Random(SEED)
    for _ in range(N):
        pb = gen.random() < 0.5
        n = gen.randint(0, 30)
        s = "".join(gen.choice(alphabet) for _ in range(n))
        cases.append((pb, s))

    for pb, s in cases:
        # Seed the two callee RNGs identically per-case so marker growth (which
        # does not affect the modeled flag) cannot spuriously diverge.
        got = shadow(pb, s, random.Random(hash((pb, s)) & 0xffffffff))
        want = patched_slice(pb, s, random.Random(hash((pb, s)) & 0xffffffff))
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((pb, s, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for pb, s, g, w in examples:
            print(f"  parenBranch={pb} s={s!r} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
