"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9281 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct objectDescription`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a value classified for display):

    objectDescription (obj : Obj) return (out : String)
        ensures out = describe obj

The carrier ``Obj`` draws the ONLY distinction the desired behaviour turns on:

  * ``Obj.enumValue className memberName genericText`` — a member of an
    enumerated type. ``className`` / ``memberName`` are the two names that
    compose the desired label; ``genericText`` is the verbose textual fallback
    the value would OTHERWISE have received (carried so the unchanged fallback
    path is observable, but NOT part of the desired rendering on this branch).
  * ``Obj.plain genericText`` — any other value, whose pre-existing generic
    textual description ``genericText`` is kept unchanged.

The pure ``describe`` is fully unfolded:

    describe (.enumValue cn mn _) = cn ++ "." ++ mn
    describe (.plain g)           = g

so the single top-level ``ensures`` clause ``out = describe obj`` combines two
distinguishable obligations keyed on the constructor of ``obj``:

  (C-enum) on an enumerated member the result is the type name and member name
           joined by a dot — the concise evaluable label — with the verbose
           fallback text IGNORED. This is the LOAD-BEARING discriminator the
           F2P test observes (a member renders as ``Type.Member``, not as the
           verbose value-revealing fallback the pre-patch code produced by
           falling through to the generic renderer).
  (C-plain) on any other value the result is the generic textual description it
           already had, unchanged.

Both parts of the label — ``className`` AND ``memberName`` — are load-bearing,
as is their ORDER and the ``.`` separator between them; and ``genericText`` is
load-bearing on the ``plain`` branch while it must NOT leak into the enum
branch. Every one of these is attacked below.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``describe`` is a concrete ``def`` in the ``pure`` region (the ``axioms`` region
declares NOTHING — the desired rendering is modeled deeply and validated ==
the real renderer by conformance_check.py, NOT consumed as an axiom). So each
rival's violation reduces to a decidable equality of concrete ``String`` values
and a witness at literal inputs discriminates it by ``decide`` — there is no
opaque callee to condition on. There is no answer-key term an echo could carry
that satisfies the ensures yet is behaviourally wrong: the unique satisfier IS
the grounded rendering, so the ungrounded-oracle-echo class is N/A (see below).

ADVERSARIAL READ of the sibling's classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the dispatch arms reordered; the closed form
    the post-image names returned directly) must still verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method has no ``require`` clause (the domain is total),
    so the residual risk on this transparent carrier is that the post-image is
    DEGENERATE at the interesting point (a spec no impl can meet reads like one
    every impl meets). ``admiss-grounded`` discharges an in-region assert pinning
    the F2P-shaped point (an enumerated ``MyEnum`` / ``FOO`` member renders as
    ``MyEnum.FOO``), the ``plain`` branch (a plain value keeps its text), AND
    that the two branches differ when the enum's ignored fallback text equals a
    plain value's text — establishing the rendering is not constant and the enum
    label genuinely differs from the fallback. The surrounding impl is kept
    verbatim so the method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival WRITES into a read-only member-name list granted at
    fractional (1/2) permission and must be rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: ``obj`` is an
    immutable value (declared read-only, not ``mut``), there is no heap and no
    aliasing, so there is no read-only input to mutate and no permission system
    to trip. Not fabricated — reported as a vacuous omission in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. C-enum / C-plain pin ``out`` to ``describe
    obj``, a fully-unfolded pure function of the input constructor's fields; the
    ``axioms`` region is empty, so there is no opaque answer key a wrong impl
    could echo. The sibling's ``echo-honest`` positive control exists to prove
    its @Pure oracle is not echo-vulnerable; here the same fact holds by
    construction (the honest positive controls compute the label directly), so
    the redundant echo control has no separate signal to add and is omitted.
  * DIVERGENCE / non-termination — the spec REJECTS it; carried as a positive
    control, and NOT a known hole. CORRECTED BY AUDIT: this bundle carries
    ``set_option loom.semantics.termination "total"`` (not ``"partial"`` — the
    earlier note here had the setting backwards, and every velvet bundle in the
    corpus now reads ``"total"``). Under total-correctness semantics the verifier
    discharges a real termination obligation, so a diverging impl does NOT verify
    vacuously. Measured, three forms, all REJECTED:

      - ``while true`` with no measure => exit 1, ``Decreasing annotations are
        required in total correctness semantics``;
      - ``while true`` + ``decreasing (0 : Nat)`` => exit 1, unsolved goal
        ``0 < 0``;
      - ``while true`` + ``decreasing i`` where ``i := i + 1`` => exit 1,
        unsolved goal ``i + 1 < i``.

    The last two matter: the corpus-wide escalation that a ``total`` bundle still
    accepts a NON-DECREASING measure does NOT reproduce on this toolchain — the
    decrease side-condition is actually emitted and actually unprovable here.

    The class is therefore shipped as ``pos-terminating-loop`` (a CORRECT
    loop-bearing impl with a genuine measure, which verifies) rather than as a
    reject case, because the negative half cannot carry a discriminating witness
    on this carrier: a rival's ``forIn Lean.Loop.mk`` term does not reduce in the
    kernel, so ``objectDescriptionTester`` gets stuck (``did not reduce to
    `isTrue` or `isFalse` ``) for EVERY claim regardless of truth. Measured
    against a diverging rival AND against a TERMINATING loop rival returning an
    unambiguously wrong value, under ``decide``, ``decide +kernel``, ``simp`` and
    ``unfold``; a trivial ``1 + 1 = 2`` claim in the same file also fails on the
    measure-less rival, so the exit code carries no information about the claim.
    A witness of the battery's shape would be hollow, so none is fabricated. The
    positive control pins the obligation from the other side: dropping ONLY the
    ``decreasing`` line from it (same loop, same invariant, same returned value)
    flips exit 0 to exit 1 on the termination obligation.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired behaviour on some sub-domain and MUST be rejected:
    the pre-patch fall-through (an enum member rendered as its verbose generic
    fallback), a wrong separator, dropping the member name, swapping the two
    names, and clobbering the plain branch's text. Each is refuted at a concrete
    input by a machine-checked witness that FAILS on the frozen solution.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``objectDescriptionTester obj = false`` says the extracted program's result
