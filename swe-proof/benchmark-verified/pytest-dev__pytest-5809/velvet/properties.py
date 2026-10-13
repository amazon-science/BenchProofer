"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5809 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, and — for the admissibility case — the ``prove_correct``
tactic body, both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct buildUploadParams``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method, ``buildUploadParams``):

  buildUploadParams (contents : List Char) return (out : UploadParams)
    ensures out.code   = contents            <-- FORWARD (depends on `contents`)
    ensures out.lexer  = "text".toList        <-- LOAD-BEARING constant label
    ensures out.expiry = "1week".toList        <-- constant retention label

The operation assembles the parameter mapping submitted alongside a chunk of
captured console output when it is uploaded to a remote paste service. There is
NO ``require`` clause and ``contents`` is a free, read-only immutable value, so
the admitted domain is total. The obligation is THREE independent top-level
clauses over the single input binder ``contents``:
  (a) FORWARD — the payload is carried through under ``code`` verbatim; this is
      the only clause that reads ``contents``;
  (b) the syntax-highlighting label is the generic plain-text label — a CONSTANT,
      the load-bearing clause the change corrects; and
  (c) the retention label is the constant ``"1week"``.

GROUNDED, NOT AN ORACLE ECHO. All three post-images are fully-unfolded functions
of the method's own input and constant character literals; the ``axioms`` region
declares nothing. There is no opaque answer key to echo — the cheapest honest
impl IS the real construction — so the ungrounded-oracle-echo class is N/A and
the positive controls are data-flow reshapes that stay correct.

