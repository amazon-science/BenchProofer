# properties.py — PBT manifest for django__django-11820. NOT a Nagini module; a
# record of adversarial cases. The runner (swebench_nagini.pbt) executes each and
# stamps RESULT. Spec cases are full model.py variants that share the frozen spec
# byte-for-byte (region-surgery edits ONLY inside # impl-start/# impl-end, which
# also contains the nested # invariants region) and are checked by Nagini verify +
# markers.same_spec; axiom cases are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (read model.py + refinement.md + mapping.md):
#   check_related_path(path: List[int], root: int) -> bool
#     Requires(Acc(list_pred(path), 1/2))   <-- READ-ONLY input (half perm)
#     Requires(root >= 0)
#     Requires(MustTerminate(2))            <-- TOTALITY: the walk must ANSWER
#     Ensures(Acc(list_pred(path), 1/2))
#     Ensures(Result() == walk_err(ToSeq(path), root, root, -1))   <-- LOAD-BEARING
#
#   The load-bearing postcondition pins Result() EXACTLY to the @Pure deep fold
#   `walk_err` evaluated on the actual inputs (path, root). `walk_err` is a fully
#   unfolded @Pure definition (NOT @ContractOnly), so the oracle is GROUNDED in the
#   args: the cheapest honest impl is `return walk_err(ToSeq(path), root, root, -1)`
#   and there is no WRONG value to echo (echoing the oracle echoes the correct
#   answer). Hence the ungrounded-oracle-echo class does NOT apply; instead we
#   carry an honest cheapest-impl positive control (pos-cheapest).
#
#   The five axioms-region functions (resolve_kind / relation_target / pk_kind /
#   pk_target / transform_present) are @ContractOnly A-reference graph data: the
#   proof consumes ONLY their return-range Ensures (branch totality), and they
#   model the UNCHANGED name-resolution machinery. The two genuinely-changed
#   behaviours are modelled DEEPLY in walk_err / the impl loop:
#     (A4) pk alias  : name==0 resolves via pk_kind/pk_target (not resolve_kind)
#     (A7) non-rel reset: after a non-relation field model becomes -1 ("none")
#   These two are the F2P discriminators (F2P 1 = parent__field1__field2 multi-hop
#   through a non-relation field; F2P 2 = parent__pk of a related model).
#
#   AXIOM_TESTS: the axioms are @ContractOnly with only range Ensures and are
#   already executable-soundness-checked end-to-end by axiom_check.py / G-AX
#   (deep fold backed by the REAL Django callees == real _check_ordering E015
#   verdict on 2 F2P + 4 P2P + 3 adversarial scenarios). We re-run that exact
#   in-Docker check as both the axiom-soundness probe (range facts hold on the
#   real callees) and the axiom-containment probe (every callee-input the model
#   reaches lies in the {model,name} graph domain the axioms cover). See rationale
#   on each probe.
from pathlib import Path

INSTANCE = "django__django-11820"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region of model.py. Every _swap below
# edits ONLY text between # impl-start and # impl-end, so spec_signature (axioms,
# pure walk_err, signature, pre/post-conditions) is preserved => same_spec.
# ---------------------------------------------------------------------------

# The pk-alias branch (the A4 fixed behaviour) verbatim from model.py impl.
_PK_BRANCH = """        elif name == 0:
            # pk alias: the field is found on the current model.
            fld_model = model
            fld_name = name
            if pk_kind(model) == 1:
                model = pk_target(model)
            else:
                model = -1
        else:"""

# The k==2 non-relation branch (the A7 fixed behaviour) verbatim from model.py.
_NONREL_BRANCH = """            else:
                fld_model = model
                fld_name = name
                model = -1
        i = i + 1"""

# The whole impl body (used to rebuild a cheapest-correct positive control while
# preserving the postcondition frame). We replace the executable body but keep the
# ghost target + the read-permission frame so Acc(list_pred(path),1/2) is returned.
_IMPL_BODY = _BASE.split("    # impl-start\n", 1)[1].split("    # impl-end", 1)[0]


