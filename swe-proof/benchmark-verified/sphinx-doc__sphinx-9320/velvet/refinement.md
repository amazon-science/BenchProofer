# refinement.md — sphinx-doc__sphinx-9320

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`optionalPathValidator` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized/opaque callee —
**A-consumed** where the proof uses an asserted `ensures`, **A-reference** where
a deep model / direct delegation is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The new lenient validator — `is_path_or_empty()`

Gold hunk (the substantive addition):
```python
+def is_path_or_empty(x: str) -> str:
+    if x == '':
+        return x
+    return is_path(x)
```
plus the one-line rewire of the `do_prompt(...)` call from `is_path` to
`is_path_or_empty` (the call site is not itself modeled — see §B).

| # | Solution.lean impl op (`optionalPathValidator`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | `require expansionAnswers entry = true` — the obligation's DOMAIN | the entries on which `is_path_or_empty(x)` comes back at all (with a value or with the `ValidationError` the call site catches) | R | mapping.md §1, §2.2. Not an op: the domain of the whole correspondence below. It restricts the ENTRY alone, keeps the empty entry inside (fact 5), and excludes only entries on which the patch changed nothing — a `~` entry whose first segment cannot be looked up escapes identically before and after the patch. §C states the cost; G-CONF asserts both edges. |
| A1 | parameter `entry : List Char` | `x: str` arg of `is_path_or_empty` | R | `str` ↔ `List Char` (mapping.md §2). `''` ↔ `[]`. G-CONF bridges via the str↔List Char carrier. |
| A2 | `if entry = [] then return Except.ok []` | `if x == '': return x` | R + I | the emptiness test (`entry = []` ↔ `x == ''`) is **I** (identical concrete branch, transliterated by G-CONF); returning the entry verbatim on the empty branch is **R** — `return x` with `x == ''` ↔ `Except.ok []` (accept-with-value, mapping.md §2). No submission happens on this path on either side (G-CONF measures it: both submit the empty entry **zero** times). |
| A3 | `if strictAccepts entry then …` — the acceptance DECISION, taken from the modeled primitives through the GUARDED expansion | `path.isdir(path.expanduser(x))`, the test inside `is_path` | A-reference + R | `strictAccepts = pathIsDir ∘ pathExpanded`, where `pathExpanded` is the guarded reading of the expansion, ↔ `isdir(expanduser(x) if _answers(x) else '')` (mapping.md §1, §1.1). Deciding is FREE — total at every argument, including one an impl derives from its own input — and that is bought by the guard being inside the term, not by the `require`: `expanduser` is not total (mapping.md §2.2), so an unguarded read would be the hole §C records. What the `require` buys is different and is about the CLAUSES, not the decision: inside the domain the guarded reading IS `expanduser(x)`, so there this `Bool` is gold's own test verbatim and there is an outcome to pin. G-CONF recomputes the decision from the real primitives through the guarded read rather than replaying gold's call order. |
| A4 | `let accepted ← strictPathValidator entry; return Except.ok accepted` — the SUBMISSION, on the branch where the entry is shown accepted | `return is_path(x)` | A-reference + I | the submission is the UNCHANGED callee `is_path` invoked verbatim (**I** — concrete call; G-CONF runs the real callee here). Modeled as an opaque PROGRAM with two assumed facts (mapping.md §3, facts 3–4), no consumed `ensures` an impl could substitute for: on an accepted entry it comes back with `pathExpanded entry`; on any other entry it has no guarantee of coming back. So a submission is an act the impl must EARN at the point it hands the entry over. The two hypotheses of fact 3 are earned TOGETHER — acceptance implies domain membership (`accepted_in_domain`, a theorem) — so what an impl may submit is exactly an entry it has shown accepted there, whether that is its own input or one it derived from it (§C). |
| A5 | `else return Except.error ()` — a non-empty entry the decision refuses | the `ValidationError` that `is_path` raises and `is_path_or_empty` propagates | R | refusal at the modeled function's own boundary is the value `Except.error ()`, because `do_prompt` catches it and re-prompts (mapping.md §2.1). Same outcome as gold; see §C for the one shape this costs. |
| A6 | result `out : Except Unit (List Char)` returned | the function's `str` return / propagated `ValidationError` | R | acceptance `Except.ok v` ↔ returned `str`; refusal `Except.error ()` ↔ `ValidationError` leaving `is_path_or_empty` (mapping.md §2). |

