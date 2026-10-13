# P2 adversarial audit — astropy__astropy-13033

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,16 +115,11 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
-    let found := present.take required.length
-    let expectedStr := renderColumnList required
-    let foundStr := renderColumnList found
+    let expectedFirst := required.headD []
+    let foundFirst := present.headD []
     let plural : List Char := if required.length > 1 then ['s'] else []
-    let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
-      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
+    let msg := className ++ " object is invalid - expected ".toList ++ quoted expectedFirst
+      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ quoted foundFirst
     return msg
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,13 +115,9 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
     let found := present.take required.length
-    let expectedStr := renderColumnList required
-    let foundStr := renderColumnList found
+    let expectedStr := bracketList required
+    let foundStr := bracketList found
     let plural : List Char := if required.length > 1 then ['s'] else []
     let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
       ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,14 +115,10 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
     let found := present.take required.length
     let expectedStr := renderColumnList required
     let foundStr := renderColumnList found
-    let plural : List Char := if required.length > 1 then ['s'] else []
+    let plural : List Char := []
     let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
       ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
     return msg
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,11 +115,7 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
-    let found := present.take required.length
+    let found := present
     let expectedStr := renderColumnList required
     let foundStr := renderColumnList found
     let plural : List Char := if required.length > 1 then ['s'] else []
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,13 +115,9 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
     let found := present.take required.length
-    let expectedStr := renderColumnList required
-    let foundStr := renderColumnList found
+    let expectedStr := renderColumnList found
+    let foundStr := renderColumnList required
     let plural : List Char := if required.length > 1 then ['s'] else []
     let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
       ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,16 +115,11 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
     let found := present.take required.length
-    let expectedStr := renderColumnList required
-    let foundStr := renderColumnList found
     let plural : List Char := if required.length > 1 then ['s'] else []
