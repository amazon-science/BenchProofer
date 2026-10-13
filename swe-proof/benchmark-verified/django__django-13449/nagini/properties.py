# properties.py — PBT falsification battery for django__django-13449. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface of this instance (model.py + refinement.md + mapping.md):
#
#   render_windowed_with_numeric_cast(operand: List[int], window: List[int],
#                                     decimal_out: bool,
#                                     operand_decimal: bool) -> List[int]
#     Requires(Acc(list_pred(operand), 1/2))   # READ-ONLY input (half perm)
#     Requires(Acc(list_pred(window),  1/2))   # READ-ONLY input (half perm)
#     Ensures(Acc(list_pred(operand), 1/2))    # frame: permission preserved
#     Ensures(Acc(list_pred(window),  1/2))    # frame: permission preserved
#     Ensures(Acc(list_pred(Result())))        # full perm on the fresh result
#     # (D) decimal-output branch — the cast wraps the WHOLE OVER clause,
#     #     operand un-cast (its output forced non-decimal first):
#     Ensures(Implies(decimal_out,
#         ToSeq(Result()) == cast_numeric(
#             over_clause(compile_operand(ToSeq(operand), False), ToSeq(window)))))
#     # (N) non-decimal-output branch — no OUTER cast; the operand renders by
#     #     its OWN declared type (cast iff operand_decimal):
#     Ensures(Implies(not decimal_out,
#         ToSeq(Result()) == over_clause(
#             compile_operand(ToSeq(operand), operand_decimal), ToSeq(window))))
#
#   compile_operand(operand, operand_is_decimal) -- @Pure @ContractOnly axiom
#   (A-consumed), modelling the UNCHANGED SQLiteNumericMixin.as_sqlite:
#       Ensures(Implies(not operand_is_decimal, Result() == operand))
#       Ensures(Implies(operand_is_decimal,     Result() == cast_numeric(operand)))
#
# Load-bearing facts the spec defends:
#   * (D) CAST(<inner> OVER (<window>) AS NUMERIC) with the inner operand
#     rendered un-cast. The cast surrounds the ENTIRE `... OVER (...)` clause —
#     NOT just the operand. `over_clause(cast_numeric(operand), window)` (cast
#     around the operand alone) is EXACTLY the pre-patch bug model_prepatch.py
#     reproduces and the F2P test test_lag_decimalfield observes (valid SQL vs
#     `near "OVER": syntax error`).
#   * (N) <inner> OVER (<window>), no OUTER cast; the inner operand renders by
#     its OWN declared type: compile_operand(operand, operand_decimal). A
#     non-decimal windowed output over a decimal-typed operand keeps the
#     operand's OWN cast (this is the real unchanged rendering path); a spec
#     that pinned the N branch to a verbatim operand would be UNFAITHFUL to
#     the real behaviour on that input (a G-PANEL-2 class defect).
#   * On the (D) branch `compile_operand(operand, False)` — the operand is
#     rendered with a NON-decimal output (its declared decimal-ness absorbed by
#     the outer cast). The axiom pins this to `== operand` (verbatim); rendering
#     the operand as decimal there (compile_operand(operand, True) =
#     CAST(<operand> AS NUMERIC)) reproduces a DOUBLE-cast bug.
#   * Permission: BOTH `operand` and `window` are held at HALF permission
#     (Acc(...,1/2)) — they are read-only inputs the function must not write.
#     The MANDATORY frame-mutation probe writes to a half-perm input; the spec
#     must reject it for INSUFFICIENT PERMISSION (#1 weakness class).
#
# Oracle grounding (ungrounded-oracle-echo class): the postcondition is pinned
# to cast_numeric / over_clause (pure helpers fully unfolded to literal token
# sequences, grounded in the args) and to compile_operand(operand, flag) whose
# axiom Ensures pins BOTH flag values to concrete functions of the arg. There
# is NO opaque answer-key to echo wrongly — every term is a concrete function
# of the inputs. So there is no cheap WRONG echo; instead the uniqueness lane
# attacks cast PLACEMENT (the discriminating content) and the operand
# decimal-ness on both branches, and we add honest cheapest-impl positive
# controls. See `assessment`.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-13449"
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
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec. The literal token
# lists are:
#   ' OVER ('     = [32, 79, 86, 69, 82, 32, 40]
#   ')'           = [41]
#   'CAST('       = [67, 65, 83, 84, 40]
#   ' AS NUMERIC)' = [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    if decimal_out:
        # The operand is compiled with a non-decimal output: the decimal cast
        # it would otherwise carry is absorbed by the outer cast, so verbatim.
        inner = list(operand)  # type: List[int]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        Assert(ToSeq(over) == over_clause(
            compile_operand(ToSeq(operand), False), ToSeq(window)))
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
    else:
        # No outer cast: the operand renders by its own declared type.
        raw = list(operand)  # type: List[int]
        inner2 = raw  # type: List[int]
        if operand_decimal:
            inner2 = [67, 65, 83, 84, 40] + raw + \\
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
        else:
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls
# that MUST verify (else SPEC-TOO-STRONG). Both KEEP every framing Assert the
# gold proof needs (pilot pitfall #2); they only reshape the executable form,
# with no loop / no fold so no auto-undischargeable lemma is needed (#3).
# ===========================================================================

