"""properties.py — G-PBT falsification battery for django__django-15380 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct frameRenamedField`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method over three read-only association-list
maps and two name strings:

    frameRenamedField priorModels currentModels renamed app curModelName
      ensures out.1 = lookupState priorModels (app, renameLookup renamed (app, curModelName))
      ensures out.2 = lookupState currentModels (app, curModelName)

The routine selects two model entries a field operation acts on. Two
independent top-level clauses:
  * (P0) out.1 — the PRIOR-state entry, keyed by the model's PRIOR name, where
    the prior name is resolved through the rename record (its rename source, or
    the current name when it was not renamed).
  * (P1) out.2 — the CURRENT-state entry, keyed by the model's CURRENT name.
    THIS is the discriminating clause: the current-state map is keyed by current
    names, so a model whose name changed is found there under its NEW name,
    independently of its prior name. The pre-image keyed the current-state entry
    by the PRIOR name, which is absent from the current-state map on a renamed
    model — the empty lookup (``none``) that in the repository manifests as the
    reported crash. The single gold change is which key the current-state lookup
    is given.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``ModelEntry`` is a ``structure`` deriving ``DecidableEq``, the two maps are
concrete ``List`` association lists, and ``lookupState`` / ``renameLookup`` are
concrete ``def``s in the ``pure`` region (the ``axioms`` region declares
nothing). So each rival's violation reduces to a decidable equality of concrete
``Option ModelEntry`` values at a small literal input, and a ``decide`` witness
discriminates. There is NO opaque callee blocking refutation — the reject lane
is fully expressible, no NO-REJECT-LANE collapse.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches it through Velvet's own tester
machinery: ``frameRenamedFieldTester <priorModels> <currentModels> <renamed>
<app> <curModelName> = false`` says the extracted program's result violates the
postcondition at that concrete input, checked in a file whose ``prove_correct``
block has been stripped (no tactic script can mask the verdict). There is no
``require`` clause, so the precondition is ``True`` and decides trivially.
Verified out of band with ``scripts/lean_verify.sh``: each witness builds green
against its rival and red against the frozen solution (the frozen solution
returns the correct pair at every witness input, so ``... = false`` is disproved
by ``decide`` — the discriminator is real, not a tautology). No ``sorry`` /
``admit`` / ``native_decide`` / ``axiom``.
"""
from pathlib import Path

INSTANCE = "django__django-15380"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the two key resolutions and the
# returned pair, with the interleaved comments). Reject rivals and the loop-free
# positive replace this block.
_BODY = """    let priorName := renameLookup renamed (app, curModelName)
    -- The prior-state entry is keyed by the prior name; the current-state entry
    -- is keyed by the current name (the current-state map is keyed by current
    -- names).
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState currentModels (app, curModelName)
    return (oldState, newState)"""
assert _BASE.count(_BODY) == 1, "frameRenamedField impl body drifted from expected text"

# The leading comment + first executable line of the impl region; an in-region
# assert prepended here is discharged by the proof without disturbing the
# method's obligation.
_IMPL_TOP = """    -- The model's prior name: its rename source, or its current name if it was
    -- not renamed.
    let priorName := renameLookup renamed (app, curModelName)"""
assert _BASE.count(_IMPL_TOP) == 1, "impl-top anchor drifted from expected text"

# The FULL frozen proof body. The admissibility case adds one alternation arm to
# discharge its ground assert; the tactic body is elided from the spec view, so
# this is a proof reshape, not a spec change.
_PROOF = "prove_correct frameRenamedField by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: the tester applied at a concrete input returns `false` exactly
# ---- when the extracted program violates the postcondition there.
_TESTER = (
    "\nextract_program_for frameRenamedField\n"
    "prove_precondition_decidable_for frameRenamedField\n"
    "prove_postcondition_decidable_for frameRenamedField\n"
    "derive_tester_for frameRenamedField\n\n"
)


