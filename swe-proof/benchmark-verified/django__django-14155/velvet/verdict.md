# P2 adversarial audit — django__django-14155

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -135,7 +135,7 @@
   ensures out = matchRepr m
   do
     -- impl-start
-    let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
+    let funcStr := m.funcPath
     return "ResolverMatch(func=" ++ funcStr ++
       ", args=" ++ m.argsText ++
       ", kwargs=" ++ m.kwargsText ++
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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -136,13 +136,15 @@
   do
     -- impl-start
     let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
+    let nameStr := match m.urlName with | none => "None" | some s => s
+    let routeStr := match m.route with | none => "None" | some s => s
     return "ResolverMatch(func=" ++ funcStr ++
       ", args=" ++ m.argsText ++
       ", kwargs=" ++ m.kwargsText ++
-      ", url_name=" ++ quotedOpt m.urlName ++
+      ", url_name=" ++ nameStr ++
       ", app_names=" ++ m.appNamesText ++
       ", namespaces=" ++ m.namespacesText ++
-      ", route=" ++ quotedOpt m.route ++ ")"
+      ", route=" ++ routeStr ++ ")"
     -- impl-end
 
 prove_correct resolverMatchRepr by
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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -139,10 +139,10 @@
     return "ResolverMatch(func=" ++ funcStr ++
       ", args=" ++ m.argsText ++
       ", kwargs=" ++ m.kwargsText ++
-      ", url_name=" ++ quotedOpt m.urlName ++
+      ", url_name=" ++ quotedOpt m.route ++
       ", app_names=" ++ m.appNamesText ++
       ", namespaces=" ++ m.namespacesText ++
-      ", route=" ++ quotedOpt m.route ++ ")"
+      ", route=" ++ quotedOpt m.urlName ++ ")"
     -- impl-end
 
 prove_correct resolverMatchRepr by
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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -136,13 +136,14 @@
   do
     -- impl-start
     let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
+    let routeStr := match m.route with | none => "" | some s => quoted s
     return "ResolverMatch(func=" ++ funcStr ++
       ", args=" ++ m.argsText ++
       ", kwargs=" ++ m.kwargsText ++
       ", url_name=" ++ quotedOpt m.urlName ++
       ", app_names=" ++ m.appNamesText ++
       ", namespaces=" ++ m.namespacesText ++
-      ", route=" ++ quotedOpt m.route ++ ")"
+      ", route=" ++ routeStr ++ ")"
     -- impl-end
 
 prove_correct resolverMatchRepr by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -135,14 +135,7 @@
   ensures out = matchRepr m
   do
     -- impl-start
-    let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
-    return "ResolverMatch(func=" ++ funcStr ++
-      ", args=" ++ m.argsText ++
-      ", kwargs=" ++ m.kwargsText ++
-      ", url_name=" ++ quotedOpt m.urlName ++
-      ", app_names=" ++ m.appNamesText ++
-      ", namespaces=" ++ m.namespacesText ++
-      ", route=" ++ quotedOpt m.route ++ ")"
+    return matchRepr m
     -- impl-end
 
 prove_correct resolverMatchRepr by
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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -135,14 +135,23 @@
   ensures out = matchRepr m
   do
     -- impl-start
+    let nameOk := match m.urlName with
+      | none => true
+      | some s => s.all (fun c => decide (c.toNat < 128))
+    let routeOk := match m.route with
+      | none => true
+      | some s => s.all (fun c => decide (c.toNat < 128))
     let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
-    return "ResolverMatch(func=" ++ funcStr ++
-      ", args=" ++ m.argsText ++
-      ", kwargs=" ++ m.kwargsText ++
-      ", url_name=" ++ quotedOpt m.urlName ++
-      ", app_names=" ++ m.appNamesText ++
-      ", namespaces=" ++ m.namespacesText ++
-      ", route=" ++ quotedOpt m.route ++ ")"
+    if nameOk && routeOk then
+      return "ResolverMatch(func=" ++ funcStr ++
+        ", args=" ++ m.argsText ++
+        ", kwargs=" ++ m.kwargsText ++
+        ", url_name=" ++ quotedOpt m.urlName ++
+        ", app_names=" ++ m.appNamesText ++
+        ", namespaces=" ++ m.namespacesText ++
+        ", route=" ++ quotedOpt m.route ++ ")"
+    else
+      return "GARBAGE"
     -- impl-end
 
 prove_correct resolverMatchRepr by
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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -136,13 +136,12 @@
   do
     -- impl-start
     let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
