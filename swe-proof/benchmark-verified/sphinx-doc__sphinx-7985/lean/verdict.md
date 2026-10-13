# P2 adversarial audit — sphinx-doc__sphinx-7985

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,11 +104,11 @@
     if hasUriScheme uri then
       return LinkStatus.unchecked
     else
-      if localFileExists then
-        return LinkStatus.working
+      if ignoreMatch then
+        return LinkStatus.ignored
       else
-        if ignoreMatch then
-          return LinkStatus.ignored
+        if localFileExists then
+          return LinkStatus.working
         else
           return LinkStatus.broken
   return httpResult
@@ -122,13 +122,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,16 +101,7 @@
   if uri.isEmpty || startsWithHashMailto uri then
     return LinkStatus.unchecked
   if !startsWithHttp uri then
-    if hasUriScheme uri then
-      return LinkStatus.unchecked
-    else
-      if localFileExists then
-        return LinkStatus.working
-      else
-        if ignoreMatch then
-          return LinkStatus.ignored
-        else
-          return LinkStatus.broken
+    return LinkStatus.broken
   return httpResult
 -- impl-end
 
@@ -122,13 +113,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -111,7 +111,7 @@
           return LinkStatus.ignored
         else
           return LinkStatus.broken
-  return httpResult
+  return LinkStatus.redirected
 -- impl-end
 
 -- proof-start
@@ -122,13 +122,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,16 +101,13 @@
   if uri.isEmpty || startsWithHashMailto uri then
     return LinkStatus.unchecked
   if !startsWithHttp uri then
-    if hasUriScheme uri then
-      return LinkStatus.unchecked
+    if localFileExists then
+      return LinkStatus.working
     else
-      if localFileExists then
-        return LinkStatus.working
+      if ignoreMatch then
+        return LinkStatus.ignored
       else
-        if ignoreMatch then
-          return LinkStatus.ignored
-        else
-          return LinkStatus.broken
+        return LinkStatus.broken
   return httpResult
 -- impl-end
 
@@ -122,13 +119,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
 def implementation_checkLink
     (uri : List Char) (localFileExists ignoreMatch : Bool)
     (httpResult : LinkStatus) : LinkStatus := Id.run do
-  if uri.isEmpty || startsWithHashMailto uri then
+  if uri.isEmpty || startsWithHashMailto uri || "ftp:".toList.isPrefixOf uri then
     return LinkStatus.unchecked
   if !startsWithHttp uri then
     if hasUriScheme uri then
@@ -122,13 +122,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
         if ignoreMatch then
           return LinkStatus.ignored
         else
-          return LinkStatus.broken
+          return httpResult
   return httpResult
 -- impl-end
 
@@ -122,13 +122,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
 def implementation_checkLink
     (uri : List Char) (localFileExists ignoreMatch : Bool)
     (httpResult : LinkStatus) : LinkStatus := Id.run do
-  if uri.isEmpty || startsWithHashMailto uri then
+  if startsWithHashMailto uri then
     return LinkStatus.unchecked
   if !startsWithHttp uri then
     if hasUriScheme uri then
@@ -122,13 +122,5 @@
   intro uri localFileExists ignoreMatch httpResult
   unfold problem_spec_checkLink implementation_checkLink
   simp only [Id.run, bind, pure]
-  split <;> rename_i h1
-  · rfl
-  · split <;> rename_i h2
-    · split <;> rename_i h3
-      · rfl
-      · split <;> rename_i h4
-        · rfl
-        · split <;> rfl
-    · rfl
+  split_ifs <;> first | rfl | simp_all | grind
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Network-free classification of a single hyperlink reference.

A documentation hyperlink checker, before contacting any server, classifies a
reference string by inspecting only the string itself plus two purely local
observations. The classification yields one of a closed set of outcomes:

* references that the checker deliberately skips (empty, in-page anchors, and
  mail addresses) are reported as `.unchecked`;
* a reference that does NOT denote a web resource (it has no `http`/`https`
  prefix) is classified locally:
    - if it carries an explicit URI scheme of the shape "letters followed by
      `://`" (e.g. a transfer scheme other than the web ones), the checker has
      no way to inspect it and reports `.unchecked`;
    - otherwise it is treated as a path relative to the source tree: if that
      path is present the reference is reported as working; if the path is
      absent, it is reported as ignored when it matches one of the configured
      skip patterns, and as an unresolved/missing target when it matches none;
