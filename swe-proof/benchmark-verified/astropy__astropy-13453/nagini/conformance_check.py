#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13453 (nagini).

SHADOW  — the impl region of model.py copied VERBATIM with the contract
          statement lines (Requires/Ensures/Invariant and their Acc/list_pred
          arguments) stripped; the model IS Python, so no transliteration.
          The @Pure helper `resolved_format` copies over as a plain function.
          The shadow works over the model's carrier types: two index-aligned
          List[int] (name tokens / prior-format tokens) and a Dict[int, int]
          (name token -> format token).

BRIDGE  — mapping.md §2's type abstraction: a column name is an opaque int
          identity token (distinct names <-> distinct ints) and a format
          specification is an opaque int identity token (distinct specs <->
          distinct ints).  The resolution only tests name equality / dict
          membership and only decides WHICH spec each column ends up bound
          to, never inspecting name or spec content, so an injective
          token<->string map is an exact bridge.  Where real format strings
          are needed (the validating column-format setter is in play) the
          fuzzer stays inside the documented compatible domain
          (mapping.md §3.1): integer-dtype columns with integer format
          strings, so the guarded A-reference equality applies.

ORACLE  — the REAL patched repo behaviour (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs), on two axes:
          (1) the genuine `astropy.io.ascii.core.BaseData._set_col_formats`
              — the per-column resolution step the model models
              (mapping.md §1) — driven on minimal column stand-ins exposing
              only the attributes the method reads (`info.name`,
              `info.format`), both directly over int tokens and over
              bridged strings; the per-column final format is the
              observable; and
          (2) end-to-end through the patched writer: a real Table written
              with format="html" and a per-name `formats` mapping; the
              rendered body-cell strings are the observable.  The shadow
              resolves each column's format token with the model's loop,
              maps the token back to its concrete spec, and renders with
              the real per-column rendering primitive
              (`col.info.iter_str_vals()` under the resolved spec) — so any
              column the patched write path binds to a different spec than
              the model resolves shows up as a cell-string disagreement.
              Specs are chosen so distinct tokens render distinctly (and
              are dtype-compatible, per the guarded-equality domain of
              mapping.md §3.1).

