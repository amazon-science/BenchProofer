"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7454 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps with a recorded verdict. Each SPEC case is a full ``Solution.lean``
variant built by region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
matching ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds by construction and the ``theorem correct_<name>``
STATEMENT stays byte-identical. No case introduces ``sorry`` / ``admit`` /
``native_decide`` / ``axiom`` or any new theorem/lemma. ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE — carrier narrowing / widening vs the nagini sibling.
  The nagini battery contracts ONE procedure over a read-only ``List[int]`` term
  (Unicode code points) held at a half fractional permission, whose
  postcondition pins TWO touched fields: the carried-through target
  (``ToSeq(Result().target) == ToSeq(text)``) and the classified kind
  (``obj`` when the token is the value name, ``class`` otherwise). This Lean
  bundle models the same single behavior — the cross-reference a single
  annotation token yields — as one total function over ``List Char`` returning a
  four-field record, whose postcondition pins ALL FOUR observable components:

    C1  result.domain = "py"                                  (always)
    C2  result.target = text                                  (carry-through)
    C3  result.label  = text                                  (carry-through)
    C4  result.kind   = if text = "None".toList then "obj"
                                                    else "class"

  So the nagini two-clause surface WIDENS to four independent top-level clauses
  here: the record carrier makes the domain and the visible label first-class
  observables the spec pins, where nagini modeled only target and kind. That is
  carrier widening, and it earns two reject rivals with no nagini counterpart
  (C1 and C3 below); it is NOT parity-chasing — each attacks a clause this
  bundle genuinely models.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION rival (nagini ``frame-mutate-text``) — SPLIT.
    The MECHANISM is inexpressible: Lean is referentially transparent, the input
    is an immutable ``List Char``, and there is no read-only half-permission to
    overwrite nor aliasing to exploit, so "store a code point through the
    read-only input" has no instance on this carrier and none is fabricated.
    But the OBSERVABLE FOOTPRINT that mechanism has — the emitted target/label
    carrying CORRUPTED CONTENT rather than the token — is expressible, and is
    exactly what the nagini refinement argument cites. An impl may build its
    reference from a locally scribbled COPY of the token, which is
    content-corruption at UNCHANGED LENGTH. The C1/C3 rivals do NOT cover that:
    ``domain-wrong`` attacks a constant field, and ``label-drop-last`` /
    ``target-drop-last`` are LENGTH-shaped (a shorter list), so a spec clause
    that pinned only the length of the carry-through would survive all of them.
    ``content-corrupt-copy`` below closes that gap at equal length.

  * DIVERGENCE / NON-TERMINATION — REJECTED BUT UNWITNESSABLE; recorded as a
    known WITNESS-lane hole, not as a vacuous class. The bundle sets no
    ``loom.semantics.termination``, so plain Lean totality governs: this is the
    "total" disposition, and a diverging rival IS genuinely rejected. AUDIT
    CORRECTION — an earlier revision of this note claimed "a non-terminating
    implementation cannot be written". That is measurably false and the two
    builds that disprove it are worth recording so the next reader does not
    re-derive them:
      - as a plain ``def``, the self-call ``implementation_annotationRef text``
        is refused by the elaborator with ``fail to show termination for
        implementation_annotationRef ... no parameters suitable for structural
        recursion``. So termination really is discharged here, i.e. the rival is
        rejected on the termination obligation exactly as the "total" lane
        predicts;
      - but it CAN be written, as ``partial def`` plus an ``Inhabited TypeRef``
        instance (both inside the impl region, so the case stays in scope). That
        variant elaborates its ``def`` and is still rejected — the frozen script
        dies at ``Tactic `unfold` failed to unfold implementation_annotationRef``,
        because a ``partial def`` is an opaque constant.
    That opacity is what blocks the case rather than any authoring difficulty:
    the witness's ``decide`` cannot reduce an opaque constant, and the measured
    rival-side build fails with ``did not reduce to `isTrue` or `isFalse` ...
    reduction got stuck at the `Decidable` instance`` — the gate's
    ``witness-undecided`` screen, which is an INCONCLUSIVE outcome and would fail
    this gate rather than pass it. Nor can a ``witness_reference`` rescue it: a
    reference relocates the GOLD-side subject, while here it is the RIVAL-side
    half (the half that must succeed) that cannot reduce. And the refutation
    cannot be restated by hypothesis either, since an opaque ``partial`` constant
    supports no equation to hypothesise about. So the honest disposition is: the
    class is real and rejected, and no admissible witness for it exists on this
    carrier — a hole in the witness lane, not a complete battery.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Every clause is GROUNDED in the input
    (an equality against ``text`` itself, or a decidable split on
    ``text = "None".toList``). mapping.md records no ``opaque`` / ``axiom``
    callee (the four components are computed by straight-line data from the
    token), so there is no answer key an impl could echo without doing the work;
    the honest substitutes are the reshaped-impl positive controls below.

  * VALUE / PARTIAL-DOMAIN + UNIQUENESS rivals — the heart of the port. The
    nagini value rivals re-express directly here as clause violations, each with
    a refutation witness stated at a ``decide``-able concrete token:
      - ``kind-always-class``  == nagini ``kind-always-type`` (the pre-patch
        unconditional class kind);
      - ``kind-swapped``       == nagini ``kind-swapped`` (tags inverted);
      - ``target-drop-last``   == nagini ``target-prefix-drop`` (drop the last
        code point of the carried target);
      - ``target-echo-none``   == nagini ``target-echo-name`` (target hard-pinned
        to the constant value name).
    plus the two carrier-widening rivals (``domain-wrong``, ``label-drop-last``)
    and ``content-corrupt-copy``, the expressible observable footprint of the
    nagini frame rival (see above).

  * AXIOM_TESTS — dropped. The axiom lane is G-AX's job; this bundle ships no
    consumed axiom (meta.json axioms == []).