-    return "ResolverMatch(func=" ++ funcStr ++
-      ", args=" ++ m.argsText ++
-      ", kwargs=" ++ m.kwargsText ++
-      ", url_name=" ++ quotedOpt m.urlName ++
-      ", app_names=" ++ m.appNamesText ++
-      ", namespaces=" ++ m.namespacesText ++
+    let head := "ResolverMatch(func=" ++ funcStr
+    let mid := ", args=" ++ m.argsText ++ ", kwargs=" ++ m.kwargsText ++
+      ", url_name=" ++ quotedOpt m.urlName
+    let tail := ", app_names=" ++ m.appNamesText ++ ", namespaces=" ++ m.namespacesText ++
       ", route=" ++ quotedOpt m.route ++ ")"
+    return head ++ mid ++ tail
     -- impl-end
 
 prove_correct resolverMatchRepr by
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
 /- No consumed axioms. This operation renders a resolved-URL match object as a
@@ -136,13 +136,15 @@
   do
     -- impl-start
     let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
+    let nameStr := match m.urlName with | none => quoted "None" | some s => quoted s
+    let routeStr := match m.route with | none => quoted "None" | some s => quoted s
     return "ResolverMatch(func=" ++ funcStr ++
       ", args=" ++ m.argsText ++
       ", kwargs=" ++ m.kwargsText ++
-      ", url_name=" ++ quotedOpt m.urlName ++
+      ", url_name=" ++ nameStr ++
       ", app_names=" ++ m.appNamesText ++
       ", namespaces=" ++ m.namespacesText ++
-      ", route=" ++ quotedOpt m.route ++ ")"
+      ", route=" ++ routeStr ++ ")"
     -- impl-end
 
 prove_correct resolverMatchRepr by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. This operation renders a resolved-URL match object as a
   single human-readable text line. Every component the line is built from is
   already in hand as a value on the match record (the callable's identity and
   its two textual forms, the already-rendered argument/keyword/name-list
   components, and the optional name and route strings); there is no unchanged
   callee whose contract the proof consumes, hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable slice of a resolved-URL match that the text rendering reads:

     * `isPartialFunc`  — whether the matched callable is a partial-application
                          callable (one carrying pre-bound arguments). Such a
                          callable is shown by its full textual form so the
                          underlying callable and its bound arguments are
                          visible; an ordinary callable is shown by its
                          dotted-path form instead;
     * `funcPartialText` — the full textual form of a partial-application
                          callable (used only when `isPartialFunc`);
     * `funcPath`       — the dotted import path of an ordinary callable;
     * `argsText`       — the already-rendered positional-argument tuple;
     * `kwargsText`     — the already-rendered keyword-argument mapping;
     * `urlName`        — the optional symbolic name of the match;
     * `appNamesText`   — the already-rendered application-namespace list;
     * `namespacesText` — the already-rendered instance-namespace list;
     * `route`          — the optional route pattern string of the match.

   The two textual `func` forms and the three already-rendered list/mapping
   components are carried verbatim (mapping.md §2): they are produced by
   rendering operations this line does not itself vary. The optional name and
   route are carried as their underlying strings so the quoted form below is
   computed here. -/
structure MatchView where
  isPartialFunc : Bool
  funcPartialText : String
  funcPath : String
  argsText : String
  kwargsText : String
  urlName : Option String
  appNamesText : String
  namespacesText : String
  route : Option String
deriving DecidableEq

/- A hexadecimal digit character for a value below sixteen: `0`-`9` then
   `a`-`f` (lowercase). -/
def hexDigit (n : Nat) : Char :=
  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (87 + n)

