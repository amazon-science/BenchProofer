# P2 adversarial audit — psf__requests-5414

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
@@ -63,7 +63,7 @@
       match idnaEncode host with
       | Except.ok enc => h := enc
       | Except.error () => return Except.error ()
-    else if startsWithInvalid host then
+    else if (match host with | [] => false | c :: _ => c == '*') then
       return Except.error ()
     return Except.ok h
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
       match idnaEncode host with
       | Except.ok enc => h := enc
       | Except.error () => return Except.error ()
-    else if startsWithInvalid host then
+    else if (match host with | [] => false | c :: _ => c == '.') then
       return Except.error ()
     return Except.ok h
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,8 +63,6 @@
       match idnaEncode host with
       | Except.ok enc => h := enc
       | Except.error () => return Except.error ()
-    else if startsWithInvalid host then
-      return Except.error ()
     return Except.ok h
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,15 +57,7 @@
 
 -- impl-start
 def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
-  Id.run do
-    let mut h := host
-    if !isAscii host then
-      match idnaEncode host with
-      | Except.ok enc => h := enc
-      | Except.error () => return Except.error ()
-    else if startsWithInvalid host then
-      return Except.error ()
-    return Except.ok h
+  idnaEncode host
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,12 +59,12 @@
 def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
   Id.run do
     let mut h := host
-    if !isAscii host then
+    if startsWithInvalid host then
+      return Except.error ()
+    else if !isAscii host then
       match idnaEncode host with
       | Except.ok enc => h := enc
       | Except.error () => return Except.error ()
-    else if startsWithInvalid host then
-      return Except.error ()
     return Except.ok h
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
 def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
   Id.run do
     let mut h := host
-    if !isAscii host then
+    if !(host.all (fun c => decide (c.toNat <= 128))) then
       match idnaEncode host with
       | Except.ok enc => h := enc
       | Except.error () => return Except.error ()
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,14 +58,13 @@
 -- impl-start
 def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
   Id.run do
-    let mut h := host
     if !isAscii host then
       match idnaEncode host with
-      | Except.ok enc => h := enc
+      | Except.ok enc => return Except.ok enc
       | Except.error () => return Except.error ()
     else if startsWithInvalid host then
       return Except.error ()
-    return Except.ok h
+    return Except.ok []
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating the host component of a requested URL.

Before a parsed host string is used to build a network location, it is checked
and, when necessary, re-encoded:

  * A host that contains any non-ASCII code point is handed to a standard
    internationalized-domain-name encoder. If that encoder accepts the name, the
    encoded form is carried forward; if it rejects the name, the host is invalid.
  * A host whose code points are all ASCII is accepted unchanged, UNLESS it
    begins with a reserved leading character — namely a wildcard marker (`*`) or
    an empty leading label introduced by a leading dot (`.`) — in which case the
    host is invalid.

We model the outcome as `Except Unit (List Char)`: `Except.error ()` is the
single "invalid host" rejection (both rejection sites raise the same error), and
`Except.ok h` carries forward the accepted host `h`.
-/

-- axioms-start
/-- A standard internationalized-domain-name encoder applied to a host that
contains non-ASCII code points. It either returns an encoded host (`Except.ok`)
or rejects the name (`Except.error ()`). It is an unchanged outside callee; the
specification constrains none of its inner behavior, only its result shape. -/
opaque idnaEncode : List Char → Except Unit (List Char)
-- axioms-end

-- pure-start
/-- Whether every code point of the host is ASCII (numeric value `< 128`). -/
def isAscii (host : List Char) : Bool :=
  host.all (fun c => decide (c.toNat < 128))

/-- Whether the host begins with a reserved leading character: a wildcard marker
(`*`) or a leading dot (`.`) that would introduce an empty leading label. The
empty host begins with neither. -/
def startsWithInvalid (host : List Char) : Bool :=
  match host with
  | [] => false
  | c :: _ => c == '*' || c == '.'
-- pure-end

-- post-conditions-start
/-- The validation outcome for a parsed host. For an all-ASCII host: rejected
(`Except.error ()`) iff it begins with a reserved leading character, otherwise
accepted unchanged (`Except.ok host`). For a host with non-ASCII code points: the
result is exactly the internationalized-domain-name encoder's outcome on it. -/
def problem_spec_validateHost
    (host : List Char) (result : Except Unit (List Char)) : Prop :=
  if isAscii host then
    (if startsWithInvalid host then result = Except.error () else result = Except.ok host)
  else
    result = idnaEncode host
-- post-conditions-end

-- impl-start
def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
  Id.run do
    let mut h := host
    if !isAscii host then
      match idnaEncode host with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()
    else if startsWithInvalid host then
      return Except.error ()
    return Except.ok h
-- impl-end