BINDER / CLAUSE COVERAGE. ``contents`` is the sole input binder; the FORWARD
clause is the only one that depends on it, and the code-drop rival abuses it (the
label clauses are constant regardless of ``contents``). Each of the three
independent clauses is attacked by exactly one reject rival (label / retention /
forward), and each of the three positive/admissibility cases keeps all three
correct. The three reject witnesses probe THREE DISTINCT payloads so the binder
``contents`` is varied and no value is pinned across the battery.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling attacks a
    read-only input (``paste_body_field``'s ``contents``) held at a fractional
    heap permission by WRITING into it before snapshotting. Lean and Velvet are
    referentially transparent: every parameter is an immutable value (this bundle
    declares no ``mut`` binder), there is no heap and no aliasing, so there is no
    read-only input to overwrite and no substitute probe to build. Reported as
    vacuous, not fabricated (see footer).
  * VERSION-BRANCH PARTIAL-DOMAIN — no binder to abuse on this carrier. The
    nagini sibling models the label producer as ``paste_mode_field(py_major)``,
    taking the interpreter major version as an INPUT, and its pre-patch rival
    diverges on the ``py_major >= 3`` sub-domain. This bundle models the label as
    an UNCONDITIONAL constant with NO version input (mapping.md §3.1: the fix
    replaces the version-dependent label with the constant, so the modeled value
    depends on nothing). With no ``py_major`` binder there is no partial-domain to
    split; the wrong-constant rival (returning the version label for every input)
    is the faithful port of the divergence and IS carried. Reported as a carrier
    narrowing, not fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A (see above): every post-image is a total,
    fully-unfolded function of the input and constant literals.
  * WRONG-CONSTANT / PARTIAL-DOMAIN — APPLIES: a label producer can only be wrong
    by emitting a different constant, and the forward clause can be wrong by
    dropping part of the payload. Each is refuted at a concrete payload.

AXIOM lane: the ``axioms`` region declares no ``axiom`` (mapping.md §3.1: no
consumed callee — the mapping is a pure data construction; the unchanged
serializer is an A-reference validated == the real callee by G-AX, out of scope
for this gate). ``AXIOM_TESTS`` is dropped; the gate ignores it regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5809"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region: the ENTIRE `-- impl-start` .. `-- impl-end` block
# ---- (the single struct-literal return). It lies wholly inside the one impl
# ---- region and is unique in Solution.lean; both facts are asserted at load by
# ---- _swap. Each variant re-emits the `-- impl-start` / `-- impl-end` markers so
# ---- the region boundary is preserved exactly. ------------------------------
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    return { code := contents, lexer := \"text\".toList, expiry := \"1week\".toList }\n"
    "    -- impl-end"
)
assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- The frozen proof body (the `prove_correct` tactic script). Elided from the
# ---- consumer spec view; the admissibility case adds an in-region `assert`
# ---- (which leaves an extra decidable side goal `loom_solve` cannot close) and
# ---- retunes the script to discharge it, keeping the obligation STATEMENT and
# ---- the `prove_correct` header untouched so same_spec still holds. ----------
_GOLD_PROOF = "prove_correct buildUploadParams by\n  loom_solve"
assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block.
    `body` is the text BETWEEN the markers; we wrap it back in the exact
    `-- impl-start` / `-- impl-end` markers so the region boundary is intact."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_BASE, _GOLD_IMPL, block)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_swap(_BASE, _GOLD_IMPL, block), _GOLD_PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `buildUploadParamsTester contents = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete payload.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. Every clause is `List Char` equality
# ---- (DecidableEq), so the postcondition is decidable and each witness closes
# ---- by `decide` for the loop-free extracted program; the frozen program uses a
# ---- constant literal that agrees with the spec, which is precisely why every
# ---- witness FAILS against the frozen solution (the required discrimination
# ---- half). Each witness probes a DISTINCT payload so the binder is varied.
_TESTER = ("extract_program_for buildUploadParams\n"
           "prove_precondition_decidable_for buildUploadParams\n"
           "prove_postcondition_decidable_for buildUploadParams\n"
           "derive_tester_for buildUploadParams\n\n")


SPEC_TESTS = [
    # =====================================================================
    # (1) POSITIVE CONTROL (soundness) — structurally different but CORRECT.
    # Reshape the data flow without changing semantics: let-bind the two constant
    # labels to typed locals and emit the struct fields in a DIFFERENT order
    # (expiry / lexer / code) than the gold literal. Named-field construction is
    # order-insensitive, so all three post-images (`out.code = contents`,
    # `out.lexer = "text".toList`, `out.expiry = "1week".toList`) are discharged
    # identically and `loom_solve` closes it unchanged. If this correct impl could
    # NOT verify, the postcondition is over-fit to the exact literal shape =>
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-reorder-letbind",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let lex : List Char := \"text\".toList\n"
            "    let exp : List Char := \"1week\".toList\n"
            "    return { expiry := exp, lexer := lex, code := contents }\n"),
        "rationale": "a correct reshape: let-bind the two constant labels and emit "
                     "the named struct fields in a different order. Named-field "
                     "construction is order-insensitive, so all three clauses "
                     "(`out.code=contents`, `out.lexer=\"text\".toList`, "
                     "`out.expiry=\"1week\".toList`) discharge identically under the "
                     "frozen `loom_solve`. Else SPEC-TOO-STRONG on impl shape. "
                     "Doubles as the honest cheapest positive control: the "
                     "post-images are grounded, so the cheapest correct impl IS the "
                     "real construction — there is no wrong echo.",
    },

    # =====================================================================
    # (2) POSITIVE CONTROL (soundness) — reshape the FORWARD leg specifically.
    # Rebind `contents` through a typed read-only local alias `payload` and
    # forward THAT under `code`. Same identity forward the gold discharges (Lean
    # is referentially transparent, so `payload = contents` definitionally); only
    # the local variable shape differs. Defends the FORWARD clause positively (the
    # code-drop rival attacks it) without introducing any new obligation, so
    # `loom_solve` closes unchanged. Else SPEC-TOO-STRONG (over-fit to the exact
    # `code := contents` text).
    # =====================================================================
    {
        "id": "pos-control-forward-alias",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let payload : List Char := contents\n"
            "    return { code := payload, lexer := \"text\".toList, expiry := \"1week\".toList }\n"),
        "rationale": "local-variable reshape of the FORWARD leg: rebind contents "
                     "through a read-only alias then forward it under `code`. Same "
                     "identity forward, no new obligation, so `out.code = contents` "
                     "still discharges under the frozen `loom_solve` (payload = "
                     "contents definitionally). Must verify or SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # (3) ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous. Re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is DEGENERATE at
    # the decisive point. The impl is kept verbatim so the method's own obligation
    # still discharges; an in-region `assert` pins the post-image at the F2P
    # corner — the plain-text label is DISTINCT from every version label the
    # pre-image could emit (`"text" != "python3"`, `"text" != "python"`) and the
    # retention label is distinct from the wrong-constant rival's (`"1week" !=
    # "1day"`). The assert is live, not decoration: a false claim leaves an
    # unsolved goal. The proof is retuned only to discharge the extra decidable
    # side goal `loom_solve` leaves for the assert.
    # =====================================================================
    {
        "id": "admiss-f2p-corner-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      ((\"text\".toList ≠ \"python3\".toList) ∧ (\"text\".toList ≠ \"python\".toList)\n"
            "        ∧ (\"1week\".toList ≠ \"1day\".toList)))\n"
            "    return { code := contents, lexer := \"text\".toList, expiry := \"1week\".toList }\n",
            "prove_correct buildUploadParams by\n"
            "  loom_solve\n"
            "  all_goals decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the F2P "
                     "corner: the plain-text label is distinct from every version "
                     "label the pre-image could emit (`\"text\" != \"python3\"`, "
                     "`\"text\" != \"python\"`) and the retention label is distinct "
                     "from the wrong-constant rival's (`\"1week\" != \"1day\"`), so "
                     "the load-bearing clause pins a specific label rather than "
                     "collapsing to any string. The in-region assert must discharge "
                     "(else the obligation is degenerate at the interesting point); "
                     "the impl is verbatim so all three equality clauses discharge "
                     "too.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec, each
    # loop-free (so its witness is `decide`-able) with a machine-checked refutation
    # witness at a DISTINCT payload, and the refinement argument that its faithful
    # real counterpart would NOT resolve the failing observation. The three rivals
    # attack the three independent clauses (label / retention / forward).
    # =====================================================================

    # (4) WRONG LABEL CONSTANT — the label producer emits the version label
    # ("python3") for EVERY input instead of the generic plain-text label. This is
    # the faithful port of the nagini wrong-constant rival: on this carrier the
    # label has no version input, so returning the version label unconditionally
    # is exactly the pre-image behaviour the fix corrects. Violates the label
    # clause everywhere; refuted at payload "abc".
    {
        "id": "weak-label-version-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return { code := contents, lexer := \"python3\".toList, expiry := \"1week\".toList }\n"),
        "refinement": "the faithful counterpart hard-codes the version-derived "
                      "language label instead of the generic plain-text label. The "
                      "submitted mapping then carries the version label, never the "
                      "plain-text label, so the failing observation — the submitted "
                      "label is the plain-text label — still sees the version label "
                      "and would NOT resolve (this is exactly the pre-image "
                      "behaviour the fix corrects).",
        "rationale": "REJECT from the load-bearing clause `out.lexer = "
                     "\"text\".toList`: the impl returns the version label for every "
                     "input, so the clause fails on every payload. Refuted at "
                     "\"abc\".",
        "witness": _TESTER +
                   "example : buildUploadParamsTester \"abc\".toList = false := by\n"
                   "  decide\n",
    },

    # (5) WRONG RETENTION CONSTANT — the retention label is "1day" instead of
    # "1week". Violates the retention clause everywhere; refuted at payload "xy"
    # (a DISTINCT payload from the other rivals, varying the binder). Cheap
    # supporting case: the retention field is unchanged by the fix but modeled for
    # fidelity, and its clause pins the specific constant.
    {
        "id": "weak-retention-wrong-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return { code := contents, lexer := \"text\".toList, expiry := \"1day\".toList }\n"),
        "refinement": "a counterpart that set the retention label to a different "
                      "constant changes the submitted mapping's retention entry; the "
                      "retention clause pins the specific unchanged label, so the "
                      "model would no longer faithfully mirror the submitted mapping "
                      "and a verifying rival would be a spec-too-weak break on the "
                      "modeled construction.",
        "rationale": "REJECT from the clause `out.expiry = \"1week\".toList`: the "
                     "impl returns a different constant, so the clause fails on "
                     "every payload. Refuted at \"xy\" (a payload distinct from the "
                     "other rivals, varying the binder).",
        "witness": _TESTER +
                   "example : buildUploadParamsTester \"xy\".toList = false := by\n"
                   "  decide\n",
    },

    # (6) DROP-FIRST FORWARD — forwards the payload with its first code point
    # dropped instead of verbatim. Correct only on the empty payload (drop 1 of []
    # is []); WRONG on every non-empty payload. This is the port of the nagini
    # body-drop-first rival and the ONLY rival that reads the `contents` binder, so
    # it is what varies the binder for the FORWARD clause. Refuted at payload "pq"
    # (a third DISTINCT payload).
    {
        "id": "weak-forward-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return { code := contents.drop 1, lexer := \"text\".toList, expiry := \"1week\".toList }\n"),
        "refinement": "a counterpart that forwarded the payload with its first byte "
                      "dropped would submit a truncated payload under `code`. The "
                      "failing observation — the payload appears in the submitted "
                      "mapping verbatim — would see the leading character missing, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from the FORWARD clause `out.code = contents`: the impl "
                     "drops the first code point, violating the identity on every "
                     "non-empty payload. Refuted at \"pq\" (a third distinct "
                     "payload, so the three reject witnesses probe three distinct "
                     "values of the binder `contents`).",
        "witness": _TESTER +
                   "example : buildUploadParamsTester \"pq\".toList = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) spread over THREE modeled