# === 1. FRAME-MUTATION (MANDATORY: path is Acc(list_pred(path),1/2) read-only) ==
# A rival that WRITES to the read-only input `path`. To "satisfy" the postcondition
# it tries to overwrite path[0]; with only half permission a write needs the full
# list_pred, so Nagini must reject for INSUFFICIENT PERMISSION. Gold invariants are
# kept verbatim so the rejection is attributable solely to the write.
_frame = _swap(
    _BASE,
    "    n = len(path)\n    i = 0\n    acc = False",
    "    n = len(path)\n    if n > 0:\n        path[0] = 0  # FRAME VIOLATION: write to read-only Acc(...,1/2) input\n    i = 0\n    acc = False",
)


# === 2. pk-alias rival (partial-domain / the A4 fixed behaviour reverted) ========
# Route the `pk` alias (name 0) through resolve_kind instead of pk_kind/pk_target.
# This is exactly model_prepatch_1's behaviour. Keeps the spec walk_err + Ensures
# verbatim, so the loop invariant whole == (acc or walk_err(...drop(i)...)) is no
# longer preserved (the buggy walk disagrees with the post-fix fold on a pk alias
# of a related model) => Nagini rejects. REFINEMENT: the faithful real patch drops
# `if part == 'pk': fld = _cls._meta.pk`, so `parent__pk` raises FieldDoesNotExist
# and wrongly emits E015 -> F2P test_ordering_pointing_to_related_model_pk FAILS
# (expects []), so the rival does NOT resolve.
_pk_rival = _swap(
    _BASE,
    _PK_BRANCH,
    """        else:
            # NO pk alias: ``pk`` (name 0) routes through resolve_kind (raises ->
            # resolves to nothing).""",
)


# === 3. non-relation-reset rival (partial-domain / the A7 fixed behaviour) =======
# After a non-relation field (k==2) leave `model` unchanged instead of setting it
# to -1. This is exactly model_prepatch_2's behaviour. REFINEMENT: the faithful
# real patch drops `else: _cls = None`, so a name following a non-relation field is
# re-resolved against the SAME model; `parent__field1__field2` then wrongly passes
# -> F2P test_ordering_pointing_multiple_times_to_model_fields FAILS (expects an
# E015), so the rival does NOT resolve. Rejected: loop invariant tying acc to the
# post-fix walk_err fold is not preserved on a multi-hop non-relation path.
_nonrel_rival = _swap(
    _BASE,
    _NONREL_BRANCH,
    """            else:
                fld_model = model
                fld_name = name
                # model UNCHANGED after a non-relation field (pre-fix)
        i = i + 1""",
)


# === 4. transform-rescue drop (partial-domain) ==================================
# In BOTH error arms (model==-1 and k==0) drop the transform-rescue guard and
# always set acc=True. This pins the transform_present clause of walk_err: a path
# whose trailing name is a REGISTERED transform of the last found field (e.g.
# `field__lower`) is legitimate (walk_err == False) but this rival reports an
# error. REFINEMENT: the faithful real patch would replace
# `if fld is None or fld.get_transform(part) is None:` with an unconditional
# `errors.append(E015)`, so any valid registered-transform ordering tail spuriously
# emits E015 (a P2P regression on transform-tail orderings) and also breaks the
# rescue path the gold validator relies on -> does NOT resolve. Rejected because
# walk_err can be False on a transform tail while this impl returns True.
_xform_rival = _swap(
    _swap(
        _BASE,
        """        if model == -1:
            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                acc = True""",
        """        if model == -1:
            # DROP transform rescue: always error when nothing to resolve against
            acc = True""",
    ),
    """            if k == 0:
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True""",
    """            if k == 0:
                # DROP transform rescue: always error on resolves-to-nothing
                acc = True""",
)