* a reference that DOES denote a web resource is handed to the (unchanged)
  network-resolution stage, whose outcome is taken as given here.

The reference is modeled per code point as `List Char`. The presence of the
relative path in the source tree and a match against the skip-pattern set are
each a single boolean observation. The outcome of the web-resolution stage is
likewise taken as a given status value.
-/

-- axioms-start
-- No unchanged callee is consumed as a proof axiom. The local-path presence
-- check and the skip-pattern match are abstracted to the boolean observations
-- `localFileExists` / `ignoreMatch` (consumed directly by the impl); the
-- explicit-scheme test is modeled deeply below (`hasUriScheme`), validated
-- equal to the real matcher by G-AX (A-reference); the web-resolution stage is
-- abstracted to its observed status `httpResult` and frame-pinned.
-- axioms-end

-- pure-start
/-- The classification outcome of a hyperlink reference. -/
inductive LinkStatus
  | unchecked
  | working
  | broken
  | ignored
  | localLink
  | redirected
deriving DecidableEq, Repr

/-- Whether a character is a lowercase ASCII letter. -/
def isLower (c : Char) : Bool := decide ('a' ≤ c ∧ c ≤ 'z')

/-- A reference the checker deliberately skips by prefix: an in-page anchor or a
mail address. -/
def startsWithHashMailto (uri : List Char) : Bool :=
  ['#'].isPrefixOf uri || "mailto:".toList.isPrefixOf uri

/-- A reference that denotes a web resource. -/
def startsWithHttp (uri : List Char) : Bool :=
  "http:".toList.isPrefixOf uri || "https:".toList.isPrefixOf uri

/-- Whether the reference begins with an explicit URI scheme of the shape
"one-or-more lowercase letters immediately followed by `://`". The leading
lowercase run is maximal, so the only candidate is the maximal lowercase prefix
followed directly by `://`. -/
def hasUriScheme (uri : List Char) : Bool :=
  let run := uri.takeWhile isLower
  !run.isEmpty && "://".toList.isPrefixOf (uri.dropWhile isLower)
-- pure-end

-- post-conditions-start
/-- Specification of the network-free classification.

`localFileExists` is whether the reference, taken as a source-relative path, is
present; `ignoreMatch` is whether it matches a configured skip pattern;
`httpResult` is the outcome the web-resolution stage would report. Every branch
pins the result completely (frame discipline). -/
def problem_spec_checkLink
    (uri : List Char) (localFileExists ignoreMatch : Bool) (httpResult : LinkStatus)
    (result : LinkStatus) : Prop :=
  if uri.isEmpty || startsWithHashMailto uri then
    result = LinkStatus.unchecked
  else if !startsWithHttp uri then
    if hasUriScheme uri then
      result = LinkStatus.unchecked
    else if localFileExists then
      result = LinkStatus.working
    else if ignoreMatch then
      result = LinkStatus.ignored
    else
      result = LinkStatus.broken
  else
    result = httpResult
-- post-conditions-end

-- impl-start
def implementation_checkLink
    (uri : List Char) (localFileExists ignoreMatch : Bool)
    (httpResult : LinkStatus) : LinkStatus := Id.run do
  if uri.isEmpty || startsWithHashMailto uri then
    return LinkStatus.unchecked
  if !startsWithHttp uri then
    if hasUriScheme uri then
      return LinkStatus.unchecked
    else
      if localFileExists then
        return LinkStatus.working
      else
        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.broken
  return httpResult
-- impl-end

-- proof-start
theorem correct_checkLink :
    ∀ (uri : List Char) (localFileExists ignoreMatch : Bool) (httpResult : LinkStatus),
      problem_spec_checkLink uri localFileExists ignoreMatch httpResult
        (implementation_checkLink uri localFileExists ignoreMatch httpResult) := by
  intro uri localFileExists ignoreMatch httpResult
  unfold problem_spec_checkLink implementation_checkLink
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · rfl
  · split <;> rename_i h2
    · split <;> rename_i h3
      · rfl
      · split <;> rename_i h4
        · rfl
        · split <;> rfl
    · rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit (refinement fidelity) for sphinx-doc__sphinx-7985 / lean.

