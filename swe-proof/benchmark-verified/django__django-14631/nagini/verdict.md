# P2 adversarial audit — django__django-14631

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec impl's faithful refined patch failed to resolve. 12 attacks encoded; 8 were rejected by the spec (verification failed), 4 verified (atk_6, atk_8, atk_9, atk_12) and ALL FOUR of their materialized faithful patches RESOLVED under the official harness (run_resolve, resolved=true, completed=true, flaky=false, attempts=1). The four verifying impls are all provably value-equal to normalise(fs.first_eval) — atk_6's guard (first_eval % 1e6 == 0) makes its raw arm equal the normalised arm; atk_8/atk_12 inline the same floor; atk_9 prepends a bounded inert loop. They are structural variants of the gold impl, not wrong impls, which is why they both verify and resolve. This matches the bundle's own G-PBT lane, which already classifies exactly this shape (_POS_INLINE) as a positive control that MUST verify.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,9 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
+    # ATTACK 1 (pre-patch bug reproduction): the value is obtained by
+    # evaluating the initial source AFRESH, un-normalised.
+    value = fs.fresh_eval
     cleaned = value
     return cleaned
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,9 +127,12 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
+    # ATTACK 2 (control-flow-effect / dead extra evaluation): perform a
+    # SECOND evaluation of the initial source whose result is discarded, then
+    # read the cached bound initial. Value-correct, effect-wrong: in the real
+    # form machinery the dead call advances the stateful source so the cached
+    # bound initial captures a LATER evaluation.
+    dead = fs.fresh_eval
     value = bound_initial(fs)
     cleaned = value
     return cleaned
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,11 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
+    # ATTACK 3 (partial correctness / divergence): never produce the value.
     value = bound_initial(fs)
