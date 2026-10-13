# P2 adversarial audit — psf__requests-5414

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec verifying wrong impl exists whose faithful refined patch fails to resolve. The postcondition `ensures out = hostAccepted host` fully pins the return value on the ENTIRE required domain (non-empty, all-ASCII hosts). Any impl that verifies must compute exactly `hostAccepted host = !(head? == some '*' || head? == some '.')`. Two independent divergence probes (atk_5 while-true, atk_9 non-terminating recursion) FAILED to verify — Velvet's partial-correctness semantics still emit the postcondition obligation on the returned value along the surviving path, so partial-correctness vacuity is closed here. The one attack that verified (atk_6) is a semantically-correct echo whose faithful patch IS the gold patch and RESOLVES.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,9 +71,8 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
+    -- ATTACK 1 (prepatch bug): reject ONLY '*', never '.'. Pre-patch guard.
+    let startsBad : Bool := host.head? == some '*'
     return !startsBad
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,9 +71,8 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
+    -- ATTACK 2 (boundary): reject ONLY '.', dropping the '*' disjunct.
+    let startsBad : Bool := host.head? == some '.'
     return !startsBad
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,10 +71,8 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
-    return !startsBad
+    -- ATTACK 3 (ungrounded accept-all): always accept.
+    return true
     -- impl-end
 
 prove_correct validateAsciiHostLabel by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,10 +71,8 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
-    return !startsBad
+    -- ATTACK 4 (ungrounded reject-all): always reject.
+    return false
     -- impl-end
 
 prove_correct validateAsciiHostLabel by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,10 +71,14 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
-    return !startsBad
+    -- ATTACK 5 (control-flow-effect / divergence): loop forever, then return a
+    -- WRONG accept-all. Under partial correctness a divergent path vacuously
+    -- satisfies any postcondition. If loom_solve accepts this, the spec admits a
+    -- non-terminating impl whose faithful patch would hang (not resolve).
+    let mut b : Bool := true
+    while b do
+      b := true
+    return true
     -- impl-end
 
 prove_correct validateAsciiHostLabel by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,10 +71,10 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
-    return !startsBad
+    -- ATTACK 6 (ungrounded-oracle echo): compute the SAME decision via a
+    -- different-but-equal expression (swapped disjuncts, negation pushed in).
+    let bad : Bool := host.head? == some '.' || host.head? == some '*'
+    return (if bad then false else true)
     -- impl-end
 
 prove_correct validateAsciiHostLabel by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,10 +71,10 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
-    return !startsBad
+    -- ATTACK 7 (echo via structural match on the leading code point).
+    match host with
+    | []      => return true
+    | c :: _  => return !(c == '*' || c == '.')
     -- impl-end
 
 prove_correct validateAsciiHostLabel by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,9 +71,8 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
+    -- ATTACK 8 (over-rejection): also reject a leading ':' (not in gold set).
+    let startsBad : Bool := host.head? == some '*' || host.head? == some '.' || host.head? == some ':'
     return !startsBad
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No axiomatized callees. The acceptance decision is a pure property of the
@@ -71,10 +71,12 @@
   ensures out = hostAccepted host
   do
     -- impl-start
-    -- Reject iff the host opens with an invalid leading label, i.e. its first
-    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
-    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
-    return !startsBad
+    -- ATTACK 9 (divergence via recursive spin): decrement-free recursion that
+    -- never terminates, then a WRONG accept-all. Partial-correctness vacuity
+    -- probe distinct from atk_5's while-loop.
+    let rec spin (n : Nat) : Bool := spin (n + 1)
+    let _ := spin 0
+    return true
     -- impl-end
 
 prove_correct validateAsciiHostLabel by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The acceptance decision is a pure property of the
--  candidate host's leading code point, modeled deeply in the `pure` region.
--  The all-ASCII screen `isAsciiHost` is a deep model of the unchanged
--  community predicate that selects this code path; it is validated against
--  that real predicate by axiom_check.py (G-AX) as an A-reference, NOT a
--  consumed axiom — it appears only in a `require` to scope the decision to the
--  all-ASCII case, and the proof never relies on its internal structure.)
-- axioms-end

