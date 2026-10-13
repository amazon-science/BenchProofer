# P2 adversarial audit — django__django-10097

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_urlUserinfoValid s result := (result = urlUserinfoValid s) is exact pointwise functional equality against a fully computable oracle. No same-spec wrong impl could close its proof; therefore no closes-but-does-not-resolve counterexample exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,9 +77,7 @@
 -- impl-start
 def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
   if s.isEmpty then return false
-  if s.head? == some ':' then return false
-  if !Nat.ble (s.count ':') 1 then return false
-  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
+  if !(s.all (fun c => !isUserinfoWhitespace c)) then return false
   return true
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,6 @@
 -- impl-start
 def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
   if s.isEmpty then return false
-  if s.head? == some ':' then return false
   if !Nat.ble (s.count ':') 1 then return false
   if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
   return true
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,6 @@
 def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
   if s.isEmpty then return false
   if s.head? == some ':' then return false
-  if !Nat.ble (s.count ':') 1 then return false
   if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
   return true
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,12 +75,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
-  if s.isEmpty then return false
-  if s.head? == some ':' then return false
-  if !Nat.ble (s.count ':') 1 then return false
-  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
-  return true
+def implementation_urlUserinfoValid (s : List Char) : Bool := true
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,6 @@
 
 -- impl-start
 def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
-  if s.isEmpty then return false
   if s.head? == some ':' then return false
   if !Nat.ble (s.count ':') 1 then return false
   if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
 def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
   if s.isEmpty then return false
   if s.head? == some ':' then return false
-  if !Nat.ble (s.count ':') 1 then return false
+  if !Nat.ble (s.count ':') 2 then return false
   if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
   return true
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   if s.isEmpty then return false
   if s.head? == some ':' then return false
   if !Nat.ble (s.count ':') 1 then return false
-  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
+  if !(s.all (fun c => isUserinfoChar c || c == ':' || c == '/')) then return false
   return true
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether the credentials portion of a URL — the `user` or
`user:password` segment that precedes the `@` in an authority — is well-formed.

A URL authority may optionally carry credentials. When present, that segment is
made of a *user* part and an optional *password* part separated by a single
colon. RFC 1738 §3.1 requires that, within these two parts, the delimiter
characters (`":"`, `"@"`, `"/"`) and whitespace never appear literally; they
must be percent-encoded to be carried. Hence the only characters admissible in
the user and password parts are those that are neither whitespace nor one of
those delimiters.

A credentials segment is therefore acceptable exactly when:

* it is non-empty;
* it does not begin with a colon (the user part must be present);
* it contains at most one colon (the single `user`/`password` separator);
* every remaining character is one of the admissible characters described above.

A single embedded colon acts purely as the user/password separator; the password
part it introduces may be empty. Any occurrence of whitespace, `"@"`, `"/"`, or a
second colon makes the segment inadmissible.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The character
-- admissibility test and the single-separator structure are modeled DEEPLY over
-- the observable input (the list of characters of the credentials segment), so
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A character admissible inside the user or password part of a URL's
credentials: neither whitespace nor one of the reserved delimiters `:`, `@`, `/`.

