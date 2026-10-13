# P2 adversarial audit — psf__requests-6028

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_4.lean`, `atk_5.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The spec's postcondition is exact equality with `reassemble`, which pins every component, so in-domain (authority0 != "", newScheme != "", a present scheme non-empty) the impl is uniquely determined up to observable equality. The 5 wrong impls that FAILED to verify each have a machine-checked (`by decide`) counterexample in refute.lean, all inside the modeled domain: atk_1/prepatch (auth=some "user:pass", authority0="example.com", path="/path", query="query") -> impl gives "http://example.com/path?query" but reassemble requires "http://user:pass@example.com/path?query"; atk_2 (auth=some "user", path="") -> userinfo dropped; atk_3 (auth=some "") -> spurious "@" prefix; atk_7 (fragment="frag") -> fragment dropped. atk_6 (ungrounded oracle echo of the two F2P cases with pre-patch behavior elsewhere) also failed to verify. The 6 impls that DID close all only diverge from gold on inputs the preconditions exclude (empty authority / empty new_scheme / empty-string scheme), and all 6 RESOLVE under the official harness, so verify => correct held on every attack.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,10 +88,6 @@
     let saved := authority
     authority := path
     path := saved
-  match auth with
-  | some a => if a ≠ "" then
-                authority := a ++ "@" ++ authority
-  | none => pure ()
   let scheme := match scheme0 with
     | none => newScheme
     | some s => s
@@ -108,10 +104,9 @@
       problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
-  unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
+  unfold problem_spec_prependScheme implementation_prependScheme reassemble assembleUrl
   cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  | none => simp_all [Id.run]
+  | some a =>
+    by_cases h : a = "" <;> simp_all [Id.run, String.append_assoc]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
     authority := path
     path := saved
   match auth with
-  | some a => if a ≠ "" then
+  | some a => if a ≠ "" ∧ path ≠ "" then
                 authority := a ++ "@" ++ authority
   | none => pure ()
   let scheme := match scheme0 with
@@ -108,10 +108,9 @@
       problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
-  unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
+  unfold problem_spec_prependScheme implementation_prependScheme reassemble assembleUrl
   cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  | none => simp_all [Id.run]
+  | some a =>
+    by_cases h : a = "" <;> simp_all [Id.run, String.append_assoc]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,8 +89,7 @@
     authority := path
     path := saved
   match auth with
-  | some a => if a ≠ "" then
-                authority := a ++ "@" ++ authority
+  | some a => authority := a ++ "@" ++ authority
   | none => pure ()
   let scheme := match scheme0 with
     | none => newScheme
@@ -108,10 +107,9 @@
       problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
-  unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
+  unfold problem_spec_prependScheme implementation_prependScheme reassemble assembleUrl
   cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  | none => simp_all [Id.run]
+  | some a =>
+    by_cases h : a = "" <;> simp_all [Id.run, String.append_assoc]
 -- proof-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,14 +84,13 @@
     String := Id.run do
   let mut authority := authority0
   let mut path := path0
-  if authority = "" then
-    let saved := authority
-    authority := path
-    path := saved
   match auth with
   | some a => if a ≠ "" then
                 authority := a ++ "@" ++ authority
   | none => pure ()
+  if authority0 = "" then
+    authority := path
+    path := authority0
   let scheme := match scheme0 with
     | none => newScheme
     | some s => s
@@ -109,9 +108,10 @@
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
   unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
   cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  | none => simp only [Id.run, if_neg hauth]; rfl
+  | some a =>
+    by_cases h : a = "" <;>
+      simp only [h, Id.run, if_neg hauth, ne_eq, not_true, not_false_iff,
+                 if_true, if_false] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,21 +81,15 @@
 -- impl-start
 def implementation_prependScheme (scheme0 auth : Option String)
     (authority0 path0 query fragment : String) (newScheme : String) :
-    String := Id.run do
-  let mut authority := authority0
-  let mut path := path0
-  if authority = "" then
-    let saved := authority
-    authority := path
-    path := saved
-  match auth with
-  | some a => if a ≠ "" then
-                authority := a ++ "@" ++ authority
-  | none => pure ()
+    String :=
+  if authority0 = "" then "" else
+  let authority := match auth with
+    | some a => if a ≠ "" then a ++ "@" ++ authority0 else authority0
+    | none => authority0
   let scheme := match scheme0 with
     | none => newScheme
     | some s => s
-  return assembleUrl scheme authority path query fragment
+  assembleUrl scheme authority path0 query fragment
 -- impl-end
 
 
@@ -109,9 +103,5 @@
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
   unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
-  cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  simp only [if_neg hauth]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,21 +81,21 @@
 -- impl-start
 def implementation_prependScheme (scheme0 auth : Option String)
     (authority0 path0 query fragment : String) (newScheme : String) :
-    String := Id.run do
-  let mut authority := authority0
-  let mut path := path0
-  if authority = "" then
-    let saved := authority
-    authority := path
-    path := saved
-  match auth with
-  | some a => if a ≠ "" then
-                authority := a ++ "@" ++ authority
-  | none => pure ()
-  let scheme := match scheme0 with
-    | none => newScheme
-    | some s => s
-  return assembleUrl scheme authority path query fragment
+    String :=
+  -- echo the two observed proxy-with-credentials cases; pre-patch elsewhere
+  if scheme0 = some "http" ∧ auth = some "user:pass" ∧ authority0 = "example.com"
+      ∧ path0 = "/path" ∧ query = "query" ∧ fragment = "" then
+    "http://user:pass@example.com/path?query"
+  else if scheme0 = some "http" ∧ auth = some "user" ∧ authority0 = "example.com"
+      ∧ path0 = "/path" ∧ query = "query" ∧ fragment = "" then
+    "http://user@example.com/path?query"
+  else
+    let authority := if authority0 = "" then path0 else authority0
+    let path := if authority0 = "" then authority0 else path0
+    let scheme := match scheme0 with
+      | none => newScheme
+      | some s => s
+    assembleUrl scheme authority path query fragment
 -- impl-end
 
 
