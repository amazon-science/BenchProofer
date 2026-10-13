# P2 adversarial audit — psf__requests-6028

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_nosep.lean`, `atk2_invguard.lean`, `atk3_ignorefb.lean`, `atk4_doubleat.lean`, `atk7_wrongbase.lean`, `atk8_drophost.lean`, `atk9_swapbranch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk5_echo.lean`, `atk6b_equiv.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_nosep.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
       if authoritySlot = [] then fallbackSlot else authoritySlot
     let out : List Char :=
       if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
+      else userinfo ++ base
     return out
     -- impl-end
 
```

Attack 2 — `atk2_invguard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,8 @@
     let base : List Char :=
       if authoritySlot = [] then fallbackSlot else authoritySlot
     let out : List Char :=
-      if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
+      if userinfo = [] then userinfo ++ ['@'] ++ base
+      else base
     return out
     -- impl-end
 
```

Attack 3 — `atk3_ignorefb.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,8 +70,7 @@
   ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
   do
     -- impl-start
-    let base : List Char :=
-      if authoritySlot = [] then fallbackSlot else authoritySlot
+    let base : List Char := authoritySlot
     let out : List Char :=
       if userinfo = [] then base
       else userinfo ++ ['@'] ++ base
```

Attack 4 — `atk4_doubleat.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
       if authoritySlot = [] then fallbackSlot else authoritySlot
     let out : List Char :=
       if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
+      else userinfo ++ ['@', '@'] ++ base
     return out
     -- impl-end
 
```

Attack 5 — `atk7_wrongbase.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,8 +70,7 @@
   ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
   do
     -- impl-start
-    let base : List Char :=
-      if authoritySlot = [] then fallbackSlot else authoritySlot
+    let base : List Char := fallbackSlot
     let out : List Char :=
       if userinfo = [] then base
       else userinfo ++ ['@'] ++ base
```

Attack 6 — `atk8_drophost.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,7 +74,7 @@
       if authoritySlot = [] then fallbackSlot else authoritySlot
     let out : List Char :=
       if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
+      else userinfo ++ ['@']
     return out
     -- impl-end
 
```

Attack 7 — `atk9_swapbranch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,8 +73,8 @@
     let base : List Char :=
       if authoritySlot = [] then fallbackSlot else authoritySlot
     let out : List Char :=
-      if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
+      if userinfo = [] then base ++ userinfo
+      else base
     return out
     -- impl-end
 
```

Attack 8 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,12 +70,7 @@
   ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
   do
     -- impl-start
-    let base : List Char :=
-      if authoritySlot = [] then fallbackSlot else authoritySlot
-    let out : List Char :=
-      if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
-    return out
+    return assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
     -- impl-end
 
 prove_correct buildAuthority by
```

Attack 9 — `atk6b_equiv.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -70,12 +70,11 @@
   ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
   do
     -- impl-start
-    let base : List Char :=
-      if authoritySlot = [] then fallbackSlot else authoritySlot
-    let out : List Char :=
-      if userinfo = [] then base
-      else userinfo ++ ['@'] ++ base
-    return out
+    let base : List Char := authorityBase authoritySlot fallbackSlot
+    if userinfo ≠ [] then
+      return userinfo ++ ['@'] ++ base
+    else
+      return base
     -- impl-end
 
 prove_correct buildAuthority by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The authority component is built entirely from the
--  parsed pieces — a pure string computation modeled in full below; nothing is
--  delegated to an unchanged callee. The upstream URL splitter that produces
--  those pieces, and the downstream re-assembler that consumes the result, are
--  exercised end-to-end by the differential conformance check, not axiomatized.)
-- axioms-end

-- pure-start
/- Assemble the authority section of a URL from the pieces a parser hands back.

   A URL's authority is the part between the scheme's `//` and the path
   (`userinfo@host:port`). Two pieces are relevant here:

   * `userinfo` — the optional credentials (user, or user:password) that precede
     an `@` in the authority. Empty when the URL carries no credentials.
   * `base` — the host(:port) portion of the authority. The caller has already
     resolved which parsed slot actually holds it (`fallback` below), since a
     known parser quirk can leave the authority slot empty and stash the value
     in the path slot instead; that resolution is a separate concern reproduced
     verbatim here so the assembly sees the right value.

   The assembled authority must carry the credentials whenever they are present:
   the userinfo, an `@`, then the host portion. With no credentials the host
   portion stands alone. This guarantees that a round-trip through a parser that
   exposes credentials separately does not silently discard them. -/
