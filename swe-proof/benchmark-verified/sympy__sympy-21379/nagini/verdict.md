# P2 adversarial audit — sympy__sympy-21379

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,40 +165,17 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
+    # PRE-PATCH SKELETON: the factor-producing call is made UNGUARDED (no
+    # try/except). For the input the helper cannot answer (code 2) it raises and
+    # the raise escapes straight to the caller, so the operation does NOT always
+    # complete — the spec's no-exception obligation (clause 1) fails. This is the
+    # bug the patch fixes.
     pr = p
     qr = q
-    try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
-        G = common_factor_compute(code)
-        Assert(G == common_factor(code))
-        Assert(code == 0 or code == 1)
-        G = common_factor(code)
-        if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
-            pr = divide_out(p, G)
-            qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
-        return build_result(G, pr, qr)
-    except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
-        return build_result(1, pr, qr)
+    G = common_factor_compute(code)
+    G = common_factor(code)
+    if G != 1:
+        pr = divide_out(p, G)
+        qr = divide_out(q, G)
+    return build_result(G, pr, qr)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,40 +165,14 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
+
     pr = p
     qr = q
     try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
         G = common_factor_compute(code)
-        Assert(G == common_factor(code))
         Assert(code == 0 or code == 1)
         G = common_factor(code)
-        if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
-            pr = divide_out(p, G)
-            qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
         return build_result(G, pr, qr)
     except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
         return build_result(1, pr, qr)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,40 +165,16 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
+
     pr = p
     qr = q
     try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
         G = common_factor_compute(code)
-        Assert(G == common_factor(code))
         Assert(code == 0 or code == 1)
         G = common_factor(code)
         if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
             pr = divide_out(p, G)
-            qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
         return build_result(G, pr, qr)
     except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
         return build_result(1, pr, qr)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,40 +165,21 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
+
     pr = p
     qr = q
+    n = 0
+    while n >= 0:
+        Invariant(n >= 0)
+        n = n + 1
     try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
         G = common_factor_compute(code)
-        Assert(G == common_factor(code))
         Assert(code == 0 or code == 1)
         G = common_factor(code)
         if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
             pr = divide_out(p, G)
             qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
         return build_result(G, pr, qr)
     except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
         return build_result(1, pr, qr)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,40 +165,17 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
+
     pr = p
     qr = q
     try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
         G = common_factor_compute(code)
-        Assert(G == common_factor(code))
         Assert(code == 0 or code == 1)
         G = common_factor(code)
         if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
             pr = divide_out(p, G)
             qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
         return build_result(G, pr, qr)
     except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
-        return build_result(1, pr, qr)
+        return build_result(0, pr, qr)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,40 +165,6 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
-    pr = p
-    qr = q
-    try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
-        G = common_factor_compute(code)
-        Assert(G == common_factor(code))
-        Assert(code == 0 or code == 1)
-        G = common_factor(code)
-        if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
-            pr = divide_out(p, G)
-            qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
-        return build_result(G, pr, qr)
-    except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
-        return build_result(1, pr, qr)
+
+    return build_result(1, p, q)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -165,40 +165,14 @@
                     Result() == build_result(common_factor(code), p, q)))
     # post-conditions-end
     # impl-start
-    # pr, qr are the operands as they enter the result: unchanged unless the
-    # factor is not the identity, in which case each is passed through the
-    # transform helper. The parameters p, q are read-only and keep their original
-    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
-    # ...) refer to the operands as given (directive 5: read-only inputs are not
-    # mutated).
+
     pr = p
     qr = q
-    try:
-        # The single factor-producing call. Its raising facet
-        # (common_factor_compute) raises for the unanswerable input (code 2); for
-        # an answerable input it returns the factor, whose value is the helper's
-        # own pure-facet output common_factor(code). On normal completion this
-        # establishes code in {0, 1}, so the value facet is well-defined and the
-        # factor G is exactly common_factor(code).
-        G = common_factor_compute(code)
-        Assert(G == common_factor(code))
-        Assert(code == 0 or code == 1)
-        G = common_factor(code)
-        if G != 1:
-            # factor is not the identity: pass each operand through the transform
-            # helper, then build the value from the transformed operands. Because
-            # G is common_factor(code) and divide_out is opaque, the transformed
-            # operands are exactly the postcondition's witnesses (clause 3a) — an
-            # implementation that skips this step cannot discharge them.
-            pr = divide_out(p, G)
-            qr = divide_out(q, G)
-        # On normal completion the operands were transformed exactly when
-        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
-        return build_result(G, pr, qr)
-    except FactorUnavailable:
-        # the unanswerable input: keep the identity factor; the operands enter
-        # the value unchanged. The raise occurs only for code 2
-        # (common_factor_compute's Exsures guard), so this handler runs only
-        # there; pr, qr are still their original p, q (never reassigned).
+    if code == 2:
         return build_result(1, pr, qr)
