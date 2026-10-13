#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12708.

The changed selection operation is modelled DEEPLY in model.py (the `selects`
filter and the `count_selected` fold over candidate-constraint attribute codes),
NOT behind a consumed axiom. G-AX therefore validates that deep model against
the REAL repository callee it abstracts -- the per-constraint matching loop of
`BaseDatabaseSchemaEditor._constraint_names` -- driven by the exact constraint
kwargs the composite-index removal passes (`{'index': True, 'unique': False}`).

It also validates the A-reference attribute-bit encoding: a composite UNIQUE
constraint is reported by introspection as an index AND unique, and a plain
composite index as an index that is not unique (so the two are distinguishable
on the same columns). These are the documented introspection contracts the deep
model relies on.

Method (no live database required): the real `_constraint_names` filtering loop
is pure Python over the dicts returned by `introspection.get_constraints`. We
load the REAL method body straight out of the patched module
(`django/db/backends/base/schema.py`) at the repository root, bind it as an
unbound function, and drive it with a minimal stub connection whose
`get_constraints` returns synthetic introspection dicts in the exact shape the
backends emit. Loading the method out of the source file (rather than importing
the whole package) keeps the check faithful to the code at this commit and free
of unrelated import-time dependencies. We then assert, over boundary +
exhaustive small + randomized fuzz candidate sets, that the names the real
filter selects for `{'index': True, 'unique': False}` are exactly the codes the
deep model's `selects` keeps, and that |selected| == model `count_selected`.

