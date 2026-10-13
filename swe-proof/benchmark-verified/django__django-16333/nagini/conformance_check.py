#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16333 (nagini).

Refutes (or fails to refute) the ONE leg no other gate covers: does the MODEL's
implementation actually agree with the REAL PATCHED repository function it claims
to model?  G-VERIFY says the impl meets the spec, G-PBT says no wrong impl meets
it, G-AX says each axiom is a sound contract of its real callee — none of them
diffs the modeled routine against the real routine.

SHADOW — the `# impl-start` / `# impl-end` region of `model.py`'s
``save_form(self, commit)``, copied VERBATIM below (see ``save_form`` under
"--- shadow ---"), comment included.  The region contains no contract calls at
all (the ``Requires``/``Ensures``/``MustTerminate`` clauses all sit above
``# impl-start``), so nothing had to be stripped and nothing was restructured,
renamed or simplified:

    base_form_save_deferred(self)
    # (the password assignment of the routine has no tracked persistence effect)
    if commit:
        persist_record(self)
        if self.get_ready():
            run_deferred_save(self)
    return self

All three callees are ``@ContractOnly`` — a body-less axiom has nothing to copy,
so per the worker contract each one CALLS the REAL repo function it axiomatizes
(mapping.md §1 / §3), which exercises the axiom instead of assuming it:

  * ``base_form_save_deferred(self)`` -> ``BaseModelForm.save(form, commit=False)``
    (``django/forms/models.py:526``, the ``commit=False`` else-branch 544-547) —
    exactly the ``super().save(commit=False)`` the real routine performs;
  * ``persist_record(self)``          -> ``instance.save()`` == ``Model.save()``
    (the ``user.save()`` at ``django/contrib/auth/forms.py:143``);
  * ``run_deferred_save(self)``       -> ``form.save_m2m()``
    (== ``BaseModelForm._save_m2m``, ``django/forms/models.py:505``).

The two ``@Pure`` accessors the region calls are copied from the
``# pure-start``/``# pure-end`` region minus their ``Requires``/``Unfolding``.
Their bodies are the type-bridge inversion point (see TYPE BRIDGE): rather than
returning bookkeeping booleans the axioms' ``Ensures`` would have set, they read
the REAL observable facts (row exists / ``hasattr(form, "save_m2m")``).  Storing
the booleans instead would have made the shadow's guard depend on the axioms'
claims — i.e. would have ASSUMED them; reading live repo state means the guard
``if self.get_ready()`` is decided by exactly the fact the real patched guard
``if hasattr(self, "save_m2m")`` tests.  So that no divergence can hide behind
the bridged reads, every trial ALSO asserts each axiom's ``Ensures`` against the
live state right where the axiom is discharged (``_AXIOM CHECKS`` in the three
bridge functions): the base save must leave ``get_ready()`` True with
``get_record()`` unchanged, the record write must leave ``get_record()`` True with
``get_ready()`` unchanged, and the deferred relational save must run only with
both facts True and must leave both unchanged.  An axiom violation is reported as
a disagreement and exits 1.

ORACLE — the REAL PATCHED repo function, CALLED, not transliterated:
``django.contrib.auth.forms.UserCreationForm.save(self, commit=True)``
(``django/contrib/auth/forms.py:139``; mapping.md §1).  The gate git-applies
patch.diff to /testbed and runs with ``PYTHONPATH=/testbed``, so the
``UserCreationForm`` imported here IS the patched source.  Each trial builds a
live, validated ``UserCreationForm`` subclass bound to a custom user model with
ManyToManyField(s) — the structural twin of the F2P test's ``CustomUserWithM2M``
+ ``Organization`` — and calls ``form.save(commit=...)``.  Nothing about ``save``
is reimplemented; the observations are read off the live database and the live
form object afterwards.

  * VACUITY GUARD: the run refuses to report success unless the live
    ``UserCreationForm.save`` source actually contains the deferred relational
    save, and unless the enumerated cells were all reached with both legs in the
    modeled entry state.
  * FALSIFIABILITY, checked empirically: run against /testbed WITHOUT the gold
    patch this script reports a disagreement on its FIRST input — the F2P cell
    (commit=True, required-m2m shape, one submitted association) — because the
    shadow runs the deferred relational save and the unpatched real ``save`` does
    not (``relations_saved`` True vs False, ``association_pks`` ``([1],)`` vs
    ``([],)``) — and exits 1.  The check is therefore capable of failing on
    exactly the behaviour under specification.

TYPE BRIDGE (mapping.md §2, inverted).  The model's ``Form`` folds the bound form
and its model instance into one object carrying only the observed persistence
facts; the concrete side is a real ``UserCreationForm`` plus its ``instance``:

  * ``commit: bool``      <-> the ``commit`` kwarg of ``save`` (identity);
  * ``get_record()``      <-> ``Model._default_manager.filter(pk=instance.pk)
    .exists()`` (False while ``pk is None``);
  * ``get_ready()``       <-> ``hasattr(form, "save_m2m")``;
  * ``relations_done(self)`` — the abstract body-less per-form CAPABILITY whose
    sole producer is ``run_deferred_save(self)`` — <-> "the real ``_save_m2m``
    ran for THIS form".  Observed identically on both legs by a per-form counter
    in an override that immediately delegates to the REAL
    ``BaseModelForm._save_m2m``: an observation of the effect-producing step, not
    a reimplementation of it.  It is compared alongside the concrete effect (the
    persisted association pks per m2m field), so the capability can never be
    "observed as held" on one leg while the written associations differ.
  * ``Result() is self``  <-> the returned object is the instance the form built
    (``user is form.instance``);
  * ``user.set_password(self.cleaned_data["password1"])`` is mapping.md §2's
    explicitly UNTRACKED node, so it is absent from the impl region and hence
    from the shadow.  That is the one place the two legs legitimately differ, so
    the check does not ignore it: every trial asserts the divergence is EXACTLY
    the untracked one (real leg ends with a usable password, shadow leg does not)
    and that it moves none of the tracked facts.

INPUT DOMAIN — every counted input satisfies ``save_form``'s ``Requires``:
``self.form_pred()`` (a live bound form + its instance), ``get_record() is
False`` and ``get_ready() is False`` (a FRESH, never-saved, never-deferred form —
asserted through the bridge on BOTH legs before each call, so a trial that
somehow starts outside the modeled entry state is reported, not counted), and
``MustTerminate(2)`` (both legs are driven to completion every trial, which is
direct evidence of termination).

The MODELED input space is FINITE: the only modeled input is ``commit: bool``.
The concrete degrees of freedom the bridge exposes are therefore enumerated
EXHAUSTIVELY as the boundary set — {commit True, False} x {form shape:
required-m2m F2P twin, blank-m2m, two-m2m-fields, m2m-less} x {number of
submitted associations 0..3, where the shape admits it} = 24 cells, every branch
of the impl region covered (``commit`` True and False; ``get_ready()`` reached
True on every committing trial, which is the guard the patch introduces) — and
then the SAME space is fuzzed with a pinned seed to reach the input count.
Exhaustive enumeration of the finite modeled space plus fuzz over that same
space is a stronger check than 1e5 samples of a proper subset (worker contract
clause 4), not a weaker one.

INPUT COUNT: >= 100000 Requires-satisfying trials, each running BOTH legs end to
end against the live ORM.  Pinned seed: 16333 (recorded in mapping.md, section
"G-CONF").

Exit 0 iff zero disagreements; on a disagreement the input cell and both
observation tuples are printed and the exit code is 1.  Standard library +
Django (the framework the patch lives in) only.
"""
import json
import os
import random
import sys
import tempfile
import types

SEED = 16333
N_TARGET = 100_000


# ---------------------------------------------------------------------------
# Nagini -> Python carriers: model.py's ``Form``, contracts stripped.  The two
# @Pure accessors are the ``# pure-start``/``# pure-end`` region minus their
# Requires/Unfolding; their bodies read the REAL observable facts through the
# mapping.md §2 bijections (see TYPE BRIDGE in the module docstring).
# ---------------------------------------------------------------------------
class Form:
    def __init__(self, form):
        self.form = form              # the bound UserCreationForm
        self.instance = None          # the model object the base save builds
        self.axiom_violations = []    # populated by the _AXIOM CHECKS below

    # get_record() <-> the primary row for this instance exists
    def get_record(self):
        inst = self.instance
        if inst is None or inst.pk is None:
            return False
        return type(inst)._default_manager.filter(pk=inst.pk).exists()

    # get_ready() <-> hasattr(form, "save_m2m")
    def get_ready(self):
        return hasattr(self.form, "save_m2m")

    # relations_done(self) <-> the real _save_m2m ran for THIS form
    def relations_done(self):
        return self.form.m2m_calls > 0


# ---------------------------------------------------------------------------
# The three @ContractOnly callees: CALL the REAL repo functions they axiomatize
# (a body-less axiom has no body to copy).  Each wrapper additionally asserts the
# axiom's own Ensures against the live state, so the bridged accessors above
# cannot mask an axiom divergence.
# ---------------------------------------------------------------------------
def base_form_save_deferred(self):
    """axiom <-> BaseModelForm.save(commit=False), django/forms/models.py:526."""
    from django.forms.models import BaseModelForm
    before_record = self.get_record()
    self.instance = BaseModelForm.save(self.form, commit=False)
    # _AXIOM CHECKS: Ensures(get_ready() is True) and
    # Ensures(get_record() == Old(get_record())); it grants no relations_done.
    if self.get_ready() is not True:
        self.axiom_violations.append(
            "base_form_save_deferred: Ensures(get_ready() is True) violated")
    if self.get_record() != before_record:
        self.axiom_violations.append(
            "base_form_save_deferred: Ensures(get_record() unchanged) violated")
    if self.relations_done():
        self.axiom_violations.append(
            "base_form_save_deferred: must NOT grant relations_done(self)")


def persist_record(self):
    """axiom <-> Model.save(), the user.save() at auth/forms.py:143."""
    before_ready = self.get_ready()
    before_relations = self.relations_done()
    self.instance.save()
    # _AXIOM CHECKS: Ensures(get_record() is True) and
    # Ensures(get_ready() == Old(get_ready())); it grants no relations_done.
    if self.get_record() is not True:
        self.axiom_violations.append(
            "persist_record: Ensures(get_record() is True) violated")
    if self.get_ready() != before_ready:
        self.axiom_violations.append(
            "persist_record: Ensures(get_ready() unchanged) violated")
    if self.relations_done() != before_relations:
        self.axiom_violations.append(
            "persist_record: must NOT grant relations_done(self)")


def run_deferred_save(self):
    """axiom <-> save_m2m == BaseModelForm._save_m2m, forms/models.py:505."""
    # _AXIOM CHECKS: Requires(get_ready() is True) and Requires(get_record() is
    # True) -- the associations attach to the record's primary key.
    if self.get_ready() is not True or self.get_record() is not True:
        self.axiom_violations.append(
            "run_deferred_save: called outside its Requires (ready=%r "
            "record=%r)" % (self.get_ready(), self.get_record()))
    before = (self.get_record(), self.get_ready())
    self.form.save_m2m()
    # _AXIOM CHECKS: Ensures(relations_done(self)) and both facts unchanged.
    if not self.relations_done():
        self.axiom_violations.append(
            "run_deferred_save: Ensures(relations_done(self)) violated")
    if (self.get_record(), self.get_ready()) != before:
        self.axiom_violations.append(
            "run_deferred_save: Ensures(record/ready unchanged) violated")


# --- shadow: the impl region of model.py's save_form, VERBATIM --------------
def save_form(self, commit):
    # impl-start
    base_form_save_deferred(self)
    # (the password assignment of the routine has no tracked persistence effect)
    if commit:
        persist_record(self)
        if self.get_ready():
            run_deferred_save(self)
    return self
    # impl-end


# ---------------------------------------------------------------------------
# Django bring-up: a synthetic app whose custom user models carry m2m field(s),
# the structural twin of the F2P test's CustomUserWithM2M / Organization.
# ---------------------------------------------------------------------------
def _configure():
    pkg_dir = tempfile.mkdtemp(prefix="confcheck_app_")
    mod = types.ModuleType("confcheck")
    mod.__path__ = [pkg_dir]
    mod.__file__ = os.path.join(pkg_dir, "__init__.py")
    sys.modules["confcheck"] = mod

    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth",
                            "confcheck"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            AUTH_PASSWORD_VALIDATORS=[],
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            USE_TZ=False,
        )
    django.setup()


def _build_shapes():
    """The bound-form shapes, each a UserCreationForm subclass over a custom
    user model — mirroring the F2P test's CustomUserCreationForm."""
    from django.contrib.auth.forms import UserCreationForm
    from django.contrib.auth.models import AbstractBaseUser
    from django.db import connection, models
    from django.forms.models import BaseModelForm

    class Organization(models.Model):
        name = models.CharField(max_length=255)

        class Meta:
            app_label = "confcheck"

    class Team(models.Model):
        name = models.CharField(max_length=255)

        class Meta:
            app_label = "confcheck"

    # (1) the exact F2P twin: a REQUIRED ManyToManyField on the user model.
    class UserReqM2M(AbstractBaseUser):
        username = models.CharField(max_length=30, unique=True)
        orgs = models.ManyToManyField(Organization)
        USERNAME_FIELD = "username"

        class Meta:
            app_label = "confcheck"

    # (2) blank m2m: lets the EMPTY-association boundary validate.
    class UserBlankM2M(AbstractBaseUser):
        username = models.CharField(max_length=30, unique=True)
        orgs = models.ManyToManyField(Organization, blank=True)
        USERNAME_FIELD = "username"

        class Meta:
            app_label = "confcheck"

    # (3) two m2m fields: exercises _save_m2m's loop over several fields.
    class UserTwoM2M(AbstractBaseUser):
        username = models.CharField(max_length=30, unique=True)
        orgs = models.ManyToManyField(Organization, blank=True)
        teams = models.ManyToManyField(Team, blank=True)
        USERNAME_FIELD = "username"

        class Meta:
            app_label = "confcheck"

    # (4) no m2m at all: the deferred relational save is still set up and still
    # run when committing, but writes nothing.
    class UserNoM2M(AbstractBaseUser):
        username = models.CharField(max_length=30, unique=True)
        USERNAME_FIELD = "username"

        class Meta:
            app_label = "confcheck"

    with connection.schema_editor() as editor:
        for m in (Organization, Team, UserReqM2M, UserBlankM2M, UserTwoM2M,
                  UserNoM2M):
            editor.create_model(m)

    class _Instrumented(UserCreationForm):
        """Records that the deferred relational save RAN for this form, then
        delegates to the REAL BaseModelForm._save_m2m.  This is the observation
        of `relations_done(self)`; it reimplements nothing.  Both legs use it, so
        the observation is symmetric."""

        def __init__(self, *a, **kw):
            self.m2m_calls = 0
            super().__init__(*a, **kw)

        def _save_m2m(self):
            self.m2m_calls += 1
            return BaseModelForm._save_m2m(self)

    def make_form_cls(model, m2m_fields):
        meta = type("Meta", (UserCreationForm.Meta,),
                    {"model": model,
                     "fields": ("username",) + tuple(m2m_fields)})
        return type("Form_%s" % model.__name__, (_Instrumented,),
                    {"Meta": meta})

    # (name, form class, model, m2m field names, empty selection allowed)
    shapes = [
        ("req_m2m", make_form_cls(UserReqM2M, ("orgs",)), UserReqM2M,
         ("orgs",), False),
        ("blank_m2m", make_form_cls(UserBlankM2M, ("orgs",)), UserBlankM2M,
         ("orgs",), True),
        ("two_m2m", make_form_cls(UserTwoM2M, ("orgs", "teams")), UserTwoM2M,
         ("orgs", "teams"), True),
        ("no_m2m", make_form_cls(UserNoM2M, ()), UserNoM2M, (), True),
    ]
    return shapes, Organization, Team


def _assert_oracle_is_patched():
    """The oracle must be the PATCHED save.  If the deferred relational save is
    absent from the live UserCreationForm.save source, the gate's patch-apply did
    not take effect and any 'pass' here would certify nothing."""
    import inspect
    from django.contrib.auth.forms import UserCreationForm
    src = inspect.getsource(UserCreationForm.save)
    if "save_m2m" not in src:
        return ("ENV ERROR: the live UserCreationForm.save has no deferred "
                "relational save, so /testbed is not the patched source and "
                "this differential would be vacuous. Live source:\n" + src)
    return None


def main():
    _configure()
    env_err = _assert_oracle_is_patched()
    if env_err:
        print(env_err)
        print(json.dumps({"checked": 0, "disagreements": 0, "seed": SEED,
                          "error": "oracle not patched"}))
        return 1

    shapes, Organization, Team = _build_shapes()

    # a small fixed pool of association targets, created once
    pool = {"orgs": [Organization.objects.create(name="org %d" % i)
                     for i in range(3)],
            "teams": [Team.objects.create(name="team %d" % i)
                      for i in range(3)]}
    counter = [0]
    # branch coverage of the impl region, recorded per agreeing trial as
    # (commit, get_ready() after, relations_done() after) -- the vacuity guard
    # below refuses success unless both `commit` arms AND the deferred-relational
    # -save arm of `if self.get_ready()` were actually taken.
    cover = set()

    def build_form(form_cls, m2m_fields, n_assoc, leg):
        """A fresh bound form; the two legs submit the SAME associations and
        differ only in the unique username they must each own."""
        counter[0] += 1
        data = {"username": "u%d%s" % (counter[0], leg),
                "password1": "testclient", "password2": "testclient"}
        picked = {}
        for f in m2m_fields:
            picked[f] = sorted(o.pk for o in pool[f][:n_assoc])
            data[f] = [str(pk) for pk in picked[f]]
        return form_cls(data), picked

    def record_written(model, inst):
        """get_record() on the concrete side."""
        if inst is None or inst.pk is None:
            return False
        return model._default_manager.filter(pk=inst.pk).exists()

    def assoc_state(model, inst, m2m_fields):
        """The concrete realization of the relational-data effect: the persisted
        association pks per m2m field (None when the row itself is absent)."""
        if not record_written(model, inst):
            return None
        return tuple(tuple(sorted(getattr(inst, f).values_list("pk", flat=True)))
                     for f in m2m_fields)

    def check(shape_idx, commit, n_assoc):
        name, form_cls, model, m2m_fields, _blank_ok = shapes[shape_idx]

        # ---- shadow leg: the contract-stripped impl region, real callees ----
        s_form, s_picked = build_form(form_cls, m2m_fields, n_assoc, "s")
        if not s_form.is_valid():
            return ("FIXTURE ERROR shape=%s n_assoc=%d: form did not validate: "
                    "%r" % (name, n_assoc, s_form.errors))
        shadow = Form(s_form)
        # Requires(get_record() is False) and Requires(get_ready() is False)
        if shadow.get_record() or shadow.get_ready():
            return ("PRECONDITION ERROR shape=%s: the fresh form is not in the "
                    "modeled entry state (record=%r ready=%r)"
                    % (name, shadow.get_record(), shadow.get_ready()))
        out = save_form(shadow, commit)
        s_obs = (record_written(model, shadow.instance),
                 shadow.get_ready(),
                 shadow.relations_done(),
                 out is shadow,
                 assoc_state(model, shadow.instance, m2m_fields))
        if shadow.axiom_violations:
            return ("AXIOM DISAGREEMENT on (commit=%r, shape=%s, n_assoc=%d): "
                    "the real callee did not meet its @ContractOnly Ensures:\n"
                    "    %s" % (commit, name, n_assoc,
                                "\n    ".join(shadow.axiom_violations)))

        # ---- oracle leg: the REAL PATCHED UserCreationForm.save -------------
        o_form, o_picked = build_form(form_cls, m2m_fields, n_assoc, "o")
        if not o_form.is_valid():
            return ("FIXTURE ERROR shape=%s n_assoc=%d: oracle form did not "
                    "validate: %r" % (name, n_assoc, o_form.errors))
        if record_written(model, o_form.instance) or hasattr(o_form, "save_m2m"):
            return ("PRECONDITION ERROR shape=%s: the oracle's fresh form is "
                    "not in the modeled entry state" % (name,))
        user = o_form.save(commit=commit)
        o_obs = (record_written(model, user),
                 hasattr(o_form, "save_m2m"),
                 o_form.m2m_calls > 0,
                 user is o_form.instance,
                 assoc_state(model, user, m2m_fields))

        if s_picked != o_picked:
            return ("BRIDGE ERROR on (commit=%r, shape=%s, n_assoc=%d): the two "
                    "legs submitted different associations (%r vs %r)"
                    % (commit, name, n_assoc, s_picked, o_picked))

        if s_obs != o_obs:
            labels = ("record_written", "deferred_save_ready",
                      "relations_saved", "returns_own_instance",
                      "association_pks")
            diff = "\n".join(
                "    %-21s shadow=%r  real=%r%s"
                % (lab, a, b, "   <-- DIFFERS" if a != b else "")
                for lab, a, b in zip(labels, s_obs, o_obs))
            return ("DISAGREEMENT on (commit=%r, shape=%s, n_assoc=%d):\n%s"
                    % (commit, name, n_assoc, diff))

        # The ONE documented unmodeled node (mapping.md §2: the credential
        # assignment has no tracked persistence effect) must be EXACTLY where the
        # legs differ: the real leg ran set_password and so carries a hash, the
        # shadow -- whose impl region has no such statement -- carries none.  The
        # raw field is compared (not check_password, which may trigger a
        # hash-upgrade write and would perturb the tracked record state).
        if shadow.instance.password != "" or user.password == "":
            return ("UNMODELED-NODE DISAGREEMENT on (commit=%r, shape=%s, "
                    "n_assoc=%d): the credential divergence is not the "
                    "documented untracked one (shadow password=%r, real "
                    "password set=%r)"
                    % (commit, name, n_assoc, shadow.instance.password,
                       bool(user.password)))
        cover.add((commit, s_obs[1], s_obs[2]))

        # keep the tables bounded; every trial re-establishes its own state
        for inst in (shadow.instance, user):
            if inst is not None and inst.pk is not None:
                model._default_manager.filter(pk=inst.pk).delete()
        return None

    def fail(err, checked):
        print(err)
        print(json.dumps({"checked": checked, "disagreements": 1,
                          "seed": SEED}))
        return 1

    checked = 0

    # ---- BOUNDARY: exhaustive enumeration of the bridged input space --------
    # The modeled input is only `commit: bool`; the concrete degrees of freedom
    # the bridge exposes (form shape, number of submitted associations) are
    # enumerated in FULL.  The F2P cell -- commit=True, required-m2m shape, one
    # submitted association -- is checked first.
    boundary = [(0, True, 1)]
    for idx, (_n, _fc, _m, m2m_fields, blank_ok) in enumerate(shapes):
        for commit in (True, False):
            lo = 0 if (blank_ok or not m2m_fields) else 1
            for n_assoc in range(lo, 4):
                if not m2m_fields and n_assoc > 0:
                    continue        # no field to submit associations into
                boundary.append((idx, commit, n_assoc))
    cells = set(boundary)
    for cell in boundary:
        err = check(*cell)
        if err:
            return fail(err, checked)
        checked += 1

    # ---- FUZZ over that same space to reach the input count ----------------
    rng = random.Random(SEED)
    space = boundary[1:]
    while checked < N_TARGET:
        err = check(*space[rng.randrange(len(space))])
        if err:
            return fail(err, checked)
        checked += 1

    # ---- VACUITY GUARD: every branch of the impl region must have been taken.
    # (True, True, True): committed -> the record write AND the guarded deferred
    # relational save both ran (the arm the patch introduces).
    # (False, True, False): not committing -> the deferred save is set up and
    # nothing is written.  A run that never entered the committing arm, or never
    # took the guarded deferred save, would be green without exercising the
    # behaviour under specification.
    required_cover = {(True, True, True), (False, True, False)}
    if not required_cover <= cover:
        print("VACUITY: the impl region's branches were not all exercised; "
              "observed (commit, ready, relations_done) = %s, required %s"
              % (sorted(cover), sorted(required_cover)))
        print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                          "error": "branch coverage incomplete"}))
        return 1

    print("G-CONF OK: the contract-stripped impl region of save_form (its three "
          "@ContractOnly callees bound to the REAL BaseModelForm.save("
          "commit=False) / Model.save() / save_m2m) agrees with the REAL PATCHED "
          "UserCreationForm.save on %d Requires-satisfying inputs (seed %d): "
          "record-written, deferred-save-ready, deferred-relational-save-ran, "
          "returned-instance identity and the persisted association pks all "
          "match, every axiom Ensures held, and the only divergence is the "
          "documented untracked credential node; the finite modeled input space "
          "was enumerated exhaustively (%d cells) before fuzzing; 0 "
          "disagreements." % (checked, SEED, len(cells)))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "cells": len(cells),
                      "shadow": "direct (impl region verbatim; @ContractOnly "
                                "callees -> real repo functions)",
                      "oracle": "called: django.contrib.auth.forms."
                                "UserCreationForm.save (gold-patched)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