/- One character of a quoted textual form: the escape character and the
   wrapping quote mark render escaped (preceded by the escape character);
   the tab, line-feed and carriage-return controls render as their
   two-letter escape codes; any other control character, and the delete
   character, renders as a two-hex-digit escape; every other character
   renders as itself. -/
def escChar (delim : Char) (c : Char) : String :=
  if c = '\\' then "\\\\"
  else if c = delim then "\\" ++ String.singleton delim
  else if c = '\t' then "\\t"
  else if c = '\n' then "\\n"
  else if c = '\r' then "\\r"
  else if c.toNat < 32 ∨ c.toNat = 127 then
    "\\x" ++ String.singleton (hexDigit (c.toNat / 16))
          ++ String.singleton (hexDigit (c.toNat % 16))
  else String.singleton c

/- The quoted textual form of a string value: the value wrapped in quote
   marks, each inner occurrence of the wrapping mark or the escape character
   escaped, and each control character rendered by its escape code. The
   wrapping mark is the single quote, except that a value containing a
   single quote but no double quote wraps in double quotes instead (so no
   inner escaping of the quote is needed in that case). (Faithful across
   the whole ASCII plane, the modeled domain of the name and route strings;
   mapping.md §2.) -/
def quoted (s : String) : String :=
  let delim : Char := if s.contains '\'' && !(s.contains '"') then '"' else '\''
  String.singleton delim
    ++ String.join (s.toList.map (escChar delim))
    ++ String.singleton delim

/- The textual form of an optional string field: an absent value renders as the
   literal `None`; a present value renders quoted. -/
def quotedOpt (o : Option String) : String :=
  match o with
  | none   => "None"
  | some s => quoted s

/- An optional string drawn from the ASCII plane — the modeled domain of the
   symbolic name and route pattern (the graded inputs are ASCII; outside it
   the printability classification of the underlying text rendering is
   standard-library specific and is not claimed; mapping.md §2). -/
def asciiOpt : Option String → Prop
  | none   => True
  | some s => ∀ c ∈ s.toList, c.toNat < 128

/- The full text line a resolved-URL match renders to. The callable component
   is the partial-application callable's full textual form when the callable is
   one, otherwise its dotted import path. The optional symbolic name and route
   render quoted (an absent one as `None`); the positional/keyword/list
   components are inserted by their already-rendered text. -/
def matchRepr (m : MatchView) : String :=
  let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
  "ResolverMatch(func=" ++ funcStr ++
  ", args=" ++ m.argsText ++
  ", kwargs=" ++ m.kwargsText ++
  ", url_name=" ++ quotedOpt m.urlName ++
  ", app_names=" ++ m.appNamesText ++
  ", namespaces=" ++ m.namespacesText ++
  ", route=" ++ quotedOpt m.route ++ ")"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a resolved-URL match as its text line: a partial-application callable
   shown by its full textual form (exposing the underlying callable and its
   bound arguments), an ordinary callable by its dotted path, and the symbolic
   name and route shown quoted. The name and route range over the ASCII plane
   (the modeled domain; mapping.md §2). -/
method resolverMatchRepr (m : MatchView) return (out : String)
  require asciiOpt m.urlName
  require asciiOpt m.route
  ensures out = matchRepr m
  do
    -- impl-start
    let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
    return "ResolverMatch(func=" ++ funcStr ++
      ", args=" ++ m.argsText ++
      ", kwargs=" ++ m.kwargsText ++
      ", url_name=" ++ quotedOpt m.urlName ++
      ", app_names=" ++ m.appNamesText ++
      ", namespaces=" ++ m.namespacesText ++
      ", route=" ++ quotedOpt m.route ++ ")"
    -- impl-end

prove_correct resolverMatchRepr by
  loom_solve <;> simp_all [matchRepr]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: `method resolverMatchRepr (m : MatchView) ... ensures out = matchRepr m` with require asciiOpt m.urlName / asciiOpt m.route. NO axioms (meta.axioms=[], deep_model_references=[], G-AX skip; grep confirms no `axiom`/`:|` token in Solution.lean). The postcondition FULLY PINS the output to the concrete pure function `matchRepr` on the ASCII precondition domain — so verify ⟺ (∀ inputs, out = matchRepr m). Any verifying impl is therefore pointwise-equal to matchRepr and refines to the identical gold behaviour; there is no under-specified slack for a verify-but-wrong impl to hide in.

