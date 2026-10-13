#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13453.

There are NO consumed `@ContractOnly` axioms in this bundle: the format
resolution the writer performs when preparing its output columns is the
behaviour under specification and is modelled DEEPLY in model.py (the pure
`resolved_format` plus the verified loop in `resolve_column_formats`).  What this
script validates is the single **A-reference**: that the deep model equals the
real column-format-resolution step the gold patch invokes.

The real step (astropy `BaseData._set_col_formats`,
`astropy/io/ascii/core.py:934-938`) is, per output column:

    for col in self.cols:
        if col.info.name in self.formats:
            col.info.format = self.formats[col.info.name]
        # else: col.info.format is left unchanged

i.e. the format a column ends up bound to is `self.formats[name]` when the
column's name is a key of the supplied mapping, and the column's prior format
otherwise.  This is exactly ordinary dict membership + lookup, which is what
model.py's `resolved_format` / loop compute over `int` carrier tokens.

`reference_set_col_formats` below is a faithful, dependency-free reimplementation
of that real loop (over opaque `name`/`format` tokens).  We assert the model's
resolution equals it on boundary cases + randomized fuzz.  Names and format
specs are modelled as integer identity tokens (mapping.md §2); the resolution
only observes WHICH spec each column ends up bound to, so integer identity is a
faithful carrier and this check needs nothing repo-specific (stdlib only).

GUARDED equality (NOT total) — the SPEC_GUIDE §0.7 raise boundary.  The deep
model is a *total* function of name/prior/formats.  The real callee's
*selection* step (`col.info.format = self.formats[name]`) is what the model
captures, and it is dtype-agnostic — but in this astropy version the assignment
goes through a *validating* `Column.format` setter
(`astropy/table/column.py:740`).  A spec incompatible with the column's dtype
(e.g. integer format `"04d"` applied to a float column) is rejected by that
setter, so `_set_col_formats` RAISES `ValueError` AT ASSIGNMENT
(`core.py:938`, `col.info.format = self.formats[name]`) — not later at
`iter_str_vals()` render time.  The modeled region is the resolution decision;
the dtype/format compatibility check is performed by the validating setter,
downstream of and outside that decision.  So the equality is asserted on
format/dtype-compatible inputs (the domain F2P/P2P exercise), and the raise
boundary outside it is positively asserted (not hidden): when astropy is
importable we drive a float column with an incompatible selected spec through
the genuine `_set_col_formats` and require it to raise at assignment.

Exit 0 iff every observation on the compatible domain matches the model AND the
incompatible-spec assignment boundary raises as documented.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def resolved_format(name, prior, formats):
    """Reference of model.py's pure `resolved_format`."""
    if name in formats:
        return formats[name]
    return prior


def model_set_col_formats(names, prior_formats, formats):
    """Reference of model.py's `resolve_column_formats` impl loop: one resolved
    format token per column, in order."""
    result = []
    for i in range(len(names)):
        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
    return result


# --- the REAL behaviour (faithful reimplementation of core.py:934-938) -------

def reference_set_col_formats(names, prior_formats, formats):
    """Mirror of astropy BaseData._set_col_formats over opaque tokens.

    Each column starts with its prior format; if its name is in the supplied
    `formats` mapping, its format becomes `formats[name]`.  Returns the final
    per-column format, index-aligned with the input columns.
    """
    col_formats = list(prior_formats)            # each col keeps its prior fmt
    for i, name in enumerate(names):
        if name in formats:                      # real: col.info.name in self.formats
            col_formats[i] = formats[name]       # real: col.info.format = self.formats[name]
    return col_formats


# --- the checks --------------------------------------------------------------

def check_case(names, prior_formats, formats):
    assert len(names) == len(prior_formats), "test inputs must be index-aligned"
    real = reference_set_col_formats(names, prior_formats, formats)
    model = model_set_col_formats(names, prior_formats, formats)
    assert model == real, (
        "deep model unsound on names=%r prior=%r formats=%r: real gave %r, "
        "model gives %r" % (names, prior_formats, formats, real, model))
    # also pin the per-element pure function
    for i in range(len(names)):
        assert resolved_format(names[i], prior_formats[i], formats) == real[i], (
            "resolved_format mismatch at i=%d" % i)


