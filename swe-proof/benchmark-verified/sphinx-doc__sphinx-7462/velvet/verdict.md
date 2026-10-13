# P2 adversarial audit — sphinx-doc__sphinx-7462

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No axiomatized callees and no deep-model references.
@@ -86,9 +86,7 @@
   ensures out = seqTokens elts
   do
     -- impl-start
-    let result : List (List Char) := match elts with
-      | []  => ["(".toList, ")".toList]
-      | _   => List.intercalate [", ".toList] elts
+    let result : List (List Char) := List.intercalate [", ".toList] elts
     return result
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
 /- No axiomatized callees and no deep-model references.
@@ -116,9 +116,7 @@
   ensures out = seqText elts
   do
     -- impl-start
-    let result : List Char := match elts with
-      | []  => "()".toList
-      | _   => List.intercalate ", ".toList elts
+    let result : List Char := List.intercalate ", ".toList elts
     return result
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
 /- No axiomatized callees and no deep-model references.
@@ -87,7 +87,7 @@
   do
     -- impl-start
     let result : List (List Char) := match elts with
-      | []  => ["(".toList, ")".toList]
+      | []  => ["()".toList]
       | _   => List.intercalate [", ".toList] elts
     return result
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
 /- No axiomatized callees and no deep-model references.
@@ -118,7 +118,7 @@
     -- impl-start
     let result : List Char := match elts with
       | []  => "()".toList
-      | _   => List.intercalate ", ".toList elts
+      | _   => List.intercalate ",".toList elts
     return result
     -- impl-end
 
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
 /- No axiomatized callees and no deep-model references.
@@ -87,7 +87,7 @@
   do
     -- impl-start
     let result : List (List Char) := match elts with
-      | []  => ["(".toList, ")".toList]
+      | []  => [")".toList, "(".toList]
       | _   => List.intercalate [", ".toList] elts
     return result
     -- impl-end
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
 /- No axiomatized callees and no deep-model references.
@@ -118,7 +118,7 @@
     -- impl-start
     let result : List Char := match elts with
       | []  => "()".toList
-      | _   => List.intercalate ", ".toList elts
+      | _   => List.intercalate ", ".toList elts ++ ", ".toList
     return result
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
 /- No axiomatized callees and no deep-model references.
@@ -86,9 +86,7 @@
   ensures out = seqTokens elts
   do
     -- impl-start
-    let result : List (List Char) := match elts with
-      | []  => ["(".toList, ")".toList]
-      | _   => List.intercalate [", ".toList] elts
+    let result : List (List Char) := ["(".toList, ")".toList]
     return result
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
 /- No axiomatized callees and no deep-model references.
@@ -86,10 +86,7 @@
   ensures out = seqTokens elts
   do
     -- impl-start
-    let result : List (List Char) := match elts with
-      | []  => ["(".toList, ")".toList]
-      | _   => List.intercalate [", ".toList] elts
-    return result
+    return seqTokens elts
     -- impl-end
 
 prove_correct renderSequenceTokens by
@@ -116,10 +113,7 @@
   ensures out = seqText elts
   do
     -- impl-start
