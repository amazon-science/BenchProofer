# properties.py — PBT falsification battery for django__django-15525. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py)
# ---------------------------------------------------------------------------
#   Deployment — the two routing facts of the deployment a loader runs in, as a
#     single GIVEN world: `default_store` (the ambient store an unrouted query
#     falls back to) and `record_store` (the store the related record actually
#     resides in). Both are spec-view text, so no variant can alter them:
#     __init__(self, default_store: int, record_store: int)
#       Requires(False)        # (W) a world is HANDED to a loader, never minted
#     A loader can neither redirect the ambient fallback nor move the related
#     record between stores, so the facts a dereference is judged against are the
#     surroundings', identical at every dereference the loader performs. (W) is
#     what makes that true of a *verifying impl* and not merely of the prose: no
#     impl can produce a second world whose numbers were chosen to make a query
#     it wanted to perform look like it succeeded.
#
#   KeyedRecord(record: ModelInstance, world: Deployment)
#     — the outcome of computing one record's natural key. The ONLY producer of
#       a KeyedRecord, and it is a spec-view constructor (not impl-region text),
#       so no variant can alter it:
#     Requires(Acc(record.routed, 1/2))                    # reads the association
#     Requires(Acc(world.default_store, 1/4) and Acc(world.record_store, 1/4))
#     Requires(dereference_succeeds(record.routed, world.default_store,
#                                   world.record_store))
#                                                          # (K) THE existence
#                                                          # condition of a key,
#                                                          # judged against the
#                                                          # GIVEN world
#     Ensures(Acc(self.routed, 1/2) and self.routed == record.routed)
#     Ensures(Acc(self.queried_store, 1/2))
#     Ensures(self.queried_store == query_store(record.routed,
#                                               world.default_store))
#
#   build_with_natural_key(target_store: int, world: Deployment) -> KeyedRecord
#     Requires(Acc(world.default_store, 1/2) and Acc(world.record_store, 1/2))
#     Requires(target_store != UNROUTED)            # target is a real store
#     Requires(world.record_store == target_store)  # related record lives in target
#         (world.default_store is FREE: any store, the target store itself
#          included, so every clause below is claimed for a target store that IS
#          the ambient default one as well as for one that differs from it)
#     Ensures(Acc(world.default_store, 1/2) and Acc(world.record_store, 1/2))
#     Ensures(Acc(Result().routed, 1/2))            # a share: readable, not assignable
#     Ensures(Result().routed == target_store)      # (A2) the association AT key time
#     Ensures(Acc(Result().queried_store, 1/2))
#     Ensures(Result().queried_store == target_store)   # (Q) where the deref went
#     Ensures(dereference_succeeds(Result().routed, world.default_store,
#                                  world.record_store))  # (A3)
#   @Pure query_store(routed, default) == (default if routed == UNROUTED else routed)
#   @Pure dereference_succeeds(routed, default, record_store)
#               == (query_store(routed, default) == record_store)
#
#   The loader's only non-int input is the world, and it is handed a HALF share of
#   each of its two fields: enough to read the routing facts, never enough to
#   write them, and it must hand that share back (Ensures), so the world it ran in
#   is the world it leaves behind. The objects a loader builds are created inside
#   the impl, and BOTH observables of the result are handed out as a HALF share
#   too, so an impl holds enough permission to read them and never enough to
#   assign them. Neither is a hygiene detail: see `uniq-restate-observables` (the
#   impl that computes the key and then writes the two fields to the values the
#   postcondition wants — refused for lack of permission) and `uniq-move-record`
#   (the impl that rewrites where the related record lives — refused the same
#   way).
#
# Load-bearing content: (W) + (K) + (A2). (K) is a precondition of the ONLY
# operation that can produce a result, so every verifying impl must prove, at the
# moment it computes a key, that the record's own association routes the
# dereference to the store the related record lives in; (A2) then pins the
# returned outcome's association to the target store; and (W) is what forces (K)
# to be judged against the world the loader was handed rather than against
# numbers of the impl's own choosing. Because (K) is a precondition of the
# producer, it binds EVERY key computation an impl performs and not only the one
# whose outcome it returns — a key computed and then discarded is still a
# dereference that had to reach the related record. Without (W) that would be
# empty: an impl could compute the key against a world in which the related
# record happens to live wherever its unassociated query lands, and hand back a
# correctly-associated outcome built against the real one. `uniq-forge-world`,
# `uniq-discarded-unrouted-key`, `uniq-echo-ambient-default` and
# `uniq-skip-assoc-keep-assert` are that family, authored below as reject cases.
#
# The prepatch (model_prepatch.py) computes the key on the freshly built,
# unassociated record and FAILS: where world.default_store != world.record_store
# the unrouted query routes to world.default_store and (K) cannot be established,
# and where they coincide the query does reach the related record but the outcome
# then reports the association UNROUTED, so (A2) fails instead. Because
# world.default_store is free, an impl must associate the record on EVERY
# admissible input, and an association established only where the target store
# differs from the ambient default one is refused on the rest of the domain
# (`uniq-assoc-only-when-not-default`). Note the shape of this claim: it is about
# the state AT the key computation, not about the final state of anything — which
# is why an impl may release the record's association afterwards and still be
# correct (`pos-control-release-after`), while an impl that computes the key first
# and associates afterwards cannot verify at all (`uniq-key-before-assoc`).
#
# Ungrounded-oracle note (directive 2): query_store / dereference_succeeds are
# @Pure but FULLY GROUNDED in their int args (definitions unfolded verbatim in
# the spec — no opaque answer-key), and evaluating them is a statement about a
# routing state rather than a query performed on a store. The echo an impl WOULD
# reach for is to satisfy (K) with numbers of its own instead of the record's own
# state and the world's facts: mint a world whose ambient default equals the
# target (`uniq-forge-world`), or claim the related record lives in the store the
# unassociated query reaches (`uniq-echo-ambient-default`,
# `uniq-skip-assoc-keep-assert`). All are authored below as reject cases; all are
# refused because a world cannot be produced (W) and because (A2)/(Q) read the
# record's association back out of the outcome. Honest positive controls
# (cheapest / structurally-different CORRECT impls) cover the other direction,
# including one that reads the world's facts and one that hands the world on to a
# further, correctly-associated key computation.
#
# Convention on the world's two facts: both are facts about the deployment the
# loader runs in, not values the loader picks, and the spec says so operationally
# rather than in prose — the loader gets a read-only share of each and no way to
# mint another world. Under the refinement map a read of world.record_store
# collapses to a read of the target alias (it is pinned == target_store), and a
# read of world.default_store collapses to DEFAULT_DB_ALIAS; neither is
# assignable, which is the refinement of "a patch cannot move rows between
# databases or redefine the default alias". One call is therefore refined in ONE
# world, and every key computation inside it is judged in that same world.
#
# Control-flow-effect note (directive 4): NOT N/A, and this is the discriminator
# the battery turns on. The spec constrains an ORDER — the association must be
# established BEFORE the key is computed — and it does so without mentioning
# order, by making the outcome producible only from an already-associated record.
# Effect-shaped rivals are therefore authored: `uniq-key-before-assoc` (right
# final values, key computed too early), `uniq-restate-observables` (right final
# values, written after the fact rather than observed), and
# `uniq-discarded-unrouted-key` (right returned value, plus one extra dereference
# that found nothing — an effect the return value cannot show). Two more hide the
# association behind a condition: `uniq-infeasible-guard` behind one the
# precondition makes impossible, and `uniq-assoc-only-when-not-default` behind
# one the precondition leaves FEASIBLE — the target store being other than the
# ambient default. The second is the case a domain pinned to a non-default target
# could not sense at all: with world.default_store free it is refused on the part
# of the domain where the two stores coincide.
#
# Axiom lane: meta.json axioms=[] — NO @ContractOnly axiom is consumed. The
# store-routing mechanism (query_store / dereference_succeeds) is an A-reference
# deep model already validated == the real django.db.utils.ConnectionRouter by
# axiom_check.py (G-AX: all boundary store combos + 20000 fuzz, status pass).
# KeyedRecord is NOT an axiom either: it has a real body, verified against its
# own contract, so nothing here is assumed rather than established. Deployment is
# not an axiom either — it is an ordinary class whose constructor is simply
# unavailable, which is a contract the verifier ENFORCES (see
# `uniq-forge-world`), not an assumption it takes on trust. The PBT axiom lane
# probes a *consumed* axiom's over-approximation against a real callee; there is
# none here, and re-running axiom_check.py would duplicate G-AX. AXIOM_TESTS is
# therefore empty (see 'assessment').
from pathlib import Path

