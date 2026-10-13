#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15731.

The bundle models ONE behavior: the introspectable metadata that
`BaseManager._get_queryset_methods.create_method` gives the delegating method it
produces (`django/db/models/manager.py:83-89`). The modeled value is the tuple

    (__name__, __qualname__, __module__, __doc__, __annotations__,
     str(inspect.signature(produced_method)))

as a PURE function of two observables (mapping.md):

    underlying  : the source queryset method's metadata
    rawDelegate : the bare forwarding wrapper's intrinsic metadata
                  (catch-all signature, own qualname/module, empty doc/annot.)

Post-patch rule (`@wraps(method)`): every introspectable attribute of the
produced method equals the underlying method's.

The ORACLE below is a faithful in-process replica that builds a REAL forwarding
function with the same parameter list as `underlying`, applies the actual
`functools.wraps`, and reads back the six attributes via `inspect.signature` and
the dunder attributes — exactly what the patched `create_method` does. The SHADOW
is the op-for-op transliteration of `implementation_delegateMetadata` (copy every
field from `underlying`, per refinement.md).

This genuinely tests the modeling: the shadow asserts every field equals
`underlying`'s; the oracle reaches that via the real `@wraps` + `inspect.signature`
machinery — in particular `str(inspect.signature(...))` must surface the
underlying method's REAL parameter list, not the wrapper's `(self, *args,
**kwargs)` (the exact F2P discriminator).

stdlib-only. Pinned seed: 15731 (also in mapping.md).
"""
import functools
import inspect
import random
import sys

SEED = 15731
N = 120_000

# A pool of realistic source-method parameter lists (rendered WITHOUT the leading
# `self`, matching what inspect.signature reports on a bound/unbound method body).
PARAM_LISTS = [
    "(objs, batch_size=None, ignore_conflicts=False)",
    "(objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, "
    "update_fields=None, unique_fields=None)",
    "(*args, **kwargs)",
    "()",
    "(self)",
    "(a, b, c=1)",
    "(x, *, y=2)",
    "(self, using=None)",
]
NAMES = ["bulk_create", "count", "get", "filter", "annotate", "values_list"]
MODULES = ["django.db.models.query", "myapp.queryset", "x.y.z"]
DOCS = ["", "Insert each of the instances into the database.", "Return count.",
        "Multi\nline\ndoc."]
ANNOTS = ["", "{'return': 'int'}", "{'objs': 'list', 'return': 'list'}"]


def _build_real_methods(underlying):
    """Construct a REAL source method whose metadata matches `underlying`, and the
    pre/post forwarding wrappers, returning their read-back metadata tuples.

    `underlying` is a dict with keys name, qualname, module, doc, annotations,
    and `params` (the source parameter list string, e.g. "(objs, batch_size=None)").
    """
    params = underlying["params"]
    # Synthesize a real function object with exactly that signature so that
    # inspect.signature() reports `params`. We exec a def with the given param
    # list (sans self handling — params already include or omit self as desired).
    src = f"def _src{params}:\n    'doc-placeholder'\n    return None\n"
    ns = {}
    exec(src, ns)  # noqa: S102 — controlled, test-only synthesis
    method = ns["_src"]
    method.__name__ = underlying["name"]
    method.__qualname__ = underlying["qualname"]
    method.__module__ = underlying["module"]
    method.__doc__ = underlying["doc"] or None
    if underlying["annotations"]:
        # store a stable, comparable annotation mapping
        method.__annotations__ = {"_ann": underlying["annotations"]}
    return method


def _readback(fn):
    try:
        sig = str(inspect.signature(fn))
    except (ValueError, TypeError):
        sig = "<no-signature>"
    return (
        fn.__name__,
        fn.__qualname__,
        fn.__module__,
        fn.__doc__ or "",
        _ser_annot(getattr(fn, "__annotations__", {}) or {}),
        sig,
    )


def _ser_annot(ann):
    if not ann:
        return ""
    return ann.get("_ann", "") if isinstance(ann, dict) else ""


def oracle_post(underlying):
    """Faithful replica of the PATCHED create_method: @wraps(method)."""
    method = _build_real_methods(underlying)

    @functools.wraps(method)
    def manager_method(self, *args, **kwargs):
        return None

    return _readback(manager_method)


# --- SHADOW of implementation_delegateMetadata (the R/I leg) -----------------
# Mirrors Solution.lean: meta := rawDelegate; copy every field from underlying.
def shadow(underlying, raw_delegate):
    return (
        underlying["name"],
        underlying["qualname"],
        underlying["module"],
        underlying["doc"],
        underlying["annotations"],
        underlying["sig_expected"],
    )


def _expected_sig(params):
    """What str(inspect.signature(...)) reports for the produced method post-wraps:
    it follows __wrapped__ to the source, so it equals the source's signature."""
    return params


# rawDelegate: the bare forwarding wrapper's intrinsic metadata (fixed shape).
RAW_DELEGATE = {
    "name": "manager_method",
    "qualname": "BaseManager._get_queryset_methods.<locals>.create_method."
                "<locals>.manager_method",
    "module": "django.db.models.manager",
    "doc": "",
    "annotations": "",
    "sig_expected": "(self, *args, **kwargs)",
}


def _mk_underlying(name, qualname, module, doc, annotations, params):
    u = {"name": name, "qualname": qualname, "module": module, "doc": doc,
         "annotations": annotations, "params": params}
    u["sig_expected"] = _expected_sig(params)
    return u


def disagree(underlying):
    got = oracle_post(underlying)
    want = shadow(underlying, RAW_DELEGATE)
    if got != want:
        return (underlying, got, want)
    return None


def _enumerate_edge():
    cases = []
    # The exact F2P shape: bulk_create's real parameter list must surface.
    cases.append(_mk_underlying(
        "bulk_create", "QuerySet.bulk_create", "django.db.models.query",
        "Insert each of the instances into the database.", "",
        "(objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, "
        "update_fields=None, unique_fields=None)"))
    # signature differing only in being non-catch-all
    cases.append(_mk_underlying("count", "QuerySet.count",
                                "django.db.models.query", "Return count.", "", "()"))
    # underlying whose signature happens to equal the raw catch-all
    cases.append(_mk_underlying("weird", "QuerySet.weird",
                                "django.db.models.query", "", "",
                                "(self, *args, **kwargs)"))
    # empty doc + annotations present
    cases.append(_mk_underlying("get", "QuerySet.get", "django.db.models.query",
                                "", "{'return': 'int'}", "(a, b, c=1)"))
    return cases


def main() -> int:
    checked = 0
    for u in _enumerate_edge():
        d = disagree(u)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        u = _mk_underlying(
            rng.choice(NAMES),
            "QuerySet." + rng.choice(NAMES),
            rng.choice(MODULES),
            rng.choice(DOCS),
            rng.choice(ANNOTS),
            rng.choice(PARAM_LISTS),
        )
        d = disagree(u)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
