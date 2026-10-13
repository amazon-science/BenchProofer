#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-12973.

This bundle has NO consumed axiom and NO `:|`-stub. Its two kind-A constructs
are deep-model REFERENCES (Solution.lean axioms region):

    prepareInPlace : Array Int -> Array Int -> Array Int
    searchInPlace  : Array Int -> Array Int -> Array Int

They model the transforms that the TWO unchanged numeric routines
`LassoLarsIC.fit` hands the caller's `X` buffer to apply to the buffer they are
handed:

    routine 1  sklearn.linear_model.base._preprocess_data(X, y, fit_intercept,
               normalize, copy)                                  (base.py:93)
    routine 2  sklearn.linear_model.least_angle.lars_path(X, y, Gram=...,
               copy_X=..., ...)                            (least_angle.py:31)

WHAT G-AX MUST CHECK (SPEC_GUIDE 0.7): an A-reference is about a callee the
changed function CALLS but does NOT change. Both routines above are unchanged by
the patch (the patch edits only `fit`'s parameter default, the resolution it
performs, and which value it forwards). We therefore validate the model against
those two REAL callees exercised DIRECTLY, never via `LassoLarsIC.fit` -- that is
the function under spec, and the choice-resolution it performs is the *changed*
op, so axiomatizing it would be the forbidden over-claim. Because both callees
are unchanged, the laws below hold identically on the in-tree (pre-patch) source
G-AX runs against, independent of patch application.

TWO OBSERVABLE BUFFERS. `fit` names one buffer `X`, but two distinct buffers are
observable per run and the model carries both:

    data  the CALLER's buffer -- the object the caller still holds after the run
    work  the buffer routine 2 is handed (what routine 1 returned), as it stands
          after routine 2 returned; `fit` READS it afterwards, at
          `R = y[:, np.newaxis] - np.dot(X, coef_path_)`, so the run's reported
          numbers are a function of it

They come apart exactly when routine 1 works on a buffer of its own: then the
caller's buffer is preserved whatever routine 2 is told to do, and only `work`
records what routine 2 was told. Law D below is the measured law behind that
clause, and law B1 is what makes it hold for a truthy gate.

THE MODELED REGION (mapping.md 3.3) is a FIXED estimator configuration. This
script (a) asserts where each pinned value comes from -- constructor default, or the
one deliberate narrowing (a falsy `Gram`, without which stage two never reaches
the buffer), (b) proves the
pin table is COMPLETE by parsing `fit`'s own two call statements and checking
that every argument they pass is either a modeled input or a pinned setting, and
(c) measures that stepping off a pin really does change the modeled transforms, so
the pins are load-bearing rather than decorative. Structural guards
(`check_array(X, copy=False, dtype=FLOAT_DTYPES) is X`, dense, falsy `Gram`) are
checked per input as before.

THE LAWS (mapping.md 3.1/3.2/3.4, refinement.md #2/#3/#4/#5):

  A1  routine 1, gate truthy  => caller's buffer preserved verbatim   [universal]
  A2  routine 1, gate falsy   => caller's buffer written              [non-degenerate class]
  A3  routine 1's OUTPUT CONTENTS are a function of (ENTRY CONTENTS, TARGET):
      replay-deterministic, independent of the target's VALUES at a fixed target
      LENGTH, and independent of its own gate -> licenses `prepareInPlace` being
      the SAME symbol on both legs, and keeps its second argument a SHAPE witness
      rather than a numeric dependence
  A4  `prepareInPlace` must be BINARY: the routine reduces column-wise, so its
      output depends on the buffer's row/column division, which the flat Lean
      carrier does not record and `target.size` does. Measured: equal flat
      C-order entries under targets of DIFFERENT lengths give DIFFERENT output,
      so no unary symbol could equal them all
  B1  routine 2, gate truthy  => the buffer it was handed is preserved verbatim
                                                                      [universal]
  B2  routine 2, gate falsy   => the buffer it was handed is written  [non-degenerate class]
  B3  routine 2's transform is a function of (HANDED BUFFER, TARGET):
      replay-deterministic, and it genuinely READS the target (distinct targets,
      same handed buffer, observed to give distinct results) -> forces
      `searchInPlace` BINARY
  C   the COMPOSITE (routine 1 then routine 2, both gates falsy, in the order
      `fit` calls them) is a deterministic function of (buffer, target) --
      the model's `searchInPlace (prepareInPlace dataOld) target`
  D   the WORK buffer, composed exactly as `fit` composes the two routines under
      ONE gate g: g truthy => work == routine 1's output (routine 2 left it
      alone); g falsy => work == the composite. This is the law the model's
      second `true`-leg clause rests on, and it holds even though the caller's
      buffer is preserved on that leg.

The one-sided form of A1/B1 vs A2/B2 is deliberate: the model asserts an EQUATION
between a buffer and an opaque function's value, NOT that the buffer changed. A
degenerate input whose processed contents coincide with its entry contents
therefore satisfies the model and must not be asserted to differ. `changed` is
asserted only on the class where the callees are measured to write.

