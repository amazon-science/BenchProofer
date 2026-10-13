# P2 adversarial audit — astropy__astropy-14508

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an EXACT functional equality: problem_spec_formatFloat inp result := result = truncate20 (normE inp.reprStr). It pins `result` to a single value on every input, so any implementation whose correct_formatFloat closes (no sorry) is extensionally equal to the gold post-patch behavior. No same-spec wrong impl closes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
 
 -- impl-start
 def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do
-  let mut valueStr := normE inp.reprStr
+  let mut valueStr := normE inp.fixedStr
   let strLen := valueStr.length
   if strLen > 20 then
     match valueStr.findIdx? (· = 'E') with
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,14 +79,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do
-  let mut valueStr := normE inp.reprStr
-  let strLen := valueStr.length
-  if strLen > 20 then
-    match valueStr.findIdx? (· = 'E') with
-    | none     => valueStr := valueStr.take 20
-    | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
-  return valueStr
+def implementation_formatFloat (inp : FmtInput) : List Char :=
+  normE inp.reprStr
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
   let strLen := valueStr.length
   if strLen > 20 then
     match valueStr.findIdx? (· = 'E') with
-    | none     => valueStr := valueStr.take 20
+    | none     => valueStr := valueStr.take 19
     | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
   return valueStr
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,8 +84,8 @@
   let strLen := valueStr.length
   if strLen > 20 then
     match valueStr.findIdx? (· = 'E') with
-    | none     => valueStr := valueStr.take 20
-    | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
+    | none     => valueStr := valueStr.take (20 - strLen) ++ valueStr.drop 0
+    | some idx => valueStr := valueStr.take 20
   return valueStr
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
 def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do
   let mut valueStr := normE inp.reprStr
   let strLen := valueStr.length
-  if strLen > 20 then
+  if strLen > 21 then
     match valueStr.findIdx? (· = 'E') with
     | none     => valueStr := valueStr.take 20
     | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,14 +79,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do
-  let mut valueStr := normE inp.reprStr
-  let strLen := valueStr.length
-  if strLen > 20 then
-    match valueStr.findIdx? (· = 'E') with
-    | none     => valueStr := valueStr.take 20
-    | some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
-  return valueStr
+def implementation_formatFloat (inp : FmtInput) : List Char :=
+  inp.reprStr
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,7 +80,7 @@
 
 -- impl-start
 def implementation_formatFloat (inp : FmtInput) : List Char := Id.run do
-  let mut valueStr := normE inp.reprStr
+  let mut valueStr := inp.reprStr
   let strLen := valueStr.length
   if strLen > 20 then
     match valueStr.findIdx? (· = 'E') with
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a floating-point value as the string written into a fixed-width
header card.

A card stores a value together with an optional trailing comment inside a field
of bounded width, so the value's textual form must be kept short: it may be at
most 20 characters long. The value is rendered from its string form and then,
only if that form is longer than the budget, shortened.

The desired behavior:

* Start from the value's *shortest* standard textual form — the representation a
  language runtime prints for the number — written with an upper-case exponent
  marker `E` (any lower-case `e` is upper-cased). This form already contains a
  decimal point or an exponent, so no extra padding is added.
* If that form fits within 20 characters, it is used verbatim.
* If it is longer than 20 characters, it is shortened to 20:
  * with no exponent marker, keep the first 20 characters;
  * with an exponent marker, keep the exponent suffix intact (from the marker to
    the end) and truncate the leading significand so the whole string is 20
    characters.

The point is that the *short* textual form is the starting point: a number such
as one whose shortest form already fits must be rendered with that short form,
never expanded to a longer fixed-precision form that would overflow the budget
and force the trailing comment to be truncated.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The numeric
-- value enters the model through its already-computed textual observations
-- (its shortest standard form and its fixed-precision form); both are grounded
-- inputs, so no `opaque`/`axiom` callee contract is needed. The shortening rule
-- is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- The textual observations of a numeric value that the rendering rule reads.

