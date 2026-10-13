# properties.py — PBT falsification battery for django__django-13786.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY — only the
# text BETWEEN `# impl-start` and `# impl-end` is edited, so the frozen spec
# (axioms / pure / pre / post-conditions + signatures) is byte-identical and
# same_spec(base, variant) holds by construction.
#
# Defended surface (reduced_create_options): given two READ-ONLY option mappings
# self_options / operation_options (each Acc(dict_pred(.),1/2) — HALF permission,
# Required AND Ensured, carrying genuine-int name tokens), produce a FRESH
# result mapping that satisfies, for EVERY option name k (clauses (1)/(3) are
# quantified; clause (2) is stated per member of the finite managed family
# {key_managed_a()=0, key_managed_b()=1} = is_managed_option; key_other()=2 is
# a representative non-managed name):
#   (1) name provided by op  -> op's value wins;
#   (2) MANAGED name omitted by op -> ABSENT (cleared, even if self carried it)
#       — THE bug->fix delta clause;
#   (3) OTHER name omitted by op -> self's value if self had it, else absent;
#   and the no-foreign-name closure: every key in Result() is in self or op.
#
# Oracle grounding: the postcondition is GROUNDED in the arguments
# (operation_options[k], self_options[k], membership) — there is NO @Pure
# answer-key the impl could echo, so the ungrounded-oracle-echo class does not
# apply (see 'assessment'); its place is taken by an honest positive control.
# Both inputs are read-only => the frame-mutation reject case is MANDATORY.

from pathlib import Path

INSTANCE = "django__django-13786"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The entire impl body (between the markers). Editing only this guarantees
# same_spec — the spec_view elides everything from # impl-start to # impl-end.
_GOLD_IMPL = """    # Step 1: merge -- the options step's values win over the creation step's.
    options = merge_options(self_options, operation_options)
    # Step 2 (the new logic): clear every managed name the options step does not
    # provide, so the options step's mapping is the complete set of managed
    # options on the collapsed creation step.
    if key_managed_a() not in operation_options:
        options = without_key(options, key_managed_a())
    if key_managed_b() not in operation_options:
        options = without_key(options, key_managed_b())
    return options"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not present")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Build a full variant module by replacing the gold impl body with new_body
    (which must itself live entirely inside the impl region)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC_TESTS
# ---------------------------------------------------------------------------

# (5) POSITIVE CONTROL — structurally different but CORRECT. Reorder the two
# guarded clearing branches (clear key_managed_b FIRST, then key_managed_a) and
# reshape with a local. The two removals commute (distinct keys), so this is the
# same value on every input; the gold proof obligations are unchanged (each
# without_key call still framed by its own Ensures). MUST verify (else
# SPEC-TOO-STRONG).
_POS = """    # Structurally different but equivalent: clear key_managed_b before
    # key_managed_a (the two removals commute on distinct keys), via a local.
    merged = merge_options(self_options, operation_options)
    result = merged
    if key_managed_b() not in operation_options:
        result = without_key(result, key_managed_b())
    if key_managed_a() not in operation_options:
        result = without_key(result, key_managed_a())
    return result"""

# (6) ADMISSIBILITY — an F2P-shaped input: a model-creation mapping carrying the
# managed name key_managed_a and a non-managed key_other, and an empty options
# step. The precondition (two half-perm dicts carrying genuine-int name tokens)
# must admit it. MUST verify (else PRECOND-TOO-STRONG).
#
# Witnessed by discharging every Requires conjunct on the concrete input rather
# than by a self-call. reduced_create_options carries Requires(MustTerminate(10)),
# a CONSTANT level, and the call-site obligation rule demands the callee's level
# be a strictly smaller measure than the caller's. For a self-call that reads
# 10 > 10, which is false for EVERY argument choice — so a self-call here is
# unbounded recursion and is rejected as an obligation leak no matter what it is
# passed. That rejection would say nothing about the precondition, so it is not
# the admissibility question; the Asserts below are. They bite non-vacuously:
# splicing Assert(False) immediately after them FAILS to verify, so the witness
# state is genuinely reachable and the Asserts discharge real obligations instead
# of passing under an infeasible path condition. The diverging self-call the
# earlier revision of this case performed is retained as its own reject-lane
# case (diverge-unguarded-self-call) — a stronger claim than it made here.
_ADMISS = """    # Admissibility witness: a normal F2P-shaped input (self has a managed name
    # + an other name; op is empty) satisfying every Requires conjunct.
    self_in = {}  # type: Dict[int, int]
    self_in[key_managed_a()] = 100
    self_in[key_other()] = 200
    op_in = {}  # type: Dict[int, int]
    Assert(Acc(dict_pred(self_in), 1 / 2))
    Assert(Acc(dict_pred(op_in), 1 / 2))
    Assert(Forall(int, lambda k: Implies(k in self_in,
                                         not isinstance(k, bool))))
    Assert(Forall(int, lambda k: Implies(k in op_in,
                                         not isinstance(k, bool))))
