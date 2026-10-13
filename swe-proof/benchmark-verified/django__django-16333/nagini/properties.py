"""properties.py — PBT falsification battery for django__django-16333.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes. Each SPEC_TEST is a FULL model.py variant built
by region-surgery — editing ONLY text inside the single `# impl-start` /
`# impl-end` block of `save_form`. The frozen spec (axioms / pure / pre- /
post-conditions, including the @ContractOnly capability predicate
`relations_done` and the MustTerminate obligations) is NEVER touched, so
`same_spec(base, variant)` holds for every case. Spec cases are checked by
Nagini verify on the host; expect="verify" passes iff (same_spec AND verifies),
expect="reject" passes iff (same_spec AND does NOT verify).

DEFENDED SURFACE (what this spec actually pins):
  save_form(self: Form, commit: bool) -> Form models UserCreationForm.save. The
  carrier Form holds two observable booleans (record_persisted, deferred_save_
  ready) behind the abstraction predicate form_pred(), read via @Pure accessors
  get_record/get_ready. Those two facts are held at READ-ONLY (1/2) permission
  inside form_pred, so an implementation can OBSERVE them and cannot SET either:
  each becomes true only by really running the step whose contract claims that
  effect (persist_record for the record fact, base_form_save_deferred for the
  deferred-save fact). This is what makes "the primary record is written" mean
  the write happened -- and, since run_deferred_save's Requires(get_record() is
  True) tests the same fact, it is also what stops the deferred save's ordering
  condition from being met by fiat instead of by the real write (the
  atk_fiat_record / atk_fiat_then_deferred cases below). The discriminating
  relational-data fact is NOT a value at all but the abstract per-form
  CAPABILITY relations_done(self): a @ContractOnly @Predicate with NO body,
  granted SOLELY by run_deferred_save(self)'s Ensures.
  The form's model RECORD OBJECT is named by a second body-less per-form
  capability record_available(self), which the form ALREADY HOLDS on entry (the
  object is built from the submitted data during validation, before this routine
  runs). Every step Requires and Ensures it, and so does save_form, so it
  constrains NO order -- it records only that all the steps, and the returned
  value, concern that same one object. The positive control
  atk_record_write_before_base_save (expect="verify") pins that: an
  implementation may write the primary record before invoking the base-form save
  and must still verify, because the repo permits exactly that order.

  Load-bearing postcondition clauses:
    Ensures(record_available(self))                           # same record object, handed back
    Ensures(self.get_ready() is True)                         # deferred save set up
    Ensures(Implies(commit, self.get_record() is True))       # record written on commit
    Ensures(Implies(commit, relations_done(self)))            # <== DISCRIMINATING:
        only run_deferred_save(self) earns the capability: no other callee's
        postcondition grants it however often it is invoked (weak-fiat-no-producer,
        a VIPER rejection on this clause), there is no relational field to assign,
        and a capability for a scratch form is relations_done(scratch) !=
        relations_done(self). Folding it by hand is closed one level earlier, by
        the front end (abstract.predicate.fold): that is a fact about the
        encoding, not a verdict Viper reached, so no reject case rests on it.
    Ensures(Implies(not commit, self.get_record() is False))  # nothing written when not committing
    Ensures(Result() is self)

  Preconditions: form_pred() (see the frame note below — the predicate is held
    in full by the caller, but the two facts INSIDE it are read-only, so the
    routine may pass it to the callees and still cannot write either fact),
    get_record() is False, record_available(self), and
    MustTerminate(2). The three callees each Requires(MustTerminate(1)) — a
    strictly smaller measure — so the function-under-spec self-echo (return
    save_form(self, commit)) is forbidden by the obligation-leak check
    (DEFECT-5). record_available(self) is required at entry and by every callee
    and ensured by all of them, so it forbids no ordering; the object is present
    throughout, exactly as in the repo, where the form built it while
    validating. Callee ORDER is constrained only where the real code constrains
    it: run_deferred_save's Requires(get_record() is True) means the deferred
    relational save may run only after the record write has REALLY happened
    (the atk_deferred_before_record case), and the read-only grounding above is
    what makes that unforgeable.

  ENTRY DOMAIN — the deferred-save fact is UNCONSTRAINED at entry, and that is
    load-bearing. get_ready() names "a deferred relational save is set up for
    this form"; asking for deferred persistence is exactly what sets one up, so
    the same form may be asked for immediate persistence afterwards and the
    routine is then entered with get_ready() already True. The repo's own
    passing suite drives that sequence. Requiring get_ready() is False at entry
    would leave the routine's behaviour on the whole re-entered half of its
    domain unclaimed: since NO postcondition mentions the ENTRY value of
    get_ready(), that half is not a case the spec constrains weakly, it is a case
    the spec does not reach at all, and an implementation may branch on it and
    persist nothing (or not return) while every clause is still discharged
    vacuously. The clauses above are therefore claimed on both entry states,
    which is what makes "committing writes the primary record and leaves the
    relational data written" a guarantee about persistence rather than about
    freshness. The atk_reentrant_* cases below are that half of the domain: each
    of them VERIFIED against the earlier, narrower entry domain (where the
    branch they take is dead code) and is rejected now. The record fact, by
    contrast, stays False at entry — this routine is what writes it, so that is
    what makes the record clauses claims about a write it performed, and it is
    the entry state the repo's callers are in.

FRAME / FIAT (#1 weakness class) — APPLICABLE and MANDATORY here, in BOTH of
  the spec's observable facts and in the capability. save_form enters with
  Requires(self.form_pred()), which it must, since it hands that permission to
  the callees that legitimately move the facts. But form_pred holds each
  underlying boolean at 1/2 (read-only) permission, so unfolding it yields no
  write access: an implementation can read record_persisted /
  deferred_save_ready and can assign NEITHER. That is what makes both
  observable facts mean "the step ran", and it is checked from two directions
  below — atk_fiat_record (forge the record fact, skip the record write, and
  still run the deferred save) and atk_fiat_then_deferred (forge it and thereby
  satisfy the deferred save's ordering condition), which are the two attacks
  that defeated the previous full-permission grounding. atk_reset_after_write
  checks the same permission in the other polarity (perform the write, then try
  to clear the fact to slip under the not-commit clause). The discriminating
  capability relations_done(self) is grounded more strongly still, and the impl
  must not obtain it by any route other than running run_deferred_save(self):
  the weak-fiat-no-producer / weak-unfold-poke-fields / weak-cross-instance-
  transfer family (expect="reject", every one of them failing on
  Ensures(Implies(commit, relations_done(self))) for insufficient permission to
  access relations_done(self) — a VIPER verdict in each case). Folding the
  capability by hand is closed a level earlier, statically, by the front end
  (abstract.predicate.fold, which also covers Unfold and Unfolding): that is a
  property of the encoding rather than something Viper judged, so no case in
  this battery is scored on it — see weak-fiat-no-producer for the translatable
  form of that attack. See 'assessment'.

AXIOM lane: meta.axioms has five entries — three A-consumed callees
  (base_form_save_deferred / persist_record / run_deferred_save) whose Ensures
  the proof consumes, and two A-reference capability predicates (relations_done,
  record_available) with NO separate real callee. Their executable soundness is validated by
  axiom_check.py (G-AX) against the real Django callees. The AXIOM_TESTS below
  re-run that real-callee soundness probe (the relations-unwritten-until-save_m2m
  claim + the ordering precondition) and add a caller-domain containment probe.
"""
from pathlib import Path