* `reprStr` — the value's shortest standard textual form (what a runtime prints
  for the number, e.g. `0.009125`);
* `fixedStr` — the value's fixed-precision textual form (a representation carried
  to many significant digits, e.g. `0.009124999999999999`).

Both are pure functions of the value; the rule uses the carrier appropriate to
the desired behavior. -/
structure FmtInput where
  reprStr : List Char
  fixedStr : List Char

/-- Upper-case the exponent marker: every lower-case `e` becomes `E`. -/
def normE (s : List Char) : List Char :=
  s.map (fun c => if c = 'e' then 'E' else c)

/-- Limit a value string to at most 20 characters. If it already fits, it is
returned unchanged; otherwise, if there is no exponent marker the first 20
characters are kept, and if there is one the exponent suffix (from the marker
onward) is kept intact while the leading significand is truncated so the whole
string is 20 characters. -/
def truncate20 (valueStr : List Char) : List Char :=
  let strLen := valueStr.length
  if strLen > 20 then
    match valueStr.findIdx? (· = 'E') with
    | none     => valueStr.take 20
    | some idx => valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
  else
    valueStr
-- pure-end

-- post-conditions-start
/-- The rendered string is the value's shortest standard textual form (with an
upper-cased exponent marker), shortened to at most 20 characters by the rule
above. The fixed-precision form is NOT used. -/
def problem_spec_formatFloat (inp : FmtInput) (result : List Char) : Prop :=
  result = truncate20 (normE inp.reprStr)
-- post-conditions-end

-- impl-start
def implementation_formatFloat (inp : FmtInput) : List Char :=
  truncate20 (normE inp.reprStr)
-- impl-end

-- proof-start
theorem correct_formatFloat :
    ∀ (inp : FmtInput),
      problem_spec_formatFloat inp (implementation_formatFloat inp) := by
  intro inp
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL executed. same_spec=True verified for pc + all 7 attacks (spec regions byte-identical; only impl+proof edited). Command per file: `bash scripts/lean_verify.sh <file>`.

### RESULTS (exit codes):
- pc.lean (positive control, alt closing impl `truncate20 (normE inp.reprStr)` by rfl): exit 0 = VERIFIES. `#print axioms correct_formatFloat` -> 'does not depend on any axioms' (clean, pc_ax.lean exit 0).
- atk_1 (prepatch bug: consume inp.fixedStr instead of reprStr): exit 1 — `rfl failed: LHS != RHS`. Genuine: differs from gold on 0.009125 (gold '0.009125' vs '0.009124999999999999').
- atk_2 (omit truncation, return normE reprStr): exit 1. Differs on any >20-char no-E carrier (len-25 '1'*25).
- atk_3 (boundary off-by-one: take 19 in none branch): exit 1. Differs (len 19 vs 20) on >20 no-E carrier.
- atk_4 (control-flow swap: none/some bodies swapped): exit 1.
- atk_5 (boundary shift: truncate only when strLen > 21): exit 1. Diverges precisely at length 21 (gold clamps to 20; a5 keeps 21). Confirmed genuine divergence.
- atk_6 (ungrounded-oracle echo: return inp.reprStr verbatim, no normE/truncate): exit 1. Differs when e-marker present and on >20 carriers.
- atk_7 (skip normE, keep truncation): exit 1. Differs on any carrier containing lower-case 'e'.

All 7 failures are genuine `rfl failed: left-hand side != right-hand side` errors (real disequalities), NOT syntax errors — confirmed by grep of verify logs. Stronger tactics (simp_all [Id.run, normE] <;> aesop) also FAIL on atk_1_strong and atk_5_strong (both exit 1), ruling out weak-tactic artifacts. A Python model of gold vs each attack confirms each attack differs from gold on a concrete input, so the universal correctness statement is false and no sound proof can close.