Whitespace here means exactly the 29 code points matched by Python's `re` `\s`
class over Unicode `str` input (the validator receives arbitrary Unicode text):
the ASCII whitespace `\t` `\n` `\v` `\f` `\r` and space, the information
separators U+001C–U+001F, NEL (U+0085), NBSP (U+00A0), OGHAM SPACE MARK
(U+1680), the fixed-width spaces U+2000–U+200A, LINE/PARAGRAPH SEPARATOR
(U+2028/U+2029), NARROW NBSP (U+202F), MEDIUM MATHEMATICAL SPACE (U+205F) and
IDEOGRAPHIC SPACE (U+3000). Lean's `Char.isWhitespace` covers only four of
these, so the class is spelled out by code point to stay faithful to
`[^\s:@/]`. -/
def isUserinfoWhitespace (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || n == 0x20 || (0x1c ≤ n && n ≤ 0x1f) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029 ||
  n == 0x202f || n == 0x205f || n == 0x3000

def isUserinfoChar (c : Char) : Bool :=
  !isUserinfoWhitespace c && c != ':' && c != '@' && c != '/'

/-- Whether the credentials segment `s` (the characters before the authority's
`@`, with the `@` itself excluded) is well-formed: non-empty, not starting with
a colon, carrying at most one colon separator, and otherwise built only from
admissible characters. -/
def urlUserinfoValid (s : List Char) : Bool :=
  if s.isEmpty then false
  else if s.head? == some ':' then false
  else if !Nat.ble (s.count ':') 1 then false
  else if !(s.all (fun c => isUserinfoChar c || c == ':')) then false
  else true
-- pure-end

-- post-conditions-start
/-- The decision returned for a credentials segment is exactly the well-formedness
verdict dictated by the rule above. -/
def problem_spec_urlUserinfoValid (s : List Char) (result : Bool) : Prop :=
  result = urlUserinfoValid s
-- post-conditions-end

-- impl-start
def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
  if s.isEmpty then return false
  if s.head? == some ':' then return false
  if !Nat.ble (s.count ':') 1 then return false
  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
  return true
-- impl-end

-- proof-start
theorem correct_urlUserinfoValid :
    ∀ (s : List Char),
      problem_spec_urlUserinfoValid s (implementation_urlUserinfoValid s) := by
  intro s
  unfold problem_spec_urlUserinfoValid implementation_urlUserinfoValid urlUserinfoValid
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** exact functional equality result = urlUserinfoValid s over a total computable oracle. Verify <=> impl extensionally equals oracle, so a closing clean-axiom proof forces the impl to agree with the oracle on ALL inputs.

**POSITIVE CONTROL:** pos_control.lean (committed impl) verifies -> `bash scripts/lean_verify.sh pos_control.lean` exit 0. Axioms clean: appended `#print axioms correct_urlUserinfoValid` -> depends on axioms: [propext] (no sorryAx/Classical/Quot).

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec against Solution.lean; impl-region-only edits; all FAIL to verify, genuine proof failures):
- atk_1 prepatch bug (\S+ model, delimiters admitted): exit 1, atk_1.lean:87:77 unsolved goals
- atk_2 drop leading-colon check (accepts ':pass'): exit 1, unsolved goals
- atk_3 drop colon-count check (accepts 'a:b:c'): exit 1, unsolved goals
- atk_4 ungrounded oracle echo `:= true`: exit 1, simp made no progress
- atk_5 drop empty check (partial-domain, accepts ''): exit 1
- atk_6 off-by-one boundary (allow <=2 colons): exit 1, unsolved goals
- atk_7 wrong char class (allow '/'): exit 1, unsolved goals
Commands: `bash scripts/lean_verify.sh atk_N.lean`; run concurrently in two batches of 4/3.

**RESOLVE STEP:** step-2 (materialize faithful patch + run_resolve) has NO applicable candidates because ZERO wrong impls closed a clean-axiom proof. patches={}.

MODEL<->PATCH CORRESPONDENCE (the only non-R/I-mechanical check here): urlUserinfoValid is faithful to gold inner-group regex `[^\s:@/]+(?::[^\s:@/]*)?`. Independent Python differential (NOT the bundle's conformance_check.py): 0 mismatches over exhaustive strings len<=3 (delimiters/ws/astral alphabet) + 200000 random fuzz over full non-surrogate code-point range. isUserinfoWhitespace == Python re \s EXACTLY: both 29 code points, symmetric difference empty over 0x0-0x10FFFF (Python 3.12).

**REFINEMENT.MD AUDIT:** 6 legs, all tagged R or I. NO A-consumed, NO A-reference, NO kind-3 legs. axiom_check.py is a justified skip (no consumed callee axiom; deep model). The A-leg attack surface this reviewer targets is empty by construction; the sole deep-model correspondence (model<->regex) is verified faithful above. Surrogate domain caveat (U+D800-DFFF) is honest and unreachable on both Lean Char and Python str.

**PREPATCH REPRODUCED:** Solution_prepatch.lean same_spec=True, fails to verify (rfl failed) -> G-DIFF live.

**VERDICT:** SOUND. >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-char-class, off-by-one, prepatch) all fail to verify; positive control verifies with clean axioms; model faithful to gold regex over full code-point space; no closes-but-does-not-resolve gap possible.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_urlUserinfoValid s result := (result = urlUserinfoValid s) is exact pointwise functional equality against a fully computable oracle. No same-spec wrong impl could close its proof; therefore no closes-but-does-not-resolve counterexample exists.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether the credentials portion of a URL — the `user` or
`user:password` segment that precedes the `@` in an authority — is well-formed.

A URL authority may optionally carry credentials. When present, that segment is
made of a *user* part and an optional *password* part separated by a single
colon. RFC 1738 §3.1 requires that, within these two parts, the delimiter
characters (`":"`, `"@"`, `"/"`) and whitespace never appear literally; they
must be percent-encoded to be carried. Hence the only characters admissible in
the user and password parts are those that are neither whitespace nor one of
those delimiters.

A credentials segment is therefore acceptable exactly when:

* it is non-empty;
* it does not begin with a colon (the user part must be present);
* it contains at most one colon (the single `user`/`password` separator);
* every remaining character is one of the admissible characters described above.