Imports only `sklearn` + `numpy` + stdlib. Exit 0 iff every observation meets
its law.
"""
import ast
import inspect
import random
import re
import sys
import textwrap
import warnings

# --- the modeled region: one PINNED estimator configuration ------------------
# Every value here is `LassoLarsIC.__init__`'s own default EXCEPT precompute,
# whose default 'auto' is truthy; the region pins it falsy because that is the
# only setting under which stage two reaches the buffer at all, and it is the
# setting both observable behaviours of this change are stated in. Provenance is
# asserted below, and together with the structural guards this list is COMPLETE
# for both routines (asserted below by parsing fit's two call statements).
PIN_FIT_INTERCEPT = True
PIN_NORMALIZE = True
PIN_PRECOMPUTE = False       # falsy Gram: keeps routine 2 on the buffer it is handed
PIN_MAX_ITER = 500
PIN_POSITIVE = False
PIN_VERBOSE = False
# Literal keyword arguments `fit` itself passes routine 2 (least_angle.py:1509-
# 1512). They are settings of the modeled routines exactly like the self.<attr>
# ones, so they are pinned here, asserted to be the values the call site really
# uses, and used BY `routine2` below, so this module cannot drift from `fit`.
PIN_COPY_GRAM = True
PIN_ALPHA_MIN = 0.0
PIN_METHOD = 'lasso'
PIN_RETURN_N_ITER = True
LITERAL_PINS = {
    'copy_Gram': PIN_COPY_GRAM,
    'alpha_min': PIN_ALPHA_MIN,
    'method': PIN_METHOD,
    'return_n_iter': PIN_RETURN_N_ITER,
}


def _eps():
    import numpy as np
    return np.finfo(float).eps


def reduction_stays_in_range(X):
    """The DOMAIN conjunct of mapping.md 3.3, decided by the repo's own arithmetic.

    Routine 1 subtracts a column-wise mean from the buffer
    (`X_offset = np.average(X, axis=0)`, base.py:149, then `X -= X_offset`,
    base.py:150) and then hands the result to `f_normalize(..., copy=False)`
    (base.py:152), whose own `check_array` asserts that every entry is finite
    (validation.py:51). For buffers whose entries sit near the top of the float64
    range that subtraction — or the mean's own summation — leaves the range, the
    assertion fires, and routine 1 RAISES instead of returning. On such a run
    routine 2 never executes at all, so there is no buffer for the composite term
    to denote, and the caller's buffer is left holding neither its entry contents
    nor the composite. Those runs are therefore OUTSIDE the modeled region: the
    model claims nothing about a buffer the routines refuse to process.

    The condition is computed the way the repo computes it — the same reduction,
    on the caller's own entries — never by a magnitude threshold this module
    invents. It is a DOMAIN restriction, in the same category as (a) below, and
    not a determinacy pin like (b) and (c): what is excluded is the runs that
    raise, not runs whose result would depend on something unmodeled."""
    import numpy as np
    with np.errstate(over='ignore', invalid='ignore'):
        offset = np.average(X, axis=0)
        if not np.isfinite(offset).all():
            return False
        centered = np.subtract(X, offset)
        return bool(np.isfinite(centered).all())


def both_routines_deliver(X, y):
    """`bothRoutinesDeliver` of Solution.lean — the DOMAIN of the two-routine
    sequence, decided by RUNNING it (mapping.md 3.5).

    `reduction_stays_in_range` above covers only the arm where ROUTINE 1's own
    centering leaves the float64 range, and that arm is a property of `X` alone.
    It is not the whole domain: routine 2 reads the TARGET, so a buffer whose
    centering is perfectly well behaved can still reach a descent that signals
    because `y` overflows. Measured: a finite 4x2 gaussian `X` (for which
    `reduction_stays_in_range` is True and `in_modeled_region` holds) under
    `y = [1e308, 1e308, -1e308, 1e308]` -> routine 1 returns, routine 2 is
    entered, and the run raises. So the spec's precondition is over the PAIR,
    and this is the predicate that decides it.

    Decided by the repo's own arithmetic — the real routines, on the caller's own
    entries — never by a magnitude threshold this module invents. Gate-free by
    construction and measured gate-independent (GUARD 5), which is what licenses
    the single spec-level predicate covering every copy-choice leg."""
    try:
        observe_run(X, y, PIN_NORMALIZE, False)
    except (ValueError, FloatingPointError):
        return False
    return True


def in_modeled_region(X):
    """The buffer-shape guards of mapping.md 3.3, as the repo decides them.

    (a) DTYPE. The buffer reaches routine 1 through `check_array(...,
        dtype=FLOAT_DTYPES)` (base.py:117), which returns the SAME object only
        for a float dtype. When it does not, every later write lands in a
        private converted array and the caller's buffer is unreachable.

    (b) MEMORY LAYOUT. The buffer must be C-contiguous. This is a determinacy
        guard, not a reachability one: routine 1 reduces over the buffer
        (`X_offset = np.average(X, axis=0)`, base.py:149, then
        `f_normalize(..., copy=False)`, base.py:152) and numpy's pairwise
        summation blocks along the memory STRIDE, so the summation order — hence
        the last bits of the float result — depends on the layout. Two buffers
        with identical CONTENTS but different layout therefore give routine 1
        different output, so without this guard `prepareInPlace` would not be a
        function of the entry contents and the modeled buffers would not be
        determined by the modeled inputs. Measured off-pin below
        (`check_pins_are_load_bearing`, GUARD 3). The model claims nothing about
        an F-ordered caller buffer.


    (c) ELEMENT FORMAT. The buffer's dtype must be `float64`. This is a
        DETERMINACY guard, not a reachability one -- unlike (a), the float32 and
        float16 members of FLOAT_DTYPES ARE reachable (`check_X_y` returns the
        caller's own object and the falsy leg writes it). But routine 1's
        reduction is carried out in the buffer's own precision, so two buffers
        with EXACTLY equal entries in different formats give routine 1 different
        output, and it reaches `coef_`. The modeled signature carries no argument
        for the format, so it is pinned here for the same reason the layout is.

    (d) RANGE. Routine 1 must be able to run to completion on the buffer at all:
        its centering step must stay inside the float64 range, because the repo
        asserts finiteness immediately afterwards and otherwise RAISES, leaving
        no buffer for the modeled terms to denote. See
        `reduction_stays_in_range` above; measured necessary below (GUARD 4).

    All four conjuncts are decided by the repo's own machinery / the buffer's
    own flags, never by anything this module invents. (a) and (d) are DOMAIN
    conjuncts — outside them the modeled buffers have no referent — while (b) and
    (c) are DETERMINACY pins on properties the signature carries no argument
    for."""
    import numpy as np
    from sklearn.utils import check_array
    from sklearn.utils.validation import FLOAT_DTYPES
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            same_object = check_array(X, copy=False, dtype=FLOAT_DTYPES) is X
    except ValueError:
        # the repo's own entry validation rejects the buffer before either
        # routine touches it (a non-finite entry, an empty buffer, ...), so the
        # run this model describes does not happen.
        return False
    return bool(same_object and X.flags['C_CONTIGUOUS']
                and X.dtype == np.float64
                and reduction_stays_in_range(X))


def routine1(X_arg, y, normalize, gate):
    """Run the REAL unchanged routine 1 DIRECTLY on the buffer X_arg, with
    `fit`'s arguments. Returns the processed pair routine 2 is handed."""
    from sklearn.linear_model.base import _preprocess_data
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        Xp, yp, _Xm, _ym, _Xs = _preprocess_data(
            X_arg, y, PIN_FIT_INTERCEPT, normalize, gate)
    return Xp, yp


def routine2(X_arg, y, gate, Gram=None, max_iter=None, eps=None,
             positive=None, method=None):
    """Run the REAL unchanged routine 2 DIRECTLY on the buffer X_arg, with
    exactly the arguments `LassoLarsIC.fit` passes it (least_angle.py:1509).

    Every non-modeled argument comes from a PIN_* constant, including the ones
    `fit` writes as literals, so `check_pin_table_complete` can compare this
    module's values against the call site's own text."""
    from sklearn.linear_model import lars_path
    if max_iter is None:
        max_iter = PIN_MAX_ITER
    if eps is None:
        eps = _eps()
    if positive is None:
        positive = PIN_POSITIVE
    if method is None:
        method = PIN_METHOD
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lars_path(X_arg, y, Gram=Gram, copy_X=gate,
                  copy_Gram=PIN_COPY_GRAM, alpha_min=PIN_ALPHA_MIN,
                  method=method, verbose=PIN_VERBOSE,
                  max_iter=max_iter, eps=eps,
                  return_n_iter=PIN_RETURN_N_ITER, positive=positive)


def _dup(A):
    """A private duplicate of the caller's buffer that KEEPS ITS LAYOUT.

    `ndarray.copy()` defaults to `order='C'`, which would silently re-lay an
    F-ordered buffer and make the layout row of the modeled region (mapping.md
    3.3) unmeasurable — the off-pin twin would arrive at the routines as C order,
    agree with the C run, and the pin would look unnecessary. `order='A'` is F
    when the source is Fortran-contiguous and C otherwise, so what the routines
    see here is the layout the caller really had."""
    return A.copy(order='A')


def observe_routine1(X, y, normalize, gate):
    """(buffer_preserved, output_contents) for routine 1 on a private copy."""
    import numpy as np
    X_arg = _dup(X)
    X_ref = _dup(X_arg)
    Xp, _yp = routine1(X_arg, y, normalize, gate)
    return bool(np.array_equal(X_arg, X_ref)), _dup(Xp)


def observe_routine1_target(X, y, normalize):
    """The target vector routine 2 receives: routine 1's processed `y`."""
    _Xp, yp = routine1(_dup(X), y, normalize, False)
    return yp


def observe_routine2(B, y, gate, Gram=None, **kw):
    """(buffer_preserved, exit_contents) for routine 2 on a private copy."""
    import numpy as np
    B_arg = _dup(B)
    B_ref = _dup(B_arg)
    routine2(B_arg, y, gate, Gram=Gram, **kw)
    return bool(np.array_equal(B_arg, B_ref)), B_arg


def observe_run(X, y, normalize, gate, **kw):
    """The two buffers the model carries, composed exactly as `fit` composes the
    two routines under ONE gate: routine 2 receives what routine 1 returned.

    Returns (caller_buffer_after, work_buffer_after, routine1_output)."""
    X_arg = _dup(X)
    Xp, yp = routine1(X_arg, y, normalize, gate)
    prepared = _dup(Xp)
    routine2(Xp, yp, gate, Gram=PIN_PRECOMPUTE, **kw)
    return X_arg, Xp, prepared


class Tally(object):
    def __init__(self):
        self.counts = {}

    def bump(self, key, n=1):
        self.counts[key] = self.counts.get(key, 0) + n

    def report(self):
        return ", ".join("%s=%d" % (k, self.counts[k])
                         for k in sorted(self.counts))


# --- the pin table, and where each pinned value comes from -------------------
def check_pin_provenance(tally):
    """Every pinned setting is either the constructor's own default or the ONE
    deliberate narrowing the model needs, and this asserts which is which.

    The deliberate narrowing is `precompute`: its constructor default `'auto'` is
    TRUTHY, and a truthy `Gram` makes routine 2 build its own product matrix and
    never touch the buffer it was handed (GUARD 2). The model's second stage only
    exists on a falsy `Gram`, so the region pins `precompute` falsy. That is not
    an exotic corner: it is the configuration both observable behaviours of this
    change are stated in (`LassoLarsIC(precompute=False)`, and the sweep
    `precompute in [True, False, 'auto', None]` whose falsy entries are the ones
    that reach the buffer)."""
    from sklearn.linear_model import LassoLarsIC
    import numpy as np
    sig = inspect.signature(LassoLarsIC.__init__)
    defaults = {
        'fit_intercept': PIN_FIT_INTERCEPT,
        'normalize': PIN_NORMALIZE,
        'max_iter': PIN_MAX_ITER,
        'positive': PIN_POSITIVE,
        'verbose': PIN_VERBOSE,
    }
    for name, value in defaults.items():
        got = sig.parameters[name].default
        assert got == value or (got is value), (
            "PIN VIOLATED: %s default is %r, the modeled region pins %r as if "
            "it were the default" % (name, got, value))
        tally.bump("pin-is-default")
    assert sig.parameters['eps'].default == np.finfo(float).eps, (
        "PIN VIOLATED: the eps default is not machine epsilon, so pinning eps "
        "to machine epsilon is not pinning the default")
    tally.bump("pin-is-default")
    # the ONE deliberate narrowing, asserted to BE a narrowing
    assert sig.parameters['precompute'].default, (
        "PIN PROVENANCE: the precompute default is already falsy, so recording "
        "the falsy-Gram guard as a deliberate narrowing is wrong")
    assert not PIN_PRECOMPUTE, (
        "PIN PROVENANCE: the region must pin a FALSY Gram for stage two to "
        "reach the buffer at all")
    tally.bump("pin-is-deliberate-narrowing")


def check_pin_table_complete(tally):
    """Parse `fit`'s OWN two call statements and check that every argument they
    pass is either a modeled input or a pinned setting. This is what makes the
    pin table complete by construction rather than by enumeration: if a future
    argument appears at either call site, this assertion fails.

    Three kinds of argument are accounted for, so the claim covers the whole
    call text and not just the names in it:
      * `self.<attr>` reads          -> must be a PINNED attribute or the gate;
      * local names                  -> must be a modeled input or a checked
                                        alias of a pinned attribute;
      * LITERAL keyword arguments    -> must appear in LITERAL_PINS with the same
                                        value, so e.g. `method='lasso'` (which
                                        selects the lasso descent rather than
                                        LAR, a genuine input of routine 2) is
                                        accounted for rather than invisible.
    Positional literals are rejected outright: there is no name to pin them
    under."""
    from sklearn.linear_model import LassoLarsIC

    src = inspect.getsource(LassoLarsIC.fit)
    tree = ast.parse(textwrap.dedent(src))
    calls = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            nm = None
            if isinstance(fn, ast.Name):
                nm = fn.id
            elif isinstance(fn, ast.Attribute):
                nm = fn.attr
            if nm in ("_preprocess_data", "lars_path"):
                calls[nm] = node
    assert set(calls) == {"_preprocess_data", "lars_path"}, (
        "COMPLETENESS: expected exactly the two routine call sites in fit, "
        "found %r" % (sorted(calls),))

    attrs, names = set(), set()
    for node in calls.values():
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) \
                    and sub.value.id == "self":
                attrs.add(sub.attr)
            elif isinstance(sub, ast.Name):
                names.add(sub.id)

    # Modeled inputs: the buffer, the target, and the copy gate. Everything else
    # a call site passes must be pinned.
    MODELED = {"X", "y", "copy_X"}
    ALIASES = {"Gram": "precompute", "max_iter": "max_iter"}
    PINNED = {"fit_intercept", "normalize", "precompute", "max_iter", "eps",
              "positive", "verbose"}
    # `copy_X` appears as `self.copy_X` pre-patch and as the local `copy_X`
    # post-patch; both are the modeled gate.
    unaccounted_attrs = attrs - PINNED - {"copy_X"}
    assert not unaccounted_attrs, (
        "COMPLETENESS VIOLATED: fit passes self.%s to a modeled routine and the "
        "region neither models nor pins it" % ", self.".join(sorted(
            unaccounted_attrs)))
    unaccounted_names = names - MODELED - set(ALIASES) - {"lars_path",
                                                          "_preprocess_data",
                                                          "LinearModel", "self"}
    assert not unaccounted_names, (
        "COMPLETENESS VIOLATED: fit passes %s to a modeled routine and the "
        "region neither models nor pins it" % ", ".join(sorted(
            unaccounted_names)))
    # the two local aliases really are the pinned attributes
    for local, attr in ALIASES.items():
        if local in names:
            assert re.search(r"\b%s\s*=\s*self\.%s\b" % (local, attr), src), (
                "COMPLETENESS VIOLATED: local %r at a call site is not "
                "`self.%s`" % (local, attr))

    # (c) the LITERAL arguments. `ast.literal_eval` is used rather than matching
    # node classes so this works on every Python the image may carry.
    literals = {}
    for nm, node in calls.items():
        for a in node.args:
            assert isinstance(a, (ast.Name, ast.Attribute)), (
                "COMPLETENESS VIOLATED: %s is passed a POSITIONAL non-name "
                "argument; there is no keyword to pin it under" % nm)
        for kw in node.keywords:
            assert kw.arg is not None, (
                "COMPLETENESS VIOLATED: %s is called with **kwargs, so its "
                "argument list cannot be enumerated" % nm)
            if isinstance(kw.value, (ast.Name, ast.Attribute)):
                continue          # already accounted for by (a)/(b)
            try:
                val = ast.literal_eval(kw.value)
            except (ValueError, SyntaxError, TypeError):
                raise AssertionError(
                    "COMPLETENESS VIOLATED: %s passes %s=<computed expression>, "
                    "which the region neither models nor pins" % (nm, kw.arg))
            assert kw.arg in LITERAL_PINS, (
                "COMPLETENESS VIOLATED: %s passes the literal %s=%r and the "
                "region neither models nor pins it" % (nm, kw.arg, val))
            assert LITERAL_PINS[kw.arg] == val, (
                "PIN VIOLATED: %s passes %s=%r but the modeled region pins %r"
                % (nm, kw.arg, val, LITERAL_PINS[kw.arg]))
            literals[kw.arg] = val
            tally.bump("literal-pin-accounted")
    assert set(literals) == set(LITERAL_PINS), (
        "PIN TABLE STALE: the region pins the literals %r but fit's own call "
        "sites pass %r" % (sorted(LITERAL_PINS), sorted(literals)))
    tally.bump("pin-table-complete")
    return sorted(attrs), sorted(names), sorted(literals)


