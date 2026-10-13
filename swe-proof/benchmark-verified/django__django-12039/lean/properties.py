"""properties.py — G-PBT falsification battery for django__django-12039 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and each ``theorem correct_*`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (two structurally-identical rendering functions):

  renderColumns      (quoteName) (columns suffixes)          : String
                     result = renderColumns quoteName columns suffixes
  renderIndexColumns (quoteName) (columns suffixes opclasses): String
                     result = renderIndexColumns quoteName columns suffixes opclasses

  Each renders a comma-joined column clause. Per entry the quoted column name
  (site 2 additionally carries a mandatory per-column annotation, space-set) is
  optionally followed by a POSITIONAL hint looked up by entry index. The
  load-bearing rule the specification pins (via the deep model ``appendSuffix``):
  a hint is appended ONLY when it is present AND non-empty, and when appended it
  is set off by exactly one space; a present-but-empty hint leaves the entry
  unchanged — no token, no stray separating space. Every code point of the
  result is grounded in the inputs; there is no opaque answer key to echo.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    ``columns``, ``suffixes``, ``opclasses`` are passed by value, there is no
    read-only heap half-permission to overwrite and no aliasing to exploit. The
    nagini sibling made this class MANDATORY (both inputs were half-permission
    ``Acc(...,1/2)`` and it carried two frame-mutation rivals that wrote to a
    read-only input). Those rivals have no expressible instance here; no
    substitute is fabricated for them.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. Each postcondition is an equality against
    a term built ONLY from the inputs, ``appendSuffix``, and fixed character
    constants (a fully-unfolded computation, not an opaque oracle). The bundle
    declares no ``opaque``/``axiom`` — the rendering rule is modeled deeply
    (``appendSuffix``) and the sole external collaborator (name-quoting) is an
    arbitrary function universally quantified in both obligations — so there is
    nothing an implementation could echo without doing the work. The nagini
    sibling reached the same conclusion (its ``joined`` was a grounded helper,
    not a consumed axiom) and its ``AXIOM_TESTS`` lane is out of scope for
    G-PBT (that lane belongs to G-AX). In place of an echo attack the battery
    carries honest positive controls.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def``; a diverging implementation cannot be written at all, so
    there is no ``diverge-*`` rival to port (the nagini sibling carries none).

  * PARTIAL-DOMAIN / VALUE — the real attacks, ported directly from nagini.
    The postcondition rejects any rival that renders even one entry wrongly on
    any point of the (quoteName, columns, suffixes[, opclasses]) domain: the
    pre-fix no-separator concat, the pre-fix unconditional join (a trailing
    space on an empty hint), a wrong separator glyph, and a value-mask that
    drops the last character of a hint.

CASE-COUNT vs NAGINI. The nagini sibling modeled two structurally-identical
functions with FIVE modeled clauses each plus a mandatory frame lane; on this
carrier the two functions collapse to one equality clause apiece and the frame
lane is vacuous. So the two nagini frame-mutation rivals are DROPPED (vacuous —
see above), the nagini axiom-soundness probe is DROPPED (out of G-PBT scope),
and the four nagini value/partial-domain rivals port. Because this carrier
models BOTH functions as first-class obligations (nagini's two sites shared one
byte-identical body), each ported rival is instantiated against WHICHEVER
obligation gives it the most discriminating, F2P-faithful witness — the
no-separator and unconditional-join and wrong-separator attacks appear on both
sites so both obligations are attacked, and each site's proof is independently
broken by its own rival. Two positives (a structural reshape covering BOTH
obligations, and an in-domain admissibility control) port from the nagini
positive/admissibility controls.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``congr 1`` script is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at one concrete, ``decide``-able input; each was checked to ELABORATE
against its rival (the rival provably contradicts the spec there) and to FAIL
against the frozen solution (so it discriminates rather than asserting a
tautology). The witnesses spread over the domain: ``quoteName`` moves between the
identity and a genuine quoting map; ``columns`` between one and two entries;
``suffixes`` over ``["DESC"]``, ``[""]``, ``["ASC"]`` and a two-element list; and
the ``opclasses`` binder (unique to site 2) is exercised by every site-2
witness, so no binder of either predicate is pinned to one value across the
battery.
"""
from pathlib import Path