A-leg audit (refinement.md §A/§B/§C): the A1–A6 rows are section-numbered R / R+I legs, NOT axiom legs — every leg is R (type refinement, e.g. ResolverMatch↔MatchView, %r↔quoted, %-format↔++, Option str↔None/some) or I (identical concrete op). §B/§C correctly claim zero A-consumed / zero A-reference and zero kind-3 steps; confirmed against meta.json (empty axioms & deep_model_references). The two genuinely-changed ops (partial-branch callable selection; %s→%r quoting of the two string fields url_name/route) are modeled DIRECTLY and CONCRETELY (if isPartialFunc / quoted / quotedOpt), not hidden behind an axiom. Model↔patch correspondence holds; the only trust point is refinement fidelity, discharged by this concrete pinning + G-CONF.

pos_control (correct impl): EXIT 0 VERIFIES ✓ (positive control good).
- atk_1 PREPATCH BUG 1 (callable ALWAYS funcPath, drops partial branch): EXIT 1, rejected. Reproduces prepatch defect / F2P test_repr_functools_partial.
- atk_2 PREPATCH BUG 2 (url_name/route rendered UNQUOTED, %s form): EXIT 1, rejected. Reproduces prepatch defect / F2P test_repr quoting.
- atk_3 BOUNDARY (swap url_name↔route components): EXIT 1, rejected.
- atk_4 CONTROL-FLOW-EFFECT (route none→"" instead of "None"): EXIT 1, rejected.
- atk_5 UNGROUNDED-ORACLE ECHO (return matchRepr m verbatim): EXIT 0 VERIFIES. Its faithful refined patch (= gold patch.diff verbatim, since matchRepr refines exactly to the patched __repr__) was MATERIALIZED and RUN through the official harness: run_resolve('django__django-14155', patch, timeout=1800) => RESOLVED=True COMPLETED=True FLAKY=False NOTE='resolved'. This verifying impl RESOLVES => does NOT break the spec.
- atk_6 PARTIAL-DOMAIN (correct only under ascii guard else GARBAGE): EXIT 1, unsolved goals — does NOT verify (loom_solve could not discharge), so no resolve needed.
- atk_7 CONTROL-FLOW rebuild (identical string via let-chain): EXIT 1, unsolved goals — does NOT verify.
- atk_8 UNGROUNDED quoting drift (none→quoted "None" instead of literal None): EXIT 1, rejected.

Commands used: `bash scripts/lean_verify.sh <f>.lean`; same_spec via swebench_unified.markers.same_spec + get_backend('velvet'); resolve via swebench_unified.harness.run_resolve. Note project root; env python python.

Result: 8 distinct wrong impls encoded & verified (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bugs, quoting drift), ≥5 satisfied. Exactly ONE verifies (the gold-equivalent echo), and its materialized faithful patch RESOLVES under the official harness. No verifying wrong impl produces a non-resolving faithful patch. verify⇒correct holds for this bundle. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
/- No consumed axioms. This operation renders a resolved-URL match object as a
   single human-readable text line. Every component the line is built from is
   already in hand as a value on the match record (the callable's identity and
   its two textual forms, the already-rendered argument/keyword/name-list
   components, and the optional name and route strings); there is no unchanged
   callee whose contract the proof consumes, hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable slice of a resolved-URL match that the text rendering reads:

     * `isPartialFunc`  — whether the matched callable is a partial-application
                          callable (one carrying pre-bound arguments). Such a
                          callable is shown by its full textual form so the
                          underlying callable and its bound arguments are
                          visible; an ordinary callable is shown by its
                          dotted-path form instead;
     * `funcPartialText` — the full textual form of a partial-application
                          callable (used only when `isPartialFunc`);
     * `funcPath`       — the dotted import path of an ordinary callable;
     * `argsText`       — the already-rendered positional-argument tuple;
     * `kwargsText`     — the already-rendered keyword-argument mapping;
     * `urlName`        — the optional symbolic name of the match;
     * `appNamesText`   — the already-rendered application-namespace list;
     * `namespacesText` — the already-rendered instance-namespace list;
     * `route`          — the optional route pattern string of the match.

   The two textual `func` forms and the three already-rendered list/mapping
   components are carried verbatim (mapping.md §2): they are produced by
   rendering operations this line does not itself vary. The optional name and
   route are carried as their underlying strings so the quoted form below is
   computed here. -/