-    let result : List Char := match elts with
-      | []  => "()".toList
-      | _   => List.intercalate ", ".toList elts
-    return result
+    return seqText elts
     -- impl-end
 
 prove_correct renderSequenceText by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees and no deep-model references.

   The rendering of each individual member of a sequence is produced by the
   surrounding recursive renderer, which neither modeled operation changes. Each
   member rendering is therefore treated as opaque already-rendered material: the
   member renderings are the arbitrary inputs `elts`, about which the
   specification assumes nothing. Both operations depend only on HOW those member
   renderings are wrapped and separated as a function of how many there are —
   never on their content — so no callee contract is consumed (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A single member rendering, when the result is a list of display tokens, is one
   list of tokens; each token is opaque text (`List Char`). A whole sequence's
   members is then a `List (List (List Char))`. -/

/- The display-token rendering of a comma-separated sequence, given the
   already-rendered tokens of each member, as a function of the member count:

     * no members  ↦  the two punctuation tokens of an empty pair, `(` then `)`;
     * one or more ↦  the members' token lists concatenated with a single
                      comma-space separator token placed BETWEEN adjacent
                      members (none at the ends).

   The separator between adjacent members is the single token comma-space. -/
def seqTokens (elts : List (List (List Char))) : List (List Char) :=
  match elts with
  | []  => ["(".toList, ")".toList]
  | _   => List.intercalate [", ".toList] elts

@[grind] lemma seqTokens_nil :
    seqTokens [] = ["(".toList, ")".toList] := rfl
@[grind] lemma seqTokens_cons (a : List (List Char)) (rest : List (List (List Char))) :
    seqTokens (a :: rest) = List.intercalate [", ".toList] (a :: rest) := rfl

/- The source-text rendering of a comma-separated sequence, given the
   already-rendered source text of each member, as a function of the member
   count:

     * no members  ↦  the empty pair `()`;
     * one or more ↦  the members' text joined by the two-character separator
                      comma-space, with no separator at the ends and no
                      surrounding wrapping.

   The separator between adjacent members is the two characters comma-space. -/
def seqText (elts : List (List Char)) : List Char :=
  match elts with
  | []  => "()".toList
  | _   => List.intercalate ", ".toList elts

@[grind] lemma seqText_nil :
    seqText [] = "()".toList := rfl
@[grind] lemma seqText_cons (a : List Char) (rest : List (List Char)) :
    seqText (a :: rest) = List.intercalate ", ".toList (a :: rest) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the display tokens of a comma-separated sequence from the
   already-rendered tokens of its members.

   The result is determined entirely by the member count. The empty sequence is
   the structural end case: it renders as the two punctuation tokens of an empty
   pair, `(` then `)`, rather than as no tokens at all. Every non-empty sequence
   is its members' token lists concatenated, with one comma-space separator token
   between adjacent members and none at the ends.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member token lists and builds a fresh result, mutating
   nothing. -/
method renderSequenceTokens (elts : List (List (List Char)))
    return (out : List (List Char))
  ensures out = seqTokens elts
  do
    -- impl-start
    let result : List (List Char) := match elts with
      | []  => ["(".toList, ")".toList]
      | _   => List.intercalate [", ".toList] elts
    return result
    -- impl-end

prove_correct renderSequenceTokens by
  loom_solve
  rfl

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the source text of a comma-separated sequence from the already-rendered
   source text of its members.

   The result is determined entirely by the member count. The empty sequence is
   the structural end case: it renders as the empty pair `()`, rather than as the
   empty string. Every non-empty sequence is its members' text joined by the
   comma-space separator, with no separator at the ends.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member text and builds a fresh result, mutating nothing. -/
method renderSequenceText (elts : List (List Char)) return (out : List Char)
  ensures out = seqText elts
  do
    -- impl-start
    let result : List Char := match elts with
      | []  => "()".toList
      | _   => List.intercalate ", ".toList elts
    return result
    -- impl-end

prove_correct renderSequenceText by
  loom_solve
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of sphinx-doc__sphinx-7462 (velvet). VERDICT: SOUND.

SPEC SHAPE: The two method contracts are COMPLETE extensional equalities against TOTAL pure oracles: `ensures out = seqTokens elts` and `ensures out = seqText elts`, where seqTokens/seqText are fully spelled-out total functions (empty->["(",")"] / "()"; non-empty->intercalate). This is the tightest possible spec shape: ANY behavioral deviation on ANY input makes prove_correct's `rfl` fail. There is no room for a verifying-but-wrong impl.

ATTACKS (all same_spec==True verified via markers.same_spec on velvet; impl-region-only edits, axioms/pure/pre/post byte-identical; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug #1, tokens partial-domain): tokens impl = `List.intercalate [", "] elts` with NO empty case -> yields [] on empty vs required ["(",")"]. EXIT=1 (rfl failed). REPRODUCES the reported IndexError prepatch bug at site #1.
- atk_2 (prepatch bug #2, text partial-domain): text impl = `List.intercalate ", " elts` NO empty case -> "" on empty vs required "()". EXIT=1 (rfl failed). REPRODUCES prepatch bug at site #2.
- atk_3 (boundary, tokens): empty -> single token ["()"] instead of two tokens ["(",")"]. EXIT=1. (cardinality wrong, catches the mapping.md §2.1 'two entries never one' claim.)
- atk_4 (boundary/separator, text): non-empty uses `,` (no space) separator instead of `, `. EXIT=1 (differs on len>=2).
- atk_5 (boundary, tokens): empty -> swapped order [")","("]. EXIT=1.
- atk_6 (control-flow-effect, text): non-empty appends a TRAILING separator (intercalate ++ ", "). EXIT=1 (wrong on every non-empty input; models a missing result.pop()/extra-sep bug).
- atk_7 (control-flow-effect, tokens): ALWAYS returns ["(",")"] ignoring members. EXIT=1 (wrong on all non-empty).
- atk_8 (ungrounded-oracle echo): both impls `return seqTokens elts` / `return seqText elts`. EXIT=1 — behaviorally CORRECT (equals the oracle) but the frozen proof script `loom_solve; rfl` errors with 'No goals to be solved' after the trivial echo. Not a falsifier; recorded as a non-verifying same-spec attack.

POSITIVE CONTROL: frozen Solution.lean copied verbatim -> lean_verify.sh EXIT=0 (verifies, no sorry).

STEP-2 (materialize+resolve faithful patches for VERIFYING wrong impls): VACUOUS — no wrong impl verified, so there is no verifying-wrong-impl whose faithful patch could fail to resolve. Hence verify NOT-refuted as implying correct for this spec.

CONFIRMATORY RESOLVE (executed, not speculated): gold patch.diff run through the official harness via run_resolve('sphinx-doc__sphinx-7462', patch.diff, timeout=1200, retries=0) -> completed=True, resolved=True, note='resolved'. Establishes the correctness endpoint (verify(Solution) => gold behavior => resolves).

A-LEG AUDIT (refinement.md §C / mapping.md §3): confirmed ZERO axiom declarations in Solution.lean (grep '^\s*axiom' -> NONE) and NO deep-model references. axiom_check.py is a documented no-op exiting 0. All refinement.md legs are R (type refinement) or I (identical concrete op): A1-A4 (tokens) and B1-B4 (text). The member renderings unparse(elem)/unparse(e) are correctly abstracted as opaque inputs `elts` (the surrounding recursive renderer is unchanged by both hunks), so there is no A-consumed or A-reference leg to falsify. Correspondence to real callees: the tokens site's non-empty loop (extend+append(', ') then result.pop()) == intercalate [', '] on >=1 members, and empty -> two desc_sig_punctuation('(' , ')') == ["(",")"]; the text site's ', '.join == intercalate ', ' on >=1, empty -> '()'. Both match the gold hunks byte-for-byte in behavior. No kind-3 (inexpressible-changed-op) leg present.

CONCLUSION: >=5 distinct same-spec wrong impls encoded (8 total: partial-domain, boundary, control-flow-effect, ungrounded-oracle echo), each verified with lean_verify.sh; NONE verifies; prepatch bug reproduced at BOTH sites; positive control verifies; gold resolves. Spec is a complete equality that admits no verifying-wrong-impl. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees and no deep-model references.

   The rendering of each individual member of a sequence is produced by the
   surrounding recursive renderer, which neither modeled operation changes. Each
   member rendering is therefore treated as opaque already-rendered material: the
   member renderings are the arbitrary inputs `elts`, about which the
   specification assumes nothing. Both operations depend only on HOW those member
   renderings are wrapped and separated as a function of how many there are —
   never on their content — so no callee contract is consumed (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A single member rendering, when the result is a list of display tokens, is one
   list of tokens; each token is opaque text (`List Char`). A whole sequence's
   members is then a `List (List (List Char))`. -/

/- The display-token rendering of a comma-separated sequence, given the
   already-rendered tokens of each member, as a function of the member count:

     * no members  ↦  the two punctuation tokens of an empty pair, `(` then `)`;
     * one or more ↦  the members' token lists concatenated with a single
                      comma-space separator token placed BETWEEN adjacent
                      members (none at the ends).

   The separator between adjacent members is the single token comma-space. -/
def seqTokens (elts : List (List (List Char))) : List (List Char) :=
  match elts with
  | []  => ["(".toList, ")".toList]
  | _   => List.intercalate [", ".toList] elts

@[grind] lemma seqTokens_nil :
    seqTokens [] = ["(".toList, ")".toList] := rfl
@[grind] lemma seqTokens_cons (a : List (List Char)) (rest : List (List (List Char))) :
    seqTokens (a :: rest) = List.intercalate [", ".toList] (a :: rest) := rfl

/- The source-text rendering of a comma-separated sequence, given the
   already-rendered source text of each member, as a function of the member
   count:

     * no members  ↦  the empty pair `()`;
     * one or more ↦  the members' text joined by the two-character separator
                      comma-space, with no separator at the ends and no
                      surrounding wrapping.

   The separator between adjacent members is the two characters comma-space. -/
def seqText (elts : List (List Char)) : List Char :=
  match elts with
  | []  => "()".toList
  | _   => List.intercalate ", ".toList elts

@[grind] lemma seqText_nil :
    seqText [] = "()".toList := rfl
@[grind] lemma seqText_cons (a : List Char) (rest : List (List Char)) :
    seqText (a :: rest) = List.intercalate ", ".toList (a :: rest) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the display tokens of a comma-separated sequence from the
   already-rendered tokens of its members.

   The result is determined entirely by the member count. The empty sequence is
   the structural end case: it renders as the two punctuation tokens of an empty
   pair, `(` then `)`, rather than as no tokens at all. Every non-empty sequence
   is its members' token lists concatenated, with one comma-space separator token
   between adjacent members and none at the ends.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member token lists and builds a fresh result, mutating
   nothing. -/
method renderSequenceTokens (elts : List (List (List Char)))
    return (out : List (List Char))
  ensures out = seqTokens elts
  do
    -- impl-start
    let result : List (List Char) := match elts with
      | []  => ["(".toList, ")".toList]
      | _   => List.intercalate [", ".toList] elts
    return result
    -- impl-end

prove_correct renderSequenceTokens by
  loom_solve
  rfl

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the source text of a comma-separated sequence from the already-rendered
   source text of its members.

   The result is determined entirely by the member count. The empty sequence is
   the structural end case: it renders as the empty pair `()`, rather than as the
   empty string. Every non-empty sequence is its members' text joined by the
   comma-space separator, with no separator at the ends.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member text and builds a fresh result, mutating nothing. -/
method renderSequenceText (elts : List (List Char)) return (out : List Char)
  ensures out = seqText elts
  do
    -- impl-start
    let result : List Char := match elts with
      | []  => "()".toList
      | _   => List.intercalate ", ".toList elts
    return result
    -- impl-end

prove_correct renderSequenceText by
  loom_solve
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of sphinx-doc__sphinx-7462 (velvet). VERDICT: SOUND.

SPEC SHAPE: The two method contracts are COMPLETE extensional equalities against TOTAL pure oracles: `ensures out = seqTokens elts` and `ensures out = seqText elts`, where seqTokens/seqText are fully spelled-out total functions (empty->["(",")"] / "()"; non-empty->intercalate). This is the tightest possible spec shape: ANY behavioral deviation on ANY input makes prove_correct's `rfl` fail. There is no room for a verifying-but-wrong impl.

ATTACKS (all same_spec==True verified via markers.same_spec on velvet; impl-region-only edits, axioms/pure/pre/post byte-identical; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug #1, tokens partial-domain): tokens impl = `List.intercalate [", "] elts` with NO empty case -> yields [] on empty vs required ["(",")"]. EXIT=1 (rfl failed). REPRODUCES the reported IndexError prepatch bug at site #1.
- atk_2 (prepatch bug #2, text partial-domain): text impl = `List.intercalate ", " elts` NO empty case -> "" on empty vs required "()". EXIT=1 (rfl failed). REPRODUCES prepatch bug at site #2.
- atk_3 (boundary, tokens): empty -> single token ["()"] instead of two tokens ["(",")"]. EXIT=1. (cardinality wrong, catches the mapping.md §2.1 'two entries never one' claim.)
- atk_4 (boundary/separator, text): non-empty uses `,` (no space) separator instead of `, `. EXIT=1 (differs on len>=2).
- atk_5 (boundary, tokens): empty -> swapped order [")","("]. EXIT=1.
- atk_6 (control-flow-effect, text): non-empty appends a TRAILING separator (intercalate ++ ", "). EXIT=1 (wrong on every non-empty input; models a missing result.pop()/extra-sep bug).
- atk_7 (control-flow-effect, tokens): ALWAYS returns ["(",")"] ignoring members. EXIT=1 (wrong on all non-empty).
- atk_8 (ungrounded-oracle echo): both impls `return seqTokens elts` / `return seqText elts`. EXIT=1 — behaviorally CORRECT (equals the oracle) but the frozen proof script `loom_solve; rfl` errors with 'No goals to be solved' after the trivial echo. Not a falsifier; recorded as a non-verifying same-spec attack.

POSITIVE CONTROL: frozen Solution.lean copied verbatim -> lean_verify.sh EXIT=0 (verifies, no sorry).

STEP-2 (materialize+resolve faithful patches for VERIFYING wrong impls): VACUOUS — no wrong impl verified, so there is no verifying-wrong-impl whose faithful patch could fail to resolve. Hence verify NOT-refuted as implying correct for this spec.

CONFIRMATORY RESOLVE (executed, not speculated): gold patch.diff run through the official harness via run_resolve('sphinx-doc__sphinx-7462', patch.diff, timeout=1200, retries=0) -> completed=True, resolved=True, note='resolved'. Establishes the correctness endpoint (verify(Solution) => gold behavior => resolves).

A-LEG AUDIT (refinement.md §C / mapping.md §3): confirmed ZERO axiom declarations in Solution.lean (grep '^\s*axiom' -> NONE) and NO deep-model references. axiom_check.py is a documented no-op exiting 0. All refinement.md legs are R (type refinement) or I (identical concrete op): A1-A4 (tokens) and B1-B4 (text). The member renderings unparse(elem)/unparse(e) are correctly abstracted as opaque inputs `elts` (the surrounding recursive renderer is unchanged by both hunks), so there is no A-consumed or A-reference leg to falsify. Correspondence to real callees: the tokens site's non-empty loop (extend+append(', ') then result.pop()) == intercalate [', '] on >=1 members, and empty -> two desc_sig_punctuation('(' , ')') == ["(",")"]; the text site's ', '.join == intercalate ', ' on >=1, empty -> '()'. Both match the gold hunks byte-for-byte in behavior. No kind-3 (inexpressible-changed-op) leg present.

CONCLUSION: >=5 distinct same-spec wrong impls encoded (8 total: partial-domain, boundary, control-flow-effect, ungrounded-oracle echo), each verified with lean_verify.sh; NONE verifies; prepatch bug reproduced at BOTH sites; positive control verifies; gold resolves. Spec is a complete equality that admits no verifying-wrong-impl. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled functions and the real repo callees.

Spec integrity: same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True — spec regions byte-identical (velvet LanguageTables). Solution.lean verifies (lean_verify exit 0); both prepatch files FAIL the spec (exit 1), so the spec is genuinely discriminating on the empty-sequence fix, not vacuous or over-tightened to pass.

Independent differential vs. the REAL patched repo at base_commit b3e26a6c (fresh seeds 999/31337, NOT the pinned 7462, so this is not a rubber-stamp of conformance_check.py):
  * Site #1: model seqTokens (empty -> two desc_sig_punctuation '(' ')'; non-empty -> member images interspersed with one ', ' desc_sig_punctuation) vs real sphinx.domains.python._parse_annotation tuple branch. 300,000 inputs incl. boundaries (), (int,), (int,str,...), nested/List/Dict/Optional members. 0 mismatches.
  * Site #2: model seqText (empty -> '()'; non-empty -> ', '.join(images)) vs real sphinx.pycode.ast.unparse on ast.Tuple. 200,000 inputs incl. (), (1,), (1,2,3), nested/empty-member tuples, Constant members. 0 mismatches.

The site-1 domain restriction (Constant members hit the unchanged inner unparse SyntaxError -> outer make_xref fallback) is legitimate input-domain scoping — the modeled op assembles already-rendered member images, and it agrees with the real callee everywhere the real ast.Tuple branch is actually reached. This is not spec-drift.

Conclusion: the modeled functions agree with the real repo on all tested inputs including the discriminating empty-tuple cases; the spec neither over- nor under-constrains relative to gold behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = elided Solution.lean (impl + prove_correct bodies removed); mapping.md/refinement.md are auditor artifacts, not solver-visible, so their verbatim gold-patch quoting is out of scope. Mechanical G-LEAK recorded 'spec view clean' (strict, not relaxed). Independently re-rendered spec_view (VelvetBackend.language) and probed: NONE of {sphinx, python.py, ast.py, pycode, domains, unparse, _parse_annotation, desc_sig, node.elts, 'if node', 'else:', IndexError, pop} appear. No diff markers, no file/module paths, no patched repo symbols. No bug/fix narration — comments describe the TARGET BEHAVIOR abstractly ('structural end case', 'comma-space separator', 'read-only input (directive 5)'). same_spec(Solution.lean, Solution_prepatch{,_2}.lean)=True: spec region byte-stable, prepatches diff only in elided impl. The spec states the correct empty-sequence rendering (source text '()' ; two tokens '(' ')') — this is the legitimate job of a spec and is directly implied by the public problem ('empty tuple Tuple[()] -> valid annotation, docs built'), not a disclosure of the gold EDIT (locations/diff/symbols). The token-domain second method is expressed purely as an abstract contract (ensures out = seqTokens elts) with the spec->repo binding held only in the non-visible mapping.md. Contrast phrases ('rather than as no tokens at all' / 'rather than as the empty string') pin the discriminating behavior abstractly, referencing no repo/patch specifics. Faithful behavioral spec, not gold-reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
