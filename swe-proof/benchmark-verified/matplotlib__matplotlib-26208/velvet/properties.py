"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26208 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is then checked by the real verifier: ``expect:"verify"``
passes iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND
does NOT verify AND its refutation ``witness`` discriminates — the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. Two independent companion-creation sites, ``inheritSharedConvA``
and ``inheritSharedConvB``, with IDENTICAL structure. Each takes one input
(``source : ConvSetting``, the shared-coordinate conversion setting the source
view's axis carries) and returns the companion axis's setting (``out``). The
carrier ``ConvSetting = Option Int`` models the setting up to object identity:
``none`` is absent, ``some t`` is a present setting whose ``Int`` tag stands for
its identity, so value equality of the model is exactly identity of the real
setting (mapping.md §2). Each method has NO precondition and two independent
top-level ensures clauses:

  inheritSharedConvA / inheritSharedConvB (source)
      ensures out = source                      -- LOAD-BEARING: the companion
                                                --   carries the SAME setting
                                                --   object (or both absent)
      ensures isPresent out = isPresent source  -- weaker: present-iff

The load-bearing clause is ``out = source`` — pure equality GROUNDED in the sole
input, not an opaque answer-key, so there is no ungrounded oracle to echo: the
only way to satisfy it is to actually carry the source setting through. The
presence clause is strictly weaker (it constrains only whether a setting is
present, not which one) and is IMPLIED by the identity clause, so it cannot be
attacked in isolation — but it IS attacked by any rival that changes presence
(the prepatch / present-at-absent rivals below).

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS here. The nagini sibling's MANDATORY
    frame case writes to a half-permission (read-only) input to make the
    postcondition fall out, and is rejected for insufficient permission. This
    backend is referentially transparent: ``source`` is an immutable value,
    there is no heap, no aliasing, and no ``mut`` binder in this bundle, so there
    is no read-only input to overwrite and no substitute probe to build. Not
    fabricated — see the module footer.
  * PARTIAL-DOMAIN / VALUE — APPLIES to both sites: the sole input ``source``
    ranges over the absent marker and present settings, and a rival can be right
    on one half of that domain and wrong on the other. Attacked at both halves.
  * VALUE-DOUBLE-MASK (fresh descriptor) — APPLIES: the sharpest rival satisfies
    the WEAK presence clause with a present setting that is NOT the source's,
    breaking only the identity clause. This is the near-miss that proves the
    identity clause is load-bearing beyond presence.
  * SITE-INDEPENDENCE — APPLIES: the two sites are pinned by separate
    obligations; a rival that corrupts only one site (leaving the other the
    correct gold copy) must still be rejected on that site's clause. Every
    B-site rival keeps the A site gold-correct, and vice versa, which is exactly
    the nagini half-fix argument.

WITNESS PLACEMENT. Every reject witness reaches the ``method`` contract through
Velvet's own tester machinery: ``<name>Tester args = false`` says the extracted
program's result violates that method's postcondition at the concrete input.
Checked in a file whose ``prove_correct`` blocks are stripped, so no tactic
script can mask the verdict. Rivals share no refutation point unless they fail
there for the same reason: the prepatch and fresh rivals are refuted at DISTINCT
present settings, and the present-at-absent rival is refuted at ``none`` — the
half of the optional domain the other two provably agree with gold on — so the
binder ``source`` is varied over both halves at each site rather than pinned.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the single copied
setting is the modeled function itself, deeply modeled, owed no contract —
mapping.md §3). There is no axiom-soundness obligation to probe here, and the
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26208"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two per-method impl regions are BYTE-IDENTICAL (both `let out := source /
# return out`), so an impl-only substring is NOT unique in the file. Every
# anchor therefore spans the impl body AND that method's `prove_correct` header,
# which carries the method name and so is unique. All edited text stays inside
# the `-- impl-start` / `-- impl-end` region or the `prove_correct` tactic body,
# both elided from the consumer spec view => same_spec is GUARANTEED and every
# obligation survives with a byte-identical statement.
# ---------------------------------------------------------------------------
def _block(meth, body):
    return (f"    {body}\n"
            f"    -- impl-end\n\n"
            f"prove_correct {meth} by\n"
            f"  loom_solve")


