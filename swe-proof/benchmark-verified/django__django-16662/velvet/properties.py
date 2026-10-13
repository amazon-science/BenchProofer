"""properties.py — G-PBT falsification battery for django__django-16662 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method that orders a collection of
import-statement lines carried per-code-point as ``List (List Char)``:

  orderImportLines (imports : List (List Char)) return (out : List (List Char))
      ensures out = sortImports imports          -- (ORD) exact ordering
      ensures List.Perm out imports              -- (PERM) same multiset

where ``sortImports l = l.mergeSort keyLe`` and ``keyLe`` is the COMPOSITE key: a
whole-module line (``isQualified = false``) sorts ahead of a qualified line
(``isQualified = true``); within a group the module token decides under the
per-code-point order ``lcharLe``. ``keyLe`` / ``isQualified`` / ``moduleTok`` /
``firstTok`` / ``afterFirst`` / ``lcharLe`` are TRANSPARENT ``def``s spelled out
over the input (directive 8), NOT an opaque answer-key: the whole ordering is a
computable function of the lines, so a rival cannot "echo an oracle" — the only
way to satisfy (ORD) is to reproduce the exact ordered list. The two stdlib
primitives it stands in for (a whitespace token split and a stable key-sort) are
validated equal by G-AX (A-references); this gate ignores that lane.

WHAT THE SPEC DEFENDS. The content of the modeled fix is the GROUPING half of the
key: whole-module lines must precede qualified lines regardless of the module
token, so a qualified line whose module token sorts lexicographically BEFORE a
whole-module line's still lands after it. That grouping lives inside ``keyLe`` and
is pinned by clause (ORD). Clause (PERM) independently pins that the operation
neither drops, adds, nor fabricates a line.

BINDER STRUCTURE (read before judging binder coverage). There is ONE input
binder, ``imports``. The five reject witnesses each probe a DISTINCT two-line list
(pts=5) and the admissibility positive probes a further three-line one inside its
proof, so ``imports`` is genuinely varied across the battery rather than pinned
at one point; each list is chosen so the rival's defect is observable there.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries this MANDATORY because
    its list inputs are held at a fractional heap permission (``Acc(.,1/2)``) an
    impl can illegally overwrite. Lean/Velvet are referentially transparent:
    ``imports`` is an immutable value, there is no ``mut`` binder, no heap and no
    aliasing — so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated (porting map: this class is vacuous here). The
    "no line dropped/added" obligation the nagini permission split protected is
    instead pinned VALUE-LEVEL by clause (PERM), which the drop rival attacks.
  * ADMISSIBILITY (nagini's F2P-shaped self-call proving the precondition) —
    RE-AIMED and CARRIED, as ``admiss-obligation-satisfiable-at-f2p-shape``. This
    bundle declares no ``require`` clause, so the literal "a legitimate input
    satisfies the precondition" probe has nothing to discharge — but that does NOT
    make the lane vacuous, and an earlier revision of this file wrongly dropped it
    on that reasoning. On a total carrier the PRECOND-TOO-STRONG analogue is the
    obligation being UNSATISFIABLE at an F2P-shaped input, which this gate cannot
    otherwise see (an unmeetable spec and a trivially-met one both present as
    "the positives verify"). The case discharges both clauses at the concrete
    three-line discriminating input by evaluation, as ``have``s, before closing the
    frozen obligation verbatim.
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent ``def`` over
    the method input, not an axiomatized oracle; the ``axioms`` region is empty.
    The no-echo positive control (``pos-transparent-def``) demonstrates that the
    cheapest impl still does the real ordering.
  * AXIOM lane (nagini's compkey / sort A-reference probes) — DROPPED. The axiom
    lane is G-AX's job; this gate ignores ``AXIOM_TESTS``.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``orderImportLinesTester imports = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped (so no tactic script can mask the
verdict) and there are no ``require`` clauses, so every input reaches the
postcondition. ``mergeSort`` uses well-founded recursion the kernel will NOT
reduce under a bare ``decide`` (measured), so each witness first ``unfold``s the
tester and its extracted program, then hands the ordering ``def``s to ``simp``,
which computes the two-element sort, and finally ``all_goals decide`` settles the
boolean equality by kernel evaluation — the trailing ``decide`` is load-bearing on
the ``List.Perm`` residual that ``simp`` alone leaves open in either direction; see
the ``_TAC`` comment for the measurement that forced it. No ``sorry`` / ``admit``
/ ``native_decide`` is used.

Every witness is confirmed with FOUR real builds, not two, because "the gold build
failed" is only evidence if its exit code tracks what the witness CLAIMS. For each
rival: the witness ELABORATES against the rival (exit 0) and FAILS against the
frozen solution (exit 1, ``Tactic `decide` proved that the proposition … is
false`` — an evaluated refutation of the concrete claim), AND the FORGERY that
flips the claim to ``= true`` (asserting the impl is CORRECT at that input)
reverses both: exit 0 on the frozen solution, exit 1 on the rival. That reversal is
what rules out a gold-side failure carrying no information about the claim.
"""
from pathlib import Path

