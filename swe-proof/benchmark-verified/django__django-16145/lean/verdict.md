# P2 adversarial audit — django__django-16145

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,8 +45,6 @@
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
   if rawIpv6 then
     return "[" ++ addr ++ "]"
-  else if addr = "0" then
-    return "0.0.0.0"
   else
     return addr
 -- impl-end
@@ -56,16 +54,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,10 +45,8 @@
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
   if rawIpv6 then
     return "[" ++ addr ++ "]"
-  else if addr = "0" then
+  else
     return "0.0.0.0"
-  else
-    return addr
 -- impl-end
 
 -- proof-start
@@ -56,16 +54,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
   if rawIpv6 then
     return "[" ++ addr ++ "]"
-  else if addr = "0" then
+  else if addr = "0.0.0.0" then
     return "0.0.0.0"
   else
     return addr
@@ -56,16 +56,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,10 +43,10 @@
 
 -- impl-start
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
-  if rawIpv6 then
+  if addr = "0" then
+    return "0.0.0.0"
+  else if rawIpv6 then
     return "[" ++ addr ++ "]"
-  else if addr = "0" then
-    return "0.0.0.0"
   else
     return addr
 -- impl-end
@@ -56,16 +56,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,12 +43,7 @@
 
 -- impl-start
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
-  if rawIpv6 then
-    return "[" ++ addr ++ "]"
-  else if addr = "0" then
-    return "0.0.0.0"
-  else
-    return addr
+  return addr
 -- impl-end
 
 -- proof-start
@@ -56,16 +51,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
 -- impl-start
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
   if rawIpv6 then
-    return "[" ++ addr ++ "]"
+    return "[" ++ addr
   else if addr = "0" then
     return "0.0.0.0"
   else
@@ -56,16 +56,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,12 +43,7 @@
 
 -- impl-start
 def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
-  if rawIpv6 then
-    return "[" ++ addr ++ "]"
-  else if addr = "0" then
-    return "0.0.0.0"
-  else
-    return addr
+  return "0.0.0.0"
 -- impl-end
 
 -- proof-start
@@ -56,16 +51,6 @@
     problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
   intro rawIpv6 addr
   unfold problem_spec_displayAddr implementation_displayAddr
-  refine ⟨?_, ?_, ?_⟩
-  · intro h
-    subst h
-    rfl
-  · intro h haddr
-    subst h
-    subst haddr
-    rfl
-  · intro h haddr
-    subst h
-    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
-    rfl
+  refine ⟨?_, ?_, ?_⟩ <;> intros <;>
+    simp_all [Id.run, Bool.false_eq_true] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Presenting a development server's bind host in its start-up banner URL.

When a lightweight development server announces the address it is listening on,
it must render the bind host as a piece of a clickable `protocol://host:port/`
URL. Two presentation rules apply to the host component:

  * a raw IPv6 literal must be wrapped in square brackets, so that it composes
    into a valid URL authority (`[host]`);
  * the unspecified-address shorthand `"0"` — which denotes binding on every
    available interface — must be shown in its canonical dotted form
    `"0.0.0.0"`, the form a web browser will actually follow.

Every other host is presented verbatim. The bracket rule takes precedence: a raw
IPv6 literal is always bracketed regardless of its textual content.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the displayed
-- host is a closed expression over the resolved bind host and the raw-IPv6 flag,
-- using only string equality, concatenation, and two literals. No `opaque`/
-- `axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed.)
-- pure-end

-- post-conditions-start
/-- The displayed host is pinned for every combination of inputs (directive 5:
no case is left unconstrained). `rawIpv6` records whether the resolved host is a
raw IPv6 literal; `addr` is the resolved bind host. A raw IPv6 literal is
bracketed; otherwise the shorthand `"0"` becomes `"0.0.0.0"` and any other host
is shown unchanged. -/
def problem_spec_displayAddr (rawIpv6 : Bool) (addr : String) (result : String) : Prop :=
  (rawIpv6 = true → result = "[" ++ addr ++ "]") ∧
  (rawIpv6 = false → addr = "0" → result = "0.0.0.0") ∧
  (rawIpv6 = false → addr ≠ "0" → result = addr)
-- post-conditions-end

-- impl-start
def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
  if rawIpv6 then
    return "[" ++ addr ++ "]"
  else if addr = "0" then
    return "0.0.0.0"
  else
    return addr
-- impl-end

-- proof-start
theorem correct_displayAddr : ∀ (rawIpv6 : Bool) (addr : String),
    problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
  intro rawIpv6 addr
  unfold problem_spec_displayAddr implementation_displayAddr
  refine ⟨?_, ?_, ?_⟩
  · intro h
    subst h
    rfl
  · intro h haddr
    subst h
    subst haddr
    rfl
  · intro h haddr
    subst h
    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-16145. Spec problem_spec_displayAddr pins `result` UNIQUELY across three JOINTLY-EXHAUSTIVE cases: (rawIpv6=true → result='['++addr++']') ∧ (rawIpv6=false → addr='0' → result='0.0.0.0') ∧ (rawIpv6=false → addr≠'0' → result=addr). There is no slack — any spec-satisfying impl is pointwise-equal to the gold impl on the modeled displayAddr function, so no closing-but-non-resolving impl can exist. Because no wrong impl closes, there are no clean-axiom-closing patches to materialize/resolve (the resolve step is vacuously satisfied).

PROTOCOL. Confirmed same_spec=True for the positive control and all 7 attacks against Solution.lean. Verifications run concurrently in two background batches of ≤4 via `bash scripts/lean_verify.sh <file>`.

Positive control (pos_control.lean = byte copy of Solution.lean): exit 0 (verifies, no sorry). `#print axioms correct_displayAddr` → depends on axioms: [propext] only (clean; no sorryAx, no custom axiom) — verified via pos_axioms.lean, exit 0.

