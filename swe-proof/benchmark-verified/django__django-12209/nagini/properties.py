"""properties.py — PBT falsification manifest for django__django-12209.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    store_single_table(pk_explicit, force_insert, pk_set, adding,
                       pk_has_default) -> bool

a PURE boolean decision (the single-table save routine `Model._save_table`'s
update/insert short-cut, abstracted to five plain bools + the unchanged UPDATE
primitive's outcome). The load-bearing contract:

    Requires(True)                                            # no input restriction
    Requires(MustTerminate(2))                                # TOTAL correctness
    Ensures(Result() == (pk_set
                         and not forces_insert(pk_explicit, force_insert,
                                               adding, pk_has_default)
                         and update_matched_row()))           # MASTER PIN (clause 1)
    Ensures(Implies(pk_explicit and pk_set and not force_insert,
                    Result() == update_matched_row()))        # POSITIVE clause 2

with the GROUNDED @Pure helpers (fully unfolded boolean functions of the args):

    shortcut_engaged(pe,fi,ad,hd) == (not pe) and (not fi) and ad and hd
    forces_insert(pe,fi,ad,hd)    == fi or shortcut_engaged(pe,fi,ad,hd)

and the single A-consumed axiom `update_matched_row() -> bool` (@Pure
@ContractOnly, nullary, NO Ensures — the weakest contract; an instance-fixed
observation of the unchanged `Model._do_update`).

What the spec defends, and the attacks it must survive:

  * FRAME-MUTATION is N/A here. There is NO read-only `Acc(x,1/2)` input: all
    five parameters are plain `bool` (immutable primitives passed by value) and
    there is no list_pred / object carrier to overwrite. There is no mutable
    frame to subvert, so the mandatory frame-mutation probe does not apply
    (documented in the structured `assessment`). In its place we carry an honest
    cheapest-impl positive control (`pos-cheapest`).

  * UNGROUNDED-ORACLE ECHO is the one genuine echo surface: `update_matched_row`
    is @ContractOnly with NO Ensures, so an impl could try `return
    update_matched_row()` (echo the nullary axiom). But clause 1 pins Result()
    EXACTLY to `pk_set and not forces_insert(...) and update_matched_row()`, a
    function OF the args ANDed with the axiom — so the bare echo is WRONG
    whenever the AND-guard is False yet the axiom is True. `echo-update-row` is
    that wrong echo and MUST reject (else SPEC-TOO-WEAK). The guard part of the
    pin is GROUNDED in `shortcut_engaged`/`forces_insert` (no opaque marker), so
    there is no wrong echo of the *decision*; the cheapest correct impl
    (`pos-cheapest`) still computes the guard and ANDs the axiom — the real work.

  * The discriminating content of the gold fix is the single added conjunct
    `not pk_explicit` (repo `not raw`) inside `shortcut_engaged`. The pre-patch
    impl drops it; that is wrong EXACTLY on the sub-domain pk_explicit=True,
    force_insert=False, pk_set=True, adding=True, pk_has_default=True (with the
    row present, update_matched_row()=True): the spec demands an UPDATE (Result
    True) but the pre-patch short-cut returns False (a blind INSERT). The primary
    partial-domain rival `prepatch-drop-conjunct` is exactly model_prepatch.py.

  * DIVERGENCE is a live surface, because the pre-condition region carries
    `Requires(MustTerminate(2))`: what the verifier proves is TOTAL correctness,
    not partial. Without it an impl that never reaches the return satisfies both
    `Ensures` clauses vacuously and VERIFIES — so `selfcall-diverges` (an
    unconditional self-call on constant arguments) is a reject-lane rival, and it
    is the case that measures the obligation: it verifies with the obligation
    removed and is rejected with it. Note that a self-call can never satisfy
    MustTerminate at ANY level, since the caller's level must strictly exceed the
    callee's; that is why the admissibility probe asserts over the pure helpers on
    the F2P input rather than calling the method.

  * CONTROL-FLOW-EFFECT is N/A: store_single_table is a total pure boolean with a
    single return path and no raise / no side effect / no read-only frame; the
    value equality of the return bool captures everything observable. (No
    capability-token rival is needed — there is no effect invisible to the value
    abstraction.)

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION catching wrong behaviour
(clause 1 / clause 2), never from a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P (the serializer/loaddata re-save of an explicit, already-stored UUID pk
must UPDATE, not re-INSERT). The axiom lane runs the REAL `Model._do_update` in
Docker — exactly the operation axiom_check.py / G-AX validates.
"""
from pathlib import Path

