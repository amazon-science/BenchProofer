"""properties.py — PBT falsification battery for sphinx-doc__sphinx-8459.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Every spec case is a full
model.py variant that shares the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited, via _swap on unique in-impl
anchors), checked by Nagini verify + markers.same_spec.

DEFENDED SURFACE (why these cases, not byte-fuzz):

  record_annotations(name0, raw0, has0, name1, raw1, has1, aliases,
                     ret_raw, ret_has) -> Dict[int, int]

  records, per annotated parameter (and the return), the ALIAS-RESOLVED
  annotation token into a freshly-built mapping. The load-bearing clauses are:

    (1) has_i  => name_i in Result() and Result()[name_i] == resolve(raw_i, aliases)
    (2) !has_i => name_i not in Result()
    (3) ret_has  => KEY_RETURN() in Result()
                    and Result()[KEY_RETURN()] == resolve(ret_raw, aliases)
        !ret_has => KEY_RETURN() not in Result()

  resolve(tok, aliases) = aliases[tok] if tok in aliases else expand(tok),
  with expand(tok) = tok + 1000. This is the FIX: the recorded token is the
  alias-resolved form. The prepatch records expand(raw) regardless of the alias
  map, which violates clause (1)/(3) exactly when an alias governs the source
  (tok in aliases) and aliases[tok] != expand(tok).

  READ-ONLY INPUT (frame-mutation applies, has_readonly_input = True):
  `aliases: Dict[int, int]` is held at Acc(dict_pred(aliases), 1/2) -- a HEAP
  predicate at FRACTIONAL permission, required AND ensured (the alias map is
  read, never mutated). A rival that WRITES to aliases (to vacuously satisfy a
  clause) cannot: a dict store needs full permission, so it fails for
  INSUFFICIENT PERMISSION. This is the project's #1 weakness class and is
  covered by `frame-write-aliases` below (MANDATORY).

  UNGROUNDED-ORACLE ECHO is N/A here: resolve is a GROUNDED @Pure oracle (a
  total function of the actual arguments -- the alias map and the token, fully
  unfolded: aliases[tok] / tok+1000). It is consumed SYMMETRICALLY on both sides
  of clause (1)/(3): the spec says Result()[name_i] == resolve(raw_i, aliases)
  and the honest impl writes exactly resolve(raw_i, aliases). There is no
  *wrong* echo -- echoing resolve IS doing the work. Per directive 2 we instead
  carry honest cheapest-correct positive controls (`pos-*`). The genuine attacks
  are the partial-domain rivals that drop the alias resolution on some slot
  (`weak-prepatch-expand`, `weak-return-expand`, `weak-slot1-expand`), each the
  faithful skeleton of a real recorder that fails the F2P alias test.

  CONTROL-FLOW-EFFECT is N/A: the function is a pure dict-builder with no
  raise / no side effect on any argument that the value abstraction misses (the
  only mutable arg, aliases, is the frame-mutation target above; the result is a
  freshly-built dict). No capability-token rival is needed.

  The F2P (test_autodoc_typehints_description_and_type_aliases) configures
  autodoc_type_aliases = {'myint': 'myint'} and annotates sum(x: myint,
  y: myint) -> myint; the gold records `myint` for each (resolve preserves the
  alias), the prepatch records `int` (expand). Every reject rival's refinement
  argument is grounded in that test.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8459"
FLOAT_ENCODING = None  # meta.float_encoding is null; int-token carrier, no --float-encoding


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl body, anchored on the full block so positive-control and
# frame-mutation variants replace ONLY text inside # impl-start .. # impl-end.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation"""


# === POSITIVE CONTROL 1 (soundness, must verify) ===========================
# Branch-REORDER: record the return slot first, then the two parameters, in a
# different textual order. The postcondition clauses are membership/value pins
# on a freshly-built dict and are order-independent, so this builds the IDENTICAL
# mapping. No loop, no fold -> no induction lemma needed (directive 3 N/A). If a
# faithful correct impl in a different order cannot verify => SPEC-TOO-STRONG.
_POS_REORDER = """    annotation = {}  # type: Dict[int, int]
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    return annotation"""


# === POSITIVE CONTROL 2 (soundness, must verify) ===========================
# Local-variable reshape: compute each resolved token into a typed local FIRST,
# then store it. Same values, different executable shape (no control-flow change,
# just an extra binding). Must verify; else SPEC-TOO-STRONG.
_POS_LOCALS = """    annotation = {}  # type: Dict[int, int]
    if has0:
        r0 = resolve(raw0, aliases)  # type: int
        annotation[name0] = r0
    if has1:
        r1 = resolve(raw1, aliases)  # type: int
        annotation[name1] = r1
    if ret_has:
        rr = resolve(ret_raw, aliases)  # type: int
        annotation[KEY_RETURN()] = rr
    return annotation"""