INSTANCE = "django__django-15525"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    # Build the instance (fresh: no store association yet).
    obj = ModelInstance(UNROUTED)
    # Associate it with the target store BEFORE computing the natural key, so
    # the dereference inside natural-key computation routes to the target.
    obj.routed = target_store
    # Compute the natural key of the now-associated instance: the dereference it
    # performs reaches the store the related record lives in, so the key — and
    # with it the resolved outcome — exists.
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). No loop / no fold, so no auto-
# undischargeable lemma is introduced (pilot pitfalls #2/#3 avoided).
# ===========================================================================

# pos-control-direct: build the instance ALREADY associated with the target
# store (pass target_store to the constructor) instead of building it UNROUTED
# and reassigning, and return the outcome directly with no local. Different
# executable shape, same observables: the key is computed on a record associated
# with the target store. Must verify (else SPEC-TOO-STRONG).
_POS_DIRECT = """    # impl-start
    # Build the instance already associated with the target store.
    obj = ModelInstance(target_store)
    return KeyedRecord(obj, world)
    # impl-end"""

# pos-control-via-record-store: associate via the world's record_store instead
# of target_store. Under the precondition world.record_store == target_store this
# is the SAME value, so it is byte-equal to the gold association and CORRECT (the
# refinement.md note: associating via the world's record_store only verifies
# because it is pinned == target_store). A structurally-different correct impl
# that also confirms the spec lets an impl READ the world's routing facts, and
# that the outcome's observables are readable by the impl that produced them.
# Must verify (else SPEC-TOO-STRONG).
_POS_VIA_RECORD = """    # impl-start
    obj = ModelInstance(UNROUTED)
    # world.record_store == target_store by precondition, so this routes to the
    # target. The world's facts are readable — just not writable, and not mintable.
    obj.routed = world.record_store
    keyed = KeyedRecord(obj, world)
    Assert(keyed.queried_store == world.record_store)
    return keyed
    # impl-end"""