Attacks (all same_spec=True, spec/axioms/pre/post byte-identical; only impl+proof edited; each given a generous generic proof `refine ⟨?_,?_,?_⟩ <;> intros <;> simp_all [Id.run,Bool.false_eq_true] <;> rfl`):
- atk_1 (prepatch bug: drop addr='0' branch, return addr verbatim) → exit 1. Fails 2nd conjunct: ⊢ pure '0' = '0.0.0.0'. This reproduces the base_commit behavior (prepatch_reproduced=true).
- atk_2 (over-eager: always '0.0.0.0' when not ipv6) → exit 1. Fails 3rd conjunct: ⊢ pure '0.0.0.0' = addr for arbitrary addr≠'0'.
- atk_3 (wrong trigger: match addr='0.0.0.0' instead of '0') → exit 1. Fails 2nd conjunct on addr='0'.
- atk_4 (control-flow-effect: reorder addr='0' branch before ipv6 → breaks bracket precedence on (true,'0')) → exit 1. Fails 1st conjunct: (if addr='0' then '0.0.0.0' else '['++addr++']') = '['++addr++']'.
- atk_5 (ungrounded-oracle echo: return addr unconditionally) → exit 1. rfl fails: pure addr = '['++addr++']' and pure '0' = '0.0.0.0'.
- atk_6 (partial/wrong concat: bracket missing closing ']') → exit 1. Fails 1st conjunct: pure ('['++addr) = '['++addr++']'.
- atk_7 (constant oracle: always '0.0.0.0') → exit 1. rfl fails: pure '0.0.0.0' = '['++addr++']' and = addr.

Commands (representative): `bash scripts/lean_verify.sh atk_N.lean`. Exit codes: pos_control=0, atk_1..atk_7 all =1 (genuine `rfl`/unsolved-goals errors, NOT timeouts, NOT linter-only). No attack produced a closing proof ⇒ no faithful patch materialization/resolve required (patches={}).

