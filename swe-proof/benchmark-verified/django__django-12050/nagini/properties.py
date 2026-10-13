# properties.py — PBT falsification battery for django__django-12050. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region (the nested # invariants region is
# part of the impl block and is also elided from the spec view, so reshaping the
# loop body / invariants keeps same_spec). The runner re-runs the Nagini verifier
# on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   resolve_iterable_value(value: Iterable) -> Iterable
#     # value is READ-ONLY (half permission):
#     Requires(Acc(value.kind, 1/2))
#     Requires(Acc(value.items, 1/2) and Acc(list_pred(value.items), 1/2))
#     Requires(value.kind == 0 or value.kind == 1)
#     # input returned at the SAME fractional permission (read-only):
#     Ensures(Acc(value.kind, 1/2))
#     Ensures(Acc(value.items, 1/2) and Acc(list_pred(value.items), 1/2))
#     # result is a fresh, fully-owned iterable:
#     Ensures(Acc(Result().kind) and Acc(Result().items) and Acc(list_pred(Result().items)))
#     # (2) THE FIX — same concrete iterable type as the input:
#     Ensures(Result().kind == value.kind)
#     # (1) same length, each item the per-item normalisation, in order:
#     Ensures(len(Result().items) == len(value.items))
#     Ensures(Forall(int, lambda k: Implies(0 <= k and k < len(value.items),
#                    Result().items[k] == normalise_item(value.items[k]))))
#   normalise_item(item: int) -> int  is  @Pure @ContractOnly with Ensures(True):
#   the UNCHANGED per-item normalisation primitive (A-consumed). It is a
#   deterministic pure function of the item ALONE; the axiom pins NO value.
#
# What the spec defends (the load-bearing facts):
#   * (2) Result().kind == value.kind — the single line carrying the FIX
#     (type(value)(...) vs the pre-patch tuple(...)). model_prepatch.py reverts to
#     out = Iterable(1) (always a tuple) and FAILS this clause when value.kind==0
#     (a list input) — exactly the F2P scenario Q(name=['a','b']) (G-DIFF).
#   * (1a) len(Result().items) == len(value.items) — every item carried through;
#     a short/long loop, a skipped first/last element, fails this.
#   * (1b) Result().items[k] == normalise_item(value.items[k]) for all 0<=k<len —
#     item k is the per-item normalisation of INPUT item k, in order. Because
#     normalise_item is an opaque @Pure fn (only Ensures(True)), the verifier can
#     prove this clause ONLY when the impl actually applies normalise_item to the
#     matching input item. It cannot prove raw value.items[k] == normalise_item(
#     value.items[k]) (identity passthrough), nor a broadcast/wrong-index value.
#   * Permission: value.kind and value.items are held at Acc(...,1/2) — READ-ONLY.
#     An impl that WRITES value (value.kind = ... / value.items.append(...) to try
#     to satisfy the postcondition by mutating the input) MUST be rejected for
#     INSUFFICIENT PERMISSION (half-perm cannot be written / list_pred mutation
#     needs full perm). This is the #1 weakness class and is MANDATORY here.
#
# Note on the @Pure oracle (ungrounded-oracle-echo class): normalise_item is
# GROUNDED in the input — the postcondition pins Result().items[k] ==
# normalise_item(value.items[k]), a function of the ACTUAL input item value.
# items[k]. There is no answer-key value to echo: any impl whose item k satisfies
# the clause must have applied the real normalise_item to the real input item k.
# So there is NO wrong echo to build (a wrong echo would change the value and
# fail the per-item clause). Instead we give honest cheapest-impl positive
# controls and attack the per-item clause via identity-passthrough / wrong-index
# rivals (which DO change the value and therefore reject). See `assessment`.
from pathlib import Path

INSTANCE = "django__django-12050"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py), INCLUDING the nested
# invariants region. We only ever replace text BETWEEN # impl-start / # impl-end,
# guaranteeing same_spec (the whole impl block — invariants included — is elided
# from the projected spec view).
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl
# MUST verify (else SPEC-TOO-STRONG). We keep EVERY gold invariant verbatim
# (pilot pitfall #2) and only reshape the EXECUTABLE body — a local-variable
# hoist of the per-item normalisation into a temp before the append. No loop
# direction flip (pitfall #3 avoided). Behaviourally identical to the gold loop.
# ===========================================================================
_POS_HOIST = """    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        nxt = normalise_item(value.items[i])  # type: int
        out.items.append(nxt)
        i = i + 1
    return out
    # impl-end"""

