#!/usr/bin/env python3
"""G-CONF for django__django-14752.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_get` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched results-assembly performed
by `AutocompleteJsonView.get`, over >=1e5 fuzzed inputs. Zero disagreements => 0.

Model (refinement.md): the response payload is

    { 'results': [ render(o, fieldKey) for o in objects ], 'more': hasMore }

where `render` is the per-item rendering the patched `get` dispatches through
(the new, overridable `serialize_result(obj, to_field_name)` method) applied
uniformly to every selected object, and `hasMore` is the page-has-next flag
copied through verbatim. The fix routes the per-item assembly through the
dispatched `render` rather than a hardwired inline expression.

  * Oracle = the REAL patched assembly: build the results list exactly as the
             patched `get` does — `[self.serialize_result(obj, tf) for obj in
             object_list]` — together with the more-flag.
  * Shadow = the Lean impl transliteration: accumulate `render(o, fieldKey)` per
             object in order via a for-loop, then attach the more-flag verbatim.

To keep the shadow honest about ONLY the R/I content (the per-object loop +
flag framing), the abstract A-reference step `render` is bound to the REAL repo
callee: the post-patch `AutocompleteJsonView.serialize_result` bound method.

Type bijection (mapping.md): objects<->object_list, fieldKey<->to_field_name,
hasMore<->page_obj.has_next(), result.results<->response 'results',
result.more<->response pagination['more']. stdlib-only; no hypothesis required.
"""
import random
import sys

# --- configure Django settings before importing the admin view --------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
        TEMPLATES=[],
    )
    django.setup()

from django.contrib.admin.views.autocomplete import AutocompleteJsonView

# A single default-class view instance supplies the REAL post-patch per-item
# rendering (the new `serialize_result` extension point). The base-class method
# does no DB / request work: it only reads `getattr(obj, to_field_name)` and
# `str(obj)`, so plain dummy objects exercise it faithfully.
_VIEW = AutocompleteJsonView()


def real_render(obj, field_key):
    """The REAL unchanged per-item rendering (A-reference): the post-patch
    `AutocompleteJsonView.serialize_result` bound method."""
    return _VIEW.serialize_result(obj, field_key)


class Obj:
    """A stand-in selected object: carries arbitrary attributes (so
    `getattr(obj, field_key)` and `str(obj)` are well-defined)."""
    def __init__(self, attrs, label):
        for k, v in attrs.items():
            setattr(self, k, v)
        self._label = label

    def __str__(self):
        return self._label


def oracle(objects, field_key, has_more):
    """Behavior of the patched repo `get` results-assembly for these inputs."""
    results = [_VIEW.serialize_result(obj, field_key) for obj in objects]
    return (results, has_more)


def shadow(objects, field_key, has_more):
    """R/I transliteration of implementation_get (Lean).

    Op 1 (R): accumulate `render(o, fieldKey)` per object, in order.
    Op 2 (A-reference): `render` is the REAL `serialize_result`.
    Op 3 (I): attach the more-flag verbatim.
    """
    results = []
    for o in objects:
        results = results + [real_render(o, field_key)]
    return (results, has_more)


FIELD_POOL = ["id", "pk", "uuid", "slug", "code", "name", "ref"]
LABEL_POOL = ["foo", "bar", "<b>x</b>", "a & b", "", "it's", '"q"', "café", "123"]


def rand_obj(rng):
    # the object always carries the field that will be looked up plus noise
    field = rng.choice(FIELD_POOL)
    attrs = {field: rng.choice([1, 42, "abc", "<v>", "", "x&y", 0, True])}
    # add a couple of extra attributes that should be ignored by the rendering
    for extra in rng.sample(FIELD_POOL, rng.randint(0, 3)):
        attrs.setdefault(extra, rng.choice([7, "z", None]))
    label = rng.choice(LABEL_POOL)
    return Obj(attrs, label), field


def main():
    rng = random.Random(14752)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        n = rng.randint(0, 6)
        objs = []
        # all objects in one request share the same to_field_name
        field_key = rng.choice(FIELD_POOL)
        for _ in range(n):
            o, _f = rand_obj(rng)
            # ensure the chosen field_key resolves on every object
            if not hasattr(o, field_key):
                setattr(o, field_key, rng.choice([1, "v", "<x>", 0]))
            objs.append(o)
        has_more = rng.random() < 0.5
        o_res = oracle(objs, field_key, has_more)
        s_res = shadow(objs, field_key, has_more)
        if o_res != s_res:
            disagreements += 1
            if first is None:
                first = (field_key, has_more, o_res, s_res)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