# === 4b. DIVERGENCE (vacuity / the audited P1 hole) ==============================
# Handle the empty path correctly, then spin forever instead of returning the
# verdict on any nonempty path. Every value postcondition holds vacuously on the
# non-returning path. REFINEMENT: a real validator that hangs on any nonempty
# ordering path (e.g. an accidental infinite retry loop before computing the
# verdict) never returns from Model.check(); every F2P/P2P checks test times
# out -> does NOT resolve. Rejected by the MustTerminate(2) termination
# obligation in the pre-conditions: the endless loop carries no termination
# measure, so Nagini reports an obligation leak. Without MustTerminate this
# rival VERIFIED (the audit's P1 witness class: any same-spec impl whose only
# defect is non-termination).
_DIVERGE_BODY = """
    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
    if len(path) == 0:
        return whole
    x = 0
    while x == 0:
        x = 0
    return whole
    """
_diverge = _swap(_BASE, _IMPL_BODY, _DIVERGE_BODY)


# === 5. POSITIVE CONTROL — cheapest honest impl (soundness) =====================
# The oracle is grounded in the inputs, so the cheapest correct impl literally
# returns the deep fold. It MUST verify (the frame Acc(...,1/2) is returned because
# we never touch path). If a faithful correct impl can't verify => SPEC-TOO-STRONG.
_pos_cheapest_body = (
    "\n    return walk_err(ToSeq(path), root, root, -1)\n    "
)
_pos_cheapest = _swap(_BASE, _IMPL_BODY, _pos_cheapest_body)


# === 6. POSITIVE CONTROL — structurally-different correct impl (soundness) =======
# Reorder the ordinary-name branch dispatch (test k==2 first, then k==1, then k==0)
# WITHOUT changing behaviour, keeping every gold invariant + framing Assert verbatim
# so the gold proof obligations still discharge. A correct structural variant must
# verify (else SPEC-TOO-STRONG). This is a branch-reorder (directive 3-safe: no
# loop-direction flip, no dropped framing assert).
_REORDER_OLD = """        else:
            k = resolve_kind(model, name)
            if k == 0:
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True
                # model and fld unchanged
            elif k == 1:
                fld_model = model
                fld_name = name
                model = relation_target(model, name)
            else:
                fld_model = model
                fld_name = name
                model = -1
        i = i + 1"""
_REORDER_NEW = """        else:
            k = resolve_kind(model, name)
            if k == 2:
                fld_model = model
                fld_name = name
                model = -1
            elif k == 1:
                fld_model = model
                fld_name = name
                model = relation_target(model, name)
            else:
                # k == 0: resolves to nothing
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True
                # model and fld unchanged
        i = i + 1"""
_pos_reorder = _swap(_BASE, _REORDER_OLD, _REORDER_NEW)


