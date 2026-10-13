#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13315 (nagini).

SHADOW: the impl region of `offered_options` from model.py, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers `occurs` and `dedup` copy over as plain functions on top of
a small immutable-tuple PSeq shim (PSeq / ToSeq / drop / take / +). This
bundle consumes no @ContractOnly axiom, so every shadow callee is the model's
own code.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.forms.models.apply_limit_choices_to_to_formfield(formfield)`, driven
through a real `ModelChoiceField` over an in-memory sqlite schema. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched code importable. This script does NOT apply any patch.

TYPE BRIDGE (mapping.md section 2):
  * The raw matching stream `matches: List[int]` (a row identifier once per
    join path satisfying the restriction) lifts to a real scenario: a Target
    row per identifier and one Link row per join path; the k-th occurrence of
    row r in the stream selects r's k-th Link via a `__in` restriction across
    the reverse relation, so applying the restriction with a plain join yields
    row r once per selected Link — exactly the modelled duplicate stream. This
    was validated against the PRE-patch code path (the raw `complex_filter`
    join), which reproduces the stream's duplicate multiplicities verbatim.
  * The offered options (the formfield's queryset after the narrowing) lower
    back to the list of yielded row primary keys.
  * Observation is multiset/membership equality (mapping.md: row equality is
    observed through assertCountEqual, order-independent), so shadow and real
    outputs are compared as sorted lists; the shadow's pinned element order is
    a strengthening on an unobserved dimension.
  * `occurs`/`dedup` use only equality on elements, so the behaviour is
    invariant under injective renaming of row identifiers; a fixed positive
    identifier universe {1..MAX_ROW} with per-row multiplicity <= MAX_MULT
    therefore covers every Requires-satisfying stream shape up to renaming
    (the precondition demands only read permission on the list).
  * The restriction is driven in both accepted forms (a Q object and a plain
    dict), alternating, since the modelled behaviour is agnostic to which the
    field supplies.

INPUT DOMAIN: streams of length 0..MAX_STREAM over the identifier universe,
including empty, singleton, all-distinct, single-row-many-paths, interleaved
and maximum-multiplicity shapes.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz streams.
Pinned fuzz seed: 133150.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random).
"""
import json
import random
import sys

SEED = 133150
N_FUZZ = 100000
MAX_ROW = 8       # distinct row identifiers available in the fixture
MAX_MULT = 16     # join paths (Links) per row in the fixture
MAX_STREAM = 20   # generated stream length cap (<= MAX_ROW * MAX_MULT shapes)


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeqShim(object):
    __slots__ = ("_t",)

    def __init__(self, t=()):
        self._t = tuple(t)

    def drop(self, n):
        return PSeqShim(self._t[n:])

    def take(self, n):
        return PSeqShim(self._t[:n])

    def __add__(self, other):
        return PSeqShim(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeqShim) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def PSeq(*items):
    return PSeqShim(items)


def ToSeq(lst):
    return PSeqShim(lst)


# --- pure helpers from model.py, decorators/contracts stripped ----------------

def occurs(v, s):
    if len(s) == 0:
        return False
    return s[0] == v or occurs(v, s.drop(1))


def dedup(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    if occurs(s[0], s.drop(1)):
        return dedup(s.drop(1))
    return PSeq(s[0]) + dedup(s.drop(1))


# --- impl region of offered_options, verbatim (contracts stripped) ------------

def offered_options(matches):
    result = []  # type: list
    i = len(matches)
    while i > 0:
        v = matches[i - 1]
        # Keep this row only if it does not recur later in the stream, so a row
        # matched along several join paths is offered exactly once.
        if occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result
        i = i - 1
    return result


# --- oracle plumbing -----------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not importable/configurable: %r" % (exc,))
        return 1

    from django.apps import apps
    from django.db import connection, models
    from django.db.models import Q
    from django import forms
    from django.forms.models import apply_limit_choices_to_to_formfield

    # Fixture: a Target row per identifier, MAX_MULT Link rows per Target.
    # (Attached to an installed app label so the reverse relation is resolvable
    # from an ad-hoc script; the label choice is bridge plumbing only.)
    class Target(models.Model):
        class Meta:
            app_label = "contenttypes"

    class Link(models.Model):
        target = models.ForeignKey(Target, on_delete=models.CASCADE,
                                   related_name="links")
        code = models.IntegerField()

        class Meta:
            app_label = "contenttypes"

    apps.clear_cache()  # make the freshly-defined reverse relation visible

    with connection.schema_editor() as editor:
        editor.create_model(Target)
        editor.create_model(Link)

    for r in range(1, MAX_ROW + 1):
        t = Target.objects.create(pk=r)
        Link.objects.bulk_create(
            [Link(target=t, code=r * 100 + j) for j in range(1, MAX_MULT + 1)])

    def lift_codes(matches):
        """Stream -> the Link codes selecting one join path per occurrence:
        the k-th occurrence of row r selects r's k-th Link."""
        seen = {}
        codes = []
        for r in matches:
            seen[r] = seen.get(r, 0) + 1
            codes.append(r * 100 + seen[r])
        return codes

    def run_real(matches, as_dict):
        """Drive the REAL patched narrowing on a fresh formfield; lower the
        offered options back to the list of yielded row pks."""
        codes = lift_codes(matches)
        if as_dict:
            restriction = {"links__code__in": codes}
        else:
            restriction = Q(links__code__in=codes)
        ff = forms.ModelChoiceField(queryset=Target.objects.all(),
                                    limit_choices_to=restriction)
        apply_limit_choices_to_to_formfield(ff)
        return list(ff.queryset.values_list("pk", flat=True))

    def check_one(matches, as_dict, label):
        real = run_real(matches, as_dict)
        shadow = offered_options(list(matches))
        # internal cross-check: the shadow must compute the pure fold exactly
        if ToSeq(shadow) != dedup(ToSeq(matches)):
            print("INTERNAL: shadow impl deviates from the pure fold on %s\n"
                  "  input=%r shadow=%r" % (label, matches, shadow))
            return False
        # observable comparison: multiset/membership equality (order-blind)
        if sorted(shadow) != sorted(real):
            print("DISAGREEMENT on %s\n  input (matching stream) = %r "
                  "(restriction as %s)\n  shadow (impl region)    = %r\n"
                  "  real (patched repo)     = %r"
                  % (label, matches, "dict" if as_dict else "Q",
                     sorted(shadow), sorted(real)))
            return False
        return True

    boundary = [
        [],
        [1],
        [1, 1],                          # one row, two join paths
        [1, 2],                          # two distinct rows
        [1, 1, 1],                       # one row, three join paths
        [1, 2, 1],                       # interleaved duplicate
        [2, 1, 2, 1],                    # the regression shape: 2 rows x 2 paths
        [3, 3, 5, 5, 7],                 # mixed multiplicities
        [8, 7, 6, 5, 4, 3, 2, 1],        # all distinct, descending
        [1] * MAX_MULT,                  # one row matched the maximum ways
        [1, 2] * (MAX_STREAM // 2),      # alternating at full length
        list(range(1, MAX_ROW + 1)) + list(range(1, MAX_ROW + 1)),
    ]

    checked = 0
    for idx, m in enumerate(boundary):
        for as_dict in (False, True):
            if not check_one(m, as_dict, "boundary[%d]" % idx):
                return 1
            checked += 1

    rng = random.Random(SEED)
    for k in range(N_FUZZ):
        n = rng.randint(0, MAX_STREAM)
        m = []
        mult = {}
        while len(m) < n:
            v = rng.randint(1, MAX_ROW)
            if mult.get(v, 0) < MAX_MULT:
                mult[v] = mult.get(v, 0) + 1
                m.append(v)
        if not check_one(m, as_dict=bool(k % 2), label="fuzz[%d]" % k):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped impl region + pure fold "
          "cross-check) == real patched narrowing on %d inputs (%d boundary "
          "x2 restriction forms + %d fuzz streams, seed %d), compared as "
          "multisets of offered row identifiers; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
