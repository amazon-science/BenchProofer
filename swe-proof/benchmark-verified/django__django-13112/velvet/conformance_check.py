#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13112 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch). The
              impl region has NO A-tagged callee (mapping.md §5), so the whole
              shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `ForeignObject.deconstruct` (resolved via `ForeignKey`, which
              inherits it) applied at base_commit with the gold patch (the
              correctness oracle, G-RESOLVE). A `ForeignKey` is constructed with
              a string model reference and `kwargs['to']` is read back.

They must agree on every input in the modeled domain. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. Inputs are restricted to the modeled domain — model references with at
most one dot separator AND all code points ASCII (< 128), the domain pinned by
Solution.lean's two `require`s (mapping.md §3) — over the identifier alphabet
(mapping.md §2), so the `str.lower()` ↔ `Char.toLower` bijection is exact.
"""
import random
import sys

SEED = 13112
N_FUZZ = 100_000
# identifier alphabet: app labels and model names (ASCII letters/digits/_), with
# mixed case so the app-label-case-preservation vs model-name-fold distinction is
# exercised. The '.' separator is added explicitly when building qualified refs.
IDENT = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"


# --- the R/I shadow: Solution.lean normalizedRef, transliterated -------------
def shadow_normalize(ref):
    """normalizedRef (ref.toList) transliterated to str.
    Qualified (one dot): app-label prefix verbatim + '.' + folded model name.
    Unqualified: fold the whole reference."""
    if "." in ref:                                  # isQualified
        app = ref[:ref.index(".")]                  # appPart = takeWhile (!= '.')
        name = ref[ref.index(".") + 1:]             # namePart = (dropWhile (!= '.')).drop 1
        return app + "." + name.lower()             # foldCase only the model name
    return ref.lower()                              # foldCase the whole ref


# --- the oracle: the REAL patched deconstruct, driven via a ForeignKey -------
_DJANGO_READY = False


def _ensure_django():
    global _DJANGO_READY
    if _DJANGO_READY:
        return
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    django.setup()
    _DJANGO_READY = True


def oracle_normalize(ref):
    """patch.diff's behaviour: construct a ForeignKey with the string model
    reference `ref` and read back kwargs['to'] from deconstruct() (the patched
    ForeignObject.deconstruct, inherited by ForeignKey)."""
    _ensure_django()
    from django.db import models
    f = models.ForeignKey(ref, on_delete=models.CASCADE)
    name, path, args, kwargs = f.deconstruct()
    return kwargs.get("to")


def gen_ref(rng):
    """Generate a model reference in the modeled domain (<=1 dot) over the
    identifier alphabet. ~half qualified (app_label.ModelName), ~half bare."""
    def ident(min_len=1, max_len=10):
        return "".join(rng.choice(IDENT) for _ in range(rng.randint(min_len, max_len)))
    if rng.random() < 0.5:
        return ident() + "." + ident()              # qualified (exactly one dot)
    return ident()                                  # unqualified (no dot)


def boundary_cases():
    # the F2P scenario and neighbours: mixed-case app label, qualified + bare
    yield "MiXedCase_migrations.Author"
    yield "MiXedCase_migrations.Book"
    yield "MiXedCase_migrations.Magazine"
    yield "App.Model"
    yield "app.model"
    yield "APP.MODEL"
    yield "MyApp.MyModel"
    yield "auth.User"
    yield "Author"
    yield "AUTHOR"
    yield "author"
    yield "MixedAuthor"
    yield "a.B"
    yield "A.b"
    yield "X.y"
    yield "lower_app.UpperModel"


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(boundary_cases())
    cases += [gen_ref(rng) for _ in range(N_FUZZ)]

    for ref in cases:
        # modeled domain only (mapping.md §3): at most one dot separator and
        # all code points ASCII (< 128) — the domain Solution.lean's requires pin
        if ref.count(".") > 1 or any(ord(c) >= 128 for c in ref):
            continue
        count += 1
        shadow = shadow_normalize(ref)
        oracle = oracle_normalize(ref)
        if shadow != oracle:
            disagreements.append((ref, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ref, sh, orc in disagreements:
            print("  ref=%r shadow=%r oracle=%r" % (ref, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of normalizeRef agrees with the real patched "
          "ForeignObject.deconstruct on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
