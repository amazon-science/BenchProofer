"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-8638.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template.

The functions under spec
------------------------
    rendered_role(role: int, target_is_null: bool) -> int      (@Pure, deep)
    make_xref(role: int) -> FieldNode                       (deep model, A-ref)
    build_variable_field_entry(type_role: int,
                               type_target_is_null: bool) -> List[FieldNode]

`make_xref` is the deep model of the unchanged per-token node-kind renderer
`sphinx.util.docfields.Field.make_xref`. Its postcondition is FULLY GROUNDED in
the role the token RENDERS UNDER:

    (X1) Result().is_xref == (role != 0)     # links iff a role is present
    (X2) Result().reftype  == role           # carries that role as the reftype

`rendered_role` is the deep model of the role NORMALISATION the python-domain
typed field applies before a token links (`PyTypedField.make_xref`,
`sphinx/domains/python.py:326-333`): a slot configured with the type-reference
role whose target names the null value renders under the fallback
object-reference role instead. It is the identity in every other case,
including on an absent role for every target.

`build_variable_field_entry` models the rendering of one attribute/instance-
variable field entry (the gold patch removes the name `rolename` from the
`'variable'` PyTypedField). Precondition + load-bearing postcondition clauses:

    (P0) Requires(type_role != 0)            # the type slot carries a role
    (P1) len(Result()) == 2                  # [name_node, type_node]
    (P2) Result()[0].is_xref is False        # NAME plain — THE FIX / discriminator
    (P2b) Result()[0].reftype == 0           # a plain NAME token carries no
                                             #   reference kind (sentinel 0)
    (P3) Result()[1].is_xref is True         # TYPE still cross-references
    (P4) Result()[1].reftype ==              # TYPE carries its type-role as
         rendered_role(type_role,            #   NORMALISED against the target
                       type_target_is_null)

P2 is the discriminating clause the F2P test `test_info_field_list_var`
observes: the `:var int attr:` name token must render as a plain
`addnodes.literal_strong`, NOT a `pending_xref`; the type `int` must be a
`pending_xref` with reftype=='class'. model_prepatch.py (name_role = NULL_ROLE)
FAILS P2.

The spec also obliges the rendering to TERMINATE: `make_xref` and
`build_variable_field_entry` each carry `Requires(MustTerminate(n))`, so the
entry must be DELIVERED in a bounded number of steps on every admissible input.
Without it P1-P4 (and X1/X2) are claimed only of runs that reach the return, so a
rival that never delivers an entry satisfies every one of them VACUOUSLY and
VERIFIES while its faithful impl hangs the F2P test. That is the
'weak-nonterminating-self-delegation' reject case below, and the sharper
partial-domain 'weak-nonterminating-on-null-target'; both were a MEASURED hole
(the first was submitted as an attack, its patch applied, kept PASS_TO_PASS
34/34, and failed the F2P), not a hypothetical one. Levels: __init__ 2 <
make_xref 6 < build_variable_field_entry 10, since Nagini admits a call only from
a strictly higher level than the callee's; the admissibility probe therefore
drives its calls from 11 (see A1).

P4 is stated through `rendered_role` because the real renderer's type-token
reftype is NOT a function of the configured type-role alone: on the type target
naming the null value the type-reference role is remapped to the fallback role.
A postcondition pinning the configured role unconditionally would contradict the
real callee on that reachable target, so the clause pins the NORMALISED role —
which the real callee guarantees on every target. Rival U7 is the impl that
skips normalisation and is rejected by exactly this clause.

Read-only inputs / frame-mutation
---------------------------------
NO modeled function takes a read-only `Acc(x, 1/2)` reference parameter: `role`,
`type_role` and `type_target_is_null` are bare `int`/`bool` passed BY VALUE, and
the only heap permissions are on the freshly-CONSTRUCTED `FieldNode`/list result
(which the postcondition hands out in full). There is therefore no caller-owned
input the spec must protect from a vacuous overwrite, so the frame-mutation
weakness class does not apply here (has_readonly_input = False). See
'assessment'. A positive control and a result-mutation sanity case stand in for
that lane.

