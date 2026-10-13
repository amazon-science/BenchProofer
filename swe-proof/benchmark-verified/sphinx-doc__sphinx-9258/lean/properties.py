"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9258 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior, one obligation). A type specification
string (a ``List Char``) is tokenised into an ordered list of classified
segments: it is split left-to-right at a separator alternation, the empty pieces
are dropped, and every surviving piece is classified either as separator text
kept verbatim or as a type name to be cross-referenced. The specification pins
the result to the reference tokenisation exactly:

  splitTypeSpec (target : List Char) : List Seg
      result = tokenize target

where ``tokenize`` splits with the separator alternation that treats a vertical
bar (optionally padded by whitespace) as one of the separators, drops empties,
and classifies each survivor by whether its front matches that alternation. The
sole binder of the spec predicate is ``target``; the postcondition is a single
definitional equality that pins BOTH the number/order of emitted segments AND
the separator-vs-name tag of each, index by index — there is no slack.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini battery's mandatory
    frame-mutation rival writes into a read-only half-permission input to prove
    the store is rejected for insufficient permission. Lean is referentially
    transparent: the input ``target`` carries no heap permission, there is no
    read-only fraction to overwrite and no aliasing to exploit. This class has
    no expressible instance here and no substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS as a WRONG echo. The postcondition equates
    the result to ``tokenize target`` fully spelled out over the input as a
    ``pure``-region fold (split / drop-empties / classify), and the bundle
    declares no ``opaque``/``axiom`` — there is no answer key to echo without
    doing the work. An impl that returns ``tokenize target`` is simply the
    CORRECT computation; it is used below as the structurally-different
    soundness positive, not as a wrong rival.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole battery. The nagini
    partial-domain rivals (correct on the no-bar sub-domain, wrong once a bar
    appears) port directly: a rival that never splits on the bar (the leg's
    prepatch), a rival that splits but drops the separator segments, and a rival
    that emits the right number of segments but mis-tags the separators as
    names. A fourth rival, added by audit, keeps the EMPTY split pieces instead
    of discarding them — the one postcondition clause the ported three all left
    unattacked. A fifth, added by a second audit, keeps the right arity AND the
    right tags but does not keep the separator text VERBATIM (it drops the
    separator's padding whitespace) — the remaining postcondition clause, and
    the only rival whose divergence is in a segment's CONTENT rather than in
    the split arity or the tag. Each shares the frozen spec and diverges from
    ``tokenize`` on a concrete input.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class. This bundle
    sets no termination semantics option, and on this carrier the only way to
    write a diverging splitter is ``partial def``, whose body is opaque to
    reduction. Such a rival IS rejected (the frozen script cannot close it), but
    its refutation is not shippable: a ``decide`` witness against it fails with
    ``Tactic `decide` failed ... its `Decidable` instance instDecidableNot did
    not reduce to `isTrue` or `isFalse``` — the rival side, which is the half a
    witness must PROVE, so no witness can attribute that rejection to the spec.
    A ``witness_reference`` cannot help either: it substitutes the gold side,
    not the stuck rival side. Measured, not assumed; recorded here as a hole in
    what the spec can be shown to sense, not as a class that does not exist.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (a structured induction over the
split list, keyed to the frozen imperative loop) is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input. The carriers are fully concrete (``List Char`` literals,
``Seg`` derives ``DecidableEq``), so the whole ``tokenize`` fold and the rival's
``Id.run do`` loop evaluate under ``decide``. Each was checked to hold of its
rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology).

BINDER / POINT SPREAD. The one spec binder ``target`` is moved across all five
reject witnesses rather than fixed at one convenient point: a bare-bar input
``"x|y"``, a spaced-bar (F2P-shaped) input ``"a | b"``, a MIXED-separator input
``"a | b, c"`` (five survivors, both a padded bar and a comma) at which the
separator/name tag is the sole divergence, a leading-bar input ``"|x"`` whose
split contains an empty piece, and a KEYWORD-separator input ``"a or b"`` — the
only point in the battery at which the bar plays no role at all, so the spec is
shown to pin the non-bar alternatives of the alternation too, not merely the one
the leg adds. The five differ in split arity as well as in content, so the
battery demonstrates the spec's dependence on the CONTENT of ``target`` (which
characters split, whether the bar splits at all, whether empty pieces are
dropped, how each survivor is tagged, and whether separator text is kept
verbatim) rather than agreeing with gold everywhere but one canonical string.