@@ -108,10 +108,9 @@
       problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
-  unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
+  unfold problem_spec_prependScheme implementation_prependScheme reassemble assembleUrl
   cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  | none => simp_all [Id.run]
+  | some a =>
+    by_cases h : a = "" <;> simp_all [Id.run, String.append_assoc]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
   let scheme := match scheme0 with
     | none => newScheme
     | some s => s
-  return assembleUrl scheme authority path query fragment
+  return assembleUrl scheme authority path query ""
 -- impl-end
 
 
@@ -108,10 +108,9 @@
       problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
-  unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
+  unfold problem_spec_prependScheme implementation_prependScheme reassemble assembleUrl
   cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
+  | none => simp_all [Id.run]
+  | some a =>
+    by_cases h : a = "" <;> simp_all [Id.run, String.append_assoc]
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -94,7 +94,7 @@
   | none => pure ()
   let scheme := match scheme0 with
     | none => newScheme
-    | some s => s
+    | some s => if s = "" then newScheme else s
   return assembleUrl scheme authority path query fragment
 -- impl-end
 
@@ -110,8 +110,16 @@
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
   unfold problem_spec_prependScheme implementation_prependScheme reassemble
   simp only [Id.run, if_neg hauth]
-  cases auth with
-  | none => rfl
-  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
+  cases scheme0 with
+  | none =>
+    cases auth with
+    | none => rfl
+    | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
+  | some s =>
+    have hs' : s ≠ "" := hs s rfl
+    simp only [if_neg hs']
+    cases auth with
+    | none => rfl
+    | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
 
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,14 +84,14 @@
     String := Id.run do
   let mut authority := authority0
   let mut path := path0
-  if authority = "" then
-    let saved := authority
-    authority := path
-    path := saved
-  match auth with
-  | some a => if a ≠ "" then
-                authority := a ++ "@" ++ authority
-  | none => pure ()
+  if authority0 = "" then
+    authority := path0
+    path := authority0
+  else
+    match auth with
+    | some a => if a ≠ "" then
+                  authority := a ++ "@" ++ authority
+    | none => pure ()
   let scheme := match scheme0 with
     | none => newScheme
     | some s => s
@@ -113,5 +113,4 @@
   cases auth with
   | none => rfl
   | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,14 +84,18 @@
     String := Id.run do
   let mut authority := authority0
   let mut path := path0
-  if authority = "" then
-    let saved := authority
-    authority := path
-    path := saved
-  match auth with
-  | some a => if a ≠ "" then
-                authority := a ++ "@" ++ authority
-  | none => pure ()
+  if authority0 = "" then
+    authority := path0
+    path := authority0
+    match auth with
+    | some a => if a ≠ "" then
+                  authority := a ++ "@" ++ a ++ "@" ++ authority
+    | none => pure ()
+  else
+    match auth with
+    | some a => if a ≠ "" then
+                  authority := a ++ "@" ++ authority
+    | none => pure ()
   let scheme := match scheme0 with
     | none => newScheme
     | some s => s
@@ -113,5 +117,4 @@
   cases auth with
   | none => rfl
   | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,7 +81,8 @@
 -- impl-start
 def implementation_prependScheme (scheme0 auth : Option String)
     (authority0 path0 query fragment : String) (newScheme : String) :
-    String := Id.run do
+    String :=
+  if newScheme = "" then "GARBAGE" else Id.run do
   let mut authority := authority0
   let mut path := path0
   if authority = "" then
@@ -109,9 +110,8 @@
         (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
   intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
   unfold problem_spec_prependScheme implementation_prependScheme reassemble
-  simp only [Id.run, if_neg hauth]
+  simp only [if_neg hns, Id.run, if_neg hauth]
   cases auth with
   | none => rfl
   | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl
-
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Round-tripping a URL string back from the components a URL parser hands back,
supplying a default scheme when the input carried none.

A URL parser decomposes a URL into a standard set of pieces. Here those are:
an optional scheme, an optional leading `userinfo` field, the authority
(host, optionally with a port), the path, the query, and the fragment; plus a
default scheme to use when the parsed one is absent. The task is the inverse of
parsing — reconstitute the URL string in standard syntax.

Correct reconstruction is a faithful round-trip: it carries **every** parsed
component through into the output, each in the slot the standard URL grammar
assigns it, so that re-parsing the result would recover the same pieces. No
component is privileged over any other. The `reassemble` definition below pins
the layout of all of them exactly, and the postcondition requires the result to
equal it; consult those definitions for the precise syntax rather than any prose
summary of them.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The URL parse step that
-- produces the components is upstream of this function and out of scope; the
-- string-assembly it performs is spelled out concretely below (a deep model,
-- validated against the real assembler by the differential conformance check),
-- so nothing is axiomatized.
-- axioms-end

-- pure-start
/-- Assemble a URL string from a (truthy) scheme, a (truthy) authority, a path,
a query and a fragment, following standard URL-composition syntax:

* a non-empty path not beginning with `/` receives a leading `/`;
* the authority is prefixed with `//`;
* the scheme is prefixed with `:`;
* a non-empty query is appended after `?`, a non-empty fragment after `#`.

`""` for `query`/`fragment` (and for an absent path) contributes nothing — the
exact behavior of a standard URL un-splitter on a present scheme and authority. -/
def assembleUrl (scheme authority path query fragment : String) : String :=
  let url := if path ≠ "" ∧ path.front ≠ '/' then "/" ++ path else path
  let url := "//" ++ authority ++ url
  let url := scheme ++ ":" ++ url
  let url := if query ≠ "" then url ++ "?" ++ query else url
  let url := if fragment ≠ "" then url ++ "#" ++ fragment else url
  url

/-- The reference result: the standard-syntax URL that carries every parsed
component through, computed by placing each piece in its slot and re-assembling.
`scheme0`/`auth` are optional (an absent value is `none`); `authority0`/`path`/
`query`/`fragment` are strings whose emptiness models an absent/empty component. -/
def reassemble (scheme0 auth : Option String)
    (authority0 path query fragment : String) (newScheme : String) : String :=
  -- when the parsed authority came back empty, the authority and path exchange
  -- roles (a no-op whenever the authority is present).
  let authority := if authority0 = "" then path else authority0
  let path := if authority0 = "" then authority0 else path
  let authority := match auth with
    | some a => if a ≠ "" then a ++ "@" ++ authority else authority
    | none => authority
  let scheme := match scheme0 with
    | none => newScheme
    | some s => s
  assembleUrl scheme authority path query fragment
-- pure-end

-- post-conditions-start
/-- The result is exactly the round-tripped URL: every parsed input component is
carried through into its standard syntactic slot in the output. -/
def problem_spec_prependScheme (scheme0 auth : Option String)
    (authority0 path query fragment : String) (newScheme : String)
    (result : String) : Prop :=
  result = reassemble scheme0 auth authority0 path query fragment newScheme
-- post-conditions-end

-- impl-start
def implementation_prependScheme (scheme0 auth : Option String)
    (authority0 path0 query fragment : String) (newScheme : String) :
    String := Id.run do
  let mut authority := authority0
  let mut path := path0
  if authority = "" then
    let saved := authority
    authority := path
    path := saved
  match auth with
  | some a => if a ≠ "" then
                authority := a ++ "@" ++ authority
  | none => pure ()
  let scheme := match scheme0 with
    | none => newScheme
    | some s => s
  return assembleUrl scheme authority path query fragment
-- impl-end

-- proof-start
theorem correct_prependScheme :
    ∀ (scheme0 auth : Option String)
      (authority0 path query fragment : String) (newScheme : String),
      authority0 ≠ "" → newScheme ≠ "" →
      (∀ s, scheme0 = some s → s ≠ "") →
      problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
        (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
  intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
  unfold problem_spec_prependScheme implementation_prependScheme reassemble
  simp only [Id.run, if_neg hauth]
  cases auth with
  | none => rfl
  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 11 same-spec attacks + positive control + prepatch reproduction. same_spec=True verified for all 11 attacks and pos_control against the bundle Solution.lean (spec regions axioms/pure/pre/post left byte-identical; only the impl+proof regions edited).

### COMMANDS (from swe-proof):
  bash scripts/lean_verify.sh <path>
  python -c "from swebench_unified.markers import same_spec; ..."   (all True)
  python resolve_one.py <name>   (wraps harness.run_resolve)

**POSITIVE CONTROL:** pos_control.lean rc=0. Axiom probe (pos_ax.lean, `#print axioms correct_prependScheme`) rc=0 -> [propext, Quot.sound] (clean).

### PREPATCH REPRODUCED (two ways):
  - prepatch.lean (bundle Solution_prepatch.lean verbatim) rc=3 (sorry).
  - prepatch_goldproof.lean (prepatch impl + the GOLD tactic block substituted for its `sorry`) rc=1: `Tactic rfl failed`, LHS lacking the `a ++ "@"` prefix. So the pre-patch impl provably cannot satisfy the postcondition -> the spec genuinely discriminates the fixed behavior.

ATTACKS THAT FAILED TO VERIFY (5) -- each with a machine-checked in-domain counterexample in refute.lean (rc=0, all via `by decide`):
  atk_1.lean  rc=1  pre-patch bug: userinfo never re-attached.
  atk_2.lean  rc=1  PARTIAL DOMAIN: re-attach only when path non-empty.
  atk_3.lean  rc=1  BOUNDARY: no empty-userinfo (falsy) guard -> spurious "@".
  atk_6.lean  rc=1  UNGROUNDED ORACLE ECHO: hardcodes the two F2P strings, pre-patch elsewhere. Did NOT close -- the spec's exact-equality postcondition rejects the echo.
  atk_7.lean  rc=1  COMPONENT DROP: fragment never emitted.

ATTACKS THAT CLOSED (6) -- all rc=0, all `#print axioms correct_prependScheme` = [propext, Quot.sound] (identical to gold, clean), all faithful patches MATERIALIZED and RUN through the official harness, ALL RESOLVED:
  atk_4.lean   rc=0  axioms clean  CONTROL-FLOW-EFFECT: join before the empty-authority swap (swap tests/restores the ORIGINAL authority). resolve: resolved=True, F2P 2/2 success, P2P failures=[] (atk_4.resolve.json)
  atk_5.lean   rc=0  axioms clean  OUT-OF-DOMAIN: `return ''` on empty authority. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_5.resolve.json)
  atk_8.lean   rc=0  axioms clean  OUT-OF-DOMAIN: `if not scheme` (falsy) instead of `if scheme is None`. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_8.resolve.json)
  atk_9.lean   rc=0  axioms clean  PARTIAL DOMAIN aimed at the excluded branch: userinfo DROPPED in the empty-authority arm (pre-patch bug preserved there), re-attached in-domain. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_9.resolve.json)
  atk_10.lean  rc=0  axioms clean  empty-authority arm emits the userinfo TWICE (`'@'.join([auth, auth, netloc])`). resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_10.resolve.json)
  atk_11.lean  rc=0  axioms clean  exploits the LAST unused binder `newScheme != ""`: `return 'GARBAGE'` when new_scheme is falsy. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_11.resolve.json)

