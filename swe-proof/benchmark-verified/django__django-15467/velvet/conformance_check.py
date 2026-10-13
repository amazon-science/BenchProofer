#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15467 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`emptyLabelFor`
              / `resolvedLabel`) transliterated to Python over the *real* repo
              types, via the mapping.md bijection
              (`Bool` ↔ bool, `Option (Option String)` ↔ kwargs key-presence,
              `Option.getD` ↔ dict.get(key, default), `Option String` ↔
              str|None). The `defaultLabel` A-reference value is the literal
              "None" here; the oracle uses the real `gettext("None")` (equal
              under the test locale, mapping.md §3.1) — that single value
              equality is G-AX's job, not G-CONF's.
  * ORACLE  — `patch.diff`'s behaviour: the *real patched*
              `ModelAdmin.formfield_for_foreignkey`, exercised end-to-end by
              constructing a `ModelAdmin` with `radio_fields` set over a
              ForeignKey and reading back the produced form field's
              `empty_label` (the value the F2P test observes). The harness
              git-applies the gold patch at base_commit before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + Django only
(no hypothesis needed). The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import os
import random
import sys

SEED = 15467
N_FUZZ = 100_000

# A sentinel distinguishing "caller supplied nothing" from "caller supplied the
# value None" — the three-way key-presence distinction the nested Option models.
_ABSENT = object()


# --- the R/I shadow: Solution.lean resolvedLabel, transliterated -------------
def shadow_empty_label(allows_blank, override):
    """resolvedLabel allowsBlank override, transliterated to Python.

    `override` is `_ABSENT` (carrier `none` — key absent) or a value `v`
    (carrier `some v`, where v may be a str or None). `Option.getD defaultLabel`
    ↔ keep `override` when present else the fallback "None"."""
    if allows_blank:
        return "None" if override is _ABSENT else override  # override.getD defaultLabel
    return None


# --- the oracle: the real patched formfield_for_foreignkey -------------------
def _build_oracle():
    """Configure a throwaway Django project and return a resolver that drives
    the real `ModelAdmin.formfield_for_foreignkey` (patched) end-to-end."""
    import django

    app_dir = "/tmp/gconf_app_15467"
    os.makedirs(app_dir, exist_ok=True)
    open(os.path.join(app_dir, "__init__.py"), "w").close()
    with open(os.path.join(app_dir, "models.py"), "w") as f:
        f.write(
            "from django.db import models\n"
            "class Inv(models.Model):\n"
            "    # blank=True  -> an empty selection is admitted\n"
            "    parent = models.ForeignKey('self', models.SET_NULL,\n"
            "                               blank=True, null=True)\n"
            "    # blank=False -> no empty selection admitted\n"
            "    nb_parent = models.ForeignKey('self', models.CASCADE,\n"
            "                                  blank=False, null=False,\n"
            "                                  related_name='x')\n"
        )
    sys.path.insert(0, "/tmp")
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                            "django.contrib.admin", "gconf_app_15467"],
            USE_TZ=True,
        )
    django.setup()

    from django.db import models
    from django.contrib import admin
    from gconf_app_15467.models import Inv

    site = admin.AdminSite()

    def resolve(field_name, override, route):
        """field_name: 'parent' (blank) | 'nb_parent' (non-blank).
        override: _ABSENT, or a value (str|None) the caller supplies.
        route: 'overrides' (formfield_overrides) | 'kwargs' (explicit kwarg)."""
        class MA(admin.ModelAdmin):
            radio_fields = {field_name: admin.VERTICAL}
        kwargs = {}
        if override is not _ABSENT:
            if route == "overrides":
                MA.formfield_overrides = {models.ForeignKey: {"empty_label": override}}
            else:
                kwargs = {"empty_label": override}
        ma = MA(Inv, site)
        ff = ma.formfield_for_dbfield(Inv._meta.get_field(field_name),
                                      request=None, **kwargs)
        return ff.empty_label

    return resolve


def fuzz_cases(n, rng):
    """Yield (field_name, allows_blank, override, route) configurations."""
    fields = [("parent", True), ("nb_parent", False)]
    routes = ["overrides", "kwargs"]
    fixed_values = ["", "Custom empty label", "None", "Custom", "I WANT MY OWN",
                    "0", "  ", "—", "Ünïcödé", None]
    # boundary cases first (plan §4.1 step 4): every field × {absent, each value}
    # × every route.
    for fname, blank in fields:
        for route in routes:
            yield (fname, blank, _ABSENT, route)
            for v in fixed_values:
                yield (fname, blank, v, route)
    # randomized fuzz
    chars = "abcABC 0_-éNoneCustom\t<>'\""
    for _ in range(n):
        fname, blank = rng.choice(fields)
        route = rng.choice(routes)
        r = rng.random()
        if r < 0.15:
            override = _ABSENT
        elif r < 0.25:
            override = None
        else:
            k = rng.randint(0, 20)
            override = "".join(rng.choice(chars) for _ in range(k))
        yield (fname, blank, override, route)


def main():
    rng = random.Random(SEED)
    try:
        oracle = _build_oracle()
    except Exception as exc:  # pragma: no cover - environment failure
        print("G-CONF ERROR: could not build oracle: %r" % (exc,))
        return 2

    disagreements = []
    count = 0
    for fname, blank, override, route in fuzz_cases(N_FUZZ, rng):
        count += 1
        want = shadow_empty_label(blank, override)
        got = oracle(fname, override, route)
        if want != got:
            disagreements.append((fname, blank, override, route, want, got))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fname, blank, ov, route, want, got in disagreements:
            ov_s = "ABSENT" if ov is _ABSENT else repr(ov)
            print("  field=%s blank=%s override=%s route=%s shadow=%r oracle=%r"
                  % (fname, blank, ov_s, route, want, got))
        return 1
    print("G-CONF OK: R/I shadow of emptyLabelFor agrees with patch.diff "
          "behaviour (real formfield_for_foreignkey) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