-- pure-start
/- Whether every code point of the host is in the 7-bit ASCII range
   (code point < 128). Front-recursive so a single unfold is available per
   element (the Velvet fold pattern). This selects the all-ASCII handling path
   for a host string. -/
def isAsciiHost : List Char → Bool
  | []      => true
  | c :: cs => decide (c.toNat < 128) && isAsciiHost cs

@[grind] lemma isAsciiHost_nil : isAsciiHost [] = true := rfl
@[grind] lemma isAsciiHost_cons (c : Char) (cs : List Char) :
    isAsciiHost (c :: cs) = (decide (c.toNat < 128) && isAsciiHost cs) := rfl

/- The host carries an invalid leading label exactly when its first code point
   is the wildcard `*` (U+002A) or the label-separator `.` (U+002E). A label is
   the dot-delimited segment of a host; a host that opens with either of these
   code points has an empty or wildcard first label, which is not a valid host
   label. Decided purely from the head of the code-point sequence. -/
def startsWithInvalidLabel (host : List Char) : Bool :=
  host.head? == some '*' || host.head? == some '.'

/- An all-ASCII host is accepted exactly when it does NOT open with an invalid
   leading label; otherwise it is rejected. Expressed structurally over the
   input's leading code point. -/
def hostAccepted (host : List Char) : Bool :=
  !startsWithInvalidLabel host

@[grind] lemma hostAccepted_def (host : List Char) :
    hostAccepted host = !(host.head? == some '*' || host.head? == some '.') := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The leading-label acceptance decision for a host that is being handled along
   the all-ASCII path, modeled over its code-point sequence: accept (return
   `true`) iff the host does not open with an invalid leading label — i.e. its
   first code point is neither the wildcard `*` nor the separator `.`; otherwise
   reject (return `false`). A reject corresponds to signalling an invalid-URL
   condition at this point.

   `host` is read-only (not `mut`); the decision computes a single boolean and
   mutates nothing (directive 5). The host reaching this decision is non-empty
   (`require host.length > 0`) and entirely ASCII (`require isAsciiHost host`):
   these scope the decision to exactly the path this branch governs. Input is a
   code-point sequence (`List Char`); the result is a `Bool`. -/
method validateAsciiHostLabel (host : List Char) return (out : Bool)
  require host.length > 0
  require isAsciiHost host = true
  ensures out = hostAccepted host
  do
    -- impl-start
    -- Reject iff the host opens with an invalid leading label, i.e. its first
    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
    return !startsBad
    -- impl-end

prove_correct validateAsciiHostLabel by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Project root here; used python and scripts/lean_verify.sh, scripts + harness confirmed. same_spec=True verified for ALL 9 attacks + pos_control (velvet backend). Verifications run concurrently in batches of 4 as required.

A-LEG / DEEP-MODEL FOCUS (my assigned emphasis): axioms region is EMPTY (no consumed axioms). The single kind-A obligation is the A-REFERENCE `isAsciiHost` (deep model of the UNCHANGED branch-selector `requests._internal_utils.unicode_is_ascii`, used only in a `require` to scope the decision to the all-ASCII path; proof never unfolds it). I re-ran axiom_check.py against the REAL callee imported from the base_commit worktree: G-AX OK, exit 0, sound on 25 boundary + 20000 fuzz inputs (seed 5414). unicode_is_ascii source at base_commit matches the mapping.md transliteration exactly (encode('ascii') success == all code points < 128). The A-reference correspondence HOLDS.

