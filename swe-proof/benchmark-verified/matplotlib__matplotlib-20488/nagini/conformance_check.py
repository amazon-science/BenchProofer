#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20488
(nagini).

SHADOW: the impl region of model.py (`sanitized_lower_bound`), copied verbatim
below with the single contract call (the else-branch `Assert`) stripped. There
are no PSeq values, no @Pure helpers, and no @ContractOnly callees in this
bundle; the model IS Python and copies over directly.

ORACLE: the REAL patched repo code the model models per mapping.md — the
lower-bound sanitisation inside `matplotlib.image._ImageBase._make_image`.
The gate applies patch.diff to /testbed before this script runs (this script
does NOT apply it); PYTHONPATH=/testbed makes the patched module importable.
Because the modeled behaviour is an inline statement of a large rendering
method rather than a standalone function, the oracle is obtained by locating
that exact statement in the patched module's AST (the unique conditional in
`_make_image` whose test consults the logarithmic-normalization type) and
executing the REAL statement object — the repo's own code, byte-for-byte, not
a transliteration — over controlled bindings of the names it reads
(`self.norm`, `s_vmin`, `scaled_dtype`, `np`, `mcolors`).

An end-to-end grounding leg additionally drives the FULL `_make_image`
pipeline through a live headless render: an image under a logarithmic
normalization whose data range is extreme enough that the resampling round
trip lands the working lower bound at or below zero. The lower bound the
normalization actually receives (observed inside its __call__, where the
sanitised value is installed) must be strictly positive and the render must
complete — the exact guarantee the model's postcondition pins.

TYPE BRIDGE (mapping.md section 2):
  is_log      <-> isinstance(self.norm, mcolors.LogNorm): realised with real
                  norm instances — a genuine LogNorm for True; Normalize /
                  NoNorm / PowerNorm (non-logarithmic siblings) for False.
  lower_bound <-> `s_vmin`, a float (Python floats plus numpy float32/float64
                  scalars, the carriers `vrange` actually yields).
  eps         <-> `np.finfo(scaled_dtype).eps` for the working dtypes
                  `_make_image` selects (float32, float64); the shadow's eps
                  parameter is instantiated at exactly those real values while
                  the oracle statement computes them itself from scaled_dtype.

