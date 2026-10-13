#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13933.

This bundle consumes NO `@ContractOnly` axiom. The one operation the modeled
behaviour relies on is the named-mapping ``%``-interpolation performed by the
message machinery when a single-object choice field's invalid-choice error is
rendered (the runtime evaluates ``message % {'value': value}``). That operation
is modeled DEEPLY in model.py's `pure` region by the front-recursive fold
`interpolated`. G-AX validates that DEEP MODEL (the A-reference) against the
REAL Python operation:

    interpolated(template, value)  ==  template % {'value': value}

over its declared domain: message templates whose only ``%``-conversion is the
named placeholder token ``%(value)s`` (Django's error-message templates are
exactly of this form; the rejected value is interpolated as a string). For such
templates, every ``%(value)s`` occurrence is replaced by the string form of the
value and every other character passes through unchanged — which is precisely
what `interpolated` computes.

Domain note (kept sound, documented for the fuzzer): the model does NOT cover
templates containing a bare ``%``, an escaped ``%%``, or any other
``%(...)s`` / ``%s`` conversion — there the real ``%``-operator does something
the model does not claim (escape / raise / a different substitution). The
fuzzer therefore builds inputs whose ONLY ``%``-construct is the placeholder,
matching exactly the domain `interpolated` is specified over. Values likewise
avoid introducing a literal ``%`` (irrelevant once interpolated, since the
substitution is applied to the already-formatted result in one pass — Python's
named mapping does not re-scan the substituted text).

Imports nothing repo-specific: only the standard library. Exit 0 iff every
observation matches the deep model.
"""
import random
import sys

# model.py's placeholder token, as code points: '%(value)s'
PLACEHOLDER = [37, 40, 118, 97, 108, 117, 101, 41, 115]


def interpolated(template, value):
    """Reference re-implementation of model.py's deep model `interpolated`,
    over lists of code points: every %(value)s token -> value, else passthrough.
    """
    out = []
    i = 0
    n = len(template)
    while i < n:
        if i + 9 <= n and template[i:i + 9] == PLACEHOLDER:
            out.extend(value)
            i += 9
        else:
            out.append(template[i])
            i += 1
    return out


def check(template_str, value_str):
    """Assert the deep model == the REAL `str` named-mapping interpolation."""
    real = template_str % {'value': value_str}          # the real operation
    model = "".join(
        chr(c) for c in interpolated(
            [ord(c) for c in template_str],
            [ord(c) for c in value_str],
        )
    )                                                    # the deep model
    assert real == model, (
        "interpolated deep model unsound on template=%r value=%r: "
        "real %%-mapping gave %r, deep model gives %r"
        % (template_str, value_str, real, model))


def main():
    PH = "%(value)s"

    # --- boundary cases ---------------------------------------------------
    boundary_templates = [
        "",
        PH,
        PH + PH,
        PH + PH + PH,
        "a" + PH + "b",
        PH + " at end",
        "start " + PH,
        "no placeholder at all",
        # the literal Django templates touched by this change:
        '"%(value)s" is not one of the available choices.',
        "Select a valid choice. That choice is not one of the available choices.",
        "Select a valid choice. %(value)s is not one of the available choices.",
        "%(value)s IS INVALID CHOICE",
        # placeholder adjacent to a character that begins its byte sequence
        "%(value)s(value)s",
    ]
    # drop any boundary template that contains a stray '%' outside a full token
    def only_token_percents(t):
        i = 0
        while i < len(t):
            if t[i] == '%':
                if t[i:i + 9] == PH:
                    i += 9
                    continue
                return False
            i += 1
        return True

    boundary_templates = [t for t in boundary_templates if only_token_percents(t)]

    boundary_values = ["invalid", "foo", "", "4", "a b c", "X",
                       "<script>", "Joe's", "café", "•", '"quoted"']
    n_boundary = 0
    for t in boundary_templates:
        for v in boundary_values:
            check(t, v)
            n_boundary += 1

    # --- randomized fuzz --------------------------------------------------
    # Build templates by interleaving the placeholder token with random
    # safe characters (no bare '%'), so the only %-construct is %(value)s.
    safe_chars = list("abcXYZ0129 .,;:!?_-=+~@#&<>()[]{}'\"/\\|") + ["é", "•", "→"]
    rng = random.Random(13933)
    n_fuzz = 0
    for _ in range(40000):
        parts = []
        segs = rng.randint(0, 6)
        for _ in range(segs):
            if rng.random() < 0.45:
                parts.append(PH)
            else:
                seglen = rng.randint(0, 5)
                parts.append("".join(rng.choice(safe_chars) for _ in range(seglen)))
        t = "".join(parts)
        assert only_token_percents(t)
        vlen = rng.randint(0, 8)
        # values must not introduce a '%' that the (one-pass) mapping would
        # see; Python applies the mapping once, but keep values %-free to keep
        # the equivalence unambiguous and match real value content.
        vchars = [c for c in safe_chars if c != "%"]
        v = "".join(rng.choice(vchars) for _ in range(vlen))
        check(t, v)
        n_fuzz += 1

    print("G-AX OK: interpolated deep model (== real str %%-mapping with "
          "{'value': ...}) sound on %d boundary + %d fuzz inputs; no consumed "
          "axioms." % (n_boundary, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
