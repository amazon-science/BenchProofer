# P2 adversarial audit — sphinx-doc__sphinx-7889

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,9 +67,7 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
+  let name : PyKey := key
   return concatName displayName name
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,7 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
-  return concatName displayName name
+  return Except.ok (displayName ++ strChars key)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,7 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
-  return concatName displayName name
+  return Except.ok (strChars key ++ '.' :: displayName)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,7 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
-  return concatName displayName name
+  return Except.ok (displayName ++ ':' :: strChars key)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,9 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
-  return concatName displayName name
+  match key with
+  | .str s => return Except.ok (displayName ++ '.' :: s)
+  | .other _ => return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,7 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
-  return concatName displayName name
+  return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,10 +67,9 @@
 -- impl-start
 def implementation_mockSubscript
     (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
-  -- Render the key to its textual form before forming the derived display name,
-  -- so the display-name join always receives a textual component.
-  let name : PyKey := PyKey.str (strChars key)
-  return concatName displayName name
+  match displayName with
+  | [] => return Except.ok (strChars key)
+  | _  => return concatName displayName (PyKey.str (strChars key))
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Subscripting a documentation placeholder object.

A placeholder object stands in for an absent imported symbol that is unavailable
while building documentation. Indexing such a placeholder with a key (the `obj[key]`
operation) yields a fresh derived placeholder. The derived placeholder is
identified by a display name formed from the parent's display name and the key:
the parent display name, a separating dot, and the key rendered as text.

The key supplied to the subscript may be any object, not only a piece of text
(for example, a type parameter used when indexing a generic). Whatever the key
is, it is first rendered to its textual form, and the derived display name is the
parent display name followed by a dot and that textual form. The operation
always succeeds and yields that derived display name.

We model a key as `PyKey`: `PyKey.str s` is a key that is already text with code
points `s`; `PyKey.other r` is a non-text key whose textual rendering has code
points `r`. The outcome is `Except Unit (List Char)`: `Except.ok d` carries the
derived display name `d`, and `Except.error ()` marks a failure to form a display
name (which arises only when a display name is built from a non-text component).
-/

-- axioms-start
-- No `opaque` callees and no consumed axioms: every operation the subscript uses
-- (rendering the key to text; forming the derived display name) is modeled
-- directly in the `pure` region and validated against the real callees by G-AX.
-- axioms-end

-- pure-start
/-- A subscript key. `str s` is a textual key with code points `s`; `other r` is
a non-textual key whose textual rendering has code points `r`. -/
inductive PyKey where
  | str (s : List Char) : PyKey
  | other (r : List Char) : PyKey
  deriving DecidableEq

/-- The textual rendering of a key. A textual key renders to itself; a non-text
key renders to its carried textual form. -/
def strChars : PyKey → List Char
  | .str s => s
  | .other r => r

/-- Forming a derived display name by joining a parent display name to a key
component with a separating dot. The join requires the component to already be
text: a textual component yields `Except.ok (module ++ '.' :: s)`, while a
non-text component cannot be joined and yields `Except.error ()`. (This models
the unchanged display-name construction callee, an A-reference validated by
G-AX.) -/
def concatName (module : List Char) (name : PyKey) : Except Unit (List Char) :=
  match name with
  | .str s => Except.ok (module ++ '.' :: s)
  | .other _ => Except.error ()
-- pure-end

-- post-conditions-start
/-- Subscripting a placeholder with display name `displayName` by key `key`
yields the derived display name: the parent display name, a separating dot, and
the key's textual rendering. The operation always succeeds for every key. -/
def problem_spec_mockSubscript
    (displayName : List Char) (key : PyKey) (result : Except Unit (List Char)) : Prop :=
  result = Except.ok (displayName ++ '.' :: strChars key)
-- post-conditions-end

-- impl-start
def implementation_mockSubscript
    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
  -- Render the key to its textual form before forming the derived display name,
  -- so the display-name join always receives a textual component.
  let name : PyKey := PyKey.str (strChars key)
  return concatName displayName name
-- impl-end

-- proof-start
theorem correct_mockSubscript :
    ∀ (displayName : List Char) (key : PyKey),
      problem_spec_mockSubscript displayName key
        (implementation_mockSubscript displayName key) := by
  intro displayName key
  unfold problem_spec_mockSubscript implementation_mockSubscript concatName
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for sphinx-doc__sphinx-7889 (lean). Spec is EXACT-EQUALITY: problem_spec_mockSubscript pins result = Except.ok (displayName ++ '.' :: strChars key), a total function of the inputs. Any impl that verifies proves ∀ dn key, impl dn key = that gold value, i.e. is extensionally equal to the gold-output function, so its faithful patch produces the gold display name for every key and must resolve. This structurally forecloses verify⇏correct against equality attacks.

Same-spec confirmed True for all 8 files via swebench_unified.markers.same_spec (impl AND proof regions both collapse in the lean spec_view, so proofs may be adapted freely). Commands: `bash scripts/lean_verify.sh <file>`.

### Results
- pos_control.lean (gold impl, byte-identical to Solution.lean): EXIT 0 (verifies, no sorry). #print axioms correct_mockSubscript => 'correct_mockSubscript' does not depend on any axioms (CLEAN).
- atk_1 (prepatch bug: forward raw key `let name := key`): EXIT 1 — PREPATCH REPRODUCED. Goal reduces to concatName dn key = ok(dn++'.'::strChars key); false on PyKey.other (error () != ok ...). Unprovable.
- atk_2 (drop dot separator: ok(dn ++ strChars key)): EXIT 1 — false ∀-goal.
- atk_3 (swap order: ok(strChars key ++ '.' :: dn)): EXIT 1 — false ∀-goal.
- atk_4 (wrong separator ':' instead of '.'): EXIT 1 — false ∀-goal.
- atk_5 (partial-domain / control-flow: ok on .str, error () on .other): EXIT 1 — fails on .other leg.
- atk_6 (ungrounded oracle echo: always Except.error ()): EXIT 1 — false ∀-goal.
- atk_7 (boundary: empty displayName returns ok(strChars key), dropping the leading dot; gold requires ok('.'::strChars key)): EXIT 1 — false ∀-goal at dn=[].

NO wrong impl closed with a clean-axiom proof, so no faithful patch needed materialization/resolve (protocol step 2 vacuous — nothing to run). ≥5 distinct attack classes exercised (prepatch bug, output-shape divergences, partial-domain, boundary, ungrounded echo); none breaks the spec.

REFINEMENT AUDIT (refinement.md): 5 legs. Rows 1-3 = R (type refinements PyKey/List Char/Except, G-CONF-covered). Row 4 = R/I deep model of the CHANGED op str(key) via strChars (idempotent on text, renders non-text) — never axiomatized. Row 5 = A-reference: concatName models the UNCHANGED display-name join module + '.' + name inside _make_subclass (ok on textual component, error()/TypeError on non-text). No kind-3 (A-consumed) legs; axioms list in meta.json is empty; G-AX recorded pass. A-reference correspondence verified against real repo: gold patch at mock.py:55-56 is exactly `key -> str(key)` (confirmed from dataset); concatName's model of module+'.'+name and the TypeError-on-non-text branch match. FAIL_TO_PASS test_MockObject adds the mock.SomeClass[T] TypeVar (non-str key) case — exactly the PyKey.other leg the fix rescues (prepatch raises TypeError == error (); postpatch renders '~T' == ok). Model↔patch↔test correspondence holds.

Verdict: SOUND. verify⟹correct holds here — the exact-equality postcondition makes every verifying same-spec impl extensionally identical to gold output.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

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

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Subscripting a documentation placeholder object.

A placeholder object stands in for an absent imported symbol that is unavailable
while building documentation. Indexing such a placeholder with a key (the `obj[key]`
operation) yields a fresh derived placeholder. The derived placeholder is
identified by a display name formed from the parent's display name and the key:
the parent display name, a separating dot, and the key rendered as text.

The key supplied to the subscript may be any object, not only a piece of text
(for example, a type parameter used when indexing a generic). Whatever the key
is, it is first rendered to its textual form, and the derived display name is the
parent display name followed by a dot and that textual form. The operation
always succeeds and yields that derived display name.

We model a key as `PyKey`: `PyKey.str s` is a key that is already text with code
points `s`; `PyKey.other r` is a non-text key whose textual rendering has code
points `r`. The outcome is `Except Unit (List Char)`: `Except.ok d` carries the
derived display name `d`, and `Except.error ()` marks a failure to form a display
name (which arises only when a display name is built from a non-text component).
-/

-- axioms-start
-- No `opaque` callees and no consumed axioms: every operation the subscript uses
-- (rendering the key to text; forming the derived display name) is modeled
-- directly in the `pure` region and validated against the real callees by G-AX.
-- axioms-end

-- pure-start
/-- A subscript key. `str s` is a textual key with code points `s`; `other r` is
a non-textual key whose textual rendering has code points `r`. -/
inductive PyKey where
  | str (s : List Char) : PyKey
  | other (r : List Char) : PyKey
  deriving DecidableEq

/-- The textual rendering of a key. A textual key renders to itself; a non-text
key renders to its carried textual form. -/
def strChars : PyKey → List Char
  | .str s => s
  | .other r => r

/-- Forming a derived display name by joining a parent display name to a key
component with a separating dot. The join requires the component to already be
text: a textual component yields `Except.ok (module ++ '.' :: s)`, while a
non-text component cannot be joined and yields `Except.error ()`. (This models
the unchanged display-name construction callee, an A-reference validated by
G-AX.) -/
def concatName (module : List Char) (name : PyKey) : Except Unit (List Char) :=
  match name with
  | .str s => Except.ok (module ++ '.' :: s)
  | .other _ => Except.error ()
-- pure-end

-- post-conditions-start
/-- Subscripting a placeholder with display name `displayName` by key `key`
yields the derived display name: the parent display name, a separating dot, and
the key's textual rendering. The operation always succeeds for every key. -/
def problem_spec_mockSubscript
    (displayName : List Char) (key : PyKey) (result : Except Unit (List Char)) : Prop :=
  result = Except.ok (displayName ++ '.' :: strChars key)
-- post-conditions-end

-- impl-start
def implementation_mockSubscript
    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
  -- Render the key to its textual form before forming the derived display name,
  -- so the display-name join always receives a textual component.
  let name : PyKey := PyKey.str (strChars key)
  return concatName displayName name
-- impl-end

-- proof-start
theorem correct_mockSubscript :
    ∀ (displayName : List Char) (key : PyKey),
      problem_spec_mockSubscript displayName key
        (implementation_mockSubscript displayName key) := by
  intro displayName key
  unfold problem_spec_mockSubscript implementation_mockSubscript concatName
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for sphinx-doc__sphinx-7889 (lean). Spec is EXACT-EQUALITY: problem_spec_mockSubscript pins result = Except.ok (displayName ++ '.' :: strChars key), a total function of the inputs. Any impl that verifies proves ∀ dn key, impl dn key = that gold value, i.e. is extensionally equal to the gold-output function, so its faithful patch produces the gold display name for every key and must resolve. This structurally forecloses verify⇏correct against equality attacks.

Same-spec confirmed True for all 8 files via swebench_unified.markers.same_spec (impl AND proof regions both collapse in the lean spec_view, so proofs may be adapted freely). Commands: `bash scripts/lean_verify.sh <file>`.

### Results
- pos_control.lean (gold impl, byte-identical to Solution.lean): EXIT 0 (verifies, no sorry). #print axioms correct_mockSubscript => 'correct_mockSubscript' does not depend on any axioms (CLEAN).
- atk_1 (prepatch bug: forward raw key `let name := key`): EXIT 1 — PREPATCH REPRODUCED. Goal reduces to concatName dn key = ok(dn++'.'::strChars key); false on PyKey.other (error () != ok ...). Unprovable.
- atk_2 (drop dot separator: ok(dn ++ strChars key)): EXIT 1 — false ∀-goal.
- atk_3 (swap order: ok(strChars key ++ '.' :: dn)): EXIT 1 — false ∀-goal.
- atk_4 (wrong separator ':' instead of '.'): EXIT 1 — false ∀-goal.
- atk_5 (partial-domain / control-flow: ok on .str, error () on .other): EXIT 1 — fails on .other leg.
- atk_6 (ungrounded oracle echo: always Except.error ()): EXIT 1 — false ∀-goal.
- atk_7 (boundary: empty displayName returns ok(strChars key), dropping the leading dot; gold requires ok('.'::strChars key)): EXIT 1 — false ∀-goal at dn=[].

NO wrong impl closed with a clean-axiom proof, so no faithful patch needed materialization/resolve (protocol step 2 vacuous — nothing to run). ≥5 distinct attack classes exercised (prepatch bug, output-shape divergences, partial-domain, boundary, ungrounded echo); none breaks the spec.

REFINEMENT AUDIT (refinement.md): 5 legs. Rows 1-3 = R (type refinements PyKey/List Char/Except, G-CONF-covered). Row 4 = R/I deep model of the CHANGED op str(key) via strChars (idempotent on text, renders non-text) — never axiomatized. Row 5 = A-reference: concatName models the UNCHANGED display-name join module + '.' + name inside _make_subclass (ok on textual component, error()/TypeError on non-text). No kind-3 (A-consumed) legs; axioms list in meta.json is empty; G-AX recorded pass. A-reference correspondence verified against real repo: gold patch at mock.py:55-56 is exactly `key -> str(key)` (confirmed from dataset); concatName's model of module+'.'+name and the TypeError-on-non-text branch match. FAIL_TO_PASS test_MockObject adds the mock.SomeClass[T] TypeVar (non-str key) case — exactly the PyKey.other leg the fix rescues (prepatch raises TypeError == error (); postpatch renders '~T' == ok). Model↔patch↔test correspondence holds.

Verdict: SOUND. verify⟹correct holds here — the exact-equality postcondition makes every verifying same-spec impl extensionally identical to gold output.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: _MockObject.__getitem__ (sphinx/ext/autodoc/mock.py:55-56). Gold patch changes key -> str(key) so the module + '.' + name display-name join always receives text and never raises TypeError (issue: obj[TypeVar]).

Checks: (1) same_spec(Solution, Solution_prepatch) = True under lean backend — spec regions byte-identical. (2) Solution.lean compiles via lean_verify.sh, exit 0. (3) #print axioms correct_mockSubscript => 'does not depend on any axioms' (no sorryAx). base_commit worktree @ ec9af606c is genuinely prepatch (raw `key`, no str()); prepatch Lean impl FAILS the spec (rfl fails on the PyKey.other leg), so the spec discriminates the bug and is not trivially satisfiable.

Faithfulness (spec too strong / drift?): the spec pins result = Except.ok (displayName ++ '.' :: strChars key), i.e. always succeeds. Replicated the real post-patch behavior (str(key) then module + '.' + str(key)) against the model on edge cases — text key, TypeVar('T')->'~T', int 42, dotted string 'b.c', None, tuple — ALL MATCH. Post-patch code always succeeds (both operands of + are str), matching the always-Except.ok claim. concatName's error leg models the UNCHANGED callee's failure on a non-text component and is correctly unreachable post-patch since str(...) always returns text — mirrors the real code, which never raises after the fix. PyKey (key carries its own textual rendering) is a standard, faithful abstraction of str(key). No input in the modeled domain makes the modeled function disagree with the real callee.

Conclusion: FAITHFUL — no diverging input; the model neither over- nor under-constrains relative to the real post-patch __getitem__.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the public problem_statement ONLY (not hints_text). The problem statement already discloses the fix essence: autodoc mock's _make_subclass throws TypeError concatenating a str to a TypeVar for generic-typed classes, and the expected behavior is that docs still build with generics. The spec view keeps this abstract ('documentation placeholder object', obj[key]) and NEVER names the patched file sphinx/ext/autodoc/mock.py, the patched symbols (__getitem__/__iter__ -> 'getitem'/'iter'), or _make_subclass. Mechanical checks all clean: (1) same_spec(Solution, Solution_prepatch)=True, so the discriminating spec region is byte-identical and encodes only the postcondition, not the impl; (2) leakage.screen passes with zero hard_failures; (3) no patched file/module path in view; (4) spec-view identifiers (mockSubscript, PyKey, strChars, concatName) embed no patched symbol; (5) no gold-diff line reproduced (str(key), _make_subclass calls absent); (6) no bug/fix narration in comments. The postcondition (result = Except.ok (displayName ++ '.' :: strChars key), i.e. subscript always succeeds by rendering the key to text) is exactly what the public 'works with generics' expectation requires and is a legitimate correct-behavior spec, not a code-edit disclosure. The docstring's mention of 'a type parameter used when indexing a generic' merely restates the public TypeVar/generic-typed-class scenario. Solution.lean compiles per the recorded G-VERIFY pass; the proof closes by rfl with no sorry. No leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
