"""properties.py — G-PBT falsification battery for django__django-12039 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct renderColumn`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method ``renderColumn (name, suffixes, idx)``
over three read-only inputs — a name token ``name : List Char``, a list of
optional trailing qualifiers ``suffixes : List (List Char)``, and a position
``idx : Nat`` — returning the rendered text of one indexed column reference. The
sole load-bearing post-image pins the result to a fully-grounded pure function
of those inputs:

  renderColumn (name, suffixes, idx)   ensures out = columnText name suffixes idx

``columnText`` (a concrete ``def`` in the ``pure`` region; the ``axioms`` region
declares nothing) has three branches, and every one is a distinct sub-domain a
rival can get wrong:

  * a qualifier is SUPPLIED and NON-EMPTY (``idx`` in range, element ≠ []) —
    the name, then exactly ONE separating space, then the qualifier;
  * a qualifier is SUPPLIED but EMPTY (``idx`` in range, element = []) — the
    name alone, not even a separating space;
  * a qualifier is ABSENT (``idx`` beyond the supplied list) — the name alone.

The issue's two defects live in the first two branches: the pre-existing bug
fused the qualifier onto the name with no separating space, and the more recent
regression emitted a trailing separator for a SUPPLIED-EMPTY qualifier. The
desired behaviour is: one separating space before a non-empty qualifier, and
nothing at all (not even a space) for an empty or absent one. All three inputs
are read-only (no ``mut`` binder), and the reject witnesses below vary all three:
``name`` (one- and two-char tokens), ``suffixes`` (empty-element, non-empty
one-char, multi-char, and empty-list), and ``idx`` (0, 1, and a position past
the end).

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries TWO mandatory
    frame-mutation probes (write to the read-only ``suffix`` input at site 1,
    write to the read-only ``base`` input at site 2) because a read-only input
    there is held at a fractional heap permission an impl can overwrite. This
    backend is referentially transparent: every parameter is an immutable value,
    this bundle declares no ``mut`` binder on any input, there is no heap and no
    aliasing — so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated (see the module footer); the sibling's "inputs are
    not mutated" obligation is structurally guaranteed by the ABSENCE of ``mut``.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``columnText``, a
    total, fully-unfolded function of the method's OWN inputs — there is no
    opaque answer key to echo (evaluating ``columnText`` IS the correct answer),
    so there is no wrong echo to build. Honest cheapest-reshape positive controls
    (``pos-*``) stand in.
  * PARTIAL-DOMAIN / VALUE — APPLIES: the sibling's pre-patch site-1 bug (no
    separator) and pre-patch site-2 bug (unconditional join / trailing space),
    plus the separator-value and last-element masks, all become rivals correct on
    PART of the branch structure and wrong on the interesting sub-domain. Each is
    refuted at a distinct concrete point.

WITNESS MECHANICS on this carrier. The spec here is a ``method`` CONTRACT, not a
bare predicate, so a witness reaches it through Velvet's own tester machinery:
``renderColumnTester <name> <suffixes> <idx> = false`` says the extracted
program's result violates the method's postcondition at that concrete input. It
is checked in a file whose ``prove_correct`` block has been stripped, so no
tactic script can mask the verdict. There is no ``require`` clause, so the
precondition is ``True`` and decides trivially. All inputs are concrete ``List
Char`` / ``Nat`` literals, so each tester ``decide``s. No ``sorry`` / ``admit`` /
``native_decide`` / ``axiom``.
"""
from pathlib import Path

INSTANCE = "django__django-12039"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The whole executable body: bind the name token, and
# ---- when a non-empty qualifier is supplied for this position append it with a
# ---- single separating space. Lies wholly inside the one impl region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). Reshaped
# ---- wholesale by the rivals and the positive controls. ----
_IMPL = (
    "    let mut col := name\n"
    "    if idx < suffixes.length then\n"
    "      let suffix := suffixes[idx]!\n"
    "      if suffix ≠ [] then\n"
    "        col := name ++ ' ' :: suffix\n"
    "    return col\n"
)

# The accumulator initializer (a substring of _IMPL, unique in the file). Anchor
# for the admissibility in-region assert.
_INIT = "    let mut col := name\n"