INSTANCE = "django__django-16333"
FLOAT_ENCODING = None  # meta.json float_encoding is null; behaviour is pure boolean/heap

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the single impl-region block of save_form (UNIQUE in model.py) ---------
# We rebuild every variant by replacing exactly this block; the spec lines that
# precede it (# impl-start) and follow it (# impl-end) are reproduced verbatim,
# so only the executable body changes and same_spec is guaranteed.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    base_form_save_deferred(self)\n"
    "    # (the password assignment of the routine has no tracked persistence effect)\n"
    "    if commit:\n"
    "        persist_record(self)\n"
    "        if self.get_ready():\n"
    "            run_deferred_save(self)\n"
    "    return self\n"
    "    # impl-end"
)


def _impl(body_lines):
    """Wrap a list of body source lines (no leading indent assumptions: caller
    provides full 4-space-indented lines) into the impl block, keeping the
    # impl-start / # impl-end markers verbatim."""
    return "    # impl-start\n" + body_lines + "\n    # impl-end"


# ===========================================================================
# SPEC TESTS
# ===========================================================================
SPEC_TESTS = [

    # -------------------------------------------------------------------
    # POSITIVE CONTROL (soundness): a structurally-DIFFERENT but CORRECT impl
    # must verify, else SPEC-TOO-STRONG. The guard `if self.get_ready()` is
    # provably True after base_form_save_deferred (its Ensures sets ready),
    # so dropping the guard is a faithful, structurally-different shape that
    # still runs run_deferred_save unconditionally inside the commit branch.
    # This keeps every callee call needed to discharge the capability and the
    # record clauses; only the executable shape changes. (refinement.md §C:
    # "gold-faithful control (record-then-deferred, guard dropped) VERIFIES".)
    # -------------------------------------------------------------------
    {
        "id": "pos-control-guard-dropped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # CORRECT, structurally different: drop the inner hasattr-guard.\n"
                "    # base_form_save_deferred's Ensures(get_ready() is True) makes the\n"
                "    # guard provably True, so running the deferred save unconditionally\n"
                "    # inside the commit branch is behaviourally identical to the gold\n"
                "    # impl. record-write THEN deferred-save order preserved (the latter's\n"
                "    # Requires(get_record() is True) is discharged by persist_record).\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "rationale": "A faithful correct impl with the always-true guard removed must "
                     "verify against all five Ensures clauses (get_ready, record-on-commit, "
                     "relations_done-on-commit, no-record-without-commit, Result() is self). "
                     "If it cannot, the postcondition over-constrains a correct impl "
                     "(SPEC-TOO-STRONG). It keeps the record-then-deferred ordering so "
                     "run_deferred_save's Requires(get_record() is True) holds — i.e. it is "
                     "not a proof-gap variant.",
    },

    # -------------------------------------------------------------------
    # ADMISSIBILITY: the precondition must accept a normal F2P-shaped input.
    # The F2P test calls form.save(commit=True) on a fresh form (nothing
    # persisted yet). We assert, inside an otherwise-gold impl, that the entry
    # state and final guarantees hold for that input — confirming
    # Requires(get_record() is False) / Requires(MustTerminate(2)) admit the
    # discriminating commit=True case. The entry deferred-save fact is NOT
    # asserted here, because it is not constrained at entry (see ENTRY DOMAIN):
    # the gold body needs no assumption about it, which is the point.
    # -------------------------------------------------------------------
    {
        "id": "admiss-commit-true",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # Admissibility witness: the F2P input is form.save(commit=True) on a\n"
                "    # fresh form (nothing persisted on entry). Assert the entry precondition\n"
                "    # is satisfiable, then run the gold body and assert the discriminating\n"
                "    # final guarantees hold for the commit branch. Note what is NOT asserted:\n"
                "    # the entry deferred-save fact, which the precondition leaves free — the\n"
                "    # gold body earns every guarantee without knowing it.\n"
                "    Assert(self.get_record() is False)\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        if self.get_ready():\n"
                "            run_deferred_save(self)\n"
                "    Assert(self.get_ready() is True)\n"
                "    return self"
            ),
        ),
        "rationale": "The literal F2P shape is form.save(commit=True) on a fresh form: "
                     "record_persisted False on entry, which is exactly Requires(get_record() "
                     "is False). The entry assert and the post-body get_ready() assert both "
                     "discharge, and they discharge WITHOUT any assumption about the entry "
                     "deferred-save fact, so the same witness covers the re-entered half of "
                     "the domain too. If this cannot verify, the precondition rejects a "
                     "legitimate input (PRECOND-TOO-STRONG).",
    },

    # -------------------------------------------------------------------
    # PREPATCH / PARTIAL-DOMAIN (uniqueness): the pre-patch body stops after
    # the record write and NEVER runs the deferred relational save. Correct on
    # commit=False (nothing written) and on the record clause, but it does NOT
    # earn relations_done(self). = model_prepatch.py exactly.
    # -------------------------------------------------------------------
    {
        "id": "weak-prepatch-no-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (pre-patch body): commit branch stops after the primary-record\n"
                "    # write; the guarded deferred relational save is absent, so the m2m\n"
                "    # associations are never persisted.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "    return self"
            ),
        ),
        "refinement": "This is the verbatim pre-patch UserCreationForm.save body (omit the "
                     "added `if hasattr(self, 'save_m2m'): self.save_m2m()` lines). On "
                     "form.save(commit=True) the m2m through-rows are never written, so "
                     "user.orgs.all() is empty and the F2P assertSequenceEqual(user.orgs."
                     "all(), [organization]) FAILS. The faithful patch (= prepatch) does NOT "
                     "resolve the F2P.",
        "rationale": "Rejected by Ensures(Implies(commit, relations_done(self))): the impl "
                     "never calls run_deferred_save, the SOLE producer of relations_done(self), "
                     "so it has insufficient permission to that capability at return "
                     "(model_prepatch.py:198). SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # UNGROUNDED-ORACLE / FIAT (uniqueness): try to obtain the capability
    # relations_done(self) WITHOUT running the deferred relational save — i.e.
    # to hold the relational-data fact without doing the work that makes it
    # true. This is the capability-grounding analogue of the frame-mutation/fiat
    # attack, and it must be stated in a form Nagini TRANSLATES, so that VIPER
    # is what rules on it.
    #
    #   This case used to carry the literal fiat, Fold(relations_done(self)).
    #   That is rejected by Nagini's FRONT END -- "Translation failed / Invalid
    #   program: abstract.predicate.fold" -- so it never reached Viper, and on
    #   this backend (nagini is in the complement of pbt.WITNESS_REQUIRED, where
    #   "did not verify" ALONE is the whole argument for a rejection) a rival
    #   that fails to translate certifies nothing about the spec. Measured: the
    #   fold body exits 1 with no Viper banner in 15.2s wall, against 19.4s of
    #   Viper time for the body below, which Viper judges.
    #
    #   What translates. Nagini's translator leaves exactly two routes to an
    #   ABSTRACT predicate instance, and the fiat's own route is the closed one:
    #     - Fold(P(x)) — statically rejected for a @ContractOnly predicate
    #       (translators/contract.py, abstract.predicate.fold); Unfold and
    #       Unfolding are rejected the same way, so the whole fold family is a
    #       front-end fact about the ENCODING and never a Viper verdict.
    #     - the postcondition of a callee — the only way to get one from
    #       nothing. run_deferred_save(self) is the sole producer, and the
    #       axioms region a rival may not touch is where the callees live.
    #     (Assume(relations_done(self)) is not a third route: a predicate
    #      access in Assume is rejected at translation too,
    #      invalid.contract.position, and "Assume(" is a banned token for this
    #      backend precisely because a trusted assumption would let a rival
    #      prove anything, testing nothing.)
    #   So the translatable fiat is: run every OTHER axiom, twice over, and
    #   never the sole producer. It is the strongest form of the question the
    #   fold was reaching for, and Viper answers it — the rival discharges
    #   EVERY other clause (record-on-commit, get_ready, no-write-without-
    #   commit, Result() is self, the record object, the termination
    #   obligations) and fails on the discriminating one alone.
    # -------------------------------------------------------------------
    {
        "id": "weak-fiat-no-producer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (fiat, in the form Nagini translates): help itself to the\n"
                "    # relational-data capability without running its SOLE producer — invoke\n"
                "    # every OTHER axiom instead, twice over, and never the deferred save.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        base_form_save_deferred(self)\n"
                "        persist_record(self)\n"
                "    return self"
            ),
        ),
        "refinement": "The faithful refinement re-runs the parts of the save that do not "
                     "write the associations — super().save(commit=False) and user.save() "
                     "again — and never calls save_m2m(). Re-running them writes no through-"
                     "rows: only save_m2m() does. So user.orgs.all() is empty, the F2P "
                     "assertSequenceEqual(user.orgs.all(), [organization]) FAILS, and a "
                     "faithful patch of this shape resolves nothing. (The literal fold has no "
                     "Django refinement at all — there is no operation that marks the "
                     "relations written without running the deferred save.)",
        "rationale": "Rejected by Ensures(Implies(commit, relations_done(self))), with a real "
                     "Viper verdict: 'Verification failed / Postcondition of save_form might "
                     "not hold. There might be insufficient permission to access "
                     "relations_done(self)' at model.py:303, in 19.4s. That is the ONLY error "
                     "reported, so the rival is correct on every other clause and is turned "
                     "down for the fiat alone: no callee but run_deferred_save(self) grants "
                     "the capability, however many times the others are invoked. Non-vacuity "
                     "control: Assert(False) added inside this body's `if commit:` branch "
                     "FAILS ('Assertion False might not hold', 12.9s), so the branch the "
                     "rejection is about is reachable. SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # FRAME-FIAT via the abstraction predicate (uniqueness): unfold form_pred,
    # poke the underlying booleans, refold — try to earn the capability by
    # writing the observable fields. There IS no relational field and the
    # capability is not held in form_pred, so poking record_persisted /
    # deferred_save_ready cannot produce relations_done(self). (refinement.md
    # §C: "An impl that unfolds form_pred and pokes ... likewise FAILS — those
    # fields do not earn the capability.")
    # -------------------------------------------------------------------
    {
        "id": "weak-unfold-poke-fields",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (fiat via the fields): run the record write, then unfold the\n"
                "    # abstraction predicate and set the observable booleans directly,\n"
                "    # hoping the field writes stand in for the relational-data capability.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        Unfold(self.form_pred())\n"
                "        self.record_persisted = True\n"
                "        self.deferred_save_ready = True\n"
                "        Fold(self.form_pred())\n"
                "    return self"
            ),
        ),
        "refinement": "Setting the observable booleans corresponds to flipping the "
                     "record/handle flags by hand; it writes NOTHING to the m2m through "
                     "table (there is no relational field at all). On form.save(commit=True) "
                     "user.orgs.all() is still empty, so the F2P FAILS. A faithful patch that "
                     "only toggles record/handle state does not resolve the F2P.",
        "rationale": "Rejected by Ensures(Implies(commit, relations_done(self))): the "
                     "relational-data fact is NOT held in form_pred, so unfolding it and "
                     "writing record_persisted/deferred_save_ready cannot produce "
                     "relations_done(self) — the impl has insufficient permission to that "
                     "capability at return. SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # CROSS-INSTANCE TOKEN TRANSFER / echo-the-oracle (uniqueness): run the
    # REAL deferred save on a throwaway scratch Form() to earn
    # relations_done(scratch), then return self hoping the scratch capability
    # discharges the postcondition for self. relations_done is parameterised by
    # the form object: relations_done(scratch) is a DIFFERENT predicate
    # instance and does NOT discharge relations_done(self). (G-EQ: atk_echo_
    # transfer FAILS "insufficient permission to access relations_done(self)".)
    # The scratch Form()'s constructor terminates so MustTerminate is satisfied,
    # and we move it to a record+ready state legitimately before the deferred save.
    # -------------------------------------------------------------------
    {
        "id": "weak-cross-instance-transfer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (token transfer): persist self's record, then earn the\n"
                "    # capability on a SCRATCH form and hope it stands in for self.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        scratch = Form()\n"
                "        base_form_save_deferred(scratch)\n"
                "        persist_record(scratch)\n"
                "        run_deferred_save(scratch)\n"
                "    return self"
            ),
        ),
        "refinement": "Running the deferred save on a throwaway form persists the m2m "
                     "associations for THAT scratch form's instance, not for the submitted "
                     "user. The submitted user's orgs through-table is untouched, so "
                     "user.orgs.all() is empty and the F2P FAILS. A faithful patch that "
                     "save_m2m's a different form does not resolve the F2P.",
        "rationale": "Rejected by Ensures(Implies(commit, relations_done(self))): "
                     "run_deferred_save(scratch) grants relations_done(scratch), a different "
                     "predicate instance that does NOT discharge relations_done(self) — "
                     "insufficient permission to access relations_done(self) at return. The "
                     "capability is non-transferable across forms. SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # CONTROL-FLOW-EFFECT / self-echo (uniqueness): re-derive the capability
    # from the routine's OWN contract via self-recursion. Under partial-
    # correctness semantics a non-terminating body vacuously satisfies the
    # postcondition (handing back relations_done(self) for free) while its
    # faithful refinement is infinite recursion that never persists. The
    # MustTerminate(2) obligation on save_form vs MustTerminate(1) on the
    # callees forbids the self-call (no strictly smaller measure). (G-EQ note:
    # atk_selfrecurse FAILS "Obligation leak check failed".)
    # -------------------------------------------------------------------
    {
        "id": "weak-self-echo-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (self-echo): re-derive the whole contract from the function\n"
                "    # under specification itself. Under partial correctness a non-\n"
                "    # terminating body would vacuously satisfy every Ensures, handing back\n"
                "    # relations_done(self) without doing any real work.\n"
                "    return save_form(self, commit)"
            ),
        ),
        "refinement": "The faithful refinement is `def save(self, commit=True): return "
                     "self.save(commit)`, which RecursionErrors before persisting anything — "
                     "neither the record nor the m2m associations are written, so the F2P "
                     "FAILS (and indeed the routine never returns). It resolves nothing.",
        "rationale": "Rejected by the obligation-leak check: save_form Requires("
                     "MustTerminate(2)); a self-call save_form(self, commit) would have to "
                     "take the same MustTerminate(2) obligation without a strictly smaller "
                     "measure, so 'Callee save_form might not take all unsatisfied "
                     "obligations'. This closes the function-under-spec self-echo "
                     "(DEFECT-5). SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # ORDERING (uniqueness): run the deferred save BEFORE the record write.
    # run_deferred_save Requires(get_record() is True) — the m2m associations
    # attach to the record's primary key, so save_m2m before the record write
    # raises ValueError in-container. (G-EQ: atk_ordering FAILS on
    # Requires(get_record() is True); axiom_check.py negative observation.)
    # -------------------------------------------------------------------
    {
        "id": "weak-deferred-before-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (ordering): run the deferred relational save BEFORE the\n"
                "    # primary-record write.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        run_deferred_save(self)\n"
                "        persist_record(self)\n"
                "    return self"
            ),
        ),
        "refinement": "save_m2m attaches the associations to self.instance via its primary "
                     "key; before user.save() the instance has no pk, so the real save_m2m "
                     "raises ValueError ('needs to have a value for field \"id\" before this "
                     "many-to-many relationship can be used') and writes nothing — the F2P "
                     "FAILS (it raises). The pre-pk negative observation in axiom_check.py "
                     "confirms this. The reordered patch does NOT resolve the F2P.",
        "rationale": "Rejected by run_deferred_save's Requires(get_record() is True): at the "
                     "call site get_record() is still False (persist_record has not run), so "
                     "the precondition is not established. The ordering precondition is "
                     "faithful to the real callee's pk requirement. SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # POSITIVE CONTROL #2 (soundness) — RECORD-OBJECT ORDER IS NOT OBSERVABLE.
    # The record object every persistence step acts on is NOT created by the
    # base-form save: the form builds it from the submitted data while
    # validating, so it already exists when the routine is entered, and the
    # base-form save merely hands it back. An implementation may therefore write
    # the primary record BEFORE calling the base-form save and still be correct —
    # it acts on the same, already-existing object. Measured directly on the real
    # repo at base_commit: this shape's faithful refinement passes the F2P test
    # and the whole auth_tests + model_forms scope (796 tests), and an exhaustive
    # sweep of the finite modeled domain ({commit} x {0..3 associations}) finds it
    # agrees with the gold patch on all four observables, persisted association
    # pks included. So the spec MUST admit it: rejecting it would be
    # SPEC-TOO-STRONG on the record-object dependency, which is what this case
    # now guards against. What the spec still constrains is the order the repo
    # really constrains — the deferred relational save may run only after the
    # record write (see weak-deferred-before-record).
    # -------------------------------------------------------------------
    {
        "id": "pos-control-record-write-before-base-save",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # CORRECT, structurally different: write the primary record BEFORE the\n"
                "    # base-form save, then set up and run the deferred relational save. The\n"
                "    # record object is the one the form already holds, so writing it first is\n"
                "    # legitimate; the deferred save still runs strictly after the record\n"
                "    # write, which is the ordering the relational data genuinely needs.\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        base_form_save_deferred(self)\n"
                "        run_deferred_save(self)\n"
                "    else:\n"
                "        base_form_save_deferred(self)\n"
                "    return self"
            ),
        ),
        "rationale": "The record object is built during validation, before the routine runs, "
                     "so no step of the routine has to wait for it: an implementation that "
                     "writes the primary record before invoking the base-form save acts on the "
                     "same object and reaches the same end state. Confirmed against the real "
                     "repo at base_commit: the faithful refinement passes the F2P test and 796 "
                     "tests across auth_tests + model_forms, and agrees with the gold patch on "
                     "every observable over the whole finite modeled domain. If this cannot "
                     "verify, the spec forbids an order the repo permits (SPEC-TOO-STRONG) — "
                     "which is exactly the record-object over-fit this case exists to catch. "
                     "It keeps the record-write-then-deferred-save order, so it is not a "
                     "proof-gap variant.",
    },

    # -------------------------------------------------------------------
    # UNCONDITIONAL-PERSIST (uniqueness): persist even when not committing.
    # Violates Ensures(Implies(not commit, get_record() is False)). A faithful
    # patch that writes on commit=False breaks the deferred-save contract and
    # the no-commit P2P expectations. (G-EQ: atk_uncond FAILS.)
    # -------------------------------------------------------------------
    {
        "id": "weak-unconditional-persist",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (unconditional): persist the record and run the deferred save\n"
                "    # regardless of `commit`, so commit=False still writes.\n"
                "    base_form_save_deferred(self)\n"
                "    persist_record(self)\n"
                "    if self.get_ready():\n"
                "        run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "refinement": "Persisting on commit=False contradicts the documented save(commit=False) "
                     "contract (return the unsaved instance, defer persistence). The "
                     "PasswordChange/AdminPasswordChange/UserCreation P2P suite and callers "
                     "that rely on commit=False NOT writing would break; the real save(commit="
                     "False) must not touch the database. A faithful patch that always writes "
                     "does NOT preserve the P2P behaviour.",
        "rationale": "Rejected by Ensures(Implies(not commit, self.get_record() is False)): "
                     "the impl calls persist_record unconditionally, so for commit=False "
                     "get_record() becomes True, violating the clause. SPEC-TOO-WEAK if it "
                     "verified.",
    },

    # -------------------------------------------------------------------
    # SUPPORTING near-miss (uniqueness): persist the record on commit but
    # SKIP the deferred save under a bogus guard that is always False, so the
    # capability is never earned. Cheap mechanical variant, but it carries a
    # real refinement (= same as prepatch in effect). Distinct from prepatch by
    # keeping a guarded-but-dead run_deferred_save call shape.
    # -------------------------------------------------------------------
    {
        "id": "weak-dead-guard-skips-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG: guard the deferred save on get_record() is False, which is\n"
                "    # always False right after persist_record, so the deferred save is\n"
                "    # dead code and the capability is never earned.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        if self.get_record() is False:\n"
                "            run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "refinement": "After persist_record, get_record() is True, so `if get_record() is "
                     "False` never fires and save_m2m is never called — behaviourally "
                     "identical to the prepatch: user.orgs.all() is empty, F2P FAILS. The "
                     "faithful patch (dead guard) does NOT resolve the F2P.",
        "rationale": "Rejected by Ensures(Implies(commit, relations_done(self))): the "
                     "run_deferred_save call is statically reachable but its guard is provably "
                     "False after persist_record, so on the commit path relations_done(self) "
                     "is never produced — insufficient permission at return. SPEC-TOO-WEAK if "
                     "it verified.",
    },

    # -------------------------------------------------------------------
    # FIAT ON THE PRIMARY-RECORD FACT (uniqueness): satisfy "the primary record
    # is written" by DECLARING it — unfold the abstraction predicate, set the
    # primary-record boolean by hand, refold — and never perform the record
    # write at all. The deferred relational save is still really run, so the
    # relational-data capability is genuinely earned; the ONLY thing missing is
    # the primary record itself. This is the attack family that a spec holding
    # the observable facts at writable permission cannot see: the record clause
    # would be discharged by an assignment rather than by the write. The fact is
    # read-only inside form_pred, so the assignment has no permission.
    # -------------------------------------------------------------------
    {
        "id": "weak-fiat-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (fiat on the record fact): claim the primary record is written by\n"
                "    # setting the observable fact directly, without ever performing the record\n"
                "    # write, then run the deferred relational save.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        Unfold(self.form_pred())\n"
                "        self.record_persisted = True\n"
                "        Fold(self.form_pred())\n"
                "        run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "refinement": "Declaring the primary record written corresponds to a patch that calls "
                     "self.save_m2m() but never user.save(): the user row is never inserted, so "
                     "the instance has no pk and save_m2m raises ValueError — nothing is "
                     "persisted, the F2P FAILS, and every PASS_TO_PASS test that creates a user "
                     "through this routine (test_success / test_normalize_username / "
                     "test_unicode_username) fails too. The faithful patch does NOT resolve the "
                     "instance.",
        "rationale": "Rejected because the primary-record fact is held at READ-ONLY permission "
                     "inside form_pred: `self.record_persisted = True` has insufficient "
                     "permission ('Assignment might fail'). The record clause can therefore be "
                     "discharged only by the step whose contract claims that effect — the real "
                     "record write. SPEC-TOO-WEAK if it verified: this shape reaches the same "
                     "modelled end state as gold while omitting the primary record write.",
    },

    # -------------------------------------------------------------------
    # FIAT USED TO UNLOCK THE ORDERING CONDITION (uniqueness): the same forgery,
    # but exploited for the ORDER rather than for the record clause. The deferred
    # relational save may run only once the primary record is really written; if
    # the record fact were writable, an impl could set it, run the deferred save
    # early (against a record that does not exist yet), and only afterwards
    # perform the real write — resurrecting exactly the ordering defect that
    # weak-deferred-before-record rejects. Read-only permission on the fact is
    # what keeps that ordering condition honest.
    # -------------------------------------------------------------------
    {
        "id": "weak-fiat-then-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (fiat to unlock the order): declare the primary record written so\n"
                "    # the deferred relational save's already-written condition is met, run the\n"
                "    # deferred save first, and only then perform the real record write.\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        Unfold(self.form_pred())\n"
                "        self.record_persisted = True\n"
                "        Fold(self.form_pred())\n"
                "        run_deferred_save(self)\n"
                "        persist_record(self)\n"
                "    return self"
            ),
        ),
        "refinement": "This is the pre-pk ordering defect with a bookkeeping flag in front of "
                     "it: the real save_m2m still runs before user.save(), so the instance has "
                     "no primary key and save_m2m raises ValueError ('needs to have a value for "
                     "field \"id\" before this many-to-many relationship can be used'). Nothing "
                     "is written and the F2P FAILS. The faithful patch does NOT resolve the "
                     "instance.",
        "rationale": "Rejected at the assignment: the primary-record fact is READ-ONLY inside "
                     "form_pred, so the impl cannot set it and therefore cannot establish "
                     "run_deferred_save's Requires(get_record() is True) other than by really "
                     "performing the record write first. SPEC-TOO-WEAK if it verified — it "
                     "would re-open the ordering hole through the back door.",
    },

    # -------------------------------------------------------------------
    # RESET-AFTER-WRITE (uniqueness): the mirror-image forgery. Perform the real
    # record write on the no-commit path (which the behaviour forbids), then
    # CLEAR the observable fact so the not-commit clause reads as satisfied. A
    # writable fact makes "nothing is written when not committing" a statement
    # about the final flag rather than about the write; read-only permission
    # makes it a statement about the write.
    # -------------------------------------------------------------------
    {
        "id": "weak-reset-after-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (reset): write the primary record on EVERY path, then on the\n"
                "    # no-commit path clear the observable fact so it looks as though nothing\n"
                "    # was written.\n"
                "    base_form_save_deferred(self)\n"
                "    persist_record(self)\n"
                "    if commit:\n"
                "        run_deferred_save(self)\n"
                "    else:\n"
                "        Unfold(self.form_pred())\n"
                "        self.record_persisted = False\n"
                "        Fold(self.form_pred())\n"
                "    return self"
            ),
        ),
        "refinement": "The row is really inserted on save(commit=False); clearing a flag does "
                     "not delete it. The documented commit=False contract (return the unsaved "
                     "instance, touch no database row) is broken, so the PASS_TO_PASS suites "
                     "that call save(commit=False) and expect no write — the password-change "
                     "and user-creation form tests — fail. The faithful patch does NOT preserve "
                     "the instance's passing behaviour.",
        "rationale": "Rejected at the assignment: the primary-record fact is READ-ONLY inside "
                     "form_pred, so `self.record_persisted = False` has insufficient "
                     "permission. Ensures(Implies(not commit, get_record() is False)) therefore "
                     "means the write did not happen, not merely that a flag ends up clear. "
                     "SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # RE-ENTERED ENTRY STATE #1 — SHORT-CIRCUIT (uniqueness). A form that was
    # already asked to defer arrives with a deferred relational save set up.
    # This impl reads that entry fact and hands the form straight back,
    # persisting nothing. Every clause about the ENTRY state is satisfied for
    # free — get_ready() is already True, the returned object is self, the
    # record object is still held — so the only thing that can reject it is that
    # the commit clauses are claimed on this entry state too. They are, because
    # the entry deferred-save fact is unconstrained (see ENTRY DOMAIN); this case
    # VERIFIED while it was pinned to False, and its branch was dead code.
    # -------------------------------------------------------------------
    {
        "id": "weak-reentrant-shortcircuit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (short-circuit on the entry state): if a deferred relational save\n"
                "    # is already set up for this form, treat the persistence as somebody\n"
                "    # else's business and return without doing any of it.\n"
                "    if self.get_ready():\n"
                "        return self\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        if self.get_ready():\n"
                "            run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "refinement": "The faithful patch is an early `if hasattr(self, 'save_m2m'): return "
                     "self.instance` at the top of the routine. A caller that asks for "
                     "deferred persistence and then for immediate persistence gets NOTHING "
                     "written on the second call: no primary record, no associations. That is "
                     "the PASS_TO_PASS test test_success (auth_tests.test_forms."
                     "UserCreationFormTest), which saves with commit=False and then saves for "
                     "real and requires the second call to have actually persisted the record "
                     "(it asserts password_changed fired exactly once, which happens inside "
                     "the record write) — it FAILS, count 0 != 1. The F2P is reached on a "
                     "fresh form and still passes, so this is the P2P half of `does not "
                     "resolve`: it fixes the reported bug and destroys behaviour that worked.",
        "rationale": "Rejected by Ensures(Implies(commit, self.get_record() is True)) (and by "
                     "Implies(commit, relations_done(self))): on the entry-ready path the impl "
                     "performs no step at all, and the primary-record fact is read-only, so "
                     "get_record() is still False at return while commit is True. It is "
                     "rejected because it is wrong on an entry state the routine really has, "
                     "not because that state was excluded. SPEC-TOO-WEAK if it verified.",
    },

    # -------------------------------------------------------------------
    # RE-ENTERED ENTRY STATE #2 — DIVERGENCE ON THE RE-ENTERED HALF
    # (uniqueness). Same entry fact, exploited the other way: under partial
    # correctness a body that never returns satisfies every Ensures vacuously,
    # so a diverging branch is a free pass for any input that reaches it. The
    # MustTerminate(2) obligation is what forbids it — but only on inputs the
    # precondition admits, which is why this case belongs to the entry domain
    # rather than to the termination family. It too VERIFIED while the entry
    # deferred-save fact was pinned False (the loop was unreachable).
    # -------------------------------------------------------------------
    {
        "id": "weak-reentrant-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (divergence): if a deferred relational save is already set up,\n"
                "    # loop forever — under partial correctness that discharges every\n"
                "    # guarantee without persisting anything.\n"
                "    if self.get_ready():\n"
                "        while True:\n"
                "            Invariant(self.form_pred())\n"
                "            Invariant(record_available(self))\n"
                "    base_form_save_deferred(self)\n"
                "    if commit:\n"
                "        persist_record(self)\n"
                "        if self.get_ready():\n"
                "            run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "refinement": "The faithful patch is `if hasattr(self, 'save_m2m'): while True: pass` "
                     "at the top of the routine. A caller that deferred first and then asks to "
                     "persist hangs: the request never completes and nothing is written, so "
                     "test_success (which performs exactly that sequence) never finishes and "
                     "the PASS_TO_PASS set fails. Nothing is resolved by a routine that does "
                     "not return.",
        "rationale": "Rejected by the termination obligation: save_form Requires("
                     "MustTerminate(2)), so every loop it executes must carry a decreasing "
                     "measure, and `while True` with only state invariants does not ('Loop "
                     "might not terminate'). Because the entry deferred-save fact is "
                     "unconstrained the loop is REACHABLE, which is what turns the obligation "
                     "into a real check here. SPEC-TOO-WEAK if it verified: divergence would "
                     "hand back every clause for free.",
    },

    # -------------------------------------------------------------------
    # RE-ENTERED ENTRY STATE #3 — PARTIAL DOMAIN (uniqueness). The mirror of #1
    # written as the negated guard: do the whole correct job, but only for the
    # half of the entry domain where nothing was deferred yet. Correct exactly
    # on the inputs the F2P exercises and inert on the other half — the shape
    # that survives whenever a spec's entry domain has been trimmed to the F2P's
    # own entry state.
    # -------------------------------------------------------------------
    {
        "id": "weak-reentrant-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_IMPL,
            _impl(
                "    # WRONG (partial domain): run the whole persistence only when no deferred\n"
                "    # relational save was set up yet; on a form that already has one, do\n"
                "    # nothing and hand it back.\n"
                "    if not self.get_ready():\n"
                "        base_form_save_deferred(self)\n"
                "        if commit:\n"
                "            persist_record(self)\n"
                "            run_deferred_save(self)\n"
                "    return self"
            ),
        ),
        "refinement": "The faithful patch wraps the whole body in `if not hasattr(self, "
                     "'save_m2m'):` and otherwise returns self.instance untouched. On a fresh "
                     "form it is the gold behaviour, so the F2P test passes; on the "
                     "defer-then-persist sequence it writes nothing, so test_success "
                     "(auth_tests.test_forms.UserCreationFormTest) FAILS — the second save "
                     "must persist the record, and its password_changed assertion counts 0 "
                     "instead of 1. Half-domain correctness does not resolve the instance.",
        "rationale": "Rejected by Ensures(Implies(commit, self.get_record() is True)): on the "
                     "entry-ready path nothing runs, and the primary-record fact cannot be set "
                     "by assignment, so the commit clause is unsatisfied. This is the case "
                     "that measures the entry domain directly: it is admissible ONLY because "
                     "the entry deferred-save fact is free, and it is refuted there. "
                     "SPEC-TOO-WEAK if it verified.",
    },
]

