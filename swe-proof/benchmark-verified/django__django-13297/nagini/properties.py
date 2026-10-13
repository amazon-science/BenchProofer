# properties.py — PBT manifest for django__django-13297. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto.
#
# Defended surface (model.py, the FROZEN spec):
#   wrap_kwarg_value(value: int) -> Wrapped, precondition includes
#     deferrals_run(0), postcondition =
#     (P1) deferrals_run(0)                              obligation (3): the
#          ledger of deferred computations run comes back at its ENTRY count, so
#          this operation ran NONE of them — THE PRESERVATION discriminator.
#     (P2a) deferral_of(Result(), value)                 facet 1a: resolution
#          PROVENANCE — the entry carries the deferred computation captured for
#          THIS value. Unconditional, on the whole admissible domain (SHARED, not
#          a discriminator): it is what forbids handing back an entry built
#          around some other value, at any value.
#     (P2b) Implies(not own_type_unpreparable(value),
#             resolves_to(Result(), value))                facet 1b: resolution
#          ROUND-TRIP — running the entry's deferred computation yields exactly
#          the original value. Guarded for the same reason P3b is: on the
#          `own_type_unpreparable` family the real operation may return, silently
#          and still binder-recognised, an entry whose deferred computation hands
#          back a value DERIVED from this one, so an unconditional round-trip
#          would predict an outcome the operation does not produce. Off the
#          family it is unconditional (SHARED, not a discriminator).
#     (P3a) binder_accepts(Result())                     facet 2a: WHOLE-DOMAIN
#          binder recognition — the binder does not refuse the entry as an
#          unsupported type. Unconditional, so it is the discriminator that holds
#          at every value, including the unpreparable family.
#     (P3b) Implies(not own_type_unpreparable(value),
#             binder_castable(Result(), value, type_of(value)))   facet 2b: the
#          per-value resolution discriminator — the unforgeable directive-8
#          capability, guarded because the real operation gives no per-value
#          resolution guarantee on the `own_type_unpreparable` family (it may
#          abort, or return an entry the binder recognises and then cannot
#          resolve to the value).
#     (P4) Exsures(Exception, own_type_unpreparable(value)) AND
#          Exsures(Exception, deferrals_run(0))         PARTIALITY: aborting is
#          PERMITTED only for a value in the `own_type_unpreparable` family, and
#          the ledger comes back at
#          its entry count on the ABORTING exit too, so an abort is not a route
#          by which a deferred computation could have been run unobserved.
#
#   `binder_castable` is an abstract @ContractOnly @Predicate (NO body): it cannot
#   be Fold-ed into existence and it names the SPECIFIC entry/value/type, so a
#   capability obtained for some other entry/value cannot be laundered onto the
#   result.  Its SOLE producer is `wrap_resolvable(value)`'s Ensures (grants
#   binder_castable(Result(), value, type_of(value))).  `wrap_opaque(value)` and
#   the bare `Wrapped()` constructor grant NO P3 capability at all.  `deferral_of`
#   is an abstract @ContractOnly @Predicate on the same terms, naming the SPECIFIC
#   entry AND value, so P2a cannot be discharged with a capability obtained for a
#   different value: that is what keeps the guarded P2b from opening a hole where
#   an impl substitutes an entry built for something else on the guarded family.
#
#   `deferrals_run(n)` is likewise an abstract @ContractOnly @Predicate (NO body)
#   meaning "exactly n deferred computations have been run so far".  `run_deferral`
#   consumes deferrals_run(n) and yields deferrals_run(n + 1); with no body to
#   Fold there is NO way back from n + 1 to n, so an impl that runs ANY entry's
#   deferred computation on ANY path cannot hand the ledger back at 0 and cannot
#   discharge P1.  `resolves_to(w, value)` and `deferral_of(w, value)` are
#   themselves abstract @ContractOnly
#   @Predicate (NO body) and NOT a readable field or a pure projection: it can be
#   held and handed back but never EVALUATED, so an impl cannot turn it into the
#   value, cannot test the value and cannot branch on it, and there is no
#   Unfold-and-read escape (an attempt is refused at TRANSLATION time, not merely
#   unprovable).  `run_deferral` is therefore the ONLY route from an entry to its
#   value, and it charges the ledger.  That pairing is what makes P1 load-bearing:
#   with a readable field — or with a @Pure projection over the entry, which is
#   equally free and silent — an impl could resolve the entry invisibly and
#   eager-vs-deferred would be indistinguishable in the model.
#
#   `value: int` is a PURE immutable value-tag — it carries NO Acc(...) permission
#   (it is not a heap object).  There is therefore NO read-only frame-mutation
#   surface on this instance (see 'assessment'); the frame-mutation class is N/A
#   and is honestly omitted.  The discriminating attacks for THIS spec are the
#   capability ones — (a) satisfy P1/P2 without producing P3 (cheapest non-doing
#   impl); (b) launder a capability from a different entry/value onto Result();
#   (c) produce the capability only on a sub-domain — AND the effect-timing ones:
#   (d) produce a fully binder-resolvable entry but run a deferred computation
#   while building it (whole domain, part of the domain, or on a different
#   entry), destroying the deferral P1 requires be preserved — AND (e) the
#   ON-FAMILY ones, which try to spend the relaxation the guards on P2b/P3b
#   introduce: on the `own_type_unpreparable` family, substitute an entry built
#   for another value, hand back the stand-in the binder refuses, or run a
#   deferred computation there. Each is refuted by the clause that stayed
#   UNCONDITIONAL on that family (P2a, P3a, P1 respectively), which is what makes
#   the guards a relaxation of two clauses rather than of the contract.
from pathlib import Path

INSTANCE = "django__django-13297"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
# The complete current impl-region body (lines between # impl-start / # impl-end).
# Swapping on this whole block GUARANTEES every edit stays inside the impl region,
# so the frozen spec is never touched (markers.same_spec holds for every case).
_IMPL = "    w = wrap_resolvable(value)  # type: Wrapped\n    return w"

