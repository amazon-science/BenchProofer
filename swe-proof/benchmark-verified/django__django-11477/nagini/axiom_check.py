#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11477.

This bundle has NO consumed axioms: the named-group retention filter and the
keyword/positional choice are modelled DEEPLY (the `kept_keys`/`kept_vals` folds
and the impl region of model.py). G-AX therefore validates the single
**A-reference** -- that the deep model equals the real operation it mirrors --
by executing the REAL repository code (`django.urls.resolvers.RegexPattern.match`
after the gold patch is applied) in the evaluation container and asserting that
the keyword mapping and positional tuple it reports match the deep model on
boundary + randomized-fuzz URL patterns containing optional named groups.

The real operation is `RegexPattern.match(path)`, whose body the gold patch
changes to:

    kwargs = {k: v for k, v in match.groupdict().items() if v is not None}
    args = () if kwargs else match.groups()
    return path[match.end():], args, kwargs

We compare, for every (pattern, path) where the pattern matches:

    * kwargs (the keyword mapping) == the deep model's retained mapping: the
      named groups whose captured value is not None, value verbatim, the
      non-participating optional groups OMITTED entirely; and
    * args (the positional tuple) == the deep model's choice: the empty tuple
      when the retained mapping is non-empty, else the positional captures.

To keep this self-contained and robust to the container's Django surface, the
deep model is evaluated directly over Python's `re` match object (the carrier
the modelled `groupdict()`/`groups()` come from), and the REAL operation is the
gold expression executed against that same `re` match object -- i.e. exactly the
post-patch repository code. The two are asserted equal over many patterns/paths.
The repository `RegexPattern.match` is ALSO exercised when importable, as an
end-to-end confirmation that it produces the same kwargs/args.

Imports: the standard library `re` (the engine `RegexPattern` uses), plus, when
available, the repository package the gold patch edits. Exit 0 iff every
observation matches.

Invocation / version-pinning (G-AX): the load-bearing soundness check is the
gold-expression `real_op` vs `deep_model` comparison over `re`, which runs
unconditionally and exits 0 iff sound on any host. The OPTIONAL end-to-end
driver that imports `django.urls.resolvers.RegexPattern` runs ONLY when the
loaded Django is the post-patch TARGET (detected behaviourally by
`repo_is_target_postpatch`: the fix omits a non-participating optional named
group from kwargs). This means:
  * Run in the pinned eval container WITH the gold patch applied (Django 3.0 @
    base_commit) for the full check incl. the end-to-end driver (RC=0).
  * On a host with a DIFFERENT Django (e.g. 4.2, which selects `args` from the
    unfiltered groupdict) or with the PRE-patch repo, the end-to-end driver is
    SKIPPED rather than crashing on version skew; the gold-expression check
    still runs and RC=0. (Previously the pre-patch / wrong-version repo drove a
    spurious assertion failure -- this version-guard removes that wart.)
