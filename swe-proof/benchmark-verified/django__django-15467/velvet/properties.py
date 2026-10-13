"""properties.py — G-PBT falsification battery for django__django-15467 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct emptyLabelFor`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over the purely-functional core):

  emptyLabelFor (allowsBlank : Bool) (override : Option (Option String))
      return (out : Option String)
    ensures out = resolvedLabel allowsBlank override      -- THE load-bearing pin

The method resolves the placeholder shown for the empty selection of a
single-choice related field. ``allowsBlank`` says an empty selection is allowed;
``override`` carries what the caller already supplied, with key-PRESENCE
semantics on the nested option — ``none`` = the caller supplied nothing (key
absent), ``some v`` = the caller supplied ``v`` (and ``v = none`` is an explicit
"nothing"). The three-way distinction is load-bearing: a plain ``Option String``
would conflate "absent" (→ fallback) with "present-and-none" (→ kept as none).

``resolvedLabel`` is a total, fully-unfolded pure ``def`` of the method's own
inputs (``if allowsBlank then override.getD defaultLabel else none``) in the
``pure`` region, where ``defaultLabel`` is the concrete literal ``some "None"``.
The ``axioms`` region is EMPTY — there is NO opaque answer key to echo
(directive 8): the post-image is grounded in the actual inputs, so the only
satisfier is the real resolution. The clause decomposes into three
independently-attackable branches:

  * FORBIDS      — ``allowsBlank = false`` yields ``none`` regardless of what the
                   caller supplied (no placeholder is shown);
  * KEEP-CALLER  — ``allowsBlank = true`` with the caller present (``some v``)
                   keeps ``v`` exactly, including the explicit ``some none``
                   (the sub-behaviour the key-presence carrier exists to pin);
  * FALLBACK     — ``allowsBlank = true`` with the caller ABSENT (``none``)
                   applies the standard fallback placeholder ``defaultLabel``.

TWO input binders, both free and both read-only (neither is ``mut``); the pin
must hold for every value of each:
  * ``allowsBlank`` — the empty-selection flag;
  * ``override``    — the caller-supplied value under key-presence semantics.
The ``pre-conditions`` region is EMPTY (no ``require``): the resolution is total.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling probes the post-state
    coupling of a genuinely-written ``kwargs`` dict (its E1/E2 clauses: the key
    is present post, and its stored value equals the returned value). Lean and
    Velvet are referentially transparent: this method declares no ``mut`` binder,
    takes two immutable values and RETURNS the resolved placeholder — there is no
    heap, no dict written in place, no aliasing, no permission system. The
    post-state-coupling clauses (E1/E2) therefore have NO counterpart here: the
    modeled core is the resolution VALUE, not the surrounding dict mutation. No
    substitute probe is fabricated (per the porting map, this class is dropped).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the nagini sibling records. The
    post-image is pinned to ``resolvedLabel allowsBlank override`` — a concrete
    ``def`` over the method's own arguments (empty ``axioms`` region; no opaque
    callee). The only satisfier is the grounded resolution itself; nothing to
    echo. The honest cheapest CORRECT impl is carried as a positive control.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface. Each rival attacks one of
    the three branches above: ignore the caller (prepatch), drop a present
    explicit-none to the fallback (the truthiness ``or``-form), resolve a value
    even when no empty selection is allowed (forbids branch), or emit no
    placeholder when the caller was absent (fallback branch).
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
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

AUDIT REVISION (independent adversarial re-derivation of a recorded SOUND). All
four original witnesses were rebuilt from scratch: each ELABORATES against its
rival (exit 0) and FAILS against the frozen solution (exit 1) with a SEMANTIC
refutation — `decide` reports "proved that the proposition ... is false", not a
stuck reduction, unknown name, or type error. Three defects were repaired:
  * `admiss-gold-total` was `_BASE` verbatim, i.e. a duplicate of the frozen
    build that could only fail if the shipped bundle did not verify. Replaced
    with a content-bearing probe that `decide`s the pin's value at all four
    sub-domain points inside the elided impl region.
  * both original positives are reshapes the frozen `loom_solve` closes by
    reduction, so neither forced the obligation to be REPROVEN. Added
    `pos-elim-reshape`, whose body is neither definitionally the frozen body nor
    closable by the frozen tactic (residual goal machine-observed), so it must
    be reproven via a retuned — still elided — proof body.
  * the falsy sub-domain was attacked only at the present-explicit-absent value.
    Added `rival-truthiness-empty-string` at `some (some "")`, the other falsy
    point a real truthiness test drops and the one no other rival held.
Attack D wrote four NEW wrong impls (including one agreeing with gold at every
one of the battery's original witness points); all four were REJECTED, so no
spec hole was found. Attack E wrote four NEW correct reshapes; all four are
provable (two needed a retuned proof body), so the spec is not too strong. The
two nagini post-state rivals this port dropped were re-derived as velvet impls
and both VERIFY as gold-equivalent — machine evidence that they are vacuous
here, not a hidden gap.

WITNESS MECHANICS ON THIS BUNDLE. The post-image mentions no opaque callee
(``defaultLabel`` is the literal ``some "None"``), so the postcondition is
DECIDABLE and the tester+``decide`` path is live — the django-13012 pattern. The
frozen impl and every reject rival are loop-free expressions, so both extracted
testers reduce under ``decide``. Each reject rival carries a machine-checked
refutation ``witness`` — a Velvet tester statement
``emptyLabelForTester allowsBlank override = false`` at ONE concrete input,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
tester ``decide``s to ``false`` — the rival's output violates the pin there) and
FAILS against the frozen solution (gold's tester ``decide``s to ``true``, so
``= false`` is refuted). No ``require`` clause exists, so no witness input is
vacuously excluded, and no witness binds a hypothesis (every input is a concrete
literal that decides the pin), so no consistency probe is needed.

AXIOM lane: EMPTY. ``AXIOM_TESTS = []``. The one deep-model reference
(``defaultLabel`` == ``gettext("None")``) is G-AX's job (axiom_check.py /
mapping.md §3.1); this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15467"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (both markers, and the leading comment lines, live inside the
# elided impl region). Every rival and reshape edits ONLY this block (and, for
# reshapes/admissibility, the elided `prove_correct` tactic body), so the spec
# view is untouched and same_spec holds by construction (asserted at load).
_IMPL = (
    "    -- When an empty selection is allowed, keep a caller-supplied placeholder\n"
    "    -- and fall back to the standard placeholder only when none was supplied;\n"
    "    -- otherwise show no placeholder.\n"
    "    if allowsBlank then\n"
    "      let e : Option String := override.getD defaultLabel\n"
    "      return e\n"
    "    else\n"
    "      return none"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as `loom_solve`, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct emptyLabelFor by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Variant with the impl body AND the elided `prove_correct` body replaced.

    Both regions are elided from the consumer spec view, so `same_spec` still
    holds and the obligation survives with a byte-identical statement. A correct
    reshape whose body is NOT definitionally the frozen `getD` form needs this:
    the frozen `loom_solve` alone leaves the residual goal open (machine-checked
    — see `pos-elim-reshape`), which is precisely why such a reshape is a
    STRONGER positive control than one the frozen tactic closes for free.
    """
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `emptyLabelForTester allowsBlank override = false` says the extracted
# ---- program's result violates the postcondition at that concrete input. There
# ---- is no `require` clause, so no input short-circuits the tester to `true`.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict; both the rival and the frozen impl are
# ---- loop-free, so both testers reduce under `decide`.
def _witness(call):
    return ("extract_program_for emptyLabelFor\n"
            "prove_precondition_decidable_for emptyLabelFor\n"
            "prove_postcondition_decidable_for emptyLabelFor\n"
            "derive_tester_for emptyLabelFor\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of branching on the
    # flag inline, it returns the pure model `resolvedLabel` directly. The
    # frozen proof (`loom_solve`) still closes the byte-identical obligation (the
    # ensures IS `out = resolvedLabel ...`, so the body is definitionally the
    # RHS). Because `resolvedLabel` is GROUNDED in the arguments (not an opaque
    # answer key), this doubles as proof the spec is not echo-vulnerable: any
    # WRONG resolution fails `out = resolvedLabel allowsBlank override`. Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-resolved-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return resolvedLabel allowsBlank override"),
        "rationale": (
            "the post-image `resolvedLabel allowsBlank override` is GROUNDED in "
            "the inputs (a total closed function, empty axioms region), so "
            "`return resolvedLabel allowsBlank override` is the honest cheapest "
            "CORRECT impl; the pin is literally `out = resolvedLabel ...`, so it "
            "MUST verify, else the postcondition is SPEC-TOO-STRONG (it would "
            "reject its own model's output). Ports the nagini honest cheapest-impl "
            "positive control (pos-control-conditional-expr) — the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — control-shape reshape: keep the flag
    # branch but resolve the caller override via an explicit `match` on the
    # key-presence carrier rather than `Option.getD`. Same value flow
    # (`none => defaultLabel`, `some v => v`), different control shape; the
    # frozen proof still closes the byte-identical obligation. Verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-match-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if allowsBlank then\n"
            "      let e : Option String := match override with\n"
            "        | none => defaultLabel\n"
            "        | some v => v\n"
            "      return e\n"
            "    else\n"
            "      return none"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (resolve the caller "
            "override with an explicit `match` on the key-presence carrier instead "
            "of `Option.getD`) must verify; the value flow is unchanged "
            "(`none => defaultLabel`, `some v => v`), so the pin still discharges "
            "and the frozen proof closes as-is. Ports the nagini branch-reshape "
            "positive control (pos-control-reorder): if it fails => SPEC-TOO-STRONG "
            "(over-fit to the `getD` code form). NOTE: machine-checked as NOT "
            "definitionally equal to the frozen body — `rfl` on `(match o with | "
            "none => defaultLabel | some v => v) = o.getD defaultLabel` FAILS "
            "(`is not definitionally equal`), so this reshape is a real shape "
            "change that `loom_solve` reduces on its own, not a restatement."
        ),
    },
    # =====================================================================
    # POSITIVE CONTROL 3 (soundness) — ADDED BY AUDIT. The strongest available
    # reshape: resolve the key-presence carrier with `Option.elim` instead of
    # `Option.getD`. Machine-checked as NOT definitionally equal to the frozen
    # body (`rfl` fails on `o.elim defaultLabel id = o.getD defaultLabel`), and —
    # unlike the two positives above — the frozen `loom_solve` does NOT close it
    # on its own (it leaves `⊢ override.elim defaultLabel id = resolvedLabel
    # allowsBlank override` open). So the obligation must be genuinely REPROVEN
    # for the new impl shape, via the retuned tactic body in the elided
    # `prove_correct` region. That makes this the case that actually tests
    # SPEC-TOO-STRONG on impl shape: the other two positives could pass by
    # reduction alone. Verified out-of-band with a real build (exit 0).
    # =====================================================================
    {
        "id": "pos-elim-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    -- Resolve the caller override by eliminating the key-presence\n"
            "    -- carrier directly, rather than via a lookup-with-default.\n"
            "    if allowsBlank then\n"
            "      return override.elim defaultLabel id\n"
            "    else\n"
            "      return none",
            "prove_correct emptyLabelFor by\n"
            "  loom_solve <;> cases override <;> simp_all [resolvedLabel]"),
        "rationale": (
            "a faithful correct impl that eliminates the key-presence carrier with "
            "`Option.elim` (`none => defaultLabel`, `some v => id v`) must verify. "
            "It is NOT definitionally the frozen body — `rfl` on `o.elim "
            "defaultLabel id = o.getD defaultLabel` fails — and the frozen "
            "`loom_solve` alone does NOT close it (residual goal `override.elim "
            "defaultLabel id = resolvedLabel allowsBlank override`), so the "
            "obligation is REPROVEN for the new shape by the retuned tactic body "
            "(both regions elided => `same_spec` holds, statement byte-identical). "
            "If a shape this close to gold could not be proven, the spec/proof "
            "surface would be over-fit to the `getD` form => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-f2p-shaped case. That case
    # established that the read-only precondition (`dict_pred` + non-None) admits
    # an F2P-shaped input. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude any input and the
    # classic "a normal input is admitted" probe is vacuous. Re-aimed at the
    # residual admissibility risk on a total domain: that the post-image is
    # jointly SATISFIABLE by a gold-shaped computation. The frozen impl
    # discharging the ensures IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        # CONTENT-BEARING probe. An earlier revision of this case used `_BASE`
        # verbatim, which made it a duplicate of the frozen build: it could only
        # fail if the shipped bundle itself did not verify (G-VERIFY's job), so it
        # attested nothing about ADMISSIBILITY. Repaired to state, inside the
        # elided impl region, what each of the pin's three sub-domains resolves
        # to — each discharged by `decide`, so the case now fails if any
        # sub-domain is unreachable or resolves to something other than the
        # branch this battery's rivals are aimed at. The frozen body then runs for
        # the real argument, so the obligation is still discharged the frozen way.
        "module": _impl(
            "    -- Admissibility: the resolution is total (no `require`), so the\n"
            "    -- live question is whether the post-image is jointly satisfiable\n"
            "    -- across the three sub-domains the pin distinguishes. Each is\n"
            "    -- checked by computation before the real body runs.\n"
            "    have _keepCaller : resolvedLabel true (some (some \"L\")) "
            "= some \"L\" := by\n"
            "      decide\n"
            "    have _keepExplicitAbsentValue : resolvedLabel true (some none) "
            "= none := by\n"
            "      decide\n"
            "    have _fallback : resolvedLabel true none = defaultLabel := by\n"
            "      decide\n"
            "    have _forbids : resolvedLabel false (some (some \"L\")) "
            "= none := by\n"
            "      decide\n"
            + _IMPL),
        "rationale": (
            "the input carries no `require`, so the resolution is total over every "
            "(flag, override) pair and the classic 'a normal input is admitted' "
            "probe has nothing to exclude. Re-aimed at the residual risk on a total "
            "domain: that the post-image is jointly SATISFIABLE and that each "
            "sub-domain the pin distinguishes is REACHABLE with the value the "
            "battery's rivals are aimed at. All four points are discharged by "
            "`decide` inside the elided impl region (KEEP-CALLER at `some (some "
            "\"L\")` => `some \"L\"`; KEEP-CALLER at the present-explicit-absent "
            "value `some none` => `none`; FALLBACK at `none` => `defaultLabel`; "
            "FORBIDS at `allowsBlank = false` => `none`), then the frozen body "
            "discharges the ensures for the real argument. If any point were "
            "unreachable or resolved elsewhere, this case FAILS => "
            "SPEC-UNSATISFIABLE / the reject lane is aimed at a phantom branch. "
            "Re-aimed from the nagini admiss-f2p-shaped, whose read-only-"
            "precondition half has no counterpart on this referentially-"
            "transparent, precondition-free carrier."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Each rival is a loop-free expression
    # so its extracted tester `decide`s; the frozen spec is untouched. The two
    # binders (`allowsBlank`, `override`) are varied across the witnesses.
    # =====================================================================
    {
        "id": "rival-prepatch-ignore-caller",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug (pre-patch): when an empty selection is allowed, install
        # the standard fallback placeholder UNCONDITIONALLY, discarding whatever
        # the caller supplied. Correct on the forbids branch and on the
        # caller-absent sub-domain; wrong on every caller-present input.
        "module": _impl(
            "    if allowsBlank then\n"
            "      return defaultLabel\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "this IS the pre-patch behaviour: the allowed-empty branch always "
            "installs the standard fallback placeholder, discarding any "
            "caller-supplied value. It is exactly what the added F2P test was "
            "written to catch (a caller-supplied placeholder must survive), so its "
            "faithful real patch — the unpatched repo — does NOT resolve the "
            "instance."
        ),
        "rationale": (
            "REJECT from `out = resolvedLabel allowsBlank override` via the "
            "KEEP-CALLER branch: with `allowsBlank = true` and the caller present, "
            "`getD` returns the caller value, but the rival returns `defaultLabel`, "
            "differing whenever the caller supplied a value other than the "
            "fallback. Refuted at (true, some (some \"X\")): gold resolves "
            "`some \"X\"`, the rival `some \"None\"`. If it verified => "
            "SPEC-TOO-WEAK (admits the reported bug)."
        ),
        "witness": _witness("emptyLabelForTester true (some (some \"X\"))"),
    },
    {
        "id": "rival-truthiness-or-form",
        "kind": "uniqueness",
        "expect": "reject",
        # The public issue's `or`-form: keep a caller value only when it is
        # "truthy", otherwise fall back to the default. Modeled on the key-presence
        # carrier: a present explicit-none (`some none`) is the falsy present value
        # gold keeps but the `or`-form drops to the fallback. Correct on
        # caller-absent, on the forbids branch, and on every present NON-none
        # caller value; diverges ONLY on the present-explicit-none sub-domain — the
        # exact distinction the nested-option carrier exists to preserve.
        "module": _impl(
            "    if allowsBlank then\n"
            "      match override with\n"
            "      | some (some s) => return (some s)\n"
            "      | _ => return defaultLabel\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "the faithful real patch is the truthiness form the issue itself "
            "proposes. It passes the lone F2P test (whose caller-supplied "
            "placeholder is truthy) and every P2P, so the suite does NOT "
            "distinguish it from gold — but it drops a caller value that is "
            "PRESENT and falsy, which a lookup-with-default keeps verbatim (here "
            "the present-explicit-absent value). If it verified, the spec would "
            "admit a patch that fails the issue's real intent on the falsy "
            "sub-domain => SPEC-TOO-WEAK."
        ),
        "rationale": (
            "REJECT from `out = resolvedLabel allowsBlank override` via the "
            "KEEP-CALLER branch on the present-explicit-none point: `getD` returns "
            "the present value `none`, but the rival falls back to `defaultLabel`. "
            "Refuted at (true, some none): gold resolves `none`, the rival "
            "`some \"None\"`. A near-miss to rival-prepatch-ignore-caller (which "
            "diverges on ALL present values), so it is refuted at the "
            "present-explicit-none point that isolates it — varying `override`."
        ),
        "witness": _witness("emptyLabelForTester true (some none)"),
    },
    {
        "id": "rival-truthiness-empty-string",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. The `or`-form's OTHER falsy point, and the one that
        # matters most for refinement: the caller supplied a placeholder that is
        # PRESENT and a string, but the empty one. `rival-truthiness-or-form`
        # above models the issue's form as dropping only the present-explicit-
        # absent value; a real truthiness test also drops the empty string, which
        # `Option (Option String)` CAN express as `some (some "")` and which no
        # other rival in this battery attacks. Correct on every other input;
        # diverges from gold only at that one point, so this is the tightest
        # near-miss the carrier admits.
        "module": _impl(
            "    if allowsBlank then\n"
            "      match override with\n"
            "      | some (some \"\") => return defaultLabel\n"
            "      | _ => return (override.getD defaultLabel)\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "the faithful real patch is the issue's own proposed truthiness form. A "
            "caller-supplied placeholder that is present but the empty string is "
            "falsy, so that form replaces it with the standard fallback, while a "
            "lookup-with-default keeps it verbatim. It passes the lone F2P test "
            "(whose override is truthy) and every P2P, so the suite does NOT "
            "distinguish it from gold — yet a caller who deliberately asked for an "
            "empty placeholder gets the fallback instead. If it verified, the spec "
            "would admit a patch that fails the issue's real intent on the "
            "empty-string sub-domain => SPEC-TOO-WEAK."
        ),
        "rationale": (
            "REJECT from `out = resolvedLabel allowsBlank override` via the "
            "KEEP-CALLER branch at the empty-string point: `getD` returns the "
            "present value `some \"\"`, but the rival falls back to `defaultLabel`. "
            "Refuted at (true, some (some \"\")): gold resolves `some \"\"`, the "
            "rival `some \"None\"`. Distinct from rival-truthiness-or-form (which "
            "diverges at `some none`) and from rival-prepatch-ignore-caller (which "
            "diverges at EVERY present value): this one holds `override` at a "
            "present NON-none value that the other two agree with gold on, adding "
            "a fifth distinct input point and a fourth `override` shape."
        ),
        "witness": _witness("emptyLabelForTester true (some (some \"\"))"),
    },
    {
        "id": "rival-ignore-forbids-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve the caller override REGARDLESS of the flag: drop the forbids
        # branch entirely and always apply `getD`. Correct on both allowed-empty
        # sub-domains, wrong on the forbids branch whenever the caller supplied a
        # value (the P2P sub-domain: a non-blank relation must show no placeholder).
        "module": _impl("    return override.getD defaultLabel"),
        "refinement": (
            "a patch that resolved the caller override even when no empty selection "
            "is allowed would give a relation that admits no empty selection a "
            "non-absent placeholder, FAILING the pre-existing P2P case that asserts "
            "exactly the opposite for that configuration; its faithful real patch "
            "does NOT resolve (it regresses a P2P). Confirmed against the P2P list "
            "in instance.json."
        ),
        "rationale": (
            "REJECT from `out = resolvedLabel allowsBlank override` via the FORBIDS "
            "branch: `allowsBlank = false` must yield `none` regardless of the "
            "caller, but the rival returns `getD`. Refuted at (false, some (some "
            "\"X\")): gold resolves `none`, the rival `some \"X\"`. Discrimination "
            "comes from `allowsBlank = false` — the value no other reject witness "
            "holds at."
        ),
        "witness": _witness("emptyLabelForTester false (some (some \"X\"))"),
    },
    {
        "id": "rival-absent-uses-none",
        "kind": "uniqueness",
        "expect": "reject",
        # Mechanical near-miss on the FALLBACK branch: when the caller supplied
        # nothing, emit no placeholder (`none`) instead of the standard fallback.
        # Correct on the forbids branch and on every caller-present input; wrong
        # only on the allowed-empty / caller-absent sub-domain, where a blank
        # relation with no override must still offer the fallback placeholder.
        "module": _impl(
            "    if allowsBlank then\n"
            "      match override with\n"
            "      | none => return none\n"
            "      | some v => return v\n"
            "    else\n"
            "      return none"),
        "refinement": (
            "a patch that produced no placeholder for a relation that DOES admit an "
            "empty selection, with no caller-supplied value, would drop the empty "
            "choice such a relation must offer, diverging from the standard fallback "
            "on the allowed-empty / no-override case the pre-existing P2P cases "
            "cover; its faithful real patch does not match gold behaviour."
        ),
        "rationale": (
            "REJECT from `out = resolvedLabel allowsBlank override` via the "
            "FALLBACK branch: `allowsBlank = true` with the caller absent must "
            "yield `defaultLabel`, but the rival yields `none`. Refuted at (true, "
            "none): gold resolves `some \"None\"`, the rival `none`. Discrimination "
            "comes from `override = none` (the absent case) — the third distinct "
            "shape of the key-presence carrier, varying `override`."
        ),
        "witness": _witness("emptyLabelForTester true none"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING.
#
# The nagini sibling has 9 SPEC cases (3 soundness/admissibility positives,
# 6 uniqueness rivals) plus an EMPTY AXIOM lane. It contracts a MUTATING dict
# operation: `set_radio_empty_label(permits_empty, kwargs)` genuinely WRITES
# `kwargs[empty_label_key()] = value` and RETURNS `value`, with five Ensures
# clauses — E1/E2 pin the post-STATE of the dict (key present; stored == return),
# E3/E4/E5 pin the returned value across the three input sub-domains. THIS bundle
# models only the purely-functional CORE — the resolution VALUE as a closed
# function of the two inputs (`out = resolvedLabel allowsBlank override`). The
# surrounding dict mutation (E1/E2) is not modeled: Velvet is referentially
# transparent, the method returns a value and mutates nothing. So the value
# clauses E3/E4/E5 port to the three branches of the single pin; the post-state
# clauses E1/E2 have no counterpart (carrier narrowing, not a gap to fabricate).
#
#   nagini case                          -> here                         disposition
#   --------------------------------------------------------------------------------
#   pos-control-reorder                  -> pos-match-reshape            RE-SHAPED
#   admiss-f2p-shaped                    -> admiss-gold-total            RE-AIMED
#   atk-truthiness-or-form               -> rival-truthiness-or-form     PORTED
#   atk-prepatch-unconditional-default   -> rival-prepatch-ignore-caller PORTED
#   atk-store-default-return-caller (E2) -> (none)                       VACUOUS (no dict post-state)
#   atk-no-write (E1)                    -> (none)                       VACUOUS (no dict post-state)
#   atk-forbids-empty-uses-default (E3)  -> rival-ignore-forbids-flag    PORTED (re-aimed)
#   atk-permits-absent-uses-sentinel(E5) -> rival-absent-uses-none       PORTED
#   pos-control-conditional-expr         -> pos-resolved-direct          RE-EXPRESSED
#   AXIOM_TESTS ([])                     -> (none)                       DROPPED (G-AX lane)
#   frame-mutation                       -> (none)                       VACUOUS
#   divergence                           -> (none)                       NO NAGINI CASE; partial hole noted
#
#   (audit additions, no nagini counterpart)
#   (new)                                -> pos-elim-reshape             ADDED (audit)
#   (new)                                -> rival-truthiness-empty-string ADDED (audit)
#
# 9 velvet SPEC cases: 3 soundness, 1 admissibility, 5 uniqueness. Every nagini
# case that attacks a clause THIS bundle models is ported; the two that attack
# the un-modeled dict post-state (E1/E2) are vacuous here and are NOT fabricated
# — DEMONSTRATED, not asserted: both were written out as velvet impls (drop the
# write / store a wrong value while returning the right one) and both VERIFY
# (exit 0), because with the return as the sole observable the "wrong stored
# value" is a dead local and "omitting the write" removes nothing. A rival that
# verifies against the frozen spec while being gold-equivalent is vacuous by
# definition, so shipping them would have added two cases attesting nothing.
#
# RE-SHAPED (pos-control-reorder -> pos-match-reshape): the nagini positive
#   hoists the not-permits-empty branch first (flat elif chain). On this carrier
#   the flag branch is a two-arm `if`, and the interesting reshape is HOW the
#   caller override is resolved — the frozen impl uses `Option.getD`, the reshape
#   an explicit `match` on the key-presence carrier. Same value flow, different
#   control shape; the frozen `loom_solve` closes the byte-identical obligation.
# RE-EXPRESSED (pos-control-conditional-expr -> pos-resolved-direct): the nagini
#   honest cheapest impl is the one-line conditional-expression form. On this
#   carrier the cheapest honest impl is `return resolvedLabel allowsBlank
#   override` — the grounded pin returned directly. Same argument (the pin is
#   satisfiable only by the real resolution; no wrong echo verifies), expressed
#   as a loop-free correct impl.
# RE-AIMED (admiss-f2p-shaped -> admiss-gold-total): the nagini case built a
#   fresh F2P-shaped dict inside the impl region and asserted the self-call's
#   Requires is establishable and E4 holds. This method has no `require` and no
#   heap, so that probe is vacuous; re-aimed at the residual total-domain risk
#   (post-image satisfiability), witnessed by the frozen impl discharging the
#   ensures.
# PORTED (rivals): atk-prepatch-unconditional-default (ignore the caller in the
#   allowed-empty branch) -> rival-prepatch-ignore-caller [KEEP-CALLER branch];
#   atk-truthiness-or-form (the issue's `or`-form drops a falsy present value)
#   -> rival-truthiness-or-form [KEEP-CALLER, present-explicit-none point];
#   atk-forbids-empty-uses-default (E3) -> rival-ignore-forbids-flag, re-aimed to
#   the FORBIDS branch as "resolve regardless of the flag" (a value even when no
#   empty selection is allowed — the same P2P regression); atk-permits-absent-
#   uses-sentinel (E5) -> rival-absent-uses-none [FALLBACK branch]. Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   gold (two real builds per case, confirmed with scripts/lean_verify.sh).
# VACUOUS (E1/E2 post-state: atk-store-default-return-caller, atk-no-write): both
#   nagini rivals attack the coupling between the dict's post-STATE and the
#   returned value (write a wrong value into the key while returning the right
#   one; or skip the write entirely). This bundle models the resolution VALUE
#   only — there is no in-place dict, no `mut` binder, no post-state to decouple
#   from the return. The clauses E1/E2 have no counterpart on the referentially-
#   transparent carrier, so these two rivals are not expressible and are NOT
#   fabricated (carrier narrowing).
# VACUOUS (frame-mutation): the nagini file already records `has_readonly_input`
#   as False (the dict is fully written, not an `Acc(.,1/2)` read-only input), so
#   the canonical permission-mutation attack does not apply even there. On this
#   backend a fortiori: no `mut` binder, no heap, no aliasing, no permission
#   system. No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# DROPPED (AXIOM_TESTS): the nagini file has no @ContractOnly axioms
#   (AXIOM_TESTS == []); the one deep-model reference here (`defaultLabel` ==
#   `gettext("None")`) is G-AX's job (axiom_check.py / mapping.md §3.1). The
#   G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The only impl-constraining clause is the pin
#   `out = resolvedLabel allowsBlank override`. Its three branches are each
#   attacked: FORBIDS (rival-ignore-forbids-flag), KEEP-CALLER
#   (rival-prepatch-ignore-caller on all present values, rival-truthiness-or-form
#   on the present-explicit-none near-miss), FALLBACK (rival-absent-uses-none).
#   The two input binders are varied by the reject witnesses:
#     allowsBlank — true (4 rivals), false (rival-ignore-forbids-flag): both values.
#     override    — some (some "X") (prepatch, ignore-forbids), some none
#                   (truthiness), some (some "") (truthiness-empty-string), none
#                   (absent): all THREE shapes of the key-presence carrier
#                   (present-value / present-explicit-absent / absent), with the
#                   present-value shape probed at BOTH a truthy and a falsy
#                   string. No binder is held fixed by every witness.
#   pts = 5 distinct input points: (true, some (some "X")), (true, some none),
#   (false, some (some "X")), (true, none), (true, some (some "")). The variation
#   is MEANINGFUL rather than two spellings of one point: gold's resolution
#   differs from at least one rival at each, and each point is the UNIQUE
#   discriminator for its rival (verified — every witness fails on gold by a
#   `decide` that proves the proposition false). All three positives and the
#   admissibility case defend the pin on the whole domain, and the admissibility
#   case additionally pins the resolved VALUE at each of the four sub-domains, so
#   the reject lane is provably not aimed at a phantom branch.
#
# WITNESS MECHANICS: the postcondition mentions no opaque callee (`defaultLabel`
#   is the literal `some "None"`), so the tester+`decide` path is LIVE. Every
#   witness extracts the executable program and refutes the pin directly via the
#   Velvet tester at one concrete input: each rival is loop-free so its tester
#   `decide`s to `false`, and gold's tester `decide`s to `true`, so the same
#   `= false` witness elaborates against the rival and FAILS against gold. No
#   `require` clause, so no input is vacuously excluded; no witness binds a
#   hypothesis, so no consistency probe is needed (witness_head_binders == "" for
#   all five, so the gate builds no third file). All FIVE re-checked with
#   scripts/lean_verify.sh during the audit: rival exit 0, gold exit 1, and gold's
#   failure text is `Tactic 'decide' proved that the proposition ... is false` —
#   a semantic refutation of the concrete claim, which is what distinguishes a
#   discriminator from a witness that fails on gold for a syntactic reason.
AXIOM_TESTS = []
