"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14053 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside an ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_<name>`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models one function ``resolve_node_names(names, feat)`` under fractional-
permission (read-only) contracts over TWO heap lists, with a deep-model fold
``built_seq`` pinning the resolved label per node. This Lean bundle models the
SAME single purely-functional core — resolve a per-node feature-index list
against a name list, emitting no label at a leaf sentinel and the looked-up name
otherwise — but Lean is referentially transparent: the inputs carry no heap
permission. So the two nagini FRAME-MUTATION rivals (writes into the read-only
``feat`` / ``names`` half-permission) are VACUOUS here and are omitted (see the
module ``assessment``); every remaining nagini case carries over as an attack on
the ONE modeled obligation ``result = featureNamesSpec featureNames features``.

DEFENDED SURFACE (one modeled behavior). The result is EXACTLY the per-entry
resolution of the index list against the name list, in order. The postcondition
pins ``result`` to a single grounded computation ``featureNamesSpec`` over the
inputs (a front-recursive fold of ``featureNameAt``), so it has these
independent, per-entry structural obligations, all attacked below:

  * a leaf-sentinel entry (index ``= -2``) resolves to NO label (``none``) — the
    CHANGED clause (the fix adds the sentinel guard);
  * a non-sentinel entry resolves to the name at THAT position
    (``featureNames[i.toNat]?``), not some other position;
  * every entry contributes EXACTLY ONE output element in order, so
    ``result.length = features.length`` and the order is preserved.

The BEHAVIOURAL DISCRIMINATOR (the fix): guard the per-entry lookup so a leaf
entry yields the neutral no-label value instead of looking a name up at the
sentinel position. The pre-fix behavior looked every entry up unconditionally;
the ``weak-drop-guard`` rival below IS that pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED so rather than
    asserted. Lean is referentially transparent: an input carries no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. The nagini frame-mutation rivals
    (``frame-mutation-feat`` writing ``feat[i-1]``, ``frame-mutation-names``
    writing ``names[0]``) have no expressible instance here; no substitute is
    fabricated. (nagini cases 3, 3b.) Audit evidence: the closest analogue,
    assigning to the input binder inside the loop
    (``featureNames := featureNames ++ ["clobber"]``), does not even elaborate —
    Lean rejects it with ```featureNames` cannot be mutated, only variables
    declared using `let mut` can be mutated``. So the rejection would attest to
    a syntax rule about function parameters, not to anything the spec says, and
    the case is correctly dropped rather than ported as a rival that "passes".

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to ``featureNamesSpec`` built only from the two inputs. There
    is no opaque answer key an implementation could echo — computing
    ``featureNamesSpec`` IS doing the work. In its place the battery carries
    honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, in two independent flavours.

    CLAUSE-PARTIAL (a rival correct on one structural class of entry and wrong
    on the other, at EVERY entry of that class): dropping the sentinel guard
    (pre-fix bug — correct at every internal entry, wrong at every leaf);
    emitting the wrong name (position 0 for every internal node — accidentally
    correct on the single-feature F2P tree); emitting ``none`` at every
    non-sentinel entry; and dropping every internal entry (length short).

    POSITION-PARTIAL (a rival that honours BOTH clauses everywhere except at one
    POSITION in the list): ``weak-second-entry-blank`` below blanks only the entry
    at position 1 and is byte-for-byte gold at every OTHER position, including
    position 0. This is the flavour the nagini design document attacked with its
    ``i > 1`` guards (cases 4 and 6), and it is a genuinely distinct obligation:
    the frozen spec's fold is positional, so a rival can satisfy every per-clause
    reading of the postcondition and still be wrong.

    Audit note, second pass (this is the case's THIRD revision and the reason it
    is stated so precisely). The port's original battery mapped nagini cases 4/6
    onto the two clause-partial rivals, which are wrong at every entry of their
    class, so the positional flavour was unported while the prose claimed it. The
    first repair added a rival blanking position 0 (``if acc.isEmpty``) and
    claimed it was "unattackable at any of the four single-entry points". That
    claim was FALSE and is the defect this pass fixes: blanking position 0 blanks
    the ONLY entry of a one-element list, so that rival evaluates to ``[none]`` at
    every single-entry point and is refutable at three of the four (it is
    observationally IDENTICAL to ``weak-internal-as-leaf`` on every single-entry
    list — measured by evaluation at all four points). It therefore did not
    isolate the positional obligation at all; it was a second spelling of the
    everywhere-blank rival with a multi-entry witness bolted on.

    The rival below is the real thing: it blanks position 1, so it AGREES with the
    frozen spec on EVERY one-element index list (machine-checked: the spec
    predicate is PROVEN by ``decide`` at all four single-entry points of this
    battery, one build, exit 0) and diverges only once a second entry exists.
    Refuting it therefore REQUIRES a multi-entry list, which is exactly the
    obligation the positional class is supposed to carry. Landed with real builds:
    rival exit 0, gold exit 1 with a semantic ``decide`` refutation, and the
    flipped-claim forgery control on gold exit 0 (so gold's exit code tracks the
    claim rather than being a constant).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. The carrier is FULLY COMPUTABLE at literal