SPEC SHAPE: problem_spec_checkLink is a total, deterministic function-graph. Its mutually-exclusive, exhaustive if/else-if branches each PIN result to exactly one concrete LinkStatus (.unchecked/.working/.ignored/.broken) or exactly to the frame input httpResult. No True, no disjunction, no unconstrained branch. Consequently any impl whose correct_ proof closes must agree with the pinned output on every input tuple => extensionally identical to the reference => resolves. This is the structural reason no closing-but-non-resolving impl can exist.

SAME-SPEC: swebench_unified.markers.same_spec == True for all 7 attacks + atk_pos + atk_prepatch (byte-identical spec/pure/axioms regions; only impl region edited).

POSITIVE CONTROL: atk_pos.lean (gold) -> `bash scripts/lean_verify.sh atk_pos.lean` EXIT=0. `#print axioms correct_checkLink` -> "does not depend on any axioms" (clean; no sorryAx). Fair-closer control: the generic proof tail used across attacks (intro; unfold; simp only [Id.run,bind,pure]; split_ifs <;> first | rfl | simp_all | grind) CLOSES the correct impl (atk_tailcheck.lean EXIT=0) — so exit-1 on the wrong impls is a genuine unprovable-goal rejection, NOT a weak-tactic artifact.

### ATTACKS (all same-spec; cmd `bash scripts/lean_verify.sh atkN.lean`; all EXIT=1, i.e. proof does NOT close):
 - atk1 (control-flow priority swap: ignoreMatch checked BEFORE localFileExists) -> unsolved `⊢ False` under localFileExists=true ∧ ignoreMatch=true (spec forces .working regardless of ignoreMatch).
 - atk2 (constant .broken on whole non-web branch) -> unsolved `⊢ False` on hasUriScheme/localFileExists sub-branches (needs .unchecked/.working).
 - atk3 (ungrounded web branch: return .redirected instead of httpResult) -> unsolved `⊢ LinkStatus.redirected = httpResult` for free httpResult.
 - atk4 (partial-domain: omit the hasUriScheme/.unchecked branch) -> unsolved `⊢ False` on scheme inputs (spec demands .unchecked).
 - atk5 (prepatch-flavored: fold `ftp:` back into the unchecked skip set) -> unsolved `⊢ False` where an ftp:-prefixed local path must classify by localFileExists/ignoreMatch/broken, not .unchecked.
 - atk6 (ungrounded-oracle echo: return httpResult on the broken branch) -> unsolved `⊢ httpResult = LinkStatus.broken` for free httpResult.
 - atk7 (boundary: drop uri.isEmpty from the skip guard) -> unsolved `⊢ False` for uri=[] (empty must be .unchecked).

No wrong impl closes with clean axioms => the step-2 obligation (materialize faithful patch + run_resolve for every closing impl) is VACUOUS: there is no closing-but-non-resolving impl to exhibit. patches={} accordingly.

PREPATCH REPRODUCED: atk_prepatch.lean (real pre-patch check(): ftp: in skip set, entire non-web branch collapses to .localLink) with a REAL proof attempt (not sorry) -> lean_verify EXIT=1, unsolved goals `⊢ False` (e.g. conf.py+localFileExists=true demands .working; path/to/notfound demands .broken) and `⊢ LinkStatus.unchecked = httpResult`. The frozen spec rejects the buggy pre-patch behavior — confirms G-DIFF and that the spec demands post-patch behavior.

REFINEMENT AUDIT (refinement.md): 7 legs, all R / A-reference / I — NO kind-3 (no inexpressible/ungrounded op), NO consumed _prop axiom. Legs: #1 skip-prefix guard R (ftp: omission modeled by omission, handled by #3); #2 !startsWithHttp guard R; #3 hasUriScheme A-reference (deep model of [a-z]+://); #4 localFileExists R (bridged bit); #5 ignoreMatch R (bridged bit); #6 .broken I; #7 httpResult web branch R (frame-pinned abstraction of the UNCHANGED downstream subtree). The lone A-leg #3 correspondence to the real callee `re.compile('[a-z]+://').match` VERIFIED: axiom_check.py (G-AX) EXIT=0 ("model == re.compile('[a-z]+://').match over all probes"), plus my independent adversarial edge-case probe (uppercase runs, digit interleaving, partial ://, unicode, whitespace, 100-char runs) -> 0 mismatches. The maximal-lowercase-run + literal-`://` model is provably equivalent to the start-anchored backtracking regex (shortening the [a-z]+ run only exposes another lowercase char, never a ':').

