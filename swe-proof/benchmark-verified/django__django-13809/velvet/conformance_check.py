#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13809.

Refutes (does not prove) the R/I refinement leg of `runStartupChecks`'s impl:
the modeled gating of the two startup effect observables by the request flag —
  announced := (not skipChecks);  checked := (not skipChecks)
realized by `if not skipChecks: announced := true; checked := true`.

REFINEMENT STRUCTURE / no A leg:
  The two effects whose occurrence is observed — the progress announcement write
  and the system-check routine invocation — are modeled DIRECTLY as boolean
  state writes (occurrence flags), not behind any consumed callee contract. The
  routine pins only WHETHER each effect happens, governed by the one request
  flag; it asserts nothing about the announcement's text or the check routine's
  result. So the impl region is pure R/I and there is no A-tagged callee to hold
  out — this is a real (non-skip) G-CONF.

ORACLE CHOICE — why we transliterate the patched source guard rather than run
`inner_run`:
  The gating happens inside `Command.inner_run(self, *args, **options)` of
  django/core/management/commands/runserver.py. Reaching it for real means
  binding a socket and starting a live development server (the `run(...)` call
  right after the guard blocks indefinitely), plus a fully-initialized command
  with stdout/settings. The F2P test itself mocks `check`, `check_migrations`
  and the server `run` to observe ONLY the two effects this bundle models. So,
  per the worker prompt, the ORACLE is the patched source guard transliterated
  VERBATIM:
      if not options['skip_checks']:
          self.stdout.write('Performing system checks...\\n\\n')  # announced
          self.check(display_num_errors=True)                    # checked
  i.e. each effect occurs exactly when `not options['skip_checks']`. The SHADOW
  is Solution.lean's `runStartupChecks` post-image transliterated. We
  differential-test SHADOW vs ORACLE over both boolean values of `skip_checks`
  (exhaustive) plus seeded fuzz. Exit 0 iff zero disagreements. stdlib only.

This mirrors the F2P test `ManageRunserver.test_skip_checks`:
  skip_checks=True  -> 'Performing system checks...' NOT written, check() NOT called
  skip_checks=False -> 'Performing system checks...' written,     check() called
"""
import random
import sys

SEED = 13809
N_FUZZ = 100_000


def shadow(skip_checks):
    """runStartupChecks post-image transliterated: from entry state
    (announced=False, checked=False), the `if not skipChecks` branch sets both
    to True; otherwise both stay False. Net: each observable == (not skip)."""
    announced = False
    checked = False
    if not skip_checks:
        announced = True
        checked = True
    return announced, checked


def oracle(skip_checks):
    """The patched inner_run guard, transliterated verbatim from
    django/core/management/commands/runserver.py (gold-patched):
        if not options['skip_checks']:
            self.stdout.write('Performing system checks...\\n\\n')  # announced
            self.check(display_num_errors=True)                    # checked
    `announced` records that the announcement was written; `checked` records
    that the check routine was invoked. Both happen iff not skip_checks."""
    announced = False
    checked = False
    if not skip_checks:
        announced = True   # self.stdout.write("Performing system checks...")
        checked = True     # self.check(display_num_errors=True)
    return announced, checked


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: both boolean values of skip_checks.
    combos = [False, True]
    # Plus seeded fuzz (redundant coverage; the prompt asks for fuzz).
    combos += [rng.random() < 0.5 for _ in range(N_FUZZ)]

    for skip in combos:
        count += 1
        s = shadow(skip)
        o = oracle(skip)
        if s != o:
            disagreements.append((skip, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of runStartupChecks agrees with the patched "
          "inner_run guard on %d inputs (2 exhaustive + fuzz, seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