inputs (``featureNamesSpec`` folds over concrete lists of ``String`` and ``Int``;
``featureNames[i.toNat]?`` is a total list index), so each witness is discharged
by ``decide`` with no conditioning needed and binds nothing. Each was checked
(two real ``lake`` builds) to HOLD of its rival and to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology.

BINDER / POINT SPREAD. The spec predicate has two input binders, ``featureNames``
and ``features``. The reject witnesses move BOTH rather than fixing them at one
convenient point, and — critically — vary the two structural sub-cases of
``features`` (a leaf-sentinel entry ``-2`` and a valid in-range index ``i >= 0``)
and the LENGTH of ``featureNames`` (single-name vs multi-name), because the
value clause is only distinguishable from the wrong-position rival when
``featureNames`` has ≥2 entries:

  * ``weak-drop-guard`` probes ``featureNames=["a","b"], features=[-2]`` (the
    sentinel entry: the guard must fire);
  * ``weak-wrong-position`` probes ``featureNames=["a","b"], features=[1]`` (a
    non-zero valid index against a ≥2-name table — the ONE point that separates
    "the right name" from "position 0");
  * ``weak-internal-as-leaf`` probes ``featureNames=["m","n"], features=[0]`` (a
    valid index the rival wrongly blanks to ``none``);
  * ``weak-drop-entry`` probes ``featureNames=["a"], features=[0]`` (the length
    clause: one entry dropped);
  * ``weak-second-entry-blank`` probes ``featureNames=["m","n"],
    features=[0, 1]`` — the only MULTI-ENTRY index list in the battery, and the
    only point where the positional structure of the fold is load-bearing. This
    rival is DEMONSTRABLY unattackable at every one of the four points above: it
    satisfies the spec predicate there, which is proven (not argued) by ``decide``
    at all four, so a multi-entry input is not a stylistic preference here but the
    only thing that can refute it.

No two rivals share a refutation point; the five reject witnesses probe five
distinct inputs (``pts=5``), and only the last has ``features.length > 1``.

DIVERGENCE lane: KNOWN HOLE, measured rather than assumed. This is a plain Lean
bundle (no ``loom.semantics.termination`` setting — that option belongs to the
velvet/loom carrier, and no such line appears in the frozen solution), so the
verifier discharges no termination obligation and there is nothing for a
divergence rival to be rejected BY. Measured: a rival replacing the loop with a
``partial def spin`` that recurses on its own argument does fail to build (exit
1), but only with ``Tactic `rfl` failed`` — the tactic cannot reduce a
``partial`` constant, which is compiler opacity, not the spec speaking — and its
witness CANNOT be landed: ``decide`` on the spec predicate at ``["a"] [0]``
fails against the rival too (exit 1, ``Tactic `decide` failed for proposition``),
because the ``partial`` term does not reduce for either side. So no witness can
discriminate, the rejection would attest to opacity rather than to the spec, and
the case is correctly ABSENT. Recorded as a known hole in the spec's reach (a
non-reducing impl is not refutable here), NOT as a vacuous class.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed operation is modeled deeply as ``featureNamesSpec``); the
axiom lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are
dropped.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14053"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive that adds a `have`, the proof region) so same_spec stays byte-
# identical and the `theorem correct_<name>` STATEMENT is untouched.

# The whole per-entry conditional of the impl loop body (the CHANGED clause).
_I_BODY = (
    "      if i ≠ sentinelIndex then\n"
    "        acc := acc ++ [featureNames[i.toNat]?]\n"
    "      else\n"
    "        acc := acc ++ [none]"
)

# The frozen proof body's `intro` line (proof region), unique in the file
# (the helper lemma introduces `features` only).
_P_INTRO = "  intro featureNames features\n  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode"