A single embedded colon acts purely as the user/password separator; the password
part it introduces may be empty. Any occurrence of whitespace, `"@"`, `"/"`, or a
second colon makes the segment inadmissible.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The character
-- admissibility test and the single-separator structure are modeled DEEPLY over
-- the observable input (the list of characters of the credentials segment), so
-- no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A character admissible inside the user or password part of a URL's
credentials: neither whitespace nor one of the reserved delimiters `:`, `@`, `/`.

Whitespace here means exactly the 29 code points matched by Python's `re` `\s`
class over Unicode `str` input (the validator receives arbitrary Unicode text):
the ASCII whitespace `\t` `\n` `\v` `\f` `\r` and space, the information
separators U+001C–U+001F, NEL (U+0085), NBSP (U+00A0), OGHAM SPACE MARK
(U+1680), the fixed-width spaces U+2000–U+200A, LINE/PARAGRAPH SEPARATOR
(U+2028/U+2029), NARROW NBSP (U+202F), MEDIUM MATHEMATICAL SPACE (U+205F) and
IDEOGRAPHIC SPACE (U+3000). Lean's `Char.isWhitespace` covers only four of
these, so the class is spelled out by code point to stay faithful to
`[^\s:@/]`. -/
def isUserinfoWhitespace (c : Char) : Bool :=
  let n := c.toNat
  (0x9 ≤ n && n ≤ 0xd) || n == 0x20 || (0x1c ≤ n && n ≤ 0x1f) ||
  n == 0x85 || n == 0xa0 || n == 0x1680 ||
  (0x2000 ≤ n && n ≤ 0x200a) || n == 0x2028 || n == 0x2029 ||
  n == 0x202f || n == 0x205f || n == 0x3000

def isUserinfoChar (c : Char) : Bool :=
  !isUserinfoWhitespace c && c != ':' && c != '@' && c != '/'

/-- Whether the credentials segment `s` (the characters before the authority's
`@`, with the `@` itself excluded) is well-formed: non-empty, not starting with
a colon, carrying at most one colon separator, and otherwise built only from
admissible characters. -/
def urlUserinfoValid (s : List Char) : Bool :=
  if s.isEmpty then false
  else if s.head? == some ':' then false
  else if !Nat.ble (s.count ':') 1 then false
  else if !(s.all (fun c => isUserinfoChar c || c == ':')) then false
  else true
-- pure-end

-- post-conditions-start
/-- The decision returned for a credentials segment is exactly the well-formedness
verdict dictated by the rule above. -/
def problem_spec_urlUserinfoValid (s : List Char) (result : Bool) : Prop :=
  result = urlUserinfoValid s
-- post-conditions-end

-- impl-start
def implementation_urlUserinfoValid (s : List Char) : Bool := Id.run do
  if s.isEmpty then return false
  if s.head? == some ':' then return false
  if !Nat.ble (s.count ':') 1 then return false
  if !(s.all (fun c => isUserinfoChar c || c == ':')) then return false
  return true
-- impl-end

-- proof-start
theorem correct_urlUserinfoValid :
    ∀ (s : List Char),
      problem_spec_urlUserinfoValid s (implementation_urlUserinfoValid s) := by
  intro s
  unfold problem_spec_urlUserinfoValid implementation_urlUserinfoValid urlUserinfoValid
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** exact functional equality result = urlUserinfoValid s over a total computable oracle. Verify <=> impl extensionally equals oracle, so a closing clean-axiom proof forces the impl to agree with the oracle on ALL inputs.

**POSITIVE CONTROL:** pos_control.lean (committed impl) verifies -> `bash scripts/lean_verify.sh pos_control.lean` exit 0. Axioms clean: appended `#print axioms correct_urlUserinfoValid` -> depends on axioms: [propext] (no sorryAx/Classical/Quot).

ATTACKS (all same_spec=True via swebench_unified.markers.same_spec against Solution.lean; impl-region-only edits; all FAIL to verify, genuine proof failures):
- atk_1 prepatch bug (\S+ model, delimiters admitted): exit 1, atk_1.lean:87:77 unsolved goals
- atk_2 drop leading-colon check (accepts ':pass'): exit 1, unsolved goals
- atk_3 drop colon-count check (accepts 'a:b:c'): exit 1, unsolved goals
- atk_4 ungrounded oracle echo `:= true`: exit 1, simp made no progress
- atk_5 drop empty check (partial-domain, accepts ''): exit 1
- atk_6 off-by-one boundary (allow <=2 colons): exit 1, unsolved goals
- atk_7 wrong char class (allow '/'): exit 1, unsolved goals
Commands: `bash scripts/lean_verify.sh atk_N.lean`; run concurrently in two batches of 4/3.

