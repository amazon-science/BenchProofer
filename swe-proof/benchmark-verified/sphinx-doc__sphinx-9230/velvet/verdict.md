# P2 adversarial audit — sphinx-doc__sphinx-9230

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. The postcondition `out = resolveParam descriptor mayCarryType` is total functional equality and the pure region (severTail/resolveParam/wsCodes) plus the proof tactic (loom_solve; simp_all [resolveParam]) are all frozen outside the impl region, so any verifying impl is behaviourally identical to the gold rsplit(None,1) resolution. The discriminating input `dict(str, str) opc_meta` separates at the LAST whitespace to (type='dict(str, str)', name='opc_meta') under the spec; the prepatch first-whitespace impl (atk_1) fails to verify exactly here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -97,9 +97,11 @@
     -- impl-start
     let out : ParsedParam :=
       if mayCarryType then
-        match severTail descriptor with
-        | some (typ, nm) => { name := nm, typeName := some typ }
-        | none           => { name := descriptor, typeName := none }
+        let s' := descriptor.dropWhile isWs
+        let head := s'.takeWhile (fun c => !isWs c)
+        let rest := (s'.dropWhile (fun c => !isWs c)).dropWhile isWs
+        if rest.isEmpty then { name := descriptor, typeName := none }
+        else { name := rest, typeName := some head }
       else
         { name := descriptor, typeName := none }
     return out
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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -98,7 +98,7 @@
     let out : ParsedParam :=
       if mayCarryType then
         match severTail descriptor with
-        | some (typ, nm) => { name := nm, typeName := some typ }
+        | some (typ, nm) => { name := typ, typeName := some nm }
         | none           => { name := descriptor, typeName := none }
       else
         { name := descriptor, typeName := none }
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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -95,13 +95,7 @@
             out = { name := a, typeName := some t }
   do
     -- impl-start
-    let out : ParsedParam :=
-      if mayCarryType then
-        match severTail descriptor with
-        | some (typ, nm) => { name := nm, typeName := some typ }
-        | none           => { name := descriptor, typeName := none }
-      else
-        { name := descriptor, typeName := none }
+    let out : ParsedParam := { name := descriptor, typeName := none }
     return out
     -- impl-end
 
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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -99,7 +99,7 @@
       if mayCarryType then
         match severTail descriptor with
         | some (typ, nm) => { name := nm, typeName := some typ }
-        | none           => { name := descriptor, typeName := none }
+        | none           => { name := descriptor, typeName := some descriptor }
       else
         { name := descriptor, typeName := none }
     return out
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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -96,7 +96,7 @@
   do
     -- impl-start
     let out : ParsedParam :=
-      if mayCarryType then
+      if !mayCarryType then
         match severTail descriptor with
         | some (typ, nm) => { name := nm, typeName := some typ }
         | none           => { name := descriptor, typeName := none }
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -95,13 +95,7 @@
             out = { name := a, typeName := some t }
   do
     -- impl-start
-    let out : ParsedParam :=
-      if mayCarryType then
-        match severTail descriptor with
-        | some (typ, nm) => { name := nm, typeName := some typ }
-        | none           => { name := descriptor, typeName := none }
-      else
-        { name := descriptor, typeName := none }
+    let out : ParsedParam := { name := [], typeName := none }
     return out
     -- impl-end
 
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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -101,7 +101,7 @@
         | some (typ, nm) => { name := nm, typeName := some typ }
         | none           => { name := descriptor, typeName := none }
       else
-        { name := descriptor, typeName := none }
+        { name := descriptor, typeName := some [] }
     return out
     -- impl-end
 
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
 /- No consumed axioms. The way a parameter descriptor is separated into a type
@@ -95,13 +95,10 @@
             out = { name := a, typeName := some t }
   do
     -- impl-start
-    let out : ParsedParam :=
-      if mayCarryType then
-        match severTail descriptor with
-        | some (typ, nm) => { name := nm, typeName := some typ }
-        | none           => { name := descriptor, typeName := none }
-      else
-        { name := descriptor, typeName := none }
+    let mut i : Nat := 0
+    while true do
+      i := i + 1
+    let out : ParsedParam := { name := [], typeName := none }
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The way a parameter descriptor is separated into a type
   part and a name part — the only behaviour this operation depends on — is
   modeled DEEPLY in the `pure` region below (`severTail`) and validated against
   its real standard-library counterpart by axiom_check.py (G-AX) as an
   A-reference. Nothing is hidden behind a consumed `axiom`. -/
-- axioms-end

-- pure-start
/- The whitespace alphabet used when separating words: the Unicode code points
   the runtime treats as whitespace when separating on "any run of whitespace"
   (no explicit separator). This is the per-code-point classifier the separation
   below consults. Provenance + soundness check: mapping.md §3 / axiom_check.py. -/
def wsCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

def isWs (c : Char) : Bool := wsCodes.contains c.toNat

/- Drop a maximal run of trailing whitespace. -/
def rstripWs (s : List Char) : List Char :=
  (s.reverse.dropWhile isWs).reverse

/- The maximal whitespace-free suffix of `s` (its final word). -/
def tailWord (s : List Char) : List Char :=
  (s.reverse.takeWhile (fun c => !isWs c)).reverse

/- Everything strictly before the final whitespace-free suffix of `s`,
   including the whitespace run that precedes that suffix. -/
def beforeTailWord (s : List Char) : List Char :=
  (s.reverse.dropWhile (fun c => !isWs c)).reverse

/- Separate `s` into (everything-but-its-final-word, its-final-word) at the LAST
   run of whitespace, after first ignoring trailing whitespace. Leading and
   interior whitespace stays attached to the left part, so a left part that
   itself contains whitespace (e.g. a bracketed expression with internal spaces)
   is kept whole. `none` when, after ignoring outer whitespace, there is no
   whitespace separating two non-empty parts (a single word, or empty). The
   deep model of separating "on the last whitespace, at most once". -/
def severTail (s : List Char) : Option (List Char × List Char) :=
  let s' := rstripWs s
  let nm := tailWord s'
  let lead := rstripWs (beforeTailWord s')
  if lead.isEmpty then none else some (lead, nm)

/- The outcome of resolving one parameter descriptor. When the descriptor may
   carry an inline type and it separates into two parts at the last whitespace,
   the leading part is recorded as the type and the trailing word becomes the
   parameter name; otherwise the descriptor is left untouched and no type is
   recorded. This is the per-parameter result the operation produces. -/
structure ParsedParam where
  name     : List Char
  typeName : Option (List Char)
  deriving DecidableEq, Inhabited

def resolveParam (descriptor : List Char) (mayCarryType : Bool) : ParsedParam :=
  if mayCarryType then
    match severTail descriptor with
    | some (typ, nm) => { name := nm, typeName := some typ }
    | none           => { name := descriptor, typeName := none }
  else
    { name := descriptor, typeName := none }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve one parameter descriptor into its name and (optional) inline type.
   Both inputs are read-only (not `mut`): the descriptor text and the
   may-carry-type flag are consulted, a fresh result is produced. When the
   descriptor may carry a type and its text separates at the last whitespace
   into a non-empty leading part and a trailing word, the leading part becomes
   the recorded type and the trailing word becomes the parameter name; in every
   other case the descriptor passes through unchanged with no recorded type
   (so a descriptor whose type expression itself contains spaces is kept whole
   as the type, and only its final word is taken as the name). -/
method resolveParamMethod (descriptor : List Char) (mayCarryType : Bool)
    return (out : ParsedParam)
  ensures out = resolveParam descriptor mayCarryType
  ensures mayCarryType = false → out = { name := descriptor, typeName := none }
  ensures out.typeName = none → out.name = descriptor
  ensures ∀ t a, severTail descriptor = some (t, a) → mayCarryType = true →
            out = { name := a, typeName := some t }
  do
    -- impl-start
    let out : ParsedParam :=
      if mayCarryType then
        match severTail descriptor with
        | some (typ, nm) => { name := nm, typeName := some typ }
        | none           => { name := descriptor, typeName := none }
      else
        { name := descriptor, typeName := none }
    return out
    -- impl-end

prove_correct resolveParamMethod by
  loom_solve
  simp_all [resolveParam]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec(velvet)=True confirmed for all 8 attacks + pos_control. Verifications run concurrently as background Bash jobs, ≤4 at a time.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean (shipped correct impl): exit 0 = VERIFIES.
- atk_1 (prepatch bug: FIRST-whitespace separation, partial-domain wrong on bracketed-type descriptors): exit 1 = rejected. Prepatch bug reproduced.
- atk_2 (boundary: swap type<->name in the some branch): exit 1.
- atk_3 (partial-domain: ignore severTail, always passthrough {name:=descriptor,none}): exit 1.
- atk_4 (none-branch records descriptor as its own type — wrong on single-word/None): exit 1.
- atk_5 (control-flow-effect: invert the mayCarryType guard to !mayCarryType): exit 1.
- atk_6 (ungrounded-oracle echo: return Inhabited default {name:=[],none}): exit 1.
- atk_7 (partial-domain subtle: correct on true, records empty type some [] on false): exit 1.
- atk_8 (control-flow-effect / vacuity probe: `while true do i:=i+1` divergence before return, targeting the termination "partial" + demonic-choice hole): exit 1 — frozen proof errors 'No goals to be solved'; diverging garbage does NOT verify.

All 6 requested wrong-impl families covered (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) plus the prepatch bug plus a divergence/vacuity probe. NO wrong impl verified, so step-2 has zero candidates — patches={} and no resolve run was needed (correctly, none skipped).

A-LEG / correspondence audit (refinement.md): legs A1=R, A2=R, A3=A-reference+I, A4=R+I, A5=R+I; §C confirms no kind-3 legs and no consumed axioms. The single A-reference (severTail deep model == real str.rsplit(None,1); wsCodes == Python split-whitespace) validated by:
  * axiom_check.py (G-AX): exit 0, 16 boundary + 50000 fuzz inputs sound, wsCodes matches Python over full BMP.
  * conformance_check.py (G-CONF): exit 0, 200032 inputs seed=9230, 0 disagreements.
  * INDEPENDENT spot-check against genuine CPython builtins: real str.rsplit(None,1) == fresh transliteration of severTail on all discriminating cases incl. 'dict(str, str) opc_meta' -> ('dict(str, str)','opc_meta'); BMP classifier mismatch count = 0. Not a rigged echo.

The spec is a total functional-equality postcondition over a frozen pure model, so verify => correct is genuinely enforced. No falsification found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. The postcondition `out = resolveParam descriptor mayCarryType` is total functional equality and the pure region (severTail/resolveParam/wsCodes) plus the proof tactic (loom_solve; simp_all [resolveParam]) are all frozen outside the impl region, so any verifying impl is behaviourally identical to the gold rsplit(None,1) resolution. The discriminating input `dict(str, str) opc_meta` separates at the LAST whitespace to (type='dict(str, str)', name='opc_meta') under the spec; the prepatch first-whitespace impl (atk_1) fails to verify exactly here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The way a parameter descriptor is separated into a type
   part and a name part — the only behaviour this operation depends on — is
   modeled DEEPLY in the `pure` region below (`severTail`) and validated against
   its real standard-library counterpart by axiom_check.py (G-AX) as an
   A-reference. Nothing is hidden behind a consumed `axiom`. -/
-- axioms-end

-- pure-start
/- The whitespace alphabet used when separating words: the Unicode code points
   the runtime treats as whitespace when separating on "any run of whitespace"
   (no explicit separator). This is the per-code-point classifier the separation
   below consults. Provenance + soundness check: mapping.md §3 / axiom_check.py. -/
def wsCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

def isWs (c : Char) : Bool := wsCodes.contains c.toNat

/- Drop a maximal run of trailing whitespace. -/
def rstripWs (s : List Char) : List Char :=
  (s.reverse.dropWhile isWs).reverse

/- The maximal whitespace-free suffix of `s` (its final word). -/
def tailWord (s : List Char) : List Char :=
  (s.reverse.takeWhile (fun c => !isWs c)).reverse

/- Everything strictly before the final whitespace-free suffix of `s`,
   including the whitespace run that precedes that suffix. -/
def beforeTailWord (s : List Char) : List Char :=
  (s.reverse.dropWhile (fun c => !isWs c)).reverse

/- Separate `s` into (everything-but-its-final-word, its-final-word) at the LAST
   run of whitespace, after first ignoring trailing whitespace. Leading and
   interior whitespace stays attached to the left part, so a left part that
   itself contains whitespace (e.g. a bracketed expression with internal spaces)
   is kept whole. `none` when, after ignoring outer whitespace, there is no
   whitespace separating two non-empty parts (a single word, or empty). The
   deep model of separating "on the last whitespace, at most once". -/
def severTail (s : List Char) : Option (List Char × List Char) :=
  let s' := rstripWs s
  let nm := tailWord s'
  let lead := rstripWs (beforeTailWord s')
  if lead.isEmpty then none else some (lead, nm)

/- The outcome of resolving one parameter descriptor. When the descriptor may
   carry an inline type and it separates into two parts at the last whitespace,
   the leading part is recorded as the type and the trailing word becomes the
   parameter name; otherwise the descriptor is left untouched and no type is
   recorded. This is the per-parameter result the operation produces. -/
structure ParsedParam where
  name     : List Char
  typeName : Option (List Char)
  deriving DecidableEq, Inhabited

def resolveParam (descriptor : List Char) (mayCarryType : Bool) : ParsedParam :=
  if mayCarryType then
    match severTail descriptor with
    | some (typ, nm) => { name := nm, typeName := some typ }
    | none           => { name := descriptor, typeName := none }
  else
    { name := descriptor, typeName := none }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve one parameter descriptor into its name and (optional) inline type.
   Both inputs are read-only (not `mut`): the descriptor text and the
   may-carry-type flag are consulted, a fresh result is produced. When the
   descriptor may carry a type and its text separates at the last whitespace
   into a non-empty leading part and a trailing word, the leading part becomes
   the recorded type and the trailing word becomes the parameter name; in every
   other case the descriptor passes through unchanged with no recorded type
   (so a descriptor whose type expression itself contains spaces is kept whole
   as the type, and only its final word is taken as the name). -/
method resolveParamMethod (descriptor : List Char) (mayCarryType : Bool)
    return (out : ParsedParam)
  ensures out = resolveParam descriptor mayCarryType
  ensures mayCarryType = false → out = { name := descriptor, typeName := none }
  ensures out.typeName = none → out.name = descriptor
  ensures ∀ t a, severTail descriptor = some (t, a) → mayCarryType = true →
            out = { name := a, typeName := some t }
  do
    -- impl-start
    let out : ParsedParam :=
      if mayCarryType then
        match severTail descriptor with
        | some (typ, nm) => { name := nm, typeName := some typ }
        | none           => { name := descriptor, typeName := none }
      else
        { name := descriptor, typeName := none }
    return out
    -- impl-end

prove_correct resolveParamMethod by
  loom_solve
  simp_all [resolveParam]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. same_spec(velvet)=True confirmed for all 8 attacks + pos_control. Verifications run concurrently as background Bash jobs, ≤4 at a time.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean (shipped correct impl): exit 0 = VERIFIES.
- atk_1 (prepatch bug: FIRST-whitespace separation, partial-domain wrong on bracketed-type descriptors): exit 1 = rejected. Prepatch bug reproduced.
- atk_2 (boundary: swap type<->name in the some branch): exit 1.
- atk_3 (partial-domain: ignore severTail, always passthrough {name:=descriptor,none}): exit 1.
- atk_4 (none-branch records descriptor as its own type — wrong on single-word/None): exit 1.
- atk_5 (control-flow-effect: invert the mayCarryType guard to !mayCarryType): exit 1.
- atk_6 (ungrounded-oracle echo: return Inhabited default {name:=[],none}): exit 1.
- atk_7 (partial-domain subtle: correct on true, records empty type some [] on false): exit 1.
- atk_8 (control-flow-effect / vacuity probe: `while true do i:=i+1` divergence before return, targeting the termination "partial" + demonic-choice hole): exit 1 — frozen proof errors 'No goals to be solved'; diverging garbage does NOT verify.

All 6 requested wrong-impl families covered (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) plus the prepatch bug plus a divergence/vacuity probe. NO wrong impl verified, so step-2 has zero candidates — patches={} and no resolve run was needed (correctly, none skipped).

A-LEG / correspondence audit (refinement.md): legs A1=R, A2=R, A3=A-reference+I, A4=R+I, A5=R+I; §C confirms no kind-3 legs and no consumed axioms. The single A-reference (severTail deep model == real str.rsplit(None,1); wsCodes == Python split-whitespace) validated by:
  * axiom_check.py (G-AX): exit 0, 16 boundary + 50000 fuzz inputs sound, wsCodes matches Python over full BMP.
  * conformance_check.py (G-CONF): exit 0, 200032 inputs seed=9230, 0 disagreements.
  * INDEPENDENT spot-check against genuine CPython builtins: real str.rsplit(None,1) == fresh transliteration of severTail on all discriminating cases incl. 'dict(str, str) opc_meta' -> ('dict(str, str)','opc_meta'); BMP classifier mismatch count = 0. Not a rigged echo.

The spec is a total functional-equality postcondition over a frozen pure model, so verify => correct is genuinely enforced. No falsification found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for the modeled callee severTail/resolveParam vs the real repo behaviour (post-patch DocFieldTransformer.transform separation, sphinx/util/docfields.py:299-307; callee str.rsplit(None,1)).

Spec-region integrity: swebench_unified.markers.same_spec(Solution, Solution) = True; same_spec(Solution, Solution_prepatch) = True (prepatch shares the frozen spec view and fails via impl, as intended for G-DIFF). Spec view elides impl/proof cleanly; no leakage in the abstract comments.

Model mapping: descriptor=fieldarg:str -> List Char; mayCarryType=typedesc.is_typed:bool -> Bool; severTail models str.rsplit(None,1) with severTail=some(t,a) <-> rsplit yields 2-list [t,a], severTail=none <-> <2 parts. resolveParam records leading part as type + trailing word as name on success, else leaves descriptor untouched with no type. Matches the try/except ValueError/else block exactly.

Independent verification (not merely re-running shipped checks):
1. Classifier: reimplemented isWs from wsCodes and compared against Python str.split() whitespace over the FULL Unicode range 0x0..0x10FFFF (the shipped axiom_check only covers the BMP up to 0x10000). 0 mismatches -- classifier exact everywhere.
2. Deep-model equality: 300,000 independent fuzz inputs (seed 12345, alphabet = all 29 ws code points + ordinary chars + astral/emoji chr(0x1F600), chr(0x10000), U+2028) comparing severTail/resolveParam against the genuine str.rsplit(None,1) 2-tuple/ValueError outcome. 0 divergences.
3. Boundary/leading-whitespace cases hand-checked against real rsplit: '  a b'->('  a','b'), '   a  b  c  '->('   a  b','c'), '\t\ta b'->('\t\ta','b'), '  x   y  '->('  x','y'), '  leadingonly'->none, 'trailingonly   '->none, ''/'   '->none, 'dict(str, str) opc_meta'->('dict(str, str)','opc_meta'). All match. Leading/interior whitespace correctly stays attached to the left part (rsplit maxsplit=1 keeps only the last separator).
4. mayCarryType=false path returns (descriptor, none) unchanged, matching the skipped `if typedesc.is_typed:` block.

The spec is NOT too strong and does not drift: the modeled function agrees with the real post-patch callee on every input tested (300k fuzz + full-BMP-and-beyond classifier + issue's discriminating bracketed-type case), and it is a deep model (no consumed axiom). No diverging input exists. Verdict: FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction audit of the velvet spec view for sphinx-doc__sphinx-9230.

### Verification performed
- Rendered the consumer spec view via swebench_unified.markers.spec_view(Solution.lean, velvet backend). Confirmed only the impl region and prove_correct body are elided; the pure region (wsCodes/isWs/rstripWs/tailWord/beforeTailWord/severTail/resolveParam/ParsedParam), the method signature + 4 ensures clauses, and all doc comments ARE in the spec view.
- Confirmed markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True: the frozen spec region is byte-identical between patched and prepatch files (only the elided impl differs), so the spec itself carries no post/pre-patch discriminator.

GOLD EDIT: split(None,1) -> rsplit(None,1) at sphinx/util/docfields.py:301 = separate a field descriptor on the LAST whitespace run instead of the FIRST, keeping a spaced type expression whole and taking the trailing word as the name.

PUBLIC problem_statement ALREADY PINS THE TARGET SEMANTICS via its worked example: input ':param dict(str, str) opc_meta:', buggy render 'str) opc_meta (dict(str,)' (first-whitespace split), expected 'opc_meta (dict(str,str))' (type kept whole = last-whitespace split, trailing word = name). The desired last-whitespace behavior is fully derivable from the public statement alone; hints_text is empty.

SPEC-VIEW CONTENT vs problem_statement:
- severTail/resolveParam/wsCodes and the doc comments encode exactly this TARGET (post-patch) behavior — separate at the last whitespace, keep spaced type whole, final word = name. A spec necessarily states correct behavior; matching the public example is not leakage.
- The spec view never names the split/rsplit token, never cites the file/line or the diff, and never states the PRE-patch first-whitespace behavior. Pre-patch information is confined to audit-only artifacts outside the consumer view: mapping.md §1 explicitly labels str.split(None,1) 'refinement audit only, not in the consumer spec view'; the first-whitespace variant lives only in Solution_prepatch.lean (G-DIFF) and refinement.md.
- The wsCodes 29-codepoint alphabet and the none/passthrough single-word case are generic Python split-on-None whitespace semantics, not gold-edit-specific disclosures.

CONCLUSION: No spec-view line adds gold-edit-specific information beyond problem_statement. The spec describes the DESIRED behavior any correct fix must achieve, not the specific edit. Consistent with recorded G-LEAK pass (lexical screen: spec view clean).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
