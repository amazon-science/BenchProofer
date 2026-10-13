"""properties.py — G-PBT falsification battery for django__django-15572 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for the admissibility case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_collectTemplateDirs``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO collector procedures (``collect_direct_locations`` /
``collect_provider_locations``) over a ``PSeq[int]`` carrier with fractional
(read-only) permission on the input, and grounds each result against a
front-recursive pure fold (``selected_direct`` / ``selected_provider``). This
Lean bundle models the SAME purely-functional core as ONE function that fuses
both collection sites — ``collectTemplateDirs`` gathers the normalized directory
paths from a configured-directory list and a loader-directory list — over a
``List String`` carrier, and grounds the result the SAME way: membership in the
result is pinned to a structural predicate over the two input lists, with no
opaque answer key to echo. Every nagini partial-domain rival carries over as an
attack on one of the two disjuncts of that membership predicate, or as a
faithful correct positive.

DEFENDED SURFACE (one modeled behavior; a membership iff with two disjuncts).
``problem_spec_collectTemplateDirs resolveDir isFrameworkPath dirs loaderDirs
result`` pins EXACTLY, for every path ``p``:

  p ∈ result  ↔
    (D)  ∃ d ∈ dirs,        d ≠ "" ∧ resolveDir d = p            -- configured
    ∨
    (L)  ∃ d ∈ loaderDirs,  d ≠ "" ∧ isFrameworkPath d = false
                                            ∧ resolveDir d = p    -- loader

The BEHAVIOURAL DISCRIMINATOR (the fix): an EMPTY directory entry must
contribute NOTHING at either site. The pre-fix behavior normalized the empty
entry into a real path and admitted it into the result. The
``pd-direct-unguarded`` and ``pd-provider-drop-present`` rivals below ARE that
pre-fix behavior at each site; on the reported empty-entry input they leak a
spurious path where the fixed behavior emits nothing.

BINDER STRUCTURE. The spec predicate has FOUR input binders: ``resolveDir`` (the
path normalizer), ``isFrameworkPath`` (the framework-internal predicate),
``dirs`` (the configured-directory list), ``loaderDirs`` (the loader-directory
list). The reject witnesses vary all four: ``dirs`` ranges over ``[""]``,
``["a"]``, ``[]``; ``loaderDirs`` over ``[]``, ``[""]``, ``["a"]``;
``isFrameworkPath`` takes ``fun _ => false``, ``fun _ => true`` AND the
non-constant ``fun s => s == "a"``; and ``resolveDir`` takes both the identity
and a non-identity ``fun s => s ++ "z"`` (so a rival that mishandled the
normalizer's argument is sensed — see ``pd-framework-post-normalize``, which
machine-checks exactly that). The SEVEN reject witnesses probe seven DISTINCT
input tuples (``pts=7``); the per-tuple table is in the POINT SPREAD note at the
foot of this file, which is the authoritative accounting.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes this class
    MANDATORY because its input is held at half (read-only) permission, so a
    rival that writes ``entries[i-1] = d`` must be rejected for insufficient
    permission. On this referentially transparent carrier there is no heap, no
    fractional permission, no aliasing, and no ``mut`` INPUT binder — ``dirs``
    and ``loaderDirs`` are immutable values. There is no read-only cell to
    overwrite, so both ``frame-mut-direct`` and ``frame-mut-provider`` have no
    counterpart. No substitute probe is fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not vacuous (audit correction).
    An earlier revision of this note claimed a diverging implementation "cannot
    be written at all on this carrier". That is FALSE and was measured false: a
    self-looping ``partial def implementation_collectTemplateDirs ... :=
    implementation_collectTemplateDirs resolveDir isFrameworkPath dirs
    loaderDirs`` passes ``variant_problems`` (``partial`` is not an assumption
    token) and ELABORATES — the only error in the file is the frozen proof's
    ``show ... = _`` step. So the class is expressible.

    What blocks SHIPPING it is the witness protocol, not expressibility, and the
    two spellings fail in different ways (both measured):
      - plain ``def`` with no decreasing measure: rejected by the termination
        checker (``error: fail to show termination for
        implementation_collectTemplateDirs``). But that error is in the IMPL
        region, so the witness file does not compile either — the witness build
        against the RIVAL exits 1, which the gate reads as ``witness-unproven``
        (inconclusive), not as a refutation. This is the "surgery leaves the file
        uncompilable" tooling category.
      - ``partial def``: elaborates, but ``partial`` makes the constant
        IRREDUCIBLE — it generates no equation lemmas, so ``unfold
        implementation_collectTemplateDirs`` fails
        (``error: Tactic `unfold` failed to unfold``) and no ground ``rfl`` can
        compute its output. A refutation stated over two inputs at once (the impl
        ignores its arguments, so it cannot be both empty at ``dirs=[]`` and
        contain ``"a"`` at ``dirs=["a"]``) is the right SHAPE, but closing it
        still needs one reduction step the carrier will not give: measured, the
        rival-side build fails at exactly that step.
    So this class is recorded as a KNOWN HOLE of the battery (the spec is not
    shown to reject a diverging impl), NOT as a vacuous class. It is not a hole
    in the frozen SPEC: the frozen impl is a total ``def`` and Lean discharges
    its termination, so a diverging rival never verifies — it merely cannot be
    attributed to the spec by a witness under this backend's protocol.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: membership
    is pinned by an existential over the actual input lists, not equated to an
    opaque answer key. Producing each path from its own entry IS doing the work;
    there is nothing to echo. In its place the battery carries honest
    cheapest-reshape POSITIVE CONTROLS that must verify.

  * SPEC-TOO-STRONG, RE-PROVING — APPLIES (audit addition). The two ported
    `let`-hoisting positives are DEFINITIONALLY the frozen loop body, which is
    exactly why they can keep the frozen proof verbatim — so they exercise no
    obligation and say nothing about whether the spec tolerates a different impl
    SHAPE. Two positives were added that the kernel CANNOT identify with the
    frozen term and that therefore re-prove the byte-identical statement on their
    own: `pos-closedform-reproved` (loop-free `filter`/`map`) and
    `pos-dedup-reproved` (output deduplicated, so it differs from the frozen impl
    observably as a list while agreeing as a set — the `set` modeling claim in
    mapping.md, machine-checked rather than asserted).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Six rivals, correct on part of the domain
    but diverging where the fix bites: drop the empty-entry guard at the
    configured site (D); invert it (keep empty, drop present) at the configured
    site (D); drop the empty-entry guard at the loader site (L); drop the
    framework-internal filter at the loader site (L); collect nothing at the
    loader site at all (L, the OMISSION direction); apply the framework filter to
    the normalized path rather than to the entry (L, the normalization clause).
    The two disjuncts, both load-bearing conjuncts of L, both DIRECTIONS of the
    iff, and the argument the framework predicate receives are each attacked.
    (The last two rivals are AUDIT ADDITIONS — see the accounting note.)

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that (a) computes the rival's concrete output
with a ``have himpl … := by rfl`` (the ``Id.run do`` / ``for`` loop reduces
definitionally at ground list literals), then (b) instantiates the membership
iff at one concrete path and derives ``False``. Each witness binds NOTHING in
its head (all inputs are ground literals / closed lambdas), so there are no
hypotheses whose joint consistency could be in question. Each was checked with
two real ``lake env lean`` builds to HOLD of its rival and to FAIL on the frozen
solution (``rfl`` fails there because the guard changes the computed list), so
it discriminates rather than asserting a tautology.

The independent audit re-derived all six rival/gold build pairs (rival exit 0,
gold exit 1 in every case) and confirmed each gold-side failure is a SEMANTIC
one: the error is `rfl` reporting the rival's claimed ground output is not
definitionally equal to the frozen impl's, never an unknown identifier, a type
error or a stuck reduction. It additionally ran a COUNTER-PROBE per witness —
the same refutation body with ``himpl`` restated at the frozen impl's TRUE
output — and each left ``⊢ False`` unsolved (exit 1), which shows the closing
``simp`` derives the contradiction from the concrete membership claim at the
named input and not from the shape of the body.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
reintroduces the reported regression (or a dual of it) at one collection site,
so on an empty-entry / framework-entry input the watcher observes a directory
set that differs from the fixed behavior, and the F2P scenario
(``DIRS: [""]`` ⇒ expected empty set) or a PASS_TO_PASS scenario would mismatch
— so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. Both path callees are modeled as universally-quantified
parameters (``resolveDir``/``isFrameworkPath``), so the proof consumes no
property of either and the bundle declares no ``opaque`` callee and no ``axiom``.
The nagini ``AXIOM_TESTS`` belong to G-AX and are dropped (see ``assessment``).
"""
from pathlib import Path

