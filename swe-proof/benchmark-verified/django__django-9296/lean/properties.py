# properties.py — G-PBT falsification battery for django__django-9296 (lean).
# Ported from the nagini sibling battery; re-expressed against this backend's
# carrier. NOT a Lean module — a record of adversarial cases the spec-lane gate
# executes, each editing ONLY the impl region (and, for the positive, the proof
# body) of the frozen Solution.lean, so `same_spec` holds by construction.
#
# Defended surface (this backend's model):
#   paginatorPages (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
#       -> List (List α)          (the ordered per-page slices produced by a walk)
#   Precondition (theorem hypothesis): 1 ≤ perPage.
#   The postcondition is a SINGLE top-level equality clause:
#     result = (pageNumbers objectList.length perPage orphans allowEmpty).map
#                (fun n => pageSlice objectList perPage orphans n)
#   which pins the result FULLY — its length is the page count and its k-th
#   entry is the slice for page k+1 — over four input binders:
#     objectList, perPage, orphans, allowEmpty.
#
# CARRIER NOTE — this bundle models MORE than the nagini sibling, and less of it
# is opaque. Nagini abstracts the per-page accessor behind an opaque pure
# `page_lookup(n)` and ranges over an ARBITRARY `List[int]` page-number run, so
# its rivals turn on count / order / value of that opaque map. Here the page
# count, the 1-based page numbering, and the per-page slice are each concrete
# pure functions of (objectList, perPage, orphans, allowEmpty) — fully
# transparent — and the page numbers are COMPUTED (`[1, …, pageCount]`), not a
# free input. Two consequences:
#   * every witness is `decide`-able at small literal inputs (no opaque term to
#     condition on), so no carrier-conditioning is needed here;
#   * nagini's `index-not-value` rival (page by the loop counter vs. the
#     page-number VALUE) has no faithful counterpart: the page numbers are not a
#     free input, so "counter" and "value" do not diverge on this carrier. This is
#     DEMONSTRATED, not asserted: `pageNumbers c p o e = List.range' 1 (pageCount
#     …)`, whose element at 0-based position i is literally `i + 1`, so paging by
#     the 1-based loop position and paging by the page-number value are the same
#     function of the input — checked equal on every (length ≤ 13, perPage ≤ 7,
#     orphans ≤ 8, allowEmpty) point, 0 divergences. A ported index-not-value
#     rival would therefore be observably IDENTICAL to gold: vacuous, and
#     unwitnessable by construction. The element-wise VALUE clause it attacks is
#     instead attacked by `const-page` and by `zero-based` (which shifts the
#     numbering by one and DOES diverge).
#   * the orphans / allowEmpty behaviour is modeled here but is entirely inside
#     nagini's opaque `page_lookup`; the `ignore-orphans` and `ignore-empty`
#     rivals below are therefore FRESH (no nagini counterpart) and are required
#     to vary those two binders. Chasing nagini's case list would leave them
#     unattacked.
#
# AUDIT (independent, post-port): attack A found the spec view, the pure
# helpers, and the `theorem correct_paginatorPages` STATEMENT byte-identical to
# the frozen file in all cases. Attack B rebuilt all reject witnesses: each
# elaborates against its rival (exit 0) and fails against the frozen solution
# (exit 1) with `Tactic 'decide' proved that the proposition ¬(...)` — i.e. the
# kernel EVALUATED the concrete claim and found gold satisfies the spec there,
# which is the plain-evaluation signature rather than a syntactic mismatch.
# Attack B′ ran the forgery pair anyway: flipping each witness's claim (dropping
# the `¬`) builds against gold at exit 0, so gold's exit code tracks the claim
# and no rejection here is hollow. Attack C re-derived every rival's divergence
# from gold by exhaustive enumeration over all (length ≤ 13, perPage ≤ 7,
# orphans ≤ 8, allowEmpty) points: all eight pre-existing rivals differ from
# gold on 63–1701 of 1764 points, so none is a mere reshape, and the three
# orphan rivals are pairwise distinct (870 differing points each). Attacks D and
# E found no spec hole: four new wrong impls (an off-by-one page stride, a
# hardwired page size in the numbering, dropping the LAST page, duplicating
# every page) were all rejected and all witnessable, and two new correct
# reshapes (a `List.range`-indexed map, a `foldr` that prepends) both verify.
# Two gaps WERE found and are fixed below: the missing admissibility lane
# (`admiss-f2p-ground`) and the unattacked `perPage` binder
# (`perpage-count-only`).
#
# VACUOUS / OMITTED LANES (stated, not fabricated):
#   * FRAME-MUTATION: nagini's two mandatory frame-mut rivals (a write-back / an
#     append into the read-only Acc(...,1/2) page-number input) have NO
#     counterpart here. Lean is referentially transparent — no aliasing, no
#     fractional permission — so there is no "write to an input" a rival could
#     perform. Omitted, legitimately.
#   * ADMISSIBILITY: nagini's admiss case exercises the half-permission via a
#     self-call. This carrier has no permission, so that EXACT case has no
#     counterpart — but the LANE does, and an earlier revision of this file
#     dropped it on the argument that `1 ≤ perPage` "cannot be unsatisfiable".
#     That argument is wrong about what the lane tests: on a total carrier the
#     analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
#     exactly an F2P-shaped input — the spec's two sides failing to meet on the
#     concrete collection the real test observes — which no amount of reasoning
#     about the hypothesis in isolation settles, because the postcondition is an
#     equality between two computations of the four binders, not a claim about
#     `perPage`. The lane is therefore LANDED below as `admiss-f2p-ground`:
#     it discharges the postcondition at the F2P-shaped input by evaluation, as a
#     `have`, before closing the frozen obligation verbatim. (Measured: exit 0.)
#     Recorded alongside it, because it is true and was measured but is NOT the
#     reason to omit anything: the frozen proof never uses `hperPage`, and the
#     obligation holds even OUTSIDE the precondition (at perPage = 0 the
#     postcondition still elaborates by `decide` — Lean's `n / 0 = 0` makes the
#     page count 0 and both sides `[]`; re-measured this audit, exit 0). So the
#     precondition is documentation of the intended domain rather than a
#     load-bearing guard — which is a fact about `hperPage`, not a licence to
#     leave the lane empty.
#   * AXIOM_TESTS: the axiom lane is G-AX's job; this gate ignores it. The model
#     has no `opaque` callee and no consumed axiom (the three helpers are deep
#     A-reference models), so there is nothing to test.
#   * DIVERGENCE: recorded as a KNOWN HOLE, not as a vacuous class, and the
#     distinction is measured rather than argued. This bundle sets no
#     `loom.semantics.termination` (that option is a velvet-only requirement;
#     the lean backend elaborates plain Lean), so a diverging rival has to be
#     expressed in Lean's own terms, and both available spellings were built:
#       - a self-recursive `def` with no decreasing measure fails at
#         `fail to show termination for` — the equation compiler refuses the
#         DEFINITION, so the rival never reaches the spec and its rejection
#         attests to the elaborator, not to the postcondition;
#       - a `partial def` (the spelling that DOES elaborate a non-terminating
#         function, via a helper so the `Inhabited` instance resolves) is
#         accepted and is scope-clean, but `partial` makes the body opaque to
#         the kernel: the witness's `decide` cannot reduce it, so the witness
#         FAILS against the rival (measured exit 1,
#         `Tactic 'decide' failed for proposition`). The half that must succeed
#         does not, so the case would be recorded `witness-unproven` —
#         inconclusive, which is a gate ERROR rather than a pass.
#     So there is no shippable diverging rival here: the terminating spelling is
#     rejected before the spec is consulted and the non-terminating one is
#     unwitnessable by construction. That is a hole in what this battery can
#     reach, stated as such.
#
# WITNESS — every reject case carries a Lean `example` refuting the rival at ONE
# concrete `decide`-able input. It is checked in a file with the proof obligation
# stripped, and must (1) elaborate against the rival and (2) FAIL against the
# frozen solution, so it is a real discriminator and not a tautology. All witness
# inputs are short `Nat` literals so `decide` reduces the `Id.run do` / `for`
# impl without any opaque term.
from pathlib import Path

