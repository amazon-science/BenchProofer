"""properties.py — G-PBT falsification battery for django__django-14376 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct selectOverride`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  selectOverride (preferredOpt : Option String) (secondaryOpt : Option String)
      (baseValue : String) return (out : String)
    ensures out = resolveWithPrecedence preferredOpt secondaryOpt baseValue

where the pure helper is fully unfolded (no opaque oracle):
  ``resolveWithPrecedence p s b = p.getD (s.getD b)``.

The operation resolves one effective configuration value from a
precedence-ordered set of three sources: a PREFERRED override, a SECONDARY
override kept for backward compatibility, and a BASE value that is always
present. The single top-level ``ensures`` clause C1 pins WHICH source wins:

  (C1) ``out = resolveWithPrecedence preferredOpt secondaryOpt baseValue``
       ``   = preferredOpt.getD (secondaryOpt.getD baseValue)``

which is one predicate combining THREE distinguishable sub-obligations, each
keyed on a different binder configuration:
  * PREFERRED wins: if the preferred source is present (``some p``) the result
    is ``p``, regardless of the other two — the highest-precedence source;
  * SECONDARY over BASE: if the preferred source is absent (``none``) but the
    secondary source is present (``some s``), the result is ``s``;
  * BASE fallback: if BOTH override sources are absent, the result is
    ``baseValue``.
Presence is KEY-PRESENCE, not value-truthiness (mapping.md §2, the load-bearing
refinement): a source that is present but EMPTY (``some ""``) still takes
precedence over the sources below it — ``(some "").getD d = ""`` — so an
empty-valued present source is NOT the same as an absent one. All three input
binders are load-bearing: ``preferredOpt`` and ``secondaryOpt`` select the
branch, ``baseValue`` is the result on the both-absent branch. There is no
opaque oracle to echo (the ``axioms`` region is empty; ``resolveWithPrecedence``
is a fully-unfolded pure function of the three input binders), so the unique
satisfier IS the honestly-resolved value.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts a RICHER function ``resolve_db_arg`` returning a
``Tuple[bool, List[int]]``: it not only selects the name (its P1) but also
DECIDES a trailing positional argument (P2: appended iff the selected name is
non-empty) and COPIES the selected name element-by-element through a forward
loop (P3 consistency, plus loop invariants). This bundle models ONLY the
purely-functional core the fix actually turns on — the three-level precedence
value SELECTION, as a total function ``(preferred, secondary, base) ↦ String``.
The append-decision boolean and the element-wise copy loop are NOT modeled here
(there is no ``bool`` result and no traversal on this carrier; the resolved
value is returned directly as a ``String``). Nagini rivals attached to those
unmodeled behaviors therefore have NO counterpart and are legitimately omitted;
see the footer for the case-by-case accounting.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame rival that WRITES through a read-only input held at
    ``Acc(list_pred(opt_db), 1/2)``. Lean and Velvet are referentially
    transparent: the three inputs are immutable values, this bundle declares NO
    ``mut`` binder, and there is no heap and no aliasing — so there is no
    read-only input to overwrite and no permission system to trip. Not fabricated
    (per the porting map, this class is vacuous on Lean/Velvet).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 pins ``out`` to a fully-unfolded pure
    function of the three input binders; there is no answer-key term a wrong impl
    could echo. The cheapest correct impl resolves the value honestly, which the
    positive controls cover.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: a rival
    that never consults the preferred source (the exact base-commit bug) is
    correct on every preferred-absent input and diverges only where the preferred
    source is present; a rival that drops the secondary source diverges only
    where the preferred is absent and the secondary present; a rival that
    hardcodes the base diverges only on the both-absent branch; and two rivals
    that treat a present-but-empty source as absent diverge only on the
    present-empty sub-domain the presence-not-truthiness refinement pins.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
carrier is fully transparent (``Option String`` / ``String`` literals), so each
witness closes by ``decide`` with no carrier conditioning and no hypothesis
(hence no joint-satisfiability obligation). The six witnesses sit at six
DISTINCT input points and vary all three binders across the three precedence
branches — ``preferredOpt`` across ``some``/``none``, ``secondaryOpt`` across
``some``/``none``, and ``baseValue`` load-bearing on the both-absent branch — so
each sub-obligation of C1 is attacked at a point that isolates it. Because each
witness is a plain evaluation, its failure on the frozen solution TRACKS the
claim rather than merely accompanying it: flipping a witness's claim
(``= false`` to ``= true``) makes the frozen-side build SUCCEED and the
rival-side build FAIL, exactly inverting both exit codes.

ADMISSIBILITY. The obligation carries no ``require``, so the lane is re-aimed at
the total-carrier analogue: the obligation must be SATISFIABLE and
non-degenerate at an F2P-shaped input. ``admiss-f2p-precedence`` discharges C1's
post-image by evaluation at the both-sources-present discriminator and at each
other precedence branch, as an in-region ``assert`` before the frozen obligation
closes verbatim. The lane is carried, not argued away — it is the only one of
the three directions this gate tests that a missing precondition could otherwise
be used to excuse.
"""
from pathlib import Path

