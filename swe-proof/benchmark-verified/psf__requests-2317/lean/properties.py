"""properties.py — G-PBT falsification battery for psf__requests-2317 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
case is a COMPLETE ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte: region surgery touches only text inside ``-- impl-start`` /
``-- impl-end`` (and, for the admissibility case, inside ``-- proof-start`` /
``-- proof-end``), so ``markers.same_spec`` holds by construction and the single
``theorem correct_normalizeMethod`` STATEMENT stays byte-identical. No case adds
an ``axiom``/``theorem``/``lemma`` and none reaches for
``sorry``/``admit``/``native_decide``.

``expect="verify"`` passes iff the variant elaborates with the obligation closed;
``expect="reject"`` passes iff the variant does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``), which is the design document, not the text to
translate. The nagini bundle models the carried token as a mutable ``List[int]``
of character/byte values plus a text-vs-bytes tag, and pins the result to that
carried sequence under a HALF-permission read-only frame. This Lean bundle models
the SAME single purely-functional core over a referentially transparent carrier:
one inductive value carrying either the supplied characters or the supplied raw
bytes, and one postcondition equation. Every nagini case that has a counterpart
on this carrier is re-expressed below; the nagini frame/permission-mutation lane
is VACUOUS here and the reasons for every omission are recorded in the
accounting block at the bottom.

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_normalizeMethod method result`` pins EXACTLY

    result = (nativeContent method).map Char.toUpper

a single top-level equation with no free output component. It composes two
behavioral requirements, and a rival can be wrong about either:

  * (B1 CONTENT) ``nativeContent method`` — the result carries the TEXTUAL
    CONTENT of the supplied token: the supplied characters for a text token, and
    for a raw byte token the characters those bytes denote — NOT a printable
    description of the token object. This is the behavior the instance is about,
    and it is the component the nagini sibling's dominant clause
    (result == the carried sequence) corresponds to.
  * (B2 CANONICAL CASE) ``.map Char.toUpper`` — the carried content is
    canonicalized to upper case, position by position. The nagini carrier does
    NOT model this component at all (its dominant clause is bare sequence
    equality), so the rivals attacking B2 are ADDED here rather than ported; see
    the accounting block.

Because the equation is element-wise, it also pins LENGTH and ORDER: a rival that
drops, adds, or permutes a position is refuted even when it keeps every character
it emits correct.

BINDER STRUCTURE. The spec predicate has exactly ONE input binder, ``method``,
and the frozen obligation quantifies over it with NO precondition hypothesis —
the modeled behavior is total, so every value of the binder is in-domain. A
single binder cannot be "held fixed while others vary", so what discrimination
means here is that the witnesses must move ``method`` across the axes the spec's
two components actually turn on. They do (see the point-spread block): both
constructors (text and raw bytes), the empty token and lengths 1/3/4, content
that is already upper case and content that is not.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling calls this its
    MANDATORY lane and its #1 weakness class, because there the supplied token is
    a mutable list held under half permission and a rival can try to satisfy the
    postcondition by WRITING the caller's token. This backend is referentially
    transparent: the supplied token is an immutable value, there is no fractional
    permission, no aliasing, no mutable input binder and no cell for a rival to
    overwrite. Both nagini frame rivals are therefore inexpressible here, and no
    substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE on this carrier, measured both
    ways. There is no ``loom.semantics.termination`` option in play: the frozen
    ``implementation_*`` is a plain total Lean ``def``, so Lean's own elaborator
    discharges termination. A diverging rival written as a total ``def`` is
    therefore rejected before the spec is ever consulted (``fail to show
    termination ... it is unchanged in the recursive calls``) — a rejection that
    attributes nothing to the SPEC — and the refutation witness cannot be built
    against it either, because the witness file carries the same non-terminating
    definition and fails to elaborate for the identical reason, so the
    rival-side half of the discrimination check never succeeds. Written instead
    as a ``partial def``, the rival compiles but the definition becomes OPAQUE:
    the witness's ``unfold`` fails (``Tactic `unfold` failed to unfold
    `implementation_normalizeMethod` ``), so nothing is decided and the case
    would be ``witness-undecided``. Neither form yields a witness whose failure
    tracks the claim, so no divergence rival is shipped — this is a carrier
    limit, not an untested spec force: every value-level force of the equation
    is attacked by the rivals below. The nagini sibling carries no such case
    either.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason the nagini sibling
    gives: the postcondition is GROUNDED in the input. ``result`` is pinned to a
    transparent function OF the supplied token, spelled out by cases, with no
    ``opaque`` callee and no axiomatized answer key an implementation could echo
    while doing nothing. Producing the content IS doing the work. In its place
    the battery carries honest cheapest-implementation positive controls.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Every rival
    below is correct on part of the domain and diverges exactly where one of B1 /
    B2 bites: rendering a byte token as a description of the object (correct on
    every text token); dropping the final position (correct on the empty token
    and on every proper prefix); inventing a character for the empty token
    (correct on every non-empty token); pinning position 0 to a fixed character
    (correct whenever the token already starts with it); omitting the case
    canonicalization (correct on already-upper content); canonicalizing only the
    LEADING position (correct on already-upper content and on every token of
    length at most one); and reversing the order (correct on palindromic
    content).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is ``intro``/``unfold``/``rfl``,
tuned to the frozen form — so a rejection ALONE attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at ONE concrete token and refuting it: ``unfold`` the spec, the
implementation and the content selector, then ``decide``. The carrier is fully
transparent (a concrete inductive value over character and byte literals), so no
witness needs to CONDITION on anything: every witness head binds NOTHING, hence
there are no hypotheses whose joint satisfiability could be in question. Each was
checked with two real builds — it holds of its rival and FAILS on the frozen
solution — so it discriminates rather than asserting a tautology.

REFINEMENT. Each reject case records why its faithful real counterpart would NOT
resolve the FAIL_TO_PASS set, so a rival that verified would be a true
verify-does-not-imply-resolve break rather than an artifact. The modeled output is
the method value finally stored on the outgoing request, so a faithful
counterpart of any rival below is a normalization step that stores a DIFFERENT
method token than the one named; the request is then directed at a method the
server does not treat as the one requested, and the F2P assertions that the
response is ok cannot hold.

AXIOM lane: DROPPED. The nagini sibling ships ``AXIOM_TESTS = []`` and this
bundle likewise declares no ``opaque`` callee and consumes no ``axiom`` (both
modeled operations are modeled deeply), so there is nothing to falsify; the axiom
lane belongs to G-AX and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "psf__requests-2317"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (checked by _swap on every use, so the manifest breaks loudly
# if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# The whole frozen impl-region BODY, comments included (the comments are inside
# `-- impl-start`/`-- impl-end`, so each variant carries its own accurate note
# without touching the spec view).
_IMPL = """\
  -- Recover the textual content of the supplied token (decoding a byte token to
  -- its characters), then upper-case it.
  let mut m := nativeContent method
  m := m.map Char.toUpper
  return m"""

# The frozen proof body's first line — inside `-- proof-start`/`-- proof-end` —
# so the admissibility case can prepend a ground `have` while leaving the
# `theorem correct_normalizeMethod` STATEMENT byte-identical.
_P_INTRO = "  intro method"

# The frozen proof body, for the two positives that legitimately re-prove a
# reshaped implementation.
_PROOF = """\
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  rfl"""


def _impl(body):
    """A full Solution.lean with the impl-region body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_proof(body, proof):
    """A full Solution.lean with the impl body AND the proof body replaced.

    Only text strictly inside the impl and proof regions changes, so same_spec
    holds and the obligation's statement is untouched — only its tactic body.
    """
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, proof)


