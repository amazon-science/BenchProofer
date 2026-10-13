# properties.py — PBT falsification battery for django__django-15161.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py variant built by region-surgery: we edit
# ONLY text inside the # impl-start / # impl-end markers, so the frozen spec
# (axioms/pure/pre/post-conditions + signatures) is byte-identical and
# `markers.same_spec(base, module)` holds for every case. The runner checks each
# variant with the real Nagini verifier on the host.
#
# DEFENDED SURFACE (reasoned, not mechanical):
#   deconstruct_path(configured, exact, module, name) -> List[int] models the
#   import path a @deconstructible expression node reports. Read-only inputs
#   (Acc(.,1/2)): configured, module, name. The load-bearing postcondition is a
#   value pin:
#     - configured non-empty AND exact  =>  Result == configured  (verbatim)
#     - otherwise                        =>  Result == module + "." + name
#   plus a rooting-equivalence clause that is fully DERIVED from those two value
#   pins (serialized_module_rooted(Result) tracks the chosen branch's source).
#   The oracle is GROUNDED in the inputs (Result is pinned equal to a function
#   of the args), so there is no opaque answer-key to echo — see assessment;
#   instead we ship an honest structural positive control.
#
# Attacks: frame-mutation on read-only `name` (MANDATORY, #1 weakness class),
# branch-misselection (prepatch echo), two partial-domain value divergences
# (off-by-one truncation of the configured path; dropped dot in the fallback),
# a structural positive control (branch reorder), and an admissibility caller.
from pathlib import Path

INSTANCE = "django__django-15161"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(src):
    """The impl region of a same-spec module, start marker included.

    Swapping one module's impl region into another's is how a whole-body rival is
    built without touching a single byte of the frozen spec, so `same_spec` holds
    by construction.
    """
    a = src.index("    # impl-start\n")
    b = src.index("    # impl-end\n")
    if a >= b:
        raise AssertionError("impl markers out of order")
    return src[a:b]


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (reject) — MANDATORY: `name` is a read-only input
#    (Requires(Acc(list_pred(name), 1/2))). A rival that WRITES to `name` to
#    build its answer must fail for INSUFFICIENT PERMISSION. We keep every gold
#    invariant/assert verbatim and only insert one mutating call, so the
#    rejection is attributable purely to the write, not to a broken proof.
_FRAME = _swap(
    _BASE,
    "        result = result + [DOT()]\n",
    "        result = result + [DOT()]\n"
    "        name.append(DOT())  # WRITE to a 1/2-permission read-only input\n",
)

# ---------------------------------------------------------------------------
# 2. POSITIVE CONTROL (verify) — structurally DIFFERENT but CORRECT: the two
#    top-level branches are reordered (test `not (...)` first). Each loop keeps
#    its identical take-prefix invariants and framing asserts, so the gold proof
#    stays valid; only the executable branch order changes. Must verify (else
#    SPEC-TOO-STRONG).
_POS_IMPL_OLD = """    result = []  # type: List[int]
    if len(configured) > 0 and exact:
        i = 0
        while i < len(configured):
            # invariants-start
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(configured) > 0 and exact)
            Invariant(0 <= i and i <= len(configured))
            Invariant(ToSeq(result) == ToSeq(configured).take(i))
            Invariant(MustTerminate(len(configured) - i + 1))
            # invariants-end
            result = result + [configured[i]]
            i = i + 1
        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
        Assert(ToSeq(result) == ToSeq(configured))
        return result
    else:
        i = 0
        while i < len(module):
            # invariants-start
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= i and i <= len(module))
            Invariant(ToSeq(result) == ToSeq(module).take(i))
            Invariant(MustTerminate(len(module) - i + 1))
            # invariants-end
            result = result + [module[i]]
            i = i + 1
        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
        result = result + [DOT()]
        j = 0
        while j < len(name):
            # invariants-start
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= j and j <= len(name))
            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
            Invariant(MustTerminate(len(name) - j + 1))
            # invariants-end
            result = result + [name[j]]
            j = j + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(ToSeq(result) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        Assert(qualified(ToSeq(module), ToSeq(name)) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        return result"""