structure MatchView where
  isPartialFunc : Bool
  funcPartialText : String
  funcPath : String
  argsText : String
  kwargsText : String
  urlName : Option String
  appNamesText : String
  namespacesText : String
  route : Option String
deriving DecidableEq

/- A hexadecimal digit character for a value below sixteen: `0`-`9` then
   `a`-`f` (lowercase). -/
def hexDigit (n : Nat) : Char :=
  if n < 10 then Char.ofNat (48 + n) else Char.ofNat (87 + n)

/- One character of a quoted textual form: the escape character and the
   wrapping quote mark render escaped (preceded by the escape character);
   the tab, line-feed and carriage-return controls render as their
   two-letter escape codes; any other control character, and the delete
   character, renders as a two-hex-digit escape; every other character
   renders as itself. -/
def escChar (delim : Char) (c : Char) : String :=
  if c = '\\' then "\\\\"
  else if c = delim then "\\" ++ String.singleton delim
  else if c = '\t' then "\\t"
  else if c = '\n' then "\\n"
  else if c = '\r' then "\\r"
  else if c.toNat < 32 ∨ c.toNat = 127 then
    "\\x" ++ String.singleton (hexDigit (c.toNat / 16))
          ++ String.singleton (hexDigit (c.toNat % 16))
  else String.singleton c

/- The quoted textual form of a string value: the value wrapped in quote
   marks, each inner occurrence of the wrapping mark or the escape character
   escaped, and each control character rendered by its escape code. The
   wrapping mark is the single quote, except that a value containing a
   single quote but no double quote wraps in double quotes instead (so no
   inner escaping of the quote is needed in that case). (Faithful across
   the whole ASCII plane, the modeled domain of the name and route strings;
   mapping.md §2.) -/
def quoted (s : String) : String :=
  let delim : Char := if s.contains '\'' && !(s.contains '"') then '"' else '\''
  String.singleton delim
    ++ String.join (s.toList.map (escChar delim))
    ++ String.singleton delim

/- The textual form of an optional string field: an absent value renders as the
   literal `None`; a present value renders quoted. -/
def quotedOpt (o : Option String) : String :=
  match o with
  | none   => "None"
  | some s => quoted s

/- An optional string drawn from the ASCII plane — the modeled domain of the
   symbolic name and route pattern (the graded inputs are ASCII; outside it
   the printability classification of the underlying text rendering is
   standard-library specific and is not claimed; mapping.md §2). -/
def asciiOpt : Option String → Prop
  | none   => True
  | some s => ∀ c ∈ s.toList, c.toNat < 128

/- The full text line a resolved-URL match renders to. The callable component
   is the partial-application callable's full textual form when the callable is
   one, otherwise its dotted import path. The optional symbolic name and route
   render quoted (an absent one as `None`); the positional/keyword/list
   components are inserted by their already-rendered text. -/
def matchRepr (m : MatchView) : String :=
  let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
  "ResolverMatch(func=" ++ funcStr ++
  ", args=" ++ m.argsText ++
  ", kwargs=" ++ m.kwargsText ++
  ", url_name=" ++ quotedOpt m.urlName ++
  ", app_names=" ++ m.appNamesText ++
  ", namespaces=" ++ m.namespacesText ++
  ", route=" ++ quotedOpt m.route ++ ")"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a resolved-URL match as its text line: a partial-application callable
   shown by its full textual form (exposing the underlying callable and its
   bound arguments), an ordinary callable by its dotted path, and the symbolic
   name and route shown quoted. The name and route range over the ASCII plane
   (the modeled domain; mapping.md §2). -/