Because NO wrong impl closes with clean axioms, there are zero verifying patches to materialize/resolve (patches={}); the resolve-run obligation is vacuously satisfied. The prepatch bug (atk_1) was reproduced and correctly REJECTED by the spec (fails to close), consistent with G-DIFF (Solution_prepatch.lean: verification failed).

REFINEMENT.MD AUDIT (A-legs): meta.json has axioms=[], deep_model_references=[], opaque_callees=[]. refinement.md tags all 7 legs R/I (ops: 1=R normE, 2/3=I length+guard, 4=R find->Option carrier, 5/6/7=I slice/return). NO A-consumed, NO A-reference, NO kind-3 leg — so there is no axiom/deep-model correspondence to falsify; the R/I legs are mechanically covered by G-CONF (checked=120025, 0 disagreements). The callees str(value)/f'{value:.16G}' are correctly modeled as grounded inputs reprStr/fixedStr (the patch changes WHICH carrier feeds truncation), not axiomatized — a fair modeling boundary. G-AX skip is correct.

Verdict: SOUND — exact-equality postcondition leaves zero extensional slack; every same-spec wrong impl (incl. the prepatch bug and 4+ further distinct wrong classes: partial-domain/boundary a3/a5, control-flow a4, ungrounded-oracle echo a6, missing-normE a7, wrong-carrier a1, missing-truncation a2) fails to verify, while the positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is an EXACT functional equality: problem_spec_formatFloat inp result := result = truncate20 (normE inp.reprStr). It pins `result` to a single value on every input, so any implementation whose correct_formatFloat closes (no sorry) is extensionally equal to the gold post-patch behavior. No same-spec wrong impl closes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a floating-point value as the string written into a fixed-width
header card.

A card stores a value together with an optional trailing comment inside a field
of bounded width, so the value's textual form must be kept short: it may be at
most 20 characters long. The value is rendered from its string form and then,
only if that form is longer than the budget, shortened.

The desired behavior:

* Start from the value's *shortest* standard textual form — the representation a
  language runtime prints for the number — written with an upper-case exponent
  marker `E` (any lower-case `e` is upper-cased). This form already contains a
  decimal point or an exponent, so no extra padding is added.
* If that form fits within 20 characters, it is used verbatim.
* If it is longer than 20 characters, it is shortened to 20:
  * with no exponent marker, keep the first 20 characters;
  * with an exponent marker, keep the exponent suffix intact (from the marker to
    the end) and truncate the leading significand so the whole string is 20
    characters.

The point is that the *short* textual form is the starting point: a number such
as one whose shortest form already fits must be rendered with that short form,
never expanded to a longer fixed-precision form that would overflow the budget
and force the trailing comment to be truncated.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The numeric
-- value enters the model through its already-computed textual observations
-- (its shortest standard form and its fixed-precision form); both are grounded
-- inputs, so no `opaque`/`axiom` callee contract is needed. The shortening rule
-- is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- The textual observations of a numeric value that the rendering rule reads.

* `reprStr` — the value's shortest standard textual form (what a runtime prints
  for the number, e.g. `0.009125`);
* `fixedStr` — the value's fixed-precision textual form (a representation carried
  to many significant digits, e.g. `0.009124999999999999`).

Both are pure functions of the value; the rule uses the carrier appropriate to
the desired behavior. -/
structure FmtInput where
  reprStr : List Char
  fixedStr : List Char

/-- Upper-case the exponent marker: every lower-case `e` becomes `E`. -/
def normE (s : List Char) : List Char :=
  s.map (fun c => if c = 'e' then 'E' else c)

/-- Limit a value string to at most 20 characters. If it already fits, it is
returned unchanged; otherwise, if there is no exponent marker the first 20
characters are kept, and if there is one the exponent suffix (from the marker
onward) is kept intact while the leading significand is truncated so the whole
string is 20 characters. -/
def truncate20 (valueStr : List Char) : List Char :=
  let strLen := valueStr.length
  if strLen > 20 then
    match valueStr.findIdx? (· = 'E') with
    | none     => valueStr.take 20
    | some idx => valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx
  else
    valueStr
