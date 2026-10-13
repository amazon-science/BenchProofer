"""PBT falsification battery for pytest-dev__pytest-6197.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TEST is a full model.py variant that shares the FROZEN spec (same_spec
guaranteed by region-surgery: every _swap edits ONLY text inside an
# impl-start/# impl-end region) and swaps the implementation; the runner checks
it with Nagini verify. expect="verify" passes iff (same_spec AND verifies);
expect="reject" passes iff (same_spec AND does NOT verify).

DEFENDED SURFACE (reasoned, not mechanical):
The bundle models a two-phase lazy-load state machine on a Container carrying
loaded:bool and load_count:int.

  access_object(c):  Requires Acc(c.loaded); Acc(c.load_count, 1/2);
                     Implies(not c.loaded, Acc(c.load_count, 1/2));
                     c.load_count>=0;
                     MustTerminate(2)                               (total correctness)
     Ensures c.loaded is True                                       (always loaded)
     Ensures Implies(Old(c.loaded), load_count==Old(load_count))    (already -> no load)
     Ensures Implies(not Old(c.loaded), load_count==Old(load_count)+1)  (fresh -> +1)

  enumerate_children(c):  Requires Acc(c.loaded, 1/2) and Acc(c.load_count, 1/2);
                     c.load_count>=0; MustTerminate(2)              (total correctness)
     Ensures c.load_count == Old(c.load_count)   (THE discriminating clause: zero loads)
     Ensures c.loaded     == Old(c.loaded)       (status untouched)

PERMISSION DISCIPLINE (irreversibility): the real load effect is an import —
once performed it has no inverse. Value clauses alone pin only the NET state
change, so a body that performs the load transition and then restores the
counter would satisfy them while its real translation still runs the import.
The contracts therefore also restrict WHERE the load state may be written:
enumerate_children holds only READ (1/2) permission on BOTH fields (any write
during discovery, even one later reverted, is a permission failure), and
access_object holds write permission on load_count only when the container is
not yet loaded (the second 1/2 is granted under Implies(not c.loaded, ...)),
so a redundant re-load on the already-loaded branch is a permission failure.

Both phases carry MustTerminate(2) in the precondition: the postconditions are
partial-correctness guarantees, so WITHOUT a termination obligation a diverging
body (`while True: pass`) satisfies every Ensures vacuously while never handing
control back to the collection run — a wrong implementation the value clauses
alone cannot reject (this exact rival was found by the audit; enum-diverge-loop
below pins it). With MustTerminate, Nagini's obligation leak check rejects any
loop that does not consume the obligation with a decreasing measure.

There are NO @ContractOnly axioms (axioms region empty) and NO @Pure oracle in
the contract: the load primitive is modelled DEEPLY as the in-line transition
`loaded := True; load_count += 1`, validated against real pytest out-of-band by
axiom_check.py (G-AX). Hence AXIOM_TESTS = [] and there is no ungrounded-oracle
to echo: both postconditions are functions of the input state via Old(...), so
they are fully grounded. The load-bearing clause is enumerate_children's
`load_count == Old(load_count)` (the gold deletes the eager
self._mount_obj_if_needed() at the head of discovery) and access_object's
exactly-one-lazy-load pair.

The frame discipline is enforced BOTH at the permission level (read-only 1/2
fractions where no load may happen — see PERMISSION DISCIPLINE above) and at
the VALUE level by the `==Old(...)` clauses. The frame attack is realised as a
value-frame rival (enum-frame-write) that writes to c during discovery and is
REJECTED — post-strengthening, by a permission error rather than merely a
postcondition failure — the same defect the prepatch witnesses, made
adversarial.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-6197"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Unique anchors INSIDE each function's impl region (region-surgery only).
# ---------------------------------------------------------------------------

# access_object impl body (unique in model.py):
_ACCESS_IMPL = (
    "    if not c.loaded:\n"
    "        c.loaded = True\n"
    "        c.load_count = c.load_count + 1\n"
)

# enumerate_children impl body (unique in model.py):
_ENUM_IMPL = (
    "    # Enumeration of children proceeds without touching the container's own\n"
    "    # underlying object; no load is triggered here.\n"
    "    pass\n"
)


SPEC_TESTS = [

    # === 6. ADMISSIBILITY (expect verify) ==================================
    # A positive-control caller proves the precondition admits a normal,
    # F2P-shaped input: a fresh Container (loaded False, load_count 0, which
    # satisfies load_count>=0) drives both phases. If the Requires could not be
    # established for this legitimate input we would have PRECOND-TOO-STRONG.
    # We embed the caller in access_object's impl region (region-surgery) and
    # keep the gold transition so the function still satisfies its own Ensures.
    {
        "id": "admiss-fresh-container",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _ACCESS_IMPL,
            "    # admissibility: a fresh Container is an in-domain input for the\n"
            "    # precondition Acc(c.loaded) and Acc(c.load_count), load_count>=0.\n"
            "    fresh = Container()\n"
            "    Assert(fresh.loaded is False)\n"
            "    Assert(fresh.load_count == 0)\n"
            "    Assert(fresh.load_count >= 0)\n"
            "    # gold transition retained so the postcondition still holds:\n"
            "    if not c.loaded:\n"
            "        c.loaded = True\n"
            "        c.load_count = c.load_count + 1\n",
        ),
        "rationale": "the precondition (Acc both fields, load_count>=0) must accept a "
                     "normal fresh Container as built by Container.__init__ "
                     "(loaded False, load_count 0); else PRECOND-TOO-STRONG.",
    },

    # === 5. POSITIVE CONTROL (soundness, expect verify) ====================
    # A structurally-DIFFERENT but CORRECT access_object. The gold guards the
    # whole load with `if not c.loaded`. This control instead always sets
    # `c.loaded = True` (idempotent: it equals its old value when already
    # loaded, since the only callers reach loaded via the load transition) and
    # increments load_count only inside the guard. It computes the SAME final
    # state but reshapes the control flow (unconditional loaded-write, separate
    # guarded count). No proof obligation is dropped; this exercises whether the
    # spec accepts a faithful different shape. If it cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-access-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ACCESS_IMPL,
            "    # structurally-different correct impl: increment the load count\n"
            "    # only on first load, then unconditionally mark loaded (which is\n"
            "    # idempotent — loaded becomes True either way and load_count is\n"
            "    # bumped exactly when it had not been loaded). Same final state,\n"
            "    # different shape.\n"
            "    if not c.loaded:\n"
            "        c.load_count = c.load_count + 1\n"
            "    c.loaded = True\n",
        ),
        "rationale": "a correct but reshaped access impl (separate count-guard + "
                     "unconditional idempotent loaded-write) must satisfy all "
                     "Ensures; else SPEC-TOO-STRONG. Keeps every obligation: the "
                     "count is bumped iff fresh, loaded ends True.",
    },
    # A second positive control for enumerate_children: an explicit no-op read
    # that touches NOTHING (reads the fields into a local but writes nothing),
    # a structurally-different rendering of "discovery loads nothing".
    {
        "id": "pos-enum-readonly",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ENUM_IMPL,
            "    # structurally-different correct impl: a discovery body may read\n"
            "    # the container's state (here, bind it to locals) but must perform\n"
            "    # no load and no write — load_count and loaded are unchanged.\n"
            "    seen_loaded = c.loaded\n"
            "    seen_count = c.load_count\n"
            "    Assert(seen_count == c.load_count)\n",
        ),
        "rationale": "a discovery body that reads but never writes c must verify "
                     "(load_count and loaded unchanged); else SPEC-TOO-STRONG.",
    },

    # === 3 (analog of FRAME-MUTATION) value-frame write on discovery =======
    # enumerate_children's load-bearing guarantee is that discovery loads
    # NOTHING and leaves loaded untouched. Because c is full-permission, a write
    # is NOT a permission error; the frame is enforced at the VALUE level by
    # `load_count == Old(load_count)` and `loaded == Old(loaded)`. This rival
    # performs the eager load during discovery — exactly the pre-patch bug
    # (self._mount_obj_if_needed() at the head of Package.collect). It MUST be
    # rejected by those postconditions. Same defect the prepatch witnesses,
    # restated as an adversarial rival.
    {
        "id": "enum-frame-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ENUM_IMPL,
            "    # ADVERSARIAL: eagerly load the container during discovery (the\n"
            "    # pre-patch bug: leading self._mount_obj_if_needed()).\n"
            "    if not c.loaded:\n"
            "        c.loaded = True\n"
            "        c.load_count = c.load_count + 1\n",
        ),
        "refinement": "this is exactly the pre-patch Package.collect that begins with "
                      "self._mount_obj_if_needed(); its faithful real patch keeps the "
                      "eager mount, so the F2P test_does_not_eagerly_collect_packages "
                      "(a package whose __init__.py runs `assert False`) ERRORS during "
                      "collection — it does NOT resolve. model_prepatch.py is this exact "
                      "skeleton.",
        "rationale": "rejected by enumerate_children's read-only Acc(...,1/2) permissions "
                     "(any write to the load state during discovery is a permission "
                     "failure), backing the c.load_count==Old(c.load_count) value clause.",
    },

    # === 4b. DIVERGENCE (vacuous-postcondition rival) ======================
    # The audit's winning attack: replace discovery's body with an infinite
    # loop. Every value postcondition is a partial-correctness guarantee and
    # holds VACUOUSLY on a body that never returns — yet the translated real
    # patch (`while True: pass` at the head of Package.collect) hangs the
    # entire test run and resolves nothing. Rejected ONLY by the
    # MustTerminate(2) obligation: Nagini's obligation leak check flags a loop
    # that does not consume the termination obligation via a decreasing
    # measure.
    {
        "id": "enum-diverge-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ENUM_IMPL,
            "    # ADVERSARIAL: diverge instead of enumerating. All value Ensures\n"
            "    # hold vacuously; only the termination obligation rejects this.\n"
            "    while True:\n"
            "        pass\n",
        ),
        "refinement": "the faithful real patch replaces the head of Package.collect "
                      "with an infinite loop: pytest hangs during collection, the F2P "
                      "tests never run, nothing resolves. This is the exact same-spec "
                      "impl the G-EQ audit built (atk_10_enum_loop.py) against the "
                      "pre-MustTerminate spec.",
        "rationale": "rejected by Requires(MustTerminate(2)): the loop carries no "
                     "decreasing-measure MustTerminate invariant, so Nagini's "
                     "obligation leak check fails ('Loop might not take all "
                     "unsatisfied obligations from the context').",
    },

    # === 4. CONTROL-FLOW-EFFECT (capability-token style) ===================
    # enumerate_children must touch NOTHING. A subtler rival than the full eager
    # load: it writes loaded := True WITHOUT bumping load_count (a "silent
    # status flip" — pretend loaded but record no load). This passes the
    # load_count==Old(load_count) clause but violates loaded==Old(loaded). It
    # discriminates the SECOND frame clause specifically. Real-patch analog: a
    # collect() that sets self._obj (marks mounted) without running the import —
    # the marker bookkeeping would then be wrong and access would skip the real
    # load, so the F2P (raising __init__ on genuine access) would be a silent
    # drop, not resolving the deferral-is-not-a-drop guarantee.
    {
        "id": "enum-status-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ENUM_IMPL,
            "    # ADVERSARIAL: flip loaded without recording a load (silent status\n"
            "    # change during discovery). load_count stays equal but loaded changes.\n"
            "    c.loaded = True\n",
        ),
        "refinement": "a real collect() that marked the node mounted (set self._obj) "
                      "without running the import would make the package appear loaded "
                      "while its top-level code never ran; a later genuine access would "
                      "then skip the real load (a silent drop), so the raising __init__ "
                      "never surfaces — the lazy-load-is-not-a-drop guarantee fails and "
                      "the access-phase F2P behaviour is wrong. It does not resolve.",
        "rationale": "rejected by enumerate_children's read-only Acc(c.loaded, 1/2): the "
                     "status write during discovery is a permission failure (and the "
                     "c.loaded==Old(c.loaded) value clause backs it up).",
    },

    # === 3. PARTIAL-DOMAIN (access_object) =================================
    # A rival correct on the already-loaded sub-domain but wrong on the FRESH
    # sub-domain: it leaves loaded True and bumps the count only when already
    # loaded, doing NOTHING when fresh. On Old(loaded)==True it matches; on
    # Old(loaded)==False it leaves loaded False (violating c.loaded is True) and
    # performs zero loads (violating not-Old(loaded) -> +1). The first-accessed
    # (fresh) container is the dominant F2P case, so this is exactly the failing
    # sub-domain.
    {
        "id": "access-partial-fresh-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ACCESS_IMPL,
            "    # ADVERSARIAL: handle only the already-loaded sub-domain; do NOTHING\n"
            "    # when the container is fresh (the dominant first-access case).\n"
            "    if c.loaded:\n"
            "        c.load_count = c.load_count\n",
        ),
        "refinement": "a real obj getter that only acted when _obj was already set "
                      "(and did nothing on the first, _obj is None, access) would NEVER "
                      "run self._getobj() on first read — the underlying object is never "
                      "imported, so a package that DOES contain tests is never collected "
                      "and a raising __init__ never surfaces on genuine access. The "
                      "deferral becomes a permanent drop; F2P access behaviour is broken.",
        "rationale": "rejected by access_object Ensures c.loaded is True AND "
                     "Implies(not Old(c.loaded), load_count==Old(load_count)+1): on a fresh "
                     "container this impl leaves loaded False and load_count unchanged.",
    },

    # === 3. PARTIAL-DOMAIN / over-load (access_object) =====================
    # A rival that ALWAYS loads (drops the `if not c.loaded` guard): correct on
    # the fresh sub-domain (+1), but on the already-loaded sub-domain it bumps
    # load_count a SECOND time, violating Implies(Old(loaded), load_count
    # unchanged) and the "<=1 load per access" guarantee.
    {
        "id": "access-double-load",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ACCESS_IMPL,
            "    # ADVERSARIAL: drop the once-only guard and always perform a load,\n"
            "    # even when the object is already loaded (re-import every access).\n"
            "    c.loaded = True\n"
            "    c.load_count = c.load_count + 1\n",
        ),
        "refinement": "an obj getter that re-ran self._getobj() on every read (no `if "
                      "obj is None` guard) would re-import the module on each access — a "
                      "duplicate import side effect. The single-load contract (used by "
                      "the marker-dedup `# used to avoid Instance collector marker "
                      "duplication`) is broken; repeated imports change observable "
                      "collection behaviour and re-run top-level code, not a faithful fix.",
        "rationale": "rejected by access_object's conditional counter permission: on an "
                     "already-loaded container only Acc(c.load_count, 1/2) is held, so the "
                     "unconditional increment is a permission failure (backing the "
                     "Implies(Old(c.loaded), load_count==Old(load_count)) value clause).",
    },

    # === uniqueness (supporting near-miss): off-by-one over-count ==========
    # Cheap supporting case: increment by 2 instead of 1 on a fresh load.
    # Violates Implies(not Old(loaded), load_count==Old(load_count)+1).
    {
        "id": "access-plus-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ACCESS_IMPL,
            "    if not c.loaded:\n"
            "        c.loaded = True\n"
            "        c.load_count = c.load_count + 2\n",
        ),
        "refinement": "loading the underlying object twice per first access (two import "
                      "side effects) is not the gold behaviour: a package's top-level code "
                      "would run twice, changing observable side effects; not a faithful patch.",
        "rationale": "rejected by access_object Ensures Implies(not Old(c.loaded), "
                     "load_count==Old(load_count)+1): a fresh access here yields +2.",
    },
]


# No @ContractOnly axioms and no A-consumed callee in this bundle (axioms region
# empty; the load primitive is modelled DEEPLY and validated against real pytest
# by axiom_check.py / G-AX as an A-reference, not a consumed axiom). There is no
# axiom Requires-domain to fuzz or contain at the SPEC layer, so AXIOM_TESTS is
# empty by construction. (The A-reference soundness/timing check already lives in
# axiom_check.py and is exercised by G-AX, the two-state real-pytest differential.)
AXIOM_TESTS = []