REFINEMENT.MD / A-LEG AUDIT: meta.json shows axioms=[], deep_model_references=[], conf_skip=false, modeled_functions=[displayAddr]. All 6 refinement legs are tagged R (args #1,#2,#6) or I (branch ops #3,#4,#5) — no A-consumed, no A-reference, NO kind-3 leg. axiom_check.py is a documented skip stub (no callee axioms), so the A-leg correspondence obligation is vacuous. R/I legs are covered by G-CONF (conformance_check.py: boundary cross-product incl. the discriminator rawIpv6=False,addr='0' + 120k fuzz, oracle==shadow branch-for-branch). Correspondence to the real callee holds: the gold patch (from dataset) is exactly if self._raw_ipv6: addr=f'[{self.addr}]' / elif self.addr=='0': addr='0.0.0.0' / else: addr=self.addr, which the Lean impl transliterates 1:1 with the same branch precedence. FAIL_TO_PASS test_zero_ip_addr exercises exactly the discriminating (rawIpv6=False, addr='0')→'0.0.0.0' case.

CONCLUSION: total, uniquely-pinning, faithful, non-A spec; 7 distinct wrong impls (prepatch, boundary, wrong-trigger, control-flow-effect, ungrounded echo, partial concat, constant) all FAIL to close. verify⇒correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Presenting a development server's bind host in its start-up banner URL.

When a lightweight development server announces the address it is listening on,
it must render the bind host as a piece of a clickable `protocol://host:port/`
URL. Two presentation rules apply to the host component:

  * a raw IPv6 literal must be wrapped in square brackets, so that it composes
    into a valid URL authority (`[host]`);
  * the unspecified-address shorthand `"0"` — which denotes binding on every
    available interface — must be shown in its canonical dotted form
    `"0.0.0.0"`, the form a web browser will actually follow.

Every other host is presented verbatim. The bracket rule takes precedence: a raw
IPv6 literal is always bracketed regardless of its textual content.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification: the displayed
-- host is a closed expression over the resolved bind host and the raw-IPv6 flag,
-- using only string equality, concatenation, and two literals. No `opaque`/
-- `axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed.)
-- pure-end

-- post-conditions-start
/-- The displayed host is pinned for every combination of inputs (directive 5:
no case is left unconstrained). `rawIpv6` records whether the resolved host is a
raw IPv6 literal; `addr` is the resolved bind host. A raw IPv6 literal is
bracketed; otherwise the shorthand `"0"` becomes `"0.0.0.0"` and any other host
is shown unchanged. -/
def problem_spec_displayAddr (rawIpv6 : Bool) (addr : String) (result : String) : Prop :=
  (rawIpv6 = true → result = "[" ++ addr ++ "]") ∧
  (rawIpv6 = false → addr = "0" → result = "0.0.0.0") ∧
  (rawIpv6 = false → addr ≠ "0" → result = addr)
-- post-conditions-end

-- impl-start
def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do
  if rawIpv6 then
    return "[" ++ addr ++ "]"
  else if addr = "0" then
    return "0.0.0.0"
  else
    return addr
-- impl-end

-- proof-start
theorem correct_displayAddr : ∀ (rawIpv6 : Bool) (addr : String),
    problem_spec_displayAddr rawIpv6 addr (implementation_displayAddr rawIpv6 addr) := by
  intro rawIpv6 addr
  unfold problem_spec_displayAddr implementation_displayAddr
  refine ⟨?_, ?_, ?_⟩
  · intro h
    subst h
    rfl
  · intro h haddr
    subst h
    subst haddr
    rfl
  · intro h haddr
    subst h
    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-16145. Spec problem_spec_displayAddr pins `result` UNIQUELY across three JOINTLY-EXHAUSTIVE cases: (rawIpv6=true → result='['++addr++']') ∧ (rawIpv6=false → addr='0' → result='0.0.0.0') ∧ (rawIpv6=false → addr≠'0' → result=addr). There is no slack — any spec-satisfying impl is pointwise-equal to the gold impl on the modeled displayAddr function, so no closing-but-non-resolving impl can exist. Because no wrong impl closes, there are no clean-axiom-closing patches to materialize/resolve (the resolve step is vacuously satisfied).

PROTOCOL. Confirmed same_spec=True for the positive control and all 7 attacks against Solution.lean. Verifications run concurrently in two background batches of ≤4 via `bash scripts/lean_verify.sh <file>`.

Positive control (pos_control.lean = byte copy of Solution.lean): exit 0 (verifies, no sorry). `#print axioms correct_displayAddr` → depends on axioms: [propext] only (clean; no sorryAx, no custom axiom) — verified via pos_axioms.lean, exit 0.

Attacks (all same_spec=True, spec/axioms/pre/post byte-identical; only impl+proof edited; each given a generous generic proof `refine ⟨?_,?_,?_⟩ <;> intros <;> simp_all [Id.run,Bool.false_eq_true] <;> rfl`):
- atk_1 (prepatch bug: drop addr='0' branch, return addr verbatim) → exit 1. Fails 2nd conjunct: ⊢ pure '0' = '0.0.0.0'. This reproduces the base_commit behavior (prepatch_reproduced=true).
- atk_2 (over-eager: always '0.0.0.0' when not ipv6) → exit 1. Fails 3rd conjunct: ⊢ pure '0.0.0.0' = addr for arbitrary addr≠'0'.
- atk_3 (wrong trigger: match addr='0.0.0.0' instead of '0') → exit 1. Fails 2nd conjunct on addr='0'.
- atk_4 (control-flow-effect: reorder addr='0' branch before ipv6 → breaks bracket precedence on (true,'0')) → exit 1. Fails 1st conjunct: (if addr='0' then '0.0.0.0' else '['++addr++']') = '['++addr++']'.
- atk_5 (ungrounded-oracle echo: return addr unconditionally) → exit 1. rfl fails: pure addr = '['++addr++']' and pure '0' = '0.0.0.0'.
- atk_6 (partial/wrong concat: bracket missing closing ']') → exit 1. Fails 1st conjunct: pure ('['++addr) = '['++addr++']'.
- atk_7 (constant oracle: always '0.0.0.0') → exit 1. rfl fails: pure '0.0.0.0' = '['++addr++']' and = addr.

Commands (representative): `bash scripts/lean_verify.sh atk_N.lean`. Exit codes: pos_control=0, atk_1..atk_7 all =1 (genuine `rfl`/unsolved-goals errors, NOT timeouts, NOT linter-only). No attack produced a closing proof ⇒ no faithful patch materialization/resolve required (patches={}).

REFINEMENT.MD / A-LEG AUDIT: meta.json shows axioms=[], deep_model_references=[], conf_skip=false, modeled_functions=[displayAddr]. All 6 refinement legs are tagged R (args #1,#2,#6) or I (branch ops #3,#4,#5) — no A-consumed, no A-reference, NO kind-3 leg. axiom_check.py is a documented skip stub (no callee axioms), so the A-leg correspondence obligation is vacuous. R/I legs are covered by G-CONF (conformance_check.py: boundary cross-product incl. the discriminator rawIpv6=False,addr='0' + 120k fuzz, oracle==shadow branch-for-branch). Correspondence to the real callee holds: the gold patch (from dataset) is exactly if self._raw_ipv6: addr=f'[{self.addr}]' / elif self.addr=='0': addr='0.0.0.0' / else: addr=self.addr, which the Lean impl transliterates 1:1 with the same branch precedence. FAIL_TO_PASS test_zero_ip_addr exercises exactly the discriminating (rawIpv6=False, addr='0')→'0.0.0.0' case.

CONCLUSION: total, uniquely-pinning, faithful, non-A spec; 7 distinct wrong impls (prepatch, boundary, wrong-trigger, control-flow-effect, ungrounded echo, partial concat, constant) all FAIL to close. verify⇒correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16145 (lean). Modeled function: displayAddr, the banner display-host computation added by patch.diff in Command.inner_run.

Verification performed:
1. Solution.lean compiles via scripts/lean_verify.sh (exit 0, no sorry).
2. #print axioms correct_displayAddr => [propext] only. No sorryAx; proof is genuine.
3. markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) == True: the spec region (post-conditions/axioms/pure) is byte-identical between the patched and prepatch bundles, so the spec was not tailored to either impl.

Spec vs real repo (post-patch code):
  if self._raw_ipv6:      addr = f"[{self.addr}]"
  elif self.addr == "0":  addr = "0.0.0.0"
  else:                   addr = self.addr
problem_spec_displayAddr:
  (rawIpv6=true  -> result = "[" ++ addr ++ "]")   <-> f-string bracket-wrap (identity concat)
  (rawIpv6=false -> addr="0"  -> result = "0.0.0.0") <-> elif literal
  (rawIpv6=false -> addr!="0" -> result = addr)      <-> else verbatim

The spec is TOTAL over (Bool, String) and agrees with the real callee on every input, with correct branch precedence (rawIpv6=true, addr="0" -> "[0]" in both spec and real code, since the raw-IPv6 branch dominates). Bijection is identity-level (value-level String equality + concatenation + literals; Bool identity), so no drift is introducible via character-sequence or normalization mismatch. Searched boundary/precedence inputs ({"0","", "::1", "0.0.0.0", arbitrary hosts} x {true,false}) — no input where the modeled function disagrees with the real repo behavior. The spec is neither too strong (does not over-constrain beyond the three real branches) nor drifting. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage screen over the spec view (Solution.lean docstring + problem_spec_displayAddr). The gold patch introduces exactly one new behavior: elif self.addr == "0": addr = "0.0.0.0" (rewrite the shorthand bind host "0" to "0.0.0.0" in the start-up banner). This entire behavioral content is fully disclosed by the PUBLIC problem_statement (verified: both '0.0.0.0' and '0:8000' appear in problem_statement, not merely hints_text): 'Output should be Starting development server at http://0.0.0.0:8000/ when providing 0:8000'. The spec docstring's other rule (raw IPv6 literal -> bracket-wrap [host]) is pre-existing base_commit behavior ('[%s]' % self.addr if self._raw_ipv6), publicly observable and NOT the gold edit. The 'else -> verbatim' rule is likewise pre-existing. No spec-view line exposes hidden gold detail beyond the public statement: no FAIL_TO_PASS test internals, no internal repo structure, no gold-only implementation specifics. The generalization from the example host '0' to the predicate addr = "0" is exactly the fix the public issue requests. Verdict: NO-LEAKAGE. (Consistent with recorded G-LEAK lexical pass and the bundle's own Role-4 finding.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
