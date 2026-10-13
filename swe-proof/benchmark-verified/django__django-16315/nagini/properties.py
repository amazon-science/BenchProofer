"""PBT manifest for django__django-16315 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (region surgery edits
ONLY inside the # impl-start/# impl-end regions, which `same_spec` elides) and
swap the implementation; they are checked by Nagini verify + markers.same_spec.

Defended surface (read first):
  * `conflict_columns(requested, field_names, field_columns) -> List[int]`
      - ALL THREE inputs are READ-ONLY: Acc(list_pred(x), 1/2). Result() is a
        fresh full-permission list.
      - Load-bearing postcondition (two clauses, jointly):
          len(Result()) == len(requested)                              (length/order)
          forall k in [0,len): Result()[k] == column_for(requested[k],   (each element is
                                 field_names, field_columns)              the COLUMN, not the name)
      - `column_for` is GROUNDED in the inputs: it is a structural front-recursive
        walk over the (field_names, field_columns) registry, fully unfolded inside
        the contract — NOT an opaque @Pure answer-key. There is therefore no
        "wrong echo": calling `lookup` / returning column_for IS the correct work,
        not a cheat. (UNGROUNDED-ORACLE-ECHO class is N/A; see assessment.)
  * `lookup(name, field_names, field_columns) -> int`
      - inputs READ-ONLY at 1/4; load-bearing postcond:
          Result() == column_for(name, field_names, field_columns)   (the COLUMN)
      - This is where the change under test lives: the storage COLUMN
        (field_columns[j]) vs the in-memory NAME (field_names[j]). The discriminator
        bites exactly when a db_column override makes column != name.

The F2P (`test_update_conflicts_unique_fields_update_fields_db_column`) uses
db_column="rAnK"/"oTheRNaMe" so column != name; a rival that returns the NAME
verifies-but-does-not-resolve only if the spec is too weak — that is the central
attack here.
"""
from pathlib import Path

INSTANCE = "django__django-16315"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# SPEC TESTS
# ===========================================================================
SPEC_TESTS = []

# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — structurally different but CORRECT `lookup`.
#    Reshape: compute the candidate column into a local before returning, and
#    reorder so the early-exit on match is expressed via a local boolean. Keep
#    EVERY framing Assert about drop(j) intact (they discharge column_for's
#    front-unfold) so this fails only if the spec rejects a correct output.
# ---------------------------------------------------------------------------
_LOOKUP_MATCH = (
    "        if field_names[j] == name:\n"
    "            # first match: column_for over the suffix returns this slot's column\n"
    "            return field_columns[j]\n"
)
_pos_lookup = _swap(
    _BASE,
    _LOOKUP_MATCH,
    "        if field_names[j] == name:\n"
    "            # first match: bind the slot column to a typed local, then return it\n"
    "            chosen = field_columns[j]  # type: int\n"
    "            return chosen\n",
)
SPEC_TESTS.append({
    "id": "pos-lookup-local-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_lookup,
    "rationale": "a correct impl that binds the matched slot's COLUMN to a typed "
                 "local before returning it (structural reshape, same value, all "
                 "drop(j) framing asserts kept) must verify; else SPEC-TOO-STRONG.",
})

# ---------------------------------------------------------------------------
# 1b. POSITIVE CONTROL (soundness) — structurally different but CORRECT
#     `conflict_columns`. Local-variable reshape: bind the resolved column to an
#     intermediate `c2`, keep the forward-append shape (matches the front-recursive
#     column_for spec — NO f(a+b) lemma needed), keep the per-element pin Assert.
# ---------------------------------------------------------------------------
_pos_cc = _swap(
    _BASE,
    "        col = lookup(requested[i], field_names, field_columns)\n"
    "        result = result + [col]\n"
    "        Assert(ToSeq(result)[i] == col)\n",
    "        col = lookup(requested[i], field_names, field_columns)\n"
    "        c2 = col  # type: int\n"
    "        result = result + [c2]\n"
    "        Assert(ToSeq(result)[i] == c2)\n",
)
SPEC_TESTS.append({
    "id": "pos-cc-local-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_cc,
    "rationale": "correct conflict_columns with an extra local alias around the "
                 "forward-append (gold proof obligations intact) must verify; else "
                 "SPEC-TOO-STRONG.",
})

# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN / DISCRIMINATOR — `lookup` returns the NAME (field_names[j])
#    instead of the COLUMN. Correct on the (name==column) sub-domain (no override),
#    WRONG on the override sub-domain (db_column set). This IS the pre-patch bug.
#    Must be REJECTED by lookup's postcondition Result()==column_for(...) (column).
#    refinement: a faithful patch that fed the field NAME to on_conflict_suffix_sql
#    is exactly the pre-patch code; it produces a clause referencing column "rAnK"
#    spelled as name "rank" -> the F2P
#    test_update_conflicts_unique_fields_update_fields_db_column does NOT resolve.
# ---------------------------------------------------------------------------
_rej_name_echo = _swap(
    _BASE,
    _LOOKUP_MATCH,
    "        if field_names[j] == name:\n"
    "            return field_names[j]\n",
)
SPEC_TESTS.append({
    "id": "rej-lookup-returns-name",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rej_name_echo,
    "refinement": "returning field_names[j] is the PRE-PATCH dataflow (field NAME, "
                  "not storage column). With db_column='rAnK' the produced ON "
                  "CONFLICT clause names 'rank' instead of column 'rAnK', so the gold "
                  "F2P test_update_conflicts_unique_fields_update_fields_db_column "
                  "stays FAILING — a verify here would be verify-but-not-resolve.",
    "rationale": "rejected by lookup post-condition Result()==column_for(name,...) "
                 "(== field_columns[match], the COLUMN) whenever column != name.",
})

# ---------------------------------------------------------------------------
# 2b. PARTIAL-DOMAIN — `lookup` returns `name` (the requested arg) directly.
#     Equivalent wrong identifier from a different surface (no index read); still
#     the name, not the column. Rejected for the same reason. Supporting case.
# ---------------------------------------------------------------------------
_rej_return_arg = _swap(
    _BASE,
    _LOOKUP_MATCH,
    "        if field_names[j] == name:\n"
    "            return name\n",
)
SPEC_TESTS.append({
    "id": "rej-lookup-returns-arg-name",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rej_return_arg,
    "refinement": "returning the requested `name` is again the field-NAME identifier "
                  "(name==field_names[j] at the match). Same pre-patch behaviour; the "
                  "F2P db_column test does not resolve (clause names 'rank' not 'rAnK').",
    "rationale": "rejected by Result()==column_for(name,...): column_for returns the "
                 "matched slot's column, which differs from name when db_column is set.",
})

# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN (off-by-one) — `lookup` returns the column of the NEXT slot
#    (field_columns[j+1] style) i.e. shifts the registry. Wrong column for the
#    designated field; rejected. Built by mutating the match to consult the
#    successor column when in range. Diverges on any registry where adjacent
#    columns differ (the F2P registry: rAnK vs oTheRNaMe).
# ---------------------------------------------------------------------------
_rej_shift = _swap(
    _BASE,
    _LOOKUP_MATCH,
    "        if field_names[j] == name:\n"
    "            # WRONG-FIELD: hand back a neighbouring slot's column\n"
    "            if j + 1 < len(field_columns):\n"
    "                return field_columns[j + 1]\n"
    "            return field_columns[j]\n",
)
SPEC_TESTS.append({
    "id": "rej-lookup-off-by-one-column",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rej_shift,
    "refinement": "selecting a neighbouring field's column is a wrong-field "
                  "resolution: a real patch doing get_field returning the next field "
                  "would hand the wrong db column (e.g. 'oTheRNaMe' for requested "
                  "'rank'), so the F2P assertion on the produced clause fails -> not "
                  "resolved.",
    "rationale": "rejected by Result()==column_for(name,...): column_for pins the "
                 "FIRST matching slot's column (field_columns[j]); the +1 slot differs.",
})