_A_GOLD = _block("inheritSharedConvA", "let out := source\n    return out")
_B_GOLD = _block("inheritSharedConvB", "let out := source\n    return out")


def _rivalA(body):
    return _swap(_BASE, _A_GOLD, _block("inheritSharedConvA", body))


def _rivalB(body):
    return _swap(_BASE, _B_GOLD, _block("inheritSharedConvB", body))


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery. `decide` on a
# ---- concrete `Int`-tagged setting is total (no opaque terms); no `sorry`,
# ---- `admit` or `native_decide` — those would make the witness hold of gold
# ---- too and defeat both halves.
def _tester(meth, example):
    return (f"extract_program_for {meth}\n"
            f"prove_precondition_decidable_for {meth}\n"
            f"prove_postcondition_decidable_for {meth}\n"
            f"derive_tester_for {meth}\n\n" + example)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
# Each keeps both obligations and only reshapes the executable surface; the
# contracts are point-wise over an immutable value, so each reproof stays close
# to the frozen `loom_solve`.
# ===========================================================================

# 1. Local-binding reshape at BOTH sites: read the source setting into a typed
#    local, then return it. Same value flows through, so identity is preserved.
_pos_local = _swap(
    _swap(_BASE, _A_GOLD,
          _block("inheritSharedConvA",
                 "let shared : ConvSetting := source\n    let out := shared\n    return out")),
    _B_GOLD,
    _block("inheritSharedConvB",
           "let shared : ConvSetting := source\n    let out := shared\n    return out"))

# 2. Total case-split reshape at BOTH sites: split the optional input and
#    rebuild the same value in each arm. Observationally `source` everywhere.
_pos_match = _swap(
    _swap(_BASE, _A_GOLD,
          _block("inheritSharedConvA",
                 "let out : ConvSetting := match source with\n"
                 "      | none => none\n"
                 "      | some c => some c\n    return out")),
    _B_GOLD,
    _block("inheritSharedConvB",
           "let out : ConvSetting := match source with\n"
           "      | none => none\n"
           "      | some c => some c\n    return out"))


# ===========================================================================
# ADMISSIBILITY — no method here has a `require` clause, so nothing could
# exclude an F2P-shaped input and the usual "a normal input satisfies the
# precondition" probe is vacuous. Re-aimed at the residual admissibility risk on
# a total domain: that the modeled behaviour is degenerate at the interesting
# point. This discharges an in-region assert that the presence observable really
# does separate a present setting from the absent marker (isPresent (some _) =
# true, isPresent none = false) — the exact fact the failing scenario reads. The
# impl is kept verbatim so both ensures clauses still discharge. The assert is
# live: replacing it with a false claim about the same point leaves an unsolved
# `False` goal.
# ===========================================================================
_adm = _swap(
    _BASE,
    "    let out := source\n    return out\n    -- impl-end\n\nprove_correct inheritSharedConvA by",
    "    assert (with_name_prefix `assert\n"
    "      (isPresent (some 0) = true ∧ isPresent (none : ConvSetting) = false))\n"
    "    let out := source\n    return out\n    -- impl-end\n\nprove_correct inheritSharedConvA by")