# Frozen anchors from the spec region: the three postcondition clauses and the
# precondition clause the battery defends. Asserted at import so a spec edit that
# forgets this file fails loudly instead of silently defending stale text.
_ANCHORS = (
    "    Requires(deferrals_run(0))",
    "    Ensures(deferrals_run(0))",
    "    Ensures(deferral_of(Result(), value))",
    "    Ensures(Implies(not own_type_unpreparable(value),\n"
    "                    resolves_to(Result(), value)))",
    "    Ensures(binder_accepts(Result()))",
    "    Ensures(Implies(not own_type_unpreparable(value),\n"
    "                    binder_castable(Result(), value, type_of(value))))",
    # the effectful ledger-advancing callee the effect-timing attacks use
    "    Ensures(deferrals_run(n + 1))",
    # the PARTIALITY clauses: aborting is permitted only for a value in the
    # `own_type_unpreparable` family, and the ledger is preserved on the
    # aborting exit too
    "    Exsures(Exception, own_type_unpreparable(value))",
    "    Exsures(Exception, deferrals_run(0))",
    # the resolution fact is an INERT capability, never an evaluable projection:
    # this is what leaves run_deferral as the only route to a deferred value
    "@ContractOnly\n@Predicate\ndef resolves_to(w: 'Wrapped', value: int) -> bool:",
    "@ContractOnly\n@Predicate\ndef deferral_of(w: 'Wrapped', value: int) -> bool:",
)
for _a in _ANCHORS:
    if _a not in _BASE:
        raise AssertionError(f"spec drift: anchor missing from model.py: {_a!r}")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in source")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Build a full model.py variant whose ONLY change is the impl-region body."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE — full model.py variants (same spec, swapped impl); host Nagini verify
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness): structurally different but CORRECT ----
    # The gold impl binds a named local then returns it. This variant returns the
    # resolvable construction DIRECTLY (no intermediate local) — a real structural
    # reshape that keeps every proof obligation the gold needs (wrap_resolvable's
    # Ensures supplies P2/P3 on the returned value verbatim, and it runs no
    # deferral so P1 survives untouched). MUST verify; if a faithful correct impl
    # cannot satisfy the Ensures => SPEC-TOO-STRONG.
    {
        "id": "pos-direct-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return wrap_resolvable(value)"),
        "rationale": "a correct impl with a different executable shape (direct "
                     "return, no local) must still verify; wrap_resolvable's "
                     "Ensures supplies P2/P3 unchanged and it runs no deferred "
                     "computation, so P1 holds. Else SPEC-TOO-STRONG.",
    },

    # ---- POSITIVE CONTROL #2 (soundness): branch reshape, both paths correct ---
    # A genuine control-flow reshape: split on value's sign, but BOTH branches do
    # the binder-resolvable construction, so the capability P3 holds on every path
    # and neither path runs a deferral.
    # (Branch-reorder, not loop-direction flip — avoids the front-recursive-fold
    # lemma trap of pilot AVOID #3.) MUST verify.
    {
        "id": "pos-branch-both-resolvable",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if value >= 0:\n"
            "        a = wrap_resolvable(value)  # type: Wrapped\n"
            "        return a\n"
            "    b = wrap_resolvable(value)  # type: Wrapped\n"
            "    return b"
        ),
        "rationale": "a structurally-different (branched) impl in which EVERY path "
                     "performs the resolvable construction must verify; both paths "
                     "grant P3 for the actual value and neither runs a deferral. "
                     "Else SPEC-TOO-STRONG.",
    },

    # ---- POSITIVE CONTROL #3 (soundness): P1 forbids RUNNING deferrals, not ---
    # ---- BUILDING extra entries ----------------------------------------------
    # Guards the new preservation clause against being read as "do nothing extra".
    # This impl constructs an additional deferred entry and discards it: wasteful
    # but CORRECT, because constructing an entry does not run its deferred
    # computation, so no advisory notice is raised and the ledger is untouched.
    # MUST verify — if it were rejected, P1 would be pinning an incidental
    # allocation count rather than the effect the real operation actually avoids.
    {
        "id": "pos-extra-entry-unrun",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    spare = wrap_resolvable(value)  # type: Wrapped\n"
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    return w"
        ),
        "rationale": "P1 forbids RUNNING a deferred computation, not building "
                     "entries: an impl that constructs a spare entry and never "
                     "runs it raises no advisory notice and must still verify. If "
                     "it were REJECTED, P1 would over-fit to the gold's allocation "
                     "count => SPEC-TOO-STRONG.",
    },

    # ---- ADMISSIBILITY: the precondition accepts a normal F2P-shaped input ----
    # The value-tag domain is unrestricted, so admissibility is exercised by
    # performing the contracted construction on the actual parameter and
    # Assert-ing BOTH capabilities it grants — proving the input is in-domain and
    # that the two facets are genuinely obtainable, not merely unfalsifiable.
    # (The probe is on `value` rather than on a constant: the construction is
    # PARTIAL, so a constant probe's permitted abort would propagate to this
    # operation's exceptional exit, where the partiality clause is about the
    # PARAMETER — an unrelated value. Probing the parameter keeps the case's
    # intent and adds no control flow.) MUST verify; else PRECOND-TOO-STRONG.
    {
        "id": "admiss-concrete-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    Assert(deferral_of(w, value))\n"
            "    Assert(binder_accepts(w))\n"
            "    if not own_type_unpreparable(value):\n"
            "        Assert(resolves_to(w, value))\n"
            "        Assert(binder_castable(w, value, type_of(value)))\n"
            "    return w"
        ),
        "rationale": "an arbitrary in-domain value is admitted: the hook-exposing "
                     "construction is callable on it and grants resolution "
                     "PROVENANCE and binder RECOGNITION unconditionally, plus the "
                     "round-trip and the per-value binder capability off the "
                     "`own_type_unpreparable` family — which is exactly what the "
                     "real construction guarantees (off that family it resolves "
                     "faithfully; on it, resolution may fail or hand back a value "
                     "derived from this one, so an unguarded round-trip Assert "
                     "here would claim what the real callee does not do, while "
                     "provenance still holds there). Else PRECOND-TOO-STRONG.",
    },

    # ---- UNGROUNDED-ORACLE / CHEAPEST-NON-DOING: bare Wrapped() ---------------
    # The cheapest impl that satisfies P1 WITHOUT doing the work: allocate a fresh
    # Wrapped(). It runs no deferral (P1 fine), but the constructor promises
    # nothing about the resolution projection (P2) and grants NO binder_castable
    # capability — P3 is unobtainable (the predicate is abstract, no body to Fold).
    # MUST reject.
    # REFINEMENT: a faithful real patch that stores the *raw value*/a plain entry
    # instead of the deferred binder-resolvable one leaves an entry that the
    # type-directed binder never casts; the DB binder rejects it ("unsupported
    # type") and test_template_params_filtering still FAILS — does not resolve F2P.
    {
        "id": "weak-bare-wrapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = Wrapped()  # type: Wrapped\n"
            "    return w"
        ),
        "refinement": "the faithful real analogue (store a plain non-resolvable "
                      "entry carrying the value) is exactly the pre-patch shape: "
                      "the type-directed binder does not cast it, the binding "
                      "fails 'unsupported type', so test_template_params_filtering "
                      "does NOT pass — verify would not imply resolve.",
        "rationale": "rejection comes from postcondition clauses P2/P3: the bare "
                     "Wrapped constructor promises nothing about the resolution "
                     "projection and never grants the abstract capability, which "
                     "cannot be Folded into existence. Viper reports the FIRST "
                     "unprovable clause, which here is the unconditional P2a "
                     "deferral_of(Result(), value); P3a and (off the guarded "
                     "family) P2b/P3b are equally unprovable on a bare entry. "
                     "If it VERIFIED, the spec "
                     "would not actually require binder-resolvability => "
                     "SPEC-TOO-WEAK.",
    },

    # ---- UNGROUNDED / PRE-PATCH ECHO: wrap_opaque(value) ---------------------
    # The pre-patch construction itself: resolves to value (P2) and runs no
    # deferral (P1), but is the NON-resolvable deferred stand-in — grants no
    # capability. MUST reject. This is literally the bug; if it verified, the spec
    # would admit the pre-patch impl.
    # REFINEMENT: this IS the pre-patch non-resolvable wrapping
    # (model_prepatch.py); G-RESOLVE on it fails (the F2P crash 'unsupported
    # type').
    {
        "id": "weak-opaque-wrapping",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_opaque(value)  # type: Wrapped\n"
            "    return w"
        ),
        "refinement": "wrap_opaque models the pre-patch non-resolvable deferred "
                      "stand-in (meta.prepatch_models): the binder leaves it "
                      "unresolved and test_template_params_filtering crashes with "
                      "the regression error — does NOT resolve the F2P.",
        "rationale": "rejection comes from P3a binder_accepts(Result()): "
                     "wrap_opaque's Ensures grants the resolution projection but "
                     "NEITHER binder capability, and P3a is the recognition half "
                     "that stayed unconditional, so it is unprovable on EVERY "
                     "value rather than only off the guarded family. That is the "
                     "exact discriminating clause model_prepatch.py fails, "
                     "measured on the twin as `Postcondition of wrap_kwarg_value "
                     "might not hold. There might be insufficient permission to "
                     "access binder_accepts(Result())` (G-DIFF). "
                     "If it VERIFIED => SPEC-TOO-WEAK (admits the pre-patch bug).",
    },

    # ---- CONTROL-FLOW-EFFECT / CAPABILITY LAUNDERING -------------------------
    # Obtain a real capability for a DIFFERENT entry+value (wrap_resolvable(7)
    # grants binder_castable(other, 7, type_of(7))), then return a bare Wrapped()
    # and try to discharge P3 = binder_castable(Result(), value, type_of(value)) on
    # IT. MUST reject: the capability names the specific entry/value/type and
    # cannot be laundered across entries (directive-8 grounding). This is the
    # attack a value-only abstraction would miss.
    {
        "id": "weak-launder-capability",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    other = wrap_resolvable(7)  # type: Wrapped\n"
            "    Assert(binder_castable(other, 7, type_of(7)))\n"
            "    w = Wrapped()  # type: Wrapped\n"
            "    return w"
        ),
        "refinement": "holding a binder-resolution capability for some unrelated "
                      "entry/value does NOT make the returned plain entry "
                      "binder-resolvable; the real DB binder inspects the ACTUAL "
                      "returned object (it must expose the resolution hook for "
                      "THIS value). The returned plain entry does not -> the F2P "
                      "still crashes; does NOT resolve.",
        "rationale": "rejection comes from the clauses tied to Result(): a "
                     "capability for `other`/`7` cannot discharge "
                     "binder_castable(Result(), value, type_of(value)) — the "
                     "abstract predicate names the specific entry, value and "
                     "real type and is not laundered across entries. Viper "
                     "reports the first such clause, P2a "
                     "deferral_of(Result(), value), which is entry-and-value "
                     "named on the same terms and unconditional, so the "
                     "laundering is refused on the whole domain. If it VERIFIED "
                     "=> SPEC-TOO-WEAK (the "
                     "capability would be forgeable/launderable).",
    },

    # ---- PARTIAL-DOMAIN ------------------------------------------------------
    # Correct on most of the domain (value < 0 -> resolvable), wrong on the
    # sub-domain value >= 0 (returns the opaque non-resolvable construction). MUST
    # reject: P3 cannot be established on the value>=0 branch.
    # REFINEMENT: such a patch (resolvable only for negatives) leaves the F2P str
    # 'Rene Magritte' (a non-negative-tag value) built opaquely -> the ORM filter
    # still crashes for it -> does NOT resolve the F2P.
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if value < 0:\n"
            "        a = wrap_resolvable(value)  # type: Wrapped\n"
            "        return a\n"
            "    b = wrap_opaque(value)  # type: Wrapped\n"
            "    return b"
        ),
        "refinement": "a patch that produces the binder-resolvable entry only for "
                      "some values and the opaque stand-in for the rest leaves the "
                      "F2P value (e.g. the str 'Rene Magritte') built opaquely; the "
                      "binder cannot resolve it and the filtering test still "
                      "crashes — does NOT resolve the F2P.",
        "rationale": "rejection comes from P3 on the value>=0 path: wrap_opaque "
                     "grants neither binder capability, so P3a "
                     "binder_accepts(Result()) is unprovable there (that is the "
                     "clause Viper reports, and being unguarded it bites on that "
                     "whole path), and so is P3b off the guarded family. If it "
                     "VERIFIED, the "
                     "spec would admit an impl that repairs only part of the input "
                     "domain => SPEC-TOO-WEAK.",
    },

    # ---- SUPPORTING near-miss: wrong value wrapped ---------------------------
    # Builds the binder-resolvable entry, and runs no deferral — so P1 and P3-for-
    # its-own-value hold — but wraps value+1. Fails P2a on the WHOLE domain (the
    # entry it hands back carries value+1's deferred computation, not this
    # value's), and fails P2b/P3b off the guarded family. Confirms the resolution
    # clauses are load-bearing, not just P1/P3 — and specifically that guarding
    # the round-trip P2b did NOT license substituting an entry built for another
    # value on the guarded family, because P2a is unconditional there.
    {
        "id": "weak-wrong-resolution",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value + 1)  # type: Wrapped\n"
            "    return w"
        ),
        "refinement": "an entry that resolves to a DIFFERENT value (value+1) does "
                      "not faithfully stand in for the original URL kwarg; the "
                      "context value is wrong and the F2P lookup (by the original "
                      "value) fails — does NOT resolve.",
        "rationale": "rejection comes from P2a (deferral_of(Result(), value) "
                     "fails on EVERY value: the capability held is for value+1, "
                     "and the predicate is abstract, names both entry and value, "
                     "and has no body to Fold, so it cannot be laundered across "
                     "values) and additionally from P2b/P3b for the REQUIRED "
                     "(value, type_of(value)) triple off the guarded family. "
                     "Supporting near-miss confirming the resolution clauses are "
                     "load-bearing. If it VERIFIED => SPEC-TOO-WEAK.",
    },

    # ---- EFFECT-TIMING (the P1 discriminator): EAGER DEFERRAL RUN ------------
    # The whole-domain effect attack. The construction is the fully correct
    # binder-resolvable one, so P2 and P3 are discharged verbatim — but before
    # handing the entry on, this impl RUNS its deferred computation. MUST reject:
    # running it advances the abstract ledger to 1 and there is no way back, so
    # P1's deferrals_run(0) is unprovable.
    {
        "id": "weak-eager-deferral-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    if not own_type_unpreparable(value):\n"
            "        seen = run_deferral(w, value, 0)  # type: int\n"
            "    return w"
        ),
        "refinement": "the faithful real analogue is the gold binder-resolvable "
                      "construction PLUS one on-the-spot resolution of the entry "
                      "while the mapping is assembled. That raises the advisory "
                      "notice at assembly time instead of at consumer access: the "
                      "notice is attributed to the wrong moment, and under a "
                      "configuration that escalates such notices to errors the "
                      "assembly aborts before any entry exists. The test that "
                      "asserts the notice arrives on ACCESS (and the cached-view "
                      "test) then fail — does NOT resolve.",
        "rationale": "rejection comes from P1 deferrals_run(0): run_deferral "
                     "consumes deferrals_run(0) and yields deferrals_run(1), and "
                     "the predicate is abstract (no body to Fold) so the count "
                     "cannot be restored. If it VERIFIED, the spec would not "
                     "require the deferral to survive the build => SPEC-TOO-WEAK "
                     "(this is the exact hole the prior audit exploited). The "
                     "run is taken where the model can express it -- running the "
                     "RETURNED entry consumes its round-trip capability, which "
                     "the contract grants off the `own_type_unpreparable` family "
                     "-- so the rejection is P1 itself and not an unavailable "
                     "precondition.",
    },

    # ---- EFFECT-TIMING, PARTIAL DOMAIN --------------------------------------
    # The same effect attack confined to part of the domain: the deferral is run
    # only for non-negative value-tags. MUST reject — P1 must hold on EVERY path,
    # and the F2P-shaped value lands on the offending branch.
    {
        "id": "weak-partial-eager-deferral-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    if value >= 0 and not own_type_unpreparable(value):\n"
            "        seen = run_deferral(w, value, 0)  # type: int\n"
            "    return w"
        ),
        "refinement": "resolving the entry on the spot for only part of the value "
                      "domain still raises the advisory notice at assembly time for "
                      "the values on that branch (the F2P-shaped value among them), "
                      "so the access-time-notice test still fails — does NOT "
                      "resolve.",
        "rationale": "rejection comes from P1 on the guarded path: the ledger is at "
                     "1 there and cannot be returned to 0, so deferrals_run(0) is "
                     "unprovable at the join. If it VERIFIED, a sub-domain effect "
                     "violation would slip through => SPEC-TOO-WEAK.",
    },

    # ---- EFFECT-TIMING, A DIFFERENT ENTRY ------------------------------------
    # Sharpens P1 from "do not resolve the entry you return" to "run NO entry's
    # deferred computation". The returned entry is never resolved; a spare entry
    # for the same value is built and resolved instead. MUST reject: the advisory
    # notice is raised all the same, at assembly time, so the ledger moves.
    {
        "id": "weak-other-entry-deferral-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    spare = wrap_opaque(value)  # type: Wrapped\n"
            "    seen = run_deferral(spare, value, 0)  # type: int\n"
            "    return w"
        ),
        "refinement": "resolving a SEPARATE deferred entry for the same value "
                      "during assembly raises the same advisory notice at the same "
                      "wrong moment (and aborts assembly under an escalating "
                      "configuration), even though the returned entry itself was "
                      "never touched — does NOT resolve.",
        "rationale": "rejection comes from P1, which counts deferred computations "
                     "run by ANY entry, not just Result(): the ledger is global and "
                     "monotone. If it VERIFIED, the spec would only protect the "
                     "returned entry and an impl could raise the notice early via a "
                     "throwaway entry => SPEC-TOO-WEAK. The throwaway is the "
                     "TOTAL hookless construction, whose round-trip capability "
                     "is unconditional, so the run is expressible on the WHOLE "
                     "domain and P1 is the sole clause that rejects.",
    },

    # ---- EFFECT-TIMING + ECHO: run, then rebuild from the resolved value -----
    # An ungrounded-oracle flavoured effect attack: resolve a probe entry to
    # recover the value, then build the returned entry from the value so obtained.
    # Every value-level clause would be satisfiable this way; MUST reject, because
    # obtaining the value at all required running a deferral, which moved the
    # ledger. Confirms that making the resolution fact an INERT capability rather
    # than a readable field is what closes the free-resolution path.
    {
        "id": "weak-run-then-rewrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    probe = wrap_opaque(value)  # type: Wrapped\n"
            "    seen = run_deferral(probe, value, 0)  # type: int\n"
            "    w = wrap_resolvable(seen)  # type: Wrapped\n"
            "    return w"
        ),
        "refinement": "recovering the value by resolving a probe entry raises the "
                      "advisory notice during assembly exactly as the eager attack "
                      "does; the rebuilt entry is fine but the notice already fired "
                      "at the wrong moment — does NOT resolve.",
        "rationale": "rejection comes from P1: the only runtime route to a deferred "
                     "entry's value is run_deferral, which advances the ledger "
                     "irreversibly. If it VERIFIED, an impl could launder the value "
                     "out of a deferred entry for free and the resolution "
                     "projection would be a readable field in disguise => "
                     "SPEC-TOO-WEAK.",
    },

    # ---- POSITIVE CONTROL #4 (soundness): PARTIALITY IS PERMITTED, NOT ---------
    # ---- REQUIRED --------------------------------------------------------------
    # Guards the partiality clauses against being read as "you MUST abort on the
    # type-valued family". An alternative way of building the entry that consults
    # no per-value type would return an entry for EVERY value and never abort;
    # this impl models exactly that (it takes the resolvable construction on both
    # sides of the case split, so it returns normally on the type-valued family
    # too). MUST verify — if it were REJECTED, the spec would be pinning an
    # incidental limitation as required behaviour and would exclude a strictly
    # better way of building the entry => SPEC-TOO-STRONG.
    {
        "id": "pos-never-aborts",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if own_type_unpreparable(value):\n"
            "        a = wrap_resolvable(value)  # type: Wrapped\n"
            "        return a\n"
            "    b = wrap_resolvable(value)  # type: Wrapped\n"
            "    return b"
        ),
        "rationale": "aborting on the type-valued family is PERMITTED, never "
                     "REQUIRED: an impl that returns an entry for every value "
                     "satisfies P1-P3 on every path and must still verify. If it "
                     "were REJECTED, the partiality clause would be over-fitting "
                     "an incidental limitation => SPEC-TOO-STRONG.",
    },

    # ---- EFFECT-TIMING, THE FREE-READ SIDE CHANNEL (this audit's hole) --------
    # THE REGRESSION TEST for the exact weakness a prior revision shipped. That
    # revision exposed what an entry resolves to as an EVALUABLE pure projection
    # over the entry. An impl could then read the value for free and silently —
    # so building the entry and then resolving it on the spot were
    # indistinguishable, and P1 constrained only the effectful route while the
    # projection was a side channel straight around it. Here the resolution fact
    # is an INERT capability instead: it can be held but never evaluated, so the
    # ONLY way to learn the value is the ledger-charging run. This case is that
    # attack transposed onto the current vocabulary — obtain the value, then hand
    # the (correctly built) entry on. MUST reject: P2 and P3 are discharged
    # verbatim, so ONLY P1 can catch it.
    {
        "id": "weak-peek-then-hand-on",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    if not own_type_unpreparable(value):\n"
            "        peek = run_deferral(w, value, 0)  # type: int\n"
            "        Assert(peek == value)\n"
            "    return w"
        ),
        "refinement": "the faithful real analogue is the gold binder-resolvable "
                      "construction plus one on-the-spot consultation of what the "
                      "entry resolves to, while the mapping is still being "
                      "assembled. Consulting it RUNS the deferred computation, so "
                      "the advisory notice fires at assembly time instead of at the "
                      "consumer's access, and under a configuration that escalates "
                      "such notices to errors the assembly aborts before any entry "
                      "exists. The test asserting the notice arrives on ACCESS, and "
                      "the cached-view test, then fail — does NOT resolve.",
        "rationale": "rejection comes from P1 alone: the entry handed on is the "
                     "fully correct one (P2/P3 hold verbatim), so the ONLY clause "
                     "that can reject is deferrals_run(0). Learning the value costs "
                     "one ledger unit and the abstract ledger cannot be walked back. "
                     "If it VERIFIED, the resolution fact would be a free silent "
                     "read after all and eager-vs-deferred would be unobservable => "
                     "SPEC-TOO-WEAK (the exact hole a prior revision shipped). "
                     "The peek is taken off the `own_type_unpreparable` family, "
                     "which is where the contract grants the round-trip "
                     "capability the peek consumes, so what rejects the case is "
                     "P1 and not an unavailable precondition.",
    },

    # ---- EFFECT-TIMING SIDE CHANNEL, LOAD-BEARING ON CONTROL FLOW ------------
    # Hardens the case above against the objection that the peeked value was
    # dead and might be optimised away: here it DRIVES the branch. MUST reject
    # for the same reason — learning the value at all already moved the ledger.
    {
        "id": "weak-peek-drives-control-flow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    if not own_type_unpreparable(value):\n"
            "        peek = run_deferral(w, value, 0)  # type: int\n"
            "        if peek == value:\n"
            "            return w\n"
            "        b = wrap_opaque(value)  # type: Wrapped\n"
            "        return b\n"
            "    return w"
        ),
        "refinement": "branching on what the entry resolves to still requires "
                      "running the deferred computation during assembly, so the "
                      "advisory notice fires at the wrong moment exactly as above — "
                      "does NOT resolve.",
        "rationale": "rejection comes from P1 on the returning path: the peek is "
                     "load-bearing (it selects the branch), so it cannot be dismissed "
                     "as dead code, and it still costs a ledger unit that cannot be "
                     "restored. If it VERIFIED => SPEC-TOO-WEAK.",
    },

    # ---- PARTIALITY ABUSED AS A LAUNDRY CHUTE --------------------------------
    # The abort exit must not be a hole. This impl runs the deferred computation
    # and THEN aborts, inside the one case where aborting is permitted — trying
    # to use the exceptional exit to hide the effect. MUST reject: the ledger is
    # required back at its entry count on the ABORTING exit too, which is
    # precisely what the second partiality clause is for.
    {
        "id": "weak-abort-hides-deferral-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    if own_type_unpreparable(value):\n"
            "        probe = wrap_opaque(value)  # type: Wrapped\n"
            "        seen = run_deferral(probe, value, 0)  # type: int\n"
            "        raise Exception()\n"
            "    return w"
        ),
        "refinement": "running the deferred computation and then reporting failure "
                      "still raised the advisory notice at assembly time; a failure "
                      "report is not a licence to have run it — does NOT resolve.",
        "rationale": "rejection comes from the ledger clause on the EXCEPTIONAL "
                     "exit: aborting is permitted, but the ledger must still come "
                     "back at its entry count there. If it VERIFIED, the permitted "
                     "abort would be a laundry chute for an arbitrary effect => "
                     "SPEC-TOO-WEAK. The deferred computation that is run belongs "
                     "to the TOTAL hookless construction, whose round-trip "
                     "capability is unconditional: the abort branch is exactly the "
                     "`own_type_unpreparable` family, where the round-trip "
                     "capability of the RETURNED entry is deliberately NOT granted, "
                     "so running that entry instead would be refused at the call "
                     "and this case would never reach the clause it defends.",
    },

    # ---- PARTIALITY ABUSED TO SKIP THE WORK ----------------------------------
    # The complement: aborting where aborting is NOT permitted. An impl that just
    # fails does no work at all and would trivially satisfy every positive clause
    # if the abort were unconstrained. MUST reject: the exceptional exit is
    # licensed ONLY for a value that is itself a type.
    {
        "id": "weak-abort-unjustified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    raise Exception()"
        ),
        "refinement": "refusing to build an entry for an ordinary value is the "
                      "assembly failing outright: no context value is produced, so "
                      "the view cannot render and the F2P test does not pass — does "
                      "NOT resolve.",
        "rationale": "rejection comes from the partiality clause "
                     "own_type_unpreparable(value), which is unprovable for an arbitrary "
                     "value: the abort is licensed only on the one family whose own "
                     "runtime type cannot be consulted. If it VERIFIED, the cheapest "
                     "non-doing impl (fail always) would satisfy the spec => "
                     "SPEC-TOO-WEAK.",
    },
    # ---- ON-FAMILY BOUNDARY #1: SUBSTITUTE ANOTHER VALUE'S ENTRY -------------
    # THE REGRESSION TEST for the guard on the round-trip clause P2b. On the
    # `own_type_unpreparable` family the contract promises no round-trip and no
    # per-value binder resolution, so a rival can argue it may hand back whatever
    # it likes there. It may not: P2a (`deferral_of`) is UNCONDITIONAL, so the
    # entry must still be the one built for THIS value on that family too. MUST
    # reject. If it VERIFIED, guarding P2b would have opened exactly the hole the
    # guard was supposed to avoid — an impl free to substitute a stand-in built
    # for something else on a domain slice it cannot even be asked to identify.
    {
        "id": "weak-family-substituted-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if own_type_unpreparable(value):\n"
            "        a = wrap_resolvable(value + 1)  # type: Wrapped\n"
            "        return a\n"
            "    b = wrap_resolvable(value)  # type: Wrapped\n"
            "    return b"
        ),
        "refinement": "on the values where the real construction gives no "
                      "round-trip guarantee it still builds the entry around the "
                      "value it was handed; an entry built around a DIFFERENT "
                      "value carries the wrong deferred computation, so the "
                      "consumer that reaches for it gets some other kwarg's "
                      "value — the view renders the wrong context and the F2P "
                      "lookup by the original value fails; does NOT resolve.",
        "rationale": "rejection comes from P2a deferral_of(Result(), value) on "
                     "the family branch: the capability held there is for "
                     "value+1, it names both entry and value, and the predicate "
                     "is abstract with no body to Fold, so it cannot be laundered "
                     "across values. Distinct from weak-wrong-resolution, which "
                     "substitutes on the WHOLE domain and would still be rejected "
                     "off the family by P2b/P3b: this case isolates the guarded "
                     "family, so it is the case that fails if P2a is ever "
                     "weakened to a guarded clause. If it VERIFIED => "
                     "SPEC-TOO-WEAK.",
    },

    # ---- ON-FAMILY BOUNDARY #2: HAND BACK THE STAND-IN THE BINDER REFUSES ----
    # The same exploit aimed at the guard on P3b. On the family the contract
    # promises no per-value binder RESOLUTION, but P3a (recognition) is
    # unconditional: the entry must never be the hookless stand-in a binder
    # refuses out of hand as an unsupported type. MUST reject.
    {
        "id": "weak-family-binder-refused",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if own_type_unpreparable(value):\n"
            "        a = wrap_opaque(value)  # type: Wrapped\n"
            "        return a\n"
            "    b = wrap_resolvable(value)  # type: Wrapped\n"
            "    return b"
        ),
        "refinement": "the real construction returns a binder-RECOGNISED entry "
                      "even where its resolution carries no guarantee; degrading "
                      "to the hookless stand-in on those values reinstates the "
                      "pre-change failure mode for them (the binder refuses it as "
                      "an unsupported type), so the assembled mapping is not "
                      "usable in a type-directed binding position — does NOT "
                      "resolve.",
        "rationale": "rejection comes from P3a binder_accepts(Result()) on the "
                     "family branch: wrap_opaque grants it at NO value. Distinct "
                     "from weak-partial-domain, which splits on an arithmetic "
                     "sub-domain: this case splits on the very family the guarded "
                     "clauses are relaxed over, so it is the case that fails if "
                     "P3a is ever weakened to a guarded clause. If it VERIFIED, "
                     "the relaxation would license the pre-change shape on part "
                     "of the domain => SPEC-TOO-WEAK.",
    },

    # ---- ON-FAMILY BOUNDARY #3: RUN A DEFERRAL UNDER COVER OF THE GUARD ------
    # The effect attack aimed at the guard. P1 is unconditional, so the family is
    # not a licence to run a deferred computation early either; the run is taken
    # on the TOTAL hookless entry so that it is expressible there at all. MUST
    # reject on the NORMAL exit (weak-abort-hides-deferral-run covers the
    # exceptional one).
    {
        "id": "weak-family-deferral-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    w = wrap_resolvable(value)  # type: Wrapped\n"
            "    if own_type_unpreparable(value):\n"
            "        probe = wrap_opaque(value)  # type: Wrapped\n"
            "        seen = run_deferral(probe, value, 0)  # type: int\n"
            "    return w"
        ),
        "refinement": "resolving a deferred computation while the mapping is "
                      "being assembled raises the advisory notice at assembly "
                      "time rather than at the consumer's access, and under a "
                      "configuration that escalates such notices the assembly "
                      "aborts before any entry exists. Confining that to the "
                      "values whose resolution carries no guarantee does not make "
                      "it acceptable: the notice still fires at the wrong moment "
                      "for them — does NOT resolve.",
        "rationale": "rejection comes from P1 deferrals_run(0) on the family "
                     "branch: the ledger is at 1 there and the abstract predicate "
                     "has no body to Fold, so it cannot be walked back before the "
                     "normal exit. If it VERIFIED, the guarded family would double "
                     "as an effect-timing loophole => SPEC-TOO-WEAK.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — real-callee probes run in the instance Docker image.