# ---------------------------------------------------------------------------
# 4. PARTIAL-DOMAIN — `conflict_columns` drops the FIRST element (start the loop
#    at i=1) so Result() is length len-1 / order-shifted. Correct on the empty
#    and singleton-ignored tail but wrong length/element-0. Rejected by
#    len(Result())==len(requested) and the element-wise Forall.
# ---------------------------------------------------------------------------
_rej_skip_first = _swap(
    _BASE,
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(requested):\n",
    "    result = []  # type: List[int]\n"
    "    i = 1 if len(requested) > 0 else 0\n"
    "    while i < len(requested):\n",
)
SPEC_TESTS.append({
    "id": "rej-cc-skip-first",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rej_skip_first,
    "refinement": "dropping the first requested field omits a conflict target from "
                  "the ON CONFLICT clause (e.g. omits 'rank'/'rAnK'); the F2P upsert "
                  "would not key on it and the test's expected rows/columns differ -> "
                  "not resolved.",
    "rationale": "rejected by len(Result())==len(requested) (now len-1 for non-empty "
                 "input) and by the element-wise Result()[k]==column_for(requested[k]).",
})

# ---------------------------------------------------------------------------
# 5. FRAME-MUTATION (MANDATORY: read-only Acc(...,1/2) inputs) — a rival that
#    WRITES to a read-only input (field_columns) to "normalise" the registry to
#    name==column, which would let returning the name vacuously match. The frozen
#    spec only grants Acc(list_pred(field_columns), 1/2): the write must FAIL for
#    INSUFFICIENT PERMISSION (a byte-fuzzer never tries this). Gold invariants kept
#    verbatim so the rejection is attributable to the write, not a proof gap.
# ---------------------------------------------------------------------------
_rej_frame_mut = _swap(
    _BASE,
    "        # the i-th requested name is registered (instantiate the Forall):\n"
    "        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))\n"
    "        # resolve the requested name to a declared field, then take its column.\n"
    "        col = lookup(requested[i], field_names, field_columns)\n",
    "        # FRAME-MUTATION ATTACK: overwrite a read-only registry slot. Only\n"
    "        # 1/2 permission to field_columns is held -> writing requires full\n"
    "        # permission and MUST be rejected for insufficient permission.\n"
    "        if len(field_columns) > 0:\n"
    "            field_columns[0] = 0\n"
    "        # the i-th requested name is registered (instantiate the Forall):\n"
    "        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))\n"
    "        # resolve the requested name to a declared field, then take its column.\n"
    "        col = lookup(requested[i], field_names, field_columns)\n",
)
SPEC_TESTS.append({
    "id": "rej-frame-mutate-field-columns",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rej_frame_mut,
    "refinement": "the real bulk_create resolution must NOT mutate the model's field "
                  "registry; an impl that overwrites a Field's stored column to force a "
                  "match would corrupt the shared _meta and break every other query — "
                  "such a patch is not the gold change and would not resolve the suite.",
    "rationale": "rejected by the permission system: only Acc(list_pred(field_columns),"
                 " 1/2) is held; writing field_columns[0] needs full permission -> "
                 "INSUFFICIENT PERMISSION (frame violation), independent of any value.",
})

# ---------------------------------------------------------------------------
# 6. FRAME-MUTATION (supporting) — `lookup` writes to its read-only field_columns
#    (held at 1/4) before returning the correct column. Must reject for insufficient
#    permission even though the returned value is right.
# ---------------------------------------------------------------------------
_rej_frame_mut_lookup = _swap(
    _BASE,
    _LOOKUP_MATCH,
    "        if field_names[j] == name:\n"
    "            ans = field_columns[j]  # type: int\n"
    "            field_columns[j] = ans  # FRAME-MUTATION: write at 1/4 permission\n"
    "            return ans\n",
)
SPEC_TESTS.append({
    "id": "rej-frame-mutate-lookup-columns",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _rej_frame_mut_lookup,
    "refinement": "writing back into the field registry (even the same value) is not "
                  "the gold read-only resolution; a patch mutating _meta during query "
                  "compilation is not the fix and would not resolve.",
    "rationale": "rejected by the permission system: lookup holds only "
                 "Acc(list_pred(field_columns), 1/4); the assignment needs full "
                 "permission -> INSUFFICIENT PERMISSION even with a correct value.",
})

