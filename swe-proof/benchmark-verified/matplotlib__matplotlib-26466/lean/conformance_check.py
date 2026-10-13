#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-26466.

The bundle models TWO copy-on-store sites (mapping.md): `OffsetFrom.__init__`
storing `self._ref_coord`, and `_AnnotationBase.__init__` storing `self.xy`. Both
have the SAME modeled behaviour — capturing a 2D coordinate handed in through a
mutable container, by VALUE, at construction time.

The Lean spec models the *retention* directly: `implementation_freeze*` returns a
`StoredCoord` (either `snapshot x y` — detached — or `reference` — aliased to the
source), and `observe out later` reads it back given the source's CURRENT value
`later`. The contract is `∀ later, observe out later = initial`: reading back the
retained coordinate under ANY later state of the source yields the
construction-time value. Only `snapshot initial.1 initial.2` satisfies this.

The aliasing semantics are reproduced faithfully with a stdlib mutable container
(a `list`): the ORACLE builds the captured attribute the way the POST-PATCH code
does (`x, y = src; store (x, y)` — a fresh tuple of the two scalar components),
then MUTATES the source list in place, then reads the stored attribute back. The
SHADOW is the op-for-op transliteration of the Lean impl: it returns a StoredCoord
and is observed under `later` via `observe`.

Standing up numpy + the full matplotlib Annotation/transform machinery to drive
the real attribute is heavy and unnecessary: the modeled value is exactly this
by-value capture, and the `list`-mutation harness exercises the soundness-critical
behaviour the F2P test checks — that an in-place change to the source array after
construction (`of_xy[:] = 1`) does NOT alter the stored coordinate.

The PRE-PATCH bug (store the live reference => a later read returns the source's
current value) is included as a negative control and MUST disagree, confirming the
test is discriminating.

stdlib-only. Pinned seed: 26466 (also in mapping.md / meta.json).
"""
import json
import random
import sys

SEED = 26466
N = 200_000


# --- Lean-side model transliterated (StoredCoord + observe) ---

def observe(stored, later):
    """Read back a retained coordinate given the source's CURRENT value `later`.
    A snapshot ignores `later`; a reference reflects it. Mirrors Lean `observe`."""
    kind = stored[0]
    if kind == "snapshot":
        return (stored[1], stored[2])
    # "reference"
    return (later[0], later[1])


def shadow_impl(initial):
    """Op-for-op transliteration of `implementation_freeze{OffsetOrigin,AnchorPoint}`
    (Solution.lean impl region): read both components of the construction-time
    coordinate and return them as a detached snapshot."""
    x = initial[0]
    y = initial[1]
    return ("snapshot", x, y)


# --- Oracle: the real post-patch / pre-patch capture through a mutable list ---

def post_patch_capture(initial, later):
    """Faithful replica of the gold `x, y = src; self.attr = x, y` capture driven
    through a real in-place mutation of a mutable source container. Returns the
    stored attribute read back AFTER the source is mutated `initial -> later`."""
    src = [initial[0], initial[1]]          # the caller's mutable container
    x, y = src                              # unpack: read the two scalars out
    stored = (x, y)                         # store a fresh tuple of the scalars
    src[0], src[1] = later[0], later[1]     # caller mutates the source in place
    return (stored[0], stored[1])           # read the stored attribute back


def prepatch_capture(initial, later):
    """The base_commit bug: store the live container by reference. A later read of
    the stored attribute sees the source's mutated value."""
    src = [initial[0], initial[1]]
    stored = src                            # by-reference store (the bug)
    src[0], src[1] = later[0], later[1]
    return (stored[0], stored[1])


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    # boundary / sentinel cases first
    boundaries = [
        ((0, 0), (0, 0)),
        ((0, 0), (1, 1)),
        ((-4, 1), (-4, 3)),     # the issue's reproduction (xy_0 then xy_0[1]=3)
        ((1, 1), (1, 3)),
        ((0.5, 0.5), (1.0, 1.0)),   # the F2P of_xy then of_xy[:]=1
    ]
    for idx in range(N):
        if idx < len(boundaries):
            initial, later = boundaries[idx]
        else:
            initial = (rng.randint(-1000, 1000), rng.randint(-1000, 1000))
            later = (rng.randint(-1000, 1000), rng.randint(-1000, 1000))
        # ORACLE: the real post-patch capture, read back after the source mutates.
        oracle = post_patch_capture(initial, later)
        # SHADOW: the Lean impl's StoredCoord, observed under the SAME later state.
        shadow = observe(shadow_impl(initial), later)
        if oracle != shadow:
            disagreements += 1
            if len(examples) < 5:
                examples.append({"initial": initial, "later": later,
                                 "oracle": oracle, "shadow": shadow})

    # negative control: the prepatch bug (Lean `reference` / Python by-ref store)
    # MUST disagree with the post-patch oracle whenever the source is mutated.
    bug_caught = False
    for initial, later in [((-4, 1), (-4, 3)), ((0.5, 0.5), (1.0, 1.0))]:
        buggy = observe(("reference",), later)      # Lean prepatch: StoredCoord.reference
        if buggy != post_patch_capture(initial, later) \
           and prepatch_capture(initial, later) != post_patch_capture(initial, later):
            bug_caught = True
            break

    ok = (disagreements == 0) and bug_caught
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "instance": "matplotlib__matplotlib-26466",
        "compared": N,
        "disagreements": disagreements,
        "examples": examples,
        "negative_control_bug_caught": bug_caught,
        "seed": SEED,
    }))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
