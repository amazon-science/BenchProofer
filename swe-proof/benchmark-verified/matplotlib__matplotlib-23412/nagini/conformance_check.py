#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-23412 (nagini).

SHADOW: the impl region of model.py (`render_dash_pattern`), copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The model IS Python: no transliteration. The axioms and pure regions are
empty, so there are no @ContractOnly callees and nothing else to embed.

ORACLE: the REAL patched repo function the model models per mapping.md —
`matplotlib.patches.Patch.draw`, specifically the dash pattern it puts in
effect for the duration of the draw and hands to the drawing back end. The
gate applies patch.diff to /testbed before this script runs
(PYTHONPATH=/testbed). The observation harness is a minimal RendererBase
subclass: `Patch.draw` obtains a graphics context via `renderer.new_gc()` and
configures it (including `gc.set_dashes(...)` with the in-effect dash
pattern) before calling `renderer.draw_path(gc, ...)`; the harness records
the gc, and `gc.get_dashes()` returns exactly the (offset, on/off list) pair
that was handed to the back end — the value the model's Result() carries.

Type bridge (mapping.md section 2):
  phase : int          <-> the stored dash offset self._dash_pattern[0]
                           (a float in the repo; integer-valued floats are
                           exact, and the tested behaviour — the stored
                           offset carried through unchanged — is value-exact,
                           so comparison is exact equality on float(phase))
  onoff : List[int]    <-> the stored on/off sequence self._dash_pattern[1],
                           element-wise (integer-valued floats, exact); the
                           repo's None (solid line) is bridged to the empty
                           list (mapping.md: empty onoff models the solid /
                           degenerate case)
  Result() : List[int] <-> head = the offset handed to the back end,
                           tail = the on/off sequence handed to the back end

The model's inputs ARE the two components of the patch object's stored
`_dash_pattern` (mapping.md section 1), so the harness binds them by
installing `(phase, onoff)` as the patch's stored dash pattern directly —
this bypasses the unmodeled linestyle-normalisation/scaling front end
(`set_linestyle`/`set_linewidth`), which is exactly the modeling boundary:
the modeled construction starts from the already-stored pair.

Requires-satisfying domain: the model requires only read access to `onoff`.
The bridged repo-side domain (a stored on/off ink-length sequence) is
non-negative elements with at least one positive element when non-empty
(the back end's gc.set_dashes validates exactly that), plus the empty/solid
case; the offset is unconstrained (zero, positive, negative all pass
through). Fuzz draws from that domain; boundaries cover phase 0 / nonzero /
negative / large, empty and None on/off, zero elements inside the sequence,
odd and even lengths, and single-element sequences.

>= 1e5 Requires-satisfying inputs: 26 boundary phases x 12 boundary on/off
shapes (the empty shape run through both its list and None repo carriers)
= 338 boundary cases + 100,000 fuzz cases = 100,338 total.
Pinned fuzz seed: 23412.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (matplotlib/numpy come from /testbed).
"""
import json
import random
import sys

SEED = 23412
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def render_dash_pattern(phase, onoff):
    result = [phase]
    i = 0
    while i < len(onoff):
        result.append(onoff[i])
        i = i + 1
    return result


# --- oracle harness: observe the dash pattern Patch.draw hands to the back end

def make_harness():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backend_bases import RendererBase
    from matplotlib.patches import Rectangle

    class CapturingRenderer(RendererBase):
        """Records the graphics contexts the draw hands to draw_path, so the
        in-effect dash pattern is observable via gc.get_dashes()."""

        def __init__(self):
            super().__init__()
            self.gcs = []

        def new_gc(self):
            gc = super().new_gc()
            self.gcs.append(gc)
            return gc

        def draw_path(self, gc, path, transform, rgbFace=None):
            pass

    patch = Rectangle((0, 0), 1, 1)

    def real_rendered_dashes(phase, onoff_repo):
        """Install (phase, onoff_repo) as the patch's stored dash pattern,
        run the REAL patched Patch.draw, and return the (offset, on/off)
        pair handed to the back end."""
        patch._dash_pattern = (phase, onoff_repo)
        renderer = CapturingRenderer()
        patch.draw(renderer)
        if len(renderer.gcs) != 1:
            raise RuntimeError("expected exactly one gc per draw, got %d"
                               % len(renderer.gcs))
        return renderer.gcs[0].get_dashes()

    return real_rendered_dashes


def check_case(real_rendered_dashes, phase, onoff, solid_as_none):
    """Run shadow and oracle on one (phase, onoff) input; return an error
    string on disagreement, else None. solid_as_none exercises the repo-side
    None (solid) carrier for the empty on/off bridge."""
    onoff_repo = None if solid_as_none else list(onoff)
    shadow = render_dash_pattern(phase, list(onoff))
    real_offset, real_onoff = real_rendered_dashes(phase, onoff_repo)

    inp = ("phase=%r onoff=%r (repo-side onoff carrier=%r)"
           % (phase, onoff, onoff_repo))
    # bridge the repo's None (solid) back to the empty tail
    real_tail = [] if real_onoff is None else list(real_onoff)
    ok = (float(real_offset) == float(shadow[0])
          and len(real_tail) == len(shadow) - 1
          and all(float(a) == float(b)
                  for a, b in zip(real_tail, shadow[1:])))
    if not ok:
        return ("DISAGREEMENT\n  input: %s\n"
                "  shadow=%r (head=offset, tail=on/off)\n"
                "  real=(offset=%r, onoff=%r)"
                % (inp, shadow, real_offset, real_onoff))
    return None


BOUNDARY_PHASES = [0, 1, -1, 2, 3, 5, 6, 7, 10, 13, 20, 100, 999, 10 ** 6,
                   -6, -100, 4, 8, 9, 11, 12, 15, 50, 64, 128, 255]

BOUNDARY_ONOFFS = [
    [],                # empty (degenerate / solid boundary)
    [10, 10],          # the classic even on/off pair
    [1, 1],
    [7],               # single element (odd length)
    [3, 1, 1, 1],
    [5, 0],            # zero off-length
    [0, 5],            # zero on-length (a positive element exists)
    [1, 2, 3],         # odd length
    [1000, 1],         # large ink length
    [1, 1000],
    [2, 2, 2, 2, 2, 2],
    [9, 0, 0, 4],      # interior zeros
]


def fuzz_onoff(rng):
    """A repo-domain on/off sequence: non-negative ints, at least one
    positive when non-empty."""
    n = rng.randint(0, 8)
    if n == 0:
        return []
    seq = [rng.randint(0, 50) for _ in range(n)]
    if not any(seq):
        seq[rng.randrange(n)] = rng.randint(1, 50)
    return seq


def main():
    real_rendered_dashes = make_harness()

    checked = 0
    for phase in BOUNDARY_PHASES:
        for onoff in BOUNDARY_ONOFFS:
            solid_variants = (False, True) if not onoff else (False,)
            for solid_as_none in solid_variants:
                err = check_case(real_rendered_dashes, phase, onoff,
                                 solid_as_none)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        phase = rng.choice((0, rng.randint(-1000, 1000),
                            rng.randint(0, 20)))
        onoff = fuzz_onoff(rng)
        solid_as_none = (not onoff) and rng.random() < 0.5
        err = check_case(real_rendered_dashes, phase, onoff, solid_as_none)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == dash pattern the real patched "
          "Patch.draw hands to the back end on %d inputs "
          "(%d boundary + %d fuzz cases, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; no "
                                "axiomatized callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
