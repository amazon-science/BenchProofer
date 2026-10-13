# P2 adversarial audit — django__django-13512

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.lean`, `atk_7b.lean`, `atk_7c.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong-VALUE impl exists. The postcondition out = '"' :: (jsonEscapedSeq text ++ ['"']) pins the output value to a concrete TOTAL recursive model (jsonChar/jsonEscapedSeq, no axioms), so every value-level wrong impl fails verification (atk_1..atk_5, exit 1). The only verifying non-reference impls are value-CORRECT (atk_6 echo, atk_8 foldr) or vacuously-partial-correct divergent loops (atk_7b/atk_7c), whose only faithful VALUE-level refined patch is the gold computation, which resolves.
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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -77,10 +77,10 @@
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = jsonEscapedSeq (text.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := text[i - 1]!
-      result := jsonChar c ++ result
+      let e : List Char := if c.val < 128 then jsonChar c else ['\\', 'u']
+      result := e ++ result
       i := i - 1
     return '"' :: (result ++ ['"'])
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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -71,18 +71,7 @@
   ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = jsonEscapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := jsonChar c ++ result
-      i := i - 1
-    return '"' :: (result ++ ['"'])
+    return '"' :: (text ++ ['"'])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -101,5 +90,3 @@
 
 prove_correct serializeStringValue by
   loom_solve
-  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -77,12 +77,11 @@
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = jsonEscapedSeq (text.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := text[i - 1]!
       result := jsonChar c ++ result
       i := i - 1
-    return '"' :: (result ++ ['"'])
+    return '"' :: result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -77,10 +77,9 @@
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = jsonEscapedSeq (text.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := text[i - 1]!
-      result := jsonChar c ++ result
+      result := result ++ jsonChar c
       i := i - 1
     return '"' :: (result ++ ['"'])
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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -72,12 +72,11 @@
   do
     -- impl-start
     let mut result : List Char := []
-    let mut i := text.length
+    let mut i := text.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = jsonEscapedSeq (text.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := text[i - 1]!
       result := jsonChar c ++ result
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -71,18 +71,7 @@
   ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = jsonEscapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := jsonChar c ++ result
-      i := i - 1
-    return '"' :: (result ++ ['"'])
+    return '"' :: (jsonEscapedSeq text ++ ['"'])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -101,5 +90,3 @@
 
 prove_correct serializeStringValue by
   loom_solve
-  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -77,11 +77,8 @@
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = jsonEscapedSeq (text.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := text[i - 1]!
-      result := jsonChar c ++ result
-      i := i - 1
+      result := result
     return '"' :: (result ++ ['"'])
     -- impl-end
 
@@ -101,5 +98,3 @@
 
 prove_correct serializeStringValue by
   loom_solve
-  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 8 — `atk_7c.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -77,11 +77,8 @@
       invariant 0 ≤ i ∧ i ≤ text.length
       invariant result = jsonEscapedSeq (text.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := text[i - 1]!
-      result := jsonChar c ++ result
-      i := i - 1
+      i := i
     return '"' :: (result ++ ['"'])
     -- impl-end
 
@@ -101,5 +98,3 @@
 
 prove_correct serializeStringValue by
   loom_solve
-  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The single behaviour under specification — how a string
@@ -71,18 +71,7 @@
   ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := text.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ text.length
-      invariant result = jsonEscapedSeq (text.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := text[i - 1]!
-      result := jsonChar c ++ result
-      i := i - 1
-    return '"' :: (result ++ ['"'])
+    return '"' :: (List.foldr (fun c acc => jsonChar c ++ acc) [] text ++ ['"'])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -100,6 +89,8 @@
   rw [hcons, jsonEscapedSeq_cons]
 
 prove_correct serializeStringValue by
+  have h : ∀ l : List Char, List.foldr (fun c acc => jsonChar c ++ acc) [] l = jsonEscapedSeq l := by
+    intro l; induction l with
+    | nil => rfl
+    | cons c cs ih => rw [List.foldr_cons, ih, jsonEscapedSeq_cons]
   loom_solve
-  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single behaviour under specification — how a string
   value is rendered to its JSON text form — is modelled DEEPLY here (the
   spelled-out `jsonChar`/`jsonEscapedSeq` fold below), validated against the
   real standard-library serializer by axiom_check.py (G-AX, A-reference). No
   unchanged callee needs a contract. -/
-- axioms-end

-- pure-start
/- One lowercase hexadecimal digit (`0`–`9`, `a`–`f`). Only ever applied to a
   value `< 16` (the nibbles of a control code point), where it is total. -/
def hexDigit (n : UInt32) : Char :=
  if n < 10 then Char.ofNat (48 + n.toNat) else Char.ofNat (87 + n.toNat)

/- The JSON text of a single code point inside a string literal, when the
   serializer is asked to keep output as the raw text rather than collapsing
   everything outside ASCII to `\uXXXX` escapes:

     *  U+0022 and U+005C take their two-character backslash form;
     *  the five whitespace/control code points with short forms
        (U+0008,U+0009,U+000A,U+000C,U+000D) take those;
     *  every other code point below U+0020 takes the six-character
        `\u00XX` form;
     *  EVERY remaining code point — crucially including all code points at or
        above U+0080 — passes through as itself, one character.

   The last clause is the whole behaviour at issue: characters outside the
   ASCII range appear as themselves, not as `\uXXXX` sequences. -/
def jsonChar (c : Char) : List Char :=
  if c.val = 34 then ['\\', '"']
  else if c.val = 92 then ['\\', '\\']
  else if c.val = 8 then ['\\', 'b']
  else if c.val = 9 then ['\\', 't']
  else if c.val = 10 then ['\\', 'n']
  else if c.val = 12 then ['\\', 'f']
  else if c.val = 13 then ['\\', 'r']
  else if c.val < 32 then ['\\', 'u', '0', '0', hexDigit (c.val / 16), hexDigit (c.val % 16)]
  else [c]

/- The escaped body of a whole string: concatenate the per-code-point JSON
   renderings. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). -/
def jsonEscapedSeq : List Char → List Char
  | []      => []
  | c :: cs => jsonChar c ++ jsonEscapedSeq cs

@[grind] lemma jsonEscapedSeq_nil : jsonEscapedSeq [] = [] := rfl
@[grind] lemma jsonEscapedSeq_cons (c : Char) (cs : List Char) :
    jsonEscapedSeq (c :: cs) = jsonChar c ++ jsonEscapedSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a string value to its JSON text: a double quote, the per-code-point
   escaped body, and a closing double quote. The post-condition pins the body to
   `jsonEscapedSeq`, so any verifying implementation emits non-ASCII code points
   literally (the `else [c]` clause), exactly as the desired behaviour demands. -/
method serializeStringValue (text : List Char) return (out : List Char)
  ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = jsonEscapedSeq (text.drop i)
      done_with i = 0
    do
      let c := text[i - 1]!
      result := jsonChar c ++ result
      i := i - 1
    return '"' :: (result ++ ['"'])
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `jsonEscapedSeq` peels one `jsonChar`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma jsonEscapedSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    jsonEscapedSeq (text.drop (i - 1)) = jsonChar text[i - 1]! ++ jsonEscapedSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, jsonEscapedSeq_cons]

prove_correct serializeStringValue by
  loom_solve
  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

COMMANDS (verify): bash scripts/lean_verify.sh <atk>.lean ; ran concurrently in batches of <=4 as background jobs.
SAME_SPEC: all 10 files (atk_pc, atk_1..atk_6, atk_7b, atk_7c, atk_8) => same_spec=True (spec/axioms/pure/pre/post byte-identical; only impl + prove_correct body edited).

### VERIFY RESULTS (exit codes):
- atk_pc (exact copy, positive control): 0 VERIFIES.
- atk_1 PREPATCH BUG (escape v>=128 as ['\\','u'], all-ASCII mode): 1 FAILS. Rejected by goal 128<=val -> ['\\','u']=jsonChar c (non-ASCII pass-through clause). => prepatch_reproduced=True.
- atk_2 no escaping (return raw text): 1 FAILS (fails on ", \, controls).
- atk_3 drop closing quote framing: 1 FAILS.
- atk_4 control-flow-effect (append at END, reversed order): 1 FAILS.
- atk_5 boundary off-by-one (i := text.length-1, misses last char): 1 FAILS.
- atk_6 ungrounded-oracle ECHO (return the postcondition RHS verbatim): 0 VERIFIES, value-correct.
- atk_7b NON-TERMINATION (partial-domain: body no-op result:=result, diverges on non-empty input): 0 VERIFIES (vacuously partial-correct).
- atk_7c NON-TERMINATION (body i:=i, never decrements): 0 VERIFIES (vacuously partial-correct).
- atk_8 structurally-distinct CORRECT (List.foldr, inductive proof foldr==jsonEscapedSeq): 0 VERIFIES (non-vacuity witness #2).
(atk_7 = an earlier `while true` attempt that FAILED to verify on a proof-plumbing omega goal; superseded by atk_7b/7c which are the real divergence witnesses.)

### MANDATORY RESOLVE (executed, NOT speculated):
  python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-13512', open('gold_faithful.patch').read(), run_id='sbu-eq-audit-13512-goldfaithful', timeout=1200, retries=1); print(r.resolved, r.completed, r.note, r.flaky)"
  => RESOLVED=True COMPLETED=True NOTE='resolved' FLAKY=False.
The faithful refined patch of EVERY verifying impl (atk_6, atk_7b, atk_7c, atk_8) is the value-level gold patch (json.dumps(value, ensure_ascii=False, cls=...)) — refinement.md's map is a VALUE/data-refinement (the while loop is tagged I, transliterated by G-CONF's value shadow to '"'+body+'"'). That patch RESOLVES, so none of these attacks break the spec.

DIVERGENCE-ATTACK ADJUDICATION (the only verify!=correct-shaped finding, resolved as NOT a break): atk_7b/atk_7c verify solely because loom.semantics.termination "partial" never proves termination — divergence vacuously satisfies partial correctness (repeat_inv_split in Loom/MonadAlgebras/WP/Basic.lean: post = inv ⊓ doneWith at exit, no decreasing measure). This is a FRAMEWORK-WIDE property of partial semantics, not a per-bundle refinement defect: the accepted GOLD Solution.lean itself uses termination "partial" with NO termination proof (G-GOLD=pass), so if divergence were a legitimate G-EQ counterexample NO partial-semantics velvet bundle could ever be SOUND.

G-EQ/refinement fidelity is scoped to A-legs + value correspondence (per prompt); termination is out of scope by construction, and G-CONF (the R/I refuter) compares OUTPUT VALUES which for any terminating transliteration equal the gold. A divergent loop has no faithful VALUE-computing Python transliteration other than the gold value the postcondition pins; I materialized a strawman divergence-faithful patch (divergent_faithful.patch, a literal `while i>0: pass` in prepare_value) but did NOT run it — a literal infinite loop merely hits the harness wall-clock (a harness-timeout artifact), which is not evidence about spec soundness and would misrepresent the faithful-refinement contract. Recorded transparently.

REFINEMENT.MD LEG AUDIT (step 3): A1 str<->List Char (R); A2 result value = '"' :: jsonEscapedSeq text ++ ['"'] modeled DEEPLY, fold ops I + deep-model equality A-reference; A3 the else [c] non-ASCII pass-through clause A-reference+I (THE discriminating change); A4 cls/encoder omission R (identity on str carrier). NO kind-3, NO consumed axioms. A-reference correspondence VALIDATED: ran axiom_check.py => exit 0 ('json_escaped_seq deep model == json.dumps(., ensure_ascii=False) sound on 68 boundary + 20000 fuzz, diverges from ensure_ascii=True on non-ASCII'). Both gold hunks (forms/fields.py:1261, admin/utils.py:403) are the SAME behavioural fix at two call sites -> one method models both; one Solution_prepatch discriminates both (correct per refinement.md §B).

**CONCLUSION:** >=5 distinct attacks run (9 total: prepatch + partial-domain + 2 framing + boundary + control-flow-effect + echo + 2 non-termination + foldr), positive controls verify (atk_pc + atk_8), spec is value-TIGHT, A-reference sound, no verifying impl's faithful (value-level) refined patch fails to resolve (gold executed => resolved). Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_6.lean`, `atk_7b.lean`, `atk_7c.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong-VALUE impl exists. The postcondition out = '"' :: (jsonEscapedSeq text ++ ['"']) pins the output value to a concrete TOTAL recursive model (jsonChar/jsonEscapedSeq, no axioms), so every value-level wrong impl fails verification (atk_1..atk_5, exit 1). The only verifying non-reference impls are value-CORRECT (atk_6 echo, atk_8 foldr) or vacuously-partial-correct divergent loops (atk_7b/atk_7c), whose only faithful VALUE-level refined patch is the gold computation, which resolves.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_7c.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single behaviour under specification — how a string
   value is rendered to its JSON text form — is modelled DEEPLY here (the
   spelled-out `jsonChar`/`jsonEscapedSeq` fold below), validated against the
   real standard-library serializer by axiom_check.py (G-AX, A-reference). No
   unchanged callee needs a contract. -/
-- axioms-end

-- pure-start
/- One lowercase hexadecimal digit (`0`–`9`, `a`–`f`). Only ever applied to a
   value `< 16` (the nibbles of a control code point), where it is total. -/
def hexDigit (n : UInt32) : Char :=
  if n < 10 then Char.ofNat (48 + n.toNat) else Char.ofNat (87 + n.toNat)

/- The JSON text of a single code point inside a string literal, when the
   serializer is asked to keep output as the raw text rather than collapsing
   everything outside ASCII to `\uXXXX` escapes:

     *  U+0022 and U+005C take their two-character backslash form;
     *  the five whitespace/control code points with short forms
        (U+0008,U+0009,U+000A,U+000C,U+000D) take those;
     *  every other code point below U+0020 takes the six-character
        `\u00XX` form;
     *  EVERY remaining code point — crucially including all code points at or
        above U+0080 — passes through as itself, one character.

   The last clause is the whole behaviour at issue: characters outside the
   ASCII range appear as themselves, not as `\uXXXX` sequences. -/
def jsonChar (c : Char) : List Char :=
  if c.val = 34 then ['\\', '"']
  else if c.val = 92 then ['\\', '\\']
  else if c.val = 8 then ['\\', 'b']
  else if c.val = 9 then ['\\', 't']
  else if c.val = 10 then ['\\', 'n']
  else if c.val = 12 then ['\\', 'f']
  else if c.val = 13 then ['\\', 'r']
  else if c.val < 32 then ['\\', 'u', '0', '0', hexDigit (c.val / 16), hexDigit (c.val % 16)]
  else [c]

/- The escaped body of a whole string: concatenate the per-code-point JSON
   renderings. Front-recursive so a single unfold is available per loop step
   (the fold pattern, plan §5.4). -/
def jsonEscapedSeq : List Char → List Char
  | []      => []
  | c :: cs => jsonChar c ++ jsonEscapedSeq cs

@[grind] lemma jsonEscapedSeq_nil : jsonEscapedSeq [] = [] := rfl
@[grind] lemma jsonEscapedSeq_cons (c : Char) (cs : List Char) :
    jsonEscapedSeq (c :: cs) = jsonChar c ++ jsonEscapedSeq cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a string value to its JSON text: a double quote, the per-code-point
   escaped body, and a closing double quote. The post-condition pins the body to
   `jsonEscapedSeq`, so any verifying implementation emits non-ASCII code points
   literally (the `else [c]` clause), exactly as the desired behaviour demands. -/
method serializeStringValue (text : List Char) return (out : List Char)
  ensures out = '"' :: (jsonEscapedSeq text ++ ['"'])
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := text.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ text.length
      invariant result = jsonEscapedSeq (text.drop i)
      done_with i = 0
    do
      let c := text[i - 1]!
      result := jsonChar c ++ result
      i := i - 1
    return '"' :: (result ++ ['"'])
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `jsonEscapedSeq` peels one `jsonChar`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma jsonEscapedSeq_drop_step (text : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ text.length) :
    jsonEscapedSeq (text.drop (i - 1)) = jsonChar text[i - 1]! ++ jsonEscapedSeq (text.drop i) := by
  have hlt : i - 1 < text.length := by omega
  have hcons : text.drop (i - 1) = text[i - 1]! :: text.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, jsonEscapedSeq_cons]

prove_correct serializeStringValue by
  loom_solve
  rw [jsonEscapedSeq_drop_step text i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

COMMANDS (verify): bash scripts/lean_verify.sh <atk>.lean ; ran concurrently in batches of <=4 as background jobs.
SAME_SPEC: all 10 files (atk_pc, atk_1..atk_6, atk_7b, atk_7c, atk_8) => same_spec=True (spec/axioms/pure/pre/post byte-identical; only impl + prove_correct body edited).

### VERIFY RESULTS (exit codes):
- atk_pc (exact copy, positive control): 0 VERIFIES.
- atk_1 PREPATCH BUG (escape v>=128 as ['\\','u'], all-ASCII mode): 1 FAILS. Rejected by goal 128<=val -> ['\\','u']=jsonChar c (non-ASCII pass-through clause). => prepatch_reproduced=True.
- atk_2 no escaping (return raw text): 1 FAILS (fails on ", \, controls).
- atk_3 drop closing quote framing: 1 FAILS.
- atk_4 control-flow-effect (append at END, reversed order): 1 FAILS.
- atk_5 boundary off-by-one (i := text.length-1, misses last char): 1 FAILS.
- atk_6 ungrounded-oracle ECHO (return the postcondition RHS verbatim): 0 VERIFIES, value-correct.
- atk_7b NON-TERMINATION (partial-domain: body no-op result:=result, diverges on non-empty input): 0 VERIFIES (vacuously partial-correct).
- atk_7c NON-TERMINATION (body i:=i, never decrements): 0 VERIFIES (vacuously partial-correct).
- atk_8 structurally-distinct CORRECT (List.foldr, inductive proof foldr==jsonEscapedSeq): 0 VERIFIES (non-vacuity witness #2).
(atk_7 = an earlier `while true` attempt that FAILED to verify on a proof-plumbing omega goal; superseded by atk_7b/7c which are the real divergence witnesses.)

### MANDATORY RESOLVE (executed, NOT speculated):
  python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-13512', open('gold_faithful.patch').read(), run_id='sbu-eq-audit-13512-goldfaithful', timeout=1200, retries=1); print(r.resolved, r.completed, r.note, r.flaky)"
  => RESOLVED=True COMPLETED=True NOTE='resolved' FLAKY=False.
The faithful refined patch of EVERY verifying impl (atk_6, atk_7b, atk_7c, atk_8) is the value-level gold patch (json.dumps(value, ensure_ascii=False, cls=...)) — refinement.md's map is a VALUE/data-refinement (the while loop is tagged I, transliterated by G-CONF's value shadow to '"'+body+'"'). That patch RESOLVES, so none of these attacks break the spec.

DIVERGENCE-ATTACK ADJUDICATION (the only verify!=correct-shaped finding, resolved as NOT a break): atk_7b/atk_7c verify solely because loom.semantics.termination "partial" never proves termination — divergence vacuously satisfies partial correctness (repeat_inv_split in Loom/MonadAlgebras/WP/Basic.lean: post = inv ⊓ doneWith at exit, no decreasing measure). This is a FRAMEWORK-WIDE property of partial semantics, not a per-bundle refinement defect: the accepted GOLD Solution.lean itself uses termination "partial" with NO termination proof (G-GOLD=pass), so if divergence were a legitimate G-EQ counterexample NO partial-semantics velvet bundle could ever be SOUND.

G-EQ/refinement fidelity is scoped to A-legs + value correspondence (per prompt); termination is out of scope by construction, and G-CONF (the R/I refuter) compares OUTPUT VALUES which for any terminating transliteration equal the gold. A divergent loop has no faithful VALUE-computing Python transliteration other than the gold value the postcondition pins; I materialized a strawman divergence-faithful patch (divergent_faithful.patch, a literal `while i>0: pass` in prepare_value) but did NOT run it — a literal infinite loop merely hits the harness wall-clock (a harness-timeout artifact), which is not evidence about spec soundness and would misrepresent the faithful-refinement contract. Recorded transparently.

REFINEMENT.MD LEG AUDIT (step 3): A1 str<->List Char (R); A2 result value = '"' :: jsonEscapedSeq text ++ ['"'] modeled DEEPLY, fold ops I + deep-model equality A-reference; A3 the else [c] non-ASCII pass-through clause A-reference+I (THE discriminating change); A4 cls/encoder omission R (identity on str carrier). NO kind-3, NO consumed axioms. A-reference correspondence VALIDATED: ran axiom_check.py => exit 0 ('json_escaped_seq deep model == json.dumps(., ensure_ascii=False) sound on 68 boundary + 20000 fuzz, diverges from ensure_ascii=True on non-ASCII'). Both gold hunks (forms/fields.py:1261, admin/utils.py:403) are the SAME behavioural fix at two call sites -> one method models both; one Solution_prepatch discriminates both (correct per refinement.md §B).

**CONCLUSION:** >=5 distinct attacks run (9 total: prepatch + partial-domain + 2 framing + boundary + control-flow-effect + echo + 2 non-termination + foldr), positive controls verify (atk_pc + atk_8), spec is value-TIGHT, A-reference sound, no verifying impl's faithful (value-level) refined patch fails to resolve (gold executed => resolved). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) audit for django__django-13512 velvet. Spec: serializeStringValue text = '"' :: (jsonEscapedSeq text ++ ['"']), modeling json.dumps(s, ensure_ascii=False) for a str leaf (the gold patch behavior). 

Evidence the modeled function does NOT drift from the real callee: (1) Exhaustive single-code-point comparison of the transliterated model vs REAL json.dumps(c, ensure_ascii=False) over EVERY Unicode scalar value (0x0..0xD7FF, 0xE000..0x10FFFF) => 0 mismatches; because JSON string encoding is per-code-point composition with fixed quote framing, per-char agreement lifts to all strings. (2) Surrogate code points 0xD800..0xDFFF also match (outside Lean Char domain but tested defensively). (3) Escape set is exactly CPython's py_encode_basestring: 0x22/0x5c -> two-char; 0x08/09/0a/0c/0d short forms; other <0x20 -> lowercase \u00xx; U+002F not escaped; all >=0x20 (incl. all >=0x80) pass through literally. (4) Recorded G-CONF passed on 100071 inputs (seed 13512) against the real patched JSONField.prepare_value oracle in-container, 0 disagreements; G-AX passed on 68 boundary + 20000 fuzz. (5) Non-vacuity: model diverges from ensure_ascii=True on non-ASCII, so it is pinned to the patched behavior, and G-DIFF's Solution_prepatch.lean fails as required. (6) Solution.lean re-verified locally via lean_verify.sh (exit 0). 

The spec is neither too strong nor too weak: it reproduces the real callee bit-for-bit across its entire str input domain. The documented scope restriction to string leaves is sound (ensure_ascii only affects string-leaf escaping; container framing is refinement-invariant and separately confirmed by G-CONF). No diverging input found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage/gold-reconstruction judgment for velvet bundle django__django-13512.

**Gold edit:** add `ensure_ascii=False` to json.dumps at django/forms/fields.py:1261 and django/contrib/admin/utils.py:403 so non-ASCII code points render literally instead of \uXXXX escapes.

Spec-region integrity: same_spec(Solution.lean, Solution_prepatch.lean)=True — spec regions (axioms/pure/pre/post + signature/ensures) are byte-identical; only the elided impl/proof regions differ. The prepatch's differing behavior lives entirely inside the hidden impl (the jsonChar >=128 arm), so the consumer spec view cannot distinguish patched vs prepatch.

Token scan of the generated spec view (markers.spec_view): none of ensure_ascii, json.dumps, prepare_value, get_prep_value, fields.py, utils.py, encoder, 1261, 403 appear. No gold-patch specifics (flag name, call sites, file/line) are present.

Beyond-problem_statement test: the public problem_statement itself fully discloses the discriminating behavior — it shows json.dumps('中国') -> "中国", states json.dumps uses ASCII by default, and complains that non-ASCII renders as ASCII escapes. The spec's post-condition and the jsonChar `else [c]` pass-through clause encode exactly that publicly-known desired behavior (code points >= U+0080 pass through literally). The surrounding JSON-escape table (quote/backslash/short forms, \u00XX for <0x20) is standard JSON encoding, not gold-specific. Nothing in the spec view reveals the fix's mechanism (the ensure_ascii flag or the two call sites) beyond what the problem statement already states.

Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md). Mechanical leakage.screen passes clean (no hard_failures). A spec that pins publicly-described correct behavior is not leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.