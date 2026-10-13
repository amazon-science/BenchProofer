#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9320.

G-AX runs at **base_commit** (the orchestrator does NOT apply the gold patch for
this gate) and validates the UNCHANGED callee(s) the modeled function relies on.
The kind-A construct in this bundle is the UNCHANGED strict path-name validator,
modeled in Solution.lean as an opaque PROGRAM (not a value) together with the two
total primitives it is built from:

    opaque pathIsDir        : List Char -> Bool               # os.path.isdir
    opaque expansionAnswers : List Char -> Bool               # WHERE it answers
    opaque rawExpansion : (entry : List Char) ->              # os.path.expanduser,
      expansionAnswers entry = true -> List Char              #   NOT total
    def pathExpanded (entry) : List Char :=                   # the GUARDED read
      if answered : expansionAnswers entry = true then rawExpansion entry answered
      else []
    def strictAccepts (entry) : Bool := pathIsDir (pathExpanded entry)
    opaque strictPathValidator : List Char -> VelvetM (List Char)

Its repo counterpart is the unchanged callee `sphinx.cmd.quickstart.is_path`
(quickstart.py:91 @ base_commit) — NOT the patch-added `is_path_or_empty`, which
does not exist at base_commit and whose lenient-vs-strict fidelity is G-CONF's
obligation at the patched commit.