SPEC-TOO-WEAK PROBES that did NOT break the spec (recorded so the next reader
does not re-spend the builds). Each is a wrong impl NOT shipped as a case above,
built against the frozen spec and refuted by it at the token named:
  * kind relaxed from equality to a PREFIX test (``"None"`` prefix of the token)
    — refuted at ``NoneType``, which the spec gives the class kind;
  * kind keyed on the token LENGTH (= 4) rather than its content — refuted at
    ``List``;
  * kind giving the object kind to the value name AND the EMPTY token — refuted
    at the empty token;
  * target truncated only on the value-name arm (a sub-domain attack that leaves
    every other token correct) — refuted at ``None``.
So C4 pins EXACT case-sensitive equality with no prefix/length/empty relaxation,
and the carry-through clauses hold on every arm, not just the else arm.
An independent audit re-ran all four of the above plus eight more (an
unconditional object kind; a capitalised ``"Class"`` tag; an object tag with a
trailing space; both carry-through fields reversed; a corruption confined to the
empty token; the label hard-pinned to the constant value name; an empty domain;
a case-folded classifier) — the frozen spec refuted every one of the twelve.

SPEC-TOO-STRONG PROBES that the spec correctly ACCEPTS (so it is not
over-constrained beyond the two positives shipped above): an impl that
pattern-matches the character list ``['N','o','n','e']`` directly instead of
comparing against ``"None".toList``, and an impl that classifies by rebuilding a
``String`` from the token and comparing ``String.mk text = "None"``. Both are
faithful reshapes and both discharge the frozen obligation. AUDIT NOTE — both do,
but neither closes under the frozen script's own one-line ``simp``/``by_cases``
shape, and the audit needed a specific extra step for each: the pattern-match
reshape wants ``refine ⟨rfl, rfl, rfl, ?_⟩; split <;> simp_all`` (a bare
``by_cases`` leaves the match unreduced), and the ``String.mk`` reshape wants the
injectivity bridge ``(String.mk text = "None") ↔ (text = "None".toList)``
supplied via ``congrArg String.data`` first. Four further reshapes were confirmed
to verify: a ``Bool``-valued ``==`` test, a ``{ base with kind := ... }`` record
update, a ``text.map (fun c => c)`` identity carry-through, and a classifier
using a recursively-defined list equality with an ``induction``-proved
correctness bridge.

WHY D AND E ARE CLOSED GLOBALLY, not merely at the probed points. The audit
proved, against the frozen file and with the obligation intact, that the
postcondition is EXACTLY extensional equality with the frozen implementation:

    theorem audit_spec_is_exactly_gold :
        ∀ (text : List Char) (r : TypeRef),
          problem_spec_annotationRef text r ↔ r = implementation_annotationRef text