INSTANCE = "django__django-12209"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The gold impl body, verbatim (between # impl-start / # impl-end).
_GOLD_IMPL = (
    "    force_insert_eff = force_insert\n"
    "    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:\n"
    "        force_insert_eff = True\n"
    "    updated = False\n"
    "    if pk_set and not force_insert_eff:\n"
    "        updated = update_matched_row()\n"
    "    return updated\n"
)
assert _BASE.count(_GOLD_IMPL) == 1, "drift: gold impl body not found verbatim"

# the guard line whose leading conjunct is the gold fix.
_GUARD = "    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:\n"
assert _BASE.count(_GUARD) == 1, "drift: guard line not unique"

# the impl head — insertion point for the admissibility self-call.
_HEAD = "    force_insert_eff = force_insert\n"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-DIFFERENT but CORRECT impl. Instead of mutating a fresh
# `force_insert_eff` local through a guard `if`, compute the effective decision
# in ONE boolean expression (De Morgan / direct disjunction matching
# forces_insert exactly), then compute `updated` in a SINGLE return with a
# conjunction (no intermediate `updated` local, no second `if`). Semantically
# identical to gold; entirely different executable shape. Pure boolean logic the
# verifier discharges directly (no induction / no framing lemma needed — there
# is no loop). If this fails to verify, the postcondition is over-fit to the gold
# control-flow shape => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _GOLD_IMPL,
    "    fi_eff = force_insert or (\n"
    "        (not pk_explicit) and (not force_insert) and adding and pk_has_default)\n"
    "    return pk_set and (not fi_eff) and update_matched_row()\n",
)

# (5b / 2) HONEST cheapest correct impl. The most direct echo of the contract
# would be `return update_matched_row()` (the nullary axiom) — but that is the
# WRONG echo handled by `echo-update-row` below. The cheapest CORRECT impl still
# computes the GROUNDED guard `pk_set and not forces_insert(...)` and ANDs the
# axiom — i.e. the real decision work. This control writes exactly that as a
# single expression mirroring clause 1's RHS, asserting (by verifying) there is
# no shorter correct form that drops the grounded guard. If it fails to verify =>
# SPEC-TOO-STRONG; that it verifies shows the grounded guard is satisfiable by a
# faithful minimal impl (and that the only echo that drops the guard is wrong,
# per echo-update-row).
_POS_CHEAPEST = _swap(
    _BASE, _GOLD_IMPL,
    "    sc = (not pk_explicit) and (not force_insert) and adding and pk_has_default\n"
    "    return pk_set and (not (force_insert or sc)) and update_matched_row()\n",
)

# (6) ADMISSIBILITY. The exact F2P-shaped input must be ADMITTED by the
# pre-condition region — the serializer re-save of an explicit, already-stored
# UUID pk: pk_explicit=True (repo raw=True), force_insert=False, pk_set=True,
# adding=True, pk_has_default=True. Stated as a reachability claim: ON that
# input the pre-condition region (`Requires(True)` AND
# `Requires(MustTerminate(2))`) must be satisfiable, and the spec must there
# demand the UPDATE — `forces_insert(...)` is False, so clause 2 pins Result()
# to the primitive's outcome. If the F2P shape could not be reached under the
# pre-condition, this body would be dead code => PRECOND-TOO-STRONG.
#
# NOTE (termination): this probe deliberately does NOT self-call. The former
# shape (`_probe = store_single_table(True, False, True, True, True)` spliced
# unconditionally at the impl head) is UNBOUNDED RECURSION on CONSTANT
# arguments — it never returns. Under `Requires(MustTerminate(2))` Nagini
# rejects it ("Callee store_single_table might not take all unsatisfied
# obligations from the caller"), and no level assignment can rescue it: a
# self-call needs the caller's level STRICTLY above the callee's, which is
# impossible when caller and callee are the same method (measured at levels 2
# and 3; both rejected, and guarding the call does not help either). That
# divergence is a real defect of the old case, not a measure this author failed
# to find, so it has MOVED to the reject lane as `selfcall-diverges` below —
# where its rejection is now an asserted PROPERTY of the spec. Admissibility is
# preserved here by a probe that tests the same F2P input without diverging.
_ADMISS = _swap(
    _BASE, _HEAD,
    "    if pk_explicit and (not force_insert) and pk_set and adding and pk_has_default:\n"
    "        Assert(not forces_insert(pk_explicit, force_insert, adding, pk_has_default))\n"
    + _HEAD,
)