INSTANCE = "django__django-15572"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The two guarded appends are the only per-site-distinct impl text. Every impl
# reshape lands entirely inside `-- impl-start` / `-- impl-end`.
_DIRECT_GUARD = (
    '    if dir ≠ "" then\n'
    '      items := items ++ [resolveDir dir]')
_PROVIDER_GUARD = (
    '    if directory ≠ "" ∧ isFrameworkPath directory = false then\n'
    '      items := items ++ [resolveDir directory]')

# The frozen proof's intro line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro resolveDir isFrameworkPath dirs loaderDirs\n"


# ---------------------------------------------------------------------------
# witness scaffold. Reduce the rival's output at ground literals via `rfl`, then
# instantiate the membership iff at one concrete path and close by `simp`.
# `body` supplies the closing lines after `rw [himpl]`.
# ---------------------------------------------------------------------------
def _w(resolveDir, isFwp, dirs, loaderDirs, out, body, fwp_binder="_"):
    # `fwp_binder` is the framework predicate's argument name: "_" for the
    # constant predicates, "s" for the one rival that needs a NON-constant
    # `isFrameworkPath` (so the framework conjunct is true at one entry and
    # false at another within a single input).
    call = (f"(fun s => {resolveDir}) (fun {fwp_binder} => {isFwp}) "
            f"{dirs} {loaderDirs}")
    return (
        f"example : ¬ problem_spec_collectTemplateDirs\n"
        f"    (fun s => {resolveDir}) (fun {fwp_binder} => {isFwp}) "
        f"{dirs} {loaderDirs}\n"
        f"    (implementation_collectTemplateDirs {call}) := by\n"
        f"  have himpl : implementation_collectTemplateDirs {call} = {out} := by rfl\n"
        f"  unfold problem_spec_collectTemplateDirs\n"
        f"  rw [himpl]\n"
        f"{body}\n")


# A path present in `result` that the spec forbids (empty entry leaks a path).
_BODY_LEAK = (
    "  intro h\n"
    '  have h2 := (h "").mp (by simp)\n'
    "  simp at h2")

