"""properties.py — G-PBT falsification battery for sympy__sympy-22456 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct reconstructInvariance`` obligation survives with a
byte-identical statement). ``expect="verify"`` passes iff (in scope AND
verifies); ``expect="reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: it must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  reconstructInvariance (s : StrObj) return (out : InvarianceResult)
    ensures applyPos out.kind s (exposedArgs s) = some s      (C1)
    ensures applyKw  out.kind s out.kwNames     = some s      (C2)

  The operation SELECTS, for an atomic string-valued object, the arity of its
  reconstruction function (``out.kind``) and the keyword names its keyword-view
  exposes (``out.kwNames``). The two clauses then APPLY that selected function to
  the object's OWN exposed positional arguments and to its keyword arguments and
  demand both reproduce the object. Because the object exposes an empty
  positional-argument view (``exposedArgs s = []``, a deep-modeled unchanged
  structural inspection):

   * C1 is satisfiable ONLY by the no-argument arity: a no-argument function
     accepts the empty positional call and yields the object, while a
     single-specifier arity rejects the empty call (no value for its required
     specifier) and reconstruction fails. C1 therefore pins ``out.kind`` to the
     no-argument form.
   * C2, given that arity, is satisfiable ONLY by the empty keyword-name set: a
     no-argument function accepts a keyword call only when no keyword names are
     supplied. C2 therefore pins ``out.kwNames`` to empty.

  So the pair pins the WHOLE selection to (no-argument arity, no keyword names) —
  the unique reconstruction view under which BOTH argument-invariance identities
  hold at once, which is exactly the behavior the issue and the failing test
  demand.

AUDIT NOTE — the soundness surface, machine-checked beyond the two positives
(attack E). Four FURTHER correct reshapes were built and all four VERIFY against
the frozen spec: deriving the keyword-name set from the exposed positional view
(`(exposedArgs s).map (·.text)`), reversing the data flow so the arity is derived
from the keyword-name set rather than the other way round, binding the whole
record in one `let` and returning it, and building the keyword-name set as a
`filter` that is provably empty. So the spec is not over-fit to the frozen impl's
data-flow shape in any of those four directions.

One reshape could NOT be landed, and it is a TOOLING limit, not a spec hole: a
`match sel with | true => return ... | false => return ...` selection over a
computed `Bool` fails to elaborate with `Failed to parse an assertion without
names: WPGen (match ... )` — the weakest-precondition generator does not accept a
`match` whose arms are `return`s in this position. That is a carrier/front-end
limitation on the impl SHAPE and says nothing about the obligation; the `if`-shaped
equivalent of the same selection verifies (it is `pos-control-arity-from-exposed-
args`). Recorded because "the reshape did not build" must not be read as
SPEC-TOO-STRONG when the error is not about the spec.

CARRIER NOTE — why this port carries four rivals against the nagini sibling's
five.

  The nagini sibling models a DIFFERENT facet of the same object. Its carrier is
  the object's defining TEXT (a code-point sequence) and its pin is that the
  reconstruction reproduces that text ELEMENT FOR ELEMENT — so its rivals attack
  a text-copy loop (drop-first, drop-last, prefix-only, wrong-value run) plus a
  read-only-frame permission surface. THIS backend does not model the text at
  all: ``StrObj`` keeps ``text`` only as the identity the object is compared by,
  and the operation under specification is the SELECTION of the reconstruction
  function's arity and keyword-name set — the actual content of the fix (the
  reconstruction function becomes nullary and the keyword-view becomes empty).
  Consequently:

   * The text-copy rivals' ELEMENT-WISE arithmetic has no counterpart: this
     carrier has no text-copy loop to break, so "drops index 0" and "emits a run
     of NULs" are not distinguishable behaviors here. Dropped with reason (see
     footer) — carrier narrowing, not an omission of convenience.
   * Their SHAPE, however, does port, and one of them is carried for it: an impl
     correct on a genuine sub-domain of the input and wrong off it. See
     ``weak-selection-varies-with-object``, which branches the selection on the
     object's own text. This is the case that makes the input binder a real
     discriminating dimension.
   * The two frame-mutation rivals are VACUOUS: this backend is referentially
     transparent, ``s`` is an immutable non-``mut`` value, there is no heap, no
     aliasing, and no fractional-permission system to trip. Dropped, not
     fabricated (per the porting map).
   * What IS discriminable here is the two-clause SELECTION. Each clause is
     attacked by exactly one clause-isolating rival: the pre-fix single-specifier
     arity (refuted by C1) and a non-empty keyword-name set under the correct
     arity (refuted by C2). Both clauses are also defended by two
     structurally-distinct positive controls.

WITNESS MECHANISM. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``reconstructInvarianceTester s = false`` says the extracted program's result
violates the method's postcondition at that concrete input. Checked in a file
whose ``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Each witness was built against its rival (must elaborate) and against
the frozen solution (must fail) before shipping.

WITNESS PLACEMENT / coverage. The CORRECT selection is constant in the single
input binder ``s``: the object exposes no positional sub-arguments regardless of
its text (``exposedArgs s = []`` for every ``s``), so gold need not read ``s`` at
all. That makes ``s`` inert FOR GOLD, but it does NOT make ``s`` undiscriminable —
a WRONG impl is free to branch on it, and one that returns the correct selection on
a sub-domain of ``s`` while returning the pre-fix selection elsewhere is both
expressible on this carrier and refutable at a concrete ``s``. So the battery
attacks THREE independent dimensions: the two OUTPUT fields the selection
comprises (``out.kind`` and ``out.kwNames``), each by its own clause-isolating
rival, and the INPUT binder ``s``, by the partial-domain rival
``weak-selection-varies-with-object`` (correct exactly on the empty-text
sub-domain, refuted at a non-empty text). The three witnesses sit at three
DISTINCT input points (``s.text`` = "a", "b", "c").

  A previous revision of this manifest asserted the opposite — that ``s`` "cannot
  be a discriminating dimension" and that "no rival can be built that mishandles a
  particular ``s`` value" — and gave that as the reason the sibling's
  partial-domain class had no counterpart here. That claim was FALSE: it confused
  "gold's answer does not depend on ``s``" with "no impl's answer may". The
  counterexample was built and now ships as a case.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22456"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap). This is
# ---- the whole gold selection body: bind the no-argument arity, bind the empty
# ---- keyword-name set, return the pair. Every variant swaps this block, so
# ---- nothing outside the impl region is ever touched.
_GOLD_IMPL = (
    "    let kind : FuncKind := FuncKind.noArgForm\n"
    "    let kwNames : List (List Char) := []\n"
    "    return { kind := kind, kwNames := kwNames }\n"
)


# ---- witness preamble. Extract the method to an executable program, prove its
# ---- pre/postconditions decidable, derive the tester, then assert the tester
# ---- REJECTS the rival at one concrete input. Appended to a file whose
# ---- `prove_correct` block has been stripped.
def _tester(s_lit):
    return (
        "extract_program_for reconstructInvariance\n"
        "prove_precondition_decidable_for reconstructInvariance\n"
        "prove_postcondition_decidable_for reconstructInvariance\n"
        "derive_tester_for reconstructInvariance\n\n"
        f"example : reconstructInvarianceTester {s_lit} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # selections that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation statement byte-identical
    # and reshapes only the executable surface; the produced selection is
    # definitionally the gold one, so the frozen proof script closes unchanged.
    # =====================================================================
    {
        "id": "pos-control-inline-return",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the two intermediate `let` bindings and build the pair
        # directly in the returned literal. The returned selection is
        # definitionally identical, so `loom_solve <;> simp_all [...]` discharges
        # both clauses unchanged.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    return { kind := FuncKind.noArgForm,"
            " kwNames := ([] : List (List Char)) }\n"),
        "rationale": "Inlining the arity/keyword-set bindings into the returned "
                     "record leaves the selection definitionally identical, so "
                     "both C1 (`applyPos out.kind s (exposedArgs s) = some s`) and "
                     "C2 (`applyKw out.kind s out.kwNames = some s`) hold and the "
                     "frozen proof closes without change. A correct reshape that "
                     "failed to verify would mean the spec is SPEC-TOO-STRONG on "
                     "the impl's data-flow shape.",
    },
    {
        "id": "pos-control-arity-from-exposed-args",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: derive the arity from the object's own exposed positional-
        # argument view rather than naming it as a constant — the no-argument
        # form exactly when the exposed positional view is empty (which it always
        # is, `exposedArgs s = []`). Observationally the gold selection; the
        # frozen proof unfolds `exposedArgs` and closes the guard.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let kind : FuncKind :=\n"
            "      if (exposedArgs s).isEmpty then FuncKind.noArgForm"
            " else FuncKind.oneArgForm\n"
            "    let kwNames : List (List Char) := []\n"
            "    return { kind := kind, kwNames := kwNames }\n"),
        "rationale": "Selecting the no-argument arity precisely when the object's "
                     "exposed positional view is empty computes the same selection "
                     "as gold (the exposed view is empty for every object), so both "
                     "clauses still hold; a correct reshape that read the arity off "
                     "the exposed-args structure must verify (else SPEC-TOO-STRONG "
                     "on how the arity is derived). A second, structurally distinct "
                     "correct impl so the soundness surface is defended by more "
                     "than one reshape.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The method carries no `require`
    # clause, so the usual "a normal input satisfies the precondition" probe has
    # nothing to exclude. The analogue on this TOTAL carrier is the obligation
    # being UNSATISFIABLE at exactly an F2P-shaped input: an obligation no
    # computation can meet at the interesting point reads, to the gate, exactly
    # like an obligation every computation meets. So the case discharges the
    # obligation's OWN two clauses BY EVALUATION at a concrete non-empty object —
    # the shape the failing test exercises — as an in-region `assert`, and then
    # lets the frozen `prove_correct` body close the real obligation verbatim.
    #
    # The assert is LOAD-BEARING, not decoration, and this was measured rather
    # than asserted: the same case with a FALSE claim about the same concrete
    # object (`applyPos oneArgForm ... = some ...`, and separately `applyKw
    # noArgForm ... ["text"] = some ...`) leaves `⊢ False` as an unsolved goal
    # under the frozen proof body and FAILS to build. So this case can only pass
    # by the two clauses actually being satisfiable at that point.
    # =====================================================================
    {
        "id": "admiss-selection-reachable-at-nonempty",
        "kind": "admissibility",
        "expect": "verify",
        # The gold impl is kept VERBATIM (the assert is prepended to it), and the
        # frozen `prove_correct` tactic body is left untouched — `loom_solve <;>
        # simp_all [applyPos, applyKw, exposedArgs]` discharges the extra assert
        # goal by the same evaluation that closes the obligation, so nothing about
        # the frozen proof is retuned or weakened.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    assert (with_name_prefix `admiss\n"
            "      (applyPos FuncKind.noArgForm { text := \"foo\".toList }\n"
            "          (exposedArgs { text := \"foo\".toList }) = some { text := \"foo\".toList }\n"
            "        ∧ applyKw FuncKind.noArgForm { text := \"foo\".toList } []"
            " = some { text := \"foo\".toList }\n"
            "        ∧ applyPos FuncKind.oneArgForm { text := \"foo\".toList }\n"
            "            (exposedArgs { text := \"foo\".toList })"
            " ≠ some { text := \"foo\".toList }\n"
            "        ∧ applyKw FuncKind.noArgForm { text := \"foo\".toList }"
            " [\"text\".toList]\n"
            "            ≠ some { text := \"foo\".toList }))\n"
            + _GOLD_IMPL),
        "rationale": "PRECOND-TOO-STRONG lane on a total carrier: the obligation "
                     "must be SATISFIABLE at an F2P-shaped input, not merely "
                     "provable for a universally quantified `s`. At the concrete "
                     "non-empty object `s.text = \"foo\"` the assert discharges, by "
                     "evaluation, that the no-argument selection meets C1 "
                     "(`applyPos noArgForm s (exposedArgs s) = some s`) AND C2 "
                     "(`applyKw noArgForm s [] = some s`) there — so the pair of "
                     "clauses is jointly reachable at exactly the shape the failing "
                     "test exercises. The two ≠ conjuncts additionally pin that the "
                     "obligation is NON-DEGENERATE at that same point: the "
                     "single-specifier arity does NOT satisfy C1 there and a "
                     "non-empty keyword-name set does NOT satisfy C2 there, so the "
                     "clauses are discriminating and not trivially true of every "
                     "selection. If the obligation were unsatisfiable at that input "
                     "this assert could not discharge and the case would FAIL, which "
                     "is the PRECOND-TOO-STRONG finding this lane exists to make.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong selections sharing the frozen
    # spec that MUST be rejected, each with a machine-checked refutation witness
    # at a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-single-specifier-arity",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix selection: the reconstruction function requires the single
        # text specifier (one-argument arity), and the keyword-view exposes that
        # lone specifier's name. Attacks C1: applying a single-specifier function
        # to the object's EMPTY exposed positional arguments supplies no value for
        # the required specifier, so the positional reconstruction fails.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let kind : FuncKind := FuncKind.oneArgForm\n"
            "    let kwNames : List (List Char) := [\"text\".toList]\n"
            "    return { kind := kind, kwNames := kwNames }\n"),
        "refinement": "This IS the pre-fix reconstruction view: the inherited "
                      "single-specifier reconstruction function paired with a "
                      "keyword-view that supplies that specifier. Its faithful real "
                      "counterpart is the UNPATCHED code, under which applying the "
                      "reconstruction function to the object's own (empty) "
                      "positional arguments fails — exactly the identity the "
                      "failing test newly asserts. Definitively non-resolving.",
        "rationale": "REJECT from C1 (`applyPos out.kind s (exposedArgs s) = "
                     "some s`): with the single-specifier arity, `applyPos` on the "
                     "empty exposed positional view returns `none`, not `some s`. "
                     "Verifying would be SPEC-TOO-WEAK on the positional-"
                     "reconstruction clause (it would admit the pre-fix arity). "
                     "Refuted at `s.text = \"a\"` via the tester.",
        "witness": _tester('{ text := "a".toList }'),
    },
    {
        "id": "weak-nonempty-keyword-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct no-argument arity (so C1 holds), but the keyword-view still
        # exposes the legacy text specifier's name. Attacks C2: a no-argument
        # function accepts a keyword call ONLY when no keyword names are supplied,
        # so applying it to a non-empty keyword-name set fails to reconstruct.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let kind : FuncKind := FuncKind.noArgForm\n"
            "    let kwNames : List (List Char) := [\"text\".toList]\n"
            "    return { kind := kind, kwNames := kwNames }\n"),
        "refinement": "A counterpart that makes the reconstruction function "
                      "no-argument (so the positional identity holds) but leaves "
                      "the keyword-view exposing the legacy specifier name would, "
                      "in the real object, pass that name to a function that "
                      "accepts none — so applying the function to the keyword "
                      "arguments raises and the pre-existing keyword-reconstruction "
                      "identity `func(**kwargs()) == self` (also asserted by the "
                      "test) breaks. It would NOT resolve.",
        "rationale": "REJECT from C2 (`applyKw out.kind s out.kwNames = some s`): "
                     "under the no-argument arity, `applyKw` succeeds only on the "
                     "empty keyword-name set, so a set containing the specifier "
                     "name returns `none`, not `some s`. This is the only rival "
                     "that attacks C2 — the clause pinning the keyword-view to "
                     "empty — and it holds C1 fixed at the correct arity, "
                     "isolating C2. Verifying would be SPEC-TOO-WEAK on the "
                     "keyword-reconstruction clause. Refuted at `s.text = \"b\"` "
                     "via the tester.",
        "witness": _tester('{ text := "b".toList }'),
    },
    {
        "id": "weak-selection-varies-with-object",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the INPUT binder `s` — the on-carrier counterpart of
        # the sibling's partial-domain class, which an earlier revision of this
        # manifest wrongly recorded as having none. The selection is made to
        # DEPEND on the object: the correct (no-argument, empty-keyword) view is
        # returned only when the object's text is empty, and the pre-fix
        # single-specifier view everywhere else. Correct on a genuine sub-domain,
        # wrong on every non-empty object — so it is refuted only by a witness
        # placed at a non-empty text, which is what makes `s` a real
        # discriminating dimension rather than an inert one.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let kind : FuncKind :=\n"
            "      if s.text.isEmpty then FuncKind.noArgForm"
            " else FuncKind.oneArgForm\n"
            "    let kwNames : List (List Char) :=\n"
            "      if s.text.isEmpty then [] else [\"text\".toList]\n"
            "    return { kind := kind, kwNames := kwNames }\n"),
        "refinement": "A counterpart that made the reconstruction view depend on "
                      "the object's own content — nullary reconstruction only for "
                      "the empty text, the inherited single-specifier "
                      "reconstruction for everything else — is faithful (it is "
                      "expressible as a real conditional on the object) but NON-"
                      "RESOLVING: the failing test asserts the positional "
                      "reconstruction identity on an object whose text is NOT "
                      "empty, and on that object this counterpart takes the "
                      "pre-fix branch and the reconstruction fails exactly as it "
                      "did before. It would resolve only the degenerate "
                      "empty-text case, which the test does not exercise.",
        "rationale": "REJECT from C1 and C2 together, at every object with a "
                     "non-empty text: on that sub-domain the selection is the "
                     "single-specifier arity, so `applyPos` on the empty exposed "
                     "positional view returns `none` (C1 fails) and `applyKw` is "
                     "handed the specifier name (C2 fails). Verifying would be "
                     "SPEC-TOO-WEAK in the most dangerous direction — admitting "
                     "an impl that is right only on a sub-domain — and it is the "
                     "one rival whose rejection is attributable to the INPUT "
                     "binder rather than to a constant output field. Refuted at "
                     "`s.text = \"c\"` via the tester; the same witness at "
                     "`s.text = \"\"` does NOT refute it, confirming the "
                     "sub-domain is genuine and the case is not merely a "
                     "differently-spelled everywhere-wrong rival.",
        "witness": _tester('{ text := "c".toList }'),
    },
    {
        "id": "weak-keyword-set-empty-name",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on C2, added by the audit (attack D). The existing C2 rival
        # exposes the legacy specifier NAME; this one exposes a keyword-name set
        # that is non-empty while every name in it is EMPTY. It is the sharpest
        # available near-miss on the "keyword-view is empty" clause, because it
        # distinguishes the two readings a weaker clause could have conflated:
        # "the keyword-name SET is empty" (what C2 actually says, and what the fix
        # does) versus "no keyword name carries content". A spec that pinned only
        # the latter — e.g. one comparing the concatenation or the joined text of
        # the names rather than the list itself — would ADMIT this selection, since
        # `[[]]` carries no characters at all. C2 as frozen rejects it, and the
        # rejection is the evidence that the clause pins the LIST and not its
        # content. Correct arity throughout, so C1 is held fixed and the rejection
        # is attributable to C2 alone.
        "module": _swap(
            _BASE, _GOLD_IMPL,
            "    let kind : FuncKind := FuncKind.noArgForm\n"
            "    let kwNames : List (List Char) := [[]]\n"
            "    return { kind := kind, kwNames := kwNames }\n"),
        "refinement": "A counterpart that made the reconstruction function "
                      "no-argument (so the positional identity holds) but left the "
                      "keyword-view exposing ONE entry under an empty name would, in "
                      "the real object, pass a keyword argument to a function that "
                      "accepts none — the call is supplied a name it has no "
                      "parameter for, so it raises and the keyword-reconstruction "
                      "identity `func(**kwargs()) == self` (also asserted by the "
                      "test) breaks. That the name happens to carry no characters "
                      "does not make the keyword-view empty: a view exposing one "
                      "entry is a call with one keyword argument. Faithful but "
                      "NON-RESOLVING.",
        "rationale": "REJECT from C2 (`applyKw out.kind s out.kwNames = some s`): "
                     "under the no-argument arity `applyKw` succeeds only on `[]`, "
                     "and `[[]]` is a one-element list, so it returns `none`. "
                     "Verifying would be SPEC-TOO-WEAK in a specific and easily "
                     "missed direction — a clause that pinned the keyword names' "
                     "CONTENT rather than the name list itself. Refuted at "
                     "`s.text = \"d\"` via the tester; the audit confirmed the "
                     "witness elaborates against this rival (exit 0), fails against "
                     "the frozen solution by a plain evaluation (exit 1, `decide` "
                     "proved the tester is `true` there), and that the flipped claim "
                     "`= true` builds on gold (exit 0) — so gold's exit code tracks "
                     "the claim rather than a syntactic gap.",
        "witness": _tester('{ text := "d".toList }'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) plus 2 AXIOM_TESTS probes. The
# sibling models a DIFFERENT facet of the same object — the element-wise
# reproduction of the object's defining TEXT by a rebuild loop, over a read-only
# heap object carrying fractional permissions. THIS bundle models the operation
# the patch actually changes: the SELECTION of the reconstruction function's
# arity and keyword-name set (the function becomes nullary, the keyword-view
# becomes empty). Every sibling case is accounted for below.
#
#   sibling case                         -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape                  -> pos-control-inline-return       PORTED
#                                           (+ pos-control-arity-from-exposed
#                                              -args ADDED)
#   admiss-nonempty-selfcall             -> admiss-selection-reachable-at-
#                                            nonempty                       PORTED
#   frame-mutate-overwrite-s             -> (none)                          VACUOUS
#   frame-mutate-clear-contents          -> (none)                          VACUOUS
#   partial-domain-prefix-empty          -> weak-single-specifier-arity     RE-EXPRESSED
#                                           (the pre-fix selection; its C1 attack
#                                            is the on-carrier analogue of the
#                                            pre-fix text-loss)
#   partial-domain-drop-last             -> weak-selection-varies-with-object
#                                                                           RE-EXPRESSED
#   partial-domain-drop-first            -> (none)                          DROPPED
#   value-mask-right-length-wrong-values -> (none)                          DROPPED
#   ax-invariance-sound                  -> (none)                          G-AX's job
#   ax-invariance-containment            -> (none)                          G-AX's job
#
# 2 ported (the soundness positive and the admissibility positive), 2
# re-expressed (+ 1 positive control and 2 uniqueness rivals ADDED), 2 dropped
# (carrier does not model the text loop), 2 vacuous (frame mutation), 2 axiom
# probes dropped (G-AX's lane).
#
# ADDED — weak-nonempty-keyword-set. The sibling has no counterpart because it
#   does not model the keyword-view at all; on this carrier C2 pins the
#   keyword-name set to empty and is a distinct, load-bearing clause (the fix
#   changes BOTH the arity and the keyword-view), so it needs its own rival. This
#   is the second independent clause of the postcondition and no other case
#   attacks it.
#
# RE-EXPRESSED (partial-domain-drop-last -> weak-selection-varies-with-object).
#   What is portable from the sibling's partial-domain family is not its
#   element-wise text arithmetic but its SHAPE: an impl that is correct on a
#   genuine sub-domain of the input and wrong off it. That shape IS expressible
#   here — branch the selection on the object's own text — and it is the only
#   rival whose rejection is attributable to the input binder. An earlier revision
#   dropped the whole family on the reasoning that `s` was undiscriminable; that
#   was wrong (see the header note) and the audit that found it landed this case.
#   One member of the family is enough: -drop-first and value-mask differ from
#   -drop-last only in WHICH text elements a rebuild loop mishandles, and that
#   distinction has no image here.
# DROPPED (partial-domain-drop-first / value-mask): these attack an element-wise
#   TEXT pin — a reconstruction that drops a particular element or emits wrong
#   values. This bundle keeps `text` only as the object's identity and does not
#   model a text-rebuild loop; there is no such loop to break and no element-wise
#   text clause to violate, so the two rivals collapse onto the sub-domain case
#   above rather than adding a distinct attack. Carrier narrowing, not an omission
#   of convenience — no case was dropped because a proof was hard.
# VACUOUS (frame-mutate-overwrite-s / -clear-contents): the sibling writes to a
#   read-only heap object held at a fractional permission and is rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: `s` is an
#   immutable non-`mut` value, there is no heap, no aliasing, and no permission
#   system to trip. No read-only input to overwrite and no permission to
#   under-hold. No substitute fabricated (per the porting map).
# PORTED (admiss-nonempty-selfcall -> admiss-selection-reachable-at-nonempty).
#   A previous revision recorded this lane as N/A on the reasoning that the method
#   carries no `require` clause (precondition ≡ True), so "there is no precondition
#   to be too strong". That is not a sufficient reason and the audit rejected it:
#   the analogue on a TOTAL carrier is the obligation being UNSATISFIABLE at
#   exactly an F2P-shaped input, which the absent-precondition observation says
#   nothing about. The claim that the two positive controls already cover it is
#   also weaker than it looks — they discharge the obligation at a UNIVERSALLY
#   quantified `s`, which a degenerate obligation provable only by a vacuity the
#   evaluator never exercises would also admit. The lane is now carried: see
#   `admiss-selection-reachable-at-nonempty`, which discharges the obligation's own
#   two clauses BY EVALUATION at a concrete non-empty object before closing the
#   frozen obligation verbatim.
#
# BINDER / CLAUSE COVERAGE. C1 (`applyPos out.kind s (exposedArgs s) = some s`)
#   is attacked by weak-single-specifier-arity; C2 (`applyKw out.kind s
#   out.kwNames = some s`) by weak-nonempty-keyword-set. Each clause has exactly
#   one attacker and one is held fixed while the other is broken, so neither
#   rival's rejection is confounded by the other clause. Both clauses are
#   defended by the two positive controls. The two OUTPUT fields the selection
#   comprises (`out.kind`, `out.kwNames`) are thus each independently varied by
#   the rivals. The INPUT binder `s` is attacked by a third rival,
#   weak-selection-varies-with-object, which breaks BOTH clauses but only on the
#   non-empty-text sub-domain: gold's answer is constant in `s`, yet a wrong
#   impl's need not be, so `s` is a real discriminating dimension and the
#   sub-domain rival is the case that exercises it. C2 additionally carries a
#   second, sharper attacker added by the audit — weak-keyword-set-empty-name,
#   which probes whether C2 pins the keyword-name LIST or merely its content. The
#   four witnesses sit at four distinct `s` values ("a", "b", "c", "d").
#
#   The sub-domain rival's sub-domain is GENUINE, measured rather than argued: its
#   tester at `s.text = ""` does NOT reduce to `false` (the `= false` claim fails
#   there because `decide` proves it is `true`, and the `= true` claim builds), so
#   the rival really does agree with gold on the empty-text sub-domain and is
#   refuted only off it. That is what distinguishes it from a differently-spelled
#   everywhere-wrong rival.
#
# UNIQUENESS, MACHINE-CHECKED (audit, attack D). Beyond the rivals, the two
#   clauses were shown to pin the selection COMPLETELY: assuming only C1 and C2,
#   `out.kind = noArgForm ∧ out.kwNames = []` is provable by
#
#     cases hk : out.kind <;> simp_all [applyPos, applyKw, exposedArgs]
#
#   and that selection does satisfy both clauses (so the postcondition is
#   satisfiable, not degenerate). There is therefore NO wrong selection this spec
#   admits: the `FuncKind × kwNames` space is exhausted, which is what makes the
#   reject lane here complete rather than merely populated.
#
#   A previous revision recorded this tactic WITHOUT the `hk :` name — plain
#   `cases out.kind <;> simp_all [...]`. That spelling does NOT close the goal: a
#   bare `cases` on the projection `out.kind` leaves the two hypotheses still
#   phrased over the un-substituted `out.kind`, so `simp_all` cannot connect the
#   case split to C1/C2 and both branches survive as `unsolved goals`. Re-run
#   during the audit; naming the equation (`hk :`) is what lets `simp_all` rewrite
#   the hypotheses, and only the named form elaborates. Recorded because a claimed
#   proof nobody re-ran is exactly the kind of prose this footer must not carry.
#
# DIVERGENCE / NON-TERMINATION lane: REJECTED BY THE SPEC, measured, deliberately
#   not shipped as a reject case, and NOT a hole. The frozen bundle sets
#   `loom.semantics.termination "total"`, under which a postcondition is claimed of
#   ALL runs and not only of terminating ones, so a diverging impl does not satisfy
#   `ensures` vacuously. Two shapes, both measured:
#     - NO annotation: an impl that returns gold's exact selection after a
#       `while n > 0 do n := n + 1` loop fails to build with `Decreasing
#       annotations are required in total correctness semantics` (exit 1);
#     - ANNOTATION PRESENT BUT FALSE, the sharper shape, so the refusal cannot be
#       read as merely the linter above: `let mut k : Nat := 1` / `while k > 0`
#       with `invariant k > 0`, `done_with k = 0`, `decreasing k`, body
#       `k := k + 1`, spliced at the impl anchor with each proof reduced to a bare
#       `loom_solve`, is REJECTED at exit 1 on the measure's OWN descent goal,
#       `case decreasing_1: k ... |- k + 1 < k`, reported as `unsolved goals`.
#   So the measure is required to be TRUE and not merely present
#   (`TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop` takes
#   `measure : β -> Nat` and emits `measure b' < measure b`; only the
#   `PartialCorrectness` twin takes an `Option ℕ` and DISCARDS it). The class is
#   real, the rival is expressible, and the spec refuses it.
#
#   What is NOT available on this bundle is a WITNESS for it, and that is the
#   reason the case is not carried. The refutation would have to be checked
#   against the diverging rival, and the diverging impl's tester does not reduce:
#   built at a concrete input it fails with
#
#     Tactic `decide` failed ... instDecidableEqBool (reconstructInvarianceTester
#     { text := "d".toList }) false did not reduce to `isTrue` or `isFalse`
#
#   because the un-normalised `forIn Lean.Loop.mk` term is exactly the
#   irreducible shape the gate's `witness-undecided` screen exists to catch. A
#   witness that cannot elaborate against its own rival attributes nothing, and
#   the gate would record the case as inconclusive rather than as a rejection. Nor
#   is a `witness_reference` a way out: the reference must be a VERIFYING impl of
#   the same spec, and the witness must FAIL there — but the claim that fails on a
#   reducing impl is precisely the one that cannot be evaluated on the diverging
#   rival, so the two halves cannot be satisfied by the same statement here.
#
#   Recorded as a limit of what THIS gate can WITNESS, not as a spec hole and not
#   as a vacuous class: the rival is expressible, the verifier rejects it on a real
#   proof obligation, and only the machine-checked refutation is unavailable. The
#   spec-side verdict is REJECT and nothing is escalated; a case whose witness
#   cannot elaborate would make the gate inconclusive, which is why none is
#   shipped. G-VERIFY is the lane in which the termination obligation is
#   discharged.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the `exposedArgs`
#   A-reference (== real `String(...).args == ()`) is validated by axiom_check.py
#   there, and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