def _witness(token, expr=None):
    """State the spec predicate at ONE concrete token and refute it.

    `token` is a ground `PyMethod` literal, so the goal is fully transparent and
    `decide` settles it: it holds of a rival whose output differs from the pinned
    value at that token and FAILS on the frozen solution, which satisfies the
    equation everywhere. Binds nothing, so there are no hypotheses to be
    inconsistent.
    """
    t = expr or token
    return (
        f"example : ¬ problem_spec_normalizeMethod {t}\n"
        f"    (implementation_normalizeMethod {t}) := by\n"
        "  unfold problem_spec_normalizeMethod implementation_normalizeMethod "
        "nativeContent\n"
        "  decide\n")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS — structurally different but CORRECT implementations that
# MUST verify, else SPEC-TOO-STRONG. Each re-proves honestly for its own shape
# with the frozen statement unchanged; no helper lemma, nothing assumed.
# ---------------------------------------------------------------------------

# pos-token-kind-split: split on the KIND of the supplied token into two arms
# that each recover their own content and canonicalize it. Ports the nagini
# is_bytes-split positive: it makes explicit that both kinds are handled on their
# own terms — a byte token by the characters its bytes denote, never by a
# description of the object.
_POS_SPLIT = """\
  -- Handle each kind of supplied token in its own arm: a text token carries its
  -- characters directly, a raw byte token the characters its bytes denote. Both
  -- arms canonicalize the recovered content to upper case.
  match method with
  | .text cs  => return cs.map Char.toUpper
  | .bytes bs => return (bs.map (fun b => Char.ofNat b.toNat)).map Char.toUpper"""