Ungrounded-oracle echo
----------------------
The postcondition is NOT pinned to an opaque answer-key: `is_xref` and `reftype`
are explicit functions of the inputs (`role != 0`, `role`, and the spelled-out
`rendered_role` normalisation, whose body is in the spec view and is checkable
by reading it). There is no oracle to echo — any output is checkable directly
against the inputs — so the ungrounded-oracle class is N/A; an honest
cheapest-impl positive control (`make-xref-pos-reorder`) stands in for it.

Region surgery
--------------
Each variant is built by `_swap` on the frozen model.py, editing ONLY text
inside an `# impl-start`/`# impl-end` region (there are two: one per implemented
function), which GUARANTEES same_spec (the frozen spec view — docstring,
signatures, pre/post-conditions and the `pure` region carrying `rendered_role`
— is never touched). Anchors are chosen to be unique across the whole file.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8638"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each unique in model.py; all strictly inside an impl region)
# ---------------------------------------------------------------------------

# make_xref impl region
_MAKEXREF_GOLD = """    if role != 0:
        return FieldNode(True, role)
    return FieldNode(False, 0)"""

# build_variable_field_entry impl region
_BVFE_GOLD = """    # The attribute / instance-variable field configures no role for its name
    # token, so the name slot is built under an absent role (code 0);
    # normalisation is the identity on an absent role, for every name target.
    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    return par"""

# The bare assignment that sets the name slot to the absent role — the single
# behavioural delta of the gold patch (refinement.md A2).
_NAME_ROLE_ABSENT = "    name_role = 0\n"


# ===========================================================================
# UNIQUENESS / WEAKNESS RIVALS  (must be REJECTED)
# ===========================================================================

# (U1 — PARTIAL-DOMAIN / pre-patch bug, THE central attack) The rival re-
# introduces a PRESENT name role (NULL_ROLE == the object-reference role the
# pre-patch config named), exactly model_prepatch.py. Every other clause
# (P1/P3/P4) is satisfied, but the NAME token now links, VIOLATING P2
# (Result()[0].is_xref is False). Rejection comes from the discriminating
# postcondition clause P2 — the no-auto-link guarantee.
#
# Refinement (why its faithful real patch would NOT resolve): a present name
# role IS the pre-patch name `rolename` on the 'variable' PyTypedField. Its
# faithful real patch is the UNMODIFIED config (the patch not applied), under
# which the real TypedField.make_field renders the `:var int attr:` name token as
# a `pending_xref` instead of a plain `literal_strong`. The F2P
# `test_info_field_list_var` asserts the name token is `[addnodes.literal_strong,
# "attr"]`, so it FAILS — this is precisely the behaviour the patch changes.
_RIVAL_PREPATCH_NAMEROLE = _swap(
    _BASE, _NAME_ROLE_ABSENT, "    name_role = NULL_ROLE\n")

# (U2 — VALUE double-mask / drop-the-type-link) The rival builds the TYPE token
# under an ABSENT role (literal 0) instead of its normalised type-role,
# collapsing it to a plain inline node. It still satisfies P1/P2, but VIOLATES P3
# (Result()[1].is_xref is True) and P4 (reftype == the normalised role).
# Rejection comes from the companion type-link clauses P3/P4 that pin the
# UNCHANGED type cross-reference, so a wrong impl cannot satisfy the spec by also
# dropping the type link (refinement.md §B).
#
# Refinement: dropping the type link corresponds to a real patch that ALSO
# removed `typerolename='class'` from the 'variable' field. The F2P asserts the
# type token is a `pending_xref` with reftype='class' (`assert_node(... pending_
# xref, reftype="class", reftarget="int")`); a plain type token FAILS that
# assertion, so it would NOT resolve.
_RIVAL_DROP_TYPE_LINK = _swap(
    _BASE, _BVFE_GOLD,
    """    name_role = 0
    name_node = make_xref(name_role)
    # WRONG: build the type token under an absent role, dropping its link
    type_node = make_xref(0)
    par = [name_node, type_node]  # type: List[FieldNode]
    return par""")