Exit 0 iff zero disagreements over the boundary cases + >=1e5 fuzzed
Requires-satisfying inputs (len(names) == len(prior_formats)).
Pinned seed: 13453.  stdlib + astropy (the repo under test) only.
"""
import random
import sys

SEED = 13453
N_FUZZ = 100_000       # phase-1 fuzz cases (genuine _set_col_formats)
N_WRITE = 2_000        # phase-2 end-to-end patched HTML-write cases


# ---------------------------------------------------------------------------
# model.py pure region, copied as a plain function (@Pure/Requires stripped).
# ---------------------------------------------------------------------------

def resolved_format(name, prior, formats):
    if name in formats:
        return formats[name]
    return prior


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant) stripped.
# ---------------------------------------------------------------------------

def resolve_column_formats(names, prior_formats, formats):
    result = []  # type: list
    i = 0
    while i < len(names):
        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# Oracle 1: the genuine BaseData._set_col_formats (the resolution callee the
# patched writer invokes), driven on minimal stand-ins exposing exactly the
# attributes the method reads.  Stand-ins carry no validating setter, so the
# observable is the pure resolution decision — total, like the model.
# ---------------------------------------------------------------------------

class _Info(object):
    __slots__ = ("name", "format")

    def __init__(self, name, fmt):
        self.name = name
        self.format = fmt


class _Col(object):
    __slots__ = ("info",)

    def __init__(self, name, fmt):
        self.info = _Info(name, fmt)


def oracle_set_col_formats(names, prior_formats, formats):
    from astropy.io.ascii.core import BaseData
    cols = [_Col(nm, pf) for nm, pf in zip(names, prior_formats)]
    data = BaseData()
    data.cols = cols
    data.formats = dict(formats)
    data._set_col_formats()          # the REAL patched-repo resolution step
    return [c.info.format for c in cols]


# String bridge for oracle 1 (injective token <-> string, exact by §2):
def _name_str(t):
    return "n%d" % t


def _spec_str(t):
    return "s%d" % t


def oracle_set_col_formats_bridged(names, prior_formats, formats):
    """Same genuine callee, but over bridged strings; result mapped back to
    tokens via the inverse of the injective spec map."""
    real = oracle_set_col_formats(
        [_name_str(t) for t in names],
        [_spec_str(t) for t in prior_formats],
        {_name_str(k): _spec_str(v) for k, v in formats.items()})
    return [int(s[1:]) for s in real]


# ---------------------------------------------------------------------------
# Oracle 2: end-to-end through the patched writer.  Real integer columns,
# integer-compatible format strings (the documented compatible domain), a
# per-name formats mapping passed to write(format="html").  The observable is
# the rendered body-cell strings: the shadow resolves each column's format
# token with the model's loop, maps it back to a concrete spec, renders with
# the real per-column rendering primitive, and the result must match the
# <td> contents the patched writer emits.  Spec strings are chosen so that
# distinct tokens render distinctly on the fixed data (zero-padding widths
# survive whitespace stripping; the token-0 "unset" default is narrower than
# any padded width), so the bridge back from rendered text is injective.
# ---------------------------------------------------------------------------

_WDATA = [1, 2, 3]           # per-column data for every write case
import re as _re
_TD = _re.compile(r"<td>(.*?)</td>", _re.DOTALL)


def _wspec(t):
    # injective token -> dtype-compatible format string (or unset for 0);
    # zero-padded widths render distinctly on _WDATA even after stripping
    return None if t == 0 else "0%dd" % (t + 2)


def _render_col(name, spec):
    """Real rendering primitive on a fresh column bound to `spec`."""
    from astropy.table import Column
    c = Column(data=list(_WDATA), name=name)
    c.info.format = spec
    return [s.strip() for s in c.info.iter_str_vals()]


def check_html_write(name_tokens, prior_tokens, format_map, disagreements):
    import io
    from astropy.table import Table
    names = [_name_str(t) for t in name_tokens]
    tab = Table([list(_WDATA) for _ in names], names=names)
    for nm, pt in zip(names, prior_tokens):
        tab[nm].info.format = _wspec(pt)
    fmts = {_name_str(k): _wspec(v) for k, v in format_map.items()
            if _wspec(v) is not None}
    # tokens mapping to the "unset" spec are dropped from the mapping (a real
    # per-name mapping supplies concrete specs); keep the token map aligned
    fmt_tokens = {k: v for k, v in format_map.items() if v != 0}

    buf = io.StringIO()
    tab.write(buf, format="html", formats=fmts)
    oracle = [m.group(1).strip() for m in _TD.finditer(buf.getvalue())]

    # SHADOW: model loop resolves the per-column tokens; real primitive renders
    resolved = resolve_column_formats(name_tokens, prior_tokens, fmt_tokens)
    per_col = [_render_col(nm, _wspec(tok))
               for nm, tok in zip(names, resolved)]
    shadow = []
    for r in range(len(_WDATA)):
        for c in range(len(names)):
            shadow.append(per_col[c][r])

    if shadow != oracle:
        disagreements.append(("write", name_tokens, prior_tokens, format_map,
                              shadow, oracle))
    return len(disagreements) < 5


# ---------------------------------------------------------------------------
# Input generation: Requires-satisfying (index-aligned lists, int dict).
# ---------------------------------------------------------------------------

def boundary_cases():
    yield ([], [], {})                                # empty column set
    yield ([0], [100], {})                            # one col, empty mapping
    yield ([0], [100], {0: 200})                      # name present
    yield ([0], [100], {1: 200})                      # name absent
    yield ([0, 1], [100, 101], {0: 200})              # first present only
    yield ([0, 1], [100, 101], {1: 201})              # second present only
    yield ([0, 1], [100, 101], {0: 200, 1: 201})      # both present
    yield ([0, 1], [100, 101], {2: 999})              # mapping names none
    yield ([0, 1, 2], [10, 11, 12], {0: 20, 2: 22})   # interleaved
    yield ([5, 5], [1, 2], {5: 9})                    # duplicate names
    yield ([0], [200], {0: 200})                      # supplied == prior
    yield ([0], [200], {0: 300})                      # supplied overrides


def gen_case(rng):
    n = rng.randint(0, 12)
    names = [rng.randint(0, 6) for _ in range(n)]
    prior = [rng.randint(0, 999) for _ in range(n)]
    m = {}
    for _k in range(rng.randint(0, 8)):
        m[rng.randint(0, 8)] = rng.randint(1000, 1999)
    return names, prior, m


def gen_write_case(rng):
    # unique names (a real Table requires them); tokens kept small so the
    # bridged format strings stay inside the compatible integer domain
    n = rng.randint(1, 4)
    name_tokens = rng.sample(range(6), n)
    prior_tokens = [rng.randint(0, 9) for _ in range(n)]
    m = {}
    for _k in range(rng.randint(0, 4)):
        m[rng.randint(0, 6)] = rng.randint(0, 9)
    return name_tokens, prior_tokens, m


def main():
    rng = random.Random(SEED)
    checked = 0
    disagreements = []

    def check(names, prior, fmts, oracle_fn, tag):
        nonlocal checked
        shadow = resolve_column_formats(names, prior, fmts)
        real = oracle_fn(names, prior, fmts)
        checked += 1
        if shadow != real:
            disagreements.append((tag, names, prior, fmts, shadow, real))
        # also pin the per-element pure function against the same oracle
        for i in range(len(names)):
            if resolved_format(names[i], prior[i], fmts) != real[i]:
                disagreements.append(
                    ("%s/pure@%d" % (tag, i), names, prior, fmts,
                     resolved_format(names[i], prior[i], fmts), real[i]))
                break
        return len(disagreements) < 5

    # phase 1a/1b: boundary through the genuine callee, both bridges
    for names, prior, fmts in boundary_cases():
        if not check(names, prior, fmts, oracle_set_col_formats, "boundary/token"):
            break
        if not check(names, prior, fmts, oracle_set_col_formats_bridged,
                     "boundary/str"):
            break

    # phase 1c: fuzz through the genuine callee (token / bridged-string mix)
    if not disagreements:
        for i in range(N_FUZZ):
            names, prior, fmts = gen_case(rng)
            fn = oracle_set_col_formats if i % 2 == 0 else \
                oracle_set_col_formats_bridged
            if not check(names, prior, fmts, fn,
                         "fuzz/%s" % ("token" if i % 2 == 0 else "str")):
                break

    # phase 2: end-to-end through the patched HTML write path
    if not disagreements:
        for _ in range(N_WRITE):
            names, prior, fmts = gen_write_case(rng)
            checked += 1
            if not check_html_write(names, prior, fmts, disagreements):
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for tag, names, prior, fmts, sh, orc in disagreements:
            print("  [%s] names=%r prior=%r formats=%r\n    shadow=%r\n"
                  "    oracle=%r" % (tag, names, prior, fmts, sh, orc))
        return 1
    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "resolution (genuine _set_col_formats: token + bridged-string "
          "bridges; plus %d end-to-end patched HTML writes) on %d inputs "
          "(seed=%d), 0 disagreements." % (N_WRITE, checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
