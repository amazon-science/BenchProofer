#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13933 (A-reference).

This bundle consumes NO axiom. The one operation that genuinely changes — the
rendering of a parametrized rejection message, i.e. filling the offending value
into the message's value placeholder — is modeled DEEPLY in Solution.lean by
`rendered`/`renderFrag` (the per-fragment fold over `List Frag`). G-AX validates
that deep model against the REAL string-interpolation the gold patch enables.

The real behavior (django/core/exceptions.py, `ValidationError.__iter__`):

    message = error.message
    if error.params:
        message %= error.params      # post-patch: params={'value': value}
    yield str(message)

So once `params={'value': value}` is supplied (the gold change), the rendered
message is exactly the printf-style interpolation `template % {'value': value}`,
which substitutes every `%(value)s` placeholder with `str(value)` and passes
literal text through. The pre-patch raised the error with NO params, so the
template was yielded verbatim (placeholder left standing).

The A-reference G-AX establishes:

    rendered(value, template)  ==  render_template % {'value': value}

where `template` is a `List Frag` whose `valueSlot` fragments correspond to the
`%(value)s` placeholders of `render_template` and whose `lit c` fragments are the
literal code points. Boundary cases (placeholder alone, leading/trailing/repeated
placeholders, no placeholder, empty template, empty value, value containing
significant characters) plus randomized fuzzing.

Imports nothing repo-specific: printf-style `%` interpolation is a Python builtin
— the same operation `ValidationError.__iter__` performs. stdlib only. Exit 0 iff
every observation matches the deep model. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 13933

# --- the deep model `rendered`/`renderFrag`, transliterated --------------------
# A fragment is either ('lit', ch) or ('slot',). A template is a list of frags.
# `rendered(value, template)` concatenates the per-fragment renderings: a literal
# contributes its one character, a value slot is FILLED with the value string.


def rendered(value, template):
    """Reference of Solution.lean's deep model `rendered` (str carrier)."""
    out = []
    for frag in template:
        if frag[0] == "lit":
            out.append(frag[1])
        else:  # ('slot',)
            out.append(value)
    return "".join(out)


def template_to_format_string(template):
    """The `%(value)s`-style printf template that the `List Frag` corresponds to
    under the mapping.md bijection: a value slot is the placeholder `%(value)s`,
    a literal char passes through (with `%` doubled to `%%` so it is a literal in
    printf syntax, never an accidental conversion specifier)."""
    parts = []
    for frag in template:
        if frag[0] == "lit":
            parts.append("%%" if frag[1] == "%" else frag[1])
        else:
            parts.append("%(value)s")
    return "".join(parts)


def check(value, template):
    """Assert the deep model == the REAL printf-style interpolation builtin
    (the operation `ValidationError.__iter__` runs once params are supplied)."""
    fmt = template_to_format_string(template)
    real = fmt % {"value": value}            # the REAL interpolation builtin
    model = rendered(value, template)        # the deep model
    assert real == model, (
        "rendered deep model unsound: template=%r value=%r real=%r model=%r"
        % (fmt, value, real, model))


def lit(s):
    return [("lit", c) for c in s]


SLOT = ("slot",)


def main():
    # The actual gold-patch / F2P template and value (the public example).
    f2p_template = lit('"') + [SLOT] + lit('" is not one of the available choices.')
    checks = [
        # F2P case: the value placeholder exposes the offending value.
        ("invalid", f2p_template),
        # placeholder alone -> exactly the value
        ("invalid", [SLOT]),
        ("4", [SLOT]),
        # no placeholder -> verbatim literal (PASS_TO_PASS: 'INVALID CHOICE')
        ("4", lit("INVALID CHOICE")),
        ("anything", lit("Select a valid choice. That choice is not one of the available choices.")),
        # empty template, empty value
        ("", []),
        ("", [SLOT]),
        ("x", []),
        # leading / trailing / repeated placeholders
        ("V", [SLOT] + lit(" tail")),
        ("V", lit("head ") + [SLOT]),
        ("V", [SLOT] + lit(" and ") + [SLOT]),
        ("V", lit("a") + [SLOT] + lit("b") + [SLOT] + lit("c")),
        # value carrying significant characters (incl. percent, which printf
        # would mis-handle if substituted into the format rather than as a param)
        ("100% done", f2p_template),
        ("a%(value)sb", [SLOT]),     # value itself looks like a placeholder
        ("<script>", f2p_template),
        ("Joe's", f2p_template),
        ("é•", f2p_template),
    ]
    for value, template in checks:
        check(value, template)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(SEED)
    lit_alphabet = list("aZ0 ;#x39271quotlgmp\"'<>&%()s") + ["é", "•"]
    val_alphabet = list("aZ0 %()valus\"'<>&") + ["é", "•"]
    for _ in range(50000):
        tlen = rng.randint(0, 16)
        template = []
        for _ in range(tlen):
            if rng.random() < 0.30:
                template.append(SLOT)
            else:
                template.append(("lit", rng.choice(lit_alphabet)))
        vlen = rng.randint(0, 12)
        value = "".join(rng.choice(val_alphabet) for _ in range(vlen))
        check(value, template)

    print("G-AX OK: rendered deep model (== printf-style `template %% "
          "{'value': value}`, the interpolation ValidationError.__iter__ runs "
          "once params are supplied) sound on %d boundary + 50000 fuzz inputs."
          % len(checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