def check_pins_are_load_bearing(tally):
    """Each pin must matter, or be reported honestly as unobserved: step off it
    and see whether the modeled composite changes. mapping.md 3.3 records the
    outcome per pin."""
    import numpy as np
    rng = np.random.RandomState(3)
    hits = {}
    for shape in [(60, 5), (30, 6), (100, 4)]:
        X = np.ascontiguousarray(rng.normal(0, 1, shape))
        y = X[:, 1] + 0.3 * rng.normal(0, 1, shape[0])
        base = observe_run(X, y, PIN_NORMALIZE, False)[1]
        # The layout off-pin: SAME contents, F order. `np.asfortranarray` copies
        # the values bit-for-bit, so np.array_equal(X, X_f) is True on entry and
        # the ONLY difference the routines see is the memory stride.
        X_f = np.asfortranarray(X)
        assert np.array_equal(X, X_f) and not X_f.flags['C_CONTIGUOUS'], (
            "the layout off-pin twin is not an equal-contents F-ordered buffer")
        offs = {
            "normalize": observe_run(X, y, not PIN_NORMALIZE, False)[1],
            "max_iter=2": observe_run(X, y, PIN_NORMALIZE, False,
                                      max_iter=2)[1],
            "max_iter=1": observe_run(X, y, PIN_NORMALIZE, False,
                                      max_iter=1)[1],
            "eps=1e-2": observe_run(X, y, PIN_NORMALIZE, False, eps=1e-2)[1],
            "positive": observe_run(X, y, PIN_NORMALIZE, False,
                                    positive=not PIN_POSITIVE)[1],
            "method=lar": observe_run(X, y, PIN_NORMALIZE, False,
                                      method='lar')[1],
            "c_contiguous": observe_run(X_f, y, PIN_NORMALIZE, False)[1],
        }
        for k, v in offs.items():
            if v.shape != base.shape or not np.array_equal(v, base):
                hits[k] = hits.get(k, 0) + 1
    for k, n in sorted(hits.items()):
        tally.bump("pin-load-bearing:" + k, n)
    assert hits.get("normalize"), (
        "PIN JUSTIFICATION: stepping off the normalize pin never changed the "
        "composite, so the recorded justification for that pin is wrong")
    # The layout pin is the reason `prepareInPlace` may be a function of the
    # entry CONTENTS alone, so it must be measured, not merely asserted.
    assert hits.get("c_contiguous"), (
        "PIN JUSTIFICATION: an equal-contents F-ordered buffer gave the SAME "
        "composite on every matrix tried, so the C-contiguity row of "
        "mapping.md 3.3 records a dependence that was not observed")
    assert len(hits) >= 2, (
        "PIN JUSTIFICATION: only %d of the pinned settings were observed to "
        "matter; the pin table's justification is not measured" % len(hits))
    return hits