# pos-control-release-after: associate the record, compute its natural key, and
# only THEN drop the record's association again. The observables the spec pins
# are what the key computation saw, so a later change to the record cannot
# falsify them — and in the real function the record whose key was computed is
# discarded after the key is in hand, so releasing it afterwards is a dead
# store. This control exists to prove the clause pins the state AT the key
# computation rather than the final state of the record: if it could not verify,
# the spec would be over-fitted to the gold impl's exact sequence
# (SPEC-TOO-STRONG).
_POS_RELEASE_AFTER = """    # impl-start
    obj = ModelInstance(UNROUTED)
    obj.routed = target_store
    keyed = KeyedRecord(obj, world)
    obj.routed = UNROUTED
    return keyed
    # impl-end"""

# pos-control-two-associated-keys: compute the natural key TWICE, both times on
# a record associated with the target store, and return the second outcome. The
# extra dereference is one that DOES find the related record, so it is a
# behaviour the real function's contract permits (an implementation is free to
# resolve a record's identity more than once as long as every dereference it
# performs reaches the related record). This control is the counterpart of
# `uniq-discarded-unrouted-key`: it proves the spec refuses key computations that
# find NOTHING rather than merely counting how many happen — if it could not
# verify, the spec would be pinning the gold impl's dereference COUNT, an
# incidental detail the real function does not guarantee (SPEC-TOO-STRONG).
_POS_TWO_KEYS = """    # impl-start
    first = ModelInstance(target_store)
    scratch = KeyedRecord(first, world)
    Assert(scratch.queried_store == target_store)
    second = ModelInstance(UNROUTED)
    second.routed = target_store
    return KeyedRecord(second, world)
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). A new module-level def would change the spec
# view and break same_spec, so the admissibility witness is injected INSIDE the
# impl region (elided from the spec view). We construct concrete F2P-shaped
# store ids (target=1, default=0, record=1 — the regression scenario: a
# non-default target "other"=1, default=0, the related record in the target)
# and assert the routing clauses hold for them, that the input really is the
# shape where the target store and the ambient default one differ, and that the
# existence condition (K) of a natural key is satisfiable there; we also assert
# the world-facing precondition clause is available on the actual parameters,
# then run the real impl.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    # The world-facing clause really is established on the actual call: the
    # loader can read the deployment's routing facts, and the related record
    # lives in the store being loaded into.
    Assert(target_store != UNROUTED)             # target is a real store
    Assert(world.record_store == target_store)   # related record lives in target
    # The regression scenario: target store 'other' (=1), default store (=0),
    # the related record loaded into the target store (record_store = 1).
    t = 1   # type: int
    d = 0   # type: int
    r = 1   # type: int
    Assert(t != UNROUTED)        # target is a real store
    Assert(r == t)               # related record lives in the target
    Assert(d != r)               # and it is the differing-stores shape
    # A natural key exists for this input: a record associated with the target
    # routes the dereference to the store the related record lives in, so the
    # producer's precondition (K) is satisfiable and the postcondition with it.
    Assert(dereference_succeeds(t, d, r))
    Assert(query_store(t, d) == t)
    # The sub-domain the free ambient default also admits: the target store IS
    # the ambient default one. Both routing clauses hold there as well, so the
    # obligations are claimed on that shape too and an impl cannot escape them
    # by treating it as out of domain.
    t2 = 1  # type: int
    d2 = 1  # type: int
    r2 = 1  # type: int
    Assert(t2 != UNROUTED)
    Assert(r2 == t2)
    Assert(d2 == r2)
    Assert(dereference_succeeds(t2, d2, r2))
    # --- end admissibility witness; the real impl follows unchanged ---
    obj = ModelInstance(UNROUTED)
    obj.routed = target_store
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN rivals — rivals that share the spec exactly and
# change ONLY the impl. Each MUST be rejected; a verifying rival is a true
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-unrouted: the twin's rival impl (model_prepatch.py). Build the instance
# and compute its natural key without ever associating it with the target store.
# Rejected by (K) wherever the ambient default store is not the one the related
# record lives in — the unrouted query routes to world.default_store !=
# world.record_store, so the producer's precondition cannot be established — and
# by (A2) on the rest of the domain, where the fallback route does reach the
# related record but the outcome then reports the association UNROUTED.
_UNIQ_UNROUTED = """    # impl-start
    obj = ModelInstance(UNROUTED)
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-key-before-assoc: the ORDER rival. Compute the natural key on the freshly
# built record and associate it with the target store afterwards, so the final
# state of the record is exactly the gold one and only the moment of the key
# computation differs. Rejected by (K) at the point of the computation.
_UNIQ_ORDER = """    # impl-start
    obj = ModelInstance(UNROUTED)
    keyed = KeyedRecord(obj, world)
    obj.routed = target_store
    return keyed
    # impl-end"""

