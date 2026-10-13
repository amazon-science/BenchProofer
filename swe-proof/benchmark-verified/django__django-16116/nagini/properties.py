"""properties.py — PBT falsification manifest for django__django-16116.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. One function is under spec:

    produce_changes_or_report(store: List[int], check_mode: bool,
                              update_variant: bool) -> None

modeling the changes-present `else:` branch of `Command.handle` AFTER the gold
patch, which MOVES `if check_changes: sys.exit(1)` ahead of the two artefact
writers. The load-bearing contract:

    Requires(list_pred(store))                                   # FULL perm (record)
    Requires(Acc(LEDGER.produced, 1 / 2))                        # HALF perm (tally)
    Ensures (not check_mode)                                     # NORMAL-RETURN guard
    Ensures (list_pred(store))
    Ensures (Acc(LEDGER.produced, 1 / 2))
    Ensures (LEDGER.produced >= Old(LEDGER.produced) + 1)        # COMMITTED pin
    Ensures (len(store) >= len(Old(ToSeq(store))) + 1)           # GROWTH pin
    Ensures (ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))  # PREFIX
    Ensures (Implies(update_variant,     new tokens all == 1))   # VARIANT-BINDING pin
    Ensures (Implies(not update_variant, new tokens all == 0))   # (kind matches flag)
    Ensures (Implies(update_variant,
             LEDGER.produced == Old(...) + update_artifact_yield()))   # COMMITTED-ONCE
    Ensures (Implies(not update_variant,
             LEDGER.produced == Old(...) + fresh_artifact_yield()))    # (committed once)
    Ensures (Implies(update_variant,
             len(store) == len(Old(...)) + update_artifact_yield()))  # ONCE pin
    Ensures (Implies(not update_variant,
             len(store) == len(Old(...)) + fresh_artifact_yield()))   # (recorded once)
    Exsures(CheckFailureExit, check_mode and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))         # EXIT-FIRST pin
    Exsures(ProducingStepDeclined, not check_mode and update_variant
            and update_step_declines() and list_pred(store)
            and Acc(LEDGER.produced, 1 / 2)
            and ToSeq(store) == Old(ToSeq(store))
            and LEDGER.produced == Old(LEDGER.produced))         # DECLINE pin
    Exsures(ProducingStepFailed,                                 # NON-COMPLETION
            not check_mode and list_pred(store)                  #   mode pin
            and Acc(LEDGER.produced, 1 / 2)
            and Implies(update_variant,     update_step_fails())  #   per-step pin
            and Implies(not update_variant, fresh_step_fails())
            and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store))
            and LEDGER.produced >= Old(...) + (len(store) - len(Old(...)))  # NO-FORGERY
            and Implies(update_variant,     new tokens all == 1)  #   kind still bound
            and Implies(not update_variant, new tokens all == 0)
            and Implies(update_variant,                           #   ONE-RUN ENVELOPE
                        len(store)          <= len(Old(...)) + update_artifact_yield()
                        and LEDGER.produced <= Old(...)      + update_artifact_yield())
            and Implies(not update_variant,
                        len(store)          <= len(Old(...)) + fresh_artifact_yield()
                        and LEDGER.produced <= Old(...)      + fresh_artifact_yield()))

TWO observables, not one. `store` is the command's own RECORD of the files it
produced; `LEDGER.produced` is the AMBIENT tally of artefact-producing acts
actually committed to the durable medium migration files live on. They are
different observables because an implementation can have one without the other,
and the medium is SHARED: an artefact committed to it counts however the
producing step chose to record the fact — including into some other record
entirely. The tally is held at HALF permission throughout, so the subject may
READ it but can never advance it by hand; only a genuine producing step (a
writer axiom) does that, which is what makes "an artefact was really produced"
unforgeable rather than a bookkeeping entry.

What this spec defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the EXIT-FIRST Exsures, and it now has TWO
    conjuncts. `ToSeq(store) == Old(ToSeq(store))`: when check mode raises, the
    produced-file record must equal its OLD value. `LEDGER.produced ==
    Old(LEDGER.produced)`: and NOTHING was committed to the durable medium
    ANYWHERE, so no producing step ran at all — not on some other record either.
    The pre-patch code ran a writer FIRST and exited afterwards, so both the
    record had grown and the tally had advanced before the raise.
    `model_prepatch.py` reproduces that order (writers, then `if check_mode:
    raise`) and FAILS the record conjunct (G-DIFF). The F2P observable is
    `assertFalse(os.path.exists(...))` — no migration file produced in --check —
    which is a property of the MEDIUM, not of any list, and the tally conjunct
    is what carries it. Rivals: `rival-write-then-exit`,
    `rival-side-medium-in-check`, `rival-partial-side-medium-in-check`.

  * The COMMITTED pin `LEDGER.produced >= Old(LEDGER.produced) + 1` and the
    COMMITTED-ONCE pins tie the normal-return path to REAL production, not to
    record-keeping. The record clauses alone are satisfiable by APPENDING TOKENS
    BY HAND: the yield symbols are readable (`@Pure @ContractOnly` functions the
    impl may call), so an impl can compute the exact required post-length and
    fabricate that many tokens of the right kind without ever invoking a writer.
    Only the tally clauses reject that, because the tally is half-permission and
    advances solely through a writer axiom. Rivals: `rival-echo-fabricate-record`
    (record forged, nothing committed), `rival-cross-carrier-production` (a real
    run committed to the medium but by the WRONG producing step, while the right
    record is hand-filled with the right kind — caught when the tally's advance is
    checked against the REQUESTED step's yield), and `rival-extra-producing-run`
    (the correct dispatch PLUS an extra real run whose artefacts land in a side
    record: the record looks perfect, the tally over-counts).

    Deliberately NOT rejected, and this is the calibration boundary: an impl that
    runs the CORRECT producing step for real, lets its artefacts be recorded into
    some other list, and hand-fills the parameter with the same number of tokens of
    the same kind. Every observable this spec has — the record's contents and the
    medium's tally — matches the reference exactly, and so does the on-disk result,
    so it is a CORRECT alternative implementation and must verify (it does; measured
    2026-08-14). Its genuinely-wrong mutations are the two rivals just named: run
    the wrong step, or run the right step twice.

  * The DECLINE Exsures makes the update step's refusal a REPORTED outcome
    rather than an escape hatch. The real fold-into-most-recent step declines
    when the most recent migration is unsuitable, committing nothing; the
    command reports that unchanged. Because `update_step_declines()` is opaque —
    nothing in the spec establishes it — an impl cannot raise the refusal on its
    own to dodge producing, and the clause additionally pins the refusal to the
    update variant outside check mode. Rivals: `rival-self-decline`,
    `rival-decline-on-fresh-side`, `rival-swallow-decline`.

  * The NON-COMPLETION Exsures is the outcome of a producing step that cannot
    carry the pending changes through to artefacts at all. The real writers
    render each migration through `MigrationWriter.as_string`
    (makemigrations.py:360 at base_commit), which raises when the change set
    holds something it cannot serialize; BOTH steps are affected, because the
    update step delegates to the fresh one (makemigrations.py:258 -> :330). The
    command reports that outcome to its caller. Measured against the real
    callee: on one unserializable app the step commits NOTHING (0 of a yield of
    1); on two apps, good-then-bad, it commits the first app's artefact and then
    stops (1 of a yield of 2). How far it got is therefore not an observable
    anything can predict, so this clause states the ENVELOPE the caller can rely
    on instead of an exact count:
      - the mode pin `not check_mode`: in check mode no producing step is
        reached at all, so this outcome cannot arise there. Rival
        `rival-non-completion-in-check`.
      - the per-step pins: the outcome is available only for the step the
        variant flag selects and only when THAT step's opaque condition holds.
        Nothing in the spec establishes either condition, so an impl can neither
        report non-completion to dodge producing (rival
        `rival-self-non-completion`) nor borrow the other step's condition
        (attack-only, measured 2026-08-14: abandon an UPDATE request because
        `fresh_step_fails()`).
      - the NO-FORGERY conjunct `LEDGER.produced >= Old + (record growth)`: the
        record may not gain a token that the medium did not gain an artefact
        for. The real callee guarantees exactly this direction and not an
        equality — it appends `writer.path` only inside the `open(...,"w")`
        block that commits the artefact (makemigrations.py:361-363) — and the
        one-sided form is also what keeps the calibration boundary above alive
        on this leg, since an impl recording into another list cannot know how
        far the run it made got.
      - the ONE-RUN ENVELOPE (`<= yield` on both observables): stopping partway
        may not be used to produce MORE than the single requested run would.
        Attack-only (measured 2026-08-14): re-running the step onto a throwaway
        record after it stopped partway, which the tally bound rejects.
      - the kind conjuncts are unchanged, so whatever a stopped run did record
        still carries the requested step's kind.
    An impl that absorbs the non-completion and returns normally is caught by
    the normal-return pins: rival `rival-swallow-non-completion`. Note the whole
    leg says nothing about `run_formatters(self.written_files)`
    (makemigrations.py:390) — the whole-container overlay the fresh step ends
    with — because it reformats artefacts already committed and recorded, adding
    no artefact and no token, so it is a step with no observable of its own
    here; on the non-completion path it is not reached at all.

  * The NORMAL-RETURN guard `Ensures(not check_mode)` forbids any impl that
    RETURNS NORMALLY in check mode (it MUST raise) — closing the "silently do
    nothing / report success" cheat. This is the control-flow-effect defence:
    raise-vs-return is invisible to the store value alone, so the spec pins it
    via `not check_mode` on the normal-return path.

  * The GROWTH pin `len(store) >= len(Old) + 1` (with the PREFIX conjunct)
    forces the artefact-producing step to be REACHED on the normal-return path:
    a writer must run and append >=1 token (prefix kept). An impl that skips the
    writers fails it.

  * The VARIANT-BINDING pins tie WHICH producing step ran to the variant flag:
    every newly-appended token's kind (``1`` update / ``0`` fresh) must match
    ``update_variant``. Each writer axiom stamps only its own kind, so the pins
    are dischargeable only by dispatching the MATCHING writer — a swapped,
    always-one-writer, or both-writers dispatch cannot verify. This closes the
    writer-dispatch surface (the two real writers have observably different
    on-disk outcomes, which the hidden tests distinguish).

  * The PRODUCED-ONCE pins tie the SIZE of the growth to the artefact yield of
    ONE run of the requested producing step:
    `len(store) == len(Old) + update_artifact_yield()` under the update flag,
    `... + fresh_artifact_yield()` otherwise. The GROWTH pin is a one-sided
    LOWER bound and the VARIANT-BINDING pins quantify over the whole new range,
    so both are satisfied by performing the MATCHING producing step more than
    once (growth becomes 2x the yield, every new token still carries the
    matching kind). These pins are the equality that senses HOW MANY TIMES the
    step ran: each writer axiom appends exactly its own yield, so a second
    invocation makes the post-state `len(Old) + 2*yield`, refuting the equality
    (`yield >= 1`, so `2*yield != yield`). The real producing steps are not
    idempotent — materialising the same pending changes a second time on top of
    the artefacts just materialised for them leaves a doubly-produced on-disk
    result the hidden tests distinguish. Deliberately stated against the OPAQUE
    yield symbols rather than a literal count: the number of pending migrations
    is not fixed (one app -> 1, two apps -> 2), so an `== +1` shape would be
    strictly stronger than the real behaviour (SPEC-TOO-STRONG); the equality
    pins the MULTIPLICITY of the producing step, never the size of the change
    set. Rival: `rival-produce-twice`.

  * `store` is held at FULL permission (NOT Acc(.,1/2)): the docstring states it
    is genuinely mutated by the writers, so a write to `store` is LEGITIMATE and
    a frame-mutation/insufficient-permission attack does NOT apply to it (there
    is no read-only list input). The relevant store attack is instead
    VALUE-LEVEL: a rival that mutates the store on the check-mode raise path is
    caught by the EXIT-FIRST `ToSeq(store) == Old` conjunct, not by the
    permission system.

  * `LEDGER.produced` is the opposite case, and its HALF permission IS
    load-bearing rather than advisory. It is the one observable the subject may
    read but must not write, so an impl that tries to satisfy the COMMITTED pins
    by assigning the tally is rejected by the permission system itself
    (`Assignment might fail. There might be insufficient permission`), while the
    writer axioms — which hold only the same READ access — still advance it.
    That asymmetry is deliberate: it models "the producing act happens out in
    the shared medium, not in a variable the caller owns". Rival:
    `rival-bump-the-tally`.

  * GROUNDEDNESS, restated honestly. The record clauses are NOT ungrounded-proof
    on their own: the yield symbols are `@Pure @ContractOnly` FUNCTIONS the impl
    may call, so `n = update_artifact_yield()` followed by a loop appending `n`
    kind-1 tokens discharges every `store`-only clause (GROWTH, PREFIX,
    VARIANT-BINDING, ONCE) without any writer running. This was measured, not
    assumed — see `rival-echo-fabricate-record`, which is exactly that impl. What
    makes the surface grounded is the TALLY: the only term in the whole spec that
    can advance `LEDGER.produced` is an invocation of a writer axiom, and the
    COMMITTED-ONCE equalities pin that advance to precisely one such invocation
    of the MATCHING writer. So the cheapest impl that satisfies the full contract
    still has to call the right real writer exactly once. Both Exsures
    store-unchanged conjuncts are grounded in `Old(...)`, functions of the entry
    state, likewise non-echoable.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY text strictly inside the single `# impl-start`/`# impl-end` region,
so `markers.same_spec` is guaranteed and a rejection comes from the
POSTCONDITION/Exsures catching wrong behaviour, never from a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P/P2P. Axiom cases run the REAL writer callee
(`Command.write_migration_files`) in Docker, mirroring axiom_check.py.
"""
from pathlib import Path

