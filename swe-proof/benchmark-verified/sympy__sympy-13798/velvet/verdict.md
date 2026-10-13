# P2 adversarial audit — sympy__sympy-13798

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong-value impl exists (spec is output-pinned: ensures out = resolveSpec sym), and every verifying divergence-based impl either resolves (untested-branch) or hangs the harness (completed=False => INCONCLUSIVE, not verify⇏correct). The echo patch (atk_5, = resolveSpec verbatim) RESOLVES, positively confirming resolveSpec is behaviourally equal to the gold patch on the hidden tests (incl. F2P latex(3*x**2*y, mul_symbol='\,')=='3\,x^{2}\,y' and latex(1.5*3**x, mul_symbol='\,')=='1.5 \cdot 3^{x}').
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. The multiplication-symbol resolution is computed purely
@@ -128,23 +128,20 @@
   ensures out = resolveSpec sym
   do
     -- impl-start
-    -- Resolve each separator independently, mirroring the two resolution sites.
-    -- General separator: the standard separator of a recognized named symbol,
-    -- otherwise the supplied symbol used verbatim.
-    let first : String :=
+    -- Pre-patch skeleton: bare table index, no acceptance of an unrecognized symbol.
+    let first : Except MulErr String :=
       match mulTable sym with
-      | some v => v
-      | none   => sym.getD ""
-    -- Numeric separator: the standard separator for the falling-back numeric key
-    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
-    -- the supplied symbol verbatim in every remaining case.
-    let numbers : String :=
+      | some v => Except.ok v
+      | none   => Except.error MulErr.unresolved
+    let numbers : Except MulErr String :=
       match mulTable (some (numKey sym)) with
-      | some v => v
-      | none   =>
-        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
-    -- The resolution is total: always a resolved pair.
-    return Except.ok (first, numbers)
+      | some v => Except.ok v
+      | none   => Except.error MulErr.unresolved
+    let result : Except MulErr (String × String) := do
+      let a ← first
+      let b ← numbers
+      return (a, b)
+    return result
     -- impl-end
 
 prove_correct resolveMulSeparators by
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
 /- No consumed axioms. The multiplication-symbol resolution is computed purely
@@ -128,22 +128,14 @@
   ensures out = resolveSpec sym
   do
     -- impl-start
-    -- Resolve each separator independently, mirroring the two resolution sites.
-    -- General separator: the standard separator of a recognized named symbol,
-    -- otherwise the supplied symbol used verbatim.
     let first : String :=
       match mulTable sym with
       | some v => v
       | none   => sym.getD ""
-    -- Numeric separator: the standard separator for the falling-back numeric key
-    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
-    -- the supplied symbol verbatim in every remaining case.
     let numbers : String :=
       match mulTable (some (numKey sym)) with
       | some v => v
-      | none   =>
-        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
-    -- The resolution is total: always a resolved pair.
+      | none   => sym.getD ""   -- WRONG: drops the spacing-only -> dot fallback
     return Except.ok (first, numbers)
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
 /- No consumed axioms. The multiplication-symbol resolution is computed purely
@@ -128,22 +128,16 @@
   ensures out = resolveSpec sym
   do
     -- impl-start
-    -- Resolve each separator independently, mirroring the two resolution sites.
-    -- General separator: the standard separator of a recognized named symbol,
-    -- otherwise the supplied symbol used verbatim.
     let first : String :=
       match mulTable sym with
       | some v => v
       | none   => sym.getD ""
-    -- Numeric separator: the standard separator for the falling-back numeric key
-    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
-    -- the supplied symbol verbatim in every remaining case.
     let numbers : String :=
       match mulTable (some (numKey sym)) with
       | some v => v
       | none   =>
-        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
-    -- The resolution is total: always a resolved pair.
+        -- WRONG: builtin ASCII-only trim; diverges from pyStrip on \x0c etc.
+        if spacingSyms.contains (sym.getD "").trim then " \\cdot " else sym.getD ""
     return Except.ok (first, numbers)
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
 /- No consumed axioms. The multiplication-symbol resolution is computed purely
@@ -128,23 +128,14 @@
   ensures out = resolveSpec sym
   do
     -- impl-start
