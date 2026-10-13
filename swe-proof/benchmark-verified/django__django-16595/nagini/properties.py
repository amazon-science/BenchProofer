# properties.py — PBT falsification battery for django__django-16595. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface of this instance (read model.py + refinement.md + mapping.md)
# ---------------------------------------------------------------------------
#   reduce(this: MigrationStep, nxt: MigrationStep,
#          nxt_references_altered_field: bool)
#       -> Tuple[Optional[List[MigrationStep]], bool]
#
#   Pre-conditions (READ-ONLY inputs, both held at 1/2 permission — NOT writable):
#     Requires(Acc(this.kind,1/2) and Acc(this.model_name_lower,1/2)
#              and Acc(this.name_lower,1/2) and Acc(this.has_explicit_column,1/2)
#              and Acc(this.elidable,1/2))
#     Requires(Acc(nxt.kind,1/2) and Acc(nxt.model_name_lower,1/2)
#              and Acc(nxt.name_lower,1/2) and Acc(nxt.elidable,1/2))
#     Requires(Implies(nxt.kind == KIND_RENAME, Acc(nxt.new_name_lower,1/2)))
#     Requires(this.kind == KIND_ALTER)          # the method is AlterField.reduce
#
#   PARTIALITY OF THE CARRIER (load-bearing, and the reason the frame is not one
#   flat conjunction): a NEW NAME is a facet only a RENAMING step carries. The
#   later step's new name is therefore lent CONDITIONALLY — read permission on
#   `nxt.new_name_lower` is held only under `nxt.kind == KIND_RENAME` — and the
#   altering step is lent no new name at all (there is no
#   Acc(this.new_name_lower) conjunct). An impl that consults the later step's
#   new name BEFORE establishing that the step is a rename is rejected for
#   INSUFFICIENT PERMISSION, which is the only way this model can observe that
#   in the real program such a read is not a value but a failure. The
#   corresponding Ensures hands the facet back on exactly the condition it was
#   lent, so the caller's frame is unchanged.
#   THE SAME CONDITION GOVERNS A STEP THE REDUCTION *BUILDS*, and this is the
#   half that a G-EQ audit broke: MigrationStep.__init__'s Ensures grants
#     Implies(kind == KIND_RENAME,
#             Acc(self.new_name_lower) and self.new_name_lower == new_name_lower)
#   so a step built as an ALTERATION hands its builder no new name to read back
#   either. The carried step of P5 is such a step, so P5 pins every facet it
#   carries but says nothing about a new name and grants the caller no access to
#   one — `AlterField` defines no `new_name` at all, so an impl that names the
#   step it returns by reading that slot off the step it just built verifies
#   under a total grant while its faithful refinement raises AttributeError
#   (see uniq-read-back-carried-name / uniq-eager-built-name).
#   A SECOND FACET IS PARTIAL FOR THE SAME REASON, and this is the half a later
#   G-EQ audit broke once the new name was closed: whether an EXPLICIT STORED
#   COLUMN is pinned is a facet of the FIELD DEFINITION a step carries, not of
#   the step, so only a step of a kind that carries a definition has one.
#   MigrationStep.__init__'s Ensures therefore grants
#     Implies(kind == KIND_ALTER or kind == KIND_REMOVE,
#             Acc(self.has_explicit_column)
#             and self.has_explicit_column == has_explicit_column)
#   — an ALTERATION is built from a definition and a REMOVAL may be given one,
#   while a RENAME is two names and no definition and a step of some other kind
#   need not carry one. The later step is lent this facet not at all (there is no
#   Acc(nxt.has_explicit_column) conjunct), so the reduction reads only its own.
#   Under a total grant an impl could build a renaming (or other) step and read
#   its column status back; refined faithfully that raises, since RenameField
#   stores field=None and a bare Operation has no `field` at all (see
#   uniq-rename-probe-column / uniq-guard-rename-probe-column /
#   uniq-other-probe-column, and pos-remove-probe-column for the boundary).
#   NOTE for anyone editing the battery: the reads of `nxt.new_name_lower` in
#   the positive controls and in the carried-step construction are all under a
#   rename guard already; a case that hoists such a read above the guard is a
#   REJECT case (see uniq-eager-new-name), not a broken variant. Likewise a case
#   that reads `new_name_lower` off a step the impl region BUILT with a kind
#   other than KIND_RENAME, or `has_explicit_column` off one BUILT with a kind
#   other than KIND_ALTER / KIND_REMOVE, is a REJECT case, not a broken variant.
#
#   Post-conditions (the load-bearing clauses, in order):
#     (P0) frame: the same 1/2 permissions on this/nxt are returned unchanged.
#     (P1) Implies(Result() is not None, Acc(list_pred(Result())))   # ownership
#     (P2) Implies(nxt.kind == KIND_REMOVE and is_same_field(this,nxt),
#                  Result()!=None and len==1 and Result()[0] is nxt)   # REMOVE collapse
#     (P3) Implies(nxt.kind == KIND_ALTER  and is_same_field(this,nxt),
#                  Result()!=None and len==1 and Result()[0] is nxt)   # THE CHANGE
#     (P4) Implies((ALTER or REMOVE) and is_same_field, singleton [nxt])  # symmetry
#     (P5) Implies(nxt.kind == KIND_RENAME and is_same_field(this,nxt)
#                  and not this.has_explicit_column,
#                  Result()!=None and len==2 and Result()[0] is nxt
#                  and Result()[1] is not nxt and Result()[1] is not this
#                  and Result()[1].kind == KIND_ALTER
#                  and Result()[1].model_name_lower == this.model_name_lower
#                  and Result()[1].name_lower == nxt.new_name_lower
#                  and Result()[1].has_explicit_column
#                      == this.has_explicit_column
#                  and not Result()[1].elidable)          # rename carry-across
#          (the carried step's CONTENT is pinned: it must be an ALTER of the
#          same model targeting the renamed field with the original field
#          definition, carrying no elidable mark — an arbitrary distinct second
#          step no longer verifies. It is a step the reduction BUILDS, so it is
#          neither of the two it was handed: `is not nxt` AND `is not this`. It
#          is an ALTERATION, so a new name is not among the facets it carries;
#          nothing is pinned about that slot and no access to it is handed out,
#          which is what stops an impl from naming its result by reading a slot
#          the real carried operation does not define.)
#     (P6) Implies(not joined_by_field_rule(this,nxt) and this.elidable,
#                  singleton [nxt])              # elidable EARLIER step elides
#     (P7) Implies(not joined_by_field_rule(this,nxt)
#                  and not this.elidable and nxt.elidable,
#                  singleton [this])              # elidable LATER step elides
#     (P8) Implies(not joined_by_field_rule(this,nxt)
#                  and not this.elidable and not nxt.elidable, Result() is None)
#     (P9) Implies(not is_same_field(this,nxt)
#                  and not this.elidable and not nxt.elidable, Result() is None)
#          (different-field corollary of P8: no same-field rule can fire, so with
#          neither elidable mark set the pair is not combined here)
#
#   P6/P7/P8 pin the generic fall-through the same-field rules do not resolve.
#   It is a TRI-STATE keyed on the two steps' elidable marks with the EARLIER
#   step's mark taking precedence, so a rival that swaps the precedence, or that
#   reports "not combined" for an elidable pair, is caught (see the
#   uniq-elidable-* cases).
#
#   is_same_field and joined_by_field_rule are @Pure helpers FULLY GROUNDED in
#   the inputs:
#     is_same_field: this.model_name_lower == other.model_name_lower
#                    and this.name_lower == other.name_lower
#     joined_by_field_rule: is_same_field(this,nxt) and (nxt.kind in
#                    {ALTER, REMOVE} or (nxt.kind == RENAME and not
#                    this.has_explicit_column))
#   Both are unfolded by the verifier into reads of the inputs; neither is an
#   opaque @ContractOnly answer-key. So there is no "ungrounded-oracle echo"
#   wrong value an impl could return to fool a value-pin: the cheapest way to
#   satisfy P2/P3/P4 (singleton [nxt]) is to literally return [nxt]. The honest
#   cheapest-impl positive control stands in for the ungrounded-oracle lane (see
#   `assessment`). There are NO @ContractOnly axioms / A-reference deep models in
#   this bundle (meta.axioms == []), so AXIOM_TESTS == [].
#
# ---------------------------------------------------------------------------
# Attack plan (adversarial, per applicable weakness class)
# ---------------------------------------------------------------------------
#   FRAME-MUTATION (MANDATORY: both inputs are read-only at 1/2):
#     overwrite this.kind / nxt.kind to satisfy a clause vacuously. MUST reject
#     for INSUFFICIENT PERMISSION (only 1/2 held; a write needs full Acc).
#   PARTIAL-DOMAIN / uniqueness (the verify-but-not-resolve hunt):
#     * revert the changed guard to REMOVE-only      -> fails P3 (== model_prepatch, the bug)
#     * collapse ALTER but drop REMOVE                -> fails P2 ("RemoveField absorbs AlterField")
#     * drop the rename carry-across (return None)    -> fails P5 ("RenameField to other side")
#     * rename collapses to [nxt] only (lose carry)   -> fails P5 (len must be 2)
#     * collapse on a DIFFERENT field too             -> fails P9 (must be None)
#     * drop the elidable fall-through arms           -> fails P6/P7 (elidable pair must collapse)
#     * swap the elidable precedence                  -> fails P6 (earlier mark wins)
#     * elide on the WRONG side of an elidable later step -> fails P7 ([this], not [nxt])
#   CONTROL-FLOW / value-double-mask:
#     * rename returns [nxt, nxt] (carry IS nxt)       -> fails P5 (Result()[1] is not nxt)
#     * carried step marked elidable                   -> fails P5 (not Result()[1].elidable)
#   NON-TERMINATION (the precondition carries MustTerminate(6), so the spec is a
#   TOTAL-correctness statement and a verifying impl must RETURN):
#     * unconditional self-call (unbounded recursion) -> obligation leak on the callee
#     * unbounded loop ahead of the gold body         -> obligation leak on the loop
#   POSITIVE CONTROLS (must verify; else SPEC-TOO-STRONG):
#     * branch-reorder (rename branch first; kinds mutually exclusive)
#     * local-variable reshape (hoist is_same_field into a bound bool)
#     * the elidable arms written as a nested if/else instead of two elifs
#   ADMISSIBILITY (must verify; else PRECOND-TOO-STRONG):
#     * an F2P-shaped witness (two same-field KIND_ALTER steps) built inside the
#       impl region and asserted to satisfy the function's exact Requires — the
#       conjuncts are asserted directly rather than probed by a self-call (see
#       the NOTE on the admissibility case).
from pathlib import Path