Discriminating content of the change — the EMPTY entry is accepted
(`entry = [] → out = Except.ok []`) **without being submitted to the strict
validator that would refuse it** — lives in the first `ensures` clause together
with the derived `strictAccepts_empty` and the assumed
`strictPathValidator_turns_away`. The pre-patch behavior (the strict validator
governs the empty entry, so it is refused and the prompt loops) is the reported
failure; `Solution_prepatch.lean` reproduces it (every entry is submitted to the
strict validator, no empty affordance) and **fails** the clause
`entry = [] → out = Except.ok []` (G-DIFF: measured exit 1, `case «ensures_2:
entry = [] → out = Except.ok []»`).

## B. The call-site rewire — `do_prompt(..., is_path)` → `do_prompt(..., is_path_or_empty)`

Gold hunk:
```python
 d['path'] = do_prompt(__('Please enter a new root path (or just Enter to exit)'),
-                      '', is_path)
+                      '', is_path_or_empty)
```
This is a **pure callee swap at one call site** and is NOT separately modeled.
Its entire observable effect is captured by site A: the F2P test
`test_exits_when_existing_confpy` monkeypatches `path.isfile` to True (forcing
the existing-conf.py loop) and feeds `''` to the "new root path" prompt; with
the lenient validator the empty entry is now ACCEPTED, so `do_prompt` returns
`''`, the subsequent `if not d['path']: sys.exit(1)` fires, and `ask_user`
raises `SystemExit`. The only behavioral lever is "the validator at this prompt
now accepts the empty entry" — exactly the A2/A3/A4 contract of
`optionalPathValidator`. No `do_prompt`/`ask_user` control flow is modeled; a
prepatch must keep the spec byte-identical (G-DIFF), and site A's prepatch
already exercises the discriminating empty-entry behavior.

This call site is also where mapping.md §2.1's first boundary is justified:
`do_prompt` catches `ValidationError` and re-prompts, so at the modeled
function's own boundary a refusal is an OUTCOME the caller observes, which is why
it is reified as `Except.error ()`.

## C. No kind-3 (inexpressible-changed-op) steps, and the one modeling limitation

Every step is R, A, or I. The operation that genuinely *changed* — accepting the
empty entry in front of the strict validator instead of submitting it — is
modeled **directly** (steps A2–A4), not hidden behind an axiom about the function
under change. The A constructs are all **unchanged** code (`is_path` and the two
`os.path` primitives it is built from), modeled with no consumed contract and
validated by G-AX (A-reference).

**MODELING LIMITATION, disclosed and measured.** The same `ValidationError` is
abstracted two ways at two boundaries (mapping.md §2.1): as the value
`Except.error ()` where the modeled function returns to a caller that catches it,
and as CONTROL NOT COMING BACK where the callee raises inside the modeled
function and nothing catches it. Both are faithful at their own boundary, and
together they are what make an unearned submission refutable at all. Their cost
is exactly one impl SHAPE. Under `loom.semantics.termination "total"` a program
that does not come back satisfies no `ensures`, so

```lean
    if entry = [] then return Except.ok []
    else
      let accepted ← strictPathValidator entry     -- submitted without deciding;
      return Except.ok accepted                    -- the refusal would propagate
```

does **not** verify (measured: exit 1) even though it is the gold patch's own
control flow, whose faithful counterpart resolves. Two consequences, both stated
plainly:

* This is a restriction on which SHAPES an impl may take, not an obligation the
  real post-patch behavior violates. The spec's clauses demand the patched
  function's BEHAVIOR with its refusal reified at its own boundary, and the
  frozen impl refines exactly that (§A, and §E below);
  `return is_path(x)` answers with the expanded entry where the entry is accepted
  and refuses otherwise, which is `Except.ok (pathExpanded entry)` /
  `Except.error ()` under mapping.md §2.
* Because that shape's faithful counterpart RESOLVES, it is deliberately NOT
  shipped as an `expect:"reject"` case in properties.py — recording it as a rival
  would assert something false. properties.py names it as measured and omitted,
  with this section as the reason.

