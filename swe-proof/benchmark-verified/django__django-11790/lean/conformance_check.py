#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_authUsernameField against the patch.diff behaviour (the
post-patch username-field configuration block in AuthenticationForm.__init__).

The impl region is R/I (no A-tagged ops), so this runs a real fuzz. The shadow
reproduces the Lean impl op-for-op:
  umax = usernameMaxLength(configured_max)            # R: `max_length or 254`
  field.max_length = umax                             # I
  field.widget.attrs['maxlength'] = umax              # I
We diff against an independent reconstruction of the patched Python block over
>=10^5 fuzzed (configured_max, init_attrs) inputs (including attribute maps that
already carry a 'maxlength', to exercise overwrite + frame).

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 11790          # pinned in mapping.md
N = 120_000           # >= 10^5


def username_max_length(configured_max):
    """R: Lean `usernameMaxLength`. Python `max_length or 254` truthiness:
    None and 0 are falsy -> 254; a positive int -> itself."""
    if configured_max is None or configured_max == 0:
        return 254
    return configured_max


def shadow(configured_max, init_attrs):
    """R/I shadow of implementation_authUsernameField.

    Returns (max_length, attrs) where attrs is the integer-valued attribute map
    after configuration.
    """
    umax = username_max_length(configured_max)
    attrs = dict(init_attrs)            # field widget attrs carrier
    max_length = umax                   # op 3
    attrs['maxlength'] = umax           # op 4
    return max_length, attrs


def patched_block(configured_max, init_attrs):
    """Independent reconstruction of the post-patch Python block:
        username_max_length = self.username_field.max_length or 254
        self.fields['username'].max_length = username_max_length
        self.fields['username'].widget.attrs['maxlength'] = username_max_length
    """
    username_max = (configured_max or 254)
    attrs = dict(init_attrs)
    field_max_length = username_max
    attrs['maxlength'] = username_max
    return field_max_length, attrs


def random_attrs(rng):
    """A small integer-valued attribute map; sometimes already has 'maxlength'."""
    keys = ["size", "tabindex", "minlength", "maxlength", "cols", "rows"]
    out = {}
    for _ in range(rng.randint(0, 4)):
        out[rng.choice(keys)] = rng.randint(0, 1000)
    return out


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        (None, {}),
        (0, {}),
        (1, {}),
        (254, {}),
        (255, {}),
        (255, {"maxlength": 10}),       # preexisting maxlength -> overwrite
        (None, {"maxlength": 99}),
        (0, {"size": 30}),
        (128, {"size": 30, "tabindex": 1}),
        (None, {"size": 5, "maxlength": 5}),
    ]
    cases = fixed + [
        (
            rng.choice([None, 0] + list(range(1, 300)) + [254, 255, 1000, 2**31]),
            random_attrs(rng),
        )
        for _ in range(N)
    ]

    for cm, attrs in cases:
        got = shadow(cm, attrs)
        want = patched_block(cm, attrs)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((cm, attrs, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for cm, a, g, w in examples:
            print(f"  configured_max={cm!r} attrs={a!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