INSTANCE = "django__django-16595"
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
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls
# that MUST verify (else SPEC-TOO-STRONG). No loop / no fold, so no induction
# lemma is needed (pilot pitfalls #2/#3 avoided); the result is identical to
# gold on every input so every postcondition clause still discharges.
# ===========================================================================

# pos-reorder: handle the RENAME branch FIRST, then the ALTER/REMOVE branch.
# A step's kind is a single tag, so RENAME / ALTER / REMOVE are mutually
# exclusive — testing rename first cannot change which arm fires for any input.
# Identical result; only the branch ORDER differs. The elidable arms stay last
# (they are only reached when no same-field rule applies).
_POS_REORDER = """    # impl-start
    if nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# pos-hoist: local-variable reshape. Bind the same-field test into a bool once
# and reuse it; split the (ALTER or REMOVE) disjunction into the same guard.
# Same control flow, same returns; only the variable shape differs.
_POS_HOIST = """    # impl-start
    same = is_same_field(this, nxt)  # type: bool
    if same and (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif same and nxt.kind == KIND_RENAME and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# pos-elidable-nested: the two elidable arms written as a NESTED if/else inside
# a single "no same-field rule fired" tail instead of two flat elifs. Same
# tri-state, same precedence (earlier mark first), identical result.
_POS_ELIDABLE_NESTED = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    else:
        if this.elidable:
            res3 = [nxt]  # type: List[MigrationStep]
            return res3, False
        else:
            if nxt.elidable:
                res4 = [this]  # type: List[MigrationStep]
                return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller function (a
# new module-level def changes the projected spec view and breaks same_spec).
# Instead we inject the witness INSIDE the impl region (elided from the spec
# view): build the exact F2P shape — two same-field KIND_ALTER steps (Foo.name,
# Foo.name) mirroring migrations.AlterField("Foo","name",...) twice — and assert
# they satisfy the function's exact Requires (the constructor's Ensures give the
# field accesses; this0.kind == KIND_ALTER is the third Requires). A second
# witness pins the OTHER admissible shape the fall-through reaches: an unrelated
# later step carrying the elidable mark. The real impl then runs unchanged over
# the actual params. If the precondition could not be established for these
# legitimate inputs, an Assert fails => PRECOND-TOO-STRONG.
#
# NOTE on the shape. The witness ASSERTS the Requires conjuncts; it deliberately
# does NOT probe them by calling reduce on the constructed pair. The precondition
# carries a termination obligation, and MustTerminate levels are per-method
# CONSTANTS admitted only strictly BELOW the caller's level, so an unguarded
# self-call is unbounded recursion that no level can discharge (it is pinned as
# the `uniq-diverging-self-call` reject case below). A self-call probe would
# therefore conflate two claims: "a caller can establish the precondition for a
# normal input" (true, and the only thing admissibility must test) with "the
# method may call itself unboundedly" (false). Asserting the conjuncts tests the
# former alone. Verified NON-VACUOUS: splicing `Assert(False)` after the witness
# Asserts FAILS to verify, so the probe path is reachable and the Asserts prove
# real facts rather than passing under an infeasible path condition.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    this0 = MigrationStep(KIND_ALTER, 7, 11, 11, False, False)
    nxt0 = MigrationStep(KIND_ALTER, 7, 11, 11, False, False)
    # the function's Requires is establishable for this concrete pair:
    Assert(Acc(this0.kind, 1 / 2) and Acc(this0.model_name_lower, 1 / 2)
           and Acc(this0.name_lower, 1 / 2) and Acc(this0.has_explicit_column, 1 / 2)
           and Acc(this0.elidable, 1 / 2))
    Assert(Acc(nxt0.kind, 1 / 2) and Acc(nxt0.model_name_lower, 1 / 2)
           and Acc(nxt0.name_lower, 1 / 2) and Acc(nxt0.elidable, 1 / 2))
    Assert(Implies(nxt0.kind == KIND_RENAME, Acc(nxt0.new_name_lower, 1 / 2)))
    Assert(this0.kind == KIND_ALTER)
    # and is_same_field holds for the same-field pair (the F2P alter-then-alter):
    Assert(is_same_field(this0, nxt0))
    Assert(joined_by_field_rule(this0, nxt0))
    # a second admissible shape: an unrelated later step bearing the elidable
    # mark, which no same-field rule resolves (the generic fall-through).
    elid = MigrationStep(KIND_OTHER, 99, 88, 88, False, True)
    Assert(Acc(elid.kind, 1 / 2) and Acc(elid.model_name_lower, 1 / 2)
           and Acc(elid.name_lower, 1 / 2) and Acc(elid.elidable, 1 / 2))
    Assert(Implies(elid.kind == KIND_RENAME, Acc(elid.new_name_lower, 1 / 2)))
    Assert(not joined_by_field_rule(this0, elid) and elid.elidable)
    # a third admissible shape, and the one that makes the CONDITIONAL lending of
    # the new-name facet non-vacuous rather than trivially true: a later step
    # that IS a rename, so the antecedent holds and the facet is genuinely
    # required and genuinely held (the rename carry-across arm).
    ren = MigrationStep(KIND_RENAME, 7, 11, 12, False, False)
    Assert(Acc(ren.kind, 1 / 2) and Acc(ren.model_name_lower, 1 / 2)
           and Acc(ren.name_lower, 1 / 2) and Acc(ren.elidable, 1 / 2))
    Assert(ren.kind == KIND_RENAME)
    Assert(Implies(ren.kind == KIND_RENAME, Acc(ren.new_name_lower, 1 / 2)))
    Assert(Acc(ren.new_name_lower, 1 / 2) and ren.new_name_lower == 12)
    Assert(joined_by_field_rule(this0, ren))
    # --- end admissibility witness; the real impl follows unchanged ---
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (MANDATORY: both inputs are read-only at Acc(...,1/2)).
# A rival that WRITES to a read-only input to satisfy a postcondition vacuously
# MUST be rejected for INSUFFICIENT PERMISSION. The gold body is kept verbatim
# after the write, so the rejection is attributable to the write, not to a
# broken proof obligation. (A byte-fuzzer never thinks to mutate the input.)
# ===========================================================================

# frame-write-this: overwrite this.kind (held at 1/2). A real patch would never
# mutate the operation being reduced; this is the canonical read-only violation.
_FRAME_WRITE_THIS = """    # impl-start
    this.kind = KIND_OTHER
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# frame-write-nxt: overwrite nxt.kind (held at 1/2). Forcing the follow-up step
# into KIND_ALTER would let an impl claim the collapse vacuously by rewriting the
# input rather than reading it; rejected for insufficient permission on nxt.kind.
_FRAME_WRITE_NXT = """    # impl-start
    nxt.kind = KIND_ALTER
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# frame-write-elidable: overwrite nxt.elidable (held at 1/2). Setting the later
# step's elidable mark would let an impl claim the P7 collapse for ANY pair by
# editing the input instead of reading its mark.
_FRAME_WRITE_ELIDABLE = """    # impl-start
    nxt.elidable = True
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN / CONTROL-FLOW — rivals that share the spec
# exactly and change ONLY the impl. Each MUST be rejected; a verifying rival is
# a real verify-but-not-resolve break (SPEC-TOO-WEAK). Every case carries the
# refinement argument that its faithful real patch would NOT resolve the F2P/P2P.
# ===========================================================================

# uniq-revert-remove-only: THE BUG. Revert the changed guard to KIND_REMOVE only
# (== model_prepatch.py / the pre-patch isinstance(operation, RemoveField)). The
# alter-then-alter pair falls through to the elidable tri-state, which returns
# None for the ordinary (non-elidable) pair instead of [nxt].
_UNIQ_REVERT_REMOVE_ONLY = """    # impl-start
    if nxt.kind == KIND_REMOVE and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-alter-only-drop-remove: the dual partial-domain miss — collapse ALTER
# (the change) but DROP the unchanged REMOVE case. A same-field RemoveField now
# falls through to the elidable tri-state instead of collapsing to [nxt].
_UNIQ_ALTER_ONLY = """    # impl-start
    if nxt.kind == KIND_ALTER and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-drop-rename: drop the rename carry-across entirely — a same-field RENAME
# with no pinned column now falls through to the elidable tri-state instead of
# yielding [nxt, carried].
_UNIQ_DROP_RENAME = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-rename-singleton: rename collapses to [nxt] only, losing the carried
# AlterField (len 1 instead of 2). The renamed field's alteration is dropped.
_UNIQ_RENAME_SINGLETON = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        res2 = [nxt]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-rename-carry-is-nxt: control-flow / value-double-mask. The rename branch
# returns [nxt, nxt] — len 2 (so it sneaks past a naive length check) but the
# carried element IS nxt rather than a fresh equivalent AlterField. The spec
# pins Result()[1] is not nxt, so this is caught.
_UNIQ_RENAME_CARRY_IS_NXT = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        res2 = [nxt, nxt]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-carry-marked-elidable: the carried alteration is built with the elidable
# mark SET. It has the right kind/model/name, so every other facet of P5 is
# satisfied, but a carried step marked elidable would be dropped by a later
# reduction — the alteration silently vanishes.
_UNIQ_CARRY_ELIDABLE = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, True)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-collapse-different-field: collapse the pair WITHOUT the same-field guard
# on the ALTER/REMOVE arm — a follow-up ALTER/REMOVE on a DIFFERENT field/model
# now wrongly returns [nxt]. The spec pins Result() is None for a different-field
# pair with neither elidable mark set.
_UNIQ_DIFFERENT_FIELD = """    # impl-start
    if nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE:
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-drop-elidable: drop the generic fall-through's elidable tri-state and
# report "not combined" for every pair no same-field rule resolves. An elidable
# step is then never elided.
_UNIQ_DROP_ELIDABLE = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-elidable-precedence-swapped: test the LATER step's elidable mark before
# the earlier step's. Both marks set is the discriminating input: the earlier
# mark must win ([nxt]), this yields [this].
_UNIQ_ELIDABLE_SWAPPED = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif nxt.elidable:
        res4 = [this]  # type: List[MigrationStep]
        return res4, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-elidable-wrong-side: keep both arms but elide the WRONG step — an
# elidable later step leaves [nxt] (the elidable step itself) instead of [this].
# Length and shape are right, so only the identity pin catches it.
_UNIQ_ELIDABLE_WRONG_SIDE = """    # impl-start
    if (nxt.kind == KIND_ALTER or nxt.kind == KIND_REMOVE) \\
            and is_same_field(this, nxt):
        res = [nxt]  # type: List[MigrationStep]
        return res, False
    elif nxt.kind == KIND_RENAME and is_same_field(this, nxt) \\
            and not this.has_explicit_column:
        carried = MigrationStep(KIND_ALTER, this.model_name_lower,
                                nxt.new_name_lower, nxt.new_name_lower,
                                this.has_explicit_column, False)
        res2 = [nxt, carried]  # type: List[MigrationStep]
        return res2, False
    elif this.elidable:
        res3 = [nxt]  # type: List[MigrationStep]
        return res3, False
    elif nxt.elidable:
        res4 = [nxt]  # type: List[MigrationStep]
        return res4, False
    return None, not nxt_references_altered_field
    # impl-end"""

# uniq-always-none: the trivial fall-through-only impl (never collapses). Cheap
# supporting near-miss: fails every collapse clause (P2/P3/P4/P5/P6/P7) at once.
_UNIQ_ALWAYS_NONE = """    # impl-start
    return None, not nxt_references_altered_field
    # impl-end"""


# ===========================================================================
# NON-TERMINATION — the divergence channel. reduce's precondition carries
# Requires(MustTerminate(6)), so the spec states TOTAL correctness: an impl that
# verifies must RETURN. Without that obligation every Ensures would be claimed
# only of runs that REACH the return, so an impl that never returns would satisfy
# P1-P9 vacuously — MEASURED on both rivals below: with the obligation removed
# from the pre-conditions region each of them VERIFIES; with it present each is
# rejected. The rejection comes from the OBLIGATION SYSTEM, not from any
# postcondition, which is exactly why no test over returned values could close
# this channel: there are no returned values to test.
# ===========================================================================

# uniq-diverging-self-call: hand the pair straight back to reduce, with no guard
# and no base case. MustTerminate levels are per-method CONSTANTS and a call is
# admitted only strictly BELOW its caller's level, so a self-call can never
# discharge the obligation its caller holds ("Obligation leak check failed.
# Callee reduce might not take all unsatisfied obligations from the caller.").
_UNIQ_DIVERGING_SELF_CALL = """    # impl-start
    return reduce(this, nxt, True)
    # impl-end"""

# uniq-diverging-loop: the second divergence channel. The gold body is kept
# verbatim but is preceded by an unbounded counting loop, so every clause is
# established of a return the method never reaches. A loop must carry its own
# MustTerminate invariant to take the obligation its context holds; this one
# carries only Invariant(spin >= 0) ("Obligation leak check failed. Loop might
# not take all unsatisfied obligations from the context.").
_UNIQ_DIVERGING_LOOP = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n"
    "    spin = 0\n"
    "    while spin >= 0:\n"
    "        Invariant(spin >= 0)\n"
    "        spin = spin + 1\n", 1)


# frame-write-nxt-new-name: overwrite nxt.new_name_lower (held at 1/2). The
# rename's target name is the caller's data; writing it would let the routine
# choose what the field gets renamed to and then carry the alteration across to
# a name of its own invention.
_FRAME_WRITE_NEW_NAME = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n    nxt.new_name_lower = this.name_lower\n", 1)


# ---------------------------------------------------------------------------
# The reordering verdict — the answer the pair gets when it is NOT combined
# here. It is a decision about the two steps, not a constant, so an impl that
# hard-codes it is wrong on half the domain while looking right on the other
# half. All three rivals below keep the gold collapse arms VERBATIM, so they
# still collapse the same-field alter-then-alter pair and still pass a test
# that only observes that collapse; they differ from gold only on pairs the
# same-field rules leave alone.
# ---------------------------------------------------------------------------

# uniq-verdict-always-withheld: never grant permission to reorder. Correct
# exactly where the later step DOES reference the altered field, wrong wherever
# it does not.
_UNIQ_VERDICT_FALSE = _IMPL_OLD.replace(
    "    return None, not nxt_references_altered_field",
    "    return None, False", 1)

# uniq-verdict-always-granted: always grant it. The mirror image: correct
# exactly where the later step does NOT reference the altered field.
_UNIQ_VERDICT_TRUE = _IMPL_OLD.replace(
    "    return None, not nxt_references_altered_field",
    "    return None, True", 1)

# uniq-verdict-inverted: read the right input and invert it — granted exactly
# when it must be withheld. Shape-identical to gold, so only the verdict clause
# can catch it.
_UNIQ_VERDICT_INVERTED = _IMPL_OLD.replace(
    "    return None, not nxt_references_altered_field",
    "    return None, nxt_references_altered_field", 1)

# uniq-verdict-echo: an ungrounded-oracle echo. Derive the verdict from the
# arguments' own shape (the kind tags and the same-field test) instead of from
# the later step's report of whether it references the altered field. It
# coincides with gold on the pairs the boundary grid hits most often — a
# same-field follow-up does reference the field, a different-model one does not
# — yet it is a guess reconstructed from the wrong inputs rather than the
# answer, and it diverges wherever a step references the altered field without
# naming it (a step on the same model that reaches the field indirectly) or
# names it without referencing it.
_UNIQ_VERDICT_ECHO = _IMPL_OLD.replace(
    "    return None, not nxt_references_altered_field",
    "    return None, not is_same_field(this, nxt)", 1)


# uniq-carried-name-kept-old: build the carry-across step against the field's
# OLD name instead of the name it was renamed to. The pair still reduces to two
# steps in the right order, so only the carried step's pinned NAME can catch it;
# an alteration aimed at a name that no longer exists after the rename would be
# applied to nothing. (This edits the step's `name_lower` — the slot P5 pins and
# the slot the real carried operation actually has. An earlier revision of this
# case edited the carrier's `new_name_lower` instead, which the real carried
# operation does not define at all, so its refinement was byte-identical to gold
# and it was rejected by a pin no repository behaviour backed. Measured on the
# patched worktree: the version below FAILS
# migrations.test_optimizer.OptimizerTests.test_alter_field_rename_field —
# "Lists differ: ... name='nom' ... != ... name='name' ..." — 38 tests, 1
# failure, while gold is 38/38 OK.)
_UNIQ_CARRIED_NAME_OLD = _IMPL_OLD.replace(
    "                                nxt.new_name_lower, nxt.new_name_lower,",
    "                                this.name_lower, this.name_lower,", 1)


# ---------------------------------------------------------------------------
# The PARTIAL carrier, one level over: a step the reduction BUILDS. Building an
# ALTERING step grants no new name to read back (MigrationStep.__init__ ensures
# that slot only under `kind == KIND_RENAME`), because the real carried
# operation is an `AlterField` and defines no `new_name` at all. Both rivals
# below return EXACTLY gold's values on every input, so no value clause can
# separate them; only the resource discipline on the BUILT step can.
# ---------------------------------------------------------------------------

# uniq-read-back-carried-name: build the carried step, then read its new-name
# slot back to name the step actually returned. Load-bearing and the sharpest
# case in the family, because the value read back is the value just written, so
# the returned pair is gold's pair facet-for-facet.
_UNIQ_READ_BACK_CARRIED_NAME = _IMPL_OLD.replace(
    "        res2 = [nxt, carried]  # type: List[MigrationStep]",
    "        echo = MigrationStep(KIND_ALTER, this.model_name_lower,\n"
    "                             carried.new_name_lower,\n"
    "                             carried.new_name_lower,\n"
    "                             this.has_explicit_column, False)\n"
    "        res2 = [nxt, echo]  # type: List[MigrationStep]", 1)

# uniq-eager-built-name: the isolation case for the same defect. Build a throw-
# away ALTERING step at the top of the body purely to read its new-name slot,
# then run gold's body VERBATIM. Nothing about the result changes, so the
# rejection is attributable solely to the read off a built alteration.
_UNIQ_EAGER_BUILT_NAME = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n"
    "    probe = MigrationStep(KIND_ALTER, this.model_name_lower,\n"
    "                          this.name_lower, this.name_lower,\n"
    "                          this.has_explicit_column, False)\n"
    "    built_name = probe.new_name_lower\n", 1)