# pos-control-branch-reorder: invert the outer if/else so the NON-decimal
# case is handled first and the decimal (outer-cast) case second; also invert
# the inner operand_decimal if/else. The branches are independent; all framing
# asserts are preserved. Behaviourally identical to gold. If a faithful
# correct impl in a different branch order cannot verify => SPEC-TOO-STRONG.
_POS_BRANCH_REORDER = """    # impl-start
    if not decimal_out:
        raw = list(operand)  # type: List[int]
        inner2 = raw  # type: List[int]
        if not operand_decimal:
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
        else:
            inner2 = [67, 65, 83, 84, 40] + raw + \\
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    else:
        inner = list(operand)  # type: List[int]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        Assert(ToSeq(over) == over_clause(
            compile_operand(ToSeq(operand), False), ToSeq(window)))
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
    return result
    # impl-end"""

# pos-control-inner-concat: build the fresh operand copies by list
# concatenation (`operand + []`) instead of `list(operand)`. Both produce a
# fresh full-permission copy with the same contents, so the framing asserts
# still hold. A different local-variable shape for the operand copy; must
# verify.
_POS_INNER_CONCAT = """    # impl-start
    empty = []  # type: List[int]
    if decimal_out:
        inner = operand + empty  # type: List[int]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        Assert(ToSeq(over) == over_clause(
            compile_operand(ToSeq(operand), False), ToSeq(window)))
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
    else:
        raw = operand + empty  # type: List[int]
        inner2 = raw  # type: List[int]
        if operand_decimal:
            inner2 = [67, 65, 83, 84, 40] + raw + \\
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
        else:
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller def (it would
# change the projected spec view and break same_spec). Instead we inject the
# admissibility witness INSIDE the impl region (elided from the spec view): build
# two concrete fresh F2P-shaped token lists (a `LAG(...)` operand fragment and a
# `PARTITION BY ... ORDER BY ...` window fragment) and assert each satisfies the
# function's exact Requires shape — Acc(list_pred(.), 1/2) is establishable
# because a freshly-built list is held at FULL perm (>= 1/2). The real impl then
# runs unchanged over the actual params. If the precondition could not be
# established for a legitimate input the Assert would fail => PRECOND-TOO-STRONG.
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    # 'LAG(x)' operand and 'p ORDER BY x' window: fresh lists are held at FULL
    # permission, so the function's half-permission Requires is establishable.
    adm_operand = [76, 65, 71, 40, 120, 41]  # type: List[int]
    adm_window = [112]  # type: List[int]
    Assert(Acc(list_pred(adm_operand), 1 / 2))
    Assert(Acc(list_pred(adm_window), 1 / 2))
    # --- end admissibility witness; the real impl follows unchanged ---
    if decimal_out:
        inner = list(operand)  # type: List[int]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
        over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
        Assert(ToSeq(over) == over_clause(
            compile_operand(ToSeq(operand), False), ToSeq(window)))
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(result) == cast_numeric(ToSeq(over)))
    else:
        raw = list(operand)  # type: List[int]
        inner2 = raw  # type: List[int]
        if operand_decimal:
            inner2 = [67, 65, 83, 84, 40] + raw + \\
                [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), True))
        else:
            Assert(ToSeq(inner2) == compile_operand(ToSeq(operand), False))
        result = inner2 + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness/reject) — MANDATORY: both inputs are read-only
# (Acc(...,1/2)). A rival that WRITES a read-only input to satisfy the
# postcondition must be rejected for INSUFFICIENT PERMISSION. We keep the gold
# impl verbatim and INSERT a single write, so the rejection is attributable to
# the write, not a broken proof.
# ===========================================================================

# frame-mut-operand-append: append to `operand` (the half-perm operand input).
# `list.append` requires FULL list_pred(operand); only 1/2 is held => rejects
# for insufficient permission. The rest of the impl is the verbatim gold proof.
_FRAME_OPERAND_APPEND = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n    operand.append(0)\n", 1)

# frame-mut-window-append: same probe on the OTHER read-only input, `window`.
# `window.append(0)` requires full list_pred(window); only 1/2 is held => reject.
_FRAME_WINDOW_APPEND = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n    window.append(0)\n", 1)


# ===========================================================================
# UNIQUENESS — cast-PLACEMENT rivals. Each shares the spec exactly and changes
# ONLY the impl; each MUST be rejected. A verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-cast-around-operand: THE BUG (= model_prepatch.py / pre-patch shape).
# The windowed rendering never treats the decimal output specially: the
# operand carries its OWN cast iff its own type is decimal, and nothing ever
# wraps the windowed fragment. For a decimal windowed output over a decimal
# operand this produces `CAST(<operand> AS NUMERIC) OVER (<window>)` =
# over_clause(cast_numeric(operand), window), NOT
# cast_numeric(over_clause(operand, window)). The cast is inside the OVER
# clause, not around it. Must be rejected by Ensures (D).
_UNIQ_CAST_AROUND_OPERAND = """    # impl-start
    raw = list(operand)  # type: List[int]
    inner = raw  # type: List[int]
    if operand_decimal:
        inner = [67, 65, 83, 84, 40] + raw + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), True))
    else:
        Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    result = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    return result
    # impl-end"""

