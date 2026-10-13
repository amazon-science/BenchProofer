"""properties.py — PBT falsification manifest for django__django-15104.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(`swebench_nagini.pbt`) executes and stamps RESULT onto. See the battery-authoring brief
(esp. §2 "four falsification checks" and §4a "Adversarial, NOT mechanical").
Every spec variant is built by REGION-SURGERY (`_swap`) editing ONLY text inside
`reduce_to_relation_agnostic`'s `# impl-start` / `# impl-end` body, so
`markers.same_spec` against the frozen model.py is GUARANTEED and a rejection is
attributable to the POSTCONDITION / the permission system / the deep-model
precondition catching wrong behaviour, never to a tampered spec.

The function under spec
-----------------------
    reduce_to_relation_agnostic(kwargs: Dict[int, int], is_relation: bool)
        -> Dict[int, int]

models the per-field body of MigrationAutodetector.only_relation_agnostic_fields
that the gold patch changed (`del deconstruction[2]['to']`  ->
`deconstruction[2].pop('to', None)`). For a relation field (is_relation true) the
related-target keyword TO()=='to' must be DROPPED for EVERY input mapping —
INCLUDING one that does not carry it (the reported KeyError input: a custom FK
that hardcodes `to` and removes it from its own deconstruct()). For a non-relation
field the mapping is returned unchanged.

The carrier
-----------
A deconstructed kwargs `dict` (str keyword name -> arbitrary value) is modeled as
`Dict[int, int]` (keyword-name token -> opaque value token); only key membership
(`k in d`) and per-key value identity (`d[k]`) are observed, so integer-keyed/
valued identity is an exact carrier. TO()==0 is the distinguished 'to' token.

READ-ONLY input => FRAME-MUTATION is MANDATORY
----------------------------------------------
Requires(Acc(dict_pred(kwargs), 1/2)) — `kwargs` is held at HALF permission, i.e.
READ-ONLY. The function is modeled FUNCTIONALLY (returns a fresh relation-agnostic
mapping related to the input) precisely to keep the input genuinely read-only
(directive 5; closes the full-perm-read-only vacuity hole). So the frame-mutation
attack APPLIES and is MANDATORY: a rival that WRITES to `kwargs` to satisfy a
postcondition vacuously must be REJECTED for INSUFFICIENT PERMISSION (the store
needs full Acc(dict_pred(kwargs)) but only 1/2 is granted). A byte-fuzzer never
thinks to mutate the input; this is the project's #1 weakness class.

The load-bearing postcondition clauses (model.py:132-148)
---------------------------------------------------------
  (Q0) Acc(dict_pred(kwargs),1/4) + Acc(dict_pred(Result()),1/4) + Result() is
       not None         — framing / permission round-trip (returns read perm).
  (Q1) Implies(is_relation, TO() not in Result())
       — RELATION: the target keyword is GONE from the result, for EVERY input
         (incl. one that never had it). This is the clause the bug violates by
         crashing instead; the post-patch must make it TOTAL.
  (Q2) Forall j: Implies(j != TO() and j in kwargs,
                         j in Result() and Result()[j] == kwargs[j])
       — every OTHER keyword is preserved with its value (no collateral loss).
  (Q3) Forall j: Implies(j in Result(), j in kwargs and Result()[j] == kwargs[j])
       — NO spurious keyword; NO value change (the result introduces nothing).
  (Q4) Implies(not is_relation, Forall j: Implies(j in kwargs,
                         j in Result() and Result()[j] == kwargs[j]))
       — NON-RELATION: the input is returned UNCHANGED — even TO() survives.
  Q1 vs Q4 PIN the is_relation control-flow fork in BOTH directions: a relation
  field MUST lose TO(); a non-relation field MUST keep it. Q2+Q3 pin that nothing
  else moves. There is no slack: a rival that misclassifies the branch, drops a
  non-target key, keeps the target on a relation field, or invents a key fails.

TERMINATION (total correctness — closes the vacuous-divergence hole)
--------------------------------------------------------------------
The precondition carries Requires(MustTerminate(2)); both deep-model removal
primitives carry the strictly smaller Requires(MustTerminate(1)). Nagini is a
partial-correctness verifier by default, so WITHOUT the obligation a rival that
diverges before returning — bare self-recursion of the contracted routine, or
an endless loop — satisfies every Ensures VACUOUSLY and verifies (a
spec-too-weak counterexample). With it, a self-call is rejected (no strictly
smaller measure is available: "Callee ... might not take all unsatisfied
obligations") and an unbounded loop is rejected ("Loop might not take all
unsatisfied obligations"), while the bounded primitive calls (measure 1 < 2)
remain admitted — verified against both attack shapes during repair.

UNGROUNDED-ORACLE ECHO: N/A as a WRONG echo
-------------------------------------------
The postcondition is GROUNDED entirely in the input: Q1..Q4 are membership/value
predicates over `kwargs` and the bare @Pure constant TO()==0 (a distinguished
token, not an answer-key that does the work). There is NO @Pure oracle returning
the whole relation-agnostic mapping that an impl could echo without doing the
removal — building the result IS the work, and any echo disagreeing with Q1..Q4
is rejected. So there is no wrong value an echo could carry that still verifies;
the honest control is therefore the cheapest faithful impl (the positive controls
below), not a wrong echo. Stated in 'assessment'.

CONTROL-FLOW-EFFECT: the is_relation fork IS the behaviour
----------------------------------------------------------
The only behavioural effect is the branch on is_relation (drop TO() vs leave
untouched). The value abstraction does NOT drop it — Q1 governs the relation arm,
Q4 the non-relation arm. So the always-drop and never-drop rivals (and the
swapped-branch rival) are the discriminators for this fork; no separate
capability token is needed. The real raise/no-raise difference (`del` crashes,
`pop(...,None)` does not) is exercised both in the SPEC lane (the prepatch
`del_present` rival fails its precondition) and the AXIOM lane (real `del` raises).

AXIOM lane (no @ContractOnly axiom; TWO A-reference deep models)
----------------------------------------------------------------
meta.axioms == [] but deep_model_references has TWO A-references:
  * pop_default  == dict.pop(k, None)  — the POST-patch primitive (consumed by
    model.py's impl). Applicable to ANY mapping (never raises).
  * del_present  == del d[k]           — the PRE-patch primitive (consumed by
    model_prepatch.py, the G-DIFF discriminator). Applicable ONLY when k in d;
    RAISES KeyError on an absent key — which is exactly the bug.
Both model Python LANGUAGE primitives, so the probes need NO repo import and run
anywhere. The probes mirror + strengthen axiom_check.py (which the runner does
NOT mount in-container — they are SELF-CONTAINED, stdlib-only, utf-8-safe):
  - axiom-soundness (pop_default): real d.pop(k,None) meets pop_default's Ensures
    on every mapping (drops k, preserves the rest, never raises);
  - axiom-soundness (del_present): real del d[k] meets del_present's Ensures when
    k present, AND raises KeyError when k absent (justifying Requires(k in d));
  - axiom-containment: every callee-input model.py can REACH (pop_default applied
    to any reachable kwargs with k=TO()==0) lies in dict.pop's no-raise domain.
"""
from pathlib import Path

