"""properties.py — G-PBT falsification battery for django__django-13964 (lean).

NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC_TESTS entry is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
``theorem correct_foreignKeyValueOnSave`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one behavior, a pure adoption decision):

  foreignKeyValueOnSave (fkValue : Option String) (objPk : String) : Option String
      result = (if fkValueIsEmpty fkValue then some objPk else fkValue)

  Given the stored key value ``fkValue`` and the related object's present
  primary key ``objPk``, the stored key value after the save-preparation
  adoption decision is ``objPk`` exactly when ``fkValue`` is EMPTY — where empty
  means the absent value (``none``) OR an empty scalar (``some ""``) — and is
  ``fkValue`` itself, unchanged, otherwise. The single postcondition clause pins
  the result entirely to the two inputs; nothing is left unconstrained.

  Independent behavioral faces the sole equality clause encodes:
    (empty→adopt)   on an empty ``fkValue`` (either shape) the result is exactly
                    ``some objPk`` — grounded in ``objPk``, not merely non-empty.
    (present→keep)  on a non-empty ``fkValue`` the result is ``fkValue`` itself,
                    untouched — the deliberate-key preservation face.
  ``fkValueIsEmpty`` collapses two empty shapes (``none``, ``some ""``); a rival
  that recognises only ONE of them is right on the other sub-domain and wrong on
  its complement, so both empty shapes must be probed independently.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival wrote to the read-only ``related_key`` held at half
    permission (``Acc(list_pred(related_key), 1/2)``) and relied on Viper to
    reject the write for INSUFFICIENT PERMISSION. Lean is referentially
    transparent: ``fkValue`` and ``objPk`` are passed by value, there is no heap,
    no aliasing, and no fractional permission to overflow. The class has no
    expressible instance here and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS as a spec defect. The postcondition is an
    equality against a term built ONLY from the two inputs and a pure predicate
    (``fkValueIsEmpty``); the bundle declares no ``opaque``/``axiom`` (the
    emptiness test and the adoption are modeled deeply, not axiomatized), so
    there is no opaque answer-key an implementation could echo. The carrier is
    fully transparent, so every reject witness is a plain ``decide`` at a
    concrete input rather than a hypothesis conditioning on an opaque term.

  * PARTIAL-DOMAIN / VALUE — the real attacks, and they port directly: the
    pre-fix ``none``-only recognition (right on the absent marker, wrong on the
    empty string), its complement (empty-string only, wrong on the absent
    marker), a truncated-contents adoption, a fixed-constant adoption that
    ignores ``objPk``, and an unconditional clobber that overwrites a deliberate
    non-empty key.

CASE-COUNT vs NAGINI. The nagini sibling contracted one procedure over a
``List[int]`` carrier with fractional-permission framing; this bundle models the
same single adoption decision over an ``Option String`` carrier with no heap. Of
the seven nagini cases: the frame-mutation rival is VACUOUS here (see above and
``assessment``); the ADMISSIBILITY and one soundness positive port; the four
value/partial-domain uniqueness rivals (none-only, drop-last, double-mask,
clobber) port directly; and ONE rival with no nagini counterpart is ADDED to
exercise the ``none`` sub-domain of ``fkValueIsEmpty`` the nagini carrier's
single ``[]``-vs-``None`` split conflated — an empty-string-only recognition
that is wrong precisely on the absent marker.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate at one concrete,
``decide``-able input; each was checked (``scripts/lean_verify.sh``) to ELABORATE
against its rival (the rival provably contradicts the spec there) and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). The witnesses spread across the domain: ``fkValue`` is moved over all
three reachable shapes (``none``, ``some ""``, ``some "abc"``) and ``objPk`` over
{"jeff", "sku", "abcd", "A"}, so neither binder is pinned to one value across the
battery and no two rivals share a probe point unless they truly fail there for
the same reason.

AXIOM lane: EMPTY. meta.json axioms == [] and there is no deep-model reference to
validate against a real callee here; the axiom lane belongs to G-AX in any case
and this gate ignores nagini's AXIOM_TESTS.
"""
from pathlib import Path

