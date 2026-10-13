#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-23412.

Band: pure-data (dash-pattern construction).

Refutes the R/I refinement leg (A3: the modeled render-time dash-pattern
construction `out = phase :: onoff` <-> the post-patch `_dash_pattern`
installed for the body of `Patch.draw`).

ORACLE CHOICE — why we transliterate the source line instead of running
`Patch.draw`:
  The patched construction lives inside `Patch.draw`, which requires a live
  Figure/Axes, a renderer, a bound draw-path function, and the full patch
  rendering pipeline; the value it builds is consumed by `gc.set_dashes(
  *self._dash_pattern)`. The behaviour under test is the pure construction of
  the dash pattern that is installed for the draw and handed to the back end.
  So, per the worker prompt, the ORACLE is the patched source line
  transliterated VERBATIM:
      _dash_pattern = (self._dash_pattern)        # == (offset, onoffseq)
  (from the gold-patched lib/matplotlib/patches.py, `Patch.draw`, the
  `cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern))` site). The
  dash pattern handed to the renderer is then `(offset, onoffseq)` — the
  patch's OWN offset (NOT the literal 0) and on/off sequence unchanged.

  The SHADOW is the modeled construction from Solution.lean's
  `renderDashPattern`: a single list whose head is the phase and whose tail is
  the on/off sequence. We bridge the model's `List Int` result back to the
  repo's `(offset, onoffseq)` tuple via mapping.md §1: `out[0]` <-> the offset
  component, `out[1:]` <-> the onoffseq component. We differential-test SHADOW
  vs ORACLE over fuzzed (offset, onoffseq) pairs. Exit 0 iff zero
  disagreements. stdlib only.

TYPE MODEL NOTE (mapping.md §2): Solution.lean models offset/onoffseq as exact
ints, because the discriminating behaviour is value-vs-zero of the offset (was
the stored offset carried through, or dropped to 0), independent of any
floating-point magnitude or scaling. The construction COPIES values; it never
arithmetically combines them, so observable-equality here is EXACT on the
constructed tuple (no ULP tolerance). We fuzz over both int and float offsets /
sequences to confirm the construction is uniform over the element type.

There are no axiomatized callees: `cbook._setattr_cm` (which installs the
value) and `gc.set_dashes` (which consumes it) are unchanged by the patch and
merely transport the constructed value; they are not part of the modeled
construction. Hence there is no axiom_check.py for this bundle.
"""
import random
import sys

SEED = 23412
N_FUZZ = 100_000


def shadow(offset, onoffseq):
    """renderDashPattern transliterated: the render-time dash pattern is the
    stored phase followed by the stored on/off sequence, in order.
    Mirrors `out = phase :: onoff` exactly, then bridged back to the repo's
    (offset, onoffseq) tuple via mapping.md (head=offset, tail=onoffseq)."""
    out = [offset] + list(onoffseq)        # phase :: onoff
    return (out[0], list(out[1:]))         # bridge: (head, tail)


def oracle(offset, onoffseq):
    """The patched source line, transliterated verbatim from
    lib/matplotlib/patches.py (gold-patched Patch.draw):
        _dash_pattern = (self._dash_pattern)   # == (offset, onoffseq)
    i.e. the patch's own offset and on/off sequence, unchanged."""
    dash_pattern = (offset, list(onoffseq))
    # gc.set_dashes(*self._dash_pattern) consumes (offset, onoffseq); we
    # observe exactly that installed pair.
    return (dash_pattern[0], list(dash_pattern[1]))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = []
    # Boundary / sentinel cases. The bug forced offset to 0, so offset==0 is the
    # degenerate (non-discriminating) case and nonzero offsets discriminate.
    sentinel_offsets = [0, 1, 6, 10, -1, -6, 1000, -1000]
    sentinel_seqs = [[], [6, 6], [0, 6, 6, 0], [1], [3, 3, 3, 3], [6.0, 6.0]]
    for off in sentinel_offsets:
        for seq in sentinel_seqs:
            cases.append((off, seq))
    # nonzero float offset (the phase shift the F2P test exercises with offset 6)
    cases.append((6, [6, 6]))
    cases.append((6.0, [6.0, 6.0]))

    def rand_seq():
        n = rng.randint(0, 8)
        if rng.random() < 0.5:
            return [rng.randint(-50, 50) for _ in range(n)]
        return [rng.uniform(-50.0, 50.0) for _ in range(n)]

    for _ in range(N_FUZZ):
        if rng.random() < 0.5:
            off = rng.randint(-1000, 1000)
        else:
            off = rng.uniform(-1000.0, 1000.0)
        cases.append((off, rand_seq()))

    for offset, onoffseq in cases:
        count += 1
        s = shadow(offset, onoffseq)
        o = oracle(offset, onoffseq)
        if s != o:
            disagreements.append((offset, onoffseq, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of renderDashPattern agrees with the patched "
          "source line on %d (offset, onoffseq) pairs (boundary + sentinel + "
          "fuzz, seed=%d), 0 disagreements. Offset passthrough (incl. nonzero "
          "phase 6) confirmed; cbook._setattr_cm / gc.set_dashes abstracted as "
          "value transport." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