# ---------------------------------------------------------------------------
# The PARTIAL carrier, the OTHER facet that is partial for the same reason:
# whether an explicit stored column is pinned is a facet of the FIELD
# DEFINITION a step carries, so only the kinds whose step carries a definition
# have one (MigrationStep.__init__ ensures that slot only under
# `kind == KIND_ALTER or kind == KIND_REMOVE`). A RENAMING step is two names and
# no definition; a step of some other kind need not carry one either. All three
# rivals below return EXACTLY gold's values on every input, so no value clause
# can separate them; only the resource discipline on the BUILT step can.
# ---------------------------------------------------------------------------

# uniq-rename-probe-column: build a RENAMING step and read its pinned-column
# facet back, then carry that value into the constructed alteration. Value-
# carried and value-identical to gold (the slot is read back with the value just
# written), so every clause P1-P9 holds of the result.
_UNIQ_RENAME_PROBE_COLUMN = _IMPL_OLD.replace(
    "        carried = MigrationStep(KIND_ALTER, this.model_name_lower,\n"
    "                                nxt.new_name_lower, nxt.new_name_lower,\n"
    "                                this.has_explicit_column, False)",
    "        probe = MigrationStep(KIND_RENAME, this.model_name_lower,\n"
    "                              this.name_lower, nxt.new_name_lower,\n"
    "                              this.has_explicit_column, False)\n"
    "        pinned = probe.has_explicit_column\n"
    "        carried = MigrationStep(KIND_ALTER, this.model_name_lower,\n"
    "                                nxt.new_name_lower, nxt.new_name_lower,\n"
    "                                pinned, False)", 1)

