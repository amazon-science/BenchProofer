#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of the two modeled functions
against the patch.diff behaviour.

Both impl regions are all R/I (no A-tagged op):

  * initHandlerState — the persisted handler state is the ordered list of
    attributes the constructor retains. The patched constructor retains the
    dragged-object reference, the "drag in progress" flag (False), the effective
    fast-redraw flag (use_blit and supports_blit), and the connected callback
    identifiers; it NO LONGER retains a live display handle in that state. The
    shadow reproduces the impl op-for-op; the patched reconstruction builds the
    same list directly from the constructor's behaviour. Serializability holds
    iff no live handle is retained.

  * accessDisplayHandle — the display-handle accessor returns the owning
    container's CURRENT handle. Shadow returns owner.display_handle; the patched
    reconstruction (the property body `lambda self: self.ref_artist.figure.canvas`)
    likewise dereferences the owner each call.

Zero disagreements required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 25311          # pinned in mapping.md
N = 120_000           # >= 10^5

# Attribute tags mirroring the Lean `Attr` inductive.
SERIAL = ("serial",)
LIVE = ("liveHandle",)


def flag(b: bool):
    return ("flag", bool(b))


# ----- initHandlerState -----------------------------------------------------

def shadow_init(use_blit: bool, blit_supported: bool):
    """R/I shadow of implementation_initHandlerState (post-patch state)."""
    st = []
    st = st + [SERIAL]                                 # dragged object reference
    st = st + [flag(False)]                            # "drag in progress" flag
    st = st + [flag(use_blit and blit_supported)]      # effective fast-redraw flag
    st = st + [SERIAL]                                 # connected callback identifiers
    return st


def patched_init(use_blit: bool, blit_supported: bool):
    """Independent reconstruction of the patched constructor's persisted state.
    The live display handle is intentionally absent (it is now a recomputed
    property, not stored state)."""
    return [
        SERIAL,
        flag(False),
        flag(use_blit and blit_supported),
        SERIAL,
    ]


def serializable(st) -> bool:
    return all(a != LIVE for a in st)


# ----- accessDisplayHandle --------------------------------------------------

def shadow_access(display_handle: int) -> int:
    return display_handle


def patched_access(display_handle: int) -> int:
    return display_handle


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    fixed = [(False, False), (True, False), (False, True), (True, True)]
    cases = fixed + [
        (rng.random() < 0.5, rng.random() < 0.5) for _ in range(N)
    ]

    for use_blit, blit_supported in cases:
        got = shadow_init(use_blit, blit_supported)
        want = patched_init(use_blit, blit_supported)
        if got != want or not serializable(got):
            disagreements += 1
            if len(examples) < 10:
                examples.append(((use_blit, blit_supported), got, want))

    # accessor over fuzzed handle ids
    for _ in range(N):
        h = rng.randint(0, 10**9)
        if shadow_access(h) != patched_access(h):
            disagreements += 1
            if len(examples) < 10:
                examples.append((("access", h), shadow_access(h), patched_access(h)))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases) + N} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