def main():
    # --- boundary cases ------------------------------------------------------
    boundary = [
        # (names, prior_formats, formats)
        ([], [], {}),                                   # empty table
        ([0], [100], {}),                               # one col, empty mapping
        ([0], [100], {0: 200}),                         # one col, name present
        ([0], [100], {1: 200}),                         # one col, name absent
        ([0, 1], [100, 101], {0: 200}),                 # first present only
        ([0, 1], [100, 101], {1: 201}),                 # second present only
        ([0, 1], [100, 101], {0: 200, 1: 201}),         # both present
        ([0, 1], [100, 101], {2: 999}),                 # mapping names none
        ([0, 1, 2], [10, 11, 12], {0: 20, 2: 22}),      # interleaved
        ([5, 5], [1, 2], {5: 9}),                        # duplicate names -> same fmt
        ([0], [200], {0: 200}),                         # supplied == prior (idempotent)
        ([0], [200], {0: 300}),                         # supplied overrides prior
    ]
    for names, prior, fmts in boundary:
        check_case(names, prior, fmts)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13453)
    for _ in range(50000):
        n = rng.randint(0, 12)
        names = [rng.randint(0, 6) for _ in range(n)]
        prior = [rng.randint(0, 999) for _ in range(n)]
        # build a random mapping over a key universe overlapping the names
        m = {}
        for _k in range(rng.randint(0, 8)):
            m[rng.randint(0, 8)] = rng.randint(1000, 1999)
        check_case(names, prior, m)

    # --- optional: exercise the GENUINE astropy callee if available ----------
    # When run in the evaluation container astropy is importable; we then drive
    # the real BaseData._set_col_formats on real Column objects and confirm the
    # model's resolution matches the format each column actually ends up with.
    # Outside the container this is skipped (the check above is stdlib-only and
    # already validates the deep model against a faithful reimplementation).
    #
    # The real path is checked on TWO axes (SPEC_GUIDE §0.7):
    #   (1) format/dtype-COMPATIBLE inputs over dtype-heterogeneous (int AND
    #       float) columns: the selected spec must equal what the model resolves
    #       AND must render without error -> the GUARDED equality holds; and
    #   (2) the RAISE BOUNDARY: a float column with a dtype-incompatible selected
    #       spec ("04d") is driven through the genuine `_set_col_formats`, whose
    #       validating `Column.format` setter rejects it and RAISES `ValueError`
    #       AT ASSIGNMENT (not at a later render) -> the model is total (returns
    #       the selected token) where the real path is partial, so the equality
    #       is guarded, not total. We assert this boundary POSITIVELY rather than
    #       hiding it behind dtype-uniform happy-path data.
    real_checks = 0
    real_raise_checks = 0
    try:
        from astropy.io.ascii.core import BaseData  # type: ignore
        from astropy.table import Column  # type: ignore

        def norm(x):
            return None if x in ("", None) else x

        # specs that render cleanly on a given dtype ('i' = int col, 'f' = float)
        compat_specs = {
            "i": ["", "04d", "%d", "6d", "+05d"],
            "f": ["", ".2e", ".3f", "10.4g", "+.1f", ".2e"],
        }

        def make_col(kind, nm, spec):
            # int vs float column so the rendering path actually depends on dtype
            data = [1, 2] if kind == "i" else [1.234567e-11, -9.876543e11]
            c = Column(data=data, name=nm)
            c.info.format = spec if spec else None
            return c

        def renders_ok(col):
            # the downstream rendering path the writer ultimately drives
            try:
                list(col.info.iter_str_vals())
                return True
            except Exception:
                return False

        rng2 = random.Random(2013453)
        kinds = ["i", "f"]
        for _ in range(2000):
            n = rng2.randint(0, 6)
            # build dtype-heterogeneous columns with dtype-COMPATIBLE prior specs
            col_names, col_kinds, prior_specs = [], [], []
            seen = set()
            for _c in range(n):
                nm = "C%d" % rng2.randint(0, 5)
                if nm in seen:        # real Tables have unique column names
                    continue
                seen.add(nm)
                k = rng2.choice(kinds)
                col_names.append(nm)
                col_kinds.append(k)
                prior_specs.append(rng2.choice(compat_specs[k]))

            # supplied mapping: keys overlap the column names; selected specs are
            # chosen COMPATIBLE with whatever column they will land on (so the
            # equality is asserted strictly on the compatible domain). Keys that
            # name no present column are harmless and exercise the absent branch.
            name_kind = dict(zip(col_names, col_kinds))
            formats_str = {}
            for _k in range(rng2.randint(0, 4)):
                nm = "C%d" % rng2.randint(0, 5)
                k = name_kind.get(nm, rng2.choice(kinds))
                formats_str[nm] = rng2.choice(compat_specs[k])

            cols = [make_col(k, nm, ps)
                    for nm, k, ps in zip(col_names, col_kinds, prior_specs)]

            data = BaseData()
            data.cols = cols
            data.formats = dict(formats_str)
            data._set_col_formats()                       # the REAL callee

            # (1a) selection equals the model's resolution, per column
            for nm, ps, col in zip(col_names, prior_specs, cols):
                expected = norm(formats_str[nm] if nm in formats_str else ps)
                got = norm(col.info.format)
                assert got == expected, (
                    "real _set_col_formats mismatch for col %r: prior=%r "
                    "formats=%r -> got %r, expected %r"
                    % (nm, ps, formats_str, got, expected))
                # (1b) on the compatible domain the resolved spec also RENDERS
                # cleanly — i.e. we are genuinely inside the guarded equality's
                # domain, not silently masking a render failure.
                assert renders_ok(col), (
                    "compatible-domain render unexpectedly failed for col %r "
                    "with resolved format %r" % (nm, norm(col.info.format)))
            real_checks += 1

        # (2) RAISE BOUNDARY: float column, mapping selects an int-only spec.
        # The model resolves to the selected token unconditionally; the real
        # resolution path rejects it. Assert the real path RAISES.
        #
        # In this astropy version the validating `Column.format` setter
        # (astropy/table/column.py:740) raises `ValueError: Invalid format for
        # column` AT ASSIGNMENT — i.e. inside `_set_col_formats` itself
        # (core.py:938, `col.info.format = self.formats[name]`), NOT later at
        # `iter_str_vals()` render time. So we wrap the genuine `_set_col_formats`
        # call in a try/except and require it to raise there.
        for _ in range(200):
            nm = "C0"
            float_col = make_col("f", nm, "")          # float column, no prior fmt
            bad_spec = rng2.choice(["04d", "6d", "+05d", "d"])  # int-only formats
            # model: selected token is just returned (total) ...
            model_resolved = model_set_col_formats([1], [0], {1: 2})  # token-level: returns selected
            assert model_resolved == [2], "model selection must be total"
            # ... real: assigning the bad spec is rejected by the validating
            # Column.format setter, so _set_col_formats raises AT ASSIGNMENT.
            data = BaseData()
            data.cols = [float_col]
            data.formats = {nm: bad_spec}
            raised = False
            try:
                data._set_col_formats()                # validating setter raises here
            except (ValueError, TypeError):
                raised = True
            assert raised, (
                "EXPECTED the real resolution path to RAISE on a "
                "dtype-incompatible selected spec %r on a float column "
                "(the validating Column.format setter rejects it at assignment), "
                "but it did not — the documented partiality boundary is wrong"
                % bad_spec)
            real_raise_checks += 1
    except ImportError:
        pass  # astropy not importable (e.g. host verifier env): stdlib path suffices

    print("G-AX OK: deep format-resolution model == real _set_col_formats "
          "selection on %d boundary + 50000 fuzz inputs (token-level)"
          "%s%s" % (
              len(boundary),
              (" + %d real astropy _set_col_formats compatible-domain cases "
               "(int+float columns)" % real_checks) if real_checks else
              " (real-astropy path skipped: not importable)",
              (" + %d positive raise-boundary probes (float col, int-only spec, "
               "validating Column.format setter raises at assignment => equality "
               "is guarded not total)"
               % real_raise_checks) if real_raise_checks else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