VERDICT: SOUND. 8 verifications run (7 wrong impls + prepatch), none breaks the spec; positive control verifies clean; the sole A-reference leg is validated; refinement legs are all R/A-reference/I with holding correspondence. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Network-free classification of a single hyperlink reference.

A documentation hyperlink checker, before contacting any server, classifies a
reference string by inspecting only the string itself plus two purely local
observations. The classification yields one of a closed set of outcomes:

* references that the checker deliberately skips (empty, in-page anchors, and
  mail addresses) are reported as `.unchecked`;
* a reference that does NOT denote a web resource (it has no `http`/`https`
  prefix) is classified locally:
    - if it carries an explicit URI scheme of the shape "letters followed by
      `://`" (e.g. a transfer scheme other than the web ones), the checker has
      no way to inspect it and reports `.unchecked`;
    - otherwise it is treated as a path relative to the source tree: if that
      path is present the reference is reported as working; if the path is
      absent, it is reported as ignored when it matches one of the configured
      skip patterns, and as an unresolved/missing target when it matches none;
* a reference that DOES denote a web resource is handed to the (unchanged)
  network-resolution stage, whose outcome is taken as given here.

The reference is modeled per code point as `List Char`. The presence of the
relative path in the source tree and a match against the skip-pattern set are
each a single boolean observation. The outcome of the web-resolution stage is
likewise taken as a given status value.
-/

-- axioms-start
-- No unchanged callee is consumed as a proof axiom. The local-path presence
-- check and the skip-pattern match are abstracted to the boolean observations
-- `localFileExists` / `ignoreMatch` (consumed directly by the impl); the
-- explicit-scheme test is modeled deeply below (`hasUriScheme`), validated
-- equal to the real matcher by G-AX (A-reference); the web-resolution stage is
-- abstracted to its observed status `httpResult` and frame-pinned.
-- axioms-end

-- pure-start
/-- The classification outcome of a hyperlink reference. -/
inductive LinkStatus
  | unchecked
  | working
  | broken
  | ignored
  | localLink
  | redirected
deriving DecidableEq, Repr

/-- Whether a character is a lowercase ASCII letter. -/
def isLower (c : Char) : Bool := decide ('a' ≤ c ∧ c ≤ 'z')

/-- A reference the checker deliberately skips by prefix: an in-page anchor or a
mail address. -/
def startsWithHashMailto (uri : List Char) : Bool :=
  ['#'].isPrefixOf uri || "mailto:".toList.isPrefixOf uri

/-- A reference that denotes a web resource. -/
def startsWithHttp (uri : List Char) : Bool :=
  "http:".toList.isPrefixOf uri || "https:".toList.isPrefixOf uri

/-- Whether the reference begins with an explicit URI scheme of the shape
"one-or-more lowercase letters immediately followed by `://`". The leading
lowercase run is maximal, so the only candidate is the maximal lowercase prefix
followed directly by `://`. -/
def hasUriScheme (uri : List Char) : Bool :=
  let run := uri.takeWhile isLower
  !run.isEmpty && "://".toList.isPrefixOf (uri.dropWhile isLower)
-- pure-end

-- post-conditions-start
/-- Specification of the network-free classification.

`localFileExists` is whether the reference, taken as a source-relative path, is
present; `ignoreMatch` is whether it matches a configured skip pattern;
`httpResult` is the outcome the web-resolution stage would report. Every branch
pins the result completely (frame discipline). -/
def problem_spec_checkLink
    (uri : List Char) (localFileExists ignoreMatch : Bool) (httpResult : LinkStatus)
    (result : LinkStatus) : Prop :=
  if uri.isEmpty || startsWithHashMailto uri then
    result = LinkStatus.unchecked
  else if !startsWithHttp uri then
    if hasUriScheme uri then
      result = LinkStatus.unchecked
    else if localFileExists then
      result = LinkStatus.working
    else if ignoreMatch then
      result = LinkStatus.ignored
    else
      result = LinkStatus.broken
  else
    result = httpResult
-- post-conditions-end

-- impl-start
def implementation_checkLink
    (uri : List Char) (localFileExists ignoreMatch : Bool)
    (httpResult : LinkStatus) : LinkStatus := Id.run do
  if uri.isEmpty || startsWithHashMailto uri then
    return LinkStatus.unchecked
  if !startsWithHttp uri then
    if hasUriScheme uri then
      return LinkStatus.unchecked
    else
      if localFileExists then
        return LinkStatus.working
      else
        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.broken
  return httpResult