# (U3 — token ORDER swap) The rival returns [type_node, name_node] — the plain
# token where the cross-reference is expected and vice-versa. It satisfies P1 and
# the Acc() clauses, but VIOLATES P2 (Result()[0] now links) and P3 (Result()[1]
# now plain). Rejection comes from the positional clauses P2/P3, which pin the
# entry order (name token first, type token second — mapping.md §2/§A4).
#
# Refinement: a real renderer that emitted the parenthesised type token before
# the name token would produce a paragraph whose first child is the `int`
# cross-reference, not `[addnodes.literal_strong, "attr"]`. The F2P pins the
# exact child sequence `([literal_strong,"attr"], " (", [pending_xref,...,"int"],
# ")", ...)`, so a swapped order FAILS — it would NOT resolve.
_RIVAL_ORDER_SWAP = _swap(
    _BASE, _BVFE_GOLD,
    """    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    # WRONG: emit the type token first, then the name token
    par = [type_node, name_node]  # type: List[FieldNode]
    return par""")

# (U4 — make_xref node-KIND inversion) Inside the make_xref deep model the rival
# inverts the link decision: a present role yields a PLAIN node and an absent role
# a cross-reference. This VIOLATES X1 (Result().is_xref == (role != 0)).
# Rejection comes from make_xref's own postcondition X1 — the core node-kind
# decision the A-reference (G-AX) validates against the real Field.make_xref.
#
# Refinement: this is the renderer reading `if rolename:` instead of `if not
# rolename:` — it would link the (role-less) name token AND un-link the (class-
# role) type token. The F2P observes a plain name + class-xref type; an inverted
# make_xref produces the exact opposite, so it would NOT resolve. (Layer-1 of
# axiom_check.py pins this against the real callee over 14 role observations.)
_RIVAL_MAKEXREF_INVERT = _swap(
    _BASE, _MAKEXREF_GOLD,
    """    if role != 0:
        return FieldNode(False, 0)
    return FieldNode(True, role)""")

# (U5 — make_xref REFTYPE mask) The rival gets the link DECISION right but pins
# the wrong reference kind: a present role still links, but it carries reftype 0
# (the "no role" sentinel) instead of the role it renders under. It satisfies X1
# but VIOLATES X2 (Result().reftype == role). Rejection comes from the
# reftype-pin clause X2 — exactly the clause G-MUT records as needed to kill the
# reftype mutants (meta.gates G-MUT note).
#
# Refinement: a renderer that built the cross-reference with `reftype=''`/a wrong
# role would propagate as the type token's reftype != 'class'. The F2P pins
# `reftype="class"` on the type cross-reference (`assert_node(... reftype=
# "class")`), so a masked reftype FAILS — it would NOT resolve.
_RIVAL_MAKEXREF_REFTYPE_MASK = _swap(
    _BASE, _MAKEXREF_GOLD,
    """    if role != 0:
        return FieldNode(True, 0)
    return FieldNode(False, 0)""")

# (U6 — RESULT-mutation sanity, stands in for the absent frame-mutation lane)
# There is no read-only caller input to clobber, but we still confirm the spec
# pins the FINAL state of the freshly-built result rather than an intermediate.
# The rival builds the correct [name, type] list, then OVERWRITES element 0 with
# a fresh LINKING node (a cross-reference) after the fact. The post-state
# Result()[0] now links, VIOLATING P2. Rejection comes from P2 being evaluated on
# the returned object's final field values, not on a transient.
#
# Refinement: an impl that ended up with a linking name token — by any route,
# in-place mutation included — renders the `:var` name as a `pending_xref`, which
# the F2P rejects (must be `literal_strong`). It would NOT resolve.
_RIVAL_RESULT_MUTATE = _swap(
    _BASE, _BVFE_GOLD,
    """    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    # WRONG: overwrite the (correct) plain name token with a linking node
    relink = make_xref(rendered_role(type_role, type_target_is_null))
    par[0] = relink
    return par""")