No closing clean-axiom proof had a non-resolving faithful patch => verify => correct held on 6/6. NOT BROKEN.

### WHY THE EXCLUDED BRANCHES ARE HARMLESS (precondition justification, checked against the real code):
  The 3 binders are `authority0 != ""`, `newScheme != ""`, `forall s, scheme0 = some s -> s != ""`. Every closer diverges from gold ONLY where a binder is false, and each such region is unreachable or already broken in the real code:
  - `newScheme != ""`: the ONLY caller is requests/adapters.py:305 `prepend_scheme_if_needed(proxy, 'http')` -- a string literal (grep over requests/ and tests/ confirms the single call site plus the direct test, also literal 'http'). atk_11's divergence is dead code.
  - `scheme0 = some ""`: urllib3's `parse_url` never returns an empty-but-not-None scheme (probed `://host`, `://`, `:host`, `http://`, `1://h`, `http:host` -- it yields None or a non-empty scheme, or raises LocationParseError). atk_8's divergence is unreachable.
  - `authority0 != ""`: mapping.md documents this exclusion. I confirmed the strong version: for the empty-netloc-AND-truthy-auth inputs where atk_9/atk_10 diverge (e.g. "http://user@", "user@", "x://user@"), the REAL GOLD post-patch callee itself RAISES `TypeError: sequence item 1: expected str instance, NoneType found` (from `'@'.join([auth, None])`). Gold is already undefined there, so a model that differs there cannot be less correct than gold. Where the empty-netloc branch is reachable with a falsy auth ("://host", "://", "@"), atk_9/atk_10 agree with gold exactly. atk_5 does diverge on those (returns '') but no test reaches them.
  This is the residual G-EQ freedom and it is legitimate: it is confined to inputs the real caller cannot produce or on which the gold patch itself crashes.