# === ADMISSIBILITY (precondition not too strong, must verify) ==============
# Insert, at the top of the impl, asserts that exercise the precondition on a
# normal F2P-shaped read: under the 1/2 permission we CAN query alias membership
# (the read path the recorder relies on), and the reserved-slot / name-distinct
# preconditions hold. This proves the Requires admits a normal input (else
# PRECOND-TOO-STRONG / a vacuously-unsatisfiable precondition). The gold body is
# kept verbatim after the inserted asserts, so it still discharges the
# postcondition.
_ADMISS_INSERT = """    annotation = {}  # type: Dict[int, int]
    # admissibility witness: the read-only (1/2-permission) alias map is
    # readable -- a membership query verifies, i.e. the Requires admits the
    # normal recorder read path; and the name-distinctness / reserved-slot
    # preconditions hold for an F2P-shaped input.
    Assert(KEY_RETURN() == -1)
    Assert(name0 != name1)
    Assert(name0 != KEY_RETURN() and name1 != KEY_RETURN())
    probe = raw0 in aliases  # type: bool
    Assert(probe or not probe)"""


# === FRAME-MUTATION (MANDATORY, must be REJECTED for INSUFFICIENT PERMISSION) =
# A rival that WRITES into the read-only alias map (held at Acc(dict_pred,1/2))
# before recording. A dict store needs FULL permission, which it does NOT have,
# so Nagini rejects it for insufficient permission -- NOT for a value mismatch.
# The gold recording (which still satisfies the value clauses) is kept verbatim
# AFTER the illegal write, so the rejection is attributable solely to the write.
_FRAME_WRITE = """    annotation = {}  # type: Dict[int, int]
    # ILLEGAL: mutate the read-only alias map (only 1/2 permission held).
    aliases[name0] = raw0
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation"""


# === UNIQUENESS / PARTIAL-DOMAIN rivals (must be REJECTED) =================

# --- weak-prepatch-expand: the ACTUAL gold bug. Records expand(raw) for every
# slot, IGNORING the alias map (== inspect.signature(obj) with type_aliases={}).
# Correct on every slot whose source is NOT aliased; diverges on every aliased
# source whenever aliases[raw] != expand(raw).
_PREPATCH_EXPAND = """    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = expand(raw0)
    if has1:
        annotation[name1] = expand(raw1)
    if ret_has:
        annotation[KEY_RETURN()] = expand(ret_raw)
    return annotation"""

# --- weak-return-expand: parameters resolved correctly, but the RETURN slot
# records expand(ret_raw), ignoring the alias map only for the return. A
# partial-domain rival diverging on a single slot.
_RETURN_EXPAND = """    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    if ret_has:
        annotation[KEY_RETURN()] = expand(ret_raw)
    return annotation"""

# --- weak-slot1-expand: slot0 + return resolved correctly, slot1 records
# expand(raw1), ignoring the alias map for the second parameter only. Tests that
# clause (1) pins EACH parameter, not "the first one".
_SLOT1_EXPAND = """    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = expand(raw1)
    if ret_has:
        annotation[KEY_RETURN()] = resolve(ret_raw, aliases)
    return annotation"""

# --- weak-drop-return: a value-LEVEL rival that records both parameters
# correctly but DROPS the return slot entirely (never records KEY_RETURN()).
# Violates clause (3) on ret_has: KEY_RETURN() must be IN the result. A faithful
# real patch that omitted `annotation['return'] = stringify(...)` would render no
# "Return type:" line -- the F2P asserts exactly 'Return type:\n      myint\n'.
_DROP_RETURN = """    annotation = {}  # type: Dict[int, int]
    if has0:
        annotation[name0] = resolve(raw0, aliases)
    if has1:
        annotation[name1] = resolve(raw1, aliases)
    return annotation"""