INSTANCE = "django__django-12039"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each the FULL body of a region, unique in Solution.lean;
# every replacement lands entirely inside the region it edits, so `same_spec`
# holds and the theorem STATEMENT is untouched). ----

# Site 1: the whole `implementation_renderColumns` def.
_IMPL1 = (
    "def implementation_renderColumns (quoteName : String → String)\n"
    "    (columns suffixes : List String) : String :=\n"
    "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
    "    let mut col := quoteName p.1\n"
    "    match suffixes[p.2]? with\n"
    "    | some suffix => if suffix ≠ \"\" then col := col ++ \" \" ++ suffix\n"
    "    | none => pure ()\n"
    "    return col))"
)
# Site 2: the whole `implementation_renderIndexColumns` def.
_IMPL2 = (
    "def implementation_renderIndexColumns (quoteName : String → String)\n"
    "    (columns suffixes opclasses : List String) : String :=\n"
    "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
    "    let mut col := quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")\n"
    "    match suffixes[p.2]? with\n"
    "    | some suffix => if suffix ≠ \"\" then col := col ++ \" \" ++ suffix\n"
    "    | none => pure ()\n"
    "    return col))"
)
# Site 1 proof body (the tactic block).
_PROOF1 = (
    "  intro quoteName columns suffixes\n"
    "  unfold problem_spec_renderColumns implementation_renderColumns renderColumns\n"
    "  congr 1"
)