INSTANCE = "django__django-9296"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Every reject variant _swap()s a substring lying ENTIRELY
# inside the impl region (so the spec view — and same_spec — is untouched, and
# the frozen proof is left intact: its rejection is attested by the witness, not
# by the tactic breakage a reshaped impl would otherwise cause). The soundness
# positive additionally rewrites the proof TACTIC body, keeping the
# `theorem correct_paginatorPages` STATEMENT byte-identical.
# ---------------------------------------------------------------------------

# The full frozen impl def (everything the impl markers enclose).
_IMPL = """\
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) := Id.run do
  let mut pages : List (List α) := []
  for n in pageNumbers objectList.length perPage orphans allowEmpty do
    pages := pages ++ [pageSlice objectList perPage orphans n]
  return pages"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof tactic body of `correct_paginatorPages` (only the soundness
# positive touches this).
_PROOF = """\
  unfold problem_spec_paginatorPages implementation_paginatorPages
  have h := paginatorPages_forIn objectList perPage orphans
    (pageNumbers objectList.length perPage orphans allowEmpty) []
  simp only [Id.run, bind, pure] at h ⊢
  rw [h]
  simp"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# Impl-region substrings each reject rival edits. Each lies fully inside _IMPL
# and is unique in the whole file (the `do` suffix / the `pages := pages ++`
# prefix keep them out of the spec's `fun n => pageSlice …` and the proof's
# `have h := … allowEmpty) []`).
_FOR_LINE = "for n in pageNumbers objectList.length perPage orphans allowEmpty do"
_BODY_LINE = "pages := pages ++ [pageSlice objectList perPage orphans n]"
_LOOP_BLOCK = _FOR_LINE + "\n    " + _BODY_LINE