INSTANCE = "django__django-16116"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace the UNIQUE occurrence of an impl-region substring. Assert it is
    found and unique so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(
            f"properties.py: substring not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark — the WHOLE impl body, strictly between # impl-start and
# # impl-end of model.py. Occurs exactly once.
# ---------------------------------------------------------------------------
_IMPL_BODY = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-different but CORRECT: keep the check-mode exit FIRST, but
# rewrite the writer dispatch in the OPPOSITE branch order (test `not
# update_variant` first, fresh writer in the then-branch, update writer in the
# else). Semantically identical (both writers satisfy the same Ensures), a
# different control-flow source. If this fails to verify the postcondition is
# over-fit to one writer-branch order => SPEC-TOO-STRONG. This is also among the
# cheapest HONEST impls: it still raises first in check mode and calls a real
# writer otherwise (the GROWTH pin has no echoable oracle).
_IMPL_REORDER = """    if check_mode:
        raise CheckFailureExit()
    if not update_variant:
        write_fresh_artifacts(store)
    else:
        write_update_artifacts(store)"""
_POS_REORDER = _swap(_BASE, _IMPL_BODY, _IMPL_REORDER)

# (5b) Structurally-different but CORRECT: collapse the if/else writer dispatch
# but keep BOTH writers reachable; use an early `return` after the raise guard is
# expressed as an explicit `else` so the writers are nested. Same semantics,
# different block structure. If it fails to verify => SPEC-TOO-STRONG (over-fit
# to the flat two-`if` shape).
_IMPL_NESTED = """    if check_mode:
        raise CheckFailureExit()
    else:
        if update_variant:
            write_update_artifacts(store)
        else:
            write_fresh_artifacts(store)"""
_POS_NESTED = _swap(_BASE, _IMPL_BODY, _IMPL_NESTED)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped, in-domain input establishes
# the precondition list_pred(store) for a normal input. We call ourselves with
# check_mode=False (so the self-call RETURNS NORMALLY — no unhandled raise) on a
# freshly-built full-permission store, under BOTH update regimes, before running
# the gold body unchanged. If the self-call cannot establish the precondition for
# a normal input => PRECOND-TOO-STRONG.
_IMPL_ADMISS = """    probe = []  # type: List[int]
    Assert(list_pred(probe))
    probe2 = []  # type: List[int]
    Assert(list_pred(probe2))
    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_POS_ADMISS = _swap(_BASE, _IMPL_BODY, _IMPL_ADMISS)

# (7) ALIASING positive control. Keep the check-mode exit first and the matching
# dispatch, but reach `store` through a second name bound to the same list. The
# two observables must not be over-fit to the syntactic parameter name: the
# record grows and the medium receives exactly one run's artefacts either way.
# If this fails to verify the clauses are keyed on a name rather than on the
# object/medium => SPEC-TOO-STRONG.
_IMPL_ALIAS = """    if check_mode:
        raise CheckFailureExit()
    alias = store
    if update_variant:
        write_update_artifacts(alias)
    else:
        write_fresh_artifacts(alias)"""
_POS_ALIAS = _swap(_BASE, _IMPL_BODY, _IMPL_ALIAS)

# (7) Structurally-different but CORRECT, and the CALIBRATION case for the
# refusal outcome: instead of letting the fold-into-most-recent step report its
# own refusal, CONSULT whether the most recent migration is foldable first and
# report the refusal from here, invoking the step only when it is foldable. Same
# observable outcomes on every admissible input — exit first in check mode,
# exactly one real producing run otherwise, refusal reported unchanged when the
# step would have declined — reached by a different control-flow source. This
# one is measured, not assumed: its faithful real patch (hoist the four
# foldability guards into a pre-check that raises the same command-level errors,
# with the exit moved first) was run through the resolve oracle on 2026-08-14 and
# RESOLVED — F2P passes, 137/137 P2P pass, including all seven update-mode tests
# that assert the refusal message. So it must VERIFY: if it fails, the DECLINE
# Exsures has over-fit to "only the callee may raise the refusal", which the real
# behaviour does not guarantee => SPEC-TOO-STRONG.
_IMPL_PRECHECK_DECLINE = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        if update_step_declines():
            raise ProducingStepDeclined()
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_POS_PRECHECK_DECLINE = _swap(_BASE, _IMPL_BODY, _IMPL_PRECHECK_DECLINE)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) THE BUG ITSELF — write-then-exit (pre-patch order). Run a writer FIRST,
# then raise in check mode (exactly model_prepatch.py). In check mode the store
# grew by >=1 token BEFORE the raise, so the Exsures store-unchanged conjunct
# (ToSeq(store) == Old(ToSeq(store))) is violated. This is the discriminating
# defect the gold patch fixes (G-DIFF).
_IMPL_WRITE_THEN_EXIT = """    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)
    if check_mode:
        raise CheckFailureExit()"""
_RIVAL_WRITE_THEN_EXIT = _swap(_BASE, _IMPL_BODY, _IMPL_WRITE_THEN_EXIT)

# (2) CONTROL-FLOW-EFFECT — drop the raise in check mode entirely: in check mode
# just return normally (do nothing), else write. A normal return with
# check_mode==True violates Ensures(not check_mode). raise-vs-return is invisible
# to the store value, so this is precisely the control-flow defence the
# normal-return guard exists for.
_IMPL_NO_RAISE = """    if check_mode:
        write_fresh_artifacts(store)
        return
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_NO_RAISE = _swap(_BASE, _IMPL_BODY, _IMPL_NO_RAISE)

