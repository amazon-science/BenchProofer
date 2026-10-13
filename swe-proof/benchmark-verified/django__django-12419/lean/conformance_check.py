#!/usr/bin/env python3
"""G-CONF for django__django-12419.

The gold patch is already applied to /testbed when this runs (so the global
default SECURE_REFERRER_POLICY == 'same-origin'). We compare the R/I Python
shadow of `implementation_referrerPolicy` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched resolution of
`settings.SECURE_REFERRER_POLICY` — read exactly as
`django.middleware.security.SecurityMiddleware` reads it
(`self.referrer_policy = settings.SECURE_REFERRER_POLICY`) — over >=1e5 fuzzed
inputs. Zero disagreements => exit 0.

Type bijection (mapping.md):
  projectSetting : Option (Option String)
                                <->  whether settings.SECURE_REFERRER_POLICY is
                                     left at its built-in default (OUTER None =>
                                     not overridden in settings) vs. pinned by
                                     the project to a value (which itself may be
                                     None or a policy string)
  result         : Option String <->  settings.SECURE_REFERRER_POLICY (None or str)

stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

from django.test import override_settings

# The post-patch built-in default of the setting. We assert the container is
# actually patched (defensive: G-CONF must run against the fixed tree).
BUILTIN_DEFAULT = getattr(settings, "SECURE_REFERRER_POLICY", "MISSING")


def oracle(project_setting):
    """Real patched behavior: read settings.SECURE_REFERRER_POLICY exactly as the
    security middleware does, under a settings context that either leaves it at
    its built-in default or pins it.

    project_setting:  ("default",) | ("set", None | str)
    Returns: None | str
    """
    if project_setting[0] == "default":
        return settings.SECURE_REFERRER_POLICY
    else:
        with override_settings(SECURE_REFERRER_POLICY=project_setting[1]):
            return settings.SECURE_REFERRER_POLICY


def shadow(project_setting):
    """R/I transliteration of implementation_referrerPolicy (Lean).

    projectSetting : Option (Option String) -> project_setting tuple above
    """
    setting = BUILTIN_DEFAULT  # defaultReferrerPolicy (the post-fix 'same-origin')
    if project_setting[0] != "default":
        setting = project_setting[1]  # `some v => setting := v`
    return setting                    # `return setting`


POLICY_POOL = [
    None, "same-origin", "origin", "no-referrer", "strict-origin",
    "origin,no-referrer-when-downgrade", "same-origin, origin",
    "unsafe-url", "no-referrer-when-downgrade", "strict-origin-when-cross-origin",
    "",
]


def rand_policy(rng):
    return rng.choice(POLICY_POOL)


def main():
    rng = random.Random(12419)  # pinned seed (mapping.md)
    if BUILTIN_DEFAULT != "same-origin":
        print("G-CONF FAIL: container not patched; SECURE_REFERRER_POLICY=%r "
              "(expected 'same-origin')" % (BUILTIN_DEFAULT,))
        return 1
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        # project setting: leave at built-in default, or pin to None / a policy
        if rng.random() < 0.5:
            project_setting = ("default",)
        else:
            project_setting = ("set", rand_policy(rng))
        o = oracle(project_setting)
        s = shadow(project_setting)
        if o != s:
            disagreements += 1
            if first is None:
                first = (project_setting, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