WHY THERE IS A THIRD PRIMITIVE, AND WHY THE EXPANSION IS READ THROUGH A GUARD.
`path.isdir` is total: it answers for every input, catching OSError and ValueError
itself (asserted below on every input this checker runs, NUL and lone surrogates
included — that is what licenses `pathIsDir`'s total function type).
`path.expanduser` is NOT. For an entry that begins with `~` whose first path
segment cannot be looked up at all, the lookup escapes — `pwd.getpwnam` raises
ValueError('embedded null byte') for a segment containing a NUL, and
UnicodeEncodeError (a ValueError subclass) for one containing a high surrogate the
filesystem encoding cannot represent — and `expanduser` catches only KeyError, so
nothing turns that into an answer. (A LOW surrogate is not such an entry:
surrogateescape encodes it, the lookup merely fails to find it, and `expanduser`
hands the entry back unchanged. The two are kept apart in the boundary list on
purpose, both regions being measured below.) Such an entry therefore has NO
expansion for anyone to read, test or discard, and no ValidationError either.

`expansionAnswers` names exactly the entries for which the expansion DOES answer.
Two things are built on it, and both are measured here. Every assumed fact that
reads the expansion's ANSWER is guarded by it, and the modeled method's `require`
restricts the obligation to that domain. Separately, the expansion is not exposed
as a total function at all: `rawExpansion` takes a PROOF that the entry is one it
answers for, and what a program may freely read is the GUARDED expansion
`pathExpanded` — the expansion where it answers, the empty entry elsewhere. Its
repo counterpart is `guarded_expansion` below, and the property that makes the
guard honest is that reading it TAKES CONTROL AWAY FROM NOBODY, at any entry
whatever, including entries DERIVED from the method's own input. That is asserted
here directly (see `check_guarded_reads_are_total`), because it is what a
refinement of a read relies on: a spec that promised it in a comment instead was
broken by a rival that read the expansion at `'~' :: NUL :: entry`.

This checker measures the guard as well as the facts, so it exercises BOTH regions
and asserts that each region is non-empty in the inputs it ran (an alphabet with
no NUL in it would agree with anything).

The spec relies on exactly FIVE assumed facts about the unchanged callee and its
primitives. Each is checked here STANDALONE against the real code, in the order
and shape it is assumed in:

  (1) `rawExpansion_empty` : rawExpansion [] answered = []
      the expansion of an empty entry — an entry it answers for, by fact (5) — is
      the empty entry.
      Real: `path.expanduser('') == ''`.
      With (5) this gives the DERIVED theorem `pathExpanded_empty : pathExpanded []
      = []` (the GUARDED reading at the empty entry), checked below as well.

  (2) `pathIsDir_empty` : pathIsDir [] = false
      the empty entry names no directory.
      Real: `path.isdir('') is False`.

  (5) `expansionAnswers_empty` : expansionAnswers [] = true
      expanding an empty entry ANSWERS — so the empty entry, the one input the
      modeled change is about, is inside the obligation's domain and is not
      excused by it.
      Real: `path.expanduser('')` returns (it does not escape); it returns `''`,
      which is fact (1).

      (1)+(2) give the DERIVED theorem `strictAccepts_empty : strictAccepts [] =
      false` — the strict validator does not accept the empty entry. That is the
      load-bearing premise for the empty affordance, and it is ALSO checked here
      end-to-end against the real callee (`is_path('')` does not come back). It is
      a statement about a GOVERNED entry precisely because of (5).

  (3) `strictPathValidator_accepted` : expansionAnswers entry = true ->
        strictAccepts entry = true ->
        strictPathValidator entry = pure (pathExpanded entry)
      on an entry the expansion answers for and the validator accepts, a
      submission COMES BACK, with the expanded entry handed straight back.
      Real: if `path.expanduser(x)` answers and `path.isdir` of it is True, then
      `is_path(x)` returns and `is_path(x) == path.expanduser(x)` verbatim.
      Checked ONLY where the expansion answers: where it does not, there is no
      `path.expanduser(x)` to compare against, which is exactly why the assumed
      fact carries the guard.

  (4) `strictPathValidator_turns_away` : strictAccepts entry = false ->
        NOT (triple True (strictPathValidator entry) (fun _ => True))
      on an entry it does not accept, a submission carries NO guarantee of
      coming back at all — the modeled form of control leaving the submitter.
      Real, and checked in BOTH regions, because this fact is deliberately NOT
      guarded:
        * where the expansion answers and `path.isdir` of it is False, `is_path`
          raises ValidationError, which propagates out of the submitter (nothing
          inside the modeled function catches it — mapping.md §2);
        * where the expansion does not answer, `is_path` does not come back
          either — the escape from `expanduser` propagates through it. Note that
          the guard makes this the LIVE half rather than a vacuous one: off the
          domain the guarded expansion is the empty entry and fact (2) says the
          empty entry names no directory, so `strictAccepts entry` is `false`
          there, the unguarded fact APPLIES, and what it then claims is exactly
          what is measured here — the real callee does not come back. Guarding
          fact (4) would give away refutations for nothing.

  A DERIVED THEOREM, measured alongside the five facts:
      `accepted_in_domain` : strictAccepts entry = true -> expansionAnswers entry
        = true. Immediate from the guard and fact (2), and it is what lets a
      program EARN a submission of an entry it DERIVED from its own input (the
      `require` covers only the input itself). Real, asserted on every accepted
      read below: `path.isdir` of the guarded expansion is true only where the
      expansion answered, so the submission such a branch earns comes back with
      `path.expanduser(entry)` verbatim rather than escaping.

Facts (3) and (4) are what make SUBMITTING an entry an act the impl must EARN
rather than a value it may compute and discard; (1)+(2) are what make the empty
entry one it can never earn; (5) is what keeps that entry inside the domain. The
model asserts nothing MORE: no claim about WHICH non-empty entries are accepted,
no claim about what any expansion is, and no claim about which entries the
expansion answers for beyond the empty one.

Runs the REAL repo callee `is_path` in-container at base_commit over boundary
inputs (empty, existing dirs, non-existing paths, `~` expansion, whitespace,
unicode, and the NUL / lone-surrogate entries that make the expansion escape)
plus randomized fuzzing. stdlib + the repo only. Exit 0 iff sound.
"""
import os
import random
import sys
import tempfile
from os import path as _ospath


def _load_quickstart():
    from sphinx.cmd import quickstart as qs
    return qs


def submit(qs, x):
    """Submit `x` to the REAL strict validator.

    Returns ('returned', value) if control came back with a value, or
    ('no-return', exc) if it did not (the raise leaves the submitter — under
    mapping.md §2 nothing inside the modeled function catches it, so at THIS
    boundary the observation is 'no value comes back'), or ('no-return-escape',
    exc) if it did not come back for a reason that is not the validator's own
    refusal — the expansion escaping through it. Both non-returning kinds are
    'control does not come back' for fact (4); they are kept apart because only
    the FIRST is the refusal the consumer catches (mapping.md §2.1), and the
    second is what the domain guard is for."""
    try:
        return ('returned', qs.is_path(x))
    except qs.ValidationError as exc:
        return ('no-return', exc)
    except BaseException as exc:      # noqa: BLE001 - the escape IS the finding
        return ('no-return-escape', exc)


def expansion_answers(x):
    """The real counterpart of `expansionAnswers x = true`: asking for the
    home-directory expansion of `x` hands an answer back at all."""
    try:
        _ospath.expanduser(x)
        return True
    except BaseException:             # noqa: BLE001 - anything else is 'no answer'
        return False


def guarded_expansion(x):
    """The real counterpart of `pathExpanded x` — the GUARDED expansion, which is
    what a program may freely read (Solution.lean's `pure`-side `def`, mapping.md
    §1.1): the expansion where it answers, and the empty entry where it does not.
    Total by construction, which is the whole point: `rawExpansion` is where the
    escape lives and it cannot be read without a proof that the entry answers."""
    if expansion_answers(x):
        return _ospath.expanduser(x)
    return ''


# --- fact (1): rawExpansion_empty ------------------------------------------
def check_expanded_empty():
    got = _ospath.expanduser('')
    assert got == '', (
        "rawExpansion_empty is unsound: expanduser('') == %r, not ''" % (got,))
    # ... and the DERIVED `pathExpanded_empty`, i.e. the guarded reading there
    got = guarded_expansion('')
    assert got == '', (
        "pathExpanded_empty is unsound: the guarded expansion of '' is %r, not ''"
        % (got,))


# --- fact (2): pathIsDir_empty ---------------------------------------------
def check_isdir_empty():
    got = _ospath.isdir('')
    assert got is False, (
        "pathIsDir_empty is unsound: isdir('') is %r, not False" % (got,))


# --- fact (5): expansionAnswers_empty --------------------------------------
def check_expansion_answers_empty():
    """The empty entry is INSIDE the obligation's domain. If this failed, the
    `require` would excuse the one input the modeled change is about and the
    empty-entry clause would be vacuous."""
    assert expansion_answers('') is True, (
        "expansionAnswers_empty is unsound: expanduser('') does not answer, so "
        "the empty entry would be OUTSIDE the obligation's domain")


# --- derived theorem: strictAccepts_empty, end-to-end on the real callee ----
def check_empty_is_not_accepted(qs):
    """The derived `strictAccepts_empty` as the real callee shows it: submitting
    the empty entry does not come back. This is why the empty entry needs an
    affordance in front of the strict validator at all."""
    kind, _ = submit(qs, '')
    assert kind == 'no-return', (
        "strict validator `is_path` unexpectedly RETURNED for the empty entry; "
        "the empty affordance in the model would be unsound")


# --- the reads a verifying program may perform ANYWHERE, and their totality --
# `pathIsDir` and `pathExpanded` have TOTAL types, so an impl that verifies may
# read them at any entry it likes: its own input, or one it DERIVES from it. That
# licence is sound only if the real counterparts take control away from nobody, so
# it is asserted here on every input this checker runs, at the entry itself AND at
# two derived families: `'~' + NUL + x`, built so the RAW expansion escapes for
# every x (the family a recorded G-EQ rival read, and the one that makes the guard
# load-bearing rather than decorative), and `'~' + x`, which is sometimes accepted
# and sometimes out of domain and is therefore the family that exercises what a
# program may DO with a derived read. This is the executable half of mapping.md
# §1.1, and it is the assertion whose absence let a comment promising totality
# stand in for a measurement.
READS = {'entry': 0, 'derived-escape': 0, 'derived-tilde': 0}
ACCEPTED = {'entry': 0, 'derived-escape': 0, 'derived-tilde': 0}


def check_guarded_reads_are_total(qs, x):
    for label, y in (('entry', x),
                     ('derived-escape', '~\x00' + x),
                     ('derived-tilde', '~' + x)):
        try:
            got_dir = _ospath.isdir(y)
        except BaseException as exc:  # noqa: BLE001 - the escape IS the finding
            raise AssertionError(
                "pathIsDir's TOTAL type is unsound: isdir(%r) took control away "
                "(%s: %s), so an impl could not read it at that entry"
                % (y, type(exc).__name__, exc))
        assert got_dir in (True, False), (
            "isdir(%r) answered %r, which is not a Bool" % (y, got_dir))
        try:
            expanded = guarded_expansion(y)
        except BaseException as exc:  # noqa: BLE001 - likewise
            raise AssertionError(
                "pathExpanded's TOTAL type is unsound: the guarded expansion of "
                "%r took control away (%s: %s)" % (y, type(exc).__name__, exc))
        if expansion_answers(y):
            assert expanded == _ospath.expanduser(y), (
                "the guarded expansion of %r is %r, not the expansion %r it "
                "answers with" % (y, expanded, _ospath.expanduser(y)))
        else:
            assert expanded == '', (
                "the guarded expansion of %r is %r, not the empty entry the "
                "model's `else` branch pins" % (y, expanded))
        try:
            accepted = _ospath.isdir(expanded)
        except BaseException as exc:  # noqa: BLE001 - likewise
            raise AssertionError(
                "strictAccepts is not free at %r: isdir of its guarded expansion "
                "%r took control away (%s: %s)"
                % (y, expanded, type(exc).__name__, exc))
        READS[label] += 1
        # --- the derived theorem `accepted_in_domain`, on the real code -------
        # ACCEPTANCE IMPLIES DOMAIN MEMBERSHIP, so a program that shows an entry
        # accepted has EARNED a submission of it even if that entry is one it
        # derived and the `require` says nothing about (properties.py
        # pos-derived-submission-earned). The Lean side is a theorem; this is the
        # measurement that the real code satisfies the same implication, at the
        # entry AND at two derived families, and that the submission it licenses
        # therefore comes back with the expansion verbatim.
        if accepted:
            ACCEPTED[label] += 1
            assert expansion_answers(y), (
                "accepted_in_domain is unsound: the guarded expansion of %r names "
                "an existing directory, yet the expansion does not answer there — "
                "so a program could earn a submission of %r and the real callee "
                "would escape out of it" % (y, y))
            kind, got = submit(qs, y)
            assert kind == 'returned', (
                "an EARNED submission did not come back: %r is accepted (isdir of "
                "its guarded expansion is True) but the real callee gave %r"
                % (y, kind))
            assert got == _ospath.expanduser(y), (
                "an EARNED submission of %r came back with %r, not expanduser(%r) "
                "== %r" % (y, got, y, _ospath.expanduser(y)))
    # the derived family is the one that makes the guard load-bearing rather than
    # decorative: its first segment carries a NUL, so the RAW expansion escapes for
    # every x, and only the guard turns that into a value.
    assert not expansion_answers('~\x00' + x), (
        "the derived entry %r ANSWERS, so this input does not exercise the guard "
        "the way it is meant to" % ('~\x00' + x,))
    raw = None
    try:
        raw = _ospath.expanduser('~\x00' + x)
    except BaseException:             # noqa: BLE001 - expected: this is the escape
        pass
    assert raw is None, (
        "the raw expansion of %r came back as %r, so the guard would be "
        "unnecessary there and this input measures nothing"
        % ('~\x00' + x, raw))


# --- how many entries landed in each of the three regions ------------------
# The two facts below say different things on either side of the domain guard,
# so a run that never left one region would agree with a spec that is wrong in
# the other. Counted, and asserted non-zero at the end.
SEEN = {'out-of-domain': 0, 'in-domain-accepted': 0, 'in-domain-refused': 0}


# --- facts (3) and (4) at one entry ----------------------------------------
def check_all_facts(qs, x):
    """Fact (3) where it is guarded to apply, fact (4) everywhere it applies, and
    the totality of every read a verifying program may perform, everywhere."""
    check_guarded_reads_are_total(qs, x)
    if not expansion_answers(x):
        # OUTSIDE the domain. Fact (3) is guarded and says nothing here, and
        # there is no `expanduser(x)` to compare a returned value against. Fact
        # (4) is UNGUARDED, so what has to hold is the half of it that does not
        # mention the expansion: a submission does not come back. (If the
        # modeled `strictAccepts x` happened to be true here the fact would
        # apply vacuously; this is the assertion that makes it sound either way.)
        SEEN['out-of-domain'] += 1
        kind, _ = submit(qs, x)
        assert kind != 'returned', (
            "strictPathValidator_turns_away is unsound OUTSIDE the domain: the "
            "expansion of %r does not answer, yet the real callee came back "
            "with a value" % (x,))
        return

    expanded = _ospath.expanduser(x)
    if _ospath.isdir(expanded):
        # fact (3): guard holds, and the entry is accepted.
        SEEN['in-domain-accepted'] += 1
        kind, got = submit(qs, x)
        assert kind == 'returned', (
            "strictPathValidator_accepted is unsound: %r is in the domain and "
            "accepted (isdir(expanduser(.)) is True) but the real callee did "
            "not come back" % (x,))
        assert got == expanded, (
            "strictPathValidator_accepted is unsound: on accepting %r the real "
            "callee handed back %r, not expanduser(%r) == %r"
            % (x, got, x, expanded))
    else:
        # fact (4) inside the domain: the entry is not accepted, so the real
        # callee refuses it, and the refusal is the ValidationError the
        # consumer catches at the METHOD's boundary (mapping.md §2.1) — not
        # some other escape.
        SEEN['in-domain-refused'] += 1
        kind, exc = submit(qs, x)
        assert kind == 'no-return', (
            "strictPathValidator_turns_away is unsound: %r is in the domain and "
            "NOT accepted (isdir(expanduser(.)) is False) yet the real callee "
            "came back as %r (%r), so a submission of it would be free rather "
            "than earned" % (x, kind, exc))


def main():
    qs = _load_quickstart()

    # --- facts (1), (2) and (5): the three boundary facts, standalone -------
    check_expanded_empty()
    check_isdir_empty()
    check_expansion_answers_empty()
    # --- the derived theorem, end-to-end on the real callee ---------------
    check_empty_is_not_accepted(qs)

    # --- facts (3) and (4) over boundary + fuzz inputs ---------------------
    with tempfile.TemporaryDirectory() as d:
        sub = os.path.join(d, 'sub')
        os.mkdir(sub)
        home = os.path.expanduser('~')
        boundary = [
            '', d, sub, home, '.', '..', '/', os.getcwd(),
            'definitely_not_a_real_path_zzz', './nope/zzz',
            ' ', '  ', '\t', 'a', 'Z', '0',
            '~', '~/', os.path.join(d, 'missing'),
            'has space', 'tab\tx', 'uniécode', '•',
            # The entries the domain guard exists for: a `~` whose first segment
            # cannot be looked up at all, so the expansion escapes instead of
            # answering (an embedded NUL, or a high surrogate no filesystem
            # encoding accepts). Plus their in-domain NEIGHBOURS — the same
            # characters outside a leading `~` segment, and a low surrogate,
            # which the lookup does accept and merely fails to find — because the
            # pair is what shows the guard tracks the real boundary rather than
            # 'the entry contains an odd character'.
            '~\x00', '~\x00abc', '~\x00/x', '~\ud800', '~\ud800abc',
            '\x00', 'a\x00b', '\x00~', '/tmp/\x00', '~/\x00', '\ud800',
            '~\udcff', '~\udcffabc', '\udcff',
            '~nonexistent_user_zzz', '~root',
        ]
        n_boundary = len(boundary)
        for x in boundary:
            check_all_facts(qs, x)
        # the empty entry must keep failing to come back throughout
        check_empty_is_not_accepted(qs)

        # --- randomized fuzz -------------------------------------------
        # The alphabet carries `~`, a NUL and a lone surrogate, so the stream
        # reaches BOTH sides of the domain guard on its own rather than only
        # through the boundary list. (A previous revision's alphabet had neither
        # of the last two, which is why its fuzzing agreed with a spec that
        # claimed an outcome for every entry: it never generated one where the
        # expansion escapes.)
        rng = random.Random(9320)
        existing = [d, sub, home]
        chars = list("abcZ0 ./~\t\\:;-_") + ["é", "•", "\x00", "\ud800", "\udcff"]
        for _ in range(20000):
            mode = rng.randint(0, 2)
            if mode == 0:
                base = rng.choice(existing)
                tail = "".join(rng.choice(chars) for _ in range(rng.randint(0, 4)))
                x = base if rng.random() < 0.5 else os.path.join(base, tail)
            else:
                k = rng.randint(0, 16)   # may be empty -> exercises the empty entry
                x = "".join(rng.choice(chars) for _ in range(k))
            check_all_facts(qs, x)
        # tilde-prefixed entries, so the region the guard is about is reached by
        # construction and not only by luck: half of these escape the expansion.
        for _ in range(2000):
            k = rng.randint(0, 8)
            x = "~" + "".join(rng.choice(chars) for _ in range(k))
            check_all_facts(qs, x)

    # --- the guard is only meaningful if BOTH regions were reached ----------
    for region, n in SEEN.items():
        assert n > 0, (
            "this run never reached the %r region, so it cannot have validated "
            "the facts that govern it (counts: %r)" % (region, SEEN))

    print("G-AX OK: all five assumed facts hold of the real unchanged code at "
          "base_commit — expanduser('') == '' and isdir('') is False (so the "
          "empty entry is not accepted, confirmed end-to-end: `is_path('')` "
          "does not come back) and expanduser('') ANSWERS (so the empty entry "
          "is inside the obligation's domain), an entry the expansion answers "
          "for and the validator accepts comes back as expanduser(entry) "
          "verbatim, an entry it answers for that is not accepted comes back as "
          "no value at all (the refusal the consumer catches), and an entry the "
          "expansion does NOT answer for does not come back either — over %d "
          "boundary + 22000 fuzz inputs, reaching every region: %r. The two reads "
          "a verifying program may perform ANYWHERE are total wherever it "
          "performs them: isdir never took control away, and neither did the "
          "GUARDED expansion (mapping.md §1.1) — checked at the entry itself and "
          "at two derived families, '~'+NUL+entry (whose RAW expansion escapes "
          "every time) and '~'+entry, %r reads. And acceptance implies domain "
          "membership, the real counterpart of the derived theorem "
          "`accepted_in_domain`: on every one of the %d reads whose guarded "
          "expansion named a directory the expansion also ANSWERED, and the "
          "submission that acceptance earns came back with expanduser(entry) "
          "verbatim — %r by family — so a program may act on a decision it took "
          "at an entry it derived, and only there."
          % (n_boundary, SEEN, READS, sum(ACCEPTED.values()), ACCEPTED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
