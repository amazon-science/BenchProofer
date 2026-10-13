#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14349.

Two kind-A obligations (mapping.md §3):

  (A-reference) the deep model `contains_forbidden` (Solution.lean's
      `containsForbidden`/`isForbidden`, pure region) == the REAL new screen
      `bool(frozenset('\\t\\r\\n').intersection(value))`. The changed string
      operation is modeled DEEPLY, not behind a consumed axiom; G-AX validates
      that deep model against the real screen over boundary + fuzz inputs.

  (A-reference) the `baselineOutcome` axiom claims ONLY that the UNCHANGED
      structural validation (the body of `URLValidator.__call__` after the
      `isinstance` guard — scheme/regex/IDN/IPv6/host-length) is a TOTAL,
      DETERMINISTIC function of `value` onto THREE outcomes:
        * accepts — the call returns normally;
        * rejects — it raises `ValidationError` (the designated refusal);
        * crashes — an unrelated error escapes (e.g. the real
          TypeError('object of type NoneType has no len()') at the host-length
          check on inputs like "http://?@[::1]" whose urlsplit().hostname is
          None — a genuine third outcome of the unchanged code, present both at
          base_commit and post-patch).
      It pins NO specific verdict (SPEC_GUIDE directives 7+8). We obtain the
      pure baseline regardless of patch state by neutralizing the added guard
      (`unsafe_chars = frozenset()`), so this runs identically at base_commit
      or with patch.diff applied.

Imports only stdlib + django (the repo under test). Exit 0 iff every obligation
holds.
"""
import random
import sys

FORBIDDEN = frozenset('\t\r\n')


def contains_forbidden(value):
    """Reference impl of Solution.lean's deep model containsForbidden:
    front-recursive per-code-point membership in {\\t,\\r,\\n}."""
    return any(ch in FORBIDDEN for ch in value)


def real_screen(value):
    """The REAL new screen, as a boolean: frozenset('\\t\\r\\n').intersection."""
    return bool(FORBIDDEN.intersection(value))


def make_baseline_validator():
    """A URLValidator whose added forbidden-char guard is neutralized, so a call
    exercises ONLY the unchanged structural validation (the `baselineOutcome`
    abstraction). Robust to patch state: if `unsafe_chars` is absent (base
    commit) the validator already is the baseline; if present (patched) we empty
    it so the guard's `intersection` is always falsy."""
    from django.core.validators import URLValidator
    v = URLValidator()
    if hasattr(v, 'unsafe_chars'):
        v.unsafe_chars = frozenset()
    return v


def baseline_outcome(v, value):
    """The unchanged validation's three-way outcome (Solution.lean's
    BaselineOutcome): 'accepts' (normal return), 'rejects' (ValidationError,
    the designated refusal), 'crashes' (any other exception escapes — e.g. the
    TypeError on hostname=None inputs). Totality = every call lands in one of
    these three classes, which is guaranteed by construction here; what G-AX
    must check is DETERMINISM of the class (same class every call)."""
    from django.core.exceptions import ValidationError
    try:
        v(value)
        return 'accepts'
    except ValidationError:
        return 'rejects'
    except Exception as e:
        return ('crashes', type(e).__name__)


def main():
    significant = ['\t', '\r', '\n']
    ordinary = list("abcZ09:/.@?#&=-_~ htps") + ['é', '[', ']', ':']

    # --- contains_forbidden deep model (A-reference): boundary cases ----------
    boundary = [
        "",
        "http://www.djangoproject.com/",
        "http://www.djangoproject.com/\n",
        "http://[::ffff:192.9.5.5]\n",
        "http://www.djangoproject.com/\r",
        "http://[::ffff:192.9.5.5]\r",
        "http://www.django\rproject.com/",
        "http://[::\rffff:192.9.5.5]",
        "http://\twww.djangoproject.com/",
        "http://\t[::ffff:192.9.5.5]",
        "\t", "\r", "\n", "\t\r\n", "a\tb", "a\rb", "a\nb",
        "no_scheme", "https://example.com",
        "tab\tin\tmiddle", "trailing ", " leading",
    ]
    for ch in significant:
        boundary += [ch, ch + ch, "x" + ch + "y"]

    for s in boundary:
        assert contains_forbidden(s) == real_screen(s), (
            "contains_forbidden deep model unsound on %r: model=%r real=%r"
            % (s, contains_forbidden(s), real_screen(s)))

    # --- contains_forbidden deep model (A-reference): randomized fuzz ---------
    rng = random.Random(14349)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 32)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        assert contains_forbidden(s) == real_screen(s), (
            "contains_forbidden deep model unsound on %r: model=%r real=%r"
            % (s, contains_forbidden(s), real_screen(s)))

    # --- baselineOutcome axiom (A-reference): totality onto 3 classes +
    #     determinism ----------------------------------------------------------
    v = make_baseline_validator()
    # Determinism + totality over a diverse mix of URL-shaped and junk strings,
    # INCLUDING ones with forbidden chars (the neutralized guard lets us probe
    # the unchanged validation on those too) AND the hostname-None crash family
    # ("http://?@[::1]" etc.), where the unchanged host-length check raises
    # TypeError — the axiom's third outcome, which must be deterministic too.
    baseline_inputs = list(boundary) + [
        "http://valid.example.com/path?q=1#frag",
        "ftp://files.example.org/", "ftps://x.example.net/",
        "http://localhost", "http://127.0.0.1:8000/",
        "http://[2001:db8::1]/", "http://user:pass@host.example.com/",
        "http://" + "a" * 300 + ".com",  # over-long host
        "://nohost", "http://", "javascript:alert(1)",
        # hostname-is-None third-outcome family (crashes, base + patched):
        "http://?@[::1]", "ftp://?@[::1]", "https://?@[::1]",
        "ftp://?q@[::ffff:1.2.3.4]", "http://?@[::1]\t",
    ]
    for _ in range(20000):
        n = rng.randint(0, 40)
        baseline_inputs.append("".join(rng.choice(alphabet) for _ in range(n)))

    n_class = {'accepts': 0, 'rejects': 0, 'crashes': 0}
    for s in baseline_inputs:
        r1 = baseline_outcome(v, s)
        r2 = baseline_outcome(v, s)
        assert r1 == r2, (
            "baselineOutcome non-deterministic on %r: %r vs %r" % (s, r1, r2))
        cls = r1 if isinstance(r1, str) else r1[0]
        assert cls in n_class  # totality onto the three modeled outcomes
        n_class[cls] += 1

    # The third outcome must actually be exercised (the crash family above),
    # otherwise this check would silently degenerate to the old 2-way model.
    assert n_class['crashes'] > 0, "crash family never hit the third outcome"

    print("G-AX OK: contains_forbidden deep model (== frozenset('\\t\\r\\n')"
          ".intersection) sound on %d boundary + 20000 fuzz inputs; "
          "baselineOutcome total (3-way: %d accepts / %d rejects / %d crashes)"
          "+deterministic on %d inputs"
          % (len(boundary), n_class['accepts'], n_class['rejects'],
             n_class['crashes'], len(baseline_inputs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
