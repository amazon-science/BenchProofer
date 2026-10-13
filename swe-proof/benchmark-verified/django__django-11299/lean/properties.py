"""properties.py — G-PBT falsification battery for django__django-11299 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_resolveColumns`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a recursive tree carrier):

  resolveColumns (bare : Bool) (q : QTree) : ColTree
    result = expectedCol bare q

A boolean filter expression is a finite tree: a leaf names one field, an
interior node groups an ordered list of children (leaves or further nodes,
arbitrarily nested). Lowering it to column references decides, per leaf, ONE of
two column forms via a single global boolean flag supplied once at the top.
The single postcondition clause ``result = expectedCol bare q`` pins the whole
output, and ``expectedCol`` has three independent things it grounds:

  * FLAG UNIFORMITY (per-leaf form) — every leaf, at EVERY nesting depth, is
    rendered with the SAME global flag. This is the load-bearing clause: the
    documented defect is a deeply-nested leaf silently taking a different form
    from a top-level one.
  * FIELD PRESERVATION — each leaf's field name is carried through unchanged.
  * STRUCTURE PRESERVATION — the grouping shape (which leaves live under which
    node, and how many) mirrors the input tree exactly; no leaf is dropped or
    invented.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini battery's cases 1 and 2
    (write to the read-only ``head`` tree at ``Acc(...,1/2)``; append to the
    read-only ``src`` list) exploit fractional heap permissions. Lean is
    referentially transparent: inputs carry no heap permission, there is no
    read-only half to overwrite and no aliasing to abuse. Both cases have no
    expressible instance here; no substitute is fabricated.

  * PARTIAL-DOMAIN / FLAG (nagini case 3, the pre-patch A5 revert) — PORTS
    DIRECTLY as ``reject-nested-flag-not-threaded``. The rival lowers a nested
    child with a hardcoded flag rather than the threaded global one, so it
    agrees with the spec only where the forced value happens to match and
    diverges on any leaf below the first nesting level.

  * PARTIAL-DOMAIN / VALUE (nagini case 4, leaf hardcodes the flag) — PORTS
    DIRECTLY as ``reject-leaf-flag-hardcoded``: a leaf ignores ``bare`` and
    emits a fixed form, correct only on the sub-domain where that fixed value
    coincides with ``bare``.

  * SEQUENCE-LENGTH / STRUCTURE (nagini case 5, drop the group's leaves) —
    PORTS DIRECTLY as ``reject-node-child-leaves-dropped``: a node child is
    lowered to an empty grouping, dropping its whole sub-expression, so the
    output structure is shorter than the input demands wherever a node has a
    child.

  * SEQUENCE-ORDER / STRUCTURE — an ADDED attack (``reject-child-order-reversed``,
    landed by audit). The length rival above leaves ORDER unprobed, and the
    ordering of ``expectedCols`` is a real, separately-falsifiable component of
    the postcondition: a rival can preserve every leaf, every field and the flag
    at every depth and still be wrong by transposing a grouping's members. This
    is the sharpest structure-clause rival precisely because it leaves every
    other observable correct.

  * FIELD PRESERVATION — an ADDED attack with no distinct nagini sibling (the
    nagini carrier's leaf payload is only the boolean mode, so the field-name
    binder of ``expectedCol`` was untested there). Covers the ``field`` binder
    of the spec predicate so a rival that mishandled the leaf's identity would
    be noticed.

  * POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    (the per-child leaf/node case-split collapsed into a single uniform
    recursive call). Ports nagini case 6's intent (a reshaped-but-equivalent
    impl must verify, else SPEC-TOO-STRONG). The frozen proof closes it
    verbatim (no re-proof needed — verified below).

  * ADMISSIBILITY — nagini case 7 (the None base case is in-domain) ports as a
    ground instance discharged at the concrete F2P-shaped nested tree, added as
    a ``have`` alongside the frozen obligation.

  * AXIOM lane — DROPPED. The nagini AXIOM_TESTS (soundness + caller-domain
    containment of the ``leaf_modes`` / ``buildLeaf`` A-reference) belong to
    G-AX, not to this gate; omitted here by design.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input, stated directly against ``problem_spec_resolveColumns`` at
literal trees. ``QTree``/``ColTree`` are finite inductives over ``String``/
``Bool``, so each witness unfolds the spec and the impl and closes by ``simp``;
each was checked to hold of its rival and to FAIL on the frozen solution (so it
discriminates rather than asserting a tautology). ``native_decide`` is banned
and not used.

BINDER COVERAGE. The spec predicate depends on ``bare`` (the global flag),
``q``'s SHAPE (leaf vs nested node vs multi-child node), and each leaf's
``field``. The reject witnesses vary all three: the flag-threading rival is
refuted at ``bare=true`` with a doubly-nested node; the leaf-hardcode rival at
``bare=false`` with a bare leaf; the structure/length rival at ``bare=false``
with a nested node; the structure/ORDER rival at ``bare=false`` with a two-child
node carrying distinct fields; the field-preservation rival at ``bare=false``
with a named leaf. Both flag values and all three tree shapes are probed, and the
divergence points are distinct across rivals.

CLAUSE-BY-CLAUSE ATTRIBUTION. Each of the three things ``expectedCol`` grounds is
falsified by at least one rival that leaves the OTHER TWO correct, so no
rejection is over-attributed: flag uniformity (the depth rival preserves fields
and structure), the leaf flag clause (the hardcode rival preserves fields and
structure), field preservation (the field rival preserves flag and structure),
structure length (the drop rival preserves flag and fields), and structure order
(the reversal rival preserves flag, fields and length).

REFINEMENT-CLAIM DISCIPLINE. Each ``refinement`` states the route by which the
rival's faithful real patch fails the graded suite. Those routes are NOT equally
strong and the prose says which is which: the depth rival is falsified by the
F2P directly, the order rival by positional reads of a lowered grouping, whereas
the leaf-hardcode rival's route is indirect (the graded suite contains no direct
assertion of the qualified column CLASS — verified by reading it — so that case
rests on emitted condition text plus its spec-coverage value, and its refinement
note says exactly that rather than overclaiming a class assertion).
"""
from pathlib import Path