# (U7 — SKIPPED NORMALISATION, the clause the faithfulness repair added) The
# rival builds the type token under the CONFIGURED type-role directly, without
# normalising it against the type target. On every target other than the null
# one that is indistinguishable from gold; on the null target the configured
# type-reference role must give way to the fallback role, and this rival keeps
# the type-reference role. It satisfies P1/P2/P3 but VIOLATES P4
# (Result()[1].reftype == rendered_role(type_role, type_target_is_null)).
# Rejection comes from P4 — the clause that states the type-token reftype the
# real renderer actually guarantees, rather than the configured role alone.
#
# Refinement: this rival IS the renderer without the null-target remap, i.e. a
# real tree with `PyTypedField.make_xref`'s `rolename == 'class' and target ==
# 'None'` branch deleted. That branch is UNCHANGED code the gold patch does not
# touch, so deleting it is a behavioural regression on `:vartype: None` (the type
# token would emit a `class` cross-reference to the null value instead of the
# `obj` one the repo produces). PASS_TO_PASS coverage of the python domain's
# field rendering observes that remap, so it would NOT resolve.
_RIVAL_SKIP_NORMALISATION = _swap(
    _BASE, _BVFE_GOLD,
    """    name_role = 0
    name_node = make_xref(name_role)
    # WRONG: link the type token under its CONFIGURED role, skipping the
    # normalisation against the type target
    type_node = make_xref(type_role)
    par = [name_node, type_node]  # type: List[FieldNode]
    return par""")

# (U8 — OVER-EAGER normalisation) The mirror image of U7: the rival normalises
# the type role on EVERY target, i.e. it emits the fallback role whenever the
# target is null OR not, collapsing the type-reference role away entirely. It
# VIOLATES P4 on the ordinary (non-null) target, where the type token must carry
# the configured type-reference role. Rejection comes from P4 in the other
# direction, so the normalisation clause pins BOTH sides of the remap and cannot
# be satisfied by a blanket rewrite.
#
# Refinement: this is `PyTypedField.make_xref` with the `target == 'None'`
# conjunct dropped, so `:vartype: int` would render an `obj` cross-reference
# instead of the `class` one. The F2P pins `reftype="class"` on the `int` type
# token, so it FAILS — it would NOT resolve.
_RIVAL_OVEREAGER_NORMALISATION = _swap(
    _BASE, _BVFE_GOLD,
    """    name_role = 0
    name_node = make_xref(name_role)
    # WRONG: normalise unconditionally, not only against the null target
    type_node = make_xref(NULL_ROLE)
    par = [name_node, type_node]  # type: List[FieldNode]
    return par""")


# (U9 — NAME-token reftype forgery) The rival gets the name token's node KIND
# right (plain, so P2 holds) but fabricates a non-zero reference kind on it,
# bypassing make_xref entirely to construct the node by hand. Under P2 alone this
# was admissible: the entry postcondition pinned only `is_xref` on the name
# token, leaving its `reftype` unconstrained. It VIOLATES P2b
# (Result()[0].reftype == 0). Rejection comes from P2b, which pins the plain
# name token's reference kind to the "no role" sentinel.
#
# Refinement: the real renderer builds the name token through
# `make_xrefs(self.rolename, ...)` -> `Field.make_xref` (`docfields.py:63-73`),
# whose falsy-role branch `return contnode or innernode(target, target)` emits an
# `addnodes.literal_strong` — a plain inline node that has NO `reftype` key at
# all (bridge code 0 per mapping.md §2). No configuration produces a plain name
# token carrying a reference kind, so this impl corresponds to no real tree; a
# node fabricated with a stray reftype is not what `Field.make_xref` returns on
# the post-patch role-less `'variable'` field — it would NOT resolve.
_RIVAL_NAME_REFTYPE_FORGERY = _swap(
    _BASE, _BVFE_GOLD,
    """    # WRONG: plain name token, but forged with a non-zero reference kind
    name_node = FieldNode(False, 42)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    return par""")


