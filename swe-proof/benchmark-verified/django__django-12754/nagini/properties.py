"""properties.py — PBT falsification battery for django__django-12754.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes (host verify + same_spec for spec cases; Docker
for axiom cases). Each spec variant is built by region-surgery on the FROZEN
model.py — editing ONLY text inside the impl region (`# impl-start`/`# impl-end`,
including the nested `# invariants-start`/`# invariants-end`) so the spec
signature is provably untouched (markers.same_spec == True).

================================  DEFENDED SURFACE  ===========================

ONE modeled function:

  removed_base_field_prereqs(candidates: PSeq[int],
                             parent_after: PSet[int],
                             child: PSet[int]) -> List[int]

It computes, for one string base, the prior-parent field names that were
WITHDRAWN from the parent (`c not in parent_after`) AND RE-DECLARED by the child
(`c in child`) — the set the gold patch spells
`set(old).difference(new).intersection(model)` — and emits a "removed field"
ordering prerequisite for each (autodetector.py:566-575 post-patch).

LOAD-BEARING postcondition:
    Ensures(ToSeq(Result()) == selected(candidates, parent_after, child))
This pins the ENTIRE returned sequence (membership AND order) to `selected`, the
@Pure front-recursive fold that keeps exactly the candidates `c` for which
`qualifies(c) == (c not in parent_after) and (c in child)`. So the spec defends
BOTH guards (withdrawn-from-parent AND re-declared-by-child) on EVERY candidate.

UNGROUNDED-ORACLE (directive 2): N/A as a *wrong* echo. `selected` is a @Pure
helper, but it is a FULLY GROUNDED total function of the three inputs — it is
spelled out (front-recursive over `candidates`, gated by the grounded predicate
`qualifies`) with no opaque answer-key / hidden marker. "Echoing"
`selected(candidates, parent_after, child)` IS doing the work (and is not even an
expressible Python return value — `selected` returns a PSeq, the function returns
a List[int]). There is therefore no wrong-echo rival; we instead include honest
positive controls (a structurally-different correct impl + an admissibility
caller) as the directive-2 substitute.

READ-ONLY inputs (directive 5, MANDATORY frame-mutation): BOTH `parent_after`
and `child` are required AND ensured at HALF permission
`Acc(set_pred(parent_after), 1/2)` / `Acc(set_pred(child), 1/2)` — they are
read-only. has_readonly_input = True => the FRAME-MUTATION reject case is
MANDATORY. The frame attack available against a `set_pred`-guarded read-only
input: a rival whose loop invariant demands FULL write permission
`Acc(set_pred(X), 1)` (the permission an impl intending to MUTATE the parent's /
child's field set would need). With only the 1/2 the precondition grants, the
verifier rejects it for INSUFFICIENT PERMISSION on `set_pred(X)` — attributable
to the permission system, not the value postcondition. (The PSet carrier is
itself immutable so an in-place mutation method does not exist; the genuine,
attributable permission failure is the full-permission demand.) We include the
frame attack on BOTH read-only inputs.

VALUE-DOUBLE-MASK: the result IS a structural claim (a subsequence), and the
postcondition pins it as a whole-sequence equality `ToSeq(Result()) ==
selected(...)` — there is no value-proxy that drops disagreeing indices; the
equality compares element-by-element including order. The partial-domain rivals
below (drop a guard / skip the first candidate) are the concrete index-level
divergences this whole-sequence pin must reject.

CONTROL-FLOW-EFFECT: N/A. The function is a pure total filter returning a list;
there is no raise / return-channel / side-effect distinction invisible to the
value abstraction, so a capability-token rival has nothing to discriminate
(stated for completeness; omitted from the battery).

PARTIAL-DOMAIN (directive 3): the core uniqueness attacks. Three rivals each
correct on most of the F2P/P2P domain but diverging on a sub-domain:
  * drop-parent_after-guard: emits a candidate that is STILL owned by the parent
    (not withdrawn) but re-declared by the child — a false "removal" prerequisite.
  * drop-child-guard: emits a withdrawn candidate the child does NOT re-declare —
    a removal prerequisite for an unrelated field.
  * skip-first-candidate: an off-by-one that never considers candidates[0]; wrong
    exactly when the FIRST prior-parent field is the withdrawn-and-clashing one.

AXIOMS: none consumed. meta.axioms == []; the lone changed op (the set
difference-then-intersection) is modeled DEEPLY as `selected` (an A-reference,
deep_model_references[0]) and validated == the real CPython set algebra by
axiom_check.py (G-AX) on 13 boundary + 20000 fuzz + 5 str-name cases. There is no
@ContractOnly axiom whose Ensures the proof consumes, so the in-container axiom
LANE is vacuous for soundness (no callee Ensures to fuzz). We nevertheless add ONE
axiom-containment probe: it re-runs the G-AX equivalence (the deep model
`selected` == `set(old).difference(new).intersection(model)`) on every caller-
reachable input shape (the model's Requires admit ANY finite int candidate/parent/
child sets), confirming the A-reference deep model covers exactly what the caller
can reach. (Embedded stdlib-only; reads no bundle file in-container.)

All spec cases share the frozen spec by construction (region-surgery inside the
impl markers) — markers.same_spec == True for every one.
"""
from pathlib import Path