AXIOM lane: EMPTY. meta.json axioms == [] and there is no consumed callee axiom
or axiomatized deep-model reference (the splitter/classifier is a ``pure``-region
fold over the observable input), so there is no axiom-soundness / axiom-
containment obligation to probe here (that lane belongs to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9258"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl region, verbatim (everything strictly BETWEEN the
# `-- impl-start` / `-- impl-end` markers). Every reject rival replaces this
# whole block, so the edit never touches the spec/pure/post regions or the proof
# statement; same_spec is guaranteed. `_BASE.count(_IMPL) == 1` anchors it.
_IMPL = (
    "def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do\n"
    "  let subTargets := reSplit true target\n"
    "  let mut results : List Seg := []\n"
    "  for sub in subTargets do\n"
    "    if sub ≠ [] then\n"
    "      if (delimLen true sub).isSome then\n"
    "        results := results ++ [Seg.sep sub]\n"
    "      else\n"
    "        results := results ++ [Seg.name sub]\n"
    "  return results\n"
)

assert _BASE.count(_IMPL) == 1, "split impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean variant with ONLY the impl region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# The frozen proof-region content (theorem statement + tactic body). Used to
# splice a re-proved tactic body for the soundness positive while keeping the
# `theorem correct_splitTypeSpec` STATEMENT byte-identical.
_THEOREM_STMT = (
    "theorem correct_splitTypeSpec :\n"
    "    ∀ (target : List Char),\n"
    "      problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by\n"
)


def _replace_proof_region(src, new_body):
    """Replace the entire proof-region content with `new_body` (markers kept)."""
    head = "-- proof-start\n"
    tail = "-- proof-end"
    lo = src.index(head) + len(head)
    hi = src.index(tail)
    return src[:lo] + new_body + src[hi:]


# ---------------------------------------------------------------------------
# SOUNDNESS positive — a structurally different but CORRECT implementation.
# Instead of the imperative accumulator loop, the result is the reference
# tokenisation directly. Observationally IT IS `tokenize target` on every input
# (that is the grounded deep model, not an opaque oracle — refinement.md blesses
# `:= tokenize target` as a correct positive control, not a wrong echo), so
# `result = tokenize target` holds by `rfl`. Re-proved because the frozen script
# is a structured induction over the loop and no longer applies; the new body is
# `rfl` with no new declaration, no axiom, no sorry, and the theorem statement
# byte-identical. If it FAILS => SPEC-TOO-STRONG (a faithful correct impl is
# rejected).
_POS_DIRECT = _replace_proof_region(
    _swap(
        _BASE, _IMPL,
        "def implementation_splitTypeSpec (target : List Char) : List Seg :=\n"
        "  -- Structurally different correct shape: return the reference\n"
        "  -- tokenisation directly instead of rebuilding it with an imperative\n"
        "  -- accumulator loop.\n"
        "  tokenize target\n",
    ),
    _THEOREM_STMT
    + "  intro target\n"
    + "  show implementation_splitTypeSpec target = tokenize target\n"
    + "  rfl\n",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the modeled behavior is SATISFIABLE (non-vacuous) at the
# F2P-shaped input (a spaced-bar union type), not only provable in the abstract.
# The frozen theorem carries no precondition hypothesis (the behavior is total,
# `∀` is unguarded), so the honest analogue of the nagini precondition-admission
# probe is to discharge the spec predicate at that ground input by evaluation,
# alongside the frozen obligation. Keeps the gold impl verbatim; only prepends a
# `have` inside the tactic body, then closes the frozen obligation unchanged.
_ADMISS = _swap(
    _BASE,
    "      problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by\n"
    "  intro target\n",
    "      problem_spec_splitTypeSpec target (implementation_splitTypeSpec target) := by\n"
    "  -- admissibility: the modeled behavior is SATISFIABLE at the F2P-shaped\n"
    "  -- input (a spaced-bar union type), reported by evaluation, before the\n"
    "  -- frozen obligation is closed verbatim.\n"
    "  have _ground :\n"
    "      problem_spec_splitTypeSpec \"a | b\".toList\n"
    "        (implementation_splitTypeSpec \"a | b\".toList) := by\n"
    "    unfold problem_spec_splitTypeSpec\n"
    "    decide\n"
    "  intro target\n",
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals — wrong impls sharing the frozen spec that
# MUST be rejected (else SPEC-TOO-WEAK). Each replaces the whole impl region.

# R1 — weak-single-name (the leg's PREPATCH): split with the alternation that
# does NOT treat the vertical bar as a separator, so a bar-joined spec is never
# split around the bar and is emitted as a SINGLE type name.
_R1_SINGLE = (
    "def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do\n"
    "  let subTargets := reSplit false target\n"
    "  let mut results : List Seg := []\n"
    "  for sub in subTargets do\n"
    "    if sub ≠ [] then\n"
    "      if (delimLen false sub).isSome then\n"
    "        results := results ++ [Seg.sep sub]\n"
    "      else\n"
    "        results := results ++ [Seg.name sub]\n"
    "  return results\n"
)

# R2 — weak-drop-separator: split correctly (bar recognised) but DROP the
# separator survivors, emitting only the type names. The separator segment that
# the fix renders between two names is omitted entirely.
_R2_NOSEP = (
    "def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do\n"
    "  let subTargets := reSplit true target\n"
    "  let mut results : List Seg := []\n"
    "  for sub in subTargets do\n"
    "    if sub ≠ [] then\n"
    "      if (delimLen true sub).isSome then\n"
    "        results := results\n"
    "      else\n"
    "        results := results ++ [Seg.name sub]\n"
    "  return results\n"
)

# R3 — weak-all-name: split correctly and emit the right NUMBER of segments, but
# classify EVERY survivor — including the separators — as a type name. The
# separator/name tag at the separator index is wrong.
_R3_ALLNAME = (
    "def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do\n"
    "  let subTargets := reSplit true target\n"
    "  let mut results : List Seg := []\n"
    "  for sub in subTargets do\n"
    "    if sub ≠ [] then\n"
    "      results := results ++ [Seg.name sub]\n"
    "  return results\n"
)

# R4 — weak-keep-empties: split correctly AND tag every survivor correctly, but
# never DROP the empty pieces. The capturing split emits an empty free-text piece
# whenever a separator sits at the very start/end of the spec or two separators
# abut, so this rival emits a spurious extra empty type-name segment at exactly
# those points while agreeing with the reference everywhere else. Isolates the
# drop-empties clause, which no other rival in this battery attacks (R1 attacks
# whether the bar splits, R2 whether separators survive, R3 how they are tagged).
_R4_KEEPEMPTY = (
    "def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do\n"
    "  let subTargets := reSplit true target\n"
    "  let mut results : List Seg := []\n"
    "  for sub in subTargets do\n"
    "    if (delimLen true sub).isSome then\n"
    "      results := results ++ [Seg.sep sub]\n"
    "    else\n"
    "      results := results ++ [Seg.name sub]\n"
    "  return results\n"
)


# R5 — weak-sep-not-verbatim: split correctly, keep every survivor, and tag every
# survivor correctly — but do not keep the separator text VERBATIM: the
# separator's padding whitespace is stripped out of the emitted segment. Arity
# and tags both match the reference at every input; the divergence is purely in
# the CONTENT of a separator segment, the one postcondition clause the other four
# rivals leave unattacked (R1 attacks whether the bar splits, R2 whether
# separators survive, R3 how they are tagged, R4 whether empties are dropped —
# all four keep the surviving text verbatim). Its witness also moves `target` to
# the only point in the battery where the bar plays NO role, so the spec is shown
# to pin the keyword alternative of the separator alternation as well.
_R5_SEPTRIM = (
    "def implementation_splitTypeSpec (target : List Char) : List Seg := Id.run do\n"
    "  let subTargets := reSplit true target\n"
    "  let mut results : List Seg := []\n"
    "  for sub in subTargets do\n"
    "    if sub ≠ [] then\n"
    "      if (delimLen true sub).isSome then\n"
    "        results := results ++ [Seg.sep (sub.filter (fun c => !isSp c))]\n"
    "      else\n"
    "        results := results ++ [Seg.name sub]\n"
    "  return results\n"
)


# ---------------------------------------------------------------------------
# SECOND soundness positive — a correct reshape whose proof is NOT `rfl`.
# `pos-direct-tokenize` above is honest but definitionally trivial: its impl IS
# the spec's right-hand side, so `rfl` closes it and the case exercises only that
# the spec is satisfiable at all. This one folds the classified survivors up with
# `List.foldl` and an append accumulator instead — extensionally `tokenize
# target`, but NOT definitionally equal to it, so `rfl` does not close it and the
# case is discharged by a genuine induction with an accumulator generalisation.
# That makes it a real SPEC-TOO-STRONG probe: a spec over-fitted to either the
# frozen imperative loop or to the `map`-over-`filter` normal form would reject
# this faithful correct impl.
_POS_FOLDL = _replace_proof_region(
    _swap(
        _BASE, _IMPL,
        "def implementation_splitTypeSpec (target : List Char) : List Seg :=\n"
        "  -- Structurally different correct shape: fold the classified survivors\n"
        "  -- up with an append accumulator. Extensionally the reference\n"
        "  -- tokenisation, but not definitionally equal to it, so this needs a\n"
        "  -- real induction rather than `rfl`.\n"
        "  ((reSplit true target).filter (· ≠ [])).foldl\n"
        "    (fun acc p => acc ++ [classifySeg p]) []\n",
    ),
    _THEOREM_STMT
    + "  intro target\n"
    + "  show implementation_splitTypeSpec target = tokenize target\n"
    + "  unfold implementation_splitTypeSpec tokenize\n"
    + "  generalize ((reSplit true target).filter (· ≠ [])) = l\n"
    + "  suffices h : ∀ (acc : List Seg),\n"
    + "      l.foldl (fun acc p => acc ++ [classifySeg p]) acc"
    + " = acc ++ l.map classifySeg by\n"
    + "    simpa using h []\n"
    + "  induction l with\n"
    + "  | nil => intro acc; simp\n"
    + "  | cons a t ih => intro acc; simp [ih (acc ++ [classifySeg a])]\n",
)


# ---------------------------------------------------------------------------
# Witness helper. States the spec predicate directly at a concrete `target`
# literal; the whole `tokenize` fold and the impl loop evaluate under `decide`.

def _witness(target, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_splitTypeSpec {target}\n"
        f"    (implementation_splitTypeSpec {target}) := by\n"
        f"  unfold problem_spec_splitTypeSpec implementation_splitTypeSpec\n"
        f"  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS positive — MUST verify (else SPEC-TOO-STRONG).
    # =====================================================================
    {
        "id": "pos-direct-tokenize",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "structurally-different but CORRECT impl: the result is the reference "
            "tokenisation returned directly rather than rebuilt by the imperative "
            "accumulator loop; it IS `tokenize target` on every input, so "
            "`result = tokenize target` holds by `rfl`. The postcondition binder "
            "`target` is left fully general. Re-proved because the frozen "
            "structured induction is keyed to the imperative loop and no longer "
            "applies; the new body is `rfl` with no new declaration, no axiom, no "
            "sorry, and the `theorem correct_splitTypeSpec` statement "
            "byte-identical. If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-foldl-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLDL,
        "rationale": (
            "second structurally-different CORRECT impl, and the one that "
            "actually loads the obligation: the classified survivors are folded "
            "up with `List.foldl` and an append accumulator, which is "
            "extensionally `tokenize target` but NOT definitionally equal to it, "
            "so `rfl` does not close it (unlike `pos-direct-tokenize`, whose impl "
            "IS the spec's right-hand side). Discharged by a real induction over "
            "the split list with the accumulator generalised, with no new "
            "declaration, no axiom, no sorry, and the `theorem "
            "correct_splitTypeSpec` statement byte-identical. If it FAILS => "
            "SPEC-TOO-STRONG: the spec would be over-fitted to a normal form "
            "(the frozen imperative loop, or `map`-over-`filter`) rather than to "
            "the tokenisation itself."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the modeled behavior is SATISFIABLE at the F2P input.
    # =====================================================================
    {
        "id": "admiss-f2p-piped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the spec predicate is discharged at the ground F2P-shaped input (a "
            "spaced-bar union type) by `decide`, confirming the modeled behavior "
            "is satisfiable at the very input the F2P exercises, then the frozen "
            "obligation is closed verbatim. Nothing is assumed: no new "
            "declaration, the theorem statement is byte-identical, and the ground "
            "instance is a `have` inside the existing tactic body. If it FAILS => "
            "the modeled behavior would be unsatisfiable at the F2P input (the "
            "analogue of PRECOND-TOO-STRONG)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — MUST be rejected. Each carries (a) the
    # refinement argument that its faithful real patch would NOT resolve the F2P
    # (so a verifying rival is a true verify-does-not-imply-resolve break, not an
    # artifact), and (b) a refutation witness pinning the violation at one
    # concrete input, checked to hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "weak-single-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R1_SINGLE),
        "refinement": (
            "splitting with the alternation that does NOT treat the vertical bar "
            "as a separator is EXACTLY the pre-existing (unfixed) behavior: a "
            "bar-joined union type is emitted as a single type name rather than "
            "the several names the F2P demands around a bar separator. The F2P "
            "asserts multiple separate cross-references with a literal separator "
            "between them, so this rival FAILS the F2P — it would NOT resolve; "
            "this is the leg's prepatch."
        ),
        "rationale": (
            "REJECT from `result = tokenize target`: on any bar-joined spec the "
            "reference tokenisation splits around the bar into several segments, "
            "while the rival returns a single name segment. Refuted at a bare-bar "
            "input where the bar is the decisive splitting character."
        ),
        "witness": _witness(
            '"x|y".toList',
            "Refuted on a bare-bar spec: the reference tokenisation splits around "
            "the bar into a name / separator / name triple, but the rival keeps it "
            "one name — so whether the bar splits is the decisive property of "
            "`target` here.",
        ),
    },
    {
        "id": "weak-drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R2_NOSEP),
        "refinement": (
            "splitting correctly but DROPPING the separator survivors — emitting "
            "only the type names — is what a real patch that split on the bar yet "
            "then discarded the separator pieces would do. The F2P asserts the "
            "literal separator node BETWEEN the two cross-references is rendered "
            "(not dropped); a result missing it is structurally different and "
            "fails the F2P assertion, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = tokenize target`: the reference tokenisation "
            "keeps the separator survivor as a `Seg.sep`, so the result length and "
            "the entry at the separator index disagree with the rival, which omits "
            "it. Refuted at a spaced-bar (F2P-shaped) input, moving `target` to a "
            "point with a padded-bar separator."
        ),
        "witness": _witness(
            '"a | b".toList',
            "Refuted on a spaced-bar spec: the reference tokenisation emits the "
            "padded-bar separator between the two names, but the rival drops it — "
            "so the presence of the separator survivor in `target`'s split is "
            "decisive.",
        ),
    },
    {
        "id": "weak-all-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R3_ALLNAME),
        "refinement": (
            "classifying every split survivor — including the separators — as a "
            "type name is what a real patch that dropped the per-piece "
            "separator-recognition test (always taking the cross-reference branch) "
            "would do. It would render the literal separator as a cross-reference "
            "instead of verbatim separator text, so the F2P (which asserts the "
            "separator is a literal node, NOT a cross-reference) fails; it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = tokenize target`: the reference tokenisation "
            "tags the separator survivor `Seg.sep` while the rival tags it "
            "`Seg.name`. The segment COUNT matches; only the tag at the separator "
            "index diverges. Refuted at a MIXED-separator input carrying both a "
            "padded bar and a comma separator, so the mis-tagging is exhibited at "
            "two separator kinds at once and the point is structurally distinct "
            "from the other rivals' (5 survivors, not 3)."
        ),
        "witness": _witness(
            '"a | b, c".toList',
            "Refuted on a mixed-separator spec where the segment count matches: "
            "both the padded-bar and the comma survivor must be tagged as "
            "separator text rather than cross-references, so the classification "
            "of those survivors in `target`'s split is decisive.",
        ),
    },
    {
        "id": "weak-keep-empties",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R4_KEEPEMPTY),
        "refinement": (
            "splitting correctly and tagging every survivor correctly, but never "
            "discarding the EMPTY pieces the capturing split emits, is what a real "
            "patch that iterated the raw split list without the empty-piece filter "
            "would do. A separator at the very start or end of a specification, or "
            "two abutting separators, makes the split yield an empty free-text "
            "piece; keeping it renders a spurious empty cross-reference alongside "
            "the real ones. The F2P asserts an exact node sequence, so an extra "
            "empty cross-reference node breaks it; it would NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = tokenize target`: the reference tokenisation "
            "filters the empty pieces out before classifying, so on a "
            "leading-separator specification the rival's result is one segment "
            "LONGER than the reference and carries an empty name segment the "
            "reference never emits. This isolates the drop-empties clause of the "
            "postcondition, which the other three rivals leave unattacked — they "
            "vary whether the bar splits, whether separators survive, and how "
            "survivors are tagged, but all three drop empties correctly. Refuted at "
            "a leading-bar input, a fourth distinct point for `target`."
        ),
        "witness": _witness(
            '"|x".toList',
            "Refuted on a leading-bar spec: the capturing split emits an empty "
            "free-text piece before the bar, which the reference tokenisation "
            "discards and the rival keeps as an empty type name — so whether the "
            "empty pieces of `target`'s split are dropped is decisive here.",
        ),
    },
    {
        "id": "weak-sep-not-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R5_SEPTRIM),
        "refinement": (
            "splitting correctly, keeping every survivor and tagging every "
            "survivor correctly, but emitting the separator with its padding "
            "whitespace stripped, is what a real patch that normalised each "
            "separator piece before rendering it (rather than passing the matched "
            "text through unchanged) would do. The F2P asserts the separator node "
            "carries the separator text as it appeared in the specification, "
            "padding included; a separator rendered with its padding removed is a "
            "different node than the one asserted, so the F2P fails and this "
            "rival would NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = tokenize target`: the reference tokenisation "
            "keeps each surviving piece VERBATIM, so a separator survivor that "
            "carries padding whitespace must be emitted with that whitespace "
            "intact. This rival's result has the right length and the right "
            "separator/name tag at every index — the divergence is purely in the "
            "CONTENT of a separator segment, which no other rival in this battery "
            "attacks (they vary whether the bar splits, whether separators "
            "survive, how survivors are tagged, and whether empties are dropped, "
            "but all four keep the surviving text verbatim). Refuted at a "
            "KEYWORD-separator input, a fifth distinct point for `target` and the "
            "only one where the vertical bar plays no role — so the spec is shown "
            "to pin the whole separator alternation, not just the bar alternative."
        ),
        "witness": _witness(
            '"a or b".toList',
            "Refuted on a keyword-separator spec, where arity and tags both "
            "match: the reference tokenisation emits the surrounding whitespace "
            "as part of the separator survivor and the rival strips it, so "
            "whether each survivor of `target`'s split is kept verbatim is "
            "decisive here — and this point involves no vertical bar at all.",
        ),
    },
]


# No consumed callee axiom and no axiomatized deep-model reference: the splitter
# and classifier are `pure`-region folds over the observable input, so there is
# no axiom-soundness / axiom-containment obligation to probe. That lane is
# G-AX's job in any case.
AXIOM_TESTS = []