-- impl-end

-- proof-start
theorem correct_checkLink :
    ∀ (uri : List Char) (localFileExists ignoreMatch : Bool) (httpResult : LinkStatus),
      problem_spec_checkLink uri localFileExists ignoreMatch httpResult
        (implementation_checkLink uri localFileExists ignoreMatch httpResult) := by
  intro uri localFileExists ignoreMatch httpResult
  unfold problem_spec_checkLink implementation_checkLink
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · rfl
  · split <;> rename_i h2
    · split <;> rename_i h3
      · rfl
      · split <;> rename_i h4
        · rfl
        · split <;> rfl
    · rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit (refinement fidelity) for sphinx-doc__sphinx-7985 / lean.

SPEC SHAPE: problem_spec_checkLink is a total, deterministic function-graph. Its mutually-exclusive, exhaustive if/else-if branches each PIN result to exactly one concrete LinkStatus (.unchecked/.working/.ignored/.broken) or exactly to the frame input httpResult. No True, no disjunction, no unconstrained branch. Consequently any impl whose correct_ proof closes must agree with the pinned output on every input tuple => extensionally identical to the reference => resolves. This is the structural reason no closing-but-non-resolving impl can exist.

SAME-SPEC: swebench_unified.markers.same_spec == True for all 7 attacks + atk_pos + atk_prepatch (byte-identical spec/pure/axioms regions; only impl region edited).

POSITIVE CONTROL: atk_pos.lean (gold) -> `bash scripts/lean_verify.sh atk_pos.lean` EXIT=0. `#print axioms correct_checkLink` -> "does not depend on any axioms" (clean; no sorryAx). Fair-closer control: the generic proof tail used across attacks (intro; unfold; simp only [Id.run,bind,pure]; split_ifs <;> first | rfl | simp_all | grind) CLOSES the correct impl (atk_tailcheck.lean EXIT=0) — so exit-1 on the wrong impls is a genuine unprovable-goal rejection, NOT a weak-tactic artifact.

### ATTACKS (all same-spec; cmd `bash scripts/lean_verify.sh atkN.lean`; all EXIT=1, i.e. proof does NOT close):
 - atk1 (control-flow priority swap: ignoreMatch checked BEFORE localFileExists) -> unsolved `⊢ False` under localFileExists=true ∧ ignoreMatch=true (spec forces .working regardless of ignoreMatch).
 - atk2 (constant .broken on whole non-web branch) -> unsolved `⊢ False` on hasUriScheme/localFileExists sub-branches (needs .unchecked/.working).
 - atk3 (ungrounded web branch: return .redirected instead of httpResult) -> unsolved `⊢ LinkStatus.redirected = httpResult` for free httpResult.
 - atk4 (partial-domain: omit the hasUriScheme/.unchecked branch) -> unsolved `⊢ False` on scheme inputs (spec demands .unchecked).
 - atk5 (prepatch-flavored: fold `ftp:` back into the unchecked skip set) -> unsolved `⊢ False` where an ftp:-prefixed local path must classify by localFileExists/ignoreMatch/broken, not .unchecked.
 - atk6 (ungrounded-oracle echo: return httpResult on the broken branch) -> unsolved `⊢ httpResult = LinkStatus.broken` for free httpResult.
 - atk7 (boundary: drop uri.isEmpty from the skip guard) -> unsolved `⊢ False` for uri=[] (empty must be .unchecked).

No wrong impl closes with clean axioms => the step-2 obligation (materialize faithful patch + run_resolve for every closing impl) is VACUOUS: there is no closing-but-non-resolving impl to exhibit. patches={} accordingly.

PREPATCH REPRODUCED: atk_prepatch.lean (real pre-patch check(): ftp: in skip set, entire non-web branch collapses to .localLink) with a REAL proof attempt (not sorry) -> lean_verify EXIT=1, unsolved goals `⊢ False` (e.g. conf.py+localFileExists=true demands .working; path/to/notfound demands .broken) and `⊢ LinkStatus.unchecked = httpResult`. The frozen spec rejects the buggy pre-patch behavior — confirms G-DIFF and that the spec demands post-patch behavior.