# The frozen impl's whole body, and the frozen proof's post-`intro` tail. Both
# unique in Solution.lean. Needed by the RE-PROVING positive below, which
# replaces the loop-based impl with a loop-free closed form: that reshape is NOT
# definitionally the frozen loop, so the frozen `show ... = _` step no longer
# applies and the case must supply its own proof of the SAME (byte-identical)
# theorem statement.
_IMPL_BODY = (
    "def implementation_collectTemplateDirs\n"
    "    (resolveDir : String → String) (isFrameworkPath : String → Bool)\n"
    "    (dirs loaderDirs : List String) : List String := Id.run do\n"
    "  let mut items : List String := []\n"
    "  for dir in dirs do\n"
    '    if dir ≠ "" then\n'
    "      items := items ++ [resolveDir dir]\n"
    "  for directory in loaderDirs do\n"
    '    if directory ≠ "" ∧ isFrameworkPath directory = false then\n'
    "      items := items ++ [resolveDir directory]\n"
    "  return items")

_PROOF_TAIL = _BASE[
    _BASE.index(_P_INTRO) + len(_P_INTRO):_BASE.index("-- proof-end")]

# The iff-closing rintro/exact block, shared by the frozen proof and the
# re-proving positive: once both sides are in `mem_append/mem_map/mem_filter`
# form the two directions are pure reassociation of the same conjunctions.
_IFF_CLOSE = (
    "  constructor\n"
    "  · rintro (⟨d, hd, heq⟩ | ⟨d, ⟨hd, hne, hfw⟩, heq⟩)\n"
    "    · obtain ⟨hd2, hne⟩ := hd; exact Or.inl ⟨d, hd2, hne, heq⟩\n"
    "    · exact Or.inr ⟨d, hd, hne, hfw, heq⟩\n"
    "  · rintro (⟨d, hd, hne, heq⟩ | ⟨d, hd, hne, hfw, heq⟩)\n"
    "    · exact Or.inl ⟨d, ⟨hd, hne⟩, heq⟩\n"
    "    · exact Or.inr ⟨d, ⟨hd, hne, hfw⟩, heq⟩\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_collectTemplateDirs` statement byte-identical and the
    # frozen proof body unchanged (the reshape is definitionally the frozen
    # loop body). (Both verified: real build.)
    # =====================================================================
    {
        "id": "pos-direct-localreshape",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the configured-site emptiness test into a `let`-bound boolean,
        # then branch on it. Same values, extra binding; definitionally the
        # frozen body, so the frozen proof still closes — no proof authoring,
        # no helper lemma, no assumption token.
        "module": _swap(
            _BASE, _DIRECT_GUARD,
            '    let present := dir ≠ ""\n'
            '    if present then\n'
            '      items := items ++ [resolveDir dir]'),
        "rationale": (
            "correct reshape that hoists the configured-site emptiness test into "
            "a `let` local; it computes the SAME result on every input, so the "
            "membership iff still holds — else SPEC-TOO-STRONG. Definitionally "
            "the frozen loop body, so the frozen proof closes; statement "
            "byte-identical, no new axiom/lemma. Ports nagini "
            "pos-direct-localreshape."),
    },
    {
        "id": "pos-provider-localreshape",
        "kind": "soundness",
        "expect": "verify",
        # Hoist both loader-site conjuncts into typed `let` locals, keep the
        # conjunction order. Same values, different executable shape.
        "module": _swap(
            _BASE, _PROVIDER_GUARD,
            '    let present := directory ≠ ""\n'
            '    let outside := isFrameworkPath directory = false\n'
            '    if present ∧ outside then\n'
            '      items := items ++ [resolveDir directory]'),
        "rationale": (
            "correct reshape that hoists both loader-site conjuncts into `let` "
            "locals, keeping the conjunction order; same result on every input, "
            "so the membership iff still holds — else SPEC-TOO-STRONG. "
            "Definitionally the frozen loop body, so the frozen proof closes; "
            "statement byte-identical, no new axiom/lemma. Ports nagini "
            "pos-provider-localreshape."),
    },

    {
        "id": "pos-closedform-reproved",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The two `let`-hoisting positives above are, by
        # construction, DEFINITIONALLY the frozen loop body — which is why they
        # keep the frozen proof verbatim. That makes them honest but weak: a
        # reshape the kernel cannot distinguish from the frozen term exercises
        # no obligation, so neither positive shows the spec tolerates a genuinely
        # different impl SHAPE. This case does: it replaces both `for` loops with
        # the loop-free `filter`/`map` closed form, which is NOT definitionally
        # the frozen `Id.run do` term (the frozen proof's `show ... = _` step
        # fails against it — measured), so the case must RE-PROVE the same
        # byte-identical theorem statement from scratch. No new axiom/lemma, no
        # `sorry`; the frozen helper lemma is left in place but goes unused.
        "module": _swap(
            _swap(
                _BASE, _IMPL_BODY,
                "def implementation_collectTemplateDirs\n"
                "    (resolveDir : String → String) "
                "(isFrameworkPath : String → Bool)\n"
                "    (dirs loaderDirs : List String) : List String :=\n"
                '  (dirs.filter (fun d => decide (d ≠ ""))).map resolveDir\n'
                "    ++ (loaderDirs.filter (fun d => decide (d ≠ \"\" ∧ "
                "isFrameworkPath d = false))).map resolveDir"),
            _PROOF_TAIL,
            "  unfold problem_spec_collectTemplateDirs "
            "implementation_collectTemplateDirs\n"
            "  intro p\n"
            "  simp only [List.mem_append, List.mem_map, List.mem_filter, "
            "decide_eq_true_eq]\n"
            + _IFF_CLOSE),
        "rationale": (
            "correct impl in a genuinely different SHAPE: the two imperative "
            "accumulation loops are replaced by the loop-free `filter`/`map` "
            "closed form. Unlike the two `let`-hoisting positives — which are "
            "definitionally the frozen loop body and so ride the frozen proof — "
            "this reshape is NOT definitionally the frozen term (the frozen "
            "proof's `show ... = _` reduction step fails against it), so the "
            "case re-proves the SAME byte-identical theorem statement on its "
            "own. It computes the same list on every input, so it must verify — "
            "else the spec is SPEC-TOO-STRONG, pinned to the frozen impl's "
            "syntactic form rather than to its values. Audit addition: the "
            "ported battery had no positive that forces a re-proof."),
    },
    {
        "id": "pos-dedup-reproved",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The modeled observable is a Python `set`, and mapping.md
        # records that the spec pins membership via `↔` precisely so that order
        # and MULTIPLICITY are irrelevant. That tolerance is a load-bearing
        # modeling claim and the ported battery never exercised it: every case's
        # impl emits the same multiset as the frozen one. This impl deduplicates
        # its output, so it differs from the frozen impl OBSERVABLY as a list
        # (`["a","a"]` vs `["a"]` on dirs=["a","a"]) while agreeing as a set. It
        # must verify, or the spec is secretly pinning list multiplicity and the
        # `set` model is wrong.
        "module": _swap(
            _swap(
                _BASE, _IMPL_BODY,
                "def implementation_collectTemplateDirs\n"
                "    (resolveDir : String → String) "
                "(isFrameworkPath : String → Bool)\n"
                "    (dirs loaderDirs : List String) : List String :=\n"
                '  ((dirs.filter (fun d => decide (d ≠ ""))).map resolveDir\n'
                "    ++ (loaderDirs.filter (fun d => decide (d ≠ \"\" ∧ "
                "isFrameworkPath d = false))).map resolveDir).dedup"),
            _PROOF_TAIL,
            "  unfold problem_spec_collectTemplateDirs "
            "implementation_collectTemplateDirs\n"
            "  intro p\n"
            "  simp only [List.mem_dedup, List.mem_append, List.mem_map, "
            "List.mem_filter,\n    decide_eq_true_eq]\n"
            + _IFF_CLOSE),
        "rationale": (
            "correct impl that DEDUPLICATES its output. The modeled observable "
            "is a set, so membership — not multiplicity — is what the spec may "
            "pin; this impl differs from the frozen one observably as a LIST "
            "(on dirs=[\"a\",\"a\"] it returns one element where the frozen impl "
            "returns two) while agreeing as a set, and it re-proves the same "
            "byte-identical statement. It must verify, else the spec is "
            "covertly pinning list multiplicity and the `set` modeling in "
            "mapping.md is unsound (SPEC-TOO-STRONG). Audit addition: no ported "
            "case varied the output multiset, so this tolerance was asserted in "
            "prose and never machine-checked."),
    },

    {
        "id": "pos-lengthguard-reproved",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION (second audit). Every other case in this battery spells
        # the emptiness test the SAME way the frozen impl does — as the string
        # disequality `d ≠ ""` — so nothing tested whether the spec is pinned to
        # that ENCODING of the guard rather than to the predicate it denotes.
        # This impl tests `dir.length ≠ 0` instead. The two are extensionally
        # equal but NOT definitionally so on `String` (the proof needs
        # `String.mk.injEq` + `List.length_eq_zero_iff` to bridge them), so the
        # case must supply that bridging step itself: the frozen `show ... = _`
        # is re-issued with the new guard and the filter predicate rewritten via
        # `hpred`. Measured: with the frozen proof body verbatim this impl FAILS
        # (`'show' tactic failed`), so the case genuinely re-proves.
        "module": _swap(
            _swap(
                _BASE, _DIRECT_GUARD,
                '    if dir.length ≠ 0 then\n'
                '      items := items ++ [resolveDir dir]'),
            _PROOF_TAIL,
            '  have hlen : ∀ s : String, (s.length = 0) ↔ (s = "") := by\n'
            "    intro s\n"
            "    cases s with | _ d =>\n"
            '      show d.length = 0 ↔ (String.mk d = String.mk [])\n'
            "      rw [String.mk.injEq]\n"
            "      exact List.length_eq_zero_iff\n"
            "  have hpred : (fun d : String => decide (d.length ≠ 0)) "
            '= (fun d : String => decide (d ≠ "")) := by\n'
            "    funext d; simp [hlen d]\n"
            "  have key : implementation_collectTemplateDirs resolveDir "
            "isFrameworkPath dirs loaderDirs\n"
            '      = (dirs.filter (fun d => decide (d ≠ ""))).map resolveDir\n'
            '        ++ (loaderDirs.filter (fun d => decide (d ≠ "" ∧ '
            "isFrameworkPath d = false))).map resolveDir := by\n"
            "    show Id.run (forIn loaderDirs\n"
            "            (Id.run (forIn dirs ([] : List String)\n"
            "              (fun dir r => if dir.length ≠ 0 then "
            "ForInStep.yield (r ++ [resolveDir dir])\n"
            "                else ForInStep.yield r)))\n"
            '            (fun directory r => if directory ≠ "" ∧ '
            "isFrameworkPath directory = false\n"
            "              then ForInStep.yield (r ++ [resolveDir directory]) "
            "else ForInStep.yield r))\n"
            "        = _\n"
            "    rw [collectTemplateDirs_loop resolveDir "
            "(fun d => d.length ≠ 0),\n"
            '        collectTemplateDirs_loop resolveDir (fun d => d ≠ "" ∧ '
            "isFrameworkPath d = false)]\n"
            "    rw [hpred]\n"
            "    simp only [List.nil_append]\n"
            "  rw [key]\n"
            "  unfold problem_spec_collectTemplateDirs\n"
            "  intro p\n"
            "  simp only [List.mem_append, List.mem_map, List.mem_filter, "
            "decide_eq_true_eq]\n"
            + _IFF_CLOSE),
        "rationale": (
            "correct impl that spells the emptiness guard as `dir.length ≠ 0` "
            "instead of `dir ≠ \"\"`. Every other case in the battery uses the "
            "frozen impl's own spelling, so nothing else tests whether the spec "
            "is pinned to that ENCODING of the guard rather than to the "
            "predicate it denotes. The two forms are extensionally equal but not "
            "definitionally so on `String`, so this case must bridge them "
            "(`String.mk.injEq` + `List.length_eq_zero_iff`) and re-prove the "
            "byte-identical statement — measured to FAIL under the frozen proof "
            "body verbatim. It must verify, else the spec is SPEC-TOO-STRONG in "
            "the guard's encoding. Audit addition (second audit)."),
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition
    # binder, so the nagini precondition-admission self-call re-expresses as:
    # discharge the spec predicate by evaluation at the exact F2P input
    # (DIRS = [""] ⇒ empty result) as a `have` prepended to the frozen tactic
    # body, then close the frozen obligation verbatim. Nothing is assumed: no
    # new declaration, statement byte-identical. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-empty",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            _P_INTRO +
            "  have _ground : problem_spec_collectTemplateDirs\n"
            '      (fun s => s) (fun _ => false) [""] []\n'
            "      (implementation_collectTemplateDirs "
            '(fun s => s) (fun _ => false) [""] []) := by\n'
            "    have himpl : implementation_collectTemplateDirs "
            '(fun s => s) (fun _ => false) [""] [] = [] := by rfl\n'
            "    unfold problem_spec_collectTemplateDirs\n"
            "    rw [himpl]\n"
            "    intro p\n"
            "    simp\n"),
        "rationale": (
            "the obligation is discharged at the exact F2P input (a single empty "
            "configured entry, no loader dirs) by evaluation as a `have` — the "
            "fixed behavior emits the EMPTY result there — then the frozen "
            "obligation is closed verbatim. Verifies (else the modeled behavior "
            "would be unsatisfiable at exactly the normal F2P input, the analogue "
            "of PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
            "statement byte-identical, ground instance is a `have` in the "
            "existing tactic body. Ports nagini admiss-direct."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P/P2P, and (b) a witness
    # pinning the violation at one concrete input.
    # =====================================================================

    # ---- (D) drop the empty-entry guard at the configured site (pre-fix) ----
    {
        "id": "pd-direct-unguarded",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior at the configured site: append EVERY configured entry,
        # including the empty one, whose normalization then leaks into the result.
        "module": _swap(
            _BASE, _DIRECT_GUARD,
            "      items := items ++ [resolveDir dir]"),
        "refinement": (
            "this IS the pre-fix behavior at the configured site: the unguarded "
            "comprehension over the configured dirs. On the reported input a "
            "single empty configured entry normalizes to a real path and enters "
            "the watched set where the fixed behavior emits nothing, so the "
            "collected set is non-empty; the F2P scenario asserts the EMPTY set "
            "for that input, so the faithful patch would NOT resolve."),
        "rationale": (
            "REJECT from disjunct (D): the spec admits a configured entry only "
            "when it is non-empty (`d ≠ \"\"`), but the rival appends the empty "
            "entry too, so `resolveDir \"\"` is in the result while (D) and (L) "
            "both fail for it. Refuted at dirs=[\"\"], loaderDirs=[]."),
        "witness": _w("s", "false", '[""]', "[]", '[""]', _BODY_LEAK),
    },

    # ---- (D) invert the configured-site guard: keep empty, drop present ----
    {
        "id": "pd-direct-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Guard the WRONG way at the configured site: keep only the empty entry,
        # drop every present one.
        "module": _swap(
            _BASE, _DIRECT_GUARD,
            '    if dir = "" then\n'
            '      items := items ++ [resolveDir dir]'),
        "refinement": (
            "inverts the configured-site guard (`if not dir` instead of "
            "`if dir`): keeps the empty entry, drops every real configured dir. "
            "A faithful patch with the inverted test would drop the configured "
            "template directories from the watch set, so the PASS_TO_PASS "
            "get-template-directories scenario (which expects the configured dir "
            "watched) would see the wrong set; the faithful patch would NOT "
            "resolve."),
        "rationale": (
            "REJECT from disjunct (D): the spec puts `resolveDir d` in the result "
            "for every NON-empty configured `d`, but the rival emits nothing for "
            "a present entry (and would emit the empty one). Refuted at "
            "dirs=[\"a\"], loaderDirs=[], resolveDir = (· ++ \"z\") (a "
            "non-identity normalizer, varying that binder): the required path "
            "\"az\" is absent from the rival's empty output."),
        "witness": _w(
            's ++ "z"', "false", '["a"]', "[]", "[]",
            "  intro h\n"
            '  have h2 := (h "az").mpr (Or.inl ⟨"a", by simp, by simp, by rfl⟩)\n'
            "  simp at h2"),
    },

    # ---- (L) drop the empty-entry guard at the loader site (pre-fix) ----
    {
        "id": "pd-provider-drop-present",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior at the loader site: keep only the framework filter,
        # drop the emptiness conjunct, so an empty loader entry leaks in.
        "module": _swap(
            _BASE, _PROVIDER_GUARD,
            "    if isFrameworkPath directory = false then\n"
            "      items := items ++ [resolveDir directory]"),
        "refinement": (
            "this IS the pre-fix behavior at the loader site: the filter keeps "
            "only `not is_django_path(directory)` and drops the emptiness "
            "conjunct. On a loader that yields an empty entry (not inside the "
            "framework tree) the normalization leaks a base path into the watched "
            "set where the fixed behavior emits nothing; the empty-entry F2P-shaped "
            "scenario would see a non-empty set, so the faithful patch would NOT "
            "resolve."),
        "rationale": (
            "REJECT from disjunct (L): the spec requires BOTH `d ≠ \"\"` AND "
            "`isFrameworkPath d = false`, but the rival drops the first conjunct, "
            "so the empty loader entry (framework-false) is emitted while (L) "
            "fails for it. Refuted at dirs=[], loaderDirs=[\"\"], "
            "isFrameworkPath = false."),
        "witness": _w("s", "false", "[]", '[""]', '[""]', _BODY_LEAK),
    },

    # ---- (L) drop the framework filter at the loader site ----
    {
        "id": "pd-provider-drop-framework",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep only the emptiness conjunct at the loader site, dropping the
        # framework-internal filter, so a framework-internal entry leaks in.
        "module": _swap(
            _BASE, _PROVIDER_GUARD,
            '    if directory ≠ "" then\n'
            "      items := items ++ [resolveDir directory]"),
        "refinement": (
            "drops the pre-existing framework-internal filter at the loader site, "
            "keeping only the emptiness test. A faithful patch that dropped the "
            "framework filter would re-add the framework's own template dirs to "
            "the watch set; the PASS_TO_PASS autoreloader scenarios that rely on "
            "framework dirs being excluded would fail, so the faithful patch "
            "would NOT resolve."),
        "rationale": (
            "REJECT from disjunct (L): the spec requires `isFrameworkPath d = "
            "false`, but the rival emits a present entry regardless, so a "
            "framework-internal entry is in the result while (L) fails for it "
            "(the framework conjunct is violated). Refuted at dirs=[], "
            "loaderDirs=[\"a\"], isFrameworkPath = true (varying that binder): "
            "\"a\" is in the rival's output but forbidden by the spec."),
        "witness": _w(
            "s", "true", "[]", '["a"]', '["a"]',
            "  intro h\n"
            '  have h2 := (h "a").mp (by simp)\n'
            "  simp at h2"),
    },

    # ---- (L) collect NOTHING at the loader site (omission, not a leak) ----
    {
        "id": "pd-loader-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. Every ported rival attacks the ← direction of the
        # membership iff (it LEAKS a path the spec forbids) at one of the
        # guards, except pd-direct-inverted which attacks → at site D. Nothing
        # attacked the → direction at site L: a rival that simply never collects
        # the loader dirs at all satisfies "nothing forbidden is present" and
        # violates only "everything required is present". Dropping the whole
        # second loop is the cheapest impl that isolates that direction.
        "module": _swap(
            _BASE,
            "  for directory in loaderDirs do\n" + _PROVIDER_GUARD + "\n",
            ""),
        "refinement": (
            "a faithful patch that stopped iterating the loader-provided "
            "directories would silently stop watching every directory the "
            "loaders contribute, while still passing the empty-entry scenario. "
            "The PASS_TO_PASS autoreloader scenarios that expect a "
            "loader-contributed directory to be watched would observe a "
            "directory set missing those entries, so the faithful patch would "
            "NOT resolve."),
        "rationale": (
            "REJECT from disjunct (L), the → direction: the spec REQUIRES "
            "`resolveDir d` to be in the result for every non-empty, "
            "non-framework loader entry `d`, but the rival never collects the "
            "loader site at all, so the required path is ABSENT. This is the "
            "omission direction of L; the other three loader/configured rivals "
            "attack leaks. Refuted at dirs=[], loaderDirs=[\"a\"], "
            "isFrameworkPath = false: \"a\" is required by (L) but the rival "
            "returns the empty list."),
        "witness": _w(
            "s", "false", "[]", '["a"]', "[]",
            "  intro h\n"
            '  have h2 := (h "a").mpr '
            '(Or.inr ⟨"a", by simp, by simp, by simp, by rfl⟩)\n'
            "  simp at h2"),
    },

    # ---- (D) apply the framework filter at the CONFIGURED site too ----
    {
        "id": "pd-framework-leaks-into-D",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION (second audit). Every existing rival edits ONE site and
        # attacks a conjunct that belongs to that site. Nothing tested that the
        # two disjuncts keep their conjuncts SEPARATE — i.e. that the framework
        # filter belongs to (L) ONLY and must not gate (D). This rival swaps the
        # guards between the sites: the configured site gains the framework
        # filter and the loader site loses it. Both disjuncts are then wrong, and
        # in OPPOSITE directions at once (D over-filters, L under-filters), which
        # no single-site rival can express.
        "module": _swap(
            _swap(
                _BASE, _DIRECT_GUARD,
                '    if dir ≠ "" ∧ isFrameworkPath dir = false then\n'
                '      items := items ++ [resolveDir dir]'),
            _PROVIDER_GUARD,
            '    if directory ≠ "" then\n'
            '      items := items ++ [resolveDir directory]'),
        "refinement": (
            "a faithful patch that applied the framework-internal test to the "
            "CONFIGURED directories as well would stop watching a "
            "user-configured template directory whenever it happens to sit "
            "inside the framework tree — a legitimate configuration the "
            "unfixed behavior watched — while simultaneously re-admitting "
            "framework-internal loader entries. The PASS_TO_PASS scenarios that "
            "expect the configured directory watched AND framework loader dirs "
            "excluded would both observe the wrong set, so the faithful patch "
            "would NOT resolve."),
        "rationale": (
            "REJECT from disjunct (D): (D) has exactly TWO requirements on a "
            "configured entry — non-empty, and normalized — and the framework "
            "predicate is NOT among them; it belongs to (L) alone. The rival "
            "gates (D) on it anyway, so a configured entry that is "
            "framework-internal is dropped where (D) requires it present. "
            "Refuted at dirs=[\"a\"], loaderDirs=[], isFrameworkPath = true: "
            "(D) requires \"a\" in the result and the rival returns []. This is "
            "the only case attacking the SEPARATION of the two disjuncts' "
            "conjuncts rather than a single conjunct."),
        "witness": _w(
            "s", "true", '["a"]', "[]", "[]",
            "  intro h\n"
            '  have h2 := (h "a").mpr (Or.inl ⟨"a", by simp, by simp, by rfl⟩)\n'
            "  simp at h2"),
    },

    # ---- the normalization clause: filter the NORMALIZED path, not the entry ----
    {
        "id": "pd-framework-post-normalize",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. The `resolveDir d = p` clause and the ARGUMENT the
        # framework predicate is applied to were never attacked: every ported
        # rival either keeps or drops a whole conjunct, and all four use a
        # CONSTANT isFrameworkPath, so a rival that tests the right predicate on
        # the wrong argument would have passed unnoticed. The prose claims such a
        # rival "would be sensed" — this case is that claim, machine-checked.
        # Needs a non-constant predicate so the answer differs between the raw
        # entry and its normalization.
        "module": _swap(
            _BASE, _PROVIDER_GUARD,
            '    if directory ≠ "" ∧ isFrameworkPath (resolveDir directory) '
            "= false then\n"
            "      items := items ++ [resolveDir directory]"),
        "refinement": (
            "applies the framework-internal test to the NORMALIZED absolute "
            "path instead of to the directory entry the loader reported. A "
            "faithful patch that moved the test onto the joined path would "
            "classify entries by the wrong string: entries the framework filter "
            "must exclude are admitted whenever normalization changes the "
            "answer, so framework-internal directories re-enter the watch set "
            "and the PASS_TO_PASS scenarios relying on their exclusion would "
            "fail — the faithful patch would NOT resolve."),
        "rationale": (
            "REJECT from disjunct (L): the spec's framework conjunct is "
            "`isFrameworkPath d = false` on the loader ENTRY `d`, not on its "
            "normalization `resolveDir d`. Refuted at loaderDirs=[\"a\"] with "
            "resolveDir = (· ++ \"z\") and isFrameworkPath = (· == \"a\") — the "
            "first NON-CONSTANT framework predicate in the battery, so the "
            "argument the predicate receives is what discriminates: "
            "isFrameworkPath \"a\" = true forbids \"az\" under (L), but the "
            "rival tests isFrameworkPath \"az\" = false and emits it anyway."),
        "witness": _w(
            's ++ "z"', 's == "a"', "[]", '["a"]', '["az"]',
            "  intro h\n"
            '  have h2 := (h "az").mp (by simp)\n'
            "  simp at h2",
            fwp_binder="s"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 mandatory
# frame-mutation rivals, 4 partial-domain uniqueness rivals, 2 soundness
# positives, 1 admissibility) plus a 2-probe AXIOM lane. This bundle models the
# SAME purely-functional core, fused into one `collectTemplateDirs` over a
# `List String` carrier, and re-expresses every sibling case that has a
# counterpart on this carrier.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   frame-mut-direct             -> (none)                    VACUOUS (no heap)
#   frame-mut-provider           -> (none)                    VACUOUS (no heap)
#   pd-direct-unguarded          -> pd-direct-unguarded       PORTED
#   pd-direct-inverted           -> pd-direct-inverted        PORTED
#   pd-provider-drop-present     -> pd-provider-drop-present  PORTED
#   pd-provider-drop-framework   -> pd-provider-drop-framework PORTED
#   pos-direct-localreshape      -> pos-direct-localreshape   PORTED (proof kept)
#   pos-provider-localreshape    -> pos-provider-localreshape PORTED (proof kept)
#   admiss-direct                -> admiss-f2p-empty          RE-EXPRESSED
#   AXIOM_TESTS (2)              -> (none)                    DROPPED (G-AX)
#   (no sibling)                 -> pd-loader-ignored         AUDIT ADDITION
#   (no sibling)                 -> pd-framework-post-normalize AUDIT ADDITION
#   (no sibling)                 -> pos-closedform-reproved   AUDIT ADDITION
#   (no sibling)                 -> pos-dedup-reproved        AUDIT ADDITION
#   (no sibling)                 -> pd-framework-leaks-into-D AUDIT ADDITION (2nd)
#   (no sibling)                 -> pos-lengthguard-reproved  AUDIT ADDITION (2nd)
#   diverge (class, no sibling case) -> (none)   KNOWN HOLE, not vacuous (2nd)
#
# AUDIT ADDITIONS (independent audit of this port; four cases, all machine-
# checked). The port's own case set left three things untested:
#   1. the → direction of disjunct L. Three of the four ported rivals LEAK a
#      forbidden path; only pd-direct-inverted attacked an omission, and only at
#      site D. `pd-loader-ignored` drops the loader loop entirely, so it violates
#      only "everything required is present" — the direction no ported case
#      reached at L.
#   2. the normalization clause / the framework predicate's ARGUMENT. All four
#      ported witnesses use a CONSTANT isFrameworkPath, so a rival that applies
#      the right predicate to the wrong string could not be sensed by any of
#      them, despite the port's prose claiming it would be.
#      `pd-framework-post-normalize` uses the battery's first non-constant
#      predicate (`· == "a"`) so the argument is what discriminates.
#   3. spec tolerance of a genuinely different impl SHAPE. Both ported positives
#      are definitionally the frozen loop body (the port says so, as the reason
#      the frozen proof still closes), so neither exercises an obligation.
#      `pos-closedform-reproved` and `pos-dedup-reproved` are not
#      kernel-identifiable with the frozen term and re-prove the statement.
#
# VACUOUS (frame-mut-direct / frame-mut-provider): the sibling makes these
#   MANDATORY because its input `entries` is held at Acc(list_pred(entries),1/2)
#   — a read-only half-permission — so a rival that writes `entries[i-1]=d` must
#   be rejected for insufficient permission. This carrier is referentially
#   transparent: `dirs`/`loaderDirs` are immutable values, there is no heap, no
#   fractional permission, no aliasing, and no `mut` INPUT binder. There is no
#   read-only cell to overwrite, so the class is inexpressible. No substitute
#   probe is fabricated (porting map: vacuous here).
# RE-EXPRESSED (admiss-f2p-empty): the sibling asserts the 1/2 precondition
#   permission is HELD for an F2P-shaped `entries` list (permission admissibility).
#   This carrier has no permission and the frozen theorem carries no precondition
#   binder, so the honest analogue is to discharge the POSTCONDITION at the exact
#   F2P input (a single empty configured entry, whose fixed result is the empty
#   set) as a `have`, proving the modeled behavior is satisfiable at a normal
#   input, then close the frozen obligation verbatim.
# DROPPED (AXIOM_TESTS): the sibling probes determinism/Boolean-ness and
#   caller-domain containment of the real `is_django_path`. Here both path
#   callees are universally-quantified PARAMETERS (`resolveDir`/`isFrameworkPath`),
#   so the proof consumes no property of either and the bundle declares no
#   `opaque`/`axiom`. There is nothing for the axiom lane to probe, and G-AX (not
#   this gate) owns it regardless.
#
# COVERAGE. The single top-level clause is the membership iff; its two disjuncts
# (D = configured, L = loader) are each attacked, and both load-bearing conjuncts
# of L (`d ≠ ""` and `isFrameworkPath d = false`) are attacked separately
# (pd-provider-drop-present, pd-provider-drop-framework). The `d ≠ ""` conjunct
# of D is attacked twice (drop and invert). BOTH DIRECTIONS of the iff are
# attacked at both sites: leaks by pd-direct-unguarded /
# pd-provider-drop-present / pd-provider-drop-framework /
# pd-framework-post-normalize, omissions by pd-direct-inverted (D) and
# pd-loader-ignored (L). The `resolveDir d = p` clause is attacked through the
# ARGUMENT the framework predicate is applied to (pd-framework-post-normalize).
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input tuples:
#   (resolveDir, isFrameworkPath, dirs, loaderDirs) =
#     (id,     false,   [""], [])    pd-direct-unguarded          D, leak
#     (·++"z", false,   ["a"], [])   pd-direct-inverted           D, omission
#     (id,     false,   [], [""])    pd-provider-drop-present     L, leak
#     (id,     true,    [], ["a"])   pd-provider-drop-framework   L, leak
#     (id,     false,   [], ["a"])   pd-loader-ignored            L, omission
#     (id,     true,    ["a"], [])   pd-framework-leaks-into-D    D, omission
#     (·++"z", (·=="a"), [], ["a"])  pd-framework-post-normalize  L, arg/leak
#   Across them dirs ∈ {[""],["a"],[]}, loaderDirs ∈ {[],[""],["a"]},
#   isFrameworkPath ∈ {const false, const true, NON-constant (· == "a")},
#   resolveDir ∈ {id, ·++"z"} — every input binder is varied, none is pinned to a
#   single value, and the framework predicate is no longer constant across the
#   whole battery (which is what makes its ARGUMENT observable at all).
AXIOM_TESTS = []