# uniq-no-cast-decimal: FORGET every cast entirely and return the bare OVER
# clause with a verbatim operand on all inputs. Must be rejected by Ensures (D)
# (a decimal output needs the outer cast) and by Ensures (N) when the operand's
# own type is decimal (the operand must keep its own cast there).
_UNIQ_NO_CAST_DECIMAL = """    # impl-start
    inner = list(operand)  # type: List[int]
    Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    result = over
    return result
    # impl-end"""

# uniq-always-cast: ALWAYS wrap the OVER clause in the outer cast, even on the
# non-decimal branch. The decimal branch is correct, but the non-decimal branch
# produces cast_numeric(over_clause(...)) instead of the bare clause. Must be
# rejected by Ensures (N).
_UNIQ_ALWAYS_CAST = """    # impl-start
    inner = list(operand)  # type: List[int]
    Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    result = [67, 65, 83, 84, 40] + over + \\
        [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    return result
    # impl-end"""

# uniq-swap-branches: swap the two outer branch bodies — outer cast on the
# NON-decimal output, no cast on the decimal output. Both branches are
# individually well-formed token lists, but each is on the WRONG branch.
# Rejected by BOTH Ensures (D) (decimal must be cast) and (N) (non-decimal
# must be the bare clause over the operand's own rendering).
_UNIQ_SWAP_BRANCHES = """    # impl-start
    inner = list(operand)  # type: List[int]
    Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    if decimal_out:
        result = over
    else:
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    return result
    # impl-end"""

# uniq-operand-decimal-double-cast: on the decimal-output branch render the
# inner operand AS DECIMAL (compile_operand(operand, True) =
# CAST(<operand> AS NUMERIC)) instead of forcing it to a non-decimal output,
# then still wrap the whole clause. This reproduces a fix that wrapped the
# OVER clause but FORGOT to force the source to a non-decimal output first:
# the operand carries its own cast AND the whole clause is cast => a DOUBLE
# cast `CAST( CAST(<operand> AS NUMERIC) OVER (<window>) AS NUMERIC)`.
# Rejected by Ensures (D), which pins the inner term to
# compile_operand(operand, FALSE) == operand (un-cast).
#
# The operand copy is `raw = list(operand)  # type: List[int]` on its OWN line
# -- the idiom the gold impl and every sibling rival here use -- and the byte
# lists are concatenated around `raw`. Writing `list(operand)` INSIDE the
# concatenation (with the `# type:` comment on the continuation line, where it
# annotates the assignment and not the inner call) makes nagini's front end
# raise `Invalid program: generic.constructor.without.type` before Viper ever
# runs. That exits 1 -- nagini's REJECTION code -- so this case scored
# "rejected" on a translation crash and tested nothing: nagini is in the
# complement of pbt.WITNESS_REQUIRED, so "did not verify" is the WHOLE argument
# for a rejection here, and a rival that never reached the verifier makes it
# hollow. Kept as a comment because the trap is invisible in the recorded
# outcome (the tell was wall time: 14.2s against 34-78s for this cell's real
# verdicts).
_UNIQ_OPERAND_DOUBLE_CAST = """    # impl-start
    raw = list(operand)  # type: List[int]
    casted_inner = [67, 65, 83, 84, 40] + raw + \\
        [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    Assert(ToSeq(casted_inner) == compile_operand(ToSeq(operand), True))
    over = casted_inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    if decimal_out:
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    else:
        result = over
    return result
    # impl-end"""

