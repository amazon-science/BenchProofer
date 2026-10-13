#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14349 (nagini).

Refutes (does not prove) the refinement leg: does the MODEL agree with the REAL
patched repository function it claims to model?

SHADOW  — the ``# impl-start`` / ``# impl-end`` region of ``model.py``, copied
          VERBATIM with only the contract calls removed (the ``Invariant(...)``
          lines between the ``# invariants-start`` / ``# invariants-end``
          markers).  The model IS Python on this backend, so nothing is
          transliterated or restructured: the shadow is still the same
          index-walking ``while`` loop that raises ``InvalidValue`` on the first
          forbidden code point and otherwise falls through to
          ``downstream_validate(accepted)``.  The ``@Pure`` helper the region
          calls, ``is_forbidden``, is copied over as a plain function (its body
          is already contract-free).  The impl region uses no ``PSeq`` /
          ``ToSeq`` carrier, so no sequence shim is needed; the only Nagini
          carriers here are ``List[int]`` and the user-defined ``InvalidValue``
          exception class, both of which are plain Python.

CALLEE   — ``downstream_validate`` is ``@ContractOnly``: it has no body to copy,
          so this check does NOT stub it with a model.  It calls the REAL repo
          callee the axiom stands for — the UNCHANGED remainder of
          ``URLValidator.__call__`` (scheme split, ``RegexValidator.__call__``
          regex, IDN/punycode retry, IPv6 recheck, host-length check;
          ``django/core/validators.py:107-137`` post-patch, mapping.md §3.1) —
          realized as the real patched ``URLValidator`` instance with the newly
          added guard neutralized (``unsafe_chars = frozenset()``), so a call
          runs exactly the post-guard body and nothing else.  The shim then
          translates that real call's control flow into the axiom's terms
          (returns normally iff it accepted, raises ``InvalidValue`` iff it
          raised ``ValidationError``) and additionally ASSERTS that the real
          outcome matches the ``accepted`` bit the driver bridged in, so the
          axiom is exercised on every input rather than assumed.

ORACLE   — the REAL patched repo function, CALLED, not transliterated:
          ``django.core.validators.URLValidator.__call__``
          (``django/core/validators.py:102`` post-patch, mapping.md §1).  The
          gate applies ``patch.diff`` to /testbed and sets PYTHONPATH before
          this script runs, so ``URLValidator()`` here is the patched class.
          The observable is the three-way call outcome: normal return
          ('accepted'), ``ValidationError`` ('rejected'), or any other escaping
          exception (('crashed', type-name) — a real third outcome of the
          unchanged code, e.g. the ``TypeError`` from ``len(hostname)`` on
          ``"http://?@[::1]"``).

BRIDGE   — mapping.md §2, inverted.  Inputs are generated as concrete ``str``
          values (the repo reality) and mapped to the model carrier by
          ``[ord(c) for c in value]`` (``value[k]`` <-> ``ord(value[k])``, empty
          ``str`` <-> ``[]``); ``InvalidValue`` <-> ``ValidationError``; and the
          model's abstract world-state bit ``accepted`` is obtained by running
          the real unchanged-remainder callee on the same ``str`` (the single
          observable mapping.md §2 assigns it).  Non-``str`` values are outside
          the model's domain by mapping.md §2 (the ``isinstance`` guard is
          explicitly omitted from the model), so only ``str`` is generated.

DOMAIN   — every generated input satisfies ``validate_url``'s ``Requires``:
          ``Acc(list_pred(value), 1/2)`` holds for any freshly built code-point
          list and ``MustTerminate(2)`` is a proof obligation, not an input
          restriction.  One class of input is excluded by the BRIDGE, not by the
          Requires: a forbidden-character-free value on which the real unchanged
          remainder raises something other than ``ValidationError`` has no
          boolean ``accepted`` that faithfully models it (mapping.md §3.1's
          axiom domain is ``{accept -> None, reject -> ValidationError}``).
          Such inputs are counted and REPORTED in the summary line, never
          silently dropped.  Note the same values WITH a forbidden character
          present are kept and checked (the screen raises before the callee is
          reached) — they are exactly the inputs on which the new screen must
          take precedence over a downstream crash, so the branch the gold patch
          added is exercised there too, not routed around.