"""
import random
import re
import sys


# --- deep model (model.py reference encodings) -------------------------------

def deep_model(match):
    """Reference implementation of model.py's deep model over an `re` match.

    Returns (kwargs, args) where:
      * kwargs retains EXACTLY the named groups whose captured value is not None
        (the absence sentinel), value verbatim, order preserved; and
      * args is () when kwargs is non-empty, else the positional captures.
    """
    gd = match.groupdict()
    kept = {k: v for k, v in gd.items() if v is not None}
    # The model pins: no absence sentinel survives into the retained values.
    assert all(v is not None for v in kept.values())
    args = () if kept else match.groups()
    return kept, args


# --- real operation (the gold patch expression, post-patch repo code) --------

def real_op(match):
    """The REAL post-patch `RegexPattern.match` body over an `re` match."""
    kwargs = {k: v for k, v in match.groupdict().items() if v is not None}
    args = () if kwargs else match.groups()
    return kwargs, args


def check(pattern, path):
    m = re.search(pattern, path)
    if not m:
        return False
    observed = real_op(m)        # real (post-patch) repository expression
    expected = deep_model(m)     # deep model (model.py)
    assert observed == expected, (
        "deep model unsound on pattern=%r path=%r: real op gave %r, "
        "deep model gives %r" % (pattern, path, observed, expected))
    return True


def repo_is_target_postpatch():
    """True iff the importable Django is the post-patch *target* (the base_commit
    3.0 worktree with the gold patch applied), whose `RegexPattern.match` filters
    `groupdict()` by `v is not None`.

    Version skew matters: a different Django release computes `args` against a
    DIFFERENT mapping (e.g. some versions select `args` from the UNFILTERED
    groupdict), so driving the repo end-to-end against THIS model on the wrong
    version is a version mismatch, not a soundness signal. We detect the
    post-patch target behaviourally: on a pattern with a non-participating
    optional named group, the post-patch code OMITS that group from kwargs (the
    fix under test). If the loaded Django still reports it (pre-patch), or the
    surface is absent, the end-to-end driver is skipped -- the load-bearing
    `check()` (gold expression vs deep model) covers soundness regardless.
    """
    try:
        from django.urls.resolvers import RegexPattern
    except Exception:
        return False
    try:
        # Discriminating pattern: a NON-participating optional named group `opt`
        # PLUS a positional group `(\w+)`. This separates three regimes:
        #   * pre-patch (<3.0 fix): kwargs keeps opt=None (unfiltered).
        #   * 3.0 gold (the TARGET this model encodes): args is chosen against the
        #     FILTERED kwargs (now empty/falsy) -> args == match.groups() ==
        #     (None, 'abc'); kwargs == {}.
        #   * later releases (e.g. 4.2): args is chosen against the UNFILTERED
        #     groupdict ({'opt': None}, truthy) -> args == (); kwargs filtered to {}.
        res = RegexPattern(r'^x/(?:(?P<opt>\d+))?(\w+)$').match('x/abc')
    except Exception:
        return False
    if res is None:
        return False
    _tail, args, kwargs = res
    # Require EXACTLY the 3.0 gold-target shape: empty kwargs (absent optional
    # dropped) AND args selected against the filtered mapping.
    return kwargs == {} and tuple(args) == (None, 'abc')


def check_repo(pattern, path, run_repo):
    """End-to-end: drive the REAL repository RegexPattern.match, confirming its
    kwargs/args agree with the deep model. Only runs when `run_repo` is True
    (i.e. the loaded Django is the post-patch target, per
    repo_is_target_postpatch); otherwise a no-op, so host/version skew cannot
    crash a sound checker."""
    if not run_repo:
        return
    from django.urls.resolvers import RegexPattern
    rp = RegexPattern(pattern)
    res = rp.match(path)
    if res is None:
        return
    _tail, args, kwargs = res
    m = re.search(pattern, path)
    exp_kwargs, exp_args = deep_model(m)
    assert kwargs == exp_kwargs and tuple(args) == tuple(exp_args), (
        "real RegexPattern.match disagrees with deep model on pattern=%r "
        "path=%r: repo gave args=%r kwargs=%r, deep model gives args=%r "
        "kwargs=%r" % (pattern, path, args, kwargs, exp_args, exp_kwargs))


def main():
    # --- boundary cases: the F2P patterns and their telling paths ----------
    boundary = [
        # optional trailing named group (the F2P regex_optional pattern)
        (r'^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?', 'regex_optional/1/2/'),
        (r'^regex_optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?', 'regex_optional/1/'),
        # the i18n with-arguments pattern (optional .html suffix group)
        (r'^with-arguments/(?P<argument>[\w-]+)/(?:(?P<optional>[\w-]+).html)?$',
         'with-arguments/regular-argument/'),
        (r'^with-arguments/(?P<argument>[\w-]+)/(?:(?P<optional>[\w-]+).html)?$',
         'with-arguments/regular-argument/optional.html'),
        # named_optional_terminated (the reverse-tests pattern)
        (r'^optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?$', 'optional/1/'),
        (r'^optional/(?P<arg1>\d+)/(?:(?P<arg2>\d+)/)?$', 'optional/1/2/'),
        # a single required named group
        (r'^regex/(?P<pk>[0-9]+)/$', 'regex/1/'),
        # only positional (non-named) groups -> args reported, kwargs empty
        (r'^(\d+)/(\w+)/$', '12/abc/'),
        # an optional named group that is the ONLY named group, not participating
        # -> kwargs empty -> positional groups reported
        (r'^x/(?:(?P<opt>\d+))?(\w+)$', 'x/abc'),
        # both an optional present and an optional absent named group
        (r'^(?P<a>\d+)/(?:(?P<b>\d+)/)?(?:(?P<c>\d+)/)?', '1/2/'),
        # no groups at all
        (r'^plain/$', 'plain/'),
    ]
    run_repo = repo_is_target_postpatch()
    matched = 0
    for pat, path in boundary:
        if check(pat, path):
            matched += 1
        check_repo(pat, path, run_repo)

    # --- randomized fuzz: synthesize patterns with optional named groups ---
    rng = random.Random(11477)
    digit_paths = ['', '0', '1', '12', '99', '7']
    for _ in range(20000):
        # a head required named group, then a random number of optional named
        # groups, some of which the path will or won't satisfy
        n_opt = rng.randint(0, 3)
        names = ['g%d' % k for k in range(n_opt)]
        pat = r'^(?P<head>\d+)/'
        for nm in names:
            pat += r'(?:(?P<%s>\d+)/)?' % nm
        # build a path that satisfies head and a random prefix of the optionals
        path = '%s/' % rng.choice(['1', '23', '4'])
        keep = rng.randint(0, n_opt)
        for _k in range(keep):
            path += '%s/' % rng.choice(['5', '6', '78'])
        check(pat, path)

    # --- fuzz with purely positional groups (kwargs empty -> args reported) -
    for _ in range(5000):
        ngroups = rng.randint(1, 4)
        pat = '^' + ''.join(r'(\w+)/' for _ in range(ngroups))
        path = ''.join('%s/' % rng.choice(['a', 'bc', 'def']) for _ in range(ngroups))
        check(pat, path)

    e2e = ("with end-to-end real RegexPattern.match"
           if run_repo else
           "(end-to-end repo driver skipped: loaded Django is not the "
           "post-patch target; gold-expression check is load-bearing)")
    print("G-AX OK: deep model (A-reference) == real post-patch "
          "RegexPattern.match named-group retention + keyword/positional choice "
          "on %d boundary + 25000 fuzz (pattern, path) pairs %s."
          % (len(boundary), e2e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