def assembleAuthority (userinfo base : List Char) : List Char :=
  if userinfo = [] then base
  else userinfo ++ ['@'] ++ base

/- Resolve which parsed slot holds the host portion: normally the authority
   slot, but if a parser left it empty the value lives in the path slot. -/
def authorityBase (authoritySlot fallbackSlot : List Char) : List Char :=
  if authoritySlot = [] then fallbackSlot else authoritySlot

/- Single-step unfolds so `loom_solve` discharges the postconditions. -/
@[grind] lemma assembleAuthority_def (userinfo base : List Char) :
    assembleAuthority userinfo base =
      (if userinfo = [] then base else userinfo ++ ['@'] ++ base) := rfl

@[grind] lemma authorityBase_def (authoritySlot fallbackSlot : List Char) :
    authorityBase authoritySlot fallbackSlot =
      (if authoritySlot = [] then fallbackSlot else authoritySlot) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the authority section of a URL from the slots a parser produced:
   `userinfo` (optional credentials), and the two slots `authoritySlot`/`fallbackSlot`
   among which the host portion may have landed. The result is the authority the
   URL should be re-assembled with. When credentials are present they are kept,
   joined to the host portion by an `@`; when absent the host portion stands
   alone. All three inputs are read-only (none declared `mut`); the builder only
   reads them (directive 5) and returns a fresh authority string. -/
method buildAuthority
    (userinfo : List Char) (authoritySlot : List Char) (fallbackSlot : List Char)
    return (out : List Char)
  ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
  do
    -- impl-start
    let base : List Char :=
      if authoritySlot = [] then fallbackSlot else authoritySlot
    let out : List Char :=
      if userinfo = [] then base
      else userinfo ++ ['@'] ++ base
    return out
    -- impl-end

prove_correct buildAuthority by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: buildAuthority's ensures is a TOTAL POINTWISE FUNCTIONAL EQUALITY: `out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)`, where assembleAuthority/authorityBase are fully spelled-out pure deep models (no partiality, no free vars). This uniquely pins `out` for EVERY input, so any verifying impl is extensionally equal to the gold authority-fold on all inputs. There are NO axioms/deep_model_references (meta.json axioms=[], deep_model_references=[]; G-AX=skip), so the A-legs reduce to the deep-model correspondence, which I audited: assembleAuthority == post-patch `netloc='@'.join([auth,netloc])` when auth truthy else identity (refinement.md A5-A7, mapping.md §2 join↔++['@']++); authorityBase == the verbatim `if not netloc: netloc,path = path,netloc` swap (A4). refinement.md legs are all R or I; §C explicitly documents no kind-3 op (the changed op is modeled deeply, not hidden behind an axiom). Correspondence holds.