# pos-control-construct-after: a different LOCAL shape — bind the kind into a
# local before constructing the result (no behavioural change). out.kind ==
# value.kind still holds (Iterable(k) Ensures self.kind == k with k == value.kind).
# Keeps all gold invariants verbatim. Must verify (else SPEC-TOO-STRONG).
_POS_KINDVAR = """    # impl-start
    k0 = value.kind  # type: int
    out = Iterable(k0)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller def (a new
# module-level def changes the projected spec view => breaks same_spec). Instead
# we inject the admissibility witness INSIDE the impl region (elided), as a
# leading block that builds a concrete F2P-shaped iterable (the list value
# ['a','b'] of the F2P test Q(name=['a','b']) => Iterable(0)) and asserts it
# satisfies the function's exact Requires (Acc at 1/2 derivable from the
# constructor's full Acc Ensures; kind in {0,1}). The real impl then runs
# unchanged over the actual param. If the precondition could not be established
# for this legitimate input the Assert fails => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm = Iterable(0)  # the F2P list value Q(name=['a','b']) -> a list (kind 0)
    # the function's Requires is establishable for this concrete iterable:
    #   Acc(adm.kind, 1/2) and Acc(adm.items, 1/2) and Acc(list_pred(adm.items), 1/2)
    #   (derivable from the constructor's FULL Acc Ensures) and adm.kind in {0,1}.
    Assert(Acc(adm.kind, 1 / 2))
    Assert(Acc(adm.items, 1 / 2) and Acc(list_pred(adm.items), 1 / 2))
    Assert(adm.kind == 0 or adm.kind == 1)
    # --- end admissibility witness; the real impl follows unchanged ---
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness/reject) — MANDATORY: `value` is READ-ONLY (held at
# Acc(...,1/2)). A rival that WRITES the input to satisfy a postcondition
# vacuously MUST be rejected for INSUFFICIENT PERMISSION. We keep every gold
# invariant/clause verbatim so the rejection is attributable to the write, not a
# proof gap. Two variants: mutate value.items (needs full list_pred perm) and
# mutate value.kind (needs full field perm).
# ===========================================================================

# frame-mut-items: append into the INPUT's items list (full list_pred perm
# required; only 1/2 held). A faithful real patch that mutated the input list in
# place would corrupt the caller's value object (aliasing bug) — the gold patch
# builds a FRESH container and never touches the input. Rejected for insufficient
# permission to write value.items (the half-permission read-only input).
_FRAME_MUT_ITEMS = """    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        value.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""

# frame-mut-kind: write the READ-ONLY value.kind field (full field perm required;
# only 1/2 held). A patch mutating the input's type tag is a write to the
# caller's object the gold patch never performs. Rejected for insufficient
# permission to write value.kind.
_FRAME_MUT_KIND = """    # impl-start
    value.kind = value.kind
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain — rivals that share the spec exactly and change
# ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-always-tuple: THE BUG — out = Iterable(1) always (a tuple), exactly
# model_prepatch.py / the pre-patch `value = tuple(resolved_values)`. Verifies
# the loop body but fails Result().kind == value.kind when value.kind == 0.
_UNIQ_ALWAYS_TUPLE = """    # impl-start
    out = Iterable(1)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == 1)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""