INSTANCE = "django__django-12754"
FLOAT_ENCODING = None  # meta.float_encoding is null; integer field-name ids, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — every one lies strictly inside the impl region (impl-start/impl-end
# or the nested invariants block), so same_spec is preserved by construction.
# ---------------------------------------------------------------------------

# (1a) frame-mutation on parent_after: bump its loop framing invariant 1/2 -> 1.
_FRAME_PA_OLD = "        Invariant(Acc(set_pred(parent_after), 1 / 2))\n"
_FRAME_PA_NEW = "        Invariant(Acc(set_pred(parent_after), 1))\n"

# (1b) frame-mutation on child: bump its loop framing invariant 1/2 -> 1.
_FRAME_CH_OLD = "        Invariant(Acc(set_pred(child), 1 / 2))\n"
_FRAME_CH_NEW = "        Invariant(Acc(set_pred(child), 1))\n"

# (2) positive control: a local-variable reshape of the SAME backward loop.
#     The guard is hoisted into a boolean local `q`; every invariant, both
#     framing asserts, and the prepend data-shape are kept VERBATIM, so the gold
#     single-unfold proof remains valid (no new lemma needed).
_GUARD_OLD = (
    "        c = candidates[i - 1]\n"
    "        Assert(candidates.drop(i - 1)[0] == c)\n"
    "        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))\n"
    "        if (not (c in parent_after)) and (c in child):\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
)
_GUARD_PC = (
    "        c = candidates[i - 1]\n"
    "        Assert(candidates.drop(i - 1)[0] == c)\n"
    "        Assert(candidates.drop(i - 1).drop(1) == candidates.drop(i))\n"
    "        # POSITIVE CONTROL: hoist the per-element guard into a boolean local\n"
    "        # (logically identical); keep every invariant/assert and the prepend.\n"
    "        withdrawn = not (c in parent_after)\n"
    "        redeclared = c in child\n"
    "        q = withdrawn and redeclared\n"
    "        if q:\n"
    "            result = [c] + result\n"
    "        i = i - 1\n"
)

# (3) admissibility caller: assert the precondition facts hold at entry for a
#     normal (F2P-shaped) input, then run the gold loop verbatim.
_ADMISS_OLD = "    result = []  # type: List[int]\n    i = len(candidates)\n"
_ADMISS_NEW = (
    "    result = []  # type: List[int]\n"
    "    # ADMISSIBILITY: the precondition admits a normal F2P-shaped input --\n"
    "    # both read-only field sets are accessible and candidates is a finite\n"
    "    # sequence (the ticket case: candidates=[id,title], parent_after={id},\n"
    "    # child={title} -> exactly one withdrawn-and-clashing name).\n"
    "    Assert(Acc(set_pred(parent_after), 1 / 2))\n"
    "    Assert(Acc(set_pred(child), 1 / 2))\n"
    "    Assert(len(candidates) >= 0)\n"
    "    i = len(candidates)\n"
)