# ===========================================================================
# AXIOM TESTS — three A-consumed callees + one A-reference capability predicate.
# All four are validated by axiom_check.py (G-AX) against the REAL Django
# callees. The probes below re-run that real-callee soundness check inside the
# instance Docker image (the real django.forms.ModelForm / Model.save / save_m2m
# live only there) and add a caller-domain CONTAINMENT probe.
#
# Pilot-bug guards honoured: the probes CALL the real callees (never scrape
# source); open no bundle files (axiom_check.py is embedded as a string at
# manifest-load time on the HOST, since the runner mounts only the probe at
# /work); and force encoding="utf-8" is irrelevant here (no file reads), but we
# keep all I/O ASCII-safe.
# ===========================================================================

# Embed axiom_check.py's source on the HOST at load time so the probe is fully
# self-contained in-container (the runner does NOT mount the bundle).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")


# Probe 1 — axiom-soundness: run the REAL three callees and assert each matches
# its axiom's Ensures under the caller's actual config (commit=False base save,
# then record write, then save_m2m), including the negative ordering observation
# (save_m2m before the record write must RAISE). This is exactly axiom_check.py;
# we execute its main() and assert RC==0.
_PROBE_SOUNDNESS = (
    "import sys\n"
    "# Embedded axiom_check.py source (the bundle is NOT mounted in-container).\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__axcheck__', '__file__': '/work/axiom_check_embedded.py'}\n"
    "exec(compile(_SRC, '/work/axiom_check_embedded.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "if rc != 0:\n"
    "    print('AXIOM-SOUNDNESS FAIL: axiom_check.main() returned', rc)\n"
    "    sys.exit(1)\n"
    "print('AXIOM-SOUNDNESS OK: real BaseModelForm.save(commit=False) / Model.save() / "
    "save_m2m match their axioms (relations unwritten until save_m2m; pre-pk save_m2m raises).')\n"
    "sys.exit(0)\n"
)


