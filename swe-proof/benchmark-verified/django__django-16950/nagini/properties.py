# properties.py — PBT falsification battery for django__django-16950.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   reset_default_related_key(instance: ParentObject, adding, key_has_default,
#                             key_is_primary, form_data_present) -> None
#   models the inline-formset add_fields clearing block: while a parent is being
#   ADDED, the parent's related-key value (instance.key: Optional[int]) is reset
#   to None EXACTLY when should_clear(...) holds, else preserved unchanged.
#   should_clear is a @Pure GROUNDED predicate (fully unfolded function of the 4
#   bool args, no opaque callee):
#       should_clear = adding and key_has_default and (key_is_primary or not form_data_present)
#   The postcondition pins the post-state with THREE load-bearing clauses:
#       (F)  Ensures(Acc(instance.key))                              [frame]
#       (C)  Implies(should_clear(...),     instance.key is None)    [clear case]
#       (P)  Implies(not should_clear(...), instance.key is Old(instance.key))  [preserve]
#   instance.key is held at FULL permission (Requires(Acc(instance.key)), not
#   Acc(.,1/2)) because the clear path GENUINELY mutates it — so there is no
#   read-only Acc(.,1/2) input and no insufficient-permission frame attack; the
#   four guard conditions are read-only bool SCALARS (no permission carrier). See
#   'assessment' for the frame-class note.
#   The PRECONDITION additionally carries a total-correctness obligation:
#       (T)  Requires(MustTerminate(2))
#   Under partial-correctness semantics a DIVERGING body (`while True: pass`) or
#   a same-measure SELF-CALL satisfies (C)/(P) vacuously — the G-PANEL-1 auditor
#   built exactly such a same-spec wrong impl (atk_7). Nagini's obligation-leak
#   check rejects a loop that does not take the unsatisfied obligation and a
#   self-call at a non-decreasing measure. ParentObject.__init__ carries
#   MustTerminate(1) (strictly smaller), so constructing a probe parent inside a
#   variant remains admissible. The weak-diverge and weak-self-echo rivals below
#   pin this lane.
#
# F2P: test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data
#      — alternate key (is_pk=False) + has_default + WITH form data while adding
#        => should_clear is False => the generated key MUST be PRESERVED. This is
#        the case the gold patch fixes (pre-patch wrongly cleared it). Pinned by
#        clause (P).
# P2P: #24377 (inlines ignore default; adding pk auto-generated) + #24958 variant
#      (alternate key, NO data => clear). Those are the should_clear==True cases,
#      pinned by clause (C); a rival that never clears would break them.
#
# No @ContractOnly axioms / A-reference deep models (axioms region empty;
# meta.json axioms == []; refinement.md C: every step R or I, the changed guard
# is a concrete I step). AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-16950"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl body (the # impl-start/# impl-end block of model.py) — the
# post-patch clearing decision. Every rival edits ONLY text inside that block.
# ---------------------------------------------------------------------------
_IMPL = """    if adding:
        if key_has_default and (key_is_primary or not form_data_present):
            instance.key = None"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but EQUIVALENT impl: collapse the nested guard into a
# single boolean computed in a local, then one conditional store. Same decision
# (adding and has_default and (is_pk or not data)), different executable shape
# (flatten + local-variable reshape — directive-2/3 safe: no loop, no fold, no
# dropped framing assert; the postcondition has no per-element invariant to keep).
# Must verify; if a faithful correct impl cannot => SPEC-TOO-STRONG.
_POS_FLAT = """    clear = adding and key_has_default and (key_is_primary or not form_data_present)
    if clear:
        instance.key = None"""
POS_FLAT = _swap(_BASE, _IMPL, _POS_FLAT)


# === POSITIVE CONTROL #2 (soundness) ======================================
# A second equivalent shape: branch-reorder — test the (is_pk or not data)
# disjunct as the OUTER guard, has_default + adding inner. De Morgan-free, same
# truth value on all 16 combinations. Keeps the conditional single store.
_POS_REORDER = """    if key_is_primary or not form_data_present:
        if adding and key_has_default:
            instance.key = None"""
POS_REORDER = _swap(_BASE, _IMPL, _POS_REORDER)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (spec_view only elides the
# impl region — anything at module level enters the spec signature). A
# self-recursive call to reset_default_related_key from inside its own body
# would need a Decreases termination measure the spec does NOT carry (a PROOF
# gap, not a spec defect — directive-3 trap). So the admissibility check lives
# INSIDE the impl region, inserted right after # impl-start and BEFORE the gold
# obligation: construct a concrete F2P-shaped ParentObject (a generated default =
# a non-None int), establish/read the Requires field (Acc(instance.key)), and
# assert the @Pure decision predicate evaluates as expected on the FAIL_TO_PASS
# configuration (adding,has_default,not-pk,data => should_clear False => the key
# must be PRESERVED). If the precondition cannot be established for this normal
# input the block fails => PRECOND-TOO-STRONG. The gold obligation below is kept.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P-shaped parent (generated default
    # int 7) must satisfy the precondition (the key field is readable) and the
    # decision predicate must classify the alternate-key-with-data case as
    # PRESERVE (should_clear False). No self-call (no Decreases in the spec).
    probe = ParentObject(7)
    Assert(probe.key == 7)                                  # Acc(probe.key) readable
    Assert(not should_clear(True, True, False, True))       # F2P case => preserve
    Assert(should_clear(True, True, True, True))            # pk-with-data => clear
    Assert(should_clear(True, True, False, False))          # alt-key no-data => clear"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- R1 PRE-PATCH shape (the bug): clear whenever adding and has_default,
# ignoring (is_pk or not data). Correct on every clear/preserve case EXCEPT the
# FAIL_TO_PASS sub-domain (adding, has_default, NOT pk, data present), where it
# clears a value the spec pins as PRESERVED. This is exactly model_prepatch.py.
# refinement: this IS the pre-patch guard `if to_field.has_default():`; the F2P
# test_..._alternate_key_relation_data asserts formset.instance.uuid is NOT None
# and forms[0].instance.parent_id == that uuid — pre-patch nulls the uuid, so
# both assertions fail and it does NOT resolve (this is the bug the patch fixes).
# rejection source: clause (P) Implies(not should_clear(...), key is Old(key)) —
# on the FAIL_TO_PASS case should_clear is False but the impl writes None.
_R1_PREPATCH = """    if adding:
        if key_has_default:
            instance.key = None"""
PREPATCH_BUG = _swap(_BASE, _IMPL, _R1_PREPATCH)


# --- R2 DROP THE PK DISJUNCT: clear only when (adding and has_default and not
# data) — drop the `key_is_primary or` arm, so a pk relation WITH form data is
# wrongly PRESERVED. Correct on the alternate-key cases; diverges on the
# pk-with-data sub-domain (should_clear True, but the impl does not clear).
# refinement: a real patch writing `... and (not form.data)` (omitting the
# `to_field.attname == ...pk.name or` disjunct) would FAIL to clear the parent's
# auto-generated pk when form data is submitted — P2P #24377 "If we're adding a
# new object, a parent's auto-generated pk" expects that pk cleared; it would NOT
# resolve.
# rejection source: clause (C) Implies(should_clear(...), key is None) — on
# (adding, hd, is_pk=True, data=True) should_clear is True but key stays Old.
_R2_DROP_PK = """    if adding:
        if key_has_default and not form_data_present:
            instance.key = None"""
DROP_PK_ARM = _swap(_BASE, _IMPL, _R2_DROP_PK)


# --- R3 DROP THE has_default GUARD: clear whenever adding and (is_pk or not
# data), even when the key carries NO default. Correct on every has_default case;
# diverges on the no-default sub-domain (should_clear False because hd False, but
# impl clears). Clears a real user-supplied value that was never a default.
# refinement: a real patch that dropped the `to_field.has_default() and` conjunct
# would null a non-default related key that the user actually set — P2P #24377
# "Inlines with a model field default should ignore that default" pins clearing
# to the HAS-default case; nulling a non-default key changes observable behaviour
# and would NOT resolve.
# rejection source: clause (P) — on (adding, hd=False, is_pk=True, data=False)
# should_clear is False but the impl writes None.
_R3_DROP_HD = """    if adding:
        if key_is_primary or not form_data_present:
            instance.key = None"""
DROP_HASDEFAULT = _swap(_BASE, _IMPL, _R3_DROP_HD)


# --- R4 IGNORE `adding`: clear whenever has_default and (is_pk or not data),
# even for a PERSISTED parent (adding False). Correct on every adding=True case;
# diverges on the not-adding sub-domain (should_clear False because adding False,
# yet impl clears) — wrongly nulls an EXISTING parent's key.
# refinement: a real patch dropping the outer `if self.instance._state.adding:`
# guard would reset the related key of an already-persisted parent every time an
# inline child form is built — P2P #24377 / #24958 only clear while ADDING; an
# existing parent's key would be destroyed, breaking edits and so NOT resolving.
# rejection source: clause (P) — on (adding=False, hd=True, is_pk=True, data=F)
# should_clear is False but the impl writes None.
_R4_IGNORE_ADDING = """    if key_has_default and (key_is_primary or not form_data_present):
        instance.key = None"""
IGNORE_ADDING = _swap(_BASE, _IMPL, _R4_IGNORE_ADDING)


# --- R5 OR-vs-AND swap on the inner disjunct: clear when adding and has_default
# and (is_pk AND not data) — replace the `or` with `and`. Tighter clearing.
# Correct everywhere the disjuncts agree; diverges on (is_pk True, data True):
# should_clear True (is_pk arm) but the AND requires not-data, so it does NOT
# clear. A pk relation WITH form data is wrongly preserved.
# refinement: a real patch writing `... and (is_pk and not form.data)` would
# leave a parent's auto-generated PK populated when the pk relation has form data
# — P2P #24377 pk-clearing case expects None; it would NOT resolve.
# rejection source: clause (C) — on (adding, hd, is_pk=True, data=True)
# should_clear is True but key stays Old.
_R5_AND = """    if adding:
        if key_has_default and (key_is_primary and not form_data_present):
            instance.key = None"""
AND_DISJUNCT = _swap(_BASE, _IMPL, _R5_AND)


# --- R6 FRAME-FLAVOUR write on the PRESERVE path: in the should-NOT-clear
# branch, write a (non-None, non-Old) value into instance.key. instance.key is
# FULL-permission so the write is ALLOWED by the permission system — the
# rejection therefore comes from the PRESERVE postcondition (P), not from
# insufficient permission (there is no Acc(.,1/2) input here; see 'assessment').
# This catches an impl that "touches" the key on a path the spec pins unchanged.
# refinement: a real patch that, on the don't-clear branch, wrote any value other
# than the existing one (e.g. setattr(self.instance, to_field.attname, <new>))
# would corrupt the parent's freshly generated alternate key — the F2P data case
# asserts parent_id == the ORIGINAL uuid; a mutated key would mismatch and NOT
# resolve.
# rejection source: clause (P) Implies(not should_clear(...), key is Old(key)) —
# the written value (999) is neither None nor Old(instance.key).
_R6_FRAME = """    if adding:
        if key_has_default and (key_is_primary or not form_data_present):
            instance.key = None
        else:
            instance.key = 999
    else:
        instance.key = 999"""
FRAME_PRESERVE_WRITE = _swap(_BASE, _IMPL, _R6_FRAME)


# --- R7 NO-OP rival (clear nothing): do nothing at all. Trivially preserves the
# key on every preserve case (clause P holds vacuously where Old==current), but
# FAILS clause (C) on every genuine-clear case — never nulls a value the spec
# requires nulled. The mirror of R1: it never clears instead of always clearing.
# refinement: this is the "remove the clearing block entirely" patch; P2P #24377
# "Inlines with a model field default should ignore that default" and #24958 both
# require the auto-generated key cleared in their (no-data / pk) configurations —
# leaving it populated reintroduces the original validation failure, so it does
# NOT resolve.
# rejection source: clause (C) Implies(should_clear(...), key is None) — on a
# genuine clear case (adding, hd, is_pk, no data) should_clear is True but the
# impl leaves Old(key) in place.
_R7_NOOP = """    pass"""
NOOP = _swap(_BASE, _IMPL, _R7_NOOP)


# --- R8 DIVERGE (control-flow-effect / vacuous-by-divergence): the body is an
# infinite loop. Under partial-correctness semantics it satisfies clauses
# (C)/(P) vacuously (no terminating path on which they could fail) — this is
# the same-spec wrong-impl class the G-PANEL-1 auditor exploited (atk_7).
# refinement: a real patch inserting `while True: pass` at the top of the
# add_fields clearing block hangs form construction forever — the F2P/P2P
# tests never reach their assertions (the run times out), so it does NOT
# resolve.
# rejection source: clause (T) Requires(MustTerminate(2)) — Nagini's
# obligation-leak check flags a loop that does not take the unsatisfied
# termination obligation.
_R8_DIVERGE = """    while True:
        pass"""
DIVERGE = _swap(_BASE, _IMPL, _R8_DIVERGE)


# --- R9 SELF-ECHO: discharge the whole contract by calling the function under
# spec itself. Under partial correctness the self-call "returns" with both
# postconditions established for free, while its faithful refinement is
# infinite recursion (add_fields' clearing step re-entering itself), which
# RecursionErrors / never returns — the F2P fails.
# rejection source: the obligation-leak check — the self-call would take the
# same MustTerminate(2) obligation without a strictly smaller measure.
_R9_SELF_ECHO = """    reset_default_related_key(instance, adding, key_has_default,
                              key_is_primary, form_data_present)"""
SELF_ECHO = _swap(_BASE, _IMPL, _R9_SELF_ECHO)


SPEC_TESTS = [
    {
        "id": "pos-flat",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_FLAT,
        "rationale": "structurally-different CORRECT impl (guard flattened into a "
        "single boolean local + one conditional store) — same decision on all 16 "
        "combinations. Must verify, else SPEC-TOO-STRONG. No loop/fold/framing "
        "assert to drop (the postcondition is over a single field), so directive-2/3 "
        "do not bite.",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "second structurally-different CORRECT impl (the (is_pk or not "
        "data) disjunct hoisted to the OUTER branch, adding+has_default inner) — same "
        "truth value everywhere. Must verify; a branch reorder keeping the single "
        "store is directive-3 safe.",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control caller constructs an F2P-shaped ParentObject "
        "(default int 7) and invokes reset_default_related_key for the FAIL_TO_PASS "
        "config (adding,hd,not-pk,data); the Requires(Acc(instance.key)) must admit "
        "this normal input and the preserve postcondition must yield key==7. If the "
        "precondition cannot be established => PRECOND-TOO-STRONG.",
    },
    {
        "id": "prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PREPATCH_BUG,
        "refinement": "this IS the pre-patch guard `if to_field.has_default():` "
        "(model_prepatch.py). The F2P test_..._alternate_key_relation_data asserts "
        "formset.instance.uuid is NOT None and forms[0].instance.parent_id == that "
        "uuid; pre-patch nulls the uuid on the alternate-key-with-data case, so both "
        "assertions fail and it does NOT resolve — it is the bug the patch fixes.",
        "rationale": "rejected by clause (P) Implies(not should_clear(...), key is "
        "Old(key)): on (adding,hd,not-pk,data) should_clear is False (PRESERVE) yet "
        "the impl writes None. PRIMARY partial-domain rival — diverges exactly on the "
        "FAIL_TO_PASS sub-domain.",
    },
    {
        "id": "drop-pk-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_PK_ARM,
        "refinement": "a real patch writing `has_default() and (not form.data)` "
        "(omitting the `attname == ...pk.name or` disjunct) would NOT clear a "
        "parent's auto-generated PK when form data is submitted — P2P #24377 'If "
        "we're adding a new object, a parent's auto-generated pk' expects that pk "
        "cleared; it would NOT resolve.",
        "rationale": "rejected by clause (C) Implies(should_clear(...), key is None): "
        "on (adding,hd,is_pk=True,data=True) should_clear is True (CLEAR) but key "
        "stays Old. partial-domain (pk-with-data sub-domain).",
    },
    {
        "id": "drop-hasdefault",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_HASDEFAULT,
        "refinement": "a real patch dropping the `to_field.has_default() and` conjunct "
        "would null a non-default related key the user actually set — P2P #24377 "
        "'Inlines with a model field default should ignore that default' pins "
        "clearing to the HAS-default case; nulling a non-default key changes "
        "observable behaviour and would NOT resolve.",
        "rationale": "rejected by clause (P): on (adding,hd=False,is_pk=True,data=F) "
        "should_clear is False (PRESERVE) but the impl writes None. partial-domain "
        "(no-default sub-domain).",
    },
    {
        "id": "ignore-adding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": IGNORE_ADDING,
        "refinement": "a real patch dropping the outer `if self.instance._state."
        "adding:` guard would reset the related key of an already-PERSISTED parent "
        "whenever an inline child form is built — P2P #24377/#24958 only clear while "
        "ADDING; an existing parent's key would be destroyed, breaking edits, so it "
        "would NOT resolve.",
        "rationale": "rejected by clause (P): on (adding=False,hd=True,is_pk=True,"
        "data=False) should_clear is False (PRESERVE) but the impl writes None. "
        "partial-domain (not-adding sub-domain).",
    },
    {
        "id": "and-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": AND_DISJUNCT,
        "refinement": "a real patch writing `(is_pk and not form.data)` instead of "
        "`(is_pk or not form.data)` would leave a parent's auto-generated PK "
        "populated when the pk relation has form data — P2P #24377 pk-clearing case "
        "expects None; it would NOT resolve.",
        "rationale": "rejected by clause (C): on (adding,hd,is_pk=True,data=True) "
        "should_clear is True (CLEAR, via the is_pk arm) but the AND requires "
        "not-data, so key stays Old. partial-domain (pk-with-data sub-domain).",
    },
    {
        "id": "frame-preserve-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_PRESERVE_WRITE,
        "refinement": "a real patch that, on the don't-clear branch, wrote any value "
        "other than the existing one (setattr(self.instance, to_field.attname, "
        "<other>)) would corrupt the parent's freshly generated alternate key — the "
        "F2P data case asserts parent_id == the ORIGINAL uuid; a mutated key would "
        "mismatch and NOT resolve.",
        "rationale": "rejected by clause (P): the written value 999 is neither None "
        "nor Old(instance.key). NOTE: instance.key is FULL-permission (not Acc(.,1/2)) "
        "because the clear path mutates it, so this is caught by the PRESERVE "
        "postcondition, not by insufficient permission — see 'assessment'. "
        "frame-mutation flavour + control-flow-effect (writes on a path pinned "
        "unchanged).",
    },
    {
        "id": "noop-never-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": NOOP,
        "refinement": "this is the 'remove the clearing block entirely' patch; P2P "
        "#24377 ('ignore that default') and #24958 (alternate key, no data) both "
        "require the auto-generated key cleared in their configurations — leaving it "
        "populated reintroduces the original validation failure, so it does NOT "
        "resolve.",
        "rationale": "rejected by clause (C) Implies(should_clear(...), key is None): "
        "on a genuine clear case (adding,hd,is_pk,no-data) should_clear is True but "
        "the impl leaves Old(key) in place. The mirror of prepatch-bug (never clears "
        "vs always clears).",
    },
    {
        "id": "weak-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DIVERGE,
        "refinement": "a real patch inserting `while True: pass` at the top of the "
        "add_fields clearing block (the G-PANEL-1 atk_7 attack class) hangs inline "
        "form construction forever: the F2P/P2P tests never reach their assertions "
        "(the run times out), so it does NOT resolve.",
        "rationale": "REJECTED by clause (T) Requires(MustTerminate(2)): a body that "
        "loops forever cannot take the unsatisfied termination obligation, so Nagini "
        "fails the obligation-leak check ('Loop might not take all unsatisfied "
        "obligations from the context'). Without (T) the body satisfies (C)/(P) "
        "VACUOUSLY under partial correctness — exactly the weakness the auditor "
        "exploited. If it VERIFIES => SPEC-TOO-WEAK (divergence admitted).",
    },
    {
        "id": "weak-self-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SELF_ECHO,
        "refinement": "the faithful refinement is the clearing step re-entering "
        "itself — infinite recursion that RecursionErrors (or never returns) before "
        "deciding anything, so form construction fails and the F2P does NOT resolve.",
        "rationale": "REJECTED by the obligation-leak check: reset_default_related_key "
        "Requires(MustTerminate(2)); the self-call would have to take the same "
        "obligation without a strictly smaller measure ('Callee "
        "reset_default_related_key might not take all unsatisfied obligations from "
        "the caller'). Closes the function-under-spec self-echo escape. If it "
        "VERIFIES => SPEC-TOO-WEAK.",
    },
]


# No @ContractOnly axioms and no A-reference deep models: the axioms region is
# empty (model.py:42-45), meta.json axioms == [], and refinement.md §C states
# every step is R or I (the changed guard is a concrete I step under R on the
# three booleans; should_clear is a deep @Pure spec, not an opaque callee). The
# decision-table behavioural-equivalence check lives in axiom_check.py (G-AX) and
# is not a @ContractOnly axiom obligation, so there is nothing for the PBT axiom
# lane (real-callee soundness/containment) to run.
AXIOM_TESTS = []
