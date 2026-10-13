#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12708 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Invariant/Assert lines removed; nothing else touched), and the
@Pure helpers `is_index` / `is_unique` copied over as plain functions. There
are no @ContractOnly callees; the impl indexes a plain List[int], so no PSeq
shim is needed at runtime.

ORACLE: the REAL patched removal pipeline the model models per mapping.md --
`BaseDatabaseSchemaEditor.alter_index_together` (deletion branch) ->
`_delete_composed_index` -> `_constraint_names`, imported from the patched
repo (the gate applies the gold patch to /testbed before this script runs;
PYTHONPATH=/testbed makes it importable). The pipeline is driven end to end
with a minimal stub connection whose introspection returns synthetic
constraint dicts in the exact backend shape (same stub strategy as
axiom_check.py), so the keyword filters the removal passes come from the real
code path, not from this script. A recording subclass observes how many
constraint names the real filter selects; that count is the oracle output.
Downstream SQL emission is out of the modeled scope and is satisfied by
collect_sql mode plus a pass-through quote_name -- the count is taken
upstream of it.

Type bridge (mapping.md section 2): each candidate constraint <-> one int
attribute code; bit 0 of the code is the constraint's `index` introspection
attribute and bit 1 its `unique` attribute. The bridge recovers the two bits
with the same arithmetic the model uses (code % 2, (code // 2) % 2), so it is
well-defined for every int the model's precondition admits. The modeled
result is the COUNT of selected constraints; the oracle count is compared to
the shadow's return value with ==. As a consistency cross-check, the pipeline
must raise its ambiguous-removal ValueError iff that count != 1.

Input domain: the model's precondition admits any List[int]. Boundary cases
cover the empty list, each single 2-bit code, the co-located unique+index
pairs, ambiguous/empty selections, and full-code permutations; fuzz draws
lists of length 0..16 with codes mostly in 0..3 plus mixed-sign and
large-magnitude ints (bridged via their two attribute bits).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz lists.
Pinned fuzz seed: 120708.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain `random`; py3.6-compatible).
"""
import json
import random
import sys

SEED = 120708
N_FUZZ = 100000


# --- pure helpers from model.py, decorators stripped -------------------------

def is_index(code):
    """Whether a candidate constraint is (backed by) a secondary index:
    bit 0 of its attribute code."""
    return code % 2 == 1


def is_unique(code):
    """Whether a candidate constraint enforces uniqueness: bit 1 of its
    attribute code."""
    return (code // 2) % 2 == 1


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def selected_for_removal(constraints):
    selected = 0
    i = len(constraints)
    while i > 0:
        code = constraints[i - 1]
        if is_index(code) and not is_unique(code):
            selected = selected + 1
        i = i - 1
    return selected


# --- bridge: attribute codes -> introspection dicts (backend shape) ----------
# The columns the composite index is declared over (constant; every candidate
# sits on these columns, matching the post-column-match candidate set the
# model abstracts -- mapping.md section 2).
COLUMNS = ['pink', 'weight']


def infodict_for_code(code):
    """The introspection dict the backends return for a constraint carrying
    the given attribute code on COLUMNS."""
    return {
        'columns': list(COLUMNS),
        'primary_key': False,
        'unique': is_unique(code),
        'foreign_key': None,
        'check': False,
        'index': is_index(code),
        # `type` is not constrained by the filter under test.
        'type': 'idx',
    }


# --- minimal stubs so the REAL pipeline runs without a database --------------

class _StubCursor(object):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _StubIntrospection(object):
    def __init__(self, constraints):
        self._constraints = constraints

    def identifier_converter(self, name):
        return name

    def get_constraints(self, cursor, table_name):
        return self._constraints


class _StubOps(object):
    def quote_name(self, name):
        return name


class _StubFeatures(object):
    can_rollback_ddl = False


class _StubConnection(object):
    ops = _StubOps()
    features = _StubFeatures()

    def __init__(self, constraints):
        self.introspection = _StubIntrospection(constraints)

    def cursor(self):
        return _StubCursor()


class _StubField(object):
    def __init__(self, column):
        self.column = column


class _StubMeta(object):
    db_table = 'sometable'
    constraints = []
    indexes = []

    def get_field(self, name):
        return _StubField(name)


class _StubModel(object):
    _meta = _StubMeta()


def check_case(recording_editor_cls, codes):
    """Run shadow and oracle on one candidate-code list; return an error
    string on disagreement, else None."""
    shadow_out = selected_for_removal(codes)

    constraints = {}
    for i, code in enumerate(codes):
        constraints['c_%d' % i] = infodict_for_code(code)
    editor = recording_editor_cls(_StubConnection(constraints),
                                  collect_sql=True)
    raised = False
    try:
        # Real deletion branch: remove the composite index over COLUMNS.
        editor.alter_index_together(_StubModel(), [list(COLUMNS)], [])
    except ValueError:
        # The pipeline's ambiguous-removal error (selection count != 1).
        raised = True
    if len(editor.recorded_counts) != 1:
        return ("HARNESS ERROR\n  codes=%r\n  expected exactly one selection "
                "by the real pipeline, observed %d"
                % (codes, len(editor.recorded_counts)))
    real_out = editor.recorded_counts[0]

    if shadow_out != real_out:
        return ("DISAGREEMENT\n  codes=%r\n  shadow=%r\n  real=%r"
                % (codes, shadow_out, real_out))
    # Consistency cross-check: the error is raised iff the count is not 1.
    if raised != (real_out != 1):
        return ("DISAGREEMENT (error semantics)\n  codes=%r\n  count=%r\n  "
                "ValueError raised=%r" % (codes, real_out, raised))
    return None


def boundary_cases():
    import itertools
    cases = [
        [],
        [0], [1], [2], [3],
        [1, 3],        # plain index + co-located unique constraint
        [3, 1],
        [1, 1],        # two plain indexes: ambiguous selection (count 2)
        [3, 3],        # only uniques: empty selection (count 0)
        [0, 2],        # no index at all
        [0, 1, 2, 3],
        [1, 2, 3, 0],
        [-1], [-2], [-3], [-4],          # negative codes (bits still defined)
        [4], [5], [6], [7],              # codes beyond two bits
        [2 ** 40 + 1, -(2 ** 40)],       # large magnitudes
    ]
    for perm in itertools.permutations([0, 1, 2, 3]):
        cases.append(list(perm))
    return cases


def rand_codes(rng):
    n = rng.randint(0, 16)
    codes = []
    for _ in range(n):
        kind = rng.random()
        if kind < 0.7:
            codes.append(rng.randint(0, 3))
        elif kind < 0.9:
            codes.append(rng.randint(-8, 8))
        else:
            codes.append(rng.randint(-2 ** 40, 2 ** 40))
    return codes


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    # REAL patched callee chain (PYTHONPATH=/testbed, gold patch applied by
    # the gate).
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor

    class RecordingEditor(BaseDatabaseSchemaEditor):
        """Real editor; records the size of each real selection while
        delegating to the real filter unchanged."""

        def __init__(self, *args, **kwargs):
            super(RecordingEditor, self).__init__(*args, **kwargs)
            self.recorded_counts = []

        def _constraint_names(self, *args, **kwargs):
            names = super(RecordingEditor, self)._constraint_names(
                *args, **kwargs)
            self.recorded_counts.append(len(names))
            return names

    checked = 0
    n_boundary = 0
    for codes in boundary_cases():
        err = check_case(RecordingEditor, codes)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(RecordingEditor, rand_codes(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real composite-index removal selection "
          "count on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