# (4) partial-domain: drop the parent_after (withdrawn) guard -> emit a candidate
#     that is STILL owned by the parent (not withdrawn) but re-declared by child.
_DROP_PA_OLD = "        if (not (c in parent_after)) and (c in child):\n"
_DROP_PA_NEW = (
    "        # WRONG: dropped the withdrawn-from-parent guard; emits a candidate\n"
    "        # still owned by the parent (not withdrawn) when the child re-declares.\n"
    "        if c in child:\n"
)

# (5) partial-domain: drop the child (re-declared) guard -> emit every withdrawn
#     candidate, whether or not the child re-declares it.
_DROP_CH_OLD = "        if (not (c in parent_after)) and (c in child):\n"
_DROP_CH_NEW = (
    "        # WRONG: dropped the re-declared-by-child guard; emits every\n"
    "        # withdrawn candidate even when the child does not re-declare it.\n"
    "        if not (c in parent_after):\n"
)

# (6) partial-domain: off-by-one that never considers candidates[0]. Correct on
#     every input EXCEPT when the first prior-parent field qualifies.
_SKIP_FIRST_OLD = "    while i > 0:\n"
_SKIP_FIRST_NEW = (
    "    # WRONG: skip the first candidate (off-by-one); drops a qualifying\n"
    "    # candidates[0].\n"
    "    while i > 1:\n"
)


# ---------------------------------------------------------------------------
# Axiom-containment probe (the A-reference deep model `selected` covers exactly
# the caller-reachable inputs). Self-contained, stdlib-only; embeds the bundle's
# G-AX reference logic (does NOT read any bundle file in-container — the runner
# mounts only the probe at /work). apply_gold False: pure set algebra, no repo.
# ---------------------------------------------------------------------------

_CONTAINMENT_PROBE = r'''
import random, sys

# Reference of model.py `qualifies` / `selected` (kept in lock-step with the
# pure region; the deep model = A-reference).
def qualifies(name, parent_after, child):
    return (name not in parent_after) and (name in child)

def selected(candidates, parent_after, child):
    out = []
    for c in candidates:
        if qualifies(c, parent_after, child):
            out.append(c)
    return out

def real_set_expr(old, new, model):
    # the gold patch's built-in set algebra (autodetector.py:569-571)
    return set(old).difference(new).intersection(model)

# CONTAINMENT: the modeled function's Requires admit ANY finite PSeq[int]
# candidates and ANY finite PSet[int] parent_after / child (no domain bound). The
# A-reference deep model `selected` must equal the real set expression on the
# WHOLE caller-reachable domain — there is no callee-input the caller can produce
# that the deep model fails to cover. We sample that domain broadly + at the
# boundaries the F2P/P2P exercise, and assert the equivalence + that every emitted
# name is a candidate (a prior-parent name). Any divergence => the A-reference is
# mis-scoped (AXIOM-TOO-WEAK-FOR-CALLER).
def check(old, new, model):
    candidates = list(dict.fromkeys(old))  # caller passes the prior-parent key set
    emitted = selected(candidates, set(new), set(model))
    real = real_set_expr(old, new, model)
    assert set(emitted) == real, (
        "deep model `selected` != real set algebra on old=%r new=%r model=%r: "
        "real=%r emitted=%r" % (old, new, model, real, set(emitted)))
    for f in emitted:
        assert f in set(old), "emitted %r not a prior-parent (candidate) name" % (f,)
    # order faithfulness: emitted follows candidate order
    assert emitted == [c for c in candidates if qualifies(c, set(new), set(model))]

boundary = [
    ([], [], []),                                  # all empty (degenerate)
    ([1], [], [1]),                                # ticket: title withdrawn+clash
    ([0, 1], [0], [1]),                            # F2P shape: id kept, title moves
    ([1], [1], [1]),                               # kept (not withdrawn) -> none
    ([1, 2], [2], [1]),                            # one withdrawn-and-clashing
    ([1, 2, 3], [3], [1, 2]),                      # two qualify (Magazine-style)
    ([1, 2, 3], [], [1, 2, 3]),                    # all withdrawn-and-clashing
    ([1, 2, 3], [1, 2, 3], [1, 2, 3]),             # nothing withdrawn -> none
    ([1], [], [2]),                                # withdrawn but child differs
    ([1, 2], [1, 2], []),                          # child empty -> none
    ([5, 6, 7], [6], [7, 8]),                      # 7 qualifies; 5 not in child; 6 kept
    (list(range(10)), [0, 1, 2], list(range(5, 10))),
]
for old, new, model in boundary:
    check(old, new, model)

rng = random.Random(127540)
for _ in range(20000):
    universe = list(range(rng.randint(0, 16)))
    rng.shuffle(universe)
    old = [n for n in universe if rng.random() < 0.7]
    new = [n for n in old if rng.random() < 0.6]
    new += [n for n in universe if n not in old and rng.random() < 0.25]
    model = [n for n in universe if rng.random() < 0.5]
    check(old, new, model)

# str-name faithfulness (the int relabeling is observationally exact: only set
# membership/equality/hashing is performed on names).
for old, new, model in [
    (["title", "id"], ["id"], ["title"]),               # the ticket example
    (["title", "name", "id"], ["id"], ["title", "name"]),  # Magazine variant
    (["a", "b", "c"], ["a", "b", "c"], ["a", "b", "c"]),   # nothing withdrawn
    (["x"], [], ["y"]),                                    # no clash
    (["f1", "f2", "f3"], ["f2"], ["f1", "f3", "f4"]),
]:
    check(old, new, model)

print("CONTAINMENT OK: deep model `selected` == real "
      "set(old).difference(new).intersection(model) on every caller-reachable "
      "shape (12 boundary + 20000 fuzz + 5 str), 0 mismatch; emitted subset of "
      "candidates, candidate-order preserved")
sys.exit(0)
'''