def check_matrix(X, y, y_alt, tally, nondegenerate):
    """All laws on one (matrix, target) observation, at the pinned region."""
    import numpy as np
    from sklearn.utils import check_X_y

    assert in_modeled_region(X), (
        "REGION: matrix is not in the modeled region (dense C-contiguous float)")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        Xc, _yc = check_X_y(X, y, y_numeric=True)
    assert Xc is X, (
        "REGION: the caller's buffer does not survive fit's own input check "
        "as the same object, so it cannot reach routine 1 in place")

    normalize = PIN_NORMALIZE

    # ---- A1: routine 1, gate truthy -> caller preserved (universal) ----------
    pres, out1_truthy = observe_routine1(X, y, normalize, True)
    assert pres, "A1 VIOLATED: routine 1 with a truthy gate wrote the caller's buffer"
    tally.bump("A1")

    # ---- A3: routine 1's output is a function of the entry contents ALONE ----
    _, out1 = observe_routine1(X, y, normalize, False)
    _, out1b = observe_routine1(X, y, normalize, False)
    assert np.array_equal(out1, out1b), (
        "A3 VIOLATED: routine 1 is not replay-deterministic")
    # `y_alt` has the SAME length as `y` (both are n_samples long), so this is
    # value-independence at a FIXED target length: it keeps `prepareInPlace`'s
    # second argument a shape witness rather than a numeric dependence. The
    # LENGTH genuinely matters and is measured by A4 (`check_shape_is_binding`).
    _, out1y = observe_routine1(X, y_alt, normalize, False)
    assert len(y_alt) == len(y), (
        "A3 PRECONDITION: the alternate target must have the same length, "
        "otherwise this would test the shape axis rather than the value axis")
    assert np.array_equal(out1, out1y), (
        "A3 VIOLATED: routine 1's output depends on the target's VALUES at a "
        "fixed length, so prepareInPlace's second argument would not be a mere "
        "shape witness")
    assert np.array_equal(out1, out1_truthy), (
        "A3 VIOLATED: routine 1's output contents depend on its own gate, so "
        "the two legs may not share one prepareInPlace symbol")
    tally.bump("A3")

    # ---- A2: routine 1, gate falsy -> written (non-degenerate class only) ----
    if nondegenerate:
        assert not np.array_equal(out1, X), (
            "A2 VIOLATED: routine 1 with a falsy gate left a non-degenerate "
            "buffer unchanged")
        tally.bump("A2")
    else:
        tally.bump("A2-degenerate-skipped")

    # routine 2's handed buffer is routine 1's output; its target is routine 1's
    # processed target.
    B = out1
    ycen = observe_routine1_target(X, y, normalize)

    # ---- B1: routine 2, gate truthy -> handed buffer preserved (universal) ---
    pres2, _ = observe_routine2(B, ycen, True, Gram=PIN_PRECOMPUTE)
    assert pres2, (
        "B1 VIOLATED: routine 2 with a truthy gate wrote the buffer it was "
        "handed")
    tally.bump("B1")

    # ---- B3: routine 2 determinacy ------------------------------------------
    _, out2 = observe_routine2(B, ycen, False, Gram=PIN_PRECOMPUTE)
    _, out2b = observe_routine2(B, ycen, False, Gram=PIN_PRECOMPUTE)
    assert np.array_equal(out2, out2b), (
        "B3 VIOLATED: routine 2 is not replay-deterministic")
    tally.bump("B3-determinism")

    # ---- B2: routine 2, gate falsy -> written (non-degenerate class only) ----
    if nondegenerate:
        assert not np.array_equal(out2, B), (
            "B2 VIOLATED: routine 2 with a falsy gate left a non-degenerate "
            "handed buffer unchanged")
        tally.bump("B2")
    else:
        tally.bump("B2-degenerate-skipped")

    # ---- B3 (target dependence): distinct targets, same handed buffer -------
    ycen_alt = observe_routine1_target(X, y_alt, normalize)
    if not np.array_equal(ycen, ycen_alt):
        _, out2alt = observe_routine2(B, ycen_alt, False, Gram=PIN_PRECOMPUTE)
        if not np.array_equal(out2, out2alt):
            tally.bump("B3-target-dependent")
        else:
            tally.bump("B3-target-coincident")

    # ---- C: the composite is a deterministic function of (buffer, target) ---
    caller_f, work_f, prepared_f = observe_run(X, y, normalize, False)
    caller_f2, work_f2, _ = observe_run(X, y, normalize, False)
    assert np.array_equal(work_f, work_f2) and np.array_equal(caller_f,
                                                              caller_f2), (
        "C VIOLATED: the composite is not a deterministic function of "
        "(buffer, target)")
    assert np.array_equal(work_f, out2), (
        "C VIOLATED: the buffer after both routines is not "
        "routine2(routine1(buffer), target)")
    assert np.array_equal(prepared_f, out1), (
        "C VIOLATED: routine 1's output inside the composition differs from "
        "routine 1 run alone")
    tally.bump("C")

    # ---- D: the WORK buffer under ONE gate ----------------------------------
    # falsy gate: the caller's buffer and the work buffer are the same buffer,
    # both holding the composite.
    assert np.array_equal(caller_f, work_f), (
        "D VIOLATED: with a falsy gate the caller's buffer and the buffer "
        "routine 2 was handed do not agree")
    tally.bump("D-falsy")
    # truthy gate: the caller's buffer is preserved AND the work buffer still
    # holds routine 1's output -- routine 2 left it alone. This is the clause a
    # caller's-buffer-only model cannot state.
    caller_t, work_t, prepared_t = observe_run(X, y, normalize, True)
    assert np.array_equal(caller_t, X), (
        "D VIOLATED: a truthy gate did not preserve the caller's buffer across "
        "both routines")
    assert np.array_equal(work_t, prepared_t), (
        "D VIOLATED: with a truthy gate the buffer routine 2 was handed does "
        "not still hold routine 1's output")
    assert np.array_equal(work_t, out1), (
        "D VIOLATED: with a truthy gate the work buffer is not "
        "prepareInPlace(dataOld)")
    tally.bump("D-truthy")
    # and the two gates give DIFFERENT work buffers on the non-degenerate class:
    # that is what makes the truthy clause discriminating.
    if nondegenerate:
        assert not np.array_equal(work_t, work_f), (
            "D VIOLATED: the two gates left the same work buffer on a "
            "non-degenerate input, so the clause could not discriminate")
        tally.bump("D-discriminating")


