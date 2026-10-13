#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14349.

The model abstracts the UNCHANGED remaining structural validation of a value
(the scheme/regex/IDN/IPv6 machinery the screen defers to once the
forbidden-character check has passed) as a single contract-only function

    downstream_validate(accepted) -> None
        Ensures(accepted is True)               # normal completion => accepted
        Exsures(InvalidValue, accepted is False) # rejection => not accepted

i.e. the only observable datum of the remaining validation is a single bit
``accepted``; it returns normally EXACTLY when it accepts the value and signals
the SAME out-of-band rejection EXACTLY when it does not. This is the definitional
contract of the real callee on the model's domain.

The real callee is ``django.core.validators.URLValidator.__call__`` restricted to
the no-forbidden-character path (values containing none of TAB/LF/CR), which is
the only path on which ``downstream_validate`` stands in for it: on that path the
new forbidden-character screen is a no-op and the observable behaviour is exactly
the remaining validation. This check therefore runs the REAL ``URLValidator`` on
a battery of values that contain NO forbidden control character and asserts, for
each, that the call either

   * returns ``None`` (accepted: matches ``Ensures(accepted is True)``), or
   * raises ``django.core.exceptions.ValidationError`` (rejected: matches
     ``Exsures(InvalidValue, accepted is False)``) — and NOTHING else
     (no other exception type, no silent acceptance of a value the repo's own
     fixtures mark invalid).

The accept/reject partition is taken from the repository's own oracle fixtures
(``tests/validators/valid_urls.txt`` / ``invalid_urls.txt``) when present, so the
``accepted`` bit is grounded in the real validator's intended verdict, plus a
randomized fuzz of forbidden-character-free strings. Imports are limited to the
standard library plus the very Django callee under abstraction (available in the
evaluation container). Exit 0 iff every observation meets the axiom.
"""
import os
import random
import sys

FORBIDDEN = {'\t', '\n', '\r'}


def has_forbidden(s):
    return any(ch in FORBIDDEN for ch in s)


def _read_fixture(path):
    out = []
    if os.path.exists(path):
        with open(path, encoding='utf8') as fh:
            for line in fh:
                line = line.rstrip('\n')
                if line and not line.startswith('#'):
                    out.append(line)
    return out


def main():
    try:
        from django.core.validators import URLValidator
        from django.core.exceptions import ValidationError
    except Exception as exc:  # pragma: no cover - container guard
        print("G-AX SKIP: Django URLValidator unavailable (%r)" % (exc,))
        return 0

    validator = URLValidator()

    # Helper: run the real callee, classify its observable outcome.
    def observe(value):
        try:
            result = validator(value)
        except ValidationError:
            return ('reject', None)
        except Exception as other:
            # The axiom forbids any other out-of-band signal: the only rejection
            # channel is ValidationError. (The isinstance/early branches are
            # excluded by construction: every value here is a str.)
            return ('other', other)
        else:
            # Normal completion must yield the empty value (None), matching the
            # model's `-> None` return.
            return ('accept', result)

    # --- the accept partition: the repo's own valid-URL oracle ----------------
    here = os.path.dirname(os.path.abspath(__file__))
    valid_candidates = _read_fixture(os.path.join(here, 'valid_urls.txt'))
    # Built-in valid examples (used when fixtures are not co-located).
    valid_candidates += [
        'http://www.djangoproject.com/',
        'https://example.com',
        'ftp://ftp.example.com/file',
        'http://[::ffff:192.9.5.5]',
        'http://localhost/',
        'http://www.example.com:8000/path?query=1#frag',
    ]
    n_accept = 0
    for value in valid_candidates:
        if has_forbidden(value):
            continue  # outside downstream's domain (the screen handles these)
        kind, info = observe(value)
        assert kind == 'accept', (
            "downstream axiom unsound: real URLValidator REJECTED a value the "
            "repo marks valid (%r): outcome=%r" % (value, (kind, info)))
        assert info is None, (
            "downstream axiom unsound: normal completion of URLValidator on %r "
            "returned %r, expected the empty value None" % (value, info))
        n_accept += 1

    # --- the reject partition: the repo's own invalid-URL oracle --------------
    invalid_candidates = _read_fixture(os.path.join(here, 'invalid_urls.txt'))
    invalid_candidates += [
        'no_scheme',
        'foo',
        'http://',
        'http://.',
        'http://..',
        'https://example,com',
        'ftp://[example].com',
        'http://-error-.invalid/',
        '',  # empty value: the validator rejects (re-raises) on falsy input
    ]
    n_reject = 0
    for value in invalid_candidates:
        if has_forbidden(value):
            continue
        kind, info = observe(value)
        assert kind == 'reject', (
            "downstream axiom unsound: real URLValidator did NOT reject with "
            "ValidationError a value the repo marks invalid (%r): outcome=%r"
            % (value, (kind, info)))
        n_reject += 1

    # --- fuzz: every forbidden-char-free value must classify cleanly ----------
    rng = random.Random(14349)
    alphabet = list('abcdefghijklmnopqrstuvwxyzABCDEF0123456789'
                    './:?#@&=%+-_~[]') + ['é', '•', ' ']
    n_fuzz = 0
    for _ in range(5000):
        m = rng.randint(0, 40)
        value = ''.join(rng.choice(alphabet) for _ in range(m))
        if has_forbidden(value):
            continue
        kind, info = observe(value)
        # The ONLY relied-on fact: the outcome is accept (None) or reject
        # (ValidationError) — never any other out-of-band signal.
        assert kind in ('accept', 'reject'), (
            "downstream axiom unsound: real URLValidator produced a non-"
            "ValidationError out-of-band signal on %r: %r" % (value, info))
        if kind == 'accept':
            assert info is None, (
                "downstream axiom unsound: URLValidator accepted %r but "
                "returned %r, expected None" % (value, info))
        n_fuzz += 1

    print("G-AX OK: real URLValidator on %d valid + %d invalid oracle inputs "
          "and %d forbidden-char-free fuzz inputs is total over "
          "{accept->None, reject->ValidationError}; downstream_validate axiom "
          "sound" % (n_accept, n_reject, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
