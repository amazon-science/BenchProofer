#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9320 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` <-> `str`, `[]` <-> `''`,
              `Except Unit (List Char)` <-> accept-with-value / turn-away). The
              impl region is:

                  if entry = [] then accept []
                  else if strictAccepts entry then submit it and accept the value
                  else turn away

              so the shadow decides acceptance from the two MODELED PRIMITIVES
              (`pathIsDir (pathExpanded entry)` <-> `isdir(guarded_expansion(
              entry))`, both TOTAL — the expansion is read through the guard the
              model puts in the term, mapping.md §1.1 — and both R) and only then
              performs the SUBMISSION, which is the A-tagged op and therefore runs
              the REAL repo callee `is_path` (mapping.md §3 leaves A-tagged ops as
              the real callee).

              Note what this does NOT do, because a previous revision's blindness
              here is exactly what a spec-too-weak finding turned on: it does not
              hardcode the gold call order and then delegate. The decision is
              recomputed from the primitives, and the submission happens where —
              and only where — the impl region performs one. So the invocation
              pattern is observable to this gate (see SUBMISSION ORDER below).
  * ORACLE   — `patch.diff`'s behaviour: the patched
              `sphinx.cmd.quickstart.is_path_or_empty` applied at base_commit
              (the real correctness oracle, G-RESOLVE).