""" + _GOLD_IMPL

# (7) DIVERGENCE — the unguarded self-call at the SAME termination level. The
# precondition is Requires(MustTerminate(10)); a self-call needs a level strictly
# below 10 and declares 10, so this recursion is unbounded and NEVER returns.
# Under the old specification (which demanded no termination) this variant
# VERIFIED — every Ensures held vacuously of the runs that reach the return, and
# none do. It is exactly the hole the obligation closes, so the specification
# must now reject it.
_DIVERGE = """    # WRONG: unguarded self-recursion — never returns. Every postcondition is
    # claimed only of runs that reach the return, and this reaches none, so a
    # specification without a termination obligation accepts it vacuously.
    return reduced_create_options(self_options, operation_options)"""

# (3a) FRAME-MUTATION (MANDATORY) — write to operation_options (a read-only
# HALF-permission input) to try to satisfy clause (1)/(3) vacuously by editing
# the input in place. With only Acc(dict_pred(operation_options),1/2) this write
# is illegal => INSUFFICIENT PERMISSION reject. Gold invariants kept verbatim so
# the rejection is attributable to the write.
_FRAME = """    # FRAME-MUTATION ATTACK: mutate the read-only input operation_options to
    # force every managed name to be 'provided', dodging the clear logic.
    operation_options[key_managed_a()] = 7  # illegal: only Acc(.,1/2) held
    operation_options[key_managed_b()] = 7  # illegal: only Acc(.,1/2) held
    options = merge_options(self_options, operation_options)
    if key_managed_a() not in operation_options:
        options = without_key(options, key_managed_a())
    if key_managed_b() not in operation_options:
        options = without_key(options, key_managed_b())
    return options"""

# (3) UNIQUENESS — bare merge, no clearing (EXACTLY the prepatch behaviour).
# Fails clause (2): a managed name on self but omitted by op survives. This is
# the bug->fix delta the F2P observes (verbose_name not cleared).
_BARE_MERGE = """    # WRONG (prepatch): merge only, never clear an omitted managed name.
    options = merge_options(self_options, operation_options)
    return options"""

# (3') UNIQUENESS / PARTIAL-DOMAIN — clear key_managed_a but FORGET
# key_managed_b. Correct everywhere except the sub-domain where key_managed_b is
# on self and omitted by op — which is EXACTLY F2P case 2 (verbose_name kept,
# verbose_name_plural must be cleared). Fails clause (2) for key_managed_b.
_FORGET_B = """    # WRONG: clears only key_managed_a; key_managed_b omitted by op survives.
    options = merge_options(self_options, operation_options)
    if key_managed_a() not in operation_options:
        options = without_key(options, key_managed_a())
    return options"""

# (3'') UNIQUENESS — over-clear: clear key_managed_a UNCONDITIONALLY (even when
# op provides it). Fails clause (1) for managed_a-provided (op's value must win,
# but the name is dropped). Diverges where op provides key_managed_a.
_OVERCLEAR = """    # WRONG: drops key_managed_a even when the options step provides it
    # (violates clause (1): a provided managed name must keep op's value).
    options = merge_options(self_options, operation_options)
    options = without_key(options, key_managed_a())
    if key_managed_b() not in operation_options:
        options = without_key(options, key_managed_b())
    return options"""

# (3''') UNIQUENESS — keep ONLY the options step's mapping: every
# creation-step-only name is dropped, managed or not (an "op replaces
# everything" impl). Satisfies clauses (1) and (2) and the no-foreign
# closure, but fails clause (3) EXACTLY: an OTHER name on self but omitted
# by op must be KEPT, not dropped. Diverges where self has key_other and op
# does not.
_CLEAR_OTHER = """    # WRONG: keep only the options step's names -- every creation-step-only
    # name is dropped, so a non-managed self-only name does not survive
    # (violates clause (3)).
    empty = {}  # type: Dict[int, int]
    options = merge_options(empty, operation_options)
    return options"""

# (3'''') UNIQUENESS — return an EMPTY mapping. Trivially carries no managed
# omitted name (clause (2) holds vacuously) and no foreign name, but fails clause
# (1)/(3): a provided/self-kept name is missing. A cheap supporting near-miss
# that the no-foreign closure alone would NOT catch — only the positive pins do.
_EMPTY = """    # WRONG: return a fresh empty mapping (drops every provided / kept name).
    empty = {}  # type: Dict[int, int]
    return empty"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder-clears",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS),
        "rationale": "a structurally-different but equivalent impl (the two "
                     "commuting clearing branches reordered, a local renamed) "
                     "must verify against the frozen post-conditions; each "
                     "without_key call is still framed by its own Ensures so no "
                     "proof obligation is dropped. If it cannot verify => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "the precondition (two Acc(dict_pred,1/2) inputs carrying "
                     "genuine-int name tokens) must admit a normal F2P-shaped "
                     "input — self carrying a managed name + an other name, an "
                     "empty op — established by discharging every Requires "
                     "conjunct on that concrete witness. A self-call cannot "
                     "serve as the witness: the constant Requires(MustTerminate"
                     "(10)) makes any self-call an obligation leak (the callee "
                     "level must be strictly below the caller's, and 10 > 10 is "
                     "false for every argument), which is a statement about "
                     "recursion rather than about the precondition. The Asserts "
                     "are non-vacuous — an Assert(False) spliced immediately "
                     "after them fails to verify, so the witness state is "
                     "reachable. If the Requires cannot be met => "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "diverge-unguarded-self-call",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DIVERGE),
        "refinement": "an implementation that never returns produces no reduced "
                      "operation at all: the optimizer call would recurse until "
                      "the interpreter's stack limit, so assertOptimizesTo never "
                      "reaches a comparison and the F2P does NOT resolve. A "
                      "hanging patch is a wrong patch.",
        "rationale": "DIVERGENCE: unguarded self-recursion at the same constant "
                     "termination level. Rejected by Requires(MustTerminate(10)) "
                     "— the callee's level must be strictly below the caller's, "
                     "so the recursion is unbounded ('Obligation leak check "
                     "failed. Callee reduced_create_options might not take all "
                     "unsatisfied obligations from the caller'). This case exists "
                     "because WITHOUT the termination obligation this variant "
                     "VERIFIES: every Ensures is claimed only of runs reaching "
                     "the return, and this variant reaches none, satisfying them "
                     "all vacuously. It is the precise witness that the "
                     "obligation upgrades the proof from partial to total "
                     "correctness.",
    },
    {
        "id": "frame-mutation-write-op",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME),
        "refinement": "the faithful real patch would mutate operation.options "
                      "(the AlterModelOptions's options dict) in place to make "
                      "the clear loop a no-op. operation.options is a live "
                      "object the AlterModelOptions still owns and may be "
                      "compared elsewhere; rewriting it corrupts the operation "
                      "and would NOT produce the optimizer's expected reduced "
                      "operations (assertOptimizesTo compares the original "
                      "operations' options), so the F2P would not resolve.",
        "rationale": "operation_options is held at Acc(dict_pred,1/2) "
                     "(read-only); writing it (operation_options[...] = ...) is "
                     "rejected for INSUFFICIENT PERMISSION by the permission "
                     "system, NOT by a value postcondition. Gold invariants are "
                     "kept verbatim so the rejection is attributable to the "
                     "write.",
    },
    {
        "id": "weak-bare-merge-no-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BARE_MERGE),
        "refinement": "this IS the prepatch code (`options = {**self.options, "
                      "**operation.options}` with no clearing loop). On F2P "
                      "case 1 it yields CreateModel(options={'verbose_name': "
                      "'My Model'}) instead of CreateModel() with no options, so "
                      "assertOptimizesTo fails — the patch does NOT resolve.",
        "rationale": "fails clause (2): "
                     "Implies(key_managed_a() not in operation_options, "
                     "key_managed_a() not in Result()) — a managed name on self "
                     "omitted by op survives. This is the bug->fix delta "
                     "(G-DIFF).",
    },
    {
        "id": "weak-forget-managed-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FORGET_B),
        "refinement": "clears verbose_name but not verbose_name_plural; on F2P "
                      "case 2 (self has both, op provides only verbose_name) it "
                      "leaves verbose_name_plural in the result, so the "
                      "optimizer produces CreateModel with both names instead of "
                      "just verbose_name — assertOptimizesTo fails, does NOT "
                      "resolve.",
        "rationale": "partial-domain: correct except where key_managed_b is on "
                     "self and omitted by op; fails clause (2) for "
                     "key_managed_b "
                     "(Implies(key_managed_b() not in operation_options, "
                     "key_managed_b() not in Result())).",
    },
    {
        "id": "weak-overclear-provided-managed-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OVERCLEAR),
        "refinement": "drops a managed name even when the alter step PROVIDES "
                      "it; e.g. CreateModel(options={}) + "
                      "AlterModelOptions(options={'verbose_name': 'X'}) would "
                      "reduce to CreateModel() with verbose_name missing instead "
                      "of CreateModel(options={'verbose_name': 'X'}) — the "
                      "optimizer's reduced operation loses a provided option, "
                      "does NOT match, does NOT resolve.",
        "rationale": "fails clause (1) for a provided managed name: "
                     "Implies(key_managed_a() in operation_options, "
                     "key_managed_a() in Result() and "
                     "Result()[key_managed_a()] == "
                     "operation_options[key_managed_a()]).",
    },
    {
        "id": "weak-clear-nonmanaged-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CLEAR_OTHER),
        "refinement": "drops every option the CreateModel alone carried — "
                      "including NON-managed ones (e.g. 'db_table' / 'proxy', "
                      "outside ALTER_OPTION_KEYS) — keeping only the alter "
                      "step's mapping; a CreateModel with a self-only "
                      "non-managed option would lose it on reduction, while the "
                      "gold keeps it — the reduced operation differs, does NOT "
                      "resolve. (The gold loop clears ONLY ALTER_OPTION_KEYS.)",
        "rationale": "satisfies clauses (1)/(2) and the no-foreign closure but "
                     "fails clause (3): a non-managed name on self and omitted "
                     "by op must be in Result() with self's value — a "
                     "non-managed self-only name must survive.",
    },
    {
        "id": "weak-empty-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY),
        "refinement": "returns an empty options mapping regardless of input; "
                      "every CreateModel-with-options reduction would lose all "
                      "its options, so no assertOptimizesTo expecting a "
                      "surviving option could match — does NOT resolve. (Cheap "
                      "supporting near-miss: it satisfies the no-foreign-name "
                      "closure and clause (2) vacuously, so ONLY the positive "
                      "pins (1)/(3) reject it.)",
        "rationale": "fails clause (1) and clause (3): a provided name "
                     "(key_managed_a/key_other in op) and a kept non-managed "
                     "self-only name are both absent from the empty Result().",
    },
]


