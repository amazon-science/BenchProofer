"""properties.py — G-PBT falsification battery for psf__requests-2931 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct encodePayload`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a TAGGED payload carrier):

  encodePayload (data : Payload) return (out : Payload)
    ensures out = data                       -- THE load-bearing clause

``Payload`` is a two-constructor inductive — ``.text (List Char)`` for a text
payload, ``.binary (List UInt8)`` for a binary payload — with ``DecidableEq``.
The carrier is deliberately TAGGED rather than content-only, because the
behaviour under test is KIND preservation: the consumer observes which of the
two alternatives it was handed, and a content-only model would be blind to a
rival that silently reinterprets one as the other.

There are NO ``require`` clauses: the method is total over the carrier, so every
constructed ``Payload`` is in-domain and no witness can be excluded vacuously.
The ``axioms`` region is EMPTY — there is no opaque callee and no answer key to
echo (directive 8). ``toNativeString`` in the ``pure`` region is a fully
transparent ``def`` over the same carrier, used by the baseline to express the
coercion the encoder must NOT perform; it is not consumed by any obligation.

Although ``ensures out = data`` is a single equation, on a tagged carrier it
decomposes into two independently-attackable sub-behaviours, and this battery
attacks both:

  * KIND — the returned payload has the SAME constructor as the input. A binary
           payload stays binary; a text payload stays text. Neither is coerced
           into the other, in either direction.
  * CONTENT — the returned payload carries the SAME sequence, elementwise and in
           the SAME order. Not truncated, not emptied, not permuted.

ONE input binder, free over the whole carrier:
  * ``data`` — both its CONSTRUCTOR (text vs binary) and its CONTENT (elements,
    length, order) matter. The reject witnesses below therefore vary the binder
    along both axes: three probe ``.binary`` values (of lengths 1, 2 and 4, one
    of them outside the coercion's own defined range) and two probe ``.text``
    values (of lengths 2 and 3). A battery that probed only one constructor
    would leave a whole half of the clause untested — a rival that mishandled
    only the other alternative would verify unnoticed.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting
in the footer):

  * FRAME / PERMISSION-MUTATION — VACUOUS here. The sibling's three
    ``frame-mut-*`` cases are its single largest class, and they are the one
    class that cannot cross: they attack a fractional-permission discipline by
    WRITING a read-only input field, and the rejection they expect comes from
    the permission system before any postcondition is considered. This backend
    is referentially transparent: ``data`` is an immutable value, the method
    declares no ``mut`` binder, and there is no heap and no aliasing, so there
    is no read-only cell to overwrite and no permission to be insufficient. No
    substitute probe is fabricated (per the porting map, this class is
    legitimately dropped rather than replaced).

  * PARTIAL-DOMAIN / KIND-SWAP — heavily exercised, and this is where the
    sibling's real adversarial content lives. Every rival below gets part of the
    domain right and diverges on one sub-behaviour, including one NEAR-MISS that
    is correct on strictly more of the domain than the baseline coercion and is
    therefore given its own separating witness.

  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The sibling
    notes its postconditions are GROUNDED in the input rather than pinned to an
    opaque answer key; here that is even more direct — the clause equates the
    result to the method's own argument. There is nothing to echo, so the
    sibling's honest grounded positive control is what carries over (the two
    soundness cases below).

  * DIVERGENCE / NON-TERMINATION — NOT a spec hole on this bundle, and no case
    is shipped. This bundle is verified under
    ``set_option loom.semantics.termination "total"`` (Solution.lean line 4), so
    a postcondition is claimed of ALL runs rather than only terminating ones and
    every loop owes a strictly decreasing measure. (An earlier version of this
    bullet placed the bundle in a ``total`` minority against a ``partial`` majority,
    citing an internal findings doc. That census is withdrawn: all 500 velvet
    bundles set ``"total"``, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the ``open``
    cannot disagree and there is no cohort to belong to.) Re-measured here with a
    real build: the
    frozen impl prefixed with ``while True do pure ()`` is rejected, with
    ``error: Decreasing annotations are required in total correctness
    semantics``. So the postcondition is claimed of ALL runs and a
    never-terminating impl does NOT satisfy ``out = data`` vacuously — the
    corpus-wide hole does not reach this artifact.
    It is nonetheless not shippable as a reject CASE, for a mechanical reason
    rather than a spec one: the gate requires the witness to ELABORATE against
    the rival, and the diverging rival's extracted tester does not reduce, so
    the witness build fails with ``Tactic `decide` failed for proposition
    encodePayloadTester (Payload.binary [65]) = false because its `Decidable`
    instance`` — an inconclusive ``witness-unproven``, not a refutation. The
    class is therefore already closed by the frozen artifact's own termination
    semantics, which is why the reject lane spends its cases on the KIND and
    CONTENT sub-behaviours instead.

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` CONTRACT, not a bare
predicate, so each witness reaches the postcondition through Velvet's own tester
machinery: ``encodePayloadTester <input> = false`` says the extracted program's
result violates the postcondition at that concrete input. The frozen impl and
every rival are LOOP-FREE (a return, a ``match``, or a single guarded
expression), so every tester reduces under ``decide``; no conditioning on an
opaque term is needed anywhere, because the carrier is fully transparent. Each
witness was checked out-of-band with ``scripts/lean_verify.sh`` in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict, and BOTH halves were observed: every witness ELABORATES against its
rival (the tester ``decide``s to ``false``) and FAILS against the frozen
solution (gold's tester ``decide``s to ``true``, so ``= false`` is refuted, and
``decide`` reports the proposition false rather than getting stuck). Rejection
is thus attributed to the spec and never to mechanical tactic breakage — which
matters here because the frozen proof is a bare ``loom_solve`` and every rival
reshapes the body it was tuned to.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed axioms; the one modeled
callee is a deep-model A-reference validated by ``axiom_check.py``, which is
G-AX's job. This gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "psf__requests-2931"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — the single statement strictly BETWEEN
# `-- impl-start` and `-- impl-end`. Every rival and reshape edits ONLY this
# line (and, for the admissibility probe, the elided `prove_correct` tactic
# body), so the spec view is untouched and same_spec holds by construction.
_IMPL = "    return data"

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. Rivals leave it as `loom_solve`, so a wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct encodePayload by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (admissibility's extra goal)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. `encodePayloadTester <input> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input. The
# ---- method has NO `require` clause, so the tester cannot short-circuit to
# ---- `true` on a precondition-false input: every witness input below is
# ---- genuinely in-domain. Checked in a file whose `prove_correct` block has
# ---- been stripped; the carrier is transparent, so every tester `decide`s.
def _witness(arg):
    return ("extract_program_for encodePayload\n"
            "prove_precondition_decidable_for encodePayload\n"
            "prove_postcondition_decidable_for encodePayload\n"
            "derive_tester_for encodePayload\n\n"
            f"example : encodePayloadTester ({arg}) = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of returning the
    # argument in one step, it CASE-SPLITS on the carrier's two alternatives
    # and rebuilds each from its own payload — a different control-flow shape
    # with identical values on every input. The frozen `loom_solve` still
    # closes the byte-identical obligation. Verified out-of-band, real build.
    # =====================================================================
    {
        "id": "pos-match-rebuild",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    match data with\n"
            "    | .text s => return .text s\n"
            "    | .binary b => return .binary b"),
        "rationale": "structurally different CORRECT impl: it splits on the "
                     "carrier's two alternatives and reconstructs each from its "
                     "own payload, instead of returning the argument whole. "
                     "Observationally identical on every input — each branch "
                     "rebuilds the same constructor with the same sequence — so "
                     "`out = data` holds on the whole domain, KIND and CONTENT "
                     "alike. A faithful reshape MUST verify; if this could not, "
                     "the clause would be SPEC-TOO-STRONG, rejecting an impl "
                     "that differs from gold only in control-flow shape. This is "
                     "the port of the sibling's local-variable/branch reshape "
                     "positives, re-aimed at the constructor split this carrier "
                     "actually has.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — the sibling's `pos-serialize-locals`
    # shape: bind the payload into a local FIRST, then return the local, rather
    # than returning the argument directly. Same value, different executable
    # shape. Frozen proof unchanged. Verified out-of-band, real build.
    # =====================================================================
    {
        "id": "pos-let-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let r := data\n"
            "    return r"),
        "rationale": "the sibling's local-binding positive: the payload is bound "
                     "to an intermediate local and the local returned, instead of "
                     "the argument being returned directly. Identical value on "
                     "every input, so `out = data` still holds; only the "
                     "statement shape differs. Must verify, else SPEC-TOO-STRONG. "
                     "Keeps a second, independent correct shape in the lane so a "
                     "single positive's accidental success cannot carry the "
                     "defended half of the battery alone.",
    },
    # =====================================================================
    # ADMISSIBILITY — the sibling's two admissibility probes assert that the
    # precondition ADMITS a normal failing-test-shaped input. This method has NO
    # `require` clause, so admission is trivial and re-asserting it would test
    # nothing. The residual admissibility risk here is the OTHER half of the
    # sibling's argument: that the obligation is NON-DEGENERATE at that input —
    # that the failing-test-shaped payload (a binary payload carrying octets
    # OUTSIDE the coercion's own defined range) is genuinely distinguishable
    # from its coerced form, so `out = data` really does forbid the coercion
    # there rather than being satisfied by both. The impl is kept verbatim so
    # the method's own obligation still discharges; the proof is retuned ONLY to
    # clear the extra in-region `assert` goal (elided from the spec view). The
    # assert is LIVE — replacing it with the opposite claim leaves `decide`
    # reporting the proposition false, verified during authoring.
    # =====================================================================
    {
        "id": "admiss-f2p-binary-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((.binary [195, 182] : Payload) = (.binary [195, 182] : Payload) ∧\n"
            "       toNativeString (.binary [195, 182]) ≠ (.binary [195, 182] : Payload)))\n"
            "    return data",
            "prove_correct encodePayload by\n"
            "  loom_solve\n"
            "  all_goals decide"),
        "rationale": "the method has no `require` clause, so the sibling's "
                     "'is this input admitted' question is trivially yes; what "
                     "carries over is its second half — the obligation must be "
                     "NON-DEGENERATE at the failing-test-shaped input. The probe "
                     "constructs exactly that input (a binary payload whose "
                     "octets lie outside the coercion's own defined range) and "
                     "asserts both that it is in-domain and that it is DISTINCT "
                     "from its coerced form. That distinctness is what gives "
                     "`out = data` its teeth there: if the two collapsed, the "
                     "clause would be satisfied by the coercion as well and the "
                     "whole battery's reject lane would be empty of content. The "
                     "impl is kept verbatim so the method's own `ensures` "
                     "discharges alongside the assert.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Every rival is loop-free
    # so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-coerce-to-text",
        "kind": "uniqueness",
        "expect": "reject",
        # THE reported defect: route every payload through the native-string
        # coercion, so a binary payload comes back as a TEXT payload. Correct on
        # text input (the coercion is the identity there); wrong on every binary
        # input, of any length and any octet value.
        "module": _impl(
            "    let r ← pure (toNativeString data)\n"
            "    return r"),
        "refinement": "this is the pre-fix behaviour the issue reports: the "
                      "payload is handed to the native-string coercion instead of "
                      "being passed through, so a binary payload is silently "
                      "turned into a text payload. The failing test's sole "
                      "assertion is that the transmitted body is STILL the binary "
                      "alternative, which a coerced payload is not; and for "
                      "octets outside the coercion's defined range the real "
                      "counterpart raises instead of returning at all. Either way "
                      "the faithful real patch does NOT resolve, so a verifying "
                      "rival here would be a true verify-does-not-imply-resolve "
                      "break.",
        "rationale": "REJECT from `out = data` via the KIND sub-behaviour: the "
                     "coercion always yields the text alternative, but the clause "
                     "requires the returned payload to carry the SAME constructor "
                     "as the input, so the two differ on every binary input. "
                     "Verifying would be SPEC-TOO-WEAK — kind preservation, the "
                     "one property the failing test observes, would be unpinned. "
                     "Refuted at `.binary [65]`: gold returns that binary payload, "
                     "the rival a text payload. The point is deliberately a "
                     "SHORT, single-octet, IN-range binary payload so this "
                     "witness does not also cover the near-miss rival below — "
                     "that rival is CORRECT at this input (checked out-of-band), "
                     "so the two rejections are separately attributed.",
        "witness": _witness(".binary [65]"),
    },
    {
        "id": "weak-coerce-nonascii-only",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS: correct on EVERY text payload AND on every binary payload
        # whose octets lie inside the coercion's defined range; coerces only the
        # out-of-range binary payloads. Agrees with gold on strictly more of the
        # domain than the rival above, so it gets its own witness at the input
        # that distinguishes it.
        "module": _impl(
            "    let out := match data with\n"
            "      | .text s => .text s\n"
            "      | .binary b =>\n"
            "        if b.all (fun u => u < 128) then .binary b else toNativeString (.binary b)\n"
            "    return out"),
        "refinement": "a subtler real counterpart: pass the payload through "
                      "whenever the coercion would succeed on it, and coerce only "
                      "the remaining payloads. This is the most plausible wrong "
                      "patch of all, because it looks like it fixes the reported "
                      "case — yet the reported case IS an out-of-range binary "
                      "payload, so it is precisely the sub-domain this rival still "
                      "gets wrong. The failing test builds its body from exactly "
                      "such a payload and asserts the body is still binary, so the "
                      "faithful patch does NOT resolve. A rival this close to gold "
                      "verifying would mean the clause pins kind preservation only "
                      "on the easy half of the carrier.",
        "rationale": "REJECT from `out = data` via KIND, but on a strictly SMALLER "
                     "wrong sub-domain than the rival above: it preserves the "
                     "constructor everywhere except on binary payloads carrying an "
                     "out-of-range octet, where it returns the text alternative. "
                     "Refuted at `.binary [195, 182]` — the failing-test-shaped "
                     "input, and the point at which this rival and the wholesale "
                     "coercion coincide while every other point separates them. "
                     "Given its own witness rather than sharing one, so its "
                     "rationale's near-miss claim is demonstrated at the input "
                     "that actually discriminates it.",
        "witness": _witness(".binary [195, 182]"),
    },
    {
        "id": "weak-coerce-to-binary",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR defect, in the direction the reported bug did not go: force
        # every payload into the BINARY alternative. Correct on binary input,
        # wrong on every text input. Without this rival the KIND clause would be
        # attacked in one direction only.
        "module": _impl(
            "    match data with\n"
            "    | .text s => return .binary (s.map (fun c => UInt8.ofNat c.toNat))\n"
            "    | .binary b => return .binary b"),
        "refinement": "the mirror of the reported defect: rather than coercing "
                      "everything to the text alternative, coerce everything to "
                      "the binary one. This WOULD satisfy the failing test, whose "
                      "only assertion is that a binary payload stays binary — "
                      "which is exactly why it must be rejected on the spec "
                      "instead. It is not the faithful behaviour: a text payload "
                      "would be re-reported as binary, changing the transmitted "
                      "form for every text body and breaking the existing "
                      "currently-passing tests that send text payloads. So the "
                      "faithful patch resolves the one failing test while "
                      "regressing the suite, and does NOT resolve the instance.",
        "rationale": "REJECT from `out = data` via KIND in the OPPOSITE direction "
                     "to the reported defect: for a text input the rival returns "
                     "the binary alternative, contradicting the clause. This is "
                     "the port of the sibling's constant-tag rival, and it is the "
                     "only case that abuses the `.text` half of the binder's "
                     "constructor axis — without it a rival that mishandled text "
                     "payloads exclusively would verify unnoticed, since every "
                     "other reject case here probes a binary input. Refuted at "
                     "`.text ['h', 'i']`.",
        "witness": _witness(".text ['h', 'i']"),
    },
    {
        "id": "weak-drop-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Right KIND, wrong CONTENT: keep the constructor, discard the sequence.
        # Passes any check that looks only at which alternative came back, so it
        # isolates the CONTENT half of the clause from the KIND half.
        "module": _impl(
            "    match data with\n"
            "    | .text _ => return .text []\n"
            "    | .binary _ => return .binary []"),
        "refinement": "a counterpart that preserved the payload's kind but "
                      "dropped its contents would transmit an EMPTY body of the "
                      "right type. The failing test's assertion about the body's "
                      "type would pass, but the transmitted payload would no "
                      "longer be the caller's data at all — every currently-"
                      "passing test that round-trips a body's contents would "
                      "break. So the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = data` via the CONTENT sub-behaviour, "
                     "with KIND deliberately held CORRECT: the constructor "
                     "matches on every input, but the sequence is replaced by the "
                     "empty one, so the two payloads differ whenever the input is "
                     "non-empty. This is the port of the sibling's "
                     "content-dropping rival, and it is what keeps the clause's "
                     "content half from resting on the kind rivals — those all "
                     "change the constructor, so a spec that pinned ONLY the tag "
                     "would still reject them while admitting this one. Refuted at "
                     "`.binary [116, 101, 115, 116]`, a longer in-range binary "
                     "payload distinct from every other witness point.",
        "witness": _witness(".binary [116, 101, 115, 116]"),
    },
    {
        "id": "weak-reverse-content",
        "kind": "uniqueness",
        "expect": "reject",
        # Right KIND, right MULTISET of elements, wrong ORDER. A near-miss on the
        # CONTENT axis: agrees with gold on every palindromic and every
        # length-<=1 payload, so it is not subsumed by the content-dropping
        # rival, which is wrong on every non-empty input.
        "module": _impl(
            "    match data with\n"
            "    | .text s => return .text s.reverse\n"
            "    | .binary b => return .binary b.reverse"),
        "refinement": "a counterpart that preserved the payload's kind AND every "
                      "one of its elements but emitted them in reverse order "
                      "would transmit a body of the right type and the right "
                      "length whose bytes are permuted. Nothing about the type "
                      "assertion would notice, yet the body would not be what the "
                      "caller supplied, so the currently-passing tests that check "
                      "a transmitted body's actual contents would break. The "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = data` via CONTENT ORDER specifically — "
                     "the sharpest content probe in the lane, since it gets the "
                     "constructor, the length AND the element multiset right and "
                     "differs only in sequencing. It is a genuine near-miss "
                     "(correct on every payload of length <= 1 and every "
                     "palindrome), so it is not subsumed by the content-dropping "
                     "rival, and a spec that pinned only kind-plus-length would "
                     "admit it. Refuted at `.text ['a', 'b', 'c']` — a text "
                     "payload, so this case also varies the binder's constructor "
                     "axis while attacking the content axis, at a length no other "
                     "witness uses.",
        "witness": _witness(".text ['a', 'b', 'c']"),
    },
    {
        "id": "weak-text-octet-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Right KIND, right LENGTH, right ORDER, and correct on
        # every text payload whose code points fit in a single octet — it round-
        # trips each code point through the octet range, which is the identity
        # below 256 and truncates above it. The narrowest wrong sub-domain in the
        # lane: every other text witness here uses ASCII, where this rival AGREES
        # with gold, so nothing else in the battery reaches this sub-domain.
        "module": _impl(
            "    match data with\n"
            "    | .text s =>\n"
            "      return .text (s.map (fun c => Char.ofNat (UInt8.ofNat c.toNat).toNat))\n"
            "    | .binary b => return .binary b"),
        "refinement": "a counterpart that narrows each code point of a text "
                      "payload to a single octet before transmitting keeps the "
                      "payload's kind, its length and its ordering, and is exactly "
                      "right on the whole single-octet range — so it passes the "
                      "type assertion and every content check whose payload stays "
                      "in that range. Above it the transmitted character is a "
                      "different one, so a currently-passing test that round-trips "
                      "a text body outside the single-octet range breaks. The "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from `out = data` via CONTENT, on the one sub-domain "
                     "no other case in this battery touches: the value of a text "
                     "payload's code points. The three other text-facing cases are "
                     "refuted at ASCII characters, where this rival is CORRECT "
                     "(machine-checked: its witness at `.text ['h', 'i']` and at "
                     "`.text ['a', 'b', 'c']` FAILS against this rival), so it is "
                     "not subsumed by any of them, and a spec that pinned kind, "
                     "length and order but not the element VALUES would admit it. "
                     "Refuted at `.text ['中']`, a code point above the octet "
                     "range — an input no other witness uses. Audit-verified with "
                     "real builds: rival module rejected, witness elaborates "
                     "against the rival (exit 0) and is refuted against the frozen "
                     "solution by plain evaluation (exit 1, `decide` proves the "
                     "proposition false).",
        "witness": _witness(".text ['中']"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (3
# frame-mutation, 3 partial-domain/tag-swap rivals, 1 content-drop rival, 2
# soundness positives, 2 admissibility — 11 counting both admissibility probes)
# plus a 2-case AXIOM lane. It contracts TWO functions over a `Value(is_bytes,
# data)` record with a PSeq carrier, plus a `to_native` @Pure @ContractOnly
# axiom.
#
# This bundle models ONE of those two functions. The sibling's
# `normalize_query_string` corresponds to the gold's SECOND hunk, which
# refinement.md §B records as deliberately NOT modeled here: it is
# behaviour-preserving and not pinned by the failing test, so there is no
# `prove_correct` for it and no obligation to defend or attack. That is carrier
# narrowing, not an omission — chasing case-count parity would mean fabricating
# rivals against a behaviour this bundle does not model. Every case below
# therefore attacks or defends the single modeled obligation.
#
#   sibling case                    -> here                          disposition
#   ---------------------------------------------------------------------------
#   frame-mut-serialize-data        -> (none)                        VACUOUS
#   frame-mut-serialize-tag         -> (none)                        VACUOUS
#   frame-mut-normalize-data        -> (none)                        VACUOUS
#   weak-serialize-native-decode    -> weak-coerce-to-text           PORTED
#   weak-serialize-flip-tag         -> weak-coerce-to-binary         PORTED
#   weak-normalize-preserve-tag     -> (none)                        NOT MODELED
#   weak-normalize-drop-content     -> weak-drop-content             PORTED (re-aimed)
#   pos-serialize-locals            -> pos-let-local                 PORTED
#   pos-normalize-direct            -> pos-match-rebuild             PORTED (re-aimed)
#   admiss-serialize-binary-nonascii-> admiss-f2p-binary-nondegenerate PORTED (re-aimed)
#   admiss-normalize-binary-ascii   -> (none)                        NOT MODELED
#   (no sibling)                    -> weak-coerce-nonascii-only     ADDED
#   (no sibling)                    -> weak-reverse-content          ADDED
#   (no sibling)                    -> weak-text-octet-truncate      ADDED (audit)
#   AXIOM_TESTS (2 cases)           -> (none)                        DROPPED (G-AX)
#   divergence / non-termination     -> (none)                       SPEC-CLOSED
#
# Of the 8 sibling cases attached to the MODELED function, all 8 ported; 2
# rivals added; 2 cases belong to the unmodeled second site; the 3-case
# frame class is vacuous; the 2-case axiom lane is out of scope.
#
# PORTED (rivals): weak-serialize-native-decode is the sibling's central case —
#   the pre-patch coercion — and ports directly as weak-coerce-to-text, with the
#   same two-pronged argument (wrong kind returned, and the coercion is not even
#   defined on the reported payload). weak-serialize-flip-tag forced the tag to a
#   constant; here the carrier is a constructor rather than a boolean field, so
#   the faithful analogue is coercing into the binary alternative
#   (weak-coerce-to-binary), which keeps the sibling's "correct only on one
#   sub-domain, breaks the other" structure intact.
# PORTED-RE-AIMED (weak-drop-content): the sibling returned native text with an
#   empty PSeq at its query site. That site is unmodeled here, but the rival's
#   ARGUMENT — right kind, dropped content — applies verbatim to the modeled
#   obligation, so it is re-aimed at this method and given its own witness. This
#   is the only case that isolates CONTENT while holding KIND correct.
# PORTED (positives): pos-serialize-locals ports as-is (bind a local, return it).
#   pos-normalize-direct inlined a call to remove an intermediate; the modeled
#   impl here has no call to inline, so the equivalent-shape-different-control-flow
#   positive is re-aimed at the carrier's constructor split (pos-match-rebuild).
#   Both verified out-of-band with real builds under the UNCHANGED frozen proof —
#   neither needed the obligation weakened, and no soundness positive was dropped
#   for an unclosable proof.
# PORTED-RE-AIMED (admissibility): the sibling asserts its precondition admits a
#   freshly built failing-test-shaped payload. This method has NO `require`
#   clause, so admission is vacuous and re-asserting it would test nothing; the
#   probe is re-aimed at the load-bearing half of the sibling's argument, that
#   the obligation is NON-DEGENERATE at that input (the payload is genuinely
#   distinct from its coerced form). The sibling's second admissibility probe
#   targets the unmodeled site.
# ADDED (weak-coerce-nonascii-only): no sibling counterpart. The sibling's
#   coercion rival is refuted partly by an unestablished ASCII precondition,
#   machinery this backend does not have — so on this carrier the natural
#   "fix only the payloads the coercion chokes on" patch is a reachable rival the
#   sibling never had to consider. It agrees with gold on strictly more of the
#   domain than any other case here, which is exactly why it is included and
#   given a separating witness rather than folded into weak-coerce-to-text.
# ADDED (weak-reverse-content): no sibling counterpart. The sibling's only
#   content rival empties the payload, which is wrong on every non-empty input; a
#   spec pinning kind-plus-length would still catch it. Order-permutation is the
#   near-miss that survives such a spec, so it is added to keep the CONTENT half
#   of the clause defended at its sharpest point.
# ADDED BY AUDIT (weak-text-octet-truncate): no sibling counterpart. The three
#   other text-facing cases are all refuted at ASCII characters, so the VALUE of a
#   text payload's code points was the one sub-domain the battery left unattacked:
#   a rival preserving kind, length and order while narrowing each code point to a
#   single octet agrees with every other witness point here and would have been
#   caught by nothing. Refuted at a code point above the octet range. Its rival
#   module and both witness builds were run for real during the audit.
# DROPPED (AXIOM_TESTS): the sibling's 2-case lane probes its `to_native` axiom
#   against the real callee. This bundle declares NO consumed axioms — the
#   coercion is a transparent deep model, whose agreement with the real callee is
#   axiom_check.py's business (G-AX, A-reference). Nothing here rests on an
#   axiom, and this gate ignores AXIOM_TESTS regardless.
# VACUOUS (frame-mutation, 3 cases): the sibling's largest class, and structurally
#   uncrossable. Those rivals WRITE a read-only input field and expect rejection
#   from the fractional-permission system before the postcondition is considered.
#   This backend has no heap, no aliasing and no permissions; `data` is an
#   immutable value and the method declares no `mut` binder, so there is no
#   read-only cell to clobber. No substitute probe is fabricated. DEMONSTRATED
#   during the audit rather than asserted: the analogue rival (`data := data`
#   spliced into the impl region, the direct translation of the sibling's
#   frame-mut-serialize-data) does not reach the postcondition at all — it fails
#   at PARSE time with "`data` cannot be mutated, only variables declared using
#   `let mut` can be mutated". A case built on it would be rejected for a syntax
#   error rather than by the spec, which is precisely the tactic-mismatch
#   attribution the witness requirement exists to forbid, so no witness can make
#   it a real reject case.
# CLOSED BY THE SEMANTICS (divergence): NOT ported, and NOT a hole here -- see the
#   DEFENDED SURFACE note above. This bundle is `total`, under which a
#   postcondition is claimed of ALL runs and every loop owes a decreasing measure.
#   (An earlier version cited an internal findings doc's split between a `partial`
#   cohort and a `total` one; that census is withdrawn, since all 500 velvet
#   bundles set "total".) Verified
#   with a real build: a `while True do pure ()` prefix is REJECTED
#   (`Decreasing annotations are required in total correctness semantics`), so the
#   diverging rival does not satisfy `out = data` and there is nothing to fix on
#   the frozen artifact. It is still not shippable as a reject case, because the
#   diverging rival's tester does not reduce and the witness cannot elaborate
#   against it (`witness-unproven`, inconclusive) — a mechanical limit on the
#   witness, not a weakness of the spec.
#
# BINDER / CLAUSE COVERAGE of the 6 reject witnesses (pts = 6 distinct points,
# no two rivals sharing an input):
#     data, constructor axis — `.binary` at 3 points, `.text` at 3. BOTH
#       alternatives are probed, so neither half of the KIND clause rests on the
#       other: weak-coerce-to-binary, weak-reverse-content and
#       weak-text-octet-truncate are refuted at text payloads, the rest at binary
#       payloads.
#     data, content axis — lengths 1, 2, 2, 3, 4; octets both inside the
#       coercion's defined range (`[65]`, `[116,101,115,116]`) and outside it
#       (`[195,182]`, the failing-test shape); a non-palindromic text sequence for
#       the order probe. Length, elements and order are each varied.
#   Both sub-behaviours of the single top-level clause are attacked: KIND in both
#   directions (weak-coerce-to-text, weak-coerce-to-binary) plus on its hardest
#   sub-domain (weak-coerce-nonascii-only), and CONTENT both wholesale
#   (weak-drop-content) and at its near-miss margin (weak-reverse-content).
#   The one modeled obligation is both defended (2 soundness + 1 admissibility)
#   and attacked (5 rivals).
AXIOM_TESTS = []
