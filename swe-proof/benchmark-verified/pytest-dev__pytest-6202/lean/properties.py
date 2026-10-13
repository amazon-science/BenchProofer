"""properties.py — G-PBT falsification battery for pytest-dev__pytest-6202 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_getmodpath`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``native_decide``
and no new ``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND
it does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate over one input
binder). A dotted path is assembled from a list of enclosing scope names,
gathered inner-to-outer:

  problem_spec_getmodpath (parts : List String) (result : String) : Prop
    result = String.intercalate "." parts.reverse   -- THE load-bearing clause

The pinned behaviour: the names are taken in REVERSE (outer-to-inner) order and
joined into one string with ``.`` as the separator, and the result is EXACTLY
that join — every supplied name appears verbatim, in order, with a single ``.``
between consecutive names and nothing added, removed, or rewritten. In
particular a name that itself contains punctuation (brackets, dots) is carried
through unaltered. There is no opaque answer key to echo: the post-image is a
term built only from the input ``parts`` (spec_guide directive 8).

The clause has three independent structural commitments a rival can violate:
  (C-rewrite) no per-character substitution is applied to the join — the exact
              defect the issue reports (a leftover post-processing rewrite that
              collapses a ``.`` immediately followed by ``[`` into ``[``);
  (C-sep)     consecutive names are separated by ``.`` (not concatenated bare);
  (C-order)   the names are joined in REVERSED order, not the gathered order.

ADVERSARIAL READ of the nagini classes on this carrier (see the accounting block
at the bottom for the full case-by-case correspondence):

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    ``parts`` is an immutable ``List String`` with no heap footprint, no
    half-permission to overwrite, no aliasing to exploit. The nagini sibling
    carries NO frame-mutation rival either (its own note records the input is an
    immutable ``PSeq`` value with no ``Acc(.,1/2)`` predicate), so there is
    nothing to port and no substitute is fabricated. See ``assessment``.

  * TERMINATION / NON-TERMINATION — VACUOUS. The nagini sibling's
    ``weak-nonterm`` rival attacks a ``MustTerminate`` precondition under
    Nagini's partial-correctness semantics: a divergent loop makes every
    postcondition hold vacuously unless a termination obligation forbids it. On
    this backend every ``def`` is total by construction (Lean rejects a
    non-terminating definition at elaboration; there is no partial-correctness
    escape and no ``MustTerminate`` binder to model), so the class has no
    expressible instance. Not fabricated. See ``assessment``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The post-image
    ``String.intercalate "." parts.reverse`` is a function of the input, not an
    axiomatized oracle; the ``axioms`` region declares no ``opaque``/``axiom``,
    so there is nothing an impl could echo without doing the work. In its place
    the battery carries honest POSITIVE CONTROLS: the cheapest admissible impl,
    plus two reshapes the kernel does NOT consider definitionally equal to the
    frozen one (so each must genuinely re-prove the obligation).

  * PARTIAL-DOMAIN / VALUE — the real attack surface, ported directly. Rivals
    that agree with gold on the ``.``-``[``-boundary-free / single-name
    sub-domain but diverge on a name producing a ``.[`` boundary (the F2P
    witness), plus rivals that drop the separator or the reversal.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``intro parts; …; rfl`` is tuned to the
frozen ``Id.run do … return String.intercalate "." parts`` — so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet proving the rival CONTRADICTS the spec at one concrete
input. Each was checked with two real ``lake env lean`` builds to ELABORATE
against its rival and to FAIL against the frozen solution (so it discriminates
rather than asserting a tautology). ``String.intercalate`` and structural
``List Char`` recursion both kernel-reduce, so the snippets ``unfold`` the spec +
impl and ``decide`` a concrete ``String`` (in)equality at literal name lists;
against gold the same ``decide`` faces ``… = String.intercalate "." parts.reverse``
and fails.

A carrier note on the substitution rivals: the pre-patch defect is a
whole-string ``.replace`` step, but Lean's ``String.replace`` is defined by
well-founded recursion and does NOT reduce under ``decide``/``rfl`` (a literal
``"a.[b".replace ".[" "[" = "a[b"`` gets stuck in the kernel). Modeling the
removed step with ``String.replace`` would leave every substitution rival's
witness undecidable. So the substitution is expressed at the equivalent, fully
reducible ``List Char`` level (a small structural ``sub*`` fold over
``s.toList``, rebuilt with ``String.mk``) — the same left-to-right,
non-overlapping ``.[`` → ``[`` rewrite, but on a carrier the kernel evaluates.
This is a faithful re-expression of the removed operation, not a weaker one.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references == []``
(the modeled tail uses only ``String.intercalate`` / ``List.reverse`` / — pre-
patch — a per-character rewrite, all modeled CONCRETELY, none axiomatized), so
there is no axiom-soundness obligation to probe here; that lane is G-AX's. The
nagini sibling's three ``AXIOM_TESTS`` are DROPPED accordingly. ``AXIOM_TESTS``
is therefore empty.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-6202"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full impl-region body; every impl reshape lands entirely inside
# `-- impl-start`/`-- impl-end`.
_IMPL = (
    "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
    "  let mut parts := parts\n"
    "  parts := parts.reverse\n"
    "  return String.intercalate \".\" parts"
)

# The full frozen tactic body (lies wholly inside `-- proof-start`/`-- proof-end`).
# Reject rivals leave this frozen (they are judged by their witness, not by
# whether this script happens to break); only positives that re-prove touch it.
_PROOF = (
    "  intro parts\n"
    "  unfold problem_spec_getmodpath implementation_getmodpath\n"
    "  rfl"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view intact)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness scaffold. The spec is a bare predicate, so a witness states it
# ---- directly at a ground `List String` literal:
# ----   ¬ problem_spec_getmodpath parts (implementation_getmodpath parts)
# ---- Checked in a file whose frozen obligation is elided by the gate, so no
# ---- tactic script can mask the verdict. `String.intercalate` and the `sub*`
# ---- folds reduce, so `decide` settles the `String` (in)equality after unfold.
def _witness(parts_lit: str) -> str:
    return (
        "example : ¬ problem_spec_getmodpath\n"
        f"    {parts_lit}\n"
        "    (implementation_getmodpath\n"
        f"      {parts_lit}) := by\n"
        "  unfold problem_spec_getmodpath implementation_getmodpath\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness / admissibility) — structurally different
    # but CORRECT implementations that MUST verify, else SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_getmodpath` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: drop the `Id.run do`/`let mut` scaffold and
        # return the grounded post-image directly. Definitionally identical, so
        # the frozen `intro parts; unfold …; rfl` still closes (verified with a
        # real build); no proof authoring, no helper lemma, no assumption token.
        "module": _with_impl(
            "def implementation_getmodpath (parts : List String) : String :=\n"
            "  String.intercalate \".\" parts.reverse"),
        "rationale": "honest cheapest implementation: return the GROUNDED "
                     "post-image `String.intercalate \".\" parts.reverse` "
                     "directly (the reverse-then-join shape). It computes the "
                     "same value on every input, so it must satisfy `result = "
                     "String.intercalate \".\" parts.reverse` — else "
                     "SPEC-TOO-STRONG. Proof: after unfolding both defs the two "
                     "sides are definitionally equal, so the frozen `rfl` "
                     "closes (statement byte-identical).",
    },
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different and CORRECT, and — unlike `pos-direct` — NOT
        # definitionally equal to the frozen impl: build the reversal as a
        # `foldl` cons-accumulator instead of calling the reversal op at all.
        # The frozen `rfl` does NOT close this (measured: exit 1 with
        # `Tactic 'rfl' failed`, the two sides are not defeq), so the case has
        # to be RE-PROVEN in the proof region — which is exactly what makes it a
        # real SPEC-TOO-STRONG probe rather than a restatement of the frozen
        # file. `simp` closes it (measured: exit 0) by rewriting the fold to
        # `parts.reverse`; no new axiom/lemma/assumption, statement unchanged.
        #
        # An earlier form of this case reversed via `reverseAux []`. That is the
        # *definitional unfolding* of `List.reverse`, so the frozen `rfl` closed
        # it unchanged: it passed while probing nothing (a "different shape" the
        # kernel cannot tell apart from the frozen one). Replaced for that
        # reason — a positive control has to be able to fail.
        "module": _swap(
            _with_impl(
                "def implementation_getmodpath (parts : List String) : String :=\n"
                "  String.intercalate \".\" (parts.foldl (fun acc p => p :: acc) [])"),
            _PROOF,
            "  intro parts\n"
            "  unfold problem_spec_getmodpath implementation_getmodpath\n"
            "  simp"),
        "rationale": "structurally-different CORRECT reshape that is NOT "
                     "definitionally equal to the frozen impl: the reversal is "
                     "open-coded as a `foldl` cons-accumulator, never calling "
                     "the reversal op. It computes the same value on every "
                     "input, so `result = String.intercalate \".\" "
                     "parts.reverse` still holds and it MUST verify (else "
                     "SPEC-TOO-STRONG). Because the frozen `rfl` fails here "
                     "(the fold and `.reverse` are not defeq), the case "
                     "genuinely re-proves the obligation — `simp` rewrites the "
                     "fold to `parts.reverse` and closes it. Nothing assumed; "
                     "statement byte-identical.",
    },
    {
        "id": "pos-forloop",
        "kind": "soundness",
        "expect": "verify",
        # A second non-defeq correct reshape, in the imperative idiom the
        # spec_guide calls PREFERRED (`Id.run do` + `let mut` + `for … in`):
        # accumulate the names onto a list by consing, which reverses them, then
        # join. This is the shape a faithful imperative skeleton would most
        # plausibly take, and the frozen `rfl` does NOT close it (measured: the
        # goal survives as a `List.foldl`/`ForInStep` term). Proven by
        # `simp [Id.run]` (which reduces the loop's fold to `parts.reverse`)
        # followed by `rfl` for the residual `pure x = x` in `Id`.
        "module": _swap(
            _with_impl(
                "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
                "  let mut acc : List String := []\n"
                "  for p in parts do\n"
                "    acc := p :: acc\n"
                "  return String.intercalate \".\" acc"),
            _PROOF,
            "  intro parts\n"
            "  unfold problem_spec_getmodpath implementation_getmodpath\n"
            "  simp [Id.run]\n"
            "  rfl"),
        "rationale": "CORRECT reshape in the preferred imperative idiom: a "
                     "`for` loop conses each name onto an accumulator (which "
                     "reverses the list), then joins with `.`. Same value on "
                     "every input, so it must verify (else SPEC-TOO-STRONG). "
                     "Not definitionally equal to the frozen impl — the frozen "
                     "`rfl` leaves the loop's `foldl` term unreduced — so the "
                     "obligation is genuinely re-proven: `simp [Id.run]` "
                     "rewrites the loop to `parts.reverse` and `rfl` discharges "
                     "the residual `pure`. Nothing assumed; statement "
                     "byte-identical.",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen `correct_getmodpath` carries NO precondition hypothesis
        # (the `∀ parts` is unguarded — the behavior is total), so the nagini
        # precondition-admission probe has no binder to attack. Honest analogue:
        # discharge the spec predicate by `decide` at the F2P collection witness
        # (a two-name list whose inner name contains a `.[` boundary, joining to
        # the F2P-asserted path), inside the proof region, alongside the frozen
        # obligation. If that ground instance could not be discharged the modeled
        # behavior would be unsatisfiable at exactly the shape the F2P exercises
        # (the analogue of PRECOND-TOO-STRONG). Only impl+proof regions change;
        # the theorem STATEMENT is byte-identical; nothing is assumed.
        #
        # The ground `have` pins the CONCRETE result string, not merely the spec
        # relation. An earlier form asserted `problem_spec_getmodpath L
        # (implementation_getmodpath L)` — a ground instance of the very
        # proposition the surrounding theorem proves for ALL inputs, so it added
        # no information beyond the frozen obligation. Fixing the literal output
        # value instead makes the case say something the obligation alone does
        # not: that on the collection-shaped input the modeled behavior yields
        # exactly the path the F2P asserts, character for character (in
        # particular the `.`-`[` boundary survives intact).
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : implementation_getmodpath [\"testmethod_two[.[]\", \"TestY\"]\n"
            "      = \"TestY.testmethod_two[.[]\" := by\n"
            "    unfold implementation_getmodpath\n"
            "    decide\n"
            "  intro parts\n"
            "  unfold problem_spec_getmodpath implementation_getmodpath\n"
            "  rfl"),
        "rationale": "admissibility: `decide` pins the CONCRETE output at a "
                     "representative collection-shaped input (a two-name list "
                     "whose inner name contains a `.[` boundary) — the modeled "
                     "behavior returns exactly the path the F2P asserts, with "
                     "that boundary carried through verbatim — and then the "
                     "frozen obligation is closed verbatim by `rfl`. Verifies "
                     "(else the behavior is unsatisfiable at the normal input, "
                     "or disagrees with the asserted path there — the analogue "
                     "of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, the `correct_` statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P tests. The witnesses probe
    # FIVE distinct input tuples, varying the number of names (the `parts`
    # length), the presence of a `.[` boundary, the ORDER of two distinct names,
    # and whether one of the names is empty.
    # =====================================================================
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-patch behaviour: after building the reversed dot-join,
        # apply the removed left-to-right, non-overlapping `.[` -> `[` rewrite
        # (all occurrences). Expressed at the reducible `List Char` level (see
        # the WITNESSES note) — the exact substitution, on a carrier the kernel
        # evaluates.
        "module": _with_impl(
            "def subAll : List Char → List Char\n"
            "  | '.' :: '[' :: rest => '[' :: subAll rest\n"
            "  | c :: rest => c :: subAll rest\n"
            "  | [] => []\n"
            "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
            "  let mut parts := parts\n"
            "  parts := parts.reverse\n"
            "  let s := String.intercalate \".\" parts\n"
            "  return String.mk (subAll s.toList)"),
        "refinement": "this IS the faithful pre-patch implementation: it "
                      "re-applies the exact post-join substitution the gold "
                      "patch DELETES. Its real-code counterpart is the "
                      "base_commit code, which the F2P (test_example_items1) "
                      "fails: the parametrised item's path assembles to the "
                      "string the test asserts verbatim, but the substitution "
                      "collapses its `.[` boundary, yielding the corrupted path "
                      "the issue reports. So a verifying weak-prepatch would be "
                      "a true verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `result = String.intercalate \".\" "
                     "parts.reverse` (C-rewrite): the rival returns the join "
                     "with the substitution applied, which differs from the "
                     "plain join exactly when a `.[` boundary is present. "
                     "Refuted at a two-name list whose reversed join contains "
                     "`.[` (the join is one code point longer than the rival's "
                     "output). partial-domain: agrees with gold on any "
                     "`.[`-free input.",
        "witness": _witness("[\"[b\", \"a\"]"),
    },
    {
        "id": "weak-firsthit",
        "kind": "uniqueness",
        "expect": "reject",
        # A subtler partial-domain bug: collapse ONLY the FIRST `.[` occurrence,
        # then copy the rest verbatim (a one-shot rewrite). A near-miss of
        # weak-prepatch — the two agree on any join with at most one `.[`, so
        # this rival carries its own DISTINGUISHING witness (a join with TWO
        # `.[` boundaries) rather than sharing weak-prepatch's single-boundary
        # input.
        "module": _with_impl(
            "def subFirst : List Char → List Char\n"
            "  | '.' :: '[' :: rest => '[' :: rest\n"
            "  | c :: rest => c :: subFirst rest\n"
            "  | [] => []\n"
            "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
            "  let mut parts := parts\n"
            "  parts := parts.reverse\n"
            "  let s := String.intercalate \".\" parts\n"
            "  return String.mk (subFirst s.toList)"),
        "refinement": "a subtler bug than the original: a one-shot substitution "
                      "collapsing only the FIRST `.[` boundary. Its faithful "
                      "real patch (e.g. a single-count replace) still fails the "
                      "F2P assertion: the parametrised item's assembled path "
                      "contains a `.[` boundary that the single replacement "
                      "collapses, producing the corrupted path. Would be a "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `result = String.intercalate \".\" "
                     "parts.reverse` (C-rewrite): on any input whose reversed "
                     "join contains a `.[`, the returned string is shorter by "
                     "one code point than the plain join. NEAR-MISS of "
                     "weak-prepatch — the two coincide when the join has at "
                     "most one `.[`, so this rival is refuted at a THREE-name "
                     "list whose reversed join contains TWO `.[` boundaries "
                     "(weak-prepatch collapses both, this rival only the first, "
                     "and both differ from gold there — a distinct probe point).",
        "witness": _witness("[\"[\", \"[b\", \"a\"]"),
    },
    {
        "id": "weak-nosep",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `.` separator: return the bare concatenation of the reversed
        # names. For a single name it coincides with gold, but for any multi-name
        # input it omits the separators.
        "module": _with_impl(
            "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
            "  let mut parts := parts\n"
            "  parts := parts.reverse\n"
            "  return String.join parts"),
        "refinement": "joins the names with NO separator instead of `.`. Its "
                      "faithful real patch fails the F2P PASS-line assertions "
                      "too: a two-name path the test asserts as `A.b` would come "
                      "back as `Ab`, so the reported module path is wrong. A "
                      "verifying weak-nosep would be a "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `result = String.intercalate \".\" "
                     "parts.reverse` (C-sep): `String.intercalate \".\"` inserts "
                     "a `.` between consecutive names; the bare concatenation "
                     "omits it, so for any multi-name input the result differs "
                     "(shorter by the number of separators). Refuted at a "
                     "two-name list (no `.[` present, so the separator — not the "
                     "rewrite — is the discriminator). partial-domain: coincides "
                     "with gold on a single-name input.",
        "witness": _witness("[\"b\", \"a\"]"),
    },
    {
        "id": "weak-noreverse",
        "kind": "uniqueness",
        "expect": "reject",
        # Join in the GATHERED (inner-to-outer) order — omit the reversal. For a
        # single name it coincides with gold, but for any multi-name input the
        # names come out in the wrong order.
        "module": _with_impl(
            "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
            "  return String.intercalate \".\" parts"),
        "refinement": "joins the names in the order they were gathered "
                      "(inner-to-outer) instead of reversed (outer-to-inner). "
                      "Its faithful real patch fails the F2P PASS-line "
                      "assertions: a path the test asserts as `Outer.inner` "
                      "would be reported as `inner.Outer`, the reversed dotted "
                      "path — wrong. A verifying weak-noreverse would be a "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `result = String.intercalate \".\" "
                     "parts.reverse` (C-order): the rival joins `parts` "
                     "directly, which equals the reversed join only when the "
                     "order is symmetric (e.g. a single name or a palindromic "
                     "list). Refuted at a two-name list with distinct names, "
                     "where the two orders disagree. partial-domain: coincides "
                     "with gold on a single-name input.",
        "witness": _witness("[\"a\", \"b\"]"),
    },
    {
        "id": "weak-dropempty",
        "kind": "uniqueness",
        "expect": "reject",
        # Filter out empty names before joining — the shape a "defensive"
        # implementation reaches for to avoid a doubled separator. It agrees
        # with gold on every input whose names are all non-empty (which is EVERY
        # input the other four witnesses probe, all of whose literals are
        # non-empty), so this attacks a sub-domain the rest of the battery
        # leaves entirely open: a name that is the empty string. The clause says
        # every supplied name appears, so an empty name must still contribute
        # its (empty) text and its separator.
        "module": _with_impl(
            "def implementation_getmodpath (parts : List String) : String := Id.run do\n"
            "  let mut parts := parts\n"
            "  parts := parts.reverse\n"
            "  return String.intercalate \".\" (parts.filter (fun p => p != \"\"))"),
        "refinement": "silently DROPS empty names instead of joining them. Its "
                      "faithful real counterpart reports a path with one fewer "
                      "separator than the assembled scope list has boundaries, "
                      "so any collected item with an empty scope name is "
                      "reported under the wrong dotted path — the PASS-line "
                      "path assertions and the F2P alike compare the reported "
                      "path verbatim. A verifying weak-dropempty would be a "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `result = String.intercalate \".\" "
                     "parts.reverse` (the every-name-appears commitment): "
                     "`String.intercalate` places a separator between EVERY "
                     "pair of consecutive names, including a pair where one is "
                     "empty, so dropping empties loses a `.`. Refuted at a "
                     "two-name list whose outer name is empty (the join is "
                     "`\".a\"`, the rival returns `\"a\"`). partial-domain, and "
                     "the sub-domain no other rival reaches: it agrees with "
                     "gold on every all-names-non-empty input, i.e. on all four "
                     "of the other witnesses' inputs.",
        "witness": _witness("[\"\", \"a\"]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus a 3-case AXIOM lane.
# This bundle models the SAME purely-functional core (the result-assembly tail:
# reverse the gathered names, then dot-join, with nothing rewritten), so the
# port is close to case-parity. Every sibling case is recorded below.
#
#   sibling case          -> here
#   -----------------------------------------------------------------
#   pos-direct            -> pos-direct                 PORTED
#   pos-reshape           -> pos-reshape                PORTED (re-authored; see below)
#   (new)                 -> pos-forloop                ADDED (2nd non-defeq positive)
#   admiss-f2p            -> admiss-f2p                 PORTED (strengthened; see below)
#   weak-prepatch         -> weak-prepatch              PORTED
#   weak-firsthit         -> weak-firsthit              PORTED
#   weak-nosep            -> weak-nosep                 PORTED
#   weak-nonterm          -> (none)                     VACUOUS (total by construction)
#   (new)                 -> weak-noreverse             ADDED (attacks C-order binder)
#   (new)                 -> weak-dropempty             ADDED (empty-name sub-domain)
#   AXIOM_TESTS (3)       -> (none)                     DROPPED (G-AX lane)
#
# PORTED (positives): pos-direct returns the grounded post-image directly (the
#   `reverse` then dot-join shape — the nagini `return join_dot(parts)`); the
#   frozen `rfl` closes it, which is honest for a case whose whole point is that
#   the cheapest impl is admissible.
#
#   pos-reshape and pos-forloop are the cases that carry the SPEC-TOO-STRONG
#   weight, and both are deliberately NOT definitionally equal to the frozen
#   impl: the frozen `rfl` fails on each (measured), so each genuinely re-proves
#   the obligation. pos-reshape open-codes the reversal as a `foldl` cons
#   accumulator (closed by `simp`); pos-forloop uses the preferred imperative
#   `Id.run do` + `let mut` + `for` idiom (closed by `simp [Id.run]; rfl`).
#
#   pos-reshape was RE-AUTHORED during audit. Its previous form reversed via
#   `reverseAux []`, which is the definitional unfolding of `List.reverse` — the
#   frozen `rfl` closed it untouched, so the "structurally different shape" was
#   one the kernel could not distinguish from the frozen impl and the case could
#   not have failed for any spec reason. A positive control that cannot fail
#   certifies nothing, so it was replaced by a reshape the kernel really does
#   see as different, and a second such reshape (pos-forloop) was added.
#
#   admiss-f2p was STRENGTHENED during audit. Its previous ground `have`
#   asserted `problem_spec_getmodpath L (implementation_getmodpath L)` at a
#   literal L — a ground instance of exactly the proposition the enclosing
#   theorem already proves for all inputs, so it restated the obligation rather
#   than adding a claim. It now pins the concrete output STRING at the
#   collection-shaped input, which the obligation alone does not give.
# PORTED (substitution rivals): weak-prepatch re-applies the removed all-
#   occurrence `.[` -> `[` rewrite; weak-firsthit the one-shot first-occurrence
#   variant. Both are expressed at the reducible `List Char` level because
#   Lean's `String.replace` does not kernel-reduce under `decide` (see the
#   WITNESSES note) — a faithful re-expression of the same rewrite, not a weaker
#   one. weak-firsthit is a NEAR-MISS of weak-prepatch (they coincide on joins
#   with ≤1 `.[`), so it carries its OWN distinguishing witness at a join with
#   TWO `.[` boundaries rather than sharing weak-prepatch's input.
# PORTED (separator rival): weak-nosep drops the `.` separator (nagini
#   `weak-nosep`), refuted on a multi-name input.
# VACUOUS (termination): the nagini `weak-nonterm` rival exploits Nagini's
#   partial-correctness semantics — a reachable infinite loop makes every
#   postcondition hold vacuously unless a `MustTerminate` obligation forbids it.
#   There is no such escape here, so the class has no rival to port. Measured
#   during audit rather than argued, because the honest statement is narrower
#   than "every `def` is total by construction":
#     * a plain recursive non-terminating `def` is rejected at ELABORATION
#       (`fail to show termination`), so it cannot even be a variant: exit 1 for
#       a reason that is not about the spec;
#     * `partial def` IS accepted by this carrier (so "Lean rejects a
#       non-terminating definition" is too strong as stated). A `partial`
#       divergent impl returning the wrong value still FAILS the obligation
#       (measured, exit 1): the theorem quantifies over all `parts` and demands
#       an equality of VALUES, and `partial` gives the constant no reduction
#       behavior to satisfy it with — there is no vacuity clause to exploit,
#       because the obligation is not conditioned on termination.
#     * a `partial` DIVERGENT PREFIX in front of gold's body verifies (measured,
#       exit 0) — but only because Lean is referentially transparent and the
#       unused `let _` is dropped, i.e. the variant is not actually a diverging
#       program. That is a modeling limit of the carrier, not a spec hole, and
#       it is NOT the velvet `partial`-semantics finding
#       (the corpus-wide termination-semantics finding), whose scope is explicitly velvet-only.
#   So: inexpressible here, on measured grounds, not for lack of effort.
# ADDED (order rival): weak-noreverse joins the names in the gathered order
#   instead of reversed. The nagini spec pins `Result() == join_dot(parts)` where
#   `parts` was already reversed in the caller, so the reversal is not a separate
#   binder there; here the spec pins `parts.reverse` explicitly, making the
#   ORDER a load-bearing structural commitment (C-order) that no other rival
#   attacks. Added so that commitment is defended.
# ADDED (empty-name rival): weak-dropempty filters empty names out before
#   joining. Every other witness in the battery uses only non-empty name
#   literals, so before this case the entire empty-name sub-domain was
#   undefended — a rival agreeing with gold on all non-empty inputs would have
#   met no probe. The clause commits to every supplied name appearing with a
#   single `.` between consecutive names, empty ones included, so this is a real
#   commitment and it is now attacked.
# DROPPED (AXIOM_TESTS): the sibling's three axiom-soundness/containment probes
#   (deep models of `str.join` and `str.replace` vs the real CPython callees)
#   belong to G-AX, which the G-PBT spec lane ignores. meta.json records
#   `axioms == []` and `deep_model_references == []` (the tail's ops are modeled
#   CONCRETELY, not axiomatized), so there is nothing to probe and the gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single input binder `parts` is varied across the
# five reject witnesses by length (two- and three-name lists), by content (with
# and without a `.[` boundary), and by whether a name is EMPTY:
#   ["[b","a"]  /  ["[","[b","a"]  /  ["b","a"]  /  ["a","b"]  /  ["","a"]
# — five DISTINCT input points, each chosen so the rival it refutes and gold
# actually disagree there (not two spellings of one point: the third and fourth
# share a length and a `.[`-free shape but differ in ORDER, which is precisely
# what separates weak-nosep from weak-noreverse). The clause's structural
# commitments are each attacked: C-rewrite by weak-prepatch + weak-firsthit,
# C-sep by weak-nosep, C-order by weak-noreverse, and every-name-appears by
# weak-dropempty.
#
# SPEC-TOO-WEAK probes run during audit that the spec correctly REJECTED (no
# hole found; recorded so the next auditor does not repeat them): filtering
# empty names (kept as weak-dropempty), collapsing `..` -> `.` after the join,
# stripping a trailing `.`, and reversing only when the list is longer than two
# names (an order bug that hides on the short F2P-shaped inputs). Each failed
# with a semantic unsolved goal against the frozen spec, not a tactic error.
AXIOM_TESTS = []
