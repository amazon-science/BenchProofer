# mapping.md — sphinx-doc__sphinx-9320

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e05cef574b8f23ab1b57f57e7da6dee509a4e230`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the A-tagged callee and its three primitives.

Repo file under change: `sphinx/cmd/quickstart.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `optionalPathValidator (entry : List Char)` | `is_path_or_empty(x)` — `sphinx/cmd/quickstart.py` (NEW function added by the patch, between `is_path` at :91 and `allow_empty` at :98) | the modeled changed behavior: the lenient path-entry validator |
| `rawExpansion : (entry : List Char) → expansionAnswers entry = true → List Char` *(opaque, PARTIAL — A-reference)* | `os.path.expanduser(x)` as called at `sphinx/cmd/quickstart.py:92`, **at an `x` where it answers** | the home-directory expansion itself. `expanduser` is NOT total (two rows down), and that is carried by the TYPE rather than by a comment: reading this requires a proof that the entry is one the expansion answers for, so there is no term anywhere — at the method's own entry or at an entry an impl derives from it — that reads the expansion off its domain. One boundary fact assumed (§3, fact 1). |
| `pathExpanded (entry) : List Char` *(derived `def`, total)* | `path.expanduser(x) if _answers(x) else ''` — the GUARDED expansion (§1.1) | the expansion as any program may READ it: `if answered : expansionAnswers entry = true then rawExpansion entry answered else []`. TOTAL, and free at every entry, because the guard is inside the definition; the `[]` in the second branch is a value and not an answer, and since `expansionAnswers` is opaque and known only at `[]`, no program can show any particular entry to be in that branch or conclude anything from it. On the obligation's domain this IS `rawExpansion`, so every clause of the method reads the expansion proper. `pathExpanded_empty` is a THEOREM from facts 1+5, not an assumption. |
| `pathIsDir : List Char → Bool` *(opaque, total — A-reference)* | `os.path.isdir(x)` as called at `sphinx/cmd/quickstart.py:93` | the directory test applied to the EXPANDED entry. GENUINELY TOTAL: answers for every input (it catches `OSError` and `ValueError` itself), has no other effect, cannot take control away from its caller. One boundary fact assumed (§3, fact 2). |
| `expansionAnswers : List Char → Bool` *(opaque, total — A-reference)* | "`os.path.expanduser(x)` hands an answer back at all" — the totality DOMAIN of the call at `sphinx/cmd/quickstart.py:92` | WHERE the expansion answers. `expanduser` catches only `KeyError` around `pwd.getpwnam(...)`, so for an entry beginning with `~` whose first segment cannot be looked up at all — a NUL segment (`ValueError: embedded null byte`) or one holding a high surrogate the filesystem encoding cannot represent (`UnicodeEncodeError`, a `ValueError` subclass) — the lookup escapes and there is no expansion for anyone to read, test or discard. This primitive names the complement of that set. It is the `require` of the modeled method (§3, fact 5) and the guard on fact 3. A LOW surrogate is NOT such an entry: `surrogateescape` encodes it, the lookup merely fails to find it, `KeyError` is caught, so it stays in the domain — both regions and that pair are measured by G-AX and G-CONF. |
| `strictAccepts (entry) : Bool` *(derived `def`)* | `path.isdir(path.expanduser(x) if _answers(x) else '')` — `pathIsDir` of the GUARDED expansion (§1.1) | the strict validator's acceptance DECISION, as a pure predicate. TOTAL and free to evaluate anywhere, for any entry, in any order, as often as an impl likes — including at an entry the impl derives from its own input — because both reads underneath it are total. **On the domain this `Bool` IS the strict validator's decision** (`path.isdir(path.expanduser(x))`, gold's own test); off the domain it is not, and nothing reads it as one. |
| `strictPathValidator : List Char → VelvetM (List Char)` *(opaque PROGRAM — A-reference)* | `is_path(x)` — `sphinx/cmd/quickstart.py:91` | SUBMITTING an entry to the unchanged strict validator (invoked, never redefined). NOT a function from entries to outcomes: on an entry the expansion answers for and it accepts, it hands back `path.expanduser(x)`; on one it does not accept it hands back nothing at all — it RAISES, so control leaves the submitter (§2); on one the expansion does not answer for it likewise hands back nothing (the escape propagates through it). Two facts assumed (§3, facts 3–4), both validated against the real callee by axiom_check.py (G-AX); no `ensures` is consumed from a contract that would let an impl substitute for it. |
| `require expansionAnswers entry = true` *(the method's domain)* | the set of entries on which the patched `is_path_or_empty(x)` COMES BACK — with a value or with the `ValidationError` the call site catches | the obligation's domain, and the one restriction on it. It restricts the ENTRY alone and says nothing about which entries are accepted, so the whole accept/turn-away decision stays inside the obligation. G-CONF asserts this row in both directions on 100k inputs: in the domain the real function always comes back (so the domain is not too small), out of it it never comes back (so the domain is not too large). |

Consequence of the `strictPathValidator` row, and the whole point of modeling the callee as a
PROGRAM rather than a value: **submitting is an act an impl must EARN**. There is
no body to unfold and no total function underneath, so a submission can appear in
a verifying impl only where that entry is shown accepted at the point it is
handed over. **Deciding** acceptance is NOT submitting — `strictAccepts` is free.
That distinction is the control-flow content of the change (the empty entry is
accepted *without ever being handed to the strict validator*), and it is what a
value-only model cannot express.

### 1.1 What a READ of a pure primitive refines to — the guard travels with it

The rows above bind each symbol at the method's own entry. This section fixes the
counterpart of a read **at an arbitrary argument**, because the method's `require`
restricts the ENTRY and says nothing about arguments an impl builds from it, and a
verifying impl may read a pure primitive wherever it likes:

| a term reads… | its repo counterpart, at **any** argument `X` |
|---|---|
| `pathIsDir X` | `path.isdir(X)` — total; answers `False` for an embedded NUL or a lone surrogate rather than escaping |
| `expansionAnswers X` | `_answers(X)`, i.e. "`path.expanduser(X)` hands an answer back" — total, a `bool` |
| `pathExpanded X` | `path.expanduser(X) if _answers(X) else ''` — **the guarded expansion**, total |
| `strictAccepts X` | `path.isdir(path.expanduser(X) if _answers(X) else '')` — total |
| `rawExpansion X h` | `path.expanduser(X)` — only reachable where `h : _answers(X)` is in hand, and there the guarded form above is equal to it |

The rule, stated once: **a read refines to the guarded form unless the term itself
carries the proof that the argument is in the domain.** Only `rawExpansion` can
carry that proof, and it can only be applied where a proof exists, so
`path.expanduser(X)` appears in a refinement exactly where the argument is known
to answer — and nowhere else. Two consequences the spec depends on:

* **no read can take control away.** Every primitive an impl may freely read is
  total on both sides of the mapping, so a verifying impl that reads the
  primitives at a derived argument refines to Python that comes back. This is the
  hole a previous revision had: `pathExpanded` was `opaque … : List Char → List
  Char`, a TOTAL FUNCTION TYPE promising totality in a comment, so a read at
  `'~' :: Char.ofNat 0 :: entry` refined to `path.expanduser('~\x00' + x)`, which
  raises `ValueError('embedded null byte')`. G-EQ recorded verifying rivals of
  exactly that shape whose faithful counterparts did NOT resolve.
* **reading is free; ANSWERING from a read is not.** The guarded value at an
  argument off the domain is `''`/`[]`, which is a value and not the expansion, and
  `expansionAnswers` is opaque — so nothing can be concluded from it, and an impl
  that turns such a read into its own verdict is refuted by the obligation
  (properties.py `weak-derived-probe-as-verdict`), while one that merely reads and
  discards still verifies (`pos-derived-probe-guarded`) and its refinement resolves.
* **an ACCEPTED read at a derived argument LICENSES a submission there.** Since
  acceptance can only happen inside the domain (`accepted_in_domain`, §3 fact 3),
  an impl that shows a derived argument accepted has thereby shown *both* halves of
  fact 3 at that argument, so it may hand that argument to the strict validator and
  the submission comes back carrying the derived entry's expansion. This is a
  genuine licence rather than a gap: it is exactly what the real
  `is_path(derived)` does, its refinement is Python that comes back, and it is the
  reason the guard on fact 3 costs nothing. What is NOT licensed is a submission at
  an argument the impl cannot show accepted, derived or not.

All three bullets are measured, not argued: G-AX asserts on every input that the
guarded expansion and `isdir` answer at the entry AND at two derived entries
(`'~' + NUL + entry`, `'~' + entry`), that the RAW expansion escapes at the first
of those every time, and — at every read that came out accepted — that the
argument was in the domain and that submitting it came back with `expanduser` of
it verbatim. G-CONF runs the `pos-derived-probe-guarded` impl as a second shadow
and the `pos-derived-submission-earned` impl as a third, asserting each is
observationally identical to the frozen one on every input and that the third's
earned submission actually fired and was accounted for. Every claim has a
negative control: replacing the guarded read with a bare `path.expanduser` fails
both gates at the derived argument; forcing an acceptance off the domain fails
G-AX with `accepted_in_domain is unsound`; and a shadow whose earned submission
never fires, is not earned, or is unaccounted for fails G-CONF (three controls,
all recorded).

Site of use (refinement audit only, not in the consumer spec view): the
`do_prompt(...)` call inside `ask_user` for the "new root path (or just Enter to
exit)" prompt (`sphinx/cmd/quickstart.py:229–230` post-patch) switches its
`validator` argument from the strict validator to the lenient one; the existing
`if not d['path']: sys.exit(1)` guard (:231) then fires on the now-accepted
empty entry. No behavior of that call site is modeled beyond the validator's
return contract — the validator is the entire substantive change.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `x: str` (the entry argument) | `List Char` | `s` (Python str) ↔ its `List Char` of code points; empty `str` `''` ↔ `[]`; `len(s)` ↔ `l.length` |
| the modeled function's RETURN on acceptance: `str` (the expanded entry, or `''` for the empty entry) | `Except.ok (v : List Char)` | accepted value `v` ↔ `Except.ok v.toList` |
| the modeled function's RETURN on refusal: `raise ValidationError(...)` | `Except.error ()` | any `ValidationError` leaving `is_path_or_empty` ↔ `Except.error ()`; the error PAYLOAD (message string) is not observed by the call site (`do_prompt` only catches it to re-loop, and the only F2P-observable outcome is accept-empty → `sys.exit`), so it is abstracted to `Unit` |
| the CALLEE's refusal: `raise ValidationError(...)` leaving `is_path` *inside* the modeled function | `strictPathValidator entry` has no guarantee of returning (§3, fact 4) | control does not come back to the submitter, so there is no outcome for it to read, test or discard |
| the modeled function NOT COMING BACK AT ALL: `ValueError`/`UnicodeEncodeError` from `pwd.getpwnam` inside `expanduser`, propagating out of `is_path_or_empty` uncaught | *(nothing — excluded by `require expansionAnswers entry = true`)* | this is a THIRD outcome at the modeled function's own boundary, and it is neither `Except.ok _` nor `Except.error ()`: the row above maps ONLY a `ValidationError` to `Except.error ()`, and the call site's `except ValidationError` does not catch this one either, so the prompt loop is left as well. It is not abstracted; it is placed OUTSIDE the obligation's domain. See §2.2. |

### 2.1 The exception at TWO boundaries (and why they differ)

The same `ValidationError` is abstracted two different ways, at two different
boundaries, and both abstractions are faithful *at their own boundary*:

* **At the modeled function's own boundary** it is a VALUE, `Except.error ()`.
  Justified because the raise is *caught*: `do_prompt` wraps the validator call
  in `try/except ValidationError` and re-prompts, so from the caller's point of
  view "the entry was turned away" is an outcome that is observed and acted on.
* **At the callee boundary, inside the modeled function**, it is NON-RETURN.
  Justified because nothing inside `is_path_or_empty` catches it: a raise from
  `is_path` propagates straight through, so the code that submitted the entry
  never resumes and can neither inspect nor discard a result.

Corollary used by the battery: an intermediate `Except`-valued binding inside the
impl region (e.g. `let decided : Except Unit (List Char) := if … then … else …`)
is a VALUE, not a raise — it models a decision an impl computes for itself from
the free primitives, not an exception crossing a boundary. Only
`strictPathValidator` crosses the callee boundary.

### 2.2 The third outcome, and why it is a DOMAIN and not an abstraction

The two rows in §2.1 abstract a `ValidationError`. A third thing can happen to a
caller of the patched function, and it is neither of them: for an entry beginning
with `~` whose first segment cannot be looked up at all, `pwd.getpwnam` raises
`ValueError('embedded null byte')` (or `UnicodeEncodeError` for a high surrogate),
`expanduser` catches only `KeyError`, and the exception leaves
`is_path_or_empty(x)` uncaught. Measured at the patched commit:
`is_path_or_empty('~\x00abc')` raises `ValueError: embedded null byte`.

That outcome cannot be mapped to `Except.error ()` — the abstraction above maps
only a `ValidationError` there, and it is deliberately tight, because the call
site's `except ValidationError` re-prompts while this exception exits the prompt
loop entirely; the two are not the same observation. It cannot be mapped to
`Except.ok _` either. So a spec of the shape "for every non-empty entry the
outcome is `ok` or `error`" claims something the real function does not do, on
those entries and only those. Under `loom.semantics.termination "total"` such a
spec also implicitly asserts the modeled function TERMINATES WITH A VALUE for
every entry it governs — and `strictAccepts` being a total-typed `Bool` hides
that, because the `if` in the `ensures` reduces for every entry whether or not
the real expansion answers.

The repair is a DOMAIN, not a wider abstraction: `require expansionAnswers entry
= true`. Two reasons this is the right axis, both measured rather than asserted:

* Modeling the third outcome instead (a three-way result carrier) would be
  modeling `pwd.getpwnam`'s encoding behaviour, which the patch does not touch
  and no F2P test observes — new assumed facts, no new obligation.
* Guarding the two `ensures` clauses with the same antecedent instead would NOT
  close it: the antecedent weakens what the postcondition claims but leaves the
  method's TERMINATION obligation standing on every entry, so an out-of-domain
  entry would still be claimed to come back. properties.py records this as the
  rejected alternative; `pos-domain-guard-redundant` there is the control that
  the `require` is what reaches the impl.

The domain is exactly the entries the expansion answers for — not larger (G-CONF
asserts the real function never comes back outside it) and not smaller (G-CONF
asserts it always comes back inside it, so no governed entry has a third
outcome). The empty entry, the entry the change is about, is INSIDE it by fact 5.

Cost of the asymmetry, stated plainly: the impl SHAPE that submits every
non-empty entry and lets the callee's raise propagate — which is the gold
patch's own control flow — cannot verify here, because under
`loom.semantics.termination "total"` a program that does not come back satisfies
no `ensures`. This restricts which shapes an impl may take; it adds no
obligation the real post-patch behavior violates (the frozen impl refines the
patched function's behavior exactly). refinement.md §C records it as a modeling
limitation; properties.py records the measured shape that is excluded.

`List Char` is the carrier because the only structural property the spec needs
is emptiness (`entry = []` ↔ `x == ''`); indexing is total and sound in Lean.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `strictPathValidator` ↔ `is_path`, `pathExpanded`/`pathIsDir` ↔ `expanduser`/`isdir`
**Callee:** `sphinx.cmd.quickstart.is_path` (unchanged by the patch). Source at
base_commit (`quickstart.py:91`):

```python
def is_path(x: str) -> str:
    x = path.expanduser(x)
    if not path.isdir(x):
        raise ValidationError(__("Please enter a valid path name."))
    return x
```

G-AX runs at **base_commit** (the gold patch is NOT applied for this gate), so it
validates ONLY this unchanged callee and the stdlib primitives it is built from —
never the patch-added `is_path_or_empty` (which does not exist at base_commit).
The spec relies on exactly **five** assumed facts, each checked standalone
against the real code by axiom_check.py, none of them pinned as a consumable
contract beyond what is stated:

1. **`rawExpansion_empty` : `∀ (answered : expansionAnswers [] = true),
   rawExpansion [] answered = []`.** Real: `path.expanduser('') == ''`. Stated of
   the RAW expansion because that is where the assumption belongs — the guarded
   reading is a definition, not an axiom. It quantifies over the proof argument
   (proof irrelevance makes that harmless) so the fact holds however the empty
   entry's domain membership was obtained. With fact 5 it gives the derived theorem
   `pathExpanded_empty : pathExpanded [] = []`, which is what the clauses read.
2. **`pathIsDir_empty` : `pathIsDir [] = false`.** Real: `path.isdir('') is
   False`.

   Facts 1+2+5 give the DERIVED theorem `strictAccepts_empty : strictAccepts [] =
   false` — the strict validator does not accept an empty entry. **This is the
   load-bearing premise for the reported behavior**: the strict validator alone
   can never let an empty entry through, so the prompt can never be satisfied by
   pressing Enter. axiom_check.py also confirms it end-to-end on the real callee
   (`is_path('')` does not come back). It is what justifies an empty affordance
   in front of the strict validator, and it is what the two hole-covering reject
   rivals in properties.py are refuted by.
3. **`strictPathValidator_accepted` : `expansionAnswers entry = true →
   strictAccepts entry = true → strictPathValidator entry = pure (pathExpanded
   entry)`.** On an entry the expansion answers for and the validator accepts, a
   submission comes back, handing back the expanded entry. Real: if
   `path.expanduser(x)` answers and `path.isdir` of it is True, then `is_path(x)`
   returns, and returns `path.expanduser(x)` verbatim (note: `expanduser`, so for
   `~` it returns `/home/<user>`, not `~`). Where the fact applies, the guarded
   reading on the right-hand side IS `rawExpansion`, i.e. `path.expanduser(x)`,
   which is what the real callee hands back.

   **The first hypothesis is IMPLIED by the second, not load-bearing, and it is
   retained anyway.** Once `pathExpanded` carries the guard, `accepted_in_domain`
   (Solution.lean, a theorem: acceptance implies domain membership) makes
   `strictAccepts entry = true` on its own enough to put `entry` in the domain, so
   dropping `expansionAnswers entry = true` here would give a fact that is
   *interderivable* with this one rather than a stronger one. That is a measured
   claim, not a reading: the two-hypothesis and one-hypothesis forms each verify
   from the other, and the earlier revision's argument that an unguarded form
   would be unsound off the domain is WRONG for a precise reason — off the domain
   the guarded expansion is `[]` and `pathIsDir [] = false`, so `strictAccepts` is
   `false` there and the equation is never asserted off the domain at all. The
   hypothesis is kept because it is the shape the submission has to EARN: the
   `@[loomSpec]` lemma's precondition names both halves, so a program (or a rival)
   is confronted with both, and G-AX checks the fact only in the region where both
   hold. axiom_check.py additionally asserts the implication itself at every
   accepted read — at the entry and at two derived entries — so `accepted_in_domain`
   is not merely derived in Lean but confirmed of the real primitives.
4. **`strictPathValidator_turns_away` : `strictAccepts entry = false → ¬ triple
   True (strictPathValidator entry) (fun _ => True)`.** On an entry it does not
   accept, a submission carries no guarantee of coming back at all. Real: if not
   `path.isdir(path.expanduser(x))` then `is_path(x)` does not return — it raises
   `ValidationError`, which propagates out of the submitter (§2.1). Meaningful in
   Lean because `NoFailure DivM` is declared inside `PartialCorrectness` and this
   bundle opens `TotalCorrectness`, so `wp c (fun _ => True)` genuinely expresses
   "control comes back". **Deliberately UNGUARDED**, and sound that way: where the
   expansion does not answer, `is_path(x)` does not come back either (the escape
   propagates through it), so whichever way the unconstrained `strictAccepts x`
   falls the fact holds — vacuously if it is true, and met by the real callee if
   it is false. Guarding it would give away refutations for nothing. Checked by
   G-AX in BOTH regions for exactly that reason.
5. **`expansionAnswers_empty` : `expansionAnswers [] = true`.** Real:
   `path.expanduser('')` answers (it returns `''`, which is fact 1). This is what
   keeps the empty entry — the one input the modeled change is about — INSIDE the
   obligation's domain, so the `require` of §1 cannot excuse it and the
   empty-entry `ensures` clause cannot be vacuous. properties.py's
   `admiss-outcome-nondegenerate` pins the same thing from the battery side.

The model asserts nothing MORE: no claim about WHICH non-empty entries are
accepted, no claim about what any particular expansion is, and no claim about
which entries the expansion answers for beyond the empty one. Facts 3+4 are
jointly satisfiable, and so are all five together — refinement.md §D records a
concrete Lean-checked model (exit 0), so nothing proved from them is proved from
a contradiction.

`strictPathValidator_hands_back` (the `@[loomSpec]` lemma the obligation is
discharged against) is a **theorem** derived from fact 3, not a further
assumption.

Note: the lenient-vs-strict *delegation* fidelity for non-empty entries — that
the patched `is_path_or_empty` gives every non-empty entry the strict
validator's own verdict — is the **R/I refinement** obligation, mechanically
refuted by **G-CONF** at the *patched* commit (`conformance_check.py`), NOT by
G-AX. G-AX stays at base_commit and never touches the patched function.

**Flag dependencies:** none. `is_path` reads only the filesystem (`path.isdir`)
and `path.expanduser`; G-AX exercises existing dirs (tempdir, `~`, cwd),
non-existing paths, `~` expansion, whitespace/unicode entries, and the NUL /
high-surrogate `~` entries that put the expansion outside its domain.

**Soundness check (G-AX):** `axiom_check.py` imports the real repo module at
**base_commit**, asserts facts 1, 2 and 5 directly against `os.path` (fact 1 in
both readings — the raw expansion of `''` and the guarded one), asserts the
derived empty-entry premise end-to-end (`is_path('')` does not come back), and
asserts facts 3 and 4 on 39 boundary + 22000 fuzz inputs (seed 9320): in the
domain every accepted entry comes back as `expanduser(entry)` verbatim and every
non-accepted entry does not come back at all, and out of the domain no entry
comes back. Every input is bucketed into out-of-domain / in-domain-accepted /
in-domain-refused and each bucket is asserted NON-EMPTY, because an alphabet with
no NUL and no high surrogate in it never reaches the first one — which is exactly
how a previous revision's fuzzing agreed with a spec that claimed an outcome for
every entry. Last measured buckets: 800 / 4475 / 16764.

It also asserts §1.1 — the totality that makes the freely readable primitives
free — on every input and at THREE arguments each: the entry itself, and the two
derived entries the method's `require` says nothing about, `'~' + NUL + entry`
(whose RAW expansion escapes for every entry, so it is the family that makes the
guard load-bearing rather than decorative) and `'~' + entry` (sometimes accepted,
sometimes out of domain, so it is the family that exercises what a program may DO
with a derived read). At all three: `isdir` took control away from nobody, the
GUARDED expansion took control away from nobody and equalled `expanduser` exactly
where it answers, and the RAW expansion at the NUL-derived argument escaped
**every** time. Last measured: 22039 reads per argument, i.e. `{'entry': 22039,
'derived-escape': 22039, 'derived-tilde': 22039}`.

And it asserts the derived theorem `accepted_in_domain` on the real primitives, at
every read that came out ACCEPTED: the expansion also answered there, and the
submission that acceptance earns came back with `expanduser(entry)` verbatim.
Last measured 5300 accepted reads, `{'entry': 4475, 'derived-escape': 0,
'derived-tilde': 825}` by family — so the derived licence of §1.1 is exercised 825
times rather than asserted, and the NUL family's `0` is the same fact from the
other side (nothing outside the domain is ever accepted, which is what the theorem
says).

Negative controls, run and recorded: with the guarded read replaced by a bare
`path.expanduser`, the gate fails with `pathExpanded's TOTAL type is unsound: the
guarded expansion of '~\x00' took control away (ValueError: embedded null byte)`;
with `isdir('')` forced True (so an out-of-domain entry reads as accepted), it
fails with `accepted_in_domain is unsound: the guarded expansion of '~\x00abc'
names an existing directory, yet the expansion does not answer there`. Imports
only stdlib + the repo. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`9320`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl region: the emptiness test and the empty affordance, then the
acceptance DECISION recomputed from the two modeled primitives through the
guarded expansion of §1.1 (`isdir(expanduser(x) if _answers(x) else '')`), and
only then the SUBMISSION, which is A-tagged and therefore runs the REAL `is_path`
(§3: A-tagged ops run the real callee, not a model). The oracle is the patched
`is_path_or_empty`.

Beyond comparing outcomes, the shadow instruments `is_path` with a counting
wrapper and checks the SUBMISSION ORDER on the input the change is about: both
sides must submit the empty entry **zero** times, and an accepted entry exactly
once. A previous revision's shadow hardcoded the gold call order and only then
delegated, which made it blind to a hoisted or extra submission by construction;
that blindness is measured and fixed — with the shadow replaced by the hoisted
shape as a negative control, the gate now fails at input `''` (`shadow
submits=1`, `oracle submits=0`). The one legitimate difference (a non-accepted
non-empty entry: the oracle submits and lets the raise propagate, the shadow
decides first) is COUNTED and reported, not asserted, per §2.1.

It also asserts THE DOMAIN of §1 in both directions, which is what makes the
`require` a measured boundary rather than a convenient exclusion (§2.2):

* IN the domain the oracle must come back — value or `ValidationError`, never a
  third outcome — else the domain is too SMALL and the spec governs an input
  whose behaviour it cannot express;
* OUT of the domain the oracle must NOT come back at all — neither a value nor a
  `ValidationError` — else the domain is too LARGE and the `require` is excusing a
  perfectly specifiable input.

Both directions have negative controls, run and recorded. With the domain replaced
by "every entry" (i.e. the previous revision's unrestricted spec) the gate fails
with `input='~\x00abc' IN the domain but the oracle did not come back (ValueError:
embedded null byte)` — the mechanical form of the finding this revision repairs.
With the domain replaced by the wider "not a `~` entry" the gate fails with
`input='~root' OUT of the domain but the oracle came back as ('ok', '/root')`.

Outcomes are compared **in the domain**, and out of it the two sides part company
by construction rather than by accident: the real function does not come back
there, while every read the modeled impl performs is the guarded one and therefore
total, so the shadow comes back with a turn-away. That difference is exactly what
the `require` excuses — the spec claims no outcome for those entries — and
comparing there would assert something the spec does not say. The claim that
replaces the comparison is asserted in its place on every out-of-domain input:
**the shadow must come back.** Nothing about the boundary rests on the comparison,
since both its edges are asserted separately and in both directions above.

The gate also asserts §1.1 behaviourally, on every input: reading the guarded
expansion at the derived argument `'~' + NUL + entry` must hand an answer back
(it did, on every input), and the `pos-derived-probe-guarded` impl from
properties.py — the frozen impl plus exactly that read — must be observationally
identical to the frozen shadow, same outcome and same submission count. Two more
negative controls, run and recorded: with the guarded read replaced by a bare
`path.expanduser` the gate fails with `reading the guarded expansion at the
derived entry '~\x00' took control away (ValueError: embedded null byte)`, and
with the probe ANSWERING from that read instead of discarding it, the gate fails
with `a guarded read at the DERIVED entry '~\x00' changed the observable behaviour
(('error',) vs ('ok', ''))`.

A THIRD shadow measures the licence rather than only the read: the
`pos-derived-submission-earned` impl from properties.py, which at the empty entry
decides acceptance of the derived entry `'~' + entry` and, inside the branch where
that decision came out accepted, SUBMITS it — the act `accepted_in_domain` licenses
(§1.1, third bullet). The gate asserts on every input that this shadow has the
frozen shadow's outcome, that its submission count differs from the frozen one by
exactly the one earned submission, and that the earned submission actually came
back; and it asserts at the end that the branch FIRED at least once, so a shadow
that quietly measured nothing is a failure rather than a pass. Three negative
controls, run and recorded: with the branch made unreachable the gate fails with
`the EARNED derived submission never fired in this run, so it measured nothing`;
with the submission moved OUT of the accepting branch (submitting `'~' + NUL +
entry`, which is never accepted) it fails with `submitting the DERIVED entry …
(('escape', 'ValueError', 'embedded null byte') vs ('ok', ''), 1 submissions vs
0 …)`; and with the extra submission not declared it fails with the same check on
the count (`1 submissions vs 0, 0 of them expected to be extra`).

Each input is also bucketed out-of-domain / in-domain-accepted / in-domain-refused
and each bucket asserted non-empty; last measured, over 100029 inputs: 3716 /
20062 / 58612 (the remaining 17639 are the empty entry, which is in the domain and
has its own submission-count assertion), 0 disagreements, 0 domain violations, 0
guarded-read drifts, 0 order violations, with the derived guarded read answering
100029 times and the earned derived submission firing 17639 times.