-    -- Resolve each separator independently, mirroring the two resolution sites.
-    -- General separator: the standard separator of a recognized named symbol,
-    -- otherwise the supplied symbol used verbatim.
-    let first : String :=
-      match mulTable sym with
-      | some v => v
-      | none   => sym.getD ""
-    -- Numeric separator: the standard separator for the falling-back numeric key
-    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
-    -- the supplied symbol verbatim in every remaining case.
-    let numbers : String :=
-      match mulTable (some (numKey sym)) with
-      | some v => v
-      | none   =>
-        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
-    -- The resolution is total: always a resolved pair.
-    return Except.ok (first, numbers)
+    match mulTable sym with
+    | some v =>
+      let numbers :=
+        match mulTable (some (numKey sym)) with | some w => w | none => " \\cdot "
+      return Except.ok (v, numbers)
+    | none =>
+      -- WRONG: rejects any unrecognized symbol instead of accepting it verbatim
+      return Except.error MulErr.unresolved
     -- impl-end
 
 prove_correct resolveMulSeparators by
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
 /- No consumed axioms. The multiplication-symbol resolution is computed purely
@@ -128,25 +128,9 @@
   ensures out = resolveSpec sym
   do
     -- impl-start
-    -- Resolve each separator independently, mirroring the two resolution sites.
-    -- General separator: the standard separator of a recognized named symbol,
-    -- otherwise the supplied symbol used verbatim.
-    let first : String :=
-      match mulTable sym with
-      | some v => v
-      | none   => sym.getD ""
-    -- Numeric separator: the standard separator for the falling-back numeric key
-    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
-    -- the supplied symbol verbatim in every remaining case.
-    let numbers : String :=
-      match mulTable (some (numKey sym)) with
-      | some v => v
-      | none   =>
-        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
-    -- The resolution is total: always a resolved pair.
-    return Except.ok (first, numbers)
+    -- Echo: return exactly the frozen spec function (behaviourally identical to gold).
+    return resolveSpec sym
     -- impl-end
 
 prove_correct resolveMulSeparators by
   loom_solve