SPEC_TESTS = [
    # ---- POSITIVE CONTROL (soundness): different shape, must verify ----------
    {
        "id": "pos-control-hoisted-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GUARD_OLD, _GUARD_PC),
        "rationale": "A structurally-different correct impl: the SAME backward "
                     "single-unfold loop, but the per-element guard "
                     "(not (c in parent_after)) and (c in child) is hoisted into "
                     "boolean locals `withdrawn`/`redeclared`/`q` and the branch "
                     "tests `q`. Logically identical to the gold guard. Every loop "
                     "invariant and BOTH framing asserts "
                     "(candidates.drop(i-1)[0]==c; .drop(1)==candidates.drop(i)) and "
                     "the prepend `result=[c]+result` are kept VERBATIM, so the gold "
                     "front-recursive single-unfold proof is preserved (no new lemma "
                     "needed — directives/pilot-bugs 2 and 3 avoided). If this "
                     "faithful correct impl could NOT verify => SPEC-TOO-STRONG.",
    },
    # ---- ADMISSIBILITY: precondition accepts an F2P-shaped input -------------
    {
        "id": "admiss-readonly-perms",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _ADMISS_OLD, _ADMISS_NEW),
        "rationale": "The impl asserts its own precondition facts at entry "
                     "(Acc(set_pred(parent_after),1/2), Acc(set_pred(child),1/2) are "
                     "accessible; len(candidates)>=0) before running the gold loop "
                     "verbatim. The asserts discharge from the Requires, proving the "
                     "precondition admits a normal F2P-shaped input (the ticket case "
                     "candidates=[id,title], parent_after={id}, child={title}). If "
                     "they could not => PRECOND-TOO-STRONG.",
    },
    # ---- FRAME-MUTATION (uniqueness, MANDATORY): write to read-only parent_after
    {
        "id": "frame-mut-parent_after-write-perm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FRAME_PA_OLD, _FRAME_PA_NEW),
        "refinement": "An impl that needs FULL write permission on "
                      "set_pred(parent_after) is one that intends to MUTATE the "
                      "parent's TARGET field set — i.e. rewrite the new ModelState to "
                      "make a name look withdrawn (or not) so the postcondition comes "
                      "out as desired, instead of reading it. A faithful real patch "
                      "that mutated to_state.models[parent].fields inside "
                      "generate_created_models would corrupt the shared autodetector "
                      "state every other operation reads, never producing the "
                      "[RemoveField, CreateModel] ordering the F2P "
                      "test_add_model_with_field_removed_from_base_model asserts while "
                      "leaving the parent's real field set intact; it is the opposite "
                      "of the read-only set difference the gold performs.",
        "rationale": "Rejection comes from the PERMISSION SYSTEM, not the value "
                     "postcondition: the loop invariant demands "
                     "Acc(set_pred(parent_after),1) but the precondition grants only "
                     "Acc(set_pred(parent_after),1/2) -> 'Loop invariant might not "
                     "hold ... insufficient permission to access "
                     "set_pred(parent_after)'. The gold invariants/asserts are kept "
                     "verbatim except the 1/2 -> 1, so the rejection is attributable "
                     "to the write-permission demand alone.",
    },
    # ---- FRAME-MUTATION (uniqueness): write to read-only child ---------------
    {
        "id": "frame-mut-child-write-perm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FRAME_CH_OLD, _FRAME_CH_NEW),
        "refinement": "Symmetric frame attack on the OTHER read-only input: an impl "
                      "demanding FULL write permission on set_pred(child) intends to "
                      "MUTATE the child (inheriting) model's field set — rewrite "
                      "model_state.fields to make names look re-declared (or not) "
                      "rather than reading them. A faithful real patch that mutated "
                      "model_state.fields would corrupt the very model being created "
                      "and could never emit the correct removal prerequisite while "
                      "preserving the child's declared fields; it is the opposite of "
                      "the read-only intersection the gold performs, so it cannot "
                      "resolve the F2P.",
        "rationale": "Rejection comes from the PERMISSION SYSTEM: the loop invariant "
                     "demands Acc(set_pred(child),1) but the precondition grants only "
                     "Acc(set_pred(child),1/2) -> insufficient permission on "
                     "set_pred(child). Only the 1/2 -> 1 changed; the rejection is "
                     "attributable to the write-permission demand alone.",
    },
    # ---- PARTIAL-DOMAIN (uniqueness): drop the withdrawn-from-parent guard ----
    {
        "id": "uniq-drop-parent_after-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DROP_PA_OLD, _DROP_PA_NEW),
        "refinement": "Dropping the `not (c in parent_after)` guard (keeping only "
                      "`c in child`) emits a removal prerequisite for a candidate that "
                      "is STILL owned by the parent after the change (NOT withdrawn) "
                      "whenever the child also declares that name. In the real patch "
                      "this is `set(old).intersection(model)` WITHOUT the "
                      "`.difference(new)` — it appends a spurious "
                      "(base, base, field, False) 'removed field' dependency for a "
                      "field that is not being removed at all, ordering the child's "
                      "CreateModel after a non-existent RemoveField. That fabricated "
                      "dependency cannot be satisfied (there is no such RemoveField), "
                      "so the autodetector's ordering breaks and the F2P / P2P "
                      "(test_add_model_with_field_removed_from_base_model and the "
                      "other inheritance-ordering tests) do not resolve.",
        "rationale": "Rejection comes from the postcondition ToSeq(Result()) == "
                     "selected(candidates, parent_after, child): `selected` keeps c "
                     "only when `qualifies(c) = (c not in parent_after) and (c in "
                     "child)`. On any input where a name is kept-by-parent AND "
                     "re-declared (e.g. candidates=[1], parent_after={1}, child={1}), "
                     "this rival emits 1 but `selected` emits nothing, so the "
                     "whole-sequence equality fails.",
    },
    # ---- PARTIAL-DOMAIN (uniqueness): drop the re-declared-by-child guard -----
    {
        "id": "uniq-drop-child-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _DROP_CH_OLD, _DROP_CH_NEW),
        "refinement": "Dropping the `c in child` guard (keeping only "
                      "`not (c in parent_after)`) emits a removal prerequisite for "
                      "EVERY withdrawn parent field, even ones the child does NOT "
                      "re-declare. In the real patch this is "
                      "`set(old).difference(new)` WITHOUT the "
                      "`.intersection(model_state.fields)` — it appends "
                      "(base, base, field, False) for unrelated parent fields that "
                      "were simply removed, forcing the child's CreateModel to wait on "
                      "RemoveFields it has nothing to do with. This over-orders "
                      "(and can create spurious/circular dependencies) on the broad "
                      "P2P inheritance/ordering tests where a parent loses a field the "
                      "child never declares, so the faithful patch does not resolve.",
        "rationale": "Rejection comes from the postcondition ToSeq(Result()) == "
                     "selected(...): `selected` keeps c only when BOTH guards hold. On "
                     "any input where a name is withdrawn but NOT re-declared (e.g. "
                     "candidates=[1], parent_after={}, child={}), this rival emits 1 "
                     "but `selected` emits nothing, failing the whole-sequence "
                     "equality.",
    },
    # ---- PARTIAL-DOMAIN (uniqueness): off-by-one, never consider candidates[0] -
    {
        "id": "uniq-skip-first-candidate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SKIP_FIRST_OLD, _SKIP_FIRST_NEW),
        "refinement": "Looping `while i > 1` instead of `while i > 0` never processes "
                      "candidates[0] (the first prior-parent field). It is correct on "
                      "every input where the first field does not qualify, but DROPS a "
                      "qualifying candidates[0]. In the real patch this is iterating "
                      "the prior-parent key set but silently skipping the first key — "
                      "so a base whose FIRST field is the withdrawn-and-re-declared one "
                      "(the ticket's own case: `title` could be enumerated first) gets "
                      "NO (base, base, field, False) dependency, the child's "
                      "CreateModel is NOT ordered after the RemoveField, and the exact "
                      "FieldError the patch fixes recurs — "
                      "test_add_model_with_field_removed_from_base_model still emits "
                      "[CreateModel, RemoveField] (wrong order), so it does not "
                      "resolve.",
        "rationale": "Rejection comes from the loop-invariant/postcondition "
                     "ToSeq(result) == selected(candidates.drop(i), ...): with i never "
                     "reaching 0 the final result equals selected(candidates.drop(1)), "
                     "not selected(candidates), so on any input where candidates[0] "
                     "qualifies (e.g. candidates=[1,2], parent_after={2}, child={1}) "
                     "the postcondition equality fails — the verifier cannot establish "
                     "ToSeq(result) == selected(candidates, ...).",
    },
]