# ---------------------------------------------------------------------------
# AXIOM_TESTS — the two A-consumed axioms are UNCHANGED language primitives
# ({**a,**b} and dict.pop(k,None)). Their probes need only the stdlib (the very
# constructs the gold patch calls), so they run self-contained; no repo library
# is touched. Probes EXECUTE the real primitive (never scrape source) and read
# observed values. apply_gold=True (the axioms describe the post-gold callees).
# ---------------------------------------------------------------------------

_PROBE_MERGE_SOUND = r'''
import random, sys

def real_merge(a, b):
    return {**a, **b}  # the exact construction the gold patch uses

ALTER_OPTION_KEYS = [
    "base_manager_name", "default_manager_name", "default_related_name",
    "get_latest_by", "managed", "ordering", "permissions",
    "default_permissions", "select_on_save", "verbose_name",
    "verbose_name_plural",
]

def check_merge(a, b):
    snap_a, snap_b = dict(a), dict(b)
    r = real_merge(a, b)
    # inputs unmutated + result fresh (frame: both inputs read-only in model)
    assert a == snap_a, "merge unsound: a mutated %r->%r" % (snap_a, a)
    assert b == snap_b, "merge unsound: b mutated %r->%r" % (snap_b, b)
    assert r is not a and r is not b, "merge unsound: result not fresh"
    # Ensures: b wins where b carries the name
    for k, v in snap_b.items():
        assert k in r and r[k] == v, "merge unsound: b key %r=%r lost" % (k, v)
    # Ensures: a's value carries where a has it and b does not
    for k, v in snap_a.items():
        if k not in snap_b:
            assert k in r and r[k] == v, "merge unsound: a key %r=%r lost" % (k, v)
    # Ensures: no name outside a U b
    for k in r:
        assert k in snap_a or k in snap_b, "merge unsound: spurious key %r" % (k,)

# F2P scenarios + the int-keyed carrier the MODEL actually passes (Dict[int,int],
# keys 0/1/2 = key_managed_a/b + key_other) + str-keyed real-option carrier.
fixed = [
    ({"verbose_name": "My Model"}, {}),
    ({"verbose_name": "M", "verbose_name_plural": "Mp"}, {"verbose_name": "M"}),
    ({}, {}),
    ({"verbose_name": "X"}, {"verbose_name": "Y"}),
    ({0: 7}, {}), ({0: 7}, {0: 9}), ({1: 7}, {}), ({2: 7}, {}),
    ({0: 7, 1: 8, 2: 9}, {0: 1}), ({0: 7, 1: 8, 2: 9}, {2: 1}),
]
for a, b in fixed:
    check_merge(a, b)

rng = random.Random(13786)
all_keys = ALTER_OPTION_KEYS + ["proxy", "indexes", "db_table"]
for _ in range(20000):
    a = {rng.choice(all_keys): rng.randint(0, 5) for _ in range(rng.randint(0, 6))}
    b = {rng.choice(all_keys): rng.randint(0, 5) for _ in range(rng.randint(0, 6))}
    check_merge(a, b)
# int-keyed fuzz (the model's actual carrier)
for _ in range(20000):
    a = {rng.randint(0, 4): rng.randint(0, 5) for _ in range(rng.randint(0, 5))}
    b = {rng.randint(0, 4): rng.randint(0, 5) for _ in range(rng.randint(0, 5))}
    check_merge(a, b)

print("AXIOM merge_options SOUND: real {**a,**b} meets Ensures (b-wins / "
      "a-elsewhere / union / fresh / inputs unmutated) on F2P + int- and "
      "str-carrier fixed cases + 40000 fuzz pairs")
sys.exit(0)
'''