def _witness(prior, current, renamed, app, cur):
    return (
        _TESTER
        + "example : frameRenamedFieldTester\n"
        + f"    {prior}\n    {current}\n    {renamed}\n    {app} {cur} = false := by\n  decide\n"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG. Each keeps the two `ensures` clauses and only reshapes the
# executable surface.
# ---------------------------------------------------------------------------

# Reorder: resolve the CURRENT-state entry first, then the prior name and the
# prior-state entry, and build the pair from locals computed in the opposite
# order. Same two lookups, same rename resolution; the frozen `loom_solve` proof
# closes untouched.
_POS_REORDER = """    let newState := lookupState currentModels (app, curModelName)
    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    return (oldState, newState)"""

# Inline: drop the `priorName` local and pass the rename resolution inline as the
# prior-state key (exactly the term the postcondition names). Same value flow.
_POS_INLINE = """    let oldState := lookupState priorModels (app, renameLookup renamed (app, curModelName))
    let newState := lookupState currentModels (app, curModelName)
    return (oldState, newState)"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY (re-aimed). The sibling's admissibility case builds an
# F2P-shaped renamed-model input and self-calls to show the (fractional-
# permission) precondition ADMITS it. This backend's method has NO `require`
# clause and no permission surface, so that probe is degenerate (every input is
# in-domain). It is re-aimed at the residual total-domain risk — that the post-
# image is DEGENERATE at the interesting point (a spec both clauses satisfy
# vacuously would read like a live one). A live in-region assert pins BOTH
# clauses at the F2P-shaped renamed point: the model's prior name is resolved
# through the rename record ("post2" -> "post"), the PRIOR-state entry IS found
# under the prior name, and the CURRENT-state entry IS found under the CURRENT
# name — the exact configuration where keying the current lookup by the prior
# name would return `none`. The impl is kept verbatim so the method's own
# obligation still discharges; the assert is live (a false claim leaves an
# unsolved goal — checked), and the proof gains one `decide` arm to close it.
# ---------------------------------------------------------------------------
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `assert\n"
    "      (lookupState [((\"a\", \"old\"), ({ name := \"p\" } : ModelEntry))]\n"
    "          (\"a\", renameLookup [((\"a\", \"new\"), \"old\")] (\"a\", \"new\")) = some { name := \"p\" } ∧\n"
    "       lookupState [((\"a\", \"new\"), ({ name := \"c\" } : ModelEntry))] (\"a\", \"new\") = some { name := \"c\" }))\n"
    + _IMPL_TOP
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected, each with a machine-checked refutation witness at a concrete
# input and the refinement argument that its faithful real counterpart would NOT
# resolve the failing test.
# ---------------------------------------------------------------------------

# THE discriminator (the pre-image). Key the CURRENT-state lookup by the PRIOR
# name instead of the current name. Correct on the unchanged-name subdomain
# (priorName == curModelName, so both keys coincide), WRONG on a renamed model
# where the current-state map has no entry under the prior name.
_R_PREPATCH = """    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState currentModels (app, priorName)
    return (oldState, newState)"""

# Read the current-state entry out of the PRIOR-state map (by the current name).
# Neither the gold nor the pre-patch key; fetches the wrong entry whenever the
# two maps hold different entries under that key. Refutable even without a
# rename (near-miss keyed correctly but on the wrong map).
_R_WRONGMAP = """    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState priorModels (app, curModelName)
    return (oldState, newState)"""

# Regress the (correct, untouched) PRIOR-state lookup: key it by the CURRENT name
# instead of resolving the prior name through the rename record. Coincides with
# gold only when the model was not renamed; on a renamed model the prior entry is
# wrong/absent. Attacks clause (P0).
_R_PRIORCURNAME = """    let oldState := lookupState priorModels (app, curModelName)
    let newState := lookupState currentModels (app, curModelName)
    return (oldState, newState)"""

# Transpose the returned pair (current entry in slot 0, prior entry in slot 1).
# Both lookups are individually correct, so no partiality, but the two clauses
# are violated whenever the two entries differ. Attacks the slot correspondence
# of (P0)/(P1) jointly.
_R_SWAP = """    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    let newState := lookupState currentModels (app, curModelName)
    return (newState, oldState)"""

# --- AUDIT ADDITIONS: the EMPTY-RESULT sub-domain of each clause. -------------
# Audit finding (attack D): every rival above is refuted at an input where BOTH
# clauses resolve to `some` — machine-checked by evaluating the spec at each of
# the four witness inputs. So the sub-domain the surface's own reading leans on
# (a lookup with NO entry under the key, i.e. `lookupState ... = none`) was
# asserted by the prose but never DEMONSTRATED by any case. A rival that agrees
# with gold wherever an entry exists and only differs by refusing to report the
# empty result would have been rejected for a tactic reason alone, with nothing
# in the battery separating it. The three rivals below close that: each is
# refuted at an input where the relevant lookup is genuinely EMPTY.

# Report a FABRICATED entry rather than the empty result when the current-state
# map holds nothing under the current name. Agrees with gold on the whole
# subdomain where an entry exists; differs exactly on the empty one. Attacks
# (P1) on the sub-domain the other (P1) rivals never reach.
_R_FABRICATE_CURRENT = """    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    let newState := match lookupState currentModels (app, curModelName) with
      | some e => some e
      | none   => some { name := curModelName }
    return (oldState, newState)"""

# The same evasion on the PRIOR clause: substitute the current-state entry when
# the prior-state map holds nothing under the prior name. Attacks (P0) on its
# empty sub-domain (symmetric coverage: (P0) was previously probed only where the
# prior entry exists).
_R_FABRICATE_PRIOR = """    let priorName := renameLookup renamed (app, curModelName)
    let oldState := match lookupState priorModels (app, priorName) with
      | some e => some e
      | none   => lookupState currentModels (app, curModelName)
    let newState := lookupState currentModels (app, curModelName)
    return (oldState, newState)"""

# LAUNDERED prior-name read — the velvet analogue of the sibling's two
# frame-mutation probes, which the port recorded as VACUOUS on the ground that a
# referentially transparent carrier has nothing to overwrite. Re-derived by the
# audit: the sibling's probes are rejected for INSUFFICIENT PERMISSION while
# RETURNING the correct value, and that permission surface is genuinely absent
# here — but their SHAPE (make a prior-name-keyed read succeed by first
# installing the entry under the prior key) transliterates to a functional
# shadowing copy, and it is refutable on VALUE. So the lane is not vacuous after
# all: the rival binds the extended map to a local, reads it under the PRIOR
# name, and disagrees with gold whenever the prior key is also present in the
# real current-state map under a DIFFERENT entry.
_R_SHADOW_INSERT = """    let priorName := renameLookup renamed (app, curModelName)
    let oldState := lookupState priorModels (app, priorName)
    let patched := match lookupState currentModels (app, curModelName) with
      | some e => ((app, priorName), e) :: currentModels
      | none   => currentModels
    let newState := lookupState patched (app, priorName)
    return (oldState, newState)"""


SPEC_TESTS = [
    # ===================== POSITIVE CONTROLS (soundness) =====================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _BODY, _POS_REORDER),
        "rationale": "structurally different but CORRECT: the current-state entry "
                     "is resolved first, then the prior name and the prior-state "
                     "entry, and the pair is built from locals computed in the "
                     "opposite order. Same rename resolution and same two lookups, "
                     "so both ensures clauses still hold and the frozen `loom_solve` "
                     "closes; a correct reshape verifying is exactly what "
                     "SPEC-TOO-STRONG would deny. (Sibling: pos-reorder.)",
    },
    {
        "id": "pos-inline-priorname",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _BODY, _POS_INLINE),
        "rationale": "drops the `priorName` local and passes the rename resolution "
                     "inline as the prior-state key — exactly the term (P0) names — "
                     "so the value flow is unchanged and both clauses still hold; "
                     "must verify else SPEC-TOO-STRONG. (Sibling: pos-inline-priorname.)",
    },

    # ===================== ADMISSIBILITY (re-aimed) =========================
    {
        "id": "admiss-grounded-renamed",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_TOP, _ADMISS_ASSERT),
            _PROOF,
            "prove_correct frameRenamedField by\n  loom_solve <;> first | decide | skip",
        ),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped renamed point: the prior name resolves through the "
                     "rename record, the PRIOR-state entry is found under the prior "
                     "name, and the CURRENT-state entry is found under the CURRENT "
                     "name — the exact configuration where keying the current lookup "
                     "by the prior name would return the empty result. The in-region "
                     "assert must discharge (a false claim leaves an unsolved goal — "
                     "checked out of band); the impl is kept verbatim so both ensures "
                     "clauses still verify. (Sibling: admiss-renamed-input, re-aimed "
                     "off the absent permission surface.)",
    },

    # ===================== UNIQUENESS / reject rivals =======================
    {
        "id": "current-keyed-by-prior-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_PREPATCH),
        "refinement": "this IS the pre-image: keying the current-state lookup by the "
                      "PRIOR name. On the renamed-model input the failing test "
                      "exercises, the model is stored in the current-state map only "
                      "under its NEW name and is ABSENT under its prior name, so the "
                      "lookup produces the empty result the issue reports as a crash. "
                      "It does NOT resolve the F2P (G-DIFF).",
        "rationale": "REJECT from (P1) out.2 = lookupState currentModels "
                     "(app, curModelName): on a renamed model (priorName != "
                     "curModelName) the rival keys the current lookup by priorName, "
                     "which is absent from the current-state map, so out.2 = none "
                     "while the spec demands the entry under the current name. "
                     "Refuted at the F2P-shaped renamed input.",
        "witness": _witness(
            '[(("testapp", "author"), ({ name := "pa" } : ModelEntry))]',
            '[(("testapp", "renamedauthor"), ({ name := "ca" } : ModelEntry))]',
            '[(("testapp", "renamedauthor"), "author")]',
            '"testapp"', '"renamedauthor"'),
    },
    {
        "id": "current-from-prior-map",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_WRONGMAP),
        "refinement": "reading the current-state entry out of the PRIOR-state map "
                      "(by the current name) is neither the gold nor the pre-patch "
                      "line; it feeds the prior ModelState where the current one is "
                      "expected into the field-rename scan, mis-comparing fields. It "
                      "would not resolve the F2P.",
        "rationale": "REJECT from (P1) out.2 = lookupState currentModels "
                     "(app, curModelName): the rival reads priorModels at that key, "
                     "and whenever the two maps hold different entries under the "
                     "current name the results differ. Refuted at an un-renamed input "
                     "whose two maps hold distinct entries under the same key — a "
                     "near-miss separated from the pre-image case: it is keyed "
                     "correctly (current name) but reads the wrong MAP, so it fails "
                     "even where the pre-image agrees with gold.",
        "witness": _witness(
            '[(("shop", "widget"), ({ name := "pw" } : ModelEntry))]',
            '[(("shop", "widget"), ({ name := "cw" } : ModelEntry))]',
            '([] : List ((String × String) × String))',
            '"shop"', '"widget"'),
    },
    {
        "id": "prior-keyed-by-current-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_PRIORCURNAME),
        "refinement": "this regresses the (correct, untouched) prior-state lookup to "
                      "key it by the CURRENT name instead of resolving the prior name "
                      "through the rename record; on a renamed model the prior entry "
                      "is wrong/absent and rename detection mis-fires. It would not "
                      "resolve the F2P.",
        "rationale": "REJECT from (P0) out.1 = lookupState priorModels "
                     "(app, renameLookup renamed (app, curModelName)): the rival keys "
                     "the prior lookup by curModelName, ignoring the rename record, so "
                     "on a renamed model out.1 disagrees with the spec (and may be "
                     "none). Refuted at a renamed input where the prior-state map "
                     "holds the entry only under the prior name — this rival varies "
                     "the `renamed` binder and attacks the OTHER clause.",
        "witness": _witness(
            '[(("blog", "post"), ({ name := "pp" } : ModelEntry))]',
            '[(("blog", "post2"), ({ name := "cp" } : ModelEntry))]',
            '[(("blog", "post2"), "post")]',
            '"blog"', '"post2"'),
    },
    {
        "id": "swap-slots",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_SWAP),
        "refinement": "returning the prior and current entries transposed feeds the "
                      "current ModelState where the prior is expected (and vice "
                      "versa) into the field-rename comparison, mis-detecting renames. "
                      "It would not resolve the F2P.",
        "rationale": "both lookups are individually correct (no partiality) but the "
                     "slot correspondence of (P0)/(P1) is violated whenever the two "
                     "entries differ: gold gives (prior, current), the rival gives "
                     "(current, prior). Refuted at an un-renamed input whose two maps "
                     "hold distinct entries under the same key (supporting case). "
                     "(Sibling: partial-swap-slots.)",
        "witness": _witness(
            '[(("crm", "lead"), ({ name := "pl" } : ModelEntry))]',
            '[(("crm", "lead"), ({ name := "cl" } : ModelEntry))]',
            '([] : List ((String × String) × String))',
            '"crm"', '"lead"'),
    },

    # ========== EMPTY-RESULT sub-domain (added by the audit) ================
    {
        "id": "fabricate-absent-current",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_FABRICATE_CURRENT),
        "refinement": "synthesizing a stand-in entry when the current-state map "
                      "holds none under the current name replaces the empty result "
                      "with an invented one, so the field-rename scan compares "
                      "against a model entry that no state actually contains. It "
                      "would not resolve the F2P: the empty result is the observable "
                      "the routine must report, not an error to paper over.",
        "rationale": "REJECT from (P1) out.2 = lookupState currentModels "
                     "(app, curModelName): where the current-state map has NO entry "
                     "under the current name the spec demands the empty result, and "
                     "the rival returns some fabricated entry instead. This rival "
                     "agrees with gold on the entire sub-domain the other (P1) "
                     "rivals are refuted on (an entry exists), so it is separated "
                     "from them precisely by the EMPTY case — the sub-domain no "
                     "other case in this battery reaches.",
        "witness": _witness(
            '[(("testapp", "author"), ({ name := "pa" } : ModelEntry))]',
            '([] : List ((String × String) × ModelEntry))',
            '[(("testapp", "renamedauthor"), "author")]',
            '"testapp"', '"renamedauthor"'),
    },
    {
        "id": "fabricate-absent-prior",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_FABRICATE_PRIOR),
        "refinement": "substituting the current-state entry when the prior-state "
                      "map holds none under the prior name makes a model with no "
                      "prior counterpart look as though it had one identical to its "
                      "current form, so no field difference is ever seen for it. It "
                      "would not resolve the F2P.",
        "rationale": "REJECT from (P0) out.1 = lookupState priorModels "
                     "(app, renameLookup renamed (app, curModelName)): on the "
                     "sub-domain where the prior-state map is empty at the prior "
                     "name the spec demands the empty result and the rival returns "
                     "the current-state entry. Gives clause (P0) the same "
                     "empty-sub-domain coverage this audit added for (P1); refuted "
                     "at an un-renamed input whose prior-state map is empty.",
        "witness": _witness(
            '([] : List ((String × String) × ModelEntry))',
            '[(("store", "invoice"), ({ name := "ci" } : ModelEntry))]',
            '([] : List ((String × String) × String))',
            '"store"', '"invoice"'),
    },
    {
        "id": "shadow-insert-prior-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BODY, _R_SHADOW_INSERT),
        "refinement": "installing the resolved entry under the PRIOR key and then "
                      "reading the current-state entry by that prior key keeps the "
                      "prior-name-keyed read the desired behavior forbids, and makes "
                      "it succeed by extending the map the routine is only supposed "
                      "to read. Where the prior key is itself occupied by a "
                      "different entry the laundered read returns that other entry, "
                      "so it is wrong on VALUE and would not resolve the F2P.",
        "rationale": "REJECT from (P1) out.2 = lookupState currentModels "
                     "(app, curModelName): the rival reads a LOCALLY EXTENDED copy "
                     "of the current-state map under the prior name rather than the "
                     "supplied map under the current name. On an input where the "
                     "prior key is present in the real current-state map under a "
                     "different entry, the extended lookup and the spec's lookup "
                     "disagree. This is the sibling's frame-mutation SHAPE carried "
                     "over as a value-level rival (see the accounting note below): "
                     "there is no permission surface here, but the laundered read is "
                     "refutable on value all the same.",
        "witness": _witness(
            '[(("legacy", "author"), ({ name := "pa" } : ModelEntry))]',
            '[(("legacy", "author"), ({ name := "ca" } : ModelEntry))]',
            '[(("legacy", "renamedauthor"), "author")]',
            '"legacy"', '"renamedauthor"'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases (2
# soundness positives, 1 admissibility, 2 mandatory frame-mutation rivals, 4
# partial-domain uniqueness rivals) plus 0 AXIOM_TESTS; this battery ships 10
# (2 soundness positives, 1 admissibility, 7 uniqueness rivals — the four ported
# value rivals plus three added by the audit). The sibling contracts
# `resolve_field_states(prior_registry, later_registry, correspondence, later)`
# over THREE read-only dict registries held at fractional heap permission
# (Acc(...,1/2)), selecting a (prior_descriptor, later_descriptor) pair. This
# bundle contracts one method, `frameRenamedField`, over the same three maps
# (prior-state, current-state, rename record) plus the app label and current
# model name, returning the (prior_entry, current_entry) pair with a deep
# `lookupState`/`renameLookup` model and no axioms. The two surfaces model the
# SAME two-key resolution (prior entry by the rename-resolved prior name; current
# entry by the CURRENT name), so the value/partial-domain rivals port near-1:1,
# with two carrier consequences: both frame-mutation rivals are VACUOUS here, and
# the nagini value clause split into two independent clauses (P0)/(P1) that are
# attacked separately.
#
#   sibling case                     kind          -> here                        disposition
#   -------------------------------------------------------------------------------------------
#   pos-reorder                      soundness     -> pos-reorder                  PORTED
#   pos-inline-priorname             soundness     -> pos-inline-priorname         PORTED
#   admiss-renamed-input             admissibility -> admiss-grounded-renamed      RE-AIMED
#   frame-mutate-later-registry      uniqueness    -> shadow-insert-prior-key      RE-AIMED
#   frame-mutate-prior-registry      uniqueness    -> (none)                       VACUOUS
#   partial-prepatch-laterkey        uniqueness    -> current-keyed-by-prior-name  PORTED
#   partial-later-from-prior-registry uniqueness   -> current-from-prior-map       PORTED
#   partial-prior-by-latername       uniqueness    -> prior-keyed-by-current-name  PORTED
#   partial-swap-slots               uniqueness    -> swap-slots                   PORTED
#
# PORTED (positives): the sibling's reorder (later lookup first) and inline
#   (inline the @Pure prior_name body as the prior key) reshape 1:1 to
#   pos-reorder (current lookup first) and pos-inline-priorname (inline
#   renameLookup as the prior-state key). Both keep the frozen `loom_solve` proof
#   and defend both clauses against SPEC-TOO-STRONG.
# RE-AIMED (admiss-renamed-input -> admiss-grounded-renamed): the sibling
#   establishes both membership preconditions for an F2P-shaped renamed input and
#   self-calls to show the (fractional-permission) precondition admits it. This
#   backend's method has NO `require` clause and no permission surface, so that
#   probe is degenerate (every input is in-domain). It is re-aimed at the residual
#   total-domain risk — a degenerate post-image — via a live in-region assert
#   pinning BOTH clauses at the F2P-shaped renamed point (prior name resolved
#   through the rename record, prior entry found under the prior name, current
#   entry found under the CURRENT name). The impl is kept verbatim so the method's
#   own obligation still discharges; the assert is live (checked: flipping it
#   false leaves an unsolved goal).
# RE-AIMED (frame-mutate-later-registry -> shadow-insert-prior-key): CORRECTED BY
#   AUDIT. The port recorded both frame-mutation probes as VACUOUS, reasoning that
#   a referentially transparent carrier with no `mut` binder has no read-only
#   input to overwrite. The first half of that is right — the PERMISSION failure
#   the sibling relies on genuinely has no analogue here, and the frame obligation
#   is discharged by the ABSENCE of `mut`, which the frozen spec already encodes
#   (spec_guide directive 5). The conclusion that therefore "no substitute probe
#   exists" was wrong, and the audit landed one. The sibling's probe is not merely
#   "a write"; its POINT is laundering — making a prior-name-keyed read succeed by
#   first installing the entry under the prior key, which is exactly the read the
#   desired behavior forbids. That laundering transliterates to a pure carrier as a
#   locally extended copy of the map (`((app, priorName), e) :: currentModels`)
#   read under the prior name, and unlike its sibling it is refutable on VALUE:
#   where the prior key already holds a different entry, the laundered read returns
#   that entry instead of the spec's. Machine-checked: module rejected, witness
#   holds of the rival and is refuted by `decide` on the frozen solution.
# VACUOUS (frame-mutate-prior-registry): the sibling's supporting probe overwrites
#   prior_registry[old_name] with the value it is about to return, so its whole
#   content is the illegal WRITE — the returned pair is unchanged. Transliterated
#   to this carrier the write becomes a discarded local copy with no observable
#   footprint, so the resulting impl is definitionally gold and the case would be
#   vacuous (attack C). Dropped for that reason, not for difficulty; its laundering
#   sibling is ported above and carries the lane.
# PORTED (the four value rivals): partial-prepatch-laterkey ports directly to
#   current-keyed-by-prior-name (THE discriminator / the pre-image line, refuted
#   on the renamed subdomain — the F2P cell). partial-later-from-prior-registry
#   ports to current-from-prior-map (read the current entry out of the prior-state
#   MAP, a near-miss keyed correctly but on the wrong map, refuted even without a
#   rename). partial-prior-by-latername ports to prior-keyed-by-current-name
#   (regress the prior lookup to the current name, attacking clause (P0)).
#   partial-swap-slots ports directly to swap-slots (transpose the returned pair).
#   The sibling's partial-prior-by-latername and partial-later-from-prior-registry
#   both looked "wrong-registry" over TWO registries; here they split cleanly into
#   an attack on (P0) (prior clause) and an attack on (P1) via the wrong map.
# DIVERGENCE lane - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
# AXIOM_TESTS (0): the sibling ships none; the axiom lane is G-AX's job and this
#   gate ignores AXIOM_TESTS regardless. lookupState/renameLookup are modeled
#   deeply (A-references validated by axiom_check.py), with no consumed axiom.
#
# EMPTY-RESULT COVERAGE (added by the audit). The four rivals the port shipped are
#   each refuted at an input where BOTH clauses resolve to `some` — verified by
#   evaluating the spec at all four witness inputs. So the empty sub-domain
#   (`lookupState ... = none`, the absent key), which the surface note above and
#   three of the rationales lean on, was claimed in prose and demonstrated by no
#   case. Three rivals now cover it: fabricate-absent-current (P1 empty),
#   fabricate-absent-prior (P0 empty), and shadow-insert-prior-key (a laundered
#   prior-key read). Each agrees with gold wherever an entry exists, so each is
#   separated from the original four precisely by the empty case.
# BINDER / CLAUSE COVERAGE. The obligation has five input binders
#   (priorModels, currentModels, renamed, app, curModelName) and two independent
#   top-level clauses (P0) out.1 and (P1) out.2. The four original reject
#   witnesses probe four DISTINCT input points, and the three audit rivals add
#   three more (7 reject points in total, all distinct):
#     app          : "testapp", "shop", "blog", "crm", "store", "legacy" —
#                    distinct values, never fixed.
#     curModelName : "renamedauthor", "widget", "post2", "lead", "invoice" —
#                    distinct.
#     renamed      : NON-EMPTY (a renamed model) for current-keyed-by-prior-name
#                    and prior-keyed-by-current-name; EMPTY for current-from-prior-
#                    map and swap-slots — both the renamed and un-renamed
#                    sub-domains are exercised, and two rivals DEPEND on the rename
#                    record diverging the two keys (their whole defect only shows
#                    when priorName != curModelName), so `renamed` is genuinely
#                    abused rather than held fixed.
#     priorModels  : varied entries; attacked directly by prior-keyed-by-current-
#                    name (P0) and read by current-from-prior-map; EMPTY for
#                    fabricate-absent-prior, so its absent-key case is exercised.
#     currentModels: varied entries; attacked by current-keyed-by-prior-name (P1)
#                    on the renamed subdomain; EMPTY for fabricate-absent-current.
#   Both clauses are attacked (P0 by prior-keyed-by-current-name and swap-slots;
#   P1 by current-keyed-by-prior-name, current-from-prior-map and swap-slots), and
#   the near-miss (current-from-prior-map, keyed correctly on the wrong map) is
#   separated from the pre-image (current-keyed-by-prior-name, keyed by the wrong
#   name on the right map): at the renamed F2P point the pre-image fails while the
#   wrong-map rival would be keyed correctly, and at the un-renamed distinct-maps
#   point the wrong-map rival fails while the pre-image agrees with gold — so each
#   carries its own separating input. No rival that mishandled only a fixed-value
#   binder could slip through.
AXIOM_TESTS = []