INPUT DOMAIN: Requires demands eps > 0 (holds for both real finfo values) and
a lower bound that compares against zero, i.e. any non-NaN float (NaN falsifies
both disjuncts, so it is outside the modeled domain and excluded). Generation
covers the sign/zero boundary densely: exact zero, negative zero, tiny and
subnormal magnitudes of both signs, the eps values themselves and their
neighbourhoods, large magnitudes, both infinities, plus wide-scale fuzz.

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz inputs.
Pinned fuzz seed: 20488.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + matplotlib (the repo under test) only.
"""
import ast
import inspect
import json
import os
import random
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp())

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.image as mimage

SEED = 20488
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract call stripped -----------

def sanitized_lower_bound(is_log, lower_bound, eps):
    result = lower_bound
    if is_log and lower_bound <= 0.0:
        result = eps
    else:
        # (proof-annotation Assert stripped; branch body is a no-op)
        pass
    return result


# --- oracle: the real sanitisation statement, extracted from the patched AST --

class _SelfProxy(object):
    """Carrier for the single attribute the statement reads off self."""
    def __init__(self, norm):
        self.norm = norm


def extract_real_statement():
    """Locate, in the PATCHED matplotlib.image source, the unique conditional
    of `_ImageBase._make_image` whose test consults the logarithmic-
    normalization type, and compile that REAL statement for direct execution.
    """
    src = inspect.getsource(mimage)
    tree = ast.parse(src)
    func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "_ImageBase":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_make_image":
                    func = item
    if func is None:
        raise RuntimeError("could not locate _ImageBase._make_image in the "
                           "patched module source")
    hits = [n for n in ast.walk(func)
            if isinstance(n, ast.If) and "LogNorm" in ast.dump(n.test)]
    if len(hits) != 1:
        raise RuntimeError("expected exactly one lower-bound guard in "
                           "_make_image, found %d" % len(hits))
    mod = ast.Module(body=[hits[0]], type_ignores=[])
    return compile(mod, "<real _make_image sanitisation>", "exec")


def real_sanitize(code, norm, s_vmin, scaled_dtype):
    """Execute the real patched statement over one binding; return the
    sanitised lower bound it leaves in s_vmin."""
    ns = {"self": _SelfProxy(norm), "mcolors": mcolors, "np": np,
          "scaled_dtype": scaled_dtype, "s_vmin": s_vmin}
    exec(code, ns)
    return ns["s_vmin"]


# --- end-to-end grounding: the full pipeline hands the norm a positive vmin ---

def end_to_end_ground():
    """Render, headless, an image under a logarithmic normalization whose data
    range is extreme enough that the resampled working range reaches zero or
    below; observe the lower bound the normalization is actually called with.
    Post-patch it must be strictly positive and the render must complete."""
    import matplotlib.pyplot as plt

    seen = []

    class ProbeNorm(mcolors.LogNorm):
        def __call__(self, value, clip=None):
            seen.append(self.vmin)
            return super(ProbeNorm, self).__call__(value, clip)

    data = np.full((5, 5), -1.0)
    data[0:2, :] = 1e20
    fig, ax = plt.subplots()
    try:
        ax.imshow(data, norm=ProbeNorm(vmin=100.0, vmax=float(data.max())),
                  interpolation="nearest")
        fig.canvas.draw()
    finally:
        plt.close(fig)
    if not seen:
        return "END-TO-END: the normalization was never invoked during the render"
    bad = [v for v in seen if not (float(v) > 0.0)]
    if bad:
        return ("END-TO-END DISAGREEMENT: the normalization received a "
                "non-positive lower bound %r (model guarantees > 0)" % (bad,))
    return None


# --- differential driver -------------------------------------------------------

def check_one(code, norm, is_log, s_vmin, scaled_dtype):
    eps = float(np.finfo(scaled_dtype).eps)
    shadow = sanitized_lower_bound(is_log, float(s_vmin), eps)
    real = real_sanitize(code, norm, s_vmin, scaled_dtype)
    # both sides only ever SELECT one of their inputs (no arithmetic), so
    # exact numeric equality is the right observable; NaN is outside the
    # modeled domain and never generated.
    if not (float(shadow) == float(real)):
        return ("DISAGREEMENT at is_log=%r s_vmin=%r (%s) scaled_dtype=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (patched statement) = %r"
                % (is_log, s_vmin, type(s_vmin).__name__, scaled_dtype,
                   shadow, real))
    return None


def boundary_vmins():
    eps32 = float(np.finfo(np.float32).eps)
    eps64 = float(np.finfo(np.float64).eps)
    vals = [0.0, -0.0, 1.0, -1.0,
            1e-300, -1e-300, 5e-324, -5e-324,      # tiny / smallest subnormal
            eps32, eps64, -eps32, -eps64,
            eps32 / 2.0, eps64 / 2.0,
            1e20, -1e20, 1e308, -1e308,
            float("inf"), float("-inf")]
    out = list(vals)
    for v in vals:
        out.append(np.float64(v))
        f32 = np.float32(v)
        if not np.isnan(f32):
            out.append(f32)
    return out


def main():
    try:
        code = extract_real_statement()
    except RuntimeError as exc:
        print("G-CONF ERROR: %s" % (exc,))
        return 1

    err = end_to_end_ground()
    if err:
        print(err)
        return 1

    log_norms = [mcolors.LogNorm(), mcolors.LogNorm(vmin=1.0, vmax=10.0)]
    nonlog_norms = [mcolors.Normalize(), mcolors.NoNorm(),
                    mcolors.PowerNorm(gamma=2.0)]
    dtypes = [np.float32, np.float64]

    checked = 0
    n_boundary = 0
    for v in boundary_vmins():
        for dt in dtypes:
            for norm in log_norms:
                err = check_one(code, norm, True, v, dt)
                if err:
                    print(err)
                    return 1
                checked += 1
                n_boundary += 1
            for norm in nonlog_norms:
                err = check_one(code, norm, False, v, dt)
                if err:
                    print(err)
                    return 1
                checked += 1
                n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        is_log = rng.random() < 0.5
        norm = rng.choice(log_norms if is_log else nonlog_norms)
        dt = rng.choice(dtypes)
        kind = rng.randint(0, 4)
        if kind == 0:
            v = rng.choice([0.0, -0.0])
        elif kind == 1:
            v = -rng.random() * (10.0 ** rng.randint(-320, 300))
        elif kind == 2:
            v = rng.random() * (10.0 ** rng.randint(-320, 300))
        elif kind == 3:
            v = rng.uniform(-5.0, 5.0)
        else:
            # numpy scalar carriers (what the working range actually yields)
            base = rng.uniform(-10.0, 10.0)
            v = np.float32(base) if rng.random() < 0.5 else np.float64(base)
            if np.isnan(v):
                v = np.float64(0.0)
        err = check_one(code, norm, is_log, v, dt)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched sanitisation statement on "
          "%d inputs (%d boundary + %d fuzz, seed %d); end-to-end render "
          "grounding passed (log normalization received a strictly positive "
          "lower bound)." % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