The excluded shape is a strict subset of "submits without deciding": an impl that
decides first (the frozen impl), or that decides and never submits at all
(`pos-decision-inlined`, measured exit 0), verifies. So no correct BEHAVIOR is
made unimplementable.

**THE ONE RESTRICTION ON THE DOMAIN, disclosed and measured.** Separately from
the shape restriction above, the obligation is restricted to part of the input
space: `require expansionAnswers entry = true` (mapping.md §1, §2.2). This is
NOT the same disclosure as the asymmetry above and is not covered by it — the
asymmetry is about which impl shapes may establish the clauses, this is about
which entries the clauses are claimed for at all.

The reason is a THIRD outcome of the real patched function. For an entry
beginning with `~` whose first segment cannot be looked up at all,
`pwd.getpwnam` raises `ValueError` (NUL) or `UnicodeEncodeError` (high
surrogate), `expanduser` catches only `KeyError`, and the exception leaves
`is_path_or_empty(x)` uncaught. Measured at the patched commit:
`is_path_or_empty('~\x00abc')` raises `ValueError: embedded null byte`. That is
neither the modeled `Except.error ()` (mapping.md §2 maps only a
`ValidationError` there, and the call site's `except ValidationError` does not
catch this one, so the prompt loop exits rather than re-prompting) nor
`Except.ok _`. A previous revision of this spec had no `require` at all, so —
because `pathExpanded`/`pathIsDir` are total-typed and `strictAccepts entry`
therefore reduces for EVERY entry, and because under
`loom.semantics.termination "total"` an `ensures` also demands coming back —
it claimed one of the two modeled outcomes for entries where the real function
produces neither. That was a spec-too-strong defect, recorded as such, and the
`require` is its repair.

What the restriction costs, stated plainly, and what it does not:

* It restricts the ENTRY alone. It says nothing about which entries the validator
  accepts, so the whole accept/turn-away decision — the substantive content — stays
  inside the obligation, for every entry in the domain, with no clause left to an
  implementation's discretion.
* The empty entry, the one input this change is about, is INSIDE the domain, and
  by a checked fact (`expansionAnswers_empty`, mapping.md §3 fact 5) rather than by
  assumption. The discriminating clause is therefore not vacuous;
  `admiss-outcome-nondegenerate` in properties.py pins it from the battery side,
  and `Solution_prepatch.lean` still fails exactly that clause with the `require`
  in context (G-DIFF).
* The domain is the boundary of what is SPECIFIABLE here, not a convenience: out
  of it the real function has no outcome to pin, so no obligation of this shape
  could be faithful there. G-CONF asserts both edges on 100k inputs — in the
  domain the real function always comes back, out of it never — so the domain is
  neither too small nor too large (mapping.md §4, with the two negative controls
  recorded there).
* Guarding the two `ensures` clauses with the same antecedent instead of adding a
  `require` would NOT have closed the defect: an antecedent weakens what the
  postcondition claims but leaves the method's TERMINATION obligation standing on
  every entry. Measured and recorded in properties.py as the rejected alternative;
  `pos-domain-guard-redundant` there is the control that the `require` is what
  reaches the impl (an impl that re-tests the domain condition itself still
  verifies, i.e. the hypothesis is genuinely available), and
  `weak-domain-guard-as-verdict` is the control that the domain condition may be
  CONSULTED but not ANSWERED FROM: the impl that reads it as the verdict (turn away
  every entry the expansion answers for, accept the empty value for the rest) is
  rejected, with a machine-checked witness at `[]` whose only hypothesis is
  `expansionAnswers_empty` — so it is also the case that would start passing if the
  domain ever grew to exclude the empty entry.

**THE READ GUARD: why the expansion is not a total function, and what that
licenses.** The `require` above restricts the method's ENTRY. It says nothing
about arguments an impl BUILDS from that entry, and a verifying impl may read a
pure primitive wherever it likes — so a primitive's TYPE, not the `require`, is
what fixes where reading it is legitimate. This is not a hypothetical: a previous
revision declared

```lean
    opaque pathExpanded : List Char → List Char        -- total FUNCTION type
```

