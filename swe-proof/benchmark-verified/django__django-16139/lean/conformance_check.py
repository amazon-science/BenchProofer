#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_passwordHelpText against the patch.diff behaviour (post-patch
help-text computation).

The impl region is NOT all-A-tagged (it has I/R structure: the URL is rebuilt
from pk), so this runs a real fuzz. The single A-reference op (the positional
template substitution) is left as the REAL repo callee `str.format` — exactly
what the changed statement calls. The shadow therefore reproduces the post-patch
behaviour op-for-op; we assert zero disagreements vs an independent
reconstruction of the patched statement over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16139          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(template: str, pk: int) -> str:
    """R/I shadow of implementation_passwordHelpText.

    url := "../../" + str(pk) + "/password/"   (mkUrl; R)
    helpText := template.format(url)            (A-reference: REAL str.format)
    return helpText.
    """
    url = "../../" + str(pk) + "/password/"
    return template.format(url)


def patched(template: str, pk: int) -> str:
    """Independent reconstruction of the post-patch django statement:
    password.help_text = password.help_text.format(f"../../{pk}/password/")."""
    return template.format(f"../../{pk}/password/")


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    text_chars = list("abcXYZ <a href=>\"/.0123456789:") + [" "]

    # Deterministic boundary cases first.
    fixed = [
        ('<a href="{}">this form</a>', 1),
        ('<a href="{}">this form</a>', 0),
        ('<a href="{}">this form</a>', 22222222),
        ("{}", 7),
        ("prefix{}suffix", 123456789012345),
    ]
    cases = list(fixed)
    for _ in range(N):
        n = rng.randint(0, 24)
        body = "".join(rng.choice(text_chars) for _ in range(n))
        pos = rng.randint(0, len(body))
        template = body[:pos] + "{}" + body[pos:]
        pk = rng.choice([
            rng.randint(0, 9),
            rng.randint(10, 9999),
            rng.randint(10 ** 6, 10 ** 12),
        ])
        cases.append((template, pk))

    for template, pk in cases:
        try:
            want = patched(template, pk)
        except (IndexError, KeyError, ValueError):
            continue
        got = shadow(template, pk)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((template, pk, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for t, pk, g, w in examples:
            print(f"  template={t!r} pk={pk} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