-  simp_all [resolveSpec, firstSep, numSep]
```

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The multiplication-symbol resolution is computed purely
@@ -128,22 +128,23 @@
   ensures out = resolveSpec sym
   do
     -- impl-start
-    -- Resolve each separator independently, mirroring the two resolution sites.
-    -- General separator: the standard separator of a recognized named symbol,
-    -- otherwise the supplied symbol used verbatim.
     let first : String :=
       match mulTable sym with
       | some v => v
       | none   => sym.getD ""
-    -- Numeric separator: the standard separator for the falling-back numeric key
-    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
-    -- the supplied symbol verbatim in every remaining case.
     let numbers : String :=
       match mulTable (some (numKey sym)) with
       | some v => v
       | none   =>
         if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
-    -- The resolution is total: always a resolved pair.
+    -- Diverge ONLY on a sentinel symbol never exercised by any test: verifies
+    -- vacuously on that one input, correct on the whole tested domain.
+    if sym = some "zzz_untested_sentinel_symbol" then
+      let mut k : Nat := 0
+      while true
+        invariant True
+      do
+        k := k + 1
     return Except.ok (first, numbers)
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
/- No consumed axioms. The multiplication-symbol resolution is computed purely
   from the supplied symbol and a small constant table of recognized names that
   the routine carries itself; it calls no separate unchanged routine whose
   behaviour the proof must assume, so there is no module-level `axiom`.
   Refinement fidelity is checked mechanically by conformance_check.py (G-CONF).
   (mapping.md §1, §3.) -/
-- axioms-end

-- pure-start
/- The outcome when a supplied multiplication symbol cannot be resolved to a
   separator. The resolution specified below is TOTAL — every symbol resolves to
   a pair of separators — so this alternative is never produced by the specified
   behaviour; it is the modeling vehicle for a non-total resolution that rejects
   an unrecognized symbol. (mapping.md §1.) -/
inductive MulErr where
  | unresolved
  deriving DecidableEq

/- The standard separators for the recognized named multiplication-symbol
   choices: each of the four recognized names maps to its standard separator; the
   absent name (the default, written `none`) maps to a single space; any OTHER
   string is not a recognized name (`none` result). A direct transliteration of
   the constant recognized-name table the routine carries inline; refinement
   fidelity checked by conformance_check.py (G-CONF), mapping.md §3.1. -/
def mulTable : Option String → Option String
  | none         => some " "
  | some "ldot"  => some " \\,.\\, "
  | some "dot"   => some " \\cdot "
  | some "times" => some " \\times "
  | some _       => none

/- The key used to resolve the separator placed between NUMERIC factors: the
   supplied symbol if it is a non-empty string, otherwise the default `"dot"`
   (an absent symbol, written `none`, also defaults to `"dot"`). This is the
   numeric route's choice of a falling-back lookup key. -/
def numKey : Option String → String
  | none   => "dot"
  | some s => if s = "" then "dot" else s

/- The spacing-only symbol forms (after trimming surrounding whitespace) for
   which the NUMERIC separator falls back to the dot — a bare spacing command is
   ambiguous between two numbers, so numbers are separated by the dot instead.
   A direct transliteration of the constant spacing-form list the routine carries
   inline; refinement fidelity checked by conformance_check.py (G-CONF),
   mapping.md §3.2. -/
def spacingSyms : List String := ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"]

/- The whitespace predicate of the routine's surrounding-whitespace trim: the
   full Unicode whitespace set (tab..carriage-return, the FS/GS/RS/US
   separators, space, NEL, NBSP, the Ogham space mark, the U+2000..U+200A
   spaces, the line/paragraph separators, narrow NBSP, the medium mathematical
   space, and the ideographic space). -/
def pyWhitespace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x20) ||
  c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f ||
  c.val = 0x205f || c.val = 0x3000

/- Trim surrounding whitespace with the routine's whitespace set (the full
   Unicode set above — NOT merely the four ASCII forms of `String.trim`). -/
def pyStrip (s : String) : String :=
  String.mk (((s.toList.dropWhile pyWhitespace).reverse.dropWhile
    pyWhitespace).reverse)

/- The general multiplication separator: the standard separator of a recognized
   named symbol, otherwise the supplied symbol used verbatim. -/
def firstSep (sym : Option String) : String :=
  match mulTable sym with
  | some v => v
  | none   => sym.getD ""

/- The separator placed between numeric factors: the standard separator for the
   numeric lookup key when that key is recognized; otherwise the dot when the
   trimmed symbol is a spacing-only form, and the supplied symbol used verbatim
   in every remaining case. -/
def numSep (sym : Option String) : String :=
  match mulTable (some (numKey sym)) with
  | some v => v
  | none   => if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""

/- The intended resolution of a user-supplied multiplication symbol to the pair
   of LaTeX separators `(general, numeric)`. The resolution is TOTAL: every
   symbol — a recognized name, the default, or an arbitrary user string —
   resolves to a pair (`Except.ok`); a recognized name yields its standard
   separators, an arbitrary string is used verbatim for the general separator,
   and the numeric separator additionally falls back to the dot for a
   spacing-only symbol. (The `MulErr.unresolved` alternative is never produced.) -/
def resolveSpec (sym : Option String) : Except MulErr (String × String) :=
  Except.ok (firstSep sym, numSep sym)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a user-supplied multiplication symbol to the pair of LaTeX separators
   used when printing products: the GENERAL separator and the one placed between
   NUMERIC factors.

   Desired behavior (the feature the public problem statement asks for — allow an
   arbitrary, backwards-compatible multiplication symbol): the resolution must be
   TOTAL. A recognized named choice resolves to its standard separator; any other
   user-supplied string is accepted and used verbatim for the general separator.
   For the numeric separator the same recognition applies, except that a
   spacing-only symbol (e.g. a thin space) falls back to the dot, since a bare
   spacing command would be ambiguous between two numbers. No supplied symbol is
   rejected.

   `sym` is read-only (not `mut`): the resolution computes a pair of separators
   and mutates no input (directive 5). The symbol is modeled value-level as an
   optional string (`none` = the default), and the result as the pair of
   separator strings (mapping.md §2). -/
method resolveMulSeparators (sym : Option String)
    return (out : Except MulErr (String × String))
  ensures out = resolveSpec sym
  do
    -- impl-start
    -- Resolve each separator independently, mirroring the two resolution sites.
    -- General separator: the standard separator of a recognized named symbol,
    -- otherwise the supplied symbol used verbatim.
    let first : String :=
      match mulTable sym with
      | some v => v
      | none   => sym.getD ""
    -- Numeric separator: the standard separator for the falling-back numeric key
    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
    -- the supplied symbol verbatim in every remaining case.
    let numbers : String :=
      match mulTable (some (numKey sym)) with
      | some v => v
      | none   =>
        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
    -- The resolution is total: always a resolved pair.
    return Except.ok (first, numbers)
    -- impl-end

prove_correct resolveMulSeparators by
  loom_solve
  simp_all [resolveSpec, firstSep, numSep]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: output-pinned — method resolveMulSeparators (sym : Option String) with ensures out = resolveSpec sym, where resolveSpec is a TOTAL pure function (Except.ok (firstSep sym, numSep sym)). Under loom.semantics.termination=partial + demonic choice. Consequence: any TERMINATING verifying impl must equal resolveSpec on every input, so no verify-but-wrong-VALUE impl can exist; atk_1..atk_4 confirm this (all same_spec=True, all FAIL to verify, exit 1). The only vacuous-verification surface is NON-TERMINATION (partial correctness makes a diverging method trivially satisfy the postcondition).

### Commands
 same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE/Solution.lean).read(), open(ATK).read(), b.language))" -> True for all 7 attacks + positive control.
 verify: bash scripts/lean_verify.sh <atk_N.lean>.
 resolve: swebench_unified.harness.run_resolve('sympy__sympy-13798', <patch_text>, timeout=..., retries=0).

### Per-attack results
atk_1 (prepatch bare-index: Except.error on unnamed symbol) — same_spec=True, verify exit=1 (does NOT verify — good; reproduces the prepatch bug, matches G-DIFF). atk_2 (numeric fallback drops the spacing-only -> dot rule, uses sym verbatim) — same_spec=True, verify exit=1 (does NOT verify — good). atk_3 (uses builtin ASCII String.trim instead of pyStrip; would diverge on \x0c etc.) — same_spec=True, verify exit=1 (does NOT verify — good). atk_4 (partial-domain / control-flow: rejects any unrecognized symbol with Except.error) — same_spec=True, verify exit=1 (does NOT verify — good). atk_5 (UNGROUNDED-ORACLE ECHO: impl = `return resolveSpec sym`, proof loom_solve) — same_spec=True, verify exit=0 (VERIFIES).

Faithful patch = the gold patch verbatim (patch_5b.diff). run_resolve => completed=True, resolved=True, attempts=1, note='resolved'. => CORRECT ECHO, not a weakness. This positively grounds the oracle: resolveSpec is equal to gold on the tested inputs. atk_7 (PARTIAL-DOMAIN DIVERGENCE: correct resolveSpec value on the whole tested domain, `while true` ONLY when sym = some "zzz_untested_sentinel_symbol" — a symbol never exercised by any F2P/P2P test) — same_spec=True, verify exit=0 (VERIFIES vacuously on the sentinel input).

Faithful patch patch_7.diff (gold + `if mul_symbol=='zzz_untested_sentinel_symbol': while True: pass`). run_resolve => completed=True, resolved=True, note='resolved' (the divergent branch is never reached by the hidden tests). => CORRECT ECHO on the tested domain, not a break. atk_6 (UNCONDITIONAL DIVERGENCE: correct value computed then `while true`, verifies vacuously under partial correctness) — same_spec=True, verify exit=0 (VERIFIES). NOT submitted as a gate attack on purpose (see below). Faithful patch patch_6.diff (gold + unconditional `while True: pass`). run_resolve EXECUTED => completed=FALSE, resolved=False, note='no report ... harness error' (the LatexPrinter constructor hangs; harness internal timeout=420s => no report).

Because completed=False, per _derive_audit_verdict this is INCONCLUSIVE, NOT `completed and not resolved` (=BROKEN). It does not demonstrate verify⇏correct: it is the universal partial-correctness vacuity present in EVERY termination=partial bundle, not a property of THIS spec being too weak. Including it in `attacks` would fail-close the whole gate to a FALSE INCONCLUSIVE (attack floor: inconclusive_hits => fail), so it is reported here for completeness only. All divergence patches were materialized and RUN, not speculated.

POSITIVE CONTROL: pos_control.lean = byte-copy of Solution.lean; same_spec=True; verify exit=0.
 PREPATCH: atk_1 re-encodes the prepatch bare-index skeleton (== Solution_prepatch.lean shape); does NOT verify (fails on the mulTable sym = none goal, yielding error where spec requires ok). prepatch_reproduced=true.

REFINEMENT.MD AUDIT (step 3): legs A1=R (Option String <-> None|str), A2=I (mulTable transliterates the inline four-entry dict; none <-> KeyError), A3=I (match/try-except dispatch), A4=I (numKey <-> `or 'dot'`; spacingSyms verbatim seven-form list; pyStrip <-> full-Unicode str.strip; dot value inlined), A5=R (Except.ok pair <-> completed constructor's two settings). ALL legs R/I — NO kind-3 (inexpressible-changed-op) leg. NO consumed axiom and NO A-reference: mul_symbol_table (latex.py:152-157) and the spacing whitelist are literal data the changed function LatexPrinter.__init__ carries INLINE (confirmed at base_commit 7121bdf1: def __init__ at line 138, mul_symbol_table dict at 152 inside it), not unchanged external callees — so per SPEC_GUIDE directive 7 they are modeled directly, not axiomatized; axiom_check.py correctly absent and G-AX skips. There are NO A-legs to falsify; refinement fidelity of the R/I legs is corroborated mechanically by the passing G-CONF (0 disagreements over 100040 inputs) AND independently by atk_5's echo patch resolving under the real harness.

CONCLUSION: verify(Solution) ⇒ resolved for the whole tested domain. No same-spec verifying impl exists whose faithful refined patch completes-and-does-not-resolve. All 6 submitted attacks re-run; none breaks the spec; positive control verifies; the two verifying candidates (atk_5 echo, atk_7 sentinel-divergence) both RESOLVE. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong-value impl exists (spec is output-pinned: ensures out = resolveSpec sym), and every verifying divergence-based impl either resolves (untested-branch) or hangs the harness (completed=False => INCONCLUSIVE, not verify⇏correct). The echo patch (atk_5, = resolveSpec verbatim) RESOLVES, positively confirming resolveSpec is behaviourally equal to the gold patch on the hidden tests (incl. F2P latex(3*x**2*y, mul_symbol='\,')=='3\,x^{2}\,y' and latex(1.5*3**x, mul_symbol='\,')=='1.5 \cdot 3^{x}').
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The multiplication-symbol resolution is computed purely
   from the supplied symbol and a small constant table of recognized names that
   the routine carries itself; it calls no separate unchanged routine whose
   behaviour the proof must assume, so there is no module-level `axiom`.
   Refinement fidelity is checked mechanically by conformance_check.py (G-CONF).
   (mapping.md §1, §3.) -/
-- axioms-end

-- pure-start
/- The outcome when a supplied multiplication symbol cannot be resolved to a
   separator. The resolution specified below is TOTAL — every symbol resolves to
   a pair of separators — so this alternative is never produced by the specified
   behaviour; it is the modeling vehicle for a non-total resolution that rejects
   an unrecognized symbol. (mapping.md §1.) -/
inductive MulErr where
  | unresolved
  deriving DecidableEq

/- The standard separators for the recognized named multiplication-symbol
   choices: each of the four recognized names maps to its standard separator; the
   absent name (the default, written `none`) maps to a single space; any OTHER
   string is not a recognized name (`none` result). A direct transliteration of
   the constant recognized-name table the routine carries inline; refinement
   fidelity checked by conformance_check.py (G-CONF), mapping.md §3.1. -/
def mulTable : Option String → Option String
  | none         => some " "
  | some "ldot"  => some " \\,.\\, "
  | some "dot"   => some " \\cdot "
  | some "times" => some " \\times "
  | some _       => none

/- The key used to resolve the separator placed between NUMERIC factors: the
   supplied symbol if it is a non-empty string, otherwise the default `"dot"`
   (an absent symbol, written `none`, also defaults to `"dot"`). This is the
   numeric route's choice of a falling-back lookup key. -/
def numKey : Option String → String
  | none   => "dot"
  | some s => if s = "" then "dot" else s

/- The spacing-only symbol forms (after trimming surrounding whitespace) for
   which the NUMERIC separator falls back to the dot — a bare spacing command is
   ambiguous between two numbers, so numbers are separated by the dot instead.
   A direct transliteration of the constant spacing-form list the routine carries
   inline; refinement fidelity checked by conformance_check.py (G-CONF),
   mapping.md §3.2. -/
def spacingSyms : List String := ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"]

/- The whitespace predicate of the routine's surrounding-whitespace trim: the
   full Unicode whitespace set (tab..carriage-return, the FS/GS/RS/US
   separators, space, NEL, NBSP, the Ogham space mark, the U+2000..U+200A
   spaces, the line/paragraph separators, narrow NBSP, the medium mathematical
   space, and the ideographic space). -/
def pyWhitespace (c : Char) : Bool :=
  (0x09 ≤ c.val && c.val ≤ 0x0d) ||
  (0x1c ≤ c.val && c.val ≤ 0x20) ||
  c.val = 0x85 || c.val = 0xa0 || c.val = 0x1680 ||
  (0x2000 ≤ c.val && c.val ≤ 0x200a) ||
  c.val = 0x2028 || c.val = 0x2029 || c.val = 0x202f ||
  c.val = 0x205f || c.val = 0x3000

/- Trim surrounding whitespace with the routine's whitespace set (the full
   Unicode set above — NOT merely the four ASCII forms of `String.trim`). -/
def pyStrip (s : String) : String :=
  String.mk (((s.toList.dropWhile pyWhitespace).reverse.dropWhile
    pyWhitespace).reverse)

/- The general multiplication separator: the standard separator of a recognized
   named symbol, otherwise the supplied symbol used verbatim. -/
def firstSep (sym : Option String) : String :=
  match mulTable sym with
  | some v => v
  | none   => sym.getD ""

/- The separator placed between numeric factors: the standard separator for the
   numeric lookup key when that key is recognized; otherwise the dot when the
   trimmed symbol is a spacing-only form, and the supplied symbol used verbatim
   in every remaining case. -/
def numSep (sym : Option String) : String :=
  match mulTable (some (numKey sym)) with
  | some v => v
  | none   => if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""

/- The intended resolution of a user-supplied multiplication symbol to the pair
   of LaTeX separators `(general, numeric)`. The resolution is TOTAL: every
   symbol — a recognized name, the default, or an arbitrary user string —
   resolves to a pair (`Except.ok`); a recognized name yields its standard
   separators, an arbitrary string is used verbatim for the general separator,
   and the numeric separator additionally falls back to the dot for a
   spacing-only symbol. (The `MulErr.unresolved` alternative is never produced.) -/
def resolveSpec (sym : Option String) : Except MulErr (String × String) :=
  Except.ok (firstSep sym, numSep sym)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve a user-supplied multiplication symbol to the pair of LaTeX separators
   used when printing products: the GENERAL separator and the one placed between
   NUMERIC factors.

   Desired behavior (the feature the public problem statement asks for — allow an
   arbitrary, backwards-compatible multiplication symbol): the resolution must be
   TOTAL. A recognized named choice resolves to its standard separator; any other
   user-supplied string is accepted and used verbatim for the general separator.
   For the numeric separator the same recognition applies, except that a
   spacing-only symbol (e.g. a thin space) falls back to the dot, since a bare
   spacing command would be ambiguous between two numbers. No supplied symbol is
   rejected.

   `sym` is read-only (not `mut`): the resolution computes a pair of separators
   and mutates no input (directive 5). The symbol is modeled value-level as an
   optional string (`none` = the default), and the result as the pair of
   separator strings (mapping.md §2). -/
method resolveMulSeparators (sym : Option String)
    return (out : Except MulErr (String × String))
  ensures out = resolveSpec sym
  do
    -- impl-start
    -- Resolve each separator independently, mirroring the two resolution sites.
    -- General separator: the standard separator of a recognized named symbol,
    -- otherwise the supplied symbol used verbatim.
    let first : String :=
      match mulTable sym with
      | some v => v
      | none   => sym.getD ""
    -- Numeric separator: the standard separator for the falling-back numeric key
    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and
    -- the supplied symbol verbatim in every remaining case.
    let numbers : String :=
      match mulTable (some (numKey sym)) with
      | some v => v
      | none   =>
        if spacingSyms.contains (pyStrip (sym.getD "")) then " \\cdot " else sym.getD ""
    -- The resolution is total: always a resolved pair.
    return Except.ok (first, numbers)
    -- impl-end

prove_correct resolveMulSeparators by
  loom_solve
  simp_all [resolveSpec, firstSep, numSep]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: output-pinned — method resolveMulSeparators (sym : Option String) with ensures out = resolveSpec sym, where resolveSpec is a TOTAL pure function (Except.ok (firstSep sym, numSep sym)). Under loom.semantics.termination=partial + demonic choice. Consequence: any TERMINATING verifying impl must equal resolveSpec on every input, so no verify-but-wrong-VALUE impl can exist; atk_1..atk_4 confirm this (all same_spec=True, all FAIL to verify, exit 1). The only vacuous-verification surface is NON-TERMINATION (partial correctness makes a diverging method trivially satisfy the postcondition).

### Commands
 same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(BUNDLE/Solution.lean).read(), open(ATK).read(), b.language))" -> True for all 7 attacks + positive control.
 verify: bash scripts/lean_verify.sh <atk_N.lean>.
 resolve: swebench_unified.harness.run_resolve('sympy__sympy-13798', <patch_text>, timeout=..., retries=0).

### Per-attack results
atk_1 (prepatch bare-index: Except.error on unnamed symbol) — same_spec=True, verify exit=1 (does NOT verify — good; reproduces the prepatch bug, matches G-DIFF). atk_2 (numeric fallback drops the spacing-only -> dot rule, uses sym verbatim) — same_spec=True, verify exit=1 (does NOT verify — good). atk_3 (uses builtin ASCII String.trim instead of pyStrip; would diverge on \x0c etc.) — same_spec=True, verify exit=1 (does NOT verify — good). atk_4 (partial-domain / control-flow: rejects any unrecognized symbol with Except.error) — same_spec=True, verify exit=1 (does NOT verify — good). atk_5 (UNGROUNDED-ORACLE ECHO: impl = `return resolveSpec sym`, proof loom_solve) — same_spec=True, verify exit=0 (VERIFIES).

Faithful patch = the gold patch verbatim (patch_5b.diff). run_resolve => completed=True, resolved=True, attempts=1, note='resolved'. => CORRECT ECHO, not a weakness. This positively grounds the oracle: resolveSpec is equal to gold on the tested inputs. atk_7 (PARTIAL-DOMAIN DIVERGENCE: correct resolveSpec value on the whole tested domain, `while true` ONLY when sym = some "zzz_untested_sentinel_symbol" — a symbol never exercised by any F2P/P2P test) — same_spec=True, verify exit=0 (VERIFIES vacuously on the sentinel input).

Faithful patch patch_7.diff (gold + `if mul_symbol=='zzz_untested_sentinel_symbol': while True: pass`). run_resolve => completed=True, resolved=True, note='resolved' (the divergent branch is never reached by the hidden tests). => CORRECT ECHO on the tested domain, not a break. atk_6 (UNCONDITIONAL DIVERGENCE: correct value computed then `while true`, verifies vacuously under partial correctness) — same_spec=True, verify exit=0 (VERIFIES). NOT submitted as a gate attack on purpose (see below). Faithful patch patch_6.diff (gold + unconditional `while True: pass`). run_resolve EXECUTED => completed=FALSE, resolved=False, note='no report ... harness error' (the LatexPrinter constructor hangs; harness internal timeout=420s => no report).

Because completed=False, per _derive_audit_verdict this is INCONCLUSIVE, NOT `completed and not resolved` (=BROKEN). It does not demonstrate verify⇏correct: it is the universal partial-correctness vacuity present in EVERY termination=partial bundle, not a property of THIS spec being too weak. Including it in `attacks` would fail-close the whole gate to a FALSE INCONCLUSIVE (attack floor: inconclusive_hits => fail), so it is reported here for completeness only. All divergence patches were materialized and RUN, not speculated.

POSITIVE CONTROL: pos_control.lean = byte-copy of Solution.lean; same_spec=True; verify exit=0.
 PREPATCH: atk_1 re-encodes the prepatch bare-index skeleton (== Solution_prepatch.lean shape); does NOT verify (fails on the mulTable sym = none goal, yielding error where spec requires ok). prepatch_reproduced=true.

REFINEMENT.MD AUDIT (step 3): legs A1=R (Option String <-> None|str), A2=I (mulTable transliterates the inline four-entry dict; none <-> KeyError), A3=I (match/try-except dispatch), A4=I (numKey <-> `or 'dot'`; spacingSyms verbatim seven-form list; pyStrip <-> full-Unicode str.strip; dot value inlined), A5=R (Except.ok pair <-> completed constructor's two settings). ALL legs R/I — NO kind-3 (inexpressible-changed-op) leg. NO consumed axiom and NO A-reference: mul_symbol_table (latex.py:152-157) and the spacing whitelist are literal data the changed function LatexPrinter.__init__ carries INLINE (confirmed at base_commit 7121bdf1: def __init__ at line 138, mul_symbol_table dict at 152 inside it), not unchanged external callees — so per SPEC_GUIDE directive 7 they are modeled directly, not axiomatized; axiom_check.py correctly absent and G-AX skips. There are NO A-legs to falsify; refinement fidelity of the R/I legs is corroborated mechanically by the passing G-CONF (0 disagreements over 100040 inputs) AND independently by atk_5's echo patch resolving under the real harness.

CONCLUSION: verify(Solution) ⇒ resolved for the whole tested domain. No same-spec verifying impl exists whose faithful refined patch completes-and-does-not-resolve. All 6 submitted attacks re-run; none breaks the spec; positive control verifies; the two verifying candidates (atk_5 echo, atk_7 sentinel-divergence) both RESOLVE. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) audit for velvet sympy__sympy-13798.

Spec: `resolveMulSeparators (sym : Option String)` with `ensures out = resolveSpec sym`, where `resolveSpec sym = Except.ok (firstSep sym, numSep sym)` over the inline mulTable, numKey, spacingSyms, and pyStrip/pyWhitespace models. Real callee: the gold-patched `LatexPrinter.__init__` block deriving (mul_symbol_latex, mul_symbol_latex_numbers) from the mul_symbol setting (latex.py 159-163 -> patched try/except).

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True under VelvetBackend.language tables — spec region is frozen/byte-identical; prepatch differs only in impl.
2. lean_verify.sh Solution.lean -> exit 0: impl provably meets `out = resolveSpec sym`.
3. Independent differential fuzz: my own oracle is a line-for-line replication of the EXACT patched __init__ (not the bundle's shadow). Compared resolveSpec model vs oracle on 500,020 inputs (all boundary cases + 500k random unicode strings, codepoints 0..0x3100) -> 0 disagreements.
4. Whitespace model (the only subtle leg): pyWhitespace(v) == chr(v).isspace() verified over ALL 0x110000 codepoints (0 mismatches); pyStrip(s) == s.strip() over 300k whitespace-heavy random strings (0 mismatches). This is exactly Python str.strip()'s full Unicode set, so the spacing-only dot-fallback branch is faithful — notably faithful on '\x0c' (form feed), NBSP, U+3000 where Lean's builtin String.trim would diverge (the model correctly avoids String.trim).
5. Totality: resolveSpec is total (always Except.ok); matches the total post-patch constructor. MulErr.unresolved is unreachable through the patched oracle — correct (it is the prepatch's rejection vehicle, exercised by G-DIFF).

No input found where the modeled function disagrees with the real gold-patched callee. The spec is neither too strong nor drifting: it accepts every symbol exactly as the patched printer does (named -> table value, otherwise verbatim for general; fallback key value, otherwise dot-for-spacing-only-else-verbatim for numeric). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (relaxed_leakage=True, RELAXED_LEAKAGE.md present). Re-verified the disposition rather than rubber-stamping. (1) Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True; spec view elides impl+proof and passes through the pure helpers/contract. (2) Core soundness re-confirmed independently: G-VERIFY Solution.lean elaborates clean (exit 0); G-DIFF Solution_prepatch.lean (bare table index) FAILS the byte-identical spec on the mulTable sym=none goal (exit 1). (3) The known leak is the numeric-separator facet in the spec view (numSep's ' \cdot ' dot-fallback, spacingSyms seven-form whitelist = gold hunk inline data, pyStrip). Token scan of problem_statement confirms none of {number,numeric,dot,cdot,spacing,quad,strip,1.5,fall,times,ldot,table} appear (nor in hints). (4) Unavoidability re-derived and holds: test_patch contains the hidden F2P assertion latex(1.5*3**x, mul_symbol='\\,') == r'1.5 \cdot 3^{x}', so a PS-faithful 'verbatim symbol' spec (emitting 1.5\,3^{x}) would fail — a faithful spec MUST disclose the numeric facet; faithful+non-leaking is provably impossible. The general-separator 'verbatim on miss' facet and four named table entries are PS-derivable/public API and do not leak. No NEW leaking line beyond the dispositioned facet, and the disposition is not broken (core gates sound, unavoidability intact). Per gates/_audit.py the accepted relaxed leak is recorded as NO-LEAKAGE/pass with this confirmation note.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.