REFINEMENT.MD AUDIT: legs A1(R), A2(R), A3(A-reference), A4(R+I), A5(R) — no kind-3 (unexpressible-changed-op) hand-wave. The genuinely changed op (adding `u'.'` to the reject set) is modeled DEEPLY and exactly via `host.head? == some '.'`, not axiomatized. The A-reference (A3) models the unchanged selector, not the changed op — correspondence validated by G-AX above.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 (PREPATCH BUG, reject only '*'): exit 1 — FAILS. Goal `(!host.head? == some '*') = hostAccepted host` unprovable on '.'-leading host. PREPATCH REPRODUCED (byte-identical logic to shipped Solution_prepatch.lean).
- atk_2 (boundary, reject only '.'): exit 1 — FAILS (P2P '*' case).
- atk_3 (ungrounded accept-all `return true`): exit 1 — FAILS.
- atk_4 (ungrounded reject-all `return false`): exit 1 — FAILS.
- atk_5 (control-flow-effect / while-true divergence + wrong accept-all): exit 1 — FAILS. Partial-correctness did NOT grant vacuity; goal `true = hostAccepted host` emitted on loop-exit path.
- atk_6 (ungrounded-oracle ECHO, swapped disjuncts + if/then): exit 0 — VERIFIES. Semantically == hostAccepted.
- atk_7 (echo via structural match on head): exit 1 — FAILS (loom_solve did not bridge the `c==` match form to `head?`; behaviorally correct but not machine-verified, so not a live attack).
- atk_8 (over-rejection, extra ':' needle): exit 1 — FAILS on ':'-leading ASCII host.
- atk_9 (divergence via non-terminating recursion + wrong accept-all): exit 1 — FAILS. Vacuity again closed.
- pos_control (gold impl): exit 0 — VERIFIES.

### RESOLVE RESULTS (protocol step 2 — EVERY verifying attack's faithful patch run through the official harness):
- atk_6.lean is the ONLY verifying wrong impl. Its faithful refined patch (materialized at atk_6.patch; identical to gold `elif host.startswith((u'*', u'.'))`) was run via run_resolve('psf__requests-5414', patch): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. Patch RESOLVES → does NOT break the spec.

VERDICT: SOUND. 9 distinct same-spec attacks encoded and machine-verified (partial-domain, boundary, control-flow-effect/divergence x2, ungrounded accept/reject, over-rejection, echo). Only the correct echo verifies, and its materialized faithful patch resolves under the official harness. No verify⇏correct witness exists. A-reference and refinement legs audited and hold.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec verifying wrong impl exists whose faithful refined patch fails to resolve. The postcondition `ensures out = hostAccepted host` fully pins the return value on the ENTIRE required domain (non-empty, all-ASCII hosts). Any impl that verifies must compute exactly `hostAccepted host = !(head? == some '*' || head? == some '.')`. Two independent divergence probes (atk_5 while-true, atk_9 non-terminating recursion) FAILED to verify — Velvet's partial-correctness semantics still emit the postcondition obligation on the returned value along the surviving path, so partial-correctness vacuity is closed here. The one attack that verified (atk_6) is a semantically-correct echo whose faithful patch IS the gold patch and RESOLVES.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The acceptance decision is a pure property of the
--  candidate host's leading code point, modeled deeply in the `pure` region.
--  The all-ASCII screen `isAsciiHost` is a deep model of the unchanged
--  community predicate that selects this code path; it is validated against
--  that real predicate by axiom_check.py (G-AX) as an A-reference, NOT a
--  consumed axiom — it appears only in a `require` to scope the decision to the
--  all-ASCII case, and the proof never relies on its internal structure.)
-- axioms-end

-- pure-start
/- Whether every code point of the host is in the 7-bit ASCII range
   (code point < 128). Front-recursive so a single unfold is available per
   element (the Velvet fold pattern). This selects the all-ASCII handling path
   for a host string. -/
def isAsciiHost : List Char → Bool
  | []      => true
  | c :: cs => decide (c.toNat < 128) && isAsciiHost cs

@[grind] lemma isAsciiHost_nil : isAsciiHost [] = true := rfl
@[grind] lemma isAsciiHost_cons (c : Char) (cs : List Char) :
    isAsciiHost (c :: cs) = (decide (c.toNat < 128) && isAsciiHost cs) := rfl

/- The host carries an invalid leading label exactly when its first code point
   is the wildcard `*` (U+002A) or the label-separator `.` (U+002E). A label is
   the dot-delimited segment of a host; a host that opens with either of these
   code points has an empty or wildcard first label, which is not a valid host
   label. Decided purely from the head of the code-point sequence. -/
def startsWithInvalidLabel (host : List Char) : Bool :=
  host.head? == some '*' || host.head? == some '.'