**RESOLVE STEP:** step-2 (materialize faithful patch + run_resolve) has NO applicable candidates because ZERO wrong impls closed a clean-axiom proof. patches={}.

MODEL<->PATCH CORRESPONDENCE (the only non-R/I-mechanical check here): urlUserinfoValid is faithful to gold inner-group regex `[^\s:@/]+(?::[^\s:@/]*)?`. Independent Python differential (NOT the bundle's conformance_check.py): 0 mismatches over exhaustive strings len<=3 (delimiters/ws/astral alphabet) + 200000 random fuzz over full non-surrogate code-point range. isUserinfoWhitespace == Python re \s EXACTLY: both 29 code points, symmetric difference empty over 0x0-0x10FFFF (Python 3.12).

**REFINEMENT.MD AUDIT:** 6 legs, all tagged R or I. NO A-consumed, NO A-reference, NO kind-3 legs. axiom_check.py is a justified skip (no consumed callee axiom; deep model). The A-leg attack surface this reviewer targets is empty by construction; the sole deep-model correspondence (model<->regex) is verified faithful above. Surrogate domain caveat (U+D800-DFFF) is honest and unreachable on both Lean Char and Python str.

**PREPATCH REPRODUCED:** Solution_prepatch.lean same_spec=True, fails to verify (rfl failed) -> G-DIFF live.

**VERDICT:** SOUND. >=7 distinct same-spec wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-char-class, off-by-one, prepatch) all fail to verify; positive control verifies with clean axioms; model faithful to gold regex over full code-point space; no closes-but-does-not-resolve gap possible.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function urlUserinfoValid (List Char -> Bool) is the acceptance predicate of the post-patch inner regex group `[^\s:@/]+(?::[^\s:@/]*)?` from django/core/validators.py:97 (gold patch confirmed against test.jsonl). Faithfulness verified rigorously: (1) isUserinfoWhitespace reproduces EXACTLY the 29 code points Python `re \s` matches over str (set-equal). (2) Exhaustive per-code-point differential over 0x0-0x10FFFF (surrogates excluded per documented, benign Char-domain restriction) in 5 structural contexts vs re.fullmatch -> 0 mismatches. (3) Exhaustive len<=4 enumeration + 2,000,000 randomized fuzz (len<=8) seeded 10097 with G-CONF look-alike traps (ZWSP, WORD JOINER, ZWNBSP, MONGOLIAN VOWEL SEPARATOR, IDEOGRAPHIC SPACE) -> 0 mismatches. (4) Single-colon/leading-colon structure correctly enforces user vs user:pass; F2P invalid URLs (foo@bar@, foo/bar@, foo:bar:baz@) rejected. (5) Proof compiles clean, `#print axioms` = [propext] only, no sorryAx. same_spec(Solution,prepatch)=False is the intended G-DIFF signal (prepatch models the old \S regex), not a spec defect. The spec neither over- nor under-approximates the real callee on any input; no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean) contains no gold-edit disclosure beyond the public problem_statement. Mechanical G-LEAK screen passes (0 hard failures). same_spec(Solution, prepatch)=True confirms the spec region is byte-identical between pre/post-patch — the spec is a stable forward acceptance predicate, not a diff.

Leak-vector checks:
- No diff markers (@@, diff --git, +++). 
- Patched file path 'django/core/validators.py' and module path absent from spec view.
- Patched repo symbol 'URLValidator' absent from spec view (identifiers + comments).
- No bug/fix narration (previously/incorrectly/broken/fix/…) in any comment.
- Pre-patch regex '\S+(?::\S*)?' does NOT appear in the spec view; it lives only in refinement.md/mapping.md (auditor docs, not the consumer spec view — out of frame for G-PANEL-3).

The one arguable fragment is the docstring quoting the post-patch character class `[^\s:@/]` and describing admissible userinfo chars as 'neither whitespace nor one of the reserved delimiters :, @, /'. This does NOT leak beyond problem_statement: the public task quotes RFC 1738 §3.1 verbatim ('Within the user and password field, any ":", "@", or "/" must be encoded') and gives the concrete invalid example http://foo/bar@example.com. Thus the exact discriminating delimiter set {:,@,/} and the whitespace exclusion (the old \S already excluded whitespace) are already solver-visible. Restating the acceptance predicate (non-empty, no leading colon, ≤1 colon separator, admissible chars) is the necessary forward specification any spec must give; it neither reproduces the gold diff line, localizes the edited regex, nor discloses information absent from the public problem statement.

**Gold edit:** r'(?:\S+(?::\S*)?@)?' -> r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'. The delta (exclude :,@,/ and disallow leading/second colon in userinfo) is exactly what RFC 1738 §3.1 in the problem statement mandates. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
