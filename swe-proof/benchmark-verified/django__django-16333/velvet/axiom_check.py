#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16333.

`Solution.lean` models the creation form's commit step as a state machine over
`FormState` and four deep-model state transformers (`prepareDeferred`,
`applyCredential`, `persistObject`, `persistRelated`).  Each transformer is an
**A-reference**: it stands for an UNCHANGED repository callee that the modeled
function calls but does not modify.  This check executes those REAL callees
against the real form/ORM machinery (in-container, on the repo at base_commit)
and asserts each one effects exactly the state-component change its deep model
claims — i.e. the `FormState` bijection of mapping.md is sound.

The four A-reference callees (mapping.md §3):

  * prepareDeferred  <-  `super().save(commit=False)` of the modeled `save`
        (the generic `BaseModelForm.save` non-commit branch): it builds the
        in-memory object WITHOUT persisting it and installs the deferred
        `save_m2m` capability.  Model effect: deferredSaveReady := True, and
        objectPersisted / relatedPersisted / credentialPending /
        credentialChanges untouched.
  * applyCredential  <-  `user.set_password(...)`: writes the secret credential
        onto the in-memory object and leaves its CHANGE OUTSTANDING for the
        object write to announce.  Model effect: passwordApplied := True,
        credentialPending := True, credentialChanges untouched.
  * persistObject    <-  `user.save()`: asks storage for the object write.  An
        ACCEPTED write stores the object AND announces an outstanding credential
        change, exactly one and only if one is outstanding, clearing it.  Model
        effect: objectPersisted := True, credentialChanges += credentialPending,
        credentialPending := False (related data still absent).  A DECLINED write
        stores nothing, announces nothing and leaves the change outstanding:
        stepRefused := True and every other component untouched.
  * persistRelated   <-  `self.save_m2m()`: asks storage for the related
        collection-valued write, using the deferred capability.  An ACCEPTED
        write sets relatedPersisted := True (announcing nothing, clearing
        nothing).  It DECLINES when the capability was never prepared, when the
        object is not yet stored, or when storage refuses the related rows:
        stepRefused := True.

Both persistence writes are DATABASE writes, and a database enforces integrity
rules the form's own validation does not see, so a write on data the form
accepted can still be declined.  That is why `FormState` carries the two
read-only acceptance components `objectWriteAccepted` / `relatedWriteAccepted`,
and why this check runs its trajectories over FOUR model configurations, not
one: a configuration where storage takes both writes, one where it declines the
related write (a user-defined m2m `through` model with a required extra column
the form does not supply), one where it declines the object write (a required
column on the user model that the form does not expose), and one where the
related field is not on the form at all, so `_save_m2m` walks its per-attribute
table and finds nothing to write.  Restricting the check to the accepting
configuration would validate the acceptance components vacuously.

Rather than assert one component per callee, the check carries a Python MIRROR
of the Lean `FormState` transformers alongside the real objects and, after every
real call, asserts that ALL TEN modeled components agree with what the real
form / object / notification stream shows.  That makes the multiplicity of the
credential-change announcement — the component the model counts rather than
latches — a checked observation rather than an assumption: a trajectory that
consumes two outstanding credentials really does announce twice, and one that
persists twice on a single credential really does announce once.

It also confirms the load-bearing guard the impl relies on: after the
non-commit `super().save`, the form really does carry a `save_m2m` attribute.