-- proof-start
theorem correct_validateHost :
    ∀ (host : List Char),
      problem_spec_validateHost host (implementation_validateHost host) := by
  intro host
  unfold problem_spec_validateHost implementation_validateHost
  simp only [Id.run]
  by_cases ha : isAscii host
  · simp only [ha, if_true, Bool.not_true]
    by_cases hs : startsWithInvalid host <;> simp only [hs, if_true] <;> rfl
  · simp only [ha, Bool.not_false]
    cases h : idnaEncode host with
    | ok enc => rfl
    | error e => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition problem_spec_validateHost is TOTAL and FUNCTIONAL: for every host it pins result to exactly one value (ASCII & startsWithInvalid -> error (); ASCII & not -> ok host; non-ASCII -> idnaEncode host, full equality to the opaque callee). So any impl that verifies must be extensionally equal to gold, and verify=>correct is structurally enforced. I encoded the prepatch bug plus 6 further DISTINCT same-spec wrong impls (all same_spec=True, verified via swebench_unified.markers.same_spec on backend lean); every one carries the gold-style proof body and FAILS to close. No verifying wrong impl exists, so there is no faithful refined patch to run through resolve.

Same_spec check (all True incl pos_control): ran `same_spec(gold, atk_N, lean.language)` -> True for atk_1..7 and pos_control.