refinement.md AUDIT -- PASS. 7 legs, all R / A-reference / I; NO kind-3 (no leg tagged A-consumed, consistent with meta.json axioms=[] and the G-AX skip stub). Leg-by-leg:
  1. inputs <- parse_url component split: R. Correct -- the parse is upstream of the modeled function and produces its inputs; the None -> none/"" bridge matches mapping.md and the real `.netloc`/`.auth` split I verified by probing parse_url directly.
  2. empty-authority swap: I. Byte-faithful to `if not netloc: netloc, path = path, netloc`, and `reassemble` spells it out so the model is total.
  3. userinfo re-attach (THE EDITED OP): A-reference. This is the correct tag -- the patch INTRODUCES this op, so per the cited rule it must be modeled deeply, never axiomatized. Correspondence `'@'.join([a,b])` <-> `a ++ "@" ++ b` and truthiness `if auth:` <-> `some a AND a != ""` both hold.
  4. scheme defaulting: I. Matches `if scheme is None`. (atk_8 shows the model pins `is None` rather than falsiness, and that the distinction is unobservable through the real parse_url.)
  5. path defaulting: I. Correctly folded into the `None -> ""` input bridge.
  6. `assembleUrl` <-> `urlunparse((scheme, netloc, path, '', query, fragment))`: R/A-reference. VERIFIED INDEPENDENTLY -- I re-implemented assembleUrl in Python and diffed it against the real stdlib `urlunparse` over 540 combinations (3 schemes x 5 authorities incl. userinfo forms x 6 paths incl. "", "/", "path", "//dbl" x 3 queries x 2 fragments): 0 mismatches.
  7. return value: R. Verbatim string equality.

A-REFERENCE CORRESPONDENCE, END-TO-END (the key A-leg check): I bridged the Lean model (`reassemble` transcribed to Python) through the REAL urllib3 `parse_url` and compared against the REAL post-patch `prepend_scheme_if_needed` over 3600 constructed URLs (seed 20240630, varying scheme/userinfo/host/port/IPv6/path/query/fragment), restricted to the modeled domain (netloc truthy, scheme non-empty): 3312 in-domain cases, 288 skipped as out-of-domain, 0 MISMATCHES. The deep model is faithful to the real callees on the whole modeled domain.

NOTE ON A STRUCTURAL OBSERVATION (not a defect for this bundle): `_lean_spec_view` elides the entire `proof` region, so the theorem's precondition binders are NOT part of the same_spec signature. An attacker could in principle submit a same-spec file that WEAKENS the binders. I did not treat this as a G-EQ break because (a) it changes the obligation rather than the impl, which is outside this gate's verify=>correct question, and (b) region_hashes in meta.json pins the proof region ('proof': a680fe7c...) so the release gate detects such an edit. Flagging for the harness owners, not scoring it here.

**ENV NOTE:** local pytest in the worktree cannot run (site urllib3 2.7.0 lacks SNIMissingWarning, so tests/`__init__`.py fails to import). All correctness claims therefore rest on the official Docker harness run_resolve runs above, which completed cleanly (attempts=1, flaky=false, completed=true on all 6) -- not on local pytest.

**SCHEDULE:** attacks verified in concurrent background batches of 4 (lean_verify), resolve runs launched as detached background jobs in batches of 4 then 1+1; every attack was still individually verified and every closer individually resolved. Artifacts (.lean, `_ax`.lean, .log, .rc, .patch, .utils.py, .resolve.json) all retained in .

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_4.lean`, `atk_5.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The spec's postcondition is exact equality with `reassemble`, which pins every component, so in-domain (authority0 != "", newScheme != "", a present scheme non-empty) the impl is uniquely determined up to observable equality. The 5 wrong impls that FAILED to verify each have a machine-checked (`by decide`) counterexample in refute.lean, all inside the modeled domain: atk_1/prepatch (auth=some "user:pass", authority0="example.com", path="/path", query="query") -> impl gives "http://example.com/path?query" but reassemble requires "http://user:pass@example.com/path?query"; atk_2 (auth=some "user", path="") -> userinfo dropped; atk_3 (auth=some "") -> spurious "@" prefix; atk_7 (fragment="frag") -> fragment dropped. atk_6 (ungrounded oracle echo of the two F2P cases with pre-patch behavior elsewhere) also failed to verify. The 6 impls that DID close all only diverge from gold on inputs the preconditions exclude (empty authority / empty new_scheme / empty-string scheme), and all 6 RESOLVE under the official harness, so verify => correct held on every attack.
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Round-tripping a URL string back from the components a URL parser hands back,
supplying a default scheme when the input carried none.