# uniq-restate-observables: the FRAME rival. Compute the natural key and then
# write the outcome's two observables to the values the postcondition asks for,
# as if where a dereference was sent were a field a later line could revise.
# Rejected for lack of permission: a share of each observable is all any impl
# ever holds.
_UNIQ_RESTATE = """    # impl-start
    obj = ModelInstance(UNROUTED)
    keyed = KeyedRecord(obj, world)
    keyed.routed = target_store
    keyed.queried_store = target_store
    return keyed
    # impl-end"""

# uniq-move-record: the WORLD-FRAME rival. Leave the record unassociated and
# instead rewrite the deployment fact that decides where the dereference lands —
# declare that the related record lives in the ambient default store, which is
# where the unassociated query goes. Rejected for lack of permission: the world's
# facts are handed to a loader as a read-only share, because no patch can move
# rows between databases.
_UNIQ_MOVE_RECORD = """    # impl-start
    obj = ModelInstance(UNROUTED)
    world.record_store = world.default_store
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-forge-world: the WORLD-MINTING rival. Leave the record unassociated and
# satisfy the key's existence condition by producing a world of the impl's own
# choosing — one whose ambient fallback is the store the related record lives in —
# then compute the key against that. Rejected by (W): a world is handed to a
# loader, never minted by it, so the constructor is unavailable on every input.
_UNIQ_FORGE_WORLD = """    # impl-start
    obj = ModelInstance(UNROUTED)
    convenient = Deployment(target_store, target_store)
    keyed = KeyedRecord(obj, convenient)
    return keyed
    # impl-end"""

# uniq-discarded-unrouted-key: the EXTRA-DEREFERENCE rival. Compute the natural
# key of the freshly built, unassociated record FIRST, throw that outcome away,
# and then do it again properly on an associated record and return that. Every
# observable of the returned value is exactly the gold one; the difference is an
# extra dereference that found nothing. Rejected by (K) on the discarded
# computation, because (K) is a precondition of producing ANY key and is judged
# against the same given world at every site.
_UNIQ_DISCARDED = """    # impl-start
    premature = ModelInstance(UNROUTED)
    thrown_away = KeyedRecord(premature, world)
    Assert(thrown_away.routed == UNROUTED)
    obj = ModelInstance(UNROUTED)
    obj.routed = target_store
    return KeyedRecord(obj, world)
    # impl-end"""