REFINEMENT AUDIT (refinement.md): 7 legs, all R / A-reference / I — NO kind-3 (no inexpressible/ungrounded op), NO consumed _prop axiom. Legs: #1 skip-prefix guard R (ftp: omission modeled by omission, handled by #3); #2 !startsWithHttp guard R; #3 hasUriScheme A-reference (deep model of [a-z]+://); #4 localFileExists R (bridged bit); #5 ignoreMatch R (bridged bit); #6 .broken I; #7 httpResult web branch R (frame-pinned abstraction of the UNCHANGED downstream subtree). The lone A-leg #3 correspondence to the real callee `re.compile('[a-z]+://').match` VERIFIED: axiom_check.py (G-AX) EXIT=0 ("model == re.compile('[a-z]+://').match over all probes"), plus my independent adversarial edge-case probe (uppercase runs, digit interleaving, partial ://, unicode, whitespace, 100-char runs) -> 0 mismatches. The maximal-lowercase-run + literal-`://` model is provably equivalent to the start-anchored backtracking regex (shortening the [a-z]+ run only exposes another lowercase char, never a ':').

VERDICT: SOUND. 8 verifications run (7 wrong impls + prepatch), none breaks the spec; positive control verifies clean; the sole A-reference leg is validated; refinement legs are all R/A-reference/I with holding correspondence. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for sphinx-doc__sphinx-7985 lean bundle. Worktree at base_commit f30284ef with gold patch applied; patch_equals_gold=True and diff byte-matches gold. Solution.lean compiles under lean_verify.sh (exit 0); `#print axioms correct_checkLink` reports NO axiom dependency (proof genuine, no sorryAx). same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with the real LeanBackend (spec region byte-identical; prepatch differs only in impl/proof and correctly fails G-DIFF). Every spec branch was checked against the real patched check() in sphinx/builders/linkcheck.py:213-231: (1) empty/#/mailto: -> unchecked (patch correctly DROPS ftp: from this set, and startsWithHashMailto omits it); (2) non-http + hasUriScheme -> unchecked, where hasUriScheme deeply models re.compile('[a-z]+://').match — validated by 400k adversarial fuzz (digits/uppercase/non-ASCII/embedded ://) with 0 mismatches and by G-AX; (3) localFileExists -> working (path.exists abstraction, sound); (4) ignoreMatch -> ignored (to_ignore loop); (5) else -> broken (for/else); (6) http/https -> httpResult, frame-pinned — the unchanged cache/check_uri subtree is soundly abstracted to its observed status, so the spec is NOT over-constrained on that branch. Branch ordering matches the Python elif chain (http URIs route to httpResult before the scheme regex). conformance_check.py differential over 200001 fuzzed inputs (real regex, bridged bits) reports zero disagreements; G-CONF and G-AX pass in meta.json. No diverging input exists on which the modeled function disagrees with the real callee. Spec is faithful and correctly scoped.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view verified byte-identical to audit: computed spec_view sha256 a3c138692d3a521567d734583fef4cf41d37585e5918cf8afd9ed3fe933982e4 == recorded G-HYGIENE spec_view hash. The panel-3 spec view = imports + docstring + axioms comment + pure block (LinkStatus/isLower/startsWithHashMailto/startsWithHttp/hasUriScheme) + post-conditions (problem_spec_checkLink); impl and proof are elided.

Lexical leakage screen over the spec view: NONE of the gold-patch identifiers or provenance appear — no 'uri_re', no 're.compile', no regex literal '[a-z]+://', no 'self.to_ignore', no 'path.exists', no 'self.srcdir', no 'linkcheck', no 'check()'/'check_thread', no 'ftp:', no file:line citations. The diff structure, the regex literal, and file:line locations live only in mapping.md / refinement.md, which are audit artifacts and NOT part of the panel-1/3 spec view.

The spec describes required post-condition behavior in fully abstracted model terms (hasUriScheme, localFileExists, ignoreMatch, httpResult, LinkStatus). The phrase 'letters followed by ://' is a behavioral description of the scheme test, not a paste of the gold's re.compile('[a-z]+://'); it does not reveal a Python-level edit. The public problem_statement already discloses the core demand (linkcheck should also check local/internal links; a broken local link must be detected and reported broken). Describing the post-condition is the legitimate, unavoidable function of a spec and does not constitute leakage of the gold edit beyond problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