# uniq-guard-rename-probe-column: the same read made GUARD-load-bearing — the
# rename arm's own pinned-column test is taken off a renaming step the impl
# built rather than off the altering step it was handed. Same value on every
# input, so again only the resource discipline can separate it.
_UNIQ_GUARD_RENAME_PROBE_COLUMN = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n"
    "    probe = MigrationStep(KIND_RENAME, this.model_name_lower,\n"
    "                          this.name_lower, this.name_lower,\n"
    "                          this.has_explicit_column, False)\n", 1).replace(
    "            and not this.has_explicit_column:",
    "            and not probe.has_explicit_column:", 1)

# uniq-other-probe-column: the isolation case one kind over — a step of some
# OTHER kind is built purely so its pinned-column facet can be read, then gold's
# body runs verbatim. A step of some other kind need not carry a field
# definition at all, so there is nothing there to ask.
_UNIQ_OTHER_PROBE_COLUMN = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n"
    "    other = MigrationStep(KIND_OTHER, this.model_name_lower,\n"
    "                          this.name_lower, this.name_lower,\n"
    "                          this.has_explicit_column, False)\n"
    "    other_column = other.has_explicit_column\n", 1)

# pos-remove-probe-column: the CALIBRATION control for the two cases above. A
# REMOVING step may be given a field definition, so its pinned-column facet IS
# there to read; an impl that builds one and reads that facet back must still
# verify. If it did not, the conditioning would be over-tight — it would reject
# a rival whose faithful refinement runs and resolves.
_POS_REMOVE_PROBE_COLUMN = _IMPL_OLD.replace(
    "        carried = MigrationStep(KIND_ALTER, this.model_name_lower,\n"
    "                                nxt.new_name_lower, nxt.new_name_lower,\n"
    "                                this.has_explicit_column, False)",
    "        gone = MigrationStep(KIND_REMOVE, this.model_name_lower,\n"
    "                             nxt.new_name_lower, nxt.new_name_lower,\n"
    "                             this.has_explicit_column, False)\n"
    "        carried = MigrationStep(KIND_ALTER, this.model_name_lower,\n"
    "                                nxt.new_name_lower, nxt.new_name_lower,\n"
    "                                gone.has_explicit_column, False)", 1)