assert _BASE.count(_IMPL1) == 1, "impl-renderColumns drifted"
assert _BASE.count(_IMPL2) == 1, "impl-renderIndexColumns drifted"
assert _BASE.count(_PROOF1) == 1, "proof-renderColumns drifted"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify. If a faithful correct
    # implementation cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. Each keeps every theorem STATEMENT byte-identical; none
    # introduces a helper lemma, an axiom, or an assumption token.
    # =====================================================================
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Both impls reshaped from the imperative `Id.run do`/`let mut`/early-
        # return form into a pure `match`, computing the SAME per-entry string.
        # The two proofs additionally `unfold appendSuffix` (a benign extra
        # unfold; the theorem STATEMENTS are untouched) and close with the frozen
        # `congr 1`.
        "module": _swap(
            _swap(
                _swap(
                    _swap(
                        _BASE,
                        _IMPL1,
                        "def implementation_renderColumns (quoteName : String → String)\n"
                        "    (columns suffixes : List String) : String :=\n"
                        "  String.intercalate \", \" (columns.zipIdx.map (fun p =>\n"
                        "    match suffixes[p.2]? with\n"
                        "    | some suffix => if suffix ≠ \"\" then quoteName p.1 ++ \" \" ++ suffix else quoteName p.1\n"
                        "    | none => quoteName p.1))",
                    ),
                    _IMPL2,
                    "def implementation_renderIndexColumns (quoteName : String → String)\n"
                    "    (columns suffixes opclasses : List String) : String :=\n"
                    "  String.intercalate \", \" (columns.zipIdx.map (fun p =>\n"
                    "    match suffixes[p.2]? with\n"
                    "    | some suffix => if suffix ≠ \"\" then (quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")) ++ \" \" ++ suffix else quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")\n"
                    "    | none => quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")))",
                ),
                _PROOF1,
                "  intro quoteName columns suffixes\n"
                "  unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix\n"
                "  congr 1",
            ),
            "  intro quoteName columns suffixes opclasses _\n"
            "  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns\n"
            "  congr 1",
            "  intro quoteName columns suffixes opclasses _\n"
            "  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns appendSuffix\n"
            "  congr 1",
        ),
        "rationale": "A correct reshape of BOTH obligations: the per-entry build "
                     "is rewritten from the imperative `let mut`/match into a pure "
                     "`match` with the same present-and-non-empty/space-set rule, "
                     "so it equals `renderColumns`/`renderIndexColumns` pointwise "
                     "(the branch mirrors `appendSuffix`). If it cannot verify, "
                     "both postconditions are SPEC-TOO-STRONG. Proof: the frozen "
                     "`congr 1` closes each after unfolding `appendSuffix`.",
    },
    {
        "id": "admiss-ground-empty-hint",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen renderColumns theorem is unconditional (no precondition
        # binder); the honest analogue of the nagini precondition-admission probe
        # is to discharge the spec at a ground, F2P-shaped input — a single
        # column with an EMPTY positional hint (the empty-suffix boundary the
        # issue is specifically about) — by evaluation, then close the frozen
        # obligation verbatim.
        "module": _swap(
            _BASE,
            _PROOF1,
            "  have _ground : problem_spec_renderColumns (fun s => s) [\"headline\"] [\"\"]\n"
            "      (implementation_renderColumns (fun s => s) [\"headline\"] [\"\"]) := by\n"
            "    unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix\n"
            "    decide\n" + _PROOF1,
        ),
        "rationale": "The obligation is discharged at a ground F2P-shaped input (a "
                     "single column carrying an empty positional hint — the exact "
                     "empty-hint boundary the issue reports) by `decide`, then the "
                     "frozen obligation is closed verbatim. Verifies (else the spec "
                     "is unsatisfiable at a normal input, the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, the ground instance "
                     "is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at
    # one concrete input, checked to elaborate against the rival and fail on
    # the frozen solution.
    # =====================================================================

    # ---- site 1 (renderColumns) ----
    {
        "id": "weak-no-separator-site1",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: the positional hint is concatenated directly onto the
        # quoted name with no separating space (and even an empty hint is
        # appended, a no-op). == the plain-list leg's prepatch.
        "module": _swap(
            _BASE,
            _IMPL1,
            "def implementation_renderColumns (quoteName : String → String)\n"
            "    (columns suffixes : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => col := col ++ suffix\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Concatenating the hint with no separator is the literal "
                      "pre-fix plain-list behavior: a descending column renders "
                      "the quoted name fused onto its hint with no space. The F2P "
                      "test asserts the clause CONTAINS the quoted name followed by "
                      "a space then the hint; the fused output does not contain "
                      "that substring, so it would NOT resolve.",
        "rationale": "REJECT from `result = renderColumns quoteName columns "
                     "suffixes`: for a present non-empty hint `appendSuffix` sets "
                     "it off by one space, but the rival fuses it directly. "
                     "Refuted at (identity, [\"headline\"], [\"DESC\"]) — the F2P "
                     "descending-column input.",
        "witness": (
            "example : ¬ problem_spec_renderColumns (fun s => s) [\"headline\"] [\"DESC\"]\n"
            "    (implementation_renderColumns (fun s => s) [\"headline\"] [\"DESC\"]) := by\n"
            "  unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-unconditional-join-site1",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the emptiness guard: the space + hint are appended even for an
        # empty hint, emitting a trailing space on the ascending (empty-hint)
        # entry. Correct only on the non-empty sub-domain.
        "module": _swap(
            _BASE,
            _IMPL1,
            "def implementation_renderColumns (quoteName : String → String)\n"
            "    (columns suffixes : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => col := col ++ \" \" ++ suffix\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Appending the space + hint unconditionally emits a trailing "
                      "space for an empty ascending hint — exactly the trailing-"
                      "space quirk the issue reports. A membership test expecting "
                      "the quoted name with no trailing separator on an ascending "
                      "entry would fail, so it would NOT resolve.",
        "rationale": "REJECT from `result = renderColumns quoteName columns "
                     "suffixes`: for a present but EMPTY hint `appendSuffix` leaves "
                     "the entry unchanged, but the rival appends a lone separator. "
                     "Refuted at (identity, [\"date\"], [\"\"]) — the empty-hint "
                     "boundary, distinct from every other site-1 probe.",
        "witness": (
            "example : ¬ problem_spec_renderColumns (fun s => s) [\"date\"] [\"\"]\n"
            "    (implementation_renderColumns (fun s => s) [\"date\"] [\"\"]) := by\n"
            "  unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-wrong-separator-tab-site1",
        "kind": "uniqueness",
        "expect": "reject",
        # Separator-VALUE attack: a tab instead of a single space. Correct
        # length, prefix, and hint-after-separator, but the separator glyph is
        # wrong.
        "module": _swap(
            _BASE,
            _IMPL1,
            "def implementation_renderColumns (quoteName : String → String)\n"
            "    (columns suffixes : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => if suffix ≠ \"\" then col := col ++ \"\\t\" ++ suffix\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Setting the hint off with a tab rather than a single space "
                      "renders the quoted name, a tab, then the hint. The F2P "
                      "test asserts a single space between the quoted name and the "
                      "hint; a tab is not that substring, so it would NOT resolve.",
        "rationale": "REJECT from `result = renderColumns quoteName columns "
                     "suffixes`: `appendSuffix` pins the separator to a single "
                     "space, and the rival emits a tab. Refuted at (a genuine "
                     "double-quoting map, [\"name\"], [\"ASC\"]) — moving `quoteName` "
                     "off the identity and the hint to `ASC`, a point no other "
                     "rival probes.",
        "witness": (
            "example : ¬ problem_spec_renderColumns (fun s => \"\\\"\" ++ s ++ \"\\\"\") [\"name\"] [\"ASC\"]\n"
            "    (implementation_renderColumns (fun s => \"\\\"\" ++ s ++ \"\\\"\") [\"name\"] [\"ASC\"]) := by\n"
            "  unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-last-hint-char-site1",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-mask: append the hint minus its last character. Matches on
        # prefix + separator and on all-but-last of the hint; diverges only on
        # the last character and the total length.
        "module": _swap(
            _BASE,
            _IMPL1,
            "def implementation_renderColumns (quoteName : String → String)\n"
            "    (columns suffixes : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => if suffix ≠ \"\" then col := col ++ \" \" ++ suffix.dropRight 1\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Dropping the last character of the hint renders `DESC` as "
                      "`DES`; the F2P substring `<quoted> DESC` is absent (any "
                      "multi-character hint is truncated), so it would NOT resolve. "
                      "This is a near-miss: it applies the space AND a hint, but "
                      "the wrong hint, diverging only on the final character.",
        "rationale": "REJECT from `result = renderColumns quoteName columns "
                     "suffixes`: `appendSuffix` appends the full hint, the rival "
                     "drops its last character. Refuted at (identity, [\"x\"], "
                     "[\"DESC\"]) — a distinct column and the value-truncation "
                     "boundary.",
        "witness": (
            "example : ¬ problem_spec_renderColumns (fun s => s) [\"x\"] [\"DESC\"]\n"
            "    (implementation_renderColumns (fun s => s) [\"x\"] [\"DESC\"]) := by\n"
            "  unfold problem_spec_renderColumns implementation_renderColumns renderColumns appendSuffix\n"
            "  decide\n"
        ),
    },

    # ---- site 2 (renderIndexColumns) — attack the opclass-annotated obligation
    # too, exercising the `opclasses` binder that has no site-1 counterpart ----
    {
        "id": "weak-no-separator-site2",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior on the annotated list: the hint is concatenated onto
        # the annotated column with no separating space.
        "module": _swap(
            _BASE,
            _IMPL2,
            "def implementation_renderIndexColumns (quoteName : String → String)\n"
            "    (columns suffixes opclasses : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => col := col ++ suffix\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Fusing the hint onto the annotated column with no space is "
                      "the pre-fix annotated-list behavior: a descending annotated "
                      "column renders `<quoted> <opclass>DESC` with no space "
                      "before the hint. The F2P asserts `<quoted> <opclass> DESC`, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from `result = renderIndexColumns quoteName columns "
                     "suffixes opclasses`: for a present non-empty hint the "
                     "separator is dropped. Refuted at (identity, two columns "
                     "[\"headline\", \"body\"], hints [\"DESC\", \"ASC\"], opclasses "
                     "[\"ops_a\", \"ops_b\"]) — the only witness with two entries and "
                     "a two-element `opclasses`, so it moves `columns`, `suffixes` "
                     "and the site-2-only `opclasses` binder off every other "
                     "probe's values.",
        "witness": (
            "example : ¬ problem_spec_renderIndexColumns (fun s => s) [\"headline\", \"body\"] [\"DESC\", \"ASC\"] [\"ops_a\", \"ops_b\"]\n"
            "    (implementation_renderIndexColumns (fun s => s) [\"headline\", \"body\"] [\"DESC\", \"ASC\"] [\"ops_a\", \"ops_b\"]) := by\n"
            "  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns appendSuffix\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-unconditional-join-site2",
        "kind": "uniqueness",
        "expect": "reject",
        # The site-2 regression the issue names explicitly: the hint's space is
        # appended even for an empty hint, leaving a trailing space after the
        # opclass annotation.
        "module": _swap(
            _BASE,
            _IMPL2,
            "def implementation_renderIndexColumns (quoteName : String → String)\n"
            "    (columns suffixes opclasses : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => col := col ++ \" \" ++ suffix\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Appending the space + hint unconditionally emits a trailing "
                      "space after the opclass annotation for an empty ascending "
                      "hint — the exact `(<quoted> <opclass> )` quirk the issue "
                      "reports for opclasses used without explicit ordering. The "
                      "F2P asserts `(<quoted> <opclass>)` with no trailing space, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from `result = renderIndexColumns quoteName columns "
                     "suffixes opclasses`: for a present but EMPTY hint the entry "
                     "must be left unchanged, but the rival appends a lone "
                     "separator after the annotation. Refuted at (identity, "
                     "[\"headline\"], [\"\"], [\"text_pattern_ops\"]) — the empty-hint "
                     "boundary on the annotated obligation.",
        "witness": (
            "example : ¬ problem_spec_renderIndexColumns (fun s => s) [\"headline\"] [\"\"] [\"text_pattern_ops\"]\n"
            "    (implementation_renderIndexColumns (fun s => s) [\"headline\"] [\"\"] [\"text_pattern_ops\"]) := by\n"
            "  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns appendSuffix\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-wrong-separator-tab-site2",
        "kind": "uniqueness",
        "expect": "reject",
        # Separator-VALUE attack on the annotated obligation: a tab before the
        # hint instead of a single space.
        "module": _swap(
            _BASE,
            _IMPL2,
            "def implementation_renderIndexColumns (quoteName : String → String)\n"
            "    (columns suffixes opclasses : List String) : String :=\n"
            "  String.intercalate \", \" (columns.zipIdx.map (fun p => Id.run do\n"
            "    let mut col := quoteName p.1 ++ \" \" ++ (opclasses[p.2]?.getD \"\")\n"
            "    match suffixes[p.2]? with\n"
            "    | some suffix => if suffix ≠ \"\" then col := col ++ \"\\t\" ++ suffix\n"
            "    | none => pure ()\n"
            "    return col))",
        ),
        "refinement": "Setting the hint off with a tab rather than a single space "
                      "on the annotated column renders `<quoted> <opclass>\\t<hint>`; "
                      "the F2P asserts a single space before the hint, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from `result = renderIndexColumns quoteName columns "
                     "suffixes opclasses`: `appendSuffix` pins the separator to one "
                     "space, the rival emits a tab. Refuted at (a genuine "
                     "double-quoting map, [\"name\"], [\"ASC\"], [\"gin_ops\"]) — "
                     "`quoteName` off the identity, a distinct opclass `gin_ops`, "
                     "so this rival's probe point is its own.",
        "witness": (
            "example : ¬ problem_spec_renderIndexColumns (fun s => \"\\\"\" ++ s ++ \"\\\"\") [\"name\"] [\"ASC\"] [\"gin_ops\"]\n"
            "    (implementation_renderIndexColumns (fun s => \"\\\"\" ++ s ++ \"\\\"\") [\"name\"] [\"ASC\"] [\"gin_ops\"]) := by\n"
            "  unfold problem_spec_renderIndexColumns implementation_renderIndexColumns renderIndexColumns appendSuffix\n"
            "  decide\n"
        ),
    },
]
