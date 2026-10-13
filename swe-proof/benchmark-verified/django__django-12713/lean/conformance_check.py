#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12713.

The bundle models ONE behavior: the widget-selection block of
`BaseModelAdmin.formfield_for_manytomany` (`django/contrib/admin/options.py`).
Its Lean implementation (`implementation_resolveWidget`) decides which form
widget a multi-valued relation field ends up with:

    widget = incoming                       # kwargs.get('widget')
    if widget is None:                       # 'widget' not in kwargs  (the fix)
        if name in auto:        widget = ('autocomplete',)
        elif name in raw:       widget = ('rawId',)
        elif name in vert+horiz: widget = ('filtered', name in vert)
    return widget

This script transliterates that R/I impl into Python (`shadow_resolve`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH selection block of `formfield_for_manytomany`:

    if 'widget' not in kwargs:               # <-- the fix
        autocomplete_fields = get_autocomplete_fields(request)
        if name in autocomplete_fields:  kwargs['widget'] = Autocomplete(...)
        elif name in raw_id_fields:      kwargs['widget'] = ManyToManyRawId(...)
        elif name in [*filter_vertical, *filter_horizontal]:
            kwargs['widget'] = FilteredSelectMultiple(verbose_name, name in filter_vertical)

We do NOT stand up Django/the admin (heavy, and the modeled value is a pure
decision over which widget KIND the field receives). Instead we reproduce the
patched selection logic over light stand-ins: a field `name`, the caller's
`incoming` widget option, and the four classification lists (mapping.md). The
read of `get_autocomplete_fields(request)` is the list `auto`; the post-patch
guard `'widget' not in kwargs` is `incoming is None`.

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`widget.isNone` guard plus `defaultWidget`, whereas the oracle reproduces the
patched `if 'widget' not in kwargs:` cascade. A caller widget is fed to BOTH
legs and must be PRESERVED whenever present — in particular when `name` matches
one of the classification lists, the case the patch fixes (pre-fix the cascade
would have overwritten the caller widget).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 12713 (also recorded in
mapping.md).
"""
import sys

SEED = 12713
N = 120_000


# --- ORACLE: the post-patch selection block, faithful in-process replica ------
# `incoming` is None or a ('supplied', id) tuple. The four lists are name lists.
# A cascade-selected widget is one of: ('autocomplete',), ('rawId',),
# ('filtered', is_vertical). The post-patch guard runs the cascade only when no
# caller widget is present.
def oracle_resolve(name, incoming, auto, raw, vert, horiz):
    widget = incoming
    if widget is None:                                   # 'widget' not in kwargs
        if name in auto:
            widget = ('autocomplete',)
        elif name in raw:
            widget = ('rawId',)
        elif name in (list(vert) + list(horiz)):
            widget = ('filtered', name in vert)
    return widget


# --- shadow of implementation_resolveWidget (the R/I leg) ---------------------
# Mirrors Solution.lean: start from incoming; only consult the configuration
# when the caller chose nothing; autocomplete first, then raw-id, then filtered.
def shadow_resolve(name, incoming, auto, raw, vert, horiz):
    widget = incoming
    if widget is None:
        if name in auto:
            widget = ('autocomplete',)
        elif name in raw:
            widget = ('rawId',)
        elif name in (list(vert) + list(horiz)):
            widget = ('filtered', name in vert)
    return widget


def disagree(name, incoming, auto, raw, vert, horiz):
    got = oracle_resolve(name, incoming, auto, raw, vert, horiz)
    want = shadow_resolve(name, incoming, auto, raw, vert, horiz)
    if got != want:
        return ((name, incoming, auto, raw, vert, horiz), got, want)
    return None


# --- input corpus -------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning the discriminating selection clause."""
    SUP = ('supplied', 42)
    cases = [
        # THE fix: caller widget present AND name in a list -> caller widget kept
        (7, SUP, [], [], [7], []),          # name in filter_vertical
        (7, SUP, [], [], [], [7]),          # name in filter_horizontal
        (7, SUP, [7], [], [], []),          # name in autocomplete
        (7, SUP, [], [7], [], []),          # name in raw_id
        # caller widget present, name matches NOTHING -> caller widget kept
        (7, SUP, [1], [2], [3], [4]),
        # no caller widget, each classification branch
        (7, None, [7], [], [], []),         # -> autocomplete
        (7, None, [], [7], [], []),         # -> rawId
        (7, None, [], [], [7], []),         # -> filtered vertical=True
        (7, None, [], [], [], [7]),         # -> filtered vertical=False
        (7, None, [1], [2], [3], [4]),      # -> no widget (None)
        # precedence: name in several lists -> autocomplete wins
        (7, None, [7], [7], [7], [7]),
        # precedence: name in raw and filtered -> rawId wins
        (7, None, [], [7], [7], []),
        # name in both vertical and horizontal -> vertical flag True
        (7, None, [], [], [7], [7]),
        # empty everything, no caller widget -> None
        (7, None, [], [], [], []),
    ]
    return cases


def _rand_lists(rnd):
    """Four classification lists drawn from a small name pool so membership
    bites; lists may overlap (the real config can too)."""
    def mklist():
        k = next(rnd) % 4                # 0..3 names
        return [next(rnd) % 6 for _ in range(k)]   # names 0..5
    return mklist(), mklist(), mklist(), mklist()


def main() -> int:
    checked = 0

    for name, inc, auto, raw, vert, horiz in _enumerate_edge():
        d = disagree(name, inc, auto, raw, vert, horiz)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        name = next(rnd) % 6                 # name 0..5 (collides with lists)
        # caller widget present ~half the time (so the guard both fires & not)
        incoming = ('supplied', next(rnd) % 1000) if (next(rnd) % 2 == 0) else None
        auto, raw, vert, horiz = _rand_lists(rnd)
        d = disagree(name, incoming, auto, raw, vert, horiz)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
