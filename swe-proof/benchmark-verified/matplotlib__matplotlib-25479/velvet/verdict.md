# P2 adversarial audit — matplotlib__matplotlib-25479

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so there is no faithful patch to run through the harness. Both postconditions fully determine the output: registeredColormap pins ALL three modeled fields (ensures out.name = name; out.extendStyle = cmap.extendStyle; out.lookupTable = cmap.lookupTable) and colormapsEqual pins out = colormapEqSpec a b exactly. The Colormap structure carries exactly {name, extendStyle, lookupTable}, so there is no behavioral slack for a verifying-yet-wrong impl to hide in.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,7 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
-    let mut stored := cmap
-    if stored.name ≠ name then
-      stored := { stored with name := name }
-    return stored
+    return cmap
     -- impl-end
 
 prove_correct registeredColormap by
@@ -86,8 +79,6 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
     return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
     -- impl-end
 
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,7 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
-    let mut stored := cmap
-    if stored.name ≠ name then
-      stored := { stored with name := name }
-    return stored
+    return { cmap with name := name, extendStyle := !cmap.extendStyle }
     -- impl-end
 
 prove_correct registeredColormap by
@@ -86,8 +79,6 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
     return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
     -- impl-end
 
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,14 +65,7 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
-    let mut stored := cmap
-    if stored.name ≠ name then
-      stored := { stored with name := name }
-    return stored
+    return { cmap with name := name, lookupTable := [] }
     -- impl-end
 
 prove_correct registeredColormap by
@@ -86,8 +79,6 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
     return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
     -- impl-end
 
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,13 +65,11 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
     let mut stored := cmap
     if stored.name ≠ name then
       stored := { stored with name := name }
+    else
+      stored := { stored with name := name ++ "!" }
     return stored
     -- impl-end
 
@@ -86,8 +84,6 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
     return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
     -- impl-end
 
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,6 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
     let mut stored := cmap
     if stored.name ≠ name then
       stored := { stored with name := name }