# The ENTIRE frozen proof-region text (both the helper lemma and the bridge
# proof), used as a single anchor so the soundness positive can re-prove for a
# reshaped impl. It lies entirely inside the proof region, so same_spec is
# untouched; the swap keeps the `featureNamesByNode_forIn` name and the
# `correct_featureNamesByNode` STATEMENT byte-identical (only tactic/proof text
# differs, which the scope rule permits) and adds no new axiom/theorem.
_P_FROZEN = (
    "theorem featureNamesByNode_forIn (featureNames : List String) :\n"
    "    ∀ (features : List Int) (acc : List (Option String)),\n"
    "      Id.run (forIn features acc (fun i r =>\n"
    "        (if i ≠ sentinelIndex then\n"
    "            (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)\n"
    "         else\n"
    "            pure (ForInStep.yield (r ++ [none])))))\n"
    "      = acc ++ featureNamesSpec featureNames features := by\n"
    "  intro features\n"
    "  induction features with\n"
    "  | nil =>\n"
    "    intro acc\n"
    "    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl\n"
    "  | cons a as ih =>\n"
    "    intro acc\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    by_cases h : a ≠ sentinelIndex\n"
    "    · simp only [if_pos h, featureNamesSpec, featureNameAt, ih, List.append_assoc,\n"
    "        List.cons_append, List.nil_append]\n"
    "    · simp only [if_neg h, featureNamesSpec, featureNameAt, ih, List.append_assoc,\n"
    "        List.cons_append, List.nil_append]\n"
    "\n"
    "theorem correct_featureNamesByNode :\n"
    "    ∀ (featureNames : List String) (features : List Int),\n"
    "      problem_spec_featureNamesByNode featureNames features\n"
    "        (implementation_featureNamesByNode featureNames features) := by\n"
    "  intro featureNames features\n"
    "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
    "  -- bridge the desugared `do … for … mut …` body to the helper's clean body\n"
    "  have h2 :\n"
    "      (Id.run do\n"
    "        let mut acc : List (Option String) := []\n"
    "        for i in features do\n"
    "          if i ≠ sentinelIndex then\n"
    "            acc := acc ++ [featureNames[i.toNat]?]\n"
    "          else\n"
    "            acc := acc ++ [none]\n"
    "        return acc)\n"
    "      = Id.run (forIn features ([] : List (Option String)) (fun i r =>\n"
    "          (if i ≠ sentinelIndex then\n"
    "              (pure (ForInStep.yield (r ++ [featureNames[i.toNat]?])) : Id _)\n"
    "           else\n"
    "              pure (ForInStep.yield (r ++ [none]))))) := rfl\n"
    "  rw [h2, featureNamesByNode_forIn]\n"
    "  simp"
)

