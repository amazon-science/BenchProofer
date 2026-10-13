"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8551 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct buildCrossRef`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

=========================================================================
DEFENDED SURFACE  (one contracted method)
=========================================================================

  buildCrossRef (curModule curClass : ScopeName) (domain kind target : List Char)
      return (out : CrossRef)
    require kind ≠ []
    ensures out = scopedRef curModule curClass domain kind target
    ensures out.scopeModule = curModule
    ensures out.scopeClass  = curClass
    ensures out.preferSpecific = true
    ensures out.kind   = normalizeKind kind target
    ensures out.target = normalizeTarget target

The method builds the cross-reference descriptor for an inline type specifier.
The behaviour AT ISSUE is that the descriptor must record the documentation
scope in effect where it was written — the current module and the current
class — so that an unqualified target resolves against the current scope rather
than matching the same short name in every (sub)module (the spurious
"more than one target" ambiguity the issue reports).

The post-image pins SIX top-level clauses, of which the master clause E0
(``out = scopedRef ...``) fixes the entire descriptor as a total function of the
method's own inputs (the ``pure`` region computes it; there is no opaque oracle
to echo — UNGROUNDED-ORACLE ECHO is N/A). The five projection clauses expose the
independently-observable fields:

  * (E1) ``scopeModule = curModule`` — the current-module context, an IDENTITY on
         the ``curModule`` input.  THE behaviour at issue.
  * (E2) ``scopeClass  = curClass``  — the current-class context, an IDENTITY on
         the ``curClass`` input.  THE behaviour at issue.
  * (E3) ``preferSpecific = true``   — the prefer-specific resolution flag.
  * (E4) ``kind   = normalizeKind kind target`` — the normalized reference kind
         (a class-kind reference to the literal target ``None`` becomes an
         object-kind reference; pre-existing behaviour inside the modeled slice).
  * (E5) ``target = normalizeTarget target`` — the stored target with a leading
         ``.``/``~`` marker stripped (pre-existing behaviour).

The descriptor also carries ``domain`` verbatim (folded into E0), the resolution
domain read downstream.

The FIVE INPUT binders are: ``curModule`` (E1), ``curClass`` (E2), ``domain``
(E0), ``kind`` (E4/E0), ``target`` (E4/E5/E0).  Only ``kind`` is
domain-restricted (``require kind ≠ []``: a kindless request takes a
display-only path that builds no descriptor at all — outside the modeled
boundary, mapping.md §1); the other four are free and the post-image must hold
for EVERY value.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see footer for the
case-by-case accounting):

  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling notes the
    class is already vacuous even on its carrier (the inputs are pure immutable
    value sequences holding NO heap permission; the only heap object is the
    freshly-allocated node), and it is doubly so here: Lean/Velvet are
    referentially transparent, every parameter is an immutable value, this bundle
    declares no ``mut`` binder, there is no heap and no aliasing. No read-only
    input to overwrite, no permission system to trip. No substitute is fabricated.
  * DIVERGENCE / NON-TERMINATION: INAPPLICABLE as a shipped reject case, and
    CLOSED BY THE SEMANTICS rather than vacuous. The sibling carries no
    ``diverge-*`` / ``nonterm-*`` case, so nothing is dropped in the port, and the
    frozen impl is a straight-line record construction with no loop to diverge, so
    no divergence rival is written here. The "simply vacuous" verdict is withdrawn:
    a rival owns the whole impl region and may splice a loop the frozen body lacks,
    so the class IS expressible; what refuses it is the descent obligation. This
    bundle runs under ``loom.semantics.termination "total"`` (mapping.md §1 pins
    total correctness deliberately), under which a postcondition is claimed of ALL
    runs, not only terminating ones, so the verifier demands a decreasing measure
    on every loop AND discharges its descent. The option cannot drift from the
    file's ``open TotalCorrectness DemonicChoice``, because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` with body
    ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. Not a spec hole here.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``scopedRef curModule curClass domain kind target`` and its projections;
    ``scopedRef`` / ``normalizeKind`` / ``normalizeTarget`` are concrete ``def``s
    in the ``pure`` region computing the descriptor from the method's own
    arguments (the ``axioms`` region is empty; no opaque answer key to echo). The
    unique satisfier IS the grounded construction, so there is no wrong echo to
    build; the honest controls are the cheapest faithful reshapes (the ``pos-*``
    cases).
  * PARTIAL-DOMAIN — exercised. The scope-dropping rivals (E1/E2) are CORRECT on
    the sub-domain where the dropped scope was already ``none`` (``none = none``),
    and wrong exactly on the present-scope sub-domain the F2P exercises (module
    "example", class "Class"); the ``normalizeTarget`` rival is correct on every
    target that carries no leading ``.``/``~`` marker, and wrong on the ones that
    do; the ``normalizeKind`` rival is correct on every non-``None`` target and
    wrong on the literal ``None`` the P2P annotation test exercises.

