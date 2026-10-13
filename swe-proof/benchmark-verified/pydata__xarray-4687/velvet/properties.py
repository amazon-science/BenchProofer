"""properties.py — G-PBT falsification battery for pydata__xarray-4687 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct selectByCondition`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  selectByCondition
      (cond : List Bool) (x : List Int) (y : List Int)
      (xAttrs : List (String × String))
      (keepAttributes : Option Bool) (globalKeepDefault : Bool)
      return (out : WhereResult)
    require cond.length = x.length
    require x.length = y.length
    ensures out.values = whereSelect cond x y
    ensures out.attrs  = (if keepResolved keepAttributes globalKeepDefault
                          then xAttrs else [])

The routine combines two operands cell-by-cell under a boolean condition, and
decides whether the result carries over the source attribute mapping. The two
``ensures`` clauses pin TWO INDEPENDENT top-level behaviours as total functions
of the method's own inputs:

  * (V) the VALUE selection — ``out.values = whereSelect cond x y`` — takes, at
        each cell, the first operand's value where the condition holds and the
        second operand's elsewhere. Depends on the three aligned cell lists
        ``cond``, ``x``, ``y``. A rival that selects from the wrong operand, or
        ignores the condition, violates (V).
  * (A) the ATTRIBUTE decision — ``out.attrs = if (keepAttributes.getD
        globalKeepDefault) then xAttrs else []`` — keeps the source mapping
        exactly when the RESOLVED choice is truthy: an explicit per-call choice
        stands as given, and absent one the ambient default applies. Depends on
        ``keepAttributes``, ``globalKeepDefault`` and ``xAttrs``. A rival that
        keeps/drops unconditionally, that ignores the per-call choice in favour
        of the default (or vice-versa), or that resolves ``none`` to the wrong
        default, violates (A).

SIX INPUT BINDERS, all free save the two length ``require``s that keep the
three cell lists aligned:
  * ``cond`` / ``x`` / ``y``          — drive (V);
  * ``keepAttributes``               — the per-call choice; drives (A);
  * ``globalKeepDefault``            — the ambient default; drives (A) when the
                                        per-call choice is absent;
  * ``xAttrs``                       — the source mapping carried by (A) on the
                                        keep branch.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's two
    mandatory frame-mutation rivals keep the gold body then WRITE THROUGH a
    read-only operand held at fractional heap permission (``Acc(...,1/2)``),
    forcing the result to equal that operand by in-place mutation, and are
    rejected for INSUFFICIENT PERMISSION rather than by the value postcondition.
    Lean and Velvet are referentially transparent: every parameter is an
    immutable value, this bundle declares no ``mut`` binder, there is no heap and
    no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is stated entirely over the
    pure ``whereSelect`` / ``keepResolved`` (concrete ``def``s in the ``pure``
    region computing the outcome from the method's own arguments) and the
    inputs; the ``axioms`` region is empty. There is no opaque answer-key to
    echo, so the honest controls are the cheapest faithful reshapes (``pos-*``).
  * PARTIAL-DOMAIN / VALUE — heavily exercised on BOTH clauses. A rival can be
    correct on part of the domain yet diverge on a sub-domain: the always-x
    value rival is right on every cell where the condition holds but wrong where
    it does not; the use-global attribute rival is right whenever the per-call
    choice agrees with the ambient default but wrong where they disagree.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces fully under ``decide``. Each reject rival carries
a machine-checked refutation ``witness`` — a Velvet tester statement
``selectByConditionTester <cond> <x> <y> <xAttrs> <keepAttributes>
<globalKeepDefault> = false`` at ONE concrete input, checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. The ``WhereResult`` return carrier already ``deriving DecidableEq`` in
the frozen file, so no instance is introduced by the witness (and no ``axiom`` /
``sorry`` / ``native_decide``). Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival and FAILS
(``decide`` proves the proposition false) against the frozen solution, so each
rejection is a genuine spec refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; ``whereSelect``
is a deep-model A-reference (validated == the real numeric primitive by
``axiom_check.py`` / G-AX) and ``globalKeepDefault`` is an R refinement of an
unchanged option query (checked by ``conformance_check.py`` / G-CONF), neither
consumed as an axiom in the proof. This gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4687"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- Resolve the keep choice: an explicit per-call choice stands; absent one,\n"
    "    -- the ambient default applies. Then keep the source attribute mapping iff\n"
    "    -- the resolved choice is to keep, otherwise expose no attributes.\n"
    "    let resolved : Bool := keepAttributes.getD globalKeepDefault\n"
    "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
    "    return { values := whereSelect cond x y, attrs := attrsOut }\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct selectByCondition by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `selectByConditionTester cond x y xAttrs keepAttributes globalKeepDefault
# ---- = false` says the extracted program's result violates the postcondition at
# ---- that concrete input (the tester short-circuits to `true` when a `require`
# ---- clause is false, so every witness below keeps the three cell lists aligned
# ---- to satisfy both length preconditions). Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask the
# ---- verdict; both the rival and the frozen impl are loop-free, so both testers
# ---- reduce under `decide`. The `WhereResult` return carrier already
# ---- `deriving DecidableEq` in the frozen file — no instance is assumed here.
def _witness(call):
    return ("extract_program_for selectByCondition\n"
            "prove_precondition_decidable_for selectByCondition\n"
            "prove_postcondition_decidable_for selectByCondition\n"
            "derive_tester_for selectByCondition\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Each keeps the value and
    # attribute outcomes identical and only reshapes the executable surface,
    # so the reproof stays close to the frozen `loom_solve`.
    # =====================================================================
    {
        "id": "pos-attrs-via-keepResolved",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: resolve the keep choice through the pure `keepResolved`
        # selector (definitionally `keepAttributes.getD globalKeepDefault`)
        # instead of spelling the `getD` inline. Same value flow.
        "module": _impl(
            "    let resolved : Bool := keepResolved keepAttributes globalKeepDefault\n"
            "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
            "    return { values := whereSelect cond x y, attrs := attrsOut }"),
        "rationale": "resolving the keep choice through the pure `keepResolved` "
                     "selector (definitionally the same `getD`) leaves both "
                     "post-images identical, so `out.values`/`out.attrs` still "
                     "match the ensures; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on how the resolution is named.",
    },
    {
        "id": "pos-named-locals-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the selected values and the resolved keep to named
        # locals, build the result record through a single typed local, and
        # inline the attrs `if` into the record literal. Same outcome on every
        # input; the do-block shape changed, so the proof is retuned.
        "module": _impl(
            "    let vals : List Int := whereSelect cond x y\n"
            "    let keep : Bool := keepAttributes.getD globalKeepDefault\n"
            "    let out : WhereResult := { values := vals, attrs := if keep then xAttrs else [] }\n"
            "    return out"),
        "rationale": "binding the selected values and the resolved keep to "
                     "named locals and assembling the result through one typed "
                     "record local computes the SAME `out.values` and "
                     "`out.attrs` on every input, so both ensures still hold; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on local "
                     "binding / record assembly order.",
    },

    # =====================================================================
    # ADMISSIBILITY — the two `require`s (the cell lists are aligned) are
    # trivially satisfiable (any equal-length triple, e.g. all empty), so the
    # sibling's "a normal input is in-domain" probe is degenerate here. The
    # residual admissibility risk is that the ATTRIBUTE decision is DEGENERATE
    # at the interesting points — a resolution that did not actually fork on the
    # per-call choice, or masked the override, would read like a live one. This
    # case discharges an in-region assert pinning that `keepResolved` genuinely
    # forks in BOTH directions AND that an explicit per-call choice OVERRIDES the
    # ambient default both ways (the exact spec-too-weak failure mode this
    # carrier is prone to). The impl is kept verbatim so the ensures still
    # discharge; the proof is retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-resolution-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (keepResolved (some true) false = true ∧\n"
            "       keepResolved (some false) true = false ∧\n"
            "       keepResolved none false = false ∧\n"
            "       keepResolved none true = true))\n"
            "    let resolved : Bool := keepAttributes.getD globalKeepDefault\n"
            "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
            "    return { values := whereSelect cond x y, attrs := attrsOut }"),
        "rationale": "the attribute resolution is non-degenerate: an explicit "
                     "per-call `some true` keeps and `some false` drops EVEN when "
                     "the ambient default points the other way (override both "
                     "ways), while `none` genuinely falls back to the default "
                     "(both directions). The in-region assert must discharge "
                     "(else the resolution would be degenerate / the override "
                     "masked); the impl is kept verbatim so the ensures still "
                     "discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # ---- Attribute-clause (A) rivals ----
    # =====================================================================
    {
        "id": "weak-attrs-always-keep",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the resolved choice entirely: always carry the source mapping.
        "module": _impl(
            "    let attrsOut : List (String × String) := xAttrs\n"
            "    return { values := whereSelect cond x y, attrs := attrsOut }"),
        "refinement": "always carrying the source mapping is what a real patch "
                      "that unconditionally propagated attrs (dropped the flag "
                      "check) would do. It keeps attrs even when the resolved "
                      "choice is to drop, changing the historical default-drop "
                      "behaviour, so it fails the PASS_TO_PASS attribute-strategy "
                      "tests that require the mapping dropped when the flag is "
                      "falsy. It would NOT resolve.",
        "rationale": "REJECT from the attrs clause (A): at a resolved-drop input "
                     "(`some false`, default false) the post-image demands "
                     "`out.attrs = []` but the rival returns the non-empty "
                     "`xAttrs`. Refuted at that point; the value clause is "
                     "untouched so only (A) fails.",
        "witness": _witness(
            'selectByConditionTester [true] [1] [0] [("k", "v")] (some false) false'),
    },
    {
        "id": "weak-attrs-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: never carry the mapping (attrs always empty).
        "module": _impl(
            "    let attrsOut : List (String × String) := []\n"
            "    return { values := whereSelect cond x y, attrs := attrsOut }"),
        "refinement": "always emptying the mapping IS the pre-patch behaviour — "
                      "the routine dropped attributes unconditionally. Its "
                      "faithful counterpart is the unchanged repo, which drops "
                      "the source attrs even when the caller asks to keep them, "
                      "exactly the bug the fix addresses. The F2P test asks to "
                      "keep and asserts the mapping survives, so it would NOT "
                      "resolve — the precise change the spec senses (G-DIFF).",
        "rationale": "REJECT from the attrs clause (A): at a resolved-keep input "
                     "(`some true`, default false) the post-image demands "
                     "`out.attrs = xAttrs` (non-empty) but the rival returns "
                     "`[]`. Refuted at that point; varies `keepAttributes` to "
                     "`some true` against the always-keep rival's `some false`.",
        "witness": _witness(
            'selectByConditionTester [true] [1] [0] [("k", "v")] (some true) false'),
    },
    {
        "id": "weak-attrs-ignore-per-call-choice",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve from the AMBIENT DEFAULT alone, ignoring the per-call choice —
        # the override-masking failure mode. Correct whenever the per-call
        # choice agrees with the default; wrong where they disagree.
        "module": _impl(
            "    let resolved : Bool := globalKeepDefault\n"
            "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
            "    return { values := whereSelect cond x y, attrs := attrsOut }"),
        "refinement": "resolving from the ambient default alone is what a real "
                      "patch that read only `OPTIONS['keep_attrs']` and ignored "
                      "the new per-call argument would do. It honours the "
                      "explicit request only when it happens to match the global "
                      "option; when the caller passes an explicit choice that "
                      "differs from the default it silently disregards it. The "
                      "F2P test passes an explicit keep under a drop-by-default "
                      "option and asserts the mapping survives, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the attrs clause (A): the post-image resolves "
                     "`keepAttributes.getD globalKeepDefault`, so at (`some "
                     "false`, default true) it demands drop (`[]`) but the rival "
                     "resolves to the default `true` and keeps `xAttrs`. "
                     "PARTIAL-DOMAIN on the per-call binder; refuted where the "
                     "choice DISAGREES with the default — varying "
                     "`globalKeepDefault` to true (not masked) so the binder is "
                     "observable.",
        "witness": _witness(
            'selectByConditionTester [true] [1] [0] [("k", "v")] (some false) true'),
    },
    {
        "id": "weak-attrs-wrong-none-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve an absent per-call choice to the WRONG constant default (keep)
        # instead of the ambient default. Correct whenever a per-call choice is
        # given; wrong on `none` under a drop-by-default option.
        "module": _impl(
            "    let resolved : Bool := keepAttributes.getD true\n"
            "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
            "    return { values := whereSelect cond x y, attrs := attrsOut }"),
        "refinement": "defaulting an absent choice to keep is what a real patch "
                      "that hard-coded the fallback to True (instead of querying "
                      "the ambient option) would do. It keeps attrs by default "
                      "even under a drop-by-default option, a breaking change to "
                      "the historical default, so it fails the default-strategy "
                      "PASS_TO_PASS tests. It would NOT resolve.",
        "rationale": "REJECT from the attrs clause (A): the post-image resolves "
                     "an absent choice through `globalKeepDefault`, so at "
                     "(`none`, default false) it demands drop (`[]`) but the "
                     "rival's constant-`true` fallback keeps `xAttrs`. Refuted at "
                     "the `none` input — varying `keepAttributes` to `none` and "
                     "making the post-image's dependence on `globalKeepDefault` "
                     "observable (every other attribute rival fixes the choice).",
        "witness": _witness(
            'selectByConditionTester [true] [1] [0] [("k", "v")] none false'),
    },

    # ---- Value-clause (V) rivals ----
    {
        "id": "weak-values-swapped-operands",
        "kind": "uniqueness",
        "expect": "reject",
        # Select from the WRONG operand: take the second where the condition
        # holds and the first elsewhere (operands swapped).
        "module": _impl(
            "    let resolved : Bool := keepAttributes.getD globalKeepDefault\n"
            "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
            "    return { values := whereSelect cond y x, attrs := attrsOut }"),
        "refinement": "swapping the two operands is what a real patch that "
                      "wired the condition to the wrong branch would do. It "
                      "returns the second operand's values where the condition "
                      "holds and the first's elsewhere — the opposite selection. "
                      "The F2P test pins the exact selected values, so it would "
                      "NOT resolve (and breaks the value-selection PASS_TO_PASS "
                      "tests).",
        "rationale": "REJECT from the value clause (V): at `cond = [true]`, "
                     "`x = [1]`, `y = [9]` the post-image demands "
                     "`out.values = whereSelect [true] [1] [9] = [1]` but the "
                     "rival computes `whereSelect [true] [9] [1] = [9]`. Refuted "
                     "at a true-condition cell where the operands differ; varies "
                     "`cond` to `[true]` and exercises the `x`/`y` operands.",
        "witness": _witness(
            'selectByConditionTester [true] [1] [9] [] (some false) false'),
    },
    {
        "id": "weak-values-ignore-condition",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the condition: return the first operand's values
        # unconditionally, ignoring `cond` and `y`. Correct on every cell where
        # the condition holds; wrong where it does not.
        "module": _impl(
            "    let resolved : Bool := keepAttributes.getD globalKeepDefault\n"
            "    let attrsOut : List (String × String) := if resolved then xAttrs else []\n"
            "    return { values := x, attrs := attrsOut }"),
        "refinement": "returning the first operand unconditionally is what a "
                      "real patch that dropped the elementwise select (leaving "
                      "`x` through) would do. It is correct on cells where the "
                      "condition holds but returns `x` where it does not, so it "
                      "fails the F2P test (which has a false-condition cell that "
                      "must take `y`) and the value-selection PASS_TO_PASS "
                      "tests. It would NOT resolve.",
        "rationale": "REJECT from the value clause (V): at `cond = [false]`, "
                     "`x = [2]`, `y = [0]` the post-image demands "
                     "`out.values = whereSelect [false] [2] [0] = [0]` but the "
                     "rival returns `x = [2]`. PARTIAL-DOMAIN: correct on "
                     "true-condition cells, wrong on false ones. Refuted at a "
                     "false-condition cell — varying `cond` to `[false]` (the "
                     "swap rival fixed it true) and `x` to `[2]`.",
        "witness": _witness(
            'selectByConditionTester [false] [2] [0] [] (some false) false'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness — two of which are the mandatory
# frame-mutation rivals). Every one is accounted for below. The sibling models
# the fix as `select_payload(attrs: List[List[int]], mode)` over a length-3
# positional operand list [cond, x, y] held at fractional heap permission, with
# `mode==0` DROPping to an empty payload and `mode==1` PRESERVEing the index-1
# payload; it conflates "which operand's attribute payload survives" with a
# single returned list. This backend SEPARATES the two behaviours the real fix
# actually has: the elementwise VALUE selection (`whereSelect cond x y`, clause
# V) and the ATTRIBUTE decision (`keepResolved`, clause A) over a richer flag
# carrier (`Option Bool` per-call choice + `Bool` ambient default) — so several
# sibling cases split or re-aim, and the value clause the sibling never modeled
# gets its own rivals.
#
#   sibling case                     -> here                             disposition
#   --------------------------------------------------------------------------------
#   pos-control-branch-reorder       -> pos-named-locals-reorder         PORTED (reshaped)
#   admiss-precond-usable            -> admiss-resolution-nondegenerate  RE-AIMED
#   frame-mut-append-readonly        -> (none)                           VACUOUS
#   frame-mut-overwrite-readonly     -> (none)                           VACUOUS
#   preserve-returns-cond-index0     -> weak-values-swapped-operands     RE-AIMED (see below)
#   preserve-returns-y-index2        -> weak-values-ignore-condition     RE-AIMED (see below)
#   preserve-drops-first-element     -> (folded into value rivals)       RE-AIMED
#   default-keeps-instead-of-drops   -> weak-attrs-always-keep           PORTED
#   (no sibling)                     -> pos-attrs-via-keepResolved       ADDED (2nd pos.)
#   (no sibling)                     -> weak-attrs-always-drop           ADDED (pre-patch/A)
#   (no sibling)                     -> weak-attrs-ignore-per-call-choice ADDED (binder cov.)
#   (no sibling)                     -> weak-attrs-wrong-none-default    ADDED (binder cov.)
#
# 1 ported reshape, 1 re-aimed admissibility, 2 vacuous frame rivals, 3
# re-aimed operand/domain rivals folded into the value clause, 1 ported
# default-keeps rival; 1 extra positive + 3 attribute-binder-coverage rivals
# added (the sibling's single returned "payload" cannot express the per-call
# vs ambient-default resolution this carrier models).
#
# VACUOUS (frame-mut-append-readonly, frame-mut-overwrite-readonly): the
#   sibling's two MANDATORY frame-mutation rivals keep the gold body then write
#   through a read-only operand held at half permission (append / in-place
#   element overwrite) to force the result to equal that operand by identity,
#   and must be rejected for INSUFFICIENT PERMISSION. This backend is
#   referentially transparent: every parameter is an immutable value, the method
#   declares no `mut` binder, there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class
#   is vacuous. No substitute is fabricated.
# RE-AIMED (admissibility): the sibling asserts the half-permission facts admit
#   reading a normal length-3 operand list and that both a PRESERVE and a
#   DEFAULT return are reachable. This backend's method has only the two length
#   `require`s (trivially satisfiable) and no permission surface, so that probe
#   is degenerate. It is re-aimed at the residual total-domain risk — that the
#   ATTRIBUTE resolution is DEGENERATE / override-masked — via an in-region
#   assert that `keepResolved` forks both ways on an explicit choice EVEN against
#   an opposing ambient default, and falls back to the default both ways on
#   `none`.
# RE-AIMED (preserve-returns-cond-index0 / preserve-returns-y-index2 /
#   preserve-drops-first-element): the sibling's "return the WRONG operand's
#   payload (index 0 / index 2)" and "drop the first element" rivals attack a
#   single conflated payload list. This carrier does not carry a per-operand
#   attribute payload (only `xAttrs`, the source mapping of the second-positional
#   operand); the "wrong operand" and "partial-domain" spirit is carried instead
#   by the VALUE clause the sibling never modeled — `weak-values-swapped-operands`
#   (select from the wrong operand) and `weak-values-ignore-condition` (a genuine
#   partial-domain break: correct on true-condition cells, wrong on false ones).
# PORTED (default-keeps-instead-of-drops): the sibling's dual-of-the-bug rival
#   keeps the payload under the DEFAULT (dropping) mode. Here that is
#   `weak-attrs-always-keep`: carry the source mapping unconditionally, wrong
#   exactly where the resolved choice is to drop.
# ADDED (pos-attrs-via-keepResolved): a second positive control naming the
#   resolution through the pure `keepResolved` selector — guards against
#   SPEC-TOO-STRONG on how the resolution is spelled.
# ADDED (weak-attrs-always-drop / -ignore-per-call-choice / -wrong-none-default):
#   the sibling's single returned "payload" has NO notion of a per-call choice
#   resolved against an ambient default; this carrier's clause (A) is
#   `keepAttributes.getD globalKeepDefault`. A battery whose attribute rivals all
#   held the flags at one value would never demonstrate the spec's dependence on
#   `keepAttributes` (the per-call choice) OR `globalKeepDefault` (the ambient
#   default): the ignore-per-call rival forces the two to DISAGREE (override
#   observable), and the wrong-none-default rival forces `none` under a
#   drop-by-default option (fallback observable). Both faithful counterparts
#   change the historical default and fail PASS_TO_PASS.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct input
# points):
#   cond            — [true] (attrs rivals, swapped-operands); [false]
#                     (ignore-condition): both truth values.
#   x               — [1] (most); [2] (ignore-condition): varied.
#   y               — [0] (most); [9] (swapped-operands): varied, and the swap
#                     rival's witness DEPENDS on x != y.
#   xAttrs          — [("k","v")] (attribute rivals) and [] (value rivals): both
#                     non-empty and empty; the attribute rivals' divergence is
#                     exactly the (non-)carried non-empty mapping.
#   keepAttributes  — some false / some true / some false / none across the four
#                     attribute rivals: both `some` polarities AND `none`.
#   globalKeepDefault — false / false / true / false: both truth values, and the
#                     ignore-per-call rival's witness DEPENDS on it being true
#                     (it must disagree with the per-call choice).
#   Both independent top-level clauses are attacked: the VALUE selection in two
#   ways (wrong operand; ignore condition) and the ATTRIBUTE decision in four
#   (always keep; always drop; ignore per-call choice; wrong none-default).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (`whereSelect` is a deep-model A-reference, `globalKeepDefault`
# an R refinement, both G-AX/G-CONF territory), and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