# ---------------------------------------------------------------------------
# The PARTIAL carrier — a facet only a rename-shaped later step has. Both
# rivals below return EXACTLY gold's values on every input, so no value clause
# can separate them; the only thing that can is the resource discipline, which
# lends the later step's new name only under `nxt.kind == KIND_RENAME`.
# ---------------------------------------------------------------------------

# uniq-eager-new-name: consult the later step's new name before anything is
# known about that step's kind. The isolation case: gold's body follows
# verbatim, so the values are gold's and only the conditional lending can catch
# the premature consultation.
_UNIQ_EAGER_NEW_NAME = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n"
    "    renamed_to = nxt.new_name_lower\n", 1)

# uniq-eager-carry-name: the same premature consultation made load-bearing —
# the carry-across name is computed up front and then used in the rename arm.
# Every returned value is identical to gold's, including the carried step's
# pinned content, so this rival is value-indistinguishable from the gold impl.
_UNIQ_EAGER_CARRY_NAME = _IMPL_OLD.replace(
    "    # impl-start\n",
    "    # impl-start\n"
    "    carry_name = nxt.new_name_lower\n", 1).replace(
    "                                nxt.new_name_lower, nxt.new_name_lower,",
    "                                carry_name, carry_name,", 1)


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "structurally-different CORRECT impl: test the RENAME branch "
                     "FIRST, then the ALTER/REMOVE branch. A step's kind is a single "
                     "tag, so the arms are mutually exclusive and reordering cannot "
                     "change which fires; the elidable tri-state stays last, so the "
                     "result is identical to gold on every input and P2-P9 all still "
                     "discharge. No loop / no fold, so no induction lemma is needed "
                     "(pilot pitfalls #2/#3). If a faithful correct impl cannot verify "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-hoist",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_HOIST),
        "rationale": "local-variable reshape: hoist is_same_field(this, nxt) into a "
                     "bound bool `same` and reuse it across both same-field arms (same "
                     "control flow, same returns). is_same_field is @Pure so its value "
                     "is stable; the result is identical to gold. Must verify (else "
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-elidable-nested",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_ELIDABLE_NESTED),
        "rationale": "the generic fall-through's two elidable arms written as a NESTED "
                     "if/else under a single else-tail instead of two flat elifs. Same "
                     "tri-state with the same precedence (the earlier step's mark "
                     "first), so the result is identical to gold on every input. A "
                     "correct restructuring of the arm the reviewer's witness lands in "
                     "must verify (else SPEC-TOO-STRONG on exactly the repaired "
                     "clause).",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "pos-remove-probe-column",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REMOVE_PROBE_COLUMN),
        "rationale": "CALIBRATION control for the pinned-column conditioning. The "
                     "impl builds a REMOVING step, reads its pinned-column facet "
                     "back and carries that value into the constructed alteration. "
                     "MigrationStep.__init__ grants that slot for KIND_ALTER and "
                     "KIND_REMOVE, so this must VERIFY -- and it must, because the "
                     "faithful refinement RUNS: RemoveField inherits "
                     "FieldOperation.__init__(model_name, name, field=None) "
                     "(fields.py:9-12), so RemoveField(model_name=..., name=..., "
                     "field=self.field).field.db_column is a value, not an error. "
                     "Measured on the patched worktree: 38/38 optimizer tests OK, "
                     "i.e. the rival RESOLVES. Rejecting it would be "
                     "SPEC-TOO-STRONG, which is what makes this the boundary of the "
                     "conditioning rather than a blanket ban on reading a built "
                     "step.",
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds the exact "
                     "F2P shape — two same-field KIND_ALTER steps (model 7, field 11), "
                     "mirroring migrations.AlterField('Foo','name',...) twice — and "
                     "asserts they satisfy reduce's exact Requires (the 1/2 field "
                     "accesses from the constructor Ensures, this0.kind == KIND_ALTER) "
                     "and that is_same_field / joined_by_field_rule hold for the pair. "
                     "A second witness pins the other admissible shape: an unrelated "
                     "later step carrying the elidable mark, for which "
                     "joined_by_field_rule is FALSE and elidable is TRUE (the "
                     "fall-through arm). A THIRD witness is a later step that IS a "
                     "rename, which is what keeps the CONDITIONALLY lent new-name "
                     "facet from being vacuous: with the antecedent true the facet is "
                     "genuinely required, is genuinely held, and reads back the value "
                     "it was built with. The real impl then runs unchanged. If the "
                     "precondition could not be established for these legitimate "
                     "inputs an Assert fails => PRECOND-TOO-STRONG. The conjuncts "
                     "are ASSERTED rather than probed by a self-call: an unguarded "
                     "self-call is unbounded recursion (kept as the "
                     "'uniq-diverging-self-call' reject case), which is a different "
                     "and false claim from 'the precondition is establishable'. "
                     "Non-vacuous: splicing Assert(False) after these Asserts fails "
                     "to verify, so the witness path is reachable.",
    },

    # ---- frame-mutation (MANDATORY; must reject for insufficient permission) ----
    {
        "id": "frame-write-this-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_WRITE_THIS),
        "refinement": "AlterField.reduce never mutates the operation it is reducing; "
                      "writing self.kind (the operation's runtime class proxy) "
                      "in-place would corrupt the shared operation object the "
                      "optimizer still holds, changing every later reduction and the "
                      "emitted migration. A faithful patch that rewrote `self`'s class "
                      "tag could never resolve the F2P/P2P (it would scramble the "
                      "operation list). The write only exists to satisfy a clause "
                      "vacuously by editing the input.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: `this` is held only at "
                     "Acc(this.kind, 1/2) (read-only); the assignment this.kind = "
                     "KIND_OTHER needs full Acc(this.kind, 1) which the precondition "
                     "does not grant. The gold body is kept verbatim, so the rejection "
                     "is attributable to the write (the #1 frame-condition weakness).",
    },
    {
        "id": "frame-write-nxt-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_WRITE_NXT),
        "refinement": "rewriting nxt.kind to KIND_ALTER would let the impl claim the "
                      "collapse for ANY follow-up step by forcing its kind, rather than "
                      "reading the real class — a patch that overwrote the operation's "
                      "type would collapse pairs that must not collapse (e.g. an "
                      "unrelated CreateModel), failing the optimizer P2P tests. The "
                      "write is a vacuous-satisfaction cheat on the input.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: `nxt` is held only at "
                     "Acc(nxt.kind, 1/2) (read-only); nxt.kind = KIND_ALTER needs full "
                     "Acc(nxt.kind, 1) which the precondition does not grant. Gold body "
                     "kept verbatim so the rejection is attributable to the write.",
    },
    {
        "id": "frame-write-nxt-elidable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_WRITE_ELIDABLE),
        "refinement": "the elidable mark is a property of the operation the caller "
                      "still holds; setting it would make every later reduction treat "
                      "an operation the migration author declared non-elidable as safe "
                      "to drop, silently deleting migration steps. A patch that wrote "
                      "the flag rather than reading it satisfies the fall-through "
                      "clause by editing its own input.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: `nxt` is held only at "
                     "Acc(nxt.elidable, 1/2) (read-only); nxt.elidable = True needs "
                     "full Acc(nxt.elidable, 1). Gold body kept verbatim so the "
                     "rejection is attributable to the write.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-revert-remove-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REVERT_REMOVE_ONLY),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags: the guard is reverted to "
                      "isinstance(operation, RemoveField) only, so a same-field "
                      "follow-up AlterField is NOT collapsed (reduce falls through to "
                      "the generic combinability flag). The sole F2P "
                      "test_alter_alter_field optimizes two same-field AlterFields and "
                      "asserts the result is the single second AlterField; pre-patch "
                      "leaves both, so it fails. Its faithful real patch (the "
                      "un-widened guard) is exactly what does NOT resolve.",
        "rationale": "rejected by P3: Implies(nxt.kind == KIND_ALTER and "
                     "is_same_field(this,nxt), Result() is not None and len==1 and "
                     "Result()[0] is nxt). With the ALTER disjunct removed, an ordinary "
                     "(non-elidable) alter-then-alter pair reaches the fall-through and "
                     "returns None, violating P3.",
    },
    {
        "id": "uniq-alter-only-drop-remove",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALTER_ONLY),
        "refinement": "collapsing only the ALTER case while dropping the (unchanged) "
                      "REMOVE case corresponds to a patch that replaced the isinstance "
                      "tuple (AlterField, RemoveField) with just AlterField. The P2P "
                      "'RemoveField should absorb AlterField' optimizes a same-field "
                      "AlterField followed by RemoveField and asserts the pair "
                      "collapses to the RemoveField; this impl leaves the pair "
                      "uncombined and the absorption regresses => does NOT resolve.",
        "rationale": "rejected by P2: Implies(nxt.kind == KIND_REMOVE and "
                     "is_same_field(this,nxt), Result() is not None and len==1 and "
                     "Result()[0] is nxt). Dropping the REMOVE disjunct returns None "
                     "for an ordinary same-field REMOVE, violating P2 (and P4, the "
                     "symmetry clause).",
    },
    {
        "id": "uniq-drop-rename",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_RENAME),
        "refinement": "dropping the rename carry-across corresponds to a patch that "
                      "deleted the `elif isinstance(operation, RenameField) ... "
                      "db_column is None` branch. The P2P 'RenameField should optimize "
                      "to the other side of AlterField' (test_swapping_fields_names) "
                      "optimizes an AlterField followed by a same-field RenameField and "
                      "asserts the pair becomes [RenameField, AlterField(renamed)]; "
                      "this impl leaves it uncombined and the carry-across is lost => "
                      "does NOT resolve.",
        "rationale": "rejected by P5: Implies(nxt.kind == KIND_RENAME and "
                     "is_same_field(this,nxt) and not this.has_explicit_column, "
                     "Result() is not None and len==2 and Result()[0] is nxt and "
                     "Result()[1] is not nxt). Returning None violates P5.",
    },
    {
        "id": "uniq-rename-singleton",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RENAME_SINGLETON),
        "refinement": "collapsing a same-field rename to [operation] only (dropping the "
                      "carried AlterField) corresponds to a patch that returned "
                      "[operation] instead of [operation, AlterField(...)] on the "
                      "rename branch. The renamed field would lose its alteration; the "
                      "'RenameField to the other side of AlterField' P2P asserts the "
                      "two-element result, so the alteration vanishes => does NOT "
                      "resolve.",
        "rationale": "rejected by P5: the clause requires len(Result()) == 2. A "
                     "singleton [nxt] has len 1, violating P5.",
    },
    {
        "id": "uniq-rename-carry-is-nxt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RENAME_CARRY_IS_NXT),
        "refinement": "returning [operation, operation] (the rename twice) instead of "
                      "[operation, AlterField(renamed)] is a control-flow / "
                      "value-double-mask cheat: it has the right length (2) but the "
                      "second element is the rename, not a fresh equivalent alteration "
                      "of the renamed field. The optimizer would emit two renames and "
                      "lose the field alteration entirely; the carry-across P2P asserts "
                      "the second element reproduces the alteration => does NOT resolve.",
        "rationale": "rejected by P5's identity pin: Result()[1] is not nxt. The carry "
                     "element here IS nxt, violating the distinctness requirement (the "
                     "length-2 check alone is masked, but the identity clause catches "
                     "it).",
    },
    {
        "id": "uniq-carry-marked-elidable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CARRY_ELIDABLE),
        "refinement": "the real carry-across builds AlterField(model_name=self."
                      "model_name, name=operation.new_name, field=self.field) — a "
                      "plain alteration, which carries the default (unset) elidable "
                      "mark. A carried step marked elidable would be dropped by the "
                      "very next reduction, so the renamed field silently loses the "
                      "alteration the carry-across exists to preserve => does NOT "
                      "resolve the carry-across P2P.",
        "rationale": "rejected by P5's elidable pin: not Result()[1].elidable. Every "
                     "other facet of P5 (kind, owning model, renamed field name, "
                     "pinned-column status, length, identity) is satisfied here, so "
                     "this case is live only because the carried step's mark is pinned.",
    },
    {
        "id": "uniq-collapse-different-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIFFERENT_FIELD),
        "refinement": "dropping the is_same_field guard on the ALTER/REMOVE arm "
                      "corresponds to a patch that removed `self.is_same_field_"
                      "operation(operation)` from the widened branch. It would collapse "
                      "an AlterField with an unrelated follow-up on a DIFFERENT field or "
                      "model, destroying independent operations. Many optimizer P2P "
                      "tests interleave operations on distinct fields and assert they "
                      "are NOT merged; collapsing them => does NOT resolve.",
        "rationale": "rejected by P9: Implies(not is_same_field(this,nxt) and not "
                     "this.elidable and not nxt.elidable, Result() is None). With the "
                     "same-field guard removed, a different-field ALTER/REMOVE with "
                     "neither elidable mark set returns [nxt] (not None), violating P9 "
                     "(and P8).",
    },
    {
        "id": "uniq-drop-elidable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_ELIDABLE),
        "refinement": "reporting 'not combined' for every pair the same-field rules do "
                      "not resolve corresponds to a patch that replaced the generic "
                      "fall-through with a bare `return False`. An elidable step would "
                      "then never be elided: the optimizer's elidable-operation tests "
                      "(a step declared safe to elide is expected to disappear across "
                      "an unrelated operation) regress => does NOT resolve the P2P set.",
        "rationale": "rejected by P6/P7: a pair no same-field rule resolves must "
                     "collapse to the singleton [nxt] when the earlier step is elidable "
                     "and to [this] when only the later one is. Returning None for both "
                     "violates the fall-through clauses.",
    },
    {
        "id": "uniq-elidable-precedence-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ELIDABLE_SWAPPED),
        "refinement": "testing the LATER step's mark first inverts the precedence of "
                      "the generic fall-through. On a pair where BOTH steps are "
                      "elidable the real reduction keeps the later step (the earlier "
                      "one elides), while this keeps the earlier one — the optimizer "
                      "emits the wrong survivor and a squashed migration loses the "
                      "later step's effect => does NOT resolve.",
        "rationale": "rejected by P6: Implies(not joined_by_field_rule(this,nxt) and "
                     "this.elidable, singleton [nxt]). With both marks set this impl "
                     "returns [this], violating P6 (P7 is guarded by not this.elidable, "
                     "so it does not excuse the swap).",
    },
    {
        "id": "uniq-elidable-wrong-side",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ELIDABLE_WRONG_SIDE),
        "refinement": "when only the LATER step is elidable, the real reduction keeps "
                      "the EARLIER step and drops the elidable one; returning the "
                      "elidable step instead drops the alteration the migration needs "
                      "and keeps the step declared safe to elide — the schema change "
                      "vanishes from the squashed migration => does NOT resolve.",
        "rationale": "rejected by P7's identity pin: Implies(not joined_by_field_rule "
                     "and not this.elidable and nxt.elidable, len==1 and Result()[0] is "
                     "this). Shape and length are right here, so only the identity pin "
                     "catches the swapped survivor.",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-always-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ALWAYS_NONE),
        "refinement": "never collapsing (always the plain combinability flag) is the "
                      "do-nothing patch: it resolves NOTHING — the F2P "
                      "test_alter_alter_field and every collapse-observing P2P "
                      "(RemoveField-absorbs-AlterField, RenameField-to-other-side, "
                      "elidable-step-elided) would fail. Supporting near-miss confirming "
                      "the collapse clauses are live.",
        "rationale": "rejected by P3 (and P2/P4/P5/P6/P7): a same-field alter-then-alter "
                     "must return the singleton [nxt]; returning None violates the "
                     "collapse postconditions outright.",
    },

    {
        "id": "frame-write-nxt-new-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_WRITE_NEW_NAME),
        "refinement": "the name a rename targets is the caller's data, not a slot "
                      "this routine owns; writing it would let the reduction pick "
                      "the new field name itself and then carry the alteration "
                      "across to that invented name, so the emitted migration "
                      "would rename to one name and alter another => does NOT "
                      "resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: `nxt` is held only at "
                     "Acc(nxt.new_name_lower, 1/2) (read-only); the assignment "
                     "needs full Acc. The gold body is kept verbatim after the "
                     "write, so the rejection is attributable to the write and not "
                     "to a broken proof obligation.",
    },
    {
        "id": "uniq-verdict-always-withheld",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_VERDICT_FALSE),
        "refinement": "always withholding permission to reorder corresponds to a "
                      "patch that ended the routine with a bare 'cannot optimize "
                      "across'. Two collapsible same-field alterations separated by "
                      "a step that does NOT touch that field would then never be "
                      "brought together, because the intervening step is never "
                      "cleared for reordering — exactly the multiple-AlterField "
                      "reduction this issue is about, left undone whenever the "
                      "alterations are not already adjacent => does NOT resolve.",
        "rationale": "rejected by the reordering-verdict clause: Implies(not "
                     "joined_by_field_rule and neither elidable, Result()[0] is None "
                     "and Result()[1] == (not nxt_references_altered_field)). For a "
                     "later step that does not reference the altered field the "
                     "verdict must be granted; a constant False withholds it.",
    },
    {
        "id": "uniq-verdict-always-granted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_VERDICT_TRUE),
        "refinement": "always granting permission is the opposite failure: a step "
                      "that really does reference the altered field would be "
                      "declared safe to optimize across, so the optimizer would "
                      "reorder operations past an alteration they depend on and "
                      "drop steps that must survive (an alteration followed by an "
                      "addition and a removal of the same field collapses to "
                      "nothing instead of to the alteration) => does NOT resolve.",
        "rationale": "rejected by the reordering-verdict clause: for a later step "
                     "that DOES reference the altered field the verdict must be "
                     "withheld; a constant True grants it. This is the dual of "
                     "uniq-verdict-always-withheld, so together they show the "
                     "clause pins a real function of the input and not merely one "
                     "of its two values.",
    },
    {
        "id": "uniq-verdict-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_VERDICT_INVERTED),
        "refinement": "reading the right input and inverting it grants reordering "
                      "exactly where it must be withheld and withholds it exactly "
                      "where it must be granted, so it commits BOTH failures above "
                      "on complementary halves of the domain while producing a "
                      "result of exactly the right shape on every input.",
        "rationale": "rejected by the reordering-verdict clause's equality: "
                     "Result()[1] == (not nxt_references_altered_field). The "
                     "inverted verdict satisfies it on no input where the flag is "
                     "set either way, and no collapse clause is disturbed, so this "
                     "case is live only because the verdict's VALUE is pinned "
                     "rather than merely its existence.",
    },
    {
        "id": "uniq-verdict-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_VERDICT_ECHO),
        "refinement": "an ungrounded-oracle echo: it reconstructs the verdict from "
                      "the two steps' names instead of from whether the later step "
                      "references the altered field. Naming a different field is "
                      "not the same as not touching it — a step can reach the "
                      "altered field through a relation while naming another field, "
                      "and can name the same field without referencing it — so the "
                      "echo clears steps for reordering that must block it and the "
                      "optimizer moves operations past alterations they depend on "
                      "=> does NOT resolve.",
        "rationale": "rejected by the reordering-verdict clause: the clause pins "
                     "Result()[1] to (not nxt_references_altered_field), a distinct "
                     "input from the name comparison is_same_field reads, so the "
                     "substitution does not discharge it. This is the lane that "
                     "confirms the clause forces the impl to CONSULT the reported "
                     "fact rather than to re-derive a plausible value from the "
                     "other arguments.",
    },
    {
        "id": "uniq-carried-name-kept-old",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CARRIED_NAME_OLD),
        "refinement": "carrying the alteration across a rename must target the "
                      "field under its NEW name; aiming it at the old name leaves "
                      "an alteration of a field that no longer exists once the "
                      "rename has run => does NOT resolve.",
        "rationale": "rejected by the rename-branch content clause, specifically "
                     "Result()[0][1].name_lower == nxt.new_name_lower: the carried "
                     "alteration must target the field under the name the rename "
                     "gives it. Every other facet of P5 is satisfied (right kind, "
                     "right model, no elidable mark, distinct fresh step, right "
                     "order), so this case is live only because the carried step's "
                     "NAME is pinned. The pinned facets are exactly the ones the "
                     "real carried operation has; the carrier's new-name slot is "
                     "NOT pinned, because the real carried operation defines no "
                     "new_name -- see mapping.md, 'Carrier slots with no repo "
                     "counterpart'.",
    },
    {
        "id": "uniq-read-back-carried-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_READ_BACK_CARRIED_NAME),
        "refinement": "the carried alteration is a real AlterField, and AlterField "
                      "defines no new_name at all (hasattr(AlterField('Foo','name',"
                      "f),'new_name') is False; the instance __dict__ is "
                      "['_constructor_args','field','model_name','name',"
                      "'preserve_default']). A faithful refinement therefore builds "
                      "the carried operation and then reads `.new_name` off it, "
                      "which raises AttributeError rather than returning the value "
                      "it just stored. Measured on the patched worktree over the "
                      "instance's 38 optimizer tests: 1 error, "
                      "test_alter_field_rename_field -- \"AttributeError: "
                      "'AlterField' object has no attribute 'new_name'\" -- i.e. the "
                      "P2P case 'RenameField should optimize to the other side of "
                      "AlterField,' errors while the F2P alter-then-alter case still "
                      "passes => does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on carried.new_name_lower "
                     "('Method call might fail. There might be insufficient "
                     "permission to access carried.new_name_lower.'): "
                     "MigrationStep.__init__ grants that slot only under "
                     "kind == KIND_RENAME, and the carried step is built as "
                     "KIND_ALTER. Value-INDISTINGUISHABLE from gold -- the slot is "
                     "read back with the value just written, so the returned pair "
                     "matches gold on every pinned facet and every clause P1-P9 "
                     "holds of it. Only the resource discipline on a BUILT step can "
                     "separate the two, which is why a total constructor grant made "
                     "this rival verify.",
    },
    {
        "id": "uniq-eager-built-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EAGER_BUILT_NAME),
        "refinement": "the isolation case for the same absent facet: a throw-away "
                      "alteration is built at the top of the body and its new-name "
                      "slot read. Refined faithfully that is "
                      "AlterField(model_name=self.model_name, name=self.name, "
                      "field=self.field).new_name, which raises on EVERY pair the "
                      "optimizer offers, not just on a rename pair. Measured on the "
                      "patched worktree: 3 errors over the 38 optimizer tests, "
                      "including the F2P test_alter_alter_field itself, all "
                      "\"AttributeError: 'AlterField' object has no attribute "
                      "'new_name'\" => does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on probe.new_name_lower. "
                     "Gold's body follows the read VERBATIM, so every returned value "
                     "is gold's and no value clause is even consulted; the rejection "
                     "is attributable solely to reading a new name off a step built "
                     "as an alteration. Pairs with uniq-eager-new-name (the same "
                     "premature read, but on the step the reduction is HANDED) so "
                     "both directions of the partiality -- received and built -- are "
                     "pinned.",
    },
    {
        "id": "uniq-rename-probe-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_RENAME_PROBE_COLUMN),
        "refinement": "the pinned-column facet refines to `self.field.db_column is "
                      "not None`, and a RENAMING step has no field definition at "
                      "all: RenameField.__init__(model_name, old_name, new_name) "
                      "(fields.py:273-276) takes no field and calls "
                      "super().__init__(model_name, old_name), so "
                      "FieldOperation.__init__ (fields.py:9-12) stores field=None. "
                      "A faithful refinement therefore builds "
                      "RenameField(model_name=self.model_name, old_name=self.name, "
                      "new_name=operation.new_name) and evaluates "
                      "probe.field.db_column, which raises. Measured on the patched "
                      "worktree over the instance's 38 optimizer tests: 1 error, "
                      "test_alter_field_rename_field -- \"AttributeError: 'NoneType' "
                      "object has no attribute 'db_column'\" -- i.e. the P2P case "
                      "'RenameField should optimize to the other side of AlterField,' "
                      "errors while the F2P alter-then-alter case still passes => "
                      "does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on "
                     "probe.has_explicit_column: MigrationStep.__init__ grants that "
                     "slot only under kind == KIND_ALTER or kind == KIND_REMOVE, and "
                     "the probe is built as KIND_RENAME. Value-INDISTINGUISHABLE "
                     "from gold -- the slot is read back with the value just "
                     "written, so the carried step's pinned-column status is gold's "
                     "and every clause P1-P9 holds. Only the resource discipline on "
                     "a BUILT step can separate the two, which is why a total "
                     "constructor grant on this slot made this rival verify. Pairs "
                     "with pos-remove-probe-column, which reads the SAME facet off a "
                     "step built as a REMOVAL and must verify, so the conditioning "
                     "is a boundary and not a ban.",
    },
    {
        "id": "uniq-guard-rename-probe-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_GUARD_RENAME_PROBE_COLUMN),
        "refinement": "the same absent facet, read in the GUARD instead of carried "
                      "as a value: the rename arm's own pinned-column test is taken "
                      "off a RenameField the impl built. Refined faithfully the guard "
                      "evaluates probe.field.db_column with probe.field None. "
                      "Measured on the patched worktree: 1 error over the 38 "
                      "optimizer tests, test_alter_field_rename_field -- "
                      "\"AttributeError: 'NoneType' object has no attribute "
                      "'db_column'\" => does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on "
                     "probe.has_explicit_column, this time while evaluating the "
                     "rename arm's guard. The probe carries the altering step's own "
                     "column status, so the guard decides exactly as gold's does and "
                     "every returned value is gold's; the rejection is attributable "
                     "solely to asking a renaming step for a facet it has no field "
                     "definition to supply. Pairs with uniq-rename-probe-column "
                     "(value-carried) so both the value and the control-flow use of "
                     "the absent facet are pinned.",
    },
    {
        "id": "uniq-other-probe-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OTHER_PROBE_COLUMN),
        "refinement": "the isolation case one kind over: a step of some OTHER kind "
                      "is built at the top of the body purely so its pinned-column "
                      "facet can be read, and gold's body then runs verbatim. "
                      "KIND_OTHER abstracts every operation class that is not an "
                      "alteration, removal or rename, and such a class need not "
                      "carry a field definition at all -- a bare Operation "
                      "(base.py) has no `field` attribute whatsoever. A faithful "
                      "refinement may therefore build Operation() and evaluate "
                      "other.field.db_column, which raises on EVERY pair the "
                      "optimizer offers. Measured on the patched worktree: 3 errors "
                      "over the 38 optimizer tests, including the F2P "
                      "test_alter_alter_field itself, all \"AttributeError: "
                      "'Operation' object has no attribute 'field'\" => does NOT "
                      "resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on "
                     "other.has_explicit_column. Gold's body follows the read "
                     "VERBATIM, so no value clause is even consulted and the "
                     "rejection is attributable solely to reading a pinned-column "
                     "status off a step built with a kind that carries no field "
                     "definition. Completes the family: KIND_RENAME (the two cases "
                     "above) and KIND_OTHER reject, KIND_ALTER (gold's carried step) "
                     "and KIND_REMOVE (pos-remove-probe-column) verify -- exactly "
                     "the kinds whose repo class accepts a field definition.",
    },
    # ---- non-termination (must reject; else SPEC-TOO-WEAK on TOTAL correctness) ----
    {
        "id": "uniq-diverging-self-call",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIVERGING_SELF_CALL),
        "refinement": "no faithful patch corresponds to this: AlterField.reduce "
                      "decides the pair from the two operations' kinds, the "
                      "same-field test and the two elidable marks, and never "
                      "re-enters itself on the same pair. A reduce that called "
                      "itself unconditionally would recurse until the stack blew "
                      "on the FIRST pair the optimizer offered it, so the F2P "
                      "test_alter_alter_field and every collapse-observing P2P "
                      "would error out rather than pass => does NOT resolve. The "
                      "case exists to pin TOTAL correctness: the rival DIVERGES.",
        "rationale": "unbounded recursion — no base case and no decreasing measure, "
                     "so reduce never returns and P1-P9 (all conditioned on "
                     "Result()) constrain only runs that never happen. Rejection "
                     "source: the OBLIGATION SYSTEM (MustTerminate levels are "
                     "per-method constants and a call is admitted only strictly "
                     "below its caller's level, so a self-call can never take the "
                     "caller's obligation). Measured load-bearing: with "
                     "Requires(MustTerminate(6)) removed from the pre-conditions "
                     "region this exact module VERIFIES. If it verified with the "
                     "obligation present => SPEC-TOO-WEAK (only partial "
                     "correctness, so an impl that hangs is admitted).",
    },
    {
        "id": "uniq-diverging-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DIVERGING_LOOP),
        "refinement": "the real reduction is a chain of guards over two operations "
                      "and contains no loop at all, so a reduce that spun before "
                      "deciding would hang the first reduction the optimizer "
                      "attempted: every F2P/P2P test that runs the optimizer would "
                      "time out rather than fail => does NOT resolve. Second "
                      "divergence channel, distinct from the self-call one.",
        "rationale": "the gold body is kept verbatim but is preceded by an unbounded "
                     "`while spin >= 0` loop, so every clause is established of a "
                     "return that is never reached — indistinguishable from gold "
                     "under partial correctness. Rejection source: the OBLIGATION "
                     "SYSTEM (the loop carries no MustTerminate invariant, so it "
                     "cannot take the obligation its context holds). Measured "
                     "load-bearing: with Requires(MustTerminate(6)) removed from the "
                     "pre-conditions region this exact module VERIFIES. If it "
                     "verified with the obligation present => SPEC-TOO-WEAK.",
    },
    {
        "id": "uniq-eager-new-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EAGER_NEW_NAME),
        "refinement": "a new name is a facet only a renaming step carries: in the "
                      "repository the later operation is an arbitrary migration "
                      "operation, and only the renaming one has a new-name attribute "
                      "at all. A faithful patch that reads it before establishing "
                      "that the later operation IS a rename does not compute a wrong "
                      "value, it raises AttributeError on the first reduction whose "
                      "later operation is an alteration or a removal. Measured on the "
                      "patched worktree over the instance's 38 optimizer tests: this "
                      "refinement fails exactly the reported alter-then-alter case "
                      "(F2P) and the remove-absorbs-alteration case (P2P), both with "
                      "AttributeError => does NOT resolve.",
        "rationale": "rejected for INSUFFICIENT PERMISSION on nxt.new_name_lower: the "
                     "precondition lends that facet only under "
                     "nxt.kind == KIND_RENAME, and at the top of the body nothing is "
                     "known about the later step's kind. The isolation case for the "
                     "partial carrier — gold's body follows VERBATIM, so every "
                     "returned value is gold's and no value clause is even "
                     "consulted; the rejection is attributable solely to the "
                     "premature consultation. If it verified => SPEC-TOO-WEAK (the "
                     "spec would be treating a facet that does not exist as though "
                     "every step carried it).",
    },
    {
        "id": "uniq-eager-carry-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EAGER_CARRY_NAME),
        "refinement": "the same premature consultation, load-bearing: the carry-across "
                      "target name is computed up front and then used to build the "
                      "carried alteration. Same failure in the repository (the read "
                      "raises before any guard runs) and the same measured outcome on "
                      "the patched worktree: the alter-then-alter F2P case and the "
                      "remove-absorbs-alteration P2P case both error => does NOT "
                      "resolve.",
        "rationale": "value-INDISTINGUISHABLE from gold: on every admissible input it "
                     "returns exactly gold's answer, carried step included, so P2-P9 "
                     "hold of it and only the resource discipline can separate it. "
                     "Rejected for INSUFFICIENT PERMISSION on nxt.new_name_lower. "
                     "This is the case that shows the conditional lending is doing "
                     "real work rather than decorating the frame: no postcondition of "
                     "any strength could reject it.",
    },
]


# ===========================================================================
# AXIOM LANE — none. meta.json axioms == [] and deep_model_references == []:
# the changed behaviour (AlterField.reduce) is pure control flow over operation
# kinds, a same-field test and the two elidable marks, modeled DEEPLY in model.py
# (refinement.md: every step R or I, no axiomatized callee). is_same_field and
# joined_by_field_rule are spelled-out @Pure predicates, NOT @ContractOnly
# axioms. So there is nothing for the axiom lane to execute (the bundle's
# axiom_check.py is a STRUCTURAL equivalence check, not an axiom soundness
# obligation). AXIOM_TESTS is therefore empty.
# ===========================================================================
AXIOM_TESTS = []
