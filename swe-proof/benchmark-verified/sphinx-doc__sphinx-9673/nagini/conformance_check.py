#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9673 (nagini).

SHADOW (provenance "direct"): the two `# impl-start` / `# impl-end` regions of
`model.py`, copied VERBATIM with only the contract calls removed (`Requires`,
`Ensures`, `Invariant`, `Assert`, `Acc`, and the `# invariants-start/-end`
markers).  No restructuring, no renaming.  The two `@Pure` helpers
(`has_return_description` / `has_return_type`) are copied over too, minus their
contracts, with `PSeq`/`ToSeq` realized by the immutable-tuple shim used by the
other nagini bundles in this corpus; the impl regions themselves never call
them (they appear only inside contracts), so they are checked here as the
POSTCONDITION surface: the fold form of the spec is diffed against the real
patched function on every case alongside the loop form of the impl.  There are
no `@ContractOnly` callees in this bundle (mapping.md §3: zero axioms), so
nothing is axiomatized away.

ORACLE: the REAL patched repo function, CALLED, not transliterated —
`sphinx.ext.autodoc.typehints.augment_descriptions_with_types`
(`sphinx/ext/autodoc/typehints.py:130`, mapping.md §1).  The gate applies the
gold patch to /testbed before this script runs and PYTHONPATH=/testbed makes
the patched module importable, so both gold hunks are live in the callee.  It
returns `None` and mutates a docutils `field_list` in place, so it is driven
through a freshly built `nodes.field_list` and observed through the fields it
APPENDS beyond the pre-existing children:

  * `augment_return_typefield`  -> observable: does an appended field carry the
    field_name 'rtype'?  (`typehints.py:168-173`, the emission block whose
    decision the model abstracts to its bool Result.)  Only the key 'return'
    ever produces a field named 'rtype'; parameter back-fill produces
    'type <name>', so the observable is exact.
  * `name_is_return_key`        -> observable: is the annotated name SKIPPED by
    the back-fill loop guard (`typehints.py:158-160`)?  Driven with the single
    existing field 'param <NAME>' and the annotation table {NAME: 'int'}, so
    NAME is in has_description and not in has_type and the guard is the only
    thing that can suppress the 'type <NAME>' field: skipped <=> 'type <NAME>'
    absent from the appended fields.

TYPE BRIDGE (mapping.md §2, inverted).  The model works over integer leading-
token CODES; the real function wants docutils fields carrying real field-name
strings, plus a `Dict[str, str]` annotation table.  Inverting §2:

    code 2  ('return'  ↦ 2)  ->  a field name whose leading token is 'return'
    code 3  ('returns' ↦ 3)  ->  a field name whose leading token is 'returns'
    code 4  ('rtype'   ↦ 4)  ->  a field name whose leading token is 'rtype'
    code ∉ {2,3,4}           ->  a field name whose leading-token
                                 classification does not touch the 'return'
                                 key of has_description / has_type
    return_annotated: True   ->  annotations contains the literal key 'return'
                                 (`typehints.py:35` stores the return
                                 annotation under that key); False -> it does not
    bool Result              ->  an 'rtype' field is appended
    int name identifiers     ->  name strings, 'return' ↦ return_key_a,
                                 'returns' ↦ return_key_b, equal ints <-> equal
                                 strings

The last clause of the code-∉{2,3,4} row is §2's own parenthetical ("any other
token ... it does not bear on the return decision") read as the definition of
the class, and it is where this abstraction is genuinely lossy: 'param' and
'type' fields join their remaining tokens into a NAME, and the three degenerate
field names whose derived name is literally 'return' ('param return',
'param <x> return', 'type return') DO touch the 'return' key while still having
a leading token outside {return, returns, rtype}.  Those three shapes are
therefore not in the class the bridge defines.  Rather than drop them silently,
they are run as an explicitly labelled BOUNDARY PROBE (probe_degenerate below)
whose outcome is printed and reported in the structured JSON line, so the
exclusion is visible evidence rather than a hole: they are unreachable from any
real Python signature ('return' is a keyword, so no parameter can be named it)
and the bundle's G-PANEL-2 record already adjudicates this same boundary as a
known lossy-modeling edge, not spec drift.  The probe does not gate the exit
code; the in-domain diff does.