INSTANCE = "django__django-14376"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen resolve-then-return body. Lies
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    let viaSecondary := secondaryOpt.getD baseValue\n"
    "    let out := preferredOpt.getD viaSecondary\n"
    "    return out"
)

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script (`loom_solve`) is tuned to the
# ---- frozen resolve-then-return body. A positive control that reshapes the impl
# ---- may need to retune it; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct selectOverride` obligation survives with an identical
# ---- statement. Unique in the file.
_PROOF = (
    "prove_correct selectOverride by\n"
    "  loom_solve"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept). Used for reject rivals (expected NOT to verify)
    and for positive controls whose reshape the frozen `loom_solve` still
    closes."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """As `_impl`, but ALSO retunes the `prove_correct` tactic body. Both edited
    regions are elided from the consumer spec view, so `markers.same_spec` still
    holds and the `prove_correct selectOverride` obligation survives with a
    byte-identical statement — the reshape is REPROVEN, not weakened. Needed for
    a positive whose impl shape the frozen `loom_solve` alone does not close, and
    for the admissibility positive (whose in-region `assert` leaves an extra
    goal)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `selectOverrideTester p s b = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict.
def _tester(body):
    return ("extract_program_for selectOverride\n"
            "prove_precondition_decidable_for selectOverride\n"
            "prove_postcondition_decidable_for selectOverride\n"
            "derive_tester_for selectOverride\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST impl: return the fully-unfolded pure resolver
        # directly. `resolveWithPrecedence p s b` is GROUNDED in the three inputs
        # (a total function, no opaque answer key), so this is a correct impl, not
        # an echo. The frozen `loom_solve` still closes (the residual goal is
        # definitional).
        "module": _impl("    return resolveWithPrecedence preferredOpt secondaryOpt baseValue"),
        "rationale": (
            "the post-image `resolveWithPrecedence preferredOpt secondaryOpt "
            "baseValue` is GROUNDED in the three inputs (a total function, no "
            "opaque answer key), so returning it directly is the honest cheapest "
            "CORRECT impl. It MUST verify — C1 is literally `out = "
            "resolveWithPrecedence …` — else the single postcondition clause is "
            "SPEC-TOO-STRONG. Also shows the spec is not echo-vulnerable: any "
            "wrong constant/echo would fail C1."
        ),
    },
    {
        "id": "pos-control-nested-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: an explicit nested branch (test the preferred source first;
        # only inside its absent case branch on the secondary source), the direct
        # analogue of the sibling's nested-if positive control. Observationally
        # `preferredOpt.getD (secondaryOpt.getD baseValue)`, so C1 holds and the
        # frozen `loom_solve` still closes the residual goal (no retune).
        "module": _impl(
            "    let out := match preferredOpt with\n"
            "      | some p => p\n"
            "      | none => match secondaryOpt with\n"
            "        | some s => s\n"
            "        | none => baseValue\n"
            "    return out"),
        "rationale": (
            "structurally-different CORRECT reshape: the flat `getD`-ladder is "
            "rewritten as an explicit nested branch (preferred-present test "
            "first, secondary tested only inside the preferred-absent arm), the "
            "analogue of the sibling's nested-if reorder. Observationally "
            "`preferredOpt.getD (secondaryOpt.getD baseValue)`, so C1 holds; the "
            "residual goal closes with a per-constructor `rfl`. A faithful "
            "reshape MUST verify, else C1 is over-fit to the `getD` spelling => "
            "SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-control-isSome-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: replace the `getD` ladder with an explicit presence TEST
        # (`Option.isSome`) plus a projection (`Option.get!`), the shape a real
        # implementation written as "if the key is present, use its value" takes.
        # Observationally `preferredOpt.getD (secondaryOpt.getD baseValue)` — the
        # two spellings agree on both constructors of each `Option` — but the
        # frozen `loom_solve` alone does NOT close it: the residual goal is an
        # `if … isSome …` ladder that needs a per-constructor case split first
        # (measured: `loom_solve` leaves `⊢ (if preferredOpt.isSome = true then
        # preferredOpt.get! else …) = resolveWithPrecedence …`). Retuned with a
        # `cases`/`rfl` tail — the tactic body is elided from the spec view, so
        # the OBLIGATION is unchanged and the reshape is reproven, not weakened.
        "module": _impl_reproved(
            "    let viaSecondary := if secondaryOpt.isSome then secondaryOpt.get! else baseValue\n"
            "    let out := if preferredOpt.isSome then preferredOpt.get! else viaSecondary\n"
            "    return out",
            "prove_correct selectOverride by\n"
            "  loom_solve\n"
            "  cases preferredOpt <;> cases secondaryOpt <;> rfl"),
        "rationale": (
            "structurally-different CORRECT reshape on the OTHER axis from "
            "pos-control-nested-match: presence is tested with `Option.isSome` "
            "and the value projected with `Option.get!`, instead of being fused "
            "into `getD`. This is the spelling a real 'if the key is present use "
            "its value' implementation takes, and it is NOT definitionally equal "
            "to the frozen ladder — the frozen `loom_solve` leaves an unsolved "
            "`if … isSome …` goal, so the case genuinely re-does the proof rather "
            "than riding the frozen script. A faithful reshape MUST verify, else "
            "C1 is over-fit to the `getD` spelling => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the analogue of the sibling's precondition probe on a
    # TOTAL carrier. This method has no `require`, so the PRECOND-TOO-STRONG
    # risk re-aims at the residual question the lane exists to answer: is the
    # obligation SATISFIABLE — and non-degenerate — at an F2P-shaped input?
    # A spec that were unsatisfiable (or that collapsed to a constant) at the
    # discriminating configuration would pass every reject case vacuously while
    # pinning nothing. The probe discharges C1's post-image BY EVALUATION at
    # four concrete points (one per precedence branch plus the present-empty
    # sub-domain) as an in-region `assert`, BEFORE the frozen impl closes the
    # frozen obligation verbatim. The `assert` is LIVE: replacing one conjunct
    # with a false claim leaves an unsolved goal (measured, exit 1).
    # =====================================================================
    {
        "id": "admiss-f2p-precedence",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (resolveWithPrecedence (some \"P\") (some \"S\") \"B\" = \"P\"\n"
            "        ∧ resolveWithPrecedence none (some \"S\") \"B\" = \"S\"\n"
            "        ∧ resolveWithPrecedence none none \"B\" = \"B\"\n"
            "        ∧ resolveWithPrecedence (some \"\") (some \"S\") \"B\" = \"\"\n"
            "        ∧ (\"P\" : String) ≠ \"S\" ∧ (\"S\" : String) ≠ \"B\"))\n"
            + _IMPL,
            "prove_correct selectOverride by\n"
            "  loom_solve\n"
            "  all_goals decide"),
        "rationale": (
            "the obligation is SATISFIABLE and NON-DEGENERATE at an F2P-shaped "
            "input — the configuration that supplies BOTH override sources with "
            "distinct values, which is exactly the discriminating shape. The "
            "in-region `assert` discharges C1's post-image by EVALUATION at four "
            "points, one per precedence branch (`(some P, some S, B) ↦ P`; "
            "`(none, some S, B) ↦ S`; `(none, none, B) ↦ B`) plus the "
            "present-empty sub-domain (`(some \"\", some S, B) ↦ \"\"`), and "
            "pins the three witness values PAIRWISE DISTINCT so no branch is "
            "satisfied by accident. The frozen impl is kept verbatim so the "
            "method's own obligation still discharges. If the assert could not "
            "discharge, the obligation would be unsatisfiable at a normal input "
            "(the total-carrier analogue of PRECOND-TOO-STRONG) and every reject "
            "case would be rejecting vacuously; if the post-image collapsed to a "
            "constant, the distinctness conjuncts would fail."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing tests.
    # =====================================================================

    # ---- PREFERRED branch: never consult the preferred source (the base-commit
    # ---- bug). Correct on every preferred-absent input; diverges exactly on the
    # ---- discriminator sub-domain (preferred present).
    {
        "id": "weak-ignore-preferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return secondaryOpt.getD baseValue"),
        "refinement": (
            "this is the base_commit behavior: the effective value is resolved "
            "from a one-level fallback that consults only the SECONDARY source "
            "(the backward-compat key) and never the preferred one. The failing "
            "test that supplies BOTH the preferred and the secondary source with "
            "different values asserts the PREFERRED value is chosen; this rival "
            "yields the secondary value — the test FAILS, so it does NOT resolve. "
            "This is the modeled bug and the prepatch discriminator. Correct on "
            "every preferred-absent input (a true partial-domain break, not a "
            "blanket wrong impl)."
        ),
        "rationale": (
            "REJECT from C1 (PREFERRED sub-obligation): on `preferredOpt = "
            "some p` the spec requires `p`, but this returns `secondaryOpt.getD "
            "baseValue`. If it verified => SPEC-TOO-WEAK (the preferred source's "
            "precedence unenforced). Refuted at `(some \"A\", some \"B\", \"C\")` "
            "— preferred present with a distinct secondary; gold resolves \"A\", "
            "the rival \"B\"."
        ),
        "witness": _tester(
            'example : selectOverrideTester (some "A") (some "B") "C" = false := by\n'
            '  decide\n'),
    },

    # ---- SECONDARY-over-BASE branch: drop the secondary source entirely (fall
    # ---- straight from preferred to base). Correct when preferred present or
    # ---- secondary absent; wrong when preferred absent and secondary present.
    {
        "id": "weak-ignore-secondary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return preferredOpt.getD baseValue"),
        "refinement": (
            "a counterpart that dropped the backward-compat secondary source, "
            "falling straight from the preferred override to the base value. The "
            "failing test's subcase that supplies the value under the SECONDARY "
            "(backward-compat) key with no preferred key asserts the secondary "
            "value is chosen; this rival yields the base value — that subcase "
            "FAILS, so it does NOT resolve. Correct on every preferred-present or "
            "secondary-absent input."
        ),
        "rationale": (
            "REJECT from C1 (SECONDARY-over-BASE sub-obligation): on "
            "`preferredOpt = none`, `secondaryOpt = some s` the spec requires "
            "`s`, but this returns `baseValue`. If it verified => SPEC-TOO-WEAK "
            "(the secondary source's precedence over base unenforced). Refuted at "
            "`(none, some \"B\", \"Z\")` — preferred absent, secondary present; "
            "gold resolves \"B\", the rival falls through to the base \"Z\" "
            "(a distinct base value, so this witness also varies `baseValue`)."
        ),
        "witness": _tester(
            'example : selectOverrideTester none (some "B") "Z" = false := by\n'
            '  decide\n'),
    },

    # ---- BASE branch: hardcode a wrong base constant instead of the base input.
    # ---- Correct on every input where an override is present; wrong on the
    # ---- both-absent branch whenever the base value differs from the constant.
    # ---- This is the ONLY rival on which `baseValue` is the deciding binder.
    {
        "id": "weak-wrong-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('    return preferredOpt.getD (secondaryOpt.getD "")'),
        "refinement": (
            "a counterpart that resolved the both-absent case to a hardcoded "
            "constant instead of the always-present base value. A PASS_TO_PASS "
            "case that supplies neither override source asserts the base value is "
            "chosen; this rival yields the constant — that case FAILS, so it does "
            "NOT resolve, except in the degenerate case where the base value "
            "equals the hardcoded constant. Correct on every input carrying an "
            "override."
        ),
        "rationale": (
            "REJECT from C1 (BASE sub-obligation): on `preferredOpt = none`, "
            "`secondaryOpt = none` the spec requires `baseValue`, but this "
            "returns the constant `\"\"`. This is the ONLY rival on which "
            "`baseValue` is the deciding binder (a rival mishandling only the "
            "base fallback is caught by no other witness). If it verified => "
            "SPEC-TOO-WEAK (the base fallback unpinned). Refuted at "
            "`(none, none, \"C\")` — both overrides absent; gold resolves \"C\", "
            "the rival \"\"."
        ),
        "witness": _tester(
            'example : selectOverrideTester none none "C" = false := by\n'
            '  decide\n'),
    },

    # ---- PRESENCE-not-truthiness (preferred): treat a present-but-EMPTY
    # ---- preferred source as absent and fall through. Correct on every input
    # ---- except a present-empty preferred with a distinct fallback.
    {
        "id": "weak-empty-preferred-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let fallback := secondaryOpt.getD baseValue\n"
            "    let out := match preferredOpt with\n"
            "      | some v => if v = \"\" then fallback else v\n"
            "      | none => fallback\n"
            "    return out"),
        "refinement": (
            "a truthiness-based counterpart (fall through on a falsy value rather "
            "than on key-absence) diverges on the present-empty preferred "
            "sub-domain: for a present-but-empty preferred source with a distinct "
            "non-empty fallback it selects the fallback where the modeled "
            "key-presence semantics select the empty preferred value — an "
            "observably different resolved value (the downstream consumer would "
            "emit the fallback as the effective argument where it must emit "
            "none). The shipped failing tests use non-empty values, so the "
            "harness would not itself flag this, but the spec faithfully models "
            "the real key-presence lookup (mapping.md §2, validated over "
            "present-empty inputs by G-CONF), so this rival is genuinely "
            "non-conformant; a faithful truthiness patch is not the modeled "
            "behavior. Correct on every input except present-empty preferred."
        ),
        "rationale": (
            "REJECT from C1 (PRESENCE-not-truthiness, preferred): on "
            "`preferredOpt = some \"\"` the spec requires `\"\"` (a present "
            "source wins even when empty — `(some \"\").getD d = \"\"`), but this "
            "rival treats it as absent and returns the fallback. If it verified "
            "=> SPEC-TOO-WEAK (key-presence collapsed to truthiness on the "
            "preferred source). Refuted at `(some \"\", some \"B\", \"C\")` — "
            "present-empty preferred with a distinct secondary; gold resolves "
            "\"\", the rival \"B\"."
        ),
        "witness": _tester(
            'example : selectOverrideTester (some "") (some "B") "C" = false := by\n'
            '  decide\n'),
    },

    # ---- PRESENCE-not-truthiness (secondary): treat a present-but-EMPTY
    # ---- secondary source as absent and fall through to base. Correct on every
    # ---- input except preferred absent & secondary present-empty & base
    # ---- distinct.
    {
        "id": "weak-empty-secondary-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let viaSecondary := match secondaryOpt with\n"
            "      | some v => if v = \"\" then baseValue else v\n"
            "      | none => baseValue\n"
            "    let out := preferredOpt.getD viaSecondary\n"
            "    return out"),
        "refinement": (
            "the same truthiness-vs-key-presence error on the SECONDARY source: "
            "for a preferred-absent input with a present-but-empty secondary and "
            "a distinct base it selects the base where key-presence semantics "
            "select the empty secondary value — an observably different resolved "
            "value. As above the shipped failing tests use non-empty values so "
            "the harness would not flag it, but the spec faithfully models the "
            "real key-presence lookup (mapping.md §2, validated over "
            "present-empty inputs by G-CONF), so a faithful truthiness patch is "
            "non-conformant. Correct on every input except preferred-absent with "
            "present-empty secondary."
        ),
        "rationale": (
            "REJECT from C1 (PRESENCE-not-truthiness, secondary): on "
            "`preferredOpt = none`, `secondaryOpt = some \"\"` the spec requires "
            "`\"\"` (present source wins even when empty), but this rival treats "
            "it as absent and returns the base value. If it verified => "
            "SPEC-TOO-WEAK (key-presence collapsed to truthiness on the secondary "
            "source). Refuted at `(none, some \"\", \"D\")` — preferred absent, "
            "present-empty secondary, distinct base; gold resolves \"\", the "
            "rival \"D\"."
        ),
        "witness": _tester(
            'example : selectOverrideTester none (some "") "D" = false := by\n'
            '  decide\n'),
    },

    # ---- VALUE-LEVEL: select the right SOURCE but return a mangled value. Every
    # ---- rival above attacks WHICH source wins; none pins that the winner's
    # ---- value is returned INTACT. This one drops its last code point: the
    # ---- precedence logic is correct on every input, so it is refuted only by
    # ---- C1's value equality, on a non-empty resolved value.
    {
        "id": "weak-truncate-resolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let resolved := preferredOpt.getD (secondaryOpt.getD baseValue)\n"
            "    return resolved.dropRight 1"),
        "refinement": (
            "a counterpart that sliced the resolved value before handing it on "
            "would emit a truncated effective value. Every failing test compares "
            "the resolved value EXACTLY, so a value one code point short FAILS "
            "them — it does NOT resolve. Note this rival picks the right SOURCE "
            "on every input (its precedence ladder is the frozen one verbatim); "
            "it is wrong only in the VALUE it hands back, which is the "
            "sub-obligation no other rival here attacks — the branch rivals all "
            "return some source's value intact."
        ),
        "rationale": (
            "REJECT from C1 (value-integrity): the spec requires `out` to EQUAL "
            "the resolved value, not a proper prefix of it. If it verified => "
            "SPEC-TOO-WEAK (C1 would pin only which source wins, not that its "
            "value survives — a spec satisfied by any value-mangling impl whose "
            "precedence is right). Refuted at `(some \"AB\", none, \"C\")` — a "
            "resolved value of length 2 so the truncation is observable; gold "
            "resolves \"AB\", the rival \"A\". Also the only rival here at which "
            "`secondaryOpt = none` with `preferredOpt` PRESENT, a "
            "binder combination no other witness point covers."
        ),
        "witness": _tester(
            'example : selectOverrideTester (some "AB") none "C" = false := by\n'
            '  decide\n'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation rival, 5 uniqueness rivals;
# AXIOM_TESTS empty). This bundle models only the purely-functional CORE the fix
# turns on — a single total function `selectOverride : (Option String)
# (Option String) (String) -> String`, the three-level precedence value
# SELECTION — where the sibling contracts a richer function returning a
# `(bool, list)` pair that also decides a trailing positional argument and copies
# the selected value element-by-element through a forward loop. The
# value-selection surface carries across intact; the append-decision and the
# copy-loop do not exist on this carrier (there is no `bool` result and no
# traversal). Every sibling case is accounted for below.
#
#   nagini case                  -> here
#   -----------------------------------------------------------------------
#   pos-reorder-selection        -> pos-control-nested-match         RE-SHAPED
#   (no sibling)                 -> pos-control-direct               ADDED
#   (no sibling)                 -> pos-control-isSome-guard         ADDED
#   admiss-both-keys             -> admiss-f2p-precedence            RE-AIMED
#   frame-write-optdb            -> (none)                           VACUOUS
#   prepatch-legacy-first (W1)   -> weak-ignore-preferred            PORTED
#   empty-primary-as-absent (W2) -> weak-empty-preferred-as-absent   PORTED
#   empty-legacy-as-absent (W3)  -> weak-empty-secondary-as-absent   PORTED
#   always-append (W4)           -> (none)                           VACUOUS
#   truncate-db-name (W5)        -> weak-truncate-resolved           RE-AIMED
#                                   (+ weak-ignore-secondary ADDED)
#                                   (+ weak-wrong-base ADDED)
#
# 3 ported, 2 re-aimed, 1 re-shaped positive, 2 added positives, 2 rivals added,
# 1 vacuous. 10 SPEC cases (3 soundness, 1 admissibility, 6 uniqueness).
#
# PORTED (W1 -> weak-ignore-preferred): the sibling's prepatch rival consults the
#   legacy option first and never examines the non-deprecated one. On this
#   carrier that is exactly `return secondaryOpt.getD baseValue` (never consult
#   the preferred source), rejected by C1 on `preferredOpt = some p`. This IS the
#   modeled bug and the prepatch discriminator.
# PORTED (W2 -> weak-empty-preferred-as-absent; W3 -> weak-empty-secondary-as-
#   absent): the sibling's two present-but-empty rivals (treat a present-empty
#   option as absent) re-express DIRECTLY as treating a present-empty `some ""`
#   source as absent on the preferred and secondary sources respectively,
#   rejected by C1 because `(some "").getD d = ""` (key-presence, not truthiness —
#   the load-bearing mapping.md §2 refinement). Their refinement argument carries
#   over (a truthiness patch diverges on the present-empty sub-domain), with the
#   honest note that the shipped F2P/P2P set uses non-empty values so the
#   divergence is pinned by the modeled key-presence semantics + G-CONF rather
#   than by a shipped failing test.
# RE-SHAPED (pos-reorder-selection -> pos-control-nested-match): the sibling's
#   nested-if reorder (compute "primary present?" first, branch on the legacy
#   option inside the else) becomes the explicit nested `match` this carrier
#   admits — observationally the `getD` ladder, closing under a per-constructor
#   `rfl` tail (the tactic body is elided from the spec view).
# ADDED (pos-control-direct): the cheapest honest impl (`return
#   resolveWithPrecedence …`), a grounded correct impl that also demonstrates the
#   spec is not echo-vulnerable.
# ADDED (weak-ignore-secondary): drops the backward-compat secondary source
#   entirely, attacking the SECONDARY-over-BASE sub-obligation with a NON-EMPTY
#   secondary value — a distinct, F2P-grounded break (the failing test's
#   backward-compat-key subcase) that the present-empty secondary rival does not
#   cleanly cover, and the natural analogue on this carrier of a one-level-fallback
#   regression in the other direction.
# ADDED (weak-wrong-base): hardcodes a wrong base constant, the ONLY rival on
#   which `baseValue` is the deciding binder — attacking the BASE sub-obligation
#   that no ported rival touches (a PASS_TO_PASS config supplies neither override).
#
# RE-AIMED (admiss-both-keys -> admiss-f2p-precedence): the sibling's control
#   asserts its fractional-permission Requires predicates are establishable for an
#   F2P-shaped input. This method has NO precondition (the pre-conditions region is
#   empty; the contract is total over `(Option String) (Option String) (String)`),
#   so there is no permission predicate to establish — but "the frozen obligation
#   has no precondition" is NOT a reason to drop the lane. On a TOTAL carrier the
#   analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE (or
#   degenerate) at exactly an F2P-shaped input, which a positive that discharges
#   the obligation AT THAT CONCRETE INPUT — by evaluation, as an in-region `assert`,
#   before closing the frozen obligation verbatim — tests directly. That is
#   admiss-f2p-precedence: it evaluates C1's post-image at the both-sources-present
#   discriminator and at each of the other two precedence branches plus the
#   present-empty sub-domain, and pins the three values pairwise distinct so the
#   branches cannot be satisfied by a constant collapse. The lane is what detects
#   PRECOND-TOO-STRONG, so it is carried rather than argued away; the earlier
#   "discharged by the positives + the reject witnesses" reasoning was indirect
#   (nothing there pins the obligation at a NAMED F2P-shaped point).
# VACUOUS (frame-write-optdb): the sibling carries this MANDATORY because an input
#   is held at Acc(list_pred(opt_db), 1/2) and a rival can illegally store into
#   it. This backend is referentially transparent and declares no `mut` binder —
#   the three inputs are immutable values with no heap footprint — so there is no
#   read-only input to overwrite and no permission system to trip. Not fabricated.
# VACUOUS (always-append W4): the sibling's rival attacks its (P2)
#   append-boolean clause (append iff the selected name is non-empty). This
#   carrier returns ONLY the resolved `String`; there is no `bool` result and no
#   append decision modeled here (the downstream truthiness `if db:` check is
#   outside the modeled value-resolution, mapping.md §2), so there is no clause to
#   violate. Dropped rather than faked (the append-decision behavior is not on
#   this carrier).
# RE-AIMED (truncate-db-name W5 -> weak-truncate-resolved): the sibling's rival
#   stops its element-wise copy loop one short, attacking its (P1) full-name clause
#   via a loop invariant. The TRAVERSAL is indeed absent here (no copy loop, no
#   loop bound to off-by-one), but the BEHAVIOR the sibling's rival attacked — the
#   returned value must be the selected value INTACT — is fully expressible on this
#   carrier and is a distinct sub-obligation: `String.dropRight 1` on the resolved
#   value reproduces exactly the "one code point short" defect without any
#   traversal. It is NOT covered by the branch rivals, all of which return some
#   source's value intact and so are refuted by WHICH source wins rather than by
#   value integrity. Carried as a value-level rival; the earlier "no distinct
#   defect to re-express" reading conflated the loop SHAPE (genuinely absent) with
#   the value-integrity CLAUSE (present, and previously unattacked).
#
# BINDER / CLAUSE COVERAGE. The three input binders are `preferredOpt : Option
#   String`, `secondaryOpt : Option String`, `baseValue : String`; the single
#   top-level clause C1 combines three precedence sub-obligations (preferred wins;
#   secondary over base; base fallback) plus the key-presence-not-truthiness
#   refinement on each override source. `preferredOpt` is varied across
#   `some "A"`/`some ""` (weak-ignore-preferred, weak-empty-preferred) and `none`
#   (weak-ignore-secondary, weak-wrong-base, weak-empty-secondary). `secondaryOpt`
#   is varied across `some "B"`/`some ""` and `none` (weak-wrong-base). `baseValue`
#   is demonstrated LOAD-BEARING by weak-wrong-base (the ONLY rival whose
#   discrimination turns on the base value, on the both-absent branch). All three
#   precedence branches AND the presence-not-truthiness property on each override
#   source are attacked, plus VALUE INTEGRITY (weak-truncate-resolved: right
#   source, mangled value). Six DISTINCT witness input points (pts=6); no two
#   rivals are refuted at the same input, and the six points cover every
#   presence combination of the two override binders —
#   (some,some), (none,some), (none,none), (some,none) — with `some ""` present on
#   each override source.
# WITNESS DISCRIMINATION (to be verified during authoring with two real builds per
#   reject case): each witness ELABORATES against its straight-line rival (the
#   extracted program's result provably violates C1 at the probed input) and FAILS
#   against the frozen solution (whose result satisfies C1). The carrier is fully
#   transparent, so each witness closes by `decide` with no hypothesis and there
#   is no joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/
#   `axiom` appears.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (there are no consumed axioms
#   in this bundle in any case — the value selection is modeled deeply), and this
#   gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