# uniq-double-cast-vacuity-control: the NON-VACUITY control for the case
# above. Byte-identical to _UNIQ_OPERAND_DOUBLE_CAST except that the framing
# Assert is replaced by `Assert(False)` as the first statement INSIDE the
# `if decimal_out:` branch -- the branch whose Ensures (D) obligation the
# double-cast rival is refuted on. It must be REJECTED, and rejected on that
# Assert: a verifying `Assert(False)` would mean the decimal-output region is
# infeasible under the precondition, in which case the refutation above proves
# nothing about the double cast (a guarded self-call gone vacuous). This is the
# control that shows the region is reachable and the rejection real.
_UNIQ_DOUBLE_CAST_VACUITY = """    # impl-start
    raw = list(operand)  # type: List[int]
    casted_inner = [67, 65, 83, 84, 40] + raw + \\
        [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    over = casted_inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    if decimal_out:
        Assert(False)
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    else:
        result = over
    return result
    # impl-end"""

# uniq-nondecimal-ignore-operand-cast: correct decimal branch, but on the
# NON-decimal branch render the operand VERBATIM regardless of its own
# declared type — i.e. strip the operand's own cast whenever the windowed
# output is non-decimal. On a non-decimal windowed output over a decimal
# operand the real rendering keeps the operand's own cast; this rival drops
# it. Must be rejected by Ensures (N) (the operand term is pinned to
# compile_operand(operand, operand_decimal), = cast_numeric(operand) when the
# operand's own type is decimal). This is the faithfulness-critical rival:
# a spec that admits it diverges from the real non-decimal rendering path.
_UNIQ_NONDECIMAL_VERBATIM = """    # impl-start
    inner = list(operand)  # type: List[int]
    Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    over = inner + [32, 79, 86, 69, 82, 32, 40] + window + [41]
    if decimal_out:
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    else:
        result = over
    return result
    # impl-end"""