# ---------------------------------------------------------------------------
# 7. ADMISSIBILITY — the precondition must admit a normal F2P-shaped input. A
#    same_spec variant can only edit impl regions (no new top-level driver), so we
#    exercise admissibility in place: inside conflict_columns' loop, assert that
#    lookup's full precondition (well-formed registry + name_present(requested[i]))
#    is establishable for the in-domain requested name BEFORE calling lookup. If
#    these asserts cannot be discharged from the caller's own Requires/invariants
#    the modeled call site is unreachable -> PRECOND-TOO-STRONG. The lookup call is
#    kept so the existing proof still closes (a positive admissibility witness).
# ---------------------------------------------------------------------------
_admiss = _swap(
    _BASE,
    "        # the i-th requested name is registered (instantiate the Forall):\n"
    "        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))\n"
    "        # resolve the requested name to a declared field, then take its column.\n"
    "        col = lookup(requested[i], field_names, field_columns)\n",
    "        # the i-th requested name is registered (instantiate the Forall):\n"
    "        Assert(name_present(ToSeq(requested)[i], ToSeq(field_names)))\n"
    "        # ADMISSIBILITY: the lookup precondition (well-formed registry + name\n"
    "        # present) is establishable for this in-domain requested name.\n"
    "        Assert(len(field_columns) == len(field_names))\n"
    "        Assert(name_present(requested[i], ToSeq(field_names)))\n"
    "        # resolve the requested name to a declared field, then take its column.\n"
    "        col = lookup(requested[i], field_names, field_columns)\n",
)
SPEC_TESTS.append({
    "id": "admiss-lookup-precond-establishable",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss,
    "rationale": "the lookup precondition (len match + name_present(requested[i])) is "
                 "derivable from conflict_columns' own Requires/invariants for an "
                 "F2P-shaped in-domain input; if these asserts cannot be discharged the "
                 "precondition is unreachable -> PRECOND-TOO-STRONG. (Kept the call so "
                 "the existing proof still closes.)",
})


# ===========================================================================
# AXIOM TESTS — none consumed. The deep model (column_for/conflict_columns) is an
# A-reference validated against the real Django callees by axiom_check.py (G-AX).
# We re-use that exact host-validated oracle as a containment+soundness probe so
# the battery still exercises the A-reference lane. The probe embeds the bundle's
# axiom_check.py source (read on the HOST at load time — the runner mounts only the
# probe at /work) and runs it in the instance image where Django is importable.
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# Embed the host-read axiom_check.py source as a literal, then execute its main()
# inside the container. Exit code mirrors the oracle (0 iff every obligation holds).
_AX_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__embedded_axiom_check__'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom_check.main() returned', rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)

AXIOM_TESTS = [
    {
        "id": "axref-column-for-equals-real-getfield-column",
        "axiom": "column_for / conflict_columns (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "There is NO consumed @ContractOnly axiom; the only trust point "
                     "is the A-reference deep model column_for == real "
                     "_meta.get_field(name).column. This probe runs the bundle's "
                     "host-validated oracle (axiom_check.py) inside the instance image: "
                     "for every requested-name subset/permutation of two real models "
                     "(one with mixed-case db_column overrides so column != name, one "
                     "without) it asserts the deep model equals the real Django pipeline "
                     "AND that the override slots disagree from the field name (no "
                     "double-mask). Exit 0 iff the deep model is sound on every "
                     "caller-reachable input. A disagreement => the A-reference (hence "
                     "verify=>resolve) is unsound.",
    },
]