SPEC_TESTS = [
    {
        "id": "pos-local-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_local,
        "rationale": "structurally-different correct impl (read the source "
                     "setting into a typed local, then return it) carries the "
                     "SAME value through at BOTH sites, so `out = source` and "
                     "`isPresent out = isPresent source` still hold. If it fails "
                     "to verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-match-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_match,
        "rationale": "a total case split on the optional input that rebuilds the "
                     "same value in each arm is observationally `source` at BOTH "
                     "sites, so both clauses discharge; a correct reshape must "
                     "verify.",
    },
    {
        "id": "admiss-presence-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _adm,
        "rationale": "the modeled behaviour is non-degenerate at the F2P-shaped "
                     "point: the presence observable separates a present setting "
                     "(isPresent (some _) = true) from the absent marker "
                     "(isPresent none = false) — exactly the fact the scenario "
                     "reads. The in-region assert must discharge (else the "
                     "observable would be degenerate) and the verbatim impl keeps "
                     "both ensures clauses discharging too.",
    },

    # ---- site A ----
    {
        "id": "weak-A-omit-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rivalA("let out : ConvSetting := none\n    return out"),
        "refinement": "this is the base_commit behaviour: the companion axis is "
                      "left carrying the absent marker instead of the source's "
                      "setting, so the failing scenario that reads the companion "
                      "setting back and requires it to be present AND to be the "
                      "source's own object still observes the absent default and "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from both clauses at site A: with a present source "
                     "the impl yields the absent marker, so `out = source` fails "
                     "(none ≠ some t) and `isPresent out = isPresent source` "
                     "fails (false ≠ true). Refuted at a present setting.",
        "witness": _tester(
            "inheritSharedConvA",
            "example : inheritSharedConvATester (some 5) = false := by\n  decide\n"),
    },
    {
        "id": "weak-A-fresh-setting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rivalA("let out : ConvSetting := some 999\n    return out"),
        "refinement": "a counterpart that gives the companion a NEW present "
                      "setting instead of the source's own leaves the companion "
                      "carrying a different object; the failing scenario asserts "
                      "the companion setting IS the source's (object identity), "
                      "so such a patch fails that identity check and does NOT "
                      "resolve, even though the companion is non-absent.",
        "rationale": "REJECT from the LOAD-BEARING `out = source` alone: a fresh "
                     "present setting satisfies the weak presence clause "
                     "(isPresent (some 999) = isPresent (some t) = true) but is "
                     "not the source's, so the identity clause rejects it. Proves "
                     "the identity clause is load-bearing beyond presence. "
                     "Refuted at a present setting DISTINCT from the omit-copy "
                     "rival's point.",
        "witness": _tester(
            "inheritSharedConvA",
            "example : inheritSharedConvATester (some 3) = false := by\n  decide\n"),
    },
    {
        "id": "weak-A-present-at-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rivalA("let out : ConvSetting := some (source.getD 0)\n    return out"),
        "refinement": "a counterpart that coerces an absent source into a "
                      "present (default) setting on the companion makes a "
                      "companion whose source carried NO setting spuriously "
                      "present, so the unchanged path that requires an absent "
                      "source to stay absent on the companion observes a present "
                      "setting instead and fails. It would NOT resolve.",
        "rationale": "REJECT at the absent half of the domain: at source = none "
                     "the impl yields some 0, so `out = source` fails (some 0 ≠ "
                     "none) and `isPresent out = isPresent source` fails (true ≠ "
                     "false). This is the partial-domain DUAL of weak-A-omit-copy "
                     "(faithful on present settings, wrong at the absent marker) "
                     "and the only site-A rival refutable at source = none.",
        "witness": _tester(
            "inheritSharedConvA",
            "example : inheritSharedConvATester none = false := by\n  decide\n"),
    },

    # ---- site B (each keeps site A the correct gold copy, so a rejection is
    # ---- attributable to site B's own obligation — the nagini half-fix
    # ---- argument, confirming the two sites are independently pinned) ----
    {
        "id": "weak-B-omit-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rivalB("let out : ConvSetting := none\n    return out"),
        "refinement": "the base_commit behaviour at the OTHER site: the companion "
                      "sharing the other coordinate is left carrying the absent "
                      "marker, so the failing scenario for that coordinate still "
                      "observes the absent default and still fails. A fix that "
                      "patched only the first site would leave this one failing "
                      "and would NOT resolve.",
        "rationale": "REJECT from both clauses at site B (site A stays gold): "
                     "with a present source the impl yields the absent marker, so "
                     "`out = source` and `isPresent out = isPresent source` both "
                     "fail. Confirms site B is independently pinned.",
        "witness": _tester(
            "inheritSharedConvB",
            "example : inheritSharedConvBTester (some 7) = false := by\n  decide\n"),
    },
    {
        "id": "weak-B-fresh-setting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rivalB("let out : ConvSetting := some 999\n    return out"),
        "refinement": "a NEW present setting at the second site leaves that "
                      "companion carrying a different object than its source; the "
                      "failing scenario asserts object identity, so it fails and "
                      "does NOT resolve despite the companion being non-absent.",
        "rationale": "REJECT from the LOAD-BEARING `out = source` alone at site B "
                     "(site A stays gold): a fresh present setting satisfies the "
                     "weak presence clause but is not the source's. Refuted at a "
                     "present setting distinct from weak-B-omit-copy's point.",
        "witness": _tester(
            "inheritSharedConvB",
            "example : inheritSharedConvBTester (some 4) = false := by\n  decide\n"),
    },
    {
        "id": "weak-B-present-at-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rivalB("let out : ConvSetting := some (source.getD 0)\n    return out"),
        "refinement": "coercing an absent source into a present default at the "
                      "second site makes a companion whose source carried no "
                      "setting spuriously present, so the unchanged path "
                      "requiring an absent source to stay absent fails. It would "
                      "NOT resolve.",
        "rationale": "REJECT at the absent half at site B (site A stays gold): at "
                     "source = none the impl yields some 0, so both clauses fail. "
                     "The partial-domain dual of weak-B-omit-copy and the only "
                     "site-B rival refutable at source = none, so the binder "
                     "`source` is varied over both halves at site B too.",
        "witness": _tester(
            "inheritSharedConvB",
            "example : inheritSharedConvBTester none = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) over two identically-shaped
# builder functions (build_companion_sharing_horizontal / _vertical). This
# bundle contracts the same two behaviours as inheritSharedConvA / _B, so the
# mapping is close to one-to-one, re-sited onto this backend's value carrier.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   pos-control-local-binding          -> pos-local-binding             PORTED
#   admiss-precond-usable              -> admiss-presence-nondegenerate  RE-AIMED
#   frame-mutate-source                -> (none)                         VACUOUS
#   prepatch-omit-copy                 -> weak-A/B-omit-copy             PORTED (split per site)
#   wrong-fresh-descriptor             -> weak-A/B-fresh-setting         PORTED (split per site)
#   half-fix-vertical-only-broken      -> weak-B-* (A stays gold)        PORTED (subsumed)
#
# VACUOUS (frame-mutation, the sibling's MANDATORY case): the sibling rejects a
#   write to the half-permission (read-only) `source.descriptor` for insufficient
#   permission. This backend is referentially transparent, `source` is an
#   immutable value, and this bundle declares no `mut` binder, so there is no
#   read-only input to overwrite and the permission system it probes does not
#   exist here. No substitute fabricated (SPEC_GUIDE §0.5).
# RE-AIMED (admissibility): the sibling asserts the precondition `descriptor is
#   not None` admits an F2P-shaped input. No method here has a `require` clause,
#   so nothing could exclude a normal input and that probe is vacuous. Re-aimed
#   at the residual total-domain risk — that the modeled observable is degenerate
#   — by discharging an in-region assert that presence separates a present
#   setting from the absent marker.
# SPLIT PER SITE: the sibling mutates BOTH sites in one same-spec variant. Here
#   each rival corrupts ONE site and keeps the other the gold copy, so a
#   rejection is attributable to that site's own obligation. This also subsumes
#   the sibling's dedicated half-fix case (every weak-B-* rival IS a half-fix:
#   site A correct, site B broken) and independently pins each site.
# ADDED (2, no sibling counterpart): weak-A-present-at-absent and
#   weak-B-present-at-absent — the partial-domain DUAL of the omit-copy rivals
#   (faithful on present settings, wrong at the absent marker). Added for BINDER
#   COVERAGE: the omit-copy and fresh-setting rivals are all refuted at present
#   settings, so without these the binder `source` would never be probed at the
#   absent marker `none` and a rival mishandling only that half would go
#   uncaught. Each is a real divergence from both clauses at source = none with a
#   machine-checked witness.
#
# CLAUSE COVERAGE. Both independent top-level clauses are attacked:
#   * `out = source` (load-bearing identity) — attacked by every rival; the
#     fresh-setting rivals attack it in ISOLATION (they satisfy the presence
#     clause and fail only identity), proving it is load-bearing beyond presence.
#   * `isPresent out = isPresent source` (presence) — strictly weaker and IMPLIED
#     by identity, so unattackable alone; attacked by the omit-copy and
#     present-at-absent rivals, which change presence.
#
# WITNESS DISTINCTNESS. The three rivals per site are refuted at DISTINCT inputs:
#   omit-copy and fresh-setting at two different present settings (some 5/some 3
#   for A, some 7/some 4 for B), present-at-absent at none. So `source` is varied
#   over both halves of the optional domain at each site rather than pinned, and
#   no two rivals share a refutation point (each fails for its own reason).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (mapping.md §3), so there is nothing there to probe.
AXIOM_TESTS = []