Stdlib + Django (the repo under test) only — no third-party deps.  Exit 0 iff
every observation matches the model.  Boundary configurations (single / pair /
all related rows, entered with and without an outstanding credential, plus the
two multiplicity trajectories and the declined-write trajectories) followed by
randomized fuzz.
"""
import os
import random
import sys
from unittest import mock

SEED = 16333
N_FUZZ = 500

# The credential-change announcement is made through this module-level callee,
# so this is the name whose call count IS `FormState.credentialChanges`.
NOTIFY = "django.contrib.auth.password_validation.password_changed"

RAW = "testclient"


class Config:
    """One model/form configuration, together with what storage will accept.

    `objectWriteAccepted` / `relatedWriteAccepted` are facts about the schema,
    not about the step: they are fixed by the model definition (which columns
    are required and which of them the form supplies), so they are read off the
    configuration and are exactly the two read-only `FormState` components.
    """

    def __init__(self, label, form_cls, rel_attr, obj_ok, rel_ok, note):
        self.label = label
        self.form_cls = form_cls
        self.rel_attr = rel_attr        # name of the related field, or None
        self.obj_ok = obj_ok
        self.rel_ok = rel_ok
        self.note = note


def _bootstrap():
    """Configure a minimal Django project around the repo's own auth_tests
    models, build the schema for the touched models, and return the handles the
    checks need.  Mirrors how the F2P test stands the model up.

    Three extra models are declared here under the `auth_tests` app label (an
    already-installed app with a real filesystem location, so the app registry
    accepts them) to reach the DECLINED-write branches: the repo's own
    `CustomUserWithM2M` uses an AUTO-created through table whose only columns are
    the two foreign keys, so storage accepts every related write it is asked for
    and the declined arms would never be exercised.
    """
    # Make the repo's tests/ importable so we reuse the SAME custom m2m user
    # model the hidden F2P test uses (auth_tests.models.with_many_to_many).
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (
        os.path.join(os.getcwd(), "tests"),
        "/testbed/tests",
        os.path.join(here, "tests"),
    ):
        if os.path.isdir(os.path.join(cand, "auth_tests")):
            sys.path.insert(0, cand)
            break

    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "auth_tests",
            ],
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        )
    django.setup()

    from django.db import connection, models
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.contrib.auth.forms import UserCreationForm
    from auth_tests.models.with_many_to_many import (
        CustomUserWithM2M, Organization)

    # ---- configuration 2: storage DECLINES the related write. The through
    # ---- model carries a required column the form has no way to supply, so
    # ---- `Field._get_default` yields None for it (no default,
    # ---- empty_strings_allowed=False) and the through-row insert violates the
    # ---- column's NOT NULL constraint.
    class UserRelDeclined(AbstractBaseUser):
        username = models.CharField(max_length=100, unique=True)
        orgs = models.ManyToManyField(
            Organization, through="auth_tests.RelDeclinedMembership")
        USERNAME_FIELD = "username"

        class Meta:
            app_label = "auth_tests"

    class RelDeclinedMembership(models.Model):
        user = models.ForeignKey(UserRelDeclined, on_delete=models.CASCADE)
        organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
        rank = models.IntegerField()          # required, no default

        class Meta:
            app_label = "auth_tests"

    # ---- configuration 3: storage DECLINES the object write. A required column
    # ---- on the user model itself that the form does not expose.
    class UserObjDeclined(AbstractBaseUser):
        username = models.CharField(max_length=100, unique=True)
        tier = models.IntegerField()          # required, not a form field
        orgs = models.ManyToManyField(Organization)
        USERNAME_FIELD = "username"

        class Meta:
            app_label = "auth_tests"

    with connection.schema_editor() as se:
        se.create_model(Organization)
        se.create_model(CustomUserWithM2M)
        se.create_model(UserRelDeclined)
        # create_model already builds every AUTO-created m2m through table, so
        # only the explicit `through=` model remains.
        se.create_model(RelDeclinedMembership)
        se.create_model(UserObjDeclined)

    def form_for(model, fields):
        return type("F_%s" % model.__name__, (UserCreationForm,),
                    {"Meta": type("Meta", (UserCreationForm.Meta,),
                                  {"model": model, "fields": fields})})

    base = UserCreationForm.Meta.fields
    configs = [
        Config("accept-both",
               form_for(CustomUserWithM2M, base + ("orgs",)), "orgs",
               True, True,
               "auto-created through table: storage takes both writes"),
        Config("decline-related",
               form_for(UserRelDeclined, base + ("orgs",)), "orgs",
               True, False,
               "user-defined through model with a required extra column: "
               "storage takes the object and DECLINES its related rows"),
        Config("decline-object",
               form_for(UserObjDeclined, base + ("orgs",)), "orgs",
               False, True,
               "required column the form does not supply: storage DECLINES the "
               "object write, so the related write is never reached"),
        Config("no-related-field",
               form_for(CustomUserWithM2M, base), None,
               True, True,
               "the model has an m2m the FORM does not expose: _save_m2m walks "
               "its per-attribute table and writes nothing, so there is no "
               "related write for storage to decline"),
    ]
    return configs, Organization


def _valid_form(cfg, orgs, idx):
    data = {
        "username": "user%d@example.com" % idx,
        "password1": RAW,
        "password2": RAW,
    }
    if cfg.rel_attr is not None:
        data[cfg.rel_attr] = [str(o.pk) for o in orgs]
    f = cfg.form_cls(data)
    assert f.is_valid(), ("form should validate, got %r" % f.errors)
    return f


# --------------------------------------------------------------------------
# Python mirror of the Lean `FormState` and of the four deep models, verbatim
# from Solution.lean's `pure` region.  Only used as the PREDICTION that the real
# callees are then asserted against.
# --------------------------------------------------------------------------
class Model:
    __slots__ = ("dataValidated", "passwordApplied", "objectPersisted",
                 "relatedPersisted", "deferredSaveReady", "credentialPending",
                 "credentialChanges", "objectWriteAccepted",
                 "relatedWriteAccepted", "stepRefused")

    def __init__(self, **kw):
        for s in self.__slots__:
            setattr(self, s, kw[s])

    def copy(self, **kw):
        d = {s: getattr(self, s) for s in self.__slots__}
        d.update(kw)
        return Model(**d)

    def __repr__(self):
        return "{%s}" % ", ".join("%s=%r" % (s, getattr(self, s))
                                  for s in self.__slots__)


def m_prepareDeferred(s):
    if s.stepRefused:
        return s
    if s.dataValidated:
        return s.copy(deferredSaveReady=True)
    return s.copy(stepRefused=True)


def m_applyCredential(s):
    if s.stepRefused:
        return s
    return s.copy(passwordApplied=True, credentialPending=True)


def m_persistObject(s):
    if s.stepRefused:
        return s
    if s.objectWriteAccepted:
        return s.copy(objectPersisted=True, credentialPending=False,
                      credentialChanges=s.credentialChanges
                      + (1 if s.credentialPending else 0))
    return s.copy(stepRefused=True)


def m_persistRelated(s):
    if s.stepRefused:
        return s
    if s.deferredSaveReady and s.objectPersisted and s.relatedWriteAccepted:
        return s.copy(relatedPersisted=True)
    return s.copy(stepRefused=True)


def observe(cfg, form, user, orgs, notify, dataValidated=True,
            stepRefused=False):
    """Read the ten modeled components off the REAL objects.

    The bijection of mapping.md §2, component by component:
      passwordApplied      <- user.check_password(RAW)
      objectPersisted      <- user.pk is not None
      relatedPersisted     <- the stored related rows equal the selection
      deferredSaveReady    <- hasattr(form, "save_m2m")
      credentialPending    <- user._password is not None (a credential has been
                              written whose change has not been announced yet)
      credentialChanges    <- how many times the announcement callee has been
                              called on this trajectory
      objectWriteAccepted  <- whether this schema lets storage take the object
      relatedWriteAccepted <- whether this schema lets storage take the related
                              rows
    Both acceptance components are read off the CONFIGURATION, because they are
    facts about the state the step is asked in and no step writes them; the
    mut-frame clauses of the contract are exactly this claim, and every `agree`
    call below re-checks it against the configuration's fixed value.

    `relatedPersisted` is "every related field the FORM exposes holds exactly
    the selection".  When the form exposes none, that conjunction is VACUOUSLY
    true and stays true throughout — which is the right reading: `_save_m2m`
    consults its per-attribute table, finds nothing admitted, and there is no
    related write either to make or to decline.  Keying it to the object write
    instead would make the object write appear to store related data, which it
    does not (measured: that spelling fails this check).
    """
    if cfg.rel_attr is None:
        persisted = True
    elif user.pk:
        rel = getattr(user, cfg.rel_attr)
        persisted = (sorted(o.pk for o in rel.all())
                     == sorted(o.pk for o in orgs))
    else:
        persisted = False
    return Model(dataValidated=dataValidated,
                 passwordApplied=user.check_password(RAW),
                 objectPersisted=user.pk is not None,
                 relatedPersisted=persisted,
                 deferredSaveReady=hasattr(form, "save_m2m"),
                 credentialPending=user._password is not None,
                 credentialChanges=notify.call_count,
                 objectWriteAccepted=cfg.obj_ok,
                 relatedWriteAccepted=cfg.rel_ok,
                 stepRefused=stepRefused)


def agree(step, predicted, actual):
    for s in Model.__slots__:
        p, a = getattr(predicted, s), getattr(actual, s)
        assert p == a, (
            "%s unsound: deep model predicts %s=%r but the real callee leaves "
            "%s=%r\n  model : %r\n  actual: %r" % (step, s, p, s, a, predicted,
                                                   actual))


def run_trajectory(cfg, orgs, idx, steps, prelatched=False):
    """Drive one sequence of REAL callees, asserting after every step that all
    ten modeled components match the deep model's prediction.

    `steps` is the call sequence, so this checks the transformers where they are
    actually used: in composition, over a state the previous callee left.
    `prelatched` enters the step with a credential already written and its
    change not yet announced — the state the second of two consecutive form
    saves is entered in, and the state at which the announcement's MULTIPLICITY
    becomes discriminating.

    Each real call runs inside its own `atomic` block, so a write storage
    DECLINES rolls back exactly that write and leaves the trajectory's earlier
    accepted writes standing — which is what the model claims a declined step
    does.  A declined step ends the trajectory, exactly as the modeled function
    ends on the error rather than continuing.
    """
    from django.db import transaction
    f = _valid_form(cfg, orgs, idx)
    with mock.patch(NOTIFY) as notify:
        user = super(cfg.form_cls, f).save(commit=False)
        if prelatched:
            user.set_password(RAW)
            assert user._password is not None, (
                "pre-latch setup: set_password must leave the credential "
                "change outstanding")
            assert notify.call_count == 0, (
                "pre-latch setup: writing a credential must announce nothing")
        # Entry state: whatever the real objects show right now.  `deferredSave
        # Ready` is already True here (super().save(commit=False) ran), which is
        # the guard the impl tests; the trajectory below re-runs prepareDeferred
        # the way the modeled function does, so its idempotence is checked too.
        state = observe(cfg, f, user, orgs, notify)
        assert state.deferredSaveReady, (
            "prepareDeferred unsound: the deferred save_m2m capability "
            "(deferredSaveReady) must be prepared by super().save(commit=False) "
            "— this is exactly the hasattr(self,'save_m2m') guard the impl "
            "relies on")
        assert not state.objectPersisted, (
            "prepareDeferred unsound: super().save(commit=False) must NOT "
            "persist the object (objectPersisted stays False)")
        for step in steps:
            declined = False
            err = None
            try:
                with transaction.atomic():
                    if step == "prepareDeferred":
                        super(cfg.form_cls, f).save(commit=False)
                    elif step == "applyCredential":
                        user.set_password(RAW)
                    elif step == "persistObject":
                        user.save()
                    elif step == "persistRelated":
                        f.save_m2m()
                    else:                              # pragma: no cover
                        raise AssertionError("unknown step %r" % step)
            except AssertionError:
                raise
            except Exception as exc:
                declined = True
                err = "%s: %s" % (type(exc).__name__, exc)
            if step == "prepareDeferred":
                state = m_prepareDeferred(state)
            elif step == "applyCredential":
                state = m_applyCredential(state)
            elif step == "persistObject":
                state = m_persistObject(state)
            else:
                state = m_persistRelated(state)
            assert state.stepRefused == declined, (
                "%s unsound: deep model predicts stepRefused=%r but the real "
                "callee %s (%s)\n  config: %s\n  model : %r"
                % (step, state.stepRefused,
                   "was DECLINED" if declined else "ran to completion",
                   err or "no error", cfg.label, state))
            agree(step, state, observe(cfg, f, user, orgs, notify,
                                       stepRefused=declined))
            if declined:
                return state
        return state


GOLD_STEPS = ["prepareDeferred", "applyCredential", "persistObject",
              "persistRelated"]
# Two credentials written, two object writes: the announcement is made TWICE.
# This is what makes credentialChanges a COUNT rather than a latch — if the real
# callee announced at most once per trajectory, a Bool would model it.
TWICE_STEPS = ["prepareDeferred", "applyCredential", "persistObject",
               "persistRelated", "applyCredential", "persistObject"]
# One credential, two object writes: the announcement is made ONCE, because the
# second write finds nothing outstanding.
ONCE_STEPS = ["prepareDeferred", "applyCredential", "persistObject",
              "persistObject", "persistRelated"]
# The related write asked for BEFORE the object exists: storage attaches related
# data only to an object it has already stored, so it is declined.
EARLY_REL_STEPS = ["prepareDeferred", "applyCredential", "persistRelated"]


def main():
    configs, Organization = _bootstrap()
    rng = random.Random(SEED)
    accept = configs[0]

    # a pool of organizations to draw from
    pool = [Organization.objects.create(name="org %d" % i) for i in range(8)]

    idx = 0
    checked = 0
    # --- boundary configurations -----------------------------------------
    # (the m2m field is required, so every valid form selects >= 1 org)
    boundary = [
        [pool[0]],          # single related row
        pool[:2],           # a couple
        pool[:],            # all of them
    ]
    for orgs in boundary:
        for prelatched in (False, True):
            st = run_trajectory(accept, orgs, idx, GOLD_STEPS,
                                prelatched=prelatched)
            assert st.credentialChanges == 1 and not st.credentialPending, (
                "the committing sequence must announce the credential change "
                "exactly once and leave none outstanding, got %r" % (st,))
            assert not st.stepRefused and st.relatedPersisted, (
                "with both writes accepted the committing sequence must run to "
                "completion and store the related data, got %r" % (st,))
            idx += 1
            checked += 1
    # --- announcement multiplicity ---------------------------------------
    for prelatched in (False, True):
        st = run_trajectory(accept, [pool[0]], idx, TWICE_STEPS,
                            prelatched=prelatched)
        assert st.credentialChanges == 2, (
            "two written credentials followed by two object writes must "
            "announce twice, got %r" % (st,))
        idx += 1
        checked += 1
        st = run_trajectory(accept, [pool[0]], idx, ONCE_STEPS,
                            prelatched=prelatched)
        assert st.credentialChanges == 1, (
            "one written credential followed by two object writes must "
            "announce once, got %r" % (st,))
        idx += 1
        checked += 1
    # --- a non-committing step announces nothing and leaves the credential
    # --- change outstanding ----------------------------------------------
    for prelatched in (False, True):
        st = run_trajectory(accept, [pool[0]], idx,
                            ["prepareDeferred", "applyCredential"],
                            prelatched=prelatched)
        assert st.credentialChanges == 0 and st.credentialPending, (
            "a step that writes the credential without an object write must "
            "announce nothing and leave the change outstanding, got %r" % (st,))
        idx += 1
        checked += 1

    # --- DECLINED writes -------------------------------------------------
    # (a) storage declines the RELATED write: the object stays stored and its
    #     announcement stands, but no related data is written and the step ends
    #     in an error.  This is the branch the acceptance components exist for.
    rel_declined = configs[1]
    for orgs in ([pool[0]], pool[:3]):
        for prelatched in (False, True):
            st = run_trajectory(rel_declined, orgs, idx, GOLD_STEPS,
                                prelatched=prelatched)
            assert st.stepRefused, (
                "a related write storage declines must end the step in an "
                "error, got %r" % (st,))
            assert st.objectPersisted and not st.relatedPersisted, (
                "the declined related write must leave the object stored and "
                "no related data written, got %r" % (st,))
            assert st.credentialChanges == 1 and not st.credentialPending, (
                "the accepted object write's announcement stands even though "
                "the later related write was declined, got %r" % (st,))
            idx += 1
            checked += 1
    # (b) storage declines the OBJECT write: nothing at all is stored, nothing
    #     is announced, and the credential's change stays outstanding — the
    #     announcement is sequenced after the write returns.
    obj_declined = configs[2]
    for orgs in ([pool[0]], pool[:3]):
        for prelatched in (False, True):
            st = run_trajectory(obj_declined, orgs, idx, GOLD_STEPS,
                                prelatched=prelatched)
            assert st.stepRefused, (
                "an object write storage declines must end the step in an "
                "error, got %r" % (st,))
            assert not st.objectPersisted and not st.relatedPersisted, (
                "the declined object write must store nothing, got %r" % (st,))
            assert st.credentialChanges == 0 and st.credentialPending, (
                "a declined object write must announce nothing and leave the "
                "credential's change outstanding, got %r" % (st,))
            idx += 1
            checked += 1
    # (c) the related write asked for before the object is stored: declined, on
    #     a configuration where storage would otherwise accept it.
    for prelatched in (False, True):
        st = run_trajectory(accept, [pool[0]], idx, EARLY_REL_STEPS,
                            prelatched=prelatched)
        assert st.stepRefused and not st.relatedPersisted, (
            "storage attaches related data only to an object it has already "
            "stored, so this must be declined, got %r" % (st,))
        idx += 1
        checked += 1
    # (d) the form does not expose the related field: `_save_m2m` consults its
    #     per-attribute table, finds nothing admitted, and writes nothing — so
    #     there is no related write for storage to decline and the step runs to
    #     completion.
    no_rel = configs[3]
    for prelatched in (False, True):
        st = run_trajectory(no_rel, [pool[0]], idx, GOLD_STEPS,
                            prelatched=prelatched)
        assert not st.stepRefused, (
            "a related write the form never asks for cannot be declined, got "
            "%r" % (st,))
        assert st.objectPersisted and st.credentialChanges == 1, (
            "the object write is still accepted and still announces once, got "
            "%r" % (st,))
        idx += 1
        checked += 1

    # --- randomized fuzz over the related-data selection and over which
    # --- writes storage accepts -------------------------------------------
    for _ in range(N_FUZZ):
        cfg = rng.choice(configs)
        k = rng.randint(1, len(pool))
        orgs = rng.sample(pool, k)
        pool_steps = [GOLD_STEPS, TWICE_STEPS, ONCE_STEPS]
        # EARLY_REL_STEPS asks for the related write before the object exists.
        # That is not a trajectory the modeled function can take (it persists the
        # object first), and on a form exposing no related field there is no
        # write to be refused, so the leg is only meaningful where the form
        # actually asks for one.
        if cfg.rel_attr is not None:
            pool_steps.append(EARLY_REL_STEPS)
        steps = rng.choice(pool_steps)
        run_trajectory(cfg, orgs, idx, steps, prelatched=rng.random() < 0.5)
        idx += 1
        checked += 1

    print("G-AX OK: 4 A-reference callees (prepareDeferred=super().save(False), "
          "applyCredential=set_password, persistObject=user.save, "
          "persistRelated=save_m2m) match their FormState deep models on all 10 "
          "components after every step of %d trajectories (%d boundary + %d "
          "fuzz), entered both with and without an outstanding credential "
          "change, over %d model configurations (%s); the announcement count is "
          "observed to rise once per written credential that an ACCEPTED object "
          "write follows, twice for two, and not at all for an object write "
          "that follows none or that storage declines; a declined write is "
          "observed to write nothing and to leave the credential's change "
          "outstanding, while an earlier accepted write stands; and the "
          "hasattr(save_m2m) guard holds after the non-commit save. (the m2m "
          "field is required wherever the form exposes it, so every such "
          "trajectory selects >= 1 related row.)"
          % (checked, checked - N_FUZZ, N_FUZZ, len(configs),
             ", ".join(c.label for c in configs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