# This bundle has A-consumed axioms (wrap_resolvable, wrap_opaque, run_deferral)
# and A-reference deep models (binder_castable, deferrals_run, resolves_to,
# deferral_of,
# type_of, own_type_unpreparable), all grounded in real Django callees:
#   - the post-change binder-resolvable deferred construction
#   - the pre-change non-resolvable deferred construction
#   - Field.get_prep_value                 (the type-directed parameter binder)
#   - the advisory-notice effect that running an entry's deferred computation has
# axiom_check.py is the canonical ground-truth soundness check; per AVOID #6 we
# read it on the HOST and embed its source into the probe (only the probe script
# is mounted in-container). It CALLS the real callees (AVOID #4), opens nothing,
# and uses only stdlib + django (AVOID #5 moot — no file reads).
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# Probe 1: AXIOM-SOUNDNESS — run the canonical axiom_check.main() which executes
# the real Django constructions + binder and asserts every A-reference obligation
# (resolves-to-value on both; post-patch IS binder-resolved to value at real type;
# pre-patch is NOT; alternative result classes admitted; and the effect ledger:
# construction raises NO advisory notice, each resolution raises exactly one).
# Exit 0 iff sound.
_PROBE_SOUNDNESS = _AXIOM_CHECK_SRC + """

# --- PBT axiom-soundness driver (appended) ---------------------------------
import sys as _sys
if __name__ == "__main__":
    rc = main()
    if rc == 0:
        print("PBT-AX-SOUND OK: the real deferred constructions + "
              "Field.get_prep_value + the real advisory-notice effect match "
              "wrap_resolvable/wrap_opaque/run_deferral/binder_castable/"
              "deferrals_run/resolves_to/deferral_of/type_of on all cases.")
    _sys.exit(rc)
"""