(closed by ``by_cases`` on the token plus ``TypeRef.mk.injEq`` and ``tauto``;
elaborated, exit 0). The four clauses jointly pin all four fields of a
four-field record, so the spec has exactly one satisfying output per token. That
makes the two failure directions unreachable rather than merely unobserved: no
wrong impl can satisfy the spec (SPEC-TOO-WEAK is impossible — any impl
disagreeing with gold at any token is refuted there), and no faithful correct
impl can fail it semantically (SPEC-TOO-STRONG is impossible — every impl
agreeing with gold satisfies it, and any such rejection is a TACTIC gap in the
re-proof, never a spec defect). The individual probes above are consistent with
this theorem and are kept as concrete instances of it.

DEFENDED SURFACE — the four clauses every rival is built to attack (see above).
  C4 is the only clause that branches on the token; C1/C2/C3 hold for every
  token. The F2P feeds the tokens ``int`` and ``None`` and pins all four fields
  for each (``refdomain='py'``, ``reftarget``/label = the token, and
  ``reftype='class'`` for ``int`` / ``'obj'`` for ``None``).

BINDER COVERAGE. The single input binder ``text`` is varied across FIVE distinct
concrete token points by the reject witnesses, so the battery exercises the
spec's dependence on the token rather than probing one point repeatedly. The
points differ in the spec's VERDICT or in the clause they falsify, not merely in
spelling:
  * ``"None".toList``  — the value-name arm of C4 (``kind-always-class``); the
    only point where C4 demands the object kind;
  * ``['i','n','t']``  — the else arm of C4 and the carry-through clauses
    (``kind-swapped``, ``target-drop-last``, ``target-echo-none``,
    ``domain-wrong``);
  * ``['a','b','c']``  — the label carry-through clause (``label-drop-last``);
    all-distinct characters, so a truncation cannot be masked by a repeat;
  * ``['x']``          — a LENGTH-ONE token (``content-corrupt-copy``), the
    shortest non-empty point. Length-shaped rivals collapse the carry-through
    clauses to the empty list here, so it is the point where a content-only
    corruption is cleanly separable from a truncation.
  * ``['n','o','n','e']`` — a NEAR-MISS of the value name
    (``kind-case-insensitive``): same length and same letters, differing only in
    the case of one character, and on the else arm of C4. The two points above
    that drive C4 (``"None"`` and ``int``) are both classified identically by an
    approximate split, so this is the only point that separates C4's EXACT
    equality from a case-insensitive one — and it is a point where gold and the
    F2P agree, so only the clause catches it.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script is tuned to the frozen form), so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete token; each was checked to HOLD of its rival and to
FAIL on the frozen solution (so it discriminates rather than asserting a
tautology). All witnesses use literal tokens with no head binders, so no
carrier-conditioning (and no consistency probe) is needed.

AUDIT — the witnesses were rebuilt independently and the FORGERY test (assert the
OPPOSITE of each witness, i.e. that the impl is CORRECT at that token, and build
it on both sides) was run for all eight reject cases. Every case gave the full
four-quadrant result, which is what makes gold's exit code informative rather
than incidental:

    witness  vs rival = 0   witness  vs gold  = 1
    forgery  vs rival = 1   forgery  vs gold  = 0

Both gold-side failures are PLAIN EVALUATIONS — ``Tactic `decide` proved that the
proposition ... is false``, with the fully-reduced four-clause conjunction and
the concrete token printed in the message. No build in this battery matches any
of the gate's stuck-reduction screens (no ``did not reduce to `isTrue` or
`isFalse```, no ``Dependent elimination failed``, no missing ``Decidable``
instance, no ``forIn Lean.Loop.mk`` unification failure): the carrier is a
finite record of ``String``/``List Char`` with ``deriving DecidableEq``, all
witnesses are stated at closed literal tokens, and the frozen impl is a
``Id.run do`` block the kernel unfolds. So the exit codes track the CLAIM here,
not the carrier.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7454"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full impl-region body (the `def` line through its final `return`).
_IMPL = (
    "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
    "  let mut kind := \"class\"\n"
    "  if text = \"None\".toList then\n"
    "    kind := \"obj\"\n"
    "  else\n"
    "    kind := \"class\"\n"
    "  return { domain := \"py\", kind := kind, target := text, label := text }\n"
)

