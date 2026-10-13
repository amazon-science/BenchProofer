# P2 adversarial audit — django__django-11206

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,41 +157,26 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
     p = decimal_pos
-    if p < 1:
-        p = 1
     shifted = exponent + p
     is_small = False  # type: bool
     if coeff == 0:
         is_small = True
     elif shifted < 0 and coeff < pow10(-shifted):
         is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
     if not is_small:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
         return result
     frac = []  # type: List[int]
     i = decimal_pos
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(frac)))
         Invariant(0 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
     result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,9 +157,6 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
     p = decimal_pos
     if p < 1:
         p = 1
@@ -167,31 +164,21 @@
     is_small = False  # type: bool
     if coeff == 0:
         is_small = True
-    elif shifted < 0 and coeff < pow10(-shifted):
+    elif shifted < 0 and coeff <= pow10(-shifted):
         is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
     if not is_small:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
         return result
     frac = []  # type: List[int]
     i = decimal_pos
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(frac)))
         Invariant(0 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
     result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,41 +157,19 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
-    p = decimal_pos
-    if p < 1:
-        p = 1
-    shifted = exponent + p
-    is_small = False  # type: bool
-    if coeff == 0:
-        is_small = True
-    elif shifted < 0 and coeff < pow10(-shifted):
-        is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
-    if not is_small:
+    if coeff != 0:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
         return result
     frac = []  # type: List[int]
     i = decimal_pos
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(frac)))
         Invariant(0 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
     result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,9 +157,6 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
     p = decimal_pos
     if p < 1:
         p = 1
@@ -169,29 +166,19 @@
         is_small = True
     elif shifted < 0 and coeff < pow10(-shifted):
         is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
     if not is_small:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
         return result
     frac = []  # type: List[int]
     i = decimal_pos
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(frac)))
-        Invariant(0 <= i and i <= decimal_pos)
+        Invariant(1 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
     result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,9 +157,6 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
     p = decimal_pos
     if p < 1:
         p = 1
@@ -169,29 +166,8 @@
         is_small = True
     elif shifted < 0 and coeff < pow10(-shifted):
         is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
     if not is_small:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
-    if decimal_pos == 0:
-        result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
-        return result
-    frac = []  # type: List[int]
-    i = decimal_pos
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(frac)))
-        Invariant(0 <= i and i <= decimal_pos)
-        Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
-        frac = [48] + frac
-        i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
-    result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
+    result = []  # type: List[int]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,41 +157,17 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
-    p = decimal_pos
-    if p < 1:
-        p = 1
-    shifted = exponent + p
-    is_small = False  # type: bool
-    if coeff == 0:
-        is_small = True
-    elif shifted < 0 and coeff < pow10(-shifted):
-        is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
-    if not is_small:
-        return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
         return result
     frac = []  # type: List[int]
     i = decimal_pos
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(frac)))
         Invariant(0 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
     result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -157,9 +157,6 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
     p = decimal_pos
     if p < 1:
         p = 1
@@ -169,29 +166,19 @@
         is_small = True
     elif shifted < 0 and coeff < pow10(-shifted):
         is_small = True
-    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
     if not is_small:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
-        Assert(ToSeq(result) == zero_render(decimal_pos))
         return result
     frac = []  # type: List[int]
     i = decimal_pos
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(frac)))
         Invariant(0 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
-    Assert(ToSeq(frac) == zeros(decimal_pos))
-    result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
-    Assert(ToSeq(result) == zero_render(decimal_pos))
+    result = [48] + frac
     return result
     # impl-end
```

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -157,9 +157,6 @@
                     opt_seq(Result()) == zero_render(decimal_pos)))
     # post-conditions-end
     # impl-start
-    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
-    # is treated as zero and rendered as a padded zero, otherwise this routine
-    # contributes nothing and the ordinary path takes over.
     p = decimal_pos
     if p < 1:
         p = 1
@@ -167,14 +164,13 @@
     is_small = False  # type: bool
     if coeff == 0:
         is_small = True
-    elif shifted < 0 and coeff < pow10(-shifted):
-        is_small = True
+    else:
+        if shifted < 0:
+            if coeff < pow10(-shifted):
+                is_small = True
     Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
     if not is_small:
         return None
-    # Build the padded-zero rendering. When at least one fractional place is
-    # requested, build the run of zero digits by prepending (matching the
-    # front-recursive `zeros`), then prefix the '0' and decimal separator.
     if decimal_pos == 0:
         result = [48]  # type: List[int]
         Assert(ToSeq(result) == zero_render(decimal_pos))
@@ -182,16 +178,13 @@
     frac = []  # type: List[int]
     i = decimal_pos
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(frac)))
         Invariant(0 <= i and i <= decimal_pos)
         Invariant(ToSeq(frac) == zeros(decimal_pos - i))
-        # invariants-end
         frac = [48] + frac
         i = i - 1
     Assert(ToSeq(frac) == zeros(decimal_pos))
     result = [48, 46] + frac
-    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
     Assert(ToSeq(result) == zero_render(decimal_pos))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11206.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric formatter is asked to render an exact base-ten value with a given
  count of visible fractional places ``decimal_pos``. The value is presented by
  its non-negative magnitude written as ``coeff * 10**exponent`` (``coeff`` the
  integer formed by its significant digits, ``exponent`` the power-of-ten
  scale), exactly as an exact base-ten number decomposes.

  The desired behaviour, derived from the problem statement and the magnitudes
  it discusses, is:

    (1) A value whose magnitude is strictly smaller than the smallest quantity
        the visible fractional window can represent is indistinguishable, at
        the requested precision, from nothing: it must be rendered as a plain
        zero padded to the requested precision, NOT in any wider/exponential
        form. The visibility threshold is ``10 ** -p`` where ``p`` is
        ``decimal_pos`` but never less than one (a request for zero fractional
        places still measures smallness against the tenths place). The
        comparison is STRICT: a magnitude exactly equal to the threshold is
        still visible and is NOT collapsed.

    (2) The plain-zero rendering at precision ``decimal_pos`` is the digit zero,
        followed -- only when at least one fractional place is requested -- by
        the decimal separator and exactly ``decimal_pos`` zero digits.

    (3) When the magnitude is at or above the visibility threshold the value is
        left for the ordinary formatting path: this routine reports "no
        collapse" (the absent value) and contributes no rendering of its own.

  The smallness decision is the changed behaviour and is modelled deeply over
  exact integer arithmetic (cross-multiplying the threshold away); the floor of
  one on the threshold exponent at zero requested places is part of that
  decision. The decomposition of an exact base-ten value into
  ``(coeff, exponent)`` and the magnitude/threshold comparison are the
  type-refinement boundary documented in mapping.md (and validated against the
  real arithmetic by axiom_check.py).

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the rendered output is carried by ``PSeq[int]``. The absent value
("no collapse, fall through to ordinary formatting") is ``None``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The smallness decision
#  and the plain-zero rendering are the changed behaviour and are modelled
#  deeply below over exact integer arithmetic. The decomposition of an exact
#  base-ten value into (coeff, exponent), the magnitude comparison, and the
#  zero-padding are the type-refinement boundary documented in mapping.md, not
#  axioms; their equality to the real arithmetic is checked out-of-band by
#  axiom_check.py / G-AX, an A-reference, not a consumed @ContractOnly.)
# axioms-end


# pure-start
@Pure
def pow10(n: int) -> int:
    """``10 ** n`` for non-negative exponents ``n``."""
    Requires(n >= 0)
    Ensures(Result() >= 1)
    if n == 0:
        return 1
    return 10 * pow10(n - 1)


@Pure
def threshold_exp(decimal_pos: int) -> int:
    """The exponent ``p`` of the visibility threshold ``10 ** -p``: the number
    of requested fractional places, but never less than one."""
    Requires(decimal_pos >= 0)
    Ensures(Result() >= 1)
    if decimal_pos >= 1:
        return decimal_pos
    return 1


@Pure
def below_cutoff(coeff: int, exponent: int, decimal_pos: int) -> bool:
    """Whether the magnitude ``coeff * 10**exponent`` is STRICTLY below the
    visibility threshold ``10 ** -threshold_exp(decimal_pos)``.

    Cross-multiplying the threshold away (multiply both sides by the positive
    ``10 ** threshold_exp``), the magnitude is below the threshold iff
    ``coeff * 10**(exponent + threshold_exp) < 1``. With ``coeff >= 0`` this is:
    a zero magnitude is always below; otherwise it is below exactly when the
    shifted scale ``exponent + threshold_exp`` is negative and ``coeff`` is
    smaller than ``10`` to that many places.
    """
    Requires(coeff >= 0)
    Requires(decimal_pos >= 0)
    if coeff == 0:
        return True
    if exponent + threshold_exp(decimal_pos) >= 0:
        return False
    return coeff < pow10(-(exponent + threshold_exp(decimal_pos)))


@Pure
def zeros(n: int) -> PSeq[int]:
    """A run of ``n`` zero digits (code point 48), front-recursive."""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n == 0:
        return PSeq(48).take(0)
    return PSeq(48) + zeros(n - 1)


@Pure
def zero_render(decimal_pos: int) -> PSeq[int]:
    """The plain-zero rendering at precision ``decimal_pos``: the digit zero
    (48), then -- only when at least one fractional place is requested -- the
    decimal separator (46) and ``decimal_pos`` zero digits."""
    Requires(decimal_pos >= 0)
    if decimal_pos == 0:
        return PSeq(48)
    return PSeq(48, 46) + zeros(decimal_pos)


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional rendering: its code points when a
    rendering is produced, the empty sequence when none is. Guards the None case
    so the spec can compare a produced rendering without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)
# pure-end


def format_small(coeff: int, exponent: int, decimal_pos: int) -> Optional[List[int]]:
    # pre-conditions-start
    # The value's non-negative magnitude is `coeff * 10**exponent`; `coeff` is
    # the integer formed by its significant digits, `exponent` its scale.
    Requires(coeff >= 0)
    Requires(decimal_pos >= 0)
    # pre-conditions-end
    # post-conditions-start
    # (1)/(3) A rendering is produced exactly when the magnitude is strictly
    # below the visibility threshold; otherwise the absent value is returned so
    # the ordinary formatting path governs.
    Ensures(Implies(not below_cutoff(coeff, exponent, decimal_pos),
                    Result() is None))
    Ensures(Implies(below_cutoff(coeff, exponent, decimal_pos),
                    Result() is not None))
    # Full write permission to the freshly built rendering when one is produced.
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    # (2) Otherwise the produced rendering equals exactly the plain-zero
    # rendering (compared through `opt_seq`, which guards the None case).
    Ensures(Implies(below_cutoff(coeff, exponent, decimal_pos),
                    opt_seq(Result()) == zero_render(decimal_pos)))
    # post-conditions-end
    # impl-start
    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
    # is treated as zero and rendered as a padded zero, otherwise this routine
    # contributes nothing and the ordinary path takes over.
    p = decimal_pos
    if p < 1:
        p = 1
    shifted = exponent + p
    is_small = False  # type: bool
    if coeff == 0:
        is_small = True
    elif shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
    if not is_small:
        return None
    # Build the padded-zero rendering. When at least one fractional place is
    # requested, build the run of zero digits by prepending (matching the
    # front-recursive `zeros`), then prefix the '0' and decimal separator.
    if decimal_pos == 0:
        result = [48]  # type: List[int]
        Assert(ToSeq(result) == zero_render(decimal_pos))
        return result
    frac = []  # type: List[int]
    i = decimal_pos
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(frac)))
        Invariant(0 <= i and i <= decimal_pos)
        Invariant(ToSeq(frac) == zeros(decimal_pos - i))
        # invariants-end
        frac = [48] + frac
        i = i - 1
    Assert(ToSeq(frac) == zeros(decimal_pos))
    result = [48, 46] + frac
    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
    Assert(ToSeq(result) == zero_render(decimal_pos))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-11206 (nagini). Verifier: SBN_VERIFY_TIMEOUT=600 bash scripts/nagini_verify.sh; same-spec/weakness: python -m swebench_unified.adversary; resolve: swebench_unified.harness.run_resolve via docker.

SPEC SHAPE: format_small(coeff,exponent,decimal_pos) has a fully-pinned modeled I/O. Postconditions pin Result()isNone <-> not below_cutoff, AND when below_cutoff, opt_seq(Result)==zero_render(decimal_pos) (exact code-point content). So any verifying same-spec impl must match the gold decision AND rendering on the modeled domain.

### ATTACKS (all same-spec SAME, confirmed via adversary same-spec):
- atk_1 (boundary): drop the floor-to-1 on p (p=decimal_pos). VERIFY FAIL on Implies(not below_cutoff, Result is None) [15.9s]. REJECTED.
- atk_2 (boundary): non-strict '<=' instead of '<' in the cross-multiplied test. VERIFY FAIL on Implies(not below_cutoff, Result is None) [13.9s]. REJECTED.
- atk_3 (partial-domain): collapse only coeff==0, small nonzero falls through. VERIFY FAIL on Implies(below_cutoff, Result is not None) [13.8s]. REJECTED.
- atk_4 (boundary render): pad decimal_pos-1 zeros. VERIFY FAIL on Implies(below_cutoff, opt_seq(Result)==zero_render) [15.0s]. REJECTED.
- atk_5 (control-flow-effect): return non-None but empty list on collapse. VERIFY FAIL on opt_seq==zero_render clause [13.6s]. REJECTED.
- atk_6 (over-collapse/ungrounded): always return zero_render ignoring decision. VERIFY FAIL on Implies(not below_cutoff, Result is None) [13.4s]. REJECTED.
- atk_7 (render boundary): omit the '.' separator (48 + zeros only). VERIFY FAIL on opt_seq==zero_render clause [15.7s]. REJECTED.
- atk_echo (correct impl, control-flow rewrite: nested- if decision + explicit Asserts): adversary weakness => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 16.2s). Per protocol materialized faithful refined patch (= gold guard; behaviorally identical to gold hunk body, diff-confirmed) and RAN run_resolve('django__django-11206', ..., timeout=1800): RESOLVED=True, COMPLETED=True, FLAKY=False. So this verifying candidate RESOLVES -> NOT a weakness (consistent with the resolve-step policy).

BASELINES: pos_control (byte-identical model.py) VERIFIES [16.4s]. prepatch (model_prepatch.py, no smallness guard, return None) VERIFY FAIL on Implies(below_cutoff, Result is not None) [14.7s] -- prepatch bug reproduced exactly as refinement.md predicts (G-DIFF).

A-LEG / correspondence audit: axioms region is EMPTY (no A-consumed axiom; model.py lines 50-58 confirm). refinement.md legs are all R (steps 1,2,3), A-reference (step 4 below_cutoff<->real abs(number)<cutoff; step 6 zero_render<->real Decimal('0') rendering), or I+R (step 5 None fall-through). No kind-3 step. Ran axiom_check.py (G-AX): EXIT 0 -- 'below_cutoff deep model (== real abs(number) < Decimal(0.+1.rjust(dp,0))) sound on boundary + exact-edge + 200000 fuzz; zero_render deep model (== real Decimal(0) rendering) sound on decimal_pos 0..32.' So both A-reference legs' correspondence to the real callees holds, including the STRICT-edge (magnitude == cutoff is NOT collapsed).

CONCLUSION: The frozen spec rejects every distinct wrong impl (7 attacks + prepatch bug across all four axes: boundary, partial-domain, control-flow-effect, ungrounded/over-collapse render), the positive control verifies, the one verifying same-spec candidate's faithful patch RESOLVES under the official harness, G-AX confirms the A-reference arithmetic, and refinement.md has no A-consumed/kind-3 legs. verify(model) => resolved holds on this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11206.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A numeric formatter is asked to render an exact base-ten value with a given
  count of visible fractional places ``decimal_pos``. The value is presented by
  its non-negative magnitude written as ``coeff * 10**exponent`` (``coeff`` the
  integer formed by its significant digits, ``exponent`` the power-of-ten
  scale), exactly as an exact base-ten number decomposes.

  The desired behaviour, derived from the problem statement and the magnitudes
  it discusses, is:

    (1) A value whose magnitude is strictly smaller than the smallest quantity
        the visible fractional window can represent is indistinguishable, at
        the requested precision, from nothing: it must be rendered as a plain
        zero padded to the requested precision, NOT in any wider/exponential
        form. The visibility threshold is ``10 ** -p`` where ``p`` is
        ``decimal_pos`` but never less than one (a request for zero fractional
        places still measures smallness against the tenths place). The
        comparison is STRICT: a magnitude exactly equal to the threshold is
        still visible and is NOT collapsed.

    (2) The plain-zero rendering at precision ``decimal_pos`` is the digit zero,
        followed -- only when at least one fractional place is requested -- by
        the decimal separator and exactly ``decimal_pos`` zero digits.

    (3) When the magnitude is at or above the visibility threshold the value is
        left for the ordinary formatting path: this routine reports "no
        collapse" (the absent value) and contributes no rendering of its own.

  The smallness decision is the changed behaviour and is modelled deeply over
  exact integer arithmetic (cross-multiplying the threshold away); the floor of
  one on the threshold exponent at zero requested places is part of that
  decision. The decomposition of an exact base-ten value into
  ``(coeff, exponent)`` and the magnitude/threshold comparison are the
  type-refinement boundary documented in mapping.md (and validated against the
  real arithmetic by axiom_check.py).

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the rendered output is carried by ``PSeq[int]``. The absent value
("no collapse, fall through to ordinary formatting") is ``None``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The smallness decision
#  and the plain-zero rendering are the changed behaviour and are modelled
#  deeply below over exact integer arithmetic. The decomposition of an exact
#  base-ten value into (coeff, exponent), the magnitude comparison, and the
#  zero-padding are the type-refinement boundary documented in mapping.md, not
#  axioms; their equality to the real arithmetic is checked out-of-band by
#  axiom_check.py / G-AX, an A-reference, not a consumed @ContractOnly.)
# axioms-end


# pure-start
@Pure
def pow10(n: int) -> int:
    """``10 ** n`` for non-negative exponents ``n``."""
    Requires(n >= 0)
    Ensures(Result() >= 1)
    if n == 0:
        return 1
    return 10 * pow10(n - 1)


@Pure
def threshold_exp(decimal_pos: int) -> int:
    """The exponent ``p`` of the visibility threshold ``10 ** -p``: the number
    of requested fractional places, but never less than one."""
    Requires(decimal_pos >= 0)
    Ensures(Result() >= 1)
    if decimal_pos >= 1:
        return decimal_pos
    return 1


@Pure
def below_cutoff(coeff: int, exponent: int, decimal_pos: int) -> bool:
    """Whether the magnitude ``coeff * 10**exponent`` is STRICTLY below the
    visibility threshold ``10 ** -threshold_exp(decimal_pos)``.

    Cross-multiplying the threshold away (multiply both sides by the positive
    ``10 ** threshold_exp``), the magnitude is below the threshold iff
    ``coeff * 10**(exponent + threshold_exp) < 1``. With ``coeff >= 0`` this is:
    a zero magnitude is always below; otherwise it is below exactly when the
    shifted scale ``exponent + threshold_exp`` is negative and ``coeff`` is
    smaller than ``10`` to that many places.
    """
    Requires(coeff >= 0)
    Requires(decimal_pos >= 0)
    if coeff == 0:
        return True
    if exponent + threshold_exp(decimal_pos) >= 0:
        return False
    return coeff < pow10(-(exponent + threshold_exp(decimal_pos)))


@Pure
def zeros(n: int) -> PSeq[int]:
    """A run of ``n`` zero digits (code point 48), front-recursive."""
    Requires(n >= 0)
    Ensures(len(Result()) == n)
    if n == 0:
        return PSeq(48).take(0)
    return PSeq(48) + zeros(n - 1)


@Pure
def zero_render(decimal_pos: int) -> PSeq[int]:
    """The plain-zero rendering at precision ``decimal_pos``: the digit zero
    (48), then -- only when at least one fractional place is requested -- the
    decimal separator (46) and ``decimal_pos`` zero digits."""
    Requires(decimal_pos >= 0)
    if decimal_pos == 0:
        return PSeq(48)
    return PSeq(48, 46) + zeros(decimal_pos)


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional rendering: its code points when a
    rendering is produced, the empty sequence when none is. Guards the None case
    so the spec can compare a produced rendering without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)
# pure-end


def format_small(coeff: int, exponent: int, decimal_pos: int) -> Optional[List[int]]:
    # pre-conditions-start
    # The value's non-negative magnitude is `coeff * 10**exponent`; `coeff` is
    # the integer formed by its significant digits, `exponent` its scale.
    Requires(coeff >= 0)
    Requires(decimal_pos >= 0)
    # pre-conditions-end
    # post-conditions-start
    # (1)/(3) A rendering is produced exactly when the magnitude is strictly
    # below the visibility threshold; otherwise the absent value is returned so
    # the ordinary formatting path governs.
    Ensures(Implies(not below_cutoff(coeff, exponent, decimal_pos),
                    Result() is None))
    Ensures(Implies(below_cutoff(coeff, exponent, decimal_pos),
                    Result() is not None))
    # Full write permission to the freshly built rendering when one is produced.
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    # (2) Otherwise the produced rendering equals exactly the plain-zero
    # rendering (compared through `opt_seq`, which guards the None case).
    Ensures(Implies(below_cutoff(coeff, exponent, decimal_pos),
                    opt_seq(Result()) == zero_render(decimal_pos)))
    # post-conditions-end
    # impl-start
    # The visibility threshold is 10 ** -p; a magnitude strictly smaller than it
    # is treated as zero and rendered as a padded zero, otherwise this routine
    # contributes nothing and the ordinary path takes over.
    p = decimal_pos
    if p < 1:
        p = 1
    shifted = exponent + p
    is_small = False  # type: bool
    if coeff == 0:
        is_small = True
    elif shifted < 0 and coeff < pow10(-shifted):
        is_small = True
    Assert(is_small == below_cutoff(coeff, exponent, decimal_pos))
    if not is_small:
        return None
    # Build the padded-zero rendering. When at least one fractional place is
    # requested, build the run of zero digits by prepending (matching the
    # front-recursive `zeros`), then prefix the '0' and decimal separator.
    if decimal_pos == 0:
        result = [48]  # type: List[int]
        Assert(ToSeq(result) == zero_render(decimal_pos))
        return result
    frac = []  # type: List[int]
    i = decimal_pos
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(frac)))
        Invariant(0 <= i and i <= decimal_pos)
        Invariant(ToSeq(frac) == zeros(decimal_pos - i))
        # invariants-end
        frac = [48] + frac
        i = i - 1
    Assert(ToSeq(frac) == zeros(decimal_pos))
    result = [48, 46] + frac
    Assert(ToSeq(result) == PSeq(48, 46) + zeros(decimal_pos))
    Assert(ToSeq(result) == zero_render(decimal_pos))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-11206 (nagini). Verifier: SBN_VERIFY_TIMEOUT=600 bash scripts/nagini_verify.sh; same-spec/weakness: python -m swebench_unified.adversary; resolve: swebench_unified.harness.run_resolve via docker.

SPEC SHAPE: format_small(coeff,exponent,decimal_pos) has a fully-pinned modeled I/O. Postconditions pin Result()isNone <-> not below_cutoff, AND when below_cutoff, opt_seq(Result)==zero_render(decimal_pos) (exact code-point content). So any verifying same-spec impl must match the gold decision AND rendering on the modeled domain.

### ATTACKS (all same-spec SAME, confirmed via adversary same-spec):
- atk_1 (boundary): drop the floor-to-1 on p (p=decimal_pos). VERIFY FAIL on Implies(not below_cutoff, Result is None) [15.9s]. REJECTED.
- atk_2 (boundary): non-strict '<=' instead of '<' in the cross-multiplied test. VERIFY FAIL on Implies(not below_cutoff, Result is None) [13.9s]. REJECTED.
- atk_3 (partial-domain): collapse only coeff==0, small nonzero falls through. VERIFY FAIL on Implies(below_cutoff, Result is not None) [13.8s]. REJECTED.
- atk_4 (boundary render): pad decimal_pos-1 zeros. VERIFY FAIL on Implies(below_cutoff, opt_seq(Result)==zero_render) [15.0s]. REJECTED.
- atk_5 (control-flow-effect): return non-None but empty list on collapse. VERIFY FAIL on opt_seq==zero_render clause [13.6s]. REJECTED.
- atk_6 (over-collapse/ungrounded): always return zero_render ignoring decision. VERIFY FAIL on Implies(not below_cutoff, Result is None) [13.4s]. REJECTED.
- atk_7 (render boundary): omit the '.' separator (48 + zeros only). VERIFY FAIL on opt_seq==zero_render clause [15.7s]. REJECTED.
- atk_echo (correct impl, control-flow rewrite: nested- if decision + explicit Asserts): adversary weakness => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 16.2s). Per protocol materialized faithful refined patch (= gold guard; behaviorally identical to gold hunk body, diff-confirmed) and RAN run_resolve('django__django-11206', ..., timeout=1800): RESOLVED=True, COMPLETED=True, FLAKY=False. So this verifying candidate RESOLVES -> NOT a weakness (consistent with the resolve-step policy).

BASELINES: pos_control (byte-identical model.py) VERIFIES [16.4s]. prepatch (model_prepatch.py, no smallness guard, return None) VERIFY FAIL on Implies(below_cutoff, Result is not None) [14.7s] -- prepatch bug reproduced exactly as refinement.md predicts (G-DIFF).

A-LEG / correspondence audit: axioms region is EMPTY (no A-consumed axiom; model.py lines 50-58 confirm). refinement.md legs are all R (steps 1,2,3), A-reference (step 4 below_cutoff<->real abs(number)<cutoff; step 6 zero_render<->real Decimal('0') rendering), or I+R (step 5 None fall-through). No kind-3 step. Ran axiom_check.py (G-AX): EXIT 0 -- 'below_cutoff deep model (== real abs(number) < Decimal(0.+1.rjust(dp,0))) sound on boundary + exact-edge + 200000 fuzz; zero_render deep model (== real Decimal(0) rendering) sound on decimal_pos 0..32.' So both A-reference legs' correspondence to the real callees holds, including the STRICT-edge (magnitude == cutoff is NOT collapsed).

CONCLUSION: The frozen spec rejects every distinct wrong impl (7 attacks + prepatch bug across all four axes: boundary, partial-domain, control-flow-effect, ungrounded/over-collapse render), the positive control verifies, the one verifying same-spec candidate's faithful patch RESOLVES under the official harness, G-AX confirms the A-reference arithmetic, and refinement.md has no A-consumed/kind-3 legs. verify(model) => resolved holds on this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verified for django__django-11206 nagini bundle (format_small models the small-magnitude→padded-zero collapse the gold patch adds to django.utils.numberformat.format).

Checks performed:
1. Spec region byte-identical: `same-spec` on an identical copy returns SAME (exit 0). The Pure spec (pow10/threshold_exp/below_cutoff/zeros/zero_render/opt_seq) and pre/post-conditions are the frozen spec.
2. G-AX (bundle axiom_check.py) passes exit 0: below_cutoff == real `abs(number) < Decimal('0.'+'1'.rjust(dp,'0'))` and zero_render == real Decimal('0') render tail.
3. Independent WIDE differential vs the real patched format (gold hunk applied to base_commit 571ab44e checkout): 700k+ inputs, decimal_pos 0..400, coefficients up to 20 digits, non-normalized Decimals with trailing zeros, both signs, and the >200-digit scientific-notation branch. For 'collapse' outputs the real result equals zero_render(dp); for 'fall-through' the real result equals the unchanged (base) rendering. Zero mismatches.
4. Decision-boundary hammering exactly at the cutoff 10**-max(dp,1) plus one-ulp above/below, dp 0..120: the STRICT `<` edge (abs == cutoff is NOT collapsed) matches the real Decimal comparison on every case; 300k additional fuzz — zero mismatches.

The type-refinement boundary is sound: threshold_exp = max(dp,1) faithfully captures the '1'.rjust(dp,'0') quirk (cutoff 10**-1 at dp in {0,1}); the cross-multiplied integer test coeff*10**(exponent+p) < 1 is exactly equivalent to abs(number) < cutoff for coeff>=0; zero_render matches the real post-collapse rendering. The modeled domain (decimal_pos is not None, non-negative; '.' separator; magnitude via abs decomposition) matches the patch's guarded call. No too-strong postcondition and no drift from real repo behavior within the modeled domain was found. Spec is FAITHFUL — not a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over model.py) discloses nothing about the gold edit beyond the public problem_statement. Public problem_statement already states the fix: when decimal_pos is supplied and the number is smaller in absolute size than what decimal_pos can encode, return '0.0000...000' instead of exponential notation, with witnesses nformat(1e-199,dp=2)='0.00' and nformat(1e-200,dp=2)='1.00e-200' (the bug), and names the cause ('hardcoded cut-off point'). The spec view expresses exactly this behavior abstractly: small magnitude (coeff*10**exponent) below visibility threshold 10**-p collapses to a padded plain zero, not a wider/exponential form; at-or-above threshold falls through. It carries NO gold-edit mechanics: no diff markers, no 'django/utils/numberformat.py' path/module, no repo symbols (Decimal, cutoff, rjust, abs(number), the guard-insertion site, number=Decimal('0')), and no reproduced gold-patch line. The only patch-changed distinctive symbol is the non-distinctive 'format', which does not appear. Added formal precision (STRICT edge at magnitude==threshold; threshold floored to >=1 at decimal_pos=0) are legitimate behavioral spec obligations, not disclosures of the edit's structure or location. Comments carry no bug/fix/patch narration ('changed behaviour' is modeling meta-language, and the problem statement already localizes the change to smallness handling). Mechanical G-LEAK screen (leakage.screen) returns passed=True with zero hard_failures, corroborating the lexical half. G-PANEL-3 semantic judgment: no leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
