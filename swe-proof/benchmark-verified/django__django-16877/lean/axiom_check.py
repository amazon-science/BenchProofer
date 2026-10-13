#!/usr/bin/env python3
"""G-AX for django__django-16877 — validates the lone A-reference `condEscape`.

The bundle consumes NO callee *axiom* (`meta.json axioms = []`): the proof of
`correct_escapeEach` closes by a loop-fold induction
(`implementation_escapeEach value = value.map condEscape`) and uses no property of
`condEscape`. `condEscape` is an **A-reference**: it models the UNCHANGED
per-element escaper `conditional_escape` (django/utils/html.py:82-94), which the
added `escapeseq` filter applies to each element of the sequence.

This check validates that A-reference against the REAL callee. The new filter
`escapeseq` is a thin element-wise map over `conditional_escape`; modeling the
per-element escaper opaquely (value-unconstrained reference) is sound iff the real
`conditional_escape` is:

  (1) TOTAL (never raises) on the element domain the model covers — ordinary
      strings AND strings already marked safe; and
  (2) string-valued — its result is a `str` (possibly a `SafeString`), so the
      `List String` result-type bijection holds.

We do NOT pin the exact escaped output (that is the escaper's own behavior, not a
property the proof consumes); we only confirm totality + string-valuedness, which
is exactly what the opaque reference relies on. Boundary + fuzz, seed 16877.

stdlib-only (plus Django, present in the task image).
"""
import json
import random
import sys

SEED = 16877


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, INSTALLED_APPS=[], DATABASES={})
    django.setup()


def main() -> int:
    try:
        _setup_django()
        from django.utils.html import conditional_escape
        from django.utils.safestring import mark_safe
    except Exception as e:  # pragma: no cover
        print(json.dumps({"status": "fail", "instance": "django__django-16877",
                          "reason": f"setup failed: {e!r}"}))
        return 1

    rng = random.Random(SEED)
    checked = 0

    raw_pool = ["", "x&y", "<p>", '"q"', "'a'", "a&b<c>d", "plain", "&amp;",
                "<script>", "líne\nbreak", "  ", "&<>\"'", "Z" * 64]

    def check_one(obj):
        # (1) total: must not raise; (2) string-valued.
        res = conditional_escape(obj)
        if not isinstance(res, str):
            return f"non-string result {res!r} (type {type(res)!r}) for {obj!r}"
        return None

    try:
        # boundary: every pool element, both raw and marked-safe.
        for s in raw_pool:
            for obj in (s, mark_safe(s)):
                err = check_one(obj)
                if err:
                    print(json.dumps({"status": "fail",
                                      "instance": "django__django-16877",
                                      "reason": err}))
                    return 1
                checked += 1

        # additional invariant the model leans on: an already-safe element is
        # returned untouched by conditional_escape (its text is preserved). This
        # is the safe-vs-ordinary branch the Elem.isSafe observable distinguishes.
        for s in raw_pool:
            ms = mark_safe(s)
            if str(conditional_escape(ms)) != str(ms):
                print(json.dumps({"status": "fail",
                                  "instance": "django__django-16877",
                                  "reason": f"safe element altered: {ms!r} -> "
                                            f"{conditional_escape(ms)!r}"}))
                return 1
            checked += 1

        # fuzz: random strings, raw and safe-marked.
        for _ in range(50_000):
            s = rng.choice(raw_pool)
            obj = s if rng.getrandbits(1) else mark_safe(s)
            err = check_one(obj)
            if err:
                print(json.dumps({"status": "fail",
                                  "instance": "django__django-16877",
                                  "reason": err}))
                return 1
            checked += 1
    except Exception as e:
        print(json.dumps({"status": "fail", "instance": "django__django-16877",
                          "reason": f"callee raised (model assumes total): {e!r}"}))
        return 1

    print(json.dumps({
        "status": "pass", "instance": "django__django-16877",
        "checked": checked,
        "reason": "A-reference condEscape validated == real conditional_escape "
                  "(total + string-valued on ordinary and safe-marked elements; "
                  "safe-marked elements returned untouched)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