# (2b) CONTROL-FLOW-EFFECT, leaner: in check mode produce an artefact then return
# (no raise). Returns normally in check mode -> violates Ensures(not check_mode);
# AND even outside check mode it is fine, so only the check-mode normal return is
# wrong. Distinct from (2) in shape (single dispatch, no early empty local).
_IMPL_CHECK_RETURNS = """    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_CHECK_RETURNS = _swap(_BASE, _IMPL_BODY, _IMPL_CHECK_RETURNS)

# (3) SKIP-THE-WRITER — outside check mode, return without producing an artefact.
# Raise first in check mode (correct there), but on the normal path do NOTHING:
# the store does not grow, violating len(store) >= len(Old) + 1.
_IMPL_SKIP_WRITER = """    if check_mode:
        raise CheckFailureExit()"""
_RIVAL_SKIP_WRITER = _swap(_BASE, _IMPL_BODY, _IMPL_SKIP_WRITER)

# (4) PARTIAL-DOMAIN — gate the check-mode exit on update_variant too:
# `if check_mode and update_variant: raise`. Correct on the (check, update) and
# every non-check sub-domain, but for (check_mode=True, update_variant=False) it
# falls through and writes a FRESH artefact then RETURNS NORMALLY — violating
# BOTH Ensures(not check_mode) (returned in check mode) and, on that path, the
# behaviour is the pre-patch bug for the fresh-writer sub-case.
_IMPL_PARTIAL = """    if check_mode and update_variant:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_PARTIAL = _swap(_BASE, _IMPL_BODY, _IMPL_PARTIAL)

# (4b) WRITER-DISPATCH SWAP — keep the check-mode exit FIRST (correct there) but
# dispatch the WRONG writer under each flag value: update flag -> fresh writer,
# otherwise -> update writer. Growth + prefix hold (both writers grow the store),
# but every new token carries the WRONG kind, violating the VARIANT-BINDING pins.
_IMPL_SWAP = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_fresh_artifacts(store)
    else:
        write_update_artifacts(store)"""
_RIVAL_SWAP = _swap(_BASE, _IMPL_BODY, _IMPL_SWAP)

# (4c) ALWAYS-ONE-WRITER — collapse the dispatch: exit first in check mode, then
# ALWAYS call the fresh writer regardless of the flag. Growth + prefix hold, but
# under the update flag the new tokens carry the fresh kind, violating the
# update-side VARIANT-BINDING pin.
_IMPL_ALWAYS_FRESH = """    if check_mode:
        raise CheckFailureExit()
    write_fresh_artifacts(store)"""
_RIVAL_ALWAYS_FRESH = _swap(_BASE, _IMPL_BODY, _IMPL_ALWAYS_FRESH)

# (4d) PRODUCE-TWICE — keep the check-mode exit FIRST and dispatch the MATCHING
# producing step under each flag, but perform it TWICE. Growth (a one-sided
# lower bound) still holds (now 2x the yield), the prefix still holds, and the
# VARIANT-BINDING kind pins still hold (both runs stamp the matching kind), so
# ONLY the PRODUCED-ONCE equality can catch it: the post-state is
# len(Old) + 2*yield, not len(Old) + yield, and yield >= 1 so the two differ.
_IMPL_DOUBLE = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)
        write_fresh_artifacts(store)"""
_RIVAL_DOUBLE = _swap(_BASE, _IMPL_BODY, _IMPL_DOUBLE)

# (5, supporting) MUTATE-THEN-EXIT-IN-CHECK — value-level store attack on the
# raise path. `store` is FULL permission so the write is permitted; the rival
# appends a token then raises in check mode. The Exsures requires
# ToSeq(store) == Old(ToSeq(store)); the append makes it grow, so the conjunct
# fails on a VALUE basis (not a permission basis — full perm allows the write).
# Demonstrates the EXIT-FIRST clause catches ANY store growth before the raise,
# not just a real writer.
_IMPL_MUTATE_RAISE = """    if check_mode:
        store.append(0)
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_MUTATE_RAISE = _swap(_BASE, _IMPL_BODY, _IMPL_MUTATE_RAISE)

# ===========================================================================
# UNIQUENESS RIVALS on the AMBIENT-MEDIUM observable — expect "reject"
# ===========================================================================
# These are the rivals the `store`-only surface could not see. Each performs a
# REAL producing run (a genuine writer-axiom invocation, i.e. a real
# artefact committed to the durable medium) whose effect on `store` is nil or
# forged, or forges the record with no run at all.

# (6) SIDE-MEDIUM-IN-CHECK — in check mode, run a real producing step whose
# produced-file tokens land in a DIFFERENT list, then exit. Every `store`-only
# clause holds vacuously (the parameter is untouched), but an artefact was
# really committed to the medium.
_IMPL_SIDE_IN_CHECK = """    if check_mode:
        side = []  # type: List[int]
        write_fresh_artifacts(side)
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_SIDE_IN_CHECK = _swap(_BASE, _IMPL_BODY, _IMPL_SIDE_IN_CHECK)