def check_shape_is_binding(tally):
    """A4. `prepareInPlace` is BINARY, and that is load-bearing rather than
    decoration.

    The Lean carrier is a FLAT `Array Int` (mapping.md 2), so it does not record
    the buffer's row/column division. Routine 1 reduces COLUMN-WISE
    (`np.average(X, axis=0)`, base.py:149), so its output DOES depend on that
    division. `check_X_y` (least_angle.py:1504) forces `len(y) == X.shape[0]`, so
    the target's LENGTH carries n_samples and hence the division.

    This asserts that the second argument is necessary: reshaping ONE flat buffer
    to several shapes -- every one of them inside the modeled region -- gives
    routine 1 DIFFERENT output. A unary symbol would have to equal all of them."""
    import numpy as np

    rng = np.random.RandomState(12973)
    flat = rng.normal(0, 1, 24)
    outs = {}
    for shape in [(6, 4), (4, 6), (12, 2), (24, 1), (8, 3), (3, 8), (2, 12)]:
        X = np.ascontiguousarray(flat.reshape(shape))
        y = np.ascontiguousarray(rng.normal(0, 1, shape[0]))
        assert in_modeled_region(X), (
            "A4: shape %r is not in the modeled region, so it cannot witness "
            "the shape axis" % (shape,))
        flat_entries = tuple(np.ascontiguousarray(X).reshape(-1).tolist())
        assert flat_entries == tuple(flat.tolist()), (
            "A4: reshaping changed the flat C-order entries, so these are not "
            "one Lean `dataOld`")
        out = observe_routine1(X, y, PIN_NORMALIZE, False)[1]
        outs[shape] = tuple(np.ascontiguousarray(out).reshape(-1).tolist())
        tally.bump("A4-shape-observed")

    distinct = len(set(outs.values()))
    assert distinct > 1, (
        "A4 VIOLATED: routine 1 gave the SAME output for one flat buffer under "
        "every shape tried, so `prepareInPlace` would not need its second "
        "argument and the binary arity would be unjustified")
    tally.bump("A4-shape-is-binding", distinct)

    # And the FORMAT axis, for the same reason the layout axis is guarded: equal
    # entries in another float format are reachable but give a different result,
    # and no signature argument carries the format.
    b = rng.normal(0, 1, (20, 4)).astype(np.float32)
    X64 = np.ascontiguousarray(b.astype(np.float64))
    X32 = np.ascontiguousarray(b)
    y64 = np.ascontiguousarray(b[:, 1].astype(np.float64))
    y32 = np.ascontiguousarray(b[:, 1])
    assert np.array_equal(X64, X32), "A4/FORMAT: the twins differ in contents"
    assert in_modeled_region(X64), "A4/FORMAT: the float64 twin is out of region"
    assert not in_modeled_region(X32), (
        "A4/FORMAT unexpectedly holds: a float32 buffer passed the region test, "
        "so the element-format row of mapping.md 3.3 is not enforced")
    o64 = observe_routine1(X64, y64, PIN_NORMALIZE, False)[1]
    o32 = observe_routine1(X32, y32, PIN_NORMALIZE, False)[1]
    assert not np.array_equal(np.asarray(o64, dtype=np.float64),
                              np.asarray(o32, dtype=np.float64)), (
        "A4/FORMAT JUSTIFICATION: routine 1 gave bit-identical output for equal "
        "contents in float64 and float32, so pinning the element format is "
        "unjustified")
    tally.bump("guard-format-is-necessary")