# Probe 2: AXIOM-CONTAINMENT (caller-domain coverage). The model passes value:int
# (an arbitrary runtime value at the call site — the F2P reaches a str, the
# problem statement reaches str/int; type_of's branches reach negative, zero and
# positive value-tags). EVERY such caller-reachable value must lie inside the
# construction callees' accepted domain, the binder must resolve the post-patch
# entry to the value at its real type, AND the deferral-ledger obligations must
# hold on it (building raises no notice; each resolution raises exactly one).
# We fuzz a spread of caller-reachable values (str incl. F2P/empty/digit-str,
# +/-/0 int, float) and assert containment: no reachable input falls outside the
# axiom domain (else AXIOM-TOO-WEAK-FOR-CALLER).
_PROBE_CONTAINMENT = r'''
import sys, warnings


def _ensure_django_configured():
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=True)
    import django
    django.setup()


def make_access_value(value):
    """Mirror the real closure: returns the captured value AND raises the
    advisory notice, so the effect ledger is exercised, not silenced."""
    def access_value(value=value):
        warnings.warn("advisory notice about this entry", DeprecationWarning,
                      stacklevel=2)
        return value
    return access_value


def main():
    _ensure_django_configured()
    from django.utils.functional import lazy, SimpleLazyObject, Promise
    from django.db.models.fields import CharField, IntegerField, FloatField

    # Caller-reachable values: the modeled `value: int` value-tag stands for an
    # arbitrary URL-kwarg runtime value. The F2P reaches a str; the problem
    # statement reaches str (slug) and the empty default ""; type_of's branches
    # reach negative / zero / positive tags -> int negatives/zero/positives and
    # a float. Each must be in BOTH construction callees' domain, be
    # binder-resolvable, and obey the deferral-ledger obligations.
    cases = [
        ("Rene Magritte", CharField()),   # the exact F2P str
        ("", CharField()),                 # the kwargs.get("offer_slug", "") default
        ("offer-slug", CharField()),
        ("42", CharField()),
        (0, IntegerField()),               # zero (type_of boundary)
        (7, IntegerField()),               # positive
        (-3, IntegerField()),              # negative (type_of's value<0 branch)
        (-1, IntegerField()),
        (3.5, FloatField()),               # float
        (0.0, FloatField()),
    ]
    failures = []
    for value, field in cases:
        # containment: the resolvable construction accepts this value, and
        # CONSTRUCTING it raises NO advisory notice (deferrals_run unchanged --
        # the model's obligation (3) on the construction step) ...
        try:
            with warnings.catch_warnings(record=True) as rec:
                warnings.simplefilter("always")
                post = lazy(make_access_value(value), type(value))()
            if len(rec) != 0:
                failures.append("constructing the resolvable entry for %r raised "
                                "%d advisory notice(s); the model says "
                                "construction leaves the ledger untouched"
                                % (value, len(rec)))
                continue
        except Exception as e:
            failures.append("resolvable-construction REJECTED reachable value %r: %r" % (value, e))
            continue
        # ... it is a Promise (binder-resolution hook present) ...
        if not isinstance(post, Promise):
            failures.append("reachable value %r: post-patch entry is not a Promise "
                            "(outside binder_castable's producible domain)" % (value,))
            continue
        # ... resolving it raises EXACTLY ONE advisory notice (run_deferral's
        # deferrals_run(n) -> deferrals_run(n + 1)) and yields the value ...
        try:
            with warnings.catch_warnings(record=True) as rec:
                warnings.simplefilter("always")
                resolved = field.get_prep_value(post)
        except Exception as e:
            failures.append("binder RAISED on reachable value %r: %r" % (value, e))
            continue
        if len(rec) != 1:
            failures.append("resolving the entry for %r raised %d advisory "
                            "notice(s), expected exactly 1 (run_deferral advances "
                            "the ledger by one)" % (value, len(rec)))
            continue
        if isinstance(resolved, Promise):
            failures.append("binder left reachable value %r unresolved (still a Promise)" % (value,))
            continue
        if resolved != value:
            failures.append("binder resolved %r to a different value %r" % (value, resolved))
            continue
        if type(resolved) is not type(value):
            failures.append("binder resolved %r to wrong real type %r (expected %r)"
                            % (value, type(resolved), type(value)))
            continue
        # ... and the opaque construction ALSO accepts this value (resolves to it
        # without raising at construction time), so wrap_opaque's domain covers
        # every reachable value too.
        try:
            with warnings.catch_warnings(record=True) as rec:
                warnings.simplefilter("always")
                pre = SimpleLazyObject(make_access_value(value))
            if len(rec) != 0:
                failures.append("constructing the opaque entry for %r raised an "
                                "advisory notice" % (value,))
                continue
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("ignore")
                assert pre == value
        except Exception as e:
            failures.append("opaque-construction REJECTED/misresolved reachable value %r: %r" % (value, e))
            continue

    if failures:
        print("AXIOM-TOO-WEAK-FOR-CALLER: caller-reachable inputs outside the axiom domain:")
        for f in failures:
            print("  -", f)
        return 1
    print("PBT-AX-CONTAIN OK: every caller-reachable value (str incl. F2P/empty, "
          "+/-/0 int, float; %d total) lies inside wrap_resolvable's AND "
          "wrap_opaque's domain, is binder-resolvable to the value at its real "
          "type, is built WITHOUT raising the advisory notice, and raises exactly "
          "one notice per resolution -- no reachable input is uncovered." % len(cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-wrappers-binder",
        "axiom": "wrap_resolvable/wrap_opaque/run_deferral/binder_castable/"
                 "deferrals_run/resolves_to/deferral_of/type_of/"
                 "own_type_unpreparable",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "runs the REAL deferred constructions and the REAL "
                     "Field.get_prep_value binder, and the REAL advisory-notice "
                     "effect (axiom_check.py ground truth): the post-patch "
                     "resolvable entry IS resolved to the value at its real type "
                     "(grants binder_castable), the pre-patch non-resolvable entry "
                     "is NOT (no capability), both resolve to the value, alt result "
                     "classes admitted, AND building either entry raises no notice "
                     "while each resolution raises exactly one (the ledger "
                     "obligations of run_deferral / deferrals_run). If the real "
                     "callee disagreed with any Ensures => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-caller-domain",
        "axiom": "wrap_resolvable/wrap_opaque/run_deferral",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "enumerates the values the model's call site can actually "
                     "reach (str incl. the F2P 'Rene Magritte' and empty default, "
                     "+/-/0 int spanning type_of's branches, float) and asserts "
                     "each lies inside both construction callees' accepted domain, "
                     "is binder-resolvable to the value at its real type, is built "
                     "without raising the advisory notice, and raises exactly one "
                     "notice per resolution. A reachable input outside the domain "
                     "=> AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
