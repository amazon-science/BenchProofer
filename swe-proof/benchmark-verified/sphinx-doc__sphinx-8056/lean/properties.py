"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8056 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
stamps with a recorded verdict. Each SPEC case is a full ``Solution.lean``
variant built by region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
matching ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds by construction and every ``theorem correct_<name>``
STATEMENT stays byte-identical. No case introduces ``sorry`` / ``admit`` /
``native_decide`` / ``axiom`` or any new theorem/lemma. ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE — carrier narrowing vs the nagini sibling.
  The nagini battery contracts ONE procedure over a read-only sequence held at a
  half fractional permission, whose result is a sequence-of-sequences produced by
  a per-piece accumulation loop. This Lean bundle models the SAME normalization
  as a single total function over an ordered list of raw entries:

    normalizeEntries (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry
      result = raws.flatMap (expandEntry splitGrouped)

  where each raw entry is a triple ``(name, type, description)`` and
  ``expandEntry`` applies, per entry, the one rule the fix introduces:
    * with grouping on AND a non-empty name, the name is separated on commas and
      each piece, with surrounding blank characters removed, becomes an entry
      carrying the shared type and description (the EXPANSION regime — the fix);
    * otherwise a single entry is kept iff it has any content, else dropped (the
      LEGACY regime).

  So nagini's two regimes (gated by ``multiple and len(name)>0``) and its six
  postcondition clauses (count, per-piece trim, keep-at-most-one, keep-when-any-
  content, drop-when-empty, verbatim-when-kept) are all present here, but folded
  into the single grounded equality ``result = raws.flatMap (expandEntry …)``.
  Every clause is therefore an equality that a wrong per-entry expansion breaks
  at a concrete raw-entry list; the spec is fully transparent (no ``opaque``
  callee, no ``axiom``), so every reject witness is stated at a ``decide``-able
  literal input.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION rival — VACUOUS as a *permission* attack. Lean is
    referentially transparent: ``raws`` is an immutable list, there is no
    read-only half-permission to overwrite and no aliasing to exploit, so the
    nagini write-to-input rival has no expressible instance. No permission
    substitute is fabricated. Its underlying FRAME concern — that the components
    the per-entry rule carries ALONG unchanged (the shared type and description)
    must be reproduced verbatim — IS attacked directly: see ``frame-drop-desc``,
    a rival that corrupts the carried description.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the input
    (an equality against ``raws.flatMap (expandEntry splitGrouped)``, computed by
    straight-line code), so there is no opaque answer key an impl could echo
    without doing the work. The honest substitute is the reshaped/functional
    positive controls below.

  * DIVERGENCE — SHIPPED, as ``diverge-measure-free-scan``. This bundle sets no
    partial-termination semantics, so an impl carrying no decreasing measure does
    NOT discharge the obligation vacuously: the verifier still demands the
    grounded equality, and a measure-free loop cannot supply it. The class was
    initially recorded here as having no expressible instance on a total carrier,
    which was wrong — ``partial def`` writes one, and although the resulting term
    is irreducible (so no witness can evaluate it), the refutation is statable
    over a computable PROJECTION of the result. See that case for the device.

  * VALUE / PARTIAL-DOMAIN rivals — the heart of the port. nagini's count
    off-by-one, no-trim, legacy-splits-anyway, and empty-field-not-dropped rivals
    each re-express as a per-entry expansion that disagrees with ``expandEntry``,
    and each carries a refutation witness. One extra rival (``keep-guard-drops-
    type-desc``) attacks the keep-when-type/description-nonempty clause, which the
    modeled ``expandEntry`` guard also enforces. nagini's ``len(Result()) <= 1``
    clause is carried by ``legacy-duplicates-kept-entry`` (the over-count
    direction, which no value rival reaches).

AUDIT ADDITIONS (independent re-derivation of the port, machine-checked).
  The port as first landed recorded SOUND honestly but under-probed four points;
  each is now a case, and each was confirmed by building the witness against the
  rival (elaborates) and against the frozen solution (fails, with ``decide``
  proving the negation FALSE — i.e. a semantic refutation at the named input, not
  a missing name or a stuck reduction):
    * ``frame-drop-type`` — the frame clause was attacked only on the carried
      DESCRIPTION; the carried TYPE was empty in every expansion witness.
    * ``order-reversed`` — every witness used a SINGLETON raws list, at which no
      cross-entry ordering error is observable, so "in-order concatenation" was
      claimed by the docstring and tested nowhere.
    * ``expansion-trim-ascii-space-only`` — the trim clause was witnessed only at
      an ASCII space, so an impl trimming ``' '`` alone (and leaving a tab or a
      no-break space) satisfied every existing witness.
    * ``legacy-duplicates-kept-entry`` — the keep clause was probed in the
      drop/reshape directions but not the duplicate direction.
  Two positives were also strengthened. ``pos-rename-accumulator`` was replaced
  by ``pos-structural-recursion``: a renamed accumulator is alpha-equivalent to
  the frozen impl, so it exercised nothing, whereas structural recursion is not
  definitionally equal to the frozen ``forIn`` term and forces a fresh inductive
  re-proof; ``pos-foldl-accumulation`` adds a third shape. The admissibility case
  now pins the F2P behavior as concrete VALUE equations in both configurations,
  because a ``have`` of the spec predicate alone is satisfiable whenever gold
  verifies and so merely restated the obligation at a point.
  Five further wrong impls were built and confirmed REJECTED with discriminating
  witnesses (guard ignoring the non-empty-name conjunct; trimming leading blanks
  only; legacy dropping the carried type; and both order reversals), and four
  correct reshapes were confirmed to VERIFY (structural recursion, foldl, the
  functional flatMap, and split-after-trimming-the-whole-name). No wrong impl
  verified and no faithful correct impl was rejected: the spec is neither too
  weak nor too strong at every point probed.

SECOND, INDEPENDENT AUDIT (a different agent; every claim below re-derived by
build, not inherited). All fourteen cases as previously landed were confirmed to
earn their outcomes: the theorem statement is byte-identical to the frozen file
in all fourteen (and the pure / post-conditions / axioms regions are untouched);
each of the ten reject witnesses was rebuilt on both sides (rival exit 0, gold
exit 1, every gold failure ``decide`` refuting the concrete claim); and each gold
failure was additionally subjected to the claim-FLIP experiment, which inverted
BOTH exit codes in all ten (gold 1→0, rival 0→1) — so no gold-side exit code was
an artifact of the term's shape. The admissibility positive's two value equations
were confirmed LOAD-BEARING by perturbing each claimed value: both perturbed
variants FAIL, so those ``have``s pin the behavior rather than restating the
obligation. Seven NEW wrong impls and five NEW correct reshapes were built; all
seven were rejected and all five verified, so no spec hole was found.
  Three real gaps were found and are now cases:
    * ``diverge-measure-free-scan`` — the divergence lane was recorded as having
      no expressible instance on a total carrier. It has one: ``partial def``
      writes a measure-free impl that this bundle's semantics do NOT excuse, and
      although the term is irreducible the refutation is statable over a
      computable projection. This was the systematically-dropped lane.
    * ``expansion-drops-empty-pieces`` — E1 was probed only in the undercount-
      everywhere direction, so what an ABSENT segment contributes was untested;
      a rival filtering the empty pieces passed every existing witness.
    * ``legacy-drops-desc`` — both frame rivals act inside the EXPANSION branch,
      so the legacy branch's carried description was unprobed.
  Two docstring claims were corrected rather than merely noted: that the
  divergence class was vacuous here, and that every witness decides a literal
  input outright (the divergence witness reasons over a projection instead).

  * AXIOM_TESTS — dropped. The axiom lane is G-AX's job and this bundle ships no
    consumed axiom (meta.json axioms == []; comma-split and blank-trim are deeply
    modeled A-references validated by G-CONF).

DEFENDED SURFACE (the clauses every rival is built to attack, via the single
grounded equality ``result = raws.flatMap (expandEntry splitGrouped)``):
  E1  EXPANSION count — with grouping and a non-empty name, one entry per
      comma-separated piece (``(commaPieces name).length`` entries), INCLUDING
      the empty piece an absent segment yields (``expansion-drops-empty-
      pieces``); the undercount direction is ``expansion-count-off-by-one``.
  E2  EXPANSION trim — each expanded piece has its surrounding blank characters
      removed (``trim piece``), not the raw piece.
  E2b EXPANSION trim SET — the removed characters are the whole modeled blank
      set (``isBlank``), not merely the ASCII space; a rival that removes only
      ``' '`` leaves a leading tab or no-break space in place.
  E3  EXPANSION frame — each expanded entry carries the shared type AND the
      shared description verbatim (BOTH carried-along components).
  L1  LEGACY verbatim/keep — without grouping, a content-bearing entry is kept
      as a single verbatim entry: the name is not split (``legacy-splits-
      anyway``) AND the carried description is reproduced (``legacy-drops-
      desc``), the legacy-side half of the frame obligation.
  T1  TERMINATION — the result must be a computed list, so an impl whose loop
      carries no decreasing measure does not discharge the obligation
      (``diverge-measure-free-scan``). This bundle sets no partial-termination
      semantics, which is what makes the class shippable rather than vacuous.
  L2  LEGACY keep-when-any-content — an entry with an empty name but a non-empty
      type OR description is still kept.
  L3  LEGACY drop-when-empty — a wholly empty entry contributes nothing.
  L4  LEGACY keep-at-most-one — a kept entry is kept ONCE, never duplicated.
  O1  ORDER — the result is the IN-ORDER concatenation: expansions of earlier
      raw entries precede expansions of later ones, and within one expansion the
      pieces keep their comma order. Needs a raws list of length > 1 to pin.

BINDER COVERAGE. ``expandEntry`` has input binders ``splitGrouped``, and each
entry's ``name`` / ``type`` / ``description``; ``normalizeEntries`` additionally
binds the raws LIST (its length and the order of its elements). The reject
witnesses vary all of these:
  * ``splitGrouped`` — true (count, no-trim, trim-set, frame-desc, frame-type)
    and false (legacy, no-drop, keep-guard, duplicate, order);
  * ``name`` — comma-bearing ['a',',','b'], DOUBLY-comma-bearing (an absent
    segment) ['a',',',',','b'], blank-padded [' ','a'], padded with a
    NON-ASCII-space blank ['\\u00A0','a'], singleton ['a'], and empty []
    (no-drop, keep-guard);
  * ``type`` — non-empty ['x'] in the LEGACY regime (keep-guard) and in the
    EXPANSION regime (frame-type) vs empty elsewhere;
  * ``description`` — non-empty [['d']] in the EXPANSION regime (frame-desc) and
    in the LEGACY regime (legacy-drops-desc) vs empty elsewhere;
  * the raws LIST — length 1 in most witnesses and length 2 in ``order-
    reversed``, which is the only point at which a cross-entry ordering error is
    observable at all.
  So no binder is held fixed across every witness: a rival mishandling only
  ``type`` / ``description`` / cross-entry order / the blank set is refuted by
  frame-type / frame-desc / order-reversed / trim-set respectively.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script is a real induction tuned to the
frozen form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate at a concrete input; each was checked to HOLD of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).
No witness binds a hypothesis (all inputs are literal), so none can be
inconsistent — and each gold-side failure was read, not just counted: every one
is ``decide`` proving the NEGATION false, which is gold satisfying the spec at
that exact input. None fails for a syntactic reason (an unknown identifier, a
type error, an unfolding failure, or a stuck reduction), which is what would make
a witness a non-discriminator the gate cannot detect. Every witness names the
concrete input it discriminates at, and none would elaborate against the frozen
solution.

  All rivals but one are fully transparent, so their witnesses ``decide`` the
  spec predicate at a literal input outright. The one exception is
  ``diverge-measure-free-scan``, whose rival is irreducible by construction (that
  IS its defect): its witness cannot evaluate the result, so it derives the
  refutation from a computable PROJECTION (``List.head?``) of the claimed
  equality. That witness was additionally checked by the claim-FLIP experiment —
  asserting the projection AGREES with the spec inverts both exit codes (gold
  elaborates, rival fails by ``decide``), so the gold-side exit code tracks what
  is claimed rather than the shape of the term.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8056"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Full impl-region body of the modeled function.