# The re-proved proof region for the single-`elem` reshaped impl: the helper is
# re-stated over the `let`-inlined loop body (no `by_cases` needed since the two
# branches are unified into one `if`), and the bridge `have h2` is retyped.
_P_NEW = (
    "theorem featureNamesByNode_forIn (featureNames : List String) :\n"
    "    ∀ (features : List Int) (acc : List (Option String)),\n"
    "      Id.run (forIn features acc (fun i r =>\n"
    "        (pure (ForInStep.yield (r ++ [if i ≠ sentinelIndex then featureNames[i.toNat]? else none])) : Id _)))\n"
    "      = acc ++ featureNamesSpec featureNames features := by\n"
    "  intro features\n"
    "  induction features with\n"
    "  | nil =>\n"
    "    intro acc\n"
    "    simp only [List.forIn_nil, featureNamesSpec, List.append_nil]; rfl\n"
    "  | cons a as ih =>\n"
    "    intro acc\n"
    "    rw [List.forIn_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    simp only [featureNamesSpec, featureNameAt, ih, List.append_assoc,\n"
    "      List.cons_append, List.nil_append]\n"
    "\n"
    "theorem correct_featureNamesByNode :\n"
    "    ∀ (featureNames : List String) (features : List Int),\n"
    "      problem_spec_featureNamesByNode featureNames features\n"
    "        (implementation_featureNamesByNode featureNames features) := by\n"
    "  intro featureNames features\n"
    "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
    "  have h2 :\n"
    "      (Id.run do\n"
    "        let mut acc : List (Option String) := []\n"
    "        for i in features do\n"
    "          let elem := if i ≠ sentinelIndex then featureNames[i.toNat]? else none\n"
    "          acc := acc ++ [elem]\n"
    "        return acc)\n"
    "      = Id.run (forIn features ([] : List (Option String)) (fun i r =>\n"
    "          (pure (ForInStep.yield (r ++ [if i ≠ sentinelIndex then featureNames[i.toNat]? else none])) : Id _))) := rfl\n"
    "  rw [h2, featureNamesByNode_forIn]\n"
    "  simp"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. Ports nagini case 1
    # (pos-control-single-prepend): the nagini positive hoisted the per-node
    # resolved entry into a single local `elem` and appended once instead of two
    # branches. Here the analogous reshape binds the resolved label to one local
    # `elem` and appends once; the proof region is re-proved to match the reshape
    # (a `let`-inlined loop body folds to the SAME `featureNamesSpec`), keeping
    # the `theorem correct_<name>` STATEMENT byte-identical and introducing no
    # new axiom / helper theorem beyond the frozen `featureNamesByNode_forIn`.
    # =====================================================================
    {
        "id": "pos-single-append",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_BODY,
                "      let elem := if i ≠ sentinelIndex then featureNames[i.toNat]? else none\n"
                "      acc := acc ++ [elem]",
            ),
            _P_FROZEN, _P_NEW,
        ),
        "rationale": "structurally-different but CORRECT impl (hoist the resolved "
                     "label into one local `elem`, append once, instead of two "
                     "`acc ++ [..]` branches); the loop still folds to "
                     "`featureNamesSpec`, so `result = featureNamesSpec …` holds. "
                     "Must verify, else SPEC-TOO-STRONG. Re-proved via a re-stated "
                     "`featureNamesByNode_forIn` over the `let`-inlined body "
                     "(theorem STATEMENT byte-identical, no new axiom/helper). "
                     "Ports nagini's single-prepend positive. Audit evidence that "
                     "the reshape is REAL and the re-proof load-bearing: this impl "
                     "paired with the FROZEN proof text fails to build (`rewrite` "
                     "finds no occurrence of the two-branch `forIn` pattern), so "
                     "the case is not a cosmetic edit the frozen script already "
                     "closed. Three further correct reshapes were checked to "
                     "verify against this spec — `features.map (featureNameAt "
                     "featureNames)`, a `foldl` appending, and a `foldl` "
                     "prepending then `.reverse` — so the spec is not "
                     "SPEC-TOO-STRONG on any shape tried.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at the
    # normal, F2P-shaped input. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, `∀` unguarded), so the nagini
    # precondition-admission self-call (case 2) has no binder to attack here; the
    # honest analogue is to discharge the spec predicate by evaluation at the
    # F2P single-feature tree (root internal node 0, then leaf sentinels) as a
    # `have`, then close the frozen obligation verbatim. Nothing is assumed: no
    # new declaration, statement byte-identical. Ports nagini case 2
    # (admissibility-self-call).
    # =====================================================================
    {
        "id": "admiss-ground-f2p-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_featureNamesByNode [\"first\"] [0, -2, -2]\n"
            "      (implementation_featureNamesByNode [\"first\"] [0, -2, -2]) := by\n"
            "    unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
            "    decide\n"
            "  intro featureNames features\n"
            "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode",
        ),
        "rationale": "the obligation is discharged at the F2P single-feature tree "
                     "(root internal node index 0 then leaf sentinels [0,-2,-2], "
                     "the shape the reported bug crashed on) by `decide` as a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the F2P input — the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, statement byte-"
                     "identical, ground instance is a `have` in the existing "
                     "tactic body. Ports nagini's self-call admissibility probe. "
                     "Audit evidence that the `decide` genuinely COMPUTES here "
                     "(rather than closing vacuously, which would make this case "
                     "attest to nothing): the same `have` with a deliberately "
                     "FALSE ground claim — the same call `.reverse`d — fails to "
                     "build, with `decide` reporting the proposition false. So the "
                     "tactic is deciding the claim, not getting stuck on it.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a `decide` witness
    # pinning the violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: drop the sentinel guard (nagini partial/value core) --
    {
        "id": "weak-drop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: look every entry up unconditionally, so a leaf
        # sentinel entry (-2) resolves via the lookup instead of yielding `none`.
        "module": _swap(
            _BASE, _I_BODY,
            "      acc := acc ++ [featureNames[i.toNat]?]",
        ),
        "refinement": "this IS the pre-fix behavior: the unconditional per-entry "
                      "lookup that the reported IndexError comes from. A faithful "
                      "real patch keeping the unconditional lookup resolves a leaf "
                      "entry to a label (in the real code an out-of-range index "
                      "into a short name list — the IndexError; in the total model "
                      "the sentinel resolves to the wrong slot) instead of no "
                      "label, so the printed per-node label list is wrong / the "
                      "call raises. The F2P asserts the exact report with leaves "
                      "carrying no name, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the sentinel clause: at a leaf entry the spec "
                     "yields `none` (`featureNameAt` returns `none` for `-2`) "
                     "while the rival yields the lookup at `(-2).toNat`, so "
                     "`result` differs. Binder spread: a ≥2-name table and a "
                     "single-leaf index list.",
        "witness": (
            "-- Refuted at a leaf-sentinel entry: the guard must fire. Fully\n"
            "-- computable at literal inputs, so `decide` closes.\n"
            "example : ¬ problem_spec_featureNamesByNode [\"a\", \"b\"] [-2]\n"
            "    (implementation_featureNamesByNode [\"a\", \"b\"] [-2]) := by\n"
            "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
            "  decide\n"
        ),
    },

    # ---- wrong position: names[0] for every internal node (nagini case 5) ----
    {
        "id": "weak-wrong-position",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve every internal node to the FIRST name (position 0) instead of
        # the name at that node's index.
        "module": _swap(
            _BASE, _I_BODY,
            "      if i ≠ sentinelIndex then\n"
            "        acc := acc ++ [featureNames[0]?]\n"
            "      else\n"
            "        acc := acc ++ [none]",
        ),
        "refinement": "resolves every internal node to name position 0 instead of "
                      "the node's own feature index. Accidentally CORRECT on the "
                      "single-feature F2P tree (every internal node selects "
                      "feature 0, so position 0 IS the right name). A faithful "
                      "patch substituting the first name for every node mislabels "
                      "any split on a feature index != 0, so every multi-feature "
                      "report is wrong — exactly why the spec must pin the EXACT "
                      "entry, not merely 'some name'. Would NOT resolve on a "
                      "multi-feature tree.",
        "rationale": "REJECT from the value clause: the spec pins "
                     "`featureNames[i.toNat]?` and the rival returns "
                     "`featureNames[0]?`; these differ once the index is non-zero "
                     "AND the table has ≥2 names. Binder spread: this is the ONLY "
                     "witness at a non-zero valid index against a ≥2-name table — "
                     "the point that separates 'the right name' from 'position 0'.",
        "witness": (
            "-- Refuted at a non-zero valid index against a two-name table: the\n"
            "-- spec wants the second name, the rival returns the first.\n"
            "example : ¬ problem_spec_featureNamesByNode [\"a\", \"b\"] [1]\n"
            "    (implementation_featureNamesByNode [\"a\", \"b\"] [1]) := by\n"
            "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
            "  decide\n"
        ),
    },

    # ---- internal node emitted as leaf (nagini case 4, partial-domain root) ---
    {
        "id": "weak-internal-as-leaf",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit no label even for an internal (non-sentinel) node: over-apply the
        # leaf blanking so an internal split loses its name.
        "module": _swap(
            _BASE, _I_BODY,
            "      acc := acc ++ [none]",
        ),
        "refinement": "emits no label for EVERY node, including internal split "
                      "nodes. A faithful patch that blanked internal nodes would "
                      "drop each split's feature name, so the report prints the "
                      "split comparison without its name (`|--- <= 0.0` instead of "
                      "`|--- first <= 0.0`); the F2P asserts the named report "
                      "verbatim, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the value clause: at an internal (non-sentinel) "
                     "entry the spec yields `some name` while the rival yields "
                     "`none`, so `result` differs. Binder spread: a distinct "
                     "≥2-name table [\"m\",\"n\"] and a single valid-index list "
                     "[0], the internal-node point (own point, not shared with "
                     "the wrong-position rival which sits at index 1).",
        "witness": (
            "-- Refuted at an internal node: the spec wants a name, the rival\n"
            "-- blanks it to none.\n"
            "example : ¬ problem_spec_featureNamesByNode [\"m\", \"n\"] [0]\n"
            "    (implementation_featureNamesByNode [\"m\", \"n\"] [0]) := by\n"
            "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
            "  decide\n"
        ),
    },

    # ---- drop an entry: length short (nagini case 6, length clause) ----
    {
        "id": "weak-drop-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip contributing an output element for an internal node, so the result
        # is one element short of the index list.
        "module": _swap(
            _BASE, _I_BODY,
            "      if i ≠ sentinelIndex then\n"
            "        acc := acc\n"
            "      else\n"
            "        acc := acc ++ [none]",
        ),
        "refinement": "skips the output element for every internal node, so the "
                      "per-node label list is shorter than the index list. The "
                      "report indexes the label list by node id, so the "
                      "misalignment prints wrong names / overruns — the F2P report "
                      "mismatches, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from the per-entry-one-element clause: the spec's "
                     "fold contributes exactly one element per index "
                     "(`result.length = features.length`), while the rival drops "
                     "internal-node elements, so `result` is short and differs. "
                     "Binder spread: a single-name table [\"a\"] and a single "
                     "valid-index list [0] (the length point).",
        "witness": (
            "-- Refuted by a length/shape mismatch: the rival contributes no\n"
            "-- element for the internal node, so its result is [].\n"
            "example : ¬ problem_spec_featureNamesByNode [\"a\"] [0]\n"
            "    (implementation_featureNamesByNode [\"a\"] [0]) := by\n"
            "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
            "  decide\n"
        ),
    },

    # ---- POSITION-PARTIAL near-miss: only the SECOND entry is wrong ---------
    # The flavour nagini attacked with its `i > 1` guards (cases 4 and 6) and
    # that no other rival here reaches: this impl honours BOTH per-entry clauses
    # (sentinel -> none, non-sentinel -> the name at that index) at every entry
    # except the one at position 1, which it blanks unconditionally.
    #
    # Position 1 rather than position 0 is the load-bearing choice, and it is
    # what distinguishes this case from the revision it replaces. A rival that
    # blanks position 0 also blanks the only entry of a ONE-element list, so it
    # collapses onto `weak-internal-as-leaf` on every single-entry input and is
    # refutable there — it does not isolate the positional obligation. Blanking
    # position 1 leaves every one-element list exactly gold, so this rival can
    # ONLY be refuted on a multi-entry input, which is precisely the obligation
    # the positional class exists to test.
    {
        "id": "weak-second-entry-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_BODY,
            "      if acc.length = 1 then\n"
            "        acc := acc ++ [none]\n"
            "      else if i ≠ sentinelIndex then\n"
            "        acc := acc ++ [featureNames[i.toNat]?]\n"
            "      else\n"
            "        acc := acc ++ [none]",
        ),
        "refinement": "blanks the label of the entry at position 1 only, and is "
                      "exactly gold at every other position. A faithful patch "
                      "behaving this way loses one interior entry's name while "
                      "every other entry prints correctly, so the rendered report "
                      "is missing exactly one name — the report is asserted "
                      "verbatim, so the faithful patch would NOT resolve. This is "
                      "the near-miss the other four rivals cannot express: they "
                      "are wrong at every entry of their class and so are "
                      "refutable on a single-entry list, whereas this one agrees "
                      "with the spec on every single-entry list and requires a "
                      "multi-entry list to expose.",
        "rationale": "REJECT from the POSITIONAL structure of the fold: "
                     "`featureNamesSpec` resolves the entry at each position "
                     "independently, so honouring both per-entry clauses at every "
                     "other position does not license blanking position 1; "
                     "`result` differs in its tail. Binder spread: the only "
                     "multi-entry index list in the battery ([0, 1], whose two "
                     "entries carry DIFFERENT valid indices so the refutation "
                     "cannot be read off any single-entry point) against a "
                     "distinct 2-name table. Machine-checked to SATISFY the frozen "
                     "spec at all four single-entry points of this battery "
                     "([\"a\",\"b\"] [-2], [\"a\",\"b\"] [1], [\"m\",\"n\"] [0], "
                     "[\"a\"] [0]) — proven by `decide`, not argued — which is what "
                     "makes it a genuine positional near-miss and not a second "
                     "spelling of `weak-internal-as-leaf`.",
        "witness": (
            "-- Refuted at the SECOND entry of a two-entry list: the spec resolves\n"
            "-- position 1 to the name at index 1, the rival blanks it. The FIRST\n"
            "-- entry agrees with the spec, and so does every one-element list, so\n"
            "-- this pins the positional clause specifically rather than a\n"
            "-- per-entry clause.\n"
            "example : ¬ problem_spec_featureNamesByNode [\"m\", \"n\"] [0, 1]\n"
            "    (implementation_featureNamesByNode [\"m\", \"n\"] [0, 1]) := by\n"
            "  unfold problem_spec_featureNamesByNode implementation_featureNamesByNode\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle declares no `opaque` callee and consumes no
# `axiom` (the changed operation is modeled deeply as `featureNamesSpec`). The
# nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