def _impl(body):
    return _swap(_BASE, _GOLD_IMPL, body)


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "branch-REORDER positive control: record the return slot first, then "
            "slot1, then slot0. The postcondition clauses are membership/value "
            "pins on a freshly-built dict and are order-independent, so the "
            "IDENTICAL mapping is built. No loop / no fold => no induction lemma "
            "(directive 3 N/A). Must verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-locals-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LOCALS),
        "rationale": (
            "local-variable reshape positive control: each resolved token is "
            "bound to a typed local (r0/r1/rr) before being stored. Same values, "
            "different executable shape. Keeps every clause satisfiable; must "
            "verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-readonly-membership",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    annotation = {}  # type: Dict[int, int]\n    if has0:",
            _ADMISS_INSERT + "\n    if has0:",
        ),
        "rationale": (
            "admissibility: asserts the precondition admits a normal F2P-shaped "
            "input -- the reserved slot KEY_RETURN()==-1, the name-distinctness "
            "preconditions hold, and the 1/2-permission alias map is readable (a "
            "membership query `raw0 in aliases` verifies). If the Requires were "
            "vacuous / too strong these would fail (PRECOND-TOO-STRONG). The gold "
            "body follows verbatim, so the postcondition still verifies."
        ),
    },
    # ----- frame-mutation (MANDATORY; must be rejected for permission) -----
    {
        "id": "frame-write-aliases",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_WRITE),
        "refinement": (
            "the alias map (app.config.autodoc_type_aliases) is GLOBAL "
            "configuration shared across every documented object; a faithful real "
            "patch that mutated it inside record_typehints would corrupt the "
            "config for all subsequent autofunction directives (and on the F2P "
            "build would poison the {'myint':'myint'} map), so it would not "
            "resolve. The real recorder only READS the map -- modelled by the 1/2 "
            "permission. A verifying mutating rival would be a true "
            "verify-but-not-resolve break."
        ),
        "rationale": (
            "rejected by the PERMISSION SYSTEM, not a value clause: `aliases` is "
            "held at Acc(dict_pred(aliases), 1/2); a dict store `aliases[name0]=..`"
            " needs FULL permission, so Nagini fails for INSUFFICIENT PERMISSION. "
            "The gold value-clause recording is kept verbatim after the write, so "
            "the rejection is attributable solely to the illegal mutation."
        ),
    },
    # ----- uniqueness / partial-domain rivals (must be rejected) ----------
    {
        "id": "weak-prepatch-expand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_EXPAND),
        "refinement": (
            "this IS the prepatch behaviour: records expand(raw) for every slot, "
            "ignoring the alias map (== inspect.signature(obj) with the default "
            "type_aliases={}). Its faithful real patch is the PRE-patch code, "
            "which fails FAIL_TO_PASS "
            "test_autodoc_typehints_description_and_type_aliases: with "
            "autodoc_type_aliases={'myint':'myint'} the gold renders 'myint' for "
            "x, y and the return, but expand records the underlying 'int' -- the "
            "exact reported bug. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause (1)/(3): Result()[name_i] must equal "
            "resolve(raw_i, aliases); when raw_i in aliases, resolve == "
            "aliases[raw_i] which (by expand(tok)=tok+1000) differs from "
            "expand(raw_i), so the recorded token is wrong. Rejection comes from "
            "the alias-resolved value pin, not from membership (every slot is "
            "still present)."
        ),
    },
    {
        "id": "weak-return-expand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RETURN_EXPAND),
        "refinement": (
            "a partial-domain rival correct on BOTH parameters but recording "
            "expand(ret_raw) for the RETURN slot only. A faithful real patch that "
            "threaded the alias map for the parameter loop but left the "
            "`annotation['return'] = stringify(sig.return_annotation)` line on the "
            "unaliased signature would render the parameters as 'myint' yet the "
            "return as 'int' -- the F2P asserts 'Return type:\\n      myint\\n', so "
            "it would not resolve. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause (3): Result()[KEY_RETURN()] must "
            "equal resolve(ret_raw, aliases); the rival stores expand(ret_raw), "
            "which differs whenever ret_raw in aliases. The return clause is "
            "pinned independently of the parameter clauses, so a single-slot "
            "divergence is caught."
        ),
    },
    {
        "id": "weak-slot1-expand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SLOT1_EXPAND),
        "refinement": (
            "a partial-domain rival correct on slot0 and the return but recording "
            "expand(raw1) for the SECOND parameter only. A faithful real patch "
            "that alias-resolved only the first parameter (e.g. an off-by-one in "
            "the parameter loop) would render x as 'myint' and y as 'int' -- the "
            "F2P asserts y is '*myint*', so it would not resolve. "
            "verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause (1) on slot1: Result()[name1] must "
            "equal resolve(raw1, aliases); the rival stores expand(raw1), which "
            "differs whenever raw1 in aliases. Clause (1) pins EACH parameter "
            "(name0 AND name1), not just the first."
        ),
    },
    {
        "id": "weak-drop-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_RETURN),
        "refinement": (
            "records both parameters correctly but DROPS the return slot entirely "
            "(never records KEY_RETURN()). A faithful real patch omitting "
            "`if sig.return_annotation is not sig.empty: annotation['return']=..` "
            "renders no 'Return type:' line, but the F2P asserts the output ends "
            "'Return type:\\n      myint\\n'. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by postcondition clause (3) on ret_has: KEY_RETURN() must be "
            "IN Result() when ret_has; the rival never inserts it, so the "
            "membership conjunct fails. (Distinct from weak-return-expand, which "
            "inserts a WRONG return value; this one inserts NO return entry.)"
        ),
    },
]

# No @ContractOnly axioms and no consumed A-reference at proof time
# (meta.axioms == []). The annotation resolution the change makes effective is
# modelled DEEPLY by resolve/expand in the pure region and is validated == the
# real typing.get_type_hints resolver out-of-band by axiom_check.py (G-AX), which
# is a model-fidelity check run separately -- NOT a consumed axiom whose Ensures
# the proof depends on. There is therefore no axiom whose soundness or
# caller-domain containment the PBT lane must (re-)probe here.
AXIOM_TESTS = []