for _anchor in (_FOR_LINE, _BODY_LINE, _LOOP_BLOCK):
    assert _BASE.count(_anchor) == 1, f"anchor not unique: {_anchor!r}"


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE — must VERIFY (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------

# pos-functional: a structurally-different but behaviourally-identical impl. It
# builds the result DIRECTLY as the pure `List.map` the spec itself names — no
# `Id.run do`, no `let mut`, no `for` accumulation — and is reproven with a
# two-line `rfl`. The theorem STATEMENT is byte-identical; only the tactic body
# changes.
#
# HONESTY NOTE (why this positive is kept but is NOT the load-bearing one): this
# impl is literally the spec's right-hand side, so it is DEFINITIONALLY equal to
# it and a bare `rfl` — with no `unfold` of the spec at all — discharges the
# obligation. Measured: dropping the `unfold` line still elaborates (exit 0). A
# positive that closes by definitional unfolding exercises the spec's SHAPE and
# nothing about its CONTENT: any spec whose RHS were written differently but
# equivalently would reject it, and any wrong impl would too, so it cannot
# distinguish a spec that is too strong from one that is merely differently
# phrased. It is retained as a cheap shape control, and the two positives below
# — which are NOT definitionally equal to the spec RHS and need a real induction
# — are what actually defend against SPEC-TOO-STRONG.
_POS_IMPL = """\
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) :=
  (pageNumbers objectList.length perPage orphans allowEmpty).map
    (fun n => pageSlice objectList perPage orphans n)"""

_POS_PROOF = """\
  unfold problem_spec_paginatorPages implementation_paginatorPages
  rfl"""

_POS = _swap(_swap(_BASE, _IMPL, _POS_IMPL), _PROOF, _POS_PROOF)


# pos-foldl: a genuinely NON-definitional correct reshape. The result is
# accumulated with `List.foldl` over the page numbers, appending each slice — a
# left fold, not a map, so it is NOT defeq to the spec's RHS and `rfl` alone does
# NOT close it (measured: the `rfl`-only proof fails, exit 1). Closing it needs
# the accumulator generalization proven inline. This is the positive that
# actually defends the equality clause against SPEC-TOO-STRONG.
_POS2_IMPL = """\
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) :=
  (pageNumbers objectList.length perPage orphans allowEmpty).foldl
    (fun acc n => acc ++ [pageSlice objectList perPage orphans n]) []"""

_POS2_PROOF = """\
  unfold problem_spec_paginatorPages implementation_paginatorPages
  have key : ∀ (xs : List Nat) (acc : List (List α)),
      xs.foldl (fun acc n => acc ++ [pageSlice objectList perPage orphans n]) acc
        = acc ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
    intro xs
    induction xs with
    | nil => intro acc; simp
    | cons a as ih => intro acc; simp [ih]
  simpa using key (pageNumbers objectList.length perPage orphans allowEmpty) []"""

_POS2 = _swap(_swap(_BASE, _IMPL, _POS2_IMPL), _PROOF, _POS2_PROOF)


# pos-reverse-walk: a correct reshape that walks the page numbers in the OPPOSITE
# direction and PREPENDS, keeping the `Id.run do` / `for` shape of the frozen
# impl. Two order reversals cancel, so it is behaviourally identical to gold
# while being structurally the mirror image — and it is the direct correct
# counterpart of the `order-reversed` rival, which is what makes the spec's
# ordering clause demonstrably a statement about the OUTPUT order rather than
# about the traversal direction. Not defeq to the spec RHS (measured: `rfl`-only
# fails, exit 1); needs its own accumulator induction.
_POS3_IMPL = """\
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) := Id.run do
  let mut pages : List (List α) := []
  for n in (pageNumbers objectList.length perPage orphans allowEmpty).reverse do
    pages := pageSlice objectList perPage orphans n :: pages
  return pages"""

_POS3_PROOF = """\
  unfold problem_spec_paginatorPages implementation_paginatorPages
  have key : ∀ (xs : List Nat) (init : List (List α)),
      Id.run (forIn xs init (fun n r =>
        (do pure PUnit.unit;
            pure (ForInStep.yield (pageSlice objectList perPage orphans n :: r)))))
        = (xs.map (fun n => pageSlice objectList perPage orphans n)).reverse ++ init := by
    intro xs
    induction xs with
    | nil => intro init; simp [Id.run, pure, List.forIn_nil]
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp
  have h := key (pageNumbers objectList.length perPage orphans allowEmpty).reverse []
  simp only [Id.run, bind, pure] at h ⊢
  rw [h]
  simp"""

_POS3 = _swap(_swap(_BASE, _IMPL, _POS3_IMPL), _PROOF, _POS3_PROOF)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation must be SATISFIABLE at an F2P-shaped input
# (else PRECOND-TOO-STRONG). The frozen impl and proof are kept verbatim; the
# case only PREPENDS a ground instance to the tactic body, so the theorem
# statement is byte-identical and nothing is assumed (no new declaration, no
# axiom, no sorry). The postcondition is discharged at the F2P-shaped
# collection by evaluation — `decide` reduces both sides — and only then is the
# frozen obligation closed as before.
# ---------------------------------------------------------------------------
_ADMISS_PROOF = (
    "  have _ground : problem_spec_paginatorPages ([1, 2, 3] : List Nat) 2 0 true\n"
    "      (implementation_paginatorPages ([1, 2, 3] : List Nat) 2 0 true) := by\n"
    "    unfold problem_spec_paginatorPages implementation_paginatorPages\n"
    "    decide\n"
) + _PROOF

_ADMISS = _swap(_BASE, _PROOF, _ADMISS_PROOF)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each edits ONLY the impl region; the frozen proof body is left intact.
# ---------------------------------------------------------------------------

# drop-first: skip the first page number, so the leading slice is omitted.
# Wrong wherever there is at least ONE page — including every single-page input,
# where it returns [] instead of the one page. It coincides with the spec ONLY on
# the zero-page sub-domain (empty collection with the empty-page flag off), where
# both yield []. Attacks the count/leading-element half of the equality.
_R_DROP = _swap(
    _BASE, _FOR_LINE,
    "for n in (pageNumbers objectList.length perPage orphans allowEmpty).drop 1 do")

# order-reversed: walk the page numbers back-to-front, reversing the produced
# order. Same length, same multiset of slices, but the ordering is wrong for any
# collection with ≥ 2 distinct pages. Attacks the ordering pinned by the map.
_R_REV = _swap(
    _BASE, _FOR_LINE,
    "for n in (pageNumbers objectList.length perPage orphans allowEmpty).reverse do")

# const-page: emit the FIRST page's slice for every page number instead of that
# page's own slice. Same length and same page numbering, wrong element image.
# This is the value-clause attack (nagini's index-not-value has no faithful
# counterpart on this carrier — see CARRIER NOTE).
_R_CONST = _swap(
    _BASE, _BODY_LINE,
    "pages := pages ++ [pageSlice objectList perPage orphans 1]")

# ignore-orphans: compute both the page numbering and the per-page slices with a
# hardwired orphan allowance of 0, ignoring the `orphans` input. Correct only
# when orphans = 0; wrong wherever a non-zero orphan allowance changes the last
# page's extent or the page count. FRESH rival (no nagini counterpart): varies
# the `orphans` binder, which nagini folds into its opaque page_lookup.
_R_ORPHANS = _swap(
    _BASE, _LOOP_BLOCK,
    "for n in pageNumbers objectList.length perPage 0 allowEmpty do\n"
    "    pages := pages ++ [pageSlice objectList perPage 0 n]")

# ignore-empty: compute the page numbering with a hardwired `allowEmpty = true`,
# ignoring the `allowEmpty` input. Correct whenever allowEmpty = true or the
# collection is non-empty; wrong for the empty-collection / allowEmpty = false
# case, where the spec demands zero pages but the rival yields one (empty) page.
# FRESH rival (no nagini counterpart): varies the `allowEmpty` binder.
_R_EMPTY = _swap(
    _BASE, _FOR_LINE,
    "for n in pageNumbers objectList.length perPage orphans true do")

# zero-based: keep the page COUNT and the traversal exactly right, but ask each
# step for the slice of page `n - 1` instead of page `n` — i.e. treat the
# numbering as 0-based. The page count and the result LENGTH are unchanged, so
# neither the count clause nor the ordering clause can catch it; only the
# 1-based-numbering content of the element-wise clause does. Added by audit: the
# battery's other value-clause rival (`const-page`) collapses every entry to the
# same slice, which a spec pinning only "all entries equal page 1" would also
# reject, so the specifically 1-BASED half of the clause was unattacked. Note
# `n - 1` is Nat-truncated, so page 1 asks for page 0 and (bottom = 0 * perPage)
# duplicates page 1's window — the shift is observable from the second page on.
_R_ZEROBASED = _swap(
    _BASE, _BODY_LINE,
    "pages := pages ++ [pageSlice objectList perPage orphans (n - 1)]")

# orphans-slice-only: honour the orphan allowance in the page NUMBERING but not
# in the per-page slice. Added by audit: `ignore-orphans` drops the allowance from
# BOTH the numbering and the slice at once, so a spec that threaded the allowance
# into only one of the two would still reject it. This rival and the next split
# that conjunction, pinning the allowance in each place independently.
_R_ORPH_SLICE = _swap(
    _BASE, _BODY_LINE,
    "pages := pages ++ [pageSlice objectList perPage 0 n]")

# orphans-count-only: the mirror image — honour the allowance in the per-page
# slice but not in the page numbering, so the collection is split into one page
# too many and the trailing page repeats items already shown.
_R_ORPH_COUNT = _swap(
    _BASE, _FOR_LINE,
    "for n in pageNumbers objectList.length perPage 0 allowEmpty do")

# perpage-count-only: honour the page SIZE when slicing each page but hardwire
# the page NUMBERING to a size of 1, so the collection is cut into one page per
# ITEM while each of those pages still shows a full `perPage`-sized window.
# Added by this audit to close a measured coverage gap: of the four input
# binders, `perPage` was the only one whose value no rival's wrongness depended
# on. Every pre-existing rival is wrong at perPage = 1 (each witness but one
# uses perPage ∈ {1, 2} incidentally, to make some OTHER binder's clause fail),
# so a spec that dropped `perPage` from the page-count computation entirely —
# using the item count in its place — would have been rejected by nothing here.
# This rival is exactly that spec's impl, and it varies the `perPage` binder in
# the only way that matters: by changing the number of pages it induces.
_R_PERPAGE_COUNT = _swap(
    _BASE, _FOR_LINE,
    "for n in pageNumbers objectList.length 1 orphans allowEmpty do")


def _wit(obj, per, orph, empty):
    """A refutation `example`: the spec predicate is FALSE at this concrete input
    for the rival impl. `decide` closes it against the rival; it fails on gold
    (which satisfies the spec everywhere), making it a real discriminator.

    `obj` is a Lean list literal string (e.g. "[1, 2, 3]"); `empty` a Bool
    literal string. Every value is a small `Nat` literal so `decide` reduces the
    `Id.run do` / `for` impl with no opaque term left over."""
    args = f"({obj} : List Nat) {per} {orph} {empty}"
    return (
        f"example : ¬ problem_spec_paginatorPages {args}\n"
        f"    (implementation_paginatorPages {args}) := by\n"
        f"  unfold problem_spec_paginatorPages implementation_paginatorPages\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "a structurally-different correct impl: the result is built as the "
            "pure `List.map` the postcondition itself names (no Id.run/let "
            "mut/for accumulation), and reproven with `rfl` since the impl is now "
            "definitionally the spec's right-hand side. Defends the single "
            "equality clause over all four binders. If it fails => SPEC-TOO-STRONG "
            "(a faithful correct impl rejected). The theorem STATEMENT is "
            "byte-identical; only the tactic body changed."
        ),
    },
    {
        "id": "pos-foldl",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS2,
        "rationale": (
            "the LOAD-BEARING positive. A correct reshape that accumulates the "
            "result with `List.foldl`, appending each page's slice, instead of "
            "mapping. Unlike `pos-functional` this is NOT definitionally equal to "
            "the spec's right-hand side — the `rfl`-only proof was measured to FAIL "
            "against it — so closing it requires the accumulator generalization to "
            "be proven inline, and its success is evidence about the spec's CONTENT "
            "rather than about its syntactic shape. Defends the single equality "
            "clause over all four binders. If it fails => SPEC-TOO-STRONG. The "
            "theorem STATEMENT is byte-identical; only the tactic body changed."
        ),
    },
    {
        "id": "pos-reverse-walk",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS3,
        "rationale": (
            "a second non-definitional correct reshape, and the direct correct "
            "counterpart of the `order-reversed` rival: it keeps the frozen impl's "
            "`Id.run do` / `for` shape but walks the page numbers in the opposite "
            "direction and PREPENDS, so the two order reversals cancel and the "
            "output order is the spec's. This is what shows the ordering clause "
            "constrains the OUTPUT sequence and not the traversal direction — the "
            "spec must accept this while rejecting `order-reversed`, and it does. "
            "Also not defeq to the spec RHS (`rfl`-only fails), so it needs its own "
            "accumulator induction. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is SATISFIABLE at an F2P-shaped input: the "
            "postcondition is discharged by evaluation at the concrete "
            "collection the real test observes — three items paged two at a "
            "time with no orphan allowance and the empty-page flag set, whose "
            "walk is the two slices [1,2] then [3] — as a `have`, and only "
            "then is the frozen obligation closed verbatim. If this failed, "
            "the modeled behaviour would be unsatisfiable at exactly a normal "
            "input, the total-carrier analogue of PRECOND-TOO-STRONG: the "
            "spec's two sides would not meet on the very shape the change is "
            "for, and every other case in this battery could still pass. "
            "Landed by this audit; the lane had been dropped on the ground "
            "that `1 ≤ perPage` cannot be unsatisfiable, which is an argument "
            "about the hypothesis in isolation and not about the obligation. "
            "Nothing is assumed: no new declaration, no axiom, statement "
            "byte-identical, the ground instance is a `have` prepended to the "
            "existing tactic body."
        ),
    },
    {
        "id": "drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP,
        "refinement": (
            "the faithful real patch is a walk that starts one page late (e.g. "
            "iterating the page range from its second element). For the F2P "
            "collection — split into pages [1,2] then [3] — it omits the first "
            "page entirely, so the observed sequence is [[3]] where the test "
            "asserts [[1,2],[3]]. It is wrong wherever at least one page exists, "
            "single-page collections included (it yields no pages at all there), "
            "and coincides with the spec only where zero pages are expected. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause: dropping the first page number "
            "removes the leading slice, so the result has the wrong length and a "
            "wrong head versus the mapped page numbering. Varies the objectList "
            "binder (a ≥ 2-page collection)."
        ),
        # gold at ([1,2,3], 2, 0, true) = [[1,2],[3]]; rival drops [1,2].
        "witness": _wit("[1, 2, 3]", 2, 0, "true"),
    },
    {
        "id": "order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_REV,
        "refinement": (
            "the faithful patch yields the pages in DECREASING page-number order "
            "(walking the page range reversed). The F2P asserts page 1 ([1,2]) "
            "BEFORE page 2 ([3]); reversed it yields [3] then [1,2], failing the "
            "test. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause's ordering: the result is the reverse "
            "of the mapped page numbering for any collection with ≥ 2 distinct "
            "pages. Varies the objectList binder (a 2-page collection with distinct "
            "slices)."
        ),
        # gold at ([1,2,3,4], 2, 0, true) = [[1,2],[3,4]]; rival = [[3,4],[1,2]].
        "witness": _wit("[1, 2, 3, 4]", 2, 0, "true"),
    },
    {
        "id": "const-page",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_CONST,
        "refinement": (
            "the faithful patch yields the SAME (first) page's contents for every "
            "page number instead of each page's own slice — e.g. re-reading page 1 "
            "on each step. Every F2P collection with ≥ 2 distinct pages would then "
            "see the wrong contents after the first, so it does NOT resolve. "
            "Correct only when all pages coincide (a single-page collection)."
        ),
        "rationale": (
            "REJECTED by the equality clause's element-wise image: entry k must be "
            "the slice for page k+1, but the rival emits page 1's slice at every "
            "position. This is the value-clause attack (nagini's index-not-value "
            "has no counterpart here — the page numbers are computed, not a free "
            "input). Varies the objectList binder (a ≥ 3-page collection with "
            "distinct slices)."
        ),
        # gold at ([1,2,3,4,5], 2, 0, true) = [[1,2],[3,4],[5]]; rival repeats [1,2].
        "witness": _wit("[1, 2, 3, 4, 5]", 2, 0, "true"),
    },
    {
        "id": "ignore-orphans",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_ORPHANS,
        "refinement": (
            "the faithful patch ignores the orphan allowance when computing both "
            "the page count and the per-page extents (hardwiring it to zero). "
            "Where a non-zero allowance folds the trailing short page into the "
            "previous one, this rival instead spills it onto its own page — a "
            "different page count and a different last-page slice — so it fails the "
            "PASS_TO_PASS paginator tests that pin the orphan behaviour. Does NOT "
            "resolve. It is correct on the whole zero-allowance sub-domain (where "
            "it IS the frozen computation), and also happens to agree at nonzero "
            "allowances that are too small to move any boundary; it breaks as soon "
            "as the allowance actually absorbs a trailing page."
        ),
        "rationale": (
            "REJECTED by the equality clause: with a non-zero orphan allowance the "
            "mapped page numbering and slices differ from the orphans-are-zero "
            "computation. FRESH rival with no nagini counterpart — it varies the "
            "`orphans` binder, which every other witness holds at 0."
        ),
        # gold at ([1,2,3], 2, 1, true): orphans absorb the last item into one
        # page of [1,2,3]; rival (orphans=0) splits into [1,2] then [3].
        "witness": _wit("[1, 2, 3]", 2, 1, "true"),
    },
    {
        "id": "ignore-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_EMPTY,
        "refinement": (
            "the faithful patch ignores the empty-collection flag when computing "
            "the page numbering (hardwiring the always-one-page behaviour). For an "
            "empty collection configured to present NO page, this rival still "
            "yields a single empty page, diverging from the PASS_TO_PASS "
            "no-content / allow-empty-false expectations. Does NOT resolve. Correct "
            "whenever the flag is set or the collection is non-empty."
        ),
        "rationale": (
            "REJECTED by the equality clause: for an empty collection with the flag "
            "false the spec's page numbering is empty (zero pages), but the rival "
            "produces one (empty) page. FRESH rival with no nagini counterpart — it "
            "varies the `allowEmpty` binder, which every other witness holds at "
            "true, at the empty-collection boundary."
        ),
        # gold at ([], 1, 0, false) = [] (no pages); rival yields [[]].
        "witness": _wit("[]", 1, 0, "false"),
    },
    {
        "id": "zero-based",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_ZEROBASED,
        "refinement": (
            "the faithful patch treats the page numbering as 0-based when asking "
            "for each page's contents, so every page after the first shows the "
            "PREVIOUS page's items and the final page's items are never shown at "
            "all. The F2P collection would be observed as [[1,2],[1,2]] instead of "
            "[[1,2],[3]] — the right number of pages, the wrong contents — so it "
            "fails the assertion and does NOT resolve. Correct only where there is "
            "at most one page."
        ),
        "rationale": (
            "REJECTED by the element-wise image clause, specifically its 1-BASED "
            "content: entry k must be the slice for page k+1, and this rival emits "
            "the slice for page k. Added by audit to attack a clause the battery "
            "left open — `const-page` collapses all entries to one value, which a "
            "weaker spec pinning only 'every entry is page 1's slice' would also "
            "reject, whereas this rival keeps the entries DISTINCT and merely "
            "shifts them, so only the true 1-based numbering catches it. Varies the "
            "objectList binder (a 2-page collection with distinct slices)."
        ),
        # gold at ([1,2], 1, 0, true) = [[1],[2]]; rival = [[1],[1]].
        "witness": _wit("[1, 2]", 1, 0, "true"),
    },
    {
        "id": "orphans-slice-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_ORPH_SLICE,
        "refinement": (
            "the faithful patch counts the pages with the orphan allowance applied "
            "but computes each page's extent without it, so the trailing items the "
            "allowance was supposed to fold into the final page are simply dropped "
            "— the last page is short and some items are never shown on any page. "
            "Fails the PASS_TO_PASS orphan expectations; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause's element-wise image. Added by audit: "
            "`ignore-orphans` removes the allowance from the numbering AND the "
            "slice simultaneously, so a spec threading the allowance into only one "
            "of the two would still reject it and look adequate. This rival pins "
            "the allowance in the SLICE alone. Varies the `orphans` binder."
        ),
        # gold at ([1,2], 1, 1, true) = [[1,2]] (allowance absorbs the tail);
        # rival numbers one page but slices it without the allowance -> [[1]].
        "witness": _wit("[1, 2]", 1, 1, "true"),
    },
    {
        "id": "orphans-count-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_ORPH_COUNT,
        "refinement": (
            "the mirror-image faithful patch: each page's extent honours the orphan "
            "allowance but the page COUNT ignores it, so the collection is split "
            "into one page more than it has, and that extra trailing page repeats "
            "items already shown on its predecessor. Fails the PASS_TO_PASS page "
            "count / orphan expectations; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the equality clause: the result is longer than the mapped "
            "page numbering the spec names. Added by audit as the complement of "
            "`orphans-slice-only`, pinning the allowance in the page COUNT alone; "
            "together the two split the conjunction that `ignore-orphans` only "
            "attacks as a whole. Varies the `orphans` binder."
        ),
        # gold at ([1,2], 1, 1, true) = [[1,2]]; rival counts 2 pages -> [[1,2],[2]].
        "witness": _wit("[1, 2]", 1, 1, "true"),
    },
    {
        "id": "perpage-count-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_PERPAGE_COUNT,
        "refinement": (
            "the faithful patch sizes each page correctly but counts the pages "
            "as though every page held a single item, so a collection is walked "
            "once per ITEM rather than once per page: the same full-size window "
            "is re-emitted from every starting offset and the walk runs far "
            "past the end of the collection. For the F2P collection — three "
            "items, two to a page — it yields three entries where the test "
            "asserts two, so it does NOT resolve. Correct only where the page "
            "size cannot change the page count (collections of at most one "
            "item, or a page size of one)."
        ),
        "rationale": (
            "REJECTED by the equality clause: the result is longer than the "
            "mapped page numbering, because the numbering is computed from a "
            "hardwired page size of 1 rather than from `perPage`. Added by this "
            "audit to close a measured coverage gap — `perPage` was the one "
            "input binder no rival's wrongness depended on, so a spec that "
            "computed the page count without it would have been rejected by "
            "nothing in this battery. Varies the `perPage` binder in the only "
            "way that changes the spec's verdict: by changing how many pages "
            "the collection has."
        ),
        # gold at ([1,2,3,4], 2, 0, true) = [[1,2],[3,4]]; the rival numbers 4
        # pages and re-slices a full 2-item window at each -> 4 entries.
        "witness": _wit("[1, 2, 3, 4]", 2, 0, "true"),
    },
]

# No opaque callee, no consumed axiom in this bundle's proof; the axiom lane is
# G-AX's responsibility and this gate ignores it.
AXIOM_TESTS = []
