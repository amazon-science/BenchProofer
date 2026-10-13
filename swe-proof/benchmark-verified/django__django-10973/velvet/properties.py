"""properties.py — G-PBT falsification battery for django__django-10973 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct passwordEnvValue`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the named ``witness_reference`` — a VERIFYING impl of this same spec, used here
in place of the frozen solution for the measured reason under WITNESS SUBJECT
below).

DEFENDED SURFACE (one contracted method):

  passwordEnvValue (passwd : List Char) return (out : List Char)
    ensures out = passwd
    ensures (out.length > 0) = (passwd.length > 0)

The operation hands a connection password to a child process through a
dedicated mechanism. The value exposed for the password is the password itself,
VERBATIM: element i of the exposed value is code point i of the input, for every
position. Two independent top-level ``ensures`` clauses:
  (Q1) ``out = passwd``                               — verbatim, no transform.
  (Q2) ``(out.length > 0) = (passwd.length > 0)``     — populated iff non-empty.
Q1 is the load-bearing clause (it already forces Q2, but Q2 is stated
independently and any rival must meet it too). Both are grounded ENTIRELY in the
sole input binder ``passwd`` — there is no opaque oracle to echo (the ``axioms``
and ``pure`` regions are empty), so the unique satisfier IS the password.

ADVERSARIAL READ of the sibling's classes:
  * FRAME-MUTATION — VACUOUS on this backend, and DEMONSTRATED so rather than
    argued. The sibling's mandatory frame-mutation rival writes back into a
    read-only input that carries only a fractional heap permission, and is
    rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: ``passwd`` is an immutable value, this bundle declares no
    ``mut`` parameter, there is no heap and no aliasing. Measured, two builds:
    a rival whose impl region assigns to the parameter (``passwd := []``) does
    not even ELABORATE — ```passwd` cannot be mutated, only variables declared
    using `let mut` can be mutated`` — so the write is a parse-level
    impossibility, not a spec obligation; and a rival that mutates a local copy
    (``let mut p := passwd; p := []``) and then exposes ``passwd`` VERIFIES
    (exit 0), because the input is unreachable from any store. So there is no
    read-only input to overwrite and no permission system to trip. No substitute
    is fabricated; a case in this class would either fail to parse (attesting to
    Velvet's grammar, not to this spec) or pass while testing nothing.
    (See footer.)
  * UNGROUNDED-ORACLE ECHO — N/A. Q1 pins ``out`` to ``passwd`` itself, grounded
    in the sole input; there is no answer-key term a wrong impl could echo. The
    cheapest correct impl simply returns the input, which the positive controls
    cover honestly.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: a rival
    that copies the password verbatim EXCEPT it re-applies a legacy per-code-
    point quoting (colon, backslash) is correct on every quote-free password and
    diverges only on the special code points; an off-by-one truncation is
    correct only on the empty password; the always-empty baseline meets Q1/Q2
    only on the empty password.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict.
The five witnesses sit at five DISTINCT input points and vary the sole binder
``passwd`` — a colon password, a backslash password, two distinct one-character
passwords, and the EMPTY password — so both clauses are attacked and neither is
demonstrated at a single pinned point. The colon and backslash witnesses probe
the Q1 verbatim clause on the two special-code-point sub-domains; the one-char
witnesses (drop-first, always-empty) additionally probe Q2 (a non-empty password
yielding an empty exposed value); the empty-password witness probes the boundary
the other four leave uncovered, where Q1 and Q2 both hold of every rival above.

WITNESS SUBJECT — MEASURED, and it is the substance of every rejection here.
The FROZEN impl cannot decide any of these witnesses. Its ``while`` loop under
``loom.semantics.choice "demonic"`` elaborates through ``Classical.choice``, so
``decide`` on ``passwordEnvValueTester`` gets stuck against it for EVERY claim,
regardless of truth::

    Tactic `decide` failed for proposition passwordEnvValueTester "a:b".toList
    = false ... did not reduce to `isTrue` or `isFalse`

Verified as carrying no information by the flipped-claim experiment: the SAME
witness with ``= true`` substituted (i.e. asserting the exposed value is CORRECT
at that input, the opposite of a refutation) fails against the frozen impl with
the byte-identical stuck-reduction error. All five witnesses behave this way, so
the frozen impl's exit code is not the discriminator and must not be read as one.
What discriminates is the loop-FREE verifying positive ``pos-control-direct``,
which does reduce: each witness elaborates against its rival (exit 0), and
against that positive it fails SEMANTICALLY —

    Tactic `decide` proved that the proposition
    passwordEnvValueTester "a:b".toList = false is false

— the kernel evaluating the tester to ``true`` and refuting the claim, while the
flipped ``= true`` form ELABORATES there (exit 0). That pair is the refutation.
Each reject case therefore names ``pos-control-direct`` as an explicit
``witness_reference`` rather than relying on the gate's fallback search, so the
attestation is recorded in the manifest instead of being rediscovered per run.
"""
from pathlib import Path