Imports: the standard library only. Exit 0 iff every observation matches the
model.
"""
import ast
import itertools
import os
import random
import sys
import types


# --- locate and load the REAL _constraint_names from the patched module ------

def _find_schema_source():
    """Return the path to django/db/backends/base/schema.py for the repo this
    check runs against (the patched module). In the G-AX container the repo is
    at /testbed; we also probe the importable django package and a few common
    roots so the check runs unchanged on the host."""
    candidates = []
    env_root = os.environ.get('REPO_ROOT')
    if env_root:
        candidates.append(os.path.join(env_root, 'django/db/backends/base/schema.py'))
    candidates.append('/testbed/django/db/backends/base/schema.py')
    try:
        import django  # noqa: F401  (only to locate the installed package dir)
        candidates.append(os.path.join(
            os.path.dirname(django.__file__),
            'db/backends/base/schema.py'))
    except Exception:
        pass
    candidates.append(os.path.join(os.getcwd(),
                                   'django/db/backends/base/schema.py'))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    raise RuntimeError("could not locate django/db/backends/base/schema.py; "
                       "set REPO_ROOT to the repository root")


def _load_real_constraint_names():
    """Extract the REAL `_constraint_names` function source from the patched
    module and compile it into a standalone unbound function (no package
    import, so no unrelated import-time dependencies)."""
    path = _find_schema_source()
    src = open(path).read()
    mod = ast.parse(src)
    fn = None
    for node in ast.walk(mod):
        if isinstance(node, ast.FunctionDef) and node.name == '_constraint_names':
            fn = node
            break
    if fn is None:
        raise RuntimeError("_constraint_names not found in %s" % path)
    import textwrap
    # py3.6 image: ast.get_source_segment is 3.8+. The FunctionDef spans
    # fn.lineno..(next top-of-class sibling); slice by line + decreasing
    # indent instead. end_lineno is also 3.8+, so scan for the first
    # subsequent line indented at or below the def's own indent.
    lines = src.splitlines(True)
    start = fn.lineno - 1
    def_indent = len(lines[start]) - len(lines[start].lstrip())
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped and not stripped.startswith('#'):
            ind = len(lines[j]) - len(lines[j].lstrip())
            if ind <= def_indent:
                end = j
                break
    func_src = textwrap.dedent(''.join(lines[start:end]))
    ns = {}
    exec(compile(func_src, path, 'exec'), ns)
    return ns['_constraint_names']


REAL_CONSTRAINT_NAMES = _load_real_constraint_names()


# --- model.py deep-model reference (kept in lock-step with model.py) ---------

def m_is_index(code):
    return code % 2 == 1


def m_is_unique(code):
    return (code // 2) % 2 == 1


def m_selects(code):
    # model.py `selects`: an index AND not unique
    return m_is_index(code) and not m_is_unique(code)


def m_count_selected(codes):
    # model.py `count_selected`
    return sum(1 for c in codes if m_selects(c))


# --- introspection-dict shape produced by the real backends ------------------
# A composite UNIQUE constraint:        index=True,  unique=True
# A plain composite (index_together):   index=True,  unique=False
# Anything else on the columns:         index=False (unique/check/fk/pk)
# We encode a candidate by the 2-bit attribute code used by model.py:
#   bit0 = is_index, bit1 = is_unique  -> code in {0,1,2,3}

def infodict_for_code(code, columns):
    """The introspection dict the real backends return for a constraint with
    the given (is_index, is_unique) attribute code on `columns`."""
    return {
        'columns': list(columns),
        'primary_key': False,
        'unique': m_is_unique(code),
        'foreign_key': None,
        'check': False,
        'index': m_is_index(code),
        # `type` is present for non-unique indexes in real introspection; the
        # filter under test does not constrain it, so any value is fine.
        'type': 'idx',
    }


# --- minimal stubs so the REAL _constraint_names runs without a database -----

class _StubCursor:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _StubIntrospection:
    def __init__(self, constraints):
        self._constraints = constraints

    def identifier_converter(self, name):
        return name

    def get_constraints(self, cursor, table_name):
        return self._constraints


class _StubConnection:
    def __init__(self, constraints):
        self.introspection = _StubIntrospection(constraints)

    def cursor(self):
        return _StubCursor()


class _StubMeta:
    db_table = 'sometable'


class _StubModel:
    _meta = _StubMeta()


class _StubEditor:
    def __init__(self, constraints):
        self.connection = _StubConnection(constraints)


# bind the real function as a method on the stub editor
_StubEditor._constraint_names = REAL_CONSTRAINT_NAMES


# The columns the composite index is declared over (kept constant; the filter
# matches on column equality and we put every candidate on these columns).
COLUMNS = ['pink', 'weight']


def real_selected(codes, **kwargs):
    """Run the REAL _constraint_names over candidate constraints carrying the
    given attribute `codes`, returning (names_list, names_set)."""
    constraints = {}
    for i, code in enumerate(codes):
        constraints['c_%d' % i] = infodict_for_code(code, COLUMNS)
    editor = _StubEditor(constraints)
    names = editor._constraint_names(_StubModel(), COLUMNS, exclude=set(), **kwargs)
    return names, set(names)


def check_set(codes):
    """Assert the real filter (post-patch kwargs) selects exactly the codes the
    deep model keeps."""
    names, selected = real_selected(codes, index=True, unique=False)
    expected_names = {'c_%d' % i for i, code in enumerate(codes) if m_selects(code)}
    assert selected == expected_names, (
        "deep model unsound on codes=%r: real _constraint_names selected %r, "
        "model `selects` keeps %r" % (codes, selected, expected_names))
    assert len(names) == m_count_selected(codes), (
        "count mismatch on codes=%r: real filter |selected|=%d, model "
        "count_selected=%d" % (codes, len(names), m_count_selected(codes)))


def check_attribute_reference():
    """A-reference: confirm the two co-located constraints are distinguishable.
    A unique constraint (code 3: index+unique) is NOT selected by the removal
    filter; a plain index (code 1: index, not unique) IS. This is the exact
    discriminating behaviour the fix relies on."""
    _, selected = real_selected([3, 1], index=True, unique=False)
    assert selected == {'c_1'}, (
        "the co-located unique constraint must be excluded; got %r" % (selected,))
    # the pre-patch over-broad filter {'index': True} would select BOTH:
    _, overbroad = real_selected([3, 1], index=True)
    assert overbroad == {'c_0', 'c_1'}, (
        "sanity: the index-only filter must be ambiguous here; got %r" % (overbroad,))


def main():
    # --- A-reference discriminating scenario --------------------------------
    check_attribute_reference()

    # --- boundary candidate sets --------------------------------------------
    boundary = [
        [],
        [0], [1], [2], [3],
        [1, 3],        # plain index + co-located unique (the bug scenario)
        [3, 1],
        [1, 1],        # two plain indexes (ambiguous even post-fix -> count 2)
        [3, 3],        # two uniques, no plain index -> count 0
        [0, 1, 2, 3],
        [1, 2, 3, 0],
    ]
    for codes in boundary:
        check_set(codes)

    # --- exhaustive small candidate sets over the 4 attribute codes ---------
    for n in range(0, 6):
        for codes in itertools.product(range(4), repeat=n):
            check_set(list(codes))

    # --- randomized fuzz (longer sets) --------------------------------------
    rng = random.Random(12708)
    for _ in range(20000):
        n = rng.randint(0, 16)
        codes = [rng.randint(0, 3) for _ in range(n)]
        check_set(codes)

    print("G-AX OK: deep model `selects`/`count_selected` == real "
          "_constraint_names filter ({'index': True, 'unique': False}) on "
          "%d boundary + exhaustive(n<=5) + 20000 fuzz candidate sets; "
          "co-located unique constraint correctly excluded." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