def check_guards(tally):
    """The structural guards of mapping.md 3.3 are REAL: outside them the
    caller's buffer is unreachable, which is why the model claims nothing
    there."""
    import numpy as np
    rng = np.random.RandomState(7)

    # GUARD 1: an integer buffer is outside the region.
    Xi = (rng.normal(0, 10, (60, 4)) * 100).astype(np.int64)
    yi = Xi[:, 1].astype(np.float64)
    assert not in_modeled_region(Xi), (
        "GUARD 1 unexpectedly holds: an int64 buffer passed the region test")
    caller, _work, _prep = observe_run(Xi, yi, PIN_NORMALIZE, False)
    assert np.array_equal(caller, Xi), (
        "GUARD 1 VIOLATED: an int64 buffer was written through, so the region "
        "narrowing in mapping.md 3.3 is not the real boundary")
    tally.bump("guard-int-outside-region")

    # GUARD 2: a truthy Gram keeps routine 2 off the buffer it is handed.
    Xf = rng.normal(0, 1, (80, 5))
    yf = Xf[:, 2].copy()
    B = observe_routine1(Xf, yf, PIN_NORMALIZE, False)[1]
    ycen = observe_routine1_target(Xf, yf, PIN_NORMALIZE)
    for Gram in (True, 'auto', np.dot(B.T, B)):
        pres2, _ = observe_routine2(B, ycen, False, Gram=Gram)
        assert pres2, (
            "GUARD 2 VIOLATED: routine 2 wrote the buffer it was handed with a "
            "truthy Gram=%r, so the precompute guard in mapping.md 3.3 is "
            "not the real boundary" % (Gram,))
        tally.bump("guard-gram-outside-stage2")

    # GUARD 3: an F-ordered buffer is outside the region, and for a DIFFERENT
    # reason from GUARD 1. It is perfectly reachable — the routines do write it —
    # but the modeled quantity is not DETERMINED there: two buffers with equal
    # contents and different layout give routine 1 different output, because its
    # reductions (base.py:149, :152) sum along the memory stride. So the region
    # excludes it, and this asserts both halves of that statement: the guard
    # rejects it, AND the exclusion is necessary rather than decorative.
    layout_divergences = 0
    for shape in [(90, 5), (40, 6)]:
        Xc = np.ascontiguousarray(rng.normal(0, 1, shape))
        yc = Xc[:, 1].copy()
        Xf = np.asfortranarray(Xc)
        assert in_modeled_region(Xc), (
            "GUARD 3: the C-ordered twin is not in the modeled region")
        assert not in_modeled_region(Xf), (
            "GUARD 3 unexpectedly holds: an F-ordered buffer passed the region "
            "test, so the layout row of mapping.md 3.3 is not enforced")
        assert np.array_equal(Xc, Xf), "GUARD 3: the twins differ in contents"
        prep_c = observe_routine1(Xc, yc, PIN_NORMALIZE, False)[1]
        prep_f = observe_routine1(Xf, yc, PIN_NORMALIZE, False)[1]
        if not np.array_equal(prep_c, prep_f):
            layout_divergences += 1
        tally.bump("guard-forder-outside-region")
    assert layout_divergences, (
        "GUARD 3 JUSTIFICATION: routine 1 gave bit-identical output for equal "
        "contents in C and F order on every matrix tried, so excluding "
        "F-ordered buffers from the region is unjustified")
    tally.bump("guard-forder-is-necessary", layout_divergences)

    # GUARD 4: a buffer whose centering leaves the float64 range is outside the
    # region, and for the same KIND of reason as GUARD 1 rather than GUARD 3 —
    # there is no modeled buffer to speak of, because routine 1 RAISES and
    # routine 2 never runs. Both halves are asserted: the guard rejects such a
    # buffer, and the exclusion is necessary (the run really does raise, and the
    # caller's buffer is left holding neither its entry contents nor anything the
    # model names). Every buffer here is finite on entry, float64 and
    # C-contiguous, so the ONLY conjunct that can be doing the rejecting is the
    # range one.
    Xctl = np.ascontiguousarray(np.array([[1e307], [-1e307]], dtype=np.float64))
    yctl = np.array([1.0, -1.0], dtype=np.float64)
    assert in_modeled_region(Xctl), (
        "GUARD 4 CONTROL: a large-but-workable buffer was excluded, so the range "
        "conjunct is stricter than the repo's own arithmetic")
    observe_run(Xctl, yctl, PIN_NORMALIZE, False)
    tally.bump("guard-range-control-runs")

    for mag in (1e308, 1.7e308):
        Xh = np.ascontiguousarray(np.array([[mag], [mag]], dtype=np.float64))
        yh = np.array([1.0, -1.0], dtype=np.float64)
        assert np.isfinite(Xh).all(), "GUARD 4: the witness is not finite on entry"
        assert Xh.dtype == np.float64 and Xh.flags['C_CONTIGUOUS'], (
            "GUARD 4: the witness fails a guard other than the range one")
        assert not reduction_stays_in_range(Xh), (
            "GUARD 4: the range conjunct accepted a buffer whose centering "
            "leaves the float64 range (magnitude %r)" % (mag,))
        assert not in_modeled_region(Xh), (
            "GUARD 4 unexpectedly holds: a buffer whose centering overflows "
            "passed the region test, so the range row of mapping.md 3.3 is not "
            "enforced")
        raised = None
        try:
            observe_run(Xh, yh, PIN_NORMALIZE, False)
        except ValueError as exc:
            raised = exc
        assert raised is not None, (
            "GUARD 4 JUSTIFICATION: the run completed on a buffer the range "
            "conjunct excludes (magnitude %r), so the exclusion is "
            "unjustified" % (mag,))
        tally.bump("guard-range-outside-region")

    # GUARD 5: the spec's precondition `bothRoutinesDeliver` is over the PAIR,
    # and the three claims that makes load-bearing are measured here.
    #
    # (i) It is GATE-INDEPENDENT. This is what licenses ONE predicate, stated
    #     ahead of the copy choice, covering every leg. If definedness varied
    #     with the gate the spec would have to carry a different hypothesis per
    #     leg, and stating it once would be unfaithful.
    # (ii) It STRICTLY EXTENDS the X-only `reduction_stays_in_range`: there are
    #     pairs the X-only conjunct (hence `in_modeled_region`) ACCEPTS on which
    #     the sequence still signals, because routine 2 reads the target. A
    #     region conjunct on the buffer alone therefore cannot express this
    #     domain, which is exactly why the precondition is a pair predicate.
    # (iii) The frame law needs NO such hypothesis: routine 1 copies before it
    #     reduces, so on the preserve leg the caller's buffer survives even a
    #     signalling run. That is why Solution.lean guards the three output
    #     clauses and leaves `data = dataOld` unconditional.
    y_arm_holes = 0
    gate_dependent = 0
    frame_survives_signal = 0
    pair_cases = [
        (np.ascontiguousarray(rng.normal(0, 1, (4, 2))),
         np.array([1e308, 1e308, -1e308, 1e308], dtype=np.float64)),
        (np.ascontiguousarray(rng.normal(0, 1, (5, 3))),
         np.array([1e308, -1e308, 1e308, -1e308, 1e308], dtype=np.float64)),
        (np.ascontiguousarray(rng.normal(0, 1, (6, 4))),
         np.ascontiguousarray(rng.normal(0, 1, 6))),
    ]
    for Xp, yp in pair_cases:
        Xp = np.ascontiguousarray(Xp.astype(np.float64))
        yp = yp.astype(np.float64)
        if not in_modeled_region(Xp):
            continue
        delivers = both_routines_deliver(Xp, yp)
        # (ii) an in-region buffer on which the sequence still signals is a hole
        # the X-only conjunct cannot see.
        if not delivers:
            assert reduction_stays_in_range(Xp), (
                "GUARD 5: this pair was meant to witness the TARGET arm, but the "
                "buffer's own centering already leaves the range")
            y_arm_holes += 1
        # (i) gate-independence, over every copy-choice leg.
        for gate in (True, False):
            g_delivers = True
            try:
                observe_run(Xp, yp, PIN_NORMALIZE, gate)
            except (ValueError, FloatingPointError):
                g_delivers = False
            if g_delivers != delivers:
                gate_dependent += 1
        # (iii) the frame law on a SIGNALLING pair, preserve leg.
        if not delivers:
            entry = _dup(Xp)
            caller = _dup(Xp)
            try:
                routine1(caller, yp, PIN_NORMALIZE, True)
            except (ValueError, FloatingPointError):
                pass
            assert np.array_equal(caller, entry), (
                "GUARD 5 (iii): routine 1 with a truthy gate wrote the caller's "
                "buffer on a signalling pair, so the UNCONDITIONAL frame clause "
                "of Solution.lean would be unfaithful")
            frame_survives_signal += 1
        tally.bump("guard5-pair-observed")
    assert not gate_dependent, (
        "GUARD 5 (i) VIOLATED: whether the two-routine sequence delivers depends "
        "on the copy gate on %d observation(s), so the spec may not state ONE "
        "gate-free `bothRoutinesDeliver` ahead of the choice" % (gate_dependent,))
    assert y_arm_holes, (
        "GUARD 5 (ii) VIOLATED: no in-region buffer was found on which the "
        "sequence signals for a target-driven reason, so the pair-level "
        "precondition would be unjustified over the X-only range conjunct")
    assert frame_survives_signal, (
        "GUARD 5 (iii): no signalling pair was exercised, so the claim that the "
        "unconditional frame clause survives a signal is unmeasured")
    tally.bump("guard5-target-arm-holes", y_arm_holes)
    tally.bump("guard5-frame-survives-signal", frame_survives_signal)

    # ... and the boundary is where the repo puts it, not where a threshold would:
    # over a band of magnitudes straddling the float64 ceiling the region
    # predicate must agree with whether the routines can run at all. A single
    # accepted-but-raising buffer here is a faithfulness violation.
    band = {}
    bandrng = np.random.RandomState(12973)
    for step in range(40):
        expo = 305.0 + 3.2 * step / 39.0
        with np.errstate(over='ignore'):
            mag = float(np.power(np.float64(10.0), np.float64(expo)))
        if not np.isfinite(mag) or mag == 0.0:
            continue
        n = 2 + (step % 4)
        Xb = np.ascontiguousarray(
            np.full((n, 2), mag, dtype=np.float64)
            * (1.0 - 0.25 * bandrng.rand(n, 2)))
        if not np.isfinite(Xb).all():
            continue
        yb = np.ascontiguousarray(bandrng.rand(n))
        inside = in_modeled_region(Xb)
        raised = False
        try:
            observe_run(Xb, yb, PIN_NORMALIZE, False)
        except ValueError:
            raised = True
        assert not (inside and raised), (
            "RANGE BOUNDARY VIOLATED: a buffer the region accepts (magnitude "
            "%.3e) made the routines raise, so the modeled buffers have no "
            "referent there" % (mag,))
        band[(inside, raised)] = band.get((inside, raised), 0) + 1
    accepted = band.get((True, False), 0)
    excluded = band.get((False, True), 0)
    assert accepted and excluded, (
        "RANGE BOUNDARY: the band did not straddle the boundary (accepted=%d "
        "excluded=%d); the exclusion is then not measured against a control"
        % (accepted, excluded))
    tally.bump("range-boundary-accepted-and-runs", accepted)
    tally.bump("range-boundary-excluded-and-raises", excluded)


