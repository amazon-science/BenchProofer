"""properties.py — G-PBT falsification battery for django__django-14539 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior over two character sequences):

  peelTrailingPunct (token tailPunct : List Char)
      -> (newToken, newTailPunct, trimmed : List Char × List Char × Bool)

A run of trailing punctuation is peeled off the end of ``token`` and prepended
to the accumulator ``tailPunct``. The *length* of that run is measured on the
entity-DECODED view of ``token`` (a standard decoder, opaque here, folds entity
sequences first so a ``;`` inside an entity is not mistaken for punctuation).
The characters actually peeled, however, are taken from the END of the ORIGINAL
``token`` and the same count is removed from it. The frozen postcondition is a
four-way conjunction, all four clauses grounded in the two input sequences and
the decoded-view lengths:

  * C1  result.1   = dropRightN token punctCount          (token minus its tail)
  * C2  result.2.1 = takeRightN token punctCount ++ tailPunct   (moved tail
        PREPENDED to the incoming accumulator)
  * C3  result.2.2 = decide (decoded ≠ stripped)          (did-peel flag)
  * C4  result.1 ++ result.2.1 = token ++ tailPunct       (conservation: the
        run is MOVED, never duplicated)

where ``punctCount = decoded.length - stripped.length`` and ``decoded`` is the
opaque decoder applied to ``token``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION (nagini cases 3 and 4, the mandatory
    ``middle``/``trail`` write rivals) — VACUOUS. Lean is referentially
    transparent: ``token`` and ``tailPunct`` are pure ``List Char`` VALUES, not
    heap objects lent at a fractional permission. There is no read-only
    half-permission to overwrite, no aliasing, and no in-place ``append`` to
    forbid — the two nagini frame rivals are not even expressible. No substitute
    is fabricated (per the porting map, this class is legitimately empty here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. All four clauses are equalities against
    terms built from the inputs (``dropRightN``/``takeRightN`` of ``token``,
    ``++ tailPunct``, and the decoded-view lengths); there is no axiomatized
    answer-key oracle to echo. The nagini sibling reached the same conclusion.

  * AXIOM lane (nagini AXIOM_TESTS: A-reference soundness + containment for the
    decode/rstrip length summaries) — DROPPED. That is G-AX's job; this gate
    ignores it. Here ``decode`` is declared ``opaque`` and NO property of it is
    consumed by the proof, so there is no axiom to probe in this lane at all.

  * PREPATCH BUG (nagini case 2) — PORTED as ``weak-prepatch-decoded-boundary``.
  * PARTIAL-DOMAIN count==1 (nagini case 5) — PORTED as
    ``weak-partial-domain-count1``.
  * POSITIVE CONTROL (nagini case 1) — PORTED as ``pos-control-reshaped``.
  * ADMISSIBILITY (nagini case 6) — PORTED as ``admiss-fshaped-input``.

  Two rivals with NO nagini counterpart are ADDED to cover clauses the nagini
  battery left implicit on this carrier: ``weak-flag-never-set`` attacks the
  boolean did-peel clause C3 (nagini's model returned only the two lists — the
  Bool is a Lean-carrier observable), and ``weak-drop-incoming-tail`` attacks
  the ``++ tailPunct`` half of C2/C4 through the SECOND input binder, which the
  ported nagini rivals only ever hold non-adversarially.

WITNESSES — the carrier's defining subtlety. On a tactic-proof backend "did not
verify" is the DEFAULT outcome of reshaping an implementation (the frozen script
is tuned to the frozen ``if``-guarded form), so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet proving the rival CONTRADICTS the spec at one concrete input.

Because ``decode`` is OPAQUE, ``decode token`` does not reduce at any concrete
literal — so a bare ``decide`` witness cannot even state the decoded-view
length. Each witness therefore SUPPLIES the decoded view as a local hypothesis
``h : decode <lit> = <lit'>`` and rewrites by it before ``decide``. That same
hypothesis is exactly what makes the frozen solution satisfy the spec at the
point, so the witness DISCRIMINATES: it elaborates against the rival (the rival
provably violates the spec under ``h``) and FAILS against gold (gold satisfies
the spec under ``h``). Both halves were run with scripts/lean_verify.sh on every
witness before shipping. No witness uses ``sorry``/``admit``/``native_decide``.

BINDER COVERAGE. The spec has two input binders, ``token`` and ``tailPunct``.
The reject witnesses vary BOTH across four distinct input points:
  * ``weak-prepatch``: token = "g&!"  (entity-bearing), tailPunct = "q"
  * ``weak-partial``:  token = "a!!"  (two-punct run, no entity), tailPunct = ""
  * ``weak-flag``:     token = "a!"   (single punct),   tailPunct = "z"
  * ``weak-drop-tail``: token = "a!"  (single punct),   tailPunct = "wv"
``tailPunct`` is EMPTY in one witness and non-empty (three different values) in
the others, so the ``++ tailPunct`` dependence in C2/C4 is genuinely exercised;
``weak-drop-incoming-tail`` is refuted specifically at a non-empty ``tailPunct``
where ignoring the accumulator first diverges. The entity distinction that the
bug turns on lives inside ``decode``, which is opaque, so it is supplied through
the per-witness ``h`` hypothesis rather than through a concrete token alone.
"""
from pathlib import Path