with a comment promising the expansion answers everywhere. Under mapping.md §1.1
a read refines to a call, so `pathExpanded ('~' :: Char.ofNat 0 :: entry)` refined
to `path.expanduser('~\x00' + x)` — which raises `ValueError('embedded null
byte')`. G-EQ recorded verifying rivals of exactly that shape whose faithful
counterparts did not resolve: verify no longer implied resolve, at an argument the
`require` could not reach even in principle.

The repair puts the guard in the terms. `rawExpansion` — the expansion itself —
takes a PROOF that the entry is one the expansion answers for, so it cannot be
applied anywhere a proof is missing; and what a program may freely read,
`pathExpanded`, is *definitionally* the guarded reading (the expansion where it
answers, `[]` elsewhere). Three consequences, each measured rather than argued:

* **No read can take control away, at any argument.** The freely readable
  primitives are total on both sides of the mapping, so a verifying impl's reads
  refine to Python that comes back. G-AX asserts this on every input at three
  arguments (the entry, `'~' + NUL + entry`, `'~' + entry`) and asserts that the
  RAW expansion at the NUL-derived one escapes every time — 22039 reads per
  argument, last measured. G-CONF asserts it behaviourally, and the
  `pos-derived-probe-guarded` impl (which performs exactly that derived read) is
  shipped as a positive: it verifies AND is observationally identical to the frozen
  impl on 10⁵ inputs. Negative control for both gates: replace the guarded read
  with a bare `path.expanduser` and each fails at the derived argument.
* **Reading is free; ANSWERING from a read is not.** Off the domain the guarded
  value is `[]`, a value and not the expansion, and `expansionAnswers` is opaque and
  known only at `[]` — so no impl can show any particular entry to be in that branch
  or conclude anything from it. `weak-derived-probe-as-verdict` (turn the derived
  read into the verdict) is refuted with a machine-checked witness; the same impl
  that reads and DISCARDS verifies.
* **An accepted read LICENSES a submission at that argument, and that licence is
  honest.** `accepted_in_domain` (Solution.lean, a theorem: acceptance implies
  domain membership) means an impl that shows a DERIVED entry accepted has earned
  both hypotheses of fact 3 there, so it may submit that entry and the submission
  comes back with its expansion. That is what the real code does too, so admitting
  it is fidelity and not laxity: G-AX measured 825 accepted derived reads whose
  submission came back with `expanduser` of the derived entry verbatim, and
  `pos-derived-submission-earned` is shipped as a positive impl doing exactly this
  (verifies; and G-CONF runs it as a third shadow, asserting the earned submission
  fired, came back, and changed no outcome, with three negative controls —
  never-fires, unearned, unaccounted). What stays excluded is unchanged: a
  submission at an argument the impl cannot show accepted (`weak-submission-hoisted`,
  `weak-unconsumed-probe`).

One consequence for mapping.md §3 fact 3, stated here because it is a *loss* of a
claim an earlier revision made: with the read guarded, the first hypothesis of
fact 3 (`expansionAnswers entry = true`) is IMPLIED by the second and is therefore
redundant rather than load-bearing. It is retained because it is the shape a
submission has to earn and the shape G-AX checks, not because dropping it would be
unsound. §D's model checks that redundancy (`m_unguarded_fact3_also_holds`) instead
of the opposite claim, which an earlier revision of this document recorded and
which is false.

## D. Joint satisfiability of the five assumed facts (Lean-checked)

The five facts of mapping.md §3 are jointly satisfiable, so nothing proved from
them is proved from a contradiction. This is not argued in prose — it is a
concrete model, checked by the same verifier the bundle uses
(`scripts/lean_verify.sh`, **exit 0**):