-    let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
-      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
+    let msg := if required.isEmpty then ([] : List Char) else
+      className ++ " object is invalid - expected ".toList ++ renderColumnList required
+        ++ " as the first column".toList ++ plural ++ " but found ".toList ++ renderColumnList found
     return msg
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,17 +115,7 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
-    let found := present.take required.length
-    let expectedStr := renderColumnList required
-    let foundStr := renderColumnList found
-    let plural : List Char := if required.length > 1 then ['s'] else []
-    let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
-      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
-    return msg
+    return errorMessage className required present
     -- impl-end
 
 prove_correct requiredColumnsError by
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
 -- (One building block is left abstract; no `axiom` is consumed. The message
@@ -115,14 +115,10 @@
   ensures out = errorMessage className required present
   do
     -- impl-start
-    -- Compare against the leading prefix of the present names, as many as were
-    -- required; render both the required and the present-prefix collections for
-    -- display (single name → quoted scalar, otherwise → bracketed list);
-    -- pluralize the noun when more than one column was required; assemble.
     let found := present.take required.length
     let expectedStr := renderColumnList required
     let foundStr := renderColumnList found
-    let plural : List Char := if required.length > 1 then ['s'] else []
+    let plural : List Char := if required.length > 0 then ['s'] else []
     let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
       ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
     return msg
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (One building block is left abstract; no `axiom` is consumed. The message
--  construction is modeled DEEPLY in the `pure` region below from concrete
--  string operations over the inputs. The single abstract leaf is the
--  platform's canonical rendering of one text value as it appears INSIDE a
--  rendered sequence: quote-delimited with the platform's own escaping rules
--  (the delimiter can switch, and escape/control characters are escaped, when
--  the value embeds such characters). That rendering is an UNCHANGED builtin
--  of the surrounding platform — the behaviour modeled here decides WHICH
--  collections are rendered and WHEN the single-name form vs the
--  whole-sequence form is used, while the per-character escaping rules belong
--  to the platform. Committing to a concrete approximation of those rules
--  here would diverge from the real behaviour on names containing
--  quote/escape/control characters, so the element rendering is `opaque`; its
--  binding to the real builtin is validated executably by G-AX
--  (axiom_check.py fuzzes the real builtin over adversarial names). The proof
--  never inspects its behaviour. The decision of WHICH branch of the
--  surrounding check fires, and the relaxation bookkeeping, are unchanged
--  control flow reached identically and are not modeled here — only the
--  message construction is. See refinement.md §B and mapping.md §3.)

/- The platform's canonical rendering of one text value as it appears inside a
   rendered sequence of values: quote-delimited with the platform's escaping
   rules. Left abstract (`opaque`); bound to the real builtin by G-AX. -/
opaque renderedName : List Char → List Char
-- axioms-end

-- pure-start
/- A column name is a sequence of characters; a collection of column names is a
   sequence of those. The message renders names for the reader. -/

/- One column name, rendered the way a SINGLE value is shown on its own: the
   name verbatim surrounded by apostrophes — plain interpolation, no escaping
   (e.g. the name `time` renders as `'time'`). -/
def quoted (s : List Char) : List Char := ['\''] ++ s ++ ['\'']

/- A comma-and-space separated run of names as they appear inside a rendered
   sequence — each name rendered by the platform's canonical `renderedName` —
   with no surrounding brackets. Front-recursive (one unfold available per
   leading element):
     []            ↦ (nothing)
     [x]           ↦ renderedName x
     x :: y :: ys  ↦ renderedName x, <rest>
   The two-element-or-more arm keeps the recursion structural. -/
def joinRendered : List (List Char) → List Char
  | []             => []
  | [x]            => renderedName x
  | x :: (y :: ys) => renderedName x ++ ", ".toList ++ joinRendered (y :: ys)

/- A whole collection of names rendered as a bracketed list, the way a sequence
   of names is displayed: `[` then the comma-separated canonically-rendered
   names then `]` (e.g. names `time`, `a` render as `['time', 'a']`; the empty
   collection renders as `[]`). -/
def bracketList (xs : List (List Char)) : List Char := ['['] ++ joinRendered xs ++ [']']

/- Render a collection of column names for display. A collection holding exactly
   one name is shown as that single quoted name — plain interpolation, no
   escaping (e.g. `'time'`); a collection of any other size (none, or two or
   more) is shown as the bracketed list, each element in its canonical rendered
   form (e.g. `['time', 'a']` or `[]`). This single/many distinction is the
   whole point of the rendering: a one-name collection reads as a scalar, a
   many-name collection reads as the explicit list it is. -/
def renderColumnList : List (List Char) → List Char
  | [x] => quoted x
  | xs  => bracketList xs

/- The full invalidity message for the required-columns check, given the table's
   class name, the names that were required as the leading columns, and the names
   actually present. The names actually compared against are the leading prefix
   of the present names, as many as were required. The message names the expected
   leading columns and the present leading columns using the display rendering
   above, and uses a plural noun exactly when more than one column was required:

     <Class> object is invalid - expected <expected> as the first column<s?> but found <found>

   where <expected> renders the required names and <found> renders the present
   leading names. Grounded in the three input sequences plus the platform's
   canonical per-element rendering (the one abstract leaf; directive 8). -/
def errorMessage (className : List Char) (required present : List (List Char)) : List Char :=
  let found := present.take required.length
  className ++ " object is invalid - expected ".toList ++ renderColumnList required
    ++ " as the first column".toList ++ (if required.length > 1 then ['s'] else [])
    ++ " but found ".toList ++ renderColumnList found
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the message reported when a table's leading columns do not match the
   columns it requires. `className` is the table's class name; `required` is the
   sequence of names required as the leading columns; `present` is the sequence
   of names actually present. All three are read-only (not `mut`): the message is
   computed and nothing is mutated (directive 5).

   Desired behaviour: the message must name the expected leading columns and the
   present leading columns using the display rendering — a single required (resp.
   present) name shown as a quoted scalar, several shown as the bracketed list —
   so that when more than one column is required the message reports the actual
   collections rather than only their first element, and pluralizes accordingly.
   The present names compared are the leading prefix of those present, as many as
   were required. -/
method requiredColumnsError (className : List Char) (required : List (List Char))
    (present : List (List Char)) return (out : List Char)
  ensures out = errorMessage className required present
  do
    -- impl-start
    -- Compare against the leading prefix of the present names, as many as were
    -- required; render both the required and the present-prefix collections for
    -- display (single name → quoted scalar, otherwise → bracketed list);
    -- pluralize the noun when more than one column was required; assemble.
    let found := present.take required.length
    let expectedStr := renderColumnList required
    let foundStr := renderColumnList found
    let plural : List Char := if required.length > 1 then ['s'] else []
    let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
    return msg
    -- impl-end

prove_correct requiredColumnsError by
  loom_solve
  simp_all [errorMessage]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit of astropy__astropy-13033 (velvet). Spec is EXACT functional equality: `ensures out = errorMessage className required present`, where errorMessage is a fully deterministic pure function (deep model quoted/joinRendered/bracketList/renderColumnList) over the three inputs, with a single opaque A-reference `renderedName` (bound to Python `repr`). Because the postcondition pins total extensional equality to that fixed function, ANY verifying impl is behaviourally identical to errorMessage on every input — leaving no room for a verifying-but-wrong impl. errorMessage itself is validated against the REAL patched _check_required_columns by G-CONF (100012 inputs, seed 13033, adversarial names, 0 disagreements) and the renderedName<->repr binding by G-AX (50104 cases, 0 disagreements), so verify => output-equals-gold-message => resolves.

### ATTACKS (all same_spec=True vs frozen Solution.lean; axioms/pure/pre/post byte-identical, only impl region edited):
- atk_1.lean (prepatch bug reproduced): message names only required.headD/present.headD each `quoted`, ignoring multi-column collections. VERIFY = exit 1 (FAIL). Residual goal is the head-vs-renderColumnList discrepancy. Matches Solution_prepatch.lean / G-DIFF.
- atk_2.lean (always bracketList, never scalar): renders a 1-element collection as ['x'] instead of 'x'. VERIFY = exit 1 (FAIL).
- atk_3.lean (control-flow-effect: drop pluralization, plural always []): VERIFY = exit 1 (FAIL).
- atk_4.lean (drop the take prefix, found := present): wrong when present longer than required. VERIFY = exit 1 (FAIL).
- atk_5.lean (swap required/found rendering): VERIFY = exit 1 (FAIL). Residual goal shows expected/found fields swapped.
- atk_6.lean (partial-domain: returns [] when required empty, else correct): VERIFY = exit 1 (FAIL). Residual goal `¬required = []` — spec equality is total, cannot dodge the empty-required point.
- atk_7.lean (ungrounded-oracle echo: `return errorMessage className required present`): behaviourally CORRECT (gold-equivalent); VERIFY = exit 1 due only to a benign proof-script artifact ('No goals to be solved' — loom_solve already closes the goal so the trailing simp_all errors). Not a wrong impl and not a soundness hole; its faithful patch would be the gold and would resolve, so it does not falsify.
- atk_8.lean (boundary: pluralize on length>0 instead of >1): wrong for single-required (adds spurious 's'). VERIFY = exit 1 (FAIL). Residual goal is exactly `(if 0<len then s else) = (if 1<len then s else)`.

Exact verify commands: `bash scripts/lean_verify.sh <file>`, scheduled concurrently in two ≤4 batches. Results: pos_control.lean exit 0 (verifies); atk_1..atk_6, atk_8 exit 1 (fail); atk_7 exit 1 (fail, benign proof artifact, behaviourally correct).

RESOLVE: patches map is EMPTY because NO wrong impl verified — there is no verifying-but-wrong candidate whose faithful patch could be materialized and run through run_resolve. The only verifying candidates are the gold-faithful Solution.lean and its errorMessage-echo (both behaviourally the gold, and G-RESOLVE already records the gold patch as 'resolved'). verify⇏correct could not be demonstrated.

REFINEMENT.MD AUDIT: legs A1–A8 are all R (type refinement str<->List Char, list[str]<->List (List Char)) or I (identical concrete op); the sole A-reference leaf (renderedName<->repr, §B, appearing in A5/A6) corresponds to the real unchanged per-element `str(list)` rendering and is validated byte-for-byte by G-AX (pass). §C explicitly asserts no kind-3 (inexpressible-changed-op) steps, and the changed operation (scalar-vs-list rendering) is modeled deeply in the pure region, NOT axiomatized — consistent with directive 7. mapping.md §1–4 binds every symbol to core.py:55 (_check_required_columns) at base_commit and the correspondence holds. No consumed axiom. All A-legs and the model↔patch correspondence check out.

VERDICT: SOUND — 8 same-spec attacks run and verified, the gold-faithful positive control verifies, every genuinely-wrong impl fails verification, and the tight functional-equality postcondition (backed by G-CONF/G-AX against the real patched method) leaves no verifying-but-wrong impl to break the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
-- (One building block is left abstract; no `axiom` is consumed. The message
--  construction is modeled DEEPLY in the `pure` region below from concrete
--  string operations over the inputs. The single abstract leaf is the
--  platform's canonical rendering of one text value as it appears INSIDE a
--  rendered sequence: quote-delimited with the platform's own escaping rules
--  (the delimiter can switch, and escape/control characters are escaped, when
--  the value embeds such characters). That rendering is an UNCHANGED builtin
--  of the surrounding platform — the behaviour modeled here decides WHICH
--  collections are rendered and WHEN the single-name form vs the
--  whole-sequence form is used, while the per-character escaping rules belong
--  to the platform. Committing to a concrete approximation of those rules
--  here would diverge from the real behaviour on names containing
--  quote/escape/control characters, so the element rendering is `opaque`; its
--  binding to the real builtin is validated executably by G-AX
--  (axiom_check.py fuzzes the real builtin over adversarial names). The proof
--  never inspects its behaviour. The decision of WHICH branch of the
--  surrounding check fires, and the relaxation bookkeeping, are unchanged
--  control flow reached identically and are not modeled here — only the
--  message construction is. See refinement.md §B and mapping.md §3.)

/- The platform's canonical rendering of one text value as it appears inside a
   rendered sequence of values: quote-delimited with the platform's escaping
   rules. Left abstract (`opaque`); bound to the real builtin by G-AX. -/
opaque renderedName : List Char → List Char
-- axioms-end

-- pure-start
/- A column name is a sequence of characters; a collection of column names is a
   sequence of those. The message renders names for the reader. -/

/- One column name, rendered the way a SINGLE value is shown on its own: the
   name verbatim surrounded by apostrophes — plain interpolation, no escaping
   (e.g. the name `time` renders as `'time'`). -/
def quoted (s : List Char) : List Char := ['\''] ++ s ++ ['\'']

/- A comma-and-space separated run of names as they appear inside a rendered
   sequence — each name rendered by the platform's canonical `renderedName` —
   with no surrounding brackets. Front-recursive (one unfold available per
   leading element):
     []            ↦ (nothing)
     [x]           ↦ renderedName x
     x :: y :: ys  ↦ renderedName x, <rest>
   The two-element-or-more arm keeps the recursion structural. -/
def joinRendered : List (List Char) → List Char
  | []             => []
  | [x]            => renderedName x
  | x :: (y :: ys) => renderedName x ++ ", ".toList ++ joinRendered (y :: ys)

/- A whole collection of names rendered as a bracketed list, the way a sequence
   of names is displayed: `[` then the comma-separated canonically-rendered
   names then `]` (e.g. names `time`, `a` render as `['time', 'a']`; the empty
   collection renders as `[]`). -/
def bracketList (xs : List (List Char)) : List Char := ['['] ++ joinRendered xs ++ [']']

/- Render a collection of column names for display. A collection holding exactly
   one name is shown as that single quoted name — plain interpolation, no
   escaping (e.g. `'time'`); a collection of any other size (none, or two or
   more) is shown as the bracketed list, each element in its canonical rendered
   form (e.g. `['time', 'a']` or `[]`). This single/many distinction is the
   whole point of the rendering: a one-name collection reads as a scalar, a
   many-name collection reads as the explicit list it is. -/
def renderColumnList : List (List Char) → List Char
  | [x] => quoted x
  | xs  => bracketList xs

/- The full invalidity message for the required-columns check, given the table's
   class name, the names that were required as the leading columns, and the names
   actually present. The names actually compared against are the leading prefix
   of the present names, as many as were required. The message names the expected
   leading columns and the present leading columns using the display rendering
   above, and uses a plural noun exactly when more than one column was required:

     <Class> object is invalid - expected <expected> as the first column<s?> but found <found>

   where <expected> renders the required names and <found> renders the present
   leading names. Grounded in the three input sequences plus the platform's
   canonical per-element rendering (the one abstract leaf; directive 8). -/
def errorMessage (className : List Char) (required present : List (List Char)) : List Char :=
  let found := present.take required.length
  className ++ " object is invalid - expected ".toList ++ renderColumnList required
    ++ " as the first column".toList ++ (if required.length > 1 then ['s'] else [])
    ++ " but found ".toList ++ renderColumnList found
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the message reported when a table's leading columns do not match the
   columns it requires. `className` is the table's class name; `required` is the
   sequence of names required as the leading columns; `present` is the sequence
   of names actually present. All three are read-only (not `mut`): the message is
   computed and nothing is mutated (directive 5).

   Desired behaviour: the message must name the expected leading columns and the
   present leading columns using the display rendering — a single required (resp.
   present) name shown as a quoted scalar, several shown as the bracketed list —
   so that when more than one column is required the message reports the actual
   collections rather than only their first element, and pluralizes accordingly.
   The present names compared are the leading prefix of those present, as many as
   were required. -/
method requiredColumnsError (className : List Char) (required : List (List Char))
    (present : List (List Char)) return (out : List Char)
  ensures out = errorMessage className required present
  do
    -- impl-start
    -- Compare against the leading prefix of the present names, as many as were
    -- required; render both the required and the present-prefix collections for
    -- display (single name → quoted scalar, otherwise → bracketed list);
    -- pluralize the noun when more than one column was required; assemble.
    let found := present.take required.length
    let expectedStr := renderColumnList required
    let foundStr := renderColumnList found
    let plural : List Char := if required.length > 1 then ['s'] else []
    let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
    return msg
    -- impl-end

prove_correct requiredColumnsError by
  loom_solve
  simp_all [errorMessage]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit of astropy__astropy-13033 (velvet). Spec is EXACT functional equality: `ensures out = errorMessage className required present`, where errorMessage is a fully deterministic pure function (deep model quoted/joinRendered/bracketList/renderColumnList) over the three inputs, with a single opaque A-reference `renderedName` (bound to Python `repr`). Because the postcondition pins total extensional equality to that fixed function, ANY verifying impl is behaviourally identical to errorMessage on every input — leaving no room for a verifying-but-wrong impl. errorMessage itself is validated against the REAL patched _check_required_columns by G-CONF (100012 inputs, seed 13033, adversarial names, 0 disagreements) and the renderedName<->repr binding by G-AX (50104 cases, 0 disagreements), so verify => output-equals-gold-message => resolves.

### ATTACKS (all same_spec=True vs frozen Solution.lean; axioms/pure/pre/post byte-identical, only impl region edited):
- atk_1.lean (prepatch bug reproduced): message names only required.headD/present.headD each `quoted`, ignoring multi-column collections. VERIFY = exit 1 (FAIL). Residual goal is the head-vs-renderColumnList discrepancy. Matches Solution_prepatch.lean / G-DIFF.
- atk_2.lean (always bracketList, never scalar): renders a 1-element collection as ['x'] instead of 'x'. VERIFY = exit 1 (FAIL).
- atk_3.lean (control-flow-effect: drop pluralization, plural always []): VERIFY = exit 1 (FAIL).
- atk_4.lean (drop the take prefix, found := present): wrong when present longer than required. VERIFY = exit 1 (FAIL).
- atk_5.lean (swap required/found rendering): VERIFY = exit 1 (FAIL). Residual goal shows expected/found fields swapped.
- atk_6.lean (partial-domain: returns [] when required empty, else correct): VERIFY = exit 1 (FAIL). Residual goal `¬required = []` — spec equality is total, cannot dodge the empty-required point.
- atk_7.lean (ungrounded-oracle echo: `return errorMessage className required present`): behaviourally CORRECT (gold-equivalent); VERIFY = exit 1 due only to a benign proof-script artifact ('No goals to be solved' — loom_solve already closes the goal so the trailing simp_all errors). Not a wrong impl and not a soundness hole; its faithful patch would be the gold and would resolve, so it does not falsify.
- atk_8.lean (boundary: pluralize on length>0 instead of >1): wrong for single-required (adds spurious 's'). VERIFY = exit 1 (FAIL). Residual goal is exactly `(if 0<len then s else) = (if 1<len then s else)`.

Exact verify commands: `bash scripts/lean_verify.sh <file>`, scheduled concurrently in two ≤4 batches. Results: pos_control.lean exit 0 (verifies); atk_1..atk_6, atk_8 exit 1 (fail); atk_7 exit 1 (fail, benign proof artifact, behaviourally correct).

RESOLVE: patches map is EMPTY because NO wrong impl verified — there is no verifying-but-wrong candidate whose faithful patch could be materialized and run through run_resolve. The only verifying candidates are the gold-faithful Solution.lean and its errorMessage-echo (both behaviourally the gold, and G-RESOLVE already records the gold patch as 'resolved'). verify⇏correct could not be demonstrated.

REFINEMENT.MD AUDIT: legs A1–A8 are all R (type refinement str<->List Char, list[str]<->List (List Char)) or I (identical concrete op); the sole A-reference leaf (renderedName<->repr, §B, appearing in A5/A6) corresponds to the real unchanged per-element `str(list)` rendering and is validated byte-for-byte by G-AX (pass). §C explicitly asserts no kind-3 (inexpressible-changed-op) steps, and the changed operation (scalar-vs-list rendering) is modeled deeply in the pure region, NOT axiomatized — consistent with directive 7. mapping.md §1–4 binds every symbol to core.py:55 (_check_required_columns) at base_commit and the correspondence holds. No consumed axiom. All A-legs and the model↔patch correspondence check out.

VERDICT: SOUND — 8 same-spec attacks run and verified, the gold-faithful positive control verifies, every genuinely-wrong impl fails verification, and the tight functional-equality postcondition (backed by G-CONF/G-AX against the real patched method) leaves no verifying-but-wrong impl to break the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found; spec is not too strong. Checks performed: (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True — spec view (axioms opaque renderedName + pure region quoted/joinRendered/bracketList/renderColumnList/errorMessage + method contract `ensures out = errorMessage className required present`) is byte-identical between the two; only the elided impl region differs. Spec view is clean. Faithfulness fuzz: transcribed the REAL patched BaseTimeSeries._check_required_columns verbatim from core.py (couldn't import the source checkout — extensions unbuilt — so transcribed the exact body incl. as_scalar_or_list_str) and drove it against the shadow transliteration of errorMessage over ~300k random cases with relax=False, enabled=True. Alphabet mixed simple identifiers with adversarial names (a'b, a\"b, backslashes, \t \n \x00 \x1b \x7f \xa0, écolønne, 列名, empty string). Compared 298,652 mismatch-arm cases (required nonempty, present nonempty, prefix-mismatch) → 0 divergences. The renderedName↔repr opaque leaf composes exactly with CPython str(list); single-name f"'{x}'" plain-interp matches `quoted`. (3) Domain scoping is faithful: the modeled function covers ONLY the mismatch-arm message (the sole behavior the gold patch changes). Out-of-domain branches (empty-colnames 'no columns' message, prefix-match no-raise, relax bookkeeping) legitimately differ from the shadow but are byte-identical pre/post patch and reached identically — refinement.md §C scoping is correct, not an over-strong claim. The modeled function agrees with the real callee everywhere it claims to model. Spec is faithful; no over-tightening or drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, velvet flavor) PASSES with zero hard failures; same_spec(Solution, Solution_prepatch) is True and the spec region is byte-identical. Semantic review of the solver-visible spec view (projected Solution.lean): (1) No spec-view identifier embeds the patched repo symbol as_scalar_or_list_str or _check_required_columns — spec names are generic (renderColumnList, quoted, bracketList, joinRendered, errorMessage, requiredColumnsError, renderedName). (2) The patched file path astropy/timeseries/core.py and dotted module astropy.timeseries.core do NOT appear in the spec view (they live only in mapping.md/refinement.md, which are auditor docs, not the consumer spec view). (3) No diff markers, no reproduced gold-patch lines (>=8 chars), no narration terms (bug/fix/patch/pre-patch/previously/etc.). (4) The spec describes the desired OUTPUT contract — single name -> quoted scalar 'time', multiple names -> bracketed list ['time','a'], plural noun when >1 required. 'time' is already public in problem_statement (the misleading-message example). The scalar-vs-list distinction is the legitimate specification of correct behavior, not a localization of the gold edit; the gold mechanism (nested helper as_scalar_or_list_str, the .format template rewrite, file/line) is not exposed. Describing the target behavior a correct fix must produce is the spec's job and does not constitute leakage beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