method resolverMatchRepr (m : MatchView) return (out : String)
  require asciiOpt m.urlName
  require asciiOpt m.route
  ensures out = matchRepr m
  do
    -- impl-start
    let funcStr := if m.isPartialFunc then m.funcPartialText else m.funcPath
    return "ResolverMatch(func=" ++ funcStr ++
      ", args=" ++ m.argsText ++
      ", kwargs=" ++ m.kwargsText ++
      ", url_name=" ++ quotedOpt m.urlName ++
      ", app_names=" ++ m.appNamesText ++
      ", namespaces=" ++ m.namespacesText ++
      ", route=" ++ quotedOpt m.route ++ ")"
    -- impl-end

prove_correct resolverMatchRepr by
  loom_solve <;> simp_all [matchRepr]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec shape: `method resolverMatchRepr (m : MatchView) ... ensures out = matchRepr m` with require asciiOpt m.urlName / asciiOpt m.route. NO axioms (meta.axioms=[], deep_model_references=[], G-AX skip; grep confirms no `axiom`/`:|` token in Solution.lean). The postcondition FULLY PINS the output to the concrete pure function `matchRepr` on the ASCII precondition domain — so verify ⟺ (∀ inputs, out = matchRepr m). Any verifying impl is therefore pointwise-equal to matchRepr and refines to the identical gold behaviour; there is no under-specified slack for a verify-but-wrong impl to hide in.

A-leg audit (refinement.md §A/§B/§C): the A1–A6 rows are section-numbered R / R+I legs, NOT axiom legs — every leg is R (type refinement, e.g. ResolverMatch↔MatchView, %r↔quoted, %-format↔++, Option str↔None/some) or I (identical concrete op). §B/§C correctly claim zero A-consumed / zero A-reference and zero kind-3 steps; confirmed against meta.json (empty axioms & deep_model_references). The two genuinely-changed ops (partial-branch callable selection; %s→%r quoting of the two string fields url_name/route) are modeled DIRECTLY and CONCRETELY (if isPartialFunc / quoted / quotedOpt), not hidden behind an axiom. Model↔patch correspondence holds; the only trust point is refinement fidelity, discharged by this concrete pinning + G-CONF.

pos_control (correct impl): EXIT 0 VERIFIES ✓ (positive control good).
- atk_1 PREPATCH BUG 1 (callable ALWAYS funcPath, drops partial branch): EXIT 1, rejected. Reproduces prepatch defect / F2P test_repr_functools_partial.
- atk_2 PREPATCH BUG 2 (url_name/route rendered UNQUOTED, %s form): EXIT 1, rejected. Reproduces prepatch defect / F2P test_repr quoting.
- atk_3 BOUNDARY (swap url_name↔route components): EXIT 1, rejected.
- atk_4 CONTROL-FLOW-EFFECT (route none→"" instead of "None"): EXIT 1, rejected.
- atk_5 UNGROUNDED-ORACLE ECHO (return matchRepr m verbatim): EXIT 0 VERIFIES. Its faithful refined patch (= gold patch.diff verbatim, since matchRepr refines exactly to the patched __repr__) was MATERIALIZED and RUN through the official harness: run_resolve('django__django-14155', patch, timeout=1800) => RESOLVED=True COMPLETED=True FLAKY=False NOTE='resolved'. This verifying impl RESOLVES => does NOT break the spec.
- atk_6 PARTIAL-DOMAIN (correct only under ascii guard else GARBAGE): EXIT 1, unsolved goals — does NOT verify (loom_solve could not discharge), so no resolve needed.
- atk_7 CONTROL-FLOW rebuild (identical string via let-chain): EXIT 1, unsolved goals — does NOT verify.
- atk_8 UNGROUNDED quoting drift (none→quoted "None" instead of literal None): EXIT 1, rejected.

Commands used: `bash scripts/lean_verify.sh <f>.lean`; same_spec via swebench_unified.markers.same_spec + get_backend('velvet'); resolve via swebench_unified.harness.run_resolve. Note project root; env python python.