# === 7. ADMISSIBILITY (precondition admits a normal F2P-shaped input) ===========
# Keep the correct impl, but additionally read the read-only input (path[0] when
# n>0) and assert root>=0 propagated, proving the precondition Acc(list_pred(path),
# 1/2) AND root>=0 are jointly establishable & non-contradictory for a normal
# nonempty related path. If this fails to verify => PRECOND-TOO-STRONG. Reading
# path[0] needs only the half permission the precondition grants, so it must hold.
_admiss = _swap(
    _BASE,
    "    n = len(path)\n    i = 0\n    acc = False",
    "    n = len(path)\n    Assert(root >= 0)  # admissibility: precond root>=0 usable\n    if n > 0:\n        Assert(path[0] == path[0])  # admissibility: half-perm read of input usable\n    i = 0\n    acc = False",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame,
        "refinement": (
            "Writing path[0] is not a behaviour the gold patch performs at all "
            "(the validator never mutates the ordering path); a real impl that "
            "overwrites the path it is validating would corrupt the very lookup "
            "string the E015 message reports and break every F2P/P2P assertion on "
            "the exact path text. The write also cannot type-check against the "
            "read-only input, so no faithful patch resolves."
        ),
        "rationale": (
            "Permission system: path is Acc(list_pred(path), 1/2); a write needs "
            "the full list_pred, so Nagini rejects for INSUFFICIENT PERMISSION. "
            "Gold invariants kept verbatim => rejection attributable to the write."
        ),
    },
    {
        "id": "pk-alias-reverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _pk_rival,
        "refinement": (
            "Equivalent to dropping `if part == 'pk': fld = _cls._meta.pk` (gold "
            "hunk A4). Then `parent__pk` routes through get_field('pk') which "
            "raises FieldDoesNotExist, so the validator wrongly appends E015 for "
            "the related-model pk path. F2P test_ordering_pointing_to_related_"
            "model_pk asserts [] (no error) -> FAILS -> does NOT resolve."
        ),
        "rationale": (
            "Postcondition Result()==walk_err(...): walk_err's name==0 branch "
            "resolves pk via pk_kind/pk_target; this rival resolves it via "
            "resolve_kind, so the loop invariant whole==(acc or walk_err(.drop(i).)) "
            "is not preserved on a pk-alias step => Nagini rejects (see "
            "model_prepatch_1.py / G-DIFF)."
        ),
    },
    {
        "id": "non-relation-reset-reverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _nonrel_rival,
        "refinement": (
            "Equivalent to dropping `else: _cls = None` (gold hunk A7). Then a "
            "name following a non-relation field is re-resolved against the SAME "
            "model, so `parent__field1__field2` (field1 is a CharField, non-"
            "relation) wrongly passes. F2P test_ordering_pointing_multiple_times_"
            "to_model_fields asserts an E015 -> FAILS -> does NOT resolve."
        ),
        "rationale": (
            "Postcondition Result()==walk_err(...): walk_err's k==2 branch sets "
            "model=-1; this rival leaves model unchanged, so the loop invariant "
            "tying acc to the post-fix walk_err fold fails on a multi-hop non-"
            "relation path => Nagini rejects (see model_prepatch_2.py / G-DIFF)."
        ),
    },
    {
        "id": "transform-rescue-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _xform_rival,
        "refinement": (
            "Equivalent to replacing `if fld is None or fld.get_transform(part) "
            "is None:` with an unconditional `errors.append(E015)`. A trailing "
            "registered transform (e.g. ordering by `field__lower`) is a "
            "legitimate target the gold validator accepts; this rival emits E015 "
            "for it, a P2P regression on transform-tail orderings -> does NOT "
            "resolve."
        ),
        "rationale": (
            "Postcondition Result()==walk_err(...): walk_err's error arms are "
            "guarded by (fld_name==-1 or not transform_present(...)); dropping the "
            "guard makes acc=True while walk_err==False on a transform tail, so "
            "the result-equals-walk_err invariant fails => Nagini rejects."
        ),
    },
    {
        "id": "diverge-nonempty-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _diverge,
        "refinement": (
            "A real validator that spins forever on any nonempty ordering path "
            "(an accidental infinite loop before the verdict is computed) never "
            "returns from Model.check(); every F2P/P2P checks-framework test "
            "hangs and the harness times out -> does NOT resolve. This is the "
            "audit's P1 witness class: a same-spec impl whose only defect is "
            "non-termination."
        ),
        "rationale": (
            "Rejected by the MustTerminate(2) termination obligation in the "
            "pre-conditions: the endless loop takes no termination measure, so "
            "Nagini reports an obligation leak. Without MustTerminate this "
            "rival verified (every value postcondition vacuous on the "
            "non-returning path) — the exact hole G-PANEL-1 flagged."
        ),
    },
    {
        "id": "pos-cheapest-return-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_cheapest,
        "rationale": (
            "The oracle walk_err is @Pure and grounded in the args, so the "
            "cheapest honest correct impl is `return walk_err(ToSeq(path), root, "
            "root, -1)`. It never touches path, so Acc(list_pred(path),1/2) is "
            "returned and the Ensures holds trivially. Must verify (else SPEC-TOO-"
            "STRONG). Doubles as proof the postcondition is satisfiable."
        ),
    },
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_reorder,
        "rationale": (
            "A structurally-different but behaviourally-identical impl: the "
            "ordinary-name dispatch tests k==2, then k==1, then k==0 (vs gold's "
            "0/1/2). Every gold invariant and framing Assert is kept verbatim, so "
            "the gold proof still discharges. A correct structural variant must "
            "verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-normal-related-path",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Keeps the correct impl and additionally asserts root>=0 (from the "
            "precondition) and reads path[0] under n>0 using only the half "
            "permission the precondition grants. This proves Requires(Acc(list_"
            "pred(path),1/2)) and Requires(root>=0) are jointly establishable and "
            "non-contradictory for a normal nonempty related path; must verify "
            "(else PRECOND-TOO-STRONG)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM_TESTS — the five axioms-region functions are @ContractOnly A-reference
# graph data with ONLY return-range Ensures. We reuse the bundle's own
# axiom_check.py (read on the HOST at load time and embedded into the probe, since
# the runner mounts only the probe at /work) as both the soundness and containment
# probe, run in the gold-patched Docker image (apply_gold=True): it executes the
# REAL Django callees (get_field/is_relation/_meta.pk/get_path_info/get_transform),
# observes the range facts hold (soundness), and folds walk_err over each path
# using those real callees to assert the deep model EQUALS the real _check_ordering
# E015 verdict (end-to-end soundness of the A-reference deep model).
# ---------------------------------------------------------------------------

# Soundness probe: run axiom_check.py verbatim (range facts + deep-model==real).
_AX_SOUND_PROBE = (
    "import sys\n"
    "# axiom_check.py source embedded from the HOST bundle (runner mounts only\n"
    "# this probe at /work; the bundle file is NOT in-container).\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__axcheck__', '__file__': '/work/axiom_check_embedded.py'}\n"
    "exec(compile(_SRC, 'axiom_check_embedded.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom-soundness: range facts + deep-model==real _check_ordering OK' if rc == 0 else 'FAIL')\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

# Containment probe: same in-container machinery, but the explicit obligation is
# that every {model, name} the model can REACH lies in the graph domain the axioms
# cover. The axioms' Requires are total over int model/name ids (range facts only,
# no domain restriction beyond root>=0 / valid model ids), so containment is
# vacuously satisfied for every caller-reachable input; we still EXECUTE the real
# callees along each genuine forward traversal (build_and_check phase (1)) to
# confirm resolve_kind in {0,1,2}, pk_kind in {1,2}, targets are real models, and
# transform_present is a bool on every {model,name} the model actually reaches.
_AX_COVER_PROBE = (
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__axcover__', '__file__': '/work/axiom_check_embedded.py'}\n"
    "exec(compile(_SRC, 'axiom_check_embedded.py', 'exec'), g)\n"
    "# Re-run the full scenario set; build_and_check's phase (1) asserts the\n"
    "# axioms' range facts hold on EVERY {model,name} reached along the forward\n"
    "# traversal (containment: no reachable input falls outside the axioms'\n"
    "# total int domain). The axioms place no domain restriction beyond the\n"
    "# return-range facts, so any caller-reachable {model,name} is covered.\n"
    "rc = g['main']()\n"
    "print('axiom-containment: every caller-reachable {model,name} lies in the axioms domain (range facts hold)' if rc == 0 else 'FAIL')\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-graph-functions",
        "axiom": "resolve_kind/relation_target/pk_kind/pk_target/transform_present",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "Runs the bundle's axiom_check.py in the gold-patched Django image: "
            "(1) the range Ensures (resolve_kind in {0,1,2}, pk_kind in {1,2}, "
            "relation_target/pk_target are real models, transform_present a bool) "
            "hold on the REAL callees; (2) the A-reference deep model walk_err, "
            "backed by those real callees, reproduces the real Model._check_"
            "ordering E015 verdict on 2 F2P + 4 P2P + 3 adversarial paths. Any "
            "violation => AXIOM-UNSOUND. No flag dependency (pk alias is hard-"
            "coded; meta says flag_dependency: none)."
        ),
    },
    {
        "id": "ax-cover-caller-domain",
        "axiom": "resolve_kind/relation_target/pk_kind/pk_target/transform_present",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "Containment: every {model, name} the modelled walk can reach is a "
            "valid (model class, field-name) pair (or the pk alias) along a real "
            "forward traversal; axiom_check.py's build_and_check phase (1) "
            "executes the real callees on each reached input and asserts the "
            "range facts, confirming no caller-reachable input falls outside the "
            "axioms' (total int) domain. A reachable input outside the covered "
            "domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists here."
        ),
    },
]
