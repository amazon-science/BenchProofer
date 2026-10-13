# P2 adversarial audit — django__django-11211

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_10.py`, `atk_11.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,7 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # PREPATCH: only the inherited base preliminary coercion; the
+    # canonicalizing parser is never reached (pre-patch UUIDField).
+    return base_prepare(value)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,10 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # right number, wrong form: canonical numeric key, but the form facet
+    # is whatever the input happened to be held in (real patch:
+    # `return self.to_python(super().get_prep_value(value)).int`).
+    if value.is_none:
+        return Value(True, value.canon, value.key, value.is_canon_form)
+    return Value(False, value.canon, value.canon, value.is_canon_form)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,10 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # partial domain: only canonicalize a value ALREADY in the canonical
+    # object form; hand every other storage form straight back.
     coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    if coerced.is_canon_form:
+        return canonicalize(coerced)
+    return coerced
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,10 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # boundary swap: the EMPTY value is given a canonical key and the
+    # non-empty ones are prepared normally.
+    if value.is_none:
+        return Value(False, value.canon, value.canon, True)
     coerced = base_prepare(value)  # type: Value
     return canonicalize(coerced)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,14 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # control-flow effect: prepare the key correctly and then diverge, so
+    # every Ensures holds only vacuously under partial correctness.
     coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    out = canonicalize(coerced)  # type: Value
+    n = 0  # type: int
+    while n >= 0:
+        Invariant(n >= 0)
+        Invariant(Acc(out.is_none) and Acc(out.canon) and Acc(out.key) and Acc(out.is_canon_form))
+        n = n + 1
+    return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,10 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # oracle echo: take the form half straight out of the spec's own join
+    # predicate evaluated on the INPUT.
+    echoed = matches_target_key(value, value.canon)  # type: bool
+    if value.is_none:
+        return Value(True, value.canon, value.key, value.is_canon_form)
+    return Value(False, value.canon, value.canon, echoed)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -184,6 +184,8 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # A-leg probe: the two A-consumed callees composed in the opposite
+    # order -- canonicalize FIRST, then the base preliminary coercion.
+    canonized = canonicalize(value)  # type: Value
+    return base_prepare(canonized)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -184,6 +184,12 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # A-leg domain abuse: strip the value down to a textual carrier (form
+    # flag cleared) and canonicalize THAT, relying on the axiom being
+    # total on every non-empty carrier rather than on the value received.
     coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    if coerced.is_none:
+        return coerced
+    textual = Value(False, coerced.canon, coerced.key, False)  # type: Value
+    return canonicalize(textual)
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -184,6 +184,9 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # A-leg bypass: construct the prepared key outright; neither
+    # A-consumed axiom's Ensures is used anywhere in the proof.
+    if value.is_none:
+        return Value(True, value.canon, value.key, value.is_canon_form)
+    return Value(False, value.canon, value.canon, True)
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,12 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # partial domain: an already-canonical value is handed back untouched
+    # (real patch: `if isinstance(value, uuid.UUID): return value`).
     coerced = base_prepare(value)  # type: Value
+    if coerced.is_none:
+        return coerced
+    if coerced.is_canon_form:
+        return coerced
     return canonicalize(coerced)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,9 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # frame attack: re-label the read-only input as canonical and return
+    # it, so the form half is 'established' by writing the input.
+    value.is_canon_form = True
+    value.key = value.canon
+    return value
     # impl-end
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -184,6 +184,7 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
-    coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    # A-leg drop: the base preliminary-coercion step is never invoked; only
+    # the canonicalizing parser runs, on the value as it arrived.
+    return canonicalize(value)
     # impl-end
```

Attack 13 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,11 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # vacuity control: gold body, then Assert(False). Must NOT verify --
+    # if it did, the proof context is contradictory and every rejection
+    # recorded above proves nothing.
     coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    out = canonicalize(coerced)  # type: Value
+    Assert(False)
+    return out
     # impl-end
```

Attack 14 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,11 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # A-leg misgrounding: canonicalize a carrier whose canon facet is the
+    # AS-STORED key, not the identity the value denotes.
     coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    if coerced.is_none:
+        return coerced
+    restated = Value(False, coerced.key, coerced.key, False)  # type: Value
+    return canonicalize(restated)
     # impl-end