+    i = 0
+    while i >= 0:
+        i = i + 1
     cleaned = value
     return cleaned
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,7 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 4 (divergence via self-recursion): delegate to itself forever.
+    cleaned = clean_bound_initial_field(fs)
     return cleaned
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,9 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 5 (boundary / off-by-one): round the sub-second component UP to
+    # the next whole second instead of dropping it. Agrees with the bound
+    # initial exactly when the sub-second component is already zero.
+    cleaned = ((fs.first_eval + 999999) // 1000000) * 1000000
     return cleaned
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -127,10 +127,13 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 6 (partial domain): on the sub-second == 0 slice return the RAW
+    # (un-normalised) first evaluation of the initial source rather than the
+    # value read through the field's bound initial; elsewhere read the bound
+    # initial.
+    if fs.first_eval % 1000000 == 0:
+        cleaned = fs.first_eval
+    else:
+        cleaned = bound_initial(fs)
     return cleaned
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,12 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 7 (ungrounded-oracle echo): fabricate a fresh field state out of
+    # the value in hand, read that fabricated state's SECOND-evaluation field
+    # (which the real spec denies this function), and answer from the
+    # fabricated state's bound initial.
+    other = FieldState(fs.first_eval, 0)
+    echo = other.fresh_eval
+    cleaned = bound_initial(other) + echo
     return cleaned
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -127,10 +127,10 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 8 (raw-source read): do NOT read the field's bound initial at
+    # all. Read the un-normalised FIRST evaluation of the initial source
+    # directly and strip its sub-second component here.
+    raw = fs.first_eval
+    cleaned = (raw // 1000000) * 1000000
     return cleaned
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -127,10 +127,13 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 9 (control-flow effect, terminating): spin a bounded loop first,
+    # then answer from the raw un-normalised first evaluation of the source.
+    i = 0
+    while i < 3:
+        Invariant(i >= 0 and i <= 3)
+        Invariant(MustTerminate(3 - i))
+        i = i + 1
+    cleaned = (fs.first_eval // 1000000) * 1000000
     return cleaned
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,10 +127,9 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 10 (frame): overwrite the field's first evaluation, then answer
+    # consistently with the overwritten state.
+    fs.first_eval = 0
+    cleaned = 0
     return cleaned
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -127,9 +127,9 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
+    # ATTACK 11 (vacuity control): if the precondition were infeasible this
+    # would verify and the whole spec would prove nothing.
+    Assert(False)
     value = bound_initial(fs)
     cleaned = value
     return cleaned
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -127,10 +127,14 @@
     Ensures(Result() == normalise(fs.first_eval))
     # post-conditions-end
     # impl-start
-    # Read the value through the field's bound initial (single cached,
-    # normalised evaluation), then clean it. Cleaning a date/time value is the
-    # identity on the value it is given.
-    value = bound_initial(fs)
-    cleaned = value
+    # ATTACK 12 (repeated permitted read): read the field's bound initial
+    # several times over, and read the first-evaluation carrier directly too,
+    # before answering. Every one of these reads is PERMITTED by the
+    # precondition (Acc(fs.first_eval, 1/2)).
+    a = bound_initial(fs)
+    b = bound_initial(fs)
+    c = fs.first_eval
+    d = fs.first_eval
+    cleaned = (c // 1000000) * 1000000
     return cleaned
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14631.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a form cleans a field whose input is taken from its bound initial value
  (the case where the field does not draw its value from submitted data, so the
  bound initial is the value to be cleaned), the cleaned value MUST equal the
  value exposed as that field's bound initial.

  The bound initial value has two defining properties:

    (1) the underlying initial source is evaluated EXACTLY ONCE and the single
        resulting value is reused (it is cached) — even when the source is a
        callable that would yield a different value on each evaluation; and

    (2) for an auto-generated date/time value whose presentation widget does
        not carry sub-second precision, the sub-second component is dropped
        (normalised), for standardised handling.

  Consequently the value produced when cleaning such a field must match the
  field's bound initial value exactly: it must be the SAME single evaluation,
  and it must be the NORMALISED (sub-second-stripped) form — never a fresh,
  un-normalised re-evaluation of the source.

  Moreover, evaluating the initial source is a STATEFUL operation: a callable
  source may advance its own state on every call, so any EXTRA evaluation —
  even one whose result is immediately discarded — can change which value the
  single cached evaluation captures (an extra call made before the cached
  bound initial is first read shifts the cache to a later evaluation).
  Cleaning the field therefore has NO RIGHT to evaluate the source afresh: it
  may only read the already-cached bound initial. In the model this is
  encoded by granting the cleaning function NO permission at all to
  `fresh_eval`: an implementation that so much as READS the fresh
  re-evaluation (i.e. performs a second evaluation of the source, even a
  dead one) fails verification for insufficient permission.

The field is modelled as a minimal class carrying only the touched quantities:
the value of the first evaluation of the initial source (`first_eval`), the
value a second, independent evaluation would yield (`fresh_eval`, distinct for a
stateful source), and the cached bound initial. A date/time value is modelled as
an integer encoding `whole_seconds * 1_000_000 + sub_second_units`; dropping the
sub-second component is modelled by `normalise`. Cleaning such a field is the
identity on the value it is given (a date/time value validates to itself).

Cleaning a field is a bounded, per-field step of form validation: it MUST
terminate and produce the cleaned value (a total-correctness obligation,
carried as MustTerminate in the precondition). An implementation that
diverges — e.g. hangs inside the cleaning step instead of producing the
value — would satisfy the value postconditions only vacuously and would hang
form validation (and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class FieldState:
    def __init__(self, first_eval: int, fresh_eval: int) -> None:
        Requires(first_eval >= 0 and fresh_eval >= 0)
        Ensures(Acc(self.first_eval, 1 / 2) and self.first_eval == first_eval)  # type: ignore
        Ensures(Acc(self.fresh_eval, 1 / 2) and self.fresh_eval == fresh_eval)  # type: ignore
        self.first_eval = first_eval
        self.fresh_eval = fresh_eval

# axioms-start
# (no @ContractOnly axioms are consumed: every operation the cleaned-value
# computation performs — the single normalised evaluation read from the bound
# initial, and the identity clean of a date/time value — is modelled deeply.)
# axioms-end

# pure-start
@Pure
def normalise(value: int) -> int:
    """Drop the sub-second component of an encoded date/time value. The
    encoding is `whole_seconds * 1_000_000 + sub_second_units` with
    `0 <= sub_second_units < 1_000_000`; normalisation floors to the whole
    second. Idempotent and a function of its argument alone."""
    Requires(value >= 0)
    Ensures(Result() >= 0)
    Ensures(Result() == (value // 1000000) * 1000000)
    return (value // 1000000) * 1000000

@Pure
def bound_initial(fs: FieldState) -> int:
    """The value exposed as the field's bound initial: the NORMALISED form of
    the SINGLE (first) evaluation of the initial source. This is the cached
    value reused everywhere the bound initial is read."""
    Requires(Acc(fs.first_eval, 1 / 4))
    Requires(fs.first_eval >= 0)
    Ensures(Result() == normalise(fs.first_eval))
    return normalise(fs.first_eval)
# pure-end

def clean_bound_initial_field(fs: FieldState) -> int:
    # pre-conditions-start
    Requires(Acc(fs.first_eval, 1 / 2))
    Requires(fs.first_eval >= 0)
    # DELIBERATELY NO permission to fs.fresh_eval: evaluating the initial
    # source is a stateful operation (a callable source advances its state on
    # every call), so ANY extra evaluation — even one whose result is
    # immediately discarded — shifts which value the single cached evaluation
    # captures and breaks cleaned == bound initial in the real form machinery.
    # Cleaning may only read the already-cached bound initial; an impl that so
    # much as READS fs.fresh_eval (performs a second evaluation of the source)
    # must fail verification for insufficient permission.
    # Cleaning a field is a bounded step of form validation: it MUST terminate
    # (total correctness). A diverging impl (e.g. hanging inside the cleaning
    # step instead of producing the cleaned value) would satisfy the value
    # postconditions only vacuously and hang form validation (and the F2P
    # test) forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fs.first_eval, 1 / 2))
    Ensures(fs.first_eval >= 0)
    # The cleaned value equals the field's bound initial value: the single,
    # cached evaluation of the source...
    Ensures(Result() == bound_initial(fs))
    # ...grounded in the inputs: it is the NORMALISED form of the first (the
    # only) evaluation of the initial source, never a fresh re-evaluation.
    Ensures(Result() == normalise(fs.first_eval))
    # post-conditions-end
    # impl-start
    # Read the value through the field's bound initial (single cached,
    # normalised evaluation), then clean it. Cleaning a date/time value is the
    # identity on the value it is given.
    value = bound_initial(fs)
    cleaned = value
    return cleaned
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: A-legs + model↔patch correspondence (R/I legs left to G-CONF, which passed 100000/0 with oracle = the real patched BaseForm._clean_fields, called not transliterated).

### Commands
  same-spec: python -m swebench_unified.adversary same-spec nagini django__django-14631 <D>/atk_N.py  -> SAME for all 12 + pos_control
  weakness:  python -m swebench_unified.adversary weakness  nagini django__django-14631 <D>/atk_N.py  (run 3-at-a-time as background jobs)
  verify:    bash scripts/nagini_verify.sh <D>/pos_control.py
  resolve:   python <D>/resolve.py atk_N   (calls swebench_unified.harness.run_resolve on <D>/patch_atk_N.diff, retries=1)

### PER-ATTACK RESULTS (exit 2 = NOT-A-COUNTEREXAMPLE i.e. spec rejected it; exit 0 = CANDIDATE):
atk_1.py  pre-patch bug (value = fs.fresh_eval)            -> exit 2. REJECTED: 'atk_1.py:132: Assignment might fail. There might be insufficient permission to access fs.fresh_eval.' PREPATCH REPRODUCED. atk_2.py  dead extra evaluation then correct value          -> exit 2. REJECTED at line 135 with the SAME insufficient-permission error.

This is the prior pass's named counterexample (refinement.md A0b's 'atk_8'); the no-Acc-on-fresh_eval pin genuinely closes it, and I confirmed the closure is by permission, not by luck. atk_3.py  divergence (while i >= 0: i += 1) after the value -> exit 2. REJECTED (MustTerminate(2)). atk_4.py  divergence via unguarded self-recursion           -> exit 2. REJECTED (MustTerminate). atk_5.py  boundary: ceil-to-second instead of floor         -> exit 2. REJECTED (fails Result() == normalise(first_eval) whenever sub-second > 0). atk_6.py  partial-domain: raw first_eval on the %1e6==0 slice -> exit 0 CANDIDATE (19.7s).

Patch <D>/patch_atk_6.diff -> RESOLVED. atk_7.py  ungrounded-oracle echo via a fabricated FieldState -> exit 2. REJECTED, but on an obligation technicality: 'atk_7.py:134: Obligation leak check failed. Callee __init__ might not take all unsatisfied obligations from the caller' (FieldState.__init__ lacks MustTerminate under the caller's obligation). I record this as a WEAK rejection: it blocks constructing a fresh carrier at all, so it does not by itself demonstrate the value spec rejects an echo. The value spec's real defence is that Result() is pinned to normalise(fs.first_eval), a @Pure function fully unfolded in the INPUT — so there is no unpinned oracle field to echo.

Verified independently by atk_8/atk_12 verifying only because they compute that exact value. atk_8.py  raw-source read + inline sub-second strip          -> exit 0 CANDIDATE (20.1s). Patch <D>/patch_atk_8.diff -> RESOLVED. atk_9.py  bounded inert loop then the normalised value       -> exit 0 CANDIDATE (19.9s). Patch <D>/patch_atk_9.diff -> RESOLVED. atk_10.py frame attack: fs.first_eval = 0 then answer 0      -> exit 2. REJECTED (write needs full permission; only Acc 1/2 held). atk_11.py vacuity control Assert(False)                      -> exit 2. REJECTED => the precondition is FEASIBLE, so the whole spec is non-vacuous (guarded-self-call/infeasible-guard failure mode ruled out). atk_12.py repeated PERMITTED reads (4x bound_initial/first_eval) -> exit 0 CANDIDATE (21.7s). Patch <D>/patch_atk_12.diff -> RESOLVED.

POSITIVE CONTROL: <D>/pos_control.py is byte-identical to the bundle model.py (cmp clean) and VERIFIES ('Verification successful', 27.5s).

### RESOLVE EVIDENCE (official harness, all completed, none flaky):
  atk_6  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
  atk_8  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
  atk_9  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
  atk_12 {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
Each patch was built by cloning django at base_commit 84400d2e9db7c51fee4e9bb04c028f665b8e7624, applying patch.diff (gold) and then replacing ONLY the disabled-field branch of _clean_fields with the attack's faithful rendering (plus the `import datetime` the rendering needs); `git diff` captured. Syntax-checked and locally exercised against both F2P tests before the harness run.

### FAITHFULNESS RULE I APPLIED (and why it is the honest one — this is the crux of the audit):
The model carries the NUMBER of source evaluations in WHICH carrier field the impl touches. Per mapping.md rows 16/17 and §2, `fs.first_eval` = the single evaluation the bound initial caches (repo: a read of the `bf.initial` @cached_property — effect-free and freely repeatable, since the cache makes re-reads free), while a SECOND, new `get_initial_for_field()` evaluation is `fs.fresh_eval`, to which the cleaning function has NO permission. So a verifying impl can never carry a new source evaluation, and a `first_eval` read must be rendered as a `bf.initial` read.

I deliberately tested the ALTERNATIVE (adversarial) rendering first: rendering atk_8's `fs.first_eval` as a fresh `self.get_initial_for_field(field, name)` call DOES break F2P test 2 locally (cleaned = ...:46 but bf.initial = ...:47, cleaned != bf.initial). I did NOT report that as a break, because that rendering imports an extra stateful evaluation the model explicitly denies the impl (it is the `fresh_eval` op, i.e. atk_1/atk_2, both of which the spec REJECTS by insufficient permission). Charging the spec for a rendering that contradicts its own permission map would be inventing weakness. Under the faithful rendering all four candidates resolve.

Corroboration that this reading is the bundle's own: properties.py's G-PBT `pos-control-inline-normalise` is behaviourally identical to atk_6/atk_8 (`whole = (first_eval//1e6)*1e6`, branch, both arms equal) and is declared a SOUNDNESS control that MUST verify; while `partial-domain-unnormalised-first` (raw first_eval, NO strip) is a reject case. My atk_6/atk_8 DO strip, so verifying is the intended, correct behaviour.

### A-LEG AUDIT (the assigned focus):
  * There is NO consumed @ContractOnly axiom (grep: the only 'ContractOnly' occurrence in model.py is line 69, a comment saying none are consumed). So there is no axiom whose Ensures could be assumed-but-false — the classic A-leg hazard is structurally absent.
  * The single A-reference (bound_initial/normalise <-> BoundField.initial) I re-ran INDEPENDENTLY, not trusting meta.json: axiom_check.py against my gold-patched checkout -> exit 0, 'R1/R2 sound ... R3 pre-patch disagreement is real', 50008 observations.
  * NON-VACUITY of that A-leg: I ran the same checker against the UNPATCHED base checkout -> it FAILS with 'R2 violated: _clean_fields value datetime(2006,10,25,14,30,46,123456) != bound initial datetime(2006,10,25,14,30,47)'. So the A-reference genuinely discriminates patched from unpatched; it is not a tautology that would pass either way.
  * Correspondence of the A-reference to the real callee checked by reading source at base_commit: boundfield.py:211-219 is `@cached_property def initial` doing `get_initial_for_field` once then `data.replace(microsecond=0)` when the value is a datetime/time and `not widget.supports_microseconds` — exactly `normalise(first_eval)` under the int encoding (both epochs have microsecond==0, so floor-to-1e6 == replace(microsecond=0)). The A3 'clean is the identity' leg matches fields.py DateTimeField.to_python returning the datetime unchanged with USE_TZ=False.

REFINEMENT.MD LEG AUDIT: A0 (R, MustTerminate), A0b (R, permission-as-effect), A1 (R, type refinement), A2 (R + A-reference), A3 (I), A4 (I); §B refactor hunks all I; §C explicitly claims no kind-3 and I confirmed it — every leg is R / A-reference / I, and the one genuinely CHANGED operation (the disabled value source) is modelled deeply rather than hidden behind an axiom about the function under change. No kind-3 leg found. §B's 'observationally inert' claim is consistent with the 117 PASS_TO_PASS tests plus my resolves (which exercise the full refactor).

CAVEATS / RESIDUAL RISK (honest limits of this pass):
  1. atk_7's rejection is by an obligation-leak technicality rather than by the value spec; the model's carrier class cannot be constructed inside the method at all. This narrows what an echo-style attack can even express here, so 'no ungrounded oracle' rests on the postcondition being grounded in fs.first_eval (which it is, textually and by the verifying/rejecting pattern of atk_5/atk_6/atk_8) rather than on atk_7 alone.
  2. The spec models ONE branch (disabled == True, non-micro widget) and the value's cleaning as the identity; anything outside that (FileField's two-arg clean, micro-supporting widgets, the bf.data branch) is out of the modelled domain by declaration in mapping.md §2, so this gate cannot speak to it. That is a stated scope limit, not a defect I can charge.
  3. The effect discipline is encoded as PERMISSION (absence of Acc on fresh_eval), not as an explicit call-count; it is sound for the extra-evaluation attack class I could express (atk_1, atk_2 both rejected), but it is an encoding of an effect in a value model.

CONCLUSION: >= 5 distinct attack classes run to completion (12 encoded: partial-domain, boundary, control-flow-effect x2, divergence x2, frame, ungrounded-oracle echo, prepatch, vacuity control, permitted-read); every CANDIDATE had its faithful patch materialized and EXECUTED through the official harness; all four resolved; the prepatch bug and the prior pass's named counterexample are both reproduced and both rejected by the spec; the positive control verifies; the vacuity control is rejected; the A-reference reproduces and discriminates. No verify-but-not-resolve gap found => verdict SOUND (advisory; runner re-runs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_10.py`, `atk_11.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_12.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying same-spec impl's faithful refined patch failed to resolve. 12 attacks encoded; 8 were rejected by the spec (verification failed), 4 verified (atk_6, atk_8, atk_9, atk_12) and ALL FOUR of their materialized faithful patches RESOLVED under the official harness (run_resolve, resolved=true, completed=true, flaky=false, attempts=1). The four verifying impls are all provably value-equal to normalise(fs.first_eval) — atk_6's guard (first_eval % 1e6 == 0) makes its raw arm equal the normalised arm; atk_8/atk_12 inline the same floor; atk_9 prepends a bounded inert loop. They are structural variants of the gold impl, not wrong impls, which is why they both verify and resolve. This matches the bundle's own G-PBT lane, which already classifies exactly this shape (_POS_INLINE) as a positive control that MUST verify.
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14631.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a form cleans a field whose input is taken from its bound initial value
  (the case where the field does not draw its value from submitted data, so the
  bound initial is the value to be cleaned), the cleaned value MUST equal the
  value exposed as that field's bound initial.

  The bound initial value has two defining properties:

    (1) the underlying initial source is evaluated EXACTLY ONCE and the single
        resulting value is reused (it is cached) — even when the source is a
        callable that would yield a different value on each evaluation; and

    (2) for an auto-generated date/time value whose presentation widget does
        not carry sub-second precision, the sub-second component is dropped
        (normalised), for standardised handling.

  Consequently the value produced when cleaning such a field must match the
  field's bound initial value exactly: it must be the SAME single evaluation,
  and it must be the NORMALISED (sub-second-stripped) form — never a fresh,
  un-normalised re-evaluation of the source.

  Moreover, evaluating the initial source is a STATEFUL operation: a callable
  source may advance its own state on every call, so any EXTRA evaluation —
  even one whose result is immediately discarded — can change which value the
  single cached evaluation captures (an extra call made before the cached
  bound initial is first read shifts the cache to a later evaluation).
  Cleaning the field therefore has NO RIGHT to evaluate the source afresh: it
  may only read the already-cached bound initial. In the model this is
  encoded by granting the cleaning function NO permission at all to
  `fresh_eval`: an implementation that so much as READS the fresh
  re-evaluation (i.e. performs a second evaluation of the source, even a
  dead one) fails verification for insufficient permission.

The field is modelled as a minimal class carrying only the touched quantities:
the value of the first evaluation of the initial source (`first_eval`), the
value a second, independent evaluation would yield (`fresh_eval`, distinct for a
stateful source), and the cached bound initial. A date/time value is modelled as
an integer encoding `whole_seconds * 1_000_000 + sub_second_units`; dropping the
sub-second component is modelled by `normalise`. Cleaning such a field is the
identity on the value it is given (a date/time value validates to itself).

Cleaning a field is a bounded, per-field step of form validation: it MUST
terminate and produce the cleaned value (a total-correctness obligation,
carried as MustTerminate in the precondition). An implementation that
diverges — e.g. hangs inside the cleaning step instead of producing the
value — would satisfy the value postconditions only vacuously and would hang
form validation (and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class FieldState:
    def __init__(self, first_eval: int, fresh_eval: int) -> None:
        Requires(first_eval >= 0 and fresh_eval >= 0)
        Ensures(Acc(self.first_eval, 1 / 2) and self.first_eval == first_eval)  # type: ignore
        Ensures(Acc(self.fresh_eval, 1 / 2) and self.fresh_eval == fresh_eval)  # type: ignore
        self.first_eval = first_eval
        self.fresh_eval = fresh_eval

# axioms-start
# (no @ContractOnly axioms are consumed: every operation the cleaned-value
# computation performs — the single normalised evaluation read from the bound
# initial, and the identity clean of a date/time value — is modelled deeply.)
# axioms-end

# pure-start
@Pure
def normalise(value: int) -> int:
    """Drop the sub-second component of an encoded date/time value. The
    encoding is `whole_seconds * 1_000_000 + sub_second_units` with
    `0 <= sub_second_units < 1_000_000`; normalisation floors to the whole
    second. Idempotent and a function of its argument alone."""
    Requires(value >= 0)
    Ensures(Result() >= 0)
    Ensures(Result() == (value // 1000000) * 1000000)
    return (value // 1000000) * 1000000

@Pure
def bound_initial(fs: FieldState) -> int:
    """The value exposed as the field's bound initial: the NORMALISED form of
    the SINGLE (first) evaluation of the initial source. This is the cached
    value reused everywhere the bound initial is read."""
    Requires(Acc(fs.first_eval, 1 / 4))
    Requires(fs.first_eval >= 0)
    Ensures(Result() == normalise(fs.first_eval))
    return normalise(fs.first_eval)
# pure-end

def clean_bound_initial_field(fs: FieldState) -> int:
    # pre-conditions-start
    Requires(Acc(fs.first_eval, 1 / 2))
    Requires(fs.first_eval >= 0)
    # DELIBERATELY NO permission to fs.fresh_eval: evaluating the initial
    # source is a stateful operation (a callable source advances its state on
    # every call), so ANY extra evaluation — even one whose result is
    # immediately discarded — shifts which value the single cached evaluation
    # captures and breaks cleaned == bound initial in the real form machinery.
    # Cleaning may only read the already-cached bound initial; an impl that so
    # much as READS fs.fresh_eval (performs a second evaluation of the source)
    # must fail verification for insufficient permission.
    # Cleaning a field is a bounded step of form validation: it MUST terminate
    # (total correctness). A diverging impl (e.g. hanging inside the cleaning
    # step instead of producing the cleaned value) would satisfy the value
    # postconditions only vacuously and hang form validation (and the F2P
    # test) forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(fs.first_eval, 1 / 2))
    Ensures(fs.first_eval >= 0)
    # The cleaned value equals the field's bound initial value: the single,
    # cached evaluation of the source...
    Ensures(Result() == bound_initial(fs))
    # ...grounded in the inputs: it is the NORMALISED form of the first (the
    # only) evaluation of the initial source, never a fresh re-evaluation.
    Ensures(Result() == normalise(fs.first_eval))
    # post-conditions-end
    # impl-start
    # Read the value through the field's bound initial (single cached,
    # normalised evaluation), then clean it. Cleaning a date/time value is the
    # identity on the value it is given.
    value = bound_initial(fs)
    cleaned = value
    return cleaned
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: A-legs + model↔patch correspondence (R/I legs left to G-CONF, which passed 100000/0 with oracle = the real patched BaseForm._clean_fields, called not transliterated).

### Commands
  same-spec: python -m swebench_unified.adversary same-spec nagini django__django-14631 <D>/atk_N.py  -> SAME for all 12 + pos_control
  weakness:  python -m swebench_unified.adversary weakness  nagini django__django-14631 <D>/atk_N.py  (run 3-at-a-time as background jobs)
  verify:    bash scripts/nagini_verify.sh <D>/pos_control.py
  resolve:   python <D>/resolve.py atk_N   (calls swebench_unified.harness.run_resolve on <D>/patch_atk_N.diff, retries=1)

### PER-ATTACK RESULTS (exit 2 = NOT-A-COUNTEREXAMPLE i.e. spec rejected it; exit 0 = CANDIDATE):
atk_1.py  pre-patch bug (value = fs.fresh_eval)            -> exit 2. REJECTED: 'atk_1.py:132: Assignment might fail. There might be insufficient permission to access fs.fresh_eval.' PREPATCH REPRODUCED. atk_2.py  dead extra evaluation then correct value          -> exit 2. REJECTED at line 135 with the SAME insufficient-permission error.

This is the prior pass's named counterexample (refinement.md A0b's 'atk_8'); the no-Acc-on-fresh_eval pin genuinely closes it, and I confirmed the closure is by permission, not by luck. atk_3.py  divergence (while i >= 0: i += 1) after the value -> exit 2. REJECTED (MustTerminate(2)). atk_4.py  divergence via unguarded self-recursion           -> exit 2. REJECTED (MustTerminate). atk_5.py  boundary: ceil-to-second instead of floor         -> exit 2. REJECTED (fails Result() == normalise(first_eval) whenever sub-second > 0). atk_6.py  partial-domain: raw first_eval on the %1e6==0 slice -> exit 0 CANDIDATE (19.7s).

Patch <D>/patch_atk_6.diff -> RESOLVED. atk_7.py  ungrounded-oracle echo via a fabricated FieldState -> exit 2. REJECTED, but on an obligation technicality: 'atk_7.py:134: Obligation leak check failed. Callee __init__ might not take all unsatisfied obligations from the caller' (FieldState.__init__ lacks MustTerminate under the caller's obligation). I record this as a WEAK rejection: it blocks constructing a fresh carrier at all, so it does not by itself demonstrate the value spec rejects an echo. The value spec's real defence is that Result() is pinned to normalise(fs.first_eval), a @Pure function fully unfolded in the INPUT — so there is no unpinned oracle field to echo.

Verified independently by atk_8/atk_12 verifying only because they compute that exact value. atk_8.py  raw-source read + inline sub-second strip          -> exit 0 CANDIDATE (20.1s). Patch <D>/patch_atk_8.diff -> RESOLVED. atk_9.py  bounded inert loop then the normalised value       -> exit 0 CANDIDATE (19.9s). Patch <D>/patch_atk_9.diff -> RESOLVED. atk_10.py frame attack: fs.first_eval = 0 then answer 0      -> exit 2. REJECTED (write needs full permission; only Acc 1/2 held). atk_11.py vacuity control Assert(False)                      -> exit 2. REJECTED => the precondition is FEASIBLE, so the whole spec is non-vacuous (guarded-self-call/infeasible-guard failure mode ruled out). atk_12.py repeated PERMITTED reads (4x bound_initial/first_eval) -> exit 0 CANDIDATE (21.7s). Patch <D>/patch_atk_12.diff -> RESOLVED.

POSITIVE CONTROL: <D>/pos_control.py is byte-identical to the bundle model.py (cmp clean) and VERIFIES ('Verification successful', 27.5s).

### RESOLVE EVIDENCE (official harness, all completed, none flaky):
  atk_6  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
  atk_8  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
  atk_9  {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
  atk_12 {"resolved": true, "completed": true, "note": "resolved", "attempts": 1}
Each patch was built by cloning django at base_commit 84400d2e9db7c51fee4e9bb04c028f665b8e7624, applying patch.diff (gold) and then replacing ONLY the disabled-field branch of _clean_fields with the attack's faithful rendering (plus the `import datetime` the rendering needs); `git diff` captured. Syntax-checked and locally exercised against both F2P tests before the harness run.

### FAITHFULNESS RULE I APPLIED (and why it is the honest one — this is the crux of the audit):
The model carries the NUMBER of source evaluations in WHICH carrier field the impl touches. Per mapping.md rows 16/17 and §2, `fs.first_eval` = the single evaluation the bound initial caches (repo: a read of the `bf.initial` @cached_property — effect-free and freely repeatable, since the cache makes re-reads free), while a SECOND, new `get_initial_for_field()` evaluation is `fs.fresh_eval`, to which the cleaning function has NO permission. So a verifying impl can never carry a new source evaluation, and a `first_eval` read must be rendered as a `bf.initial` read.

I deliberately tested the ALTERNATIVE (adversarial) rendering first: rendering atk_8's `fs.first_eval` as a fresh `self.get_initial_for_field(field, name)` call DOES break F2P test 2 locally (cleaned = ...:46 but bf.initial = ...:47, cleaned != bf.initial). I did NOT report that as a break, because that rendering imports an extra stateful evaluation the model explicitly denies the impl (it is the `fresh_eval` op, i.e. atk_1/atk_2, both of which the spec REJECTS by insufficient permission). Charging the spec for a rendering that contradicts its own permission map would be inventing weakness. Under the faithful rendering all four candidates resolve.

Corroboration that this reading is the bundle's own: properties.py's G-PBT `pos-control-inline-normalise` is behaviourally identical to atk_6/atk_8 (`whole = (first_eval//1e6)*1e6`, branch, both arms equal) and is declared a SOUNDNESS control that MUST verify; while `partial-domain-unnormalised-first` (raw first_eval, NO strip) is a reject case. My atk_6/atk_8 DO strip, so verifying is the intended, correct behaviour.

### A-LEG AUDIT (the assigned focus):
  * There is NO consumed @ContractOnly axiom (grep: the only 'ContractOnly' occurrence in model.py is line 69, a comment saying none are consumed). So there is no axiom whose Ensures could be assumed-but-false — the classic A-leg hazard is structurally absent.
  * The single A-reference (bound_initial/normalise <-> BoundField.initial) I re-ran INDEPENDENTLY, not trusting meta.json: axiom_check.py against my gold-patched checkout -> exit 0, 'R1/R2 sound ... R3 pre-patch disagreement is real', 50008 observations.
  * NON-VACUITY of that A-leg: I ran the same checker against the UNPATCHED base checkout -> it FAILS with 'R2 violated: _clean_fields value datetime(2006,10,25,14,30,46,123456) != bound initial datetime(2006,10,25,14,30,47)'. So the A-reference genuinely discriminates patched from unpatched; it is not a tautology that would pass either way.
  * Correspondence of the A-reference to the real callee checked by reading source at base_commit: boundfield.py:211-219 is `@cached_property def initial` doing `get_initial_for_field` once then `data.replace(microsecond=0)` when the value is a datetime/time and `not widget.supports_microseconds` — exactly `normalise(first_eval)` under the int encoding (both epochs have microsecond==0, so floor-to-1e6 == replace(microsecond=0)). The A3 'clean is the identity' leg matches fields.py DateTimeField.to_python returning the datetime unchanged with USE_TZ=False.

REFINEMENT.MD LEG AUDIT: A0 (R, MustTerminate), A0b (R, permission-as-effect), A1 (R, type refinement), A2 (R + A-reference), A3 (I), A4 (I); §B refactor hunks all I; §C explicitly claims no kind-3 and I confirmed it — every leg is R / A-reference / I, and the one genuinely CHANGED operation (the disabled value source) is modelled deeply rather than hidden behind an axiom about the function under change. No kind-3 leg found. §B's 'observationally inert' claim is consistent with the 117 PASS_TO_PASS tests plus my resolves (which exercise the full refactor).

CAVEATS / RESIDUAL RISK (honest limits of this pass):
  1. atk_7's rejection is by an obligation-leak technicality rather than by the value spec; the model's carrier class cannot be constructed inside the method at all. This narrows what an echo-style attack can even express here, so 'no ungrounded oracle' rests on the postcondition being grounded in fs.first_eval (which it is, textually and by the verifying/rejecting pattern of atk_5/atk_6/atk_8) rather than on atk_7 alone.
  2. The spec models ONE branch (disabled == True, non-micro widget) and the value's cleaning as the identity; anything outside that (FileField's two-arg clean, micro-supporting widgets, the bf.data branch) is out of the modelled domain by declaration in mapping.md §2, so this gate cannot speak to it. That is a stated scope limit, not a defect I can charge.
  3. The effect discipline is encoded as PERMISSION (absence of Acc on fresh_eval), not as an explicit call-count; it is sound for the extra-evaluation attack class I could express (atk_1, atk_2 both rejected), but it is an encoding of an effect in a value model.

CONCLUSION: >= 5 distinct attack classes run to completion (12 encoded: partial-domain, boundary, control-flow-effect x2, divergence x2, frame, ungrounded-oracle echo, prepatch, vacuity control, permitted-read); every CANDIDATE had its faithful patch materialized and EXECUTED through the official harness; all four resolved; the prepatch bug and the prior pass's named counterexample are both reproduced and both rejected by the spec; the positive control verifies; the vacuity control is rejected; the A-reference reproduces and discriminates. No verify-but-not-resolve gap found => verdict SOUND (advisory; runner re-runs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Cloned django_django.git at base_commit 84400d2e9db7; built three trees: patched (gold patch + test patch applied cleanly), basetest (test patch only), deadcall/aftercall (gold + injected probe). Confirmed F2P fails at base (2 failures) and passes with gold (120/120 OK), so the oracle is real.

SPEC INTEGRITY. markers.region_hashes on the bundle model.py reproduces the G-HYGIENE record exactly (pre a3466.../57a1cf...; post a4a154...; impl 25b75c...; spec_view 5a01f1...). NOTE: meta.json's TOP-LEVEL region_hashes block is STALE — its post-conditions/pre-conditions/spec_view (a3466255/988954b5/430c8159) disagree with both the G-HYGIENE record and the live file. Bookkeeping drift only; the live model.py matches the gate that actually adjudicated it. same-spec on the unmodified model returns SAME (exit 0); nagini_verify.sh on model.py: Verification successful (14.75s).

FAITHFULNESS PROBES (real patched repo, driven end-to-end through form.errors -> full_clean -> _clean_fields, nothing stubbed except a recording wrapper on the initial SOURCE, which is an input):
1. Bundle gates re-run independently: axiom_check exit 0; conformance_check exit 0 (100000 inputs, seed 14631, 0 disagreements, source evaluated exactly once every case).
2. INDEPENDENT off-seed fuzz (my own harness, seeds 999331/424242/7/20260814, 120000 inputs total over full datetime range x sub-second range x {DateTimeField,TimeField} x {form_initial,field_initial} x {stateful,stateless}): 0 divergences on all three legs (value == normalise(first_eval); cleaned == real BoundField.initial; ncalls == 1).
3. Extremes/edges: datetime.min, datetime.max, time.min, time.max, us=0/1/500000/999999, fold=1, a datetime SUBCLASS source, SplitDateTimeField (supports_microseconds False), large state step — all AGREE.
4. Interference orderings: as_p() / has_changed() / changed_data / bf.initial read BEFORE cleaning — all still ncalls=1 and AGREE, so the cached_property model is robust to the refactored _bound_items/_has_changed paths.

PERMISSION PIN IS GROUNDED, NOT DECORATIVE. Injected a DEAD `self.get_initial_for_field(field, name)` BEFORE `value = bf.initial` into the real patched _clean_fields: both F2P tests FAIL (cleaned 14:30:47 != 14:30:46). So refinement.md A0b / mapping.md §2 'permission-as-effect' reflects real repo behavior — a discarded extra evaluation really does shift the cache and break the hidden tests. The no-Acc(fs.fresh_eval) pin closes a genuine partial-correctness gap (the atk_8 shape).

STRENGTH ASYMMETRY (disclosed, sound direction). The same dead call placed AFTER `value = bf.initial` is HARMLESS in reality (120/120 OK), yet an impl reading fs.fresh_eval after bound_initial would fail verification for insufficient permission. So the permission pin is order-insensitive where reality is order-sensitive, i.e. the spec is strictly STRONGER than the repo on that axis. This is over-restriction of the impl space, not unsoundness: it can only reject behaviourally-correct impls, never admit a wrong one, so verify=>resolve is unharmed. It is also explicitly disclosed — mapping.md §2 spells out the very ordering dependency ('the cache captures the NEXT evaluation if the extra call happens before bf.initial is first read') and then conservatively forbids all reads. Documented conservatism, not drift.

OUT-OF-DOMAIN DIVERGENCES (each excluded by the bundle in writing, so not faithfulness breaks): (a) micro-supporting widget (TextInput/HiddenInput) -> cleaned keeps microseconds, model says normalise — conformance_check MODELED BRANCH names this exclusion explicitly and says it is 'deliberately excluded rather than silently avoided'; (b) USE_TZ=True -> clean attaches tzinfo so cleaned != bf.initial — mapping §3.2 and conformance setup pin USE_TZ=False, which is Django's own tests/test_sqlite.py setting; (c) DateField with a datetime source -> cleaned is a `date`, outside the model carrier — mapping §1/§2 bind the carrier to datetime/time and the clean step to DateTimeField.

UNDER-DISCLOSED BUT NOT DIVERGENT (worth a doc nit, not a defect): the modeled function's repo counterpart _clean_fields also (i) overrides cleaned_data[name] via the `clean_<name>` hook and (ii) omits the cleaned_data entry entirely when a validator raises ValidationError. I confirmed both against the real repo (clean_f hook shifts cleaned by +1 day; a rejecting validator leaves cleaned_data['f'] ABSENT while the model unconditionally returns a value). Neither is reachable in the F2P scenario, and refinement.md A4 anchors the modeled return at the pre-hook `self.cleaned_data[name] = value` line while mapping §3.2 scopes the clean-identity claim to 'the tested input' — so the modeled step legitimately ends before the hook/error paths. Flagging as scope narrowness the docs could state more explicitly, not as a modeled-function/real-callee disagreement.

CONCLUSION. No input inside the documented domain (disabled temporal field, non-micro widget, USE_TZ=False, datetime/time carrier) where the modeled function disagrees with the real callee, across ~220k adversarial inputs plus targeted boundary/ordering/subclass probes. The one place the spec exceeds the repo (order-insensitive permission pin) errs strictly toward rejecting impls and is disclosed. Verdict FAITHFUL; no diverging input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SPEC INTEGRITY: same-spec on a copy of the bundle model.py returns SAME (exit 0); recomputed spec_view sha256=5a01f182a17c9fdf86d5cd03dbcd1c4a89a5f8c36c84a078ac9de975f301dbfb, matching meta.json gates.G-LEAK harness state (region_hashes.spec_view in meta is a stale pre-edit value for pre/post/spec_view, but that is a G-HYGIENE bookkeeping matter, not leakage). spec_view is idempotent. Elision is real: the impl region collapses to '...  # implementation elided', so the consumer never sees 'value = bound_initial(fs); cleaned = value'.

MECHANICAL SCREEN: leakage.screen() on the nagini flavor returns passed=True, zero hard failures. Independently re-derived each rule rather than trusting the aggregate: (L1) no diff marker in the view; no gold changed line reproduced (normalized, len>=8) - zero hits. (L2) neither patched path 'django/forms/forms.py' nor 'django/forms/boundfield.py' nor any dotted module path appears; probed 26 repo-specific strings (_bound_items, _has_changed, get_initial_for_field, _field_data_value, _widget_data_value, cached_property, BoundField, _clean_fields, cleaned_data, disabled, FileField, microsecond, supports_microseconds, changed_data, full_clean, ticket ids 22502/32917) - ALL absent. (L3) narration scan over the full _NARRATION vocabulary (bug/fix/patch/regression/previously/incorrectly/wrong/broken...) finds NONE - notable since the docstring and precondition comments are prose-heavy and the known G-LEAK trap is measure/justification prose tripping 'fixed'/'copy'. (L5) no spec-view identifier embeds a patched symbol.

I checked the screen's problem_statement skip-list was not masking anything, symbol by symbol. Of the 8 changed symbols, only 'value' collides with a spec-view identifier and only 'data'/'value' appear in comments - both are generic English/PS-public words, and both are PS-public anyway. The four symbols NOT in the PS (field_data_value, widget_data_value, has_changed, full_clean) have zero identifier and zero comment hits, so no skip was load-bearing. Spec-view identifiers are all either Nagini builtins or neutral coinages (FieldState, first_eval, fresh_eval, normalise, bound_initial, clean_bound_initial_field) - none echoes a gold symbol.

SEMANTIC HALF (the part the lexer cannot see). The question is whether the two 'defining properties' of the bound initial reconstruct the edit beyond the PS. They do not:

(1) 'evaluated EXACTLY ONCE and cached' and (2) 'sub-second component dropped' are both properties of BoundField.initial at base_commit (boundfield.py:212-220, a @cached_property calling get_initial_for_field then data.replace(microsecond=0)). Confirmed by hunk arithmetic that the gold patch's boundfield.py hunks target lines 1-7, 119-125, 131-152 - BoundField.initial at 212-220 is UNTOUCHED, and the phrase 'standardized handling'/'nix the microseconds' appears nowhere in the gold patch, not even as context. So the spec view is describing pre-existing, unchanged, publicly readable source that the PS explicitly points the solver at ('form[name].initial'). Reading unchanged code is exactly what a solver is supposed to do.

(2) The PS is unusually explicit and already contains everything the spec view abstracts: it names _clean_fields, changed_data, BoundField, form[name].initial, 'disabled', 'callable', even the gold-introduced helper _bound_items and the bf.did_change/_bound_items code sketch verbatim. The spec view is strictly LESS specific than the PS - it never names a single Django symbol, file, or method, and states the goal in abstract behavioral terms ('the cleaned value MUST equal the value exposed as that field's bound initial'), which is a de-narrated restatement of the PS's own 'can return a different value from form[name].initial when they should be the same'.

HINTS-TEXT DISCIPLINE (the pilot's #1 leak, checked explicitly since leakage is judged against problem_statement ONLY): hints_text contains 'datetime.datetime.now' but NOT 'microseconds'. The spec view contains neither string. It also carries no hidden-test specifics: probed FakeTime, elapsed_seconds, 2006, 14/30/46, 123456, 'one second', test names, assertEqual - all absent. The stateful-callable framing in the docstring is generic ('a callable source may advance its own state on every call') and is anchored by the PS's own 'can return a different value ... when they should be the same' plus the PS-named public test test_datetime_clean_initial_callable_disabled; it does not reveal the hidden test's one-second-per-call fake clock or the microsecond-stripping assertion.

CLOSEST CALL, and why it still is not leakage: the no-permission-to-fresh_eval precondition comment is a strong nudge - it tells the solver that any extra evaluation of the source, even a dead one, is forbidden. But that is a statement of the required BEHAVIOR (idempotent single evaluation), not of the edit: it does not say which function to change, which call to delete, or that get_initial_for_field should be replaced by bf.initial. A solver could satisfy it by caching inside get_initial_for_field, by memoizing on the form, or by routing through BoundField - the spec does not pick. Note this comment is a G-EQ hardening artifact (it closes the atk_8 dead-read gap recorded in refinement.md A0b), and hardening against a partial-correctness gap is legitimate spec strengthening rather than gold disclosure. Same for MustTerminate(2), which is generic total-correctness boilerplate.

GOLD-RECONSTRUCTION TEST: from the spec view ALONE (no PS), a solver learns only that some abstract field-cleaning step must return normalise(first_eval) over an int encoding. There is no way to locate BaseForm._clean_fields, discover the disabled branch, or derive the _bound_items/_has_changed refactor. All of the localization power in this task comes from the PS, which is public. The refactor hunks (_bound_items, BoundField._has_changed, _field_data_value removal, changed_data one-liner) are entirely unmodelled and entirely unhinted in the view.

Caveat on scope: meta.json also ships modeled_functions to the consumer in spec modes, and its repo_location/repo_symbol fields DO name 'django/forms/forms.py:389' and 'BaseForm._clean_fields (disabled-field value branch)'. That is outside the spec view this gate judges, is by-design localization for modes 1/2 (mirrored by eval_localization for non-spec modes so info-env parity holds), and the PS already names _clean_fields - so it is not a spec-view leak. Flagging it only for completeness.

VERDICT: NO-LEAKAGE. Mechanical screen clean on every rule, no skip masking a real hit, and the semantic content of the view is a faithful abstraction of behavior that is already public in the problem_statement and in unchanged base_commit source. No relaxation needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
