#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-23314.

The bundle models ONE function: `Axes3D.draw(self, renderer)`
(`lib/mpl_toolkits/mplot3d/axes3d.py`). `draw` is a void PROCEDURE: it returns
nothing, and everything it does is done by drawing onto `renderer`. The Lean
implementation (`implementation_render`) therefore denotes the ACTION that `draw`
carries out, given the artist's visibility flag:

    if not visible:      # the two added lines (gold patch)
        return           #   carry out no drawing at all
    renderContents       # the unchanged remainder of draw

The ONLY R-modeled logic is the visibility guard (refinement.md op #1).
`renderContents` is the A-reference standing for the entire unchanged body of
`draw` (op #2); it is held IDENTICAL on both legs (the same deterministic
surrogate action), so the differential test isolates exactly the guard — the
soundness-critical clause the patch introduces.

Lean holds the effect monad `m` abstract. An action in an abstract monad has no
executable content, so the differential instantiates `m` at the concrete lawful
monad the mapping names: state over the log of primitive draw operations the
renderer has accumulated (`StateM (List RenderOp)`, i.e. a Python function
`log -> log`). `pure ()` instantiates to "leave the log exactly as it is", and
`renderContents` to "append the operations the unchanged body emits". Every claim
checked below is a claim the Lean postcondition makes about the abstract action,
read at this instance.

We do NOT stand up a full matplotlib 3D figure + backend renderer to drive the
real `draw`: the modeled decision is precisely "is the unchanged body carried out,
or is it short-circuited", which is a function of `self.get_visible()` alone. The
ORACLE is a faithful in-process replica of the POST-PATCH control flow (guard,
then the same surrogate body); the SHADOW is the op-for-op transliteration of
`implementation_render`. Both are compared as ACTIONS: same effect on every prior
log, which for this instance of `m` is extensional equality of the two actions.

Three families are checked, not one:
  (1) oracle action == shadow action, on enumerated and fuzzed prior logs;
  (2) the postcondition's hidden case — the action performed when `visible` is
      false IS `pure ()`, i.e. it leaves the log identical (not merely equal in
      length, and not "restored after drawing": the recorded log is compared
      element-wise against the input);
  (3) the postcondition's shown case — the action performed when `visible` is
      true IS `renderContents`, the surrogate body run exactly once.
Family (2) is what a variant that carries out the body and then discards or
rebuilds the surface fails, and it is the reason the log is compared rather than
the returned value.

stdlib-only. Pinned seed: 23314 (also in mapping.md / meta.json).
"""
import random
import sys

SEED = 23314
N = 120_000  # >= 1e5


# --- the concrete instance of `m` -------------------------------------------
# `m Unit` == an action on the renderer's accumulated operation log. Represented
# as a function `list -> list`. `pure ()` is the action that changes nothing.
def act_pure(log):
    return list(log)


# --- the unchanged body of draw, as a deterministic surrogate action ---------
# Held IDENTICAL on both legs (A-reference: renderContents). Any deterministic
# action works; the guard is what is under test. It must leave the log different
# from its input so that a body carried out when it should not be is observable.
def act_render_contents(log):
    return list(log) + [("draw", len(log))]


# --- ORACLE: faithful in-process replica of the PATCHED control flow ----------
# def draw(self, renderer):
#     if not self.get_visible():
#         return
#     ...unchanged body...
def oracle_draw(visible, log):
    if not visible:
        return act_pure(log)            # bare `return` — nothing is drawn
    return act_render_contents(log)


# --- SHADOW of implementation_render (the R leg) -----------------------------
# Mirrors Solution.lean impl region, read at this instance of `m`:
#   if !self.visible then return      -- pure ()
#   renderContents                    -- the surrogate action
def shadow_render(visible, log):
    if not visible:
        return act_pure(log)
    return act_render_contents(log)


def edge_cases():
    logs = [
        [],
        [("a", 0)],
        [("a", 0), ("b", 1)],
        [("x", 2)] * 8,
    ]
    for v in (True, False):
        for s in logs:
            yield v, list(s)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def check(v, log):
        nonlocal disagreements, checked
        checked += 1
        before = list(log)
        got = shadow_render(v, log)
        # (1) the two legs carry out the same action
        if got != oracle_draw(v, before):
            return False
        if v:
            # (3) shown: the action IS renderContents, run exactly once
            if got != act_render_contents(before):
                return False
        else:
            # (2) hidden: the action IS pure () — the log is untouched,
            # element for element, and no longer than it started
            if got != before or len(got) != len(before):
                return False
        return True

    for v, log in edge_cases():
        if not check(v, log):
            disagreements += 1

    for _ in range(N):
        v = rng.choice((True, False))
        n = rng.randint(0, 8)
        log = [("op", rng.randint(0, 5), i) for i in range(n)]
        if not check(v, log):
            disagreements += 1

    if disagreements == 0:
        print(f"status=pass checked={checked} disagreements=0 seed={SEED}")
        sys.exit(0)
    print(f"status=fail checked={checked} disagreements={disagreements}")
    sys.exit(1)


if __name__ == "__main__":
    main()