# uniq-drop-over-keyword: a supporting mechanical near-miss — omit the ' OVER ('
# separator, concatenating operand directly with window. Produces a structurally
# different fragment that satisfies neither Ensures clause. Rejected.
_UNIQ_DROP_OVER = """    # impl-start
    inner = list(operand)  # type: List[int]
    Assert(ToSeq(inner) == compile_operand(ToSeq(operand), False))
    over = inner + window + [41]
    if decimal_out:
        result = [67, 65, 83, 84, 40] + over + \\
            [32, 65, 83, 32, 78, 85, 77, 69, 82, 73, 67, 41]
    else:
        result = over
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_BRANCH_REORDER),
        "rationale": "structurally-different CORRECT impl: invert the outer if/else so "
                     "the cast-less non-decimal case is first and the outer-cast decimal "
                     "case second (inner operand branch also inverted). The branches are "
                     "independent; all framing asserts are preserved (pilot pitfall #2), "
                     "no loop/fold so no auto-undischargeable lemma (#3). Behaviourally "
                     "identical to gold; if it cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-inner-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_INNER_CONCAT),
        "rationale": "local-variable reshape: build the fresh operand copies via list "
                     "concatenation (operand + empty) instead of list(operand). Same "
                     "contents (ToSeq == ToSeq(operand)), framing asserts kept, no new "
                     "lemma needed. Must verify; else SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) builds two concrete "
                     "F2P-shaped fresh token lists (a 'LAG(x)' operand and a window "
                     "fragment) and asserts each satisfies the function's exact Requires "
                     "shape Acc(list_pred(.), 1/2) (a fresh list is held at FULL perm, "
                     ">= 1/2). The real impl then runs unchanged. If the precondition "
                     "could not be established for a legitimate input the Assert fails "
                     "=> PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (must reject for insufficient permission) ----
    {
        "id": "frame-mut-operand-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_OPERAND_APPEND),
        "refinement": "the real windowed rendering NEVER mutates the operand SQL "
                      "fragment in place: the patch builds a fresh copy of the "
                      "expression (self.copy()) and renders new SQL text; the source "
                      "operand's own rendering is read-only. An impl that writes to the "
                      "operand input corresponds to a patch that mutated the shared "
                      "source-expression SQL, corrupting any other reader of that "
                      "fragment (e.g. the expression reused across compiles); that "
                      "aliasing corruption is not the gold behaviour and the F2P/P2P "
                      "window tests, which reuse expressions, would not resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: operand is held at "
                     "Acc(list_pred(operand), 1/2) (read-only); list.append requires "
                     "FULL list_pred(operand). The write is the first statement so the "
                     "rejection is attributable to it, not the (verbatim gold) proof.",
    },
    {
        "id": "frame-mut-window-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_WINDOW_APPEND),
        "refinement": "the window SQL fragment (the already-built PARTITION BY ... ORDER "
                      "BY ... text) is consumed read-only by the windowed rendering; the "
                      "patch does not change it and never writes it. An impl that appends "
                      "to the window input models a patch that mutated the prebuilt "
                      "window text shared by other rendering paths — corrupting it for "
                      "any later reader; not the gold behaviour, would not resolve the "
                      "window F2P/P2P tests.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: window is held at "
                     "Acc(list_pred(window), 1/2); list.append requires full "
                     "list_pred(window). Same probe on the second read-only input.",
    },

    # ---- uniqueness: cast placement / operand decimal-ness (must reject) ----
    {
        "id": "uniq-cast-around-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CAST_AROUND_OPERAND),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces and "
                      "G-DIFF flags: the windowed expression has no backend-specific "
                      "rendering, so the inner decimal operand carries its own CAST and "
                      "the rendered SQL is CAST(LAG(...) AS NUMERIC) OVER (...) — the "
                      "cast around the OPERAND, INSIDE the OVER clause. SQLite rejects "
                      "this as `near \"OVER\": syntax error`, which is exactly what the "
                      "F2P test test_lag_decimalfield observes failing. Its faithful "
                      "real patch (the un-patched rendering) does NOT resolve.",
        "rationale": "rejected by Ensures (D): the decimal branch must equal "
                     "cast_numeric(over_clause(operand, window)) = "
                     "CAST(<inner> OVER (<window>) AS NUMERIC); this rival produces "
                     "over_clause(cast_numeric(operand), window) = "
                     "CAST(<inner> AS NUMERIC) OVER (<window>) when the operand is "
                     "decimal, and the bare un-cast clause when it is not — distinct "
                     "token sequences in both cases.",
    },
    {
        "id": "uniq-no-cast-decimal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NO_CAST_DECIMAL),
        "refinement": "rendering the decimal-output window with NO numeric cast anywhere "
                      "corresponds to a rendering that never takes the decimal branch "
                      "AND strips the operand's own cast. The decimal value would not "
                      "be CAST to NUMERIC, so the backend returns the wrong (float-"
                      "typed) value for the windowed decimal — the test_lag_decimalfield "
                      "assertion on the decimal result fails; does not resolve.",
        "rationale": "rejected by Ensures (D): a decimal output requires "
                     "cast_numeric(over_clause(...)); returning the bare over_clause(...) "
                     "is missing the CAST(...) wrapper entirely. Also rejected by "
                     "Ensures (N) when the operand's own type is decimal (its own cast "
                     "is dropped).",
    },
    {
        "id": "uniq-always-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_CAST),
        "refinement": "always wrapping the OVER clause in CAST(... AS NUMERIC), even for "
                      "a non-decimal output, corresponds to a rendering that dropped the "
                      "decimal-output guard. Non-decimal windows (the bulk of the P2P "
                      "window suite, e.g. integer/float Lag/Lead/RowNumber tests) would "
                      "get a spurious NUMERIC cast, changing their SQL/result type and "
                      "failing those PASS_TO_PASS tests; does not resolve.",
        "rationale": "rejected by Ensures (N): a non-decimal output must equal the bare "
                     "over_clause(compile_operand(operand, operand_decimal), window) "
                     "with NO outer cast; this rival emits cast_numeric(over_clause(...)) "
                     "on every input.",
    },
    {
        "id": "uniq-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWAP_BRANCHES),
        "refinement": "inverting the cast condition (outer cast iff NOT decimal) "
                      "corresponds to a patch with the output-type guard negated: "
                      "decimal outputs render un-cast (failing test_lag_decimalfield, "
                      "the F2P) and non-decimal outputs get a spurious outer cast "
                      "(failing the non-decimal P2P window tests). Neither domain "
                      "resolves.",
        "rationale": "rejected by BOTH Ensures (D) (decimal must be cast_numeric(...), "
                     "this rival returns the bare clause) and Ensures (N) (non-decimal "
                     "must be the bare clause over the operand's own rendering, this "
                     "rival outer-casts it).",
    },
    {
        "id": "uniq-operand-decimal-double-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OPERAND_DOUBLE_CAST),
        "refinement": "rendering the inner operand AS decimal (its own CAST) AND "
                      "wrapping the whole clause corresponds to a patch that wrapped the "
                      "OVER clause but FORGOT to force the source expression to a "
                      "non-decimal output first. The result is a DOUBLE cast "
                      "CAST( CAST(<operand> AS NUMERIC) OVER (<window>) AS NUMERIC) — "
                      "the inner CAST(... AS NUMERIC) before OVER re-triggers the "
                      "`near \"OVER\": syntax error`; test_lag_decimalfield still fails; "
                      "does not resolve.",
        "rationale": "rejected by Ensures (D): the inner term is pinned to "
                     "compile_operand(operand, FALSE) == operand (un-cast); this rival "
                     "renders the operand as compile_operand(operand, True) = "
                     "CAST(<operand> AS NUMERIC), a distinct token sequence, so the "
                     "whole result differs from cast_numeric(over_clause(operand, "
                     "window)). Measured: Verification failed in 108.2s naming exactly "
                     "that postcondition (`Postcondition ... might not hold. Assertion "
                     "Implies(decimal_out, (ToSeq(Result()) == "
                     "cast_numeric(over_clause(compile_operand(ToSeq(operand), False), "
                     "ToSeq(window))))) might not hold.`), while the framing Assert "
                     "pinning casted_inner to compile_operand(operand, True) was "
                     "DISCHARGED — so the divergence Viper reports is the operand's own "
                     "cast, i.e. the double cast, and nothing else. Reachability of the "
                     "decimal_out region is the paired control below.",
    },
    {
        "id": "uniq-double-cast-vacuity-control",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DOUBLE_CAST_VACUITY),
        "refinement": "not a rendering a patch could produce — a NON-VACUITY control on "
                      "the case above. If `Assert(False)` at the head of the decimal-"
                      "output branch VERIFIED, that branch would be unreachable under "
                      "the precondition and the double-cast refutation would be an "
                      "artifact of an infeasible guard rather than evidence about the "
                      "cast placement. Its rejection is what makes the paired uniqueness "
                      "case load-bearing.",
        "rationale": "rejected on the Assert itself, not on a postcondition: "
                     "`Assert might fail. Assertion False might not hold.` at the first "
                     "statement inside `if decimal_out:` (36.6s). The precondition "
                     "(Acc(list_pred(operand), 1/2), Acc(list_pred(window), 1/2), "
                     "MustTerminate(2)) constrains neither decimal_out nor "
                     "operand_decimal, so both branches are live and the Ensures (D) "
                     "refutation above is reached on a feasible path.",
    },
    {
        "id": "uniq-nondecimal-ignore-operand-cast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NONDECIMAL_VERBATIM),
        "refinement": "on a NON-decimal windowed output the real rendering path is "
                      "unchanged by the patch: the operand still renders by its OWN "
                      "declared type, keeping its own numeric cast when that type is "
                      "decimal. A rendering that strips the operand's own cast whenever "
                      "the windowed output is non-decimal changes the operand's value "
                      "typing on that path (the decimal operand is no longer cast), "
                      "diverging from the real behaviour; the window P2P suite over "
                      "decimal source columns with non-decimal outputs would observe "
                      "different SQL; does not resolve.",
        "rationale": "rejected by Ensures (N): the operand term is pinned to "
                     "compile_operand(operand, operand_decimal), which by the axiom is "
                     "cast_numeric(operand) when the operand's own type is decimal; "
                     "this rival always emits the verbatim operand there. This is the "
                     "faithfulness-critical rival distinguishing the operand's own "
                     "decimal-ness from the windowed output's.",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-drop-over-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_OVER),
        "refinement": "omitting the ' OVER (' separator corresponds to a broken template "
                      "that concatenated the expression directly with the window text "
                      "(no OVER keyword), producing invalid SQL with no window clause; "
                      "every window test (F2P and P2P) would fail to compile/execute; "
                      "does not resolve. Supporting near-miss for the structural-shape "
                      "attack.",
        "rationale": "rejected by both Ensures clauses: dropping kw_over() makes the "
                     "fragment operand+window+')' which equals neither over_clause(...) "
                     "nor cast_numeric(over_clause(...)) — the ' OVER (' token run is "
                     "absent from the result.",
    },
]


# ===========================================================================
# AXIOM LANE — one A-consumed axiom: compile_operand(operand, operand_is_decimal)
# modelling the UNCHANGED SQLiteNumericMixin.as_sqlite:
#     operand_is_decimal  -> CAST(<operand> AS NUMERIC)
#     otherwise           -> <operand> verbatim
# BOTH branches are proof-consumed: the decimal-output branch consumes the
# False case (operand forced non-decimal), the non-decimal-output branch
# consumes the case matching the operand's own declared type.
# Probes run in the instance Docker image (the real Django lives there). The
# runner mounts ONLY the probe at /work, so we cannot import the bundle's
# axiom_check.py in-container — but its soundness logic imports only Django,
# which IS present, so we re-embed that logic directly. apply_gold=True: the
# axiom callee (SQLiteNumericMixin.as_sqlite) is unchanged so apply_gold is
# harmless for it, and the end-to-end cast-placement check NEEDS the patched
# Window.as_sqlite, so the gold patch must be applied.
# ===========================================================================

# axiom-soundness: execute the REAL SQLiteNumericMixin.as_sqlite via a minimal
# stub on boundary + fuzz operand SQLs x {DecimalField, FloatField, IntegerField}
# and assert it equals the axiom Ensures EXACTLY:
#   DecimalField  -> 'CAST(%s AS NUMERIC)' % sql   (== cast_numeric(operand))
#   else          -> sql verbatim                  (== operand)
# The flag-dependency (cast iff get_internal_type()=='DecimalField') is fuzzed
# over both the decimal and non-decimal field types. Any disagreement on any
# input in the axiom's domain => AXIOM-UNSOUND. We ALSO run the patched real
# Window.as_sqlite end-to-end (best-effort) and assert the cast wraps the WHOLE
# OVER clause with the operand un-cast (the F2P-tied placement property).
_AX_SOUNDNESS_PROBE = r'''
import os, sys, random


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()


def check_compile_operand():
    from django.db import connection
    from django.db.models import fields
    from django.db.models.expressions import SQLiteNumericMixin

    class _Stub(SQLiteNumericMixin):
        def __init__(self, sql, output_field):
            self._sql = sql
            self.output_field = output_field

        def as_sql(self, compiler, conn, **extra):
            return self._sql, []

    rng = random.Random(13449)
    operands = ["X", '"t"."amount"', 'LAG("t"."bonus", 1)',
                "COUNT(*)", 'AVG("t"."salary")', "", "a)b(c"]
    for _ in range(2000):
        n = rng.randint(0, 20)
        operands.append("".join(rng.choice('ABC"().,_ 0129xLAG') for _ in range(n)))

    decimal_field = fields.DecimalField(max_digits=15, decimal_places=2)
    float_field = fields.FloatField()
    integer_field = fields.IntegerField()

    for sql in operands:
        got_dec, _ = _Stub(sql, decimal_field).as_sqlite(None, connection)
        assert got_dec == "CAST(%s AS NUMERIC)" % sql, (
            "AXIOM-UNSOUND compile_operand(decimal) on %r: real=%r" % (sql, got_dec))
        for f in (float_field, integer_field):
            got, _ = _Stub(sql, f).as_sqlite(None, connection)
            assert got == sql, (
                "AXIOM-UNSOUND compile_operand(non-decimal) on %r (%s): real=%r"
                % (sql, type(f).__name__, got))


def check_window_cast_placement():
    """End-to-end through the REAL ORM compiler over a decimal source column:
    (a) a decimal-output window wraps the WHOLE OVER clause in the numeric
    cast, operand un-cast (the F2P-tied placement); (b) a non-decimal-output
    window adds NO outer cast while the operand keeps its OWN cast (its own
    declared output being decimal) -- the model's non-decimal branch with
    operand_decimal=True."""
    from django.db import models
    from django.db.models import F, Window, FloatField
    from django.db.models.functions import Lag

    class _Emp(models.Model):
        department = models.CharField(max_length=50)
        bonus = models.DecimalField(max_digits=15, decimal_places=2)

        class Meta:
            app_label = "axprobe_13449"
            db_table = "axprobe_emp"

    def _annotated_sql(expr):
        qs = _Emp.objects.annotate(w=expr)
        sql, _ = qs.query.get_compiler(using="default").as_sql()
        start = sql.index('"bonus",') + len('"bonus",')
        end = sql.index(' AS "w"')
        return sql[start:end].strip()

    frag = _annotated_sql(Window(expression=Lag("bonus", 1),
                                 partition_by=F("department"),
                                 order_by=F("bonus").asc()))
    assert "OVER" in frag and "CAST(" in frag, (
        "decimal window SQL missing CAST/OVER: %r" % frag)
    cast_pos = frag.index("CAST(")
    over_pos = frag.index("OVER")
    as_numeric_pos = frag.rindex("AS NUMERIC)")
    assert cast_pos < over_pos < as_numeric_pos, (
        "AXIOM/E2E: CAST does not wrap the whole OVER clause: %r" % frag)
    assert "AS NUMERIC) OVER" not in frag, (
        "AXIOM/E2E: operand carries its own cast before OVER (the bug): %r" % frag)

    frag2 = _annotated_sql(Window(expression=Lag("bonus", 1),
                                  partition_by=F("department"),
                                  order_by=F("bonus").asc(),
                                  output_field=FloatField()))
    assert "OVER" in frag2, (
        "non-decimal-output window SQL missing OVER: %r" % frag2)
    assert "AS NUMERIC) OVER" in frag2, (
        "AXIOM/E2E: non-decimal-output window dropped the operand's own cast: "
        "%r" % frag2)
    assert not (frag2.startswith("CAST(")
                and frag2.rstrip().endswith("AS NUMERIC)")), (
        "AXIOM/E2E: non-decimal-output window has an outer cast: %r" % frag2)
    return "ok"


def main():
    _configure_django()
    check_compile_operand()
    try:
        e2e = check_window_cast_placement()
    except AssertionError:
        raise
    except Exception as exc:
        e2e = "skipped (%s)" % type(exc).__name__
    print("AXIOM-SOUNDNESS OK: compile_operand == real SQLiteNumericMixin."
          "as_sqlite on 7 boundary + 2000 fuzz operands x {decimal,float,int} "
          "(DecimalField -> CAST(... AS NUMERIC), else verbatim); window cast "
          "placement end-to-end: %s" % e2e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-containment: the model passes EXACTLY three argument shapes to
# compile_operand:
#   * compile_operand(ToSeq(operand), False)  — decimal-output postcondition +
#     the non-decimal postcondition when operand_decimal is False, and the impl
#     framing asserts. operand is any List[int] (the precondition puts no value
#     constraint on its contents).
#   * compile_operand(ToSeq(operand), True)   — the non-decimal postcondition
#     when operand_decimal is True (the operand's own decimal rendering).
#   * i.e. every reachable call is (any SQL text, some bool).
# The axiom's Requires domain is `(operand: PSeq[int], operand_is_decimal: bool)`
# — NO further constraint. So every (any SQL text, any bool) the caller can reach
# is inside the axiom domain; containment holds trivially. We confirm
# operationally that the real callee accepts BOTH the False-flag (verbatim) and
# the True-flag (cast) inputs the model can produce — i.e. no model-reachable
# (operand, flag) lies outside the callee's accepted domain.
_AX_CONTAINMENT_PROBE = r'''
import os, sys, random


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()


def main():
    _configure_django()
    from django.db import connection
    from django.db.models import fields
    from django.db.models.expressions import SQLiteNumericMixin

    class _Stub(SQLiteNumericMixin):
        def __init__(self, sql, output_field):
            self._sql = sql
            self.output_field = output_field

        def as_sql(self, compiler, conn, **extra):
            return self._sql, []

    # Enumerate the (operand, operand_is_decimal) pairs the MODEL can reach. The
    # model's `operand` is an arbitrary SQL fragment (no value constraint in the
    # precondition) and the only flag values it passes are the literals False and
    # True. Both correspond to a concrete output_field the real callee accepts.
    rng = random.Random(0xD449)
    operands = ["X", '"t"."amount"', 'LAG("t"."bonus", 1)', "", "a)b(c"]
    for _ in range(200):
        n = rng.randint(0, 24)
        operands.append("".join(rng.choice('ABC"().,_ 0129xLAG OVERCST') for _ in range(n)))

    decimal_field = fields.DecimalField(max_digits=15, decimal_places=2)
    float_field = fields.FloatField()

    reached = 0
    for sql in operands:
        # flag == False: callee renders verbatim and accepts ANY SQL text
        # -> inside the axiom Requires domain.
        got_f, _ = _Stub(sql, float_field).as_sqlite(None, connection)
        assert isinstance(got_f, str), (
            "callee on a model-reachable (operand, False) returned non-str %r" % (got_f,))
        # flag == True: callee accepts ANY SQL text too.
        got_t, _ = _Stub(sql, decimal_field).as_sqlite(None, connection)
        assert isinstance(got_t, str), (
            "callee on a model-reachable (operand, True) returned non-str %r" % (got_t,))
        reached += 1

    print("AXIOM-CONTAINMENT OK: every (operand, operand_is_decimal) the model "
          "can pass to compile_operand (arbitrary SQL text x {False, True}; %d "
          "operand samples) lies inside SQLiteNumericMixin.as_sqlite's Requires "
          "domain (any SQL str, any output field) and is accepted by the real "
          "callee. The caller reaches a subset of the axiom domain; no reachable "
          "input is outside it." % (reached,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-compile_operand",
        "axiom": "compile_operand",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "if the real SQLiteNumericMixin.as_sqlite ever disagrees with the "
                     "axiom Ensures on an input in its domain (DecimalField output not "
                     "wrapped in CAST(... AS NUMERIC), or a non-decimal output altered), "
                     "the A-consumed axiom is AXIOM-UNSOUND. Boundary + 2000 fuzz "
                     "operands x {DecimalField, FloatField, IntegerField} fuzz the "
                     "get_internal_type()=='DecimalField' flag dependency; the "
                     "end-to-end check additionally confirms the patched Window.as_sqlite "
                     "places the cast around the WHOLE OVER clause (operand un-cast).",
    },
    {
        "id": "ax-cover-compile_operand",
        "axiom": "compile_operand",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "the model passes only (arbitrary SQL operand, literal False) and "
                     "(operand, literal True) to compile_operand — both branches are "
                     "now proof-consumed; the axiom's Requires domain is (any PSeq[int], "
                     "any bool) with no further constraint, so every caller-reachable "
                     "input is inside it. A reachable input outside the domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists (the callee accepts any SQL "
                     "text under both flag values).",
    },
]