_PROBE_WITHOUT_KEY_SOUND = r'''
import random, sys

def real_without_key(d, k):
    r = dict(d)        # functional view of the gold's in-place d.pop(k, None)
    r.pop(k, None)
    return r

ALTER_OPTION_KEYS = [
    "base_manager_name", "default_manager_name", "default_related_name",
    "get_latest_by", "managed", "ordering", "permissions",
    "default_permissions", "select_on_save", "verbose_name",
    "verbose_name_plural",
]

def check_without_key(d, k):
    snap = dict(d)
    r = real_without_key(d, k)
    assert d == snap, "without_key unsound: d mutated %r->%r" % (snap, d)
    assert r is not d, "without_key unsound: result not fresh"
    # Ensures: k is gone
    assert k not in r, "without_key unsound: removed key %r still present" % (k,)
    # Ensures: every other name carried with its value
    for j, v in snap.items():
        if j != k:
            assert j in r and r[j] == v, "without_key unsound: key %r=%r lost" % (j, v)
    # Ensures: no spurious / changed name
    for j in r:
        assert j != k and j in snap and r[j] == snap[j], \
            "without_key unsound: spurious/changed key %r" % (j,)

# The MODEL only ever calls without_key(options, key_managed_a()/b()) i.e. on a
# merge-result dict with an INT key in {0,1}. Cover that + str-option dicts and
# the absent-key (no-op) path.
fixed_dicts = [
    {}, {0: 7}, {1: 8}, {2: 9}, {0: 7, 1: 8, 2: 9},
    {"verbose_name": "X"}, {"verbose_name": "X", "proxy": True},
    {k: i for i, k in enumerate(ALTER_OPTION_KEYS)},
]
fixed_keys = [0, 1, 2, 3, "verbose_name", "proxy", "nonexistent"]
for d in fixed_dicts:
    for k in fixed_keys:
        check_without_key(d, k)

rng = random.Random(137862)
all_keys = ALTER_OPTION_KEYS + ["proxy", "indexes", "db_table"]
for _ in range(20000):
    d = {rng.choice(all_keys): rng.randint(0, 5) for _ in range(rng.randint(0, 6))}
    k = rng.choice(all_keys + ["absent_a", "absent_b"])
    check_without_key(d, k)
# int-keyed fuzz with int removal key (the model's actual carrier, keys 0/1)
for _ in range(20000):
    d = {rng.randint(0, 4): rng.randint(0, 5) for _ in range(rng.randint(0, 5))}
    check_without_key(d, rng.randint(0, 4))

print("AXIOM without_key SOUND: real dict.pop(k,None) residue meets Ensures "
      "(k absent / others carried / no spurious-or-changed / d unmutated / "
      "fresh) on int- and str-carrier fixed cases + the no-op absent-key path "
      "+ 40000 fuzz cases")
sys.exit(0)
'''