# Axiom lane: no @ContractOnly axiom consumed (meta.axioms == []). The lone
# changed op (the set difference-then-intersection) is the A-reference deep model
# `selected`; its only obligation is CONTAINMENT/EQUIVALENCE with the real CPython
# set algebra over the caller-reachable domain (there is no callee Ensures to fuzz
# for unsoundness). The probe below re-establishes G-AX's equivalence on every
# caller-reachable input shape, confirming the deep model is not mis-scoped.
AXIOM_TESTS = [
    {
        "id": "ax-containment-selected",
        "axiom": "selected",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,  # pure set algebra; no repo callee needed
        "probe": _CONTAINMENT_PROBE,
        "rationale": "The A-reference deep model `selected` (the spelled-out "
                     "front-recursive filter that stands in for "
                     "set(old).difference(new).intersection(model)) must equal the "
                     "REAL CPython set algebra on every input the caller can reach. "
                     "The modeled function's Requires place NO domain bound beyond "
                     "finite int sets, so the probe samples the whole reachable domain "
                     "(boundary F2P/ticket shapes + 20000 fuzz + str-name "
                     "faithfulness) and asserts selected==real, emitted subset of "
                     "candidates, candidate-order preserved. A reachable input where "
                     "they diverge => the A-reference is mis-scoped "
                     "(AXIOM-TOO-WEAK-FOR-CALLER). 0 mismatch expected.",
    },
]
