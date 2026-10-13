"""properties.py — G-PBT falsification battery for astropy__astropy-8707 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``axiom``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over a single input carrier that is
EITHER a sequence of textual characters OR a sequence of raw 8-bit bytes; the
output is the constant-width card-image text, modeled as
``Except CardErr (List Char)``):

  cardFromString (image : CardImage) : Except CardErr (List Char)
    result = ok (padCard (decodeImage image))

  where ``decodeImage`` passes text through unchanged and reinterprets each raw
  byte as the code point whose numeric value equals that byte (the Latin-1
  correspondence over 0..255), and ``padCard`` extends the textual content with
  trailing spaces to a multiple of the constant card width. Construction always
  SUCCEEDS (``Except.ok`` on every input; the error carrier exists only to model
  the pre-fix inability to treat a raw-byte input as text).

The single load-bearing clause bundles three independent obligations that the
richer nagini carrier expressed as separate postcondition conjuncts — carrier
NARROWING, not a weakening:

  * ALWAYS-OK — a raw-byte input must be accepted (never fail), which requires
    reinterpreting it as text before the width step;
  * FAITHFUL DECODE — each byte maps to the code point equal to its value (the
    identity over 0..255), not to some lossy transform;
  * FULL CONTENT — the whole reinterpreted content is retained (no dropped
    element) before the width step;
  * PADDING — that content is extended with trailing spaces to a multiple of the
    card width.

Each reject rival below attacks one of these FOUR faces of the single clause.
The port originally bundled CONTENT and PADDING into one face and shipped three
rivals, all of which kept `padCard` applied to whatever content they computed —
so the width step itself went unprobed. The `no-width-padding` rival was added by
audit to attack it, and it is a real gap rather than a formality: `padCard` is
where the whole `cardWidth` constant and the not-already-a-multiple branch enter
the clause, and nothing else in the battery would notice their removal.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so rather than
    asserted. Lean is referentially transparent: the input carries no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. The nagini rival's distinguishing act is a write back
    into the input (``raw[i-1] = c``); transcribed here, the nearest expressible
    analogue is a rebind of the input carrier to itself, which on an immutable
    inductive is a NO-OP. Built as a variant, it VERIFIES under the frozen proof
    script unchanged — i.e. it is observably identical to the frozen impl, which
    is exactly what makes the case vacuous on this carrier (attack C: a rival
    indistinguishable from gold attests to nothing). It is therefore not shipped
    as a reject case, and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the input
    (an equality against a term built only from ``image`` via ``decodeImage`` /
    ``padCard``, both fully unfolded); the bundle declares no ``opaque``/
    ``axiom``, so there is no answer key an implementation could echo without
    doing the work. In its place the battery carries honest POSITIVE CONTROLS
    (a structurally different but correct implementation) plus an ADMISSIBILITY
    control pinning satisfiability at the normal inputs the behavior is
    exercised on.

  * CONTROL-FLOW-EFFECT + PARTIAL-DOMAIN + VALUE-MASK — APPLIES. The three
    reject rivals port the nagini control-flow-effect (pre-fix bug), partial-
    domain (dropped element) and value-mask (lossy reinterpretation) cases.

BINDER COVERAGE. The spec has a SINGLE input binder, ``image``, whose two shapes
are both exercised by the reject witnesses: the raw-byte constructor at a LOW
byte value (``bytes [65]``) and at a HIGH byte value 128..255 (``bytes [200]``),
and the textual constructor (``text ['A']``, ``text ['X','Y']``). Probing only one
shape or only the low-byte sub-range would leave a whole half of the carrier
unattacked — a rival lossy only on high bytes, or one that mishandled only the
textual form, would be invisible. The four witnesses probe four DISTINCT inputs.

The variation is MEANINGFUL, not two spellings of one point, and each point was
checked to be load-bearing by re-aiming its own witness at a neighbouring input
where its rival is CORRECT and confirming the witness then FAILS: ``bytes [200]``
against ``bytes [65]`` (the mask is the identity on low bytes), ``text ['A']``
against ``text []`` (dropping one element is a no-op on the empty list), and
``text ['X','Y']`` against a length-80 input (already a whole record, so the
width step is a no-op). Each of those neighbours is a point where the clause and
the rival AGREE, so the witness's success at its own point is attributable to the
input and not to the script.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (``cases image … rfl``) is tuned
to the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input: it states ``¬ problem_spec …`` at
that input, introduces the spec equation as a hypothesis, and asks ``simp`` to
reduce that hypothesis over the FULL definition chain
(``implementation_cardFromString``, ``decodeImage``, ``bytesAsText``, ``padCard``,
``cardWidth``). Against a rival that really is wrong at the point, the two sides
reduce to distinct concrete lists and ``simp`` closes the goal from the resulting
contradiction; against a solution that is CORRECT there, ``simp`` proves the
equation instead, leaving ``h : True ⊢ False`` unsolved. That residual goal is
the discriminating signal, and it is a SEMANTIC one.

WITNESS FORM — why the hypothesis is reduced rather than the goal rewritten. An
earlier form of these witnesses opened with
``unfold problem_spec_cardFromString implementation_cardFromString`` followed by
``simp only [Id.run, pure]`` and then either ``Except.noConfusion h`` or
``rw [Except.ok.injEq] at h``. That form was measured to be a NON-discriminator
on this carrier. The frozen implementation is written with ``let mut``/``if let``
inside ``Id.run do``, whose elaboration leaves a ``do PUnit.unit`` prefix that
``simp only [Id.run, pure]`` does not clear, so on the frozen solution the
``rw``/``noConfusion`` step failed on the SHAPE of the goal ("did not find an
occurrence of the pattern …") before ever reaching the equation's content. Held
to that syntactic shape while the SEMANTICS were varied, the same scripts failed
identically against a WRONG implementation written in the frozen shape — i.e.
their exit code tracked the impl's spelling, not its correctness. The
hypothesis-reducing form above was checked to track the CLAIM instead: it
succeeds against each rival, fails with ``h : True`` against the frozen solution
AND against an independently correct reshape, succeeds against a wrong impl
written in the frozen solution's own shape, and fails when aimed at an input
where its own rival happens to be correct.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total computation over the input's own data, so there is
no axiom-soundness / axiom-containment obligation to probe here (that lane
belongs to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "astropy__astropy-8707"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the one impl region, and the FULL tactic body of the one
# proof region, so every replacement lands entirely inside the region it edits
# and the spec view (hence same_spec) and the theorem STATEMENT stay identical.
_IMPL = (
    "def implementation_cardFromString (image : CardImage) :\n"
    "    Except CardErr (List Char) := Id.run do\n"
    "  let mut img := image\n"
    "  -- a raw-byte input is first reinterpreted as text, each byte taken as the\n"
    "  -- code point equal to its value, before any further processing\n"
    "  if let CardImage.bytes bs := img then\n"
    "    img := CardImage.text (bytesAsText bs)\n"
    "  let chars := match img with\n"
    "    | CardImage.text cs  => cs\n"
    "    | CardImage.bytes _  => []\n"
    "  return Except.ok (padCard chars)"
)
_PROOF = (
    "  intro image\n"
    "  cases image with\n"
    "  | text cs => rfl\n"
    "  | bytes bs => rfl"
)

assert _IMPL in _BASE and _BASE.count(_IMPL) == 1, "impl anchor drift / not unique"
assert _PROOF in _BASE and _BASE.count(_PROOF) == 1, "proof anchor drift / not unique"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. The
    # theorem statement is byte-identical and the frozen tactic body is retained
    # (the reshape is definitional — both branches still reduce identically —
    # so the frozen `cases … rfl` still closes). No helper lemma, axiom, or
    # assumption token is introduced. Ports nagini case (1)
    # pos-control-reshaped-loop.
    #
    # BECAUSE the reshape is definitional, this case cannot by itself show the
    # clause is provable of an impl the frozen script does not already reduce;
    # `pos-control-mod256-decode` below is the control that does, and the two are
    # kept as a pair for that reason.
    # =====================================================================
    {
        "id": "pos-control-direct-match",
        "kind": "soundness",
        "expect": "verify",
        # Drop the mutable-carrier rebind and the dead totality arm: match the
        # input directly and, on each branch, pad the branch's textual content.
        # Same ok/error decision and same produced text on both shapes, so both
        # obligation branches reduce exactly as the frozen impl does.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_cardFromString (image : CardImage) :\n"
            "    Except CardErr (List Char) := Id.run do\n"
            "  match image with\n"
            "  | CardImage.text cs  => return Except.ok (padCard cs)\n"
            "  | CardImage.bytes bs => return Except.ok (padCard (bytesAsText bs))",
        ),
        "rationale": "structurally different (no mutable rebind; the input is "
                     "matched directly and each branch pads its own textual "
                     "content) but observably identical: on text it returns "
                     "`ok (padCard cs)` and on bytes `ok (padCard (bytesAsText "
                     "bs))`, exactly `ok (padCard (decodeImage image))`. A "
                     "faithful correct reshape must verify, else the single "
                     "clause is SPEC-TOO-STRONG. Proof: frozen tactic body "
                     "retained — each branch is definitionally the frozen one, "
                     "so `cases image … rfl` still closes both cases.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal inputs the behavior is exercised
    # on, not only provable in the abstract. The frozen theorem carries NO
    # precondition hypothesis (construction is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack; the
    # honest analogue is to discharge the spec predicate at ground inputs of both
    # shapes — a textual input and a raw-byte input — by evaluation inside the
    # proof region, alongside the frozen obligation. If either ground instance
    # could not be discharged, the behavior would be unsatisfiable at exactly an
    # input it must admit (the analogue of PRECOND-TOO-STRONG). Ports nagini
    # case (2) admissibility-indomain.
    # =====================================================================
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "  have _g_text : problem_spec_cardFromString (CardImage.text ['A', 'B', 'C'])\n"
            "      (implementation_cardFromString (CardImage.text ['A', 'B', 'C'])) := by rfl\n"
            "  have _g_bytes : problem_spec_cardFromString (CardImage.bytes [65, 66, 67])\n"
            "      (implementation_cardFromString (CardImage.bytes [65, 66, 67])) := by rfl\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at two ground inputs by "
                     "evaluation — a textual input and a raw-byte input, both "
                     "reaching a normal (`Except.ok`) result — then the frozen "
                     "obligation is closed verbatim. Verifies (else the behavior "
                     "is unsatisfiable at a normal input it must admit). Nothing "
                     "is assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instances are `have`s inside "
                     "the tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P (constructing a card
    # from a raw-byte input must succeed and yield the correct textual content,
    # from which the graded keyword/value are parsed), so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "control-flow-no-reinterpret",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ALWAYS-OK FACE (the literal pre-fix behavior): a raw-byte input is
        # never reinterpreted as text and so cannot be handed to the width step;
        # the construction has no result (modeled as `Except.error`). Correct on
        # every textual input, wrong on EVERY raw-byte input. Ports nagini case
        # (4) control-flow-prepatch-bug.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_cardFromString (image : CardImage) :\n"
            "    Except CardErr (List Char) := Id.run do\n"
            "  match image with\n"
            "  | CardImage.text cs  => return Except.ok (padCard cs)\n"
            "  | CardImage.bytes _  => return Except.error CardErr.illTyped",
        ),
        "refinement": "declining to reinterpret a raw-byte input before the "
                      "width step is the pre-fix behavior: the raw bytes reach a "
                      "text-only step that cannot consume them and construction "
                      "fails outright — exactly the crash the issue reports. The "
                      "F2P test constructs a card from a raw-byte input and "
                      "asserts a parsed keyword/value; a faithful patch that "
                      "keeps handing raw bytes to the text-only step still fails "
                      "there and would NOT resolve.",
        "rationale": "REJECT from the ALWAYS-OK face of the clause `result = ok "
                     "(padCard (decodeImage image))`: on a raw-byte input the "
                     "rival returns `Except.error`, while the spec requires "
                     "`Except.ok (padCard (bytesAsText bs))`. Source: the "
                     "reinterpret-before-pad requirement folded into "
                     "`decodeImage` on the bytes constructor.",
        # Refutation at a raw-byte input: the rival answers `Except.error` where
        # the clause demands `Except.ok (padCard (bytesAsText [65]))`. `simp`
        # over the full definition chain reduces the assumed equation to an
        # error-vs-ok clash and closes. On any solution CORRECT here (the frozen
        # one, or a correct reshape) the same `simp` PROVES the equation, leaving
        # `h : True ⊢ False` — so the failure tracks the claim, not the spelling.
        "witness": (
            "example : ¬ problem_spec_cardFromString (CardImage.bytes [65])\n"
            "    (implementation_cardFromString (CardImage.bytes [65])) := by\n"
            "  intro h\n"
            "  simp [problem_spec_cardFromString, implementation_cardFromString,\n"
            "    decodeImage, bytesAsText, padCard, cardWidth] at h\n"
        ),
    },
    {
        "id": "value-mask-7bit",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FAITHFUL-DECODE FACE: reinterpret each raw byte through a 7-bit
        # mask (b % 128) instead of the value-preserving identity. Agrees with
        # gold on bytes 0..127 but DIFFERS on 128..255 (the input admits the full
        # 0..255 range). Ports nagini case (6) value-mask-ascii-7bit.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_cardFromString (image : CardImage) :\n"
            "    Except CardErr (List Char) := Id.run do\n"
            "  match image with\n"
            "  | CardImage.text cs  => return Except.ok (padCard cs)\n"
            "  | CardImage.bytes bs =>\n"
            "      return Except.ok (padCard (bs.map (fun b => Char.ofNat (b.toNat % 128))))",
        ),
        "refinement": "reinterpreting through a 7-bit mask (or an ASCII-only "
                      "decode) agrees with the value-preserving rule on bytes "
                      "0..127 but corrupts (or would reject) bytes 128..255 — "
                      "exactly the non-ASCII bytes the value-preserving rule "
                      "deliberately retains so that malformatted input is kept "
                      "verbatim. A raw-byte input carrying such a byte would be "
                      "mangled, so a faithful patch using the masked decode does "
                      "not reproduce the intended behavior on its declared domain "
                      "and would NOT resolve.",
        "rationale": "REJECT from the FAITHFUL-DECODE face of the clause: "
                     "`b % 128` equals the identity (`decodeImage`) only on "
                     "0..127; on a high byte the reinterpreted code point "
                     "differs, so `result = ok (padCard (bytesAsText bs))` fails. "
                     "Source: the value-preserving byte↦code-point map in "
                     "`bytesAsText`, consumed by the clause.",
        # Refutation at a HIGH byte (200), the sub-range where the mask and the
        # value-preserving rule part company: the rival's content begins
        # `Char.ofNat 72` where the clause demands `Char.ofNat 200`. Aimed
        # instead at a LOW byte (65) — where this rival IS correct — the same
        # script fails with `h : True`, which is what makes the high byte the
        # load-bearing part of the input rather than an arbitrary literal.
        "witness": (
            "example : ¬ problem_spec_cardFromString (CardImage.bytes [200])\n"
            "    (implementation_cardFromString (CardImage.bytes [200])) := by\n"
            "  intro h\n"
            "  simp [problem_spec_cardFromString, implementation_cardFromString,\n"
            "    decodeImage, bytesAsText, padCard, cardWidth] at h\n"
        ),
    },
    {
        "id": "partial-domain-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FULL-CONTENT FACE: reinterpret correctly but DROP the first element
        # of the textual content before padding. On any non-empty input the
        # content is one element short and no longer equals the input's textual
        # content, so the produced text diverges. Attacks the TEXTUAL shape of
        # the binder (refuted at a text input). Ports nagini case (5)
        # partial-domain-drop-first-byte.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_cardFromString (image : CardImage) :\n"
            "    Except CardErr (List Char) := Id.run do\n"
            "  let chars := match image with\n"
            "    | CardImage.text cs  => cs\n"
            "    | CardImage.bytes bs => bytesAsText bs\n"
            "  return Except.ok (padCard (chars.drop 1))",
        ),
        "refinement": "dropping the first element of the textual content decodes "
                      "the wrong text: the card image begins one character late, "
                      "so the parsed keyword/value the F2P test asserts are "
                      "wrong. A faithful patch that drops the leading character "
                      "produces a mis-aligned card image and would NOT resolve.",
        "rationale": "REJECT from the FULL-CONTENT face of the clause: with "
                     "`chars.drop 1` the produced content is `padCard ((decodeImage "
                     "image).drop 1)`, which for any non-empty input differs from "
                     "`padCard (decodeImage image)` (the first character becomes a "
                     "pad space), so the clause fails. Source: the requirement "
                     "that the whole textual content is retained before padding.",
        # Refutation at a NON-EMPTY textual input: dropping the leading element
        # shifts the content one place left and turns the last column into a pad
        # space, so the produced text differs from `padCard (decodeImage image)`.
        # Aimed at the EMPTY input — where dropping one element is a no-op and
        # the rival is correct — the same script fails with `h : True`, so
        # non-emptiness is the load-bearing part of the input.
        "witness": (
            "example : ¬ problem_spec_cardFromString (CardImage.text ['A'])\n"
            "    (implementation_cardFromString (CardImage.text ['A'])) := by\n"
            "  intro h\n"
            "  simp [problem_spec_cardFromString, implementation_cardFromString,\n"
            "    decodeImage, bytesAsText, padCard, cardWidth] at h\n"
        ),
    },
    {
        "id": "no-width-padding",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PADDING FACE, added by audit. The three original rivals all attack
        # the CONTENT that reaches the width step (accept-at-all, how a byte is
        # reinterpreted, whether an element is dropped); every one of them keeps
        # `padCard` applied to whatever content it computed, so the width step
        # itself was never probed. This rival reinterprets faithfully and retains
        # every element, then returns the content WITHOUT extending it to a
        # multiple of the constant width.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_cardFromString (image : CardImage) :\n"
            "    Except CardErr (List Char) := Id.run do\n"
            "  match image with\n"
            "  | CardImage.text cs  => return Except.ok cs\n"
            "  | CardImage.bytes bs => return Except.ok (bytesAsText bs)",
        ),
        "refinement": "returning the content unextended skips the constant-width "
                      "step entirely. Downstream the card image is read as a "
                      "fixed-width record and the graded keyword/value are parsed "
                      "out of it positionally, so a short record does not present "
                      "the field layout the parse expects. A faithful patch that "
                      "reinterprets a raw-byte input correctly but never brings the "
                      "text up to a whole record does NOT resolve.",
        "rationale": "REJECT from the PADDING face of the clause `result = ok "
                     "(padCard (decodeImage image))`: the rival returns "
                     "`ok (decodeImage image)`, which differs from "
                     "`ok (padCard (decodeImage image))` at every input whose "
                     "length is not already a positive multiple of `cardWidth`. "
                     "Source: `padCard`, consumed by the clause — the one "
                     "component of the clause the other three rivals leave intact.",
        "witness": (
            "example : ¬ problem_spec_cardFromString (CardImage.text ['X', 'Y'])\n"
            "    (implementation_cardFromString (CardImage.text ['X', 'Y'])) := by\n"
            "  intro h\n"
            "  simp [problem_spec_cardFromString, implementation_cardFromString,\n"
            "    decodeImage, bytesAsText, padCard, cardWidth] at h\n"
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness), added by audit — a correct reshape whose
    # equivalence to the frozen impl is NOT definitional, so unlike
    # `pos-control-direct-match` it cannot pass by the frozen tactic script
    # reducing both sides to the same normal form. It re-proves the frozen
    # obligation with a real argument, and so tests that the clause is provable
    # rather than merely `rfl`-shaped.
    # =====================================================================
    {
        "id": "pos-control-mod256-decode",
        "kind": "soundness",
        "expect": "verify",
        # Reinterpret each byte through `b.toNat % 256`. On this carrier a byte's
        # numeric value is always below 256, so the reduction is the identity and
        # the impl is CORRECT — but `% 256` does not reduce away definitionally on
        # an abstract `b`, so `rfl` alone cannot close the bytes branch. The proof
        # region supplies the missing step (the mod is inert below the bound) and
        # then finishes as the frozen script does. If this could NOT be proven,
        # the clause would be rejecting a faithful correct implementation.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def implementation_cardFromString (image : CardImage) :\n"
                "    Except CardErr (List Char) := Id.run do\n"
                "  match image with\n"
                "  | CardImage.text cs  => return Except.ok (padCard cs)\n"
                "  | CardImage.bytes bs =>\n"
                "      return Except.ok (padCard (bs.map (fun b => Char.ofNat (b.toNat % 256))))",
            ),
            _PROOF,
            "  intro image\n"
            "  cases image with\n"
            "  | text cs => rfl\n"
            "  | bytes bs =>\n"
            "    simp only [problem_spec_cardFromString, implementation_cardFromString,\n"
            "      decodeImage, bytesAsText, Id.run]\n"
            "    have hf : (fun b : UInt8 => Char.ofNat (b.toNat % 256))\n"
            "        = (fun b : UInt8 => Char.ofNat b.toNat) := by\n"
            "      funext b\n"
            "      congr 1\n"
            "      exact Nat.mod_eq_of_lt b.toNat_lt_size\n"
            "    rw [hf]\n"
            "    rfl",
        ),
        "rationale": "a correct reshape that is NOT definitionally the frozen "
                     "impl: `b.toNat % 256` is extensionally the identity on this "
                     "carrier (a byte's value is below 256) but does not reduce on "
                     "an abstract `b`, so the frozen `cases … rfl` cannot close the "
                     "bytes branch and the proof must actually argue that the "
                     "reduction is inert below the bound. This is the soundness "
                     "control that `pos-control-direct-match` cannot be, since that "
                     "one's branches ARE definitionally the frozen ones. Verifies, "
                     "so the clause is not SPEC-TOO-STRONG against a faithful "
                     "implementation whose equivalence needs a proof. No new "
                     "declaration and no assumption token is introduced: the added "
                     "step is a `have` inside the frozen proof region and the "
                     "theorem statement is byte-identical.",
    },
]

# No AXIOM_TESTS: the bundle declares no opaque callee / axiom (the two ops on
# the changed path are modeled deeply), so the axiom lane is empty here; it
# belongs to G-AX in any case.
AXIOM_TESTS = []