```lean
def mIsDir (entry : List Char) : Bool := !entry.isEmpty

def mExpansionAnswers (entry : List Char) : Bool :=
  match entry with
  | '~' :: _ => false
  | _ => true

def mRawExpansion (entry : List Char) (_ : mExpansionAnswers entry = true) :
    List Char := entry

def mExpanded (entry : List Char) : List Char :=
  if answered : mExpansionAnswers entry = true then mRawExpansion entry answered
  else []

def mAccepts (entry : List Char) : Bool := mIsDir (mExpanded entry)

def mNoReturn {α : Type} [Inhabited α] : VelvetM α :=
  NonDetT.vis (DivM.div : DivM PUnit) (fun _ => pure default)

def mValidator (entry : List Char) : VelvetM (List Char) :=
  if mExpansionAnswers entry && mAccepts entry then pure (mExpanded entry)
  else mNoReturn

theorem m_raw_empty (answered : mExpansionAnswers [] = true) :
    mRawExpansion [] answered = [] := by
  simp [mRawExpansion]

theorem m_isdir_empty : mIsDir [] = false := by simp [mIsDir]
theorem m_answers_empty : mExpansionAnswers [] = true := by simp [mExpansionAnswers]

theorem m_expanded_empty : mExpanded [] = [] := by
  simp [mExpanded, mExpansionAnswers, mRawExpansion]

theorem m_accepts_empty : mAccepts [] = false := by
  simp [mAccepts, m_expanded_empty, mIsDir]

theorem m_accepted (entry : List Char) :
    mExpansionAnswers entry = true → mAccepts entry = true →
    mValidator entry = pure (mExpanded entry) := by
  intro hd h; simp [mValidator, hd, h]

theorem m_turns_away (entry : List Char) :
    mAccepts entry = false →
    ¬ triple (l := Prop) True (mValidator entry) (fun _ => True) := by
  intro h hcon
  simp only [mValidator, h, Bool.and_false, Bool.false_eq_true, if_false, mNoReturn,
    triple, NonDetT.wp_vis] at hcon
  simp [wp, liftM, monadLift, MAlg.lift, MAlgOrdered.μ, Functor.map] at hcon

theorem m_out_of_domain_does_not_come_back :
    ¬ triple (l := Prop) True (mValidator ['~']) (fun _ => True) := by
  refine m_turns_away ['~'] ?_
  simp [mAccepts, mExpanded, mExpansionAnswers, mIsDir]

theorem m_accepted_in_domain (entry : List Char) :
    mAccepts entry = true → mExpansionAnswers entry = true := by
  intro h
  by_cases hd : mExpansionAnswers entry = true
  · exact hd
  · simp [mAccepts, mExpanded, hd, mIsDir] at h

theorem m_unguarded_fact3_also_holds (entry : List Char) :
    mAccepts entry = true → mValidator entry = pure (mExpanded entry) := by
  intro h
  exact m_accepted entry (m_accepted_in_domain entry h) h
```

`m_raw_empty`/`m_isdir_empty`/`m_answers_empty`/`m_accepted`/`m_turns_away` are the
five facts with
`rawExpansion`/`pathIsDir`/`expansionAnswers`/`strictPathValidator` instantiated to
`mRawExpansion`/`mIsDir`/`mExpansionAnswers`/`mValidator`, under the bundle's own
`set_option loom.semantics.termination "total"` and `open TotalCorrectness
DemonicChoice`. The model mirrors the SHAPE of the spec and not only its facts:
`mRawExpansion` carries the domain proof exactly as `rawExpansion` does, and
`mExpanded` is the guarded reading, so `m_expanded_empty`, `m_accepts_empty` and
`m_accepted_in_domain` are derived here in the same way they are derived in
Solution.lean. Four things this model settles, each machine-checked rather than
asserted:

* `m_turns_away` shows that "no guarantee of coming back" is inhabited rather than
  vacuous, by exhibiting a program (`DivM.div`) that genuinely fails to satisfy
  `wp c (fun _ => True)`.
* `mExpansionAnswers` is NOT the constant `true` here, so the five facts do not
  force the domain to be everything, and `m_answers_empty` is not proved by a
  degenerate domain. The model mirrors the real shape: `['~']` is an entry outside
  the domain for which the validator does not come back
  (`m_out_of_domain_does_not_come_back`) — exactly the situation mapping.md §2.2
  measures at `'~\x00abc'`.
* `m_accepted_in_domain` shows the derived theorem the derived-submission licence
  of §C rests on is derivable in a concrete model too, and not only from the
  opaque declarations.
* `m_unguarded_fact3_also_holds` records what an earlier revision of this document
  got backwards. It claimed the guard on fact 3 was NECESSARY, with a theorem
  (`m_unguarded_fact3_would_be_false`) that is UNPROVABLE once the read is guarded:
  in this model `mAccepts ['~']` is `false`, because off the domain the guarded
  expansion is `[]` and `mIsDir [] = false`, so the unguarded form of fact 3 is not
  refutable — it FOLLOWS, via `m_accepted_in_domain`. The guard is therefore
  redundant but harmless, exactly as mapping.md §3 fact 3 now states. (The earlier
  model reached the opposite result honestly: it had `mExpanded = id`, i.e. an
  unguarded expansion, which is the very defect §C repairs.)