# field producers (paste_mode_field / paste_body_field / paste_expiry_field).
# This bundle models the same behaviour as ONE method `buildUploadParams` whose
# structure carries all three fields, with three independent postcondition
# clauses, so every sibling case that has a counterpart lands on those clauses,
# re-expressed against the `List Char`/`UploadParams` carrier.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-mode-branch-split          -> (subsumed)                        RE-AIMED
#   pos-body-local-reshape         -> pos-control-forward-alias         PORTED
#   admiss-body-half-perm          -> admiss-f2p-corner-nondegenerate   RE-AIMED
#   frame-mutate-contents          -> (none)                            VACUOUS
#   weak-mode-prepatch-branch      -> (none)                            NO-BINDER
#   weak-mode-wrong-const          -> weak-label-version-const          PORTED
#   weak-body-drop-first           -> weak-forward-drop-first           PORTED
#   weak-expiry-wrong-const        -> weak-retention-wrong-const        PORTED
#   + pos-control-reorder-letbind  (added, whole-clause positive control)
#
# RE-AIMED (pos-mode-branch-split): the sibling's mode positive branches on the
#   `py_major` input and returns the plain-text label in BOTH branches. This
#   bundle models the label as an unconditional constant with NO `py_major`
#   input, so there is no branch to reshape. Its intent — a structurally
#   different correct impl of the label producer must verify — is subsumed by
#   `pos-control-reorder-letbind` (let-bind the labels + reorder the struct
#   fields), which is the analogous structural reshape on this carrier and keeps
#   all three clauses correct.
#
# RE-AIMED (admissibility): the sibling self-calls paste_body_field on the
#   F2P-shaped body to attest the half-permission precondition admits it. This
#   bundle has NO `require` clause, so "admits a normal input" is vacuous; the
#   case is re-aimed at proving the post-image is non-degenerate at the F2P corner
#   (the plain-text label is DISTINCT from every version label the pre-image could
#   emit, and the retention label is distinct from the wrong-constant rival's).
#   The in-region assert is discharged by `decide` against concrete literals.
#
# VACUOUS (frame-mutation): the sibling's rival WRITES paste_body_field's
#   read-only `contents`, held at a fractional heap permission. This backend is
#   referentially transparent, has no heap and no aliasing, and this bundle
#   declares NO `mut` binder — there is no read-only input to overwrite and no
#   discriminating witness could exist. Not fabricated.
#
# NO-BINDER (weak-mode-prepatch-branch): the sibling's pre-patch rival diverges
#   on the `py_major >= 3` sub-domain, returning the version label there and the
#   plain-text label otherwise — a genuine partial-domain split over the
#   `py_major` INPUT. This bundle does not model `py_major` as an input at all
#   (mapping.md §3.1: the fix makes the label unconditional, depending on
#   nothing but being the plain-text label). With no `py_major` binder there is
#   no sub-domain to split, so the partial-domain form has no counterpart. Its
#   discriminating content — emitting the version label instead of the plain-text
#   label — is carried faithfully by `weak-label-version-const` (which emits the
#   version label for EVERY input, the only shape the wrong-label divergence can
#   take on this carrier). This is a carrier narrowing, not a dropped attack: the
#   clause the split would violate is still attacked.
#
# BINDER / CLAUSE COVERAGE. `contents` is the sole input binder; the FORWARD
#   clause is the only clause that reads it, and `weak-forward-drop-first` abuses
#   it. Each of the three independent clauses is attacked by exactly one rival
#   (label / retention / forward), and all three positive/admissibility cases keep
#   every clause correct. The three reject witnesses probe THREE DISTINCT payloads
#   ("abc" / "xy" / "pq"), so the binder is varied and no value is pinned.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   `axiom` (the construction is a pure data assembly; the unchanged serializer is
#   an A-reference), and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