# (U10 — NEVER DELIVERS THE ENTRY, whole domain) The rival hands the entry
# rendering straight back to itself, so no token is ever emitted and no entry is
# ever delivered. Every value clause (P1-P4) says what the entry LOOKS LIKE once
# it exists; on its own that is claimed only of runs that reach the return, so
# this rival satisfies all of them VACUOUSLY. It is rejected by the termination
# obligation the precondition states, and by nothing else — which is exactly why
# the obligation is part of the spec.
#
# Refinement: the faithful real impl is the renderer delegating one entry's
# rendering back to itself, so rendering `:var int attr:` never completes and
# F2P `test_info_field_list_var` never finishes. Measured: that patch applies,
# keeps 34/34 PASS_TO_PASS, and FAILS the F2P — it does NOT resolve.
_RIVAL_DIVERGE_SELF = _swap(
    _BASE, _BVFE_GOLD,
    """    # WRONG: hand the entry rendering back to itself, so the entry is never
    # delivered and every value clause below is met only vacuously
    par = build_variable_field_entry(type_role, type_target_is_null)
    return par""")


# (U11 — NEVER DELIVERS THE ENTRY on the null target only; PARTIAL DOMAIN) The
# sharper version of U10: the rival renders the entry correctly and then, on the
# null type target alone, spins without ever handing it back. On every other
# target it is byte-for-byte gold, so no value clause can separate it — the two
# tokens it builds are exactly the right ones. Rejected by the termination
# obligation, which is owed on EVERY admissible input, not merely on the ones an
# implementation chooses to answer. MEASURED both ways: against the unobligated
# spec this rival VERIFIES; with the obligation Nagini rejects it with
# 'Obligation leak check failed. Loop might not take all unsatisfied obligations
# from the context.'
#
# Refinement: its faithful real impl renders `:vartype: None` entries forever, so
# any build documenting a variable typed as the null value hangs. The null target
# is inside the modelled domain (the admissibility probe witnesses it), and the
# rendering of that target is what the type-token clause is stated through, so a
# rival that never delivers there does NOT resolve.
_RIVAL_DIVERGE_NULL_TARGET = _swap(
    _BASE, _BVFE_GOLD,
    """    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    # WRONG: on the null type target the tokens are built but the entry is
    # never handed back (correct on every other target -- partial domain)
    spin = 0
    while type_target_is_null and spin >= 0:
        Invariant(spin >= 0)
        spin = spin + 1
    par = [name_node, type_node]  # type: List[FieldNode]
    return par""")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY
# ===========================================================================

# (S1 — make_xref BRANCH-REORDER) Structurally different but CORRECT: test the
# absent-role case first, the present-role case second (no loop, no induction
# lemma needed — avoids the forward-append pitfall). Must VERIFY against X1/X2;
# if a faithful reordering cannot satisfy make_xref's postcondition, SPEC-TOO-
# STRONG.
_POS_MAKEXREF_REORDER = _swap(
    _BASE, _MAKEXREF_GOLD,
    """    if role == 0:
        return FieldNode(False, 0)
    return FieldNode(True, role)""")

# (S2 — build_variable_field_entry LITERAL/RESHAPE) Structurally different but
# CORRECT: drop the `name_role` local entirely and build the name token directly
# from the literal absent role `0`, spell the normalisation out inline with an
# explicit branch instead of calling the pure helper, and assemble the list via
# two appends instead of a single literal. Keeps every gold obligation (name
# plain, type linking under the NORMALISED role, order name-then-type). Must
# VERIFY against P1-P4; if not, SPEC-TOO-STRONG. This is the control that the
# normalisation clause is satisfiable by an impl that does not merely echo the
# spec's own helper call.
_POS_BVFE_RESHAPE = _swap(
    _BASE, _BVFE_GOLD,
    """    # No name role is configured: build the name token directly under the
    # absent role (literal 0), without the intermediate local.
    name_node = make_xref(0)
    # Spell the normalisation out inline rather than calling the pure helper.
    if type_role == TYPE_ROLE and type_target_is_null:
        type_node = make_xref(NULL_ROLE)
    else:
        type_node = make_xref(type_role)
    par = []  # type: List[FieldNode]
    par.append(name_node)
    par.append(type_node)
    return par""")


