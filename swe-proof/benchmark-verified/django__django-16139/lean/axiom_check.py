#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model `formatFirst` against the REAL
standard-library callee that the changed statement delegates to,
`str.format` (one positional argument, template with a single `{}`).

The proof consumes NO callee axiom (axioms region empty), but the
single-positional-field template substitution is an A-reference (refinement.md
row 3): the Lean `formatFirst` is asserted to agree, character-for-character,
with the real `str.format(repl)` on boundaries + fuzz. This guards the deep
model against drift from the real substitution.

The real template carries exactly one `{}` and no other brace; G-AX fuzzes that
shape (one `{}`, otherwise brace-free text) and brace-free replacement strings,
matching how the modeled function calls `.format`.

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import sys

SEED = 16139


def format_first_model(template: str, repl: str) -> str:
    """The Lean `formatFirst`: replace the FIRST `{}` with repl, rest verbatim;
    no `{}` -> template unchanged."""
    idx = template.find("{}")
    if idx == -1:
        return template
    return template[:idx] + repl + template[idx + 2:]


def main() -> int:
    rng = random.Random(SEED)

    # Brace-free surrounding text alphabet (the real template's chars).
    text_chars = list("abcXYZ <a href=>\"/.0123456789:") + [" "]
    repl_chars = list("../0123456789password/") + [" "]

    cases = []
    # Deterministic boundary cases first.
    cases.append(('<a href="{}">this form</a>', "../../42/password/"))
    cases.append(("{}", ""))
    cases.append(("{}", "../../0/password/"))
    cases.append(("prefix{}suffix", "X"))
    cases.append(("no placeholder here", "ignored"))
    cases.append(("{}", "{}"))   # repl itself may not be a brace pair in reality,
    # but str.format substitutes literally without re-scanning the replacement.

    for _ in range(100_000):
        n = rng.randint(0, 20)
        body = "".join(rng.choice(text_chars) for _ in range(n))
        # Insert exactly one '{}' at a random position (real template shape).
        pos = rng.randint(0, len(body))
        template = body[:pos] + "{}" + body[pos:]
        m = rng.randint(0, 20)
        repl = "".join(rng.choice(repl_chars) for _ in range(m))
        cases.append((template, repl))

    mismatches = 0
    examples = []
    for template, repl in cases:
        try:
            want = template.format(repl)   # REAL callee (one positional arg)
        except (IndexError, KeyError, ValueError):
            # Templates with stray braces are out of the modeled shape; skip.
            continue
        got = format_first_model(template, repl)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append((template, repl, got, want))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs str.format")
        for t, r, g, w in examples:
            print(f"  template={t!r} repl={r!r} model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: formatFirst == str.format (one positional field) on all "
          f"probes (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
