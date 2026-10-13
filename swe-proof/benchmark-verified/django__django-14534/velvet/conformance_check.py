#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-14534 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `refinement.md`: the deep
recorded-id model of Solution.lean (`labelIdentifier` = `recordedId attrs =
attrs.lookup "id"`) transliterated to Python, differential-tested against
`patch.diff`'s behaviour over many widget-data points.

ORACLE CHOICE — why we transliterate the patched `id_for_label` body VERBATIM
instead of driving the real `BoundWidget.id_for_label` property:
  `BoundWidget.id_for_label` is a one-line `@property` reading `self.data`. To
  obtain a real `BoundWidget` whose `self.data` carries the recorded `'attrs'`
  one must construct a `Form` with a `MultipleChoiceField`/`CheckboxSelectMultiple`
  widget, bind it, build the `BoundField`, materialize `subwidgets` (which calls
  `widget.subwidgets(name, value, attrs=...)` to populate each subwidget's
  `data['attrs']['id']`) — all UNCHANGED by the patch and present only to fill in
  `self.data`. The patch changes only WHAT `id_for_label` reads back from that
  already-populated `self.data`: the synthesized `'id_%s_%s' % (name, index)`
  becomes `self.data['attrs'].get('id')`. So, per the worker prompt, the ORACLE
  is the gold-patched `id_for_label` body transliterated verbatim
  (`data['attrs'].get('id')`), driven over the space of possible `self.data`
  values (the recorded `name`, `index`, and `attrs` a `BoundWidget` can carry).
  The SHADOW is the deep model `recordedId attrs = attrs.lookup "id"` from
  Solution.lean. We differential-test over many `self.data` points. Exit 0 iff
  zero disagreements.

stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 14534
N_FUZZ = 100_000


# ---- type bijection (mapping.md §2) ----------------------------------------
# Lean `Attrs = List (String x String)` <-> Python attrs `dict[str, str]`.
# `List.lookup "id" attrs` (some v / none) <-> `attrs.get('id')` (v / None).
def attrs_to_dict(pairs):
    """Bridge a Lean-side ordered (key, value) list to a Python attrs dict.
    A name occurs at most once (mapping.md §2), so order is irrelevant to the
    observable `.get('id')`."""
    d = {}
    for k, v in pairs:
        d.setdefault(k, v)
    return d


# ---- ORACLE: patch.diff `id_for_label` body, transliterated verbatim -------
def oracle_id_for_label(data):
    """The gold-patched `BoundWidget.id_for_label` body (boundfield.py:280
    post-patch): `return self.data['attrs'].get('id')`. `data` is the widget's
    recorded `self.data` mapping."""
    return data['attrs'].get('id')


# ---- SHADOW: Solution.lean `labelIdentifier` = recordedId attrs ------------
def shadow_label_identifier(name, index, attrs_pairs):
    """labelIdentifier name index attrs = recordedId attrs = attrs.lookup "id",
    transliterated. `name`/`index` are passed but (correctly) not consulted."""
    d = attrs_to_dict(attrs_pairs)
    # recordedId attrs = attrs.lookup "id"  ->  None when absent.
    return d.get('id')


# observable equality: Option String is exact-string-or-None; compare directly.


def rand_attr_pairs(rng, with_id):
    """Build a recorded-attrs (key, value) list. When `with_id`, include an
    'id' attribute carrying a plausible recorded id (default or caller-prefixed,
    with a subwidget index)."""
    pairs = []
    # a sprinkling of unrelated attributes a real widget may record
    pool = ['class', 'required', 'disabled', 'checked', 'value', 'type', 'name']
    for _ in range(rng.randint(0, 4)):
        k = rng.choice(pool)
        pairs.append((k, str(rng.randint(0, 999))))
    if with_id:
        prefix = rng.choice(['id', 'prefix', 'custom', 'myCustomID', 'id_form'])
        field = rng.choice(['name', 'field', 'beatles', 'choices', 'opt'])
        idx = rng.randint(0, 9)
        # both the default 'id_<field>_<idx>' shape and prefixed shapes
        style = rng.randint(0, 2)
        if style == 0:
            rid = 'id_%s_%d' % (field, idx)
        elif style == 1:
            rid = '%s_%s_%d' % (prefix, field, idx)
        else:
            rid = '%s_%s' % (prefix, field)
        pairs.append(('id', rid))
    return pairs


def points(rng):
    """Yield (name, index, attrs_pairs) test points."""
    # boundary cases first (plan §4.1 step 4)
    #  - recorded id present, matching the default synthesized shape
    yield ('name', '0', [('id', 'id_name_0')])
    #  - recorded id present, caller prefix (F2P test_boundfield_subwidget_...)
    yield ('field', '0', [('id', 'prefix_field_0')])
    yield ('field', '1', [('id', 'prefix_field_1')])
    #  - NO recorded id: result must be None (F2P test_iterable_boundfield_select)
    yield ('name', '0', [])
    yield ('name', '0', [('class', 'x'), ('required', '1')])
    #  - recorded id whose value differs from the synthesized one
    yield ('name', '3', [('id', 'totally_different')])
    for _ in range(N_FUZZ):
        with_id = rng.random() < 0.6
        name = rng.choice(['name', 'field', 'beatles', 'q', ''])
        index = str(rng.randint(0, 12))
        yield (name, index, rand_attr_pairs(rng, with_id))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for name, index, attrs_pairs in points(rng):
        count += 1
        data = {'name': name, 'index': index, 'attrs': attrs_to_dict(attrs_pairs)}
        try:
            o = oracle_id_for_label(data)
            o_err = None
        except Exception as e:                       # noqa: BLE001
            o, o_err = None, type(e).__name__
        try:
            s = shadow_label_identifier(name, index, attrs_pairs)
            s_err = None
        except Exception as e:                       # noqa: BLE001
            s, s_err = None, type(e).__name__
        if (o, o_err) != (s, s_err):
            disagreements.append((name, index, attrs_pairs,
                                  (s, s_err), (o, o_err)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, index, pairs, sh, orc in disagreements:
            print("  name=%r index=%r attrs=%r shadow=%r oracle=%r"
                  % (name, index, pairs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of labelIdentifier/recordedId agrees with "
          "patch.diff id_for_label behaviour over %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
