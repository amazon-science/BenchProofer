#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11163 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `keep` / `selectNames` over the candidate names, the
              optional selector (`fields`), and the omit list (`exclude`). This
              is pure R/I (the bundle has NO axioms, mapping.md §3), so the whole
              shadow is in scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `django.forms.models.model_to_dict`. We do not reconstruct a full
              Django model; `model_to_dict` only reads
              `instance._meta.{concrete_fields, private_fields, many_to_many}`,
              `getattr(f, 'editable', False)`, `f.name`, and
              `f.value_from_object(instance)`. We therefore feed it a DUCK-TYPED
              fake instance + fake field objects, so the real patched code path
              decides the key set. The test observes the dict's KEY set
              (`sorted(model_to_dict(...))`), exactly what the F2P / added tests
              assert; field VALUES (`value_from_object`) are an unmodeled
              R-identity (refinement.md row 6) and are not compared.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), stdlib
+ the in-image Django only. The fuzz seed is pinned (mapping.md §4).
"""
import itertools
import random
import sys

SEED = 11163
N_FUZZ = 100_000


# --- ORACLE setup: import the REAL patched model_to_dict ---------------------

def _load_real_model_to_dict():
    """Import the gold-patched django.forms.models.model_to_dict. Configure a
    minimal settings module first so the forms package imports cleanly."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            USE_I18N=False,
            USE_TZ=False,
            DATABASES={},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
        django.setup()
    from django.forms.models import model_to_dict
    return model_to_dict


class _FakeField:
    """Duck-typed stand-in for a Django model field, as model_to_dict sees it."""
    def __init__(self, name, editable=True):
        self.name = name
        self.editable = editable

    def value_from_object(self, instance):
        # Unmodeled R-identity (refinement.md row 6): the VALUE is irrelevant to
        # the observed key set. Return something deterministic.
        return "v:" + self.name


class _FakeMeta:
    def __init__(self, concrete, private, m2m):
        self.concrete_fields = concrete
        self.private_fields = private
        self.many_to_many = m2m


class _FakeInstance:
    def __init__(self, meta):
        self._meta = meta


# --- SHADOW: Solution.lean keep / selectNames, transliterated ----------------

def shadow_select(names, fields, exclude):
    """selectNames(selector, excl, candidates) transliterated.

    `names`   : the editable candidate field names, in order (List Int -> str).
    `fields`  : the optional selector  (None -> none, list -> some [...]).
    `exclude` : the omit list          (None/[] both -> []).
    Returns the kept names in candidate order (the modeled `out`)."""
    excl = exclude or []

    def keep(n):
        sel_ok = True if fields is None else (n in fields)   # presence, not truthiness
        return sel_ok and (n not in excl)

    return [n for n in names if keep(n)]


def main():
    rng = random.Random(SEED)
    try:
        model_to_dict = _load_real_model_to_dict()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched model_to_dict: %r" % e)
        return 2

    pool = ["id", "name", "score", "writer_ptr", "age", "email", "x", "y", "z"]

    def make_instance(editable_names, noneditable_names):
        # Split the editable candidates across the three field groups
        # model_to_dict chains, to exercise the chain() iteration too.
        ef = [_FakeField(n, editable=True) for n in editable_names]
        nf = [_FakeField(n, editable=False) for n in noneditable_names]
        # interleave non-editable into the concrete group; m2m/private get a slice
        third = max(1, len(ef) // 3)
        concrete = ef[:third] + nf
        private = ef[third:2 * third]
        m2m = ef[2 * third:]
        return _FakeInstance(_FakeMeta(concrete, private, m2m)), \
            [f.name for f in (concrete + private + m2m) if f.editable]

    def oracle_keys(instance, fields, exclude):
        kwargs = {}
        if fields is not None:
            kwargs["fields"] = fields
        if exclude is not None:
            kwargs["exclude"] = exclude
        return sorted(model_to_dict(instance, **kwargs))

    disagreements = []
    count = 0

    def run_case(editable_names, noneditable_names, fields, exclude):
        nonlocal count
        count += 1
        instance, cand = make_instance(editable_names, noneditable_names)
        shadow = sorted(shadow_select(cand, fields, exclude))
        oracle = oracle_keys(instance, fields, exclude)
        if shadow != oracle:
            disagreements.append(
                (editable_names, noneditable_names, fields, exclude, shadow, oracle))

    # --- boundary cases (the issue + the added F2P assertions) ---------------
    base = ["id", "name", "score", "writer_ptr"]
    boundary = [
        (base, [], None, None),                 # everything
        (base, [], [], None),                   # fields=[]  -> {}   (the bug)
        (base, [], ["id", "name"], None),        # subset
        (base, [], None, []),                   # exclude=[] -> all
        (base, [], None, ["id", "name"]),        # exclude subset
        (base, [], [], []),                      # both empty -> {}
        (base, [], ["id", "name"], ["name"]),    # exclude overrides fields
        ([], [], None, None),                    # no candidates
        ([], [], [], None),                      # no candidates, fields=[]
        (base, ["secret"], None, None),          # a non-editable candidate
        (base, ["secret"], ["secret"], None),    # select a non-editable name
        (base, [], ["missing"], None),           # select a name not present
    ]
    for en, ne, f, x in boundary:
        run_case(en, ne, f, x)

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_FUZZ):
        k = rng.randint(0, len(pool))
        editable = rng.sample(pool, k)
        rest = [p for p in pool if p not in editable]
        ne = rng.sample(rest, rng.randint(0, len(rest)))
        all_names = editable + ne
        # fields: None, or a random subset of all_names (possibly empty / with
        # names not among candidates)
        fchoice = rng.random()
        if fchoice < 0.34:
            fields = None
        elif fchoice < 0.5:
            fields = []
        else:
            fields = rng.sample(all_names, rng.randint(0, len(all_names))) \
                if all_names else []
            if rng.random() < 0.2:
                fields = fields + ["ghost"]      # a name not among candidates
        xchoice = rng.random()
        if xchoice < 0.34:
            exclude = None
        elif xchoice < 0.5:
            exclude = []
        else:
            exclude = rng.sample(all_names, rng.randint(0, len(all_names))) \
                if all_names else []
        run_case(editable, ne, fields, exclude)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for en, ne, f, x, sh, orc in disagreements:
            print("  editable=%r noneditable=%r fields=%r exclude=%r "
                  "shadow=%r oracle=%r" % (en, ne, f, x, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectModelFields agrees with the real "
          "patched model_to_dict key set on %d inputs (12 boundary + fuzz, "
          "seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