WITNESS MECHANICS ON THIS BUNDLE. The carrier is FULLY TRANSPARENT: ``CrossRef``
derives ``DecidableEq`` and every field is a ``List Char`` / ``Option (List
Char)`` / ``Bool`` literal, and the frozen impl is STRAIGHT-LINE (no loop, no
opaque callee), so the extracted program reduces fully under ``decide`` — no
conditioning on an opaque term is needed. Each reject rival carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``buildCrossRefTester <curModule> <curClass> <domain> <kind> <target> = false``
at ONE concrete input, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict, closed by ``decide``. Both
halves were checked out-of-band with ``scripts/lean_verify.sh``: every witness
ELABORATES against its rival (exit 0) and FAILS against the frozen solution
(``decide`` proves the proposition false), so each rejection is a genuine spec
refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no ``:|``
callee stub; ``scopedRef`` / ``normalizeKind`` / ``normalizeTarget`` are deep
models (A-reference), refinement-checked by ``conformance_check.py`` (G-CONF),
not axiomatized. Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8551"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything from the method's `-- impl-start`
# through `-- impl-end` (marker lines included). Every rival and reshape edits
# ONLY this block (and, for reshapes/admissibility, the elided `prove_correct`
# tactic body), so the spec view is untouched and same_spec holds by
# construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- `None` is not a type: a class-kind reference to the literal target `None`\n"
    "    -- is built as an object-kind reference instead (unchanged behaviour)\n"
    "    let kindAdj :=\n"
    "      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then\n"
    "        ['o','b','j']\n"
    "      else kind\n"
    "    -- the base reference built for this target, carrying the raw target\n"
    "    let base : CrossRef :=\n"
    "      { domain := domain, kind := kindAdj, target := target,\n"
    "        preferSpecific := false, scopeModule := none, scopeClass := none }\n"
    "    -- ask resolution to prefer the most specific match\n"
    "    let withSpec := { base with preferSpecific := true }\n"
    "    -- record the documentation scope in effect onto the reference, so a\n"
    "    -- same-scope target can be preferred over equally-named targets elsewhere\n"
    "    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }\n"
    "    -- normalize an explicit-prefix target (leading scope/short-name marker)\n"
    "    let result :=\n"
    "      match target with\n"
    "      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }\n"
    "                     else withScope\n"
    "      | []        => withScope\n"
    "    return result\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = (
    "prove_correct buildCrossRef by\n"
    "  loom_solve <;>\n"
    "    (simp only [scopedRef, normalizeKind, normalizeTarget]\n"
    "     cases target with\n"
    "      | nil => simp\n"
    "      | cons c rest => by_cases h : c = '.' ∨ c = '~' <;> simp [h])"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (proof kept)."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `buildCrossRefTester <curModule> <curClass> <domain> <kind> <target> =
# ---- false` says the extracted program's result violates the method's
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask the
# ---- verdict. `CrossRef` derives DecidableEq, so each witness closes by
# ---- `decide` on fully-concrete literal inputs (no opaque term to condition on).
def _witness(call):
    return ("extract_program_for buildCrossRef\n"
            "prove_precondition_decidable_for buildCrossRef\n"
            "prove_postcondition_decidable_for buildCrossRef\n"
            "derive_tester_for buildCrossRef\n\n"
            f"example : {call} = false := by\n  decide\n")