# ---- proof-body anchors. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its tactic script without
# ---- touching the spec or dropping the obligation. ----
_PROOF = "prove_correct renderColumn by\n  loom_solve <;> simp_all [columnText]"


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. ----
_TESTER = (
    "extract_program_for renderColumn\n"
    "prove_precondition_decidable_for renderColumn\n"
    "prove_postcondition_decidable_for renderColumn\n"
    "derive_tester_for renderColumn\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the identical
    # theorem statement; only the executable surface moves.
    # =====================================================================
    {
        "id": "pos-return-spec-directly",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the branch-and-accumulate skeleton and return the modeled
        # rendering directly. Observationally identical (the skeleton's result IS
        # the rendering), so the post-image holds definitionally and the frozen
        # tactic discharges it.
        "module": _swap(_BASE, _IMPL, "    return columnText name suffixes idx\n"),
        "rationale": "returning the modeled rendering directly satisfies "
                     "`out = columnText name suffixes idx` definitionally, so a "
                     "correct branch-free reshape must verify (else SPEC-TOO-STRONG "
                     "on the skeleton form).",
    },
    {
        "id": "pos-empty-branch-explicit",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: spell out the supplied-qualifier case as an explicit if/else on
        # emptiness (empty -> name; non-empty -> name + space + qualifier) instead
        # of guarding with `≠ []`. Same three-branch behaviour, so the post-image
        # still holds and the frozen tactic discharges it.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut col := name\n"
            "    if idx < suffixes.length then\n"
            "      let suffix := suffixes[idx]!\n"
            "      if suffix = [] then\n"
            "        col := name\n"
            "      else\n"
            "        col := name ++ ' ' :: suffix\n"
            "    return col\n"),
        "rationale": "an explicit empty/non-empty case split computes the identical "
                     "three-branch rendering (empty qualifier -> name; non-empty -> "
                     "name + one space + qualifier; absent -> name), so "
                     "`out = columnText name suffixes idx` still discharges; must "
                     "verify else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY. No method here has a `require` clause, so there is no
    # precondition that could exclude a normal input; the sibling's "the
    # half-permission precondition admits a normal F2P-shaped input" probe is
    # vacuous. The residual admissibility risk on a total domain is that the
    # post-image is DEGENERATE at the interesting points — a spec no impl can
    # meet reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert` pinning the rendering's discriminating behaviour at the
    # two F2P-shaped inputs (a supplied non-empty qualifier -> one separating
    # space; a supplied EMPTY qualifier -> the bare name, no trailing space). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-rendering-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `assert\n"
                "      (columnText ['a'] [['D']] 0 = ['a', ' ', 'D'] ∧\n"
                "       columnText ['a'] [([] : List Char)] 0 = ['a']))\n"
                + _INIT),
            _PROOF,
            "prove_correct renderColumn by\n"
            "  loom_solve <;> first | (refine ⟨by decide, by decide⟩) "
            "| simp_all [columnText]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the two "
                     "F2P-shaped inputs: a supplied non-empty qualifier renders with "
                     "exactly one separating space (`['a',' ','D']`) and a supplied "
                     "EMPTY qualifier renders as the bare name (`['a']`, no trailing "
                     "space). The in-region assert must discharge (else the "
                     "obligation is degenerate); the impl is kept verbatim so the "
                     "ensures clause still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival keeps the
    # frozen `prove_correct` block (which no longer closes for the reshaped
    # impl); the witness is what attributes the rejection to the SPEC.
    # =====================================================================
    {
        "id": "weak-no-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-existing defect: when a qualifier is supplied, append it by bare
        # concatenation with no separating space and no empty guard.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut col := name\n"
            "    if idx < suffixes.length then\n"
            "      col := name ++ suffixes[idx]!\n"
            "    return col\n"),
        "refinement": "a counterpart that concatenates the ordering qualifier "
                      "directly onto the name token with no separating space "
                      "renders the two fused together (a name immediately followed "
                      "by its DESC qualifier), which is exactly the un-spaced output "
                      "the problem statement rejects and the failing descending "
                      "test forbids (it requires a space before the qualifier). It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = columnText name suffixes idx`: on the "
                     "supplied-non-empty branch the impl omits the ' ' separator the "
                     "post-image demands. Refuted at name `['a']`, one supplied "
                     "non-empty qualifier `['b']`, `idx = 0`.",
        "witness": _TESTER +
                   "example : renderColumnTester ['a'] [['b']] 0 = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-unconditional-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # The more recent regression: append the separator + qualifier
        # UNCONDITIONALLY whenever a qualifier is supplied, dropping the
        # empty-qualifier guard. A supplied EMPTY qualifier then emits a trailing
        # separator.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut col := name\n"
            "    if idx < suffixes.length then\n"
            "      let suffix := suffixes[idx]!\n"
            "      col := name ++ ' ' :: suffix\n"
            "    return col\n"),
        "refinement": "a counterpart that always joins with a separating space when "
                      "a qualifier position exists — even when that qualifier is the "
                      "empty string — emits a trailing space after the name for an "
                      "ascending column, exactly the trailing-whitespace quirk the "
                      "problem statement calls out. It would NOT resolve the "
                      "no-trailing-space behaviour the fix requires.",
        "rationale": "REJECT from `out = columnText name suffixes idx`: on the "
                     "supplied-EMPTY branch the impl appends a spurious ' ' where "
                     "the post-image demands the bare name. Refuted at name `['h']`, "
                     "a supplied EMPTY qualifier `[]`, `idx = 0` — the empty-string "
                     "qualifier the issue describes.",
        "witness": _TESTER +
                   "example : renderColumnTester ['h'] [([] : List Char)] 0 = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct length, correct prefix, correct qualifier-after-separator, but
        # the SEPARATOR VALUE is wrong: a tab (code point 9) instead of the
        # U+0020 space.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut col := name\n"
            "    if idx < suffixes.length then\n"
            "      let suffix := suffixes[idx]!\n"
            "      if suffix ≠ [] then\n"
            "        col := name ++ (Char.ofNat 9) :: suffix\n"
            "    return col\n"),
        "refinement": "a counterpart that separates the name from its qualifier "
                      "with a tab (or any glyph other than a single space) produces "
                      "output that is not the spaced form the problem statement "
                      "shows and the failing test asserts (a single space before the "
                      "qualifier). It would NOT resolve.",
        "rationale": "REJECT from `out = columnText name suffixes idx`: the "
                     "separator character must be the space `' '` the post-image "
                     "pins; a tab makes the code point after the name wrong. Refuted "
                     "at a two-char name `['a','b']`, one supplied non-empty "
                     "qualifier `['D']`, `idx = 0`.",
        "witness": _TESTER +
                   "example : renderColumnTester ['a', 'b'] [['D']] 0 = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-drop-last-qualifier-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss / value-proxy mask: correct name, correct separator, correct
        # all-but-last of the qualifier; diverges only on the LAST qualifier
        # character (and the total length). Attacks the exact element-wise pin on
        # the input that fails last.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut col := name\n"
            "    if idx < suffixes.length then\n"
            "      let suffix := suffixes[idx]!\n"
            "      if suffix ≠ [] then\n"
            "        col := name ++ ' ' :: suffix.dropLast\n"
            "    return col\n"),
        "refinement": "a counterpart that renders the qualifier one character short "
                      "truncates the ordering token (a multi-character qualifier "
                      "loses its final letter), so the rendered reference does not "
                      "contain the full spaced qualifier the failing test asserts. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = columnText name suffixes idx`: dropping the "
                     "last qualifier character makes the appended suffix "
                     "`suffix.dropLast`, not `suffix`, so the element-wise pin "
                     "fails. Refuted at name `['h']`, `idx = 1` selecting the "
                     "multi-char qualifier `['D','E']` from `[['x'],['D','E']]` — a "
                     "point where prefix + separator + all-but-last agree but the "
                     "last element and length diverge.",
        "witness": _TESTER +
                   "example : renderColumnTester ['h'] [['x'], ['D', 'E']] 1 = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-trailing-space-when-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the THIRD branch — the absent-qualifier case (idx beyond the
        # supplied list, the modeled analogue of the IndexError path). A rival
        # that appends a separator there emits a trailing space for a column with
        # no qualifier position at all.
        "module": _swap(
            _BASE, _IMPL,
            "    let mut col := name\n"
            "    if idx < suffixes.length then\n"
            "      let suffix := suffixes[idx]!\n"
            "      if suffix ≠ [] then\n"
            "        col := name ++ ' ' :: suffix\n"
            "    else\n"
            "      col := name ++ [' ']\n"
            "    return col\n"),
        "refinement": "a counterpart that appends a separating space when NO "
                      "qualifier position is supplied for this column emits a "
                      "trailing space after a plain column reference, so the "
                      "rendered reference is not the bare name the fix requires. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = columnText name suffixes idx`: on the "
                     "absent-qualifier branch (`idx ≥ suffixes.length`) the "
                     "post-image demands the bare name, but the impl appends a "
                     "trailing ' '. Refuted at name `['a']`, empty qualifier list "
                     "`[]`, `idx = 3` — a position past the end that no other "
                     "witness probes.",
        "witness": _TESTER +
                   "example : renderColumnTester ['a'] [] 3 = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 mandatory frame-mutation, 4 uniqueness rivals) and