/- An all-ASCII host is accepted exactly when it does NOT open with an invalid
   leading label; otherwise it is rejected. Expressed structurally over the
   input's leading code point. -/
def hostAccepted (host : List Char) : Bool :=
  !startsWithInvalidLabel host

@[grind] lemma hostAccepted_def (host : List Char) :
    hostAccepted host = !(host.head? == some '*' || host.head? == some '.') := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The leading-label acceptance decision for a host that is being handled along
   the all-ASCII path, modeled over its code-point sequence: accept (return
   `true`) iff the host does not open with an invalid leading label — i.e. its
   first code point is neither the wildcard `*` nor the separator `.`; otherwise
   reject (return `false`). A reject corresponds to signalling an invalid-URL
   condition at this point.

   `host` is read-only (not `mut`); the decision computes a single boolean and
   mutates nothing (directive 5). The host reaching this decision is non-empty
   (`require host.length > 0`) and entirely ASCII (`require isAsciiHost host`):
   these scope the decision to exactly the path this branch governs. Input is a
   code-point sequence (`List Char`); the result is a `Bool`. -/
method validateAsciiHostLabel (host : List Char) return (out : Bool)
  require host.length > 0
  require isAsciiHost host = true
  ensures out = hostAccepted host
  do
    -- impl-start
    -- Reject iff the host opens with an invalid leading label, i.e. its first
    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
    return !startsBad
    -- impl-end

prove_correct validateAsciiHostLabel by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. Project root here; used python and scripts/lean_verify.sh, scripts + harness confirmed. same_spec=True verified for ALL 9 attacks + pos_control (velvet backend). Verifications run concurrently in batches of 4 as required.

A-LEG / DEEP-MODEL FOCUS (my assigned emphasis): axioms region is EMPTY (no consumed axioms). The single kind-A obligation is the A-REFERENCE `isAsciiHost` (deep model of the UNCHANGED branch-selector `requests._internal_utils.unicode_is_ascii`, used only in a `require` to scope the decision to the all-ASCII path; proof never unfolds it). I re-ran axiom_check.py against the REAL callee imported from the base_commit worktree: G-AX OK, exit 0, sound on 25 boundary + 20000 fuzz inputs (seed 5414). unicode_is_ascii source at base_commit matches the mapping.md transliteration exactly (encode('ascii') success == all code points < 128). The A-reference correspondence HOLDS.

REFINEMENT.MD AUDIT: legs A1(R), A2(R), A3(A-reference), A4(R+I), A5(R) — no kind-3 (unexpressible-changed-op) hand-wave. The genuinely changed op (adding `u'.'` to the reject set) is modeled DEEPLY and exactly via `host.head? == some '.'`, not axiomatized. The A-reference (A3) models the unchanged selector, not the changed op — correspondence validated by G-AX above.

### VERIFY RESULTS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 (PREPATCH BUG, reject only '*'): exit 1 — FAILS. Goal `(!host.head? == some '*') = hostAccepted host` unprovable on '.'-leading host. PREPATCH REPRODUCED (byte-identical logic to shipped Solution_prepatch.lean).
- atk_2 (boundary, reject only '.'): exit 1 — FAILS (P2P '*' case).
- atk_3 (ungrounded accept-all `return true`): exit 1 — FAILS.
- atk_4 (ungrounded reject-all `return false`): exit 1 — FAILS.
- atk_5 (control-flow-effect / while-true divergence + wrong accept-all): exit 1 — FAILS. Partial-correctness did NOT grant vacuity; goal `true = hostAccepted host` emitted on loop-exit path.
- atk_6 (ungrounded-oracle ECHO, swapped disjuncts + if/then): exit 0 — VERIFIES. Semantically == hostAccepted.
- atk_7 (echo via structural match on head): exit 1 — FAILS (loom_solve did not bridge the `c==` match form to `head?`; behaviorally correct but not machine-verified, so not a live attack).
- atk_8 (over-rejection, extra ':' needle): exit 1 — FAILS on ':'-leading ASCII host.
- atk_9 (divergence via non-terminating recursion + wrong accept-all): exit 1 — FAILS. Vacuity again closed.
- pos_control (gold impl): exit 0 — VERIFIES.

