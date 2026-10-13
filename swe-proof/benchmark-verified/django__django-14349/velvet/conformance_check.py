#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14349 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch,
              CallOutcome ↔ {return normally, raise ValidationError, other
              exception escapes}). The control flow is
              `if containsForbidden value: rejected else: liftBaseline(baselineVerdict)`.
              The A-tagged callee `baselineOutcome` is NOT replaced by a model:
              G-CONF leaves it as the REAL unchanged validator's three-way
              outcome (run the real post-`isinstance` body, with the new guard
              neutralized) — the A leg stays with G-AX; here it is a shared
              subroutine on both sides.
  * ORACLE  — `patch.diff`'s behaviour: the patched `URLValidator.__call__`,
              observed as 'rejected' (raise ValidationError) / 'accepted'
              (normal return) / ('crashed', exc-type) (any other exception —
              e.g. the TypeError on hostname-None inputs like
              "http://?@[::1]", a real third outcome of the unchanged code).

They must agree (same three-way outcome, incl. the escaping exception's type on
crashes) on every input. Exit 0 iff zero disagreements; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with patch.diff
applied), stdlib + django only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 14349
N_FUZZ = 100_000
FORBIDDEN = frozenset('\t\r\n')


# --- the R/I shadow: Solution.lean isForbidden/containsForbidden + control flow
def contains_forbidden(value):
    """containsForbidden (value.toList) transliterated: per-code-point
    membership in {\\t,\\r,\\n} (isForbidden), front-recursive OR."""
    return any(ch in FORBIDDEN for ch in value)


def _baseline_validator():
    """The unchanged validation as a real callee (A-tagged): a URLValidator with
    the added forbidden-char guard neutralized, so a call exercises ONLY the
    structural scheme/regex/IDN/IPv6/host-length validation."""
    from django.core.validators import URLValidator
    v = URLValidator()
    if hasattr(v, 'unsafe_chars'):
        v.unsafe_chars = frozenset()
    return v


def baseline_outcome(v, value):
    """The unchanged validation's three-way outcome = Solution.lean's
    baselineOutcome, already lifted through liftBaseline into observable
    call-outcome terms (mapping.md §2): accepts→'accepted', rejects→'rejected',
    crashes→('crashed', exc-type)."""
    from django.core.exceptions import ValidationError
    try:
        v(value)
        return 'accepted'
    except ValidationError:
        return 'rejected'
    except Exception as e:
        return ('crashed', type(e).__name__)


def shadow_outcome(v, value):
    """outcome = if containsForbidden value then CallOutcome.rejected
    else liftBaseline baselineVerdict (mapping.md A2/A3).
    baselineVerdict = real unchanged validation's three-way outcome."""
    if contains_forbidden(value):
        return 'rejected'
    return baseline_outcome(v, value)


# --- the oracle: patch.diff's behaviour (the real patched __call__) ----------
def oracle_outcome(value):
    from django.core.validators import URLValidator
    from django.core.exceptions import ValidationError
    validator = URLValidator()  # patched: includes the unsafe_chars guard
    try:
        validator(value)
        return 'accepted'
    except ValidationError:
        return 'rejected'
    except Exception as e:
        return ('crashed', type(e).__name__)


def fuzz_inputs(n, rng):
    significant = list(FORBIDDEN)
    ordinary = list("abcZ09:/.@?#&=-_~ htps[]") + ["é"]
    alphabet = significant + ordinary
    # boundary cases first (plan §4.1 step 4) — incl. the F2P matrix and the
    # hostname-None crash family (third outcome)
    fixed = [
        "", "http://www.djangoproject.com/",
        "http://www.djangoproject.com/\n", "http://[::ffff:192.9.5.5]\n",
        "http://www.djangoproject.com/\r", "http://[::ffff:192.9.5.5]\r",
        "http://www.django\rproject.com/", "http://[::\rffff:192.9.5.5]",
        "http://\twww.djangoproject.com/", "http://\t[::ffff:192.9.5.5]",
        "\t", "\r", "\n", "\t\r\n",
        "no_scheme", "https://valid.example.com/",
        "ftp://files.example.org/", "http://localhost",
        "http://valid.example.com/path?q=1#frag",
        "http://[2001:db8::1]/", "a\tb", "a\rb", "a\nb",
        # hostname-is-None crash family: baseline crashes; with a forbidden
        # char prepended/appended the screen must win (rejected, no crash)
        "http://?@[::1]", "ftp://?@[::1]", "https://?@[::1]",
        "ftp://?q@[::ffff:1.2.3.4]", "http://?@[::1]\t", "\nhttp://?@[::1]",
    ]
    for s in fixed:
        yield s
    for _ in range(n):
        k = rng.randint(0, 32)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    v = _baseline_validator()
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_outcome(v, s)
        oracle = oracle_outcome(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of validateUrl agrees with patch.diff "
          "behaviour (3-way outcome) on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
