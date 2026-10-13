"""properties.py — G-PBT falsification battery for sympy__sympy-16450 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_posify``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled PARTIAL function):

  implementation_posify (syms : List Assumptions) : Option (List Assumptions)

  Each element of ``syms`` is one symbol's known property record — a list of
  ``(name, value)`` pairs, a property absent when its value is undetermined. The
  routine keeps only the symbols whose sign is undetermined (no ``positive``
  key), and for each such symbol builds the full inferred property record of a
  fresh symbol declared with THE ORIGINAL PROPERTIES AUGMENTED WITH POSITIVITY.
  Declaring a symbol from a property set is PARTIAL — a set that states a
  property twice is not a declaration, and a set whose values cannot hold
  together has no symbol — so the routine has a value only when every
  declaration it FORMS is accepted. The postcondition is therefore two clauses
  read together:

    problem_spec_posify syms result :=
      if h : ∀ a ∈ syms.filter signUndetermined,
               declAccepted (assertPositive a) = true then
        result = some ((syms.filter signUndetermined).pmap
          (fun a ha => resolveAssumptions (assertPositive a) ha) h)
      else
        result = none

  where ``declAccepted decl`` is the TOTAL question "is ``decl`` a property set
  that has a record" and ``resolveAssumptions decl h`` is the inference itself,
  carried as an operation on its DOMAIN (applicable only together with the
  yes-answer ``h``), and ``assertPositive a = ("positive", true) :: a``. The
  clause has these independent, load-bearing dimensions, each attacked by a
  distinct rival below:

    * FILTER — only the sign-undetermined symbols contribute
      (``syms.filter signUndetermined``); including a determined symbol refutes
      it. Attacked by ``nofilter-include-determined``.
    * BASE PRESERVATION — the declared set handed to the engine is the original
      properties, not the empty set; discarding them refutes it. Attacked by
      ``prepatch-empty-base`` (this is the pre-fix behaviour).
    * POSITIVITY — the declared set is augmented with ``positive`` before the
      engine sees it; omitting the augmentation refutes it. Attacked by
      ``wrong-flag-no-positive``.
    * ENGINE IDENTITY / STRUCTURE — each output element IS the engine's record
      for that augmented set; fabricating a record or padding it refutes it.
      Attacked by ``bypass-engine`` and ``spurious-key``.
    * CARDINALITY / ORDER — the result carries exactly ONE element per kept
      symbol, in the input's order (``.filter … |>.pmap``); emitting fewer
      elements, or the right elements in the wrong order, refutes it. Attacked
      by ``drop-later-kept`` and ``reversed-order``. Both need a MULTI-symbol
      input: on a singleton every list of the right elements is trivially of
      the right length and trivially sorted, so neither clause is observable
      there.
    * BASE INTEGRITY — the declared set handed to the engine carries the
      symbol's OWN properties and nothing invented; planting a property the
      symbol never declared refutes it. Attacked by ``inject-base-fact``.
    * DEFINEDNESS (the raise leg) — when a KEPT symbol's augmented declaration
      is refused, the routine has NO VALUE; returning a shortened list instead
      refutes it. Attacked by ``definedness-drop-refused``.
    * DEFINEDNESS SCOPE — definedness is inherited from the declarations the
      routine FORMS, i.e. the kept symbols' only. An implementation whose
      valuedness also depends on the declaration a NOT-replaced symbol would
      give rise to is refuted. Attacked by ``weak-definedness-leak``. This is
      the dimension the earlier revision of this bundle did not have (see
      'AUDIT RECORD' below), and it is the one the recorded attack exploited.

  Input binder of the spec predicate: ``syms``. The reject witnesses vary it
  across distinct records — a FINITE-only symbol, an INTEGER-only symbol, a
  POSITIVE-stating (sign-determined) symbol, and a two-symbol list carrying
  FINITE-only then INTEGER-only — so no dimension is probed at a single fixed
  point, and the length/order clauses are probed at an input where they are
  observable at all. The two definedness cases additionally vary the OPAQUE
  ACCEPTANCE hypothesis (``= false`` rather than ``= true``), which is the only
  way the valueless outcome is reachable at all: no literal input decides an
  opaque predicate.

AUDIT RECORD — what this battery previously failed to catch.

  The earlier revision declared ``resolveAssumptions`` TOTAL
  (``Assumptions → Assumptions``) and the result total
  (``List Assumptions``). Under a total pure oracle ``map`` and ``filter``
  commute, so "apply the oracle to every symbol, select afterwards" is
  propositionally EQUAL to "select, then apply" — and the recorded attack
  ``atk_13`` did exactly that, verified with clean axioms, and refined to a
  patch that raises ``TypeError`` on the first assertion of the F2P test
  (``resolved=False``: F2P ``test_posify`` and P2P ``test_separatevars``
  failing). A sibling record (faithfulness) noted that the total model also
  claimed a value for a sign-undetermined symbol carrying
  ``rational=False, irrational=False``, where the routine has none. Both are one
  defect: the declaration operation is partial, and the battery had no dimension
  for definedness at all — nine rivals, none of which could express it.

  The repaired spec carries the partiality as an operation on its domain, and
  this battery gains the two dimensions above: ``weak-definedness-leak`` (the
  attack's shape: definedness propagated from a symbol that is NOT replaced) and
  ``definedness-drop-refused`` (a refused kept declaration answered with a
  shortened list instead of no value). ``pos-probe-every-symbol`` records, as a
  positive control rather than as silence, what the repaired spec still ADMITS:
  an implementation that ASKS the domain question at every symbol and discards
  the answer where it does not replace. That is behaviour-preserving — the
  faithful Python of "ask" is a probe that completes whichever way it comes out —
  so such a patch resolves, and it must verify.

ADVERSARIAL READ of the nagini classes on THIS carrier (nagini
``properties.py`` is the design document; each nagini rival is re-expressed
against the frozen Lean carrier or explicitly dropped):

  * FRAME / PERMISSION MUTATION (nagini ``frame-mutate-stated``) — PORTED as
    ``inject-base-fact``. The nagini rival WROTE a fabricated fact into the
    symbol's read-only property record before handing it to the engine, to be
    rejected for insufficient permission. The PERMISSION MECHANISM is indeed
    inexpressible here — Lean is referentially transparent, so there is no
    fractional permission to overstep and no aliasing to exploit — but the
    OBSERVABLE the nagini rival was aimed at survives the carrier change
    intact: the engine must be handed the symbol's own properties, not a set
    with an extra fact planted in it. On an immutable carrier that same wrong
    behaviour is written as a functional injection
    (``assertPositive (("finite", true) :: a)``) rather than a mutation, and it
    is refuted by the spec's own clause at an INTEGER-only symbol — the planted
    property changes which declared set reaches the engine, so the resulting
    record differs from the spec's.

  * PREPATCH / EMPTY-BASE (nagini ``prepatch-empty-base``) — PORTED as
    ``prepatch-empty-base``. The rival hands the engine the empty declared set
    plus positivity, dropping the symbol's own properties. This IS the pre-fix
    behaviour and attacks BASE PRESERVATION.

  * WRONG-FLAG (nagini ``wrong-flag-no-positive``) — PORTED as
    ``wrong-flag-no-positive``. The rival carries the original properties but
    omits the positivity augmentation; attacks POSITIVITY.

  * SPURIOUS-KEY INJECTION (nagini ``atk12-spurious-key``) — PORTED as
    ``spurious-key``. The rival takes the engine's real record and pads it with
    a fabricated key the engine never produced; attacks ENGINE IDENTITY /
    STRUCTURE (the padded element is longer than the engine record).

  * FRESH-DICT TOTALITY EVASION (nagini ``fresh-dict-not-engine-map``) — PORTED
    as ``bypass-engine``. The rival returns a hand-rolled record that never
    calls the inference closure; attacks ENGINE IDENTITY.

  * FILTER (new on this carrier) — ``nofilter-include-determined``. The nagini
    bundle modeled only the single-symbol resolve and enforced the
    sign-undetermined domain in its own precondition; the Lean carrier models
    the WHOLE list including the ``syms.filter signUndetermined`` step, so the
    filter is a clause of the modeled postcondition itself. The rival drops the
    filter guard and includes a sign-DETERMINED symbol, refuted by the filter
    clause.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``declAccepted``/``resolveAssumptions``
    are opaque, so a witness cannot compute their values; the refutations that
    turn on them CONDITION on the carrier (an acceptance answer, or
    ``resolveAssumptions X … ≠ resolveAssumptions Y …``, as a hypothesis)
    instead of computing it. Each such hypothesis set is jointly satisfiable
    (checked by the gate's consistency probe: ``False`` is not derivable from
    it).

  * POSITIVE CONTROL (soundness) + ADMISSIBILITY — PORTED (nagini
    ``pos-control-local-base`` / ``admiss-finite-base``). Three
    structurally-different CORRECT impls that must verify, and one ground
    F2P-shaped admissibility probe.

  * CARDINALITY + ORDER (new on this carrier) — ``drop-later-kept`` and
    ``reversed-order``. The nagini bundle modeled ONE symbol's resolve, so
    neither clause existed there; the Lean carrier models the whole list, so
    "one element per kept symbol, in order" is a clause of the modeled
    postcondition. Both stand at a two-symbol input, the only shape where they
    are observable.

  * DEFINEDNESS (new on this carrier, and the audit repair) —
    ``definedness-drop-refused`` and ``weak-definedness-leak``. The nagini
    bundle's contract had a precondition instead of a definedness clause, so
    neither existed there.

  * DIVERGENCE / NON-TERMINATION — VACUOUS ON THIS CARRIER, demonstrated. The
    frozen solution sets no ``loom.semantics.termination`` option at all (it is a
    plain ``import Mathlib`` Lean file, not a loom bundle), so there is no
    termination obligation to fail and no ``partial``/``opaque`` escape a variant
    may take: ``variant_scope`` bans a new ``opaque``, and the frozen
    ``implementation_posify`` is a structural recursion over a ``List``. Both
    diverging shapes were BUILT to check this rather than argued: a
    ``partial def implementation_posify syms := implementation_posify syms``
    and an unguarded non-``partial`` self-call. Both are rejected (exit 1), but
    for reasons that attribute nothing to the SPEC — the ``partial`` one because
    the compiler-introduced constant is opaque to reduction, so every branch of
    the frozen induction is left with the specified value un-derivable
    (``unsolved goals`` at ``case nil`` and ``case pos``, then ``simp made no
    progress``), the plain one because Lean refuses the definition
    outright (``fail to show termination ... no parameters suitable for
    structural recursion``, i.e. the file does not compile). Neither admits a
    witness: the first has no computable projection to refute at, and the second
    is not a well-formed impl to refute at all. So the class is vacuous here, not
    a known hole in the spec — a diverging impl cannot be expressed as an
    admissible same-spec variant on this carrier.

  * AXIOM-SOUNDNESS / CONTAINMENT (nagini ``ax-sound-resolve`` /
    ``ax-contain-resolve``) — OUT OF LANE, not inexpressible. These probe the
    A-reference deep model against the real dependency at runtime, which is
    G-AX/G-CONF's job; the G-PBT spec lane has no runtime oracle (see 'AXIOM
    lane' below). Recorded here so the drop is visible rather than silent.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen induction script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each opens by INTRODUCING the spec
equation as a hypothesis (``intro heq``), then

  * discharges the spec's definedness guard at that input from its own
    acceptance hypotheses (``rw [dif_pos hall] at heq``, or ``dif_neg`` for the
    valueless leg) — a step that holds of ANY impl, gold included;
  * computes the spec's own value there by ``rfl`` (``hspec``: the ``pmap`` over
    the filtered list is a concrete list of engine records);
  * states the RIVAL's value at that input as an unfolding equation
    (``hunf … := rfl``), reduces the rival's own acceptance question, and
    projects the resulting equation — the list HEAD against a carrier hypothesis
    (base/flag/engine/inject/order rivals), the LENGTH (cardinality, padding), or
    a structural clash (``some _ = some []`` / ``none = some []`` for the filter
    and definedness rivals).

The opaque engine is never computed; it remains a symbolic head, which is
exactly what a witness quantifies over.

Each was machine-checked to ELABORATE against its rival and to FAIL against the
frozen solution. That pair alone is NOT sufficient evidence, and this battery
previously failed the stronger test twice over. A gold-side error is admissible
only if it DEPENDS ON THE CLAIM. The superseded shape stated the rival's value as
a standalone reduction (``have hunf ... := rfl``) before projecting; that step is
a claim about the difference between two implementations, so it failed on the
frozen solution regardless of what the witness concluded. Ordering ``intro heq``
first did NOT repair this — gold's failure landed on the ``hunf`` line, which
never mentions ``heq``. Demonstrated by control: with each of those ten
conclusions replaced by ``True``, the file still elaborated against the rival
(exit 0) and still failed against the frozen solution (exit 1) with a byte-
identical error modulo line number. Ten witnesses asserting NOTHING would have
been recorded as ten refutations.

The shape below instead normalises the rival's own definition INTO the introduced
equation (``simp [... implementation_posify ...] at heq``) and reads the
contradiction off the result, so no step is checkable without the claim. The
control is re-run as a gate on the shape: neutering any conclusion to ``True``
breaks the body against the RIVAL too (exit 1). Type-revealed with
``exact (heq : Nat)``, gold's ``heq`` is ``True`` — simp PROVED the spec equation
there — or a residual acceptance hypothesis, while the rival's is a concrete false
equation between distinct opaque records.

Every conditioned witness binds only hypotheses about DISTINCT opaque terms (an
acceptance answer, or a disequality between two engine records), and the gate's
consistency probe confirms ``False`` is not derivable from them. No witness
references a name the rival declares and the frozen solution does not, so no
gold-side failure is an unknown identifier; none is an unfolding failure, a stuck
reduction, or a timeout.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` (the ``resolve``/``derived``
A-reference deep-model soundness + containment probes against real
``sympy.Dummy``/``posify``) belong to G-AX, which the G-PBT spec lane ignores.
The proof of ``correct_posify`` consumes NO property of ``declAccepted`` or
``resolveAssumptions`` (they occur identically in the specification and the
implementation), so there is no axiom-soundness obligation for this gate.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16450"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl or proof region and is
# unique in the file, so every replacement preserves same_spec by construction.
# ---------------------------------------------------------------------------

# The accumulation line of the kept branch: the engine record of the
# positivity-augmented declaration, consed onto the tail's records.
_CONS_LINE = ("        (implementation_posify as).map "
              "(fun rs => resolveAssumptions (assertPositive a) h :: rs)\n")

# The inner `else none`: a refused KEPT declaration leaves the call valueless.
_DECL_ELSE = "      else\n        none\n"

# The domain question + the accumulation + the valueless answer.
_DECL_GUARD = ("      if h : declAccepted (assertPositive a) = true then\n"
               + _CONS_LINE + _DECL_ELSE)

# The whole cons branch (filter guard, kept branch, skipped branch).
_KEEP_BLOCK = ("    if signUndetermined a then\n" + _DECL_GUARD
               + "    else\n      implementation_posify as\n")

# The whole impl body (used by the functional-form positive control).
_IMPL_BLOCK = ("def implementation_posify : List Assumptions → Option (List Assumptions)\n"
               "  | [] => some []\n"
               "  | a :: as =>\n" + _KEEP_BLOCK)

# The frozen proof body of correct_posify (the filter/pmap induction).
_OLD_PROOF = (
    "  intro syms\n"
    "  induction syms with\n"
    "  | nil => simp [problem_spec_posify, implementation_posify]\n"
    "  | cons a as ih =>\n"
    "    unfold problem_spec_posify at ih ⊢\n"
    "    rw [List.filter_cons]\n"
    "    by_cases hs : signUndetermined a = true\n"
    "    · rw [if_pos hs]\n"
    "      by_cases hd : declAccepted (assertPositive a) = true\n"
    "      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,\n"
    "            declAccepted (assertPositive x) = true\n"
    "        · rw [dif_pos ht] at ih\n"
    "          rw [dif_pos (fun x hx => by\n"
    "            rcases List.mem_cons.mp hx with h' | h'\n"
    "            · subst h'; exact hd\n"
    "            · exact ht x h')]\n"
    "          simp [implementation_posify, hs, hd, ih, List.pmap]\n"
    "        · rw [dif_neg ht] at ih\n"
    "          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]\n"
    "          simp [implementation_posify, hs, hd, ih]\n"
    "      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]\n"
    "        simp [implementation_posify, hs, hd]\n"
    "    · rw [if_neg hs]\n"
    "      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]\n"
    "      exact ih\n"
)

assert _BASE.count(_CONS_LINE) == 1, "cons-line anchor drifted from Solution.lean"
assert _BASE.count(_DECL_ELSE) == 1, "decl-else anchor drifted from Solution.lean"
assert _BASE.count(_DECL_GUARD) == 1, "decl-guard anchor drifted from Solution.lean"
assert _BASE.count(_KEEP_BLOCK) == 1, "keep-block anchor drifted from Solution.lean"
assert _BASE.count(_IMPL_BLOCK) == 1, "impl-block anchor drifted from Solution.lean"
assert _BASE.count(_OLD_PROOF) == 1, "proof-body anchor drifted from Solution.lean"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot satisfy the frozen obligation
# the spec is SPEC-TOO-STRONG. Each keeps the `theorem correct_posify` statement
# byte-identical and introduces no helper lemma, axiom, or assumption.
# ---------------------------------------------------------------------------

# pos-local-base: bind the replacement declaration to a local `decl` before
# asking the domain question and before the inference (a data-flow reshape). The
# question asked and the record accumulated are unchanged, so the postcondition
# is unchanged and the frozen proof body still discharges (the local
# zeta-reduces).
_POS_LOCAL = _swap(
    _BASE, _DECL_GUARD,
    "      let decl := assertPositive a\n"
    "      if h : declAccepted decl = true then\n"
    "        (implementation_posify as).map (fun rs => resolveAssumptions decl h :: rs)\n"
    "      else\n"
    "        none\n",
)

# pos-func-map: replace the recursion with the direct dite/pmap form — the same
# function the spec names. The proof collapses to a case split on the guard.
_POS_FUNC = _swap(
    _swap(
        _BASE, _IMPL_BLOCK,
        "def implementation_posify (syms : List Assumptions) : Option (List Assumptions) :=\n"
        "  if h : ∀ a ∈ syms.filter signUndetermined, declAccepted (assertPositive a) = true then\n"
        "    some ((syms.filter signUndetermined).pmap\n"
        "      (fun a ha => resolveAssumptions (assertPositive a) ha) h)\n"
        "  else\n"
        "    none\n",
    ),
    _OLD_PROOF,
    "  intro syms\n"
    "  unfold problem_spec_posify implementation_posify\n"
    "  by_cases h : ∀ a ∈ syms.filter signUndetermined, declAccepted (assertPositive a) = true\n"
    "  · simp only [dif_pos h]\n"
    "  · simp only [dif_neg h]\n",
)

# pos-probe-every-symbol: ASK the domain question at every symbol — including the
# ones the routine does not replace — and discard the answer where it does not.
# This is what the repaired spec still admits, and it is behaviour-preserving:
# the faithful Python of "ask" is a probe that completes whichever way it comes
# out, so the corresponding patch resolves. Shipped as a positive control rather
# than left undocumented; it MUST verify (the frozen proof body is retained).
_POS_PROBE = _swap(
    _BASE, _KEEP_BLOCK,
    "    let probe := if h : declAccepted (assertPositive a) = true then\n"
    "        some (resolveAssumptions (assertPositive a) h) else none\n"
    "    if signUndetermined a then\n"
    "      match probe with\n"
    "      | some r => (implementation_posify as).map (fun rs => r :: rs)\n"
    "      | none => none\n"
    "    else\n"
    "      implementation_posify as\n",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the modeled behavior is exhibited as SATISFIED at a ground,
# F2P-shaped input (a single FINITE-only symbol, the exact issue example) with a
# concrete value, as an `example` appended inside the proof region; the frozen
# obligation is closed verbatim alongside it. If that ground instance could not
# be discharged, the modeled behavior would be unsatisfiable at exactly the shape
# the F2P exercises — the analogue of PRECOND-TOO-STRONG. The frozen theorem
# carries no precondition hypothesis (only the definedness guard, which the
# `example` discharges from the acceptance of that one declaration), so this
# ground-instance form is the honest analogue of the nagini precondition-
# admission probe. Nothing is assumed beyond the acceptance answer: no new
# theorem/lemma, the statement is byte-identical, and the value is computed by
# `rfl`.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE, _OLD_PROOF,
    _OLD_PROOF
    + "\n"
    "example (hd : declAccepted (assertPositive [(\"finite\", true)]) = true) :\n"
    "    problem_spec_posify [[(\"finite\", true)]]\n"
    "      (some [resolveAssumptions (assertPositive [(\"finite\", true)]) hd]) := by\n"
    "  have hf : List.filter signUndetermined ([[(\"finite\", true)]] : List Assumptions)\n"
    "      = [[(\"finite\", true)]] := rfl\n"
    "  have hall : ∀ a ∈ List.filter signUndetermined ([[(\"finite\", true)]] : List Assumptions),\n"
    "      declAccepted (assertPositive a) = true := by\n"
    "    intro a ha\n"
    "    rw [hf] at ha\n"
    "    have ha' : a = [(\"finite\", true)] := by simpa using ha\n"
    "    rw [ha']\n"
    "    exact hd\n"
    "  unfold problem_spec_posify\n"
    "  rw [dif_pos hall]\n"
    "  have hspec : (List.filter signUndetermined "
    "([[(\"finite\", true)]] : List Assumptions)).pmap\n"
    "      (fun a ha => resolveAssumptions (assertPositive a) ha) hall\n"
    "      = [resolveAssumptions (assertPositive [(\"finite\", true)]) hd] := rfl\n"
    "  rw [hspec]\n",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each ships the FROZEN proof body verbatim (a `sorry` would
# violate variant scope), so its rejection is the frozen script failing against
# the reshaped impl — which is exactly why the WITNESS, not the rejection,
# attributes the failure to the spec.
# ---------------------------------------------------------------------------

# prepatch-empty-base: hand the engine the empty declared set + positivity,
# discarding the symbol's own properties. THE PRE-FIX BEHAVIOUR. The domain
# question is asked of that same bare declaration, as the pre-fix code asks it.
_RIVAL_PREPATCH = _swap(
    _BASE, _DECL_GUARD,
    "      if h : declAccepted [(\"positive\", true)] = true then\n"
    "        (implementation_posify as).map "
    "(fun rs => resolveAssumptions [(\"positive\", true)] h :: rs)\n"
    "      else\n"
    "        none\n",
)

# wrong-flag-no-positive: carry the original properties but omit the positivity
# augmentation (the engine never sees `positive`).
_RIVAL_WRONGFLAG = _swap(
    _BASE, _DECL_GUARD,
    "      if h : declAccepted a = true then\n"
    "        (implementation_posify as).map (fun rs => resolveAssumptions a h :: rs)\n"
    "      else\n"
    "        none\n",
)

# spurious-key: take the engine's real record and pad it with a fabricated key.
_RIVAL_SPURIOUS = _swap(
    _BASE, _CONS_LINE,
    "        (implementation_posify as).map (fun rs =>\n"
    "          (resolveAssumptions (assertPositive a) h ++ [(\"finite\", true)]) :: rs)\n",
)

# nofilter-include-determined: drop the sign-undetermined guard, so a determined
# symbol also gets a replacement (and also contributes its declaration to the
# definedness).
_RIVAL_NOFILTER = _swap(
    _BASE, _KEEP_BLOCK,
    "    if h : declAccepted (assertPositive a) = true then\n"
    "      (implementation_posify as).map "
    "(fun rs => resolveAssumptions (assertPositive a) h :: rs)\n"
    "    else\n"
    "      none\n",
)

# bypass-engine: return a hand-rolled record that never calls the inference.
_RIVAL_BYPASS = _swap(
    _BASE, _CONS_LINE,
    "        (implementation_posify as).map (fun rs => [(\"positive\", true)] :: rs)\n",
)

# inject-base-fact: plant a property the symbol never declared into the declared
# set handed to the engine (the immutable-carrier form of the nagini frame
# rival), and ask the domain question of that planted declaration.
_RIVAL_INJECT = _swap(
    _BASE, _DECL_GUARD,
    "      if h : declAccepted (assertPositive ((\"finite\", true) :: a)) = true then\n"
    "        (implementation_posify as).map (fun rs =>\n"
    "          resolveAssumptions (assertPositive ((\"finite\", true) :: a)) h :: rs)\n"
    "      else\n"
    "        none\n",
)

# drop-later-kept: emit only the FIRST kept symbol's record — the tail's records
# are computed (so definedness is unchanged) and then discarded (CARDINALITY).
_RIVAL_DROPLATER = _swap(
    _BASE, _CONS_LINE,
    "        (implementation_posify as).map "
    "(fun _ => [resolveAssumptions (assertPositive a) h])\n",
)

# reversed-order: accumulate by appending, so the kept symbols' records come out
# in reverse input order (ORDER).
_RIVAL_REVERSED = _swap(
    _BASE, _CONS_LINE,
    "        (implementation_posify as).map "
    "(fun rs => rs ++ [resolveAssumptions (assertPositive a) h])\n",
)

# definedness-drop-refused: a KEPT symbol whose augmented declaration is refused
# is answered with a shortened list instead of no value (DEFINEDNESS, raise leg).
_RIVAL_DROPREFUSED = _swap(
    _BASE, _DECL_ELSE,
    "      else\n"
    "        some []\n",
)

# weak-definedness-leak: ask the domain question at EVERY symbol and PROPAGATE
# the answer, selecting only afterwards. The values are right; the definedness is
# not — it now depends on declarations the routine never forms. This is the
# recorded attack's shape (map-then-filter) written in the frozen vocabulary.
_RIVAL_LEAK = _swap(
    _BASE, _KEEP_BLOCK,
    "    if h : declAccepted (assertPositive a) = true then\n"
    "      (implementation_posify as).map (fun rs =>\n"
    "        if signUndetermined a then resolveAssumptions (assertPositive a) h :: rs else rs)\n"
    "    else\n"
    "      none\n",
)


# ---- witnesses ------------------------------------------------------------
#
# SHAPE, and why it is this shape. Every witness INTRODUCES the spec equation at
# one concrete input (`intro heq`), unfolds the spec there, discharges the
# definedness guard from its own acceptance hypotheses (`dif_pos`/`dif_neg` — a
# step that holds of ANY impl, gold included), and then normalises the RIVAL'S OWN
# DEFINITION INTO that hypothesis with `simp [... implementation_posify ...] at
# heq`. The contradiction is read off the normalised hypothesis.
#
# What this shape avoids, and why it matters. A witness must not contain any step
# that is checkable WITHOUT the introduced equation. An earlier revision of this
# battery stated the rival's value as a standalone reduction
#
#     have hunf : implementation_posify <input> = <rival value> := rfl
#
# which is a claim about the DIFFERENCE BETWEEN TWO IMPLEMENTATIONS, not about
# what the witness concludes. It type-checks against the rival and fails against
# the frozen solution on its own, so gold's exit code was determined before the
# conclusion was ever reached. Measured on this cell: replacing the conclusion of
# each of those ten witnesses with `True` — asserting NOTHING — still elaborated
# against the rival (exit 0) and still failed against the frozen solution (exit 1)
# with an error byte-identical modulo line number to the real witness's. All ten
# would have been recorded as refutations by a file that claimed nothing. It is
# NOT sufficient that `intro heq` come first: gold's failure landed on the `hunf`
# line, which never mentions `heq`, so ordering the tactics did not make the
# failure depend on the claim.
#
# The control every witness below passes: neuter the conclusion to `True` and the
# body no longer compiles against the RIVAL either (exit 1), because every step
# after `intro heq` consumes the introduced equation. Discrimination therefore
# cannot survive the removal of the claim. Type-revealed with `exact (heq : Nat)`,
# gold's `heq` normalises to `True` (simp PROVED the spec equation there) or to a
# residual acceptance hypothesis, while the rival's is a concrete false equation
# between distinct opaque records — so gold's failure is semantic, not a missing
# identifier, an unfolding failure, or a timeout.
#
# No witness references a name the rival declares and the frozen solution does
# not, and each conditioned witness binds only hypotheses about DISTINCT opaque
# terms, so the gate's consistency probe is meaningful and passes.

# prepatch: at a FINITE-only symbol the rival hands the engine the bare positivity
# declaration where the spec hands it positive+finite, so normalising the spec
# equation leaves those two opaque records EQUATED. Conditioned on both
# declarations being accepted and on the records differing (jointly satisfiable).
_WIT_PREPATCH = """example (hacc : declAccepted [("positive", true)] = true)
    (hd : declAccepted [("positive", true), ("finite", true)] = true)
    (h : ∀ h1 h2, resolveAssumptions [("positive", true)] h1
        ≠ resolveAssumptions [("positive", true), ("finite", true)] h2) :
    ¬ problem_spec_posify [[("finite", true)]]
      (implementation_posify [[("finite", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha; subst ha; exact hd)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hacc] at heq
  exact h _ _ heq
"""

# wrong-flag: at an INTEGER-only symbol the engine never sees `positive`, so the
# normalised spec equation equates the record of [integer] with the record of
# [positive,integer]. Conditioned on that difference.
_WIT_WRONGFLAG = """example (hacc : declAccepted [("integer", true)] = true)
    (hd : declAccepted [("positive", true), ("integer", true)] = true)
    (h : ∀ h1 h2, resolveAssumptions [("integer", true)] h1
        ≠ resolveAssumptions [("positive", true), ("integer", true)] h2) :
    ¬ problem_spec_posify [[("integer", true)]]
      (implementation_posify [[("integer", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha; subst ha; exact hd)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hacc] at heq
  exact h _ _ heq
"""

# spurious: at a FINITE-only symbol the rival's element is the engine record padded
# by one pair, so the normalised spec equation asserts `record ++ [pair] = record`,
# which simp refutes by LENGTH. Only the one acceptance is assumed.
_WIT_SPURIOUS = """example (hd : declAccepted [("positive", true), ("finite", true)] = true) :
    ¬ problem_spec_posify [[("finite", true)]]
      (implementation_posify [[("finite", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha; subst ha; exact hd)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify] at heq
"""

# nofilter: at a POSITIVE-stating (sign-DETERMINED) symbol the spec's result is
# `some []` (the filter keeps nothing, so the guard holds vacuously) while the rival
# still forms that symbol's declaration and yields `some [record]`; the normalised
# equation is a structural clash simp closes.
_WIT_NOFILTER = """example (hacc : declAccepted [("positive", true), ("positive", true)] = true) :
    ¬ problem_spec_posify [[("positive", true)]]
      (implementation_posify [[("positive", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hacc] at heq
"""

# bypass: at a FINITE-only symbol the rival's element is a hand-rolled constant
# where the spec's is the engine record; conditioned on those differing.
_WIT_BYPASS = """example (hd : declAccepted [("positive", true), ("finite", true)] = true)
    (h : ∀ h1, resolveAssumptions [("positive", true), ("finite", true)] h1
        ≠ [("positive", true)]) :
    ¬ problem_spec_posify [[("finite", true)]]
      (implementation_posify [[("finite", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha; subst ha; exact hd)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hd] at heq
  exact h _ heq.symm
"""

# inject: at an INTEGER-only symbol the rival resolves a declaration carrying a
# planted property, so the normalised equation equates the record of
# [positive,finite,integer] with that of [positive,integer]. Conditioned on that.
_WIT_INJECT = """example (hacc : declAccepted [("positive", true), ("finite", true), ("integer", true)] = true)
    (hd : declAccepted [("positive", true), ("integer", true)] = true)
    (h : ∀ h1 h2, resolveAssumptions [("positive", true), ("finite", true), ("integer", true)] h1
        ≠ resolveAssumptions [("positive", true), ("integer", true)] h2) :
    ¬ problem_spec_posify [[("integer", true)]]
      (implementation_posify [[("integer", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha; subst ha; exact hd)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hacc] at heq
  exact h _ _ heq
"""

# drop-later: at a TWO-symbol input (both kept) the rival emits one element where
# the spec demands two, so the normalised equation is a length clash simp closes.
# Not observable at a singleton input, hence the two-element binder.
_WIT_DROPLATER = """example (hd1 : declAccepted [("positive", true), ("finite", true)] = true)
    (hd2 : declAccepted [("positive", true), ("integer", true)] = true) :
    ¬ problem_spec_posify [[("finite", true)], [("integer", true)]]
      (implementation_posify [[("finite", true)], [("integer", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by
    intro a ha; simp [signUndetermined] at ha
    rcases ha with h' | h' <;> subst h' <;> [exact hd1; exact hd2])] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hd1, dif_pos hd2] at heq
"""

# reversed: at the same TWO-symbol input the rival emits the right records in the
# wrong order, so the normalised equation equates the first symbol's record with the
# second's. Conditioned on those differing. Invisible at a singleton input.
_WIT_REVERSED = """example (hd1 : declAccepted [("positive", true), ("finite", true)] = true)
    (hd2 : declAccepted [("positive", true), ("integer", true)] = true)
    (h : ∀ h1 h2, resolveAssumptions [("positive", true), ("finite", true)] h1
        ≠ resolveAssumptions [("positive", true), ("integer", true)] h2) :
    ¬ problem_spec_posify [[("finite", true)], [("integer", true)]]
      (implementation_posify [[("finite", true)], [("integer", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by
    intro a ha; simp [signUndetermined] at ha
    rcases ha with h' | h' <;> subst h' <;> [exact hd1; exact hd2])] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_pos hd1, dif_pos hd2] at heq
  exact h _ _ heq.2
"""

# definedness-drop-refused: at a FINITE-only symbol whose augmented declaration is
# REFUSED the spec demands `none` while the rival answers `some []`. Conditioned on
# the refusal — the only way the valueless outcome is reachable, since no literal
# input decides an opaque question.
_WIT_DROPREFUSED = """example (hb : declAccepted [("positive", true), ("finite", true)] ≠ true) :
    ¬ problem_spec_posify [[("finite", true)]]
      (implementation_posify [[("finite", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_neg (by
    intro H; exact hb (H [("finite", true)] (by simp [signUndetermined])))] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, implementation_posify,
        dif_neg hb] at heq
"""

# leak: at a POSITIVE-stating symbol (NOT replaced, so the routine forms no
# declaration for it) the spec's result is `some []` whatever that symbol's would-be
# declaration answers; the rival asks anyway and PROPAGATES, so where it is refused
# the rival has `none`. THIS IS THE RECORDED ATTACK'S DEFECT.
_WIT_LEAK = """example (hb : declAccepted [("positive", true), ("positive", true)] ≠ true) :
    ¬ problem_spec_posify [[("positive", true)]]
      (implementation_posify [[("positive", true)]]) := by
  intro heq
  unfold problem_spec_posify at heq
  rw [dif_pos (by intro a ha; simp [signUndetermined] at ha)] at heq
  unfold implementation_posify at heq
  simp [signUndetermined, assertPositive, List.pmap, implementation_posify,
        dif_neg hb] at heq
"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-local-base",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": "Structurally-different CORRECT impl: the replacement "
                     "declaration is bound to a local `decl` before the domain "
                     "question is asked and before the inference (data-flow "
                     "reshape). The question asked and the record accumulated are "
                     "unchanged, so both halves of the postcondition (definedness "
                     "scoped to the kept declarations; the in-order engine "
                     "records) still hold; must verify (else SPEC-TOO-STRONG — a "
                     "faithful correct impl rejected). The frozen proof body is "
                     "retained verbatim (the local zeta-reduces).",
    },
    {
        "id": "pos-func-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNC,
        "rationale": "Structurally-different CORRECT impl: the recursion is "
                     "replaced by the direct dite/pmap form the spec names. "
                     "Denotationally identical, so the postcondition is "
                     "unchanged; must verify (else SPEC-TOO-STRONG). The proof "
                     "becomes a case split on the definedness guard — no new "
                     "lemma, axiom, or assumption, and the `correct_posify` "
                     "statement is byte-identical.",
    },
    {
        "id": "pos-probe-every-symbol",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PROBE,
        "rationale": "The impl ASKS the domain question at EVERY symbol, "
                     "including the ones it does not replace, and discards the "
                     "answer where it does not replace. This is what the spec "
                     "still admits, and it is behaviour-preserving: the faithful "
                     "Python of 'ask' is a probe that completes whichever way it "
                     "comes out (it does not raise), so the corresponding patch "
                     "resolves. Must verify — rejecting it would make the spec "
                     "SPEC-TOO-STRONG about an unobservable evaluation order. It "
                     "is shipped as a positive control precisely so this residual "
                     "admission is recorded rather than silent; contrast "
                     "`weak-definedness-leak`, which PROPAGATES the answer instead "
                     "of discarding it and is refuted.",
    },
    # =====================================================================
    # ADMISSIBILITY
    # =====================================================================
    {
        "id": "admiss-finite-base",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "The modeled behavior is exhibited as SATISFIED at a ground "
                     "F2P-shaped input (a single FINITE-only symbol — the exact "
                     "issue example) by a concrete value, as an `example` "
                     "appended inside the proof region; the frozen obligation is "
                     "closed verbatim alongside it. Verifies (else the modeled "
                     "behavior would be unsatisfiable at the shape the F2P "
                     "exercises — the analogue of PRECOND-TOO-STRONG, and in "
                     "particular a definedness guard nothing could discharge). "
                     "Nothing is assumed beyond that one declaration's acceptance: "
                     "no new theorem/lemma, the statement is byte-identical, and "
                     "the value is computed by `rfl`.",
    },
    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "prepatch-empty-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PREPATCH,
        "refinement": "This IS the pre-fix behaviour: the engine is handed only "
                      "the positivity declaration, discarding the symbol's own "
                      "declared properties (and the domain question is asked of "
                      "that bare declaration, as the pre-fix code asks it). A "
                      "faithful real patch that omits the original property set "
                      "makes the replacement symbol lose every stated property "
                      "(e.g. finiteness), so the added F2P whole-record equality "
                      "on the finite symbol FAILS -> the instance is NOT resolved. "
                      "A verifying rival would be a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from the BASE-PRESERVATION dimension: the engine "
                     "record must be built from the symbol's properties augmented "
                     "with positivity, but this rival uses the empty set. Witness "
                     "reduces the rival at a FINITE-only symbol to the record of "
                     "[positive] and the spec's value to the record of "
                     "[positive,finite], then derives the contradiction from the "
                     "hypothesis that those two opaque records differ; it fails "
                     "on gold (whose element IS the [positive,finite] record). "
                     "Varies the `syms` binder (a FINITE-only record).",
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "wrong-flag-no-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_WRONGFLAG,
        "refinement": "The rival carries the original properties but never adds "
                      "positivity, so the engine sees the un-augmented set. A "
                      "faithful real patch that forgot the positivity assertion "
                      "would leave the replacement symbol's sign undetermined — "
                      "posify's whole purpose is the positive stand-in — so its "
                      "record would lack `positive: True` and the F2P record "
                      "equality FAILS -> NOT resolved.",
        "rationale": "REJECT from the POSITIVITY dimension: the declared set must "
                     "be augmented with `positive` before the engine sees it. "
                     "Witness reduces the rival at an INTEGER-only symbol to the "
                     "record of [integer] and the spec's value to the record of "
                     "[positive,integer], then derives the contradiction from the "
                     "hypothesis that those two opaque records differ; it fails "
                     "on gold. Varies the `syms` binder (an INTEGER-only record, "
                     "distinct from the FINITE inputs).",
        "witness": _WIT_WRONGFLAG,
    },
    {
        "id": "spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SPURIOUS,
        "refinement": "The rival takes the engine's real record and pads it with "
                      "a key the engine never produced. A faithful real patch "
                      "that forced an extra property onto the replacement symbol "
                      "would make its full record differ from a freshly built "
                      "symbol's, so the F2P whole-record equality FAILS -> NOT "
                      "resolved (and a fabricated property can be inconsistent).",
        "rationale": "REJECT from the ENGINE-IDENTITY/STRUCTURE dimension: each "
                     "output element must BE the engine record, not a padded "
                     "copy. Witness reduces the rival at a FINITE-only symbol so "
                     "its single element is the engine record appended with one "
                     "extra pair, while the spec's element is the bare engine "
                     "record; refuted by the element LENGTH (strictly longer), no "
                     "disequality hypothesis needed. Fails on gold. Varies the "
                     "`syms` binder (a FINITE-only record).",
        "witness": _WIT_SPURIOUS,
    },
    {
        "id": "nofilter-include-determined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NOFILTER,
        "refinement": "The rival drops the sign-undetermined guard, so a symbol "
                      "whose sign is ALREADY determined also gets replaced. A "
                      "faithful real patch that replaced every symbol rather than "
                      "only the sign-undetermined ones would rewrite symbols the "
                      "routine must leave untouched, changing the returned set on "
                      "the pre-existing posify tests -> NOT resolved (and, for a "
                      "symbol that already states positivity, the declaration it "
                      "forms is not one the constructor accepts at all).",
        "rationale": "REJECT from the FILTER dimension: only sign-undetermined "
                     "symbols contribute (syms.filter signUndetermined). Witness "
                     "at a POSITIVE-stating (determined) symbol: the spec's value "
                     "is `some []` (the filter keeps nothing, so the definedness "
                     "guard holds vacuously) while the rival's value is "
                     "`some [record]` or `none` depending on an opaque acceptance "
                     "— and BOTH clash with `some []`, so the witness is "
                     "unconditional (it case-splits and refutes either way). "
                     "Fails on gold. Varies the `syms` binder (a POSITIVE-stating "
                     "record — a third distinct input).",
        "witness": _WIT_NOFILTER,
    },
    {
        "id": "bypass-engine",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_BYPASS,
        "refinement": "The rival returns a hand-rolled record that never calls "
                      "the inference closure, so it lacks the engine's closure "
                      "(real/finite/nonnegative/... and the stated facts). A "
                      "faithful real patch that hard-coded the replacement's "
                      "record instead of building a fresh symbol would miss the "
                      "inferred properties, so the F2P whole-record equality "
                      "FAILS -> NOT resolved.",
        "rationale": "REJECT from the ENGINE-IDENTITY dimension: each element "
                     "must be the engine record `resolveAssumptions (...) h`, not "
                     "a constant. Witness reduces the rival at a FINITE-only "
                     "symbol to the hand-rolled [[positive]] and the spec's value "
                     "to the engine record of [positive,finite], then derives the "
                     "contradiction from the hypothesis that the engine record "
                     "differs from the hand-rolled one; it fails on gold. Varies "
                     "the `syms` binder (a FINITE-only record). Note the rival "
                     "still ASKS the domain question, so its definedness matches "
                     "the spec's — only the value is wrong, which is what makes "
                     "this a clean single-dimension probe.",
        "witness": _WIT_BYPASS,
    },
    {
        "id": "inject-base-fact",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_INJECT,
        "refinement": "The rival plants a property the symbol never declared "
                      "into the declared set handed to the engine, so the "
                      "replacement is built from a set the original symbol does "
                      "not have. A faithful real patch that seeded the "
                      "replacement's declaration with an invented property would "
                      "give it a record no freshly built symbol with the symbol's "
                      "OWN properties carries, so the F2P whole-record equality "
                      "FAILS -> NOT resolved (and an invented property can "
                      "contradict the symbol's real ones).",
        "rationale": "REJECT from the BASE-INTEGRITY dimension: the declared set "
                     "must be the symbol's own properties augmented with "
                     "positivity and NOTHING else. This is the immutable-carrier "
                     "port of the nagini frame-mutation rival — the permission "
                     "encoding does not survive the carrier change but the "
                     "observable does, written as a functional injection instead "
                     "of a write. Witness reduces the rival at an INTEGER-only "
                     "symbol to the record of [positive,finite,integer] and the "
                     "spec's value to the record of [positive,integer], then "
                     "derives the contradiction from the hypothesis that those "
                     "two opaque records differ; it fails on gold. Varies the "
                     "`syms` binder (an INTEGER-only record).",
        "witness": _WIT_INJECT,
    },
    {
        "id": "drop-later-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROPLATER,
        "refinement": "The rival replaces only the FIRST sign-undetermined "
                      "symbol and leaves every later one alone (it still asks the "
                      "later declarations' questions, so its definedness is "
                      "unchanged — only the records are dropped). A faithful real "
                      "patch that built a replacement for just one of the "
                      "expression's sign-undetermined symbols would leave the "
                      "others un-substituted, so a multi-symbol expression comes "
                      "back still carrying sign-undetermined symbols and the "
                      "returned replacement map is short -> the pre-existing "
                      "multi-symbol tests of this routine FAIL -> NOT resolved.",
        "rationale": "REJECT from the CARDINALITY dimension: the result carries "
                     "exactly one element per kept symbol. Witness stands at a "
                     "TWO-symbol input (FINITE-only then INTEGER-only, both kept) "
                     "where the rival emits one element and the spec demands two; "
                     "refuted by LENGTH, with no disequality hypothesis (only the "
                     "two acceptances, which the spec's own value needs). Fails "
                     "on gold. This clause is NOT observable at a singleton input "
                     "— every list of the right elements is then trivially the "
                     "right length — which is why this case varies the `syms` "
                     "binder to a two-element list.",
        "witness": _WIT_DROPLATER,
    },
    {
        "id": "reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_REVERSED,
        "refinement": "The rival accumulates by appending, so it emits exactly "
                      "the right records in reverse input order. A faithful real "
                      "patch whose replacement records came back transposed "
                      "relative to the symbols they belong to would pair each "
                      "symbol with another symbol's stand-in, so every symbol is "
                      "substituted by the wrong replacement and the returned "
                      "inverse map is wrong -> NOT resolved.",
        "rationale": "REJECT from the ORDER dimension: the result is the pmapped "
                     "FILTERED list, so element i is the i-th kept symbol's "
                     "record. Witness stands at the same TWO-symbol input, where "
                     "the rival's head is the SECOND symbol's record while the "
                     "spec's head is the first's; the contradiction follows from "
                     "the hypothesis that those two opaque records differ (jointly "
                     "satisfiable). Fails on gold. Like the cardinality clause "
                     "this is invisible at a singleton input, where any "
                     "one-element list is trivially in order. HONESTY NOTE: this "
                     "rival is a REORDERING, so it is wrong only because the "
                     "frozen spec pins the result to the pmapped filtered list, "
                     "whereas mapping.md records the per-symbol order as NOT "
                     "observable in the real system (the replacements are compared "
                     "as a multiset). Its rejection therefore attests that the "
                     "LEAN spec is order-sensitive, not that a transposed real "
                     "patch is refuted by the F2P — it is kept as an honest probe "
                     "of a clause the frozen spec really does assert, and is "
                     "labelled rather than credited as a behavioural rival. See "
                     "'assessment'.",
        "witness": _WIT_REVERSED,
    },
    {
        "id": "definedness-drop-refused",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROPREFUSED,
        "refinement": "The rival answers a REFUSED kept declaration with a "
                      "shortened list instead of no value. A faithful real patch "
                      "of that shape would have to swallow the exception the "
                      "constructor raises and return an expression with some "
                      "sign-undetermined symbols left un-substituted together "
                      "with an incomplete inverse map — a value where the patched "
                      "routine has none, so the caller (`separatevars`, "
                      "`solve`, ...) proceeds on a half-substituted expression. "
                      "That is a different routine from the one the patch "
                      "produces, and the P2P suite pins the raising behaviour: "
                      "NOT resolved.",
        "rationale": "REJECT from the DEFINEDNESS dimension (the raise leg): when "
                     "a kept symbol's augmented declaration is refused the "
                     "routine has NO VALUE. Witness stands at a FINITE-only "
                     "symbol with that declaration's acceptance hypothesised "
                     "FALSE — the only way the valueless outcome is reachable, "
                     "since no literal input decides an opaque question — where "
                     "the spec demands `none` and the rival answers `some []`. "
                     "Fails on gold (whose value there IS `none`). This dimension "
                     "did not exist in the earlier revision of this bundle, whose "
                     "model was total; it is the clause the faithfulness finding "
                     "was about.",
        "witness": _WIT_DROPREFUSED,
    },
    {
        "id": "weak-definedness-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LEAK,
        "refinement": "This is the recorded attack, in the frozen vocabulary: ask "
                      "the domain question at every symbol, PROPAGATE the answer, "
                      "and select only afterwards. Its values are exactly the "
                      "spec's; its definedness is not — it inherits from "
                      "declarations the routine never forms. The faithful Python "
                      "is the one that broke: build the replacement for every "
                      "free symbol and filter afterwards, which forms "
                      "`Dummy(name, positive=True, **s.assumptions0)` for a "
                      "symbol whose record ALREADY states positivity, so the call "
                      "gets that keyword twice and raises `TypeError` on the "
                      "first assertion of the F2P test -> NOT resolved (F2P "
                      "test_posify and P2P test_separatevars both failing, as "
                      "measured on the attack that this repair closes).",
        "rationale": "REJECT from the DEFINEDNESS-SCOPE dimension: definedness is "
                     "inherited from the declarations the routine FORMS — the kept "
                     "symbols' only — so the acceptance of a declaration formed "
                     "from a symbol that is NOT replaced cannot influence the "
                     "outcome in either direction. Witness stands at a "
                     "POSITIVE-stating symbol (not replaced) with that symbol's "
                     "would-be declaration hypothesised REFUSED: the spec demands "
                     "`some []` and the rival has `none`. Fails on gold. THIS IS "
                     "THE CASE THE EARLIER REVISION COULD NOT EXPRESS: with a "
                     "total oracle, 'probe every symbol then select' is "
                     "propositionally equal to 'select then probe', so this rival "
                     "VERIFIED there while its patch did not resolve. Contrast "
                     "`pos-probe-every-symbol`, which asks the same questions but "
                     "DISCARDS the answers it does not use and is admitted.",
        "witness": _WIT_LEAK,
    },
]