INSTANCE = "django__django-13964"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body (the `implementation_foreignKeyValueOnSave` def) and
# the FULL proof-region tactic body. Every replacement lands entirely inside the
# region it means to edit, so `same_spec` holds and the theorem STATEMENT is
# untouched.
_IMPL = (
    "def implementation_foreignKeyValueOnSave\n"
    "    (fkValue : Option String) (objPk : String) : Option String := Id.run do\n"
    "  -- start from the foreign-key field's currently stored key value\n"
    "  let mut result := fkValue\n"
    "  -- when that stored value is still empty, adopt the related object's primary key\n"
    "  if fkValueIsEmpty result then\n"
    "    result := some objPk\n"
    "  return result"
)
_PROOF = (
    "  intro fkValue objPk\n"
    "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
    "  by_cases h : fkValueIsEmpty fkValue\n"
    "  · simp only [Id.run, h, if_true]; rfl\n"
    "  · simp only [Id.run, h]; rfl"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations / proofs that MUST verify. If a faithful
    # correct implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps the theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-match-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: instead of the imperative "start from the stored
        # value, conditionally overwrite" shape, pattern-match on the stored
        # value and choose the result in each arm. Same value on every input; a
        # fresh proof (case split mirroring the match) closes the identical
        # obligation.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def implementation_foreignKeyValueOnSave\n"
                "    (fkValue : Option String) (objPk : String) : Option String :=\n"
                "  match fkValue with\n"
                "  | none   => some objPk\n"
                "  | some s => if s.isEmpty then some objPk else some s",
            ),
            _PROOF,
            "  intro fkValue objPk\n"
            "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave fkValueIsEmpty\n"
            "  cases fkValue with\n"
            "  | none => rfl\n"
            "  | some s => by_cases h : s.isEmpty <;> simp [h]",
        ),
        "rationale": "a correct reshape (pattern match on the stored value, "
                     "choosing the result per arm) computes `if fkValueIsEmpty "
                     "fkValue then some objPk else fkValue` on every input — the "
                     "`none` arm and the empty-`some` arm both yield `some objPk`, "
                     "the non-empty arm yields `some s = fkValue` — so it must "
                     "satisfy the sole postcondition clause; if it cannot, the "
                     "foreignKeyValueOnSave postcondition is SPEC-TOO-STRONG. The "
                     "theorem statement is byte-identical; the proof is a case "
                     "split over the match with no new lemma, axiom, or `sorry`.",
    },
    {
        "id": "admiss-ground-empty-string",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen theorem has no precondition hypothesis to admit (objPk is a
        # present String by typing); the honest analogue of the nagini
        # precondition-admission probe is to discharge the spec at a ground,
        # F2P-shaped input (the empty-string placeholder adopting a textual key)
        # by evaluation, alongside the frozen obligation closed verbatim.
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_foreignKeyValueOnSave (some \"\") \"jeff\"\n"
            "      (implementation_foreignKeyValueOnSave (some \"\") \"jeff\") := by\n"
            "    unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
            "    decide\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input "
                     "(an empty-string stored value adopting a textual primary key "
                     "\"jeff\" — the exact case the issue reports) by `decide`, then "
                     "the frozen obligation is closed verbatim. Verifies (else the "
                     "spec is unsatisfiable at the normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, the ground instance "
                     "is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P/P2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete, decide-able input. The frozen (gold) proof body is retained
    # in each rival; against the reshaped/wrong impl it fails to close, so the
    # case does NOT verify — the witness is what attributes the rejection to the
    # spec rather than to tactic breakage.
    # =====================================================================
    {
        "id": "partial-absent-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix baseline: recognise ONLY the absent marker as empty and
        # adopt then; leave an empty-string placeholder untouched. Correct on the
        # absent-marker sub-domain and on non-empty keys; diverges on the
        # empty-string sub-domain — the case the fix adds.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_foreignKeyValueOnSave\n"
            "    (fkValue : Option String) (objPk : String) : Option String := Id.run do\n"
            "  let mut result := fkValue\n"
            "  if result.isNone then\n"
            "    result := some objPk\n"
            "  return result",
        ),
        "refinement": "recognising only the absent marker as empty is exactly the "
                      "pre-fix behavior: a stored key value that starts as the "
                      "empty scalar (a textual-PK relation initialized empty and "
                      "assigned its key later) is left as the empty scalar instead "
                      "of adopting the related object's key. The F2P test observes "
                      "the stored key value ending as the empty string rather than "
                      "the adopted key — it is the exact bug the patch fixes, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from `result = if fkValueIsEmpty fkValue then some "
                     "objPk else fkValue`: on the empty-string shape "
                     "`fkValueIsEmpty (some \"\") = true`, so the result must be "
                     "`some objPk`, but the rival leaves `some \"\"`. Refuted at "
                     "(some \"\", \"jeff\") — the empty-string shape with a textual "
                     "key. Partial-domain (empty-string sub-domain).",
        "witness": (
            "example : ¬ problem_spec_foreignKeyValueOnSave (some \"\") \"jeff\"\n"
            "    (implementation_foreignKeyValueOnSave (some \"\") \"jeff\") := by\n"
            "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
            "  decide\n"
        ),
    },
    {
        "id": "partial-empty-string-only",
        "kind": "uniqueness",
        "expect": "reject",
        # No nagini counterpart: nagini's carrier conflated the two empty shapes
        # into one None/[] split. This complement recognises ONLY the empty-string
        # scalar as empty and adopts then; leaves the ABSENT marker untouched.
        # Correct on the empty-string sub-domain and on non-empty keys; diverges
        # on the absent-marker sub-domain.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_foreignKeyValueOnSave\n"
            "    (fkValue : Option String) (objPk : String) : Option String := Id.run do\n"
            "  let mut result := fkValue\n"
            "  if result == some \"\" then\n"
            "    result := some objPk\n"
            "  return result",
        ),
        "refinement": "recognising only the empty scalar and not the absent marker "
                      "narrows the emptiness test the other way: a stored key value "
                      "that is absent (the numeric/nullable relation case) is no "
                      "longer adopted from the related object. The pre-existing "
                      "absent-marker adoption the surrounding tests rely on "
                      "(a nullable foreign key whose key value is absent until its "
                      "related object is saved) would break — the stored key value "
                      "would stay absent instead of adopting the related key — so a "
                      "faithful patch this narrow would NOT resolve.",
        "rationale": "REJECT from `result = if fkValueIsEmpty fkValue then some "
                     "objPk else fkValue`: on the absent shape `fkValueIsEmpty none "
                     "= true`, so the result must be `some objPk`, but the rival "
                     "leaves `none`. Refuted at (none, \"sku\") — the absent-marker "
                     "shape, the ONLY witness that moves `fkValue` onto `none`, a "
                     "binder value no other rival exercises.",
        "witness": (
            "example : ¬ problem_spec_foreignKeyValueOnSave none \"sku\"\n"
            "    (implementation_foreignKeyValueOnSave none \"sku\") := by\n"
            "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
            "  decide\n"
        ),
    },
    {
        "id": "value-truncated-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Fires on every empty placeholder (control flow correct) and ends
        # non-empty, but adopts a TRUNCATED key (drops the last character) — the
        # contents are wrong. Attacks whether the empty→adopt face pins the EXACT
        # key, not merely non-emptiness.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_foreignKeyValueOnSave\n"
            "    (fkValue : Option String) (objPk : String) : Option String := Id.run do\n"
            "  let mut result := fkValue\n"
            "  if fkValueIsEmpty result then\n"
            "    result := some (objPk.dropRight 1)\n"
            "  return result",
        ),
        "refinement": "adopting a truncated form of the related object's primary "
                      "key stores the wrong key: for a textual primary key \"jeff\" "
                      "the stored key value would become \"jef\". The F2P test "
                      "asserts the stored key value equals the related object's "
                      "primary key exactly, so a truncated key would FAIL it -> NOT "
                      "resolve.",
        "rationale": "REJECT from `result = if fkValueIsEmpty fkValue then some "
                     "objPk else fkValue`: on an empty stored value the result must "
                     "be `some objPk` exactly, but `some (objPk.dropRight 1)` "
                     "differs whenever `objPk` is non-empty. Refuted at "
                     "(some \"\", \"abcd\") — the empty-string shape with a distinct "
                     "multi-character key. Confirms the empty→adopt face pins the "
                     "exact key, not just non-emptiness.",
        "witness": (
            "example : ¬ problem_spec_foreignKeyValueOnSave (some \"\") \"abcd\"\n"
            "    (implementation_foreignKeyValueOnSave (some \"\") \"abcd\") := by\n"
            "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
            "  decide\n"
        ),
    },
    {
        "id": "value-fixed-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # On the empty path, adopt a FIXED non-empty key ignoring objPk. Ends
        # non-empty (satisfies the non-emptiness face) but never reads objPk — the
        # cheapest impl that fakes "adopted" without doing the adoption. Must be
        # rejected by the exact-key pin, proving the result is GROUNDED in objPk.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_foreignKeyValueOnSave\n"
            "    (fkValue : Option String) (objPk : String) : Option String := Id.run do\n"
            "  let mut result := fkValue\n"
            "  if fkValueIsEmpty result then\n"
            "    result := some \"0\"\n"
            "  return result",
        ),
        "refinement": "storing a fixed constant instead of the related object's "
                      "primary key writes the wrong key; the stored key value would "
                      "not equal the related object's primary key, so the F2P "
                      "assertion that they are equal would FAIL -> NOT resolve.",
        "rationale": "REJECT from `result = if fkValueIsEmpty fkValue then some "
                     "objPk else fkValue`: a fixed `some \"0\"` satisfies "
                     "non-emptiness but is not `some objPk` for an arbitrary key. "
                     "Refuted at (some \"\", \"A\") — the empty-string shape with a "
                     "key distinct from the constant. Proves the result is grounded "
                     "in `objPk`: no constant echo verifies.",
        "witness": (
            "example : ¬ problem_spec_foreignKeyValueOnSave (some \"\") \"A\"\n"
            "    (implementation_foreignKeyValueOnSave (some \"\") \"A\") := by\n"
            "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
            "  decide\n"
        ),
    },
    {
        "id": "clobber-deliberate-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the guard entirely and ALWAYS adopt objPk. Correct on both empty
        # shapes; diverges on the non-empty sub-domain, where it clobbers an
        # existing deliberate key with the related object's key. Attacks the
        # present→keep (preservation) face.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_foreignKeyValueOnSave\n"
            "    (fkValue : Option String) (objPk : String) : Option String := Id.run do\n"
            "  let result := some objPk\n"
            "  return result",
        ),
        "refinement": "unconditionally adopting the related object's key overwrites "
                      "a deliberately-set, non-empty stored key value. The "
                      "surrounding behavior where a non-empty stored key value is "
                      "left untouched (a foreign key assigned a concrete key that "
                      "must survive the save) would break — the deliberate key "
                      "would be replaced -> NOT resolve.",
        "rationale": "REJECT from `result = if fkValueIsEmpty fkValue then some "
                     "objPk else fkValue`: on a non-empty stored value "
                     "`fkValueIsEmpty (some \"abc\") = false`, so the result must be "
                     "`fkValue` (= `some \"abc\"`), but the rival returns "
                     "`some objPk`. Refuted at (some \"abc\", \"jeff\") — the ONLY "
                     "witness that moves `fkValue` onto a non-empty value, "
                     "exercising the preservation face. Partial-domain (non-empty "
                     "sub-domain).",
        "witness": (
            "example : ¬ problem_spec_foreignKeyValueOnSave (some \"abc\") \"jeff\"\n"
            "    (implementation_foreignKeyValueOnSave (some \"abc\") \"jeff\") := by\n"
            "  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave\n"
            "  decide\n"
        ),
    },
]