The input space is infinite (arbitrary ``str``), so the check is boundary cases
first — empty value, singleton values, each of TAB/LF/CR alone, forbidden
character at the first / an interior / the last position, each of the eight
F2P URLs from the test patch, both downstream verdicts (accept and reject) on
forbidden-character-free values, and the downstream-crash family with and
without a forbidden character — then seeded fuzz until >= 1e5 inputs have actually been
CHECKED (the bridge exclusions above are counted separately and cannot erode the
count; the run hard-FAILS if the target is not reached).  Every branch
of the impl region is taken by the boundary block: loop not entered (empty
value), loop body raising (forbidden code point), loop running to completion
then deferring to the callee on both of its outcomes.

Exit 0 iff zero disagreements.  stdlib + django only; seed pinned below and
recorded in mapping.md §G-CONF.
"""
import random
import sys

SEED = 14349
# Target number of CHECKED inputs (boundary + fuzz).  Fuzzing continues until
# this many inputs have actually been compared, so the bridge exclusions below
# cannot silently erode the count; FUZZ_CAP bounds the loop.
N_CHECKED_TARGET = 100_000
FUZZ_CAP = 400_000
MAX_REPORTED = 5

# The three forbidden code points, used ONLY by the driver's bridge/bookkeeping
# (the shadow itself decides via the copied `is_forbidden`).
FORBIDDEN_CHARS = ('\t', '\r', '\n')


class InvalidValue(Exception):
    """model.py's rejection carrier (mapping.md §2: stands in for
    django.core.exceptions.ValidationError)."""
    pass


class AxiomViolation(Exception):
    """Raised if the REAL unchanged-remainder callee disagrees with the
    `accepted` bit bridged in for this input (would mean the mapping.md §2
    bridge, or the callee's determinism, is broken)."""
    pass


# ---------------------------------------------------------------------------
# The real callee behind the @ContractOnly `downstream_validate`, plus the
# per-call context the shim needs (the concrete `str` whose abstract verdict
# `accepted` is).  This lives OUTSIDE the copied impl region.
# ---------------------------------------------------------------------------

_CTX = {"value": None, "structural": None, "patched": None}


def _structural_outcome(value):
    """Run the REAL unchanged remainder of URLValidator.__call__ on `value`
    and report its raw three-way outcome."""
    from django.core.exceptions import ValidationError
    try:
        _CTX["structural"](value)
        return 'accepted'
    except ValidationError:
        return 'rejected'
    except Exception as e:
        return ('crashed', type(e).__name__)


def downstream_validate(accepted):
    """model.py's @ContractOnly callee — no body to copy.  Calls the REAL repo
    callee it axiomatizes (mapping.md §3.1) and reproduces the axiom's control
    flow from that call's actual outcome: return normally iff the real callee
    accepted, raise InvalidValue iff it raised ValidationError.  The `accepted`
    bit is cross-checked against the real outcome, so the axiom is exercised."""
    outcome = _structural_outcome(_CTX["value"])
    if outcome == 'accepted':
        real_accepted = True
    elif outcome == 'rejected':
        real_accepted = False
    else:
        # Outside the axiom's domain; the driver excludes these inputs, so
        # reaching here at all is a bug in this script, not a model finding.
        raise AxiomViolation("real callee produced %r on %r"
                             % (outcome, _CTX["value"]))
    if real_accepted is not accepted:
        raise AxiomViolation("accepted=%r but real callee %r on %r"
                             % (accepted, outcome, _CTX["value"]))
    if real_accepted:
        return None
    raise InvalidValue()


# ---------------------------------------------------------------------------
# model.py `# pure-start` region, verbatim (already contract-free).
# ---------------------------------------------------------------------------


def is_forbidden(c):
    return c == 9 or c == 10 or c == 13


# ---------------------------------------------------------------------------
# model.py `# impl-start` .. `# impl-end`, VERBATIM with the Invariant(...)
# lines (and their markers) stripped.  Nothing else is changed.
# ---------------------------------------------------------------------------


def validate_url(value, accepted):
    # impl-start
    i = 0
    while i < len(value):
        if is_forbidden(value[i]):
            raise InvalidValue()
        i = i + 1
    downstream_validate(accepted)
    # impl-end


# ---------------------------------------------------------------------------
# Bridge + observation
# ---------------------------------------------------------------------------


def shadow_outcome(value, accepted):
    """Drive the shadow over the model carrier and observe the same three-way
    call outcome as the oracle.  `value` is the concrete str; the carrier is
    the code-point list (mapping.md §2)."""
    code_points = [ord(c) for c in value]
    _CTX["value"] = value
    try:
        validate_url(code_points, accepted)
        return 'accepted'
    except InvalidValue:          # <-> ValidationError (mapping.md §2)
        return 'rejected'
    except AxiomViolation:
        raise
    except Exception as e:
        return ('crashed', type(e).__name__)


def oracle_outcome(value):
    """The REAL patched URLValidator.__call__, called."""
    from django.core.exceptions import ValidationError
    validator = _CTX["patched"]
    try:
        validator(value)
        return 'accepted'
    except ValidationError:
        return 'rejected'
    except Exception as e:
        return ('crashed', type(e).__name__)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

BOUNDARY = [
    # empty / singleton / the forbidden code points alone
    "", "\t", "\r", "\n", "\t\r\n", "a", " ",
    # the eight F2P URLs the test patch adds/keeps (forbidden char at the end,
    # in the interior, and right after the scheme; plain and IPv6 hosts)
    "http://www.djangoproject.com/\n",
    "http://[::ffff:192.9.5.5]\n",
    "http://www.djangoproject.com/\r",
    "http://[::ffff:192.9.5.5]\r",
    "http://www.django\rproject.com/",
    "http://[::\rffff:192.9.5.5]",
    "http://\twww.djangoproject.com/",
    "http://\t[::ffff:192.9.5.5]",
    # forbidden char at position 0 / interior / last of an otherwise valid URL
    "\thttp://www.djangoproject.com/",
    "\nhttp://www.djangoproject.com/",
    "\rhttp://www.djangoproject.com/",
    "http://www.djangoproj\nect.com/",
    "http://www.djangoproject.com/\t",
    # forbidden-char-free values: downstream ACCEPTS
    "http://www.djangoproject.com/",
    "https://valid.example.com/path?q=1#frag",
    "ftp://files.example.org/a/b",
    "ftps://secure.example.com/",
    "http://[::ffff:192.9.5.5]",
    "http://localhost:8000/",
    "http://127.0.0.1/",
    "http://[2001:db8::1]/",
    "http://www.djangoéproject.com/",
    # forbidden-char-free values: downstream REJECTS
    "no_scheme", "foo://bar.com", "http://", "javascript:alert(1)",
    "http://www.asdasdasdasdsadfm.com.br ",
    "http://www.asdasdasdasdsadfm.com.br z",
    "http://[::ffff:192.9.5.5",
    "http://" + "a" * 260 + ".com/",
    # near-miss whitespace that must NOT trip the screen
    "http://www.djangoproject.com/\x0b",
    "http://www.djangoproject.com/\x0c",
    "http://www.djangoproject.com/\xa0",
    "http://www.django project.com/",
    # the downstream-CRASH family (hostname None -> TypeError): bridged out
    # when forbidden-char-free, kept when the screen must take precedence
    "http://?@[::1]", "ftp://?@[::1]", "https://?@[::1]",
    "ftp://?q@[::ffff:1.2.3.4]",
    "http://?@[::1]\t", "\nhttp://?@[::1]", "http://?@[:\r:1]",
    # short mixed strings
    "a\tb", "a\rb", "a\nb", "ab", "\t\t", "\r\n",
]

FUZZ_ALPHABET = (list("abcZ09:/.@?#&=-_~ htps[]") + ["é", " ", "\x0b"]
                 + ["\t", "\r", "\n"])

FUZZ_BODIES = [
    "http://www.djangoproject.com/", "https://www.example.com/path?q=1#frag",
    "ftp://files.example.com/a/b", "http://[::ffff:192.9.5.5]",
    "http://localhost:8000/", "http://127.0.0.1/", "no_scheme",
    "foo://bar.com", "http://", "", "http://?@[::1]",
    "http://www.djangoéproject.com/", "http://[::1]",
]


def fuzz_value(rng):
    """Half free-form strings over an alphabet that includes the three
    forbidden characters, half real URL bodies with forbidden / near-miss
    characters injected at random positions (so the screen's branch is hit on
    values the unchanged validator would otherwise ACCEPT — the bpo-43882
    shape the patch exists for)."""
    mode = rng.randint(0, 3)
    if mode == 0:
        k = rng.randint(0, 32)
        return "".join(rng.choice(FUZZ_ALPHABET) for _ in range(k))
    body = list(rng.choice(FUZZ_BODIES))
    if mode == 1:
        for _ in range(rng.randint(1, 3)):
            body.insert(rng.randint(0, len(body)), rng.choice(FORBIDDEN_CHARS))
    elif mode == 2:
        body.insert(rng.randint(0, len(body)),
                    rng.choice([" ", "\x0b", "\x0c", "\xa0", "", "%", "é"]))
    return "".join(body)


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=False, SECRET_KEY="conf-check-14349",
                           USE_I18N=False, USE_TZ=True, DATABASES={},
                           INSTALLED_APPS=[])
        django.setup()
    from django.core.validators import URLValidator

    # The real patched class, twice: once as the oracle (guard active), once
    # with the added guard neutralized to realize the axiomatized unchanged
    # remainder the @ContractOnly callee stands for.
    _CTX["patched"] = URLValidator()
    structural = URLValidator()
    structural.unsafe_chars = frozenset()
    _CTX["structural"] = structural

    rng = random.Random(SEED)

    def value_stream():
        """Boundary cases first, then seeded fuzz until N_CHECKED_TARGET inputs
        have actually been CHECKED (not merely generated)."""
        for v in BOUNDARY:
            yield v
        for _ in range(FUZZ_CAP):
            if checked >= N_CHECKED_TARGET:
                return
            yield fuzz_value(rng)

    checked = 0
    excluded = 0
    branch_raise = 0
    branch_defer_accept = 0
    branch_defer_reject = 0
    branch_empty = 0
    disagreements = []

    for value in value_stream():
        forbidden_present = any(c in value for c in FORBIDDEN_CHARS)
        ds = _structural_outcome(value)
        if not forbidden_present and isinstance(ds, tuple):
            # no boolean `accepted` faithfully models this callee outcome
            excluded += 1
            continue
        accepted = (ds == 'accepted')
        shadow = shadow_outcome(value, accepted)
        oracle = oracle_outcome(value)
        checked += 1
        if forbidden_present:
            branch_raise += 1
        elif not value:
            branch_empty += 1
        elif accepted:
            branch_defer_accept += 1
        else:
            branch_defer_reject += 1
        if shadow != oracle:
            disagreements.append((value, accepted, shadow, oracle))
            if len(disagreements) >= MAX_REPORTED:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d checked inputs "
              "(seed=%d):" % (len(disagreements), checked, SEED))
        for value, accepted, sh, orc in disagreements:
            print("  input=%r accepted=%r shadow=%r oracle=%r"
                  % (value, accepted, sh, orc))
        return 1
    if checked < N_CHECKED_TARGET:
        print("G-CONF FAIL: only %d inputs checked, target %d "
              "(fuzz cap %d exhausted)" % (checked, N_CHECKED_TARGET, FUZZ_CAP))
        return 1
    if min(branch_raise, branch_defer_accept, branch_defer_reject,
           branch_empty) == 0:
        print("G-CONF FAIL: impl branch coverage incomplete "
              "(raise=%d empty=%d defer-accept=%d defer-reject=%d)"
              % (branch_raise, branch_empty, branch_defer_accept,
                 branch_defer_reject))
        return 1
    print("G-CONF OK: model.py impl region (verbatim shadow, @ContractOnly "
          "downstream_validate calling the REAL unchanged remainder) agrees "
          "with the real patched URLValidator.__call__ on all %d checked "
          "inputs (seed=%d, 3-way outcome; branches raise=%d empty=%d "
          "defer-accept=%d defer-reject=%d; %d input(s) excluded: "
          "forbidden-char-free values whose unchanged remainder raises a "
          "non-ValidationError, outside the axiom's 2-valued domain), "
          "0 disagreements."
          % (checked, SEED, branch_raise, branch_empty, branch_defer_accept,
             branch_defer_reject, excluded))
    return 0


if __name__ == "__main__":
    sys.exit(main())