# ===========================================================================
# ADMISSIBILITY (precondition not too strong) — must VERIFY
# ===========================================================================

# (A1) Confirm Requires(type_role != 0) admits a normal F2P-shaped input, and
# that BOTH target cases are admissible (the null target is the reviewer's
# witness class and must stay inside the domain). The probe calls
# build_variable_field_entry on the type-reference role with the target non-null
# (the `:var int attr:` F2P shape) and again with the target null (the
# `:vartype: None` shape), asserting the postcondition holds in both. The calls'
# Requires (type_role != 0) is discharged by TYPE_ROLE != 0. If either call site
# failed to establish Requires — or if the null-target case were excluded from
# the domain — PRECOND-TOO-STRONG. The gold body is kept VERBATIM ahead of the
# probe so the function still satisfies its own postcondition.
#
# TERMINATION LEVELS. The probe is a SEPARATE method appended inside the impl
# region, not a self-call spliced into build_variable_field_entry's own body. The
# spec carries `Requires(MustTerminate(10))`, and a call is admissible only from
# a STRICTLY HIGHER level than the callee's, so a self-call at level 10 into
# level 10 leaves no room beneath it and Nagini reports
#   `Obligation leak check failed. Callee build_variable_field_entry might not
#    take all unsatisfied obligations from the caller.`
# That rejection is about the CALL SITE's level, not about the precondition, so
# leaving the self-call in place would report PRECOND-TOO-STRONG for a domain
# fact that is in fact perfectly establishable — a false finding against the
# spec. Driving the probe from `_admissibility_probe` at `MustTerminate(11)`
# restores the intended claim: 11 > the callee's 10, so the obligation
# transfers, and what the verifier then checks is exactly what this case exists
# to check — that both F2P-shaped argument pairs satisfy Requires and that the
# pinned post consequences follow. The probe is itself obligated, so it opens no
# hole: a diverging probe body would be rejected too.
_ADMISS_BVFE = _swap(
    _BASE, _BVFE_GOLD,
    """    # gold body (kept verbatim so this function still meets its postcondition)
    name_role = 0
    name_node = make_xref(name_role)
    type_node = make_xref(rendered_role(type_role, type_target_is_null))
    par = [name_node, type_node]  # type: List[FieldNode]
    return par


def _admissibility_probe() -> None:
    # admissibility probe: the precondition must admit a present type-role on
    # BOTH targets - the ordinary one and the null one. Driven from a level
    # STRICTLY ABOVE the entry builder's own obligation, so the termination
    # obligation transfers and the only thing under test here is the
    # precondition.
    Requires(MustTerminate(11))
    probe = build_variable_field_entry(TYPE_ROLE, False)
    Assert(len(probe) == 2)
    Assert(probe[0].is_xref is False)
    Assert(probe[1].is_xref is True)
    Assert(probe[1].reftype == TYPE_ROLE)
    probe_null = build_variable_field_entry(TYPE_ROLE, True)
    Assert(len(probe_null) == 2)
    Assert(probe_null[0].is_xref is False)
    Assert(probe_null[1].is_xref is True)
    Assert(probe_null[1].reftype == NULL_ROLE)""")