# Probe 2 — axiom-containment: enumerate the callee-inputs the MODEL can reach
# and assert each lies in the corresponding axiom's Requires domain. The model
# reaches each callee in exactly ONE control-flow state:
#   base_form_save_deferred(self): entry state record=False, ready=False
#       (Requires: form_pred — always held).
#   persist_record(self): after base save, record=False, ready=True
#       (Requires: form_pred — held).
#   run_deferred_save(self): after persist_record (commit branch),
#       record=True, ready=True (Requires: form_pred AND get_ready() is True AND
#       get_record() is True — ALL held because persist_record ran first and the
#       base save set ready). This is the load-bearing containment: the model
#       never reaches run_deferred_save with get_record() is False, so the
#       ordering precondition is never violated by the caller. We verify this by
#       driving the real callees in the SAME order the model does and asserting
#       the run_deferred_save precondition state (record written) holds at its
#       call site — and that the FORBIDDEN state (record not written) is exactly
#       the one the model never reaches and the one the real callee rejects.
_PROBE_CONTAINMENT = (
    "import sys, os, types\n"
    "import django\n"
    "from django.conf import settings\n"
    "if 'axcheck2' not in sys.modules:\n"
    "    mod = types.ModuleType('axcheck2')\n"
    "    mod.__path__ = ['/work']\n"
    "    mod.__file__ = '/work/axcheck2.py'\n"
    "    sys.modules['axcheck2'] = mod\n"
    "if not settings.configured:\n"
    "    settings.configure(\n"
    "        INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth','axcheck2'],\n"
    "        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': ':memory:'}},\n"
    "        USE_TZ=False)\n"
    "django.setup()\n"
    "from django import forms\n"
    "from django.db import connection, models\n"
    "class Target(models.Model):\n"
    "    name = models.CharField(max_length=50)\n"
    "    class Meta:\n"
    "        app_label = 'axcheck2'\n"
    "class Record(models.Model):\n"
    "    label = models.CharField(max_length=50)\n"
    "    rels = models.ManyToManyField(Target, blank=True)\n"
    "    class Meta:\n"
    "        app_label = 'axcheck2'\n"
    "with connection.schema_editor() as editor:\n"
    "    editor.create_model(Target)\n"
    "    editor.create_model(Record)\n"
    "class RecordForm(forms.ModelForm):\n"
    "    class Meta:\n"
    "        model = Record\n"
    "        fields = ('label','rels')\n"
    "def record_written(instance):\n"
    "    return instance.pk is not None and Record.objects.filter(pk=instance.pk).exists()\n"
    "# Drive the real callees in the EXACT order the model's impl does (commit=True).\n"
    "t = Target.objects.create(name='t')\n"
    "form = RecordForm(data={'label':'r','rels':[str(t.pk)]})\n"
    "assert form.is_valid(), form.errors\n"
    "# Step 1 == base_form_save_deferred(self): containment of its Requires (form_pred only).\n"
    "instance = forms.ModelForm.save(form, commit=False)\n"
    "assert hasattr(form, 'save_m2m'), 'ready handle must be installed (caller state for step 3)'\n"
    "assert not record_written(instance), 'caller reaches persist_record with record NOT yet written'\n"
    "# Step 2 == persist_record(self): containment of its Requires (form_pred only).\n"
    "instance.save()\n"
    "# Step 3 == run_deferred_save(self): the model reaches it ONLY here, where\n"
    "# get_record() is True AND get_ready() is True. Assert the caller-reachable\n"
    "# state satisfies run_deferred_save's Requires (record written, handle present).\n"
    "assert record_written(instance), (\n"
    "    'AXIOM-CONTAINMENT FAIL: model reaches run_deferred_save with record NOT written — '\n"
    "    'outside its Requires(get_record() is True) domain')\n"
    "assert hasattr(form, 'save_m2m'), (\n"
    "    'AXIOM-CONTAINMENT FAIL: model reaches run_deferred_save with no handle — '\n"
    "    'outside its Requires(get_ready() is True) domain')\n"
    "# Confirm the FORBIDDEN state (record not written) is the one the model never\n"
    "# reaches AND the one the real callee rejects (so the axiom is not too weak).\n"
    "form2 = RecordForm(data={'label':'r2','rels':[str(t.pk)]})\n"
    "assert form2.is_valid(), form2.errors\n"
    "inst2 = forms.ModelForm.save(form2, commit=False)\n"
    "raised = False\n"
    "try:\n"
    "    form2.save_m2m()\n"
    "except Exception:\n"
    "    raised = True\n"
    "assert raised, ('the pre-record-write state is rejected by the real callee — the model '\n"
    "    'never reaches run_deferred_save in that state, so the axiom domain covers exactly '\n"
    "    'the caller-reachable inputs')\n"
    "form.save_m2m()  # the in-domain call the model actually makes succeeds.\n"
    "assert list(instance.rels.all()) == [t], 'in-domain deferred save writes the associations'\n"
    "print('AXIOM-CONTAINMENT OK: every callee-input the model reaches lies inside the '\n"
    "      'axiom Requires domain (run_deferred_save only after the record write); the '\n"
    "      'forbidden pre-pk state is unreachable by the caller and rejected by the callee.')\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-soundness-callees",
        "axiom": "run_deferred_save",  # the discriminating callee; probe covers all three
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "Executes the three REAL unchanged callees (BaseModelForm.save("
                     "commit=False), Model.save(), save_m2m) over 50 observations incl. the "
                     "empty-m2m boundary and the NEGATIVE pre-pk ordering observation. Asserts "
                     "the relations-unwritten-until-save_m2m claim (grounds relations_done) and "
                     "that save_m2m before the record write RAISES (grounds run_deferred_save's "
                     "Requires(get_record() is True)). If any real callee violated its axiom's "
                     "Ensures, AXIOM-UNSOUND.",
    },
    {
        "id": "ax-containment-deferred",
        "axiom": "run_deferred_save",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "The model reaches run_deferred_save in exactly ONE state — after "
                     "persist_record (record written) and after the base save (handle "
                     "present) — so every callee-input the caller can produce lies inside "
                     "run_deferred_save's Requires(get_record() is True AND get_ready() is "
                     "True). The probe drives the real callees in the model's order and "
                     "asserts the reachable state satisfies the precondition, while the "
                     "forbidden pre-pk state (which the model never reaches) is exactly the "
                     "one the real callee rejects. A reachable input outside the domain would "
                     "be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