INPUT DOMAIN AND COUNT.  `Requires` is only `Acc(list_pred(field_kinds), 1/2)`
(read-only permission) — every finite int list satisfies it, so the real
constraint is the bridge above.  Modulo the bridge, the modeled input space is
FINITE IN THE CODE CLASSES: a field list is a word over the 4-letter alphabet
{2, 3, 4, other} and the decision depends on nothing else.  So the check is
EXHAUSTIVE over that alphabet up to length 7 (sum_{n<=7} 4^n = 21845 words) in
both settings of `return_annotated` = 43690 cases, which is a stronger check
than sampling: every reachable classification pattern of a <=7-field docstring
is covered, not just a random slice.  Seeded fuzz then fills the count to
>= 1e5 over the SAME space with longer field lists (up to 14) and randomized
realizations of each code class (so 'return the value', 'returns decremented
number', 'rtype extra', 'param x y', 'Returns' (the Google-header homograph),
'returned', '' and friends all get exercised, not one canonical spelling), plus
extra non-'return' annotation keys.  Boundary cases run first, including the
empty field list, every singleton, the exact F2P shape (a lone plural
':returns:' field with a return annotation and no rtype field -> rtype must be
emitted), the pre-patch discriminator, and each impl branch at least once.
`name_is_return_key`'s space is finite and small under the bridge, so it is
enumerated EXHAUSTIVELY over the name pool.  Pinned seed: SEED = 9673 (recorded
in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit code is 1.  stdlib + docutils + sphinx only.
"""
import itertools
import json
import random
import sys

SEED = 9673
N_FUZZ = 80_000
EXHAUSTIVE_LEN = 7
MAX_FUZZ_FIELDS = 14


# ---------------------------------------------------------------------------
# PSeq shim: Nagini's immutable sequence carrier, realized as a tuple wrapper.
# Only the operations the copied @Pure helpers use are provided.
# ---------------------------------------------------------------------------
class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# SHADOW — model.py's `pure` region, contracts stripped, verbatim otherwise.
# These are the postcondition surface of `augment_return_typefield`.
# ---------------------------------------------------------------------------
def has_return_description(kinds):
    """True iff the field collection contains a return-DESCRIPTION field under
    EITHER spelling: the short marker (code 2) OR its plural (code 3)."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 2 or kinds[0] == 3 or has_return_description(kinds.drop(1))


def has_return_type(kinds):
    """True iff the field collection contains a return-TYPE field (code 4)."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 4 or has_return_type(kinds.drop(1))


# ---------------------------------------------------------------------------
# SHADOW — model.py's two impl regions, copied VERBATIM with only the contract
# calls (Requires/Ensures/Invariant/Assert/Acc) and the invariants markers
# removed.  Nothing renamed, nothing restructured.
# ---------------------------------------------------------------------------
def shadow_augment_return_typefield(field_kinds, return_annotated):
    # impl-start
    described = False
    typed = False
    i = len(field_kinds)
    while i > 0:
        c = field_kinds[i - 1]
        if c == 2 or c == 3:
            # a return-description field under either spelling
            described = True
        elif c == 4:
            # a return-type field
            typed = True
        i = i - 1
    if return_annotated:
        if described and not typed:
            return True
    return False
    # impl-end


def shadow_name_is_return_key(name, return_key_a, return_key_b):
    # impl-start
    if name == return_key_a or name == return_key_b:
        return True
    return False
    # impl-end


def spec_augment_return_typefield(field_kinds, return_annotated):
    """The Ensures of `augment_return_typefield`, verbatim (model.py:81-83)."""
    return (return_annotated and
            has_return_description(ToSeq(field_kinds)) and
            not has_return_type(ToSeq(field_kinds)))


def spec_name_is_return_key(name, return_key_a, return_key_b):
    """The Ensures of `name_is_return_key`, verbatim (model.py:121)."""
    return name == return_key_a or name == return_key_b


# ---------------------------------------------------------------------------
# TYPE BRIDGE — code class -> concrete field-name realizations (mapping.md §2
# inverted).  Every realization of the OTHER class has a leading token outside
# {return, returns, rtype} AND a classification that does not touch the
# 'return' key of has_description / has_type.
# ---------------------------------------------------------------------------
CODE_RETURN_SHORT = 2      # leading token 'return'
CODE_RETURN_PLURAL = 3     # leading token 'returns'
CODE_RETURN_TYPE = 4       # leading token 'rtype'
OTHER_CODES = (0, 1, 5)    # any code not in {2, 3, 4}

REALIZATIONS = {
    CODE_RETURN_SHORT: [
        'return',
        'return the value',
        'return  spaced  words',
    ],
    CODE_RETURN_PLURAL: [
        'returns',
        'returns decremented number',
        'returns  a  thing',
    ],
    CODE_RETURN_TYPE: [
        'rtype',
        'rtype extra',
        'rtype  x  y',
    ],
    # code not in {2,3,4}: does not bear on the 'return' key
    0: [
        'param x',
        'param',
        'param x y',
        'param value',
        'param returns',          # derived name 'returns' != 'return': in class
    ],
    1: [
        'type y',
        'type value',
        'type x y',
        'type returns',           # derived name 'returns' != 'return': in class
    ],
    5: [
        'meta a',
        'raises ValueError',
        'keyword k',
        'Returns',                # Google-style header homograph, not a match
        'Return',
        'returned',
        'returnss',
        'rtypes',
        'vartype v',
        '',
    ],
}

# Excluded from the bridge's OTHER class, run as a labelled boundary probe:
# leading token outside {return, returns, rtype} but derived name == 'return'.
DEGENERATE_OTHER = ['param return', 'param x return', 'type return']

RET_ANN_TEXT = 'int'
EXTRA_KEYS = ['x', 'y', 'value', 'n', 'rtype', 'param', 'self']


def realize_fields(kinds, pick):
    """kinds (list of int codes) -> list of concrete field-name strings.
    `pick(code, index)` chooses which realization of the class to use."""
    return [pick(c, i) for i, c in enumerate(kinds)]


def make_annotations(return_annotated, extra=()):
    """return_annotated -> an annotation table containing the literal key
    'return' iff True (mapping.md §2; typehints.py:35)."""
    ann = {}
    for k, v in extra:
        if k != 'return':
            ann[k] = v
    if return_annotated:
        ann['return'] = RET_ANN_TEXT
    return ann


# ---------------------------------------------------------------------------
# ORACLE — the REAL patched repo function, called.
# ---------------------------------------------------------------------------
def appended_field_names(augment, field_names, annotations):
    """Drive the real `augment_descriptions_with_types` and return the ordered
    field_name strings of the fields it APPENDED to the field list."""
    from docutils import nodes
    node = nodes.field_list()
    for fname in field_names:
        f = nodes.field()
        f += nodes.field_name('', fname)
        f += nodes.field_body('', nodes.paragraph('', 'description text'))
        node += f
    n_before = len(node)
    augment(node, annotations)
    return [f[0].astext() for f in list(node)[n_before:]]


def oracle_emits_rtype(augment, field_names, annotations):
    """Observable for `augment_return_typefield`: was an 'rtype' field
    appended? (typehints.py:168-173)"""
    return 'rtype' in appended_field_names(augment, field_names, annotations)


def oracle_name_skipped(augment, name):
    """Observable for `name_is_return_key`: did the back-fill loop guard skip
    this annotated name? (typehints.py:158-160)

    With the single existing field 'param <name>', has_description == {name}
    and has_type == {} for any single-token name, so the 'type <name>' field is
    appended iff the guard did NOT skip the name."""
    appended = appended_field_names(augment, ['param ' + name],
                                    {name: RET_ANN_TEXT})
    return ('type ' + name) not in appended


# ---------------------------------------------------------------------------
# Case generation.
# ---------------------------------------------------------------------------
def boundary_cases():
    """(kinds, field_names, return_annotated, extra_annotation_keys, label)."""
    R, P, T, O = CODE_RETURN_SHORT, CODE_RETURN_PLURAL, CODE_RETURN_TYPE, 0
    cases = [
        ([], [], False, (), 'empty field list, no annotation'),
        ([], [], True, (), 'empty field list, return annotated'),
        ([R], ['return'], True, (), 'short spelling documented -> rtype'),
        # the exact F2P shape: ':returns:' + a return annotation, no rtype
        ([P], ['returns'], True, (), 'F2P: plural spelling documented -> rtype'),
        ([P], ['returns decremented number'], True, (),
         'F2P verbatim marker text'),
        ([P], ['returns'], False, (), 'plural spelling, no return annotation'),
        ([R], ['return'], False, (), 'short spelling, no return annotation'),
        ([T], ['rtype'], True, (), 'declared type only -> no rtype'),
        ([O], ['param x'], True, (('x', 'int'),), 'param only -> no rtype'),
        ([R, T], ['return', 'rtype'], True, (), 'short + already typed'),
        ([T, R], ['rtype', 'return'], True, (), 'already typed, rtype first'),
        ([P, T], ['returns', 'rtype'], True, (), 'plural + already typed'),
        ([T, P], ['rtype', 'returns'], True, (), 'plural, rtype first'),
        ([R, P], ['return', 'returns'], True, (), 'both spellings present'),
        ([P, R], ['returns', 'return'], True, (), 'both spellings, reversed'),
        ([R, P, T], ['return', 'returns', 'rtype'], True, (), 'all three'),
        ([O, P], ['param x', 'returns'], True, (('x', 'int'),),
         'param back-fill alongside the plural return description'),
        ([5], ['Returns'], True, (),
         'Google-style header homograph is NOT the reST marker'),
        ([5], ['returned'], True, (), 'prefix-only token is not a match'),
        ([5], [''], True, (), 'empty field name'),
        ([O], ['param returns'], True, (),
         "derived name 'returns' does not touch the 'return' key"),
    ]
    return cases


def exhaustive_cases():
    """Every word over the 4 code classes {2,3,4,other} up to EXHAUSTIVE_LEN,
    in both settings of return_annotated.  The decision depends on nothing but
    these classes, so this covers the modeled space exactly for <=7 fields."""
    alphabet = (CODE_RETURN_SHORT, CODE_RETURN_PLURAL, CODE_RETURN_TYPE, 0)
    out = []
    rot = 0
    for n in range(EXHAUSTIVE_LEN + 1):
        for word in itertools.product(alphabet, repeat=n):
            kinds = list(word)
            # rotate realizations so the exhaustive pass is not pinned to one
            # spelling per class, while staying fully deterministic
            names = []
            for c in kinds:
                pool = REALIZATIONS[c]
                names.append(pool[rot % len(pool)])
                rot += 1
            for ann in (False, True):
                out.append((kinds, names, ann, (), 'exhaustive len=%d' % n))
    return out


def fuzz_case(rng):
    n = rng.randint(0, MAX_FUZZ_FIELDS)
    kinds = []
    names = []
    for _ in range(n):
        r = rng.random()
        if r < 0.22:
            c = CODE_RETURN_SHORT
        elif r < 0.46:
            c = CODE_RETURN_PLURAL
        elif r < 0.66:
            c = CODE_RETURN_TYPE
        else:
            c = rng.choice(OTHER_CODES)
        kinds.append(c)
        names.append(rng.choice(REALIZATIONS[c]))
    extra = []
    for _ in range(rng.randint(0, 3)):
        extra.append((rng.choice(EXTRA_KEYS), rng.choice(['int', 'str', ''])))
    return kinds, names, rng.random() < 0.6, tuple(extra), 'fuzz'


def name_pool():
    """The finite name-identifier pool for `name_is_return_key`, under the
    bridge 'return' -> return_key_a, 'returns' -> return_key_b.  Single tokens
    only (a name identifier is atomic; a multi-token field name would be
    re-derived by the repo's ' '.join and is a different carrier)."""
    return ['return', 'returns', 'Return', 'Returns', 'returned', 'returnss',
            'rtype', 'rtypes', 'param', 'type', 'x', 'y', 'value', 'n',
            'self', 'cls', 'return_', '_return', 'ret', 'returnvalue',
            'foo_bar', 'a']


# ---------------------------------------------------------------------------
def main():
    from sphinx.ext.autodoc.typehints import augment_descriptions_with_types \
        as augment                                       # REAL patched callee

    rng = random.Random(SEED)

    cases = boundary_cases()
    n_boundary = len(cases)
    cases += exhaustive_cases()
    n_exhaustive = len(cases) - n_boundary
    for _ in range(N_FUZZ):
        cases.append(fuzz_case(rng))

    checked = 0
    branches = {'described_short': 0, 'described_plural': 0, 'typed': 0,
                'other': 0, 'loop_zero': 0, 'result_true': 0,
                'result_false': 0}

    for kinds, names, return_annotated, extra, label in cases:
        annotations = make_annotations(return_annotated, extra)
        shadow = shadow_augment_return_typefield(kinds, return_annotated)
        spec = spec_augment_return_typefield(kinds, return_annotated)
        oracle = oracle_emits_rtype(augment, names, annotations)
        if shadow != oracle or spec != oracle:
            print('G-CONF FAIL: augment_return_typefield disagrees with the '
                  'real patched augment_descriptions_with_types')
            print('  case            : %s' % label)
            print('  field_kinds     : %r' % (kinds,))
            print('  field names     : %r' % (names,))
            print('  return_annotated: %r' % (return_annotated,))
            print('  annotations     : %r' % (annotations,))
            print('  shadow (impl)   : %r' % (shadow,))
            print('  shadow (Ensures): %r' % (spec,))
            print('  oracle (rtype?) : %r' % (oracle,))
            return 1
        checked += 1
        if not kinds:
            branches['loop_zero'] += 1
        for c in kinds:
            if c == CODE_RETURN_SHORT:
                branches['described_short'] += 1
            elif c == CODE_RETURN_PLURAL:
                branches['described_plural'] += 1
            elif c == CODE_RETURN_TYPE:
                branches['typed'] += 1
            else:
                branches['other'] += 1
        branches['result_true' if shadow else 'result_false'] += 1

    # --- name_is_return_key: the name pool is finite, so enumerate it all ---
    pool = name_pool()
    ids = dict((nm, i) for i, nm in enumerate(pool))
    id_short, id_plural = ids['return'], ids['returns']
    for nm in pool:
        shadow = shadow_name_is_return_key(ids[nm], id_short, id_plural)
        spec = spec_name_is_return_key(ids[nm], id_short, id_plural)
        oracle = oracle_name_skipped(augment, nm)
        if shadow != oracle or spec != oracle:
            print('G-CONF FAIL: name_is_return_key disagrees with the real '
                  'patched back-fill skip guard')
            print('  name            : %r (id %d)' % (nm, ids[nm]))
            print('  return_key_a    : %r (id %d)' % ('return', id_short))
            print('  return_key_b    : %r (id %d)' % ('returns', id_plural))
            print('  shadow (impl)   : %r' % (shadow,))
            print('  shadow (Ensures): %r' % (spec,))
            print('  oracle (skipped): %r' % (oracle,))
            return 1
        checked += 1
    n_names = len(pool)

    # --- labelled boundary probe: the three degenerate field names the bridge
    # --- excludes from the code-not-in-{2,3,4} class (see the docstring).
    probe = []
    for deg in DEGENERATE_OTHER:
        for companion, companion_kind in ((None, None), ('returns',
                                                         CODE_RETURN_PLURAL)):
            names = ([companion] if companion else []) + [deg]
            kinds = ([companion_kind] if companion else []) + [0]
            ann = make_annotations(True)
            s = shadow_augment_return_typefield(kinds, True)
            o = oracle_emits_rtype(augment, names, ann)
            if s != o:
                probe.append({'field_names': names, 'kinds': kinds,
                              'shadow': s, 'oracle': o})

    print('G-CONF OK: shadow (contract-stripped impl regions of model.py, plus '
          'their Ensures folds) == the REAL patched '
          'sphinx.ext.autodoc.typehints.augment_descriptions_with_types on '
          '%d inputs (%d boundary incl. the F2P plural-":returns:" shape, '
          '%d EXHAUSTIVE over all code-class words of length <= %d x both '
          'return_annotated settings, %d fuzz up to %d fields, %d exhaustive '
          'name-identifier cases, seed %d); 0 disagreements. %d labelled '
          'out-of-bridge degenerate-name probe divergence(s) (see docstring / '
          'G-PANEL-2), not gating.'
          % (checked, n_boundary, n_exhaustive, EXHAUSTIVE_LEN, N_FUZZ,
             MAX_FUZZ_FIELDS, n_names, SEED, len(probe)))
    print(json.dumps({
        'checked': checked,
        'disagreements': 0,
        'seed': SEED,
        'shadow': 'direct (contract-stripped impl regions of model.py)',
        'oracle': 'called: sphinx.ext.autodoc.typehints.'
                  'augment_descriptions_with_types (patched)',
        'exhaustive_code_words_len_le': EXHAUSTIVE_LEN,
        'n_boundary': n_boundary,
        'n_exhaustive': n_exhaustive,
        'n_fuzz': N_FUZZ,
        'n_name_identifiers': n_names,
        'branch_hits': branches,
        'out_of_bridge_probe_divergences': probe,
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())