SPEC_TESTS = [
    {
        "id": "pos-makexref-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAKEXREF_REORDER,
        "rationale": "a branch-reordered but correct make_xref (absent case first) "
                     "must satisfy X1/X2; else SPEC-TOO-STRONG. No induction/lemma "
                     "needed (no loop), so a verify failure would be a real spec defect.",
    },
    {
        "id": "pos-bvfe-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BVFE_RESHAPE,
        "rationale": "a correct build_variable_field_entry that drops the name_role "
                     "local, spells the normalisation out inline instead of calling the "
                     "pure helper, and assembles via two appends must satisfy P1-P4; "
                     "else SPEC-TOO-STRONG. Keeps every gold obligation, changes only "
                     "shape — and shows P4 is satisfiable without echoing the spec's "
                     "own helper call.",
    },
    {
        "id": "admiss-bvfe-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_BVFE,
        "rationale": "self-calls build_variable_field_entry(TYPE_ROLE, False) and "
                     "(TYPE_ROLE, True) on an in-domain present type-role establish "
                     "Requires(type_role != 0) and their asserted postconditions on "
                     "BOTH targets; if either could not, PRECOND-TOO-STRONG. The "
                     "null-target case is the reviewer's witness class and must stay "
                     "admissible.",
    },
    {
        "id": "rival-prepatch-namerole",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PREPATCH_NAMEROLE,
        "refinement": "a present name role IS the pre-patch name rolename; the faithful "
                      "real patch (config unchanged) renders the :var name token as a "
                      "pending_xref, so F2P test_info_field_list_var "
                      "(name must be [literal_strong,'attr']) FAILS — would NOT resolve.",
        "rationale": "rejected by P2 (Result()[0].is_xref is False) — the discriminating "
                     "no-auto-link clause; if it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-drop-type-link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_TYPE_LINK,
        "refinement": "building the type token under role 0 == a real patch that also "
                      "removed typerolename='class'; F2P asserts the type token is "
                      "pending_xref(reftype='class'), a plain type token FAILS — would "
                      "NOT resolve.",
        "rationale": "rejected by P3/P4 (type token must link and carry its normalised "
                     "type-role) — the companion clauses pinning the UNCHANGED type "
                     "cross-reference; if it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ORDER_SWAP,
        "refinement": "[type, name] order makes the paragraph's first child the int "
                      "cross-reference, not [literal_strong,'attr']; F2P pins the exact "
                      "child sequence (name first, parenthesised type second) — FAILS, "
                      "would NOT resolve.",
        "rationale": "rejected by the positional clauses P2 (Result()[0] plain) and P3 "
                     "(Result()[1] links); if it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-makexref-invert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_MAKEXREF_INVERT,
        "refinement": "inverting the link decision is `if rolename:` instead of `if not "
                      "rolename:` — it links the role-less name and un-links the class "
                      "type; the real renderer would produce the exact opposite of the "
                      "F2P-observed plain-name/class-xref-type pair — would NOT resolve.",
        "rationale": "rejected by make_xref's X1 (is_xref == (role != 0)) — the core "
                     "node-kind decision the A-reference validates against the real "
                     "Field.make_xref; if it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-makexref-reftype-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_MAKEXREF_REFTYPE_MASK,
        "refinement": "a present role that links but carries reftype 0 == a cross-"
                      "reference built with the wrong reference kind; this propagates "
                      "as the type token's reftype != 'class', which the F2P pins "
                      "(assert_node reftype='class') — FAILS, would NOT resolve.",
        "rationale": "rejected by make_xref's X2 (reftype == role) — the reftype-pin "
                     "clause G-MUT records as needed to kill the reftype mutants; if it "
                     "verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-result-mutate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_RESULT_MUTATE,
        "refinement": "overwriting the (correct plain) name token with a linking node "
                      "yields a name token that links by ANY route; the rendered :var "
                      "name would be a pending_xref, which the F2P rejects (must be "
                      "literal_strong) — would NOT resolve.",
        "rationale": "rejected by P2 evaluated on the returned object's FINAL field "
                     "values (post-state), not on a transient; if it verified, the spec "
                     "would admit a linking-name impl (SPEC-TOO-WEAK).",
    },
    {
        "id": "rival-skip-normalisation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SKIP_NORMALISATION,
        "refinement": "linking the type token under the CONFIGURED role, unnormalised, "
                      "is the real PyTypedField.make_xref with its null-target remap "
                      "branch deleted — UNCHANGED code the gold patch does not touch. On "
                      ":vartype: None the type token would carry the type-reference role "
                      "instead of the fallback role the repo emits, a regression on "
                      "python-domain field rendering — would NOT resolve.",
        "rationale": "rejected by P4 (reftype == rendered_role(type_role, "
                     "type_target_is_null)) — the clause stating the type-token reftype "
                     "the real renderer actually guarantees. This is the rival the "
                     "faithfulness repair exists to kill: under the previous, "
                     "unnormalised P4 it WAS the frozen impl. If it verified, the spec "
                     "would have no teeth on the null target (SPEC-TOO-WEAK).",
    },
    {
        "id": "rival-name-reftype-forgery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NAME_REFTYPE_FORGERY,
        "refinement": "the real name token comes from Field.make_xref's falsy-role "
                      "branch (`return contnode or innernode(target, target)`, "
                      "docfields.py:63-73), which emits a plain addnodes.literal_strong "
                      "with no reftype key at all (bridge code 0). No configuration "
                      "yields a plain name token carrying a reference kind, so this "
                      "impl corresponds to no real tree — would NOT resolve.",
        "rationale": "rejected by P2b (Result()[0].reftype == 0). Under P2 alone the "
                     "entry postcondition pinned only the name token's node KIND and "
                     "left its reference kind free, so this impl VERIFIED; P2b closes "
                     "that hole. If it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-overeager-normalisation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OVEREAGER_NORMALISATION,
        "refinement": "normalising on EVERY target is PyTypedField.make_xref with the "
                      "`target == 'None'` conjunct dropped, so :vartype: int would emit "
                      "an obj cross-reference; the F2P pins reftype='class' on the int "
                      "type token — FAILS, would NOT resolve.",
        "rationale": "rejected by P4 in the opposite direction from U7, so the "
                     "normalisation clause pins BOTH sides of the remap and cannot be "
                     "satisfied by a blanket rewrite; if it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-nonterminating-self-delegation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DIVERGE_SELF,
        "refinement": "the entry rendering is handed back to itself, so no token is "
                      "ever emitted and no entry is ever delivered. Its faithful real "
                      "impl renders one :var entry by delegating to itself, so "
                      "rendering `:var int attr:` never completes: MEASURED through "
                      "the official harness, the patch applies, keeps PASS_TO_PASS "
                      "34/34, and FAILS F2P test_info_field_list_var — it does NOT "
                      "resolve.",
        "rationale": "rejected by the termination obligation the precondition states: "
                     "the entry must be delivered in a bounded number of steps for "
                     "every admissible input. Without that obligation P1-P4 are "
                     "claimed only of runs that REACH the return, so this rival meets "
                     "every one of them VACUOUSLY and verifies — a measured verify-"
                     "not-resolve hole, not a hypothetical one. Verifier output with "
                     "the obligation present: 'Obligation leak check failed. Callee "
                     "build_variable_field_entry might not take all unsatisfied "
                     "obligations from the caller.' If it verified, SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-nonterminating-on-null-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DIVERGE_NULL_TARGET,
        "refinement": "builds exactly the gold pair of tokens and then, on the null "
                      "type target ALONE, never hands the entry back; on every other "
                      "target it is gold. Its faithful real impl renders `:vartype: "
                      "None` entries forever, so a build documenting a variable typed "
                      "as the null value hangs — that target is inside the modelled "
                      "domain and is the one the type-token clause is stated through, "
                      "so it does NOT resolve.",
        "rationale": "rejected by the termination obligation, which is owed on EVERY "
                     "admissible input rather than only where an implementation "
                     "chooses to answer. No VALUE clause can separate this rival — "
                     "the tokens it builds are the right ones — so it is the sharpest "
                     "check that the obligation, and not a value clause, is what "
                     "carries the partial-domain divergence lane. Verifier output: "
                     "'Obligation leak check failed. Loop might not take all "
                     "unsatisfied obligations from the context.' If it verified, "
                     "SPEC-TOO-WEAK.",
    },
]

# No @ContractOnly axioms are consumed (meta.axioms == []). The three deep models
# (rendered_role, make_xref, build_variable_field_entry) are A-reference and
# validated against the real sphinx callees by axiom_check.py (G-AX), which
# exercises the null-target remap directly. The PBT axiom lane adds no new
# in-container probe beyond that soundness check; AXIOM_TESTS is therefore empty
# by design (see 'assessment').
AXIOM_TESTS = []
