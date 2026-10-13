#!/usr/bin/env python3
"""G-CONF for django__django-11119.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_renderToString` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`Engine.render_to_string`, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): for a template that is literal text framing a single
interpolated value (`obj:{{ obj }}\\n` => leading "obj:", trailing "\\n"), the
rendered output is

    leading + render_value_in_context(value, context) + trailing

where the only thing the downstream value-rendering step reads off the context is
its `autoescape` flag. The fix selects that flag as: the supplied context's own
flag when a ready-made Context is passed, else the engine's configured flag.

  * Oracle  = the REAL patched `Engine.render_to_string` rendering the template.
  * Shadow  = leading + renderValue(eff, value) + trailing, where
              eff = suppliedCtxAutoescape if suppliedIsContext else engineAutoescape,
              and renderValue is the REAL `render_value_in_context` callee
              (the A-reference op #3) applied to a context carrying `eff`.

Type bijection (mapping.md): engineAutoescape<->Engine.autoescape (bool),
suppliedIsContext<->isinstance(context, Context) (bool),
suppliedCtxAutoescape<->context.autoescape (bool), value<->the data value (str),
result<->rendered output (str).
stdlib-only; no hypothesis required.
"""
import os
import random
import sys
import tempfile

# --- configure Django settings before importing the template machinery -------
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

from django.template import Context
from django.template.engine import Engine
from django.template.base import render_value_in_context

# Template framing a single interpolated value, mirroring tests' test_context.html.
TEMPLATE_TEXT = "obj:{{ obj }}\n"
LEADING = "obj:"
TRAILING = "\n"

_tmpdir = tempfile.mkdtemp(prefix="gconf_11119_")
with open(os.path.join(_tmpdir, "t.html"), "w") as f:
    f.write(TEMPLATE_TEXT)


def oracle(engine_autoescape, supplied_is_context, supplied_ctx_autoescape, value):
    """Behavior of the patched repo function for these inputs."""
    engine = Engine(dirs=[_tmpdir], autoescape=engine_autoescape)
    if supplied_is_context:
        ctx = Context({"obj": value}, autoescape=supplied_ctx_autoescape)
        return engine.render_to_string("t.html", ctx)
    else:
        return engine.render_to_string("t.html", {"obj": value})


def shadow(engine_autoescape, supplied_is_context, supplied_ctx_autoescape, value):
    """R/I transliteration of implementation_renderToString (Lean).

    Op 1/2: select the effective escaping flag.
    Op 3 (A-reference): apply the REAL render_value_in_context value step.
    Op 4/5: frame with the unchanged literal text.
    """
    autoescape = supplied_ctx_autoescape
    if not supplied_is_context:
        autoescape = engine_autoescape
    # renderValue eff value  <->  real render_value_in_context with that flag.
    step_ctx = Context({}, autoescape=autoescape)
    rendered_value = render_value_in_context(value, step_ctx)
    return LEADING + rendered_value + TRAILING


VALUE_POOL = [
    "<script>", "a & b", '"quoted"', "it's", "<b>x</b>",
    "plain", "", "<>&\"'", "&amp;", "a<b>c&d", "100% sure",
    "no markup here", "<a href='x'>", "& < > \" '",
]


def rand_str(rng):
    n = rng.randint(0, 8)
    alpha = "ab<>&\"' /=cD0 "
    return "".join(rng.choice(alpha) for _ in range(n))


def main():
    rng = random.Random(11119)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        engine_autoescape = rng.choice([True, False])
        supplied_is_context = rng.choice([True, False])
        supplied_ctx_autoescape = rng.choice([True, False])
        value = rng.choice(VALUE_POOL) if rng.random() < 0.6 else rand_str(rng)
        o = oracle(engine_autoescape, supplied_is_context, supplied_ctx_autoescape, value)
        s = shadow(engine_autoescape, supplied_is_context, supplied_ctx_autoescape, value)
        if o != s:
            disagreements += 1
            if first is None:
                first = (engine_autoescape, supplied_is_context,
                         supplied_ctx_autoescape, value, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
