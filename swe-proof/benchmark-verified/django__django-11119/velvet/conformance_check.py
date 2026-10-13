#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11119 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `valueToDisplay` impl
              region transliterated to Python over the real repo types
              (`Bool` ↔ engine.autoescape, `List Char` ↔ str), via the
              mapping.md bijection. The escape (the A-reference `escapedSeq`) is
              an R/I leg for G-CONF, so it is transliterated here; its equality
              to the real callee is G-AX's job. The surrounding fixed template
              text `obj:` / `\n` is the I (identity) passthrough of the literal
              TextNodes (mapping.md §2).
  * ORACLE  — `patch.diff`'s behaviour: the patched `Engine.render_to_string`
              run through an in-memory (locmem) loader on the `obj:{{ obj }}\n`
              template, over BOTH engine autoescape settings (the real
              correctness oracle, G-RESOLVE).

They must agree on every input × both autoescape settings. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 11119
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean entity/escapedSeq, transliterated ---------
# entity (c : Char) : List Char  -- per-code-point substitution, legacy '&#39;'.
_ENTITY = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
}


def shadow_escape(text):
    """escapedSeq (text.toList) transliterated to str (the per-code-point
    concatenation the backward `while` fold computes)."""
    return "".join(_ENTITY.get(ch, ch) for ch in text)


def shadow_render(encode_markup, value):
    """The R/I shadow of `valueToDisplay`, wrapped by the fixed template literal
    `obj:` ... `\n` (the I passthrough of the TextNodes). This is the rendered
    output Solution.lean's spec pins."""
    display = shadow_escape(value) if encode_markup else value
    return "obj:" + display + "\n"


# --- the oracle: patched Engine.render_to_string -----------------------------
def _make_engine(autoescape):
    from django.template.engine import Engine
    # In-memory loader so render_to_string resolves the template without a
    # filesystem dir; the loader/template content is fixed and unchanged by the
    # patch — only the autoescape threading differs.
    return Engine(
        loaders=[
            ('django.template.loaders.locmem.Loader', {
                'test_context.html': 'obj:{{ obj }}\n',
            }),
        ],
        autoescape=autoescape,
    )


def oracle_render(autoescape, value):
    """patch.diff's behaviour: patched render_to_string threads
    Context(context, autoescape=self.autoescape)."""
    engine = _make_engine(autoescape)
    return engine.render_to_string('test_context.html', {'obj': value})


def fuzz_inputs(n, rng):
    significant = list(_ENTITY.keys())
    ordinary = list("aZ0 ;#x39271quotlgmpscri") + ["é", "•"]
    alphabet = significant + ordinary
    # boundary cases first (plan §4.1 step 4)
    yield ""
    for c in significant:
        yield c
        yield c + c
    yield "".join(significant)
    yield "".join(reversed(significant))
    yield "a&b<c>d\"e'f"
    yield "<script>"                      # exact F2P value
    yield "<script>alert('xss')</script>"
    yield "x=1&amp;y=&lt;2&gt;"
    yield "Joe's Crab Shack"
    yield "Can't find my keys"
    yield "!$&'()*+,;=~:@,"
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            TEMPLATES=[],
            USE_TZ=False,
            USE_L10N=False,
        )
    django.setup()


def main():
    _setup_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        for autoescape in (True, False):
            count += 1
            shadow = shadow_render(autoescape, s)
            oracle = oracle_render(autoescape, s)
            if shadow != oracle:
                disagreements.append((autoescape, s, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d renders:"
              % (len(disagreements), count))
        for ae, s, sh, orc in disagreements:
            print("  autoescape=%r input=%r shadow=%r oracle=%r"
                  % (ae, s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of valueToDisplay agrees with patch.diff "
          "render_to_string behaviour on %d renders (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