INSTANCE = "django__django-11299"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full body of the single impl region (the `mutual` block), and the full
# tactic/term body of the single proof region, so every replacement lands
# entirely inside the region it means to edit.
_I_IMPL = (
    "mutual\n"
    "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
    "  | .leaf field => buildLeaf bare field\n"
    "  | .node children => .node (resolveChildren bare children)\n"
    "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
    "  | [] => []\n"
    "  | child :: rest =>\n"
    "      let built :=\n"
    "        match child with\n"
    "        | .leaf field => buildLeaf bare field\n"
    "        | .node _      => implementation_resolveColumns bare child\n"
    "      built :: resolveChildren bare rest\n"
    "end\n"
)

_P_PROOF = (
    "  intro bare q\n"
    "  unfold problem_spec_resolveColumns\n"
    "  exact impl_eq_expected bare q\n"
)

# sanity: both anchors present exactly once in the frozen solution.
assert _BASE.count(_I_IMPL) == 1, "impl anchor drifted from Solution.lean"
assert _BASE.count(_P_PROOF) == 1, "proof anchor drifted from Solution.lean"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation of
    # the modeled behavior cannot satisfy the frozen obligation the spec is
    # SPEC-TOO-STRONG. The per-child leaf/node case-split is collapsed into a
    # single uniform recursive call (`implementation_resolveColumns bare child`
    # handles both constructors already), producing the identical value on every
    # input. The `theorem correct_resolveColumns` STATEMENT is byte-identical.
    # The proof region is ALSO carried over verbatim (the swap installs the same
    # tactic text): the frozen `impls_eq_expecteds` induction still closes the
    # reshaped recursion, because its inner `cases c` reduces the leaf child to
    # `buildLeaf bare field` (`rfl`) and the node child through
    # `impl_eq_expected` exactly as before — the collapse of the per-child match
    # does not change what the mutual lemmas must prove. No helper lemma beyond
    # the frozen pair, no axiom, no assumption token. (The soundness content is
    # in the IMPL reshape, which differs from frozen; the proof needing no edit
    # is the point, not a weakening.)
    # =====================================================================
    {
        "id": "pos-uniform-child-recursion",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_IMPL,
                "mutual\n"
                "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
                "  | .leaf field => buildLeaf bare field\n"
                "  | .node children => .node (resolveChildren bare children)\n"
                "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
                "  | [] => []\n"
                "  | child :: rest =>\n"
                "      implementation_resolveColumns bare child :: resolveChildren bare rest\n"
                "end\n",
            ),
            _P_PROOF,
            "  intro bare q\n"
            "  unfold problem_spec_resolveColumns\n"
            "  exact impl_eq_expected bare q\n",
        ),
        "rationale": "collapsing the per-child leaf/node split into one uniform "
                     "recursive call preserves the exact value flow — both "
                     "constructors were already handled by "
                     "`implementation_resolveColumns` — so `result = expectedCol "
                     "bare q` still holds and a correct reshape must verify (else "
                     "SPEC-TOO-STRONG). The frozen proof closes it VERBATIM (the "
                     "proof region is carried over unchanged): the same mutual "
                     "induction (`impl_eq_expected`/`impls_eq_expecteds`) still "
                     "applies, its inner `cases c` discharging the leaf child by "
                     "`rfl` and the node child through `impl_eq_expected` as "
                     "before. Ports nagini case 6 (reorder-descents positive "
                     "control).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the exact F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries no precondition, so
    # the honest analogue of nagini's None-base-case admission probe (case 7) is
    # to discharge the spec predicate at the concrete F2P tree — a nested group
    # holding a two-leaf sub-group plus a top-level leaf, the OR(AND(leaf,leaf),
    # leaf) shape the F2P exercises — by evaluation, inside the proof region
    # alongside the frozen obligation. If that ground instance could not be
    # discharged, the modeled behavior would be unsatisfiable at exactly the
    # input the F2P touches.
    # =====================================================================
    {
        "id": "admiss-f2p-nested-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_PROOF,
            "  have _ground : problem_spec_resolveColumns true\n"
            "      (.node [.node [.leaf \"num\", .leaf \"name\"], .leaf \"num\"])\n"
            "      (implementation_resolveColumns true\n"
            "        (.node [.node [.leaf \"num\", .leaf \"name\"], .leaf \"num\"])) := by\n"
            "    unfold problem_spec_resolveColumns\n"
            "    rfl\n"
            "  intro bare q\n"
            "  unfold problem_spec_resolveColumns\n"
            "  exact impl_eq_expected bare q\n",
        ),
        "rationale": "the obligation is discharged at the concrete F2P-shaped tree "
                     "(a nested group with a two-leaf sub-group plus a top-level "
                     "leaf, under the global flag) by evaluation, then the frozen "
                     "obligation is closed verbatim. Verifies (else the spec is "
                     "unsatisfiable at the exact input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and the "
                     "ground instance is a `have` inside the existing tactic body. "
                     "Ports nagini case 7 (in-domain base-case admission).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the graded suite,
    # so a verifying rival is a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, checked to hold of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "reject-nested-flag-not-threaded",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH DEFECT. A node child is lowered with a hardcoded flag
        # (`false`) instead of the threaded global one, so leaves below the first
        # nesting level silently take the wrong form. Correct on flat input and
        # on the sub-domain where the top flag is already `false`; diverges on
        # any nested leaf when the top flag is `true`.
        "module": _swap(
            _BASE, _I_IMPL,
            "mutual\n"
            "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
            "  | .leaf field => buildLeaf bare field\n"
            "  | .node children => .node (resolveChildren bare children)\n"
            "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
            "  | [] => []\n"
            "  | child :: rest =>\n"
            "      let built :=\n"
            "        match child with\n"
            "        | .leaf field => buildLeaf bare field\n"
            "        | .node _      => implementation_resolveColumns false child\n"
            "      built :: resolveChildren bare rest\n"
            "end\n"),
        "refinement": "this is the literal pre-fix behavior: the recursion into a "
                      "nested group omits the global flag, so it defaults to the "
                      "qualified form and leaves below the first nesting level are "
                      "rendered table-qualified even when the top asked for the bare "
                      "form. The F2P builds exactly a nested-group condition under "
                      "the bare-form global flag and asserts that the deeply-nested "
                      "leaves are rendered bare; the faithful real patch (no threading) "
                      "leaves them qualified, so the F2P assertion on the nested leaves "
                      "fails and the suite does NOT resolve.",
        "rationale": "REJECT from `result = expectedCol bare q`: the spec renders a "
                     "nested leaf with the global `bare`, but this rival forces the "
                     "qualified form inside every node, so for `bare=true` and a leaf "
                     "under a node the forms disagree. Attacks the FLAG-UNIFORMITY "
                     "clause (the load-bearing depth-uniformity guarantee). If it "
                     "verified the spec would be SPEC-TOO-WEAK on the nested "
                     "sub-domain. Ports nagini case 3 (A5-reverted descent).",
        "witness": (
            "-- Under the bare-form global flag, a leaf buried two levels deep must\n"
            "-- still be rendered bare; the rival forces the qualified form inside\n"
            "-- every node, so at bare=true and a doubly-nested leaf the forms\n"
            "-- disagree. This is exactly the depth-uniformity guarantee.\n"
            "example : ¬ problem_spec_resolveColumns true (.node [.node [.leaf \"a\"]])\n"
            "    (implementation_resolveColumns true (.node [.node [.leaf \"a\"]])) := by\n"
            "  unfold problem_spec_resolveColumns\n"
            "  simp [implementation_resolveColumns, resolveChildren, expectedCol,\n"
            "    expectedCols, buildLeaf]\n"
        ),
    },
    {
        "id": "reject-leaf-flag-hardcoded",
        "kind": "uniqueness",
        "expect": "reject",
        # A leaf ignores the global flag and emits a fixed (bare) form. Correct
        # only on the sub-domain where the top flag is already the bare form;
        # wrong on every leaf when the flag asks for the qualified form.
        "module": _swap(
            _BASE, _I_IMPL,
            "mutual\n"
            "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
            "  | .leaf field => buildLeaf true field\n"
            "  | .node children => .node (resolveChildren bare children)\n"
            "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
            "  | [] => []\n"
            "  | child :: rest =>\n"
            "      let built :=\n"
            "        match child with\n"
            "        | .leaf field => buildLeaf true field\n"
            "        | .node _      => implementation_resolveColumns bare child\n"
            "      built :: resolveChildren bare rest\n"
            "end\n"),
        "refinement": "always rendering the bare column form regardless of the global "
                      "flag breaks every ordinary lowering, which requires the "
                      "table-qualified form (with its table prefix) so a multi-table "
                      "condition is unambiguous. NOTE ON THE GRADED SUITE (measured, "
                      "not assumed): no graded test asserts the qualified column CLASS "
                      "directly — the only column-form assertions in the suite are five "
                      "`assertIsInstance(..., <bare form>)` checks, all on the bare side, "
                      "and the 103 remaining graded tests reference neither column class "
                      "and issue no multi-table/related-field lookup (0 of 113 ORM calls "
                      "traverse a relation). So the non-resolution route is NOT a direct "
                      "class assertion. It is the emitted condition text: the bare form "
                      "drops the table prefix, and the graded suite does assert generated "
                      "condition strings, so a constant-bare lowering changes them. That "
                      "route is weaker and less direct than the flag-threading rival's, "
                      "which the F2P falsifies outright; this case's primary value is "
                      "SPEC coverage of the leaf flag clause independent of nesting, and "
                      "the machine-checked witness below is what carries it.",
        "rationale": "REJECT from `result = expectedCol bare q`: the leaf clause of "
                     "`expectedCol` is the flag `bare`; emitting a constant form makes "
                     "the result differ whenever the flag holds the other value. "
                     "Attacks the FLAG clause at a leaf specifically (independent of "
                     "nesting). If it verified the spec would be SPEC-TOO-WEAK on the "
                     "opposite-flag sub-domain. Ports nagini case 4 (leaf hardcodes "
                     "the mode).",
        "witness": (
            "-- At the qualified-form flag (bare=false), a leaf must be rendered\n"
            "-- qualified; the rival emits the bare form regardless. This is the\n"
            "-- only sub-domain where the leaf clause diverges.\n"
            "example : ¬ problem_spec_resolveColumns false (.leaf \"a\")\n"
            "    (implementation_resolveColumns false (.leaf \"a\")) := by\n"
            "  unfold problem_spec_resolveColumns implementation_resolveColumns\n"
            "    expectedCol buildLeaf\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-node-child-leaves-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # A node child is lowered to an EMPTY grouping, dropping its whole
        # sub-expression. Correct on group-free input (top-level leaves only);
        # diverges (structure too short / missing leaves) whenever a node has a
        # child of its own.
        "module": _swap(
            _BASE, _I_IMPL,
            "mutual\n"
            "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
            "  | .leaf field => buildLeaf bare field\n"
            "  | .node children => .node (resolveChildren bare children)\n"
            "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
            "  | [] => []\n"
            "  | child :: rest =>\n"
            "      let built :=\n"
            "        match child with\n"
            "        | .leaf field => buildLeaf bare field\n"
            "        | .node _      => .node []\n"
            "      built :: resolveChildren bare rest\n"
            "end\n"),
        "refinement": "compiling a nested group but never carrying its lowered "
                      "children into the parent drops the whole sub-expression of the "
                      "combined condition. The F2P's nested-group condition would lose "
                      "its inner branch entirely — wrong output, missing leaves — so "
                      "the nested-leaf assertions fail and the suite does NOT resolve.",
        "rationale": "REJECT from `result = expectedCol bare q`: `expectedCol` on a "
                     "node emits `expectedCols` of ALL its children; replacing a node "
                     "child with an empty grouping yields a strictly shorter/missing "
                     "structure whenever that node has >=1 child. Attacks the "
                     "STRUCTURE-PRESERVATION clause (grouping shape / sequence "
                     "length). If it verified the spec would be SPEC-TOO-WEAK. Ports "
                     "nagini case 5 (drop the group's leaves).",
        "witness": (
            "-- A node child carrying a leaf must appear in the output with that leaf;\n"
            "-- the rival lowers it to an empty grouping, so the structures differ\n"
            "-- (a dropped leaf). Probed at the qualified-form flag and a nested tree.\n"
            "example : ¬ problem_spec_resolveColumns false (.node [.node [.leaf \"x\"]])\n"
            "    (implementation_resolveColumns false (.node [.node [.leaf \"x\"]])) := by\n"
            "  unfold problem_spec_resolveColumns\n"
            "  simp [implementation_resolveColumns, resolveChildren, expectedCol,\n"
            "    expectedCols, buildLeaf]\n"
        ),
    },
    {
        "id": "reject-child-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The existing structure rival attacks sequence LENGTH
        # (a child subtree dropped). Nothing in the battery attacked sequence
        # ORDER: this rival preserves every leaf, every field, and the global
        # flag at every depth, and emits the grouping's children in REVERSED
        # order. It is the strongest structure-clause rival, because every other
        # observable the spec grounds is left correct.
        "module": _swap(
            _BASE, _I_IMPL,
            "mutual\n"
            "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
            "  | .leaf field => buildLeaf bare field\n"
            "  | .node children => .node (resolveChildren bare children)\n"
            "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
            "  | [] => []\n"
            "  | child :: rest =>\n"
            "      resolveChildren bare rest ++ [implementation_resolveColumns bare child]\n"
            "end\n"),
        "refinement": "a lowering that emits a grouping's members in the opposite order "
                      "to the input reorders the operands of the combined condition. The "
                      "graded suite indexes the lowered grouping positionally — it pulls "
                      "members out by position and asserts which comparison and which "
                      "field each one carries — so a reversed grouping hands back the "
                      "members transposed and those positional assertions fail. Both the "
                      "F2P (which destructures a two-member sub-grouping) and several "
                      "graded tests read members by index, so this does NOT resolve.",
        "rationale": "REJECT from `result = expectedCol bare q`: `expectedCol` on a node "
                     "is `expectedCols` of its children, a front-recursive fold that "
                     "fixes the ORDER of the lowered list. Reversing it differs at any "
                     "node with two distinguishable children. Attacks the "
                     "STRUCTURE-PRESERVATION clause along the ORDER axis specifically — "
                     "flag uniformity, field preservation and sequence length are all "
                     "left CORRECT by this rival, so its rejection is attributable to "
                     "the order component alone, which no other case probes.",
        "witness": (
            "-- Two distinguishable leaves under one grouping must come out in input\n"
            "-- order; the rival emits them reversed, so the lowered lists differ even\n"
            "-- though both leaves, both fields and the flag are preserved. Probed at\n"
            "-- the qualified-form flag with two differently-named leaves.\n"
            "example : ¬ problem_spec_resolveColumns false (.node [.leaf \"a\", .leaf \"b\"])\n"
            "    (implementation_resolveColumns false (.node [.leaf \"a\", .leaf \"b\"])) := by\n"
            "  unfold problem_spec_resolveColumns\n"
            "  simp [implementation_resolveColumns, resolveChildren, expectedCol,\n"
            "    expectedCols, buildLeaf]\n"
        ),
    },
    {
        "id": "reject-leaf-field-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # A leaf discards its field name and emits a constant empty field. The
        # column form is correct (flag threaded, structure preserved), but the
        # leaf's identity is lost — wrong on every non-empty-named leaf. Covers
        # the `field` binder of `expectedCol`, which the nagini carrier (mode-only
        # leaf payload) never exercised.
        "module": _swap(
            _BASE, _I_IMPL,
            "mutual\n"
            "def implementation_resolveColumns (bare : Bool) : QTree → ColTree\n"
            "  | .leaf _ => buildLeaf bare \"\"\n"
            "  | .node children => .node (resolveChildren bare children)\n"
            "def resolveChildren (bare : Bool) : List QTree → List ColTree\n"
            "  | [] => []\n"
            "  | child :: rest =>\n"
            "      let built :=\n"
            "        match child with\n"
            "        | .leaf _ => buildLeaf bare \"\"\n"
            "        | .node _      => implementation_resolveColumns bare child\n"
            "      built :: resolveChildren bare rest\n"
            "end\n"),
        "refinement": "lowering a leaf while discarding which field it names produces "
                      "a column reference to the wrong (empty) column. The graded "
                      "suite asserts each rendered leaf references its ORIGINAL field; "
                      "a fix that loses the field name references a non-existent "
                      "column and does NOT resolve.",
        "rationale": "REJECT from `result = expectedCol bare q`: `expectedCol` "
                     "preserves each leaf's `field`; substituting a constant empty "
                     "field differs on every leaf with a non-empty name, at either "
                     "flag value. Attacks the FIELD-PRESERVATION clause and the "
                     "`field` binder of the spec predicate — a binder the nagini "
                     "carrier's boolean-only leaf payload could not vary, so this is "
                     "an added attack with no distinct nagini sibling.",
        "witness": (
            "-- The rendered leaf must name its original field; the rival emits an\n"
            "-- empty field, so at a named leaf the fields differ. Probed at the\n"
            "-- qualified-form flag with a concretely named leaf.\n"
            "example : ¬ problem_spec_resolveColumns false (.leaf \"name\")\n"
            "    (implementation_resolveColumns false (.leaf \"name\")) := by\n"
            "  unfold problem_spec_resolveColumns implementation_resolveColumns\n"
            "    expectedCol buildLeaf\n"
            "  simp\n"
        ),
    },
]