_IMPL_GOLD = (
    "def implementation_normalizeEntries\n"
    "    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry := Id.run do\n"
    "  let mut fields : List FieldEntry := []\n"
    "  for f in raws do\n"
    "    let (name, typ, desc) := f\n"
    "    if splitGrouped && (name != []) then\n"
    "      for piece in commaPieces name do\n"
    "        fields := fields ++ [(trim piece, typ, desc)]\n"
    "    else if (name != []) || (typ != []) || (desc != []) then\n"
    "      fields := fields ++ [(name, typ, desc)]\n"
    "  return fields\n"
)

# Full proof-region body of the obligation (unique in the file).
_PROOF_GOLD = _BASE[_BASE.index("-- proof-start"):
                    _BASE.index("-- proof-end") + len("-- proof-end")]

# Sub-anchors, each unique inside the impl region and lying ENTIRELY inside it.
_A_PIECES_LOOP = "      for piece in commaPieces name do\n"
_A_APPEND_TRIMMED = "        fields := fields ++ [(trim piece, typ, desc)]\n"
_A_APPEND_LEGACY = "      fields := fields ++ [(name, typ, desc)]\n"
_A_KEEP_GUARD = "    else if (name != []) || (typ != []) || (desc != []) then\n"
_A_INTRO = "  intro splitGrouped raws\n"

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted"
assert _BASE.count(_PROOF_GOLD) == 1, "proof region drifted"
for _a in (_A_PIECES_LOOP, _A_APPEND_TRIMMED, _A_APPEND_LEGACY, _A_KEEP_GUARD,
           _A_INTRO):
    assert _BASE.count(_a) == 1, f"sub-anchor drifted: {_a!r}"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Each keeps the
    # ``theorem correct_<name>`` STATEMENT byte-identical; no new lemma, axiom,
    # or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-structural-recursion",
        "kind": "soundness",
        "expect": "verify",
        # Genuinely different CONTROL STRUCTURE: replace the imperative
        # accumulation loop with direct structural recursion over `raws`,
        # cons-ing each entry's expansion onto the recursive result. This is NOT
        # definitionally equal to the frozen `Id.run do ... forIn` term — the
        # frozen tactic script (a hand-rolled `forIn` induction) does not apply
        # at all, so the case needs its OWN inductive re-proof, which is exactly
        # what makes it a real soundness control rather than a rename. (A mere
        # accumulator RENAME was the previous occupant of this slot: it is
        # alpha-equivalent to the frozen impl, so it tested nothing but the
        # verifier's tolerance of a bound name.)
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "def implementation_normalizeEntries\n"
                "    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry :=\n"
                "  match raws with\n"
                "  | [] => []\n"
                "  | f :: rest =>\n"
                "    expandEntry splitGrouped f "
                "++ implementation_normalizeEntries splitGrouped rest\n",
            ),
            _PROOF_GOLD,
            "-- proof-start\n"
            "theorem correct_normalizeEntries :\n"
            "    ∀ (splitGrouped : Bool) (raws : List FieldEntry),\n"
            "      problem_spec_normalizeEntries splitGrouped raws\n"
            "        (implementation_normalizeEntries splitGrouped raws) := by\n"
            "  intro splitGrouped raws\n"
            "  unfold problem_spec_normalizeEntries\n"
            "  induction raws with\n"
            "  | nil => rfl\n"
            "  | cons f rest ih =>\n"
            "    rw [implementation_normalizeEntries, List.flatMap_cons, ih]\n"
            "-- proof-end",
        ),
        "rationale": "a correct impl with a genuinely different CONTROL "
                     "STRUCTURE — structural recursion over `raws` in place of "
                     "the imperative `forIn` accumulation — computes the same "
                     "in-order concatenation, so the grounded equality `result = "
                     "raws.flatMap (expandEntry splitGrouped)` still holds; must "
                     "verify, else SPEC-TOO-STRONG. It is NOT definitionally "
                     "equal to the frozen term (the frozen `forIn` induction does "
                     "not apply), so the obligation is genuinely RE-PROVEN here "
                     "by a fresh induction on `raws`, not restated. No new "
                     "declaration or assumption — only the impl and the tactic "
                     "body change, and the theorem STATEMENT is byte-identical.",
    },
    {
        "id": "pos-foldl-accumulation",
        "kind": "soundness",
        "expect": "verify",
        # A THIRD shape: left-fold accumulation. Unlike the flatMap positive this
        # is NOT definitionally equal to the spec's `flatMap` (foldl threads an
        # accumulator), so it needs the generalized `acc ++ ...` lemma to close —
        # the same proof burden a real alternative solution would carry.
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "def implementation_normalizeEntries\n"
                "    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry :=\n"
                "  raws.foldl (fun acc f => acc ++ expandEntry splitGrouped f) []\n",
            ),
            _PROOF_GOLD,
            "-- proof-start\n"
            "theorem correct_normalizeEntries :\n"
            "    ∀ (splitGrouped : Bool) (raws : List FieldEntry),\n"
            "      problem_spec_normalizeEntries splitGrouped raws\n"
            "        (implementation_normalizeEntries splitGrouped raws) := by\n"
            "  intro splitGrouped raws\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  have key : ∀ (rs : List FieldEntry) (acc : List FieldEntry),\n"
            "      rs.foldl (fun acc f => acc ++ expandEntry splitGrouped f) acc\n"
            "        = acc ++ rs.flatMap (expandEntry splitGrouped) := by\n"
            "    intro rs\n"
            "    induction rs with\n"
            "    | nil => intro acc; simp\n"
            "    | cons f rest ih =>\n"
            "      intro acc\n"
            "      simp [List.foldl_cons, List.flatMap_cons, ih, List.append_assoc]\n"
            "  simpa using key raws []\n"
            "-- proof-end",
        ),
        "rationale": "a correct impl in a third shape — a left fold threading an "
                     "accumulator, which is neither the frozen `forIn` loop nor "
                     "definitionally the spec's `flatMap` — satisfies the grounded "
                     "equality, and closing it requires the generalized "
                     "`foldl … acc = acc ++ flatMap` lemma proven inline by "
                     "induction. Must verify, else SPEC-TOO-STRONG. Together with "
                     "the structural-recursion and flatMap positives this shows "
                     "the spec admits every faithful shape, not just terms "
                     "definitionally equal to the frozen one. No new top-level "
                     "declaration or assumption.",
    },
    {
        "id": "pos-functional-flatMap",
        "kind": "soundness",
        "expect": "verify",
        # Genuinely different SHAPE: replace the imperative accumulation loop with
        # the pure functional `raws.flatMap (expandEntry splitGrouped)`. This is
        # observationally equal to gold by definition of the spec, so the proof
        # collapses to `rfl` — a stronger soundness control than a mere rename.
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "def implementation_normalizeEntries\n"
                "    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry :=\n"
                "  raws.flatMap (expandEntry splitGrouped)\n",
            ),
            _PROOF_GOLD,
            "-- proof-start\n"
            "theorem correct_normalizeEntries :\n"
            "    ∀ (splitGrouped : Bool) (raws : List FieldEntry),\n"
            "      problem_spec_normalizeEntries splitGrouped raws\n"
            "        (implementation_normalizeEntries splitGrouped raws) := by\n"
            "  intro splitGrouped raws\n"
            "  rfl\n"
            "-- proof-end",
        ),
        "rationale": "a structurally different but correct impl (the pure "
                     "functional flatMap of the per-entry expansion, replacing "
                     "the imperative accumulation loop) satisfies the grounded "
                     "equality definitionally, so `rfl` closes the byte-identical "
                     "obligation; must verify, else SPEC-TOO-STRONG. No new "
                     "declaration or assumption — only the impl and the tactic "
                     "body change.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input. The frozen
    # theorem carries NO precondition hypothesis (the behavior is total,
    # `∀ splitGrouped raws` unguarded), so nagini's precondition-admission probe
    # has no binder to attack; the honest analogue discharges the spec predicate
    # at the exact F2P grouped comma-name entry inside the proof region, before
    # the frozen obligation is closed verbatim.
    # =====================================================================
    {
        "id": "admiss-F2P-grouped-comma-name",
        "kind": "admissibility",
        "expect": "verify",
        # Insert two ground instances right after `intro`, then run the frozen
        # proof. The FIRST pins the concrete VALUE at the F2P input (both halves:
        # grouped expands to the two trimmed entries, non-grouped keeps the comma
        # name whole) rather than only asserting the spec predicate holds there —
        # a `have ... := by decide` of the spec predicate alone is satisfiable by
        # construction whenever gold verifies, so it would restate the frozen
        # obligation at a point instead of exhibiting the F2P behavior.
        "module": _swap(
            _BASE, _A_INTRO,
            "  intro splitGrouped raws\n"
            "  -- the F2P grouped comma name expands into the two TRIMMED pieces,\n"
            "  -- each carrying the shared type and description\n"
            "  have _expansion : implementation_normalizeEntries true "
            "[(['x','1',',',' ','x','2'], [], [])]\n"
            "      = [(['x','1'], [], []), (['x','2'], [], [])] := by decide\n"
            "  -- and the non-grouped configuration keeps it as ONE verbatim entry\n"
            "  have _legacy : implementation_normalizeEntries false "
            "[(['x','1',',',' ','x','2'], [], [])]\n"
            "      = [(['x','1',',',' ','x','2'], [], [])] := by decide\n"
            "  have _ground : problem_spec_normalizeEntries true "
            "[(['x','1',',',' ','x','2'], [], [])]\n"
            "      (implementation_normalizeEntries true "
            "[(['x','1',',',' ','x','2'], [], [])]) := by\n"
            "    unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "    decide\n",
        ),
        "rationale": "the modeled behavior is exhibited CONCRETELY at the exact "
                     "F2P grouped comma-separated name entry `x1, x2`: `decide` "
                     "closes the ground VALUE equations for both configurations — "
                     "with grouping it expands into exactly the two trimmed "
                     "entries `x1` and `x2` sharing the type and description, "
                     "without grouping it stays ONE verbatim entry `x1, x2` — and "
                     "the spec predicate is then discharged there, before the "
                     "frozen obligation is closed verbatim. Verifies, else the "
                     "modeled behavior is unsatisfiable at the normal input (the "
                     "analogue of PRECOND-TOO-STRONG). The two value equations are "
                     "what make this more than a restatement of the obligation: "
                     "they would FAIL for an impl that satisfied the spec "
                     "vacuously or expanded to anything else. Nothing is assumed: "
                     "the theorem STATEMENT is byte-identical, the ground "
                     "instances are `have`s inside the existing tactic body, no "
                     "new declaration or axiom or `sorry`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break, and (b) a refutation witness
    # pinning the violation at one concrete input.
    # =====================================================================

    # ---- E1: EXPANSION count (one entry per comma piece) ----
    {
        "id": "expansion-count-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the LAST comma piece in the expansion loop: emits one fewer entry
        # than there are pieces. Correct only on names with no comma (where there
        # is a single piece and dropLast would drop it too — actually diverges
        # there as well); wrong on every grouped multi-piece name.
        "module": _swap(
            _BASE, _A_PIECES_LOOP,
            "      for piece in (commaPieces name).dropLast do\n",
        ),
        "refinement": "a faithful real patch whose expansion loop dropped the "
                      "last comma piece would emit one fewer entry than the name "
                      "has comma-separated pieces. For the F2P grouped name "
                      "`x1, x2` it emits ONE entry (x1) where the test asserts TWO "
                      "(x1 AND x2), so the added multi-parameter behavior is lost "
                      "=> does NOT resolve.",
        "rationale": "REJECT from clause E1 (count): the expansion produces "
                     "`(commaPieces name).length - 1` entries, one fewer than the "
                     "grounded `expandEntry` requires, so the equality fails on "
                     "any grouped name with at least one comma.",
        "witness": (
            "-- Refuted on a grouped comma-bearing name: the expansion must emit\n"
            "-- one entry per comma piece, so dropping the last piece undercounts\n"
            "-- (clause E1).\n"
            "example : ¬ problem_spec_normalizeEntries true [(['a',',','b'], [], [])]\n"
            "    (implementation_normalizeEntries true [(['a',',','b'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- E2: EXPANSION trim (each piece has surrounding blanks removed) ----
    {
        "id": "expansion-no-trim",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit each piece UNTRIMMED. The count E1 is still right; E2 fails on any
        # piece with surrounding blank characters.
        "module": _swap(
            _BASE, _A_APPEND_TRIMMED,
            "        fields := fields ++ [(piece, typ, desc)]\n",
        ),
        "refinement": "this IS the expansion with the surrounding-blank removal "
                      "forgotten. For the F2P grouped name `x1, x2` the pieces are "
                      "['x1',' x2']; without trimming the second entry's name is "
                      "' x2' (a leading blank) not 'x2', so the rendered "
                      "per-parameter output mismatches => does NOT resolve.",
        "rationale": "REJECT from clause E2 (trim): the impl stores the raw piece "
                     "where `expandEntry` stores `trim piece`; on a piece with a "
                     "surrounding blank those differ, so the equality fails.",
        "witness": (
            "-- Refuted on a grouped name whose sole piece has a leading blank:\n"
            "-- the expansion must trim it, so storing the raw piece violates\n"
            "-- clause E2.\n"
            "example : ¬ problem_spec_normalizeEntries true [([' ','a'], [], [])]\n"
            "    (implementation_normalizeEntries true [([' ','a'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- E3: EXPANSION frame (carried type + description reproduced) ----
    {
        "id": "frame-drop-desc",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the carried-along FRAME component: in the expansion branch pair
        # each trimmed piece with an EMPTY description instead of the shared one.
        # This is the referentially-transparent analogue of the nagini FRAME-
        # MUTATION rival — a rival that corrupts the component the rule carries
        # along unchanged. Without clause E3 the spec would let it verify.
        "module": _swap(
            _BASE, _A_APPEND_TRIMMED,
            "        fields := fields ++ [(trim piece, typ, [])]\n",
        ),
        "refinement": "dropping the shared description from the expanded entries "
                      "corrupts a component the rule carries along untouched: each "
                      "expanded parameter would lose its description text, so the "
                      "F2P per-parameter output (which repeats the shared "
                      "description on every split entry) mismatches => does NOT "
                      "resolve. This regresses the frame the surrounding behavior "
                      "guarantees.",
        "rationale": "REJECT from clause E3 (frame): each expanded entry must "
                     "carry the shared description verbatim, but the rival "
                     "substitutes `[]`; on a non-empty description they differ, so "
                     "the equality fails. This is the clause pinning the carried-"
                     "along component a permission-mutation rival would abuse on "
                     "nagini.",
        "witness": (
            "-- Refuted on a grouped entry with a non-empty description: each\n"
            "-- expanded entry must carry the shared description, so emptying it\n"
            "-- violates clause E3.\n"
            "example : ¬ problem_spec_normalizeEntries true [(['a'], [], [['d']])]\n"
            "    (implementation_normalizeEntries true [(['a'], [], [['d']])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- E2b: EXPANSION trim SET (the whole blank set, not just ' ') ----
    {
        "id": "expansion-trim-ascii-space-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Trim ONLY the ASCII space character instead of the modeled blank set.
        # The `expansion-no-trim` rival above is refuted at a leading ASCII space,
        # so it leaves this narrower error unattacked: an impl that strips `' '`
        # and nothing else passes that witness's input while still mishandling a
        # tab or a no-break space. Two witnesses pin both, one ASCII-adjacent
        # (tab) and one non-ASCII (U+00A0).
        "module": _swap(
            _BASE, _A_APPEND_TRIMMED,
            "        fields := fields ++ "
            "[(((piece.dropWhile (fun c => c == ' ')).reverse.dropWhile "
            "(fun c => c == ' ')).reverse, typ, desc)]\n",
        ),
        "refinement": "a faithful real patch that removed only the ASCII space "
                      "from each separated piece would leave any OTHER surrounding "
                      "blank character in place: a name piece introduced with a "
                      "tab after the comma keeps its leading tab, so the rendered "
                      "per-piece output carries a stray blank and mismatches the "
                      "asserted text => does NOT resolve. It is the plausible "
                      "near-miss of the trimming step, agreeing with the correct "
                      "behavior on every space-padded piece and diverging only on "
                      "the rest of the blank set.",
        "rationale": "REJECT from clause E2b (trim SET): `expandEntry` stores "
                     "`trim piece`, which removes every character the modeled "
                     "`isBlank` set contains, but the rival removes only `' '`; on "
                     "a piece padded with any other blank the two differ, so the "
                     "equality fails. Distinct from `expansion-no-trim`, which is "
                     "refuted at an ASCII space this rival handles correctly — "
                     "without this case the SIZE of the trimmed set is unprobed.",
        "witness": (
            "-- Refuted twice on grouped names padded with a blank that is NOT the\n"
            "-- ASCII space: trimming must remove the whole modeled blank set, so\n"
            "-- an ASCII-space-only trim leaves the pad in place (clause E2b).\n"
            "-- (a) a tab, the ASCII-adjacent case.\n"
            "example : ¬ problem_spec_normalizeEntries true [(['\\t','a'], [], [])]\n"
            "    (implementation_normalizeEntries true [(['\\t','a'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
            "-- (b) a no-break space, the non-ASCII case.\n"
            "example : ¬ problem_spec_normalizeEntries true "
            "[(['\\u00A0','a'], [], [])]\n"
            "    (implementation_normalizeEntries true "
            "[(['\\u00A0','a'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- E3: EXPANSION frame, the TYPE half (desc is covered above) ----
    {
        "id": "frame-drop-type",
        "kind": "uniqueness",
        "expect": "reject",
        # The OTHER carried-along component. `frame-drop-desc` empties the shared
        # description; this empties the shared TYPE, which that rival leaves
        # untouched (and which every other expansion witness holds empty, so the
        # type is unprobed in the EXPANSION regime without this case).
        "module": _swap(
            _BASE, _A_APPEND_TRIMMED,
            "        fields := fields ++ [(trim piece, [], desc)]\n",
        ),
        "refinement": "dropping the shared type from the expanded entries "
                      "corrupts the second component the rule carries along "
                      "untouched: each expanded item would lose its type "
                      "annotation, so the rendered per-item type output is empty "
                      "where the asserted output repeats the shared type on every "
                      "separated entry => does NOT resolve.",
        "rationale": "REJECT from clause E3 (frame, type half): each expanded "
                     "entry must carry the shared TYPE verbatim, but the rival "
                     "substitutes `[]`; on a non-empty type they differ, so the "
                     "equality fails. `frame-drop-desc` cannot catch this — it "
                     "leaves the type alone — and this witness is the only "
                     "EXPANSION-regime point where `type` is non-empty.",
        "witness": (
            "-- Refuted on a grouped entry with a non-empty type: each expanded\n"
            "-- entry must carry the shared type, so emptying it violates E3.\n"
            "example : ¬ problem_spec_normalizeEntries true [(['a'], ['x'], [])]\n"
            "    (implementation_normalizeEntries true [(['a'], ['x'], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- O1: ORDER (in-order concatenation across raw entries) ----
    {
        "id": "order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # PREPEND each emission instead of appending, in BOTH branches, so the
        # result is the reverse-order concatenation. Every other case in this
        # battery is witnessed at a SINGLETON raws list, where no ordering error
        # is observable at all — this is the only case that varies the list
        # binder, and without it "in-order" is asserted by the docstring and
        # tested nowhere.
        "module": _swap(
            _swap(_BASE, _A_APPEND_TRIMMED,
                  "        fields := [(trim piece, typ, desc)] ++ fields\n"),
            _A_APPEND_LEGACY,
            "      fields := [(name, typ, desc)] ++ fields\n",
        ),
        "refinement": "a faithful real patch that prepended each produced entry "
                      "rather than appending it would emit the documented items in "
                      "REVERSE order: the rendered block would list the last item "
                      "first, so the asserted output — which is order-sensitive "
                      "line-for-line — mismatches on any block with two or more "
                      "items => does NOT resolve.",
        "rationale": "REJECT from clause O1 (order): the spec is the IN-ORDER "
                     "concatenation `raws.flatMap (expandEntry splitGrouped)`, but "
                     "the rival prepends, producing the reverse; on a two-entry "
                     "raws list the two lists differ, so the equality fails. This "
                     "is the only witness whose raws list has length > 1, hence "
                     "the only one at which an ordering error is observable.",
        "witness": (
            "-- Refuted on a TWO-entry raws list: the result must concatenate the\n"
            "-- entries' expansions in order, so prepending reverses them and\n"
            "-- violates clause O1. (A singleton list cannot see this.)\n"
            "example : ¬ problem_spec_normalizeEntries false "
            "[(['a'], [], []), (['b'], [], [])]\n"
            "    (implementation_normalizeEntries false "
            "[(['a'], [], []), (['b'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- L1: LEGACY verbatim (name kept whole, not split) ----
    {
        "id": "legacy-splits-anyway",
        "kind": "uniqueness",
        "expect": "reject",
        # In the LEGACY (non-grouped) branch, keep only the FIRST comma piece of
        # the name instead of the whole verbatim name. Keep count is still one;
        # the kept name is wrong on any name containing a comma.
        "module": _swap(
            _BASE, _A_APPEND_LEGACY,
            "      fields := fields ++ [((commaPieces name).headD [], typ, desc)]\n",
        ),
        "refinement": "a faithful real patch that split the name even without "
                      "grouping (keeping the first comma piece) would, under the "
                      "non-grouped F2P configuration, keep the parameter field as "
                      "`x1` instead of the verbatim `x1, x2` the test asserts => "
                      "does NOT resolve (the non-grouped half of the F2P).",
        "rationale": "REJECT from clause L1 (legacy verbatim): the non-grouped "
                     "branch must keep the name whole, but the rival keeps only "
                     "the first comma piece; on any name with a comma the kept "
                     "entry differs from `expandEntry`'s single verbatim entry, so "
                     "the equality fails.",
        "witness": (
            "-- Refuted on a non-grouped comma-bearing name: it must be kept\n"
            "-- verbatim as one entry, so keeping only the first piece violates\n"
            "-- clause L1.\n"
            "example : ¬ problem_spec_normalizeEntries false [(['a',',','b'], [], [])]\n"
            "    (implementation_normalizeEntries false [(['a',',','b'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- L2: LEGACY keep-when-any-content (type/description alone keeps it) ----
    {
        "id": "keep-guard-drops-type-desc",
        "kind": "uniqueness",
        "expect": "reject",
        # Narrow the legacy keep-guard to the NAME alone: an entry with an empty
        # name but a non-empty type or description is now dropped. Violates L2.
        "module": _swap(
            _BASE, _A_KEEP_GUARD,
            "    else if (name != []) then\n",
        ),
        "refinement": "a faithful real patch that kept an entry only when its "
                      "NAME is non-empty would drop content-bearing entries whose "
                      "name is empty but which carry a type or a description "
                      "(e.g. an unnamed but typed parameter), erasing them from "
                      "the rendered output where the surrounding behavior keeps "
                      "them => does NOT resolve.",
        "rationale": "REJECT from clause L2 (keep-when-any-content): `expandEntry` "
                     "keeps an entry when name OR type OR description is non-empty, "
                     "but the rival keeps it only when the name is; on an empty-"
                     "name entry with a non-empty type the rival emits nothing "
                     "where the spec keeps one entry, so the equality fails. "
                     "Varies the `type` binder (held empty by every other "
                     "witness).",
        "witness": (
            "-- Refuted on an empty-name entry carrying a non-empty type: it must\n"
            "-- still be kept, so a name-only keep-guard drops it (clause L2).\n"
            "example : ¬ problem_spec_normalizeEntries false [([], ['x'], [])]\n"
            "    (implementation_normalizeEntries false [([], ['x'], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- L3: LEGACY drop-when-empty (a wholly empty entry contributes nothing) ----
    {
        "id": "empty-entry-not-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Replace the legacy keep-guard with an unconditional `else`: a wholly
        # empty entry is now emitted as one (empty) entry. Violates L3.
        "module": _swap(
            _BASE, _A_KEEP_GUARD,
            "    else\n",
        ),
        "refinement": "a faithful real patch that dropped the keep-guard and "
                      "always emitted an entry would produce a spurious empty "
                      "entry for a wholly empty raw entry; the downstream "
                      "formatter renders one line per entry, so an extra blank "
                      "line appears where the gold emits none, diverging from the "
                      "asserted output => does NOT resolve.",
        "rationale": "REJECT from clause L3 (drop-when-empty): `expandEntry` maps "
                     "a wholly empty entry to the empty list, but the rival always "
                     "appends one entry; on the empty entry the rival emits one "
                     "where the spec emits zero, so the equality fails.",
        "witness": (
            "-- Refuted on a wholly empty entry: it must contribute nothing, so\n"
            "-- always appending emits one entry where zero is required "
            "(clause L3).\n"
            "example : ¬ problem_spec_normalizeEntries false [([], [], [])]\n"
            "    (implementation_normalizeEntries false [([], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- E1b: EXPANSION count, the EMPTY-PIECE half ----
    {
        "id": "expansion-drops-empty-pieces",
        "kind": "uniqueness",
        "expect": "reject",
        # Filter the empty pieces out of the expansion. `expansion-count-off-by-
        # one` undercounts at EVERY grouped multi-piece name, so it is refuted at
        # a name whose pieces are all non-empty and never reaches the question of
        # what an ABSENT segment contributes. `commaPieces` is delimiter-based and
        # so yields an empty piece for an absent segment; the expansion keeps it
        # (trimmed to the empty name) rather than discarding it. This rival agrees
        # with the correct behavior on every name whose segments are all non-empty
        # — including every existing witness's input — and diverges only where a
        # segment is absent, which is the plausible "skip the blanks" near-miss.
        "module": _swap(
            _BASE, _A_PIECES_LOOP,
            "      for piece in (commaPieces name).filter (fun p => p != []) do\n",
        ),
        "refinement": "a faithful real patch that discarded the empty separated "
                      "pieces would, on a name written with an absent segment "
                      "(a doubled separator, or a trailing one), emit fewer "
                      "entries than the name has segments: the rendered output "
                      "loses the placeholder item the surrounding behavior emits "
                      "for that segment, so the asserted per-item text mismatches "
                      "=> does NOT resolve. It agrees with the correct behavior "
                      "on every all-segments-present name, which is what makes it "
                      "a near-miss rather than a coarse error.",
        "rationale": "REJECT from clause E1 (count), the EMPTY-PIECE half: "
                     "`expandEntry` maps EVERY piece `commaPieces` yields to an "
                     "entry, including the empty piece an absent segment "
                     "produces, but the rival drops those; on a name with a "
                     "doubled separator the lists differ in length, so the "
                     "equality fails. `expansion-count-off-by-one` cannot catch "
                     "this: it undercounts at every grouped name and is refuted "
                     "at a name whose pieces are all non-empty, so the treatment "
                     "of an absent segment is unprobed without this case.",
        "witness": (
            "-- Refuted on a grouped name with an ABSENT middle segment (a\n"
            "-- doubled separator): the expansion must emit one entry per piece\n"
            "-- INCLUDING the empty one, so filtering it out undercounts (E1).\n"
            "example : ¬ problem_spec_normalizeEntries true "
            "[(['a',',',',','b'], [], [])]\n"
            "    (implementation_normalizeEntries true "
            "[(['a',',',',','b'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- E3/L-frame: the LEGACY branch's carried DESCRIPTION ----
    {
        "id": "legacy-drops-desc",
        "kind": "uniqueness",
        "expect": "reject",
        # The frame clause in the LEGACY regime. `frame-drop-desc` and
        # `frame-drop-type` both corrupt a carried component inside the EXPANSION
        # branch; the legacy branch's reproduce-verbatim obligation is attacked
        # only on the NAME (legacy-splits-anyway) and on presence/count
        # (keep-guard, empty-entry, duplicates). So a rival that keeps the entry,
        # with the right name and the right count, but empties the description it
        # was carrying passes every existing legacy witness.
        "module": _swap(
            _BASE, _A_APPEND_LEGACY,
            "      fields := fields ++ [(name, typ, [])]\n",
        ),
        "refinement": "a faithful real patch that emptied the description when "
                      "keeping a non-grouped entry would strip the description "
                      "text from every item in the unchanged non-grouped "
                      "configuration: the rendered block keeps the item but "
                      "loses its prose, so the asserted output mismatches => "
                      "does NOT resolve. It regresses the configuration the "
                      "surrounding behavior must leave exactly as it was.",
        "rationale": "REJECT from clause L1 (legacy verbatim), the DESCRIPTION "
                     "component: the legacy regime must keep the entry with all "
                     "three components verbatim, but the rival substitutes `[]` "
                     "for the description; on a non-empty description they "
                     "differ, so the equality fails. The two frame rivals both "
                     "act inside the EXPANSION branch, so the legacy branch's "
                     "carried description is unprobed without this case.",
        "witness": (
            "-- Refuted on a non-grouped entry with a non-empty description: the\n"
            "-- kept entry must reproduce it verbatim, so emptying it violates L1.\n"
            "example : ¬ problem_spec_normalizeEntries false "
            "[(['a'], [], [['d']])]\n"
            "    (implementation_normalizeEntries false "
            "[(['a'], [], [['d']])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # ---- L4: LEGACY keep-at-most-one (a kept entry is kept ONCE) ----
    {
        "id": "legacy-duplicates-kept-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the kept legacy entry TWICE. This is the direct analogue of the
        # nagini `len(Result()) <= 1` clause, which the port's original docstring
        # listed as folded into the grounded equality but attacked with no rival:
        # every other legacy rival either changes the kept VALUE (legacy-splits-
        # anyway, keep-guard) or emits one where zero is required (empty-entry),
        # so an over-count in the KEEP direction was unprobed.
        "module": _swap(
            _BASE, _A_APPEND_LEGACY,
            "      fields := fields ++ [(name, typ, desc), (name, typ, desc)]\n",
        ),
        "refinement": "a faithful real patch that appended the kept entry twice "
                      "would render every non-grouped item twice in the output "
                      "block; the asserted text lists each item once, so the "
                      "duplicated lines mismatch => does NOT resolve. It also "
                      "regresses the unchanged non-grouped configuration, which "
                      "the surrounding behavior must leave exactly as it was.",
        "rationale": "REJECT from clause L4 (keep-at-most-one): `expandEntry` maps "
                     "a content-bearing entry in the legacy regime to a "
                     "SINGLETON list, but the rival emits two copies; the two "
                     "lists differ in length, so the equality fails. This is the "
                     "over-count direction of the keep clause, which no other "
                     "legacy rival reaches.",
        "witness": (
            "-- Refuted on a single content-bearing non-grouped entry: it must be\n"
            "-- kept exactly ONCE, so emitting two copies violates clause L4.\n"
            "example : ¬ problem_spec_normalizeEntries false [(['a'], [], [])]\n"
            "    (implementation_normalizeEntries false [(['a'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries implementation_normalizeEntries\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # DIVERGENCE — an impl that carries NO decreasing measure. This bundle sets
    # no partial-termination semantics, so the frozen obligation must still be
    # discharged for such an impl and cannot be: nothing is known about the value
    # a measure-free loop returns. The class was originally recorded here as
    # having no expressible instance; it does, so it ships.
    # =====================================================================
    {
        "id": "diverge-measure-free-scan",
        "kind": "uniqueness",
        "expect": "reject",
        # The recursive call repeats the SAME argument, so nothing advances and
        # the definition is admitted only under `partial` — which makes the term
        # irreducible rather than false, so a witness cannot simply evaluate it.
        # The device that makes the violation STATABLE is the prepended marker
        # entry: the refutation is taken over the computable HEAD projection,
        # where the rival's value is the marker and the spec's is the kept entry.
        # `partial` is not an assumption token — it proves nothing and closes no
        # goal; it only declines to supply a termination measure, which is
        # precisely the defect under attack.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "partial def spinEntries (raws : List FieldEntry) : List FieldEntry :=\n"
            "  spinEntries raws\n"
            "\n"
            "def implementation_normalizeEntries\n"
            "    (splitGrouped : Bool) (raws : List FieldEntry) : List FieldEntry :=\n"
            "  ([','], [], []) :: spinEntries raws\n",
        ),
        "refinement": "a faithful real patch whose per-entry scan never advanced "
                      "would never finish assembling the normalized list, so the "
                      "documentation block it feeds would never be rendered at "
                      "all: the F2P asserts on the rendered text, and a call that "
                      "does not return cannot satisfy that assertion — nor can "
                      "any of the pre-existing assertions exercising the same "
                      "path. So it does NOT resolve, and it regresses everything "
                      "green at base rather than only the new assertion. This is "
                      "why the class is worth a case on a carrier with no "
                      "partial-termination semantics: the obligation is NOT "
                      "discharged vacuously by a non-returning impl, so the spec "
                      "really does exclude it.",
        "rationale": "REJECT from the grounded equality itself: the measure-free "
                     "scan supplies no information about the list it returns, and "
                     "the impl prepends a marker entry, while the spec pins the "
                     "result to `raws.flatMap (expandEntry false)` — at this "
                     "input the single kept entry. Unlike every other rival in "
                     "this lane the defect is not a wrong VALUE on part of the "
                     "domain but the absence of a terminating computation, which "
                     "is the third direction this gate tests; any input refutes "
                     "it, so the choice of input carries no claim of a "
                     "distinguishing sub-domain.",
        "witness": (
            "-- Refuted on a single content-bearing non-grouped entry. The\n"
            "-- measure-free scan yields no information about its tail, so the\n"
            "-- refutation is stated over the computable HEAD projection: the\n"
            "-- spec's first normalized entry here is the kept entry itself,\n"
            "-- which the rival's head (the prepended marker) is not. No reduction\n"
            "-- of the irreducible tail is needed.\n"
            "example : ¬ problem_spec_normalizeEntries false [(['a'], [], [])]\n"
            "    (implementation_normalizeEntries false [(['a'], [], [])]) := by\n"
            "  unfold problem_spec_normalizeEntries\n"
            "  intro h\n"
            "  have hh := congrArg List.head? h\n"
            "  simp only [implementation_normalizeEntries, List.head?_cons] at hh\n"
            "  revert hh\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references to re-discharge here: the
# comma-split and blank-trim operations are deeply modeled (commaPieces / trim)
# and validated == their real library counterparts by G-CONF (meta.json
# axioms == []), so there is no in-model axiom obligation for the PBT axiom lane.
# The axiom lane is G-AX's job in any case.
AXIOM_TESTS = []