INSTANCE = "django__django-14539"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique and entirely inside its region) ------------
# The FULL frozen impl def body (inside the impl region) and the opening of the
# frozen tactic body up to and including the `by_cases` split (inside the proof
# region). Every replacement lands within the region it means to edit, so
# same_spec holds and the `theorem correct_*` statement is untouched.
_GOLD_IMPL = (
    "def implementation_peelTrailingPunct (token tailPunct : List Char) :\n"
    "    List Char × List Char × Bool := Id.run do\n"
    "  let mut token := token\n"
    "  let mut tailPunct := tailPunct\n"
    "  let mut trimmed := false\n"
    "  let decoded := decode token\n"
    "  let stripped := rstripPunct decoded\n"
    "  if decoded ≠ stripped then\n"
    "    let punctCount := decoded.length - stripped.length\n"
    "    tailPunct := takeRightN token punctCount ++ tailPunct\n"
    "    token := dropRightN token punctCount\n"
    "    trimmed := true\n"
    "  return (token, tailPunct, trimmed)"
)

# The opening of the frozen proof, entirely inside the proof region. Prepending
# the admissibility `have` here keeps the `theorem correct_*` statement and the
# rest of the tactic body byte-identical.
_PROOF_OPEN = (
    "  intro token tailPunct\n"
    "  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : decode token ≠ rstripPunct (decode token)"
)


# ---- soundness positive: structurally reshaped, CORRECT ---------------------
# Bind the ORIGINAL token to `orig`, build the retained part FIRST via
# `dropRightN orig`, then the moved tail via `takeRightN orig` (the reverse of
# the frozen order), inline the count `decoded.length - stripped.length` at both
# uses (no `punctCount` local). Same take/drop boundaries on the same original
# sequence, so it computes the identical result on every input and the FROZEN
# proof closes it unchanged — no reproof, no new lemma, no assumption token.
_POS_IMPL = (
    "def implementation_peelTrailingPunct (token tailPunct : List Char) :\n"
    "    List Char × List Char × Bool := Id.run do\n"
    "  let orig := token\n"
    "  let mut token := token\n"
    "  let mut tailPunct := tailPunct\n"
    "  let mut trimmed := false\n"
    "  let decoded := decode orig\n"
    "  let stripped := rstripPunct decoded\n"
    "  if decoded ≠ stripped then\n"
    "    token := dropRightN orig (decoded.length - stripped.length)\n"
    "    tailPunct := takeRightN orig (decoded.length - stripped.length) ++ tailPunct\n"
    "    trimmed := true\n"
    "  return (token, tailPunct, trimmed)"
)