INSTANCE = "django__django-15104"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl-region body (everything strictly BETWEEN the function's
# `# impl-start` / `# impl-end`), verbatim. Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec view (axioms/pure/pre-/post-conditions
# + signature); same_spec is therefore GUARANTEED.
_IMPL = (
    "    if is_relation:\n"
    "        return pop_default(kwargs, TO())\n"
    "    return kwargs"
)
assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body: str) -> str:
    """Full model.py variant with ONLY the function impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (pos-branch-reorder) Structurally DIFFERENT but behaviourally IDENTICAL: the two
# arms of the is_relation fork are swapped in source order (handle the
# non-relation case first via an early return, then fall through to the relation
# removal). The two arms are MUTUALLY EXCLUSIVE on is_relation, so reordering is a
# pure source reshape with identical semantics; it calls the SAME deep model
# pop_default on the SAME operands, so every gold proof obligation (Q1..Q4) holds
# exactly as for gold (directive 2/3: no dropped lemma, no loop-direction flip, no
# forward-append against a fold — there is no loop here at all). If this CORRECT
# impl fails to verify => SPEC-TOO-STRONG (a faithful, structurally-different
# correct impl is rejected).
_POS_REORDER = (
    "    if not is_relation:\n"
    "        return kwargs\n"
    "    return pop_default(kwargs, TO())"
)

# (pos-local-reshape) Bind the relation-agnostic result to a typed local before
# returning it (a different data shape: name-then-return instead of return-inline).
# Same deep model, same operands, same behaviour. Must verify, else the spec is
# over-fit to the inline-return form => SPEC-TOO-STRONG. The `# type:` annotation
# attaches to an ASSIGNMENT target (out), never to a bare `return` (directive/
# pitfall 1), and carries no trailing parenthetical.
_POS_LOCAL = (
    "    if is_relation:\n"
    "        out = pop_default(kwargs, TO())  # type: Dict[int, int]\n"
    "        return out\n"
    "    return kwargs"
)

# (admiss-reads) ADMISSIBILITY. The precondition is the single half-permission
# Acc(dict_pred(kwargs),1/2). A self-call cannot round-trip the permission here
# (the postcondition only returns 1/4, leaving too little for the gold body's
# pop_default which needs 1/2), so admissibility is shown the READ-ONLY way: under
# the half-permission, assert the membership observation the operation makes
# (`TO() in kwargs`) is admitted — a trivial tautology that nonetheless REQUIRES
# read access to dict_pred(kwargs) to evaluate. No write, so no extra permission
# demand; the gold body is kept verbatim afterward. If the half-permission could
# not admit a legitimate input's membership read => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: the half-permission admits the membership observation\n"
    "    # the relation-agnostic reduction performs on a normal input mapping.\n"
    "    Assert(Implies(TO() in kwargs, TO() in kwargs))\n"
    "    if is_relation:\n"
    "        return pop_default(kwargs, TO())\n"
    "    return kwargs"
)


# ===========================================================================
# FRAME-MUTATION (MANDATORY) + UNIQUENESS RIVALS — expect "reject"
# ===========================================================================

# (rival-frame-mutate-input — MANDATORY, directive 5) Keep the gold removal/return
# verbatim, but FIRST write back onto the READ-ONLY input `kwargs`
# (kwargs[TO()] = TO()). To assign kwargs[...] Nagini needs FULL permission on
# dict_pred(kwargs), but Requires grants only Acc(dict_pred(kwargs),1/2): the write
# is REJECTED for INSUFFICIENT PERMISSION, before any postcondition is even
# considered. The store is guarded by is_relation so it is reachable on the F2P
# relation-field input; the gold body is otherwise verbatim so the rejection is
# attributable SOLELY to the write.
_RIVAL_FRAME_MUTATE = (
    "    if is_relation:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        kwargs[TO()] = TO()\n"
    "        return pop_default(kwargs, TO())\n"
    "    return kwargs"
)

# (rival-prepatch-del — the PRE-PATCH bug; PARTIAL-DOMAIN + control-flow/raise)
# EXACTLY model_prepatch.py: use the narrowly-applicable removal del_present (==
# del d['to']) in the relation arm instead of pop_default. del_present carries
# Requires(k in d), i.e. TO() in kwargs, which the relation arm CANNOT discharge
# (a relation field's kwargs may omit TO() — the reported KeyError input). It must
# be REJECTED at the call site for an UNDISCHARGED PRECONDITION. This is the spec
# sensing the exact change (G-DIFF).
_RIVAL_PREPATCH = (
    "    if is_relation:\n"
    "        return del_present(kwargs, TO())\n"
    "    return kwargs"
)

# (rival-guard-present — PARTIAL-DOMAIN, the TO()-absent sub-domain) A SUBTLER
# pre-patch sibling that DOES NOT crash: only drop TO() when it is present, else
# return kwargs unchanged. Correct on every relation field that HAPPENS to carry
# TO() (the common case), but on a relation field whose kwargs OMIT TO() it returns
# the input unchanged. That still satisfies Q1 (TO() not in Result(), vacuously)
# and Q2/Q3 — so this rival is actually CORRECT and is a partial-domain *trap* we
# must NOT mislabel. >>> It is moved to the POSITIVE-CONTROL list, NOT here. <<<
# (kept as documentation; see _POS_GUARD below.)
_POS_GUARD = (
    "    if is_relation:\n"
    "        if TO() in kwargs:\n"
    "            return del_present(kwargs, TO())\n"
    "        return kwargs\n"
    "    return kwargs"
)

# (rival-always-drop — CONTROL-FLOW-EFFECT) Drop TO() UNCONDITIONALLY, ignoring the
# is_relation guard (always call pop_default). Correct on the relation arm but on a
# NON-relation field it strips TO() too, violating Q4 (not is_relation => every key
# incl. TO() survives). The is_relation fork is collapsed.
_RIVAL_ALWAYS_DROP = (
    "    return pop_default(kwargs, TO())"
)

# (rival-never-drop — CONTROL-FLOW-EFFECT, the dual) Return kwargs unchanged in
# BOTH arms (never drop). Correct on the non-relation arm but on a relation field
# it KEEPS TO() (if present), violating Q1 (is_relation => TO() not in Result()).
# This is the "deleted the removal line" rival.
_RIVAL_NEVER_DROP = (
    "    return kwargs"
)

# (rival-drop-extra-key — Q2 collateral loss) On a relation field drop TO() AND a
# second, NON-target keyword: pop TO() then pop a fixed non-target token (1). On a
# relation field whose kwargs carry keyword 1, that keyword is LOST, violating Q2
# (j != TO() and j in kwargs => j in Result() with same value). Pins that ONLY the
# target keyword is removed. (Composes two real removals, both deeply modeled.)
_RIVAL_DROP_EXTRA = (
    "    if is_relation:\n"
    "        tmp = pop_default(kwargs, TO())\n"
    "        return pop_default(tmp, 1)\n"
    "    return kwargs"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT impl: the two MUTUALLY-EXCLUSIVE arms "
            "of the is_relation fork are swapped in source order (handle non-relation "
            "first via early return, then the relation removal). Same deep model "
            "pop_default on the same operands; every postcondition clause Q1..Q4 holds "
            "exactly as for gold. No loop/lemma to preserve (directive 2/3). If it "
            "FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LOCAL),
        "rationale": (
            "structurally-different but CORRECT impl: bind the relation-agnostic result "
            "to a typed local (out) before returning (name-then-return shape vs inline "
            "return). Same deep model, same operands, same behaviour. The `# type:` "
            "annotation attaches to the assignment target, not a bare return (pitfall "
            "1). If it FAILS => SPEC-TOO-STRONG (over-fit to the inline-return form)."
        ),
    },
    {
        "id": "pos-guard-present",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_GUARD),
        "rationale": (
            "PARTIAL-DOMAIN TRAP made a positive control: a relation field drops TO() "
            "only when present (via the narrow del_present, whose Requires(k in d) IS "
            "discharged inside the `if TO() in kwargs` guard) else returns kwargs. This "
            "is BEHAVIOURALLY CORRECT — when TO() is absent, returning kwargs already "
            "satisfies Q1 (TO() not in Result(), vacuously) and Q2/Q3/Q4 — so it MUST "
            "verify. It documents that the spec does not over-constrain the *mechanism* "
            "of removal, only the result. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (single Acc(dict_pred(kwargs),1/2) half-permission) must "
            "admit a normal F2P-shaped input: the membership observation the reduction "
            "makes (`TO() in kwargs`) is readable under the half-permission "
            "(Assert(Implies(TO() in kwargs, TO() in kwargs)) — a tautology that still "
            "requires read access to evaluate). Gold body otherwise verbatim, no write. "
            "A self-call is avoided deliberately (the postcondition returns only 1/4, "
            "not enough to re-run pop_default — that would be a permission-accounting "
            "artifact, not a precondition defect). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {
        "id": "rival-frame-mutate-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_FRAME_MUTATE),
        "refinement": (
            "WRITES back into the read-only input `kwargs` (kwargs[TO()] = TO()) before "
            "the gold removal. The half-permission Acc(dict_pred(kwargs),1/2) abstracts "
            "the gold contract that only_relation_agnostic_fields READS the deconstructed "
            "kwargs and the patch's pop('to', None) removes only 'to' — it does NOT add "
            "keys back. The deconstruction object is appended to fields_def and compared "
            "by VALUE for rename detection; a real patch that re-inserted 'to' (or any "
            "key) into deconstruction[2] would defeat the relation-agnostic comparison "
            "(two relations pointing at different targets would no longer compare equal), "
            "so rename detection would misfire — it would NOT be the gold patch and would "
            "NOT resolve the F2P/P2P. The store is a no-op only by coincidence; the point "
            "is the spec must forbid ANY write to the read-only input."
        ),
        "rationale": (
            "FRAME-MUTATION (directive 5; the #1 weakness class). Rejection source: the "
            "PERMISSION SYSTEM — assigning kwargs[TO()] needs full Acc(dict_pred(kwargs)) "
            "but Requires grants only 1/2, so the write fails for INSUFFICIENT PERMISSION "
            "before any postcondition is considered. Gold body kept verbatim so the "
            "rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame is hollow (a byte-fuzzer never mutates the input)."
        ),
    },
    {
        "id": "rival-prepatch-del",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the relation arm uses "
            "the narrowly-applicable removal del_present (== `del deconstruction[2]['to']`) "
            "instead of pop_default (== `.pop('to', None)`). Its faithful real patch is the "
            "UNCHANGED repo line `del deconstruction[2]['to']`, which RAISES KeyError on a "
            "relation field whose deconstructed kwargs omit 'to' — exactly the reported bug "
            "(a custom FK that hardcodes 'to' and removes it from its deconstruct()). It "
            "fails the F2P test_add_custom_fk_with_hardcoded_to (which builds precisely that "
            "field and expects the autodetector to NOT crash). Does NOT resolve — the precise "
            "change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "PARTIAL-DOMAIN + control-flow/raise. Rejection source: del_present's "
            "Requires(k in d) (i.e. TO() in kwargs) CANNOT be discharged at the call site "
            "in the relation arm — a relation field may omit TO(). The verifier rejects the "
            "call for an UNDISCHARGED PRECONDITION (`precondition (k in d) might not hold`). "
            "If it VERIFIES => SPEC-TOO-WEAK (the totality the patch introduces is not "
            "enforced — the spec would admit the crashing pre-patch removal)."
        ),
    },
    {
        "id": "rival-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_ALWAYS_DROP),
        "refinement": (
            "drops TO() UNCONDITIONALLY, ignoring the is_relation guard (always "
            "pop('to', None)). Its faithful real patch is a removal placed OUTSIDE the "
            "`if field.remote_field and field.remote_field.model:` guard, so it strips 'to' "
            "from NON-relation fields' deconstructed kwargs too. A non-relation field never "
            "carries a relation 'to', but a plain field could legitimately have an unrelated "
            "kwarg the autodetector must preserve; stripping a keyword the comparison relies "
            "on for non-relation fields corrupts rename detection for those fields and breaks "
            "P2P deconstruction-equality tests (e.g. the nested-deconstruction / "
            "supports_functools_partial P2P). Does NOT resolve."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT (the is_relation fork collapsed). Rejection source: Q4 "
            "(Implies(not is_relation, Forall j: j in kwargs => j in Result() with same "
            "value)): for a non-relation field carrying TO(), the rival's pop_default "
            "removes TO(), so TO() in kwargs but TO() not in Result() — Q4 violated. If it "
            "VERIFIES => SPEC-TOO-WEAK (the non-relation arm is unpinned)."
        ),
    },
    {
        "id": "rival-never-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_NEVER_DROP),
        "refinement": (
            "returns kwargs unchanged in BOTH arms — the 'deleted the removal line' rival "
            "(its faithful real patch simply OMITS the `del`/`pop` line). On a relation "
            "field carrying 'to' it keeps 'to', so two relations pointing at DIFFERENT "
            "targets no longer compare equal in the relation-agnostic reduction; "
            "generate_renamed_models then fails to detect a renamed model used in a "
            "relation. It fails the renamed-model P2P tests (e.g. the rename-of-a-model-"
            "pointed-to-by-FK tests). Does NOT resolve (this is the no-op-on-relation bug)."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT (dual; the removal removed). Rejection source: Q1 "
            "(Implies(is_relation, TO() not in Result())): for a relation field carrying "
            "TO(), the rival returns kwargs with TO() still present, so TO() in Result() "
            "while is_relation — Q1 violated. If it VERIFIES => SPEC-TOO-WEAK (the relation "
            "arm's removal is unpinned)."
        ),
    },
    {
        "id": "rival-drop-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_DROP_EXTRA),
        "refinement": (
            "on a relation field drops TO() AND a second, NON-target keyword (token 1). Its "
            "faithful real patch is a removal that pops one keyword too many — e.g. "
            "`deconstruction[2].pop('to', None); deconstruction[2].pop('related_name', None)` "
            "— stripping an attribute the relation-agnostic comparison must keep. Two "
            "relations that differ ONLY in that second keyword would then wrongly compare "
            "equal, mis-detecting a rename and producing the wrong migration; it breaks the "
            "relation-rename P2P tests. Does NOT resolve."
        ),
        "rationale": (
            "Q2 collateral-loss. Rejection source: Q2 (Forall j: j != TO() and j in kwargs "
            "=> j in Result() and Result()[j] == kwargs[j]): for a relation field carrying "
            "keyword 1, the rival's second pop removes it, so 1 in kwargs (and 1 != TO()) "
            "but 1 not in Result() — Q2 violated. Pins that ONLY the target keyword is "
            "removed. If it VERIFIES => SPEC-TOO-WEAK (collateral keyword loss admitted)."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — the TWO A-reference deep models vs the REAL Python primitives.
# meta.axioms == [] (NO @ContractOnly axiom). pop_default == dict.pop(k, None) and
# del_present == del d[k] are Python LANGUAGE primitives, so the probes need NO
# repo import and run anywhere. Each probe is SELF-CONTAINED (stdlib-only:
# copy/random/sys), utf-8-safe (no file reads), and mirrors + strengthens
# axiom_check.py. apply_gold=True (pop_default is the post-patch primitive; the
# del_present soundness check is a language fact independent of the patch, but we
# keep the image consistent).
# ===========================================================================

# (axiom-soundness, pop_default) The REAL d.pop(k, None) — applied to a COPY so the
# returned mapping is the "result" — meets pop_default's Ensures on EVERY mapping:
# k absent, every other entry preserved with its value, none introduced, and it
# NEVER raises (no precondition on k). Fuzz heavily over both arms (k present /
# absent), since totality is the whole point of the patch.
_AX_SOUND_POP = r'''
import copy
import random
import sys

TO = 0


def assert_drops_key(before, result, k, label):
    """Shared Ensures of both removal models: k absent, every other entry
    preserved with its value, none introduced."""
    assert k not in result, "%s unsound: key %r still present" % (label, k)
    for j, v in before.items():
        if j != k:
            assert j in result and result[j] == v, (
                "%s unsound: entry %r lost/changed (was %r now %r)"
                % (label, j, v, result.get(j)))
    for j in result:
        assert j != k and j in before and result[j] == before[j], (
            "%s unsound: spurious/changed entry %r" % (label, j))


def check_pop_default(d, k):
    before = copy.deepcopy(d)
    result = copy.deepcopy(d)
    raised = False
    try:
        result.pop(k, None)              # broadly-applicable: must NOT raise
    except Exception:
        raised = True
    assert not raised, "pop_default unsound: d.pop(%r, None) RAISED (must be total)" % (k,)
    assert_drops_key(before, result, k, "pop_default")


boundary = [
    {},                                 # empty -- the bug input shape
    {TO: 99},                           # only the target keyword
    {1: 10},                            # one non-target, no TO
    {1: 10, 2: 20},                     # several non-target, no TO
    {TO: 99, 1: 10, 2: 20},             # target + others
    {TO: 0},                            # target with falsy value
    {0: 0, 1: 0, 2: 0, 3: 0},           # TO + others, repeated value
    {5: 5},                             # disjoint single key
    {TO: 7, 5: 5, 9: 9, 13: 13},        # target + scattered others
]
for d in boundary:
    check_pop_default(d, TO)

rng = random.Random(151041)
for _ in range(20000):
    d = {}
    n = rng.randint(0, 8)
    for _ in range(n):
        d[rng.randint(0, 6)] = rng.randint(-3, 50)   # key space straddles TO==0
    coin = rng.random()
    if coin < 0.4:
        d[TO] = rng.randint(-3, 50)                   # force TO present
    elif coin < 0.8:
        d.pop(TO, None)                               # force TO absent
    check_pop_default(d, TO)

print("AXIOM-SOUNDNESS OK (pop_default == d.pop(k,None)): total on %d boundary + "
      "20000 fuzz mappings; drops TO==0, preserves the rest, never raises." % len(boundary))
sys.exit(0)
'''

# (axiom-soundness, del_present) The REAL del d[k] meets del_present's Ensures
# WHEN k is present (k absent after, rest preserved) AND RAISES KeyError when k is
# absent — which is precisely why del_present legitimately carries Requires(k in d)
# and pop_default does not. This is the discriminating soundness fact (G-DIFF).
_AX_SOUND_DEL = r'''
import copy
import random
import sys

TO = 0


def assert_drops_key(before, result, k, label):
    assert k not in result, "%s unsound: key %r still present" % (label, k)
    for j, v in before.items():
        if j != k:
            assert j in result and result[j] == v, (
                "%s unsound: entry %r lost/changed (was %r now %r)"
                % (label, j, v, result.get(j)))
    for j in result:
        assert j != k and j in before and result[j] == before[j], (
            "%s unsound: spurious/changed entry %r" % (label, j))


def check_del_present(d, k):
    if k in d:
        before = copy.deepcopy(d)
        result = copy.deepcopy(d)
        del result[k]                      # narrowly-applicable: here defined
        assert_drops_key(before, result, k, "del_present")
    else:
        raised = False
        result = copy.deepcopy(d)
        try:
            del result[k]
        except KeyError:
            raised = True
        assert raised, (
            "del_present precondition UNSOUND: del d[%r] did NOT raise on an absent "
            "key (model wrongly claims it applicable; Requires(k in d) unjustified)" % (k,))


boundary = [
    {},                                 # empty -- del must RAISE
    {TO: 99},                           # only TO present -- del defined
    {1: 10},                            # no TO -- del must RAISE
    {1: 10, 2: 20},                     # no TO -- del must RAISE
    {TO: 99, 1: 10, 2: 20},             # TO + others -- del defined
    {TO: 0},                            # TO falsy value -- del defined
    {0: 0, 1: 0, 2: 0, 3: 0},           # TO + others -- del defined
    {5: 5},                             # no TO -- del must RAISE
    {TO: 7, 5: 5, 9: 9, 13: 13},        # TO + scattered -- del defined
]
for d in boundary:
    check_del_present(d, TO)

rng = random.Random(151042)
present = absent = 0
for _ in range(20000):
    d = {}
    n = rng.randint(0, 8)
    for _ in range(n):
        d[rng.randint(0, 6)] = rng.randint(-3, 50)
    coin = rng.random()
    if coin < 0.4:
        d[TO] = rng.randint(-3, 50)
    elif coin < 0.8:
        d.pop(TO, None)
    if TO in d:
        present += 1
    else:
        absent += 1
    check_del_present(d, TO)

assert present > 0 and absent > 0, "fuzz did not exercise both del arms"
print("AXIOM-SOUNDNESS OK (del_present == del d[k]): defined (drops TO, rest "
      "preserved) on present mappings and RAISES KeyError on absent (justifying "
      "Requires(k in d)); %d boundary + present=%d/absent=%d fuzz."
      % (len(boundary), present, absent))
sys.exit(0)
'''

# (axiom-containment) Which callee-inputs can model.py REACH? model.py's impl calls
# ONLY pop_default(kwargs, TO()). pop_default has NO precondition on k (Requires
# only Acc(dict_pred(d),1/2)), so its domain is ALL mappings; with k=TO()==0 fixed
# and `kwargs` any finite int-keyed dict (membership/value carrier; the F2P input
# is the EMPTY/no-'to' mapping). Every reachable callee-input therefore lies in
# dict.pop(k, None)'s no-raise domain. We CONFIRM containment by executing the real
# dict.pop(0, None) across the whole reachable operand space (empty, TO-present,
# TO-absent, scattered keys, large finer values) and asserting it never raises and
# leaves TO absent. Covering MORE than the caller reaches (e.g. non-int keys) would
# be sound, not a defect; we only need containment. (del_present's narrower
# Requires(k in d) is INTENTIONAL — model.py never calls it; it is the G-DIFF
# discriminator. The caller can reach TO()-absent, which is OUTSIDE del_present's
# domain BY DESIGN — that is exactly why the prepatch fails, not an axiom defect.)
_AX_CONTAINMENT = r'''
import random
import sys

TO = 0
fails = 0


def reachable_kwargs():
    # representative reachable `kwargs` mappings: empty (the F2P input), TO-present,
    # TO-absent, scattered keys, large finer-level values; plus heavy fuzz.
    yield {}
    yield {TO: 99}
    yield {1: 10}
    yield {1: 10, 2: 20, 3: 30}
    yield {TO: 99, 1: 10, 2: 20}
    yield {TO: 0}
    yield {5: 5, 9: 9, 13: 13}
    rng = random.Random(151043)
    for _ in range(20000):
        d = {}
        for _ in range(rng.randint(0, 8)):
            d[rng.randint(0, 1000)] = rng.randint(-3, 1000)
        if rng.random() < 0.5:
            d[TO] = rng.randint(-3, 1000)
        else:
            d.pop(TO, None)
        yield d


for d in reachable_kwargs():
    work = dict(d)
    try:
        work.pop(TO, None)            # the real callee on a reachable input (k=TO)
    except Exception as exc:
        fails += 1
        print("CONTAINMENT FAIL: dict.pop(%r, None) raised on reachable kwargs %r: %s"
              % (TO, d, exc))
        continue
    if TO in work:
        fails += 1
        print("CONTAINMENT/SOUNDNESS FAIL: TO still present after pop on %r" % (d,))

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside dict.pop's "
          "no-raise domain or mismatched" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every callee-input model.py can reach "
      "(pop_default(kwargs, TO()==0) for any finite int-keyed kwargs, incl. the "
      "empty / TO-absent F2P input) lies in dict.pop(k, None)'s no-raise domain "
      "(total; never raises). del_present's narrower Requires(k in d) is the "
      "intentional G-DIFF discriminator (model.py never calls it).")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-pop_default",
        "axiom": "pop_default",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_POP,
        "rationale": (
            "pop_default is an A-reference deep model of dict.pop(k, None) (the post-patch "
            "primitive; no consumed @ContractOnly axiom). AXIOM-SOUNDNESS: the real "
            "d.pop(k, None) on a copy must meet pop_default's Ensures on EVERY mapping — k "
            "absent, every other entry preserved with its value, none introduced, and it "
            "NEVER raises (totality is the whole point of the patch). The probe runs the "
            "real primitive on 9 boundary + 20000 fuzz mappings (TO present/absent forced); "
            "mirrors axiom_check.py. Any disagreement => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-sound-del_present",
        "axiom": "del_present",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_DEL,
        "rationale": (
            "del_present is an A-reference deep model of `del d[k]` (the pre-patch primitive; "
            "the G-DIFF discriminator, consumed by model_prepatch.py). AXIOM-SOUNDNESS, BOTH "
            "halves: when k is present, real `del d[k]` drops k and preserves the rest "
            "(del_present's Ensures); when k is absent, real `del d[k]` RAISES KeyError — "
            "which is precisely why del_present carries Requires(k in d) and pop_default does "
            "not. The probe asserts both arms on 9 boundary + 20000 fuzz mappings (both arms "
            "exercised). If `del` did NOT raise on an absent key, del_present's precondition "
            "would be unjustified => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-pop_default",
        "axiom": "pop_default",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": (
            "AXIOM-CONTAINMENT: model.py's impl calls ONLY pop_default(kwargs, TO()==0). "
            "pop_default has no precondition on k (its domain is ALL mappings), so every "
            "reachable callee-input — any finite int-keyed kwargs, k=TO()==0, INCLUDING the "
            "empty / TO-absent F2P input — lies inside dict.pop(k, None)'s no-raise domain. "
            "The probe executes the real dict.pop(0, None) across the reachable operand space "
            "(empty + TO-present + TO-absent + scattered + large-value, + 20000 fuzz) and "
            "asserts it never raises and leaves TO absent. A reachable input outside the "
            "domain => AXIOM-TOO-WEAK-FOR-CALLER (none expected: dict.pop is total; "
            "del_present's narrower Requires(k in d) is the intentional discriminator, not "
            "reached by model.py)."
        ),
    },
]