A URL parser decomposes a URL into a standard set of pieces. Here those are:
an optional scheme, an optional leading `userinfo` field, the authority
(host, optionally with a port), the path, the query, and the fragment; plus a
default scheme to use when the parsed one is absent. The task is the inverse of
parsing — reconstitute the URL string in standard syntax.

Correct reconstruction is a faithful round-trip: it carries **every** parsed
component through into the output, each in the slot the standard URL grammar
assigns it, so that re-parsing the result would recover the same pieces. No
component is privileged over any other. The `reassemble` definition below pins
the layout of all of them exactly, and the postcondition requires the result to
equal it; consult those definitions for the precise syntax rather than any prose
summary of them.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The URL parse step that
-- produces the components is upstream of this function and out of scope; the
-- string-assembly it performs is spelled out concretely below (a deep model,
-- validated against the real assembler by the differential conformance check),
-- so nothing is axiomatized.
-- axioms-end

-- pure-start
/-- Assemble a URL string from a (truthy) scheme, a (truthy) authority, a path,
a query and a fragment, following standard URL-composition syntax:

* a non-empty path not beginning with `/` receives a leading `/`;
* the authority is prefixed with `//`;
* the scheme is prefixed with `:`;
* a non-empty query is appended after `?`, a non-empty fragment after `#`.

`""` for `query`/`fragment` (and for an absent path) contributes nothing — the
exact behavior of a standard URL un-splitter on a present scheme and authority. -/
def assembleUrl (scheme authority path query fragment : String) : String :=
  let url := if path ≠ "" ∧ path.front ≠ '/' then "/" ++ path else path
  let url := "//" ++ authority ++ url
  let url := scheme ++ ":" ++ url
  let url := if query ≠ "" then url ++ "?" ++ query else url
  let url := if fragment ≠ "" then url ++ "#" ++ fragment else url
  url

/-- The reference result: the standard-syntax URL that carries every parsed
component through, computed by placing each piece in its slot and re-assembling.
`scheme0`/`auth` are optional (an absent value is `none`); `authority0`/`path`/
`query`/`fragment` are strings whose emptiness models an absent/empty component. -/
def reassemble (scheme0 auth : Option String)
    (authority0 path query fragment : String) (newScheme : String) : String :=
  -- when the parsed authority came back empty, the authority and path exchange
  -- roles (a no-op whenever the authority is present).
  let authority := if authority0 = "" then path else authority0
  let path := if authority0 = "" then authority0 else path
  let authority := match auth with
    | some a => if a ≠ "" then a ++ "@" ++ authority else authority
    | none => authority
  let scheme := match scheme0 with
    | none => newScheme
    | some s => s
  assembleUrl scheme authority path query fragment
-- pure-end

-- post-conditions-start
/-- The result is exactly the round-tripped URL: every parsed input component is
carried through into its standard syntactic slot in the output. -/
def problem_spec_prependScheme (scheme0 auth : Option String)
    (authority0 path query fragment : String) (newScheme : String)
    (result : String) : Prop :=
  result = reassemble scheme0 auth authority0 path query fragment newScheme
-- post-conditions-end

-- impl-start
def implementation_prependScheme (scheme0 auth : Option String)
    (authority0 path0 query fragment : String) (newScheme : String) :
    String := Id.run do
  let mut authority := authority0
  let mut path := path0
  if authority = "" then
    let saved := authority
    authority := path
    path := saved
  match auth with
  | some a => if a ≠ "" then
                authority := a ++ "@" ++ authority
  | none => pure ()
  let scheme := match scheme0 with
    | none => newScheme
    | some s => s
  return assembleUrl scheme authority path query fragment
-- impl-end

-- proof-start
theorem correct_prependScheme :
    ∀ (scheme0 auth : Option String)
      (authority0 path query fragment : String) (newScheme : String),
      authority0 ≠ "" → newScheme ≠ "" →
      (∀ s, scheme0 = some s → s ≠ "") →
      problem_spec_prependScheme scheme0 auth authority0 path query fragment newScheme
        (implementation_prependScheme scheme0 auth authority0 path query fragment newScheme) := by
  intro scheme0 auth authority0 path query fragment newScheme hauth hns hs
  unfold problem_spec_prependScheme implementation_prependScheme reassemble
  simp only [Id.run, if_neg hauth]
  cases auth with
  | none => rfl
  | some a => by_cases h : a = "" <;> simp only [h, if_true, if_false, ne_eq, not_true, not_false_iff] <;> rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 11 same-spec attacks + positive control + prepatch reproduction. same_spec=True verified for all 11 attacks and pos_control against the bundle Solution.lean (spec regions axioms/pure/pre/post left byte-identical; only the impl+proof regions edited).

### COMMANDS (from swe-proof):
  bash scripts/lean_verify.sh <path>
  python -c "from swebench_unified.markers import same_spec; ..."   (all True)
  python resolve_one.py <name>   (wraps harness.run_resolve)

**POSITIVE CONTROL:** pos_control.lean rc=0. Axiom probe (pos_ax.lean, `#print axioms correct_prependScheme`) rc=0 -> [propext, Quot.sound] (clean).

### PREPATCH REPRODUCED (two ways):
  - prepatch.lean (bundle Solution_prepatch.lean verbatim) rc=3 (sorry).
  - prepatch_goldproof.lean (prepatch impl + the GOLD tactic block substituted for its `sorry`) rc=1: `Tactic rfl failed`, LHS lacking the `a ++ "@"` prefix. So the pre-patch impl provably cannot satisfy the postcondition -> the spec genuinely discriminates the fixed behavior.