_POS_IMPL_NEW = """    result = []  # type: List[int]
    if not (len(configured) > 0 and exact):
        i = 0
        while i < len(module):
            # invariants-start
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= i and i <= len(module))
            Invariant(ToSeq(result) == ToSeq(module).take(i))
            Invariant(MustTerminate(len(module) - i + 1))
            # invariants-end
            result = result + [module[i]]
            i = i + 1
        Assert(ToSeq(module).take(len(module)) == ToSeq(module))
        result = result + [DOT()]
        j = 0
        while j < len(name):
            # invariants-start
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(module), 1 / 2))
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(not (len(configured) > 0 and exact))
            Invariant(0 <= j and j <= len(name))
            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
            Invariant(MustTerminate(len(name) - j + 1))
            # invariants-end
            result = result + [name[j]]
            j = j + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
        Assert(ToSeq(result) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        Assert(qualified(ToSeq(module), ToSeq(name)) ==
               ToSeq(module) + PSeq(DOT()) + ToSeq(name))
        return result
    else:
        i = 0
        while i < len(configured):
            # invariants-start
            Invariant(Acc(list_pred(configured), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(len(configured) > 0 and exact)
            Invariant(0 <= i and i <= len(configured))
            Invariant(ToSeq(result) == ToSeq(configured).take(i))
            Invariant(MustTerminate(len(configured) - i + 1))
            # invariants-end
            result = result + [configured[i]]
            i = i + 1
        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))
        Assert(ToSeq(result) == ToSeq(configured))
        return result"""

_POS = _swap(_BASE, _POS_IMPL_OLD, _POS_IMPL_NEW)

# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN (reject) — off-by-one truncation of the configured path.
#    Correct on the empty/fallback domain, but on the F2P configured-branch
#    inputs it drops the LAST code point, returning `django.db.models.Valu`
#    instead of `django.db.models.Value`. Rejected by the value pin
#    `Implies(len(configured)>0 and exact, ToSeq(Result()) == ToSeq(configured))`.
_PARTIAL_TRUNC = _swap(
    _BASE,
    "        while i < len(configured):\n",
    "        while i < len(configured) - 1:\n",
)
# the take-prefix invariant `ToSeq(result) == ToSeq(configured).take(i)` still
# holds with this shorter loop, and the in-region framing asserts below are now
# the only place the proof would have to bridge to the full length — the
# postcondition equality (Result == configured) is what fails, exactly the
# weakness we want to expose. We DROP the now-false in-region asserts so the
# failure surfaces at the postcondition (the spec), not at a stale local assert.
_PARTIAL_TRUNC = _swap(
    _PARTIAL_TRUNC,
    "        Assert(ToSeq(configured).take(len(configured)) == ToSeq(configured))\n"
    "        Assert(ToSeq(result) == ToSeq(configured))\n",
    "",
)

# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN (reject) — dropped-dot fallback. The configured branch is
#    correct; in the else (fallback) branch it concatenates module+name WITHOUT
#    the '.' separator, returning `django.db.models.expressionsValue` instead of
#    `django.db.models.expressions.Value`. Rejected by
#    `Implies(not(...), ToSeq(Result()) == qualified(module, name))`, since
#    qualified pins the dot in.
_DROP_DOT = _swap(
    _BASE,
    "        result = result + [DOT()]\n",
    "",  # delete the separator-append entirely
)
# the name-loop invariant and the closing fallback asserts reference
# `ToSeq(module) + PSeq(DOT()) + ...`, which are now false; drop them so the
# rejection surfaces at the postcondition rather than a stale local assert.
_DROP_DOT = _swap(
    _DROP_DOT,
    "            Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))\n",
    "            Invariant(ToSeq(result) == ToSeq(module) + ToSeq(name).take(j))\n",
)
_DROP_DOT = _swap(
    _DROP_DOT,
    "        Assert(ToSeq(name).take(len(name)) == ToSeq(name))\n"
    "        Assert(ToSeq(result) ==\n"
    "               ToSeq(module) + PSeq(DOT()) + ToSeq(name))\n"
    "        Assert(qualified(ToSeq(module), ToSeq(name)) ==\n"
    "               ToSeq(module) + PSeq(DOT()) + ToSeq(name))\n",
    "        Assert(ToSeq(name).take(len(name)) == ToSeq(name))\n",
)

# ---------------------------------------------------------------------------
# 5. BRANCH-MISSELECTION / prepatch echo (reject) — always take the fallback
#    branch, ignoring the configured path. This is literally the pre-patch
#    behaviour (model_prepatch.py): a node with a configured public path still
#    reports `module.name` (the internal-submodule fallback). Rejected by the
#    value pin `Implies(len(configured)>0 and exact, ToSeq(Result())==ToSeq(configured))`
#    — when the configured branch is required, this returns qualified(module,name)
#    instead. This is the exact G-DIFF discriminator.
# The rival is model_prepatch.py's own impl region, not a disabled guard. Two
# reasons, both measured. (1) The else arm carries
# `Invariant(not (len(configured) > 0 and exact))`, which is established by the
# NEGATION of the gold guard, so any rewrite of that guard leaves the invariant
# unprovable and the rejection lands on a loop invariant instead of on the value
# pin this case is about. (2) `if False:` makes the true arm unreachable, and
# Nagini's front end rejects that (`dead.code`) before Viper sees anything, so the
# case recorded a rejection no prover ever issued (43c6680f6). The prepatch impl
# has no guard at all, which IS the behaviour claimed here: the configured path is
# never consulted.
_WRONG_BRANCH = _swap(
    _BASE,
    _impl(_BASE),
    _impl((Path(__file__).parent / "model_prepatch.py").read_text()),
)

# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY (verify) — the gold impl with an in-region Assert that the
#    precondition `no_dot(ToSeq(name))` is established and usable for a normal
#    F2P-shaped input. If the Requires could not be admitted, this Assert would
#    fail to verify => PRECOND-TOO-STRONG. (Self-call/caller cannot live in the
#    impl region without changing the spec view, so we re-assert the precond
#    in-region, which exercises the same admissibility obligation.)
_ADMISS = _swap(
    _BASE,
    "    result = []  # type: List[int]\n",
    "    result = []  # type: List[int]\n"
    "    Assert(no_dot(ToSeq(name)))  # precondition admits this input\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": "structurally-different CORRECT impl (top-level branches "
                     "reordered, condition negated); each loop keeps its gold "
                     "take-prefix invariants + framing asserts so the proof is "
                     "intact. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-precond-name-no-dot",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "in-region Assert(no_dot(ToSeq(name))) re-establishes the "
                     "precondition for an F2P-shaped input; verifying confirms "
                     "Requires admits a normal input (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "frame-mutate-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME,
        "refinement": "A faithful real patch that mutates the class name passed "
                      "to the deconstruct fallback would corrupt the reported "
                      "import path (e.g. append a dot), so the F2P "
                      "test_deconstruct (expects exactly 'django.db.models.Value') "
                      "and test_serialize_complex_func_index would NOT resolve.",
        "rationale": "PERMISSION SYSTEM: `name` is Requires(Acc(list_pred(name),"
                     " 1/2)) (read-only). `name.append(DOT())` needs full "
                     "permission and is rejected for INSUFFICIENT PERMISSION. "
                     "Gold invariants/asserts kept verbatim so the rejection is "
                     "attributable solely to the write. #1 weakness class.",
    },
    {
        "id": "wrong-branch-prepatch-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WRONG_BRANCH,
        "refinement": "This IS the pre-patch behaviour: a configured public path "
                      "is ignored and the node reports the internal-submodule "
                      "fallback 'django.db.models.expressions.Value'. F2P "
                      "test_deconstruct expects 'django.db.models.Value' and the "
                      "writer test expects the short models.X form, so it does "
                      "NOT resolve (this is the G-DIFF discriminator).",
        "rationale": "POSTCONDITION clause 2: "
                     "Implies(len(configured) > 0 and exact, "
                     "ToSeq(Result()) == ToSeq(configured)). Taking the fallback "
                     "when the configured branch is required returns "
                     "qualified(module, name) != configured, so the clause fails.",
    },
    {
        "id": "partial-truncate-configured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_TRUNC,
        "refinement": "Off-by-one: drops the LAST code point of the configured "
                      "path, reporting 'django.db.models.Valu'. F2P "
                      "test_deconstruct expects exactly 'django.db.models.Value', "
                      "so the faithful real patch would NOT resolve.",
        "rationale": "POSTCONDITION clause 2: ToSeq(Result()) == ToSeq(configured)"
                     " is violated (Result is one code point short). Correct on "
                     "the empty/fallback sub-domain, wrong on the F2P "
                     "configured-branch inputs (partial-domain).",
    },
    {
        "id": "partial-drop-dot-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_DOT,
        "refinement": "Drops the '.' separator in the fallback branch, reporting "
                      "'django.db.models.expressionsValue'. The pre-patch F2P "
                      "discriminator and any real patch with this bug would emit "
                      "a malformed import path and NOT resolve.",
        "rationale": "POSTCONDITION clause 3: Implies(not(...), "
                     "ToSeq(Result()) == qualified(module, name)); qualified pins "
                     "module + '.' + name, so omitting the dot violates it. "
                     "Correct on the configured sub-domain, wrong on the fallback "
                     "sub-domain (partial-domain).",
    },
]


# No @ContractOnly consumed axioms in this bundle (axioms region is empty); the
# two deep models (deconstruct_path choice, serialized_module_rooted) are
# A-references validated == the real callees by axiom_check.py / G-AX, not
# consumed axioms with an Ensures the verifier relies on. Per PBT_PLAN §4 the
# axiom lane is therefore N/A here.
AXIOM_TESTS = []