Five things are checked, and one is recorded:

  OUTCOMES (must agree on every input IN the obligation's domain) — accept-with-
    value vs turn-away vs ESCAPE (control leaving the modeled function for a
    reason that is not its own refusal). OUT of the domain the outcomes are
    deliberately NOT compared, and the reason is a modeling fact rather than a
    convenience: the real function does not come back there, while every read the
    modeled impl performs is GUARDED and therefore total, so the shadow comes back
    with a turn-away. That is precisely what the `require` excuses — the spec
    claims no outcome for those entries — and comparing there would be asserting
    something the spec does not say. The claim that replaces it is asserted in its
    place, on every out-of-domain input: THE SHADOW MUST COME BACK. Both edges of
    the domain are asserted separately and in both directions (below), so nothing
    about the boundary rests on the comparison.
  THE GUARDED READ IS FREE (must hold on every input) — the model lets a program
    read the expansion at ANY entry, including one it derives from its own input,
    because what it reads is the guarded expansion. Two measurements, on every
    input: reading it at the derived entry `'~' + NUL + entry` — an argument the
    method's `require` says nothing about, and the shape that broke a previous
    revision of this spec, where the expansion had a TOTAL FUNCTION TYPE and the
    read refined to a bare `expanduser` that RAISES — must hand an answer back;
    and the pos-derived-probe-guarded impl (properties.py), which is the frozen
    impl plus exactly that read, must be observationally identical to the frozen
    impl, same outcome and same submission count.
  AN EARNED DERIVED SUBMISSION COMES BACK (must hold on every input, and must
    actually fire) — the guard makes `strictAccepts entry = true →
    expansionAnswers entry = true` a theorem, so an impl may SUBMIT an entry it
    derived from its own input inside the branch that shows that derived entry
    accepted. pos-derived-submission-earned is run as a third shadow: its extra
    submission of `'~' + entry` must come back, must leave the outcome unchanged,
    and must add exactly one submission where the branch fires. How often it fired
    is counted and asserted NON-ZERO, because a branch that never fires would
    agree with anything.
  THE DOMAIN IS EXACTLY RIGHT (must hold on every input) — the modeled method
    carries `require expansionAnswers entry = true`, whose repo counterpart is
    "asking for `path.expanduser(entry)` hands an answer back at all". Two
    assertions pin that boundary from both sides:
      * IN the domain the oracle must come back — either with a value or with the
        `ValidationError` the call site catches — and must never ESCAPE. If it
        escaped, the domain would be too SMALL: an input the spec governs would
        have a third outcome the spec cannot express.
      * OUT of the domain the oracle must NOT come back at all — neither a value
        nor a `ValidationError`. If it came back, the domain would be too LARGE:
        the `require` would be excusing an input whose outcome is perfectly
        specifiable, i.e. gratuitously weakening the obligation.
    Together these say the `require` names precisely the entries on which the
    real patched function has one of the two modeled outcomes.
  SUBMISSION ORDER (must agree on the discriminating input) — with `is_path`
    instrumented by a counting wrapper, BOTH sides must submit the empty entry
    ZERO times, and both must submit an ACCEPTED entry exactly once. That is the
    control-flow content of the change: the empty entry is accepted without ever
    being handed to the strict validator.
  DISCLOSED ASYMMETRY (recorded, not asserted) — for a NON-empty entry that is
    not accepted, the oracle submits once (and the raise propagates) while the
    shadow submits zero times (it decides first). The OUTCOME is identical, which
    is the R obligation; the difference is the deliberate modeling asymmetry of
    refinement.md §C — a raise inside the modeled function is control not coming
    back, so the modeled impl must decide before it submits. The same pattern
    appears out of domain (the oracle submits and the expansion escapes through
    the callee; the shadow reads the GUARDED expansion, decides against the entry
    and never submits), where it is likewise counted.

Every input is bucketed into out-of-domain / in-domain-accepted /
in-domain-refused and each bucket is asserted NON-EMPTY at the end: an alphabet
with no NUL and no high surrogate in it never reaches the first bucket and would
therefore agree with a spec whose domain is wrong. That is why the boundary list
and the fuzz alphabet carry both.

Exit 0 iff zero outcome disagreements, zero domain-boundary violations, zero
guarded-read drifts and zero submission-order violations; any disagreement is a
mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib + the repo only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import os
import random
import sys
import tempfile
from os import path as _ospath

SEED = 9320
N_FUZZ = 100_000


def _load_quickstart():
    from sphinx.cmd import quickstart as qs
    return qs


class Counter:
    """`is_path` wrapped so every SUBMISSION is observable to this gate."""

    def __init__(self, real):
        self.real = real
        self.n = 0

    def __call__(self, x):
        self.n += 1
        return self.real(x)


def expansion_answers(entry):
    """The repo counterpart of the method's `require expansionAnswers entry =
    true`: asking for the home-directory expansion of `entry` hands an answer
    back at all. It does not for an entry beginning with `~` whose first segment
    cannot be looked up — a NUL makes `pwd.getpwnam` raise ValueError, a high
    surrogate UnicodeEncodeError, and `expanduser` catches only KeyError."""
    try:
        _ospath.expanduser(entry)
        return True
    except BaseException:             # noqa: BLE001 - anything else is 'no answer'
        return False


def _escape(exc):
    """Control leaving for a reason that is not the validator's own refusal,
    described tightly enough that the two sides have to escape the SAME way."""
    return ('escape', type(exc).__name__, str(exc))


def guarded_expansion(entry):
    """The repo counterpart of `pathExpanded entry` — the GUARDED expansion, which
    is what the modeled impl may freely read (mapping.md §1.1): the expansion where
    it answers, the empty entry where it does not. TOTAL by construction, and that
    is the point: in the model the escape lives in `rawExpansion`, which cannot be
    read without a proof that the entry answers, so no read the impl region
    performs — at its own entry or at one it derives — can take control away."""
    if expansion_answers(entry):
        return _ospath.expanduser(entry)
    return ''


def strict_accepts(entry):
    """The modeled decision, from the two modeled primitives (R): the directory
    test applied to the GUARDED expansion. `isdir` is total and so is the guarded
    expansion, so this is free — it answers for every entry, including entries
    derived from the method's input, and takes control away from nobody. On the
    obligation's domain the guarded expansion IS the expansion, so there this is
    `isdir(expanduser(entry))` verbatim, which is gold's own test."""
    return _ospath.isdir(guarded_expansion(entry))


def shadow_validate(qs, entry):
    """The shadow of optionalPathValidator's impl region:
        if entry == '':            accept ''                 -- R/I, no submission
        elif strictAccepts entry:  submit it, accept the value -- A: real is_path
        else:                      turn away                 -- R/I, no submission
    Returns ('ok', value), ('error',) or an ('escape', ...) triple. It should never
    escape at all: the decision is a guarded read and the submission only happens
    where the entry is accepted. An escape here is a finding, and the main loop
    reports it as one."""
    if entry == '':
        return ('ok', '')
    try:
        accepted = strict_accepts(entry)
    except BaseException as exc:      # noqa: BLE001 - a guarded read must not
        return _escape(exc)           #   escape; reported as modeling drift
    if accepted:
        try:
            return ('ok', qs.is_path(entry))
        except qs.ValidationError:
            # unreachable if fact (3) holds; G-AX owns that, so surface it here
            # as a disagreement rather than swallowing it
            return ('error-unexpected',)
        except BaseException as exc:  # noqa: BLE001 - likewise a disagreement
            return _escape(exc)
    return ('error',)


def shadow_derived_probe(qs, entry):
    """The impl region of pos-derived-probe-guarded (properties.py): the frozen
    impl with a read of the guarded expansion at an entry DERIVED from its own
    input — `'~' + NUL + entry` — in front of the empty-entry arm, ignored.

    This is the shape a recorded G-EQ attack used to break the previous revision,
    where the expansion had a TOTAL FUNCTION TYPE and the read refined to a bare
    `path.expanduser('~\\x00' + entry)` that RAISES. Refined through the guard it
    is behaviourally invisible, and that is asserted here on every input rather
    than argued: this shadow must agree with the oracle exactly where the frozen
    shadow does."""
    if entry == '':
        _ = _ospath.isdir(guarded_expansion('~\x00' + entry))   # read, ignored
        return ('ok', '')
    return shadow_validate(qs, entry)


def shadow_derived_submission(qs, entry):
    """The impl region of pos-derived-submission-earned (properties.py): the frozen
    impl, but in the empty-entry arm it SUBMITS an entry it derived from its own
    input — `'~' + entry` — inside the branch where it has shown that derived entry
    accepted, then discards what came back.

    That submission is earned rather than assumed: in the model the branch
    hypothesis `strictAccepts ('~' :: entry) = true` yields domain membership
    through the derived theorem `accepted_in_domain`. Here the same implication is
    what makes the submission SAFE — `path.isdir` of the guarded expansion is true
    only where the expansion answered — so `is_path` of that entry returns instead
    of escaping. Unlike the read probe this branch is LIVE (at `entry == ''` the
    derived entry is `'~'`, which expands to the home directory), so the main loop
    counts how often it fired and asserts it fired at all.

    Returns `(outcome, extra_submissions)` — the outcome in the same shape as the
    frozen shadow, plus how many submissions this impl makes that the frozen one
    does not, so the main loop can hold the submission count to account instead of
    guessing it from the outcome."""
    if entry == '':
        derived = '~' + entry
        if _ospath.isdir(guarded_expansion(derived)):
            _ = qs.is_path(derived)          # earned submission, value discarded
            return (('ok', ''), 1)
        return (('ok', ''), 0)
    return (shadow_validate(qs, entry), 0)


def oracle_validate(qs, entry):
    """patch.diff's behaviour: the patched is_path_or_empty()."""
    try:
        return ('ok', qs.is_path_or_empty(entry))
    except qs.ValidationError:
        return ('error',)
    except BaseException as exc:      # noqa: BLE001 - the third outcome
        return _escape(exc)


def fuzz_inputs(n, rng, existing):
    # boundary cases first (plan §4.1 step 4)
    yield ''
    yield '.'
    yield '..'
    yield '/'
    yield ' '
    yield '\t'
    yield 'a'
    yield '~'
    yield '~/'
    yield 'definitely_not_a_real_path_zzz'
    yield '~nonexistent_user_zzz'
    yield '~root'
    # OUT of the obligation's domain: a `~` whose first segment cannot be looked
    # up at all, so the expansion escapes instead of answering. Plus their
    # in-domain NEIGHBOURS — the same characters away from a leading `~` segment,
    # and a LOW surrogate, which the lookup accepts and merely fails to find —
    # because the pair is what shows the domain tracks the real boundary rather
    # than 'the entry contains an odd character'.
    for x in ('~\x00', '~\x00abc', '~\x00/x', '~\ud800', '~\ud800abc',
              '\x00', 'a\x00b', '\x00~', '~/\x00', '\ud800',
              '~\udcff', '~\udcffabc', '\udcff'):
        yield x
    for e in existing:
        yield e
    chars = list("abcZ0 ./~\t\\:;-_") + ["é", "•", "\x00", "\ud800", "\udcff"]
    for _ in range(n):
        r = rng.random()
        if r < 0.15:
            yield ''                      # exercise the empty branch often
            continue
        if r < 0.25:
            # tilde-prefixed, so the out-of-domain region is reached by
            # construction and not only by luck
            k = rng.randint(0, 8)
            yield "~" + "".join(rng.choice(chars) for _ in range(k))
            continue
        if rng.random() < 0.4:
            base = rng.choice(existing)
            tail = "".join(rng.choice(chars) for _ in range(rng.randint(0, 4)))
            yield base if rng.random() < 0.5 else os.path.join(base, tail)
        else:
            k = rng.randint(0, 16)
            yield "".join(rng.choice(chars) for _ in range(k))


def main():
    qs = _load_quickstart()
    rng = random.Random(SEED)
    counter = Counter(qs.is_path)
    qs.is_path = counter                 # both sides now submit through it
    disagreements = []
    order_violations = []
    domain_violations = []
    drift = []
    asymmetric = 0
    out_asymmetric = 0
    count = 0
    derived_reads = 0
    derived_submissions = 0
    seen = {'out-of-domain': 0, 'in-domain-accepted': 0, 'in-domain-refused': 0}
    try:
        with tempfile.TemporaryDirectory() as d:
            sub = os.path.join(d, 'sub')
            os.mkdir(sub)
            existing = [d, sub, os.path.expanduser('~'), os.getcwd()]
            for s in fuzz_inputs(N_FUZZ, rng, existing):
                count += 1
                counter.n = 0
                shadow = shadow_validate(qs, s)
                shadow_submits = counter.n
                counter.n = 0
                oracle = oracle_validate(qs, s)
                oracle_submits = counter.n
                # --- THE DERIVED READ IS INVISIBLE, AND IT IS TOTAL -------
                # (a) the pos-derived-probe-guarded shape must be observationally
                # identical to the frozen impl on EVERY input, in the domain and
                # out of it: adding a guarded read changes nothing that can be
                # seen. (b) the read itself, at an argument the method's `require`
                # says nothing about, must hand an answer back every time.
                counter.n = 0
                try:
                    probe = shadow_derived_probe(qs, s)
                except BaseException as exc:      # noqa: BLE001
                    probe = _escape(exc)
                if counter.n != shadow_submits or probe != shadow:
                    drift.append(
                        (s, 'a guarded read at the DERIVED entry %r changed the '
                            'observable behaviour (%r vs %r, %d submissions vs '
                            '%d), so it is not the free read mapping.md §1.1 '
                            'licenses' % ('~\x00' + s, probe, shadow, counter.n,
                                          shadow_submits)))
                try:
                    _ = _ospath.isdir(guarded_expansion('~\x00' + s))
                    derived_reads += 1
                except BaseException as exc:      # noqa: BLE001
                    drift.append(
                        (s, 'reading the guarded expansion at the derived entry '
                            '%r took control away (%s: %s)'
                            % ('~\x00' + s, type(exc).__name__, exc)))
                # (c) an EARNED submission of a derived entry (pos-derived-
                # submission-earned) must come back and must not change the
                # outcome. `accepted_in_domain` is why: the branch only fires
                # where the derived entry's guarded expansion names a directory,
                # which can only happen where the expansion answered.
                counter.n = 0
                try:
                    sub_outcome, extra = shadow_derived_submission(qs, s)
                except BaseException as exc:      # noqa: BLE001
                    sub_outcome, extra = _escape(exc), 0
                if (sub_outcome != shadow
                        or counter.n - shadow_submits != extra):
                    drift.append(
                        (s, 'submitting the DERIVED entry %r inside the branch that '
                            'shows it accepted changed the observable behaviour '
                            '(%r vs %r, %d submissions vs %d, %d of them expected '
                            'to be extra), so the submission `accepted_in_domain` '
                            'licenses is not the one the real callee answers'
                            % ('~' + s, sub_outcome, shadow, counter.n,
                               shadow_submits, extra)))
                else:
                    derived_submissions += extra
                if len(drift) >= 5:
                    break
                # --- IS THE DOMAIN EXACTLY RIGHT? -------------------------
                in_domain = expansion_answers(s)
                if not in_domain:
                    seen['out-of-domain'] += 1
                    if oracle[0] != 'escape':
                        domain_violations.append(
                            (s, 'OUT of the domain but the oracle came back as '
                                '%r, so the domain is too LARGE — the `require` '
                                'excuses a specifiable input' % (oracle,)))
                    # The two sides part company here, by construction rather than
                    # by accident, and the outcomes are deliberately NOT compared:
                    # the oracle does not come back (asserted just above), while
                    # every read the modeled impl performs is GUARDED and therefore
                    # total, so the shadow comes back with a turn-away. That is
                    # exactly what the `require` excuses — the spec claims no
                    # outcome here — and comparing would assert something the spec
                    # does not say. What IS asserted is the modeling claim that
                    # replaces it: the shadow must not escape, anywhere, ever.
                    if shadow[0] == 'escape':
                        drift.append(
                            (s, 'the shadow ESCAPED (%s: %s), but every read the '
                                'modeled impl performs is guarded and total, so '
                                'mapping.md §1.1 is not being followed here'
                                % (shadow[1], shadow[2])))
                    if shadow_submits == 0 and oracle_submits == 1:
                        out_asymmetric += 1
                    if shadow_submits > 1 or oracle_submits > 1:
                        order_violations.append(
                            (s, 'an out-of-domain entry submitted more than once',
                             shadow_submits, oracle_submits))
                    if len(domain_violations) >= 5 or len(drift) >= 5:
                        break
                    continue
                if shadow != oracle:
                    disagreements.append((s, shadow, oracle))
                    if len(disagreements) >= 5:
                        break
                if oracle[0] == 'escape':
                    domain_violations.append(
                        (s, 'IN the domain but the oracle did not come back (%s: '
                            '%s), so the domain is too SMALL — the spec governs '
                            'an input with a third outcome it cannot express'
                            % (oracle[1], oracle[2])))
                    if len(domain_violations) >= 5:
                        break
                    continue
                # --- SUBMISSION ORDER (in the domain) ---------------------
                # Past this point `strict_accepts` cannot escape, and not merely
                # by luck: the entry is non-empty and the oracle came back, so the
                # oracle ran `is_path`, so the expansion answered for this entry.
                if s == '':
                    if shadow_submits or oracle_submits:
                        order_violations.append(
                            (s, 'empty entry submitted to the strict validator',
                             shadow_submits, oracle_submits))
                elif strict_accepts(s):
                    seen['in-domain-accepted'] += 1
                    if shadow_submits != 1 or oracle_submits != 1:
                        order_violations.append(
                            (s, 'accepted entry not submitted exactly once',
                             shadow_submits, oracle_submits))
                else:
                    seen['in-domain-refused'] += 1
                    # the disclosed asymmetry (refinement.md §C): the oracle
                    # submits and lets the raise propagate; the shadow decides
                    # first and never submits. Outcomes agree, which is the
                    # obligation, and BOTH patterns are faithful here — so this
                    # is counted, not asserted. Only an impossible pattern (more
                    # than one submission of the same entry) is a violation.
                    if shadow_submits == 0 and oracle_submits == 1:
                        asymmetric += 1
                    if shadow_submits > 1 or oracle_submits > 1:
                        order_violations.append(
                            (s, 'a non-accepted entry submitted more than once',
                             shadow_submits, oracle_submits))
                if len(order_violations) >= 5 or len(domain_violations) >= 5:
                    break
    finally:
        qs.is_path = counter.real
    # --- the domain boundary is only measured if BOTH sides of it were reached --
    empty_regions = [r for r, n in seen.items() if n == 0]
    # An earned derived submission that never fired would make the check above
    # agree with anything, so its liveness is part of the verdict.
    if not drift and derived_submissions == 0:
        drift.append(
            ('', 'the EARNED derived submission never fired in this run, so it '
                 'measured nothing; pos-derived-submission-earned submits `\'~\' + '
                 'entry` at the empty entry, which should be accepted here'))
    if (disagreements or order_violations or domain_violations or drift
            or empty_regions):
        print("G-CONF FAIL over %d inputs: %d outcome disagreement(s), %d "
              "domain-boundary violation(s), %d submission-order violation(s), "
              "%d guarded-read drift(s), %d unreached region(s) %r:"
              % (count, len(disagreements), len(domain_violations),
                 len(order_violations), len(drift), len(empty_regions), seen))
        for s, sh, orc in disagreements:
            print("  outcome  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        for s, why in domain_violations:
            print("  domain   input=%r %s" % (s, why))
        for s, why in drift:
            print("  read     input=%r %s" % (s, why))
        for r in empty_regions:
            print("  region   %r was never reached, so this run cannot have "
                  "measured the obligation's domain" % (r,))
        for s, why, sh, orc in order_violations:
            print("  order    input=%r %s (shadow submits=%d oracle submits=%d)"
                  % (s, why, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of optionalPathValidator agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements IN the "
          "obligation's domain, reaching every region: %r. The domain is exactly "
          "right: IN it the oracle always came back (a value or the "
          "ValidationError the call site catches) and never escaped, so it is "
          "not too small; OUT of it the oracle never came back at all, so it is "
          "not too large — and there the shadow always DID come back, because "
          "every read it performs is the guarded one (mapping.md §1.1). "
          "Submission order also agrees where the change is: the empty entry is "
          "submitted to the strict validator ZERO times by both sides, and an "
          "accepted entry exactly once by both. A guarded read at the DERIVED "
          "entry '~'+NUL+entry — the shape that broke the previous revision, "
          "where the expansion had a total function type — answered every one of "
          "%d times and left outcome and submission count untouched on every "
          "input; and an EARNED submission of the derived entry '~'+entry, which "
          "`accepted_in_domain` licenses inside the branch that shows it accepted, "
          "fired %d times, came back every time and changed no outcome. Disclosed "
          "asymmetry (refinement.md §C), same outcome either "
          "way: on %d non-accepted non-empty in-domain inputs (and %d "
          "out-of-domain ones) the oracle submits once and lets the raise "
          "propagate while the shadow decides first and does not submit."
          % (count, SEED, seen, derived_reads, derived_submissions, asymmetric,
             out_asymmetric))
    return 0


if __name__ == "__main__":
    sys.exit(main())