Attacks (cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug: rejects only leading '*', not '.'): exit=1. Goal reduces to `pure (Except.ok host) = Except.error ()` on the .example.com class -> unsolvable. Reproduces the documented prepatch defect (FAIL_TO_PASS http://.example.com).
- atk_2 (mirror bug: rejects only leading '.', not '*'): exit=1. Fails on the leading-'*' class (PASS_TO_PASS http://*example.com).
- atk_3 (partial-domain / drop reserved-char check: never rejects ASCII): exit=1. Goal `pure (Except.ok host) = Except.error ()`.
- atk_4 (ungrounded-oracle echo: return idnaEncode host for all hosts): exit=1. rfl fails: opaque `idnaEncode host` not def-eq to `Except.error ()`/`Except.ok host` on ASCII branch. Confirms the opaque A-reference cannot be echoed into the ASCII leg.
- atk_5 (control-flow-effect swap: test reserved-char BEFORE ascii): exit=1. Changes behavior for non-ASCII hosts starting with '*'/'.'; proof fails on non-ASCII branch (idnaEncode vs error).
- atk_6 (boundary: ascii test uses c.toNat <= 128 instead of < 128): exit=1. Off-by-one on code point 128 (non-ASCII per spec) => proof does not close.
- atk_7 (accepted-host corruption: return Except.ok [] instead of ok host on accept): exit=1. Goal `pure (Except.ok []) = Except.ok host` unsolvable.

Exit codes: 1=proof error (no sorry, none exit 3/124). No log contains 'sorry'. positive_control (byte-identical gold Solution.lean) verifies exit=0.

Verification ran concurrently in two background batches of 4 (atk_1-4; atk_5-7+pos_control), <=4 at a time.

refinement.md audit: legs are 1=R (str<->List Char), 2=R (Except<->raise/carry), 3=A-reference/I (isAscii deep model of unchanged unicode_is_ascii, no _prop consumed), 4=A-reference (idnaEncode opaque unchanged _get_idna_encoded_host, used identically in spec & impl, proof consumes no property; excluded from G-CONF differential), 5=I (startsWithInvalid = the changed line startswith((u'*',u'.')), deeply modeled), 6=I (accepted path). NO kind-3 / no A-consumed axiom. A-legs' correspondence to real callees holds: patch edits exactly startswith(u'*')->startswith((u'*',u'.')) matching startsWithInvalid checking BOTH '*' and '.' (atk_1/atk_2 prove neither half is droppable); idnaEncode leg is pinned by full equality (atk_4/atk_5 prove it cannot be echoed/reordered). conf_skip=false is justified: R/I ASCII leg is differentially tested by conformance_check.py against a faithful post-patch replica.

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
Validating the host component of a requested URL.

Before a parsed host string is used to build a network location, it is checked
and, when necessary, re-encoded:

  * A host that contains any non-ASCII code point is handed to a standard
    internationalized-domain-name encoder. If that encoder accepts the name, the
    encoded form is carried forward; if it rejects the name, the host is invalid.
  * A host whose code points are all ASCII is accepted unchanged, UNLESS it
    begins with a reserved leading character — namely a wildcard marker (`*`) or
    an empty leading label introduced by a leading dot (`.`) — in which case the
    host is invalid.

We model the outcome as `Except Unit (List Char)`: `Except.error ()` is the
single "invalid host" rejection (both rejection sites raise the same error), and
`Except.ok h` carries forward the accepted host `h`.
-/

-- axioms-start
/-- A standard internationalized-domain-name encoder applied to a host that
contains non-ASCII code points. It either returns an encoded host (`Except.ok`)
or rejects the name (`Except.error ()`). It is an unchanged outside callee; the
specification constrains none of its inner behavior, only its result shape. -/
opaque idnaEncode : List Char → Except Unit (List Char)
-- axioms-end

-- pure-start
/-- Whether every code point of the host is ASCII (numeric value `< 128`). -/
def isAscii (host : List Char) : Bool :=
  host.all (fun c => decide (c.toNat < 128))

/-- Whether the host begins with a reserved leading character: a wildcard marker
(`*`) or a leading dot (`.`) that would introduce an empty leading label. The
empty host begins with neither. -/
def startsWithInvalid (host : List Char) : Bool :=
  match host with
  | [] => false
  | c :: _ => c == '*' || c == '.'
-- pure-end

-- post-conditions-start
/-- The validation outcome for a parsed host. For an all-ASCII host: rejected
(`Except.error ()`) iff it begins with a reserved leading character, otherwise
accepted unchanged (`Except.ok host`). For a host with non-ASCII code points: the
result is exactly the internationalized-domain-name encoder's outcome on it. -/
def problem_spec_validateHost
    (host : List Char) (result : Except Unit (List Char)) : Prop :=
  if isAscii host then
    (if startsWithInvalid host then result = Except.error () else result = Except.ok host)
  else
    result = idnaEncode host
-- post-conditions-end

-- impl-start
def implementation_validateHost (host : List Char) : Except Unit (List Char) :=
  Id.run do
    let mut h := host
    if !isAscii host then
      match idnaEncode host with
      | Except.ok enc => h := enc
      | Except.error () => return Except.error ()
    else if startsWithInvalid host then
      return Except.error ()
    return Except.ok h
-- impl-end

-- proof-start
theorem correct_validateHost :
    ∀ (host : List Char),
      problem_spec_validateHost host (implementation_validateHost host) := by
  intro host
  unfold problem_spec_validateHost implementation_validateHost
  simp only [Id.run]
  by_cases ha : isAscii host
  · simp only [ha, if_true, Bool.not_true]
    by_cases hs : startsWithInvalid host <;> simp only [hs, if_true] <;> rfl
  · simp only [ha, Bool.not_false]
    cases h : idnaEncode host with
    | ok enc => rfl
    | error e => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The postcondition problem_spec_validateHost is TOTAL and FUNCTIONAL: for every host it pins result to exactly one value (ASCII & startsWithInvalid -> error (); ASCII & not -> ok host; non-ASCII -> idnaEncode host, full equality to the opaque callee). So any impl that verifies must be extensionally equal to gold, and verify=>correct is structurally enforced. I encoded the prepatch bug plus 6 further DISTINCT same-spec wrong impls (all same_spec=True, verified via swebench_unified.markers.same_spec on backend lean); every one carries the gold-style proof body and FAILS to close. No verifying wrong impl exists, so there is no faithful refined patch to run through resolve.

Same_spec check (all True incl pos_control): ran `same_spec(gold, atk_N, lean.language)` -> True for atk_1..7 and pos_control.

Attacks (cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 (prepatch bug: rejects only leading '*', not '.'): exit=1. Goal reduces to `pure (Except.ok host) = Except.error ()` on the .example.com class -> unsolvable. Reproduces the documented prepatch defect (FAIL_TO_PASS http://.example.com).
- atk_2 (mirror bug: rejects only leading '.', not '*'): exit=1. Fails on the leading-'*' class (PASS_TO_PASS http://*example.com).
- atk_3 (partial-domain / drop reserved-char check: never rejects ASCII): exit=1. Goal `pure (Except.ok host) = Except.error ()`.
- atk_4 (ungrounded-oracle echo: return idnaEncode host for all hosts): exit=1. rfl fails: opaque `idnaEncode host` not def-eq to `Except.error ()`/`Except.ok host` on ASCII branch. Confirms the opaque A-reference cannot be echoed into the ASCII leg.
- atk_5 (control-flow-effect swap: test reserved-char BEFORE ascii): exit=1. Changes behavior for non-ASCII hosts starting with '*'/'.'; proof fails on non-ASCII branch (idnaEncode vs error).
- atk_6 (boundary: ascii test uses c.toNat <= 128 instead of < 128): exit=1. Off-by-one on code point 128 (non-ASCII per spec) => proof does not close.
- atk_7 (accepted-host corruption: return Except.ok [] instead of ok host on accept): exit=1. Goal `pure (Except.ok []) = Except.ok host` unsolvable.

Exit codes: 1=proof error (no sorry, none exit 3/124). No log contains 'sorry'. positive_control (byte-identical gold Solution.lean) verifies exit=0.

Verification ran concurrently in two background batches of 4 (atk_1-4; atk_5-7+pos_control), <=4 at a time.

refinement.md audit: legs are 1=R (str<->List Char), 2=R (Except<->raise/carry), 3=A-reference/I (isAscii deep model of unchanged unicode_is_ascii, no _prop consumed), 4=A-reference (idnaEncode opaque unchanged _get_idna_encoded_host, used identically in spec & impl, proof consumes no property; excluded from G-CONF differential), 5=I (startsWithInvalid = the changed line startswith((u'*',u'.')), deeply modeled), 6=I (accepted path). NO kind-3 / no A-consumed axiom. A-legs' correspondence to real callees holds: patch edits exactly startswith(u'*')->startswith((u'*',u'.')) matching startsWithInvalid checking BOTH '*' and '.' (atk_1/atk_2 prove neither half is droppable); idnaEncode leg is pinned by full equality (atk_4/atk_5 prove it cannot be echoed/reordered). conf_skip=false is justified: R/I ASCII leg is differentially tested by conformance_check.py against a faithful post-patch replica.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) audit for psf__requests-5414 lean bundle. Modeled fragment: host-validation block of PreparedRequest.prepare_url (requests/models.py:398-405), the exact fragment the gold patch edits (startswith(u'*') -> startswith((u'*', u'.'))).

### Checks performed
1. Build/axioms: Solution.lean compiles via lean_verify.sh (exit 0). `#print axioms correct_validateHost` => [propext] only. No sorryAx; proof is genuine (not fake). Prepatch carries a `sorry` as expected (gold proof cannot close against the buggy impl).
2. Spec byte-identity: swebench_unified.markers.same_spec(post, prepatch, lean tables) = True. The spec view (axioms+pure+post-conditions) is identical between gold and prepatch; only the impl region differs. Spec is not tailored to the gold impl.
3. conformance_check.py (G-CONF): passes, checked=120022, disagreements=0, over edge cases + 120k LCG-fuzzed ASCII hosts.
4. Independent differential (300020 inputs, seed 5414) against the REAL repo callee unicode_is_ascii imported, covering non-ASCII, control chars \x7f/\x80, empty, and every leading-char position: 0 divergences between the spec's abstraction and the real post-patch branch structure.

### FAITHFULNESS ARGUMENT (spec not too strong / no drift):
- isAscii host := host.all (c.toNat < 128) exactly models unicode_is_ascii (u_string.encode('ascii') succeeds iff all code points < 128). Verified against the real callee.
- startsWithInvalid host := first code point in {'*','.'} (empty => false) exactly models post-patch host.startswith((u'*', u'.')) — Python startswith on a 1-char-each tuple over a str matches char-0 membership; empty host => False in both.
- Non-ASCII leg: spec pins result = idnaEncode host, an opaque unchanged callee (=_get_idna_encoded_host), used IDENTICALLY in spec and impl; proof discharges it by case analysis, consuming no property. This is not spec-too-strong: it constrains the non-ASCII result to be EXACTLY whatever the real callee returns, which is faithful, and it is excluded from the differential by construction (identical in both legs).
- Error modeling: both raise sites (IDNA UnicodeError, reserved leading char) raise the identical InvalidURL('URL has an invalid label.'), correctly collapsed to the single Except.error ().
- Result is fully determined for every host (frame complete); no unconstrained output component and no opaque oracle governing the changed decision.

No input found where the modeled function disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `elif host.startswith(u'*'):` -> `elif host.startswith((u'*', u'.')):`, i.e. also reject an all-ASCII host beginning with a leading dot as an invalid label. The discriminating behavior is ALREADY public in the problem_statement, which (a) names the exact input `http://.example.com`, (b) states the desired outcome `InvalidUrl: URL has an invalid label.` in place of the current `UnicodeError`, and (c) links directly to `requests/models.py` L401 — the very `elif host.startswith(u'*')` line the patch edits. So the leading-dot rejection is disclosed by the public statement, not the spec.

Spec-view analysis: same_spec(Solution, Solution_prepatch, lean) = True — the marked spec region (docstring + axioms + pure helpers + post-conditions) is byte-identical between post- and pre-patch bundles; the only divergence lives in the elided impl selector (`c == '*'` vs `c == '*' || c == '.'`) and the proof, both of which are NOT in the spec view. The spec_view text describes the post-fix outcome abstractly ("reserved leading character — namely a wildcard marker (`*`) or an empty leading label introduced by a leading dot (`.`)") as any faithful, sound spec must, and never quotes the patch's literal `startswith((u'*', u'.'))` form. The `*` guard mentioned is pre-existing base_commit behavior; the `.` rejection is exactly the fix the public issue requests. G-LEAK lexical screen: no gold-patch specifics or non-public phrasing appear beyond the public problem_statement. Nothing leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
