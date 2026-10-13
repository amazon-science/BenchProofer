#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14534.

The bundle models ONE function: `BoundWidget.id_for_label`
(`django/forms/boundfield.py`). Its Lean implementation
(`implementation_idForLabel`) reports the DOM identifier to associate with a
rendered option's label by reading the value stored under the `'id'` key of the
option's attribute table:

    return attrs.lookup('id')            # some v / none

This script transliterates that R/I impl into Python (`shadow_id_for_label`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `id_for_label`:

    @property
    def id_for_label(self):
        return self.data['attrs'].get('id')   # <-- the fix

We do NOT stand up Django/forms (heavy, and the modeled value is a pure lookup
into the subwidget presentation dict). Instead we reproduce the patched body over
light stand-in subwidget dicts: a `data` dict with keys `attrs` (a dict of HTML
attributes), `name`, and `index` (mapping.md). Both legs are fed the SAME data;
they must agree on every input, including the case the patch fixes — a custom
`auto_id` prefix where `attrs['id']` differs from the pre-fix synthesized
`'id_%s_%s' % (name, index)`, and the case `attrs` has no `'id'` key (result
`None`).

The Lean `attrs` is an association list with DISTINCT keys; a Python dict has the
same semantics for `.get('id')`, so the bijection is faithful (mapping.md).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 14534 (also recorded in
mapping.md).
"""
import sys

SEED = 14534
N = 120_000


# --- ORACLE: the post-patch id_for_label, faithful in-process replica --------
# `data` is a dict with keys 'attrs' (dict[str,str]), 'name' (str), 'index'(str).
def oracle_id_for_label(data):
    return data['attrs'].get('id')


# --- shadow of implementation_idForLabel (the R/I leg) -----------------------
# Mirrors Solution.lean: return data.attrs.lookup "id".
def shadow_id_for_label(data):
    return data['attrs'].get('id')


def disagree(data):
    got = oracle_id_for_label(data)
    want = shadow_id_for_label(data)
    if got != want:
        return (data, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning the discriminating lookup clause."""
    return [
        # THE fix: custom auto_id prefix; attrs['id'] differs from synthesized id
        {'attrs': {'id': 'prefix_field_0'}, 'name': 'field', 'index': '0'},
        {'attrs': {'id': 'prefix_field_1'}, 'name': 'field', 'index': '1'},
        # no 'id' key -> None (auto_id=False case)
        {'attrs': {}, 'name': 'name', 'index': '0'},
        {'attrs': {'class': 'x'}, 'name': 'name', 'index': '0'},
        # default-style id present and matching the would-be synthesis
        {'attrs': {'id': 'id_name_0'}, 'name': 'name', 'index': '0'},
        # other attributes present alongside id
        {'attrs': {'class': 'c', 'id': 'myCustomID', 'checked': 'true'},
         'name': 'f', 'index': '3'},
        # empty strings
        {'attrs': {'id': ''}, 'name': '', 'index': ''},
    ]


_KEYS = ['class', 'checked', 'value', 'type', 'name']
_NAMES = ['field', 'name', 'f', 'beatles', '']
_IDXS = ['0', '1', '2', '10', '']


def _rand_data(rnd):
    attrs = {}
    n_extra = next(rnd) % 4          # 0..3 non-id attributes
    for _ in range(n_extra):
        k = _KEYS[next(rnd) % len(_KEYS)]
        attrs[k] = 'v%d' % (next(rnd) % 100)
    name = _NAMES[next(rnd) % len(_NAMES)]
    index = _IDXS[next(rnd) % len(_IDXS)]
    # 'id' present in ~half the cases, with values that both match and diverge
    # from the pre-fix synthesized 'id_%s_%s' % (name, index).
    if next(rnd) % 2 == 0:
        choice = next(rnd) % 3
        if choice == 0:
            attrs['id'] = 'id_%s_%s' % (name, index)        # default-style
        elif choice == 1:
            attrs['id'] = 'prefix_%s_%s' % (name, index)    # custom prefix
        else:
            attrs['id'] = 'custom%d' % (next(rnd) % 1000)    # arbitrary
    return {'attrs': attrs, 'name': name, 'index': index}


def main() -> int:
    checked = 0

    for data in _enumerate_edge():
        d = disagree(data)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        data = _rand_data(rnd)
        d = disagree(data)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
