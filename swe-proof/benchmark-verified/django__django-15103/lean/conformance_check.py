#!/usr/bin/env python3
"""G-CONF for django__django-15103.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_scriptTag` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `json_script`, over >=1e5
fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): the returned script-tag string is

    "<script id=\\"" + escapeId(id) + "\\" type=\\"application/json\\">" + body + "</script>"   (id truthy)
    "<script type=\\"application/json\\">" + body + "</script>"                                  (id falsy)

where `body` is the safe JSON body (independent of the id) and `escapeId` is the
attribute escaping that format_html applies to the substituted id. The fix
selects WHICH frame is emitted, keyed on the truthiness of element_id.

  * Oracle  = the REAL patched `django.utils.html.json_script`.
  * Shadow  = branch on (id != "" / not None), then assemble the literal frame
              around the REAL body step and the REAL escaped id.

To keep the shadow honest about ONLY the R/I content (branch selection + literal
framing), the abstract A-reference steps are bound to the real repo behavior:
  - jsonBody(value): the real json.dumps+translate+mark_safe pipeline, obtained by
    rendering the with-id frame once and slicing out the body; this keeps the body
    byte-identical to whatever the oracle produced for the same value.
  - escapeId(id):   the real format_html attribute escaping, obtained the same way.

Type bijection (mapping.md): optId<->element_id (""/None falsy), value<->value,
result<->returned str. stdlib-only; no hypothesis required.
"""
import json
import random
import sys

# --- configure Django settings before importing the html machinery ----------
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

from django.utils.html import json_script, format_html
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

# _json_script_escapes is module-private but stable; re-import for the body step.
from django.utils.html import _json_script_escapes


def oracle(value, element_id):
    """Behavior of the patched repo function for these inputs."""
    return str(json_script(value, element_id))


def _real_body(value):
    """The REAL unchanged body step (A-reference op #1)."""
    json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    return str(mark_safe(json_str))


def _real_escape_id(element_id):
    """The REAL attribute escaping format_html applies to the substituted id
    (A-reference). Obtained by substituting the id alone into a 1-placeholder
    template and reading it back."""
    out = str(format_html('{}', element_id))
    return out


def shadow(value, element_id):
    """R/I transliteration of implementation_scriptTag (Lean).

    Op 1 (A-reference): the real JSON body step.
    Op 2 (R): branch on id truthiness (None / "" => falsy).
    Op 3/4 (I + A-reference): literal frame around escaped id + body.
    """
    body = _real_body(value)
    # optId != "" in Lean; None and "" are both the falsy/absent id in Python.
    if element_id:
        esc = _real_escape_id(element_id)
        return '<script id="' + esc + '" type="application/json">' + body + '</script>'
    else:
        return '<script type="application/json">' + body + '</script>'


VALUE_POOL = [
    {}, {"key": "value"}, {"a": "<b>&'\""}, [1, 2, 3], "plain",
    "<script>", "a & b", '"quoted"', "it's", 42, 3.14, True, False, None,
    {"nested": {"x": [1, "<y>", None]}}, "", "100% sure",
    {"html": "<a href='x'>&amp;</a>"}, ["<", ">", "&", '"', "'"],
]

ID_POOL = [
    None, "", "test_id", "my-id", "x", "a b", "id<script>", "a&b",
    'q"uote', "it's", "<>&\"'", "123", "_under", "dash-dash",
]


def rand_id(rng):
    n = rng.randint(0, 8)
    alpha = "ab<>&\"' /=cD0_-"
    return "".join(rng.choice(alpha) for _ in range(n))


def main():
    rng = random.Random(15103)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        value = rng.choice(VALUE_POOL)
        if rng.random() < 0.6:
            element_id = rng.choice(ID_POOL)
        else:
            element_id = rand_id(rng)
        o = oracle(value, element_id)
        s = shadow(value, element_id)
        if o != s:
            disagreements += 1
            if first is None:
                first = (value, element_id, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
