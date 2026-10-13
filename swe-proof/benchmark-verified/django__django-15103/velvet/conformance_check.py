#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15103 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (`List Char` ↔ `str`; empty identifier `[]` ⟺ a falsy
              `element_id`). The modeled function `jsonScriptTag` decides ONLY
              which template is used and how the (already-encoded payload,
              already-escaped identifier) are spliced into it; both of those
              inputs are abstracted (R) and computed here with the UNCHANGED
              repo helpers, exactly as the gold patch does, then the modeled
              `wrapNoId` / `wrapWithId` concatenation is applied.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.utils.html.json_script` applied at base_commit (the real
              correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.

CALLEE ABSTRACTION: the JSON encoder
(`json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)`) and
the identifier escaper (`conditional_escape`, inside `format_html`) are UNCHANGED
by the patch and identical on both sides of the fix. They are abstracted as the
`content` / `identifier` inputs (mapping.md §3) and computed with the real
helpers here — there is no axiom and no axiom_check.py.
"""
import random
import sys

SEED = 15103
N_FUZZ = 100_000


def _ensure_settings():
    """DjangoJSONEncoder / format_html resolve lazily against settings; make sure
    a minimal configuration exists when run outside the test harness."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_TZ=True,
            USE_I18N=False,
            DEBUG=False,
        )
    try:
        import django
        django.setup()
    except Exception:
        pass


# --- the R/I shadow: Solution.lean wrapNoId/wrapWithId, transliterated --------

_OPEN_PLAIN = '<script type="application/json">'
_SCRIPT_CLOSE = '</script>'


def _open_with_id(identifier):
    # openWithId identifier = '<script id="' ++ identifier ++ '" type="application/json">'
    return '<script id="' + identifier + '" type="application/json">'


def shadow_json_script(value, element_id):
    """jsonScriptTag transliterated to str over the real repo types.

    `content` (abstracted, R): the unchanged JSON-encode + escape of the payload.
    `identifier` (abstracted, R): the unchanged escape of element_id.
    The MODELED change is the branch on the empty identifier and the two
    template concatenations wrapNoId / wrapWithId."""
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    from django.utils.html import _json_script_escapes, conditional_escape
    from django.utils.safestring import mark_safe

    json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    content = str(mark_safe(json_str))            # abstracted payload (R)

    # truthiness bridge (mapping.md §2): identifier = [] iff element_id falsy.
    if not element_id:
        # wrapNoId content = openPlain ++ content ++ scriptClose
        return _OPEN_PLAIN + content + _SCRIPT_CLOSE
    else:
        identifier = str(conditional_escape(element_id))   # abstracted id (R)
        # wrapWithId identifier content = openWithId id ++ content ++ scriptClose
        return _open_with_id(identifier) + content + _SCRIPT_CLOSE


def oracle_json_script(value, element_id):
    """patch.diff's behaviour: the patched django json_script()."""
    from django.utils.html import json_script
    if element_id is _UNSET:
        return str(json_script(value))            # exercise the new default arg
    return str(json_script(value, element_id))


_UNSET = object()


def fuzz_cases(n, rng):
    # payloads spanning the JSON value space (incl. chars that trigger the
    # _json_script_escapes translate: < > &).
    payloads = [
        {}, [], "", 0, 1, -1, True, False, None,
        {"key": "value"},
        {"a": "testing\r\njson 'string\" <b>escaping</b>"},
        {"</script>": "<x>&y</x>"},
        [1, 2, {"n": "<a&b>"}],
        "plain string",
        "x<y>z&w",
        12345,
        3.5,
        {"nested": {"deep": ["a", "<b>", "&c"]}},
    ]
    # identifiers: the falsy branch (None, "", and the new no-arg default) and
    # the truthy branch (varied strings, incl. ones needing HTML escaping).
    falsy_ids = [None, "", _UNSET]
    truthy_ids = [
        "test_id", "a", "x-1", "myId", "el id", "id&<>\"'",
        "<script>", "0", "False",
    ]

    # boundary cases first (plan §4.1 step 4): every payload x every id kind.
    for p in payloads:
        for eid in falsy_ids:
            yield (p, eid)
        for eid in truthy_ids:
            yield (p, eid)

    # randomized fuzz
    id_alphabet = list("abcXYZ0-_ <>&\"'")
    for _ in range(n):
        p = rng.choice(payloads)
        kind = rng.randint(0, 2)
        if kind == 0:
            eid = rng.choice(falsy_ids)
        else:
            k = rng.randint(1, 16)
            eid = "".join(rng.choice(id_alphabet) for _ in range(k))
            # a random string of only spaces is still truthy in Python; keep it.
        yield (p, eid)


def main():
    _ensure_settings()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for value, element_id in fuzz_cases(N_FUZZ, rng):
        count += 1
        try:
            o = oracle_json_script(value, element_id)
        except Exception as e:
            print("G-CONF ERROR: oracle raised on value=%r element_id=%r: %r"
                  % (value, element_id, e))
            return 1
        # shadow uses the same falsy semantics; map the _UNSET default to None
        # (the patched default is element_id=None, so no-arg ⟺ element_id=None).
        eid_for_shadow = None if element_id is _UNSET else element_id
        s = shadow_json_script(value, eid_for_shadow)
        if s != o:
            disagreements.append((value, element_id, s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for value, eid, s, o in disagreements:
            print("  value=%r element_id=%r shadow=%r oracle=%r" % (value, eid, s, o))
        return 1
    print("G-CONF OK: R/I shadow of jsonScriptTag agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements. JSON encoder and "
          "identifier escaper abstracted as content/identifier inputs."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