# ---- admissibility positive: ground instance + frozen proof -----------------
# Prepend, inside the SAME tactic body, a `have` discharging the obligation at a
# concrete F2P-shaped ENTITY-BEARING input (token "g&!" whose decoded view "g!"
# is shorter, the exact bug-triggering domain) UNDER the decoded-view hypothesis
# — since `decode` is opaque the ground fact is an implication `decode ... = ...
# -> spec`, discharged by `decide` after rewriting. Then close the frozen
# obligation verbatim. No new declaration; statement byte-identical.
_ADMISS_HAVE = (
    "  have _ground : decode ['g', '&', '!'] = ['g', '!'] →\n"
    "      problem_spec_peelTrailingPunct ['g', '&', '!'] ['q']\n"
    "        (implementation_peelTrailingPunct ['g', '&', '!'] ['q']) := by\n"
    "    intro hg\n"
    "    unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
    "    simp only [hg]\n"
    "    decide\n"
    "  intro token tailPunct\n"
    "  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : decode token ≠ rstripPunct (decode token)"
)


# ---- uniqueness rivals (impl-only reshape; frozen proof retained) -----------
# (2) PREPATCH BUG: the peeled tail is taken by DROPPING the first
# `stripped.length` characters of the ORIGINAL token. That index is measured on
# the decoded view, so when the token carries entity sequences (token longer
# than its decoded view) the slice starts too early and captures extra
# characters into the accumulator, duplicating them and breaking C2/C4.
_PREPATCH_IMPL = (
    "def implementation_peelTrailingPunct (token tailPunct : List Char) :\n"
    "    List Char × List Char × Bool := Id.run do\n"
    "  let mut token := token\n"
    "  let mut tailPunct := tailPunct\n"
    "  let mut trimmed := false\n"
    "  let decoded := decode token\n"
    "  let stripped := rstripPunct decoded\n"
    "  if decoded ≠ stripped then\n"
    "    tailPunct := token.drop stripped.length ++ tailPunct\n"
    "    token := dropRightN token (decoded.length - stripped.length)\n"
    "    trimmed := true\n"
    "  return (token, tailPunct, trimmed)"
)

# (5) PARTIAL-DOMAIN count==1: hardcode the peeled run length to 1. Correct when
# the decoded view had exactly one trailing punct; wrong for any longer run.
_PARTIAL_IMPL = (
    "def implementation_peelTrailingPunct (token tailPunct : List Char) :\n"
    "    List Char × List Char × Bool := Id.run do\n"
    "  let mut token := token\n"
    "  let mut tailPunct := tailPunct\n"
    "  let mut trimmed := false\n"
    "  let decoded := decode token\n"
    "  let stripped := rstripPunct decoded\n"
    "  if decoded ≠ stripped then\n"
    "    tailPunct := takeRightN token 1 ++ tailPunct\n"
    "    token := dropRightN token 1\n"
    "    trimmed := true\n"
    "  return (token, tailPunct, trimmed)"
)

# (added) FLAG-NEVER-SET: peels correctly but always reports `false`, attacking
# the boolean did-peel clause C3 (a Lean-carrier observable the nagini list-only
# model had no counterpart for).
_FLAG_IMPL = (
    "def implementation_peelTrailingPunct (token tailPunct : List Char) :\n"
    "    List Char × List Char × Bool := Id.run do\n"
    "  let mut token := token\n"
    "  let mut tailPunct := tailPunct\n"
    "  let mut trimmed := false\n"
    "  let decoded := decode token\n"
    "  let stripped := rstripPunct decoded\n"
    "  if decoded ≠ stripped then\n"
    "    let punctCount := decoded.length - stripped.length\n"
    "    tailPunct := takeRightN token punctCount ++ tailPunct\n"
    "    token := dropRightN token punctCount\n"
    "    trimmed := false\n"
    "  return (token, tailPunct, trimmed)"
)