# (6b) PARTIAL-DOMAIN SIDE-MEDIUM-IN-CHECK — the same laundering, but only on
# the (check, update) corner: correct everywhere else. A domain-incomplete
# version of (6), which a clause that only looked at one flag pair would miss.
_IMPL_PARTIAL_SIDE = """    if check_mode:
        if update_variant:
            side = []  # type: List[int]
            write_fresh_artifacts(side)
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_PARTIAL_SIDE = _swap(_BASE, _IMPL_BODY, _IMPL_PARTIAL_SIDE)

# (7) ECHO / FABRICATED RECORD — the ungrounded-oracle rival. Reads the yield
# symbol (they are @Pure @ContractOnly FUNCTIONS, so an impl may call them),
# then appends exactly that many tokens of the matching kind BY HAND. Every
# `store`-only clause is discharged; NO producing step ever runs.
_IMPL_ECHO = """    if check_mode:
        raise CheckFailureExit()
    n = 0  # type: int
    tok = 0  # type: int
    if update_variant:
        n = update_artifact_yield()
        tok = 1
    else:
        n = fresh_artifact_yield()
    i = 0
    while i < n:
        Invariant(list_pred(store) and Acc(LEDGER.produced, 1 / 2)
                  and 0 <= i and i <= n
                  and len(store) == len(Old(ToSeq(store))) + i
                  and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
        Invariant(Forall(int, lambda k: Implies(
            len(Old(ToSeq(store))) <= k and k < len(store), store[k] == tok)))
        Invariant(MustTerminate(n - i + 1))
        store.append(tok)
        i += 1"""
_RIVAL_ECHO = _swap(_BASE, _IMPL_BODY, _IMPL_ECHO)

# (8) EXTRA PRODUCING RUN — the correct dispatch onto `store` PLUS one more real
# producing run whose artefacts are recorded into a side list. The record is
# byte-perfect; the medium received twice the artefacts.
_IMPL_EXTRA_RUN = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)
    side = []  # type: List[int]
    write_fresh_artifacts(side)"""
_RIVAL_EXTRA_RUN = _swap(_BASE, _IMPL_BODY, _IMPL_EXTRA_RUN)

# (9) CROSS-CARRIER — run the WRONG producing step for real onto a side list,
# then hand-record the RIGHT kind onto `store`. The record claims the requested
# variant; the medium got the other step's artefacts.
_IMPL_CROSS = """    if check_mode:
        raise CheckFailureExit()
    side = []  # type: List[int]
    n = 0  # type: int
    tok = 0  # type: int
    if update_variant:
        write_fresh_artifacts(side)
        n = update_artifact_yield()
        tok = 1
    else:
        write_update_artifacts(side)
        n = fresh_artifact_yield()
    i = 0
    while i < n:
        Invariant(list_pred(store) and Acc(LEDGER.produced, 1 / 2)
                  and 0 <= i and i <= n
                  and len(store) == len(Old(ToSeq(store))) + i
                  and ToSeq(store).take(len(Old(ToSeq(store)))) == Old(ToSeq(store)))
        Invariant(Forall(int, lambda k: Implies(
            len(Old(ToSeq(store))) <= k and k < len(store), store[k] == tok)))
        Invariant(MustTerminate(n - i + 1))
        store.append(tok)
        i += 1"""
_RIVAL_CROSS = _swap(_BASE, _IMPL_BODY, _IMPL_CROSS)

# (10) BUMP-THE-TALLY — try to discharge the COMMITTED pins by advancing the
# ambient tally directly instead of producing anything. The tally is held at
# HALF permission, so this is a PERMISSION failure, which is exactly the point:
# the subject may read how much has been committed and may never commit.
_IMPL_BUMP = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        LEDGER.produced = LEDGER.produced + update_artifact_yield()
    else:
        LEDGER.produced = LEDGER.produced + fresh_artifact_yield()"""
_RIVAL_BUMP = _swap(_BASE, _IMPL_BODY, _IMPL_BUMP)


# ===========================================================================
# UNIQUENESS RIVALS on the REFUSAL outcome — expect "reject"
# ===========================================================================

# (11) SELF-DECLINE — dodge producing by raising the refusal outcome directly,
# without invoking the step that can legitimately refuse.
_IMPL_SELF_DECLINE = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        raise ProducingStepDeclined()
    write_fresh_artifacts(store)"""
_RIVAL_SELF_DECLINE = _swap(_BASE, _IMPL_BODY, _IMPL_SELF_DECLINE)

# (11b) DECLINE-ON-FRESH-SIDE — raise the refusal on the variant whose real
# producing step has no refusal to raise.
_IMPL_DECLINE_FRESH = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        raise ProducingStepDeclined()"""
_RIVAL_DECLINE_FRESH = _swap(_BASE, _IMPL_BODY, _IMPL_DECLINE_FRESH)

# (11c) SWALLOW-DECLINE — invoke the update step, swallow its refusal, and
# return normally having produced nothing. The command must report the refusal,
# not convert it into a silent success.
_IMPL_SWALLOW = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        try:
            write_update_artifacts(store)
        except ProducingStepDeclined:
            pass
    else:
        write_fresh_artifacts(store)"""
_RIVAL_SWALLOW = _swap(_BASE, _IMPL_BODY, _IMPL_SWALLOW)


# ===========================================================================
# UNIQUENESS RIVALS on the NON-COMPLETION outcome — expect "reject"
# ===========================================================================

# (12) SELF-NON-COMPLETION — dodge producing by reporting that the step could
# not carry the changes through, without ever invoking a step that could
# legitimately stop partway.
_IMPL_SELF_FAIL = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        raise ProducingStepFailed()
    write_fresh_artifacts(store)"""
_RIVAL_SELF_FAIL = _swap(_BASE, _IMPL_BODY, _IMPL_SELF_FAIL)

# (12b) NON-COMPLETION-IN-CHECK — in check mode, consult whether the producing
# step could carry the changes through and report ITS non-completion instead of
# the check-mode failure exit. Nothing is committed and nothing is recorded, so
# every value conjunct of the exit outcome would hold: only the mode pin on the
# non-completion outcome can reject it.
_IMPL_FAIL_IN_CHECK = """    if check_mode:
        if fresh_step_fails():
            raise ProducingStepFailed()
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)"""
_RIVAL_FAIL_IN_CHECK = _swap(_BASE, _IMPL_BODY, _IMPL_FAIL_IN_CHECK)

# (12c) SWALLOW-NON-COMPLETION — invoke the step, absorb its non-completion and
# return normally, reporting success for a request that only got partway.
_IMPL_SWALLOW_FAIL = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        try:
            write_fresh_artifacts(store)
        except ProducingStepFailed:
            pass"""
_RIVAL_SWALLOW_FAIL = _swap(_BASE, _IMPL_BODY, _IMPL_SWALLOW_FAIL)

# (12d) RELABEL-NON-COMPLETION-AS-REFUSAL — report a step that stopped partway
# as the fold-refusal, which claims a state (nothing committed, nothing
# recorded) that a partway run need not be in.
_IMPL_RELABEL_FAIL = """    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        try:
            write_update_artifacts(store)
        except ProducingStepFailed:
            raise ProducingStepDeclined()
    else:
        write_fresh_artifacts(store)"""