# 1 AXIOM_TEST. This bundle NARROWS the sibling's two byte-identical modeled
# functions (render_column at site 1, render_column_with_opclass at site 2) to a
# SINGLE modeled method `renderColumn`: mapping.md establishes the two repo sites
# make the identical whitespace fix and site 2's tests are PostgreSQL-only (skipped
# on the eval image), so site A's `columnText` captures the only harness-observable
# change. The sibling's per-site pair of cases therefore collapses to one case
# each here — this is carrier narrowing, not a dropped attack.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder      -> pos-empty-branch-explicit         PORTED
#   (new honest reshape)            -> pos-return-spec-directly           ADDED (2nd control)
#   admiss-readonly-inputs          -> admiss-rendering-nondegenerate     RE-AIMED
#   frame-mut-suffix-site1          -> (none)                            VACUOUS
#   frame-mut-base-site2            -> (none)                            VACUOUS
#   partial-no-separator            -> weak-no-separator                 PORTED
#   partial-unconditional-join      -> weak-unconditional-separator      PORTED
#   wrong-separator-tab             -> weak-wrong-separator               PORTED
#   drop-last-suffix-char           -> weak-drop-last-qualifier-char      PORTED
#   (new: absent-qualifier branch)  -> weak-trailing-space-when-absent    ADDED
#
# 5 ported, 1 re-aimed, 2 added, 2 vacuous.
#
# RE-AIMED (admissibility): the sibling's admissibility case asserts a normal
#   F2P-shaped input satisfies the half-permission precondition (len(base)>=0,
#   len(suffix)>=0). There is no permission surface here and no `require` clause,
#   so that reading is vacuous. It is re-aimed at the residual admissibility risk
#   on a total domain — that the post-image is degenerate at the interesting
#   points — by discharging an in-region assert that the two F2P-shaped inputs (a
#   supplied non-empty qualifier -> one space; a supplied EMPTY qualifier -> bare
#   name) render as pinned. This preserves the sibling's exact discriminating
#   points (the DESC space and the empty-string trailing-space quirk).
#
# ADDED (2 cases). The narrowing frees room to strengthen coverage of the single
#   modeled surface without chasing sibling parity: pos-return-spec-directly is a
#   second, maximally-different correct reshape (branch-free) guarding against a
#   skeleton-shape-specific SPEC-TOO-STRONG; weak-trailing-space-when-absent
#   attacks columnText's THIRD branch (idx beyond the supplied list, the modeled
#   IndexError path), which the sibling's rivals — all aimed at the two supplied
#   branches — never exercise. This is the `idx` binder being abused by a rival,
#   not padding.
#
# VACUOUS (both frame-mutation probes): the sibling's MANDATORY probes write to an
#   input held at half heap permission (`suffix.append(...)` at site 1,
#   `base.append(...)` at site 2) and are rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent, there is no heap, no aliasing, and
#   this bundle declares no `mut` binder on `name`, `suffixes`, or `idx`, so there
#   is no read-only input to overwrite and no substitute probe exists. Not
#   fabricated (spec_guide directive 5: the frame obligation here is discharged by
#   the ABSENCE of a `mut`, which the frozen spec already encodes).
#
# BINDER / CLAUSE COVERAGE. The sole postcondition clause
#   `out = columnText name suffixes idx` has three branches; every one is attacked:
#   supplied-non-empty by weak-no-separator / weak-wrong-separator /
#   weak-drop-last-qualifier-char, supplied-empty by weak-unconditional-separator,
#   absent by weak-trailing-space-when-absent. All three input binders are varied
#   across the five reject witnesses:
#     name     : ['a'], ['h'], ['a','b']                       (1- and 2-char tokens)
#     suffixes : [['b']], [[]], [['D']], [['x'],['D','E']], []  (non-empty / empty
#                 element / multi-char / empty list)
#     idx      : 0, 0, 0, 1, 3                                  (in-range and past-end)
#   Five distinct witness points, so pts = 5; no binder is held constant across
#   all rivals, and the near-miss (drop-last) is separated from the exact-value
#   rivals at its own multi-char point.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model (the rendering is modeled deeply in the pure
# region and checked by G-CONF), so there is nothing there to probe.
AXIOM_TESTS = []