# (added) DROP-INCOMING-TAIL: builds the new accumulator from the moved run only,
# forgetting to PREPEND the incoming `tailPunct`. Attacks the `++ tailPunct` half
# of C2 (and C4) through the SECOND binder; invisible whenever tailPunct is empty,
# so its witness fixes tailPunct NON-EMPTY.
_DROPTAIL_IMPL = (
    "def implementation_peelTrailingPunct (token tailPunct : List Char) :\n"
    "    List Char × List Char × Bool := Id.run do\n"
    "  let mut token := token\n"
    "  let mut tailPunct := tailPunct\n"
    "  let mut trimmed := false\n"
    "  let decoded := decode token\n"
    "  let stripped := rstripPunct decoded\n"
    "  if decoded ≠ stripped then\n"
    "    let punctCount := decoded.length - stripped.length\n"
    "    tailPunct := takeRightN token punctCount\n"
    "    token := dropRightN token punctCount\n"
    "    trimmed := true\n"
    "  return (token, tailPunct, trimmed)"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the four-clause postcondition is SPEC-TOO-STRONG. Keeps the
    # `theorem correct_peelTrailingPunct` statement byte-identical; the FROZEN
    # proof closes it unchanged (same boundaries on the same original sequence),
    # so no reproof, no helper lemma, no assumption token.
    # =====================================================================
    {
        "id": "pos-control-reshaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_IMPL),
        "rationale": (
            "a structurally reshaped but CORRECT impl (bind the original to "
            "`orig`, build the retained part before the moved tail — reverse of "
            "the frozen order — and inline the count with no `punctCount` local) "
            "slices the SAME original sequence at the SAME boundaries, so it "
            "computes the identical result and the frozen proof closes it "
            "unchanged. Defends all four clauses C1-C4; if it could not verify "
            "the postcondition would be SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, ENTITY-BEARING F2P-shaped input
    # rather than only provable in the abstract. Since `decode` is opaque the
    # ground fact is an IMPLICATION under the decoded-view hypothesis; it is
    # discharged by `decide` alongside the frozen obligation, closed verbatim.
    # =====================================================================
    {
        "id": "admiss-fshaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_OPEN, _ADMISS_HAVE),
        "rationale": (
            "the obligation is discharged at a ground entity-bearing input "
            "(token whose decoded view is strictly shorter — the exact "
            "bug-triggering domain, F2P shape) under the decoded-view hypothesis "
            "by `decide`, then the frozen obligation is closed verbatim. "
            "Verifies (else the modeled behavior would be unsatisfiable at the "
            "very input the F2P exercises, the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: no new declaration, statement byte-identical, "
            "the ground instance is a `have` inside the existing tactic body."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation
    # witness pinning the violation at one concrete input under the necessary
    # decoded-view hypothesis, checked to hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "weak-prepatch-decoded-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PREPATCH_IMPL),
        "refinement": (
            "This is the pre-patch shape verbatim: the peeled tail is taken by "
            "dropping the first `stripped.length` characters of the ORIGINAL "
            "token, an index measured on the DECODED view. On an entity-bearing "
            "token (encoded longer than decoded) the slice starts too early and "
            "leaks the extra characters into the accumulator. Its faithful real "
            "patch is exactly the buggy block the issue reports; on the reported "
            "trigger it emits the leaked extra characters in the trailing text, "
            "so the F2P assertion stays RED. Does NOT resolve — a verifying "
            "rival here would be a true verify-does-not-imply-resolve break."),
        "rationale": (
            "REJECT from clauses C2/C4: the rival's accumulator is "
            "`token.drop stripped.length ++ tailPunct`, which equals the "
            "required `takeRightN token punctCount ++ tailPunct` only when the "
            "token has no entities (encoded length == decoded length); any "
            "shorter decoded view makes it capture too many characters, so "
            "`result.1 ++ result.2.1 ≠ token ++ tailPunct`. Witness probes an "
            "entity-bearing token (decoded view supplied by hypothesis) with a "
            "non-empty incoming accumulator."),
        "witness": (
            "example (h : decode ['g', '&', '!'] = ['g', '!']) :\n"
            "    ¬ problem_spec_peelTrailingPunct ['g', '&', '!'] ['q']\n"
            "        (implementation_peelTrailingPunct ['g', '&', '!'] ['q']) := by\n"
            "  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
            "  simp only [h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-partial-domain-count1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PARTIAL_IMPL),
        "refinement": (
            "Correct on the sub-domain where the decoded view had exactly one "
            "trailing punctuation char, but hardcodes the peeled run length to "
            "1. Its faithful real patch peels a single char regardless of the "
            "real run length, so on a token whose trailing run is two or more "
            "(covered by the unchanged-inputs F2P) it leaves punctuation on the "
            "token and under-fills the accumulator, leaving those assertions "
            "RED. Does NOT resolve."),
        "rationale": (
            "REJECT from clause C1 (and C2): the precondition to the trim branch "
            "only guarantees the decoded view HAS trailing punctuation "
            "(punctCount >= 1), NOT punctCount == 1, so on a two-punct run the "
            "hardcoded boundary keeps one char too many — "
            "`result.1 ≠ dropRightN token punctCount`. Witness probes a "
            "two-trailing-punct token with an EMPTY incoming accumulator (a "
            "distinct tailPunct point from the other rivals)."),
        "witness": (
            "example (h : decode ['a', '!', '!'] = ['a', '!', '!']) :\n"
            "    ¬ problem_spec_peelTrailingPunct ['a', '!', '!'] []\n"
            "        (implementation_peelTrailingPunct ['a', '!', '!'] []) := by\n"
            "  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
            "  simp only [h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-flag-never-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FLAG_IMPL),
        "refinement": (
            "Peels the run correctly but always reports the did-peel flag as "
            "`false`. Its faithful real patch would fail to record that anything "
            "was trimmed, so the caller's loop that re-examines the token while "
            "trimming occurred would terminate early / mis-drive its state, "
            "diverging from the intended markup. Does NOT resolve."),
        "rationale": (
            "REJECT from clause C3 (result.2.2 = decide (decoded ≠ stripped)): "
            "when the decoded view HAS trailing punctuation the flag must be "
            "`true`, but the rival returns `false`. Witness probes a "
            "single-trailing-punct token (decoded view = token, supplied by "
            "hypothesis) with a non-empty incoming accumulator; this is the only "
            "rival attacking the boolean observable."),
        "witness": (
            "example (h : decode ['a', '!'] = ['a', '!']) :\n"
            "    ¬ problem_spec_peelTrailingPunct ['a', '!'] ['z']\n"
            "        (implementation_peelTrailingPunct ['a', '!'] ['z']) := by\n"
            "  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
            "  simp only [h]\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-incoming-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DROPTAIL_IMPL),
        "refinement": (
            "Builds the new accumulator from the moved run ALONE, forgetting to "
            "prepend the incoming accumulator `tailPunct`. Its faithful real "
            "patch would discard punctuation already collected from later tokens "
            "in the surrounding loop, so accumulated trailing text is lost and "
            "the final markup diverges. Does NOT resolve."),
        "rationale": (
            "REJECT from clause C2/C4 (result.2.1 = takeRightN token punctCount "
            "++ tailPunct): the rival returns `takeRightN token punctCount` with "
            "the incoming accumulator dropped, so `result.1 ++ result.2.1 ≠ "
            "token ++ tailPunct` whenever `tailPunct` is non-empty. Witness "
            "probes a NON-EMPTY incoming accumulator (the point where ignoring "
            "the second binder first diverges) — the tailPunct binder that the "
            "other rivals hold non-adversarially."),
        "witness": (
            "example (h : decode ['a', '!'] = ['a', '!']) :\n"
            "    ¬ problem_spec_peelTrailingPunct ['a', '!'] ['w', 'v']\n"
            "        (implementation_peelTrailingPunct ['a', '!'] ['w', 'v']) := by\n"
            "  unfold problem_spec_peelTrailingPunct implementation_peelTrailingPunct\n"
            "  simp only [h]\n"
            "  decide\n"
        ),
    },
]