SAME-SPEC: all 11 files (9 attacks + pos_control + prepatch) confirmed same_spec=True via swebench_unified.markers.same_spec (velvet language table). Each built by editing ONLY the impl region of the frozen Solution.lean.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently in batches of 4):
  pos_control.lean       -> exit 0 (verifies)  [correct gold impl]
  atk_prepatch.lean      -> exit 1 (rejected)  [prepatch bug: out=base, credentials dropped; genuine `unsolved goals` at prove_correct]
  atk1_nosep.lean        -> exit 1 (rejected, unsolved goals) [dropped '@' separator]
  atk2_invguard.lean     -> exit 1 (rejected, unsolved goals) [inverted userinfo guard]
  atk3_ignorefb.lean     -> exit 1 (rejected, unsolved goals) [ignores fallbackSlot; partial-domain]
  atk4_doubleat.lean     -> exit 1 (rejected, unsolved goals) [double '@','@' separator; boundary]
  atk7_wrongbase.lean    -> exit 1 (rejected, unsolved goals) [base:=fallbackSlot always; ungrounded]
  atk8_drophost.lean     -> exit 1 (rejected, unsolved goals) [drops host after '@'; control-flow-effect]
  atk9_swapbranch.lean   -> exit 1 (rejected, unsolved goals) [swapped branch results]
  atk6_equiv.lean        -> exit 1 (PARSE error on dependent-if `if h :`; NOT a valid spec attack, discarded — Velvet WPGen can't parse it)
  atk5_echo.lean         -> exit 0 (VERIFIES) [ungrounded-oracle echo: literally returns assembleAuthority userinfo (authorityBase ...)]
  atk6b_equiv.lean       -> exit 0 (VERIFIES) [behaviorally-gold-equivalent: negated non-dependent guard, `if userinfo ≠ [] then userinfo++['@']++base else base`]
All 8 behaviorally-wrong impls fail with genuine `error: unsolved goals` at the prove_correct/loom_solve line (81/83:29), i.e. real postcondition rejection, NOT syntax artifacts — the spec is genuinely tight.

RESOLVE (protocol step 2): both verifying impls (atk5_echo, atk6b_equiv) are extensionally equal to the gold authority-fold, so their faithful refined patch IS the gold hunk `if auth: netloc='@'.join([auth,netloc])`. Materialized as faithful_patch.diff and RUN through the official harness: run_resolve('psf__requests-6028', patch, timeout=1200, retries=0) => RESOLVED=True, COMPLETED=True. Both F2P tests pass (test_prepend_scheme_if_needed[http://user:pass@...] and [http://user@...]) plus all PASS_TO_PASS, 0 failures. So every verifying wrong impl's faithful patch RESOLVES — verify⇒correct holds here.

CONCLUSION: No verifying same-spec impl whose faithful patch fails to resolve was found. The prepatch bug is reproduced and rejected. The spec (a total functional equality with faithful deep models and no axioms) admits only gold-equivalent implementations. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_nosep.lean`, `atk2_invguard.lean`, `atk3_ignorefb.lean`, `atk4_doubleat.lean`, `atk7_wrongbase.lean`, `atk8_drophost.lean`, `atk9_swapbranch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk5_echo.lean`, `atk6b_equiv.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_nosep.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_invguard.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_ignorefb.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_doubleat.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk7_wrongbase.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk8_drophost.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk9_swapbranch.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk6b_equiv.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The authority component is built entirely from the
--  parsed pieces — a pure string computation modeled in full below; nothing is
--  delegated to an unchanged callee. The upstream URL splitter that produces
--  those pieces, and the downstream re-assembler that consumes the result, are
--  exercised end-to-end by the differential conformance check, not axiomatized.)
-- axioms-end

-- pure-start
/- Assemble the authority section of a URL from the pieces a parser hands back.

   A URL's authority is the part between the scheme's `//` and the path
   (`userinfo@host:port`). Two pieces are relevant here:

   * `userinfo` — the optional credentials (user, or user:password) that precede
     an `@` in the authority. Empty when the URL carries no credentials.
   * `base` — the host(:port) portion of the authority. The caller has already
     resolved which parsed slot actually holds it (`fallback` below), since a
     known parser quirk can leave the authority slot empty and stash the value
     in the path slot instead; that resolution is a separate concern reproduced
     verbatim here so the assembly sees the right value.

   The assembled authority must carry the credentials whenever they are present:
   the userinfo, an `@`, then the host portion. With no credentials the host
   portion stands alone. This guarantees that a round-trip through a parser that
   exposes credentials separately does not silently discard them. -/
def assembleAuthority (userinfo base : List Char) : List Char :=
  if userinfo = [] then base
  else userinfo ++ ['@'] ++ base

/- Resolve which parsed slot holds the host portion: normally the authority
   slot, but if a parser left it empty the value lives in the path slot. -/
def authorityBase (authoritySlot fallbackSlot : List Char) : List Char :=
  if authoritySlot = [] then fallbackSlot else authoritySlot

/- Single-step unfolds so `loom_solve` discharges the postconditions. -/
@[grind] lemma assembleAuthority_def (userinfo base : List Char) :
    assembleAuthority userinfo base =
      (if userinfo = [] then base else userinfo ++ ['@'] ++ base) := rfl

@[grind] lemma authorityBase_def (authoritySlot fallbackSlot : List Char) :
    authorityBase authoritySlot fallbackSlot =
      (if authoritySlot = [] then fallbackSlot else authoritySlot) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the authority section of a URL from the slots a parser produced:
   `userinfo` (optional credentials), and the two slots `authoritySlot`/`fallbackSlot`
   among which the host portion may have landed. The result is the authority the
   URL should be re-assembled with. When credentials are present they are kept,
   joined to the host portion by an `@`; when absent the host portion stands
   alone. All three inputs are read-only (none declared `mut`); the builder only
   reads them (directive 5) and returns a fresh authority string. -/
method buildAuthority
    (userinfo : List Char) (authoritySlot : List Char) (fallbackSlot : List Char)
    return (out : List Char)
  ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)
  do
    -- impl-start
    let base : List Char :=
      if authoritySlot = [] then fallbackSlot else authoritySlot
    let out : List Char :=
      if userinfo = [] then base
      else userinfo ++ ['@'] ++ base
    return out
    -- impl-end

prove_correct buildAuthority by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: buildAuthority's ensures is a TOTAL POINTWISE FUNCTIONAL EQUALITY: `out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)`, where assembleAuthority/authorityBase are fully spelled-out pure deep models (no partiality, no free vars). This uniquely pins `out` for EVERY input, so any verifying impl is extensionally equal to the gold authority-fold on all inputs. There are NO axioms/deep_model_references (meta.json axioms=[], deep_model_references=[]; G-AX=skip), so the A-legs reduce to the deep-model correspondence, which I audited: assembleAuthority == post-patch `netloc='@'.join([auth,netloc])` when auth truthy else identity (refinement.md A5-A7, mapping.md §2 join↔++['@']++); authorityBase == the verbatim `if not netloc: netloc,path = path,netloc` swap (A4). refinement.md legs are all R or I; §C explicitly documents no kind-3 op (the changed op is modeled deeply, not hidden behind an axiom). Correspondence holds.

SAME-SPEC: all 11 files (9 attacks + pos_control + prepatch) confirmed same_spec=True via swebench_unified.markers.same_spec (velvet language table). Each built by editing ONLY the impl region of the frozen Solution.lean.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>, run concurrently in batches of 4):
  pos_control.lean       -> exit 0 (verifies)  [correct gold impl]
  atk_prepatch.lean      -> exit 1 (rejected)  [prepatch bug: out=base, credentials dropped; genuine `unsolved goals` at prove_correct]
  atk1_nosep.lean        -> exit 1 (rejected, unsolved goals) [dropped '@' separator]
  atk2_invguard.lean     -> exit 1 (rejected, unsolved goals) [inverted userinfo guard]
  atk3_ignorefb.lean     -> exit 1 (rejected, unsolved goals) [ignores fallbackSlot; partial-domain]
  atk4_doubleat.lean     -> exit 1 (rejected, unsolved goals) [double '@','@' separator; boundary]
  atk7_wrongbase.lean    -> exit 1 (rejected, unsolved goals) [base:=fallbackSlot always; ungrounded]
  atk8_drophost.lean     -> exit 1 (rejected, unsolved goals) [drops host after '@'; control-flow-effect]
  atk9_swapbranch.lean   -> exit 1 (rejected, unsolved goals) [swapped branch results]
  atk6_equiv.lean        -> exit 1 (PARSE error on dependent-if `if h :`; NOT a valid spec attack, discarded — Velvet WPGen can't parse it)
  atk5_echo.lean         -> exit 0 (VERIFIES) [ungrounded-oracle echo: literally returns assembleAuthority userinfo (authorityBase ...)]
  atk6b_equiv.lean       -> exit 0 (VERIFIES) [behaviorally-gold-equivalent: negated non-dependent guard, `if userinfo ≠ [] then userinfo++['@']++base else base`]
All 8 behaviorally-wrong impls fail with genuine `error: unsolved goals` at the prove_correct/loom_solve line (81/83:29), i.e. real postcondition rejection, NOT syntax artifacts — the spec is genuinely tight.

RESOLVE (protocol step 2): both verifying impls (atk5_echo, atk6b_equiv) are extensionally equal to the gold authority-fold, so their faithful refined patch IS the gold hunk `if auth: netloc='@'.join([auth,netloc])`. Materialized as faithful_patch.diff and RUN through the official harness: run_resolve('psf__requests-6028', patch, timeout=1200, retries=0) => RESOLVED=True, COMPLETED=True. Both F2P tests pass (test_prepend_scheme_if_needed[http://user:pass@...] and [http://user@...]) plus all PASS_TO_PASS, 0 failures. So every verifying wrong impl's faithful patch RESOLVES — verify⇒correct holds here.

CONCLUSION: No verifying same-spec impl whose faithful patch fails to resolve was found. The prepatch bug is reproduced and rejected. The spec (a total functional equality with faithful deep models and no axioms) admits only gold-equivalent implementations. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/too-strong) check for the modeled slice `netloc` in prepend_scheme_if_needed (requests/utils.py). Spec model: buildAuthority ensures out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot) = (if userinfo=[] then base else userinfo ++ ['@'] ++ base) where base = (if authoritySlot=[] then fallbackSlot else authoritySlot). Real (gold-patched) callee: netloc=parsed.netloc; if not netloc: netloc,path = path,netloc; if auth: netloc='@'.join([auth,netloc]).

Method: ran the REAL parse_url + patched logic in the base worktree (v2.27.0) and compared against a faithful Python transliteration of the Lean model. Curated cases + two fuzz campaigns (300k random URLs, seeds 12345 and 999; schemes ''/http://///ftp://https://mailto:, alphabet incl @,:,/,.,%,-,_ , spaces, brackets). Under the documented type bridge (auth/netloc/path Optional[str] with None and '' both mapping to the empty List Char [] — mapping.md §2/§3.1), there were ZERO divergences on every input where the real function returns normally (117k+ / 300k normal returns matched exactly; the rest raise inside parse_url and are out of scope).

The sole model-vs-real mismatch found ('http://user@': parse_url gives auth='user', netloc='', path=None, the swap makes netloc=None, and '@'.join(['user',None]) raises TypeError) is a case where the REAL function RAISES, i.e. intrinsic partiality of the gold fix. mapping.md §3.1 documents this and G-CONF only compares on inputs where the oracle returns normally, so the model is held to the same domain. This is not a spec-strength defect and yields no diverging_input where real returns normally but disagrees.

Bridge equivalence confirmed: urlunparse does not distinguish netloc None vs '' (both produce 'http:///p'), so the None/''↔[] collapse is observationally sound for the modeled value.

Ancillary checks: Solution.lean elaborates clean (lean_verify exit 0); Solution_prepatch.lean fails precisely on the userinfo≠[] leg (unsolved goal at ensures), confirming the discriminating credentials-preservation behavior; spec regions of Solution.lean and Solution_prepatch.lean are byte-identical (impl region excised). No divergence establishes the spec is neither too strong nor drifting from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the solver-visible spec view (Solution.lean projected via markers.spec_view for the velvet/lean flavor) against the PUBLIC problem_statement only (the vague 'proxy authentication bug / 407' report), excluding hints_text (which contains the real diagnosis: netloc/auth/'@'.join/prepend_scheme_if_needed).

Mechanical G-LEAK screen: PASS (rep.passed=True, no hard failures). Confirmed independently:
- No diff markers, no patched file path 'requests/utils.py', no patched module path in view.
- Gold-patch changed lines ('if auth:', "netloc = '@'.join([auth, netloc])", the two gold comments) are NOT reproduced: the spec expresses the join abstractly as `userinfo ++ ['@'] ++ base` under an `if userinfo = []` guard — no verbatim overlap.
- Distinctive patched symbol {prepend_scheme_if_needed} does not appear in any spec-view identifier or comment. Model identifiers are fully abstracted (buildAuthority, userinfo, authoritySlot, fallbackSlot, assembleAuthority, authorityBase) — none echo repo symbols netloc/auth/parse_url/urlunparse/prepend_scheme_if_needed.
- No narration terms (bug/fix/patch/regression/etc.) in comments; comments describe abstract URL-authority assembly behavior generically.

Semantic judgment: a spec necessarily pins correct behavior (credentials preserved via userinfo+@+host); that is inherent to any faithful spec and is NOT leakage of the *edit*. The view does not localize the edit to a file/function/line, does not name the parser or re-assembler, and does not disclose anything from problem_statement's absent detail beyond what a spec must state. The gold-hunk quotations and file paths that DO appear in refinement.md/mapping.md are auditor-facing derivation artifacts, not part of the screened spec view.

Cross-checks: same_spec(prepatch, postpatch)=True (byte-identical spec region — the fix is not encoded into the contract differently pre/post; the prepatch impl merely fails to satisfy the identical ensures clause). This is a genuine no-axiom pure bundle.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.