Result: 8 distinct wrong impls encoded & verified (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bugs, quoting drift), ≥5 satisfied. Exactly ONE verifies (the gold-equivalent echo), and its materialized faithful patch RESOLVES under the official harness. No verifying wrong impl produces a non-resolving faithful patch. verify⇒correct holds for this bundle. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attempted a faithfulness break on the model of ResolverMatch.__repr__ (django/urls/resolvers.py). No divergence found on the modeled domain. Evidence: (1) same_spec(Solution, Solution_prepatch_1)=True and same_spec(Solution, Solution_prepatch_2)=True under velvet LanguageTables — spec region byte-identical, not weakened. (2) Independent re-transliteration of quoted/escChar/hexDigit checked vs real Python repr(str): exhaustive over all 128 1-char strings and all 16384 2-char ASCII strings, plus 500k random ASCII strings (len 0-8) — 0 mismatches; delimiter-choice (double-quote wrap iff value has ' and no "), backslash doubling, \t/\n/\r codes, and \xNN control/DEL escapes all match CPython exactly on ASCII. (3) End-to-end: applied the ACTUAL gold patch to a fresh copy of the base_commit worktree and ran the bundle's conformance_check.py shadow (matchRepr/resolverMatchRepr) against the LIVE patched ResolverMatch.__repr__ — 100031 inputs across partial/non-partial/CBV callables, present/absent name+route, empty/non-empty containers, and tricky quote/backslash/control-char strings — 0 disagreements. (4) Precondition scope: the two `require asciiOpt` guards restrict claims to the ASCII plane; this is a legitimate domain restriction (repr printability off-ASCII is Unicode-table-driven) and every F2P input (no-kwargs, ^no_kwargs/([0-9]+)/$, partial reprs) is ASCII, so nothing the real callee is exercised on escapes the modeled domain. The %s->%r change being observationally inert on containers (str==repr for tuple/dict/list) is confirmed in the differential. (5) Solution.lean proof verifies (only a cosmetic <;> linter warning). The spec neither over-constrains nor drifts from the real callee on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Properly-dispositioned relaxed-leakage bundle (meta relaxed_leakage=true, G-LEAK status=relaxed, RELAXED_LEAKAGE.md present). Independently re-verified, not rubber-stamped. (1) Spec region byte-identical: same_spec(Solution,prepatch_1)=True and same_spec(Solution,prepatch_2)=True. (2) Gold makes two changes: (a) functools.partial handling — FULLY PUBLIC in problem_statement (names functools.partial, 'the func argument', 'accessible in __repr__'); the isPartialFunc?funcPartialText:funcPath choice leaks nothing beyond the issue. (b) %s->%r quoting flip, observable only on url_name/route — token scan of problem_statement = 0 hits for quote/%r/%s/single/url_name/route (its 3 'repr' tokens all name the __repr__ method); hints_text empty. The spec's quoted/escChar/quotedOpt clauses disclose facet (b), derivable only from gold/hidden test_patch. (3) Unavoidability re-derived: Solution_prepatch_2.lean is exactly the PS-only solver's impl (partial fixed, url_name/route unquoted); it fails prove_correct on the quoting clause and the hidden F2P test_repr assertion (url_name='no-kwargs', route='^no_kwargs/...$'). A spec weak enough to hide (b) would admit a non-resolving impl, so faithful+non-leaking is provably impossible — the defining relaxed-leakage shape. (4) Core soundness intact: G-VERIFY pass, both prepatch skeletons fail on exactly one distinct discriminator each (G-DIFF), G-CONF pass over 1e5 seed-14155 fuzz, patch.diff byte-verbatim match against frozen dataset gold (G-RESOLVE), G-AX skip (genuinely axiom-free). (5) No NEW leak beyond dispositioned facet (b): spec view names no patched file/symbol (resolvers.py, _func_path, functools.partial all absent — only abstract 'partial-application callable'), no diff line, no mechanism; no problem_statement-only derivation of the single-quoting exists. Per _audit.py convention, honest recording is NO-LEAKAGE (=pass): dispositioned quoting facet re-confirmed, no leak beyond it found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.