# uniq-always-list: the OTHER direction — out = Iterable(0) always (a list).
# Fails Result().kind == value.kind when value.kind == 1 (a tuple input coerced
# to a list). Supporting partial-domain twin of always-tuple.
_UNIQ_ALWAYS_LIST = """    # impl-start
    out = Iterable(0)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == 0)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""

# uniq-flip-kind: 1 - value.kind (swap list<->tuple). Always the WRONG type.
# Fails Result().kind == value.kind for every input. The invariant pins
# out.kind == value.kind which now cannot hold (out.kind == 1 - value.kind).
_UNIQ_FLIP_KIND = """    # impl-start
    out = Iterable(1 - value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == 1 - value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""

# uniq-drop-last: process only i < len-1 (skip the LAST item). Fails
# len(Result().items) == len(value.items) for any non-empty input. Partial-domain
# attack on the length/per-item clause (the last element diverges).
_UNIQ_DROP_LAST = """    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items) - 1:
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end"""

# uniq-identity-passthrough: append the RAW item value.items[i] instead of its
# normalisation normalise_item(value.items[i]). Fails the per-item clause:
# normalise_item is an opaque @Pure fn, so the verifier cannot prove
# value.items[k] == normalise_item(value.items[k]). This is the attack that the
# normalise_item axiom (NOT identity) is load-bearing: the per-item rule resolves
# expression-bearing sub-values (F() etc.), so a passthrough returns the wrong
# resolved value for an expression item and would fail the resolution the branch
# performs. (The invariant per-item pin is changed to the raw item to make the
# loop locally consistent; the POSTCONDITION per-item clause — frozen — still
# pins normalise_item and is what rejects.)
_UNIQ_IDENTITY = """    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == value.items[k]))))
        # invariants-end
        out.items.append(value.items[i])
        i = i + 1
    return out
    # impl-end"""

# uniq-broadcast-first: append normalise_item(value.items[0]) for EVERY position
# (broadcast the first item's normalisation). Fails the per-item clause for k>=1
# (Result().items[k] would be normalise_item(value.items[0]) != normalise_item(
# value.items[k]) for a generic input). Partial-domain: correct only at k==0.
_UNIQ_BROADCAST = """    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[0])))))
        # invariants-end
        out.items.append(normalise_item(value.items[0]))
        i = i + 1
    return out
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-hoist",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_HOIST),
        "rationale": "structurally-different CORRECT impl: hoist the per-item "
                     "normalisation into a local `nxt` before appending (same "
                     "forward loop, all gold invariants kept verbatim per pilot "
                     "pitfall #2). Behaviourally identical to the gold loop; "
                     "out.items[k] == normalise_item(value.items[k]) still holds. "
                     "No loop-direction flip / no fold lemma (pitfall #3 avoided). "
                     "If a faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-kindvar",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_KINDVAR),
        "rationale": "local-variable reshape: bind value.kind into a local k0 and "
                     "construct Iterable(k0). out.kind == value.kind still holds "
                     "(constructor Ensures self.kind == k0 with k0 == value.kind). "
                     "All gold invariants kept verbatim. Must verify (else "
                     "SPEC-TOO-STRONG).",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds the "
                     "concrete F2P-shaped iterable Iterable(0) (the list value "
                     "Q(name=['a','b'])) and asserts it satisfies the function's "
                     "exact Requires: Acc(adm.kind,1/2), Acc(adm.items,1/2) and "
                     "Acc(list_pred(adm.items),1/2) (derivable from the "
                     "constructor's full Acc Ensures) and adm.kind in {0,1}. The "
                     "real impl then runs unchanged. If the precondition could not "
                     "be established for this legitimate input the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (must reject for INSUFFICIENT PERMISSION; MANDATORY) ----
    {
        "id": "frame-mut-items",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUT_ITEMS),
        "refinement": "appending into the INPUT's items list mutates the caller's "
                      "value object in place. The gold patch builds a FRESH "
                      "container (type(value)(generator)) and never writes the "
                      "input iterable; a real patch that mutated the input list "
                      "would corrupt the caller's data (an aliasing bug) and would "
                      "not be the gold behaviour the F2P/P2P tests observe (e.g. "
                      "the rhs value compared by test_iterable_lookup_value).",
        "rationale": "rejected by the permission system: value.items / "
                     "list_pred(value.items) are held at Acc(...,1/2) (read-only); "
                     "value.items.append(...) requires FULL list_pred permission, "
                     "which the function does not hold => insufficient permission.",
    },
    {
        "id": "frame-mut-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUT_KIND),
        "refinement": "writing value.kind mutates the input iterable's type tag — "
                      "a write to the caller's object the gold patch never "
                      "performs (it only constructs a fresh result of the input's "
                      "type). A real patch that reassigned the input's type would "
                      "not match the gold behaviour.",
        "rationale": "rejected by the permission system: value.kind is held at "
                     "Acc(value.kind, 1/2) (read-only); the assignment value.kind "
                     "= ... requires FULL field permission, which is not held => "
                     "insufficient permission.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-always-tuple",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_TUPLE),
        "refinement": "out = Iterable(1) always (a tuple) is EXACTLY the pre-patch "
                      "behaviour model_prepatch.py reproduces and G-DIFF flags: the "
                      "branch did `value = tuple(resolved_values)`, coercing a list "
                      "input to a tuple. The sole F2P test_iterable_lookup_value "
                      "builds Q(name=['a','b']) and asserts the resolved rhs is "
                      "\"['a', 'b']\" (a list repr); with a tuple result the rhs is "
                      "('a', 'b') and the assertEqual fails — the un-patched branch "
                      "is exactly what does NOT resolve.",
        "rationale": "rejected by Ensures(Result().kind == value.kind): out.kind "
                     "is pinned to 1, but value.kind may be 0 (a list input), so "
                     "the verifier cannot prove out.kind == value.kind. (Clause 2, "
                     "the fix.)",
    },
    {
        "id": "uniq-always-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_LIST),
        "refinement": "out = Iterable(0) always (a list) is the mirror coercion: a "
                      "tuple input is turned into a list. The problem statement "
                      "demands the return type MATCH the input iterable type for "
                      "BOTH directions (PickledField-style exact-value queries "
                      "break either way); a patch always returning a list would "
                      "fail a tuple-input case the same way the gold patch fixes "
                      "the list-input case. The P2P/real semantics (axiom_check "
                      "(B): a tuple stays a tuple) would not resolve.",
        "rationale": "rejected by Ensures(Result().kind == value.kind): out.kind "
                     "is pinned to 0, but value.kind may be 1 (a tuple input), so "
                     "out.kind == value.kind cannot be proven.",
    },
    {
        "id": "uniq-flip-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FLIP_KIND),
        "refinement": "Iterable(1 - value.kind) inverts the type for every input "
                      "(list->tuple AND tuple->list). No real patch behaves this "
                      "way; it fails both the list-input F2P case and any tuple "
                      "case. Supporting twin of the coercion attacks.",
        "rationale": "rejected by Ensures(Result().kind == value.kind): out.kind "
                     "== 1 - value.kind != value.kind for kind in {0,1}, so "
                     "out.kind == value.kind is unprovable.",
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_LAST),
        "refinement": "looping i < len-1 drops the LAST item. A patch that built "
                      "the result short by one element would return a "
                      "shorter iterable than the input — the F2P "
                      "test_iterable_lookup_value's ['a','b'] would resolve to a "
                      "one-element ['a'] (repr \"['a']\" != \"['a', 'b']\"), and "
                      "any multi-item lookup would silently lose a value. Does not "
                      "resolve.",
        "rationale": "rejected by Ensures(len(Result().items) == len(value.items)): "
                     "the loop stops one short, so len(out.items) == len(value."
                     "items) - 1 for any non-empty input; the length clause "
                     "(clause 1a) cannot be proven.",
    },
    {
        "id": "uniq-identity-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_IDENTITY),
        "refinement": "appending the RAW item instead of normalise_item(item) "
                      "skips the per-item resolution the branch performs. The real "
                      "per-item rule resolves expression-bearing sub-values (an F() "
                      "or other resolve_expression-bearing item) — a passthrough "
                      "would leave an unresolved expression object in the rhs, "
                      "breaking lookups whose items are expressions (the branch "
                      "comment: 'items ... may be expressions and therefore need to "
                      "be resolved independently'). A patch dropping the recursive "
                      "resolve_lookup_value call does not resolve.",
        "rationale": "rejected by Ensures(Forall k: Result().items[k] == "
                     "normalise_item(value.items[k])): normalise_item is an opaque "
                     "@Pure fn (Ensures(True)); the verifier cannot prove the raw "
                     "value.items[k] equals normalise_item(value.items[k]) "
                     "(clause 1b).",
    },
    {
        "id": "uniq-broadcast-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_BROADCAST),
        "refinement": "broadcasting normalise_item(value.items[0]) into every "
                      "position returns the first item's resolution for all "
                      "positions. A patch resolving only the first sub-value and "
                      "repeating it would produce a wrong rhs for any multi-item "
                      "lookup (e.g. ['a','b'] -> ['a','a']), failing the F2P/P2P "
                      "value comparisons. Correct only at k==0 (partial-domain).",
        "rationale": "rejected by Ensures(Forall k: Result().items[k] == "
                     "normalise_item(value.items[k])): for k>=1 the result item is "
                     "normalise_item(value.items[0]), which the verifier cannot "
                     "prove equals normalise_item(value.items[k]) (two distinct "
                     "opaque-@Pure applications; clause 1b).",
    },
]


# ===========================================================================
# AXIOM LANE — one A-consumed axiom: normalise_item(item: int) -> int with the
# sole Ensures(True), modelling the UNCHANGED per-item normalisation the branch
# performs (per-item self.resolve_lookup_value(sub, ...)). Probes run in the
# instance Docker image (the real Django lives there). We re-derive the bundle's
# own axiom_check.py soundness logic (the runner mounts ONLY the probe at /work,
# so we cannot import axiom_check.py in-container — but its logic imports only
# Django, which IS present). apply_gold=True: the callee per-item rule is
# UNCHANGED by the patch, so gold-applied is the correct end-to-end runtime.
# ===========================================================================

# axiom-soundness: the load-bearing soundness fact the refinement rests on is
# CONTAINER-INDEPENDENCE — normalising one item yields the SAME result whether the
# item sits in a list or a tuple, so the only behavioural difference between the
# two container kinds is the container TYPE itself (clause 2, the fix). We drive
# the REAL django.db.models.sql.query.Query.resolve_lookup_value end-to-end: a
# list of items and the SAME items as a tuple must produce element-wise EQUAL
# per-item results (only the container type differs), a scalar passes through,
# and a list stays a list / a tuple stays a tuple. Any per-item disagreement
# between the list and tuple container, or a type that does not match the input,
# => AXIOM-UNSOUND. Fuzzed over many mixed (plain + expression-bearing) sequences
# plus boundary sizes.
_AX_SOUNDNESS_PROBE = r'''
import random, sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.contrib.auth.models import User
    from django.db.models.sql.query import Query
    from django.db.models import F

    query = Query(User)

    def resolve(value):
        return query.resolve_lookup_value(value, can_reuse=set(),
                                          allow_joins=True, simple_col=False)

    # Pool of per-item identities: plain scalars (passthrough) + expression-
    # bearing items (F(...) resolves to a non-identity). The per-item rule must
    # be the SAME whether the item is inside a list or a tuple.
    def make_items(rng):
        pool = [0, 1, -3, 42, "a", "b", "alpha", "", "['a', 'b']", 3.5, True,
                None, F("pk"), F("id")]
        n = rng.randint(0, 8)
        return [rng.choice(pool) for _ in range(n)]

    rng = random.Random(120500)
    boundary = [
        [], [0], ["a"], ["a", "b"], [F("pk")], ["a", F("id"), 3],
        [None, True, "", 0],
    ]
    n_checked = 0

    def check(items):
        nonlocal n_checked
        as_list = resolve(list(items))
        as_tuple = resolve(tuple(items))
        # container TYPE preserved (the fix) ...
        assert isinstance(as_list, list), (
            "AXIOM/FIX: a list value must stay a list, got %r" % type(as_list))
        assert isinstance(as_tuple, tuple), (
            "AXIOM/FIX: a tuple value must stay a tuple, got %r" % type(as_tuple))
        # ... same length ...
        assert len(as_list) == len(items) == len(as_tuple), (
            "length mismatch: %r vs %r vs %d" % (len(as_list), len(as_tuple),
                                                 len(items)))
        # ... and CONTAINER-INDEPENDENCE: per-item result identical between the
        # list and tuple containers (the normalise_item axiom's soundness fact).
        for i in range(len(items)):
            li = as_list[i]
            ti = as_tuple[i]
            same = (li == ti) or (repr(li) == repr(ti))
            assert same, (
                "AXIOM-UNSOUND: per-item normalisation depends on container kind "
                "at item %d: list gave %r, tuple gave %r" % (i, li, ti))
        n_checked += 1

    for items in boundary:
        check(items)
    for _ in range(4000):
        check(make_items(rng))

    # a scalar passes through unchanged (the recursive per-item rule's identity
    # case used by normalise_item for plain sub-values).
    assert resolve(7) == 7
    assert resolve("x") == "x"

    print("AXIOM-SOUNDNESS OK: the real Query.resolve_lookup_value per-item rule "
          "is container-independent (list vs tuple produce element-wise equal "
          "items) over %d sequences (plain + F() expression items); a list stays "
          "a list, a tuple stays a tuple, a scalar passes through. normalise_item "
          "(Ensures(True), container-independent) is sound." % (n_checked,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-containment: the model can only ever pass `value.items[i]` (for
# 0 <= i < len(value.items)) to normalise_item. value.items is List[int], so
# every reachable item is an int — exactly the axiom's Requires domain
# (item: int, no further constraint). So EVERY caller-reachable item lies inside
# the axiom domain; containment holds trivially. We confirm operationally that
# the real per-item callee accepts the kinds of sub-values the branch reaches
# (the opaque item identities the model abstracts as int) and resolves each
# independently regardless of position — i.e. the caller never reaches an item
# the per-item rule cannot handle. (Covering MORE — any item type, including
# expression-bearing items — is SOUND, not a defect; the model abstracts items as
# opaque int identities, a subset.)
_AX_CONTAINMENT_PROBE = r'''
import random, sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-CONTAINMENT FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.contrib.auth.models import User
    from django.db.models.sql.query import Query
    from django.db.models import F

    query = Query(User)

    def resolve(value):
        return query.resolve_lookup_value(value, can_reuse=set(),
                                          allow_joins=True, simple_col=False)

    # The model passes `value.items[i]` (an int item identity) for every index
    # i in 0..len-1 to normalise_item. The axiom's Requires domain is `item: int`
    # (no further constraint). Enumerate the per-item inputs the model reaches
    # (every position of representative iterables) and confirm the real per-item
    # callee accepts each and resolves it independently of position — so no
    # reachable item is outside the per-item rule's domain.
    rng = random.Random(120501)
    pool = [0, 1, -3, 42, "a", "b", "", "['a', 'b']", 3.5, True, None,
            F("pk"), F("id")]
    reached = 0
    for _ in range(2000):
        n = rng.randint(0, 8)
        items = [rng.choice(pool) for _ in range(n)]
        out_list = resolve(list(items))
        out_tuple = resolve(tuple(items))
        # every position the model can index is reached and resolved.
        assert len(out_list) == len(items), (
            "AXIOM-TOO-WEAK-FOR-CALLER: a reachable position was not resolved")
        for i in range(len(items)):
            # the per-item rule resolves each index independently; resolving the
            # item standalone matches its in-container resolution (position- and
            # container-independent), i.e. the reachable item is in the domain.
            standalone = resolve(items[i])
            li = out_list[i]
            same = (li == standalone) or (repr(li) == repr(standalone))
            assert same, (
                "AXIOM-TOO-WEAK-FOR-CALLER: item %d (%r) in-container resolution "
                "%r differs from standalone %r — a reachable input the per-item "
                "rule does not handle uniformly" % (i, items[i], li, standalone))
            reached += 1

    print("AXIOM-CONTAINMENT OK: every per-item input the model can reach "
          "(value.items[i], an item identity at any position; %d sampled) lies "
          "inside normalise_item's domain and is resolved by the real per-item "
          "rule independently of position and container. The caller reaches a "
          "subset of the axiom domain; no reachable input is outside it." % (reached,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-normalise_item",
        "axiom": "normalise_item",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # per-item rule is UNCHANGED; gold-applied is the runtime
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "if the real per-item resolution differed between a list and "
                     "a tuple container (container-dependence), the normalise_item "
                     "axiom's load-bearing soundness fact would fail => "
                     "AXIOM-UNSOUND, because then the only difference between the "
                     "kinds would NOT be the container type alone. Driven on the "
                     "REAL Query.resolve_lookup_value over plain + F() expression "
                     "items: per-item results are element-wise equal between list "
                     "and tuple; list stays list, tuple stays tuple, scalar passes "
                     "through.",
    },
    {
        "id": "ax-cover-normalise_item",
        "axiom": "normalise_item",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every input the model can pass to normalise_item is "
                     "value.items[i] (an int item identity at a position in "
                     "0..len-1); the axiom's Requires domain is `item: int` (no "
                     "further constraint), so each reachable item is inside it. A "
                     "reachable item outside the domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; the real per-item rule resolves "
                     "every reachable position independently and uniformly, so "
                     "none exists.",
    },
]