## E. verify(Solution) ⇒ resolved

`optionalPathValidator` verifies only if, for every entry in its domain (an entry
the expansion answers for — §C), (A2) it accepts the empty entry as the empty
value, (A3–A5) it gives every non-empty entry the strict validator's own verdict —
the expanded entry where the strict validator accepts it, a refusal everywhere
else — and (A4) it never submits an entry it has not shown accepted at the point of
submission. By R (`str ↔ List Char`, `'' ↔ []`, accept ↔ `ok`,
refusal-at-the-function-boundary ↔ `error ()`) the verified validator equals the
gold `is_path_or_empty` on the tested inputs; by G-AX the five assumed facts hold
of the real unchanged code, including that the empty entry is not accepted (so
the empty affordance is the observable behavior change), that a submission of
a non-accepted entry does not come back (so the structural obligation is real,
not a modeling artifact), and that the empty entry is inside the domain (so the
`require` does not excuse the input the change is about); by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs, submits the
empty entry zero times on both sides, and the domain is exactly the entries on
which the real function comes back at all. The call-site swap (§B) turns that
accept-empty behavior into the `sys.exit` the F2P test demands.

This leg holds at arguments the `require` does not mention, which is precisely
where a previous revision's did not (§C). Every primitive a verifying impl may
freely read is guarded and total, so each of its reads refines to Python that comes
back whatever argument it reads at; and the only thing it can DO at a derived
argument — submit one it has shown accepted — refines to a real `is_path(derived)`
that comes back with that argument's expansion (G-AX measured 825 such submissions,
all of them returning `expanduser` of the derived entry verbatim). So "verifies ⇒
resolves" is not conditional on an impl confining itself to its own input, and the
two shipped positives that leave that confinement (`pos-derived-probe-guarded`,
`pos-derived-submission-earned`) are shipped precisely because their refinements
resolve.

The domain does not weaken this leg for the behaviour under test. The F2P input is
the empty entry, which is in the domain; every entry the F2P and P2P tests feed
this prompt is in the domain; and out of the domain the real patched function
raises out of `ask_user` entirely, which no test observes and which the pre-patch
code does identically (`is_path('~\x00abc')` escapes the same way, so the domain is
not where the patch changed anything).

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement, the audited callee, the one excluded shape of §C
(which is a shape restriction, not a behavioral one) and the domain restriction of
§C (which excludes only entries on which the patch changed nothing and no outcome
is expressible). The gold patch resolves (G-RESOLVE). Trust points are exactly the
two of plan §1.1: callee soundness (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).

The two verifying-but-not-resolving impls a prior G-EQ pass recorded — bind the
strict validator's answer for `entry` once up front and then select (hoisted
delegation), and submit the entry, discard the answer, then run the gold branch
(unconsumed probe) — are refuted by this model rather than admitted by it: each
submits `[]`, and `strictPathValidator_turns_away []` (via the derived
`strictAccepts_empty`) says a submission of `[]` has no guarantee of coming back,
so neither can establish any `ensures`. Both are shipped as reject cases with
machine-checked witnesses in properties.py
(`weak-submission-hoisted`, `weak-unconsumed-probe`).

The later G-EQ finding — rivals that read the expansion at an argument DERIVED from
the entry, which verified while their Python raised `ValueError('embedded null
byte')` — is closed the other way round, and it is worth being explicit that this is
deliberate. Those impls are not refuted: reading is legitimate, so refuting them
would make a correct behaviour unimplementable. What changed is the READ they refine
to. With `pathExpanded` guarded by construction (§C, mapping.md §1.1) the rival's
own refinement is the guarded call, which comes back — so it verifies and it
resolves, and both facts are shipped as positives with the gates that measure them
(`pos-derived-probe-guarded`, `pos-derived-submission-earned`; G-AX at three
arguments, G-CONF as two extra shadows). The impl that turns such a read into its
verdict is the one that is refuted (`weak-derived-probe-as-verdict`), because that
one really does behave differently from the gold patch.
