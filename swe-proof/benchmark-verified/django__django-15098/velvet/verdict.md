# P2 adversarial audit — django__django-15098

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_0a.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. Every attack (all same_spec=True) is rejected at the discriminating postcondition clause `ensures out = pathLanguage path strict`. Since no verifying-but-wrong impl exists, step-2 resolve runs are vacuous (there is no faithful patch to materialize).
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -170,12 +170,11 @@
     while i < path.length
       -- invariants-start
       invariant 0 ≤ i ∧ i ≤ path.length
-      invariant st = (path.take i).foldl (lstep 2) initLS
+      invariant st = (path.take i).foldl (lstep 1) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
-      st := lstep 2 st path[i]!
+      st := lstep 1 st path[i]!
       i := i + 1
     let tag := ldecode st
     let result :| result = (match tag with
@@ -187,5 +186,5 @@
 
 prove_correct resolvePathLanguage by
   loom_solve
-  · rw [foldl_take_succ (lstep 2) initLS path i (by omega), ← invariant_2]
+  · rw [foldl_take_succ (lstep 1) initLS path i (by omega), ← invariant_2]
   · simp_all [pathLanguage, leadingLocaleTag, List.take_length]
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -170,12 +170,11 @@
     while i < path.length
       -- invariants-start
       invariant 0 ≤ i ∧ i ≤ path.length
-      invariant st = (path.take i).foldl (lstep 2) initLS
+      invariant st = (path.take i).foldl (lstep 3) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
-      st := lstep 2 st path[i]!
+      st := lstep 3 st path[i]!
       i := i + 1
     let tag := ldecode st
     let result :| result = (match tag with
@@ -187,5 +186,5 @@
 
 prove_correct resolvePathLanguage by
   loom_solve
-  · rw [foldl_take_succ (lstep 2) initLS path i (by omega), ← invariant_2]
+  · rw [foldl_take_succ (lstep 3) initLS path i (by omega), ← invariant_2]
   · simp_all [pathLanguage, leadingLocaleTag, List.take_length]
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -172,15 +172,12 @@
       invariant 0 ≤ i ∧ i ≤ path.length
       invariant st = (path.take i).foldl (lstep 2) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
       st := lstep 2 st path[i]!
       i := i + 1
     let tag := ldecode st
-    let result :| result = (match tag with
-      | none    => none
-      | some lc => listedLanguage lc strict)
+    let result :| result = none
     return result
     -- impl-end
 end
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -172,7 +172,6 @@
       invariant 0 ≤ i ∧ i ≤ path.length
       invariant st = (path.take i).foldl (lstep 2) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
       st := lstep 2 st path[i]!
@@ -180,7 +179,7 @@
     let tag := ldecode st
     let result :| result = (match tag with
       | none    => none
-      | some lc => listedLanguage lc strict)
+      | some lc => listedLanguage lc true)
     return result
     -- impl-end
 end
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -172,15 +172,12 @@
       invariant 0 ≤ i ∧ i ≤ path.length
       invariant st = (path.take i).foldl (lstep 2) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
       st := lstep 2 st path[i]!
       i := i + 1
     let tag := ldecode st
-    let result :| result = (match tag with
-      | none    => none
-      | some lc => listedLanguage lc strict)
+    let result :| result = listedLanguage path strict
     return result
     -- impl-end
 end
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -166,13 +166,12 @@
   do
     -- impl-start
     let mut st := initLS
-    let mut i := 0
+    let mut i := 1
     while i < path.length
       -- invariants-start
       invariant 0 ≤ i ∧ i ≤ path.length
       invariant st = (path.take i).foldl (lstep 2) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
       st := lstep 2 st path[i]!
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -170,12 +170,11 @@
     while i < path.length
       -- invariants-start
       invariant 0 ≤ i ∧ i ≤ path.length
-      invariant st = (path.take i).foldl (lstep 2) initLS
+      invariant st = (path.take i).foldl (lstep 0) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
-      st := lstep 2 st path[i]!
+      st := lstep 0 st path[i]!
       i := i + 1
     let tag := ldecode st
     let result :| result = (match tag with
@@ -187,5 +186,5 @@
 
 prove_correct resolvePathLanguage by
   loom_solve
-  · rw [foldl_take_succ (lstep 2) initLS path i (by omega), ← invariant_2]
+  · rw [foldl_take_succ (lstep 0) initLS path i (by omega), ← invariant_2]
   · simp_all [pathLanguage, leadingLocaleTag, List.take_length]
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -172,15 +172,12 @@
       invariant 0 ≤ i ∧ i ≤ path.length
       invariant st = (path.take i).foldl (lstep 2) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
       st := lstep 2 st path[i]!
       i := i + 1
     let tag := ldecode st
-    let result :| result = (match tag with
-      | none    => none
-      | some lc => listedLanguage lc strict)
+    let result :| result = tag
     return result
     -- impl-end
 end
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
 /- The resolver that maps a candidate locale tag to the configured language it
@@ -172,15 +172,12 @@
       invariant 0 ≤ i ∧ i ≤ path.length
       invariant st = (path.take i).foldl (lstep 2) initLS
       done_with i = path.length
-      decreasing path.length - i
       -- invariants-end
     do
       st := lstep 2 st path[i]!
       i := i + 1
     let tag := ldecode st
-    let result :| result = (match tag with
-      | none    => none
-      | some lc => listedLanguage lc strict)
+    let result :| result = listedLanguage st.acc strict
     return result
     -- impl-end
 end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0a.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The resolver that maps a candidate locale tag to the configured language it
   stands for. Given the tag carried by a URL path (and whether the lookup is
   strict), it returns the listed language code to activate, or `none` when no
   configured language matches. Its behaviour depends only on the ambient set of
   configured languages and is unaffected by this change; it is modeled as an
   opaque function of (candidate tag, strict flag) — the weakest possible
   contract (no asserted property). Provenance + the per-configuration
   functional-determinism justification: mapping.md / axiom_check.py (G-AX). -/
axiom listedLanguage : List Char → Bool → Option (List Char)
-- axioms-end

-- pure-start
/- A "word" character of a locale tag: an ASCII letter or digit, or underscore. -/
def isWordChar (c : Char) : Bool := c.isAlphanum || c == '_'

/- A subtag separator: the two delimiters a locale tag uses between its
   subtags. -/
def isSubtagSep (c : Char) : Bool := c == '-' || c == '@'

/- A single left-to-right scan over a URL path, recognising the leading locale
   tag it carries.

   * `status` : 0 while still scanning; 1 once the tag is locked in by a
                trailing path separator; 2 once the prefix is rejected; 3 once a
                trailing line-terminator has tentatively closed the tag — this
                only stands if that terminator is the very last character of the
                path (any further character turns it into a rejection);
   * `phase`  : 0 expecting the opening path separator; 1 needing the first
                word character of the primary subtag; 2 inside a word run;
                3 just past a subtag separator, needing a word character;
   * `acc`    : the locale tag accumulated so far (the recognised characters);
   * `segs`   : how many *additional* subtags (beyond the primary one) have been
                accepted. -/
structure LS where
  status : Nat
  phase  : Nat
  acc    : List Char
  segs   : Nat
deriving Inhabited, DecidableEq

/- The scan before any character is consumed. -/
def initLS : LS := ⟨0, 0, [], 0⟩

/- One step of the scan. A locale tag is a primary subtag optionally followed by
   further subtags — each an extra separator plus word run — and a path tag may
   carry up to `maxSegs` such additional subtags (for a language this is its
   script and region, per the public RFC 5646 langtag grammar). The tag is
   recognised only when a path separator, the end of the path, or a single
   trailing line-terminator follows it; reaching the additional-subtag limit and
   then seeing another separator (with no closing path separator) rejects the
   prefix, as does any non-word, non-separator character or a dangling separator.

   A line-terminator seen at the end of a word run closes the tag only
   tentatively (`status 3`): a path that ends right there carries the tag, but
   any further character after that terminator turns the prefix into a rejection
   (the terminator was not actually the last character of the path). -/
def lstep (maxSegs : Nat) (st : LS) (c : Char) : LS :=
  if st.status = 1 ∨ st.status = 2 then st
  else if st.status = 3 then { st with status := 2 }
  else if st.phase = 0 then
    if c = '/' then { st with phase := 1 } else { st with status := 2 }
  else if st.phase = 1 then
    if isWordChar c then { st with phase := 2, acc := st.acc ++ [c] }
    else { st with status := 2 }
  else if st.phase = 2 then
    if isWordChar c then { st with acc := st.acc ++ [c] }
    else if isSubtagSep c then
      if st.segs < maxSegs then { st with phase := 3, acc := st.acc ++ [c] }
      else { st with status := 2 }
    else if c = '/' then { st with status := 1 }
    else if c = '\n' then { st with status := 3 }
    else { st with status := 2 }
  else
    if isWordChar c then { st with phase := 2, acc := st.acc ++ [c], segs := st.segs + 1 }
    else { st with status := 2 }

/- Read the recognised locale tag off a finished scan: a tag locked in by a
   trailing path separator, a word run that ran to the end of the path, or a tag
   closed by a single trailing line-terminator that was the last character
   (`status 3`), is the accumulated characters; any rejected or never-started
   scan yields none. -/
def ldecode (st : LS) : Option (List Char) :=
  if st.status = 1 then some st.acc
  else if st.status = 2 then none
  else if st.status = 3 then some st.acc
  else if st.phase = 2 then some st.acc
  else none

/- The leading locale tag a URL path carries, allowing up to `maxSegs`
   additional subtags after the primary one: fold `lstep` over the path, then
   decode. `none` when the path has no recognisable locale tag. -/
def leadingLocaleTag (maxSegs : Nat) (path : List Char) : Option (List Char) :=
  ldecode (path.foldl (lstep maxSegs) initLS)

/- The language a URL path resolves to: take the leading locale tag the path
   carries (allowing the primary subtag plus up to two additional subtags — a
   script and a region — per the public langtag grammar), then resolve that tag
   to a configured language. A path with no recognisable locale tag, or whose
   tag resolves to no configured language, yields none. -/
noncomputable def pathLanguage (path : List Char) (strict : Bool) : Option (List Char) :=
  match leadingLocaleTag 2 path with
  | none    => none
  | some lc => listedLanguage lc strict
-- pure-end

/- The non-deterministic resolver choice below is well-posed: for any target
   value `v` the set of values equal to `v` is non-empty (`v` itself). This
   supplies the constructive existence witness so the `:|` choice elaborates. It
   does NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate allows — here exactly the named
   resolver result. -/
noncomputable instance findableEqOpt (v : Option (List Char)) (n : Lean.Name) :
    Findable (fun e : Option (List Char) => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element — the single fact the loop body leaves
   for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a URL path to the language code that should be activated for it.

   The path is scanned for the locale tag it begins with — a primary subtag
   followed by up to two further '-'/'@'-separated subtags (the script and
   region a locale may carry, per the public RFC 5646 langtag grammar) — and
   that tag is resolved to a configured language. A path carrying no recognised
   locale tag, or whose tag matches no configured language, resolves to none.

   Modeled domain: the path ranges over the ASCII plane (every code point
   < 128). The langtag grammar, every configured language code, and every
   graded input are ASCII; outside ASCII the word-character classification of
   the real matcher is library-specific and is not claimed (mapping.md §2,
   §3.1 domain note).

   Both inputs are read-only — neither `path` nor `strict` is declared `mut`
   (directive 5): the scan only reads the path characters and the strict flag,
   and the resolver reads the recognised tag. -/
noncomputable section
method resolvePathLanguage (path : List Char) (strict : Bool)
    return (out : Option (List Char))
  require ∀ c ∈ path, c.toNat < 128
  ensures out = pathLanguage path strict
  do
    -- impl-start
    let result :| result = pathLanguage path strict
    return result
    -- impl-end
end

prove_correct resolvePathLanguage by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: The frozen postcondition is an EXACT equality `out = pathLanguage path strict`, where `pathLanguage path strict = match leadingLocaleTag 2 path with | none => none | some lc => listedLanguage lc strict`. `leadingLocaleTag 2 / lstep / ldecode` is a fully CONCRETE deep automaton model of the changed regex (the A-reference, G-CONF-validated); the ONLY opaque symbol is the axiom `listedLanguage` (the unchanged callee get_supported_language_variant, G-AX-validated, weakest contract). Because the postcondition is exact equality with a concrete RHS (mod the single opaque callee that is pinned to the impl-computed decoded tag + real strict flag), any verifying impl must be behaviourally identical to gold on all inputs — leaving no room for a verifying-but-wrong impl.

SAME-SPEC CHECK: all 11 candidate files (atk_0, atk_0a, atk_1..atk_9) return same_spec=True vs the bundle Solution.lean (velvet backend). Verified via swebench_unified.markers.same_spec. Edits are confined to the impl region (lines 168-183) and the elided prove_correct body — both outside the spec view.

VERIFY COMMANDS: `bash scripts/lean_verify.sh <file>.lean` run concurrently in batches of <=4 background jobs.

### Results
- POSITIVE CONTROL atk_0a (direct compute: `result :| result = pathLanguage path strict; return result`, proof `loom_solve`): same_spec=True, verify EXIT 0. Spec is satisfiable/non-vacuous. (atk_0/atk_0b were proof-engineering variants of the same impl that failed to close the trivial goal — 'No goals to be solved' / leftover goal — NOT spec failures; atk_0a is the clean positive control.)
- bundle Solution.lean (gold): EXIT 0. Solution_prepatch.lean: EXIT 1, rejected at `ensures_1` with goal `ldecode(foldl (lstep 1)) ... = ldecode(foldl (lstep 2)) ...` — the F2P two-additional-subtag (/en-latn-us/) discriminator. Prepatch reproduced.
- atk_1 lstep 1 (prepatch bug, partial-domain under-match): EXIT 1, goal `lstep 1 fold = lstep 2 fold`.
- atk_2 lstep 3 (boundary over-match, admits 3 extra subtags): EXIT 1, same maxSegs discriminator.
- atk_3 result:=none always (control-flow-effect / constant): EXIT 1, `none = match ldecode ...`.
- atk_4 flag-pinning `listedLanguage lc true` (ignores strict): EXIT 1, `listedLanguage lc true = ... listedLanguage lc strict` — strict is load-bearing.
- atk_5 ungrounded-oracle echo `listedLanguage path strict` (raw path, skip decode): EXIT 1, `listedLanguage path strict = match ldecode st_1 ...` — callee cannot be echoed on wrong arg.
- atk_6 off-by-one loop start i=1 (skips leading '/'): EXIT 1 at ensures_1.
- atk_7 lstep 0 (primary subtag only, boundary): EXIT 1, same discriminator.
- atk_8 echo tag `result = tag = ldecode st` (skip resolve): EXIT 1, `ldecode st_1 = match ldecode st_1 | some lc => listedLanguage lc strict` — none-gate + resolve mandatory.
- atk_9 `listedLanguage st.acc strict` (drop the ldecode none-gate, resolve raw acc): EXIT 1 — the none-gate is mandatory.

STEP-2 RESOLVE: no verifying wrong impl exists, so there is no faithful patch to materialize and run through run_resolve. verify => correct is NOT falsified for this bundle.

REFINEMENT.MD AUDIT (no kind-3): §A legs A1/A2/A5 = R (str<->List Char, bool<->Bool, Option<->str/None type refinements); A3 = A-reference + I — the single genuinely-changed op (regex subtag bound `?`->`{0,2}`) is modeled DEEPLY/CONCRETELY as leadingLocaleTag 2 (lstep/ldecode fold + verified while-loop), NOT behind an axiom about the function-under-change; its correspondence to the real patched language_code_prefix_re.match(path)[1] is validated by G-CONF (meta.json: pass, 100040 inputs, 0 disagreements, seed 15098). A4 = A-consumed + R — the lone consumed axiom `listedLanguage` <-> the UNCHANGED callee get_supported_language_variant, opaque/weakest-contract, validated by G-AX (meta.json: pass, deterministic total-dichotomy, 5102 obs). Every leg is R / A-consumed / A-reference / I; NO kind-3. The A-legs' correspondence to the real callees holds (G-CONF + G-AX both pass in-container per meta.json).

HISTORY: verdict.md records an earlier faithfulness (G-PANEL) TOO-STRONG defect on trailing-single-newline paths (/en\n) that was subsequently refined (status-3 line-terminator handling) and re-accepted. That is a G-PANEL faithfulness matter, not a G-EQ (verify-implies-correct) break; the current frozen spec models the `$`-before-trailing-newline case and G-CONF passes. It does not affect this G-EQ verdict.

VERDICT: SOUND. >=9 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, flag-pin, off-by-one) all verified and all rejected; positive control verifies; prepatch reproduced; no faithful patch of a verifying wrong impl exists to break the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_0a.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. Every attack (all same_spec=True) is rejected at the discriminating postcondition clause `ensures out = pathLanguage path strict`. Since no verifying-but-wrong impl exists, step-2 resolve runs are vacuous (there is no faithful patch to materialize).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0a.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The resolver that maps a candidate locale tag to the configured language it
   stands for. Given the tag carried by a URL path (and whether the lookup is
   strict), it returns the listed language code to activate, or `none` when no
   configured language matches. Its behaviour depends only on the ambient set of
   configured languages and is unaffected by this change; it is modeled as an
   opaque function of (candidate tag, strict flag) — the weakest possible
   contract (no asserted property). Provenance + the per-configuration
   functional-determinism justification: mapping.md / axiom_check.py (G-AX). -/
axiom listedLanguage : List Char → Bool → Option (List Char)
-- axioms-end

-- pure-start
/- A "word" character of a locale tag: an ASCII letter or digit, or underscore. -/
def isWordChar (c : Char) : Bool := c.isAlphanum || c == '_'

/- A subtag separator: the two delimiters a locale tag uses between its
   subtags. -/
def isSubtagSep (c : Char) : Bool := c == '-' || c == '@'

/- A single left-to-right scan over a URL path, recognising the leading locale
   tag it carries.

   * `status` : 0 while still scanning; 1 once the tag is locked in by a
                trailing path separator; 2 once the prefix is rejected; 3 once a
                trailing line-terminator has tentatively closed the tag — this
                only stands if that terminator is the very last character of the
                path (any further character turns it into a rejection);
   * `phase`  : 0 expecting the opening path separator; 1 needing the first
                word character of the primary subtag; 2 inside a word run;
                3 just past a subtag separator, needing a word character;
   * `acc`    : the locale tag accumulated so far (the recognised characters);
   * `segs`   : how many *additional* subtags (beyond the primary one) have been
                accepted. -/
structure LS where
  status : Nat
  phase  : Nat
  acc    : List Char
  segs   : Nat
deriving Inhabited, DecidableEq

/- The scan before any character is consumed. -/
def initLS : LS := ⟨0, 0, [], 0⟩

/- One step of the scan. A locale tag is a primary subtag optionally followed by
   further subtags — each an extra separator plus word run — and a path tag may
   carry up to `maxSegs` such additional subtags (for a language this is its
   script and region, per the public RFC 5646 langtag grammar). The tag is
   recognised only when a path separator, the end of the path, or a single
   trailing line-terminator follows it; reaching the additional-subtag limit and
   then seeing another separator (with no closing path separator) rejects the
   prefix, as does any non-word, non-separator character or a dangling separator.

   A line-terminator seen at the end of a word run closes the tag only
   tentatively (`status 3`): a path that ends right there carries the tag, but
   any further character after that terminator turns the prefix into a rejection
   (the terminator was not actually the last character of the path). -/
def lstep (maxSegs : Nat) (st : LS) (c : Char) : LS :=
  if st.status = 1 ∨ st.status = 2 then st
  else if st.status = 3 then { st with status := 2 }
  else if st.phase = 0 then
    if c = '/' then { st with phase := 1 } else { st with status := 2 }
  else if st.phase = 1 then
    if isWordChar c then { st with phase := 2, acc := st.acc ++ [c] }
    else { st with status := 2 }
  else if st.phase = 2 then
    if isWordChar c then { st with acc := st.acc ++ [c] }
    else if isSubtagSep c then
      if st.segs < maxSegs then { st with phase := 3, acc := st.acc ++ [c] }
      else { st with status := 2 }
    else if c = '/' then { st with status := 1 }
    else if c = '\n' then { st with status := 3 }
    else { st with status := 2 }
  else
    if isWordChar c then { st with phase := 2, acc := st.acc ++ [c], segs := st.segs + 1 }
    else { st with status := 2 }

/- Read the recognised locale tag off a finished scan: a tag locked in by a
   trailing path separator, a word run that ran to the end of the path, or a tag
   closed by a single trailing line-terminator that was the last character
   (`status 3`), is the accumulated characters; any rejected or never-started
   scan yields none. -/
def ldecode (st : LS) : Option (List Char) :=
  if st.status = 1 then some st.acc
  else if st.status = 2 then none
  else if st.status = 3 then some st.acc
  else if st.phase = 2 then some st.acc
  else none

/- The leading locale tag a URL path carries, allowing up to `maxSegs`
   additional subtags after the primary one: fold `lstep` over the path, then
   decode. `none` when the path has no recognisable locale tag. -/
def leadingLocaleTag (maxSegs : Nat) (path : List Char) : Option (List Char) :=
  ldecode (path.foldl (lstep maxSegs) initLS)

/- The language a URL path resolves to: take the leading locale tag the path
   carries (allowing the primary subtag plus up to two additional subtags — a
   script and a region — per the public langtag grammar), then resolve that tag
   to a configured language. A path with no recognisable locale tag, or whose
   tag resolves to no configured language, yields none. -/
noncomputable def pathLanguage (path : List Char) (strict : Bool) : Option (List Char) :=
  match leadingLocaleTag 2 path with
  | none    => none
  | some lc => listedLanguage lc strict
-- pure-end

/- The non-deterministic resolver choice below is well-posed: for any target
   value `v` the set of values equal to `v` is non-empty (`v` itself). This
   supplies the constructive existence witness so the `:|` choice elaborates. It
   does NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate allows — here exactly the named
   resolver result. -/
noncomputable instance findableEqOpt (v : Option (List Char)) (n : Lean.Name) :
    Findable (fun e : Option (List Char) => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element — the single fact the loop body leaves
   for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a URL path to the language code that should be activated for it.

   The path is scanned for the locale tag it begins with — a primary subtag
   followed by up to two further '-'/'@'-separated subtags (the script and
   region a locale may carry, per the public RFC 5646 langtag grammar) — and
   that tag is resolved to a configured language. A path carrying no recognised
   locale tag, or whose tag matches no configured language, resolves to none.

   Modeled domain: the path ranges over the ASCII plane (every code point
   < 128). The langtag grammar, every configured language code, and every
   graded input are ASCII; outside ASCII the word-character classification of
   the real matcher is library-specific and is not claimed (mapping.md §2,
   §3.1 domain note).

   Both inputs are read-only — neither `path` nor `strict` is declared `mut`
   (directive 5): the scan only reads the path characters and the strict flag,
   and the resolver reads the recognised tag. -/
noncomputable section
method resolvePathLanguage (path : List Char) (strict : Bool)
    return (out : Option (List Char))
  require ∀ c ∈ path, c.toNat < 128
  ensures out = pathLanguage path strict
  do
    -- impl-start
    let result :| result = pathLanguage path strict
    return result
    -- impl-end
end

prove_correct resolvePathLanguage by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: The frozen postcondition is an EXACT equality `out = pathLanguage path strict`, where `pathLanguage path strict = match leadingLocaleTag 2 path with | none => none | some lc => listedLanguage lc strict`. `leadingLocaleTag 2 / lstep / ldecode` is a fully CONCRETE deep automaton model of the changed regex (the A-reference, G-CONF-validated); the ONLY opaque symbol is the axiom `listedLanguage` (the unchanged callee get_supported_language_variant, G-AX-validated, weakest contract). Because the postcondition is exact equality with a concrete RHS (mod the single opaque callee that is pinned to the impl-computed decoded tag + real strict flag), any verifying impl must be behaviourally identical to gold on all inputs — leaving no room for a verifying-but-wrong impl.

SAME-SPEC CHECK: all 11 candidate files (atk_0, atk_0a, atk_1..atk_9) return same_spec=True vs the bundle Solution.lean (velvet backend). Verified via swebench_unified.markers.same_spec. Edits are confined to the impl region (lines 168-183) and the elided prove_correct body — both outside the spec view.

VERIFY COMMANDS: `bash scripts/lean_verify.sh <file>.lean` run concurrently in batches of <=4 background jobs.

### Results
- POSITIVE CONTROL atk_0a (direct compute: `result :| result = pathLanguage path strict; return result`, proof `loom_solve`): same_spec=True, verify EXIT 0. Spec is satisfiable/non-vacuous. (atk_0/atk_0b were proof-engineering variants of the same impl that failed to close the trivial goal — 'No goals to be solved' / leftover goal — NOT spec failures; atk_0a is the clean positive control.)
- bundle Solution.lean (gold): EXIT 0. Solution_prepatch.lean: EXIT 1, rejected at `ensures_1` with goal `ldecode(foldl (lstep 1)) ... = ldecode(foldl (lstep 2)) ...` — the F2P two-additional-subtag (/en-latn-us/) discriminator. Prepatch reproduced.
- atk_1 lstep 1 (prepatch bug, partial-domain under-match): EXIT 1, goal `lstep 1 fold = lstep 2 fold`.
- atk_2 lstep 3 (boundary over-match, admits 3 extra subtags): EXIT 1, same maxSegs discriminator.
- atk_3 result:=none always (control-flow-effect / constant): EXIT 1, `none = match ldecode ...`.
- atk_4 flag-pinning `listedLanguage lc true` (ignores strict): EXIT 1, `listedLanguage lc true = ... listedLanguage lc strict` — strict is load-bearing.
- atk_5 ungrounded-oracle echo `listedLanguage path strict` (raw path, skip decode): EXIT 1, `listedLanguage path strict = match ldecode st_1 ...` — callee cannot be echoed on wrong arg.
- atk_6 off-by-one loop start i=1 (skips leading '/'): EXIT 1 at ensures_1.
- atk_7 lstep 0 (primary subtag only, boundary): EXIT 1, same discriminator.
- atk_8 echo tag `result = tag = ldecode st` (skip resolve): EXIT 1, `ldecode st_1 = match ldecode st_1 | some lc => listedLanguage lc strict` — none-gate + resolve mandatory.
- atk_9 `listedLanguage st.acc strict` (drop the ldecode none-gate, resolve raw acc): EXIT 1 — the none-gate is mandatory.

STEP-2 RESOLVE: no verifying wrong impl exists, so there is no faithful patch to materialize and run through run_resolve. verify => correct is NOT falsified for this bundle.

REFINEMENT.MD AUDIT (no kind-3): §A legs A1/A2/A5 = R (str<->List Char, bool<->Bool, Option<->str/None type refinements); A3 = A-reference + I — the single genuinely-changed op (regex subtag bound `?`->`{0,2}`) is modeled DEEPLY/CONCRETELY as leadingLocaleTag 2 (lstep/ldecode fold + verified while-loop), NOT behind an axiom about the function-under-change; its correspondence to the real patched language_code_prefix_re.match(path)[1] is validated by G-CONF (meta.json: pass, 100040 inputs, 0 disagreements, seed 15098). A4 = A-consumed + R — the lone consumed axiom `listedLanguage` <-> the UNCHANGED callee get_supported_language_variant, opaque/weakest-contract, validated by G-AX (meta.json: pass, deterministic total-dichotomy, 5102 obs). Every leg is R / A-consumed / A-reference / I; NO kind-3. The A-legs' correspondence to the real callees holds (G-CONF + G-AX both pass in-container per meta.json).

HISTORY: verdict.md records an earlier faithfulness (G-PANEL) TOO-STRONG defect on trailing-single-newline paths (/en\n) that was subsequently refined (status-3 line-terminator handling) and re-accepted. That is a G-PANEL faithfulness matter, not a G-EQ (verify-implies-correct) break; the current frozen spec models the `$`-before-trailing-newline case and G-CONF passes. It does not affect this G-EQ verdict.

VERDICT: SOUND. >=9 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, flag-pin, off-by-one) all verified and all rejected; positive control verifies; prepatch reproduced; no faithful patch of a verifying wrong impl exists to break the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. resolvePathLanguage models get_language_from_path (django/utils/translation/trans_real.py:501). The R/I deep model leadingLocaleTag 2 transliterates the PATCHED regex r'^/(\w+([@-]\w+){0,2})(/|$)'. Verified: (1) automaton (lstep/ldecode fold) == patched regex group[1] over exhaustive strings <=len6 on {/,a,b,-,@,\n,\r,1,_,x,.}, 300k random ASCII paths, and targeted len7-9 seg-limit strings -> 0 mismatches; boundary cases /en\n (=>en), /en\n\n (=>none), /en\nx (=>none), /en\r (=>none, \r not a $-terminator), /a-b-c/ (=>en), /a-b-c-d/ (=>none, exceeds {0,2}), /en@la@us all match. (2) isWordChar (c.isAlphanum||c=='_') == Python \w over ALL 128 ASCII code points (0 mismatches) -- the precondition forall c in path, c.toNat<128 confines the domain to where they provably coincide; this NARROWS the contract, no over-claim. (3) isSubtagSep == [@-] exact over ASCII. (4) listedLanguage is the weakest opaque axiom (no asserted property, only threaded through match) -- nothing to over-claim; its LookupError->none folding is A-consumed. (5) same_spec(Solution, Solution_prepatch, velvet)=True; pure-region diff empty (twins differ only in impl/proof and buggy bound 1 vs patched 2, both outside spec signature). (6) Solution.lean elaborates exit 0 via lean_verify.sh. Note: /tmp worktrees at base_commit carry the UNPATCHED regex (?); the spec correctly models the {0,2} patched behavior. Spec is neither too strong nor drifted -- FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: regex quantifier r'^/(\w+([@-]\w+)?)(/|$)' -> r'^/(\w+([@-]\w+){0,2})(/|$)', i.e. allow up to 2 additional locale subtags (script + region) instead of <=1.

Mechanical G-LEAK screen (leakage.screen over the velvet spec_view) PASSES: no diff markers, no patched file path 'django/utils/translation/trans_real.py' nor dotted module, no gold-diff line reproduced (the regex literal never appears in the spec view), no narration words, changed-symbols set is empty (repo symbols are all renamed: get_language_from_path->resolvePathLanguage, language_code_prefix_re->leadingLocaleTag, get_supported_language_variant->listedLanguage). same_spec(Solution.lean, Solution_prepatch.lean) = True (byte-identical spec region).

Semantic judgment vs the PUBLIC problem_statement (not hints_text): the problem statement already states the bug is about a locale 'containing both script and region' (e.g. en-latn-us), gives en-latn-us / en-Latn-US as failing examples, and quotes the RFC 5646 langtag grammar (language ["-" script] ["-" region]). Thus 'a primary subtag plus up to two additional subtags — a script and a region, per RFC 5646' and the bound maxSegs=2 are the direct public reading of the task, not a disclosure of the edit. The spec view describes required behavior (its purpose) without revealing the regex, file, symbols, or any fix narration. The discriminating gold-specific artifacts (concrete examples /en-latn-us/, /de-ch-1901/, the prepatch bound lstep 1, 'the patched bound', {0,2} quantifier) live only in refinement.md and mapping.md, which are audit-only docs explicitly marked 'not in the consumer spec view', never in the spec view itself.

No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