@@ -86,9 +82,7 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
-    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
+    return (decide (a.name = b.name) && decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
     -- impl-end
 
 prove_correct colormapsEqual by
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,6 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
     let mut stored := cmap
     if stored.name ≠ name then
       stored := { stored with name := name }
@@ -86,9 +82,7 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
-    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
+    return decide (a.extendStyle = b.extendStyle)
     -- impl-end
 
 prove_correct colormapsEqual by
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,6 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
     let mut stored := cmap
     if stored.name ≠ name then
       stored := { stored with name := name }
@@ -86,9 +82,7 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
-    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
+    return true
     -- impl-end
 
 prove_correct colormapsEqual by
```

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,6 @@
   ensures out.lookupTable = cmap.lookupTable
   do
     -- impl-start
-    -- Take the colormap to be stored (a content copy, identity on the modeled
-    -- fields). When the colormap still advertises a name other than the chosen
-    -- registration name, update its advertised name to the registration name so
-    -- the two agree; its end-style and colour lookup table are left untouched.
     let mut stored := cmap
     if stored.name ≠ name then
       stored := { stored with name := name }
@@ -86,9 +82,7 @@
   ensures out = colormapEqSpec a b
   do
     -- impl-start
-    -- The same colormap value iff the end-styles agree and the colour lookup
-    -- tables agree; the advertised names do not enter the comparison.
-    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
+    return ((decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable)) || decide (a.name = b.name))
     -- impl-end
 
 prove_correct colormapsEqual by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model reference. Two independent behaviours are
-- modeled here, each as a pure decision over a colormap's own observable fields:
-- (1) which name a colormap carries once it has been stored under a chosen
-- registration name, and (2) when two colormaps are considered the same value.
-- Both are total functions of the structure's fields (name, the extend style,
-- and the color lookup table); there is no foreign callee whose contract the
-- proof assumes and none that is deep-modeled. See refinement.md §C / mapping.md
-- §3 (there is no `axiom` declaration and no A-reference).
-- axioms-end

-- pure-start
/- The observable state of a colormap that the modeled behaviours depend on:
   the human-readable `name` it advertises, the `extendStyle` flag that records
   whether its out-of-range ends are drawn specially, and the `lookupTable` of
   per-sample colour rows it resolves values through (each row a fixed-width
   tuple of integer colour components). Only the fields the modeled behaviours
   read or write are carried; everything else about a colormap is irrelevant
   here and omitted (mapping.md §2). -/
structure Colormap where
  name : String
  extendStyle : Bool
  lookupTable : List (List Int)
deriving DecidableEq, Inhabited, Repr

/- Value-equality of two colormaps: they advertise the same out-of-range
   end-style AND resolve values through the same colour lookup table. A
   colormap's advertised name is metadata that does NOT participate — two
   colormaps that differ only in name still resolve every value identically and
   are therefore the same colormap value. -/
def colormapEqSpec (a b : Colormap) : Bool :=
  decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable)
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the inputs are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the methods below)
-- post-conditions-end

/- The colormap that ends up stored under a chosen registration name.

   Desired behaviour: a colormap may be stored for future lookup under a name
   chosen at storage time that differs from the name the colormap object itself
   advertises. The stored colormap must advertise the name it was stored under —
   otherwise a later lookup that consults the stored colormap's own advertised
   name would disagree with the name it is reachable by. Storing is otherwise
   content-preserving: it keeps the colormap's end-style and colour lookup table
   exactly. `cmap` is the colormap being stored; it is a read-only input (not
   `mut`) and is never altered in place (directive 5) — the result is the stored
   colormap. `name` is the chosen registration name. -/
method registeredColormap (cmap : Colormap) (name : String) return (out : Colormap)
  ensures out.name = name
  ensures out.extendStyle = cmap.extendStyle
  ensures out.lookupTable = cmap.lookupTable
  do
    -- impl-start
    return { cmap with name := name }
    -- impl-end

prove_correct registeredColormap by
  loom_solve

/- Whether two colormaps are the same colormap value (see `colormapEqSpec`).
   Both colormaps are read-only inputs. Desired behaviour: the verdict turns on
   the end-style and the colour lookup table only; the advertised names are
   ignored, so a colormap and a renamed duplicate of it compare equal. -/
method colormapsEqual (a : Colormap) (b : Colormap) return (out : Bool)
  ensures out = colormapEqSpec a b
  do
    -- impl-start
    -- The same colormap value iff the end-styles agree and the colour lookup
    -- tables agree; the advertised names do not enter the comparison.
    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
    -- impl-end

prove_correct colormapsEqual by
  loom_solve
  simp_all [colormapEqSpec]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 files (pc + atk1..atk8) confirmed same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language, editing ONLY the impl regions (axioms/pure/pre/post byte-identical).

VERIFY COMMAND: bash scripts/lean_verify.sh <f>.lean  (run concurrently, <=4 at a time).

### Results
- pc.lean (positive control: reg unconditionally stamps `{cmap with name := name}`, eq gold-literal) -> exit 0 VERIFIES. [Note: an earlier pc using `return colormapEqSpec a b` for eq failed with 'No goals to be solved' — a proof-SCRIPT artifact from the trailing `simp_all [colormapEqSpec]`, not a spec fault; replaced with the field-conjunction gold body which verifies clean.]
- atk1 (partial-domain, == prepatch_1: reg `return cmap`) -> exit 1 FAIL: unsolved `cmap.name = name`.
- atk2 (control-flow-effect: reg flips extendStyle) -> exit 1 FAIL: unsolved `(!cmap.extendStyle) = cmap.extendStyle`.
- atk3 (content-drop: reg empties lookupTable) -> exit 1 FAIL: unsolved `[] = cmap.lookupTable`.
- atk4 (boundary: reg mangles name `name ++ "!"` on the advertised==reg branch) -> exit 1 FAIL: unsolved `name ++ "!" = name` under `¬cmap.name ≠ name`.
- atk5 (partial-domain, == prepatch_2: eq re-adds `decide (a.name = b.name)` conjunct) -> exit 1 FAIL: name-conjunct residual vs colormapEqSpec.
- atk6 (partial-domain: eq drops the lut conjunct) -> exit 1 FAIL: unsolved `a.extendStyle = b.extendStyle → a.lookupTable = b.lookupTable`.
- atk7 (ungrounded-oracle echo: eq `return true`) -> exit 1 FAIL: unsolved `a.extendStyle = b.extendStyle ∧ a.lookupTable = b.lookupTable`.
- atk8 (boundary/OR-echo: eq ORs in name equality) -> exit 1 FAIL: unsolved `a.name = b.name → a.extendStyle = b.extendStyle ∧ a.lookupTable = b.lookupTable`.

8 distinct same-spec wrong impls across all required families (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo), plus both named prepatch bugs re-encoded (atk1==prepatch_1, atk5==prepatch_2). None verified => no materialized patch / resolve run was applicable (resolve only fires for a verifying wrong impl). prepatch_reproduced=true (atk1/atk5 reproduce the recorded prepatch_1/prepatch_2 failures at the same goals).

REFINEMENT AUDIT (A-leg focus): Solution.lean has 0 `axiom` decls, 0 `sorry`/`admit`; meta.json records axioms=[] and deep_model_references=[] => G-AX vacuous, NO A-legs to audit (A-leg concern vacuously satisfied). refinement.md legs A1-A4 (register site) and B1-B5 (__eq__ site) are all R or I — no kind-3 (inexpressible-changed-op). Model↔callee correspondence verified against patch.diff: registeredColormap↔ColormapRegistry.register (cm.py:153 name-stamping hunk), colormapsEqual↔Colormap.__eq__ (colors.py:776, drops the `self.name != other.name` disjunct), colormapEqSpec↔patched __eq__ body. B2 isinstance guard correctly modeled away (both F2P operands are Colormap); B4 np.array_equal↔`=` on List (List Int) including size-mismatch path. Correspondence holds.

VERDICT: SOUND. verify⇒correct holds — both postconditions completely determine the output, leaving no room for a verifying wrong impl; all 8 adversarial same-spec attacks were fully verified (all FAIL) and the positive control verifies.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so there is no faithful patch to run through the harness. Both postconditions fully determine the output: registeredColormap pins ALL three modeled fields (ensures out.name = name; out.extendStyle = cmap.extendStyle; out.lookupTable = cmap.lookupTable) and colormapsEqual pins out = colormapEqSpec a b exactly. The Colormap structure carries exactly {name, extendStyle, lookupTable}, so there is no behavioral slack for a verifying-yet-wrong impl to hide in.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model reference. Two independent behaviours are
-- modeled here, each as a pure decision over a colormap's own observable fields:
-- (1) which name a colormap carries once it has been stored under a chosen
-- registration name, and (2) when two colormaps are considered the same value.
-- Both are total functions of the structure's fields (name, the extend style,
-- and the color lookup table); there is no foreign callee whose contract the
-- proof assumes and none that is deep-modeled. See refinement.md §C / mapping.md
-- §3 (there is no `axiom` declaration and no A-reference).
-- axioms-end

-- pure-start
/- The observable state of a colormap that the modeled behaviours depend on:
   the human-readable `name` it advertises, the `extendStyle` flag that records
   whether its out-of-range ends are drawn specially, and the `lookupTable` of
   per-sample colour rows it resolves values through (each row a fixed-width
   tuple of integer colour components). Only the fields the modeled behaviours
   read or write are carried; everything else about a colormap is irrelevant
   here and omitted (mapping.md §2). -/
structure Colormap where
  name : String
  extendStyle : Bool
  lookupTable : List (List Int)
deriving DecidableEq, Inhabited, Repr

/- Value-equality of two colormaps: they advertise the same out-of-range
   end-style AND resolve values through the same colour lookup table. A
   colormap's advertised name is metadata that does NOT participate — two
   colormaps that differ only in name still resolve every value identically and
   are therefore the same colormap value. -/
def colormapEqSpec (a b : Colormap) : Bool :=
  decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable)
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the inputs are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the inline `ensures` clauses on the methods below)
-- post-conditions-end

/- The colormap that ends up stored under a chosen registration name.

   Desired behaviour: a colormap may be stored for future lookup under a name
   chosen at storage time that differs from the name the colormap object itself
   advertises. The stored colormap must advertise the name it was stored under —
   otherwise a later lookup that consults the stored colormap's own advertised
   name would disagree with the name it is reachable by. Storing is otherwise
   content-preserving: it keeps the colormap's end-style and colour lookup table
   exactly. `cmap` is the colormap being stored; it is a read-only input (not
   `mut`) and is never altered in place (directive 5) — the result is the stored
   colormap. `name` is the chosen registration name. -/
method registeredColormap (cmap : Colormap) (name : String) return (out : Colormap)
  ensures out.name = name
  ensures out.extendStyle = cmap.extendStyle
  ensures out.lookupTable = cmap.lookupTable
  do
    -- impl-start
    return { cmap with name := name }
    -- impl-end

prove_correct registeredColormap by
  loom_solve

/- Whether two colormaps are the same colormap value (see `colormapEqSpec`).
   Both colormaps are read-only inputs. Desired behaviour: the verdict turns on
   the end-style and the colour lookup table only; the advertised names are
   ignored, so a colormap and a renamed duplicate of it compare equal. -/
method colormapsEqual (a : Colormap) (b : Colormap) return (out : Bool)
  ensures out = colormapEqSpec a b
  do
    -- impl-start
    -- The same colormap value iff the end-styles agree and the colour lookup
    -- tables agree; the advertised names do not enter the comparison.
    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))
    -- impl-end

prove_correct colormapsEqual by
  loom_solve
  simp_all [colormapEqSpec]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 files (pc + atk1..atk8) confirmed same_spec=True via swebench_unified.markers.same_spec with get_backend('velvet').language, editing ONLY the impl regions (axioms/pure/pre/post byte-identical).

VERIFY COMMAND: bash scripts/lean_verify.sh <f>.lean  (run concurrently, <=4 at a time).

### Results
- pc.lean (positive control: reg unconditionally stamps `{cmap with name := name}`, eq gold-literal) -> exit 0 VERIFIES. [Note: an earlier pc using `return colormapEqSpec a b` for eq failed with 'No goals to be solved' — a proof-SCRIPT artifact from the trailing `simp_all [colormapEqSpec]`, not a spec fault; replaced with the field-conjunction gold body which verifies clean.]
- atk1 (partial-domain, == prepatch_1: reg `return cmap`) -> exit 1 FAIL: unsolved `cmap.name = name`.
- atk2 (control-flow-effect: reg flips extendStyle) -> exit 1 FAIL: unsolved `(!cmap.extendStyle) = cmap.extendStyle`.
- atk3 (content-drop: reg empties lookupTable) -> exit 1 FAIL: unsolved `[] = cmap.lookupTable`.
- atk4 (boundary: reg mangles name `name ++ "!"` on the advertised==reg branch) -> exit 1 FAIL: unsolved `name ++ "!" = name` under `¬cmap.name ≠ name`.
- atk5 (partial-domain, == prepatch_2: eq re-adds `decide (a.name = b.name)` conjunct) -> exit 1 FAIL: name-conjunct residual vs colormapEqSpec.
- atk6 (partial-domain: eq drops the lut conjunct) -> exit 1 FAIL: unsolved `a.extendStyle = b.extendStyle → a.lookupTable = b.lookupTable`.
- atk7 (ungrounded-oracle echo: eq `return true`) -> exit 1 FAIL: unsolved `a.extendStyle = b.extendStyle ∧ a.lookupTable = b.lookupTable`.
- atk8 (boundary/OR-echo: eq ORs in name equality) -> exit 1 FAIL: unsolved `a.name = b.name → a.extendStyle = b.extendStyle ∧ a.lookupTable = b.lookupTable`.

8 distinct same-spec wrong impls across all required families (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo), plus both named prepatch bugs re-encoded (atk1==prepatch_1, atk5==prepatch_2). None verified => no materialized patch / resolve run was applicable (resolve only fires for a verifying wrong impl). prepatch_reproduced=true (atk1/atk5 reproduce the recorded prepatch_1/prepatch_2 failures at the same goals).

REFINEMENT AUDIT (A-leg focus): Solution.lean has 0 `axiom` decls, 0 `sorry`/`admit`; meta.json records axioms=[] and deep_model_references=[] => G-AX vacuous, NO A-legs to audit (A-leg concern vacuously satisfied). refinement.md legs A1-A4 (register site) and B1-B5 (__eq__ site) are all R or I — no kind-3 (inexpressible-changed-op). Model↔callee correspondence verified against patch.diff: registeredColormap↔ColormapRegistry.register (cm.py:153 name-stamping hunk), colormapsEqual↔Colormap.__eq__ (colors.py:776, drops the `self.name != other.name` disjunct), colormapEqSpec↔patched __eq__ body. B2 isinstance guard correctly modeled away (both F2P operands are Colormap); B4 np.array_equal↔`=` on List (List Int) including size-mismatch path. Correspondence holds.

VERDICT: SOUND. verify⇒correct holds — both postconditions completely determine the output, leaving no room for a verifying wrong impl; all 8 adversarial same-spec attacks were fully verified (all FAIL) and the positive control verifies.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the two modeled functions in Solution.lean for matplotlib__matplotlib-25479 (velvet). Both check out against the REAL patched repo callees.

SITE B — colormapsEqual ↔ patched Colormap.__eq__ (lib/matplotlib/colors.py:776). Spec: colormapEqSpec a b = (a.extendStyle = b.extendStyle) && (a.lookupTable = b.lookupTable), name-independent. I ran the patched __eq__ against this spec on the discriminating cases (same content + different name -> equal; different extend -> unequal; different lut -> unequal; different lut size (cm_copy._lut[:10,:]) -> unequal; identical -> equal; diff name + diff extend -> unequal). All 6 agree. np.array_equal <-> Lean '=' on List (List Int) is exact (equal shape+elements). FAITHFUL.

SITE A — registeredColormap ↔ patched register (lib/matplotlib/cm.py:113, body 153-156). Spec: ensures out.name = name, extendStyle/lookupTable preserved. I simulated the patched storage path (self._cmaps[name]=cmap.copy(); if stored.name!=name: stored.name=name) and compared the stored copy's .name to the spec's out.name. On non-empty registration names (advertised != reg, advertised == reg) it agrees exactly, including content preservation.

ONE APPARENT DIVERGENCE, RESOLVED AS A DOCUMENTED BOUNDARY: passing an empty name argument. Real register first does `name = name or cmap.name`, so an empty arg resolves to the colormap's advertised name and the stored .name becomes cmap.name (e.g. 'builtin'), NOT ''. The Lean spec, read with `name` = the raw argument, would claim out.name = '' — a disagreement. However mapping.md §A1 explicitly binds the Lean `name` parameter to the RESOLVED name ('the resolved name'), i.e. `name or cmap.name`, not the raw argument. Under that binding there is no divergence, and the pinned conformance_check.py honors it (reg = rng.choice(names) or 'n' — never an empty resolved name). This is a legitimate abstraction of an argument-defaulting step, not spec drift. Not a genuine counterexample.

Corroboration: spec region byte-identical across Solution.lean and both prepatch variants (swebench_unified.markers.same_spec = True for both); Solution.lean verifies cleanly under total correctness via lean_verify.sh (exit 0); recorded G-CONF pass (R/I shadows agree with patched repo on 100009 inputs, seed 25479, 0 disagreements); meta.json declares no axioms and no deep-model references (nothing over-abstracted / no vacuous-callee escape). Total-correctness semantics closes the divergent-impl vacuity hole. No spec-too-strong defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Dispositioned relaxed_leakage bundle (meta.json relaxed_leakage=true, G-LEAK=relaxed, RELAXED_LEAKAGE.md present). Independently re-verified per the G-PANEL-3 recording convention rather than rubber-stamping.

Gold patch = two hunks: (1) cm.py register stamps the registration name onto the stored copy; (2) colors.py __eq__ drops the `self.name != other.name` disjunct -> name-independent value-equality. The public problem_statement describes ONLY hunk 1 (registered-name vs colormap.name confusion at lookup, ValueError). Confirmed the equality-site discriminator is absent from problem_statement (tokens equal/__eq__/==/compare/comparison/colorbar_extend/_lut all absent; only 'lut' hit is inside an unrelated pyplot traceback) and absent from hints_text.

Spec view discloses two behaviours: registeredColormap (name stamping, fully derivable from PS) and colormapsEqual/colormapEqSpec (name-independent equality, NOT derivable from PS). The second is the known relaxed disclosure -- the leak is in the tested behaviour itself, established unavoidable: FAIL_TO_PASS tests (test_colormap_equals flips assert cm_copy!=cmap -> ==, test_set_cmap_mismatched_name asserts cmap_returned==cmap) require a faithful spec to pin name-independent equality; prepatch_2 re-adds the name conjunct and fails at `ensures out = colormapEqSpec a b`. No PS-only derivation of the equality obligation exists.

Re-verified disposition validity: (a) core sound -- Solution.lean verifies under loom.semantics.termination "total" (lean_verify exit 0), same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True, and meta.json shows G-VERIFY/G-DIFF/G-EQ/G-CONF/G-MUT/G-RESOLVE all pass; (b) no NEW leaking line beyond the dispositioned name-independent-equality facet -- the spec view names no patched file (cm.py/colors.py), no symbol (register/__eq__), no attribute (colorbar_extend/_lut), and no edit mechanics; extendStyle/lookupTable are de-narrated renames; (c) the mechanical lexical G-LEAK screen passes (semantic leak only, as the policy expects). No leak beyond the dispositioned facet found; unavoidability argument re-confirmed and not refuted. Honest recording is NO-LEAKAGE (equivalently pass).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