### RESOLVE RESULTS (protocol step 2 — EVERY verifying attack's faithful patch run through the official harness):
- atk_6.lean is the ONLY verifying wrong impl. Its faithful refined patch (materialized at atk_6.patch; identical to gold `elif host.startswith((u'*', u'.'))`) was run via run_resolve('psf__requests-5414', patch): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. Patch RESOLVES → does NOT break the spec.

VERDICT: SOUND. 9 distinct same-spec attacks encoded and machine-verified (partial-domain, boundary, control-flow-effect/divergence x2, ungrounded accept/reject, over-rejection, echo). Only the correct echo verifies, and its materialized faithful patch resolves under the official harness. No verify⇏correct witness exists. A-reference and refinement legs audited and hold.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) audit for psf__requests-5414 velvet. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language)=True; Solution.lean verifies via lean_verify.sh (exit 0). (2) Modeled function validateAsciiHostLabel returns out=hostAccepted host = !(head?==some '*' || head?==some '.'), scoped by require host.length>0 and require isAsciiHost host. (3) Domain scoping faithful to real repo prepare_url (requests/models.py:394-407 @ base 39d0fdd9): length>0 == passed `if not host`; isAsciiHost host == reaching the `elif` only when unicode_is_ascii(host) is True. isAsciiHost validated == real unicode_is_ascii over 50k random unicode inputs + boundary chars (chr(127)/chr(128)/chr(200)): 0 mismatches. (4) Decision fidelity: compared model accept/reject vs real post-patch guard host.startswith((u'*', u'.')) (reject) else accept, over 200,020 in-domain (non-empty, all-ASCII) random inputs seeded 5414 PLUS targeted boundaries ('*','.', '.example.com','*example.com','..','.*','*.', control chars, chr(0), chr(127)): 0 mismatches. For single-char prefixes startswith equals head test, so the tuple form is exactly head in {'*','.'}. The spec agrees with the real callee on every input in the modeled domain and the domain matches exactly the branch the patch governs (non-ASCII takes the unchanged IDNA branch, correctly out of scope). No diverging input exists; the spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `host.startswith(u'*')` -> `host.startswith((u'*', u'.'))` at requests/models.py:406, i.e. additionally reject a host whose first character is '.'.

Public problem_statement already discloses the entire discriminating content of the gold edit: title 'Getting http://.example.com raises UnicodeError', reproduction `requests.get("http://.example.com")`, expected result `InvalidUrl: URL has an invalid label.`, and a direct link to requests/models.py#L401 (the exact guard region). So the public issue itself specifies: a host beginning with '.' must be rejected as an invalid-label URL, at that exact code location.

Spec view (impl-start..impl-end and the prove_correct body are elided by markers.spec_view) exposes:
  - startsWithInvalidLabel host := host.head? == some '*' || host.head? == some '.'
  - hostAccepted host := !startsWithInvalidLabel host
  - ensures out = hostAccepted host
The '.' disjunct = exactly the publicly-demanded behavior (reject '.'-leading host). The '*' disjunct is PRE-EXISTING repo behavior (pre-patch elif host.startswith(u'*')), NOT part of the gold edit; it is retained to preserve the P2P test test_invalid_url[...http://*example.com]. Revealing unchanged/pre-existing behavior does not leak the gold edit. A postcondition that constrains the answer is the intended design of a spec-based benchmark, not leakage; the leakage screen concerns gold-patch specifics BEYOND the public statement, and here every discriminating fact (reject '.'-leading host, at the ASCII-host guard, signalling invalid-URL) is already fully public.

No gold-patch literal string, file/line pointer to the CHANGED line, or non-public phrasing appears in the spec view that isn't derivable from problem_statement. (mapping.md/refinement.md contain patch specifics but are AUDIT-only docs, not part of the consumer spec view produced by markers.spec_view.)

Mechanical checks: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True (spec region byte-identical; only elided impl differs, so G-DIFF genuinely senses the change via impl). markers.spec_view rendered cleanly with impl+prove_correct elided.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