# The full frozen proof body (between the theorem STATEMENT's `:= by` and the
# closing `-- proof-end`). Swapping this leaves the STATEMENT byte-identical.
_PROOF = (
    "  intro text\n"
    "  unfold problem_spec_annotationRef implementation_annotationRef\n"
    "  by_cases h : text = \"None\".toList <;>\n"
    "    simp only [h, Id.run, if_pos, pure] <;>\n"
    "    exact ⟨rfl, rfl, rfl, rfl⟩\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL) == 1, "impl region drifted"
assert _BASE.count(_PROOF) == 1, "proof region drifted"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Each keeps the
    # ``theorem correct_annotationRef`` STATEMENT byte-identical and re-proves
    # inside the proof region with tactics only (no new lemma/axiom/sorry).
    # =====================================================================
    {
        "id": "pos-kind-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-order flip: test the COMPLEMENT (text ≠ "None") first, assigning
        # the class kind in the taken branch and the object kind in the else.
        # Same classification, different control shape; C4 and the carry-through
        # clauses are unchanged.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
                "  let mut kind := \"class\"\n"
                "  if text ≠ \"None\".toList then\n"
                "    kind := \"class\"\n"
                "  else\n"
                "    kind := \"obj\"\n"
                "  return { domain := \"py\", kind := kind, target := text, label := text }\n",
            ),
            _PROOF,
            "  intro text\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  by_cases h : text = \"None\".toList <;>\n"
            "    simp only [h, Id.run, if_pos, if_neg, pure, ne_eq, not_true, not_false_iff] <;>\n"
            "    exact ⟨rfl, rfl, rfl, rfl⟩\n",
        ),
        "rationale": "a correct but branch-reordered classifier (complement "
                     "tested first) still yields the object kind exactly for the "
                     "value name and the class kind otherwise, so C4 and all "
                     "carry-through clauses hold; must verify, else "
                     "SPEC-TOO-STRONG. The re-proof is tactics only over the "
                     "byte-identical statement — no new declaration or "
                     "assumption.",
    },
    {
        "id": "pos-kind-prebound",
        "kind": "soundness",
        "expect": "verify",
        # Pure-functional reshape: no `Id.run do`, no mutable local, no branch
        # statement — the kind is computed inline as an `if` expression inside
        # the record literal. A genuinely different data/control shape that is
        # provably the same value on every token.
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "def implementation_annotationRef (text : List Char) : TypeRef :=\n"
                "  { domain := \"py\",\n"
                "    kind := if text = \"None\".toList then \"obj\" else \"class\",\n"
                "    target := text, label := text }\n",
            ),
            _PROOF,
            "  intro text\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  by_cases h : text = \"None\".toList <;> simp [h]\n",
        ),
        "rationale": "a correct impl that drops the imperative wrapper and "
                     "computes the kind inline as an `if` expression still yields "
                     "the same record on every token, so all four clauses hold; "
                     "must verify, else SPEC-TOO-STRONG. Re-proof is tactics only "
                     "over the byte-identical statement.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the exact F2P value-name token 'None' rather
    # than only in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the behavior is total, ``∀ text`` unguarded), so nagini's
    # precondition-admission probe has no binder to attack; the honest analogue
    # discharges the spec predicate at 'None' as a `have` inside the proof
    # region, alongside (and before) the frozen obligation, which is then closed
    # verbatim.
    # =====================================================================
    {
        "id": "admiss-None-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_annotationRef \"None\".toList\n"
            "      (implementation_annotationRef \"None\".toList) := by\n"
            "    unfold problem_spec_annotationRef implementation_annotationRef\n"
            "    simp only [Id.run, if_pos, pure]\n"
            "    exact ⟨rfl, rfl, rfl, rfl⟩\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at the exact F2P value-name "
                     "token 'None' (domain 'py', target/label = the token, kind "
                     "'obj') by `⟨rfl, rfl, rfl, rfl⟩`, then the frozen "
                     "obligation is closed verbatim. Verifies, else the modeled "
                     "behavior is unsatisfiable at the normal input (the analogue "
                     "of PRECOND-TOO-STRONG). Nothing is assumed: the theorem "
                     "STATEMENT is byte-identical, the ground instance is a "
                     "`have` inside the existing tactic body, no new declaration "
                     "or axiom or `sorry`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete token.
    # Reject variants swap only the impl region; the frozen proof is kept (it
    # necessarily fails to close against the reshaped impl, which is precisely
    # why the witness — not the failed build — is what attributes the rejection
    # to the spec).
    # =====================================================================

    # ---- C4 (kind): the value-name arm ----
    {
        "id": "kind-always-class",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BUG: every token classified as the class kind (the old
        # unconditional class reference). Correct on every token EXCEPT the value
        # name, where it must be the object kind.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  return { domain := \"py\", kind := \"class\", target := text, label := text }\n",
        ),
        "refinement": "this is the pre-patch behavior the fix removed: the value "
                      "name is given the class kind, so the F2P assertion for the "
                      "'None' token (which pins reftype='obj') fails => does NOT "
                      "resolve (this IS the original bug). Agrees with gold on "
                      "every other token, so a sampler that never tried the value "
                      "name would miss it.",
        "rationale": "REJECT from clause C4 (result.kind = if text = \"None\".toList "
                     "then \"obj\" else \"class\"): on the value-name arm the kind "
                     "must be the object kind but this impl gives the class kind.",
        "witness": (
            "-- Refuted on the value-name token: C4 forces the object kind there,\n"
            "-- so an unconditional class kind violates it.\n"
            "example : ¬ problem_spec_annotationRef \"None\".toList\n"
            "    (implementation_annotationRef \"None\".toList) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },
    # ---- C4 (kind): the else arm (tags inverted) ----
    {
        "id": "kind-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # The classifier INVERTED: value name -> class kind, every other token ->
        # object kind. Fails C4 in BOTH directions. Witnessed on the ELSE arm
        # (a non-value token), a point distinct from `kind-always-class`.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text = \"None\".toList then\n"
            "    kind := \"class\"\n"
            "  else\n"
            "    kind := \"obj\"\n"
            "  return { domain := \"py\", kind := kind, target := text, label := text }\n",
        ),
        "refinement": "this reverses the rule: a non-value token like 'int' gets "
                      "the object kind (F2P wants class) AND the value name gets "
                      "the class kind (F2P wants obj); BOTH F2P reftype "
                      "assertions fail => does NOT resolve.",
        "rationale": "REJECT from clause C4 in BOTH directions: on the else arm "
                     "(a non-value token) the kind must be the class kind but "
                     "this impl gives the object kind; symmetrically on the "
                     "value-name arm. Witnessed on the else arm at 'int'.",
        "witness": (
            "-- Refuted on a non-value token: C4's else arm forces the class\n"
            "-- kind, so giving the object kind there violates it.\n"
            "example : ¬ problem_spec_annotationRef ['i','n','t']\n"
            "    (implementation_annotationRef ['i','n','t']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },

    # ---- C4 (kind): the else arm at a NEAR-MISS of the discriminating token ----
    # Added by audit. Every other C4 rival is refuted at a point that is either
    # the value name itself or a token bearing no resemblance to it ('int'), so
    # all of them survive a spec whose split were merely APPROXIMATE — a
    # case-insensitive, prefix, or length-keyed classification agrees with C4 at
    # both 'None' and 'int'. This rival misclassifies exactly the case-variant
    # near-misses, which is the sub-domain the shipped reject lane left
    # unattacked, and pins C4 to EXACT case-sensitive equality as a shipped
    # machine-checked case rather than as a prose claim about an unshipped probe.
    {
        "id": "kind-case-insensitive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text.map Char.toLower = \"none\".toList then\n"
            "    kind := \"obj\"\n"
            "  else\n"
            "    kind := \"class\"\n"
            "  return { domain := \"py\", kind := kind, target := text, label := text }\n",
        ),
        "refinement": "case-folding the token before classifying gives the "
                      "object kind to tokens that are not the value name, e.g. "
                      "the lowercase 'none' — which names no documented object, "
                      "so the reference resolves nowhere and the reader gets a "
                      "dead link where a class-kind reference was wanted. It "
                      "agrees with gold on BOTH F2P tokens, so the F2P alone "
                      "would not catch it; it is caught by the clause, which is "
                      "the point of shipping it.",
        "rationale": "REJECT from clause C4 (result.kind = if text = "
                     "\"None\".toList then \"obj\" else \"class\"): the "
                     "condition is EXACT list equality against the value name, "
                     "so a token differing only in letter case takes the else "
                     "arm and must carry the class kind. This impl gives it the "
                     "object kind.",
        "witness": (
            "-- Refuted at a CASE-VARIANT near-miss of the value name: C4 splits\n"
            "-- on exact equality, so a token differing only in case takes the\n"
            "-- else arm and must carry the class kind.\n"
            "example : ¬ problem_spec_annotationRef ['n','o','n','e']\n"
            "    (implementation_annotationRef ['n','o','n','e']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },

    # ---- C2 (target): carry-through, length-shaped attack ----
    {
        "id": "target-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Carry the token through but drop its LAST code point as the target.
        # Correct only on the empty token; wrong (shorter) on every non-empty
        # token (incl. the F2P 'int'/'None').
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text = \"None\".toList then\n"
            "    kind := \"obj\"\n"
            "  else\n"
            "    kind := \"class\"\n"
            "  return { domain := \"py\", kind := kind, target := text.dropLast, label := text }\n",
        ),
        "refinement": "dropping the last character of the target gives reftarget "
                      "= 'in' for 'int' and 'Non' for 'None', so the F2P "
                      "reftarget assertion fails => does NOT resolve. Correct "
                      "only on the empty token.",
        "rationale": "REJECT from clause C2 (result.target = text): the target is "
                     "one character shorter than the token on every non-empty "
                     "token, so the equality fails.",
        "witness": (
            "-- Refuted where the target drops the token's last character: C2\n"
            "-- pins the target to the whole token, so a truncated target fails.\n"
            "example : ¬ problem_spec_annotationRef ['i','n','t']\n"
            "    (implementation_annotationRef ['i','n','t']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },
    # ---- C2 (target): carry-through, constant-echo attack ----
    {
        "id": "target-echo-none",
        "kind": "uniqueness",
        "expect": "reject",
        # Hard-pin the target to the constant value name for EVERY token,
        # ignoring the input — the closest analogue of an "oracle echo". But the
        # target is grounded in the token (C2), so a constant cannot satisfy it
        # for any other token. Correct only when the token IS the value name.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text = \"None\".toList then\n"
            "    kind := \"obj\"\n"
            "  else\n"
            "    kind := \"class\"\n"
            "  return { domain := \"py\", kind := kind, target := \"None\".toList, label := text }\n",
        ),
        "refinement": "hard-coding the target to the constant value name gives "
                      "reftarget='None' for the token 'int', so the F2P reftarget "
                      "assertion fails => does NOT resolve. Correct only when the "
                      "token itself is the value name.",
        "rationale": "REJECT from clause C2 (result.target = text): the constant "
                     "value name differs from the token for every token other "
                     "than the value name, so the equality fails.",
        "witness": (
            "-- Refuted on a non-value token: C2 pins the target to the token\n"
            "-- itself, so a constant target differs from it.\n"
            "example : ¬ problem_spec_annotationRef ['i','n','t']\n"
            "    (implementation_annotationRef ['i','n','t']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },

    # ---- C1 (domain): carrier-widening rival (no nagini counterpart) ----
    {
        "id": "domain-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the wrong reference domain for EVERY token. This attacks the
        # component the modeled change leaves untouched (the referentially-
        # transparent analogue of the nagini FRAME concern): a rival that
        # corrupts the always-'py' domain. Without clause C1 the spec would let
        # it verify.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text = \"None\".toList then\n"
            "    kind := \"obj\"\n"
            "  else\n"
            "    kind := \"class\"\n"
            "  return { domain := \"js\", kind := kind, target := text, label := text }\n",
        ),
        "refinement": "emitting a wrong reference domain makes every token "
                      "resolve in the wrong documentation set, so the F2P "
                      "refdomain='py' assertion fails => does NOT resolve. This "
                      "corrupts a component the modeled change leaves untouched, "
                      "so a faithful such patch would regress the domain the "
                      "surrounding behavior guarantees.",
        "rationale": "REJECT from clause C1 (result.domain = \"py\"): this impl "
                     "returns a different domain, so C1 fails on every token. "
                     "This is the clause that pins the UNCHANGED domain "
                     "component; a spec leaving result.domain free would wrongly "
                     "accept this rival.",
        "witness": (
            "-- Refuted on any token: C1 pins the domain to \"py\", so a wrong\n"
            "-- domain violates it.\n"
            "example : ¬ problem_spec_annotationRef ['i','n','t']\n"
            "    (implementation_annotationRef ['i','n','t']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },

    # ---- C3 (label): carrier-widening rival (no nagini counterpart) ----
    {
        "id": "label-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Carry the token through as the target but drop the last code point of
        # the visible LABEL. Attacks the other carry-through clause the record
        # carrier makes observable; witnessed at an all-distinct token where the
        # target is correct but the label is short.
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text = \"None\".toList then\n"
            "    kind := \"obj\"\n"
            "  else\n"
            "    kind := \"class\"\n"
            "  return { domain := \"py\", kind := kind, target := text, label := text.dropLast }\n",
        ),
        "refinement": "dropping the last character of the visible label shows a "
                      "truncated token to the reader (e.g. 'in' for 'int'), so "
                      "the F2P assertion pinning the displayed text to the whole "
                      "token fails => does NOT resolve. This corrupts a "
                      "carry-through component the modeled change leaves "
                      "untouched.",
        "rationale": "REJECT from clause C3 (result.label = text): the label is "
                     "one character shorter than the token on every non-empty "
                     "token, so the equality fails. C3 is the visible-label "
                     "carry-through clause the record carrier makes observable.",
        "witness": (
            "-- Refuted where the label drops the token's last character: C3\n"
            "-- pins the label to the whole token, so a truncated label fails.\n"
            "example : ¬ problem_spec_annotationRef ['a','b','c']\n"
            "    (implementation_annotationRef ['a','b','c']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },

    # ---- C2+C3 (carry-through): CONTENT corruption at UNCHANGED LENGTH ----
    # The expressible observable footprint of the nagini frame rival (see the
    # PORT NOTE). Every other carry-through rival here is LENGTH-shaped
    # (dropLast) or constant-valued, so all of them would still be caught by a
    # spec that pinned only `result.target.length = text.length`. This one emits
    # a same-length token with one character replaced, so it is refuted ONLY by
    # the full list equality C2/C3 actually state.
    {
        "id": "content-corrupt-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL,
            "def implementation_annotationRef (text : List Char) : TypeRef := Id.run do\n"
            "  let mut kind := \"class\"\n"
            "  if text = \"None\".toList then\n"
            "    kind := \"obj\"\n"
            "  else\n"
            "    kind := \"class\"\n"
            "  let scratch := text.set 0 'X'\n"
            "  return { domain := \"py\", kind := kind, target := scratch, label := scratch }\n",
        ),
        "refinement": "building the reference from a scribbled-over copy of the "
                      "token emits target and displayed text 'Xnt' for the token "
                      "'int' and 'Xone' for 'None' — the same LENGTH as the token "
                      "but not the token — so the F2P assertions pinning both the "
                      "looked-up target and the visible text to the whole token "
                      "fail => does NOT resolve. The kind classification is left "
                      "correct, so this rival is refuted purely by the "
                      "carry-through clauses.",
        "rationale": "REJECT from clauses C2 (result.target = text) and C3 "
                     "(result.label = text): both are full LIST equalities, not "
                     "length or prefix constraints, so a same-length token with "
                     "one character replaced violates them. This is the only "
                     "rival attacking carry-through CONTENT independently of "
                     "length; the dropLast rivals would both survive a spec that "
                     "pinned only the length.",
        "witness": (
            "-- Refuted at a LENGTH-ONE token, where a truncation would give the\n"
            "-- empty list but this impl gives a same-length corrupted token: C2\n"
            "-- and C3 pin the target and label to the token itself.\n"
            "example : ¬ problem_spec_annotationRef ['x']\n"
            "    (implementation_annotationRef ['x']) := by\n"
            "  unfold problem_spec_annotationRef implementation_annotationRef\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: all four components are
# computed by straight-line data from the token (mapping.md records no
# opaque/axiom callee), so there is no in-model axiom obligation for the PBT
# axiom lane to re-discharge. The axiom lane is G-AX's job in any case.
AXIOM_TESTS = []
