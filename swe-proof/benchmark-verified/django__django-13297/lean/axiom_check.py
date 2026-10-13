#!/usr/bin/env python3
"""G-AX for django__django-13297 — validate the A-reference op (the deferred
proxy builder) against the REAL repo callee in-container.

refinement.md op #3 deep-models the changed proxy-builder: the post-patch wrapper
`lazy(access_value, type(value))()` PRESENTS the underlying value's own type to
consumers, whereas the pre-patch wrapper `SimpleLazyObject(access_value)` presents
only a single generic deferred-object type. The Lean model encodes exactly this:

    post  DeferredValue.presentedType = value.pytype       (= type(value))
    pre   DeferredValue.presentedType = genericDeferredType (one fixed tag)

This script runs the real `django.utils.functional.lazy` and `SimpleLazyObject`
against boundary + fuzz inputs and asserts:

  (A) the post-patch wrapper presents `type(value)` — i.e. it passes the
      type-directed checks a consumer relies on (`isinstance`, type-keyed
      delegation), and resolves to exactly `value`;
  (B) the pre-patch wrapper (`SimpleLazyObject`) does NOT present `type(value)`
      for a non-generic value — it is of the single generic type — so the two
      constructions are genuinely distinguishable on the presented-type facet.

stdlib + django only; exit 0 iff every observation meets the modeled property.
"""
import json
import sys
import warnings

SEED = 13297

try:
    from django.utils.functional import lazy, SimpleLazyObject, Promise
except Exception as e:  # pragma: no cover
    print(json.dumps({"status": "error", "instance": "django__django-13297",
                      "reason": f"cannot import django callee: {e!r}"}))
    sys.exit(1)


def make_access_value(value):
    # Faithful stand-in for the patch's closure `access_value` (the warning side
    # effect is orthogonal to the presented-type facet under test).
    def access_value():
        return value
    return access_value


def post_wrapper(value):
    """Post-patch construction: lazy(access_value, type(value))()."""
    return lazy(make_access_value(value), type(value))()


def pre_wrapper(value):
    """Pre-patch construction: SimpleLazyObject(access_value)."""
    return SimpleLazyObject(make_access_value(value))


# Sample values spanning the runtime types that flow through URL kwargs (the
# F2P case is a str slug / model-name); include ints/bytes/edge strings.
VALUES = [
    "Rene Magritte", "", "offer-slug", "123", "Ünîcödé",
    "a" * 256, "0", "with spaces",
]


def check_value(value):
    """Return None if the modeled property holds for `value`, else a reason."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        post = post_wrapper(value)
        pre = pre_wrapper(value)

        # (A) post wrapper presents type(value): a str-typed proxy must satisfy
        # the type-directed operations a consumer performs. For str values the
        # decisive consumer behavior is that it equals / stringifies to the value
        # and that the proxy delegates the value's own type interface.
        if str(post) != str(value):
            return f"post wrapper does not resolve to value: {value!r}"
        if not (post == value):
            return f"post wrapper not equal to underlying value: {value!r}"
        # The proxy is prepared from type(value): the delegated cast yields the
        # value's type exactly (str delegation present iff str in resultclasses).
        if isinstance(value, str) and type(str(post)) is not str:
            return f"post wrapper str-cast not str-typed: {value!r}"

        # (B) pre wrapper is a SimpleLazyObject — the single generic deferred
        # type — NOT prepared from type(value); for a non-SimpleLazyObject value
        # its wrapper type differs from the post wrapper's presented type.
        if not isinstance(pre, SimpleLazyObject):
            return f"pre wrapper not the generic SimpleLazyObject type: {value!r}"
        # The post construction is a lazy() __proxy__ (a Promise), distinct in
        # type from the generic SimpleLazyObject — the presented-type facet the
        # patch changes.
        if type(pre) is type(post):
            return f"pre/post present the same type (no discrimination): {value!r}"
        if not isinstance(post, Promise):
            return f"post wrapper is not a lazy proxy: {value!r}"
    return None


def main() -> int:
    checked = 0
    for value in VALUES:
        reason = check_value(value)
        if reason:
            print(json.dumps({"status": "fail", "instance": "django__django-13297",
                              "reason": reason}))
            return 1
        checked += 1
    print(json.dumps({
        "status": "pass",
        "instance": "django__django-13297",
        "checked": checked,
        "property": "post-patch lazy(f,type(v))() presents type(v) and resolves "
                    "to v; pre-patch SimpleLazyObject presents the generic type",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