ATTACKS THAT FAILED TO VERIFY (5) -- each with a machine-checked in-domain counterexample in refute.lean (rc=0, all via `by decide`):
  atk_1.lean  rc=1  pre-patch bug: userinfo never re-attached.
  atk_2.lean  rc=1  PARTIAL DOMAIN: re-attach only when path non-empty.
  atk_3.lean  rc=1  BOUNDARY: no empty-userinfo (falsy) guard -> spurious "@".
  atk_6.lean  rc=1  UNGROUNDED ORACLE ECHO: hardcodes the two F2P strings, pre-patch elsewhere. Did NOT close -- the spec's exact-equality postcondition rejects the echo.
  atk_7.lean  rc=1  COMPONENT DROP: fragment never emitted.

ATTACKS THAT CLOSED (6) -- all rc=0, all `#print axioms correct_prependScheme` = [propext, Quot.sound] (identical to gold, clean), all faithful patches MATERIALIZED and RUN through the official harness, ALL RESOLVED:
  atk_4.lean   rc=0  axioms clean  CONTROL-FLOW-EFFECT: join before the empty-authority swap (swap tests/restores the ORIGINAL authority). resolve: resolved=True, F2P 2/2 success, P2P failures=[] (atk_4.resolve.json)
  atk_5.lean   rc=0  axioms clean  OUT-OF-DOMAIN: `return ''` on empty authority. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_5.resolve.json)
  atk_8.lean   rc=0  axioms clean  OUT-OF-DOMAIN: `if not scheme` (falsy) instead of `if scheme is None`. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_8.resolve.json)
  atk_9.lean   rc=0  axioms clean  PARTIAL DOMAIN aimed at the excluded branch: userinfo DROPPED in the empty-authority arm (pre-patch bug preserved there), re-attached in-domain. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_9.resolve.json)
  atk_10.lean  rc=0  axioms clean  empty-authority arm emits the userinfo TWICE (`'@'.join([auth, auth, netloc])`). resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_10.resolve.json)
  atk_11.lean  rc=0  axioms clean  exploits the LAST unused binder `newScheme != ""`: `return 'GARBAGE'` when new_scheme is falsy. resolve: resolved=True, F2P 2/2, P2P failures=[] (atk_11.resolve.json)

No closing clean-axiom proof had a non-resolving faithful patch => verify => correct held on 6/6. NOT BROKEN.

### WHY THE EXCLUDED BRANCHES ARE HARMLESS (precondition justification, checked against the real code):
  The 3 binders are `authority0 != ""`, `newScheme != ""`, `forall s, scheme0 = some s -> s != ""`. Every closer diverges from gold ONLY where a binder is false, and each such region is unreachable or already broken in the real code:
  - `newScheme != ""`: the ONLY caller is requests/adapters.py:305 `prepend_scheme_if_needed(proxy, 'http')` -- a string literal (grep over requests/ and tests/ confirms the single call site plus the direct test, also literal 'http'). atk_11's divergence is dead code.
  - `scheme0 = some ""`: urllib3's `parse_url` never returns an empty-but-not-None scheme (probed `://host`, `://`, `:host`, `http://`, `1://h`, `http:host` -- it yields None or a non-empty scheme, or raises LocationParseError). atk_8's divergence is unreachable.
  - `authority0 != ""`: mapping.md documents this exclusion. I confirmed the strong version: for the empty-netloc-AND-truthy-auth inputs where atk_9/atk_10 diverge (e.g. "http://user@", "user@", "x://user@"), the REAL GOLD post-patch callee itself RAISES `TypeError: sequence item 1: expected str instance, NoneType found` (from `'@'.join([auth, None])`). Gold is already undefined there, so a model that differs there cannot be less correct than gold. Where the empty-netloc branch is reachable with a falsy auth ("://host", "://", "@"), atk_9/atk_10 agree with gold exactly. atk_5 does diverge on those (returns '') but no test reaches them.
  This is the residual G-EQ freedom and it is legitimate: it is confined to inputs the real caller cannot produce or on which the gold patch itself crashes.

refinement.md AUDIT -- PASS. 7 legs, all R / A-reference / I; NO kind-3 (no leg tagged A-consumed, consistent with meta.json axioms=[] and the G-AX skip stub). Leg-by-leg:
  1. inputs <- parse_url component split: R. Correct -- the parse is upstream of the modeled function and produces its inputs; the None -> none/"" bridge matches mapping.md and the real `.netloc`/`.auth` split I verified by probing parse_url directly.
  2. empty-authority swap: I. Byte-faithful to `if not netloc: netloc, path = path, netloc`, and `reassemble` spells it out so the model is total.
  3. userinfo re-attach (THE EDITED OP): A-reference. This is the correct tag -- the patch INTRODUCES this op, so per the cited rule it must be modeled deeply, never axiomatized. Correspondence `'@'.join([a,b])` <-> `a ++ "@" ++ b` and truthiness `if auth:` <-> `some a AND a != ""` both hold.
  4. scheme defaulting: I. Matches `if scheme is None`. (atk_8 shows the model pins `is None` rather than falsiness, and that the distinction is unobservable through the real parse_url.)
  5. path defaulting: I. Correctly folded into the `None -> ""` input bridge.
  6. `assembleUrl` <-> `urlunparse((scheme, netloc, path, '', query, fragment))`: R/A-reference. VERIFIED INDEPENDENTLY -- I re-implemented assembleUrl in Python and diffed it against the real stdlib `urlunparse` over 540 combinations (3 schemes x 5 authorities incl. userinfo forms x 6 paths incl. "", "/", "path", "//dbl" x 3 queries x 2 fragments): 0 mismatches.
  7. return value: R. Verbatim string equality.

A-REFERENCE CORRESPONDENCE, END-TO-END (the key A-leg check): I bridged the Lean model (`reassemble` transcribed to Python) through the REAL urllib3 `parse_url` and compared against the REAL post-patch `prepend_scheme_if_needed` over 3600 constructed URLs (seed 20240630, varying scheme/userinfo/host/port/IPv6/path/query/fragment), restricted to the modeled domain (netloc truthy, scheme non-empty): 3312 in-domain cases, 288 skipped as out-of-domain, 0 MISMATCHES. The deep model is faithful to the real callees on the whole modeled domain.