-- pure-end

-- post-conditions-start
/-- The rendered string is the value's shortest standard textual form (with an
upper-cased exponent marker), shortened to at most 20 characters by the rule
above. The fixed-precision form is NOT used. -/
def problem_spec_formatFloat (inp : FmtInput) (result : List Char) : Prop :=
  result = truncate20 (normE inp.reprStr)
-- post-conditions-end

-- impl-start
def implementation_formatFloat (inp : FmtInput) : List Char :=
  truncate20 (normE inp.reprStr)
-- impl-end

-- proof-start
theorem correct_formatFloat :
    ∀ (inp : FmtInput),
      problem_spec_formatFloat inp (implementation_formatFloat inp) := by
  intro inp
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL executed. same_spec=True verified for pc + all 7 attacks (spec regions byte-identical; only impl+proof edited). Command per file: `bash scripts/lean_verify.sh <file>`.

### RESULTS (exit codes):
- pc.lean (positive control, alt closing impl `truncate20 (normE inp.reprStr)` by rfl): exit 0 = VERIFIES. `#print axioms correct_formatFloat` -> 'does not depend on any axioms' (clean, pc_ax.lean exit 0).
- atk_1 (prepatch bug: consume inp.fixedStr instead of reprStr): exit 1 — `rfl failed: LHS != RHS`. Genuine: differs from gold on 0.009125 (gold '0.009125' vs '0.009124999999999999').
- atk_2 (omit truncation, return normE reprStr): exit 1. Differs on any >20-char no-E carrier (len-25 '1'*25).
- atk_3 (boundary off-by-one: take 19 in none branch): exit 1. Differs (len 19 vs 20) on >20 no-E carrier.
- atk_4 (control-flow swap: none/some bodies swapped): exit 1.
- atk_5 (boundary shift: truncate only when strLen > 21): exit 1. Diverges precisely at length 21 (gold clamps to 20; a5 keeps 21). Confirmed genuine divergence.
- atk_6 (ungrounded-oracle echo: return inp.reprStr verbatim, no normE/truncate): exit 1. Differs when e-marker present and on >20 carriers.
- atk_7 (skip normE, keep truncation): exit 1. Differs on any carrier containing lower-case 'e'.

All 7 failures are genuine `rfl failed: left-hand side != right-hand side` errors (real disequalities), NOT syntax errors — confirmed by grep of verify logs. Stronger tactics (simp_all [Id.run, normE] <;> aesop) also FAIL on atk_1_strong and atk_5_strong (both exit 1), ruling out weak-tactic artifacts. A Python model of gold vs each attack confirms each attack differs from gold on a concrete input, so the universal correctness statement is false and no sound proof can close.

Because NO wrong impl closes with clean axioms, there are zero verifying patches to materialize/resolve (patches={}); the resolve-run obligation is vacuously satisfied. The prepatch bug (atk_1) was reproduced and correctly REJECTED by the spec (fails to close), consistent with G-DIFF (Solution_prepatch.lean: verification failed).

REFINEMENT.MD AUDIT (A-legs): meta.json has axioms=[], deep_model_references=[], opaque_callees=[]. refinement.md tags all 7 legs R/I (ops: 1=R normE, 2/3=I length+guard, 4=R find->Option carrier, 5/6/7=I slice/return). NO A-consumed, NO A-reference, NO kind-3 leg — so there is no axiom/deep-model correspondence to falsify; the R/I legs are mechanically covered by G-CONF (checked=120025, 0 disagreements). The callees str(value)/f'{value:.16G}' are correctly modeled as grounded inputs reprStr/fixedStr (the patch changes WHICH carrier feeds truncation), not axiomatized — a fair modeling boundary. G-AX skip is correct.