+    G = common_factor(code)
+    if G != 1:
+        pr = divide_out(p, G)
+        qr = divide_out(q, G)
+    return build_result(G, pr, qr)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-21379.

Behaviour under specification (an abstract behavioural contract, not an edit):

  An operation finishes by producing a single value built from a scalar (call it
  the factor) together with its two operands. The factor comes from a helper that
  is defined for most inputs but, for some inputs, has no defined answer and
  reports that by raising. The operation classifies its input by an integer code
  selecting exactly one of three cases the contract distinguishes.

  The behaviour pinned here, in terms of the value the operation returns:

    (1) The operation ALWAYS completes for every input it is given: it does not
        let the helper's raise escape to its own caller.

    (2) For the input the helper cannot answer (code 2), the value is built from
        the identity factor (1) and the two operands exactly as given: neither
        operand is transformed.

    (3) For an input the helper can answer (code 0 or 1), the value is built from
        the factor the helper returns and the two operands. If that factor is the
        identity (1), the operands enter the value unchanged; if it is something
        other than the identity, each operand is FIRST passed through the
        transform helper (parameterised by the factor) and the value is built
        from those transformed operands. (An implementation that builds the value
        from the untransformed operands when the factor is not the identity does
        NOT satisfy the contract.)

The two operands are rich objects abstracted by integer value carriers; the
input is abstracted by an integer code selecting the case. The factor the helper
returns, the transformed operand value, and the built result are all OPAQUE axiom
values (so every part of the postcondition is grounded in the modeled
computation rather than a literal an implementation could echo; SPEC_GUIDE §8).
The helper's "no defined answer" is reported by a user-defined exception (a
builtin exception in an ``Exsures`` crashes the Nagini translator; mapping.md §2).