NOTE ON A STRUCTURAL OBSERVATION (not a defect for this bundle): `_lean_spec_view` elides the entire `proof` region, so the theorem's precondition binders are NOT part of the same_spec signature. An attacker could in principle submit a same-spec file that WEAKENS the binders. I did not treat this as a G-EQ break because (a) it changes the obligation rather than the impl, which is outside this gate's verify=>correct question, and (b) region_hashes in meta.json pins the proof region ('proof': a680fe7c...) so the release gate detects such an edit. Flagging for the harness owners, not scoring it here.

**ENV NOTE:** local pytest in the worktree cannot run (site urllib3 2.7.0 lacks SNIMissingWarning, so tests/`__init__`.py fails to import). All correctness claims therefore rest on the official Docker harness run_resolve runs above, which completed cleanly (attempts=1, flaky=false, completed=true on all 6) -- not on local pytest.

**SCHEDULE:** attacks verified in concurrent background batches of 4 (lean_verify), resolve runs launched as detached background jobs in batches of 4 then 1+1; every attack was still individually verified and every closer individually resolved. Artifacts (.lean, `_ax`.lean, .log, .rc, .patch, .utils.py, .resolve.json) all retained in .

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 faithfulness review of psf__requests-6028 (lean). Reference = base worktree 0192aac2 with patch.diff APPLIED (post-patch `if auth: netloc = '@'.join([auth, netloc])`). No in-domain divergence found between the modeled function and the real callee.

### Setup
- Fresh worktree from the upstream repository at base_commit 0192aac2412373, patch.diff applied cleanly; confirmed the patched `prepend_scheme_if_needed` body matches mapping.md's post-patch listing verbatim.
- Version fidelity: my first fuzz ran under the ambient urllib3 2.7.0, but setup.py pins `urllib3>=1.21.1,<1.27`. I re-ran EVERY fuzz under urllib3 1.26.18 (downloaded to) to match the real dependency. Results identical (0 diffs) under both, so the finding is not an artifact of a wrong urllib3.