_PROBE_CONTAINMENT = r'''
import sys
# CONTAINMENT: enumerate EXACTLY the callee-inputs reduced_create_options can
# reach and assert each lies in the axiom Requires domain.
#
#   merge_options(a, b)  -- Requires Acc(dict_pred(a),1/2) & Acc(dict_pred(b),1/2):
#       any pair of dicts. The model passes (self_options, operation_options),
#       both Dict[int,int] from the model's own Requires. -> dict, dict: IN.
#   without_key(d, k)    -- Requires Acc(dict_pred(d),1/2): any dict, any int k.
#       The model passes (options, key_managed_a()=0 / key_managed_b()=1) where
#       options is the merge result (a Dict[int,int]). -> dict, int: IN.
#
# The axiom Requires impose NO value/shape narrowing beyond "is a dict" (and an
# int key for without_key) -- exactly the model's carrier type -- so there is no
# caller-reachable input OUTSIDE the covered domain (no float-vs-int gap). This
# probe records the reachable shapes and confirms containment structurally.

# reachable merge_options inputs: (self_options, operation_options)
def reachable_merge_inputs():
    # representative Dict[int,int] carriers the model can hold (keys 0/1/2)
    return [
        ({}, {}),
        ({0: 5}, {}),
        ({0: 5, 1: 6, 2: 7}, {0: 9}),
        ({2: 7}, {2: 1}),
    ]

# reachable without_key inputs: (merge_result, key in {0,1})
def reachable_without_key_inputs():
    out = []
    for a, b in reachable_merge_inputs():
        merged = {**a, **b}
        for k in (0, 1):  # key_managed_a(), key_managed_b()
            out.append((merged, k))
    return out

for a, b in reachable_merge_inputs():
    assert isinstance(a, dict) and isinstance(b, dict), \
        "merge_options reachable input not a dict: %r %r" % (a, b)

for d, k in reachable_without_key_inputs():
    assert isinstance(d, dict), "without_key reachable d not a dict: %r" % (d,)
    assert isinstance(k, int) and k in (0, 1), \
        "without_key reachable k outside model keys: %r" % (k,)

print("CONTAINMENT OK: every caller-reachable callee input lies in the axiom "
      "Requires domain -- merge_options sees (dict, dict); without_key sees "
      "(dict, int in {0,1}). The axioms constrain dicts (and an int key), "
      "exactly the model's Dict[int,int] carrier; no reachable input is outside "
      "the covered domain (no float-vs-int mis-scope).")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-merge_options",
        "axiom": "merge_options",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_MERGE_SOUND,
        "rationale": "merge_options models the unchanged primitive {**a,**b} "
                     "(PEP 448) the gold patch composes. Executing the real "
                     "merge on the F2P scenarios, the int-keyed carrier the "
                     "model actually passes, and 40000 fuzz pairs must meet the "
                     "axiom Ensures (b-wins / a-elsewhere / union / fresh / "
                     "inputs unmutated). Any violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-sound-without_key",
        "axiom": "without_key",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_WITHOUT_KEY_SOUND,
        "rationale": "without_key models the unchanged primitive dict.pop(k,None) "
                     "residue the gold patch composes. Executing the real "
                     "residue (incl. the absent-key no-op path) on int- and "
                     "str-carrier cases + 40000 fuzz cases must meet the axiom "
                     "Ensures (k absent / others carried / no spurious-or-"
                     "changed / d unmutated / fresh). Any violation => "
                     "AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-callee-domain",
        "axiom": "merge_options+without_key",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "every callee-input reduced_create_options can reach "
                     "(merge_options on (dict,dict); without_key on (dict, int "
                     "in {0,1})) lies inside the axiom Requires domain, which "
                     "constrains only 'is a dict' (+ an int key) — exactly the "
                     "model's Dict[int,int] carrier. No reachable input is "
                     "outside the covered domain, so there is no "
                     "AXIOM-TOO-WEAK-FOR-CALLER gap.",
    },
]