INSTANCE = "django__django-10973"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen backward-copy loop body. Lies
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    let mut result : List Char := []\n"
    "    let mut i := passwd.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ passwd.length\n"
    "      invariant result = passwd.drop i\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := passwd[i - 1]!\n"
    "      result := c :: result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward-copy loop (it discharges the loop-body goal via `drop_copy_step`).
# ---- A positive control that reshapes the impl away from that loop must retune
# ---- the tactic body; both the impl region and the `prove_correct` body are
# ---- elided from the spec view, so same_spec still holds and the
# ---- `prove_correct passwordEnvValue` obligation survives with an identical
# ---- statement. Unique in the file.
_PROOF = (
    "prove_correct passwordEnvValue by\n"
    "  loom_solve\n"
    "  rw [drop_copy_step passwd i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a goal that closes
# without the loop-body drop-step lemma; retune to the bare tactic.
_PROOF_STRAIGHT = "prove_correct passwordEnvValue by\n  loom_solve"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept — used for reject rivals, which are expected NOT
    to verify)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body (soundness positives
    whose reshaped impl no longer matches the frozen loop-tuned script)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `passwordEnvValueTester passwd = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for passwordEnvValue\n"
            "prove_precondition_decidable_for passwordEnvValue\n"
            "prove_postcondition_decidable_for passwordEnvValue\n"
            "derive_tester_for passwordEnvValue\n\n" + body)


# ---- WITNESS REFERENCE. Every reject witness below is refuted against THIS
# ---- impl, not against the frozen one, and the reason is measured rather than
# ---- assumed: the frozen impl's `while` loop under
# ---- `loom.semantics.choice "demonic"` elaborates through `Classical.choice`,
# ---- which the kernel cannot unfold, so `decide` on `passwordEnvValueTester`
# ---- is STUCK against it for every claim ("did not reduce to `isTrue` or
# ---- `isFalse`") — the identical error appears for the flipped `= true` claim,
# ---- so the frozen impl's exit code carries no information about what the
# ---- witness asserts. This impl is the same one `pos-control-direct` submits as
# ---- a soundness positive: it shares the frozen spec, it VERIFIES (so it cannot
# ---- violate its own spec, which is what makes refuting a witness against it
# ---- sound), and being loop-free it REDUCES, so `decide` reaches a verdict —
# ---- semantically refuting each witness ("`decide` proved that the proposition
# ---- ... is false") while ELABORATING the flipped `= true` form. Named
# ---- explicitly rather than left to the gate's fallback search so the manifest
# ---- itself records which impl earned each rejection.
_WITNESS_REF = _impl_proof(
    "    let out : List Char := passwd\n    return out",
    _PROOF_STRAIGHT)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG. Each replaces the frozen backward-copy loop with a
    # straight-line verbatim exposure and retunes the tactic body to `loom_solve`
    # (the loop-body drop-step lemma is no longer needed).
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: expose the password directly, no per-element loop. Trivially
        # `out = passwd` and length-equal. Doubles as the `witness_reference`
        # every reject case below is refuted against (see _WITNESS_REF), so its
        # verifying is load-bearing twice over.
        "module": _WITNESS_REF,
        "rationale": (
            "a straight-line verbatim exposure (`out := passwd`) is the simplest "
            "correct impl and must satisfy both `out = passwd` (Q1) and the "
            "length clause (Q2). If it fails to verify the spec is "
            "SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-control-append-nil",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a structurally different but observationally identical copy —
        # append the empty list. NOT definitional: `example (l : List Char) :
        # l ++ [] = l := rfl` FAILS to elaborate (measured: `type mismatch ...
        # but is expected to have type l ++ [] = l`), since `List.append`
        # recurses on its LEFT argument. So the reshape leaves a real goal that
        # the retuned tactic must close by a lemma, not a reshape the carrier
        # collapses for free.
        "module": _impl_proof(
            "    let out : List Char := passwd ++ []\n    return out",
            _PROOF_STRAIGHT),
        "rationale": (
            "`passwd ++ []` is PROPOSITIONALLY but not definitionally `passwd` "
            "(`rfl` does not close `l ++ [] = l`; `List.append` recurses on its "
            "left argument), so this reshape leaves a genuine goal to discharge "
            "before Q1 (`out = passwd`) and Q2 (the length clause) hold; a "
            "second, structurally-different correct reshape defends the "
            "soundness surface. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        # Reshape that stays a LOOP, in the opposite direction: accumulate a
        # forward prefix (`result ++ [c]`, index rising) rather than consing a
        # backward suffix (index falling). The frozen invariant `result =
        # passwd.drop i` becomes `result = passwd.take i` and the frozen
        # `drop_copy_step` lemma no longer applies at all, so the tactic body is
        # retuned to close the take-step goal instead. This is the reshape the
        # other two positives do NOT cover: both of them delete the loop
        # entirely, so before this case the whole loop-with-invariants surface
        # was defended by the frozen impl alone, and a spec over-fit to the
        # BACKWARD traversal would not have been caught.
        "module": _impl_proof(
            "    let mut result : List Char := []\n"
            "    let mut i := 0\n"
            "    while i < passwd.length\n"
            "      invariant i ≤ passwd.length\n"
            "      invariant result = passwd.take i\n"
            "      done_with i = passwd.length\n"
            "      decreasing passwd.length - i\n"
            "    do\n"
            "      let c := passwd[i]!\n"
            "      result := result ++ [c]\n"
            "      i := i + 1\n"
            "    return result",
            "prove_correct passwordEnvValue by\n"
            "  loom_solve\n"
            "  · rw [show passwd[i]! = passwd[i] from by\n"
            "      rw [List.getElem!_eq_getElem?_getD, "
            "List.getElem?_eq_getElem (by omega)]; rfl]\n"
            "    rw [List.take_succ_eq_append_getElem (by omega)]\n"
            "    simp_all"),
        "rationale": (
            "a FORWARD per-code-point copy (rising index, prefix accumulator, "
            "`take i` invariant) is behaviourally identical to the frozen "
            "backward copy (falling index, suffix accumulator, `drop i` "
            "invariant) and must satisfy Q1 and Q2 just as well. It is the only "
            "positive here that keeps a loop with invariants and a termination "
            "measure, so it is what defends the spec against being over-fit to "
            "the traversal DIRECTION rather than to the exposed value: the "
            "frozen `drop_copy_step` lemma is inapplicable and the tactic body "
            "is retuned to a take-step goal instead. If it fails => "
            "SPEC-TOO-STRONG on traversal order."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY. This method has NO `require` clause (the pre-conditions
    # region is empty; the contract is total over `List Char`), so the sibling's
    # "a normal input satisfies the precondition" probe has no literal
    # counterpart. The residual PRECOND-TOO-STRONG risk on a TOTAL carrier is
    # the obligation being UNSATISFIABLE at exactly an F2P-shaped input — a
    # post-image no impl can meet reads exactly like one every impl meets — so
    # that is what this case discharges: a `have` exhibiting a concrete value
    # that meets BOTH clauses at an F2P-shaped password (separator-bearing AND
    # multi-byte-accented, the two shapes the failing tests drive) and that is
    # observably distinct from a near-miss, proven by EVALUATION, before the
    # frozen obligation closes verbatim below it.
    # =====================================================================
    {
        "id": "admiss-postimage-satisfiable-at-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        # The impl region is kept BYTE-IDENTICAL to the frozen one and the frozen
        # tactic script is kept verbatim underneath, so the method's own
        # obligation still discharges exactly as it does frozen; the only
        # addition is a leading `have` in the elided tactic body. No new lemma,
        # no new axiom, no `sorry` — the `have` is closed by `decide` on
        # concrete literals.
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct passwordEnvValue by\n"
            "  have hadm : ∃ out : List Char, out = \"s:é\".toList\n"
            "      ∧ ((out.length > 0) = ((\"s:é\".toList).length > 0))\n"
            "      ∧ out.length = 3 ∧ out ≠ [] "
            "∧ out ≠ (\"s:é\".toList).drop 1 := by\n"
            "    exact ⟨\"s:é\".toList, rfl, rfl, by decide⟩\n" + _PROOF[len(
                "prove_correct passwordEnvValue by\n"):]),
        "rationale": (
            "PRECOND-TOO-STRONG analogue on a total carrier: the obligation must "
            "be SATISFIABLE at an F2P-shaped input, not merely satisfiable "
            "somewhere. The `have` exhibits, by evaluation at a concrete "
            "separator-bearing accented password, a value meeting Q1 AND Q2 "
            "simultaneously and pins it to a length (3 code points, so the "
            "multi-byte code point counts as ONE) distinct from the near-miss "
            "value a dropped-leading-code-point impl would expose. If the "
            "post-image were jointly unsatisfiable or degenerate at that point, "
            "this term would not elaborate. LOAD-BEARING, negative-control "
            "checked in both directions: replacing the length with 4 fails "
            "(`decide` proved the proposition is false), and replacing the "
            "`≠ drop 1` with `=` fails the same way — so it is not a tautology "
            "any value would satisfy. The impl region is byte-identical to the "
            "frozen one and the frozen tactic script is kept, so the method's "
            "own obligation is discharged as usual."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-colon-escape",
        "kind": "uniqueness",
        "expect": "reject",
        # Verbatim copy EXCEPT the colon code point is still expanded to a
        # two-code-point escape sequence. Correct on every colon-free password;
        # diverges only on the colon sub-domain.
        "module": _impl(
            "    let out : List Char :=\n"
            "      passwd.flatMap (fun c => if c = ':' then ['\\\\', ':'] else [c])\n"
            "    return out"),
        "refinement": (
            "a counterpart that switched to the direct-exposure mechanism but "
            "still ran the password through a separator escape (a plausible "
            "half-fix — 'I dropped the file fragment but kept escaping the "
            "separator') exposes a two-character-longer value for any password "
            "containing that separator, where the failing tests now assert the "
            "RAW password. Correct on every separator-free password (so it is a "
            "true partial-domain break, not a blanket wrong impl), but it would "
            "NOT resolve the separator-bearing case."
        ),
        "rationale": (
            "REJECT from Q1 (`out = passwd`): at the colon the exposed value "
            "gains a code point, so `out` is strictly longer than `passwd` and "
            "cannot equal it. If this verified the spec would be SPEC-TOO-WEAK on "
            "the separator sub-domain. Refuted at a colon-bearing password — the "
            "sub-domain no other rival isolates."
        ),
        "witness": _tester(
            'example : passwordEnvValueTester "a:b".toList = false := by\n'
            '  decide\n'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-legacy-quote",
        "kind": "uniqueness",
        "expect": "reject",
        # The full legacy per-code-point quoting reborn: the backslash code point
        # is doubled and the colon is escaped, every other code point identity.
        # Correct on every backslash/colon-free password; diverges on either.
        "module": _impl(
            "    let out : List Char :=\n"
            "      passwd.flatMap (fun c =>\n"
            "        if c = '\\\\' then ['\\\\', '\\\\']\n"
            "        else if c = ':' then ['\\\\', ':'] else [c])\n"
            "    return out"),
        "refinement": (
            "this is the full pre-change per-code-point quoting: the backslash "
            "doubled, the separator escaped. Its faithful counterpart is the "
            "unchanged code, which exposes a doubled-backslash value where a "
            "failing test asserts the raw backslash password, and the escaped "
            "form where another asserts the raw separator password. It would NOT "
            "resolve those cases."
        ),
        "rationale": (
            "REJECT from Q1 (`out = passwd`): at the first backslash (or colon) "
            "the exposed value gains a code point, so `out ≠ passwd`. This is the "
            "precise change the spec senses. If it verifies => SPEC-TOO-WEAK (the "
            "verbatim requirement unenforced). Refuted at a backslash-bearing "
            "password, distinct from the colon rival's input — the backslash "
            "sub-domain the colon rival copies correctly."
        ),
        "witness": _tester(
            'example : passwordEnvValueTester "c\\\\d".toList = false := by\n'
            '  decide\n'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one: expose the password starting at index 1, dropping the first
        # code point. Correct only on the empty password.
        "module": _impl(
            "    let out : List Char := passwd.drop 1\n    return out"),
        "refinement": (
            "an off-by-one counterpart that built the exposed value from the "
            "password minus its first code point exposes a value one code point "
            "short for every non-empty password, and an empty value for a "
            "one-code-point password — failing every non-empty-password test. It "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from Q1 (content differs by the dropped first code point) AND "
            "from Q2 for a one-code-point password (the exposed value is empty, "
            "so `out.length > 0` is false while `passwd.length > 0` is true). If "
            "it verifies => SPEC-TOO-WEAK (the first code point and the "
            "populated-iff-non-empty clause unpinned). Refuted at a one-character "
            "password, where BOTH clauses fail."
        ),
        "witness": _tester(
            'example : passwordEnvValueTester "z".toList = false := by\n'
            '  decide\n'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The trivial too-weak baseline: always expose nothing. What a rival that
        # "forgot to populate the mechanism" would do. Meets Q1/Q2 only on the
        # empty password.
        "module": _impl(
            "    let out : List Char := []\n    return out"),
        "refinement": (
            "always exposing nothing is what a counterpart that never populated "
            "the mechanism would do; it exposes an empty value for every "
            "non-empty password, failing every test that asserts the actual "
            "password. It would NOT resolve. A cheap supporting near-miss with a "
            "genuine refinement."
        ),
        "rationale": (
            "REJECT from Q1 (empty ≠ a non-empty password) AND Q2 (for a "
            "non-empty password `out.length > 0` is false while "
            "`passwd.length > 0` is true). If it verifies => SPEC-TOO-WEAK. "
            "Refuted at a one-character password distinct from the other rivals' "
            "inputs."
        ),
        "witness": _tester(
            'example : passwordEnvValueTester "x".toList = false := by\n'
            '  decide\n'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-empty-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The four rivals above are all refuted at NON-EMPTY
        # passwords, and every one of them is CORRECT at the empty password
        # (verbatim-with-escaping, drop-one and always-empty all expose nothing
        # for an empty input). So before this case the empty-password boundary —
        # the sub-domain where Q2's right-hand side is false and the mechanism
        # must NOT be populated — was pinned by no witness at all. This rival is
        # the mirror image: verbatim and CORRECT on every non-empty password,
        # wrong at exactly the empty one, where it populates the mechanism with a
        # value the caller never supplied.
        "module": _impl(
            "    let out : List Char := "
            "if passwd.isEmpty then ['x'] else passwd\n"
            "    return out"),
        "refinement": (
            "a counterpart that populated the mechanism unconditionally, "
            "substituting a placeholder when the caller supplied no password, "
            "exposes a value for the no-password configuration where the failing "
            "test asserts that NOTHING is exposed. Correct on every non-empty "
            "password — the exact complement of the rivals above, so it is a "
            "true partial-domain break on the one sub-domain they all get right "
            "— but it would NOT resolve the no-password case."
        ),
        "rationale": (
            "REJECT from Q2 ((`out.length > 0`) = (`passwd.length > 0`)): at the "
            "empty password the exposed value is non-empty while the input is "
            "empty, so the two sides of the length clause disagree — AND from Q1, "
            "since a one-code-point value is not the empty list. This is the only "
            "case that attacks Q2 in the `false = true` direction (the others "
            "attack it as `true = false`, an empty exposure for a non-empty "
            "password), and the only witness at the empty input. If it verifies "
            "=> SPEC-TOO-WEAK on the no-password boundary."
        ),
        "witness": _tester(
            'example : passwordEnvValueTester [] = false := by\n'
            '  decide\n'),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation rival, 4 uniqueness rivals). This
# bundle models only the purely-functional core — a single method
# `passwordEnvValue` — where the sibling contracts one function
# `password_env_value` over a permission-bearing heap object. The value surface
# carries across intact; the permission surface does not exist here. Every
# sibling case is accounted for below.
#
#   sibling case            -> here
#   -----------------------------------------------------------------------
#   pos-cached-bound        -> pos-control-forward-loop         RE-SHAPED
#                              (+ pos-control-direct,
#                                 pos-control-append-nil ADDED)
#   admiss-reads            -> admiss-postimage-satisfiable-
#                              at-f2p-input                    RE-AIMED
#   frame-mut-write         -> (none)                            VACUOUS
#   weak-prepatch-quote     -> weak-legacy-quote                PORTED
#   weak-colon-only         -> weak-colon-escape                PORTED
#   weak-drop-first         -> weak-drop-first                  PORTED
#   weak-always-empty       -> weak-always-empty                PORTED
#                              (+ weak-empty-boundary ADDED)
#
# 4 ported, 2 re-shaped/re-aimed, 1 vacuous; 2 positive controls and 1 rival
# added.
#
# VACUOUS (frame-mut-write): the sibling's mandatory frame-mutation rival writes
#   back into a read-only input that carries only a fractional heap permission,
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `passwd` is an immutable value, this bundle declares no `mut`
#   parameter, there is no heap and no aliasing. DEMONSTRATED with two builds
#   rather than asserted: assigning to the parameter inside the impl region does
#   not elaborate at all (``passwd` cannot be mutated, only variables declared
#   using `let mut` can be mutated`), so the mutation is a grammar-level
#   impossibility; and mutating a LOCAL copy of the input and then exposing the
#   input verifies (exit 0), since no store is observable through an immutable
#   value. A case in this class would therefore either fail to parse — attesting
#   to Velvet's grammar rather than to this spec — or pass while testing nothing.
#   No substitute is fabricated (per the porting map, this class is legitimately
#   dropped rather than replaced).
# RE-AIMED (admiss-reads -> admiss-postimage-satisfiable-at-f2p-input): the
#   sibling's admissibility control confirms the fractional half-permission
#   precondition admits the reads a normal password needs. The PERMISSION half has
#   no counterpart here (this method has no `require`; the contract is total over
#   `List Char`), but the lane is NOT vacuous on that account — an earlier reading
#   of this cell recorded it as vacuous and that was the defect this audit
#   repaired. On a total carrier the PRECOND-TOO-STRONG analogue is the obligation
#   being unsatisfiable at exactly an F2P-shaped input, and the ported case tests
#   that directly: a `have` discharged BY EVALUATION at a concrete
#   separator-bearing accented password exhibits a value meeting Q1 and Q2 jointly
#   and distinguishes it from a near-miss, before the frozen obligation closes
#   verbatim underneath. Negative-controlled in both directions (a wrong length,
#   and the near-miss inequality flipped to an equality, each fail), so it is not
#   a tautology.
# RE-SHAPED (pos-cached-bound -> pos-control-forward-loop): the sibling's positive
#   control caches the loop bound, keeping the loop and its invariants. The
#   faithful analogue here is the reshape that likewise keeps a loop — the FORWARD
#   copy, rising index with a `take i` invariant against the frozen falling index
#   with a `drop i` invariant — and retunes the tactic body, which is elided from
#   the spec view. (Recorded as re-shaped to `pos-control-direct` before this
#   audit; that mapping understated the port, since a loop-free reshape drops the
#   invariant surface the sibling case exists to defend.)
# ADDED (3): pos-control-direct — the cheapest correct impl (`out := passwd`),
#   which also serves as every reject case's `witness_reference`;
#   pos-control-append-nil — a second correct reshape (`passwd ++ []`), which is
#   propositionally but NOT definitionally the input (`rfl` does not close
#   `l ++ [] = l`), so it leaves a real goal; and weak-empty-boundary — a rival
#   correct on every non-empty password and wrong at exactly the empty one, the
#   sub-domain all four ported rivals satisfy.
#
# BINDER / CLAUSE COVERAGE. The sole input binder is `passwd`; the two
#   independent top-level clauses are Q1 (`out = passwd`) and Q2 (the length
#   clause). Q1 is attacked by all five rivals; Q2 additionally by
#   weak-drop-first and weak-always-empty in the `true = false` direction (a
#   non-empty password yielding an empty exposed value) and by
#   weak-empty-boundary in the `false = true` direction (an empty password
#   yielding a populated one) — the two directions of that equality being
#   genuinely different failures, not two spellings of one. `passwd` is varied
#   across five DISTINCT witness inputs (pts=5): a colon-bearing password, a
#   backslash-bearing password, two distinct one-character passwords, and the
#   empty password — covering the two special-code-point sub-domains the verbatim
#   clause pins, the empty-result sub-domain, and the empty-INPUT boundary.
#
# SPEC-STRENGTH PROBES RUN BY AUDIT AND NOT SHIPPED (recorded so the next reader
#   knows which directions were already measured and found clean).
#   SPEC-TOO-WEAK direction — five further wrong impls, none of which verifies
#   (all exit 1, each on the `out = passwd` clause): the password reversed; the
#   last code point truncated; the password replaced by a fixed one-code-point
#   mask when non-empty; every code point lower-cased (wrong only on a password
#   with an upper-case code point, a genuine sub-domain break); and adjacent
#   duplicate code points collapsed (wrong only on a password with a repeat).
#   They are not shipped because each is rejected by the same clause and at the
#   same kind of point as a rival already in the battery, so they would add builds
#   without adding coverage. No spec hole found in this direction.
#   SPEC-TOO-STRONG direction — three further correct reshapes, all of which
#   verify (exit 0): `passwd.reverse.reverse`, `passwd.map id`, and
#   `passwd.foldr (fun c acc => c :: acc) []`. The first needs no retuning at all;
#   the other two need one extra frozen-library lemma in the simp set. Not shipped
#   for the same reason (the two shipped straight-line positives plus the forward
#   loop already cover the reshape surface). No soundness hole found.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (there are no consumed
#   axioms here in any case), and this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