The operation is a bounded, straight-line computation: it MUST terminate and
actually DELIVER its value to the caller (a total-correctness obligation,
carried as ``MustTerminate`` in the precondition). Nagini is a
partial-correctness verifier by default, so without this obligation an
implementation that diverges before returning (e.g. an unbounded loop inserted
ahead of the factor-producing call) would satisfy every value postcondition
vacuously yet would hang the operation — and the reported scenario — forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FactorUnavailable(Exception):
    """Signals that the helper has no defined answer for the given input (code 2)
    and reports it by raising. A user-defined exception stands in because a
    builtin exception in an ``Exsures`` crashes the Nagini translator
    (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def common_factor(code: int) -> int:
    """The factor the helper yields, as a value (the cases it can answer, codes 0
    and 1). For code 1 it is the identity (1); for code 0 it is something other
    than the identity (!= 1). The exact non-identity value is OPAQUE (unpinned),
    so a caller can obtain it only by invoking the helper, never by fabricating a
    literal (SPEC_GUIDE §8). Weakest contract the proof needs; provenance +
    soundness check in mapping.md / axiom_check.py.
    """
    Requires(code == 0 or code == 1)
    Ensures(Implies(code == 1, Result() == 1))
    Ensures(Implies(code == 0, Result() != 1))


@ContractOnly
def common_factor_compute(code: int) -> int:
    """The helper as actually CALLED: it returns the factor for the cases it can
    answer (codes 0, 1) but, for the input it cannot answer (code 2), raises
    ``FactorUnavailable``. Its normal return equals ``common_factor(code)``.
    Non-pure (it may raise), so it is used only in the implementation, never
    inside an ``Ensures``.
    """
    Requires(0 <= code and code <= 2)
    # The real helper is a bounded computation: the single call always finishes
    # (normally or by raising). The strictly smaller measure (1 < 2) lets the
    # contracted caller holding MustTerminate(2) invoke it without leaking its
    # own termination obligation.
    Requires(MustTerminate(1))
    Ensures(code != 2)
    Ensures(Result() == common_factor(code))
    Exsures(FactorUnavailable, code == 2)


@Pure
@ContractOnly
def divide_out(value: int, factor: int) -> int:
    """The transform helper: maps one operand to a new value, parameterised by
    the factor. Pure; the exact result is OPAQUE — nothing constrains it to equal
    the input, so an implementation can produce ``divide_out(value, factor)``
    only by actually invoking the helper, never by leaving the operand untouched
    (SPEC_GUIDE §8). Applied only when ``factor != 1``.
    """
    Requires(factor != 1)


@Pure
@ContractOnly
def build_result(factor: int, p: int, q: int) -> int:
    """The result-construction step: the operation's returned value is built from
    the factor together with the two (possibly transformed) operands. OPAQUE —
    two applications are equal only when their three arguments are provably
    equal, so the value observably depends on whether each operand was
    transformed (SPEC_GUIDE §8).
    """
    Ensures(True)
# axioms-end


# pure-start
# (no derived pure spec helpers: the operand-shape branch is concrete integer
# control flow over the axiomatized callees above.)
# pure-end


def reduce_extract_common_factor(code: int, p: int, q: int) -> int:
    # pre-conditions-start
    # The input is classified into exactly one of three cases: a factor other
    # than the identity (0), the identity factor (1), or the case the helper
    # cannot answer (2).
    Requires(0 <= code and code <= 2)
    # Total correctness: the operation is a bounded, straight-line computation
    # over the helpers and MUST terminate and deliver its value (measure 2
    # leaves room for the factor-producing sub-call's own MustTerminate(1)
    # obligation). Nagini is a partial-correctness verifier by default, so
    # without this obligation an implementation that diverges before returning
    # (e.g. an unbounded loop ahead of the factor-producing call) satisfies
    # every value postcondition vacuously yet would hang the operation — and
    # the reported scenario — forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (1) The operation ALWAYS completes — it never lets the helper's raise
    #     escape to its caller. There is NO Exsures, so the spec requires the
    #     method to raise no exception on any input.
    #
    # (2) For the input the helper cannot answer the value is built from the
    #     identity factor and the two operands exactly as given (neither operand
    #     is transformed).
    Ensures(Implies(code == 2, Result() == build_result(1, p, q)))
    # (3a) For an answerable input whose factor is NOT the identity, the factor is
    #      the helper's own (opaque) output and EACH operand is first passed
    #      through the transform helper before the value is built. Because
    #      divide_out is opaque, this is dischargeable only by an implementation
    #      that actually performs the transform — an implementation that builds
    #      the value from the untransformed operands cannot prove
    #      p == divide_out(p, ...) and so does NOT verify.
    Ensures(Implies(code != 2 and common_factor(code) != 1,
                    Result() == build_result(
                        common_factor(code),
                        divide_out(p, common_factor(code)),
                        divide_out(q, common_factor(code)))))
    # (3b) For an answerable input whose factor IS the identity, that factor is
    #      the helper's own (identity) output and the operands enter the value
    #      unchanged.
    Ensures(Implies(code != 2 and common_factor(code) == 1,
                    Result() == build_result(common_factor(code), p, q)))
    # post-conditions-end
    # impl-start
    # pr, qr are the operands as they enter the result: unchanged unless the
    # factor is not the identity, in which case each is passed through the
    # transform helper. The parameters p, q are read-only and keep their original
    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
    # ...) refer to the operands as given (directive 5: read-only inputs are not
    # mutated).
    pr = p
    qr = q
    try:
        # The single factor-producing call. Its raising facet
        # (common_factor_compute) raises for the unanswerable input (code 2); for
        # an answerable input it returns the factor, whose value is the helper's
        # own pure-facet output common_factor(code). On normal completion this
        # establishes code in {0, 1}, so the value facet is well-defined and the
        # factor G is exactly common_factor(code).
        G = common_factor_compute(code)
        Assert(G == common_factor(code))
        Assert(code == 0 or code == 1)
        G = common_factor(code)
        if G != 1:
            # factor is not the identity: pass each operand through the transform
            # helper, then build the value from the transformed operands. Because
            # G is common_factor(code) and divide_out is opaque, the transformed
            # operands are exactly the postcondition's witnesses (clause 3a) — an
            # implementation that skips this step cannot discharge them.
            pr = divide_out(p, G)
            qr = divide_out(q, G)
        # On normal completion the operands were transformed exactly when
        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
        return build_result(G, pr, qr)
    except FactorUnavailable:
        # the unanswerable input: keep the identity factor; the operands enter
        # the value unchanged. The raise occurs only for code 2
        # (common_factor_compute's Exsures guard), so this handler runs only
        # there; pr, qr are still their original p, q (never reassigned).
        return build_result(1, pr, qr)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Env: python; verifier via scripts/nagini_verify.sh.

SPEC SHAPE: postcondition pins the returned value in ALL THREE code branches via opaque axioms build_result / divide_out / common_factor, PLUS no-Exsures (must not raise on any input) PLUS Requires(MustTerminate(2)) (total correctness). Tight on all four surfaces.

SAME-SPEC: all 7 attacks + positive control returned same-spec exit 0 (spec byte-identical; only impl region edited).

POSITIVE CONTROL (pos_control.py = model.py): `bash scripts/nagini_verify.sh` exit 0 (verifies).

### ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-21379 <atk>`):
- atk_1.py (PREPATCH: unguarded common_factor_compute, no try/except): exit 2, NOT-A-COUNTEREXAMPLE. Direct verify signature: `error: Exhale might fail. Assertion "method raises no exceptions" might not hold.` -> prepatch bug REPRODUCED (no-exception obligation / clause 1).
- atk_2.py (keep try/except, DROP the operand transform, build from untransformed operands): exit 2, rejected -> clause 3a (opaque divide_out unprovable).
- atk_3.py (partial-domain: transform ONLY the first operand pr, leave qr untransformed): exit 2, rejected -> clause 3a on q.
- atk_4.py (control-flow/divergence: `while n>=0: n=n+1` unbounded loop ahead of the factor call): exit 2, rejected -> MustTerminate(2) has no decreasing measure.
- atk_5.py (boundary/effect: on FactorUnavailable return build_result(0,...) i.e. non-identity factor on refusal): exit 2, rejected -> clause 2 (code==2 => build_result(1,p,q)).
- atk_6.py (ungrounded-oracle echo: `return build_result(1, p, q)` unconditionally): exit 2, rejected -> clauses 2/3a (cannot match common_factor(code) opaque factor nor divide_out transform).
- atk_7.py (restructured control flow: `if code==2: return build_result(1,p,q)` decided FIRST, then G=common_factor(code), transform under G!=1, build; try scope effectively only around the factor call): exit 0 CANDIDATE, VERIFIES (11.6s).

CANDIDATE RESOLVE (MANDATORY): materialized atk_7's faithful refined patch at atk_7.patch.diff (wraps only `G = gcd(p,q)` in try/except PolynomialError -> G=S.One, leaves the gcd_terms transform outside the guard — faithful to atk_7's control flow). Ran official harness via swebench_unified.harness.run_resolve (timeout 1800, retries 1). RESULT: `[ATK7] resolved=True completed=True note='resolved'`. Gold control (benchmark-verified/.../patch.diff) run identically: `[GOLD] resolved=True`. atk_7 is a behavioral ECHO that RESOLVES -> per the resolve-based G-EQ/panel_1 policy (the audit protocol) a same-spec verifying impl whose faithful patch resolves is NOT a weakness. verify=>correct holds for it.

WHY atk_7's structural difference is benign on the tested inputs: gold wraps BOTH gcd and gcd_terms in the try; atk_7 wraps only gcd. They diverge ONLY if gcd_terms raises PolynomialError on a code-0 input where gcd itself succeeded — which does not occur on the F2P/P2P suite (harness confirms resolved). No tested input exercises that gap, so no counterexample exists on the oracle.

REFINEMENT AUDIT (refinement.md): legs A1(R), A2(A-consumed, gcd two-facet split), A3(R+A-consumed, gcd_terms), A4(R+A-consumed, Mul/Mod construction), A5(R+I, PolynomialError<->FactorUnavailable, S.One<->1). All R / A-consumed / I — NO kind-3, and section D explicitly declares NO A-reference (the changed op — the try/except wrapping — is modeled DIRECTLY in the impl with a no-Exsures postcondition, not hidden behind an axiom). The only consumed axioms cover UNCHANGED callees (gcd, gcd_terms, Mul/Mod); soundness checked by axiom_check.py / G-AX (code-0 !=1, code-1 ==1, code-2 Piecewise->raise, end-to-end F2P transform assertions). A-leg correspondence to real callees holds. sympy present locally (1.14.0) — G-AX proper run is in-container against the patched repo.

CONCLUSION: >=6 distinct wrong impls attacked (prepatch + drop-transform + partial-domain + divergence + wrong-refusal-factor + ungrounded-echo + restructured-echo). The one verifying candidate (atk_7) RESOLVES, so it is not a broken counterexample. Spec rejects every genuinely-incorrect impl. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-21379.

Behaviour under specification (an abstract behavioural contract, not an edit):

  An operation finishes by producing a single value built from a scalar (call it
  the factor) together with its two operands. The factor comes from a helper that
  is defined for most inputs but, for some inputs, has no defined answer and
  reports that by raising. The operation classifies its input by an integer code
  selecting exactly one of three cases the contract distinguishes.

  The behaviour pinned here, in terms of the value the operation returns:

    (1) The operation ALWAYS completes for every input it is given: it does not
        let the helper's raise escape to its own caller.

    (2) For the input the helper cannot answer (code 2), the value is built from
        the identity factor (1) and the two operands exactly as given: neither
        operand is transformed.

    (3) For an input the helper can answer (code 0 or 1), the value is built from
        the factor the helper returns and the two operands. If that factor is the
        identity (1), the operands enter the value unchanged; if it is something
        other than the identity, each operand is FIRST passed through the
        transform helper (parameterised by the factor) and the value is built
        from those transformed operands. (An implementation that builds the value
        from the untransformed operands when the factor is not the identity does
        NOT satisfy the contract.)

The two operands are rich objects abstracted by integer value carriers; the
input is abstracted by an integer code selecting the case. The factor the helper
returns, the transformed operand value, and the built result are all OPAQUE axiom
values (so every part of the postcondition is grounded in the modeled
computation rather than a literal an implementation could echo; SPEC_GUIDE §8).
The helper's "no defined answer" is reported by a user-defined exception (a
builtin exception in an ``Exsures`` crashes the Nagini translator; mapping.md §2).

The operation is a bounded, straight-line computation: it MUST terminate and
actually DELIVER its value to the caller (a total-correctness obligation,
carried as ``MustTerminate`` in the precondition). Nagini is a
partial-correctness verifier by default, so without this obligation an
implementation that diverges before returning (e.g. an unbounded loop inserted
ahead of the factor-producing call) would satisfy every value postcondition
vacuously yet would hang the operation — and the reported scenario — forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FactorUnavailable(Exception):
    """Signals that the helper has no defined answer for the given input (code 2)
    and reports it by raising. A user-defined exception stands in because a
    builtin exception in an ``Exsures`` crashes the Nagini translator
    (mapping.md §2)."""


# axioms-start
@Pure
@ContractOnly
def common_factor(code: int) -> int:
    """The factor the helper yields, as a value (the cases it can answer, codes 0
    and 1). For code 1 it is the identity (1); for code 0 it is something other
    than the identity (!= 1). The exact non-identity value is OPAQUE (unpinned),
    so a caller can obtain it only by invoking the helper, never by fabricating a
    literal (SPEC_GUIDE §8). Weakest contract the proof needs; provenance +
    soundness check in mapping.md / axiom_check.py.
    """
    Requires(code == 0 or code == 1)
    Ensures(Implies(code == 1, Result() == 1))
    Ensures(Implies(code == 0, Result() != 1))


@ContractOnly
def common_factor_compute(code: int) -> int:
    """The helper as actually CALLED: it returns the factor for the cases it can
    answer (codes 0, 1) but, for the input it cannot answer (code 2), raises
    ``FactorUnavailable``. Its normal return equals ``common_factor(code)``.
    Non-pure (it may raise), so it is used only in the implementation, never
    inside an ``Ensures``.
    """
    Requires(0 <= code and code <= 2)
    # The real helper is a bounded computation: the single call always finishes
    # (normally or by raising). The strictly smaller measure (1 < 2) lets the
    # contracted caller holding MustTerminate(2) invoke it without leaking its
    # own termination obligation.
    Requires(MustTerminate(1))
    Ensures(code != 2)
    Ensures(Result() == common_factor(code))
    Exsures(FactorUnavailable, code == 2)


@Pure
@ContractOnly
def divide_out(value: int, factor: int) -> int:
    """The transform helper: maps one operand to a new value, parameterised by
    the factor. Pure; the exact result is OPAQUE — nothing constrains it to equal
    the input, so an implementation can produce ``divide_out(value, factor)``
    only by actually invoking the helper, never by leaving the operand untouched
    (SPEC_GUIDE §8). Applied only when ``factor != 1``.
    """
    Requires(factor != 1)


@Pure
@ContractOnly
def build_result(factor: int, p: int, q: int) -> int:
    """The result-construction step: the operation's returned value is built from
    the factor together with the two (possibly transformed) operands. OPAQUE —
    two applications are equal only when their three arguments are provably
    equal, so the value observably depends on whether each operand was
    transformed (SPEC_GUIDE §8).
    """
    Ensures(True)
# axioms-end


# pure-start
# (no derived pure spec helpers: the operand-shape branch is concrete integer
# control flow over the axiomatized callees above.)
# pure-end


def reduce_extract_common_factor(code: int, p: int, q: int) -> int:
    # pre-conditions-start
    # The input is classified into exactly one of three cases: a factor other
    # than the identity (0), the identity factor (1), or the case the helper
    # cannot answer (2).
    Requires(0 <= code and code <= 2)
    # Total correctness: the operation is a bounded, straight-line computation
    # over the helpers and MUST terminate and deliver its value (measure 2
    # leaves room for the factor-producing sub-call's own MustTerminate(1)
    # obligation). Nagini is a partial-correctness verifier by default, so
    # without this obligation an implementation that diverges before returning
    # (e.g. an unbounded loop ahead of the factor-producing call) satisfies
    # every value postcondition vacuously yet would hang the operation — and
    # the reported scenario — forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (1) The operation ALWAYS completes — it never lets the helper's raise
    #     escape to its caller. There is NO Exsures, so the spec requires the
    #     method to raise no exception on any input.
    #
    # (2) For the input the helper cannot answer the value is built from the
    #     identity factor and the two operands exactly as given (neither operand
    #     is transformed).
    Ensures(Implies(code == 2, Result() == build_result(1, p, q)))
    # (3a) For an answerable input whose factor is NOT the identity, the factor is
    #      the helper's own (opaque) output and EACH operand is first passed
    #      through the transform helper before the value is built. Because
    #      divide_out is opaque, this is dischargeable only by an implementation
    #      that actually performs the transform — an implementation that builds
    #      the value from the untransformed operands cannot prove
    #      p == divide_out(p, ...) and so does NOT verify.
    Ensures(Implies(code != 2 and common_factor(code) != 1,
                    Result() == build_result(
                        common_factor(code),
                        divide_out(p, common_factor(code)),
                        divide_out(q, common_factor(code)))))
    # (3b) For an answerable input whose factor IS the identity, that factor is
    #      the helper's own (identity) output and the operands enter the value
    #      unchanged.
    Ensures(Implies(code != 2 and common_factor(code) == 1,
                    Result() == build_result(common_factor(code), p, q)))
    # post-conditions-end
    # impl-start
    # pr, qr are the operands as they enter the result: unchanged unless the
    # factor is not the identity, in which case each is passed through the
    # transform helper. The parameters p, q are read-only and keep their original
    # value, so the postcondition's witnesses divide_out(p, ...) / divide_out(q,
    # ...) refer to the operands as given (directive 5: read-only inputs are not
    # mutated).
    pr = p
    qr = q
    try:
        # The single factor-producing call. Its raising facet
        # (common_factor_compute) raises for the unanswerable input (code 2); for
        # an answerable input it returns the factor, whose value is the helper's
        # own pure-facet output common_factor(code). On normal completion this
        # establishes code in {0, 1}, so the value facet is well-defined and the
        # factor G is exactly common_factor(code).
        G = common_factor_compute(code)
        Assert(G == common_factor(code))
        Assert(code == 0 or code == 1)
        G = common_factor(code)
        if G != 1:
            # factor is not the identity: pass each operand through the transform
            # helper, then build the value from the transformed operands. Because
            # G is common_factor(code) and divide_out is opaque, the transformed
            # operands are exactly the postcondition's witnesses (clause 3a) — an
            # implementation that skips this step cannot discharge them.
            pr = divide_out(p, G)
            qr = divide_out(q, G)
        # On normal completion the operands were transformed exactly when
        # common_factor(code) != 1: the build arguments match clause (3a)/(3b).
        return build_result(G, pr, qr)
    except FactorUnavailable:
        # the unanswerable input: keep the identity factor; the operands enter
        # the value unchanged. The raise occurs only for code 2
        # (common_factor_compute's Exsures guard), so this handler runs only
        # there; pr, qr are still their original p, q (never reassigned).
        return build_result(1, pr, qr)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Env: python; verifier via scripts/nagini_verify.sh.

SPEC SHAPE: postcondition pins the returned value in ALL THREE code branches via opaque axioms build_result / divide_out / common_factor, PLUS no-Exsures (must not raise on any input) PLUS Requires(MustTerminate(2)) (total correctness). Tight on all four surfaces.

SAME-SPEC: all 7 attacks + positive control returned same-spec exit 0 (spec byte-identical; only impl region edited).

POSITIVE CONTROL (pos_control.py = model.py): `bash scripts/nagini_verify.sh` exit 0 (verifies).

### ATTACKS (cmd: `python -m swebench_unified.adversary weakness nagini sympy__sympy-21379 <atk>`):
- atk_1.py (PREPATCH: unguarded common_factor_compute, no try/except): exit 2, NOT-A-COUNTEREXAMPLE. Direct verify signature: `error: Exhale might fail. Assertion "method raises no exceptions" might not hold.` -> prepatch bug REPRODUCED (no-exception obligation / clause 1).
- atk_2.py (keep try/except, DROP the operand transform, build from untransformed operands): exit 2, rejected -> clause 3a (opaque divide_out unprovable).
- atk_3.py (partial-domain: transform ONLY the first operand pr, leave qr untransformed): exit 2, rejected -> clause 3a on q.
- atk_4.py (control-flow/divergence: `while n>=0: n=n+1` unbounded loop ahead of the factor call): exit 2, rejected -> MustTerminate(2) has no decreasing measure.
- atk_5.py (boundary/effect: on FactorUnavailable return build_result(0,...) i.e. non-identity factor on refusal): exit 2, rejected -> clause 2 (code==2 => build_result(1,p,q)).
- atk_6.py (ungrounded-oracle echo: `return build_result(1, p, q)` unconditionally): exit 2, rejected -> clauses 2/3a (cannot match common_factor(code) opaque factor nor divide_out transform).
- atk_7.py (restructured control flow: `if code==2: return build_result(1,p,q)` decided FIRST, then G=common_factor(code), transform under G!=1, build; try scope effectively only around the factor call): exit 0 CANDIDATE, VERIFIES (11.6s).

CANDIDATE RESOLVE (MANDATORY): materialized atk_7's faithful refined patch at atk_7.patch.diff (wraps only `G = gcd(p,q)` in try/except PolynomialError -> G=S.One, leaves the gcd_terms transform outside the guard — faithful to atk_7's control flow). Ran official harness via swebench_unified.harness.run_resolve (timeout 1800, retries 1). RESULT: `[ATK7] resolved=True completed=True note='resolved'`. Gold control (benchmark-verified/.../patch.diff) run identically: `[GOLD] resolved=True`. atk_7 is a behavioral ECHO that RESOLVES -> per the resolve-based G-EQ/panel_1 policy (the audit protocol) a same-spec verifying impl whose faithful patch resolves is NOT a weakness. verify=>correct holds for it.

WHY atk_7's structural difference is benign on the tested inputs: gold wraps BOTH gcd and gcd_terms in the try; atk_7 wraps only gcd. They diverge ONLY if gcd_terms raises PolynomialError on a code-0 input where gcd itself succeeded — which does not occur on the F2P/P2P suite (harness confirms resolved). No tested input exercises that gap, so no counterexample exists on the oracle.

REFINEMENT AUDIT (refinement.md): legs A1(R), A2(A-consumed, gcd two-facet split), A3(R+A-consumed, gcd_terms), A4(R+A-consumed, Mul/Mod construction), A5(R+I, PolynomialError<->FactorUnavailable, S.One<->1). All R / A-consumed / I — NO kind-3, and section D explicitly declares NO A-reference (the changed op — the try/except wrapping — is modeled DIRECTLY in the impl with a no-Exsures postcondition, not hidden behind an axiom). The only consumed axioms cover UNCHANGED callees (gcd, gcd_terms, Mul/Mod); soundness checked by axiom_check.py / G-AX (code-0 !=1, code-1 ==1, code-2 Piecewise->raise, end-to-end F2P transform assertions). A-leg correspondence to real callees holds. sympy present locally (1.14.0) — G-AX proper run is in-container against the patched repo.

CONCLUSION: >=6 distinct wrong impls attacked (prepatch + drop-transform + partial-domain + divergence + wrong-refusal-factor + ungrounded-echo + restructured-echo). The one verifying candidate (atk_7) RESOLVES, so it is not a broken counterexample. Spec rejects every genuinely-incorrect impl. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No spec drift found; the modeled function agrees with the real Mod.eval 'extract gcd' block on every shape code.

Evidence:
1. Spec region: model.py verifies (Nagini, 10.95s); model_prepatch.py (unguarded gcd call) fails exactly on 'method raises no exceptions' — the frozen no-Exsures postcondition senses the real bug (unguarded gcd raising PolynomialError on Piecewise operands).
2. Axiom soundness vs REAL repo (axiom_check.py run with, exit 0): common_factor/common_factor_compute ↔ sympy.gcd is faithful — 7 code-0 pairs return !=1 normally, 6 code-1 pairs return ==1 normally, 5 code-2 (Piecewise/z etc.) pairs RAISE PolynomialError. Independently confirmed.
3. Behavioral correspondence per code:
   - code 2: real post-fix catches PolynomialError, sets G=S.One, leaves operands unchanged, no exception escapes -> spec clause Implies(code==2, Result()==build_result(1,p,q)) + absence of Exsures. Matches.
   - code 1 (gcd==1): if-branch skipped, operands unchanged -> clause 3b. Matches.
   - code 0 (gcd!=1): each operand rewritten via gcd_terms(i/G) before result built -> clause 3a; opaque divide_out/build_result force the transform. Verified real block yields 3*Mod(6*y,x) = F2P assertion for (12*x+18*y)%(3*x).
4. Termination: MustTerminate(2)/(1) faithfully models the bounded straight-line real block (one gcd call, optional pair of gcd_terms, one construction; no loop/recursion).
5. Searched for divergence: probed edge inputs (gcd(0,0), gcd(x,0), gcd(1/x,y)) — real gcd returns normally, never raises a non-PolynomialError on in-domain shapes, so the no-Exsures obligation is not over-strong. The three-code partition covers the real branch structure exactly; no input where the modeled function disagrees with the real callee.

Conclusion: the spec is neither too strong nor drifting from real repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py projected via markers.spec_view, impl elided) reviewed for leakage of the gold edit beyond the public problem_statement. Gold edit: wrap `G = gcd(p, q); if G!=1: gcd_terms(...)` block in `try/except PolynomialError: G = S.One` in sympy/core/mod.py Mod.eval, plus a PolynomialError import. 

Mechanical G-LEAK screen PASSES (verified via leakage.screen): no diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file path `sympy/core/mod.py`, no patched module path echoed, no patched symbols (`eval`,`doit`) embedded in spec-view identifiers or named in comments/docstrings, and no narration terms (bug/fix/patch/etc.).

Semantic gold-reconstruction review: the spec view is written entirely in repo-neutral, abstract vocabulary — an integer `code` classifying three cases, opaque axiom callees `common_factor`/`common_factor_compute`/`divide_out`/`build_result`, and a generic 'helper/factor/operand/transform'. None of the gold-edit localizers appear anywhere in the view: `gcd`, `gcd_terms`, `Mod.eval`, `PolynomialError`, `Piecewise`, `S.One`, `mod.py`, `sympy/core`, `polys`, `singleton`, `subs`, `sinh/cosh/tanh`, `try`, or the issue number `21373`. (The only `except` substring hits are inside the abstract word 'exception'; the string `21379` is only the public instance-id in the module-header docstring, i.e. the solver's task name, not an edit locator.)

The contract the spec encodes (the operation must catch the helper's raise rather than propagate it, yielding the identity factor with unchanged operands) is the abstract behavior any faithful spec of this fix must state; it does not reveal WHERE in the repo the edit lives or the concrete mechanism (try/except PolynomialError around gcd). The public problem_statement already exposes the symptom (`PolynomialError: Piecewise generators do not make sense`), so the spec view discloses nothing that would let a solver reconstruct the gold patch beyond what is already public. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