Verdict: SOUND — exact-equality postcondition leaves zero extensional slack; every same-spec wrong impl (incl. the prepatch bug and 4+ further distinct wrong classes: partial-domain/boundary a3/a5, control-flow a4, ungrounded-oracle echo a6, missing-normE a7, wrong-carrier a1, missing-truncation a2) fails to verify, while the positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) on astropy__astropy-14508 lean bundle. Modeled function: _format_float(value), card.py:1300-1327. patch_equals_gold=True.

Checks performed:
1. Solution.lean compiles via scripts/lean_verify.sh (exit 0). #print axioms correct_formatFloat => 'does not depend on any axioms' (no sorryAx; proof is genuine).
2. same_spec(Solution, Solution_prepatch) = True with the lean LanguageTables; the two variants differ only in the impl carrier (reprStr post-patch vs fixedStr pre-patch), which is exactly the discriminating clause the patch/test observe.
3. conformance_check.py passes (checked=120025, disagreements=0), including real str(float) carriers and F2P values 0.009125/8.95/-99.9.

Correspondence to real post-patch callee: value_str = str(value).replace('e','E'); if len>20 { idx=find('E'); [:20] or [:20-(str_len-idx)]+[idx:] }. Lean models reprStr=str(value), normE = per-char e->E (== single-substring replace for numeric reprs), truncate20 = op-for-op transliteration.

Only candidate divergence: Lean Nat truncated subtraction in `20 - (strLen - idx)`. When the E-suffix length (strLen-idx) > 20, Python computes a NEGATIVE slice index (dropping trailing chars) while Lean Nat floors to 0 (take 0 = []). This branch would make the model disagree with the real function. However I searched 2,000,000 random floats plus specials (subnormals 5e-324/1e-323, max 1.8e308, inf/nan): the maximum E-suffix length of any real str(float) is 5 chars ('E-323'/'E+308') because CPython float exponents are at most 3 digits. Since strLen-idx <= 5 << 20 for every possible float `value` (the sole input the real callee receives), the divergent branch is UNREACHABLE. On the reachable domain the modeled function agrees with the real post-patch _format_float on all inputs. Note the conformance shadow is a Python replica and does not itself exercise Lean Nat semantics, but the reachability argument closes this independently.

The abstraction (str(value) -> free List Char input reprStr) over-generalizes only to synthetic strings that no float produces; it does not weaken or over-strengthen behavior on the real input domain. Spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigor checks done: same_spec(Solution.lean, Solution_prepatch.lean)=True with the lean LanguageTables (spec region — imports, doc comment, axioms block, pure helpers normE/truncate20, post-condition — is byte-identical; only the impl differs: reprStr vs fixedStr). Solution.lean compiles clean via scripts/lean_verify.sh (exit 0) and `#print axioms correct_formatFloat` reports 'does not depend on any axioms' — a genuine proof, no sorryAx.

Leakage judgment (spec view vs PUBLIC problem_statement only; hints ignored): NO-LEAKAGE. The public problem_statement is exhaustively self-disclosing. It (a) names the exact function `_format_float` with a source-line link, (b) identifies the exact culprit `f"{value:.16G}"`, (c) gives the exact failing case verbatim ('0.009125' unnecessarily expanded to '0.009124999999999999'), and (d) explicitly prescribes the gold fix in prose: 'before doing f"{value:.16G}", we should attempt to use the string representation provided by Python (str(value)), and we should only attempt to format it ourselves if the resulting string does not fit in 20 characters.'

Every material element of the spec view is already present in the public statement: 'shortest standard textual form' == the problem's str(value); the 20-char 'shorten only if longer' budget == the problem's 'only format ourselves if it does not fit in 20 characters'; the example values 0.009125 / 0.009124999999999999 are quoted in the problem_statement itself. The single discriminating clause of the gold edit (start from the short form, not the fixed-precision form) IS the fix the reporter prescribes publicly. The spec adds only immaterial modeling detail (exponent-marker upper-casing; the UNCHANGED shared 20-char truncation block, which is context common to pre/post-patch, not the edit). Nothing in the spec view makes the task easier than the already-complete public disclosure. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