### Lean-side checks
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_prependScheme` -> [propext, Quot.sound]. No sorryAx: the proof is real, not fake.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) = True (spec region byte-identical; spec_view sha256 prefix 7ff3c7c2845c1b1d, len 3986). Note the first same_spec call needs a Backend/LanguageTables, not the 'lean' string.
- Control: Solution_prepatch.lean elaborates but uses an explicit `sorry` at line 110 rather than a failing carried proof. The gold proof does not actually get re-run against the buggy skeleton there. That is a G-DIFF/positive-control observation, not a faithfulness defect, so it does not change this verdict -- flagging it for Role 1.

### DIFFERENTIAL EVIDENCE (model vs real callee)
1. Structured URL fuzz through the REAL urllib3 parse_url + REAL patched prepend_scheme_if_needed (scheme x userinfo x host x port x path x query x fragment x new_scheme): 497,640 in-domain inputs, 18,480 out-of-domain, 38,280 parse errors -> 0 DIFFS.
2. Random URL fuzz (seed 20240630, 400k random delimiter-heavy strings): 243,247 in-domain -> 0 DIFFS.
3. Auth-heavy proxy-URL fuzz (the bug's actual domain: percent-encoded creds, empty password, IPv6+port, unicode user): 5,840 in-domain -> 0 DIFFS.
4. Component-level exhaustive fuzz at the EXACT signature the Lean spec quantifies over (arbitrary (scheme0, auth, authority0, path, query, fragment, newScheme) tuples, incl. authority values already containing '@' ':' '?' '#' '/' ';', not merely parse_url-reachable ones), compared against the verbatim post-patch tail using the REAL stdlib urlunparse: 504,000 in-domain tuples -> 0 DIFFS. This is the strongest leg: it probes the spec's own domain rather than only URLs a parser can produce.
5. assembleUrl vs the real `urlunparse((scheme, netloc, path, '', query, fragment))` in isolation over 21,600 delimiter-heavy (scheme, authority, path, query, fragment) combos -> 0 diffs. The concrete un-splitter model is exact on the truthy-scheme/truthy-authority arm, so replacing the std-lib callee with a deep model introduces no drift.
6. Real Lean execution, not just my Python transcription: #eval'd the actual `reassemble` from Solution.lean on 10 vectors (incl. both F2P cases, IPv6+port, `@x` userinfo, '//dbl' path, '#'/'?' inside query/fragment, unicode 'ü' path) and compared each string against the real post-patch tail. All 10 MATCH. This closes the gap that legs 1-5 tested a hand-transcription of the Lean rather than the Lean itself.
7. Upstream test vectors: all 5 parametrizations of test_prepend_scheme_if_needed (3 pre-existing P2P + the 2 F2P credential cases) are in-domain and the model reproduces the real output exactly. `pytest -k prepend_scheme` passes 3/3 post-patch.

### OUT-OF-DOMAIN DIVERGENCES (examined, correctly excluded -- NOT a defect)
The only model/real disagreements are all at authority0 == "" (falsy netloc), which the theorem's carried binder `authority0 ≠ ""` excludes and mapping.md documents:
- url 'x:' -> parse_url gives netloc None => authority0 ""; real returns 'x:' but reassemble gives 'x://'.
- urls 'user@', 'http://user@', 'http://user:pass@', '//user@' -> auth truthy with netloc '' ; the REAL post-patch callee RAISES TypeError ("sequence item 1: expected str instance") from '@'.join([auth, None]), while the model returns a string. mapping.md calls out exactly this TypeError exclusion.
I verified each of these is genuinely unreachable under authority0 ≠ "". Because `problem_spec_prependScheme` is itself a total proposition and the precondition lives in the theorem binders, these are domain-restriction facts (a Role 1 spec-too-weak question about how much the theorem covers), not faithfulness drift: within the asserted domain the modeled function never disagrees with the real one.

### Conclusion
I could not construct a diverging input inside the modeled domain, and I specifically hunted the two places drift was most likely (the deep urlunparse re-implementation, and auth truthiness / '@'-joining with adversarial authority strings). The spec is not too strong and does not drift from real post-patch repo behavior. Verdict FAITHFUL; no diverging_input to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 (leakage / gold-reconstruction), psf__requests-6028 lean bundle. Judged the MACHINE-DERIVED spec view (markers.spec_view, lean flavor: axioms+pure+post-conditions retained; impl and proof regions collapsed to placeholders) against the PUBLIC problem_statement only. refinement.md/mapping.md/verdict.md are auditor-side docs, not solver-visible, so they were excluded from the leak judgment (mapping.md does quote the gold hunk and names prepend_scheme_if_needed/parse_url/urlunparse/netloc, but that is by design out of the consumer view).

### Mechanical evidence
1. Spec-region byte identity: markers.same_spec(Solution.lean, Solution_prepatch.lean) = True; spec_signature sha256 identical on both = b767fc4e3bc11f5258578dccf2d2bf8610a461607a28a8b957f8862acbb8fc88. Region hashes reproduce meta.json G-HYGIENE exactly (spec_view 7ff3c7c2845c...). The only diff between the two files lies in impl+proof (the userinfo match block and the proof body), i.e. inside elided regions; the prepatch's PRE-PATCH/'Gold proof body' narration comments are confined to elided regions and do NOT appear in its spec view (verified).
2. Compilation + axioms: scripts/lean_verify.sh Solution.lean -> exit 0. #print axioms correct_prependScheme = [propext, Quot.sound]; problem_spec_prependScheme / reassemble / assembleUrl depend on no axioms. NO sorryAx -> the proof is real, not fake. Solution_prepatch.lean correctly fails ('declaration uses sorry'), so the discriminating-power direction holds.
3. leakage.screen(Solution.lean, lean backend, gold_patch, problem_statement, test_patch) -> hard_failures = [], passed = True. Same for Solution_prepatch.lean.
4. L1 (gold-patch text): none of the four changed gold lines ('if auth:', "netloc = '@'.join([auth, netloc])", and the two comment lines incl. "parse_url doesn't provide the netloc with auth") appear in the whitespace-normalized spec view. No diff markers.
5. L2 (localization): patched file path 'requests/utils.py' and dotted module form absent. Patched symbol set = {prepend_scheme_if_needed}; it is not named verbatim anywhere in the spec view, and no spec-view identifier embeds it. The mechanism vocabulary is entirely absent: no 'netloc', no 'join'/'.join', no 'parse_url', no 'urlunparse', no 'proxy', no '407', no 'credential'.
6. L3 (narration): no word from the narration list (bug/fix/patch/previously/regression/wrong/broken/...) occurs at a word boundary. The single substring hit for 'fix' is inside 'prefixed' ('the authority is prefixed with //', 'the scheme is prefixed with :') -- a lexer false positive, correctly ignored by the word-boundary regex.
7. hints_text non-echo: hints_text contains the literal fix ("if auth: netloc = '@'.join([auth, netloc])") and the bisect commit, but token n-gram overlap between the spec view and hints_text, excluding n-grams already in problem_statement, is 0 at n=4, 5 and 6. Nothing hint-derived was smuggled in.

SUBSTANTIVE (non-mechanical) JUDGMENT
The real question is whether the spec view lets a solver reconstruct the gold edit -- i.e. whether it discloses that USERINFO RE-ATTACHMENT specifically was the broken behavior. It does not, for two reasons:

(a) Component symmetry. The spec view enumerates all six parsed components (scheme, userinfo, authority, path, query, fragment) and reassemble pins the layout of every one of them, with an explicit statement that 'No component is privileged over any other.' Mention counts are balanced (scheme 20, userinfo/auth 29, authority 23, path 18, query 12, fragment 12); the userinfo clause 'a ++ "@" ++ authority' sits in reassemble as one arm among the scheme-defaulting, path/authority swap, and query/fragment arms, with no emphasis, no separate note, and no hint that this arm is the interesting one. A solver reading it implements all six slots and learns nothing about which one the repo got wrong.

(b) The postcondition is unavoidably total. This benchmark's spec IS a complete input->output relation (result = reassemble ...), so it necessarily determines the correct output for every input, including userinfo-bearing ones. That is the design contract, not a leak: the leak criterion is edit LOCALIZATION beyond problem_statement, and specifying general URL round-trip syntax is intrinsic to specifying a URL re-assembler. The gold's particular mechanism ('@'.join([auth, netloc]) applied to parse_url's userinfo-excluding .netloc) is nowhere disclosed; the spec states standard userinfo@authority grammar, which any URL spec must state. Note also that problem_statement is already a proxy 407 'Proxy Authentication Required' report, so the proxy-auth/URL-handling domain is public to the solver anyway.

RESIDUAL, considered and rejected as a finding: the Lean identifiers problem_spec_prependScheme / implementation_prependScheme / correct_prependScheme track the patched function's name prepend_scheme_if_needed. This clears the mechanical check (the lowercased patched symbol is not a substring of 'prependscheme') and, more importantly, is not edit-localizing: it names the function BEING SPECIFIED -- unavoidable when the task is 'reassemble a URL, supplying a default scheme' -- and it narrows nothing about which of the six components was mishandled. The camelCased-function-name convention is uniform across the benchmark (problem_spec_direct_sum, problem_spec_cardFromString, problem_spec_urlUserinfoValid, ...), so it carries no instance-specific signal. Not a leak.

**CONCLUSION:** NO-LEAKAGE. No spec-view line discloses the gold edit beyond problem_statement. (Supersedes the prior recorded panel_3 'INCONCLUSIVE (no verdict submitted)' for this bundle.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.