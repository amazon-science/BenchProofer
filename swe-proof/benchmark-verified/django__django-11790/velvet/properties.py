"""properties.py — G-PBT falsification battery for django__django-11790 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over two read-only inputs).

  configureFieldLimit (field modelLimit)
      ensures result.maxLength       = some (resolveLimit modelLimit)     -- C1
      ensures result.widgetMaxLength = some (resolveLimit modelLimit)     -- C3

A form field's input-length limit is derived from an account model's configured
limit (``modelLimit : Option Nat``; ``resolveLimit`` selects the configured value
when one is set, a standard default otherwise) and must be recorded on BOTH
facets the routine keeps in agreement: the limit the field itself enforces
(``maxLength``) AND the SAME limit exposed to the field's rendered control
(``widgetMaxLength``). The regression this routine repairs is precisely a field
that enforces the limit but whose rendered control never advertises it — so both
facets must end up holding the single derived limit. ``resolveLimit`` is a total,
fully unfolded function of the method's own ``modelLimit`` argument (a concrete
``def`` in the ``pure`` region; the ``axioms`` region declares NO ``axiom`` — no
opaque answer key to echo). ``modelLimit`` is FREE (no ``require`` clause), which
is what makes the partial-domain rival below refutable at a concrete point.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling carries this
    class as a VALUE-level attack (a rival that disturbs a pre-existing UNRELATED
    widget attribute, e.g. an autofocus/autocomplete hint), because its carrier
    is a full-permission attribute MAP and the membership/value frame clauses
    (its C5/C6/C7) guard the other keys. This carrier models ONLY the two length
    facets the routine keeps in agreement (mapping.md §2: other field attributes
    are untouched and are NOT carried in ``BoundedField``). There is no attribute
    map, no membership, no other-key value to preserve, and no ``mut`` binder to
    overwrite — so this whole class (nagini W4 wrong-key, W5 clobber-other, W7
    spurious-extra) has NO counterpart here. Reported as an omission under carrier
    narrowing, not faked. (See ``assessment``.)
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``resolveLimit`` is a total,
    fully unfolded function of the method's own argument; there is no opaque
    answer key to echo. The positive controls are honest cheapest-reshape
    controls instead.
  * VALUE / PARTIAL-DOMAIN — the heart of this surface. A rival can get one facet
    right and the other wrong (drop or mis-set the widget facet, offset the field
    facet), or be right on part of the ``modelLimit`` domain (the default branch)
    and wrong on the rest (a configured limit).
  * FREE-INPUT COVERAGE — the discriminating binder is ``modelLimit``; the reject
    witnesses move it off any fixed value, and they cover all THREE cases the
    resolution distinguishes: a positive configured limit, the absent-limit
    default branch, and the vacuous zero limit that the selection also sends to
    the default. A rival can be wrong at exactly one of the three (``w8``) while
    agreeing with the frozen behaviour on the other two, so probing fewer than
    three would leave a whole case of the resolution taken on trust.

DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and the gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` (the resolution is
modeled deeply as ``resolveLimit``; ``meta.json`` axioms == [],
deep_model_references == []), so there is nothing here for this manifest.
"""
from pathlib import Path

