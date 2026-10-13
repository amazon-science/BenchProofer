#!/usr/bin/env python3
r"""G-CONF differential conformance check for pytest-dev__pytest-5787 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (TraceReport <-> the rendered longrepr object; Link <-> one
              `(reprtraceback, reprcrash, description)` chain element; Serialized
              <-> the builtin dict produced by serialization). Concretely the
              shadow is `decode (encode r)` — the `roundTripReport`
              postcondition `out = r`. There are NO A-tagged callees in the
              computed output (no consumed axioms — refinement.md §C), so the
              shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched real
              `_report_kwargs_from_json(_report_to_json(report))` applied to a
              report whose `longrepr` is a real
              `ExceptionChainRepr` / `ReprExceptionInfo`, then the reconstructed
              longrepr read back (the real correctness oracle, G-RESOLVE). The
              harness applies patch.diff at base_commit before this runs.

Both sides are normalized to a comparable tag:
  ('simple',  text, summary, extras)
  ('chained', [(text, summary, desc), ...], extras)

They must agree on every input, including the multi-link chains the issue is
about (#5786): the entire chain must survive the round-trip, not just its
outermost link. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the repo's
own `_pytest` package. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 5787
N_FUZZ = 100_000

DESCRIPTIONS = [
    "The above exception was the direct cause of the following exception:",
    "During handling of the above exception, another exception occurred:",
]


# --- the model domain (mirrors Solution.lean's pure region) ------------------
# A model report is one of:
#   ('simple',  text:int, summary:int, extras:list[(str,str,str)])
#   ('chained', links:list[(text:int, summary:int, desc:str|None)],
#               extras:list[(str,str,str)])

def encode(r):
    """Solution.lean `encode` transliterated."""
    if r[0] == 'simple':
        _, t, s, xs = r
        return {'text': t, 'summary': s, 'extras': xs, 'chain': None}
    _, links, xs = r
    last = links[-1] if links else (0, 0, None)
    return {'text': last[0], 'summary': last[1], 'extras': xs,
            'chain': list(links)}


def decode(s):
    """Solution.lean `decode` transliterated."""
    if s['chain'] is not None:
        return ('chained', [tuple(l) for l in s['chain']], s['extras'])
    return ('simple', s['text'], s['summary'], s['extras'])


def shadow(r):
    """decode (encode r) — the roundTripReport R/I shadow. Returns the model
    report it reconstructs (must equal `r`)."""
    return decode(encode(r))


# --- the oracle: build real longrepr, run the gold serialize/deserialize -----

def _make_real_modules():
    from _pytest._code.code import (
        ExceptionChainRepr, ReprExceptionInfo, ReprTraceback,
        ReprFileLocation, ReprEntryNative,
    )
    from _pytest.reports import _report_to_json, _report_kwargs_from_json
    return dict(
        ExceptionChainRepr=ExceptionChainRepr,
        ReprExceptionInfo=ReprExceptionInfo,
        ReprTraceback=ReprTraceback,
        ReprFileLocation=ReprFileLocation,
        ReprEntryNative=ReprEntryNative,
        _report_to_json=_report_to_json,
        _report_kwargs_from_json=_report_kwargs_from_json,
    )


# token <-> distinctive content carried verbatim by the per-link codec (R)
def _tb(M, text_token):
    # one native entry carrying the rendered text token; survives via
    # serialize_repr_entry / deserialize_repr_entry verbatim.
    entry = M['ReprEntryNative'](["TEXT[%d]" % text_token])
    return M['ReprTraceback']([entry], None, "long")


def _crash(M, summary_token):
    # reprcrash: the one-line summary token lives in `lineno`.
    return M['ReprFileLocation']("mod.py", summary_token, "MSG[%d]" % summary_token)


def _extract_text(tb):
    # inverse of _tb on the carried token (an R refinement, content verbatim)
    line = tb.reprentries[0].lines[0]
    return int(line[len("TEXT["):-1])


def _extract_summary(crash):
    return int(crash.lineno)


def _build_longrepr(M, r):
    if r[0] == 'simple':
        _, t, s, xs = r
        lr = M['ReprExceptionInfo'](_tb(M, t), _crash(M, s))
    else:
        _, links, xs = r
        chain = [(_tb(M, t), _crash(M, s), desc) for (t, s, desc) in links]
        lr = M['ExceptionChainRepr'](chain)
    for (title, content, sep) in xs:
        lr.addsection(title, content, sep)
    return lr


def _make_report(longrepr):
    # The gold functions consume `report.__dict__` and `report.longrepr`. A
    # minimal duck-typed report with only builtin scalar fields is sufficient;
    # `toterminal`/`reprtraceback`/`reprcrash` come from the longrepr object.
    class _Rep:
        pass
    rep = _Rep()
    rep.nodeid = "test_x::test_y"
    rep.outcome = "failed"
    rep.when = "call"
    rep.longrepr = longrepr
    return rep


def _normalize_loaded(M, longrepr):
    if isinstance(longrepr, M['ExceptionChainRepr']):
        links = [(_extract_text(tb), _extract_summary(crash), desc)
                 for (tb, crash, desc) in longrepr.chain]
        return ('chained', links, list(longrepr.sections))
    # ReprExceptionInfo (simple)
    return ('simple', _extract_text(longrepr.reprtraceback),
            _extract_summary(longrepr.reprcrash), list(longrepr.sections))


def make_oracle(M):
    def oracle(r):
        longrepr = _build_longrepr(M, r)
        rep = _make_report(longrepr)
        data = M['_report_to_json'](rep)            # gold serialize
        kwargs = M['_report_kwargs_from_json'](data)  # gold deserialize
        loaded = kwargs['longrepr']
        return _normalize_loaded(M, loaded)
    return oracle


# --- input stream ------------------------------------------------------------

def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ('simple', 1, 2, [])
    yield ('simple', 7, 9, [("title", "contents", "=")])
    # a 2-link chain — the exact shape of the F2P test (#5786)
    yield ('chained',
           [(11, 12, DESCRIPTIONS[0]), (13, 14, None)],
           [("title", "contents", "=")])
    # a 3-link chain (the problem_statement's worked examples)
    yield ('chained',
           [(21, 22, DESCRIPTIONS[1]), (23, 24, DESCRIPTIONS[1]), (25, 26, None)],
           [])
    # single-link chain (a chain object with one element)
    yield ('chained', [(31, 32, None)], [])
    for _ in range(n):
        if rng.random() < 0.4:
            yield ('simple', rng.randint(0, 9999), rng.randint(0, 9999),
                   _rand_extras(rng))
        else:
            k = rng.randint(1, 6)
            links = []
            for j in range(k):
                desc = (None if j == k - 1
                        else rng.choice(DESCRIPTIONS))
                links.append((rng.randint(0, 9999), rng.randint(0, 9999), desc))
            yield ('chained', links, _rand_extras(rng))


def _rand_extras(rng):
    m = rng.randint(0, 3)
    return [("t%d" % i, "c%d" % i, rng.choice(["-", "=", "_"]))
            for i in range(m)]


def main():
    rng = random.Random(SEED)
    try:
        M = _make_real_modules()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not load patched _pytest.reports: %r" % e)
        return 2
    oracle = make_oracle(M)

    disagreements = []
    count = 0
    for r in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # SHADOW: roundTripReport must reconstruct the original model report.
        sh = shadow(r)
        if sh != r:
            disagreements.append((r, ("SHADOW", sh), ("ORIG", r)))
            if len(disagreements) >= 5:
                break
            continue
        # ORACLE: the patched real serialize/deserialize must agree with it.
        try:
            orc = oracle(r)
        except Exception as e:
            disagreements.append((r, sh, "ORACLE-RAISED:%r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if sh != orc:
            disagreements.append((r, sh, orc))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for r, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (r, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of roundTripReport (decode . encode) agrees "
          "with patch.diff (patched _report_to_json/_report_kwargs_from_json) "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