def main():
    import numpy as np

    tally = Tally()
    check_pin_provenance(tally)
    attrs, names, lits = check_pin_table_complete(tally)
    pin_hits = check_pins_are_load_bearing(tally)
    check_guards(tally)
    check_shape_is_binding(tally)

    rng = np.random.RandomState(0)
    pyrng = random.Random(12973)

    # boundary matrices: a fixed well-conditioned one, plus degenerate classes
    # (constant / rank-deficient / all-zero) that live INSIDE the region and are
    # allowed to coincide with their processed contents.
    X0 = rng.normal(0, 1, (100, 5))
    degenerate = [
        np.zeros((60, 4)),
        np.ones((60, 4)),
    ]
    Xdup = rng.normal(0, 1, (60, 2))
    degenerate.append(np.hstack([Xdup, Xdup]))

    y0 = X0[:, 2].copy()
    y0_alt = X0[:, 0] + X0[:, 1]
    check_matrix(X0, y0, y0_alt, tally, nondegenerate=True)
    for Xd in degenerate:
        yd = np.arange(Xd.shape[0]).astype(np.float64)
        yd_alt = yd[::-1].copy()
        check_matrix(Xd, yd, yd_alt, tally, nondegenerate=False)

    # randomized fuzz over shapes and scales inside the region. The element
    # format is NOT fuzzed: it is a pinned guard of the region (mapping.md 3.3),
    # because routine 1's reduction runs in the buffer's own precision, so a
    # float32 buffer is a DIFFERENT modeled input rather than the same one.
    for _ in range(24):
        n = pyrng.randint(20, 120)
        p = pyrng.randint(3, 8)
        scale = pyrng.choice([0.1, 1.0, 10.0, 100.0])
        dtype = np.float64
        Xf = np.ascontiguousarray(rng.normal(0, scale, (n, p)), dtype=dtype)
        yf = np.ascontiguousarray(Xf[:, min(2, p - 1)], dtype=dtype)
        yf_alt = np.ascontiguousarray(rng.normal(0, scale, (n,)), dtype=dtype)
        check_matrix(Xf, yf, yf_alt, tally, nondegenerate=True)

    # `searchInPlace` may only be BINARY if the target is genuinely read.
    dependent = tally.counts.get("B3-target-dependent", 0)
    assert dependent >= 3, (
        "B3 VIOLATED: routine 2's transform was never observed to vary with the "
        "target (%d dependent observations); a unary model would then suffice "
        "and the second argument would be unjustified" % dependent)

    print("G-AX OK: prepareInPlace / searchInPlace frame + determinacy "
          "references sound against the real unchanged callees _preprocess_data "
          "and lars_path exercised directly, over the pinned modeled region "
          "(default configuration: fit_intercept=%r normalize=%r precompute=%r "
          "max_iter=%r eps=machine positive=%r verbose=%r; dense C-contiguous "
          "float64 buffer whose centering stays inside the float64 range). "
          "Pin table complete against fit's own call sites (self attrs passed: "
          "%s; locals passed: %s; literal kwargs passed: %s). "
          "Pins observed load-bearing: %s. "
          "Observations: %s."
          % (PIN_FIT_INTERCEPT, PIN_NORMALIZE, PIN_PRECOMPUTE, PIN_MAX_ITER,
             PIN_POSITIVE, PIN_VERBOSE, ",".join(attrs), ",".join(names),
             ",".join(lits),
             ",".join("%s x%d" % (k, v) for k, v in sorted(pin_hits.items())),
             tally.report()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