```

Attack 15 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -184,6 +184,11 @@
     Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
     # post-conditions-end
     # impl-start
+    # control-flow effect: prepare the key correctly, then recurse on the
+    # same value forever instead of delivering it.
     coerced = base_prepare(value)  # type: Value
-    return canonicalize(coerced)
+    out = canonicalize(coerced)  # type: Value
+    if out.is_canon_form or out.is_none:
+        return prepare_key(value)
+    return out
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11211.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stored value is prepared for use as the lookup key of a globally
  unique identifier field, the prepared key must MATCH the key the target
  record contributes on the other side of the in-Python join a deferred
  relation traversal performs across a heterogeneous holder and its target.

  That join compares keys with the host language's equality, and the target
  side always holds its identifier in the CANONICAL OBJECT FORM, keyed by the
  canonical identity. That equality is sensitive to the FORM as well as to the
  identity: a key not held in the canonical object form never compares equal to
  one that is, however its numeric part reads. Both halves of the target's key
  therefore have to be delivered.

  Concretely: preparing any non-empty value yields a key that is (a) in the
  canonical object form (``Result().is_canon_form``) and (b) numerically the
  canonical identity the value denotes (``Result().key == value.canon``) —
  independent of how that value was stored, so a value held in its textual
  storage form and the same identity held in its already-canonical object form
  prepare to the SAME matchable key. A bare ``None`` (no identity stored)
  prepares to a bare ``None`` key, unchanged in every facet.

A value is modelled as a minimal class carrying only the facets the join
observes: the canonical identity it denotes (``canon``); whether it is held in
the canonical object form (``is_canon_form``) — the form half of its join key;
and the numeric part of the join key its *current* storage form yields
(``key``). Two keys match in the join iff their emptiness, their form flag AND
their numeric part all agree, which is why the form flag is load-bearing: the
numeric part alone cannot tell a canonical identifier apart from a plain number
spelling the same 128 bits, and the real join can. For an already-canonical
value ``key`` and ``canon`` coincide; for a textual storage form they need not.
Two unchanged callees the field invokes are axiomatized: the base preliminary-
coercion step (identity on the relevant facets) and the canonicalizing parser
(yields a value in the canonical object form whose numeric key is the canonical
identity).

Total correctness: preparing a key is bounded, loop-free work that must
actually complete and deliver its result. Nagini checks partial correctness
by default — a diverging body would satisfy every postcondition vacuously —
so every function carries a ``MustTerminate`` obligation (with strictly
decreasing measures for callees) to reject non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Value:
    def __init__(self, is_none: bool, canon: int, key: int,
                 is_canon_form: bool) -> None:
        # Terminates: field initialisation is straight-line work; measure 2
        # lets any caller holding a larger measure construct a value without
        # leaking its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_none) and self.is_none == is_none)          # type: ignore
        Ensures(Acc(self.canon) and self.canon == canon)                # type: ignore
        Ensures(Acc(self.key) and self.key == key)                      # type: ignore
        Ensures(Acc(self.is_canon_form) and                             # type: ignore
                self.is_canon_form == is_canon_form)                    # type: ignore
        self.is_none = is_none
        self.canon = canon
        self.key = key
        self.is_canon_form = is_canon_form

# axioms-start
@ContractOnly
def base_prepare(value: Value) -> Value:
    """The unchanged base preliminary-coercion step the field defers to first.
    On the values this field receives it is the identity on every relevant
    facet: it casts a lazy proxy to its concrete value and otherwise returns
    the value unchanged, so the canonical identity, the numeric part of the
    current join key, the form the value is held in and the emptiness flag are
    all preserved. It is bounded, loop-free work, so it always terminates
    (measure 6, strictly below its caller's, so a body holding the caller's
    obligation can invoke it without leaking it). Provenance + executable
    soundness: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(6))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    Ensures(Result().key == value.key)
    # The form the value is held in is untouched by this step: it neither
    # canonicalizes nor de-canonicalizes.
    Ensures(Result().is_canon_form == value.is_canon_form)

@ContractOnly
def canonicalize(value: Value) -> Value:
    """The unchanged canonicalizing parser the field reuses. It interprets any
    non-empty storage form of an identity and returns that identity IN ITS
    CANONICAL OBJECT FORM — so the result carries the canonical form flag, and
    its numeric join key is, by construction, the canonical identity itself. An
    empty value passes through unchanged, form flag included. Parsing a bounded
    storage form is bounded work, so it always terminates (measure 10, strictly
    below its caller's, so a body holding the caller's obligation can invoke it
    without leaking it). Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(MustTerminate(10))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    # A non-empty value comes back in the canonical object form ...
    Ensures(Implies(not value.is_none, Result().is_canon_form))
    # ... and the canonical form's numeric join key is the canonical identity
    # it denotes.
    Ensures(Implies(not value.is_none, Result().key == value.canon))
    # An empty value is handed straight back, in the same form.
    Ensures(Implies(value.is_none, Result().key == value.key))
    Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
# axioms-end

# pure-start
@Pure
def matches_target_key(prepared: Value, identity: int) -> bool:
    """The join predicate, spelled out: does ``prepared``, used as the holder
    side of the in-Python join, compare EQUAL to the key the target record
    whose canonical identity is ``identity`` contributes?

    The target side is a stored record's own identifier: never empty, always
    held in the canonical object form, and numerically its canonical identity.
    The host language's equality on keys compares form first, so all three
    facets must agree — a prepared key that is numerically right but not held
    in the canonical object form does NOT match, and the traversal yields
    nothing.
    """
    Requires(Acc(prepared.is_none, 1 / 8) and Acc(prepared.key, 1 / 8) and
             Acc(prepared.is_canon_form, 1 / 8))
    return (not prepared.is_none) and prepared.is_canon_form and \
        prepared.key == identity
# pure-end

def prepare_key(value: Value) -> Value:
    # pre-conditions-start
    # TERMINATION: preparing a key is a bounded, loop-free composition of two
    # always-terminating steps and MUST actually complete (total correctness).
    # Under partial-correctness semantics a diverging body (e.g. an endless
    # loop before the return) satisfies every Ensures clause only vacuously
    # yet never delivers the prepared key to its caller; the real preparation
    # always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(14))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    # Faithfulness: the prepared value still denotes the same identity and the
    # same emptiness; preparation must not invent or drop an identity.
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    # THE DISCRIMINATING GUARANTEE, both halves of the target's key. For any
    # non-empty value the prepared key must be the key a target record whose
    # canonical identity is value.canon contributes: held in the canonical
    # object form AND numerically that canonical identity. The two clauses
    # below are the halves; the third states them as the join predicate they
    # exist to satisfy, so the guarantee cannot be met by a key that merely
    # reads the right number while being held in some other form.
    Ensures(Implies(not value.is_none, Result().is_canon_form))
    Ensures(Implies(not value.is_none, Result().key == value.canon))
    Ensures(Implies(not value.is_none, matches_target_key(Result(), value.canon)))
    # An empty value prepares to an empty key, unchanged in every facet.
    Ensures(Implies(value.is_none, Result().key == value.key))
    Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL: correct, structurally different -- named locals, an
    # explicit emptiness split and in-body Asserts deriving the join
    # predicate from the two A-consumed axioms.
    coerced = base_prepare(value)  # type: Value
    result = canonicalize(coerced)  # type: Value
    if not value.is_none:
        Assert(result.is_canon_form)
        Assert(result.key == value.canon)
        Assert(matches_target_key(result, value.canon))
    else:
        Assert(result.is_none)
        Assert(result.key == value.key)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, A-legs. 16 same-spec attacks encoded  (all built by copying the bundle model.py and editing ONLY the impl region; all 17 files incl. the control confirmed same_spec=True AND admissible=True via markers.same_spec + variant_scope.unsound_evasions). 15 submitted (atk_13 withheld, see below). Bundle untouched: model.py sha256=5d63c305e525e5b9d7008cec184144ff8f82d3973d6e55fe74333053aceec483.

**COMMANDS.** Weakness (run 3-at-a-time as background jobs via run_weak.sh; each Nagini check spawns a JVM+Z3): `python -m swebench_unified.adversary weakness nagini django__django-11211 atk_N.py`. Direct verifier messages: `bash scripts/nagini_verify.sh <file>`. Raw evidence retained per file as atk_N.weak / atk_N.verify / atk_N.resolve.json.

REJECTED (exit 2 = not a counterexample), with the clause the verifier named:
- atk_1 PREPATCH BUG re-encoded (`return base_prepare(value)`; UUIDField inherits Field.get_prep_value and never canonicalizes) -> rejected on P5 `Implies((not value.is_none), Result().is_canon_form)` at line 179. Matches G-DIFF/model_prepatch.py exactly. prepatch_reproduced=true.
- atk_2 prior recorded counterexample (right NUMBER, form copied from the input; real patch `to_python(...).int`) -> P5 line 179.
- atk_3 partial-domain: canonicalize only what is already canonical -> P5 line 179.
- atk_4 boundary: emptiness guard inverted (empty value given a canonical key) -> rejected.
- atk_5 control-flow effect: correct key then diverge in a loop -> `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` (MustTerminate(14) at the METHOD level).
- atk_6 ungrounded-oracle echo: form half read out of matches_target_key applied to the INPUT -> rejected. The predicate is a transparent conjunction of the RESULT's facets, so it cannot serve as an answer key.
- atk_10 partial-domain: already-canonical passthrough -> rejected.
- atk_11 frame: re-label the read-only input's FORM facet + key and return it -> `Assignment might fail. There might be insufficient permission to access value.is_canon_form.` (the Acc(...,1/2) fractions are load-bearing).
- atk_15 A-LEG MISGROUNDING (sharpest new A-leg probe): invoke `canonicalize` on a fabricated carrier whose canon facet is the AS-STORED key rather than the identity the value denotes -> rejected on P2 `Result().canon == value.canon` (line 171). The canonicalize axiom's `Result().key == value.canon` is therefore grounded in the ORIGINAL value's identity, not in whatever carrier the impl chooses to hand it.
- atk_16 control-flow effect via unbounded SELF-RECURSION (correct key, then recurse) -> `Obligation leak check failed. Callee prepare_key might not take all unsatisfied obligations from the caller.` Confirms the termination obligation rejects divergence that is not loop-shaped.
- atk_14 VACUITY CONTROL: gold body + `Assert(False)` -> `Assert might fail. Assertion False might not hold.` The proof context is NOT contradictory, so every rejection above is a real rejection rather than an artifact of an infeasible context.

CANDIDATES (exit 0 = same-spec AND verifies). All four had their faithful refined patch MATERIALIZED and EXECUTED through the official harness (run_resolve). Executed results, all completed=True resolved=True attempts=1 flaky=False, F2P 1/1 (test_prefetch_GFK_uuid_pk) and P2P 76/76:
- atk_7 (`canonicalize(value)` then `base_prepare`, i.e. the two A-consumed callees composed in the OPPOSITE order) -> patch `return super().get_prep_value(self.to_python(value))` -> RESOLVED. Correct echo: on every reachable input Field.get_prep_value is the identity on all four facets, so the composition commutes.
- atk_8 (A-leg domain abuse: canonicalize a fabricated de-canonicalized carrier instead of the value received) -> patch `self.to_python(self.to_python(value).hex)` -> RESOLVED. Correct echo: re-expressing the identity in a non-canonical form and re-parsing is idempotent on the identity.
- atk_9 (A-leg BYPASS: build the prepared key outright, consuming NEITHER axiom's Ensures) -> patch `uuid.UUID(int=self.to_python(value).int)` -> RESOLVED. Correct echo, and the sharpest evidence that the spec's postcondition — not the axioms' presence — is what pins the result.
- atk_12 (A-LEG DROP: the A2 leg / `super().get_prep_value` is never invoked at all) -> patch `return self.to_python(value)` -> RESOLVED. This is the one leg-correspondence gap worth naming: the A2 axiom is stated as the identity on all four facets, so dropping the call is unobservable in the model AND, as executed, unobservable to the oracle. I probed the base callee's only non-identity input directly (a real django.utils.functional lazy Promise wrapping the stored hex): to_python(base(p)) and to_python(p) both return the same UUID, because uuid.UUID(hex=...) accepts the proxy's `__str__`. So the A2 leg carries no discriminating content on this path — consistent with mapping.md 3.1/2.2, which explicitly scope the axiom to the non-Promise prefetch inputs and do NOT claim anything about the Promise branch. Not a spec weakness: refinement.md A2's claim ("on these inputs it is the identity on every facet") is TRUE, merely not load-bearing.

**NOT SUBMITTED.** atk_13 (correct key, then leave by an exceptional edge: `raise ValueError()`) returned `Translation failed / Not supported: Unsupported builtin function` — a Nagini translation limit, not a rejection by the spec. Crediting the spec with a rejection it never made would be exactly the retained-attack-label error, so it is excluded from the floor. The control-flow-effect lane is covered instead by atk_5 (loop divergence) and atk_16 (self-recursion), both of which reach a genuine verdict on the termination obligation.

**POSITIVE CONTROL:** pos_control.py — correct but structurally different (named locals, explicit is_none split, in-body Asserts deriving both halves and matches_target_key from the two axioms). weakness exit 0 (same-spec AND verifies), so the spec does not over-constrain a faithful reshaping.

REFINEMENT.MD LEG AUDIT (as required, every leg): A1 = R (value -> the four join-observable facets is_none/canon/key/is_canon_form; is_canon_form = isinstance(value, uuid.UUID)); A2 = A-consumed (base_prepare <-> Field.get_prep_value, `__init__`.py:771-775); A3 = A-consumed (canonicalize <-> UUIDField.to_python, `__init__`.py:2338-2349). No A-reference leg (no deep model exists), and no kind-3 step — the changed operation is the ADDITION of the composition A2∘A3, which is expressed and verified rather than assumed. Section B states this explicitly and the claim holds.

I checked all three legs against the base_commit source (git show ba726067604ce5a8ca3919edf653496722b433ab) and independently re-ran both A-leg correspondences in ax_local.py against the REAL callee bodies over 5 boundary + 5000 fuzz UUIDs x {uuid, hex32, hyphen, int} + None: both axioms hold on all four facets, the stored-str and uuid forms prepare to keys that are equal AND compare equal, and the hash-equal / ==-unequal / dict-miss demonstration holds (so the is_canon_form facet is not a dead clause). Neither axiom is over-strong: A3 deliberately omits the ValidationError raise path and A2 omits the Promise branch, both of which are documented scope limits rather than assumptions the proof leans on.

MODEL<->PATCH CORRESPONDENCE: the gold hunk is a 3-line added UUIDField.get_prep_value whose two statements are exactly the impl region's two statements under R. refinement.md §D's claim that no facet is left free is correct: is_none and canon are pinned unconditionally, and the non-empty and empty branches each pin key and is_canon_form. I confirmed the four-facet closure is what forces the join by cross-checking all five impls (gold + the four candidates) against a real one-entry dict keyed by (uuid.UUID pk, class): every one JOINs on all four storage forms and returns None for None. §D's correction of the earlier numeric-only document is also right — atk_2 reproduces that exact rival and it now rejects on the form clause.

**ORACLE REFUTATION POWER:** recorded G-RESOLVE=pass on the gold patch, so `_oracle_cannot_refute_here` is empty and a not-resolved verdict on this instance would have carried information. It simply never occurred.

**VERDICT:** SOUND. 15 admissible attacks reached a verdict; 11 were rejected by the spec (each on a named, attributable clause, with a passing Assert(False) vacuity control), 4 verified and ALL FOUR had their materialized faithful patches EXECUTED through the official harness and RESOLVED (F2P 1/1, P2P 76/76) — i.e. every candidate is a correct echo of the reference solution, not a spec weakness. No verifying same-spec impl was found whose faithful refined patch fails to resolve, so no witness of verify⇏correct exists for this bundle. The one substantive observation is advisory, not a defect: the A2 leg (base_prepare) is faithful but carries no discriminating content on the prefetch path, so the bundle's guarantee rests on A3 plus the four-facet postcondition.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_10.py`, `atk_11.py`, `atk_14.py`, `atk_15.py`, `atk_16.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11211.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a stored value is prepared for use as the lookup key of a globally
  unique identifier field, the prepared key must MATCH the key the target
  record contributes on the other side of the in-Python join a deferred
  relation traversal performs across a heterogeneous holder and its target.

  That join compares keys with the host language's equality, and the target
  side always holds its identifier in the CANONICAL OBJECT FORM, keyed by the
  canonical identity. That equality is sensitive to the FORM as well as to the
  identity: a key not held in the canonical object form never compares equal to
  one that is, however its numeric part reads. Both halves of the target's key
  therefore have to be delivered.

  Concretely: preparing any non-empty value yields a key that is (a) in the
  canonical object form (``Result().is_canon_form``) and (b) numerically the
  canonical identity the value denotes (``Result().key == value.canon``) —
  independent of how that value was stored, so a value held in its textual
  storage form and the same identity held in its already-canonical object form
  prepare to the SAME matchable key. A bare ``None`` (no identity stored)
  prepares to a bare ``None`` key, unchanged in every facet.

A value is modelled as a minimal class carrying only the facets the join
observes: the canonical identity it denotes (``canon``); whether it is held in
the canonical object form (``is_canon_form``) — the form half of its join key;
and the numeric part of the join key its *current* storage form yields
(``key``). Two keys match in the join iff their emptiness, their form flag AND
their numeric part all agree, which is why the form flag is load-bearing: the
numeric part alone cannot tell a canonical identifier apart from a plain number
spelling the same 128 bits, and the real join can. For an already-canonical
value ``key`` and ``canon`` coincide; for a textual storage form they need not.
Two unchanged callees the field invokes are axiomatized: the base preliminary-
coercion step (identity on the relevant facets) and the canonicalizing parser
(yields a value in the canonical object form whose numeric key is the canonical
identity).

Total correctness: preparing a key is bounded, loop-free work that must
actually complete and deliver its result. Nagini checks partial correctness
by default — a diverging body would satisfy every postcondition vacuously —
so every function carries a ``MustTerminate`` obligation (with strictly
decreasing measures for callees) to reject non-terminating implementations.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Value:
    def __init__(self, is_none: bool, canon: int, key: int,
                 is_canon_form: bool) -> None:
        # Terminates: field initialisation is straight-line work; measure 2
        # lets any caller holding a larger measure construct a value without
        # leaking its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_none) and self.is_none == is_none)          # type: ignore
        Ensures(Acc(self.canon) and self.canon == canon)                # type: ignore
        Ensures(Acc(self.key) and self.key == key)                      # type: ignore
        Ensures(Acc(self.is_canon_form) and                             # type: ignore
                self.is_canon_form == is_canon_form)                    # type: ignore
        self.is_none = is_none
        self.canon = canon
        self.key = key
        self.is_canon_form = is_canon_form

# axioms-start
@ContractOnly
def base_prepare(value: Value) -> Value:
    """The unchanged base preliminary-coercion step the field defers to first.
    On the values this field receives it is the identity on every relevant
    facet: it casts a lazy proxy to its concrete value and otherwise returns
    the value unchanged, so the canonical identity, the numeric part of the
    current join key, the form the value is held in and the emptiness flag are
    all preserved. It is bounded, loop-free work, so it always terminates
    (measure 6, strictly below its caller's, so a body holding the caller's
    obligation can invoke it without leaking it). Provenance + executable
    soundness: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(6))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    Ensures(Result().key == value.key)
    # The form the value is held in is untouched by this step: it neither
    # canonicalizes nor de-canonicalizes.
    Ensures(Result().is_canon_form == value.is_canon_form)

@ContractOnly
def canonicalize(value: Value) -> Value:
    """The unchanged canonicalizing parser the field reuses. It interprets any
    non-empty storage form of an identity and returns that identity IN ITS
    CANONICAL OBJECT FORM — so the result carries the canonical form flag, and
    its numeric join key is, by construction, the canonical identity itself. An
    empty value passes through unchanged, form flag included. Parsing a bounded
    storage form is bounded work, so it always terminates (measure 10, strictly
    below its caller's, so a body holding the caller's obligation can invoke it
    without leaking it). Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(MustTerminate(10))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    # A non-empty value comes back in the canonical object form ...
    Ensures(Implies(not value.is_none, Result().is_canon_form))
    # ... and the canonical form's numeric join key is the canonical identity
    # it denotes.
    Ensures(Implies(not value.is_none, Result().key == value.canon))
    # An empty value is handed straight back, in the same form.
    Ensures(Implies(value.is_none, Result().key == value.key))
    Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
# axioms-end

# pure-start
@Pure
def matches_target_key(prepared: Value, identity: int) -> bool:
    """The join predicate, spelled out: does ``prepared``, used as the holder
    side of the in-Python join, compare EQUAL to the key the target record
    whose canonical identity is ``identity`` contributes?

    The target side is a stored record's own identifier: never empty, always
    held in the canonical object form, and numerically its canonical identity.
    The host language's equality on keys compares form first, so all three
    facets must agree — a prepared key that is numerically right but not held
    in the canonical object form does NOT match, and the traversal yields
    nothing.
    """
    Requires(Acc(prepared.is_none, 1 / 8) and Acc(prepared.key, 1 / 8) and
             Acc(prepared.is_canon_form, 1 / 8))
    return (not prepared.is_none) and prepared.is_canon_form and \
        prepared.key == identity
# pure-end

def prepare_key(value: Value) -> Value:
    # pre-conditions-start
    # TERMINATION: preparing a key is a bounded, loop-free composition of two
    # always-terminating steps and MUST actually complete (total correctness).
    # Under partial-correctness semantics a diverging body (e.g. an endless
    # loop before the return) satisfies every Ensures clause only vacuously
    # yet never delivers the prepared key to its caller; the real preparation
    # always returns. This obligation rejects any such implementation.
    Requires(MustTerminate(14))
    Requires(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
             Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(value.is_none, 1 / 2) and Acc(value.canon, 1 / 2) and
            Acc(value.key, 1 / 2) and Acc(value.is_canon_form, 1 / 2))
    Ensures(Acc(Result().is_none) and Acc(Result().canon) and
            Acc(Result().key) and Acc(Result().is_canon_form))
    # Faithfulness: the prepared value still denotes the same identity and the
    # same emptiness; preparation must not invent or drop an identity.
    Ensures(Result().is_none == value.is_none)
    Ensures(Result().canon == value.canon)
    # THE DISCRIMINATING GUARANTEE, both halves of the target's key. For any
    # non-empty value the prepared key must be the key a target record whose
    # canonical identity is value.canon contributes: held in the canonical
    # object form AND numerically that canonical identity. The two clauses
    # below are the halves; the third states them as the join predicate they
    # exist to satisfy, so the guarantee cannot be met by a key that merely
    # reads the right number while being held in some other form.
    Ensures(Implies(not value.is_none, Result().is_canon_form))
    Ensures(Implies(not value.is_none, Result().key == value.canon))
    Ensures(Implies(not value.is_none, matches_target_key(Result(), value.canon)))
    # An empty value prepares to an empty key, unchanged in every facet.
    Ensures(Implies(value.is_none, Result().key == value.key))
    Ensures(Implies(value.is_none, Result().is_canon_form == value.is_canon_form))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL: correct, structurally different -- named locals, an
    # explicit emptiness split and in-body Asserts deriving the join
    # predicate from the two A-consumed axioms.
    coerced = base_prepare(value)  # type: Value
    result = canonicalize(coerced)  # type: Value
    if not value.is_none:
        Assert(result.is_canon_form)
        Assert(result.key == value.canon)
        Assert(matches_target_key(result, value.canon))
    else:
        Assert(result.is_none)
        Assert(result.key == value.key)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, A-legs. 16 same-spec attacks encoded  (all built by copying the bundle model.py and editing ONLY the impl region; all 17 files incl. the control confirmed same_spec=True AND admissible=True via markers.same_spec + variant_scope.unsound_evasions). 15 submitted (atk_13 withheld, see below). Bundle untouched: model.py sha256=5d63c305e525e5b9d7008cec184144ff8f82d3973d6e55fe74333053aceec483.

**COMMANDS.** Weakness (run 3-at-a-time as background jobs via run_weak.sh; each Nagini check spawns a JVM+Z3): `python -m swebench_unified.adversary weakness nagini django__django-11211 atk_N.py`. Direct verifier messages: `bash scripts/nagini_verify.sh <file>`. Raw evidence retained per file as atk_N.weak / atk_N.verify / atk_N.resolve.json.

REJECTED (exit 2 = not a counterexample), with the clause the verifier named:
- atk_1 PREPATCH BUG re-encoded (`return base_prepare(value)`; UUIDField inherits Field.get_prep_value and never canonicalizes) -> rejected on P5 `Implies((not value.is_none), Result().is_canon_form)` at line 179. Matches G-DIFF/model_prepatch.py exactly. prepatch_reproduced=true.
- atk_2 prior recorded counterexample (right NUMBER, form copied from the input; real patch `to_python(...).int`) -> P5 line 179.
- atk_3 partial-domain: canonicalize only what is already canonical -> P5 line 179.
- atk_4 boundary: emptiness guard inverted (empty value given a canonical key) -> rejected.
- atk_5 control-flow effect: correct key then diverge in a loop -> `Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.` (MustTerminate(14) at the METHOD level).
- atk_6 ungrounded-oracle echo: form half read out of matches_target_key applied to the INPUT -> rejected. The predicate is a transparent conjunction of the RESULT's facets, so it cannot serve as an answer key.
- atk_10 partial-domain: already-canonical passthrough -> rejected.
- atk_11 frame: re-label the read-only input's FORM facet + key and return it -> `Assignment might fail. There might be insufficient permission to access value.is_canon_form.` (the Acc(...,1/2) fractions are load-bearing).
- atk_15 A-LEG MISGROUNDING (sharpest new A-leg probe): invoke `canonicalize` on a fabricated carrier whose canon facet is the AS-STORED key rather than the identity the value denotes -> rejected on P2 `Result().canon == value.canon` (line 171). The canonicalize axiom's `Result().key == value.canon` is therefore grounded in the ORIGINAL value's identity, not in whatever carrier the impl chooses to hand it.
- atk_16 control-flow effect via unbounded SELF-RECURSION (correct key, then recurse) -> `Obligation leak check failed. Callee prepare_key might not take all unsatisfied obligations from the caller.` Confirms the termination obligation rejects divergence that is not loop-shaped.
- atk_14 VACUITY CONTROL: gold body + `Assert(False)` -> `Assert might fail. Assertion False might not hold.` The proof context is NOT contradictory, so every rejection above is a real rejection rather than an artifact of an infeasible context.

CANDIDATES (exit 0 = same-spec AND verifies). All four had their faithful refined patch MATERIALIZED and EXECUTED through the official harness (run_resolve). Executed results, all completed=True resolved=True attempts=1 flaky=False, F2P 1/1 (test_prefetch_GFK_uuid_pk) and P2P 76/76:
- atk_7 (`canonicalize(value)` then `base_prepare`, i.e. the two A-consumed callees composed in the OPPOSITE order) -> patch `return super().get_prep_value(self.to_python(value))` -> RESOLVED. Correct echo: on every reachable input Field.get_prep_value is the identity on all four facets, so the composition commutes.
- atk_8 (A-leg domain abuse: canonicalize a fabricated de-canonicalized carrier instead of the value received) -> patch `self.to_python(self.to_python(value).hex)` -> RESOLVED. Correct echo: re-expressing the identity in a non-canonical form and re-parsing is idempotent on the identity.
- atk_9 (A-leg BYPASS: build the prepared key outright, consuming NEITHER axiom's Ensures) -> patch `uuid.UUID(int=self.to_python(value).int)` -> RESOLVED. Correct echo, and the sharpest evidence that the spec's postcondition — not the axioms' presence — is what pins the result.
- atk_12 (A-LEG DROP: the A2 leg / `super().get_prep_value` is never invoked at all) -> patch `return self.to_python(value)` -> RESOLVED. This is the one leg-correspondence gap worth naming: the A2 axiom is stated as the identity on all four facets, so dropping the call is unobservable in the model AND, as executed, unobservable to the oracle. I probed the base callee's only non-identity input directly (a real django.utils.functional lazy Promise wrapping the stored hex): to_python(base(p)) and to_python(p) both return the same UUID, because uuid.UUID(hex=...) accepts the proxy's `__str__`. So the A2 leg carries no discriminating content on this path — consistent with mapping.md 3.1/2.2, which explicitly scope the axiom to the non-Promise prefetch inputs and do NOT claim anything about the Promise branch. Not a spec weakness: refinement.md A2's claim ("on these inputs it is the identity on every facet") is TRUE, merely not load-bearing.

**NOT SUBMITTED.** atk_13 (correct key, then leave by an exceptional edge: `raise ValueError()`) returned `Translation failed / Not supported: Unsupported builtin function` — a Nagini translation limit, not a rejection by the spec. Crediting the spec with a rejection it never made would be exactly the retained-attack-label error, so it is excluded from the floor. The control-flow-effect lane is covered instead by atk_5 (loop divergence) and atk_16 (self-recursion), both of which reach a genuine verdict on the termination obligation.

**POSITIVE CONTROL:** pos_control.py — correct but structurally different (named locals, explicit is_none split, in-body Asserts deriving both halves and matches_target_key from the two axioms). weakness exit 0 (same-spec AND verifies), so the spec does not over-constrain a faithful reshaping.

REFINEMENT.MD LEG AUDIT (as required, every leg): A1 = R (value -> the four join-observable facets is_none/canon/key/is_canon_form; is_canon_form = isinstance(value, uuid.UUID)); A2 = A-consumed (base_prepare <-> Field.get_prep_value, `__init__`.py:771-775); A3 = A-consumed (canonicalize <-> UUIDField.to_python, `__init__`.py:2338-2349). No A-reference leg (no deep model exists), and no kind-3 step — the changed operation is the ADDITION of the composition A2∘A3, which is expressed and verified rather than assumed. Section B states this explicitly and the claim holds.

I checked all three legs against the base_commit source (git show ba726067604ce5a8ca3919edf653496722b433ab) and independently re-ran both A-leg correspondences in ax_local.py against the REAL callee bodies over 5 boundary + 5000 fuzz UUIDs x {uuid, hex32, hyphen, int} + None: both axioms hold on all four facets, the stored-str and uuid forms prepare to keys that are equal AND compare equal, and the hash-equal / ==-unequal / dict-miss demonstration holds (so the is_canon_form facet is not a dead clause). Neither axiom is over-strong: A3 deliberately omits the ValidationError raise path and A2 omits the Promise branch, both of which are documented scope limits rather than assumptions the proof leans on.

MODEL<->PATCH CORRESPONDENCE: the gold hunk is a 3-line added UUIDField.get_prep_value whose two statements are exactly the impl region's two statements under R. refinement.md §D's claim that no facet is left free is correct: is_none and canon are pinned unconditionally, and the non-empty and empty branches each pin key and is_canon_form. I confirmed the four-facet closure is what forces the join by cross-checking all five impls (gold + the four candidates) against a real one-entry dict keyed by (uuid.UUID pk, class): every one JOINs on all four storage forms and returns None for None. §D's correction of the earlier numeric-only document is also right — atk_2 reproduces that exact rival and it now rejects on the form clause.

**ORACLE REFUTATION POWER:** recorded G-RESOLVE=pass on the gold patch, so `_oracle_cannot_refute_here` is empty and a not-resolved verdict on this instance would have carried information. It simply never occurred.

**VERDICT:** SOUND. 15 admissible attacks reached a verdict; 11 were rejected by the spec (each on a named, attributable clause, with a passing Assert(False) vacuity control), 4 verified and ALL FOUR had their materialized faithful patches EXECUTED through the official harness and RESOLVED (F2P 1/1, P2P 76/76) — i.e. every candidate is a correct echo of the reference solution, not a spec weakness. No verifying same-spec impl was found whose faithful refined patch fails to resolve, so no witness of verify⇏correct exists for this bundle. The one substantive observation is advisory, not a defect: the A2 leg (base_prepare) is faithful but carries no discriminating content on the prefetch path, so the bundle's guarantee rests on A3 plus the four-facet postcondition.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference used correctly:  = git worktree of the upstream repository at base_commit ba726067604ce5a8ca3919edf653496722b433ab with patch.diff APPLIED (the modeled function UUIDField.get_prep_value). Base commit used only for the two untouched callees the axioms model (Field.get_prep_value:771-775, UUIDField.to_python:2338-2349 -- patch.diff does not touch either, verified via `git diff --stat` = 1 file / 4 insertions, all inside the new get_prep_value method).

**SPEC REGION IDENTITY:** `adversary same-spec nagini django__django-11211 atk.py` => exit 0, "SAME -- attack shares the bundle's exact specification" on a verbatim copy of model.py. model_prepatch.py also returns exit 0 (SAME), so the G-DIFF rival is spec-identical and only the impl region differs -- the frozen spec is genuinely byte-identical across both.

**NO DIVERGING INPUT FOUND.** Evidence:

1. WIDE-DOMAIN SPEC DIFFERENTIAL (my own, atk_faith_11211.py, independent of the bundle's checkers): evaluated every Ensures clause of prepare_key -- Result().is_none==value.is_none, Result().canon==value.canon, Implies(not is_none, Result().is_canon_form), Implies(not is_none, Result().key==value.canon), matches_target_key(Result(), value.canon) (checked on real objects AND a real one-entry dict join), Implies(is_none, key/form unchanged) -- against the REAL patched UUIDField.get_prep_value. Domain strictly WIDER than conformance_check.py's 7 forms: 11 storage forms (uuid, hex32, hyphen, HEXUP, HYPHUP, braced, urn, int, braced_hex, urn_hex, byteshex) x 7 boundary identities (int=0, int=1, int=`2**128`-1, int=`2**127`, uuid1, uuid4, uuid5) + None + exotic types that legitimately lower (bool True/False, int subclass, str subclass, uuid.UUID subclass, int 0) + 3 lazy Promise wrappings + whitespace/mixed-separator strings + 30000 seeded fuzz identities. Result: 0 violations. Any raw input with no Value lowering per mapping.md sec 2 (malformed hex etc.) was excluded as out-of-domain, and I confirmed the real function RAISES ValidationError exactly there, matching mapping.md sec 3.2's stated axiom scope.

2. SPEC IS NOT TOO STRONG / DOES NOT OVERREACH -- two structural over-strength candidates probed and both resolve as NON-defects:
   (a) ALIASING. The spec demands full Acc(Result().*) while retaining Acc(value.*, 1/2). I measured that the real patched function RETURNS THE INPUT OBJECT ITSELF for an already-canonical uuid.UUID (`get_prep_value(u) is u` => True) and for None (`is None` => True), so Result() aliases value in reality while the spec's permissions imply separation. This is NOT a behavioural divergence: uuid.UUID is immutable (`u.int = 5` raises TypeError, measured), so the aliasing is unobservable on every facet the join reads -- there is no input on which the modeled function and the real callee produce differing observable facets. Permission separation is a Nagini heap-encoding artifact, not a claim about repo behavior, and it makes the spec HARDER to discharge, not weaker.

   (b) PROMISE-WRAPPED uuid.UUID. This is the one input where base_prepare's Ensures(Result().is_canon_form == value.is_canon_form) fails on the real callee: lazy(lambda: u, uuid.UUID)() has is_canon_form False going in and True coming out of Field.get_prep_value (measured). But that input has NO Value lowering at all -- mapping.md's canonical_int raises AttributeError("'`__proxy__`' object has no attribute 'replace'") on it -- so it is outside the admitted domain, exactly as mapping.md sec 3.1/2.2 documents ("it does NOT claim anything about the Promise branch, which never fires for these inputs"; the holder's object_pk is a DB-loaded str). Critically, even on that input prepare_key's OWN postconditions still hold on the real function (out=UUID, is_canon_form True, key==canon True), so the axiom-scope boundary leaks nothing into the top-level guarantee. Promise-wrapped str and int forms preserve the form facet correctly (measured) and satisfy every clause.

3. THE DISCRIMINATING CLAUSE TRACKS THE REAL DELTA (not spec drift): full oracle loop run. Patched worktree + test_patch => GenericRelationTests 8/8 OK including test_prefetch_GFK_uuid_pk. Reverting ONLY patch.diff (keeping the test patch) => test_prefetch_GFK_uuid_pk FAILS with [None] != [<Article...>], i.e. the join silently misses -- precisely the behavior the is_canon_form clause encodes. Correspondingly `nagini_verify.sh model_prepatch.py` => "Verification failed... Postcondition of prepare_key might not hold. Assertion Implies((not value.is_none), Result().is_canon_form) might not hold", and `nagini_verify.sh model.py` => "Verification successful" (11.46s). So the spec is satisfied by the patched behavior and rejected by the base behavior -- the correct direction, no drift.

4. BUNDLE CHECKERS REPRODUCED INDEPENDENTLY against my own worktree (not a pre-baked /testbed): axiom_check.py => G-AX OK (5 boundary + 5000 fuzz, all four facets); conformance_check.py => G-CONF OK, 100071 inputs, 0 disagreements, seed 11211, every non-empty prepared key resolving in a real dict join.

The two-half join key (numeric identity + canonical object form) is a real property of the repo, not an invented strengthening: I confirmed hash(u)==hash(u.int) but u!=u.int and {(u,C):x}.get((u.int,C)) is None on the live uuid module, which is what makes the form half load-bearing rather than decorative. mapping.md sec 2.2 further documents that no carrier well-formedness precondition (is_canon_form => key==canon) was assumed, keeping the admitted domain wider than reachable values -- I verified prepare_key's Requires is permission-only, so the guarantee was not obtained by domain restriction.

**CONCLUSION:** no input exists on which the modeled prepare_key disagrees with the real patched UUIDField.get_prep_value at the granularity the prefetch join observes. Verdict FAITHFUL. Caveat recorded for the panel: the aliasing gap in (a) and the Promise-uuid axiom-scope boundary in (b) are real modeling approximations, both documented in mapping.md and both provably non-exploitable (immutability; no Value lowering), so neither rises to an unfaithfulness finding.

**Reference used correctly:**  = git worktree of the upstream repository at base_commit ba726067604ce5a8ca3919edf653496722b433ab with patch.diff APPLIED (the modeled function UUIDField.get_prep_value). Base commit used only for the two untouched callees the axioms model (Field.get_prep_value:771-775, UUIDField.to_python:2338-2349 -- patch.diff does not touch either, verified via `git diff --stat` = 1 file / 4 insertions, all inside the new get_prep_value method).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE ROLE (3) on django__django-11211 nagini. NO relaxation in this bundle: meta.json has no `relaxed_leakage` key (checked all 17 top-level keys), no RELAXED_LEAKAGE.md exists anywhere under the instance dir, and gates.G-LEAK.status == "pass" (not "relaxed"). So this is judged as an ordinary strict no-leakage review, not a relaxation assessment.

**ARTIFACT ANCHORING.** Computed the spec view myself via markers.spec_view(model.py, nagini backend) -> sha256 918dfe64b97eb6de18260485aa89b22e02bc862963c41f89e7ea9c05b235bdb0, which matches meta.json region_hashes.spec_view. All 5 recorded region hashes (axioms/pure/pre-conditions/post-conditions/impl) recompute equal; spec_view is idempotent (no marker rot). Confirmed the impl region IS elided in the view (replaced by the consumer placeholder), so the gold body `base_prepare(value)` + `canonicalize(coerced)` is not consumer-visible.

**WHAT CONSUMERS ACTUALLY SEE.** Traced eval/dataset.py + eval/prompts.py + adapter.spec_view: only the spec view is rendered into the task prompt (plus modeled-function symbol names). mapping.md is NOT exposed -- which matters here, because mapping.md names `get_prep_value`, `to_python`, `django/db/models/fields/__init__.py:2328`, and quotes the gold hunk verbatim. Had mapping.md been consumer-visible this would be a flagrant LEAKAGE; it is not, so those disclosures are out of scope for this gate.

MECHANICAL SCREEN (non-vacuous). leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Confirmed non-vacuity by printing what it compared: it extracted changed_symbols={get_prep_value, deconstruct}, changed_files=['django/db/models/fields/`__init__`.py'], and all 3 changed gold lines, and checked them against 24 spec-view identifiers. Each of the 3 normalized gold lines is independently confirmed absent from the normalized view. Screened against problem_statement only, never hints_text (hints here are just "GFK doesn't support prefetch_related" -- a WRONG diagnosis that the spec correctly does not echo).

MANUAL PROBES beyond the mechanical screen. Absent from the spec view: get_prep_value, to_python, prep_value, super(), UUIDField, uuid, django/db, models/fields, `__init__`.py, GenericForeignKey, prefetch_related, CharField, ContentType, content_type, object_id, fk_val, get_prefetch_queryset. Narration vocabulary sweep (bug/fix/patch/regression/previously/incorrectly/wrong/broken/instead of/currently/returns none) -> zero hits. The docstring is written as desired behaviour ("the prepared key must MATCH the key the target record contributes"), never as an edit or a diagnosis; the only edit-adjacent words are "unchanged"/"defers to first"/"reuses" describing the AXIOMATIZED CALLEES, which is required axiom hygiene (an axiom must assert the callee is unchanged) and localizes nothing -- both callees are described purely behaviourally ("base preliminary-coercion step", "canonicalizing parser"), never named.

LOAD-BEARING TEST (the usual test, run rather than asserted). Stripped every comment and blanked every docstring from the spec view, then verified: gold impl on the prose-stripped spec -> `Verification successful` (exit 0); prepatch impl (`return base_prepare(value)`) on the prose-stripped spec -> `Verification failed`, exit 1, error `Postcondition of prepare_key might not hold. Assertion Implies((not value.is_none), Result().is_canon_form) might not hold`. Identical outcome with prose present (gold exit 0 / prepatch exit 1, same clause). So the discrimination between pre- and post-patch behaviour is carried entirely by the FORMAL postcondition, and the removed narration was NOT load-bearing -- the prose is explanatory, not the discriminator. That is the opposite of the relaxation signature.

**PS-DERIVABILITY OF THE DISCRIMINATOR.** The spec's discriminating guarantee is "a non-empty prepared key must be in the canonical object form AND numerically the canonical identity". Every ingredient is public in the problem_statement: it exhibits `models.UUIDField(primary_key=True, default=uuid.uuid4)` as the target pk, `foo_object_id = models.CharField(max_length=255)` as the holder's stored form, `GenericForeignKey`, `prefetch_related('foo')`, and the observed symptom "django orm engine return None for attribute foo". A solver reading only the PS has the str-holder vs UUID-pk type mismatch and the None-result symptom in hand; "the two sides must agree in form as well as value for the in-Python join to match" is the direct derivation, not privileged knowledge. The spec view names the abstract facet (canonical object form) without naming the mechanism site, the method, or the two-line body. Notably the spec view does NOT reveal WHERE to edit (nothing points at UUIDField or the field-preparation hook) -- a solver still has to localize.

**BUNDLE-DIRECTED-TEXT CHECK.** Grepped all bundle.md/.py for text addressing an attacker/panel/reviewer or prescribing a verdict ("attacker", "panel", "reviewer", "verdict", "NO-LEAKAGE", "submit_result", "you should", "honest verdict", "do not report"). All hits were incidental English ("record contributes", "recorded refutation", "harness records a timeout") in behavioural prose. NO file in this bundle attempts to instruct me how to record or which verdict to submit. Nothing to report on that axis.

**VERDICT:** NO-LEAKAGE. The spec view quotes no gold line, names no patched file/module/symbol, uses no identifier echoing a patched repo symbol, narrates no bug->fix mechanism, and echoes no hints_text-only vocabulary; its discriminating clause is formally load-bearing and independently derivable from the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
