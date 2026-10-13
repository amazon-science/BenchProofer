#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13933 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List Frag` ↔ the parametrized `%(value)s` message template,
              `List Char` ↔ the offending value `str`). The fold ops
              (`renderFrag`, `++`, the backward `while`) are the I/R legs; the
              deep model's equality to the real interpolation is the A-reference,
              left to G-AX. Here the shadow is the spelled-out per-fragment fold.
  * ORACLE  — `patch.diff`'s behaviour: the gold patch makes `to_python` raise
              `ValidationError(self.error_messages['invalid_choice'],
              code='invalid_choice', params={'value': value})`. What the F2P test
              observes is `exception.messages` — i.e. the rendered message. The
              oracle reproduces exactly that repo path: it constructs the real
              `django.core.exceptions.ValidationError` with `params={'value':
              value}` and reads `.messages[0]` (the value substituted into the
              template's placeholder by `ValidationError.__iter__`).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 13933
N_FUZZ = 100_000

SLOT = ("slot",)


def lit(s):
    return [("lit", c) for c in s]


# --- the R/I shadow: Solution.lean rendered/renderFrag, transliterated ---------
def shadow_render(value, template):
    """`rendered value template` transliterated to str (mapping.md bijection).
    The backward `while` fold of renderInvalidChoice computes exactly this
    left-to-right per-fragment concatenation: a literal contributes its char, a
    value slot is FILLED with the value."""
    out = []
    for frag in template:
        if frag[0] == "lit":
            out.append(frag[1])
        else:  # value slot
            out.append(value)
    return "".join(out)


def template_to_format_string(template):
    """mapping.md bijection: a `List Frag` ↔ a `%(value)s`-style template string.
    A value slot is the named placeholder `%(value)s`; a literal char passes
    through, with a literal '%' doubled to '%%' (printf syntax) so it is never an
    accidental conversion specifier — the real `error_messages['invalid_choice']`
    a developer writes is exactly such a printf template."""
    parts = []
    for frag in template:
        if frag[0] == "lit":
            parts.append("%%" if frag[1] == "%" else frag[1])
        else:
            parts.append("%(value)s")
    return "".join(parts)


# --- the oracle: patch.diff's behaviour via the REAL repo path -----------------
def oracle_render(value, template):
    """patch.diff's behaviour: the gold `to_python` raises
    `ValidationError(template, code='invalid_choice', params={'value': value})`
    and the test observes `exception.messages`. Reproduce that exact repo path
    using the real django ValidationError."""
    from django.core.exceptions import ValidationError
    fmt = template_to_format_string(template)
    err = ValidationError(fmt, code="invalid_choice", params={"value": value})
    return err.messages[0]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    f2p = lit('"') + [SLOT] + lit('" is not one of the available choices.')
    yield ("invalid", f2p)
    yield ("4", f2p)
    yield ("invalid", [SLOT])              # placeholder alone -> exactly value
    yield ("4", [SLOT])
    yield ("4", lit("INVALID CHOICE"))     # PASS_TO_PASS: no placeholder, verbatim
    yield ("x", lit("Select a valid choice. That choice is not one of the available choices."))
    yield ("", [])                         # empty template, empty value
    yield ("", [SLOT])
    yield ("x", [])
    yield ("V", [SLOT] + lit(" tail"))     # leading
    yield ("V", lit("head ") + [SLOT])     # trailing
    yield ("V", [SLOT] + lit(" and ") + [SLOT])   # repeated
    yield ("V", lit("a") + [SLOT] + lit("b") + [SLOT] + lit("c"))
    yield ("100% done", f2p)               # value with percent
    yield ("a%(value)sb", [SLOT])          # value that looks like a placeholder
    yield ("<script>", f2p)
    yield ("Joe's", f2p)
    yield ("é•", f2p)

    lit_alphabet = list("aZ0 ;#x39271quotlgmp\"'<>&%()s") + ["é", "•"]
    val_alphabet = list("aZ0 %()valus\"'<>&") + ["é", "•"]
    for _ in range(n):
        tlen = rng.randint(0, 16)
        template = []
        for _ in range(tlen):
            if rng.random() < 0.30:
                template.append(SLOT)
            else:
                template.append(("lit", rng.choice(lit_alphabet)))
        vlen = rng.randint(0, 12)
        value = "".join(rng.choice(val_alphabet) for _ in range(vlen))
        yield (value, template)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for value, template in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_render(value, template)
        oracle = oracle_render(value, template)
        if shadow != oracle:
            disagreements.append((template_to_format_string(template), value, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fmt, v, sh, orc in disagreements:
            print("  template=%r value=%r shadow=%r oracle=%r" % (fmt, v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderInvalidChoice agrees with patch.diff "
          "behaviour (real ValidationError(...).messages with params={'value': "
          "value}) on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
