#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15103.

This bundle consumes NO @ContractOnly axiom: the modelled behaviour is the
conditional assembly of constant markup around an already-serialized payload
(see model.py / refinement.md). The single soundness obligation that G-AX must
discharge is the REFINEMENT assumption stated in refinement.md: the real wrapper
callees (`format_html` positional interpolation + `mark_safe` on the payload)
preserve exactly the character structure the model assembles, namely

    present id : '<script id="' + element_id + '" type="application/json">'
                 + payload + '</script>'
    absent  id : '<script type="application/json">' + payload + '</script>'

where an identifier counts as present iff it is truthy (non-None, non-empty).

This check therefore validates the model's structural assembly (`build_json_script`,
reproduced below as a list-of-code-points reference) against the REAL post-patch
`django.utils.html.json_script` over boundary cases (no id / empty id / present
id; payloads exercising the JSON-script escapes `> < &`; HTML-special-free ids,
matching the tested usage) plus randomized fuzz. The payload supplied to the
model is exactly the real serialized+escaped JSON string the callee produces, so
the comparison isolates the conditional-wrapping behaviour under change.

Imports Django (the package under test, present in the eval container) + stdlib
only. Exit 0 iff every observation matches the model.
"""
import json
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()

from django.core.serializers.json import DjangoJSONEncoder  # noqa: E402
from django.utils.html import _json_script_escapes, json_script  # noqa: E402


# --- model.py reference encodings (kept in lock-step with the spec) ----------

_TAG_OPEN_WITH_ID = [ord(c) for c in '<script id="']
_ATTR_CLOSE_AND_TYPE = [ord(c) for c in '" type="application/json">']
_TAG_OPEN_NO_ID = [ord(c) for c in '<script type="application/json">']
_TAG_CLOSE = [ord(c) for c in '</script>']


def build_json_script(payload, element_id):
    """Reference implementation of model.py's `build_json_script`, as a list of
    code points. `payload` and `element_id` are lists of code points;
    `element_id` may be None (absent)."""
    present = element_id is not None and len(element_id) > 0
    if present:
        prefix = _TAG_OPEN_WITH_ID + list(element_id) + _ATTR_CLOSE_AND_TYPE
    else:
        prefix = list(_TAG_OPEN_NO_ID)
    return prefix + list(payload) + _TAG_CLOSE


def real_payload(value):
    """The already-serialized, JSON-script-escaped payload the real callee wraps
    (the unchanged `json.dumps(...).translate(_json_script_escapes)` step)."""
    return json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)


def check_one(value, element_id_str):
    """Assert the model's structural assembly == the REAL json_script output."""
    payload = [ord(c) for c in real_payload(value)]
    eid = None if element_id_str is None else [ord(c) for c in element_id_str]
    expected = build_json_script(payload, eid)                     # model
    if element_id_str is None:
        observed_str = json_script(value)                          # real callee
    else:
        observed_str = json_script(value, element_id_str)
    observed = [ord(c) for c in str(observed_str)]
    assert observed == expected, (
        "structural refinement unsound for value=%r id=%r:\n"
        " real json_script -> %r\n model build_json_script -> %r"
        % (value, element_id_str, observed_str,
           "".join(chr(c) for c in expected)))


def main():
    # ids restricted to HTML-special-free tokens (the tested usage): with these,
    # format_html's conditional_escape of the id is the identity, matching the
    # model's literal-id assembly.
    id_alphabet = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                   "0123456789-_")

    # payload values exercising the JSON-script escapes and ordinary content
    values = [
        {}, [], "", "x", 0, 1, True, False, None,
        {"key": "value"},
        {"a": "<script>test&ing</script>"},
        "&<>",
        "a<b>&",
        {"a": "testing\r\njson 'string\" <b>escaping</b>"},
        ["<", ">", "&", "plain"],
        {"nested": {"u": "  "}},
        "quotes \" and ' apostrophe",
    ]

    # --- boundary: absent id, empty id, present id ------------------------
    boundary_ids = [None, "", "test_id", "x", "a", "ID-42", "_priv"]
    n = 0
    for v in values:
        for eid in boundary_ids:
            check_one(v, eid)
            n += 1

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(15103)
    for _ in range(4000):
        v = rng.choice(values)
        choice = rng.randint(0, 2)
        if choice == 0:
            eid = None
        elif choice == 1:
            eid = ""               # empty -> treated as absent
        else:
            m = rng.randint(1, 12)
            eid = "".join(rng.choice(id_alphabet) for _ in range(m))
        check_one(v, eid)
        n += 1

    print("G-AX OK: model build_json_script == real django.utils.html.json_script "
          "(conditional id-attribute wrapping) on %d boundary + fuzz cases "
          "(absent / empty / present id; JSON-script escape payloads)." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