# The gold impl body (kindAdj / base / withSpec / withScope / result). Rivals are
# expressed as minimal edits of this text so that ONLY the attacked field moves.
_GOLD_BODY = (
    "    let kindAdj :=\n"
    "      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then\n"
    "        ['o','b','j']\n"
    "      else kind\n"
    "    let base : CrossRef :=\n"
    "      { domain := domain, kind := kindAdj, target := target,\n"
    "        preferSpecific := false, scopeModule := none, scopeClass := none }\n"
    "    let withSpec := { base with preferSpecific := true }\n"
    "    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }\n"
    "    let result :=\n"
    "      match target with\n"
    "      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }\n"
    "                     else withScope\n"
    "      | []        => withScope\n"
    "    return result"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify; else the post-image is SPEC-TOO-STRONG. Each
    # keeps the returned descriptor identical on every input and only reshapes
    # the executable surface.
    # =====================================================================
    {
        "id": "pos-locals-single-record",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the prefer-specific flag and both scope contexts to local
        # variables, compute the normalized target inline, then build the whole
        # descriptor in ONE record literal (no `with`-update chain). Same value on
        # every input (assignment preserves the contexts; the inline `match`
        # equals `normalizeTarget`), so E0-E5 all still hold. The do-block changed
        # shape (the frozen `cases target` script no longer applies verbatim), so
        # the proof is retuned to `loom_solve <;> simp_all [...]`.
        "module": _impl_reproved(
            "    let kindAdj : List Char :=\n"
            "      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then\n"
            "        ['o','b','j']\n"
            "      else kind\n"
            "    let flag : Bool := true\n"
            "    let m : ScopeName := curModule\n"
            "    let c : ScopeName := curClass\n"
            "    let tgt : List Char :=\n"
            "      match target with\n"
            "      | ch :: rest => if ch = '.' ∨ ch = '~' then rest else target\n"
            "      | []         => target\n"
            "    let result : CrossRef :=\n"
            "      { domain := domain, kind := kindAdj, target := tgt,\n"
            "        preferSpecific := flag, scopeModule := m, scopeClass := c }\n"
            "    return result",
            "prove_correct buildCrossRef by\n"
            "  loom_solve <;> simp_all [scopedRef, normalizeKind, normalizeTarget]"),
        "rationale": "binding the flag/contexts to locals and building the whole "
                     "descriptor in one record literal (inlining the target "
                     "normalization) computes the IDENTICAL `out` on every input, "
                     "so E0-E5 are unchanged; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on record-construction shape.",
    },
    {
        "id": "pos-scope-before-flag",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: record the documentation scope FIRST, then set the
        # prefer-specific flag (the two `with`-updates commute — they touch
        # disjoint fields). Same descriptor on every input. The target `match`
        # keeps the gold shape, so the frozen proof still closes verbatim.
        "module": _impl(
            "    let kindAdj :=\n"
            "      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then\n"
            "        ['o','b','j']\n"
            "      else kind\n"
            "    let base : CrossRef :=\n"
            "      { domain := domain, kind := kindAdj, target := target,\n"
            "        preferSpecific := false, scopeModule := none, scopeClass := none }\n"
            "    let withScope := { base with scopeModule := curModule, scopeClass := curClass }\n"
            "    let withSpec := { withScope with preferSpecific := true }\n"
            "    let result :=\n"
            "      match target with\n"
            "      | c :: rest => if c = '.' ∨ c = '~' then { withSpec with target := rest }\n"
            "                     else withSpec\n"
            "      | []        => withSpec\n"
            "    return result"),
        "rationale": "swapping the order of the two field-disjoint record updates "
                     "(record the scope, then set the flag) leaves the built "
                     "descriptor identical on every input, so E0-E5 hold and the "
                     "frozen proof closes verbatim; a correct reshape must verify, "
                     "else SPEC-TOO-STRONG on update order.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries ONE precondition (`kind ≠ []`), which
    # the F2P scenario satisfies (`kind = 'class'`). The residual admissibility
    # risk on this spec is that the scope-recording clause is DEGENERATE at the
    # interesting point — a spec that only ever saw `none` scopes would read like
    # a live one. This case discharges an in-region assert pinning that the
    # required behaviour genuinely records a PRESENT scope (module "example",
    # class "Class") — the exact F2P scenario — rather than collapsing it to
    # `none`. The impl is kept verbatim so the ensures still discharge; the proof
    # is retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-present-scope-recorded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- admissibility (F2P scenario): kind 'class' is non-empty (the\n"
            "    -- precondition holds), and under a PRESENT module/class scope the\n"
            "    -- built descriptor records that scope rather than collapsing to none\n"
            "    assert (with_name_prefix `assert\n"
            # AUDIT FIX: the literals were abbreviated stand-ins (`['e','x']` /
            # `['C']`) while this case's own prose claimed "the exact F2P
            # scenario". Abbreviated literals discharge just as easily, so the
            # case passed while demonstrating a DIFFERENT point than it claimed.
            # Now stated at the genuine F2P scope names (module "example",
            # class "Class"); re-checked out of band, exit 0.
            "      ((['c','l','a','s','s'] : List Char) ≠ [] ∧\n"
            "       (scopedRef (some ['e','x','a','m','p','l','e'] : ScopeName)\n"
            "          (some ['C','l','a','s','s'] : ScopeName)\n"
            "          ['p','y'] ['c','l','a','s','s'] ['s','t','r']).scopeModule\n"
            "            = some ['e','x','a','m','p','l','e'] ∧\n"
            "       (scopedRef (some ['e','x','a','m','p','l','e'] : ScopeName)\n"
            "          (some ['C','l','a','s','s'] : ScopeName)\n"
            "          ['p','y'] ['c','l','a','s','s'] ['s','t','r']).scopeClass\n"
            "            = some ['C','l','a','s','s']))\n"
            + _GOLD_BODY,
            "prove_correct buildCrossRef by\n"
            "  loom_solve <;>\n"
            "    (first\n"
            "     | decide\n"
            "     | (simp only [scopedRef, normalizeKind, normalizeTarget]\n"
            "        cases target with\n"
            "         | nil => simp\n"
            "         | cons c rest => by_cases h : c = '.' ∨ c = '~' <;> simp [h]))"),
        "rationale": "the scope-recording behaviour is non-degenerate at the "
                     "F2P-shaped point: with a present module/class scope the "
                     "built descriptor records `scopeModule = some ...` and "
                     "`scopeClass = some ...` (not `none`), so the identity "
                     "clauses E1/E2 really fork on a present scope. The in-region "
                     "assert must discharge (else the recording would be "
                     "degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so the ensures still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P (or would regress a P2P test).
    # =====================================================================
    {
        "id": "weak-drop-module",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug (module half): build the descriptor without recording the
        # current module — scopeModule := none. Exactly the prepatch state (the
        # descriptor carried no `py:module`). E1 fails whenever curModule is
        # present.
        "module": _impl(_GOLD_BODY.replace(
            "scopeModule := curModule, scopeClass := curClass",
            "scopeModule := none, scopeClass := curClass")),
        "refinement": "this IS the prepatch state for the module half: the built "
                      "descriptor carries no current-module context, so a later "
                      "resolution step receives no module and falls to the fuzzy "
                      "'ends-with .name' search, which returns EVERY same-named "
                      "target in every (sub)module — the spurious 'more than one "
                      "target' ambiguity. The F2P test (`test_info_field_list`) "
                      "asserts the produced cross-reference carries "
                      "`py:module='example'`; with the module context dropped "
                      "that attribute is absent and the assertion FAILS. It would "
                      "NOT resolve — a true verify-not-resolve break.",
        "rationale": "REJECT from E1 (`out.scopeModule = curModule`): with the "
                     "module recorded as `none` the built descriptor's scopeModule "
                     "is `none`, but at a present module (`curModule = some "
                     "'example'`) the post-image demands `some 'example'`. Refuted "
                     "at the F2P scenario input (module 'example', class 'Class', "
                     "kind 'class', target 'str') — where the class half is also "
                     "present, so E1 alone carries the rejection.",
        "witness": _witness(
            'buildCrossRefTester (some "example".toList) (some "Class".toList) '
            '"py".toList "class".toList "str".toList'),
    },
    {
        "id": "weak-drop-class",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug (class half): build the descriptor without recording the
        # current class — scopeClass := none. Mirrors the prepatch state (no
        # `py:class`). PARTIAL-DOMAIN: correct on the curClass-is-none sub-domain
        # (none = none) but wrong when a class context is present (the F2P).
        "module": _impl(_GOLD_BODY.replace(
            "scopeModule := curModule, scopeClass := curClass",
            "scopeModule := curModule, scopeClass := none")),
        "refinement": "this IS the prepatch state for the class half: the built "
                      "descriptor carries no current-class context. The F2P "
                      "scenario registers a current class and asserts the produced "
                      "cross-reference carries `py:class='Class'`; with the class "
                      "context dropped that attribute is absent and the assertion "
                      "FAILS. (Correct only on the curClass-is-none sub-domain; the "
                      "F2P exercises a present class.) It would NOT resolve — a "
                      "true verify-not-resolve break.",
        "rationale": "PARTIAL-DOMAIN REJECT from E2 (`out.scopeClass = curClass`): "
                     "with the class recorded as `none`, at a present class "
                     "(`curClass = some 'C'`) the post-image demands `some 'C'`. "
                     "Refuted at a NO-module, present-class input (module `none`, "
                     "class 'C', kind 'class', target 'int') — varying both scope "
                     "binders against weak-drop-module (there module present / "
                     "class present; here module ABSENT / class present), and "
                     "isolating E2 as the sole violated clause.",
        "witness": _witness(
            'buildCrossRefTester none (some "C".toList) '
            '"py".toList "class".toList "int".toList'),
    },
    {
        "id": "weak-drop-specific-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the prefer-specific flag: leave preferSpecific := false. Mirrors NOT
        # setting `refspecific = True`. E3 fails on every input.
        "module": _impl(_GOLD_BODY.replace(
            "let withSpec := { base with preferSpecific := true }",
            "let withSpec := { base with preferSpecific := false }")),
        "refinement": "a counterpart that does not set the prefer-specific flag "
                      "leaves the descriptor without the marker that asks "
                      "resolution to prefer the most specific match; the "
                      "unqualified name is then resolved by the non-specific "
                      "search path (the prefer-specific module/class cascade never "
                      "runs), so even with the scope recorded the contextual "
                      "single resolution does not occur. The F2P's expected "
                      "single contextual resolution does not happen and the test "
                      "FAILS. It would NOT resolve.",
        "rationale": "REJECT from E3 (`out.preferSpecific = true`): the rival "
                     "leaves the flag `false`, so the post-image's `= true` is "
                     "violated on EVERY input. Refuted at a present-scope input "
                     "(module 'm', class 'C', kind 'class', target 'str'); this is "
                     "the only rival attacking E3, the clause the F2P node-shape "
                     "assertions do not themselves observe (it drives the later "
                     "resolution step) — see the footer's disclosure.",
        "witness": _witness(
            'buildCrossRefTester (some "m".toList) (some "C".toList) '
            '"py".toList "class".toList "str".toList'),
    },
    {
        "id": "weak-target-prefix-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the leading-marker normalization: store the raw target even when it
        # begins with `.`/`~`. Mirrors dropping the `startswith(('.','~'))` block.
        # E5 fails on any target with a leading `.` or `~`; PARTIAL-DOMAIN (correct
        # on every marker-free target).
        "module": _impl(_GOLD_BODY.replace(
            "    let result :=\n"
            "      match target with\n"
            "      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }\n"
            "                     else withScope\n"
            "      | []        => withScope\n"
            "    return result",
            "    let result := withScope\n"
            "    return result")),
        "refinement": "a counterpart that stores the raw target verbatim omits the "
                      "leading-`.`/`~` normalization that every inline type "
                      "specifier relies on to select the alternate scope/short-name "
                      "lookup mode; a target written `.mod.Cls` or `~mod.Cls` is "
                      "then stored WITH its marker and resolves against the wrong "
                      "name, so a build exercising a marked inline type reference "
                      "regresses. A genuine PARTIAL-DOMAIN break on the "
                      "leading-marker sub-domain; it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN REJECT from E5 (`out.target = normalizeTarget "
                     "target`): the rival stores `target` verbatim, but for a "
                     "target beginning with `.`/`~` the post-image demands the "
                     "marker stripped. Refuted at a NO-scope, leading-`.` target "
                     "(module `none`, class `none`, kind 'class', target '.foo') — "
                     "the leading-marker sub-domain where it diverges and the "
                     "scope/kind rivals do not.",
        "witness": _witness(
            'buildCrossRefTester none none '
            '"py".toList "class".toList ".foo".toList'),
    },
    {
        "id": "weak-kind-not-normalized",
        "kind": "uniqueness",
        "expect": "reject",
        # Skip the `class`+`None` -> `obj` kind rewrite: keep the requested kind
        # verbatim. Mirrors dropping the pre-existing `if rolename == 'class' and
        # target == 'None': rolename = 'obj'` guard. E4 fails at (kind='class',
        # target='None'); PARTIAL-DOMAIN (correct on every other kind/target).
        "module": _impl(_GOLD_BODY.replace(
            "    let kindAdj :=\n"
            "      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then\n"
            "        ['o','b','j']\n"
            "      else kind\n",
            "    let kindAdj := kind\n")),
        "refinement": "a counterpart that stores the requested kind verbatim drops "
                      "the pre-existing `None`-is-not-a-type rewrite: a class-kind "
                      "reference to the literal target `None` is kept as a "
                      "class-kind reference instead of an object-kind one. The P2P "
                      "test `test_parse_annotation` asserts that the annotation "
                      "`None` produces a reference of kind `obj` (not `class`); "
                      "with the rewrite dropped that reference is kind `class` and "
                      "the assertion FAILS, regressing a passing test. A genuine "
                      "PARTIAL-DOMAIN break on the (class, None) point; it would "
                      "NOT resolve.",
        "rationale": "PARTIAL-DOMAIN REJECT from E4 (`out.kind = normalizeKind kind "
                     "target`): the rival returns `kind` verbatim, but at "
                     "(kind='class', target='None') the post-image demands 'obj'. "
                     "Refuted at exactly that point (module `none`, class `none`, "
                     "domain 'js', kind 'class', target 'None') — the single "
                     "kind/target combination where the rewrite fires and no other "
                     "rival's witness lands.",
        "witness": _witness(
            'buildCrossRefTester none none '
            '"js".toList "class".toList "None".toList'),
    },
    {
        # AUDIT ADDITION. `weak-target-prefix-ignored` drops the WHOLE
        # leading-marker normalization, so its witness lands on the `.` marker
        # and the `~` disjunct of E5 was never separately probed: a rival that
        # honours one marker and not the other passed unattacked. This rival
        # strips `.` but not `~` — correct on every target except a `~`-marked
        # one, the narrowest partial domain in E5.
        "id": "weak-tilde-marker-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GOLD_BODY.replace(
            "if c = '.' ∨ c = '~' then", "if c = '.' then")),
        "refinement": "a counterpart that recognizes only ONE of the two leading "
                      "markers still stores the other marker verbatim: a target "
                      "written with the short-name marker keeps that character in "
                      "the stored target and resolves against a name that is not "
                      "registered, so a marked inline type reference fails to "
                      "resolve while the unmarked and dot-marked ones keep "
                      "working. A genuine PARTIAL-DOMAIN break confined to the "
                      "second marker; it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN REJECT from E5 (`out.target = "
                     "normalizeTarget target`) on the SECOND disjunct of the "
                     "marker test, which weak-target-prefix-ignored's witness "
                     "does not reach (that one is refuted at a leading-'.' "
                     "target). Refuted at a leading-'~' target (module `none`, "
                     "class `none`, kind 'class', target '~foo'), where the "
                     "post-image demands the marker stripped and the rival keeps "
                     "it.",
        "witness": _witness(
            'buildCrossRefTester none none '
            '"py".toList "class".toList "~foo".toList'),
    },
    {
        # AUDIT ADDITION. Both scope clauses were only ever attacked by rivals
        # that ERASE a scope (`:= none`). A rival that records both scopes but
        # CROSSES them satisfies "the descriptor carries a scope" and is even
        # correct on the whole symmetric sub-domain (curModule = curClass, which
        # includes the both-`none` case), so it probes E1/E2 as a matched PAIR
        # rather than as two independent erasures.
        "id": "weak-scopes-crossed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GOLD_BODY.replace(
            "scopeModule := curModule, scopeClass := curClass",
            "scopeModule := curClass, scopeClass := curModule")),
        "refinement": "a counterpart that records the two scope contexts into "
                      "each other's slot stamps the descriptor with a module "
                      "name where the class name belongs and vice versa; "
                      "resolution then searches a scope that does not exist, so "
                      "the same-scope preference cannot fire and the unqualified "
                      "name still resolves ambiguously (or not at all). The F2P "
                      "asserts the produced cross-reference carries the module "
                      "attribute equal to the enclosing module name and the class "
                      "attribute equal to the enclosing class name; with the two "
                      "crossed BOTH assertions carry the wrong value and FAIL. It "
                      "would NOT resolve.",
        "rationale": "REJECT from E1 and E2 JOINTLY (`out.scopeModule = "
                     "curModule`, `out.scopeClass = curClass`): the rival "
                     "satisfies neither at any input where the two scope "
                     "arguments differ, while carrying a present scope in each "
                     "field — so it is not caught by 'the scope is missing' but "
                     "by the scopes being MATCHED to their own binders. Correct "
                     "on the symmetric sub-domain (curModule = curClass, "
                     "including both-`none`), which is why the erasure rivals' "
                     "witnesses do not cover it. Refuted at an asymmetric input "
                     "(module 'm', class `none`, kind 'class', target 'str').",
        "witness": _witness(
            'buildCrossRefTester (some "m".toList) none '
            '"py".toList "class".toList "str".toList'),
    },
    {
        "id": "weak-domain-hardcoded",
        "kind": "uniqueness",
        "expect": "reject",
        # Hard-code the resolution domain instead of passing it through. Attacks
        # the domain field folded into master clause E0. E0 fails whenever the
        # requested domain differs from the hardcoded one.
        "module": _impl(_GOLD_BODY.replace(
            "{ domain := domain, kind := kindAdj",
            "{ domain := ['p','y'], kind := kindAdj")),
        "refinement": "a counterpart that hard-codes the resolution domain (rather "
                      "than threading the requested one through) mislabels the "
                      "reference domain for any request outside the hardcoded "
                      "value, so resolution consults the wrong domain's object "
                      "inventory and the reference fails to resolve where it "
                      "should. The F2P asserts the produced reference carries "
                      "`refdomain='py'`; a build whose field registration supplies "
                      "a different domain would carry the wrong one. It would NOT "
                      "resolve for the mismatched-domain sub-domain.",
        "rationale": "REJECT from E0 (`out = scopedRef ... domain ...`), whose "
                     "`domain` component the master clause pins to the input: the "
                     "rival's descriptor has `domain = 'py'` regardless, so at a "
                     "request whose domain input differs from 'py' the post-image "
                     "is violated. Refuted at a present-module input whose domain "
                     "is 'func' (module 'm', class `none`, domain 'func', kind "
                     "'exc', target 'str') — varying the `domain` binder, which "
                     "no other rival moves off 'py', AND the `kind` binder off "
                     "'class' (this violation is independent of the kind, so the "
                     "witness also demonstrates the spec's dependence on a "
                     "non-'class' kind).",
        "witness": _witness(
            'buildCrossRefTester (some "m".toList) none '
            '"func".toList "exc".toList "str".toList'),
    },
    {
        # AUDIT ADDITION (second audit pass). E5 (`out.target = normalizeTarget
        # target`) has TWO branches: the STRIP branch (a leading `.`/`~` is
        # removed) and the IDENTITY branch (any other target is stored
        # verbatim). Both marker rivals attack the strip branch only — they
        # under-strip, so they agree with the frozen impl on every marker-free
        # target. Checked mechanically across all eight retained rivals: on
        # targets 'str'/'int'/'None'/'Cls' NOT ONE of them produces a `target`
        # field differing from the frozen impl's, so an impl that REWRITES a
        # marker-free target passed the whole battery unattacked. This rival
        # over-writes it: it pre-qualifies the stored target with the current
        # module (the plausible alternative "fix" for the ambiguity — resolve by
        # rewriting the name instead of by recording the scope) while keeping
        # BOTH scope fields, the flag, the domain and the kind exactly right, so
        # no other clause is disturbed and E5's identity branch carries the
        # rejection alone. This is also the clause-analogue the port's own
        # accounting claimed was "already attacked head-on" when it dropped the
        # sibling's `weak-pre-qualify-target`; it was not.
        "id": "weak-target-prequalified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GOLD_BODY.replace(
            "    let result :=\n"
            "      match target with",
            "    let withScope := { withScope with target := (match curModule with\n"
            "                        | some m => m ++ ['.'] ++ target\n"
            "                        | none   => target) }\n"
            "    let result :=\n"
            "      match target with")),
        "refinement": "a counterpart that resolves the ambiguity by REWRITING the "
                      "stored target into a scope-qualified name — rather than by "
                      "recording the documentation scope and letting resolution "
                      "prefer the same-scope match — changes the target every "
                      "consumer reads. The stored target is no longer the name the "
                      "author wrote, so the reference's display text and its "
                      "resolution key diverge: a target that is legitimately "
                      "resolvable in a parent scope no longer matches anything "
                      "under the rewritten name, and the reference breaks for "
                      "every inline type specifier written under a module scope. "
                      "The F2P asserts the produced cross-reference keeps the "
                      "ORIGINAL unqualified target while carrying the scope "
                      "attributes; with the target pre-qualified that assertion "
                      "FAILS. It would NOT resolve.",
        "rationale": "REJECT from E5 (`out.target = normalizeTarget target`) on "
                     "the IDENTITY branch of the marker test — the branch neither "
                     "marker rival reaches, since both UNDER-strip and therefore "
                     "agree with the required target on every marker-free input. "
                     "This rival OVER-writes it: at a marker-free target under a "
                     "present module the post-image demands the target verbatim "
                     "and the rival supplies a module-qualified one. Refuted at "
                     "(module 'pkg.mod', class `none`, kind 'class', target "
                     "'Cls') — a marker-free target with a present module, the "
                     "sub-domain where the rewrite fires; both scope fields, the "
                     "flag, the domain and the kind are left correct, so E5 alone "
                     "carries the rejection.",
        "witness": _witness(
            'buildCrossRefTester (some "pkg.mod".toList) none '
            '"py".toList "class".toList "Cls".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The nagini sibling has 7 SPEC cases (2 soundness positives, 1 admissibility,
# 4 uniqueness) and 0 AXIOM_TESTS. Its carrier is `PSeq[int]` tokens and a
# freshly-allocated `RefNode` with fields (target, specific, ctx_mod, ctx_cls);
# its postcondition pins P1 target-identity, P2 prefer-specific flag, P3 ctx_mod
# identity, P4 ctx_cls identity, P5/P6 the resolve_count/resolve_name resolution
# facts (which the sibling notes are ENTAILED by P1/P3/P4 + precondition — no
# opaque oracle). This backend models the SAME builder but with a RICHER, fully
# transparent carrier: a `CrossRef` structure pinned field-by-field, PLUS two
# pre-existing normalizations the sibling folded away — `normalizeKind`
# (`class`+`None` -> `obj`) and `normalizeTarget` (leading `.`/`~` stripping) —
# and it carries a real precondition (`kind ≠ []`). The master clause E0
# (`out = scopedRef ...`) plays the role of the sibling's "the node records the
# genuine context" observation; the projection clauses E1-E5 are its
# field-identity clauses made individually observable.
#
#   sibling case                  -> here                            disposition
#   -------------------------------------------------------------------------
#   pos-local-reshape             -> pos-locals-single-record        PORTED
#   pos-explicit-resolve-asserts  -> pos-scope-before-flag           RE-AIMED
#   admiss-issue-scenario         -> admiss-present-scope-recorded   RE-AIMED
#   weak-drop-module              -> weak-drop-module                PORTED
#   weak-drop-class               -> weak-drop-class                 PORTED
#   weak-drop-specific-flag       -> weak-drop-specific-flag         PORTED
#   weak-pre-qualify-target       -> weak-target-prequalified        PORTED (see below)
#   (no sibling)                  -> weak-target-prefix-ignored      ADDED (E5 clause)
#   (no sibling)                  -> weak-kind-not-normalized        ADDED (E4 clause)
#   (no sibling)                  -> weak-domain-hardcoded           ADDED (E0/domain binder)
#   (no sibling)                  -> weak-tilde-marker-ignored       ADDED (E5, 2nd marker)
#   (no sibling)                  -> weak-scopes-crossed             ADDED (E1+E2 jointly)
#
# 5 ported, 2 re-aimed, 0 dropped; 5 added for the clauses/binders this richer
# carrier models that the sibling's `RefNode` did not. Two of the additions came
# from a first audit of this battery: E5's marker test has TWO disjuncts and only
# the first was reached by a witness, and E1/E2 were only ever attacked by scope
# ERASURE, never by a rival that records both scopes into each other's slot
# (correct on the whole symmetric sub-domain, so no erasure witness covers it).
# Both were built, refuted at a concrete input, and confirmed to fail against the
# frozen solution before being added.
#
# PORTED, after a second audit REVERSED an earlier drop (weak-pre-qualify-
#   target -> weak-target-prequalified): the sibling's "resolve-by-rewriting-the-
#   target" rival returns a node whose `target` is `cur_module + target` (the
#   pre-qualified name) — violating its P1 (target-identity). A previous pass
#   recorded this as DROPPED-because-REDUNDANT, on the stated ground that its
#   P1-analogue E5 was "already attacked head-on and more sharply by
#   weak-target-prefix-ignored". That ground was FALSE, and the claim is what the
#   audit checked rather than believed. E5 (`out.target = normalizeTarget
#   target`) has two branches, and both marker rivals attack only the STRIP
#   branch: they UNDER-strip, so they agree with the frozen impl's `target` on
#   every marker-free input. Enumerated over all eight then-retained rivals at
#   targets 'str'/'int'/'None'/'Cls': NOT ONE produced a `target` field differing
#   from the frozen impl's. So E5's IDENTITY branch — a marker-free target must
#   be stored verbatim — had no rival at all, and an impl that OVER-writes the
#   target (the plausible rival "fix": qualify the name instead of recording the
#   scope) passed the battery unattacked. It is now carried as
#   weak-target-prequalified, which keeps both scopes, the flag, the domain and
#   the kind correct so E5's identity branch carries the rejection alone.
#   Rebuilt and confirmed: witness elaborates against the rival (exit 0) and
#   `decide` proves the proposition false against the frozen solution (exit 1).
# RE-AIMED (pos-scope-before-flag): the sibling's second positive adds redundant
#   `Assert`s of the resolution facts P5/P6. This backend has no separate
#   resolution oracle to assert (the resolution intent is captured structurally
#   by the recorded scope in E0-E2), so the "make the reasoning explicit" spirit
#   is re-aimed at a second behaviour-preserving reshape: commute the two
#   field-disjoint record updates (record the scope, then set the flag). Same
#   descriptor on every input; guards against SPEC-TOO-STRONG on update order.
# RE-AIMED (admissibility): the sibling self-CALLS make_field_ref on a concrete
#   F2P witness to discharge the `member`/`count_suffix>=2` precondition. This
#   backend's only precondition is `kind ≠ []`, trivially satisfied; the residual
#   admissibility risk is a DEGENERATE scope-recording clause. It is re-aimed at
#   an in-region assert that the required behaviour records a PRESENT scope
#   (module 'example', class 'Class' — the F2P scenario) rather than collapsing it
#   to `none`, i.e. that E1/E2 genuinely fork on a present scope.
#
# CLAUSE / BINDER COVERAGE of the reject witnesses (9 rivals, 9 distinct input
#   points):
#     E0 (master / domain)          — weak-domain-hardcoded (domain 'func' ≠ 'py')
#     E1 (scopeModule)              — weak-drop-module (erasure)
#     E2 (scopeClass)               — weak-drop-class (erasure)
#     E1+E2 jointly                 — weak-scopes-crossed (both present, swapped)
#     E3 (preferSpecific)           — weak-drop-specific-flag
#     E4 (normalizeKind)            — weak-kind-not-normalized
#     E5 (normalizeTarget), strip '.'    — weak-target-prefix-ignored
#     E5 (normalizeTarget), strip '~'    — weak-tilde-marker-ignored
#     E5 (normalizeTarget), IDENTITY     — weak-target-prequalified
#   Every top-level clause is attacked, and the two clauses with internal
#   structure are attacked per-branch: E5 at BOTH marker disjuncts AND at its
#   identity branch (a marker-free target must be stored verbatim — the branch
#   the two marker rivals cannot reach, since under-stripping agrees with the
#   required target on every marker-free input), and the scope pair both by
#   erasure and by cross-assignment (the latter is the only rival correct on the
#   entire symmetric sub-domain curModule = curClass). The E5 trio also brackets
#   the clause from both sides: two rivals that store TOO MUCH of a marked
#   target and one that stores too much of an unmarked one.
#   INPUT binders, all five varied:
#     curModule : some 'example' / none / some 'm' / none / none / none /
#                 some 'm' / some 'm' / some 'pkg.mod'
#                 (present AND none, never held fixed)
#     curClass  : some 'Class' / some 'C' / some 'C' / none / none / none /
#                 none / none / none    (present AND none)
#     domain    : 'py' x6 / 'js' / 'func' / 'py'
#                 (moved off 'py' by weak-domain-hardcoded and weak-kind)
#     kind      : all 'class' EXCEPT weak-domain-hardcoded ('exc') — the others
#                 use 'class' because a NON-'class' kind cannot exercise the
#                 normalizeKind branch and the F2P/P2P descriptors are
#                 class-kind; kind is domain-restricted (`require kind ≠ []`)
#                 and every witness holds it non-empty, so the precondition is
#                 respected. It IS varied in VALUE across the target axis it
#                 interacts with (target 'str'/'int'/'None'/'.foo'/'~foo'/'Cls').
#     target    : 'str' / 'int' / 'str' / '.foo' / '~foo' / 'None' / 'str' /
#                 'str' / 'Cls'  (marker-free, leading-'.', leading-'~', and
#                 literal 'None' — every sub-domain E4/E5 fork on; 'Cls' is
#                 marker-free under a PRESENT module, where the identity branch
#                 of E5 is the only thing pinning the stored target)
#
# DISCLOSURE — E3 (preferSpecific) and the F2P node-shape assertions. The F2P
#   test asserts the CONSTRUCTED node's shape (`refdomain`, `reftype`,
#   `reftarget`, `py:module`, `py:class`) but NOT `refspecific`; the
#   prefer-specific flag is observed by the LATER resolution step, not by the
#   node-shape assertion. weak-drop-specific-flag's refinement argues its faithful
#   patch (omitting the flag) breaks the F2P via that resolution step (searchmode
#   falls to the non-specific path, so the single contextual resolution the F2P
#   expects does not occur). The spec clause E3 is real and load-bearing; the
#   rival is soundly refuted by the witness at the spec level. This is disclosed
#   as the one rival whose F2P failure route is the downstream resolver rather
#   than a direct node-attribute assertion — grounded in mapping.md §2.1
#   (`refspecific` drives `find_obj(searchmode=1)`), not fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom and no `:|` stub (`scopedRef`/`normalizeKind`/`normalizeTarget`
# are A-reference deep models checked by G-CONF), and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