_RIVAL_RELABEL_FAIL = _swap(_BASE, _IMPL_BODY, _IMPL_RELABEL_FAIL)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder-writers", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but semantically identical impl: check-mode raise kept "
                  "FIRST, writer dispatch rewritten in the opposite branch order (test "
                  "`not update_variant` first). Both writers satisfy the same Ensures, so the "
                  "GROWTH/PREFIX pins and the EXIT-FIRST Exsures still hold. If it fails to "
                  "verify the postcondition is over-fit to one writer-branch order => "
                  "SPEC-TOO-STRONG. Also the cheapest honest impl (still calls a real writer; the "
                  "GROWTH pin has no echoable oracle)."},
    {"id": "pos-control-nested-else", "kind": "soundness", "expect": "verify",
     "module": _POS_NESTED,
     "rationale": "a correct impl with a DIFFERENT block structure (writers nested under an "
                  "explicit else of the check-mode guard) instead of two flat `if`s; same "
                  "semantics. If it fails to verify the spec is over-fit to the flat two-`if` "
                  "shape => SPEC-TOO-STRONG."},
    {"id": "pos-control-aliased-store", "kind": "soundness", "expect": "verify",
     "module": _POS_ALIAS,
     "rationale": "a correct impl that reaches the produced-file record through a SECOND name "
                  "bound to the same list. Both observables must be keyed on the object and the "
                  "medium, not on the syntactic parameter name: exactly one producing run happens "
                  "and its artefacts are recorded, however the list is spelled. If it fails to "
                  "verify the clauses are name-keyed => SPEC-TOO-STRONG."},
    {"id": "pos-control-precheck-decline", "kind": "soundness", "expect": "verify",
     "module": _POS_PRECHECK_DECLINE,
     "rationale": "the calibration boundary for the DECLINE Exsures. A correct impl that reports "
                  "the refusal from HERE, after consulting whether the most recent migration is "
                  "foldable, rather than letting the producing step report it. Observationally "
                  "identical to the reference on every admissible input, and its faithful real "
                  "patch (foldability guards hoisted into a pre-check raising the same "
                  "command-level errors, exit moved first) was put through the resolve oracle on "
                  "2026-08-14: RESOLVED, F2P pass, 137/137 P2P pass. So the DECLINE clause must NOT "
                  "demand that only the callee can raise the refusal — it demands that the refusal "
                  "be genuine (the opaque condition holds) and that nothing was committed. If this "
                  "fails to verify => SPEC-TOO-STRONG. Contrast `rival-self-decline`, which raises "
                  "the refusal WITHOUT the condition holding and is rejected."},
    {"id": "admiss-self-call", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "self-calls on F2P-shaped in-domain inputs (freshly-built full-permission "
                  "store, check_mode=False so the call returns normally, under BOTH update "
                  "regimes) must establish the precondition list_pred(store). If the self-call "
                  "cannot establish the precondition for a normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-write-then-exit", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRITE_THEN_EXIT,
     "refinement": "this is the PRE-PATCH order verbatim (writers first, `if check_changes: "
                   "sys.exit(1)` after — model_prepatch.py reverts to exactly this). Its faithful "
                   "real patch is the UNCHANGED pre-patch makemigrations, which in --check mode "
                   "WRITES the migration file(s) and THEN exits non-zero. That is precisely the "
                   "bug the F2P test asserts against: `makemigrations --check` must produce NO "
                   "migration artefact (assertFalse the file exists) — the pre-patch order leaves "
                   "the file on disk, so it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (mirrors G-DIFF / model_prepatch.py:118). "
                  "Rejection source: the EXIT-FIRST Exsures conjunct "
                  "ToSeq(store) == Old(ToSeq(store)) — a writer ran before the raise so the store "
                  "grew by >=1 token (writer axioms' len >= +1), unequal to its old value. If it "
                  "verified => SPEC-TOO-WEAK (admits the very bug)."},
    {"id": "rival-no-raise-in-check", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_RAISE,
     "refinement": "drops the check-mode exit: in --check it writes an artefact then RETURNS 0. A "
                   "faithful real patch that removed `sys.exit(1)` would make `makemigrations "
                   "--check` exit 0 even when migrations are missing — the F2P test asserts a "
                   "non-zero exit / SystemExit on pending changes (the whole point of --check), so "
                   "it would NOT resolve.",
     "rationale": "control-flow-effect rival: returns normally in check mode. Rejection source: "
                  "Ensures(not check_mode) on the normal-return path — a normal return with "
                  "check_mode==True is forbidden. If it verified => SPEC-TOO-WEAK (the "
                  "raise-vs-return distinction unconstrained, the 'silently report success' cheat "
                  "admitted)."},
    {"id": "rival-check-returns-normally", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CHECK_RETURNS,
     "refinement": "omits the check-mode guard entirely: ALWAYS dispatches a writer and returns "
                   "normally, even in --check. Faithful real patch = makemigrations with the "
                   "`if check_changes: sys.exit(1)` deleted: --check writes the migration and exits "
                   "0, failing the F2P non-zero-exit/no-artefact assertions — would NOT resolve.",
     "rationale": "control-flow-effect rival (leaner shape, single dispatch). Rejection source: "
                  "Ensures(not check_mode) — when check_mode==True the impl returns normally, "
                  "violating the normal-return guard. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-skip-writer", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SKIP_WRITER,
     "refinement": "raises correctly in check mode but on the normal (not-check) path does NOTHING "
                   "— never reaches a writer. A faithful real patch that skipped the writer "
                   "dispatch would make `makemigrations` (no --check) produce no migration file, "
                   "failing the P2P writing behaviour (the command must actually write migrations) "
                   "— would NOT resolve.",
     "rationale": "the normal-return path must produce an artefact. Rejection source: the GROWTH "
                  "pin len(store) >= len(Old) + 1 — with no writer run the store does not grow, so "
                  "the pin is unprovable. If it verified => SPEC-TOO-WEAK (artefact-production on "
                  "the normal path not enforced)."},
    {"id": "rival-partial-domain-update-gated-exit", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "gates the check-mode exit on `update_variant` too (`if check_mode and "
                   "update_variant: raise`). Correct on (check & update) and all non-check inputs, "
                   "but for (check_mode=True, update_variant=False) it falls through, writes a "
                   "FRESH migration, and returns 0 — i.e. `makemigrations --check` (without "
                   "--update) writes a file and exits 0. That is the pre-patch bug on the "
                   "fresh-writer sub-domain (the exact F2P configuration: --check on a plain app), "
                   "so it would NOT resolve.",
     "rationale": "partial-domain rival: correct on most of the flag domain, wrong on the "
                  "(check, not-update) sub-domain. Rejection source: Ensures(not check_mode) — for "
                  "check_mode=True/update_variant=False the impl returns normally in check mode. "
                  "(The store-grew Exsures conjunct is also unreachable since it returns, not "
                  "raises.) If it verified => SPEC-TOO-WEAK (domain-incomplete on the check-mode "
                  "exit)."},
    {"id": "rival-writer-dispatch-swap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP,
     "refinement": "keeps the exit-first fix but SWAPS the two writer callees under the flag "
                   "(update flag -> fresh writer, otherwise -> update writer). Its faithful real "
                   "patch swaps self.write_to_last_migration_files <-> self.write_migration_files "
                   "under the exit-first fix: the two callees have observably different on-disk "
                   "outcomes (fold into / rewrite the most recent migration file vs. emit a new "
                   "one), so the hidden update-mode and write-behaviour tests fail — would NOT "
                   "resolve.",
     "rationale": "writer-dispatch rival: growth + prefix hold for BOTH writers, so only the "
                  "VARIANT-BINDING pins can catch it. Rejection source: "
                  "Implies(update_variant, new tokens == 1) — the swapped dispatch stamps kind-0 "
                  "tokens under the update flag. If it verified => SPEC-TOO-WEAK (writer identity "
                  "unbound from the flag)."},
    {"id": "rival-always-one-writer", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_FRESH,
     "refinement": "keeps the exit-first fix but collapses the dispatch to ALWAYS the fresh "
                   "writer. Its faithful real patch always calls self.write_migration_files, "
                   "ignoring self.update: every update-mode hidden test (which asserts the most "
                   "recent migration is amended, not a new file emitted) fails — would NOT "
                   "resolve.",
     "rationale": "dispatch-collapse rival: growth + prefix hold, so only the VARIANT-BINDING "
                  "pins can catch it. Rejection source: Implies(update_variant, new tokens == 1) "
                  "— under the update flag the impl stamps kind-0 tokens. If it verified => "
                  "SPEC-TOO-WEAK (the update variant unconstrained)."},
    {"id": "rival-produce-twice", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DOUBLE,
     "refinement": "keeps the exit-first fix and the correct writer dispatch but performs the "
                   "MATCHING producing step TWICE. Its faithful real patch duplicates the "
                   "matching writer call (self.write_to_last_migration_files(changes) twice under "
                   "--update, self.write_migration_files(changes) twice otherwise) under the "
                   "exit-first fix. The real writers are NOT idempotent: the update writer folds "
                   "the pending changes into the most recent migration, renames it and deletes the "
                   "previous file, so a second run folds the already-folded operations in again "
                   "and renames/deletes on top of the artefact the first run just produced. The "
                   "hidden update-mode tests (which assert the amended migration's name, contents "
                   "and the previous file's disposition) and the scriptable-log test therefore "
                   "fail — machine-checked: this rival's faithful patch applies cleanly but the "
                   "official harness returns RESOLVED=False with 4 PASS_TO_PASS failures, while "
                   "the gold patch resolves 137/137 + 1/1. Would NOT resolve.",
     "rationale": "invocation-CARDINALITY rival: growth is a one-sided LOWER bound and the kind "
                  "pins quantify over the whole new range, so both survive a doubled dispatch "
                  "(growth 2x the yield, every token still the matching kind). Rejection source: "
                  "the PRODUCED-ONCE pin "
                  "Implies(update_variant, len(store) == len(Old) + update_artifact_yield()) "
                  "(and its fresh twin) — two invocations give len(Old) + 2*yield and yield >= 1, "
                  "so the equality fails. If it verified => SPEC-TOO-WEAK (the number of times the "
                  "producing step runs unconstrained; this was the recorded 2026-08-13 breaker "
                  "atk_7_double)."},
    {"id": "rival-mutate-then-exit-in-check", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MUTATE_RAISE,
     "refinement": "appends a produced-file token then raises in check mode — modelling a patch "
                   "that produces an artefact (even a single stray file) before exiting in --check. "
                   "Any such patch leaves a migration artefact on disk in --check, failing the F2P "
                   "no-artefact assertion — would NOT resolve. (No frame violation: `store` is full "
                   "permission, so the write is permitted; the defect is the resulting VALUE.)",
     "rationale": "value-level store attack on the raise path (supporting; carries a real "
                  "refinement). Rejection source: the EXIT-FIRST Exsures conjunct "
                  "ToSeq(store) == Old(ToSeq(store)) — the append grows the store before the raise "
                  "so it is unequal to its old value. Demonstrates the conjunct catches ANY store "
                  "growth before the raise, not only a real writer. If it verified => "
                  "SPEC-TOO-WEAK."},

    # ---- ambient-medium rivals (must be REJECTED) ----
    {"id": "rival-side-medium-in-check", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SIDE_IN_CHECK,
     "refinement": "in check mode it runs a REAL producing step whose produced-file tokens are "
                   "recorded into a throwaway list, then exits. Refined faithfully, the patch "
                   "swaps the command's own produced-file record for a throwaway list around a "
                   "real writer call in the --check branch and then exits non-zero: the record is "
                   "left exactly as it was, but the real writer still serializes the migration "
                   "file to the durable medium, so the F2P no-artefact assertion "
                   "(assertFalse(os.path.exists(...))) fails — would NOT resolve. This is the "
                   "recorded 2026-08-14 breaker (atk_8_sidestore).",
     "rationale": "the ungrounded-medium rival the store-only surface could not see: every clause "
                  "over the `store` parameter holds VACUOUSLY because the parameter is untouched. "
                  "Rejection source: the EXIT-FIRST conjunct "
                  "LEDGER.produced == Old(LEDGER.produced) — the writer axiom advanced the ambient "
                  "tally by its yield (>= 1), so something WAS committed to the medium before the "
                  "exit. If it verified => SPEC-TOO-WEAK (production modeled as a local list "
                  "effect rather than an act on the shared medium)."},
    {"id": "rival-partial-side-medium-in-check", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_SIDE,
     "refinement": "the same laundering restricted to the (--check, --update) corner: correct on "
                   "every other flag pair. Its faithful patch produces a migration file to disk "
                   "before exiting in --check --update, failing the same no-artefact assertion on "
                   "that configuration — would NOT resolve.",
     "rationale": "partial-domain version of the medium rival: a clause that pinned the tally on "
                  "only one flag pair would admit it. Rejection source: the same EXIT-FIRST tally "
                  "conjunct, which is stated for the whole check-mode domain rather than per flag "
                  "pair. If it verified => SPEC-TOO-WEAK (domain-incomplete on the medium)."},
    {"id": "rival-echo-fabricate-record", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ECHO,
     "refinement": "produces NOTHING and instead fabricates the produced-file record: it reads the "
                   "requested step's artefact yield and appends that many tokens of the matching "
                   "kind by hand. Refined faithfully, the patch appends plausible paths to the "
                   "command's written_files without writing any migration file, so `makemigrations` "
                   "(no --check) creates no migration on disk: the P2P writing tests fail — would "
                   "NOT resolve.",
     "rationale": "the ungrounded-oracle rival, and the reason the record clauses alone are NOT "
                  "grounded: the yield symbols are @Pure @ContractOnly FUNCTIONS the impl may "
                  "CALL, so the exact required post-length is computable and GROWTH + PREFIX + "
                  "VARIANT-BINDING + ONCE all discharge with no writer running (measured against "
                  "the store-only spec: it verified). Rejection source: the COMMITTED pin "
                  "LEDGER.produced >= Old(LEDGER.produced) + 1 — the only term in the spec that "
                  "can advance the tally is a writer-axiom invocation, and none occurred. If it "
                  "verified => SPEC-TOO-WEAK (the whole surface echoable)."},
    {"id": "rival-extra-producing-run", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_RUN,
     "refinement": "the correct exit-first dispatch onto the real record PLUS one extra real "
                   "producing run recorded into a throwaway list. Its faithful patch calls the "
                   "fresh writer an extra time with the record swapped out, so extra migration "
                   "files are serialized to disk while written_files looks correct: the update-mode "
                   "and scriptable P2P tests fail — would NOT resolve. This is the recorded "
                   "2026-08-14 second breaker (atk_9_sidestore_extra).",
     "rationale": "the record is byte-PERFECT here — growth, prefix, kinds and the produced-once "
                  "equality all hold on `store` — so no store-only clause can reject it. "
                  "Rejection source: the COMMITTED-ONCE pin "
                  "Implies(update_variant, LEDGER.produced == Old(...) + update_artifact_yield()) "
                  "(and its fresh twin): the medium received TWO runs' artefacts, so the tally is "
                  "at Old + yield + fresh_artifact_yield(), and both yields are >= 1. If it "
                  "verified => SPEC-TOO-WEAK (extra producing acts unconstrained)."},
    {"id": "rival-cross-carrier-production", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CROSS,
     "refinement": "runs the WRONG producing step for real (into a throwaway record) while "
                   "hand-recording the RIGHT kind onto the real record. Its faithful patch calls "
                   "write_migration_files under --update (and vice versa) with the record swapped, "
                   "then fakes written_files: the update-mode tests, which assert the most recent "
                   "migration was amended rather than a new file emitted, fail — would NOT resolve.",
     "rationale": "splits the two observables apart deliberately: the record claims the requested "
                  "variant's kind while the medium got the other step's artefacts. Rejection "
                  "source: the COMMITTED-ONCE pins, which name the yield of the REQUESTED step — "
                  "the wrong step advanced the tally by ITS yield, and the two yields are distinct "
                  "opaque symbols, so the equality is unprovable. If it verified => SPEC-TOO-WEAK "
                  "(the medium's producing step unbound from the variant flag)."},
    {"id": "rival-bump-the-tally", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BUMP,
     "refinement": "produces nothing and instead advances the ambient count of committed artefacts "
                   "directly. There is no faithful real patch that does this — the count of files "
                   "committed to the medium is not a variable the command can assign, it is the "
                   "consequence of writing files — which is precisely why the carrier is held at "
                   "HALF permission. Any patch that satisfied the committed-artefact clauses "
                   "without writing files would leave `makemigrations` producing no migration, "
                   "failing the P2P writing tests — would NOT resolve.",
     "rationale": "permission-level rival, and the guard that the COMMITTED pins are not "
                  "self-dischargeable. Rejection source: Acc(LEDGER.produced, 1/2) — the subject "
                  "holds READ access only, so the assignment fails with 'insufficient permission' "
                  "while the writer axioms, holding the same read access, still advance the tally. "
                  "If it verified => SPEC-TOO-WEAK (the medium observable forgeable by "
                  "bookkeeping)."},

    # ---- refusal-outcome rivals (must be REJECTED) ----
    {"id": "rival-self-decline", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SELF_DECLINE,
     "refinement": "escapes producing under the update variant by raising the refusal outcome "
                   "itself, without invoking the step that can legitimately refuse. Its faithful "
                   "patch raises the command-level error unconditionally under --update, so "
                   "`makemigrations --update` never amends the most recent migration: every "
                   "update-mode P2P test fails — would NOT resolve.",
     "rationale": "the refusal outcome must be a REPORTED consequence of the real step declining, "
                  "not an escape hatch. Rejection source: the DECLINE Exsures conjunct "
                  "update_step_declines() — the condition is OPAQUE (@Pure @ContractOnly with no "
                  "Ensures), so nothing in the spec establishes it and only a real invocation of "
                  "the update step, which Ensures `not update_step_declines()` on its normal path "
                  "and the condition on its refusal path, can discharge it. If it verified => "
                  "SPEC-TOO-WEAK (any impl could decline its way out of producing)."},
    {"id": "rival-decline-on-fresh-side", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DECLINE_FRESH,
     "refinement": "raises the refusal on the variant whose real producing step has no refusal to "
                   "raise: plain `makemigrations` would error out instead of writing fresh "
                   "migration files, failing the P2P writing tests — would NOT resolve.",
     "rationale": "the refusal is pinned to the variant that can produce it. Rejection source: the "
                  "DECLINE Exsures conjunct `update_variant`, which is false on this path. If it "
                  "verified => SPEC-TOO-WEAK (the refusal available across the whole domain)."},
    {"id": "rival-swallow-decline", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWALLOW,
     "refinement": "invokes the update step, swallows its refusal and returns normally having "
                   "produced nothing. Its faithful patch wraps the update writer in a bare "
                   "except and returns 0, so `makemigrations --update` on a squashed/applied/"
                   "depended-on most-recent migration silently succeeds instead of reporting the "
                   "error the P2P tests assert (test_makemigrations_update_squash_migration and "
                   "siblings assert the CommandError) — would NOT resolve.",
     "rationale": "control-flow-effect rival on the refusal path: the command must REPORT the "
                  "refusal, never convert it into a silent success. Rejection source: the "
                  "COMMITTED pin LEDGER.produced >= Old(LEDGER.produced) + 1 on the normal-return "
                  "path — the swallowed refusal committed nothing, so a normal return cannot show "
                  "the required advance. If it verified => SPEC-TOO-WEAK (a refusal launderable "
                  "into success)."},

    # ---- uniqueness rivals on the NON-COMPLETION outcome (must be REJECTED) ----
    {"id": "rival-self-non-completion", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SELF_FAIL,
     "refinement": "reports that the producing step could not carry the changes through, without "
                   "invoking it. Its faithful patch raises the serialization error unconditionally "
                   "under --update, so `makemigrations --update` never amends the most recent "
                   "migration: all seven update-mode P2P tests fail — would NOT resolve.",
     "rationale": "the non-completion outcome must be a REPORTED consequence of a real step "
                  "stopping partway, never a way out of producing. Rejection source: the "
                  "NON-COMPLETION Exsures conjunct Implies(update_variant, update_step_fails()) — "
                  "the condition is OPAQUE (@Pure @ContractOnly), so only a real invocation of "
                  "that step, which Ensures `not update_step_fails()` on its normal path and the "
                  "condition on its non-completion path, can discharge it. If it verified => "
                  "SPEC-TOO-WEAK (the new outcome would be a universal escape hatch, which is "
                  "exactly the failure mode of adding an outcome to a contract)."},
    {"id": "rival-non-completion-in-check", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FAIL_IN_CHECK,
     "refinement": "in check mode, consults whether the changes can be rendered and surfaces THAT "
                   "error instead of the documented non-zero exit. The real command exits non-zero "
                   "in --check for every change set it detects, including one it could not render: "
                   "measured on the real callee (check + unserializable app -> SystemExit(1), with "
                   "the writers never reached). No graded test drives check-mode-with-an-"
                   "unserializable-change, so this rival is justified by that measured divergence "
                   "from the reference rather than by a test break; the F2P's contract "
                   "('--check should exit with a non-zero status') is what it changes.",
     "rationale": "the non-completion outcome is pinned OUTSIDE check mode, because in check mode "
                  "no producing step is reached at all. Rejection source: the NON-COMPLETION "
                  "Exsures conjunct `not check_mode`. Note this rival commits nothing and records "
                  "nothing, so every value conjunct it could otherwise trip holds — the mode pin "
                  "is the only thing standing between the spec and a second, laundered exit path "
                  "out of check mode. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-swallow-non-completion", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWALLOW_FAIL,
     "refinement": "invokes the fresh step, absorbs its non-completion and returns normally. Its "
                   "faithful patch wraps the writer in `except ValueError: pass`, so a change set "
                   "with an unserializable default makes `makemigrations` exit 0 having written "
                   "nothing, while the P2P test test_failing_migration asserts "
                   "assertRaisesMessage(ValueError, 'Cannot serialize') — would NOT resolve.",
     "rationale": "control-flow-effect rival on the new path: the command must REPORT the "
                  "non-completion, never convert it into a silent success. Rejection source: the "
                  "normal-return pins — a step that stopped partway advanced the tally by at most "
                  "part of its yield, so neither LEDGER.produced >= Old + 1 nor the "
                  "COMMITTED-ONCE equality can be shown on a normal return. If it verified => "
                  "SPEC-TOO-WEAK (a failed producing run launderable into success)."},
    {"id": "rival-relabel-non-completion-as-refusal", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_RELABEL_FAIL,
     "refinement": "converts a step that stopped partway into the fold-refusal outcome. Its "
                   "faithful patch catches the serialization error and re-raises the command-level "
                   "refusal, so `makemigrations --update` on an unserializable change set reports "
                   "'migration cannot be folded' where the real command surfaces the serialization "
                   "error (measured: update + unserializable app -> ValueError('Cannot "
                   "serialize'), nothing committed), and it asserts the refusal's state (nothing "
                   "committed, nothing recorded) for a run that may have committed part of its "
                   "yield — the amended file would be left on disk while the caller is told "
                   "nothing happened.",
     "rationale": "the two abnormal outcomes are DISTINCT and neither may be reported for the "
                  "other. Rejection source: the DECLINE Exsures, whose conjunct "
                  "update_step_declines() cannot be shown on this path (the step reported "
                  "non-completion, which establishes update_step_fails() and says nothing about "
                  "foldability) and whose ToSeq(store) == Old / LEDGER.produced == Old conjuncts "
                  "cannot be shown for a partway run. If it verified => SPEC-TOO-WEAK (outcomes "
                  "interchangeable, and a partial commit concealable behind the refusal)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real Command.write_migration_files callee)
# ===========================================================================
# Two @ContractOnly A-consumed axioms model the UNCHANGED artefact writers:
#   write_fresh_artifacts(store)  <-> Command.write_migration_files
#   write_update_artifacts(store) <-> Command.write_to_last_migration_files
# Each axiom's Ensures: ONE invocation of the writer appends exactly that
# writer's own artefact yield of produced-file tokens
# (len(store) == len(Old) + <yield>(), the yield being an opaque `>= 1` quantity
# of the pending changes, NOT a literal) and keeps the previously-produced
# tokens as a prefix. The `>= 1`-but-unpinned shape is what keeps the axiom
# sound across change-set sizes (one app -> +1, two apps -> +2) while still
# making the count of INVOCATIONS observable — probe (2) below is the
# over-claim guard that a literal `== +1` would fail.
# The probes EXECUTE the real callee (mirroring axiom_check.py) — never
# scrape source. Imports Django (the package under test) + stdlib only. The
# fresh writer is exercised directly on real autodetector `changes` dicts; the
# update writer shares the artefact-producing shape (mapping.md §3.2) and the
# end-to-end portion validates that some writer produces an artefact iff --check
# is off. Files opened with encoding="utf-8" (old-Python ASCII-locale guard).
#
# Bootstrap: build two writable single-model apps (so there ARE pending
# changes), configure Django, return helpers that drive the REAL autodetector
# and the REAL Command.write_migration_files. Adapted verbatim-in-spirit from
# tasks/django__django-16116/axiom_check.py (read on the HOST and embedded; the
# runner mounts ONLY the probe at /work, so axiom_check.py is NOT in-container).

_BOOT = r'''
import os, sys, tempfile, shutil

def _make_app(work, name):
    pkg = os.path.join(work, name)
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    with open(os.path.join(pkg, "models.py"), "w", encoding="utf-8") as fh:
        fh.write(
            "from django.db import models\n"
            "class Widget(models.Model):\n"
            "    name = models.CharField(max_length=20)\n"
            "    class Meta:\n"
            "        app_label = %r\n" % (name,)
        )
    mig = os.path.join(pkg, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return mig

_WORK = tempfile.mkdtemp(prefix="pbt16116_")
sys.path.insert(0, _WORK)
_MIG1 = _make_app(_WORK, "axcheck")
_MIG2 = _make_app(_WORK, "axcheck2")

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "axcheck", "axcheck2"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        MIGRATION_MODULES={"axcheck": "axcheck.migrations",
                           "axcheck2": "axcheck2.migrations"},
    )
django.setup()

from django.apps import apps
from django.core.management import call_command
from django.core.management.commands.makemigrations import Command
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import NonInteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState
from io import StringIO

def real_changes(trim_apps):
    loader = MigrationLoader(None, ignore_no_migrations=True)
    questioner = NonInteractiveMigrationQuestioner(
        specified_apps=set(), dry_run=False, verbosity=0)
    autodetector = MigrationAutodetector(
        loader.project_state(), ProjectState.from_apps(apps), questioner)
    return autodetector.changes(graph=loader.graph,
                                trim_to_apps=set(trim_apps),
                                convert_apps=set(trim_apps), migration_name=None)

def fresh_command():
    cmd = Command()
    cmd.verbosity = 0; cmd.interactive = False; cmd.dry_run = False
    cmd.merge = False; cmd.empty = False; cmd.scriptable = False
    cmd.include_header = True; cmd.update = False; cmd.migration_name = None
    cmd.written_files = []; cmd.stdout = StringIO(); cmd.stderr = StringIO()
    return cmd

def _cleanup(paths):
    for p in paths:
        try: os.remove(p)
        except OSError: pass

def clean_mig(mig):
    for fn in os.listdir(mig):
        if fn != "__init__.py":
            fp = os.path.join(mig, fn)
            (shutil.rmtree if os.path.isdir(fp) else os.remove)(fp)

def mig_files(mig):
    return sorted(f for f in os.listdir(mig)
                  if f.endswith(".py") and f != "__init__.py")
'''

# (1) axiom-soundness — YIELD-EXACT growth + PREFIX preservation, single-app
# changes. The real Command.write_migration_files on a one-app changes dict must
# append exactly its yield of tokens for those changes (here +1 = len(changes),
# >=1) to written_files and keep the previously-recorded tokens as a prefix, with
# each recorded file on disk. A no-growth or a dropped-prefix => the writer axiom
# (len == len(Old) + yield, yield >= 1, prefix) is UNSOUND.
_AX_GROWTH_SOUND = _BOOT + r'''
changes1 = real_changes({"axcheck"})
assert changes1, "setup invalid: autodetector reported NO pending changes"
cmd = fresh_command()
before = list(cmd.written_files)
# seed a pre-existing recorded token to test prefix preservation
cmd.written_files = ["/pre/existing/0001_seed.py"]
before = list(cmd.written_files)
cmd.write_migration_files(changes1)
after = list(cmd.written_files)
grew = len(after) - len(before)
if grew < 1:
    print("AXIOM-UNSOUND: real write_migration_files appended NO token "
          "(%r -> %r); writer not artefact-producing" % (before, after))
    sys.exit(1)
if after[:len(before)] != before:
    print("AXIOM-UNSOUND: prefix not preserved (%r -> %r)" % (before, after))
    sys.exit(1)
for p in after[len(before):]:
    if not os.path.exists(p):
        print("AXIOM-UNSOUND: recorded produced file %r not on disk" % (p,))
        sys.exit(1)
_cleanup(after[len(before):]); clean_mig(_MIG1)
print("OK growth+prefix sound: single-app changes grew written_files by %d "
      "(>= +1), prefix preserved, files on disk" % (grew,))
sys.exit(0)
'''

# (2) axiom-soundness — the OVER-CLAIM check: a TWO-app changes dict grows the
# store by 2, proving the writer's per-invocation append is the change set's own
# yield and a LITERAL `== +1` axiom would be UNSOUND. This is the exact reason
# the contract is stated against an unpinned `yield >= 1`, never a constant.
_AX_OVERCLAIM = _BOOT + r'''
changes2 = real_changes({"axcheck", "axcheck2"})
if len(changes2) < 2:
    print("setup invalid: expected >= 2 pending migrations, got %d"
          % (len(changes2),)); sys.exit(1)
cmd = fresh_command()
before = list(cmd.written_files)
cmd.write_migration_files(changes2)
after = list(cmd.written_files)
grew = len(after) - len(before)
if grew < 1:
    print("AXIOM-UNSOUND: multi-app changes produced no token (%r -> %r)"
          % (before, after)); sys.exit(1)
if grew < 2:
    print("OVER-CLAIM: a >=2-migration changes grew the store by only %d; an "
          "'== +1' axiom would be UNSOUND — the contract MUST be '>= +1'" % (grew,))
    sys.exit(1)
if after[:len(before)] != before:
    print("AXIOM-UNSOUND: prefix not preserved on multi-app changes"); sys.exit(1)
_cleanup(after); clean_mig(_MIG1); clean_mig(_MIG2)
print("OK over-claim guard: two-app changes grew the store by %d (>= 2), so an "
      "unpinned per-invocation yield is the only sound bound ('== +1' is "
      "over-claimed)" % (grew,))
sys.exit(0)
'''

# (2b) axiom-soundness — PER-INVOCATION yield: ONE invocation appends the change
# set's yield, and a SECOND invocation on the same changes appends that yield
# AGAIN (the store ends at len(Old) + 2*yield). This is what licenses stating the
# function postcondition as an EQUALITY against a single writer's yield: the real
# producing step is not idempotent in its produced-file record, so performing it
# twice is observably twice as much production. If a second invocation appended
# NOTHING (an idempotent writer) the produced-once equality would be
# indistinguishable from the lower bound and could not sense a doubled dispatch.
_AX_PER_INVOCATION = _BOOT + r'''
changes1 = real_changes({"axcheck"})
if not changes1:
    print("setup invalid: autodetector reported NO pending changes"); sys.exit(1)
cmd = fresh_command()
cmd.write_migration_files(changes1)
after1 = list(cmd.written_files)
one = len(after1)
if one < 1:
    print("AXIOM-UNSOUND: first invocation appended NO token"); sys.exit(1)
# second invocation of the SAME producing step on the SAME pending changes
cmd.write_migration_files(changes1)
after2 = list(cmd.written_files)
two = len(after2) - one
if after2[:one] != after1:
    print("AXIOM-UNSOUND: second invocation did not keep the first invocation's "
          "tokens as a prefix (%r -> %r)" % (after1, after2)); sys.exit(1)
if two != one:
    print("PER-INVOCATION MIS-MODELED: one invocation appended %d token(s) but a "
          "second appended %d; the axiom's 'each invocation appends its yield' "
          "shape does not hold" % (one, two)); sys.exit(1)
_cleanup(after2); clean_mig(_MIG1)
print("OK per-invocation yield: one invocation appended %d token(s), a second "
      "invocation on the same pending changes appended %d more (total %d = "
      "2x yield), prefix preserved — the producing step is NOT idempotent, so "
      "an equality against a SINGLE invocation's yield genuinely senses how "
      "many times it ran" % (one, two, len(after2)))
sys.exit(0)
'''

# (3) axiom-containment — every callee-input the MODEL can reach lies in the
# axiom's Requires(list_pred(store)) domain. The model passes `store` (any
# produced-file list, incl. empty) to a writer ONLY on the not-check path; the
# writer accepts any list state. We exercise the real writer on (a) a fresh
# command (empty written_files) and (b) a command with a pre-seeded written_files
# (non-empty), under a real one-app changes dict — both the regimes the model's
# control flow can reach. A regime the callee rejected would be
# AXIOM-TOO-WEAK-FOR-CALLER. (Covering MORE callee inputs than the model reaches
# would be SOUND, not a defect; we only confirm the reachable ones are accepted.)
_AX_CONTAINMENT = _BOOT + r'''
changes1 = real_changes({"axcheck"})
assert changes1, "setup invalid: no pending changes"
# regime (a): empty store (fresh command, written_files == [])
cmd = fresh_command()
try:
    cmd.write_migration_files(changes1)
except Exception as e:
    print("AXIOM-TOO-WEAK-FOR-CALLER: writer rejected the empty-store regime: %r"
          % (e,)); sys.exit(1)
_cleanup(cmd.written_files); clean_mig(_MIG1)
# regime (b): non-empty store (pre-seeded written_files)
cmd = fresh_command()
cmd.written_files = ["/pre/existing/0001_seed.py"]
try:
    cmd.write_migration_files(changes1)
except Exception as e:
    print("AXIOM-TOO-WEAK-FOR-CALLER: writer rejected the non-empty-store regime: %r"
          % (e,)); sys.exit(1)
_cleanup([p for p in cmd.written_files if p.startswith("/tmp") or "axcheck" in p])
clean_mig(_MIG1)
print("containment OK: real write_migration_files accepts every model-reachable "
      "store regime (empty AND non-empty written_files) on real pending changes; "
      "no caller-reachable input lies outside the axiom's list_pred(store) domain.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-growth-prefix-sound", "axiom": "write_fresh_artifacts",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_GROWTH_SOUND,
     "rationale": "the writer axiom's Ensures says ONE invocation appends that writer's own "
                  "artefact yield (len(store) == len(Old) + yield(), yield >= 1) and keeps the "
                  "prefix. The REAL Command.write_migration_files on a one-app changes dict must "
                  "grow written_files by that yield (>=1), preserve the pre-seeded prefix, and "
                  "write each recorded file to disk. Any no-growth or dropped prefix => "
                  "AXIOM-UNSOUND. (Patch-state-independent: the writer is unchanged by the gold "
                  "patch.)"},
    {"id": "ax-overclaim-ge-not-eq", "axiom": "write_fresh_artifacts",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_OVERCLAIM,
     "rationale": "validates that the per-invocation append must be stated against an UNPINNED "
                  "yield, never a literal `== +1`: a two-app changes dict grows the store by 2 "
                  "(one token per migration). A literal `== +1` axiom would be strictly stronger "
                  "than the real callee here, hence UNSOUND; the opaque `yield >= 1` is the only "
                  "sound way to say 'this step's own output' (G-AX Defect 1+2 fix)."},
    {"id": "ax-per-invocation-yield", "axiom": "write_fresh_artifacts",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_PER_INVOCATION,
     "rationale": "validates the shape the PRODUCED-ONCE function pin rests on: EACH invocation "
                  "appends the change set's yield, so a second invocation of the same producing "
                  "step on the same pending changes appends that yield AGAIN (store ends at "
                  "len(Old) + 2*yield) with the first invocation's tokens kept as a prefix. The "
                  "real producing step is therefore NOT idempotent in its produced-file record. "
                  "Were it idempotent (second call appends nothing) the equality "
                  "len(store) == len(Old) + yield() would be satisfied by a doubled dispatch too "
                  "and could not sense invocation cardinality — the axiom would not support the "
                  "clause that rejects rival-produce-twice."},
    {"id": "ax-containment", "axiom": "write_fresh_artifacts",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach (store = any produced-file list, empty "
                  "OR non-empty, passed to a writer only on the not-check path) lies in the "
                  "axiom's Requires(list_pred(store)) domain: the real writer accepts both an "
                  "empty and a pre-seeded written_files on real pending changes. A model-reachable "
                  "input the callee rejected would be AXIOM-TOO-WEAK-FOR-CALLER; here the domain "
                  "covers every reachable store regime."},
]
