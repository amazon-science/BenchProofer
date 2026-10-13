"""properties.py — G-PBT falsification battery for sympy__sympy-22456 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a positive that legitimately re-proves or adds
a ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a single-input domain, indexed by the
argument-passing convention):

  reconstructString (s : StringObj) : ReconCall → Option StringObj
      ∀ c : ReconCall, result c = some s

  An atomic string value carries its text intrinsically (``s.text : String``) and
  exposes NO positional children (``stringArgs s = []``). The modeled behavior is
  the argument-reconstruction round-trip: handing the value's reconstruction
  callable the value's OWN self-reported argument data. That data is published
  under TWO conventions the same value exposes about itself — a positional list
  (``expr.func(*expr.args)``) and a keyword mapping
  (``expr.func(**expr.kwargs())``) — and the clause is universally quantified
  over both. On each convention the round-trip must SUCCEED (the ``none`` failure
  branch is excluded) AND carry back EXACTLY the original value (its whole
  ``text`` field, unchanged). The results are fully determined by the input:
  nothing is left unconstrained.

  WHY THE QUANTIFIER IS LOAD-BEARING. An earlier revision of this spec modeled
  ONLY the positional convention. That admitted a rival which honours the data
  the value publishes positionally while REFUSING the data it publishes as
  keywords — a value whose two self-reports disagree about what its own
  reconstruction accepts. Such a rival satisfies a positional-only clause and is
  nonetheless wrong: the round-trip identity is a property of the value's
  reconstruction, not of one calling syntax. The ``convention-split`` rivals
  below are that attack point, and they are the reason the clause quantifies.
  Note the pin is on AGREEMENT, not on any particular keyword mapping: a value
  whose callable tolerates the keywords it publishes satisfies the clause just as
  a value that publishes none does, and ``pos-tolerant-callable`` is the control
  proving the clause does not over-fit to one of those spellings.

ADVERSARIAL READ of the nagini classes on this carrier (mapping.md):

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an input-write
    attack MANDATORY: its ``s`` is held at fractional (read-only) permission, and
    a rival that rebinds ``s.text`` or appends into the list contents is rejected
    for INSUFFICIENT PERMISSION rather than a wrong value. Lean is referentially
    transparent: ``s`` is a plain immutable ``StringObj`` value, there is no
    half-permission to violate and no aliasing to exploit, so both nagini frame
    rivals (``frame-mutate-overwrite-s``, ``frame-mutate-clear-contents``) have NO
    expressible instance here. No substitute is fabricated for them. This was
    CHECKED, not assumed: the closest expressible analogue (``let mut s := s;
    s := { text := "" }; return some s``, the nagini overwrite rival transcribed)
    rebinds a LOCAL copy, leaves the caller's ``s`` untouched, and so is
    observationally just "return a fixed empty-text carrier" — i.e. it is
    definitionally the ``weak-payload-constant`` rival already ported below, with
    the same witness refuting it. Landing it separately would add a second
    spelling of one attack point, not a new one, so it is dropped as vacuous.

  * THE PIN (nagini: ``ToSeq(Result().text) == ToSeq(s.text)``, element for
    element) — APPLIES, and is the bulk of the battery. On this carrier the atomic
    value is modeled by its ``text : String`` field directly, so element-wise text
    equality collapses into ``result c = some s`` (whole-value equality of the
    ``Option``) at each convention. The nagini text-loss rivals port along two
    axes the pin still forces here:
      - the ``Option`` CONSTRUCTOR: a round-trip that reports failure (``none``)
        instead of ``some``. This is the literal PRE-FIX behavior — the generic
        positional reconstruction has no positional argument to rebuild the text
        from, so the round-trip fails (the real pre-patch raises ``TypeError``).
        Nagini's ``partial-domain-prefix-empty`` (rebuild from the empty arg list)
        maps here to the ``none`` branch, since a "fresh empty carrier" is no
        longer distinct from failure once the text field is the whole payload.
      - the PAYLOAD: a round-trip that succeeds (``some``) but carries the WRONG
        value. Nagini's value/partial-domain rivals (``value-mask``,
        ``drop-last``, ``drop-first``) all state "the reconstructed text is not
        exactly ``s.text``", but they fail at DIFFERENT places and each is
        separately expressible here, so all four are ported rather than
        collapsed into representatives: a constant wrong text, a text truncated
        by one character (drop-last), a text missing its first character
        (drop-first), and a right-LENGTH/wrong-VALUES character mask. The last
        two matter independently: the mask is the probe that a length-only or
        length-plus-first-character pin would wrongly admit, and drop-first is
        the probe that a pin on a text's SUFFIX would wrongly admit. Each was
        built against its rival (witness elaborates) and against the frozen
        solution (witness fails, by evaluation).

  * CONVENTION SPLIT — APPLIES, and is the attack point the quantifier exists
    for. A rival may be RIGHT on one argument-passing convention and WRONG on
    the other, so a spec that pinned a single convention would admit it. Two are
    landed because they fail on opposite sides and a one-sided clause would
    admit exactly one of them: ``convention-split-keyword-fails`` (the
    positional-only rival, which is the recorded counterexample this battery was
    strengthened against) and ``convention-split-positional-fails`` (its mirror,
    which is the PRE-FIX shape). Their coexistence is what demonstrates the
    clause pins the round-trip per-convention rather than picking a favourite.
    A THIRD rival, ``convention-split-keyword-refused``, spells the same defect
    the way the real callee exhibits it: the value still publishes a
    reconstruction keyword while its callable admits no keyword at all, so its
    two self-reports disagree.

  * UNGROUNDED-ORACLE ECHO — N/A here exactly as on the nagini carrier: the only
    helper (``stringArgs``) returns the CONSTANT ``[]`` and is not an answer key
    for the result; the sole way to satisfy the pin is to reproduce ``s`` itself.
    The honest analogue is the cheapest-correct POSITIVE CONTROL below.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this carrier, demonstrated rather
    than asserted. This bundle sets NO ``loom.semantics.termination`` option (it
    is a plain Lean file, not a Velvet ``prove_correct`` bundle), so there is no
    partial-correctness reading under which a diverging impl could discharge the
    obligation vacuously. A self-recursive ``partial def`` rival WAS built to
    check this rather than argued: the ``partial`` keyword makes the definition
    OPAQUE to reduction, so the frozen ``unfold`` step fails
    (``Tactic `unfold` failed to unfold `implementation_reconstructString` ``) —
    the rival does not verify, so it is not a spec hole. It is also not a
    shippable reject case: the SAME unfolding failure blocks any witness stated
    over it (rebuilt: witness-vs-rival exits 1 with that identical unfold error,
    so the rival half of the discrimination check cannot pass), and
    ``partial`` is a banned assumption token for witnesses in any event. So the
    class is genuinely vacuous here — no diverging impl verifies, and none can
    be attributed to the spec.

  * AXIOM_TESTS — DROPPED (the axiom lane is G-AX's job; this gate ignores it).
    This bundle declares NO ``opaque`` / ``axiom`` and NO deep-model reference
    (mapping.md: G-AX is a skip); the reconstruction is modeled directly over the
    input, so there is no in-model axiom obligation for this gate to re-discharge.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases`` / ``rfl`` script is tuned to
the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a concrete literal input; each was built (against the
rival, must ELABORATE) and rebuilt (against the frozen solution, must FAIL) to
confirm it holds of its rival and discriminates against gold rather than
asserting a tautology. The carrier COMPUTES (``StringObj`` derives
``DecidableEq``, ``ReconCall`` derives ``DecidableEq`` and ``Fintype``, so the
universally quantified clause is decidable), so each witness unfolds the spec +
impl and closes with ``decide``; no conditioning on an opaque term is needed, so
no witness binds a hypothesis (all inputs are literals).

BINDER COVERAGE. The single input binder ``s`` is varied across the reject
witnesses, and every point is chosen because it is the one that BITES for its
rival, not merely to spell a different literal: refuted at ``{ text := "foobar" }``
(the ``none`` / pre-fix rival — also the F2P literal), at ``{ text := "a" }`` (the
constant-wrong-payload rival, whose empty-text carrier agrees with gold at
``""``), at ``{ text := "ab" }`` (the truncated-payload rival, invisible on empty
text and needing length ≥ 2 to be distinct from the constant rival), at
``{ text := "xy" }`` (the drop-first rival, which agrees with gold on empty text
and whose result is a strict SUFFIX) and at ``{ text := "abc" }`` (the
character-mask rival, which agrees with gold on empty text and on any all-``x``
text, so it needs a length ≥ 1 text containing a non-``x`` character). The three
convention-split rivals are refuted at ``{ text := "foobar" }``, ``{ text := "q" }``
and ``{ text := "kw" }``: they disagree with gold at EVERY input including the
empty text (the defect is which convention is honoured, not what the text is),
so their witnesses discriminate on the CONVENTION axis rather than the payload
axis — which is exactly the axis the payload witnesses cannot reach.
``pts`` = 8 distinct input points across 8 reject rivals, so the battery
demonstrates the clause's dependence on the constructor, on the full text
payload — position by position, not merely its length, its first character, or
its suffix — AND on every argument-passing convention rather than one of them.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22456"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen proof body, so every replacement
# lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=\n"
    "  fun c =>\n"
    "    -- The positional argument list the value reports about itself (empty for an\n"
    "    -- atomic value).\n"
    "    let args := stringArgs s\n"
    "    -- The keyword argument names the value reports about itself. An atomic value\n"
    "    -- publishes no reconstruction keywords, so the mapping is empty too.\n"
    "    let kwargNames : List String := []\n"
    "    -- The value's reconstruction callable. It consumes NO reconstruction data at\n"
    "    -- all and yields the value itself, so it admits exactly the empty positional\n"
    "    -- list and the empty keyword mapping — which is precisely the data the value\n"
    "    -- publishes under each convention.\n"
    "    let reconstructPositional : List StringObj → Option StringObj :=\n"
    "      fun pos => if pos.isEmpty then some s else none\n"
    "    let reconstructKeyword : List String → Option StringObj :=\n"
    "      fun kw => if kw.isEmpty then some s else none\n"
    "    -- Apply the callable to the value's own self-reported data, per convention.\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstructPositional args\n"
    "    | ReconCall.keyword => reconstructKeyword kwargNames"
)

_PROOF_GOLD = (
    "  intro s\n"
    "  unfold problem_spec_reconstructString implementation_reconstructString\n"
    "  intro c\n"
    "  cases c <;> rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted; update _PROOF_GOLD"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# The frozen proof script, reused verbatim by every rival whose shape it still
# closes. Rivals are not required to keep it — a rival that breaks it is
# rejected, and its witness is what makes that rejection attributable.
_HEAD = ("def implementation_reconstructString (s : StringObj) : "
         "ReconCall → Option StringObj :=\n  fun c =>\n")


# ---------------------------------------------------------------------------
# Rival / positive impl bodies (each a full impl region; only the impl changes,
# so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# NONE / PRE-FIX: the round-trip reports FAILURE on BOTH conventions. The generic
# positional reconstruction has no argument data to rebuild the text from, so it
# cannot reproduce the value and yields `none`. Correct on NO input (the spec
# always demands `some s`).
_NONE_IMPL = _HEAD + (
    "    let _args := stringArgs s\n"
    "    match c with\n"
    "    | ReconCall.positional => none\n"
    "    | ReconCall.keyword => none"
)

# PAYLOAD — CONSTANT WRONG VALUE: the round-trip succeeds (`some`) on both
# conventions but ignores the input entirely and returns a fixed empty-text
# carrier. Right constructor, wrong payload. Correct ONLY when `s.text = ""`.
_PAYLOAD_CONST_IMPL = _HEAD + (
    "    let _args := stringArgs s\n"
    "    let reconstruct : Unit → Option StringObj := fun _ => some { text := \"\" }\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstruct ()\n"
    "    | ReconCall.keyword => reconstruct ()"
)

# PAYLOAD — TRUNCATED VALUE: the round-trip succeeds but carries the input text
# with its final character dropped. Right constructor, payload off by one
# character. Agrees with gold only on empty text; diverges on every text of
# length >= 1 (analogue of nagini's drop-last / partial-domain rival).
_PAYLOAD_TRUNC_IMPL = _HEAD + (
    "    let _args := stringArgs s\n"
    "    let reconstruct : Unit → Option StringObj :=\n"
    "      fun _ => some { text := s.text.dropRight 1 }\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstruct ()\n"
    "    | ReconCall.keyword => reconstruct ()"
)

# PAYLOAD — DROP THE FIRST CHARACTER: the round-trip succeeds but carries the
# input text with its FIRST character dropped, so the reconstructed text is a
# strict SUFFIX of the original. Agrees with gold only on empty text. Distinct
# attack point from the truncated rival: a spec that pinned the text's suffix (or
# its length-minus-one prefix) would admit one and reject the other, so both are
# needed to show the pin is position-wise. Analogue of nagini's drop-first rival.
_PAYLOAD_DROPFIRST_IMPL = _HEAD + (
    "    let _args := stringArgs s\n"
    "    let reconstruct : Unit → Option StringObj :=\n"
    "      fun _ => some { text := s.text.drop 1 }\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstruct ()\n"
    "    | ReconCall.keyword => reconstruct ()"
)

# PAYLOAD — CHARACTER MASK (right LENGTH, wrong VALUES): the round-trip succeeds
# and returns a text of exactly the original LENGTH, but every character is
# replaced by a constant `x`. This is the value-level double-mask probe: a spec
# that pinned only the reconstructed text's LENGTH — or that compared texts by a
# proxy tolerant of disagreeing positions — would wrongly ADMIT it. Agrees with
# gold only on empty text or an all-`x` text. Analogue of nagini's
# value-mask-right-length-wrong-values rival.
_PAYLOAD_MASK_IMPL = _HEAD + (
    "    let _args := stringArgs s\n"
    "    let reconstruct : Unit → Option StringObj :=\n"
    "      fun _ => some { text := String.mk (s.text.data.map (fun _ => 'x')) }\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstruct ()\n"
    "    | ReconCall.keyword => reconstruct ()"
)

# CONVENTION SPLIT — KEYWORD FAILS. Honours the argument data the value publishes
# POSITIONALLY and refuses the data it publishes as KEYWORDS. This is the
# recorded counterexample the battery was strengthened against: a reconstruction
# callable wired to one calling syntax only. Correct on NO input.
_SPLIT_KEYWORD_FAILS_IMPL = _HEAD + (
    "    let args := stringArgs s\n"
    "    let reconstruct : List StringObj → Option StringObj := fun _ => some s\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstruct args\n"
    "    | ReconCall.keyword => none"
)

# CONVENTION SPLIT — KEYWORD REFUSED, the way the real callee exhibits it. The
# value still PUBLISHES a reconstruction keyword while its callable admits no
# keyword at all, so the value's two self-reports about its own reconstruction
# disagree and the keyword round-trip is refused. Correct on NO input.
_SPLIT_KEYWORD_REFUSED_IMPL = _HEAD + (
    "    let args := stringArgs s\n"
    "    -- the value still publishes its text as a reconstruction keyword\n"
    "    let kwargNames : List String := [\"text\"]\n"
    "    let reconstructPositional : List StringObj → Option StringObj :=\n"
    "      fun pos => if pos.isEmpty then some s else none\n"
    "    -- ...but the callable admits no keyword whatsoever\n"
    "    let reconstructKeyword : List String → Option StringObj :=\n"
    "      fun kw => if kw.isEmpty then some s else none\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstructPositional args\n"
    "    | ReconCall.keyword => reconstructKeyword kwargNames"
)

# CONVENTION SPLIT — POSITIONAL FAILS (the mirror, and the PRE-FIX shape).
# Honours the keyword data the value publishes and fails positionally, because
# the generic callable rebuilds from the data handed to it and the positional
# list is empty. Correct on NO input. Its coexistence with the two rivals above
# is what shows the clause does not privilege one convention.
_SPLIT_POSITIONAL_FAILS_IMPL = _HEAD + (
    "    let args := stringArgs s\n"
    "    let kwargNames : List String := [\"text\"]\n"
    "    let reconstructPositional : List StringObj → Option StringObj :=\n"
    "      fun pos => match pos with\n"
    "        | (a :: _) => some a\n"
    "        | []       => none\n"
    "    let reconstructKeyword : List String → Option StringObj :=\n"
    "      fun kw => if kw.isEmpty then none else some s\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstructPositional args\n"
    "    | ReconCall.keyword => reconstructKeyword kwargNames"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl. Rather
# than gate on the shape of the self-reported data, it rebuilds a FRESH carrier
# from the intrinsic text field on each convention (`some { text := s.text }`),
# which is equal to `some s` by structure eta. Same value on every input and
# every convention; statement byte-identical, no new lemma/axiom.
_POS_IMPL = _HEAD + (
    "    let _args := stringArgs s\n"
    "    let reconstruct : Unit → Option StringObj := fun _ => some { text := s.text }\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstruct ()\n"
    "    | ReconCall.keyword => reconstruct ()"
)

# POSITIVE CONTROL (soundness, ANTI-OVER-FIT): a correct impl whose reconstruction
# callable is TOLERANT of arguments — it accepts whatever data the value publishes
# under either convention, including a non-empty keyword mapping, and yields the
# value itself. This is the control proving the clause pins the AGREEMENT between
# what the value publishes and what its callable admits, NOT the particular
# spelling in which an atomic value publishes nothing. A clause over-fitted to
# "the keyword mapping is empty" would wrongly REJECT this correct alternative.
_POS_TOLERANT_IMPL = _HEAD + (
    "    -- reconstruction callable tolerant of any self-reported data: it consumes\n"
    "    -- whatever it is handed and yields the value itself.\n"
    "    let reconstructPositional : List StringObj → Option StringObj := fun _ => some s\n"
    "    let reconstructKeyword : List String → Option StringObj := fun _ => some s\n"
    "    match c with\n"
    "    | ReconCall.positional => reconstructPositional (stringArgs s)\n"
    "    -- the value publishes its text as a keyword and the callable admits it\n"
    "    | ReconCall.keyword => reconstructKeyword [\"text\"]"
)

# ADMISSIBILITY: the frozen impl+proof, with a ground instance discharged at the
# F2P-shaped input (a non-empty text token — the discriminating case the pre-fix
# round-trip breaks) BEFORE the frozen obligation, proving the modeled behavior
# is SATISFIABLE at exactly the input the F2P exercises, on every convention. The
# theorem STATEMENT is byte-identical; the ground instance is a `have` inside the
# existing tactic body; no new declaration/axiom/`sorry`.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_reconstructString { text := \"foobar\" }\n"
    "      (implementation_reconstructString { text := \"foobar\" }) := by\n"
    "    unfold problem_spec_reconstructString implementation_reconstructString\n"
    "    intro c\n"
    "    cases c <;> rfl\n"
    + _PROOF_GOLD
)


def _witness(text):
    """A witness stating the spec predicate is VIOLATED at a concrete literal
    input; unfold + `decide`. The clause quantifies over `ReconCall`, which
    derives `DecidableEq` and `Fintype`, so the quantified claim is decidable
    and no per-convention case split is needed in the witness."""
    return (
        f"example : ¬ problem_spec_reconstructString {{ text := {text!r} }}\n"
        f"    (implementation_reconstructString {{ text := {text!r} }}) := by\n"
        f"  unfold problem_spec_reconstructString implementation_reconstructString\n"
        f"  decide"
    ).replace("'", '"')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-fresh-carrier",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_IMPL),
        "rationale": (
            "a correct reshape that reconstructs a FRESH carrier from the intrinsic "
            "text field (`some { text := s.text }`) on each convention, instead of "
            "gating on the shape of the self-reported data, must satisfy "
            "`∀ c, result c = some s` (equal by structure eta, the structure having a "
            "single field); if it cannot, the spec is over-fit to the gold spelling "
            "(SPEC-TOO-STRONG). No new declaration, axiom, or assumption token, and "
            "the theorem STATEMENT is byte-identical."
        ),
    },
    {
        "id": "pos-tolerant-callable",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_TOLERANT_IMPL),
        "rationale": (
            "the ANTI-OVER-FIT control for the quantified clause. A correct value "
            "whose reconstruction callable TOLERATES the data it is handed — "
            "including a non-empty keyword mapping it publishes about itself — "
            "round-trips on every convention and so must verify. This is what keeps "
            "the clause a statement about AGREEMENT between what the value publishes "
            "and what its callable admits, rather than a pin on the particular "
            "spelling in which an atomic value publishes no keywords: a clause "
            "over-fitted to 'the keyword mapping is empty' would wrongly reject this "
            "correct alternative (SPEC-TOO-STRONG). Verified against the real repo: "
            "this is the shape of a reconstruction callable accepting any arguments, "
            "and the F2P test passes against it."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input. The frozen theorem
    # carries NO precondition hypothesis (the behavior is total, so `∀` is
    # unguarded), so nagini's precondition-admission probe has no binder to
    # attack; the honest analogue discharges the spec predicate at the F2P ground
    # input (a non-empty text token) inside the proof region, alongside the frozen
    # obligation.
    # =====================================================================
    {
        "id": "admiss-nonempty-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_GOLD, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a non-empty text "
            "token `foobar` — the discriminating case the pre-fix round-trip breaks) "
            "on every argument-passing convention, then the frozen obligation is "
            "closed verbatim. Verifies (else the spec is unsatisfiable at the normal "
            "input, the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
            "theorem STATEMENT is byte-identical, the ground instance is a `have` "
            "inside the existing tactic body, and no new declaration/axiom/`sorry` is "
            "introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-roundtrip-fails-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NONE_IMPL),
        "refinement": (
            "this IS the pre-fix behavior: the generic positional reconstruction has "
            "no argument data to rebuild the value's text from, so the "
            "round-trip cannot reproduce the value and reports FAILURE (the real "
            "pre-patch raises `TypeError`). Its faithful real patch is the UNPATCHED "
            "code, which FAILS the F2P identity `expr.func(*expr.args) == expr` (the "
            "round-trip does not return the original value). Definitively "
            "non-resolving — the literal pre-patch."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: the rival returns `none` "
            "on every convention, which is never `some s`, so the postcondition fails "
            "at EVERY input. If it verifies, the spec does not exclude the "
            "failed-round-trip branch (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("foobar"),
    },
    {
        "id": "weak-payload-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PAYLOAD_CONST_IMPL),
        "refinement": (
            "the round-trip succeeds (right constructor) but ignores the input and "
            "returns a fixed empty-text carrier — right shape, wrong payload. Its "
            "faithful real patch (a reconstruction callable that always yields an "
            "empty-text value) FAILS the F2P identity for any non-empty token: "
            "`func(*args)` would be the empty String, not the original. Faithful but "
            "non-resolving."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at `s = { text := \"a\" }` "
            "the rival returns `some { text := \"\" }` != `some s`. Refuted where the "
            "reconstructed value must carry a non-empty text; a spec that pinned only "
            "the constructor (round-trip 'succeeds') would wrongly admit it. If it "
            "verifies, the payload is unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("a"),
    },
    {
        "id": "weak-payload-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PAYLOAD_TRUNC_IMPL),
        "refinement": (
            "the round-trip succeeds but carries the input text with its final "
            "character dropped (off-by-one on the payload). It agrees with gold only "
            "on empty text; on every text of length >= 1 it under-copies. Its "
            "faithful real patch (a reconstruction dropping the final character) FAILS "
            "the F2P identity (e.g. reconstructs `'fooba'` for `'foobar'`). Faithful "
            "but non-resolving — the analogue of nagini's drop-last partial-domain "
            "rival."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at `s = { text := \"ab\" }` "
            "the rival returns `some { text := \"a\" }` != `some s`. Refuted at a "
            "length-2 text distinct from the other witnesses (the drop is invisible on "
            "empty text and needs length >= 2 to bite next to the constant rival), so "
            "the clause is shown to pin the WHOLE text payload element for element, "
            "not merely its length or its first character. If it verifies, the "
            "postcondition leaves the final character unpinned (partial-domain "
            "SPEC-TOO-WEAK)."
        ),
        "witness": _witness("ab"),
    },
    {
        "id": "weak-payload-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PAYLOAD_DROPFIRST_IMPL),
        "refinement": (
            "the round-trip succeeds but carries the input text with its FIRST "
            "character dropped, so the reconstruction is a strict SUFFIX of the "
            "original. It agrees with gold only on empty text; on every non-empty "
            "text it loses the leading character. Its faithful real patch (a "
            "reconstruction callable sourcing the text from all-but-the-first "
            "position) FAILS the F2P identity `expr.func(*expr.args) == expr` (it "
            "reconstructs `'oobar'` for `'foobar'`). Faithful but non-resolving — the "
            "analogue of nagini's drop-first partial-domain rival."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at `s = { text := \"xy\" }` "
            "the rival returns `some { text := \"y\" }` != `some s`. This is a DIFFERENT "
            "attack point from the truncated rival: that one loses the LAST character "
            "and this one the FIRST, so a postcondition pinning only the text's suffix "
            "(or only its leading prefix) would admit exactly one of the two. Together "
            "they show the clause pins the payload POSITION BY POSITION. If it "
            "verifies, the leading character is unpinned (partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": _witness("xy"),
    },
    {
        "id": "weak-payload-mask-right-length",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PAYLOAD_MASK_IMPL),
        "refinement": (
            "the round-trip succeeds and returns a text of exactly the original "
            "LENGTH, but every character is replaced by a constant `x` — right shape, "
            "right size, wrong content at every position. It agrees with gold only on "
            "empty text or an all-`x` text. Its faithful real patch (a reconstruction "
            "callable emitting a same-length run of a fixed character) FAILS the F2P "
            "identity (it reconstructs `'xxxxxx'` for `'foobar'`). Faithful but "
            "non-resolving — the analogue of nagini's value-mask rival."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at `s = { text := \"abc\" }` "
            "the rival returns `some { text := \"xxx\" }` != `some s`. This is the "
            "value-level double-mask probe, and it is the one attack the other payload "
            "rivals cannot make: every one of them changes the reconstructed text's "
            "LENGTH, so a spec that pinned only the length (or compared texts by any "
            "proxy tolerant of disagreeing positions) would reject them all while "
            "wrongly ADMITTING this one. Its rejection is therefore what shows the "
            "clause demands element-wise agreement rather than a size agreement. If it "
            "verifies, the text's CONTENT is unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("abc"),
    },
    {
        "id": "convention-split-keyword-fails",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SPLIT_KEYWORD_FAILS_IMPL),
        "refinement": (
            "the round-trip reproduces the value when handed the data the value "
            "publishes POSITIONALLY, and reports failure when handed the data it "
            "publishes as KEYWORDS — a reconstruction callable wired to one calling "
            "syntax only. Its faithful real patch supplies a reconstruction callable "
            "that takes no keyword arguments while the value keeps publishing its text "
            "as one, so `expr.func(*expr.args) == expr` holds but "
            "`expr.func(**expr.kwargs()) == expr` RAISES TypeError. EXECUTED on the "
            "real repo: the F2P test asserts both identities, and that patch fails it "
            "(the round-trip identity is a property of the value's reconstruction, not "
            "of one calling syntax). Faithful but non-resolving — and this is the "
            "recorded counterexample that a positional-only clause admitted, which is "
            "why the clause now quantifies over the convention."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at "
            "`s = { text := \"foobar\" }` the rival returns `some s` on the positional "
            "convention but `none` on the keyword convention, so the quantified claim "
            "fails at `c = keyword`. It is refuted at EVERY input including the empty "
            "text — the defect is which convention is honoured, not what the text is — "
            "so this witness discriminates on the CONVENTION axis that no payload "
            "witness can reach. If it verifies, the spec pins only one calling "
            "convention and admits a value whose two self-reports disagree about its "
            "own reconstruction (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("foobar"),
    },
    {
        "id": "convention-split-keyword-refused",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SPLIT_KEYWORD_REFUSED_IMPL),
        "refinement": (
            "the same defect as the rival above, spelled the way the real callee "
            "exhibits it: the value still PUBLISHES a reconstruction keyword while its "
            "callable admits no keyword at all, so the value's two self-reports about "
            "its own reconstruction DISAGREE and the keyword round-trip is refused. "
            "Its faithful real patch leaves the value's keyword self-report untouched "
            "and supplies a callable accepting nothing, which is exactly the patch the "
            "F2P test rejects. Faithful but non-resolving. Landed alongside the rival "
            "above because it locates the disagreement in the value's self-report "
            "rather than in a hard-coded failure branch — a clause that merely banned "
            "an explicit `none` would admit this one."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at `s = { text := \"q\" }` "
            "the value publishes the keyword it does not admit, so the keyword "
            "round-trip yields `none` while the positional one yields `some s`; the "
            "quantified claim fails at `c = keyword`. Refuted at every input, on the "
            "convention axis. If it verifies, the spec tolerates a value whose "
            "published reconstruction data its own callable rejects (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("q"),
    },
    {
        "id": "convention-split-positional-fails",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SPLIT_POSITIONAL_FAILS_IMPL),
        "refinement": (
            "the MIRROR of the two rivals above, and the PRE-FIX shape: the value "
            "round-trips when handed the keyword data it publishes and FAILS when "
            "handed the positional data, because the generic callable rebuilds the "
            "value from whatever it is handed and the positional list is empty. Its "
            "faithful real patch is the UNPATCHED code, whose "
            "`expr.func(**expr.kwargs()) == expr` holds while "
            "`expr.func(*expr.args) == expr` raises — definitively non-resolving, and "
            "measured as such on the real repo."
        ),
        "rationale": (
            "REJECT from the clause `∀ c, result c = some s`: at `s = { text := \"kw\" }` "
            "the rival returns `none` on the positional convention, so the quantified "
            "claim fails at `c = positional`. This rival exists to prove the clause "
            "does not merely privilege the OTHER convention: it and "
            "`convention-split-keyword-fails` fail on opposite sides, so a "
            "one-convention clause would admit exactly one of the two, and only a "
            "clause quantifying over both rejects both. If it verifies, the spec has "
            "simply moved its blind spot rather than closing it (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("kw"),
    },
]


# No consumed axioms and no deep-model references (mapping.md: G-AX is a skip):
# the reconstruction round-trip is modeled directly over the input, so there is
# no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