# (6b) The DIVERGING former admissibility probe, now a uniqueness rival. An
# unconditional self-call on constant arguments never reaches the return, so
# every `Ensures` holds vacuously of it. Under the obligation-free spec it
# VERIFIED (measured); with `Requires(MustTerminate(2))` it must be REJECTED.
_RIVAL_SELFCALL = _swap(
    _BASE, _HEAD,
    "    _probe = store_single_table(True, False, True, True, True)\n" + _HEAD,
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (3, PRIMARY partial-domain == the discriminating BUG) DROP THE ADDED CONJUNCT.
# Remove the leading `(not pk_explicit) and` from the guard — the EXACT pre-gold
# behaviour (model_prepatch.py; repo: the guard without `not raw and`). Correct
# on every input where pk_explicit is False, WRONG on the explicit-pk sub-domain.
_RIVAL_PREPATCH = _swap(
    _BASE, _GUARD,
    "    if (not force_insert) and adding and pk_has_default:\n",
)

# (2, UNGROUNDED-ORACLE ECHO) Echo the nullary @ContractOnly axiom directly:
# `return update_matched_row()`. The axiom has NO Ensures, so this is the bare
# echo. It IGNORES the entire grounded guard `pk_set and not forces_insert(...)`,
# so it is WRONG whenever that guard is False yet the row exists (e.g.
# force_insert=True, pk_set=True, update_matched_row()=True: spec requires Result
# False — the short-cut/forced insert was taken — but the echo returns True).
_RIVAL_ECHO = _swap(
    _BASE, _GOLD_IMPL,
    "    return update_matched_row()\n",
)

# (3b, partial-domain) DROP the `pk_set` factor. Return the decision WITHOUT the
# identifier-present gate: `not forces_insert(...) and update_matched_row()`.
# Correct whenever pk_set is True; WRONG on every pk_set=False input where the
# rest hold (spec requires Result False — no identifier to match — but this
# returns the axiom value). Targets the `pk_set` factor of clause 1.
_RIVAL_DROP_PKSET = _swap(
    _BASE, _GOLD_IMPL,
    "    sc = (not pk_explicit) and (not force_insert) and adding and pk_has_default\n"
    "    return (not (force_insert or sc)) and update_matched_row()\n",
)

# (3c, INVERTED conjunct — the opposite-direction bug) Use `pk_explicit` instead
# of `not pk_explicit`, so the short-cut engages ONLY for a caller-supplied
# identifier and is SUPPRESSED for a field-generated one. This is wrong in the
# mirror direction: on pk_explicit=False, force_insert=False, pk_set=True,
# adding=True, pk_has_default=True (the genuinely-new UUID-default INSERT case)
# the spec requires the short-cut to engage (forces_insert True => Result False),
# but this impl suppresses it and returns the axiom value. A faithful real patch
# `if raw and ...:` would re-INSERT genuinely-new instances (and break the
# ordinary create() fast-path the original commit added) — it would NOT resolve.
_RIVAL_INVERT = _swap(
    _BASE, _GUARD,
    "    if pk_explicit and (not force_insert) and adding and pk_has_default:\n",
)

# (3d, DROP the force_insert FACTOR of the effective decision) Compute the
# short-cut but DON'T OR-in the caller's `force_insert`: the update path is gated
# only on `not shortcut_engaged(...)`, ignoring a caller-forced insert. Wrong on
# force_insert=True, pk_set=True, shortcut=False, row present: spec requires
# Result False (the caller forced an INSERT, no UPDATE) but this returns the axiom
# True. A faithful real patch that drops the `not force_insert` consultation of
# the *returned-flag* path would UPDATE on a force_insert=True save — violating
# the force_insert contract that many P2P saves rely on; it would NOT resolve.
_RIVAL_DROP_FORCE = _swap(
    _BASE, _GOLD_IMPL,
    "    sc = (not pk_explicit) and (not force_insert) and adding and pk_has_default\n"
    "    updated = False\n"
    "    if pk_set and not sc:\n"
    "        updated = update_matched_row()\n"
    "    return updated\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but correct: the effective force-insert decision is "
                  "computed in ONE disjunction (matching forces_insert) and the result in a "
                  "SINGLE return conjunction (no `force_insert_eff`/`updated` locals, no second "
                  "`if`). Pure boolean logic the verifier discharges directly — no loop, no "
                  "induction/framing lemma. If it fails to verify, the spec is over-fit to the "
                  "gold control-flow shape => SPEC-TOO-STRONG."},
    {"id": "pos-cheapest", "kind": "soundness", "expect": "verify",
     "module": _POS_CHEAPEST,
     "rationale": "the cheapest CORRECT impl still computes the GROUNDED guard "
                  "`pk_set and not (force_insert or shortcut_engaged(...))` and ANDs the nullary "
                  "axiom — the real decision work. Written as clause 1's RHS verbatim; must "
                  "verify (else SPEC-TOO-STRONG). Demonstrates the only echo that drops the guard "
                  "is the WRONG one (echo-update-row), i.e. the decision part of the pin is "
                  "grounded, not an opaque marker."},
    {"id": "admiss-fshape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the exact F2P-shaped input (pk_explicit=True i.e. repo raw=True, "
                  "force_insert=False, pk_set=True, adding=True, pk_has_default=True — the "
                  "serializer re-save of an explicit, already-stored UUID pk) must be ADMITTED by "
                  "the pre-condition region `Requires(True)` + `Requires(MustTerminate(2))`, and "
                  "the spec must there demand the UPDATE (forces_insert False). Verifying shows "
                  "the branch is live, i.e. the precondition is satisfiable on the F2P shape; the "
                  "VACUITY CONTROL is `Assert(False)` under the same guard, which FAILS (measured) "
                  "— so the guard is feasible and this asserts something. If the F2P shape were "
                  "inadmissible the body would be dead code => PRECOND-TOO-STRONG. Does NOT "
                  "self-call: see selfcall-diverges for why that shape cannot terminate."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "selfcall-diverges", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SELFCALL,
     "refinement": "an unconditional self-call on CONSTANT arguments "
                   "(`store_single_table(True, False, True, True, True)` at the impl head) is "
                   "unbounded recursion with no base case: the routine NEVER returns. Its "
                   "faithful real patch is a `Model._save_table` that re-enters itself on every "
                   "save and hangs the process — every save path (not merely the F2P one) fails to "
                   "complete, so it resolves nothing.",
     "rationale": "DIVERGENCE rival — the hole `Requires(MustTerminate(2))` exists to close. "
                  "Because it never reaches the return, both `Ensures` clauses hold VACUOUSLY of "
                  "it: partial correctness cannot see this defect at all. Measured: with the "
                  "obligation REMOVED from the pre-condition region this module VERIFIES "
                  "(`Verification successful`), which is precisely `verify` failing to imply "
                  "`correct`; WITH the obligation Nagini rejects it ('Obligation leak check "
                  "failed. Callee store_single_table might not take all unsatisfied obligations "
                  "from the caller'). No level rescues it — a self-call requires the caller's "
                  "level strictly ABOVE the callee's, unsatisfiable when they are the same method "
                  "(levels 2 and 3 both measured as rejected). This case was formerly the "
                  "admissibility probe `admiss-fshape`, which asserted the spec ACCEPTS it; that "
                  "was only true while the spec demanded no termination. If it verified => "
                  "SPEC-TOO-WEAK (a non-terminating impl satisfies the spec)."},
    {"id": "prepatch-drop-conjunct", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "drops the gold-added `not pk_explicit` conjunct (repo `not raw and`) — the "
                   "EXACT pre-gold guard (model_prepatch.py). Its faithful real patch is the "
                   "Django-3.0 regression: re-saving an instance with an explicit, already-stored "
                   "UUID pk in raw/serialiser mode takes the straight-to-INSERT short-cut and "
                   "issues a second INSERT (duplicate-key failure) instead of an UPDATE. The "
                   "serializer/loaddata re-save F2P (UUIDDefaultData round-trip; the "
                   "problem_statement's `s1 = Sample(pk=s0.pk); s1.save()` => UPDATE) FAILS; it "
                   "would NOT resolve.",
     "rationale": "the discriminating bug / primary partial-domain on the explicit-pk sub-domain "
                  "(correct for pk_explicit=False, wrong for pk_explicit=True). Rejection source: "
                  "clause 1 `Result() == (pk_set and not forces_insert(pk_explicit,...) and "
                  "update_matched_row())`. Witness pk_explicit=True, force_insert=False, "
                  "pk_set=True, adding=True, pk_has_default=True, row present: forces_insert is "
                  "False so the spec requires Result True (UPDATE) but this impl sets the "
                  "short-cut and returns False. Also caught by clause 2. If it verified => "
                  "SPEC-TOO-WEAK (admits the regression)."},
    {"id": "echo-update-row", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ECHO,
     "refinement": "`return update_matched_row()` blindly returns the UPDATE primitive's outcome "
                   "regardless of whether the update path is ever reached. Its faithful real "
                   "patch would report `updated=True` for a present row even when the routine "
                   "actually took the straight-to-INSERT short-cut or force_insert (no UPDATE was "
                   "issued) — fabricating an update that never happened. It mis-handles every "
                   "force_insert / short-cut save and every absent-pk save; it would NOT resolve.",
     "rationale": "the ungrounded-oracle echo of the nullary @ContractOnly axiom (which has NO "
                  "Ensures). Rejection source: clause 1 pins Result() to "
                  "`pk_set and not forces_insert(...) and update_matched_row()`. Witness "
                  "force_insert=True, pk_set=True, update_matched_row()=True: forces_insert is "
                  "True so the spec requires Result False, but the echo returns True. If it "
                  "verified => SPEC-TOO-WEAK (the axiom could be echoed without doing the "
                  "decision work)."},
    {"id": "drop-pk-set", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_PKSET,
     "refinement": "drops the `pk_set` identifier-present gate, returning "
                   "`not forces_insert(...) and update_matched_row()`. Its faithful real patch "
                   "would attempt/report an UPDATE for an instance with NO primary-key value "
                   "present (pk_set False) — Django never reaches `_do_update` without a pk, so "
                   "this fabricates an update outcome on the no-pk save path; it would NOT "
                   "resolve.",
     "rationale": "partial-domain on the pk_set factor of clause 1 (correct when pk_set=True, "
                  "wrong when pk_set=False). Rejection source: clause 1's `pk_set and ...`. "
                  "Witness pk_set=False, force_insert=False (so forces_insert False), "
                  "update_matched_row()=True: spec requires Result False, this returns True. If "
                  "it verified => SPEC-TOO-WEAK (pk_set unpinned)."},
    {"id": "invert-conjunct", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "refinement": "uses `pk_explicit` instead of `not pk_explicit`, suppressing the short-cut "
                   "for a field-GENERATED pk and engaging it only for a caller-supplied one — the "
                   "mirror of the gold fix. Its faithful real patch `if raw and ...:` would "
                   "re-attempt an UPDATE on a genuinely-new UUID-default `create()` (the very "
                   "fast-path the original 3.0 commit added) instead of going straight to INSERT, "
                   "and would still mishandle the raw re-save; it would NOT resolve.",
     "rationale": "opposite-direction conjunct bug. Rejection source: clause 1. Witness "
                  "pk_explicit=False, force_insert=False, pk_set=True, adding=True, "
                  "pk_has_default=True (the genuinely-new UUID-default INSERT case): "
                  "shortcut_engaged is True so forces_insert is True and the spec requires Result "
                  "False (go straight to INSERT, no UPDATE), but this impl suppresses the "
                  "short-cut and returns update_matched_row(). If it verified => SPEC-TOO-WEAK "
                  "(the conjunct's polarity is unpinned)."},
    {"id": "drop-force-insert-factor", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_FORCE,
     "refinement": "gates the update path only on `not shortcut_engaged(...)`, ignoring the "
                   "caller's `force_insert`. Its faithful real patch would issue/report an UPDATE "
                   "on a `force_insert=True` save (where the caller demanded an INSERT and "
                   "`_do_update` is never consulted), violating the force_insert contract many "
                   "P2P saves depend on; it would NOT resolve.",
     "rationale": "partial-domain on the force_insert disjunct of forces_insert. Rejection "
                  "source: clause 1 — forces_insert = force_insert OR shortcut_engaged. Witness "
                  "force_insert=True, pk_set=True, pk_explicit=True (shortcut False), "
                  "update_matched_row()=True: forces_insert is True so the spec requires Result "
                  "False, but this impl (sc False) reaches the update path and returns True. If "
                  "it verified => SPEC-TOO-WEAK (the force_insert override is unpinned)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real Model._do_update) — the A-consumed soundness +
# caller-domain containment for `update_matched_row`.
# ===========================================================================
# The single axiom `update_matched_row()` is @Pure @ContractOnly with NO Ensures
# (the weakest contract): it merely names the bool the unchanged
# `Model._do_update` reports along the `if pk_set and not force_insert:` update
# path. The proof CONSUMES that bool as the returned `updated` value. Soundness =
# the real `_do_update` returns True iff a stored row matched the pk (True for a
# present row, False for absent), under the caller's actual runtime config (the
# default sqlite3 backend; a UUID-default pk — the twin of the test's
# UUIDDefaultData). Containment = the only callee-inputs the model can reach are
# present-pk and absent-pk observations, both inside _do_update's domain.
#
# These probes EXECUTE the real callee (never scrape source). The runner mounts
# ONLY the probe at /work, so axiom_check.py is NOT in-container; its source is
# read on the HOST at load time and embedded below, then driven directly.

# (1) axiom-soundness: reuse axiom_check.py's exact logic — configure in-memory
# sqlite + a UUID-default model and assert the REAL _do_update returns True for a
# present row and False for an absent one over 100 observations. apply_gold=True
# (the axiom describes the unchanged callee in the patched routine's context).
# The runner executes the probe as `python /work/<script>`, so axiom_check.py's
# own `if __name__ == "__main__": sys.exit(main())` block fires and propagates
# the exit code (0 iff sound). Embedded verbatim — read on the HOST at load time
# (the runner mounts only the probe at /work, so axiom_check.py is NOT in the
# container).
_AX_SOUND = _AXIOM_CHECK_SRC

# (2) axiom-containment: the model reaches `update_matched_row()` ONLY along the
# `if pk_set and not force_insert_eff:` path — i.e. only with an identifier
# present, asking the SAME present/absent question. Enumerate exactly those two
# reachable callee-inputs (a stored pk present; that same pk absent after delete)
# and confirm each is IN _do_update's domain (the call returns a clean bool, no
# raise). Covering more (any pk / any values) would be sound; the model reaches
# strictly these two. A reachable input outside the domain => AXIOM-TOO-WEAK.
_AX_CONTAINMENT = r'''
import os, sys, uuid

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("CONTAINMENT FAIL: Django could not be configured: %r" % (exc,))
        return 1

    from django.db import connection, models

    class UUIDDefault(models.Model):
        data = models.UUIDField(primary_key=True, default=uuid.uuid4)

        class Meta:
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(UUIDDefault)

    # The model reaches update_matched_row() only along `if pk_set and not
    # force_insert_eff:` — an identifier IS present, and _do_update is asked the
    # present/absent question. Enumerate exactly those two reachable callee-inputs
    # and confirm each is IN _do_update's domain (a clean bool, no raise).
    checked = 0
    for _ in range(25):
        obj = UUIDDefault.objects.create()      # pk present (the reachable input #1)
        pk = obj.pk
        assert pk is not None
        base_qs = UUIDDefault._base_manager.using("default")

        # reachable input #1: present pk -> in domain, returns a bool.
        r1 = obj._do_update(base_qs, "default", pk, [], None, False)
        assert isinstance(r1, bool), ("reachable present-pk input out of domain: %r" % (r1,))
        checked += 1

        # reachable input #2: same pk after delete (absent) -> in domain, bool.
        UUIDDefault.objects.filter(pk=pk).delete()
        r2 = obj._do_update(base_qs, "default", pk, [], None, False)
        assert isinstance(r2, bool), ("reachable absent-pk input out of domain: %r" % (r2,))
        checked += 1

    print("CONTAINMENT OK: every model-reachable update_matched_row() callee-input "
          "(present-pk and absent-pk along the update path) lies in Model._do_update's "
          "domain (clean bool, no raise) over %d observations; model-reachable subset of "
          "callee domain." % (checked,))
    return 0

sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-update-matched-row-sound", "axiom": "update_matched_row",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUND,
     "rationale": "the A-consumed axiom update_matched_row() must equal the REAL "
                  "Model._do_update: True for a present row, False for absent, under the caller's "
                  "actual config (default sqlite3 backend; UUID-default pk = twin of "
                  "UUIDDefaultData). Reuses axiom_check.py's exact 100-observation probe "
                  "(executing the real callee, never scraping source). Any mismatch => "
                  "AXIOM-UNSOUND."},
    {"id": "ax-update-matched-row-containment", "axiom": "update_matched_row",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "the model reaches update_matched_row() ONLY along the `if pk_set and not "
                  "force_insert_eff:` path — present-pk and (delete then) absent-pk observations, "
                  "both IN Model._do_update's domain (a clean bool, no raise). A reachable input "
                  "outside that domain => AXIOM-TOO-WEAK-FOR-CALLER; covering more is sound."},
]