_POS_SPLIT_PROOF = """\
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  cases method <;> rfl"""

# pos-fused-recovery: same two arms, but the byte arm FUSES recovery and
# canonicalization into a single traversal instead of two. A different
# executable shape computing the same value — the analogue of the nagini
# positive that changes only how the result is accumulated.
_POS_FUSED = """\
  -- Same behavior, different traversal shape: the byte arm recovers each
  -- character and canonicalizes it in a single pass instead of two.
  match method with
  | .text cs  => return cs.map Char.toUpper
  | .bytes bs => return bs.map (fun b => Char.toUpper (Char.ofNat b.toNat))"""

_POS_FUSED_PROOF = """\
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  cases method
  · rfl
  · simp [nativeContent, List.map_map]"""

# admiss-ground-token: the implementation is the frozen one; the proof body is
# prepended with a ground `have` discharging the obligation's predicate at an
# F2P-shaped supplied token (a raw byte token spelling a lower-case method), then
# the frozen obligation is closed verbatim. Ports the nagini admissibility case,
# which asserts the postcondition SHAPE on a normal in-domain token: it shows the
# modeled behavior is SATISFIABLE at exactly such an input, so the obligation is
# not vacuous there.
_ADMISS_PROOF = """\
  have _ground : problem_spec_normalizeMethod (PyMethod.bytes [103, 101, 116])
      (implementation_normalizeMethod (PyMethod.bytes [103, 101, 116])) := by
    unfold problem_spec_normalizeMethod implementation_normalizeMethod
      nativeContent
    decide
  intro method"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — wrong implementations sharing the FROZEN spec that must be
# REJECTED, each with a witness pinning the violation at one concrete token.
# ---------------------------------------------------------------------------

# weak-object-render: a raw byte token is rendered as a printable DESCRIPTION of
# the token object (the characters `b` and `'`, the token's characters, a closing
# `'`) instead of the characters its bytes denote. A text token is unaffected.
# This is the behavior the instance is about, and the same rival the nagini
# sibling ports from its prepatch model.
_WEAK_RENDER = """\
  -- Adversary: a raw byte token is rendered as a printable description of the
  -- token OBJECT — the characters `b` and `'`, then the token's characters, then
  -- a closing `'` — instead of the characters its bytes denote. A text token is
  -- unaffected, so this is wrong only on the byte-token sub-domain.
  let mut m := match method with
    | .text cs  => cs
    | .bytes bs => ['b', '\\''] ++ bs.map (fun b => Char.ofNat b.toNat) ++ ['\\'']
  m := m.map Char.toUpper
  return m"""

# weak-drop-last: off-by-one — every position but the LAST is carried over.
# Vacuously correct on the empty token and on every proper prefix.
_WEAK_DROP_LAST = """\
  -- Adversary: off-by-one — carry every position but the last. Correct on the
  -- empty token and on every proper prefix, wrong at the final position of any
  -- non-empty token.
  let mut m := nativeContent method
  m := m.take (m.length - 1)
  m := m.map Char.toUpper
  return m"""

# weak-invent-empty: correct on every non-empty token, but invents a character
# for the EMPTY one. Partial-domain on the length-0 boundary.
_WEAK_INVENT_EMPTY = """\
  -- Adversary: for the EMPTY supplied token invent a single character instead of
  -- carrying nothing. Correct on every non-empty token.
  let mut m := nativeContent method
  if m.isEmpty then
    return ['G']
  m := m.map Char.toUpper
  return m"""

# weak-pin-first: correct everywhere except position 0, which is pinned to a
# fixed character. The identity whenever the token already starts with it.
_WEAK_PIN_FIRST = """\
  -- Adversary: pin position 0 to a fixed character instead of carrying the
  -- supplied one. The identity whenever the token already starts with that
  -- character, wrong at position 0 otherwise.
  let mut m := nativeContent method
  m := m.map Char.toUpper
  match m with
  | []      => return m
  | _ :: cs => return 'G' :: cs"""

# weak-no-canonical-case: recovers the content correctly (so it is right about
# the component the instance is about) but omits the case canonicalization.
# Correct on every token whose content is already upper case.
_WEAK_NO_UPPER = """\
  -- Adversary: recover the textual content correctly but omit the canonical-case
  -- step, storing the content in whatever case it was supplied. Correct on every
  -- token whose content is already upper case.
  let mut m := nativeContent method
  return m"""

# weak-capitalize-only: canonicalizes only the LEADING position — capitalizes the
# recovered content instead of upper-casing all of it. The strongest near-miss in
# the lane: it is correct about B1 content, correct about B2 at position 0, and
# agrees with the spec on every token of length <= 1 and on all already-upper
# content. Only a token with a lower-case character at position >= 1 separates it.
_WEAK_CAPITALIZE = """\
  -- Adversary: canonicalize only the LEADING position instead of every position,
  -- i.e. capitalize the recovered content rather than upper-casing it. Correct on
  -- content that is at most one character long and on already-upper content,
  -- wrong at every later lower-case position.
  let m := nativeContent method
  match m with
  | []      => return []
  | c :: cs => return Char.toUpper c :: cs"""

# weak-reversed-order: carries exactly the right characters, canonicalized, but
# in the opposite ORDER. Correct on palindromic content; refuted by the
# element-wise (positional) pin.
_WEAK_REVERSE = """\
  -- Adversary: carry exactly the right characters, canonicalized, but in the
  -- opposite order. Correct on palindromic content, wrong otherwise.
  let mut m := nativeContent method
  m := m.map Char.toUpper
  m := m.reverse
  return m"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — MUST verify.
    # =====================================================================
    {
        "id": "pos-token-kind-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_SPLIT, _POS_SPLIT_PROOF),
        "rationale": (
            "structurally-different CORRECT implementation: instead of one "
            "content-recovery call followed by the canonicalization, it splits on "
            "the KIND of supplied token and each arm recovers its own content and "
            "canonicalizes it. It computes the same value on every input, so the "
            "single spec equation (B1 content + B2 canonical case) still holds; "
            "if it FAILS the spec rejects a faithful reshape => SPEC-TOO-STRONG. "
            "Re-proved honestly for the new shape (`cases method <;> rfl`) with "
            "the `theorem correct_normalizeMethod` statement byte-identical, no "
            "new axiom/lemma, nothing assumed. Ports the nagini kind-split "
            "positive, which makes the same point on its tag binder."
        ),
    },
    {
        "id": "pos-fused-recovery",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_FUSED, _POS_FUSED_PROOF),
        "rationale": (
            "second correct shape: the byte-token arm FUSES content recovery and "
            "case canonicalization into a single traversal instead of two, so the "
            "result is built by a different executable computation than the "
            "frozen one while agreeing with it everywhere. Must verify, else "
            "SPEC-TOO-STRONG. Re-proved for the fused shape (traversal-composition "
            "rewrite) with the statement byte-identical and no helper lemma. "
            "Ports the nagini positive that changes only how the result is "
            "accumulated."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, F2P-shaped
    # supplied token (the analogue of PRECOND-TOO-STRONG if it failed).
    # =====================================================================
    {
        "id": "admiss-ground-token",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_PROOF),
        "rationale": (
            "the frozen obligation quantifies over the token binder with NO "
            "precondition hypothesis, so admissibility here is that the pinned "
            "input->output relation is actually SATISFIABLE at a normal, "
            "F2P-shaped input rather than only vacuously true. The proof body is "
            "prepended with a ground `have` discharging the spec predicate BY "
            "EVALUATION at a raw byte token spelling a lower-case method (the "
            "shape the instance is about), then closes the frozen obligation "
            "verbatim. Nothing is assumed: no new declaration, statement "
            "byte-identical, the ground instance is a `have` inside the existing "
            "tactic body. Ports the nagini admissibility case, which asserts the "
            "postcondition shape on a normal in-domain token."
        ),
    },

    # =====================================================================
    # UNIQUENESS RIVALS — MUST be rejected, each with a discriminating witness.
    # =====================================================================
    {
        "id": "weak-object-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_RENDER),
        "refinement": (
            "this is the behavior the instance reports: a method supplied as a raw "
            "byte token is stored as a printable description of the token object "
            "rather than the characters it denotes, so the request is directed at "
            "a method name that is three characters longer than the one asked "
            "for and contains punctuation. A faithful counterpart storing that "
            "description sends a token the server does not recognize as the "
            "requested method and answers not-found, so the F2P assertion that "
            "the response is ok fails. Does NOT resolve — this is exactly the "
            "state of the tree before the change."
        ),
        "rationale": (
            "REJECT from B1 (content) of the single spec equation: the spec pins "
            "`result = (nativeContent method).map Char.toUpper`, i.e. for a byte "
            "token the characters its bytes denote, while the rival emits those "
            "characters wrapped in a description of the object — three positions "
            "LONGER for EVERY byte token, which the element-wise equation refutes "
            "on its own. It is NOT additionally wrong at position 0 for every byte "
            "token: a token whose content itself begins with the description's "
            "introducing character agrees there, and only the length (and the "
            "trailing positions) separate the two — so the length force is what "
            "carries this rival on the whole byte sub-domain, and the witness "
            "point below is one where position 0 differs too. Partial-domain: "
            "text tokens are handled correctly, so only the byte sub-domain "
            "discriminates. Refuted at a raw byte token spelling a lower-case "
            "three-character method. If it VERIFIED the spec would not sense the "
            "reported behavior at all => SPEC-TOO-WEAK."
        ),
        "witness": _witness("(PyMethod.bytes [103, 101, 116])"),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_LAST),
        "refinement": (
            "dropping the final position turns a three-character method into a "
            "two-character one. A faithful counterpart storing a truncated method "
            "sends a token that is not a method the server implements, so it "
            "answers with an error rather than the requested resource and the F2P "
            "assertions that the response is ok — and the redirect-history "
            "assertions, which depend on the method actually taking effect — "
            "fail. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the element-wise/positional force of the spec equation: "
            "`result` must equal the canonicalized content at EVERY position "
            "(hence also in length), but the rival's result is one position "
            "shorter for every non-empty token. Partial-domain: vacuously correct "
            "on the empty token and on every proper prefix, diverging only at the "
            "final position — a boundary a random-token fuzzer misses. Refuted at "
            "a TEXT token (a distinct binder shape from the byte-token rivals) "
            "with lower-case content."
        ),
        "witness": _witness("(PyMethod.text ['g', 'e', 't'])"),
    },
    {
        "id": "weak-invent-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_INVENT_EMPTY),
        "refinement": (
            "inventing a character for the empty supplied token synthesizes a "
            "method the caller never named. A faithful counterpart doing this "
            "does not carry the supplied token's content — it substitutes its own "
            "when the token is empty — so it is not a faithful normalization of "
            "the supplied method, and any caller that supplies an empty token has "
            "a different method sent than the one it asked for. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the spec equation on the length-0 sub-domain: the spec "
            "pins the empty result for an empty token, while the rival returns a "
            "one-character result (so both the positional pin and the induced "
            "length agree fail). Partial-domain on exactly the empty boundary — "
            "correct on every non-empty token. Refuted at the EMPTY raw byte "
            "token, a distinct point from every other witness."
        ),
        "witness": _witness("(PyMethod.bytes [])"),
    },
    {
        "id": "weak-pin-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PIN_FIRST),
        "refinement": (
            "pinning position 0 to a fixed character rewrites the first letter of "
            "every method that does not already start with it, so a caller asking "
            "for one method has a different one sent. A faithful counterpart "
            "normalizing the leading position that way changes which operation "
            "the server performs — the F2P cases that submit bodies and follow "
            "redirects depend on the requested method being the one that takes "
            "effect, so they fail. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the element-wise pin at ONE position: the spec forces "
            "`result` to equal the canonicalized content at every position, so a "
            "single mismatched position refutes it. Partial-domain / NEAR-MISS: "
            "every position but the first is carried faithfully, and the rival is "
            "the identity on any token already starting with the pinned "
            "character — so it is refuted at a token whose first character is "
            "something else (a four-character lower-case TEXT token, distinct "
            "from every other witness point)."
        ),
        "witness": _witness("(PyMethod.text ['p', 'o', 's', 't'])"),
    },
    {
        "id": "weak-no-canonical-case",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_UPPER),
        "refinement": (
            "this rival is RIGHT about recovering the token's content and wrong "
            "only about the canonical case, so its faithful counterpart stores the "
            "method in whatever case the caller supplied. Method tokens are "
            "canonicalized to upper case precisely because the wire form is "
            "case-significant: the F2P cases reach the modeled step through the "
            "convenience entry points, which name their method in lower case, so "
            "a counterpart that stored the supplied case would send a token the "
            "server does not treat as the named method and the assertions that "
            "the response is ok fail. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from B2 (canonical case) of the spec equation — the component "
            "the nagini carrier does not model at all (its dominant clause is "
            "bare sequence equality), so this rival is ADDED here rather than "
            "ported. The spec pins "
            "`result = (nativeContent method).map Char.toUpper`; the rival emits "
            "`nativeContent method` unchanged, which differs at every position "
            "whose supplied character is not already upper case. Partial-domain: "
            "correct on all already-upper content. Refuted at a raw byte token "
            "spelling a LOWER-CASE four-character method — the point that "
            "exercises B1 and B2 together, and distinct from the render rival's "
            "point. If it VERIFIED the spec would be weaker than written on the "
            "case component => SPEC-TOO-WEAK."
        ),
        "witness": _witness("(PyMethod.bytes [112, 111, 115, 116])"),
    },
    {
        "id": "weak-capitalize-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CAPITALIZE),
        "refinement": (
            "canonicalizing only the leading position stores a method token that "
            "is capitalized rather than upper-cased. A faithful counterpart that "
            "capitalized instead of upper-casing sends a token whose later "
            "characters keep the case the caller supplied; the wire form is "
            "case-significant, so the server does not treat it as the named "
            "method and answers with an error rather than the requested resource. "
            "The F2P assertions that the response is ok therefore fail — and the "
            "single-character-token case where this rival coincides with the "
            "correct behavior is not a method any of them names. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from B2 (canonical case) at a position OTHER than the first — "
            "the strongest near-miss in the lane, and the gap the other rivals "
            "leave open. weak-no-canonical-case omits the canonicalization "
            "entirely, so a spec that only checked position 0 would still catch "
            "it; this rival performs the canonicalization correctly at position 0 "
            "and skips it everywhere after, so it is refutable only by the "
            "element-wise force of `.map Char.toUpper` applying at EVERY position. "
            "Partial-domain / near-miss: it agrees with the spec on all "
            "already-upper content, on the empty token, and on every "
            "single-character token, so it is refuted at a raw byte token "
            "spelling a lower-case FOUR-character method whose divergence begins "
            "at position 1 — a token no other witness in the lane uses. If it "
            "VERIFIED, the spec would pin the case component only at the head "
            "=> SPEC-TOO-WEAK. ADDED by audit: the six shipped rivals left "
            "per-position canonicalization beyond the head unattacked."
        ),
        "witness": _witness("(PyMethod.bytes [104, 101, 97, 100])"),
    },
    {
        "id": "weak-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REVERSE),
        "refinement": (
            "carrying exactly the right characters in the wrong ORDER stores an "
            "anagram of the requested method. A faithful counterpart that emitted "
            "the token's characters reversed sends a name that is not a method at "
            "all, so the server answers with an error instead of the requested "
            "resource and the F2P assertions that the response is ok fail — "
            "including the byte-token case, whose token reversed is not the method "
            "it names. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the ORDER force of the element-wise equation: `result` "
            "must equal the canonicalized content POSITION BY POSITION, not merely "
            "carry the same multiset of characters, so a permutation is refuted "
            "even though the rival's length and character content are both right. "
            "Partial-domain: correct on palindromic content (and on the empty and "
            "single-character tokens), so it is refuted at a non-palindromic "
            "token — the raw byte token spelling the exact three-character "
            "upper-case method the reported case supplies, a point no other "
            "witness uses. ADDED here (the nagini rivals attack length and "
            "individual positions but never the ordering) so that no structural "
            "force of the equation is left unattacked."
        ),
        "witness": _witness("(PyMethod.bytes [71, 69, 84])"),
    },
]

# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 uniqueness rivals) plus
# an EMPTY axiom lane. This bundle models the SAME single purely-functional core,
# so nothing is dropped for carrier narrowing except the frame lane, which is
# inexpressible here. Every sibling case is recorded.
#
#   sibling case              -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-isbytes-split         -> pos-token-kind-split        PORTED (re-proved)
#   pos-append-shape          -> pos-fused-recovery          RE-EXPRESSED
#   admiss-shape              -> admiss-ground-token         RE-EXPRESSED
#   frame-mut-overwrite       -> (none)                      VACUOUS
#   frame-mut-extend          -> (none)                      VACUOUS
#   weak-prepatch-bytes       -> weak-object-render          PORTED
#   weak-truncate-last        -> weak-drop-last              PORTED
#   weak-pad-empty            -> weak-invent-empty           PORTED
#   weak-uppercase-first      -> weak-pin-first              PORTED
#   (none)                    -> weak-no-canonical-case      ADDED (B2)
#   (none)                    -> weak-capitalize-only         ADDED (B2 non-head)
#   (none)                    -> weak-reversed-order         ADDED (order)
#   AXIOM_TESTS (0)           -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED (pos-fused-recovery): the sibling's second positive changes how the
#   result is ACCUMULATED (element append vs list concatenation), a distinction
#   that does not exist on this carrier — there is no accumulator loop to reshape,
#   the result is a traversal of the recovered content. The faithful analogue of
#   "same values, different executable construction" is to FUSE the recovery and
#   the canonicalization into one traversal instead of two, which is what this
#   case does; it is re-proved honestly for the fused shape.
# RE-EXPRESSED (admiss-ground-token): the sibling's admissibility case asserts the
#   postcondition SHAPE inside the impl region, where its assertions are
#   proof-local, and its interesting content is that the PRECONDITION (an ASCII /
#   permission side condition) admits an F2P-shaped token. The frozen obligation
#   here carries NO precondition hypothesis — the modeled behavior is total — so
#   there is no precondition to probe for over-strength. The honest analogue is
#   to discharge the obligation's predicate by evaluation at exactly such a token,
#   showing the relation is satisfiable there and not vacuously true, then close
#   the frozen obligation verbatim.
# VACUOUS (frame-mut-overwrite, frame-mut-extend): the sibling's MANDATORY lane,
#   and the one class that does not survive the carrier change. There the supplied
#   token is a mutable list held under HALF permission and each rival tries to
#   satisfy the postcondition by writing it (element write / append), which the
#   permission system must refuse. This backend is referentially transparent: the
#   supplied token is an immutable value, there is no fractional permission, no
#   aliasing and no mutable input binder, so neither rival can even be written.
#   DEMONSTRATED rather than asserted: the closest expressible analogue on this
#   carrier is an impl that locally rebinds the input binder (`let mut method :=
#   method`, then reassigns it) before emitting the right answer — the only "write
#   the input" this carrier admits. That variant VERIFIES, because the rebinding is
#   local to the callee and unobservable to the caller, which is exactly why there
#   is no frame obligation here to violate: a rival cannot be REJECTED for a write
#   the semantics cannot see. Shipping it as an `expect="reject"` case would record
#   a false finding, and shipping it as a positive would only restate the existing
#   positives, so no substitute probe is fabricated.
# ADDED (weak-no-canonical-case, weak-capitalize-only, weak-reversed-order): not
#   fabricated for an unmodeled behavior — all three attack load-bearing force of
#   the SAME single frozen equation that the sibling's rivals happen to leave
#   alone. The sibling's dominant clause is bare sequence equality, so its carrier
#   has no case-canonicalization component to attack (B2), and none of its four
#   rivals permutes the sequence, so the equation's ORDER force went untested.
#   weak-capitalize-only was ADDED BY AUDIT: with only weak-no-canonical-case, the
#   case component was attacked solely by a rival that skips canonicalization
#   everywhere, which a spec pinning the case at position 0 alone would still
#   reject — so "the canonicalization applies at EVERY position" was the one force
#   of the equation no rival isolated. With these three, every structural force of
#   the equation — content, per-position value, length, order, and per-position
#   case — is attacked by some rival.
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT tokens (pts=7), and
# the sole spec binder `method` moves across every axis the equation turns on:
#
#   token                          rival                     force attacked
#   ---------------------------------------------------------------------------
#   bytes, 3 bytes, lower case     weak-object-render        B1 content
#   text,  3 chars, lower case     weak-drop-last            length / last posn
#   bytes, EMPTY                   weak-invent-empty         length-0 boundary
#   text,  4 chars, lower case     weak-pin-first            position 0
#   bytes, 4 bytes, lower case     weak-no-canonical-case    B2 canonical case
#   bytes, 4 bytes, lower case*    weak-capitalize-only      B2 beyond position 0
#   bytes, 3 bytes, UPPER case     weak-reversed-order       order
#
#   (*) a DIFFERENT four-byte lower-case token from weak-no-canonical-case's, so
#   no point is shared; what distinguishes the two cases is not the length but
#   which positions the rival gets wrong.
#
#   Constructor: 5 x bytes, 2 x text (both arms of the carrier, so a rival wrong
#   about only one kind is caught). Length: 0, 3, 3, 3, 4, 4, 4 (empty boundary
#   plus two non-empty lengths, so a length-sensitive rival cannot hide). Case of
#   the supplied content: 5 x strictly needs canonicalization ('get', 'get',
#   'post', 'post', 'head'), 2 x already canonical ('GET' and the empty token,
#   which is canonical trivially) — so neither a rival that skips the
#   canonicalization nor one that corrupts already-canonical content can hide. Of
#   the five needing canonicalization, 4 need it at a position BEYOND the head, so
#   a rival that canonicalizes only the leading position is caught too. No witness
#   point is reused and no axis of the binder is held constant across the lane.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# `opaque` callee and consumes no `axiom` (both modeled operations are modeled
# deeply), so there is nothing to probe and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