INSTANCE = "django__django-16662"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE two-line impl body; lies wholly inside
# ---- the single `-- impl-start` / `-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). Anchoring on the
# ---- whole body keeps every surgery inside the elided region — the `method`
# ---- header, the two `ensures`, and the `pure` region (which spells out `keyLe`
# ---- and its callees) are never touched, so `same_spec` holds by construction.
_IMPL = "    let result := imports.mergeSort keyLe\n    return result"

# ---- frozen proof body. Elided from the consumer spec view, so a positive whose
# ---- reshaped impl makes a side goal trivial (`return sortImports imports` makes
# ---- the (ORD) goal `rfl`, which `loom_solve` then closes, leaving the frozen
# ---- `· rfl` with no goal) may retune the tactic body. The `prove_correct`
# ---- header and the obligation STATEMENT are untouched, so `same_spec` holds.
_PROOF = ("prove_correct orderImportLines by\n  loom_solve\n"
          "  · exact (List.mergeSort_perm imports keyLe)\n  · rfl")


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_proof(new_impl: str, new_proof: str) -> str:
    """Reshape the impl body AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble + tactic. Reach the contract through Velvet's tester
# ---- machinery, then compute the small sort explicitly (mergeSort is
# ---- irreducible under bare `decide`, so `simp` unfolds it first). ----
#
# The trailing `all_goals decide` is LOAD-BEARING, not belt-and-braces, and it is
# there because of a measured defect in the previous revision of this file. That
# revision stopped after the `simp` line. On three of the four rivals that was
# enough — `simp` settled the boolean equality outright, so the gold-side build
# failed with `⊢ False`, and flipping the claim to `= true` made gold SUCCEED
# (exit 0), i.e. the gold exit code tracked the claim.
#
# On the fourth (`identity-no-sort`) it was NOT enough. There `simp` reduced the
# tester to a residual `List.Perm` goal it could not settle in either direction,
# so gold failed with `⊢ ¬[...].Perm [...]` for the real witness AND with
# `⊢ [...].Perm [...]` for the flipped claim — two builds, both exit 1. Gold's
# exit code therefore carried NO information about what the witness asserted, and
# a forged witness asserting the frozen solution is CORRECT at that input would
# have cleared both halves of the discrimination check and been recorded as
# `rejected`. That is the hollow-case shape the forgery test exists to catch.
#
# `decide` closes the residual goal by KERNEL EVALUATION of the `List.Perm`
# decidability instance on the two concrete two-element lists, so the gold-side
# message becomes ``Tactic `decide` proved that the proposition ... is false`` —
# an evaluated refutation of the concrete claim — and the flipped claim builds
# clean (exit 0) on gold. Re-measured for all five rivals below: real claim
# rival 0 / gold 1, flipped claim gold 0 / rival 1. The exit code now tracks the
# claim on both sides, which is what makes each rejection attributable.
_TESTER = (
    "extract_program_for orderImportLines\n"
    "prove_precondition_decidable_for orderImportLines\n"
    "prove_postcondition_decidable_for orderImportLines\n"
    "derive_tester_for orderImportLines\n\n"
)
_TAC = (
    "  unfold orderImportLinesTester orderImportLinesExec\n"
    "  simp [NonDetT.run, orderImportLines, sortImports, List.mergeSort, "
    "keyLe, isQualified, moduleTok, firstTok, afterFirst, lcharLe]\n"
    "  all_goals decide\n"
)


def _witness(imports_lit: str) -> str:
    return _TESTER + (f"example : orderImportLinesTester {imports_lit} = false := by\n"
                      + _TAC)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both verified out-of-band with a
    # real build.
    # =====================================================================
    {
        "id": "pos-inline-return",
        "kind": "soundness",
        "expect": "verify",
        # Inline the ordered list into the return expression, dropping the named
        # intermediate local. Observationally identical on every input; the data
        # flow is unchanged, so the frozen `prove_correct` body still discharges.
        "module": _with_impl("    return imports.mergeSort keyLe"),
        "rationale": "a correct reshape (inline the ordered list into the return, "
                     "dropping the intermediate local) computes the identical "
                     "`out` on every input and adds no new proof obligation, so "
                     "both clauses `out = sortImports imports` and "
                     "`List.Perm out imports` still discharge under the frozen "
                     "`prove_correct` body; else SPEC-TOO-STRONG on impl shape.",
    },
    {
        "id": "pos-transparent-def",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying (ORD): return the transparent ordering
        # `def` directly. Because `sortImports` is spelled out over the input (a
        # `mergeSort` under the concrete `keyLe`), NOT an opaque answer key, this
        # still does the real ordering work — there is no wrong echo that
        # verifies. Demonstrates the spec is not echo-vulnerable. Returning the
        # def makes the (ORD) goal reduce to `rfl` (which `loom_solve` closes), so
        # the frozen trailing `· rfl` is retuned away; the STATEMENT is untouched.
        "module": _with_impl_proof(
            "    return sortImports imports",
            "prove_correct orderImportLines by\n  loom_solve\n"
            "  · exact (List.mergeSort_perm imports keyLe)"),
        "rationale": "the cheapest impl satisfying `out = sortImports imports` "
                     "still builds the exact ordered list, because the post-image "
                     "`sortImports` is a transparent function of `imports` (a "
                     "`mergeSort` under the concrete `keyLe`) — not an axiomatized "
                     "answer key. Shows the spec is NOT echo-vulnerable: there is "
                     "no wrong echo that verifies. Must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini sibling's F2P-shaped precondition
    # case, and ADDED UNDER AUDIT. The previous revision dropped this lane with the
    # reason "this bundle declares no `require`, so there is no precondition to
    # admit". That reason is true of the pre-conditions region and beside the point:
    # on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input — a spec no impl can meet reads,
    # to this gate, exactly like a spec every impl meets, because both directions
    # show up as "the positives verify". Dropping the lane removed one of the three
    # directions G-PBT exists to test, so it is landed here instead.
    #
    # The probe discharges BOTH clauses at the concrete three-line F2P-shaped input
    # — two whole-module lines plus one qualified line whose module token sorts
    # lexicographically BEFORE the second whole-module line's, which is the
    # discriminating configuration this spec is about — by EVALUATION, as two
    # `have`s, BEFORE closing the frozen obligation verbatim. `hf2p` computes
    # `sortImports` at that literal and pins the ordered list to the GROUPED order
    # (both whole-module lines ahead of the qualified line, despite the qualified
    # line's smaller module token); `hperm` then derives (PERM) at that same point
    # from it. If the post-image were unsatisfiable there, or if the grouped order
    # were not what `sortImports` actually produces at an F2P-shaped input, neither
    # `have` could be discharged and this case would FAIL.
    #
    # The `have`s are LIVE, not decoration: the same case asserting the INTERLEAVED
    # (module-token-only) order at that input instead — the one clause (ORD) must
    # forbid — fails to elaborate (measured out-of-band, exit 1, residual `⊢ False`
    # under the same `simp`). Only the elided tactic body changes; the `method`
    # header and both `ensures` are byte-identical, so `same_spec` holds.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_proof(
            _IMPL,
            "prove_correct orderImportLines by\n"
            "  have hf2p : sortImports [\"import datetime\".toList, "
            "\"import time\".toList, \"from django.db import migrations, "
            "models\".toList]\n"
            "      = [\"import datetime\".toList, \"import time\".toList, "
            "\"from django.db import migrations, models\".toList] := by\n"
            "    simp [sortImports, List.mergeSort, keyLe, isQualified, "
            "moduleTok, firstTok, afterFirst, lcharLe]\n"
            "  have hperm : List.Perm (sortImports [\"import datetime\".toList, "
            "\"import time\".toList, \"from django.db import migrations, "
            "models\".toList]) [\"import datetime\".toList, "
            "\"import time\".toList, \"from django.db import migrations, "
            "models\".toList] := by\n"
            "    rw [hf2p]\n"
            "  loom_solve\n"
            "  · exact (List.mergeSort_perm imports keyLe)\n  · rfl"),
        "rationale": "PASS SOURCE = the method's own obligation is SATISFIABLE at "
                     "the concrete F2P-shaped input: three lines, two whole-module "
                     "and one qualified, where the qualified line's module token "
                     "sorts lexicographically BEFORE the second whole-module "
                     "line's. The in-region `have hf2p` EVALUATES `sortImports` at "
                     "that literal and pins the result to the GROUPED order (both "
                     "whole-module lines first), and `have hperm` derives clause "
                     "(PERM) at the same point from it — so both `ensures` are "
                     "jointly satisfiable by an actual computation at exactly the "
                     "input the ordering rule is about, not merely unfalsified. If "
                     "the obligation were unsatisfiable there, or if the ordered "
                     "list at that input were the interleaved (module-token-only) "
                     "order rather than the grouped one, `hf2p` would not close and "
                     "this case would FAIL => PRECOND-TOO-STRONG / "
                     "SPEC-UNSATISFIABLE at the F2P shape. The `have`s are live: "
                     "the variant asserting the interleaved order at that input "
                     "instead fails to elaborate (measured, exit 1). The frozen "
                     "`loom_solve` tail still closes the real obligation, and the "
                     "header plus both `ensures` are untouched. Must verify.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input (ELABORATES against the rival, FAILS against gold —
    # both halves confirmed out-of-band with real builds) and the refinement
    # argument for why its faithful real counterpart would NOT resolve the
    # failing test. The four witnesses probe four distinct two-line lists, so the
    # sole input binder `imports` is varied across the battery (pts=4).
    # =====================================================================
    {
        "id": "order-by-module-token-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug: order by the module token ALONE, dropping the grouping
        # half of the key. Correct whenever the module-token order already happens
        # to be grouped, wrong exactly when a qualified line's module token sorts
        # before a whole-module line's — the discriminating configuration.
        "module": _with_impl(
            "    let result := imports.mergeSort "
            "(fun x y => lcharLe (moduleTok x) (moduleTok y))\n    return result"),
        "refinement": "orders by the module token only, with no grouping — the "
                      "exact pre-fix behaviour. Its faithful real counterpart "
                      "interleaves a qualified line between whole-module lines "
                      "whenever the qualified line's module token sorts first, so "
                      "the failing test that pins the whole-module lines AHEAD of "
                      "the qualified line (even though the qualified line's module "
                      "token is lexicographically smaller) still observes them "
                      "interleaved and still fails. It would NOT resolve. This is "
                      "the bug the fix removes.",
        "rationale": "REJECT from clause (ORD) `out = sortImports imports`: at a "
                     "whole-module line with a larger module token and a qualified "
                     "line with a smaller one, the post-image (`sortImports`, whose "
                     "`keyLe` groups whole-module lines first) puts the "
                     "whole-module line first, but the module-token-only rival puts "
                     "the qualified line first — the two ordered lists differ. "
                     "Refuted at `[\"import t\", \"from d x\"]` (module d < t, so "
                     "the rival emits the qualified line first).",
        "witness": _witness('["import t".toList, "from d x".toList]'),
    },
    {
        "id": "grouping-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss of the bug: it DOES group by qualification (so it is not the
        # module-only rival), but groups in the WRONG direction — qualified lines
        # first, whole-module lines second. Diverges from gold at the cross-group
        # boundary regardless of the module tokens, so refuted at a DIFFERENT input
        # than the module-only rival.
        "module": _with_impl(
            "    let cmp : List Char → List Char → Bool := fun x y =>\n"
            "      if isQualified x = isQualified y then "
            "lcharLe (moduleTok x) (moduleTok y)\n"
            "      else (isQualified x == true)\n"
            "    let result := imports.mergeSort cmp\n    return result"),
        "refinement": "groups qualified lines AHEAD of whole-module lines — the "
                      "opposite of the required grouping. Its faithful real "
                      "counterpart emits every qualified line before any "
                      "whole-module line, so the failing test that pins the "
                      "whole-module lines first still observes the reverse and "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from clause (ORD): the post-image groups whole-module "
                     "lines (`isQualified = false`) first, but this rival groups "
                     "qualified lines first, so at any cross-group pair the ordered "
                     "lists differ regardless of the module tokens. Refuted at "
                     "`[\"import a\", \"from b y\"]` — a whole-module and a "
                     "qualified line, where the rival emits the qualified line "
                     "first. A separate failure mode from the module-only rival "
                     "(this one DOES group, but the wrong way), refuted at a "
                     "distinct input.",
        "witness": _witness('["import a".toList, "from b y".toList]'),
    },
    {
        "id": "group-on-wrong-token",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED UNDER AUDIT (attack D). The three ordering rivals above all attack
        # the grouping DIRECTION or its presence; none attacks the PREDICATE that
        # decides which group a line belongs to. This one keeps the composite-key
        # shape intact — two groups, whole-module first, module token within — and
        # gets only the group test wrong: it asks whether the MODULE token is the
        # word `from` instead of whether the LEADING token is. That predicate is
        # false of every real line, so every line lands in the same group and the
        # grouping silently degenerates to module-token-only order, while the impl
        # still LOOKS like it groups. Probes `isQualified`'s argument position,
        # which the rest of the battery leaves unattacked.
        "module": _with_impl(
            "    let q : List Char → Bool := fun l => moduleTok l == "
            "\"from\".toList\n"
            "    let result := imports.mergeSort (fun x y =>\n"
            "      if q x = q y then lcharLe (moduleTok x) (moduleTok y) "
            "else (q x == false))\n"
            "    return result"),
        "refinement": "tests the wrong token for the group predicate, so the "
                      "grouping it appears to perform never fires and the lines "
                      "come out in module-token order. Its faithful real "
                      "counterpart therefore behaves exactly like the unfixed "
                      "ordering on every real line: it still interleaves a "
                      "qualified line among the whole-module lines whenever that "
                      "qualified line's module token sorts first, so the failing "
                      "test that pins the whole-module lines AHEAD of the "
                      "qualified line still observes them interleaved and still "
                      "fails. It would NOT resolve.",
        "rationale": "REJECT from clause (ORD) `out = sortImports imports`: the "
                     "post-image's `keyLe` groups on `isQualified`, i.e. on the "
                     "LEADING token being the word `from`; this rival groups on the "
                     "MODULE token being that word, which no real import line "
                     "satisfies. Both lines then compare within one group and the "
                     "output is module-token order, so at a cross-group pair whose "
                     "module tokens are inverted the ordered lists differ. Refuted "
                     "at `[\"import z\", \"from c w\"]` (module c < z, so the rival "
                     "emits the qualified line first while the post-image puts the "
                     "whole-module line first). A distinct failure mode from the "
                     "three ordering rivals: the key SHAPE is right and only the "
                     "group predicate's argument is wrong, and it is refuted at a "
                     "fifth distinct input.",
        "witness": _witness('["import z".toList, "from c w".toList]'),
    },
    {
        "id": "identity-no-sort",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the lines in input order, no sort. Multiset-correct (PERM holds)
        # but violates (ORD) on any input whose lines are not already ordered.
        "module": _with_impl("    return imports"),
        "refinement": "drops the ordering entirely and emits the lines in "
                      "assembly order. Its faithful real counterpart leaves the "
                      "import lines unsorted, so the failing test that pins a "
                      "specific ordered substring still observes assembly order "
                      "and still fails. It would NOT resolve.",
        "rationale": "REJECT from clause (ORD) `out = sortImports imports`: the "
                     "rival returns `imports` unchanged, so for any input not "
                     "already in `keyLe` order the emitted list differs from "
                     "`sortImports imports`. (Clause (PERM) `List.Perm out "
                     "imports` still holds — this rival attacks (ORD) alone.) "
                     "Refuted at `[\"from a x\", \"import b\"]` (a qualified line "
                     "before a whole-module line, which the ordering must swap).",
        "witness": _witness('["from a x".toList, "import b".toList]'),
    },
    {
        "id": "drop-first-line",
        "kind": "uniqueness",
        "expect": "reject",
        # Sorted-LOOKING but drops lines: keep only the first ordered line. The
        # output is a prefix of the correct order (locally ordered) but is missing
        # lines, so clause (PERM) — not (ORD) — is what refutes it. This is the
        # value-level analogue of the nagini frame-mutation / drop obligation.
        "module": _with_impl(
            "    let result := (imports.mergeSort keyLe).take 1\n    return result"),
        "refinement": "keeps only the first ordered line and drops the rest — a "
                      "buggy truncation. Its faithful real counterpart emits a "
                      "migration missing import lines, so every test that reads "
                      "back the dropped lines still fails. It would NOT resolve.",
        "rationale": "REJECT from clause (PERM) `List.Perm out imports`: the rival "
                     "returns a length-1 prefix of the ordered list, whose "
                     "multiset differs from `imports` whenever `imports` has more "
                     "than one line — so `out` is not a permutation of the input. "
                     "(Its output is a locally-ordered prefix, so it is (ORD)-like "
                     "on what it keeps; the divergence is PERM, which pins that no "
                     "line is dropped — the value-level analogue of the nagini "
                     "read-only-frame obligation.) Refuted at "
                     "`[\"import a\", \"import b\"]` (two lines; the rival emits "
                     "one).",
        "witness": _witness('["import a".toList, "import b".toList]'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 4 uniqueness rivals) plus a 1-case
# AXIOM lane. Both artifacts model the SAME functional core — order the import
# lines under the composite (group, module-token) key — so the ordering-attacking
# SPEC cases port directly; the PERMISSION class is vacuous on a
# referentially-transparent carrier, the PRECONDITION class is re-aimed (not
# vacuous — see below), and the nagini multiset (M) obligation the
# fractional-permission split protected is re-expressed as the value-level (PERM)
# clause, attacked by the drop rival.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-sort-network        -> pos-inline-return          RE-EXPRESSED
#   (no-echo demonstration)         -> pos-transparent-def        ADDED
#   admissibility-f2p-shape         -> admiss-obligation-satisfiable-at-f2p-shape
#                                                                 RE-AIMED
#   frame-mutation-flags            -> (none)                     VACUOUS (no heap)
#   frame-mutation-modules          -> (none)                     VACUOUS (no heap)
#   partial-domain-module-only-sort -> order-by-module-token-only PORTED (the bug)
#   identity-no-sort                -> identity-no-sort            PORTED
#   value-drop-duplicate            -> drop-first-line            RE-EXPRESSED
#   constant-zeros                  -> (none)                     SUBSUMED
#   AXIOM_TESTS (1)                 -> (none)                     DROPPED (G-AX lane)
#
# RE-EXPRESSED (pos-inline-return): nagini's sort-network positive is a
#   structurally-different but correct sort. Here `sortImports` is a single
#   `mergeSort` primitive (an A-reference), so the structurally-different-yet-
#   correct reshape available in the fragment is to inline the ordered list into
#   the return; it must verify under the frozen proof.
# ADDED (pos-transparent-def): the no-echo control. Nagini grounds this with a
#   master-assert; here the post-image is a transparent `def`, so the equivalent
#   demonstration is the cheapest correct impl (return `sortImports imports`
#   directly), which verifies and, because `sortImports` reduces to the real
#   ordering, admits no wrong echo.
# RE-EXPRESSED (drop-first-line): nagini's drop/duplicate rival attacks the
#   multiset clause (M). This backend pins the same content value-level as clause
#   (PERM) `List.Perm out imports`; a truncating rival violates it. Duplication is
#   not separately expressible as a distinct cheap rival here (the sort operates
#   on the actual input list), so the single drop rival carries the (PERM) attack.
# SUBSUMED (constant-zeros): nagini's canned-constant near-miss also attacks the
#   multiset clause. On this carrier a constant output is just another
#   multiset-violating rival covered by drop-first-line's (PERM) attack; adding a
#   second (PERM) rival would not move the sole binder to a new failure mode, so
#   it is omitted rather than fabricated.
# RE-AIMED (admissibility): this bundle declares no `require` clause, so nagini's
#   literal "the precondition admits this input" assert has nothing to discharge.
#   An earlier revision read that as the lane being VACUOUS and dropped it; that
#   was wrong, and it removed one of the three directions this gate tests. The
#   analogue on a total carrier is the obligation being UNSATISFIABLE at an
#   F2P-shaped input, so the case discharges both clauses at the concrete
#   three-line discriminating input by evaluation before closing the frozen
#   obligation verbatim. See `admiss-obligation-satisfiable-at-f2p-shape`.
# ADDED (group-on-wrong-token): found by an attack-D sweep for unprobed clause
#   surface. The three ordering rivals all attack the grouping's DIRECTION or its
#   presence; none attacked the PREDICATE deciding group membership. This rival
#   keeps the composite-key shape and gets only that predicate's argument wrong,
#   which degenerates the grouping to module-token order while still looking like
#   it groups.
# VACUOUS (frame-mutation x2): this backend is referentially transparent, declares
#   no `mut` binder, and has no heap — there is no read-only input to overwrite and
#   no substitute probe. The "no line dropped" content the nagini permission split
#   protected is instead a value-level obligation, clause (PERM), attacked by
#   drop-first-line. Not fabricated.
#
# BINDER / CLAUSE / POINT COVERAGE. One input binder (`imports`); the five reject
#   witnesses probe five DISTINCT two-line lists (pts=5, the figure the coverage
#   reporter measures) and the admissibility positive adds a sixth, three-line point
#   inside its proof, so `imports` is varied, not pinned, and the variation is
#   MEANINGFUL: each point is chosen so the ordered list there differs between the
#   rival and the post-image (verified per case by the forgery pair, which shows the
#   verdict at that point actually flips with the claim). Both top-level clauses are
#   attacked: (ORD) `out = sortImports imports` by order-by-module-token-only,
#   grouping-reversed, group-on-wrong-token, and identity-no-sort (four distinct
#   ordering failure modes: no grouping / reversed grouping / grouping on the wrong
#   token / no ordering at all), and (PERM) `List.Perm out imports` by
#   drop-first-line. Both clauses are defended by the two positive controls, and
#   their joint SATISFIABILITY at the discriminating input by the admissibility case.
#
# SPEC-TOO-WEAK / SPEC-TOO-STRONG sweeps run under audit, for the record. Wrong
#   impls additionally tried and all REJECTED (exit 1), so no spec hole:
#   `(mergeSort keyLe).reverse`; whole-line lex with no grouping; grouping with the
#   within-group order dropped; comparing module tokens by LENGTH instead of code
#   point; keying on the leading token instead of the module token; `.eraseDups` on
#   the ordered list; the ordered list with an extra line appended. Correct reshapes
#   additionally tried and all VERIFIED (exit 0), so no soundness hole: the
#   comparator written as a `match` on the two qualification bits (pointwise equal to
#   `keyLe` but NOT definitionally so — closed via a `funext` + case-split lemma),
#   and `sortImports` bound to a local before returning it.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the whitespace split and the
#   stable key-sort are A-references validated there, and this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