INSTANCE = "django__django-11790"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load). It runs from the
# ---- effective-limit computation through `return result`; the two leading
# ---- comment lines and the impl markers are OUTSIDE the anchor and untouched,
# ---- so every variant differs only inside the impl region => same_spec holds. --
_IMPL_GOLD = (
    "    let limit : Nat :=\n"
    "      match modelLimit with\n"
    "      | some n => if n = 0 then 254 else n\n"
    "      | none   => 254\n"
    "    -- Record the limit on the field, and expose the same limit to its rendered\n"
    "    -- control.\n"
    "    let mut result := field\n"
    "    result := { result with maxLength := some limit }\n"
    "    result := { result with widgetMaxLength := some limit }\n"
    "    return result"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: configureFieldLimit body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- the admissibility case that adds an in-region assert may retune it without
# ---- touching the spec or the `prove_correct` header). The reject rivals keep
# ---- this frozen proof — they are refuted by the witness, not by whether the
# ---- tuned script happens to close. ----
_PROOF_GOLD = "prove_correct configureFieldLimit by\n  loom_solve"
assert _PROOF_GOLD in _BASE, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `configureFieldLimitTester field modelLimit = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. Every argument is a concrete literal
# ---- (a `BoundedField` record and an `Option Nat`) so `decide` reduces the
# ---- extracted program fully (both carriers derive DecidableEq). ----
_TESTER = (
    "\n"
    "extract_program_for configureFieldLimit\n"
    "prove_precondition_decidable_for configureFieldLimit\n"
    "prove_postcondition_decidable_for configureFieldLimit\n"
    "derive_tester_for configureFieldLimit\n\n"
)


def _witness(field_lit, model_lit):
    return _TESTER + (
        f"example : configureFieldLimitTester ({field_lit} : BoundedField) "
        f"{model_lit} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof
    # script (both facets end up `some (resolveLimit modelLimit)` regardless of
    # the executable order / data-flow, which `loom_solve` closes).
    # =====================================================================
    {
        "id": "pos-control-single-update",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct reshape: derive the limit by CALLING the pure
        # `resolveLimit` model directly (instead of the inline match) and set BOTH
        # facets in a single record update. Same observable content on both facets;
        # no `mut`, no loop, no lemma.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat := resolveLimit modelLimit\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let result : BoundedField :=\n"
            "      { field with maxLength := some limit, widgetMaxLength := some limit }\n"
            "    return result"),
        "rationale": "derives the limit via the pure `resolveLimit` model and sets "
                     "both facets in one record update; both `result.maxLength` and "
                     "`result.widgetMaxLength` are `some (resolveLimit modelLimit)`, "
                     "so C1 and C3 both hold. A correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the executable form.",
    },
    {
        "id": "pos-control-widget-first",
        "kind": "soundness",
        "expect": "verify",
        # Reshape mirroring the nagini positive: perform the WIDGET write FIRST,
        # then the field write, reading the limit from the same computation. The
        # two facet assignments target disjoint fields, so order is irrelevant to
        # the returned value.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat :=\n"
            "      match modelLimit with\n"
            "      | some n => if n = 0 then 254 else n\n"
            "      | none   => 254\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let mut result := field\n"
            "    result := { result with widgetMaxLength := some limit }\n"
            "    result := { result with maxLength := some limit }\n"
            "    return result"),
        "rationale": "swapping the order of the two facet writes (widget first) "
                     "targets disjoint fields, so the returned value is unchanged "
                     "on both facets; a correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so the usual "a normal
    # input satisfies the precondition" probe is vacuous: nothing could exclude an
    # F2P-shaped input. The residual admissibility risk on a total domain is that
    # the post-image is UNSATISFIABLE / DEGENERATE at the interesting point — a
    # spec no impl can meet reads exactly like a spec every impl meets. This case
    # discharges an in-region `assert`, at the two concrete F2P-shaped points, that
    # the resolution is NON-DEGENERATE: a configured limit resolves to itself (255)
    # while the absent-limit branch resolves to the standard default (254), and the
    # two disagree — the two behaviours the failing tests distinguish. The impl is
    # kept verbatim after the assert so the method's own obligation still
    # discharges; `loom_solve` (the frozen proof) clears the extra assert goal as
    # part of its solve, so the proof body is left untouched. The assert is live:
    # a false claim about those points leaves an unsolved goal (verified: swapping
    # 254 for a wrong constant makes `loom_solve` fail).
    # =====================================================================
    {
        "id": "admiss-resolution-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    assert (with_name_prefix `admiss\n"
            "      (resolveLimit (some 255) = 255\n"
            "        ∧ resolveLimit none = 254\n"
            "        ∧ resolveLimit (some 255) ≠ resolveLimit none))\n"
            + _IMPL_GOLD),
        "rationale": "the post-image is satisfiable AND non-degenerate at concrete "
                     "F2P-shaped points: a configured limit resolves to itself (255, "
                     "the matches-user-model branch) while the absent-limit branch "
                     "resolves to the default (254, the defaults-to-254 branch), and "
                     "the two disagree. The in-region assert must discharge (else the "
                     "obligation is degenerate at the interesting point); the impl is "
                     "kept verbatim so both facet clauses discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "w1-drop-widget-write",
        "kind": "uniqueness",
        "expect": "reject",
        # Omits the widget-facet write entirely: only the field facet is set, the
        # rendered-control limit is left at the incoming field value. This is the
        # regression itself — the field enforces the limit but its control never
        # advertises it.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat :=\n"
            "      match modelLimit with\n"
            "      | some n => if n = 0 then 254 else n\n"
            "      | none   => 254\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let mut result := field\n"
            "    result := { result with maxLength := some limit }\n"
            "    return result"),
        "refinement": "omits the write that exposes the limit to the rendered "
                      "control (== the pre-patch behaviour: the field's enforced "
                      "limit is set but its control never advertises it). Its "
                      "faithful counterpart is the literal single-line pre-patch "
                      "assignment; the rendered control's length attribute stays "
                      "absent, so both F2P tests — which assert that attribute equals "
                      "255 / 254 — FAIL. It does NOT resolve (this is the bug the "
                      "patch fixes). Headline weakness.",
        "rationale": "REJECT from C3 (result.widgetMaxLength = some (resolveLimit "
                     "modelLimit)): the widget facet is never written, so it retains "
                     "the INCOMING widget-facet value. Refuted at a configured limit "
                     "with the incoming widget facet absent — the field facet is "
                     "correct, only the widget facet violates.",
        "witness": _witness("{ maxLength := none, widgetMaxLength := none }", "(some 255)"),
    },
    {
        # AUDIT-ADDED (wave audit, attack D). The vacuous-limit sub-domain of the
        # resolution (`some 0`) was attacked by NO rival: every pre-existing reject
        # witness sits at `some 255` (w1/w2/w6) or `none` (w3), so the `n = 0` guard
        # inside `resolveLimit` — one of the three cases mapping.md §2 explicitly
        # claims fidelity for — was entirely unprobed. This rival drops that guard
        # and passes the configured limit straight through, so it is CORRECT on
        # `none` and on every positive limit and wrong ONLY at `some 0`. Confirmed
        # by real builds during the audit: variant exit 1 (both ensures left as
        # unsolved goals `some (match modelLimit with | some n => n | none => 254) =
        # some (resolveLimit modelLimit)`), witness exit 0 against the rival and
        # exit 1 against the frozen solution, the gold-side failure being the
        # SEMANTIC refutation `decide proved that the proposition ... is false`.
        "id": "w8-vacuous-limit-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat :=\n"
            "      match modelLimit with\n"
            "      | some n => n\n"
            "      | none   => 254\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let mut result := field\n"
            "    result := { result with maxLength := some limit }\n"
            "    result := { result with widgetMaxLength := some limit }\n"
            "    return result"),
        "refinement": "keeps the absent-limit default but drops the vacuous-limit "
                      "guard, propagating a configured limit of zero verbatim to both "
                      "facets instead of falling back to the standard default. Its "
                      "faithful counterpart replaces the configured-value-else-default "
                      "selection with a plain absent-check, which is NOT the selection "
                      "the modeled behaviour performs: on an account model whose "
                      "configured limit is a vacuous zero it caps both the enforced "
                      "and the advertised input length at zero, so no identifier of "
                      "any length can be entered or submitted. Narrowest-miss rival: "
                      "it agrees with the frozen behaviour on the whole rest of the "
                      "domain (the absent branch AND every positive limit), which is "
                      "exactly why the two F2P-shaped points the other rivals are "
                      "refuted at cannot see it.",
        "rationale": "REJECT from C1 AND C3 (both facets = some (resolveLimit "
                     "modelLimit)): at modelLimit = some 0 the resolution is the "
                     "standard default 254 while the rival writes 0 to both facets. "
                     "Refuted at modelLimit = some 0 — the ONLY point at which this "
                     "rival and the frozen behaviour disagree, and a third value of "
                     "the modelLimit binder no other witness reaches.",
        "witness": _witness("{ maxLength := some 3, widgetMaxLength := none }", "(some 0)"),
    },
    {
        "id": "w2-widget-wrong-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Sets the field facet correctly but writes the DEFAULT 254 into the widget
        # facet regardless of the configured limit (the two facets no longer carry
        # the same value on the configured-limit branch).
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat :=\n"
            "      match modelLimit with\n"
            "      | some n => if n = 0 then 254 else n\n"
            "      | none   => 254\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let mut result := field\n"
            "    result := { result with maxLength := some limit }\n"
            "    result := { result with widgetMaxLength := some 254 }\n"
            "    return result"),
        "refinement": "writes the default 254 into the rendered-control limit "
                      "regardless of the configured limit (value double-mask: the "
                      "field enforces the configured limit while the control "
                      "advertises the default). Its faithful counterpart hardcodes "
                      "the literal default on the widget write; the F2P "
                      "matches-user-model test asserts the control attribute equals "
                      "the configured 255 -> FAILS. It does NOT resolve.",
        "rationale": "REJECT from C3 (widget facet = some (resolveLimit modelLimit)): "
                     "on a configured limit of 255, the constant 254 != 255. Refuted "
                     "at modelLimit = some 255 (the configured-limit branch, where "
                     "the constant and the resolution diverge).",
        "witness": _witness("{ maxLength := some 10, widgetMaxLength := some 20 }", "(some 255)"),
    },
    {
        "id": "w3-field-offby1",
        "kind": "uniqueness",
        "expect": "reject",
        # Sets the widget facet correctly but returns the field facet off by one
        # (the two facets diverge; the enforced cap is one past the resolved limit).
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat :=\n"
            "      match modelLimit with\n"
            "      | some n => if n = 0 then 254 else n\n"
            "      | none   => 254\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let mut result := field\n"
            "    result := { result with maxLength := some (limit + 1) }\n"
            "    result := { result with widgetMaxLength := some limit }\n"
            "    return result"),
        "refinement": "sets the enforced field limit to resolved+1 while the "
                      "rendered control is correct (the enforced cap is one past the "
                      "resolved limit). Its faithful counterpart offsets the field "
                      "assignment; the F2P tests assert the field's enforced limit "
                      "equals the resolved value (254 on the defaults branch) -> "
                      "FAILS. It does NOT resolve.",
        "rationale": "REJECT from C1 (result.maxLength = some (resolveLimit "
                     "modelLimit)): resolved+1 != resolved. Refuted at modelLimit = "
                     "none (the default branch): gold field facet = some 254, rival = "
                     "some 255. This is the only reject witness on the `none` branch, "
                     "moving the modelLimit binder off `some`.",
        "witness": _witness("{ maxLength := some 7, widgetMaxLength := some 8 }", "none"),
    },
    {
        "id": "w6-hardcode-default-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the configured limit entirely and uses the constant default 254
        # for BOTH facets. Correct on the absent-limit (defaults-to-254) branch;
        # DIVERGES on the configured-limit branch.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let limit : Nat := 254\n"
            "    -- Record the limit on the field, and expose the same limit to its rendered\n"
            "    -- control.\n"
            "    let mut result := field\n"
            "    result := { result with maxLength := some limit }\n"
            "    result := { result with widgetMaxLength := some limit }\n"
            "    return result"),
        "refinement": "ignores the configured limit and uses the default 254 for "
                      "both facets. Correct on the absent-limit branch "
                      "(defaults-to-254 F2P test), but its faithful counterpart "
                      "collapses the resolution to the literal default; the "
                      "matches-user-model F2P test (configured 255) asserts both "
                      "facets equal 255 -> FAILS. It does NOT resolve. Partial-domain "
                      "rival (passes the default branch, fails the configured branch).",
        "rationale": "REJECT from C1 AND C3 (both facets = some (resolveLimit "
                     "modelLimit)): on modelLimit = some 255, resolveLimit = 255 but "
                     "the rival writes 254 to both. Refuted at modelLimit = some 255 "
                     "(the sub-domain where the constant and the resolution diverge).",
        "witness": _witness("{ maxLength := none, widgetMaxLength := some 5 }", "(some 255)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals) over
# `configure_username_field(declared_max_length, widget_attrs)`, whose carrier is
# a full-permission attribute MAP written under a `maxlength` token plus a
# returned field-level limit. This bundle models the SAME behaviour as ONE method
# `configureFieldLimit` whose two facets (`maxLength`, `widgetMaxLength`, both
# `Option Nat`) are the ONLY carried state (mapping.md §2: other field/widget
# attributes are untouched by the modeled block and are not carried). That carrier
# narrowing is what determines which sibling cases have a counterpart.
#
#   sibling case                          -> here
#   -----------------------------------------------------------------------
#   pos-control (widget-first, read-back) -> pos-control-widget-first     PORTED
#                                            + pos-control-single-update   ADDED
#   admissibility (self-call, in-domain)  -> admiss-resolution-nondeg...   RE-AIMED
#   W1 drop-widget-write                  -> w1-drop-widget-write          PORTED
#   W2 widget-wrong-value (default)       -> w2-widget-wrong-constant      PORTED
#   W3 field-offby1                       -> w3-field-offby1               PORTED
#   W6 hardcode-default-partial-domain    -> w6-hardcode-default-partial.. PORTED
#   (no sibling: 3-case resolution here)  -> w8-vacuous-limit-passthrough  ADDED
#   W4 wrong-widget-key                   -> (none)  OMITTED (carrier)
#   W5 clobber-preexisting-attr           -> (none)  OMITTED (carrier)
#   W7 spurious-extra-attr                -> (none)  OMITTED (carrier)
#
# RE-AIMED (admissibility): the sibling's self-call establishes that a normal
#   F2P-shaped input satisfies the `Requires` clauses. This backend has NO
#   `require` clause, so nothing could exclude an F2P-shaped input and that probe
#   is vacuous. It is re-aimed at the residual admissibility risk on a total
#   domain: that the post-image is UNSATISFIABLE / DEGENERATE at the interesting
#   point. The case discharges an in-region assert that a configured limit
#   resolves to itself (255) and the absent-limit branch to the default (254) and
#   the two differ — the two behaviours the failing tests distinguish.
#
# OMITTED (3) — all under carrier narrowing, none because hard; no substitute
#   fabricated:
#   * W4 wrong-widget-key: the sibling writes under an unrelated attribute TOKEN
#     instead of the `maxlength` key. This carrier has no attribute map and no
#     key — the rendered-control limit is a dedicated facet (`widgetMaxLength`).
#     A "wrong key" is inexpressible; its observable effect (the maxlength limit
#     never established) is exactly what `w1-drop-widget-write` already probes via
#     C3. No distinct sub-domain remains, so no discriminating witness exists.
#   * W5 clobber-preexisting-attr and W7 spurious-extra-attr: the sibling's
#     value-frame (C6/C7) and membership-frame (C5) attacks — a rival that
#     disturbs, or adds a spurious, UNRELATED widget attribute (an
#     autofocus/autocomplete hint). This carrier does not carry any other
#     attribute: `BoundedField` holds ONLY the two length facets (mapping.md §2).
#     With no other-attribute state and no `mut` binder there is nothing to
#     clobber or add and no frame clause to violate — the whole frame/membership
#     class is vacuous here (the referentially-transparent analogue of the
#     sibling's already-vacuous fractional-permission class).
#
# ADDED (2), neither with a sibling counterpart:
#   * pos-control-single-update (a second cheapest-reshape positive that calls the
#     pure `resolveLimit` model directly and sets both facets in one record
#     update, sharing the frozen proof).
#   * w8-vacuous-limit-passthrough (AUDIT-ADDED, attack D). The sibling's
#     resolution is a two-case `declared if declared is not None else default`, so
#     its domain has only the two points its rivals already move between. THIS
#     carrier's resolution has THREE cases (mapping.md §2: `none ↦ 254`,
#     `some 0 ↦ 254`, `some n (n>0) ↦ n`), because the modeled selection treats a
#     vacuous zero limit as unconfigured. The vacuous-limit case therefore has no
#     sibling rival to port and was left unattacked by the port: every other reject
#     witness sits at `some 255` or `none`, both of which this rival gets RIGHT.
#     Added so the third case of the resolution is probed by a rival that is wrong
#     at exactly one point.
#
# COVERAGE. Independent post-image clauses: C1 (field facet = some (resolveLimit
#   modelLimit)) attacked by w3-field-offby1, w6-hardcode-default and
#   w8-vacuous-limit-passthrough; C3 (widget facet = same) attacked by
#   w1-drop-widget-write, w2-widget-wrong-constant, w6-hardcode-default and
#   w8-vacuous-limit-passthrough. Both clauses defended by both positive controls
#   and the admissibility case. Binder moved by the reject witnesses: `modelLimit`
#   ∈ {some 255 (configured branch: w1, w2, w6), none (default branch: w3),
#   some 0 (vacuous-limit branch: w8)} — all THREE cases of the resolution
#   probed, so no witness pins the modelLimit binder and no case of `resolveLimit`
#   is taken on trust. The `field` binder does NOT appear in either ensures
#   clause: the routine builds a fresh result with BOTH carried facets overwritten
#   (directive 5 — `field` is not `mut` and nothing of it survives), so the output
#   is independent of `field` and there is no `field`-dependent behaviour for a
#   rival to abuse; witnesses nonetheless vary the incoming `field` across the
#   five points. `pts = 5`.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the resolution is modeled deeply as `resolveLimit`; meta.json
#   axioms == [], deep_model_references == []), so there is nothing here to probe.
AXIOM_TESTS = []