# uniq-default-store: associate the instance with the DEFAULT store instead of
# the target store (route the natural-key dereference to the default DB). This
# is the G-MUT mutant. Rejected on every input where the ambient default store is
# not the one the related record lives in: (K) cannot be established there
# (query_store(world.default_store, world.default_store) = world.default_store !=
# world.record_store) and (A2) fails too (world.default_store != target_store).
# Routing to the ambient default coincides with routing to the target only where
# the two stores are the same store, and the obligations are claimed for the
# whole domain at once.
_UNIQ_DEFAULT = """    # impl-start
    obj = ModelInstance(UNROUTED)
    obj.routed = world.default_store
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-partial-positive-only: a partial-domain rival that associates with the
# target store ONLY when target_store >= 0, and leaves the instance UNROUTED
# otherwise. The precondition forces target_store != UNROUTED (= -1) but does
# NOT force target_store >= 0; an admissible input target_store = -2 (a real
# store id distinct from the -1 sentinel) takes the else branch and computes the
# key on an unrouted record, failing (K) on that sub-domain.
_UNIQ_PARTIAL = """    # impl-start
    obj = ModelInstance(UNROUTED)
    if target_store >= 0:
        obj.routed = target_store
    else:
        obj.routed = UNROUTED
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-off-by-routing: route to a store derived as the ambient default's
# neighbour — a wrong store that happens to equal target_store only on a
# sub-domain. Set routed = world.default_store + 1. The precondition fixes
# world.record_store == target_store but NOT target_store == world.default_store
# + 1, so on an admissible input where they differ (e.g. target=5, default=0,
# record=5) the key computation is sent to store 1, which lacks the related
# record: (K) fails there.
_UNIQ_OFFBY = """    # impl-start
    obj = ModelInstance(UNROUTED)
    obj.routed = world.default_store + 1
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-infeasible-guard: hide the association behind a condition the
# precondition makes impossible (the related record living somewhere other than
# the store being loaded into), so that on every admissible input the key is
# computed on an unassociated record while the impl still reads as if it
# associated one. Rejected by (K) / (A2).
_UNIQ_GUARD = """    # impl-start
    obj = ModelInstance(UNROUTED)
    if world.record_store != target_store:
        obj.routed = target_store
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-assoc-only-when-not-default: associate the record with the target store
# ONLY where that target store is not the ambient default one, and leave it
# unassociated where the two coincide. Every clause of the postcondition is
# claimed for both, because world.default_store is free: on the part of the
# domain where default == record == target the fallback route does reach the
# related record — (K) holds — but the outcome then reports the association
# UNROUTED, and (A2) fails there.
_UNIQ_ONLY_NON_DEFAULT = """    # impl-start
    obj = ModelInstance(UNROUTED)
    if target_store != world.default_store:
        obj.routed = target_store
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-skip-assoc-keep-assert: a supporting near-miss — build the record and
# 'check' dereference success against the world's record_store directly (NOT the
# record's own association), then compute the key on the still-unassociated
# record. The local Assert is satisfiable (the record's own store routes to
# itself trivially) but the record itself is never associated. Rejected by (K).
_UNIQ_SKIP_ASSERT = """    # impl-start
    obj = ModelInstance(UNROUTED)
    Assert(dereference_succeeds(world.record_store, world.default_store,
                                world.record_store))
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end"""

# uniq-twin-record: associate the built record with the target store, then
# compute the natural key of a SECOND, never-associated record and return that
# outcome. The record that was associated is not the record whose key was
# computed. Rejected by (K) on the twin.
_UNIQ_TWIN = """    # impl-start
    obj = ModelInstance(UNROUTED)
    obj.routed = target_store
    twin = ModelInstance(UNROUTED)
    keyed = KeyedRecord(twin, world)
    Assert(obj.routed == target_store)
    return keyed
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_DIRECT),
        "rationale": "structurally-different CORRECT impl: build the instance ALREADY "
                     "associated with the target store (ModelInstance(target_store)) "
                     "instead of building it UNROUTED and reassigning, and return the "
                     "outcome with no local. The constructor Ensures gives "
                     "Result().routed == target_store directly; (K) holds because "
                     "query_store(target_store, world.default_store) == target_store == "
                     "world.record_store (target_store != UNROUTED), and (Q) follows from "
                     "the same equality. Same observables, different executable shape, no "
                     "loop/fold => no auto-undischargeable lemma. If this faithful "
                     "correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-via-record-store",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_VIA_RECORD),
        "rationale": "associate via the world's record_store rather than target_store. "
                     "Under the precondition world.record_store == target_store the two are "
                     "byte-equal, so this is the SAME association as the gold and is "
                     "CORRECT (the refinement.md note: an impl reading the world's "
                     "record_store coincides with reading target_store). It also confirms "
                     "that the world's routing facts are READABLE by the loader — the half "
                     "share is a read-only share, not an absent one — and that the half "
                     "share the producer hands out is enough for the impl to read the "
                     "outcome's observables (the Assert on queried_store). Must verify "
                     "(else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-release-after",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_RELEASE_AFTER),
        "rationale": "associate, compute the natural key, then DROP the record's "
                     "association again. Correct: the observables the spec pins are what "
                     "the key computation saw, and in the real function the record whose "
                     "key was computed is discarded once the key is in hand (the lookup "
                     "that follows targets the store explicitly), so a later store to "
                     "that record is dead. This control is the counterpart of "
                     "uniq-key-before-assoc: together they show the spec pins the state "
                     "AT the key computation, not the final state of the record. If it "
                     "could not verify the spec would be over-fitted to the gold "
                     "sequence => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-two-associated-keys",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_TWO_KEYS),
        "rationale": "resolve the record's identity TWICE, both times on a record "
                     "associated with the target store, and return the second outcome. "
                     "Every dereference this impl performs reaches the store the related "
                     "record lives in, so nothing it does would raise in the real system; "
                     "an implementation that computes the key more than once (a retry, a "
                     "validation pass) is a correct implementation. This is the anti-"
                     "overfit counterpart of uniq-discarded-unrouted-key: the spec must "
                     "refuse key computations whose dereference finds NOTHING, not count "
                     "how many key computations happen. If this verified only for a single "
                     "dereference the spec would be pinning the gold impl's dereference "
                     "count, an incidental detail the real function does not guarantee => "
                     "SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) first asserts, on the ACTUAL "
                     "parameters, that the routing clauses are really established for the "
                     "call (target != UNROUTED; world.record_store == target_store) — so "
                     "the world-facing precondition is not an unsatisfiable domain. It then "
                     "instantiates the regression scenario's concrete store ids (target=1 "
                     "'other', default=0, record=1) and asserts the same clauses plus that "
                     "this input is the shape where the target and ambient default stores "
                     "differ (default != record) — and that a natural key exists there at "
                     "all: the producer's condition (K) dereference_succeeds(1, 0, 1) and "
                     "query_store(1, 0) == 1. A second witness (target=default=record=1) "
                     "then shows the other shape the free ambient default admits, so the "
                     "obligations are claimed on the coinciding sub-domain too and an impl "
                     "cannot treat it as out of domain. The real impl then runs unchanged "
                     "over the actual params. If the precondition could not be established "
                     "for these legitimate inputs the Asserts fail => PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-unrouted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_UNROUTED),
        "refinement": "this IS the pre-patch behaviour (model_prepatch.py): build the "
                      "record and compute its natural key WITHOUT first setting "
                      "obj._state.db = db (the instance stays unassociated, _state.db "
                      "None). On the F2P scenario (loaddata into the non-default 'other' "
                      "DB, the related Person row present only in 'other'), the natural-"
                      "key dereference self.author.natural_key() routes the related-object "
                      "query to the DEFAULT db, which lacks the row, and raises "
                      "DoesNotExist — the exact traceback in the problem statement. It is "
                      "the un-patched code and does NOT resolve the F2P.",
        "rationale": "rejected by (K), the existence condition of the only operation that "
                     "can produce a result: for a free world.default_store, "
                     "dereference_succeeds(UNROUTED, world.default_store, "
                     "world.record_store) cannot be established, because "
                     "query_store(UNROUTED, world.default_store) = world.default_store, "
                     "which nothing pins equal to world.record_store. No key, so no "
                     "outcome; the verifier reports the producer's precondition, not a "
                     "postcondition. (On the one sub-domain where the ambient default does "
                     "equal the record's store the key exists and (A2) is what refuses this "
                     "impl, since the reported association is UNROUTED.)",
    },
    {
        "id": "uniq-key-before-assoc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ORDER),
        "refinement": "compute the natural key first and associate the record with the "
                      "target store afterwards: `natural_key = obj.natural_key()` then "
                      "`obj._state.db = db`. The record ends in exactly the gold state, "
                      "and the key was still computed while _state.db was None, so on the "
                      "F2P scenario the related-object query goes to the default DB and "
                      "raises DoesNotExist before the association is ever reached. Only "
                      "the ORDER differs from the gold patch, and it does NOT resolve.",
        "rationale": "rejected by (K) at the point of the computation: at that moment the "
                     "record's association is still UNROUTED, so "
                     "dereference_succeeds(UNROUTED, world.default_store, "
                     "world.record_store) cannot be established. The later store to "
                     "obj.routed cannot repair it, because the outcome reports the "
                     "association the computation SAW (Ensures self.routed == "
                     "record.routed at construction). This is the rival a postcondition "
                     "over the final state cannot catch.",
    },
    {
        "id": "uniq-restate-observables",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RESTATE),
        "refinement": "compute the natural key on the unassociated record and then write "
                      "the two reported observables to the values the postcondition wants. "
                      "Refined, that is a patch that computes the key before any "
                      "association and then sets obj._state.db = db: the deref has already "
                      "raised DoesNotExist, so it does NOT resolve. The written values have "
                      "no repo counterpart at all: what store the deref was sent to is an "
                      "event, not a field a later line can revise.",
        "rationale": "rejected for lack of permission — `Assignment might fail. There "
                     "might be insufficient permission to access keyed.routed.` The "
                     "producer hands out Acc(self.routed, 1/2) and "
                     "Acc(self.queried_store, 1/2), which is enough to read the "
                     "observables and never enough to assign them, so no impl can restate "
                     "what the key computation saw. This is the case that makes the half "
                     "share load-bearing rather than cosmetic. (The key computation itself "
                     "is already refused by (K); the restatement cannot rescue it either "
                     "way.)",
    },
    {
        "id": "uniq-move-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_MOVE_RECORD),
        "refinement": "leave the instance unassociated and instead declare that the "
                      "related record lives in the ambient default store — refined, a "
                      "patch that responds to the missing related row by asserting the row "
                      "is in the default database rather than by associating the instance "
                      "with the database being loaded into. Where the related row actually "
                      "is is a fact about the fixture and the databases, which no line of "
                      "build_instance can change; the deref still routes to the default DB "
                      "and still raises DoesNotExist. Does NOT resolve.",
        "rationale": "rejected for lack of permission — the deployment's routing facts are "
                     "handed to the loader as Acc(..., 1/2), a read-only share, so "
                     "`world.record_store = ...` fails on the assignment. This is the "
                     "world-frame counterpart of uniq-restate-observables and the reason "
                     "the share is a HALF rather than a full one: a loader may read the "
                     "world it runs in and may not rewrite it.",
    },
    {
        "id": "uniq-forge-world",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FORGE_WORLD),
        "refinement": "leave the instance unassociated and satisfy the natural key's "
                      "existence condition against a world of the impl's own choosing — "
                      "one in which the store an unrouted query falls back to is the store "
                      "holding the related record. Refined, that is a patch that leaves "
                      "_state.db None and argues the fallback will reach the related row "
                      "anyway: it will not, because the fallback is DEFAULT_DB_ALIAS "
                      "(django/db/utils.py:236) and the related row is in the database "
                      "being loaded into, not the default one. It raises DoesNotExist and "
                      "does NOT resolve.",
        "rationale": "rejected by (W): a Deployment is a fact about the surroundings, so "
                     "its constructor Requires(False) and no impl can produce one — "
                     "`The precondition of method __init__ might not hold. Assertion False "
                     "might not hold.` This is the case that makes the world load-bearing: "
                     "with a mintable world an impl could satisfy (K) with numbers it chose "
                     "and (K) would constrain nothing about the deployment the loader "
                     "actually runs in. Every dereference is judged against the ONE world "
                     "the loader was handed.",
    },
    {
        "id": "uniq-discarded-unrouted-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DISCARDED),
        "refinement": "compute the natural key of the freshly built, unassociated record "
                      "first, discard that result, then associate the record and compute "
                      "the key again — refined, a patch that keeps the original "
                      "`Model(**data).natural_key()` line (perhaps to log it, validate it, "
                      "or hand it to a fallback path) and ADDS the associated computation "
                      "afterwards. The first call is exactly the unpatched line: on the "
                      "F2P scenario it dereferences the FK with _state.db None, routes to "
                      "the default DB, and raises RelatedObjectDoesNotExist before the "
                      "second computation is ever reached — the try/except in "
                      "build_instance wraps only the get_by_natural_key lookup, so it does "
                      "not catch it. Every value it eventually returns is right and it "
                      "still does NOT resolve.",
        "rationale": "rejected by (K) on the DISCARDED computation: (K) is a precondition "
                     "of producing any key at all, and it is evaluated against the same "
                     "given world at every site, so a computation on an UNROUTED record "
                     "cannot be performed even if its result is thrown away. This is the "
                     "rival no postcondition over Result() can catch — the returned "
                     "outcome's three observables are byte-identical to the gold's — and "
                     "it is the reason the existence condition sits on the producer rather "
                     "than in the caller's Ensures. Note the discrimination is on whether "
                     "a dereference FINDS the related record, not on how many happen: "
                     "pos-control-two-associated-keys performs two and verifies.",
    },
    {
        "id": "uniq-default-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DEFAULT),
        "refinement": "associate the instance with the ambient DEFAULT store instead of "
                      "the target — a patch writing obj._state.db = DEFAULT_DB_ALIAS rather "
                      "than = db. The natural-key dereference would then route to the "
                      "default DB, which on a non-default loaddata target does not hold "
                      "the related record, so it raises DoesNotExist exactly as the bug. "
                      "This is the G-MUT mutant; it does NOT resolve.",
        "rationale": "rejected by (K): query_store(world.default_store, "
                     "world.default_store) = world.default_store, which nothing pins equal "
                     "to world.record_store, so on any admissible input with a differing "
                     "ambient default the key does not exist and the producer's "
                     "precondition fails. Where it is reached (the two stores coinciding) "
                     "(A2) still holds only because they coincide there, which is exactly "
                     "why the association must not be read off the ambient default.",
    },
    {
        "id": "uniq-partial-positive-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PARTIAL),
        "refinement": "a partial fix that associates the instance with the target store "
                      "only on a SUB-DOMAIN (here target_store >= 0) and leaves it "
                      "unassociated otherwise — modelling a patch that guarded "
                      "obj._state.db = db behind some predicate on the alias that does "
                      "not always hold. On an admissible input outside that sub-domain "
                      "(a real store id != the unrouted sentinel but not in the guarded "
                      "set) the key is computed on an unrouted record, the deref falls "
                      "back to the default DB and raises DoesNotExist. Correct on most "
                      "inputs, wrong on the rest; it does NOT resolve for the skipped "
                      "sub-domain.",
        "rationale": "rejected by (K) on the target_store < 0 sub-domain: the "
                     "precondition forces target_store != UNROUTED (= -1) but NOT "
                     "target_store >= 0, so target_store = -2 is admissible, takes the "
                     "else branch, and computes the key on a record whose association is "
                     "UNROUTED. Partial-domain divergence the unconditional existence "
                     "condition catches.",
    },
    {
        "id": "uniq-off-by-routing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OFFBY),
        "refinement": "route the dereference to a WRONG store computed as the ambient "
                      "default's neighbour rather than the target store — a patch that set "
                      "_state.db to a miscomputed alias. It coincides with the target only "
                      "on the sub-domain target_store == default + 1; on an admissible "
                      "input where they differ (e.g. target=record=5, default=0) the deref "
                      "is sent to store 1, which lacks the related record, and raises "
                      "DoesNotExist. It does NOT resolve.",
        "rationale": "rejected by (K): the key computation is sent to "
                     "world.default_store + 1, which no precondition clause pins equal to "
                     "world.record_store (the precond fixes world.record_store == "
                     "target_store, not target_store == world.default_store + 1). Fails on "
                     "every admissible input where those differ.",
    },
    {
        "id": "uniq-infeasible-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_GUARD),
        "refinement": "guard the association on a condition the scenario makes false "
                      "(the related record living in some store other than the one being "
                      "loaded into) — a patch that wrote obj._state.db = db only when the "
                      "FK target row is somewhere other than db, which for a fixture "
                      "carrying both rows into the same target never happens. On every "
                      "admissible input the key is computed on an unassociated record and "
                      "raises DoesNotExist. Does NOT resolve.",
        "rationale": "rejected by (K)/(A2): the guard is infeasible under the "
                     "precondition world.record_store == target_store, so obj.routed is "
                     "UNROUTED on every admissible input — the producer's precondition "
                     "cannot be established where the ambient default differs from the "
                     "record's store, and where they coincide the reported association is "
                     "UNROUTED != target_store. Guards the verifier must not be allowed "
                     "to satisfy vacuously.",
    },
    {
        "id": "uniq-assoc-only-when-not-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ONLY_NON_DEFAULT),
        "refinement": "associate the record ONLY where the store being loaded into is "
                      "not the ambient default one — a patch reading `if db != "
                      "DEFAULT_DB_ALIAS: obj._state.db = db` before computing the natural "
                      "key, and leaving _state.db None otherwise. The real function's "
                      "association is not conditional on the alias it is handed, so this "
                      "impl differs from it on every load into the ambient default store: "
                      "there the key is computed on an instance with no association at "
                      "all, and the related-object query is routed by the fallback rule "
                      "rather than by the instance. Does NOT match the real function on "
                      "that half of the domain.",
        "rationale": "rejected by (A2) on the sub-domain where the ambient default, the "
                     "record's store and the target all coincide, which the free ambient "
                     "default admits: the guard is false there, so the key is computed on "
                     "an UNROUTED record. (K) is satisfiable there (the fallback route "
                     "happens to reach the related record) and (Q) holds too "
                     "(query_store(UNROUTED, world.default_store) == world.default_store "
                     "== target_store), so this rival is caught by (A2) ALONE — it is the "
                     "case that makes 'the outcome reports the record's own association' "
                     "load-bearing independently of the existence condition, and the case "
                     "a domain that pinned the target store away from the ambient default "
                     "one could not sense at all.",
    },

    # ---- supporting mechanical near-misses (cheap; still carry a refinement) ----
    {
        "id": "uniq-skip-assoc-keep-assert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_ASSERT),
        "refinement": "build the record and 'check' dereference success against the store "
                      "the related record lives in directly, WITHOUT ever associating the "
                      "instance (no obj._state.db = db), then compute the key anyway. The "
                      "local Assert is satisfiable (that store routes to itself trivially) "
                      "but the instance itself is never routed — modelling a patch that "
                      "validated success against the wrong handle while leaving the actual "
                      "instance unassociated. The real natural-key dereference uses the "
                      "instance's own _state.db, which is still None, so it routes to the "
                      "default DB and raises DoesNotExist. It does NOT resolve.",
        "rationale": "rejected by (K): the Assert establishes something about the world's "
                     "record_store, not about the record handed to the key computation, "
                     "whose association is still UNROUTED — so "
                     "dereference_succeeds(UNROUTED, world.default_store, "
                     "world.record_store) is what has to be proved and cannot be. "
                     "Supporting near-miss for the load-bearing pin: the existence "
                     "condition is read off the record's own association, never off a "
                     "convenient nearby number.",
    },
    {
        "id": "uniq-twin-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_TWIN),
        "refinement": "associate the built record with the target store and then compute "
                      "the natural key of a DIFFERENT, never-associated record — a patch "
                      "that set obj._state.db = db on one instance and called "
                      "Model(**data).natural_key() on a second, freshly built one. The "
                      "second instance's _state.db is None, so its deref goes to the "
                      "default DB and raises DoesNotExist; the association on the first "
                      "instance is dead. Does NOT resolve.",
        "rationale": "rejected by (K) on the twin: the record whose key is computed has "
                     "association UNROUTED, and the association established on the other "
                     "record does not enter the producer's precondition. Confirms the "
                     "existence condition is read off the record actually handed to the "
                     "key computation, not off any associated record in scope.",
    },
]


# ===========================================================================
# AXIOM LANE — none. meta.json axioms=[]; NO @ContractOnly axiom is consumed.
# The store-routing mechanism is an A-reference deep model (query_store /
# dereference_succeeds) already validated == the real django.db.utils.
# ConnectionRouter routing by axiom_check.py (G-AX: all boundary store combos +
# 20000 fuzz, status pass). KeyedRecord, the producer of the modelled outcome,
# is not an axiom either: it carries a real body verified against its own
# contract, so no obligation is assumed rather than established. Deployment is
# likewise not an axiom: it is an ordinary class, and the unavailability of its
# constructor is a precondition the verifier discharges (uniq-forge-world) rather
# than an assumption it grants. There is no consumed-axiom over-approximation to
# probe for soundness/containment, and re-running axiom_check.py here would
# merely duplicate G-AX. AXIOM_TESTS is therefore empty.
# ===========================================================================
AXIOM_TESTS = []