violates the postcondition at that concrete input, checked in a file whose
``prove_correct`` block has been stripped (no tactic script can mask the
verdict). Every carrier is a concrete ``String`` literal, so ``decide`` settles
each witness. Both halves were checked out of band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival and FAILS
against the frozen solution. Re-derived independently by a second audit, and each
gold-side failure is a FULL EVALUATION (``Tactic `decide` proved that the
proposition ... is false``), never a stuck reduction. The forgery test was run on
all seven: flipping the claim to ``= true`` and rebuilding against the frozen
solution EXITS 0, so the gold-side exit code tracks what the witness asserts
rather than some claim-independent elaboration failure.

Note the carrier boundary this relies on: these witnesses reduce because every
shipped rival is LOOP-FREE. A loop-bearing rival leaves an unreduced
``forIn Lean.Loop.mk`` term in the tester and no witness of this shape decides
anything against it (measured — see the ``w-diverge`` footer entry), which is why
the termination lane ships a positive control instead of a rival.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the desired
rendering is modeled deeply (validated by conformance_check.py). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9281"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: classify then return.
_IMPL = (
    "    let out : String :=\n"
    "      match obj with\n"
    "      | .enumValue className memberName _ => className ++ \".\" ++ memberName\n"
    "      | .plain genericText                => genericText\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "objectDescription impl region drifted from expected text"

# The enumerated-branch arm and the plain-branch arm in isolation; a rival edits
# exactly one arm to attack exactly one obligation while the other stays verbatim.
_ENUM_ARM = "      | .enumValue className memberName _ => className ++ \".\" ++ memberName\n"
assert _BASE.count(_ENUM_ARM) == 1, "enum arm drifted from expected text"
_PLAIN_ARM = "      | .plain genericText                => genericText\n"
assert _BASE.count(_PLAIN_ARM) == 1, "plain arm drifted from expected text"

# The FULL frozen proof body (everything after `prove_correct ... by`). A
# positive control may retune it; the tactic body is elided from the spec view,
# so this is a proof reshape, not a spec change. Unique in the file.
_PROOF = "prove_correct objectDescription by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl-region body replaced (frozen
    tactic script kept — used for reject rivals, expected NOT to verify)."""
    return _swap(_BASE, _IMPL, new_body)


def _arm_reproved(old_arm, new_arm, tactics):
    """One dispatch arm replaced AND the tactic body retuned.

    For a positive control whose reshape is NOT definitionally equal to the
    frozen impl: the frozen `loom_solve` is tuned to the frozen impl's exact
    `++` nesting, so a genuinely re-associated (but observationally identical)
    impl needs its obligation RE-DISCHARGED rather than replayed. The tactic
    body is elided from the consumer spec view, so retuning it is a proof
    reshape, not a spec change — `markers.same_spec` still holds and the
    `prove_correct objectDescription` statement stays byte-identical.
    """
    return _swap(_swap(_BASE, old_arm, new_arm), _PROOF,
                 "prove_correct objectDescription by\n" + tactics)


def _arm(old_arm, new_arm):
    """Replace exactly one dispatch arm, leaving the rest of the impl verbatim."""
    return _swap(_BASE, old_arm, new_arm)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `objectDescriptionTester obj = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for objectDescription\n"
            "prove_precondition_decidable_for objectDescription\n"
            "prove_postcondition_decidable_for objectDescription\n"
            "derive_tester_for objectDescription\n\n" + body)


def _witness(call):
    return _tester(f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG. Each keeps the `ensures out = describe obj` obligation
    # and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: dispatch the two branches in the OPPOSITE order (plain arm
        # first, enumerated arm second). The constructors are mutually exclusive,
        # so the branch each value takes is identical; the frozen `loom_solve`
        # still closes.
        "module": _impl(
            "    let out : String :=\n"
            "      match obj with\n"
            "      | .plain genericText                => genericText\n"
            "      | .enumValue className memberName _ => className ++ \".\" ++ memberName\n"
            "    return out"),
        "rationale": (
            "the two match arms are reordered (plain first, enumerated second); "
            "the constructors are mutually exclusive so each value takes the same "
            "branch and `out = describe obj` still holds. A structurally-different "
            "but correct reshape verifying is exactly what SPEC-TOO-STRONG would "
            "deny (over-fit to the literal arm order)."
        ),
    },
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the closed form the post-image names directly, instead
        # of re-deriving the label with a local match. Observationally identical;
        # a maximally different (no local `let`/`match`) control-flow shape. The
        # frozen `loom_solve` still closes.
        "module": _impl("    return (describe obj)"),
        "rationale": (
            "returns the closed form the post-image names directly, computing the "
            "identical rendering with no intermediate match/let; `out = describe "
            "obj` holds definitionally. A second structurally-different correct "
            "impl defends the soundness surface. If it fails to verify the spec is "
            "SPEC-TOO-STRONG. AUDIT NOTE: its CONTROL FLOW differs (no local "
            "`let`/`match`), but the term it returns is the post-image itself, so "
            "the obligation closes by `rfl` — this control defends the spec "
            "against over-fitting to the impl's SYNTAX, not against over-fitting "
            "to the returned term's SHAPE. `pos-reassociated` below is the "
            "control that carries the latter signal (its term is NOT "
            "definitionally the frozen one)."
        ),
    },
    {
        "id": "pos-reassociated",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the label with the concatenations RE-ASSOCIATED to the
        # right — `append cn (append "." mn)` where the frozen impl has the
        # left-nested `(cn ++ ".") ++ mn`. Observationally identical (String
        # append is associative), but NOT definitionally equal to the frozen
        # term, so the frozen `loom_solve` cannot replay: the obligation is
        # genuinely RE-PROVEN here (via String.ext_iff + List.append_assoc)
        # rather than discharged by `rfl` on an unchanged term. This is the only
        # positive whose proof does not reduce to the frozen one.
        "module": _arm_reproved(
            _ENUM_ARM,
            "      | .enumValue className memberName _ => "
            "String.append className (String.append \".\" memberName)\n",
            "  loom_solve <;> cases obj <;>\n"
            "    simp [describe, String.ext_iff, String.append, List.append_assoc]"),
        "rationale": (
            "the two `++` in the label are RE-ASSOCIATED to the right "
            "(`append cn (append \".\" mn)` vs the frozen left-nested "
            "`(cn ++ \".\") ++ mn`). String append is associative, so this is a "
            "faithful correct impl producing the byte-identical label — but the "
            "term is NOT definitionally the frozen one, so the frozen tactic "
            "`loom_solve` alone leaves `unsolved goals` on it (measured). The "
            "obligation is therefore genuinely RE-DISCHARGED from the "
            "associativity of the underlying character-list append, which is "
            "what makes this the load-bearing SPEC-TOO-STRONG control: the two "
            "other positives close by `rfl` on a term definitionally equal to "
            "gold's, so only this one shows the spec admits a label built in a "
            "different SHAPE. If NO retuned tactic could close it, the spec "
            "would be over-fit to the frozen impl's concatenation nesting => "
            "SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-terminating-loop",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (termination lane, attack F′). This bundle carries
        # `set_option loom.semantics.termination "total"`, so the verifier
        # discharges a real termination obligation and the divergence class is
        # LIVE here, not a known hole. This positive is the control half of that
        # lane: a correct impl that computes the frozen label and then runs a
        # bounded `while` carrying a genuine `decreasing` measure. It MUST
        # verify, and it does under the FROZEN tactic (measured exit 0).
        #
        # Its paired negative control is `weak-nonterminating` below: the SAME
        # loop, the SAME invariant and the SAME returned value with only the
        # `decreasing` line removed is REJECTED (measured exit 1,
        # `Decreasing annotations are required in total correctness semantics`).
        # The pair isolates the termination obligation as the sole cause: if this
        # positive failed, the spec would be over-fit to a loop-free impl shape
        # => SPEC-TOO-STRONG.
        "module": _impl(
            _IMPL[:-len("    return out")]
            + "    let mut i : Nat := 3\n"
              "    while i > 0\n"
              "      invariant out = describe obj\n"
              "      done_with i = 0\n"
              "      decreasing i\n"
              "    do\n"
              "      i := i - 1\n"
              "    return out"),
        "rationale": (
            "a CORRECT impl carrying a bounded loop with a genuine `decreasing i` "
            "measure: it computes the frozen label, spins a terminating countdown "
            "whose invariant preserves `out = describe obj`, and returns that "
            "label. Observationally identical to the frozen impl, so it must "
            "verify — measured exit 0 under the UNTOUCHED frozen `loom_solve`. "
            "This is the control half of the termination lane: it shows the "
            "rejection of `weak-nonterminating` (the same loop minus the measure) "
            "is attributable to the TERMINATION obligation and not to the loop's "
            "mere presence or to a tactic gap. If a correct loop-bearing impl "
            "could not verify, the spec would be over-fit to a loop-free shape "
            "=> SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause (total domain), so the
    # residual risk is that the post-image is DEGENERATE at the interesting
    # point. This case discharges an in-region assert establishing that the
    # rendering pins the F2P-shaped label, keeps a plain value's text, and that
    # the enum label genuinely DIFFERS from the ignored fallback text — i.e. the
    # rendering is not constant. The surrounding impl is kept verbatim so the
    # method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (describe (Obj.enumValue \"MyEnum\" \"FOO\" \"gen\") = \"MyEnum.FOO\" ∧\n"
            "       describe (Obj.plain \"raw\") = \"raw\" ∧\n"
            "       describe (Obj.enumValue \"MyEnum\" \"FOO\" \"gen\") ≠ describe (Obj.plain \"gen\")))\n"
            + _IMPL),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "point: an enumerated `MyEnum` / `FOO` member renders as the concise "
            "label `MyEnum.FOO` (not the verbose fallback), a plain value keeps "
            "its text, and the enum label DIFFERS from what the ignored fallback "
            "text would give — so the rendering is not constant. The in-region "
            "assert must discharge (else the obligation is degenerate / "
            "SPEC-UNUSABLE); the impl is kept verbatim so `out = describe obj` "
            "still verifies."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-enum-as-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: an enumerated member renders as its verbose generic
        # fallback text instead of the concise label. Correct on every plain
        # value; diverges precisely on the enumerated sub-domain the F2P feeds.
        "module": _arm(
            _ENUM_ARM,
            "      | .enumValue className memberName g => g\n"),
        "refinement": (
            "this is the pre-change behaviour: a member of an enumerated type is "
            "not special-cased, so it falls through to the generic textual "
            "fallback (the verbose value-revealing form) instead of the concise "
            "type-name-dot-member-name label. Its faithful counterpart is the "
            "unchanged code, under which the failing test — which asserts the "
            "member renders as the concise label — still sees the verbose "
            "fallback, so it would NOT resolve. Correct on every non-enumerated "
            "value (a true partial-domain break, not a blanket wrong impl)."
        ),
        "rationale": (
            "REJECT from C-enum: on `Obj.enumValue \"MyEnum\" \"FOO\" \"gen\"` the "
            "spec requires `\"MyEnum.FOO\"`, but this returns the fallback text "
            "`\"gen\"`, so `out ≠ describe obj`. This is the precise change the "
            "spec senses and the headline discriminator. If it verified => "
            "SPEC-TOO-WEAK (admits the pre-patch fall-through). Refuted on the "
            "enumerated sub-domain, and the only reject demonstrating that "
            "`genericText` must NOT leak into the enum branch."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.enumValue "MyEnum" "FOO" "gen")'),
    },
    {
        "id": "weak-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Joins the two names with the wrong separator ("/" instead of "."). It
        # agrees with gold on no enumerated member (every label has exactly one
        # separator); refuted at any enum input.
        "module": _arm(
            _ENUM_ARM,
            "      | .enumValue className memberName _ => className ++ \"/\" ++ memberName\n"),
        "refinement": (
            "a counterpart that joined the type name and member name with the "
            "wrong punctuation would render `Type/Member` where the desired "
            "evaluable label is `Type.Member`. The failing test pins the "
            "dot-separated label exactly, so a wrong-separator patch would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C-enum: on `Obj.enumValue \"A\" \"B\" \"g\"` the spec "
            "requires `\"A.B\"`, but this returns `\"A/B\"`. If it verified => "
            "SPEC-TOO-WEAK (the separator not pinned). Refuted at a distinct "
            "enumerated input, isolating the separator between the two names."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.enumValue "A" "B" "g")'),
    },
    {
        "id": "weak-class-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the member name: renders just `className ++ "."`. Correct only
        # when the member name is empty (never, for a real member); refuted at any
        # enum input with a non-empty member name.
        "module": _arm(
            _ENUM_ARM,
            "      | .enumValue className memberName _ => className ++ \".\"\n"),
        "refinement": (
            "a counterpart that emitted only the type name and the separator "
            "would render `Type.` and drop the member name entirely. The failing "
            "test requires the member name to appear after the dot, so a "
            "class-name-only patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from C-enum: on `Obj.enumValue \"C\" \"D\" \"g\"` the spec "
            "requires `\"C.D\"`, but this returns `\"C.\"` — the member name is "
            "dropped. If it verified => SPEC-TOO-WEAK (the member name unpinned). "
            "Refuted at a distinct enumerated input, isolating the `memberName` "
            "binder."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.enumValue "C" "D" "g")'),
    },
    {
        "id": "weak-swapped-names",
        "kind": "uniqueness",
        "expect": "reject",
        # Swaps the two names: renders `memberName ++ "." ++ className`. Uses both
        # names and the dot, so it is refutable ONLY where the two names differ —
        # isolating the ORDER of the label's two components.
        "module": _arm(
            _ENUM_ARM,
            "      | .enumValue className memberName _ => memberName ++ \".\" ++ className\n"),
        "refinement": (
            "a counterpart that emitted the member name before the type name "
            "would render `Member.Type` where the desired label is `Type.Member`. "
            "The failing test pins the type-name-first order, so a swapped-order "
            "patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from C-enum: on `Obj.enumValue \"Cls\" \"Mem\" \"g\"` the spec "
            "requires `\"Cls.Mem\"`, but this returns `\"Mem.Cls\"`. This rival "
            "uses BOTH names and the dot, so it is refutable only where the two "
            "names differ — the case that pins the ORDER of the two components "
            "(neither the drop-member nor the wrong-separator rival senses it). "
            "If it verified => SPEC-TOO-WEAK (component order unpinned)."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.enumValue "Cls" "Mem" "g")'),
    },
    {
        "id": "weak-plain-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER branch: a plain value's generic text is discarded and
        # replaced by the empty string. Correct on every enumerated member; wrong
        # on any plain value with non-empty text.
        "module": _arm(
            _PLAIN_ARM,
            "      | .plain genericText                => \"\"\n"),
        "refinement": (
            "a counterpart that discarded a non-enumerated value's existing "
            "generic description would render every other value as empty text, "
            "changing the byte-for-byte-unchanged rendering the fix must preserve. "
            "Every regression test that pins the existing description for a "
            "non-enumerated value would break, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C-plain: on `Obj.plain \"xyz\"` the spec requires "
            "`\"xyz\"`, but this returns `\"\"`. This is the only reject attacking "
            "the `plain` branch — it holds `obj`'s constructor at `plain` (all "
            "other rivals hold it at `enumValue`), so it varies the sole input "
            "binder's constructor and pins the unchanged-fallback obligation. If "
            "it verified => SPEC-TOO-WEAK (the plain branch unpinned)."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.plain "xyz")'),
    },
    {
        "id": "weak-member-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Drops the CLASS name: renders just `"." ++ memberName`.
        # The mirror of weak-class-name-only, and the gap that rival left: no
        # existing reject drops `className` to nothing. Correct only when the
        # class name is empty (never, for a real enumerated type).
        "module": _arm(
            _ENUM_ARM,
            "      | .enumValue className memberName _ => \".\" ++ memberName\n"),
        "refinement": (
            "a counterpart that emitted only the separator and the member name "
            "would render `.Member` and drop the owning type's name entirely. "
            "The failing test requires the type name to appear BEFORE the dot, "
            "so a member-name-only patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from C-enum: on `Obj.enumValue \"Ns\" \"Mm\" \"gg\"` the spec "
            "requires `\"Ns.Mm\"`, but this returns `\".Mm\"` — the class name is "
            "dropped. The MIRROR of weak-class-name-only and the binder gap it "
            "left: before this case, `className` was never dropped to nothing "
            "(only moved or ignored), so a rival that omitted the type name "
            "outright was unattacked. If it verified => SPEC-TOO-WEAK "
            "(`className`'s presence unpinned)."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.enumValue "Ns" "Mm" "gg")'),
    },
    {
        "id": "weak-generic-suffix",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Builds the correct label but APPENDS the ignored
        # fallback text to it. A strict near-miss: it contains the whole desired
        # label as a prefix, so every rival above that checks a component's
        # presence would pass it — only exactness catches it.
        "module": _arm(
            _ENUM_ARM,
            "      | .enumValue className memberName g => "
            "className ++ \".\" ++ memberName ++ g\n"),
        "refinement": (
            "a counterpart that emitted the concise label but then appended the "
            "verbose fallback text would render `Type.Membergeneric` — the label "
            "is present but the value-revealing text the change exists to "
            "SUPPRESS is still there. The failing test compares the rendered "
            "string EXACTLY, so a patch that only prepends the label without "
            "replacing the fallback would NOT resolve."
        ),
        "rationale": (
            "REJECT from C-enum: on `Obj.enumValue \"P\" \"Q\" \"z\"` the spec "
            "requires `\"P.Q\"`, but this returns `\"P.Qz\"`. The strictest "
            "near-miss in the battery: the desired label is a PREFIX of the "
            "result, so both names, the separator and the order are all correct "
            "— it is refuted only by the spec pinning the rendering EXACTLY "
            "rather than up to extra trailing text. weak-enum-as-fallback shows "
            "`genericText` must not REPLACE the label; this shows it must not be "
            "APPENDED to it either, which is the residual half of the "
            "suppression obligation. If it verified => SPEC-TOO-WEAK (the "
            "rendering pinned only up to a prefix)."
        ),
        "witness": _witness(
            'objectDescriptionTester (Obj.enumValue "P" "Q" "z")'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives + 1 admissibility; 5 uniqueness rivals — one the mandatory
# frame-mutation rival, one the divergence rival) plus 2 AXIOM_TESTS entries. The
# sibling contracts ONE function, `describe(value: Value) -> List[int]`, over a
# read-only `Value` record carrying fractional heap permissions on every field,
# rendering the enumerated member per code-point with copy loops (whose loop
# invariants live in the impl region) and pinning the result to the @Pure oracle
# `enum_rendering(class_name, member_name) = class_name ++ '.' ++ member_name`.
#
# This bundle models the SAME decision — which rendering a value receives — but
# on a value carrier: `objectDescription (obj : Obj) return (out : String)` with
# `ensures out = describe obj`, where `describe` is a concrete pure `def` (the
# @Pure `enum_rendering`/`dot` folds are refined to Lean `String` concatenation,
# mapping.md §2). The per-code-point copy loops, the fractional permissions, and
# the total-correctness `MustTerminate` obligation have no counterpart on this
# referentially-transparent value carrier; the value surface — the enum label,
# its separator, its two components and their order, and the unchanged fallback —
# carries across intact.
#
#   sibling case                   kind          -> here                    disposition
#   ----------------------------------------------------------------------------------------
#   pos-control-disj-reorder       soundness     -> pos-arm-reorder         PORTED (re-shaped)
#   echo-honest                    soundness     -> (none)                  N/A (no opaque oracle)
#   admiss-enum-shaped             admissibility -> admiss-grounded         PORTED (re-aimed)
#   frame-mutate-member            uniqueness    -> (none)                  VACUOUS
#   rival-enum-as-fallback         uniqueness    -> weak-enum-as-fallback   PORTED
#   rival-wrong-separator          uniqueness    -> weak-wrong-separator    PORTED
#   rival-class-name-only          uniqueness    -> weak-class-name-only    PORTED
#   w-diverge                      uniqueness    -> pos-terminating-loop    PORTED (re-aimed,
#                                                                           audit; positive half
#                                                                           only — see footer)
#   (no sibling)                   soundness     -> pos-closed-form         ADDED (shape cov.)
#   (no sibling)                   soundness     -> pos-reassociated        ADDED BY AUDIT
#   (no sibling)                   uniqueness    -> weak-swapped-names      ADDED (order cov.)
#   (no sibling)                   uniqueness    -> weak-plain-clobber      ADDED (branch cov.)
#   (no sibling)                   uniqueness    -> weak-member-name-only   ADDED BY AUDIT
#   (no sibling)                   uniqueness    -> weak-generic-suffix     ADDED BY AUDIT
#   ax-sound-enum-rendering        axiom         -> (none)                  G-AX
#   ax-contain-enum-rendering      axiom         -> (none)                  G-AX
#
# 3 uniqueness ported, 1 soundness ported + 3 added (4 total), 1 admissibility
# re-aimed, 1 termination lane re-aimed to a positive, 1 vacuous, 0 known holes;
# 4 rivals added for order/branch/component and exactness coverage.
#
# AUDIT ADDITIONS (independent adversarial re-derivation of this port).
# Every original case was re-judged; all 5 original witnesses were rebuilt
# out of band against BOTH the rival and the frozen solution, and each gold-side
# build failed with `Tactic 'decide' proved that the proposition ... is false` —
# a fully-evaluated SEMANTIC refutation, not a stuck reduction, a missing name
# or a timeout. Three gaps were found and closed:
#
# 1. ADDED pos-reassociated. The two original positives are both closed by the
#    FROZEN tactic because the term each returns is definitionally equal to the
#    frozen one (`(cn ++ ".") ++ mn` — `++` is left-associative, so even a
#    hand-parenthesised left nesting is the SAME term, measured: it verifies
#    under the untouched `loom_solve`). So neither positive actually tested
#    whether the spec admits a label of a different SHAPE. A right-re-associated
#    impl (`append cn (append "." mn)`) does NOT close under the frozen tactic
#    (`unsolved goals`, measured), and closes only once the obligation is
#    re-discharged from `List.append_assoc` — which is the genuine
#    SPEC-TOO-STRONG signal the battery was missing. The spec is NOT too strong:
#    the reshape verifies with a retuned proof (measured exit 0).
# 2. ADDED weak-member-name-only. The original coverage note claimed
#    "`className` — dropped-into-nothing is not attacked directly", which was
#    accurate but left the mirror of weak-class-name-only unbuilt. Now built.
# 3. ADDED weak-generic-suffix. No original rival made the enum branch produce
#    a SUPERSTRING of the desired label, so nothing tested that the rendering is
#    pinned EXACTLY rather than up to a prefix — the residual half of the
#    "the verbose fallback must be suppressed" obligation.
#
# CORRECTED PROSE: pos-closed-form's rationale called itself "a maximally
# different (no local `let`/`match`) control-flow shape". Its control flow does
# differ, but the returned TERM is the post-image itself, so it closes by `rfl`
# and carries no shape signal; the rationale now says which signal it does and
# does not carry, and points at pos-reassociated for the other.
#
# SECOND AUDIT (independent adversarial re-derivation; builds re-run from
# scratch). Attack A: every one of the then-11 variants was diffed against the
# frozen file — all diffs confined to the impl region or the tactic body, the
# `ensures out = describe obj` statement and the whole `pure` region byte-
# identical, so no case reformats or weakens the obligation. Attack B: all 7
# witnesses rebuilt (rival exit 0, gold exit 1 in every case) and every gold-side
# failure read `Tactic `decide` proved that the proposition ... is false` — a
# fully-evaluated refutation. Attack B′ (forgery): for all 7, the claim was
# FLIPPED (`= false` -> `= true`) and rebuilt against gold; every flipped claim
# built at exit 0 while the witness fails at exit 1, so the gold-side exit code
# demonstrably tracks the claim and none of the 7 is hollow. The admissibility
# assert was probed conjunct-by-conjunct: falsifying the F2P label, the plain
# branch, or the non-degeneracy claim each flips exit 0 -> exit 1, so all three
# conjuncts are load-bearing and the case is not a no-op.
#
# One defect found and fixed: the DIVERGENCE lane was recorded as a known spec
# hole on the false premise that this bundle is `"partial"`. It is `"total"`; the
# class is live, the spec rejects every diverging rival, and the lane is now
# shipped as `pos-terminating-loop`. See the w-diverge footer entry.
#
# ATTACK E (spec-too-strong probes — the spec is NOT over-fit): besides
#   `pos-reassociated`, a `String.intercalate "." [className, memberName]` reshape
#   was landed (verifies with a retuned `cases obj <;> rfl`, exit 0), and a
#   loop-bearing correct impl verifies under the UNTOUCHED frozen tactic (now
#   shipped as `pos-terminating-loop`). A `String.mk (className.data ++ '.' ::
#   memberName.data)` reshape could NOT be closed with the tactics tried (simp
#   loops on `String.append`/`HAppend`); recorded as UNCERTAIN, not as a hole —
#   the two reshapes that did close are the evidence the spec admits a different
#   label SHAPE.
#
# ATTACK D (spec-too-weak probes that FAILED to find a hole — the spec held):
#   an `if className == "" then memberName else <label>` guard (a conditional
#   near-miss agreeing with gold off the empty-class-name point) and a rival
#   appending "." to the PLAIN branch were both REJECTED by the frozen spec.
#   No input was found on which a wrong impl verifies. Both re-measured
#   independently by the second audit (exit 1 each), plus NINE further wrong
#   impls the battery does not contain, ALL rejected (exit 1):
#     - `if g == "" then <label> else g` (guarded on the IGNORED fallback field,
#       so it agrees with gold exactly where the carried text is empty);
#     - `if className == memberName then "" else <label>` (agrees off the
#       diagonal);
#     - `className ++ ".." ++ memberName` (doubled separator);
#     - `"." ++ genericText` on the plain branch;
#     - both branches crossed (enum -> its fallback text, plain -> text ++ ".");
#     - `(className ++ "." ++ memberName).toUpper` (a "normalizing" rival);
#     - `className ++ "." ++ memberName ++ "."` (trailing separator);
#     - `panic! "boom"` (the obligation is NOT discharged by a panic: the goal
#       `panicWithPosWithDecl ... = describe obj` survives);
#     - a TERMINATING `while` loop with a real measure returning `"WRONG"`.
#   The last one is the sharpest: the spec is `out = describe obj` against a
#   concrete total `describe`, which pins `out` UNIQUELY at every input, so the
#   only route to SPEC-TOO-WEAK is vacuity (an unreachable exit) — and the
#   termination obligation closes that route (see the w-diverge footer entry).
#   No spec hole found in either direction.
#
# PORTED (pos-control-disj-reorder -> pos-arm-reorder): the sibling reorders the
#   collection-arm membership disjunction. The value carrier has a two-way match,
#   not a disjunction, so the reshape spirit becomes reordering the two dispatch
#   arms (plain first, enumerated second) — a correct, order-independent reshape
#   the frozen proof still closes. ADDED pos-closed-form gives a maximally
#   different (loop-free, no local match) second correct shape.
# N/A (echo-honest): the sibling's echo control re-asserts the @Pure-oracle pin
#   to prove the spec is NOT echo-vulnerable. Here the pin is `out = describe
#   obj` with `describe` a fully-unfolded pure `def` and an EMPTY axioms region —
#   there is no opaque answer key an impl could echo, so the class holds by
#   construction and the honest positive controls (which compute the label
#   directly) discharge it. No separate signal to add.
# PORTED (admiss-enum-shaped -> admiss-grounded): the sibling asserts the oracle
#   on the 'MyEnum'/'FOO' code points equals the 'MyEnum.FOO' code points. Here
#   the in-region assert pins the same F2P-shaped label on `String`, plus the
#   plain branch and the enum-vs-fallback difference, so the post-image is shown
#   satisfiable and non-degenerate at the interesting point.
# PORTED (rival-enum-as-fallback -> weak-enum-as-fallback): direct port of the
#   discriminating bug — an enumerated member rendered as its verbose generic
#   fallback. THE modeled bug and prepatch discriminator. Refuted on the enum
#   sub-domain, also demonstrating `genericText` must not leak into the label.
# PORTED (rival-wrong-separator -> weak-wrong-separator): direct port; join with
#   the wrong punctuation. Refuted at a distinct enum input.
# PORTED (rival-class-name-only -> weak-class-name-only): direct port; drop the
#   member name. Refuted at a distinct enum input, isolating `memberName`.
# ADDED (weak-swapped-names): no sibling counterpart, but the value carrier makes
#   the ORDER of the label's two components a separable clause. Uses both names
#   and the dot, so it is refutable only where the names differ — the sole reject
#   pinning component order (neither drop-member nor wrong-separator senses it).
# ADDED (weak-plain-clobber): no sibling counterpart directly, but the `plain`
#   branch's unchanged-fallback obligation is a separable clause. This is the only
#   reject holding `obj`'s constructor at `plain` (all others hold it at
#   `enumValue`), so it varies the sole binder's constructor and pins C-plain.
#
# VACUOUS (frame-mutate-member): the sibling's MANDATORY frame-mutation rival
#   WRITES `value.member_name[j] = 65` into a member-name list granted only at
#   half permission, and must be rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent: `obj` is an immutable value, the method
#   declares no `mut` binder, there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class is
#   vacuous. No substitute is fabricated.
# PORTED (w-diverge -> pos-terminating-loop): CORRECTED BY AUDIT. The previous
#   note recorded this as a KNOWN SPEC HOLE on the stated ground that the bundle
#   carries `set_option loom.semantics.termination "partial"`. That was FALSE:
#   `Solution.lean` line 4 reads `"total"`, and all 500 velvet bundles in the
#   corpus do. The option could not have disagreed with the file's
#   `open TotalCorrectness` in any case: the `set_option` elaborator itself runs
#   `openScope `TotalCorrectness` (`Loom/MonadAlgebras/WP/Options.lean:169-186`).
#   (An internal findings doc that recorded the opposite disposition for a
#   `partial` cohort is withdrawn along with the claim, and no longer exists.)
#   Under `"total"` the
#   sibling's `MustTerminate` analogue IS discharged, so the class is live and
#   shippable rather than a hole. Measured: a diverging rival is REJECTED with no
#   measure (`Decreasing annotations are required in total correctness
#   semantics`), with `decreasing (0 : Nat)` (goal `0 < 0`), and with an
#   INCREASING `decreasing i` (goal `i + 1 < i`) — so the corpus-wide
#   non-decreasing-measure escalation does not reproduce on this toolchain.
#   Shipped as the POSITIVE control `pos-terminating-loop` (correct impl, real
#   measure, verifies under the frozen tactic) because the reject half admits no
#   honest witness: every loop-bearing rival leaves an unreduced
#   `forIn Lean.Loop.mk` in the tester, so `decide` / `decide +kernel` / `simp` /
#   `unfold` are all stuck for ANY claim (a trivial `1 + 1 = 2` fails in the same
#   file), and a witness whose gold-side exit code is claim-independent would be
#   hollow. The residual gap is the reject direction only, and it is a CARRIER
#   limit (kernel irreducibility of the loop term), not a spec weakness: the
#   obligation itself demonstrably bites, as the positive's measure-stripped
#   control shows (exit 0 -> exit 1).
# AXIOM_TESTS (2: ax-sound/ax-contain-enum-rendering): dropped. The axiom lane is
#   G-AX's job (conformance_check.py validates `describe` == the real renderer);
#   the rendering is modeled deeply here as an A-reference with no consumed axiom,
#   and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the sole input binder
#   `obj : Obj` of the single ensures `out = describe obj` (pts = 5 distinct input
#   points):
#     obj's constructor  — `enumValue` (six rivals) AND `plain` (plain-clobber):
#                          both constructors of the sole binder attacked, so BOTH
#                          top-level clauses (C-enum, C-plain) are attacked.
#     className          — DROPPED to nothing (member-name-only, added by audit),
#                          moved to second position (swapped-names), and ignored
#                          (enum-as-fallback): all three ways to mishandle it.
#     exactness          — the label must be the WHOLE result, not a prefix of it
#                          (generic-suffix, added by audit): a rival emitting the
#                          correct label followed by the suppressed fallback text
#                          is refuted.
#     memberName         — dropped (class-name-only), moved (swapped-names),
#                          ignored (enum-as-fallback): thoroughly varied.
#     separator          — "." vs "/" (wrong-separator): pinned.
#     component order    — Type.Member vs Member.Type (swapped-names): pinned.
#     genericText        — must NOT leak on the enum branch (enum-as-fallback
#                          returns it and is rejected) AND must be preserved on the
#                          plain branch (plain-clobber drops it and is rejected):
#                          both roles of genericText attacked.
#   Every independent top-level behaviour of the post-image is attacked: the enum
#   label's presence (enum-as-fallback), its separator (wrong-separator), its
#   member component (class-name-only), its class component (member-name-only),
#   the order of its two components (swapped-names), its EXACTNESS against a
#   trailing-text superstring (generic-suffix), and the unchanged plain fallback
#   (plain-clobber). Seven DISTINCT witness input points (pts=7), one per rival,
#   each machine-checked to elaborate against its rival and to be proven FALSE by
#   `decide` against the frozen solution.
AXIOM_TESTS = []
