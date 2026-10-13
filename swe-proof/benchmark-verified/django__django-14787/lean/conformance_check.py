#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_attachIdentity
against the patch.diff behaviour (the post-patch construction of `bound_method`),
plus a direct check of the POSTCONDITION against that same real construction.

The impl region has R/I content (init a bare callable, copy identity, return), so
this runs a real fuzz. The shadow reproduces the Lean impl's control flow
op-for-op:
    bound = bareCallable            -- let mut bound := bareCallable   (R)
    bound = copyIdentity(src,bound) -- bound := copyIdentity source bound (A: real callee)
    return bound                    -- return bound                    (I)
The identity-copy op is A-tagged (a deep-model reference to the stdlib
`functools.update_wrapper`), so -- per the G-CONF protocol -- it is realised here
by the REAL repo callee (`functools.wraps(method)(...)` == `update_wrapper`).

The patched side is an independent reconstruction of the POST-patch line
`bound_method = wraps(method)(partial(method.__get__(self, type(self))))`: build a
real `partial` over a real bound method `method`, wrap it with `wraps(method)`, and
observe what the decorators downstream will see.

OBSERVED SURFACE — TWO LAYERS PER ATTRIBUTE. Each identity attribute of a
callable is read at both of the layers the Lean model carries in `IdentityAttr`:

    observed  -- what `getattr(obj, attr)` answers        (IdentityAttr.observed)
    ownEntry  -- what `obj.__dict__` holds for it         (IdentityAttr.ownEntry)

Both are needed because `update_wrapper` writes the destination twice: once per
attribute from what a reader observes on the source (its `assigned` pass), and
then once with the source's own attribute table laid over the destination's as a
whole (its `updated` pass, WRAPPER_UPDATES == ('__dict__',)). The destination the
patched line builds is a `functools.partial`, which answers for these attributes
out of its own table -- so both passes write the SAME storage and the table pass,
being later, is the one whose entry survives. A single-layer `getattr`-only
surface cannot see that at all: it agrees with the real routine on every source
whose two layers coincide, and the sources the repo's own decorator stack
produces are exactly the ones where they do NOT (see `src_stacked_method`, which
runs the real stack: its inner wrapper answers with the original method's name
while its table holds the decorator's).

Values are compared in the model's THREE-state encoding: `ABSENT` <-> Lean
`AttrSlot.vacant`, `('held', v)` <-> `AttrSlot.filled v`, so a held attribute
containing None stays distinct from one that is not held (the distinction both of
`update_wrapper`'s passes make, since each dispatches on presence and never on
content).

Also compared: whether __wrapped__ is set, AND whether the resulting callable can
be run supplying only the arguments of the call itself (the Lean model's
`selfSufficient`). That last facet is observed by actually CALLING the constructed
object at the modeled call shape: the whole point of the construction is that the
decorators receive something they can invoke without supplying the instance, and a
construction that handed back the original unbound function would carry identical
metadata while failing that call. Sources built over a real unbound `method`
taking `self` keep the facet non-trivial -- such a source is NOT runnable on its
own while the result must be.

THREE LEGS, all asserted over the same inputs:
  (1) IMPL CONFORMANCE: shadow(method) == patched(method) on the surface above.
  (2) POSTCONDITION: the Lean postcondition's predicted values, computed here from
      the source's two layers exactly as `problem_spec_attachIdentity` states them
      (`transferredEntry` at each of the result's two layers), equal what the real
      post-patch construction actually exposes. This is the postcondition checked
      against the repo rather than against itself.
  (3) COVERAGE: the sweep must actually reach sources whose own table entry
      differs from what a reader observes -- otherwise legs (1) and (2) would pass
      against a model that has only the first of the routine's two passes, and the
      run would certify nothing about the second.

ENVIRONMENT OF RECORD. Run this INSIDE the instance image (conda `testbed` env,
CPython 3.9.20) with patch.diff applied, which is how G-CONF runs it and the
interpreter the instance's own tests run under. One modeled carrier fact is
interpreter-dependent: from CPython 3.10 on a static C type's `__module__` is
recorded in the type's own dict and so becomes reachable through an instance, so
a fresh `functools.partial` answers `'functools'` for `__module__` there while
through 3.9 the same read raises. On a 3.10+ interpreter this file therefore
reports mispredictions on the module facet of every source that supplies no
module -- that is the interpreter differing from the reference one, not the
postcondition differing from the repo. See mapping.md, "Environment of record".

exit 0 iff zero disagreements. stdlib-only.
"""
import functools
import random
import sys

SEED = 14787
N = 120_000

ATTRS = ('__name__', '__module__', '__qualname__')


def self_sufficient(obj):
    """Whether `obj` runs when given only the arguments of the call itself.

    A callable that still expects the instance handed in first refuses with a
    TypeError naming a missing positional argument -- the issue's failure. Any
    other outcome means the call shape was accepted."""
    try:
        obj()
    except TypeError as e:
        msg = str(e)
        if 'required positional argument' in msg or 'positional argument' in msg:
            return False
        return True
    except Exception:
        return True
    return True


class _Absent:
    def __repr__(self):
        return 'ABSENT'


# "not held at all", kept DISTINCT from the value None ("held, containing nothing
# in particular"); see the module docstring.
ABSENT = _Absent()


def overlay(src, dst):
    """Lean `AttrSlot.overlay`: whichever layer holds an entry wins, `src` first;
    content is carried along but never consulted."""
    return dst if src is ABSENT else src


def read_layer(obj, name):
    """What a reader of `name` on `obj` is answered with (Lean `observed`)."""
    try:
        return ('held', getattr(obj, name))
    except AttributeError:
        return ABSENT


def table_layer(obj, name):
    """What `obj`'s OWN attribute table holds for `name` (Lean `ownEntry`) -- the
    layer the routine's second pass reads and writes."""
    try:
        table = object.__getattribute__(obj, '__dict__')
    except AttributeError:
        return ABSENT
    if not isinstance(table, dict) or name not in table:
        return ABSENT
    return ('held', table[name])


def observe(obj):
    return {
        'observed': {n: read_layer(obj, n) for n in ATTRS},
        'ownEntry': {n: table_layer(obj, n) for n in ATTRS},
        '__wrapped__': hasattr(obj, '__wrapped__'),
        'self_sufficient': self_sufficient(obj),
    }


def spec_prediction(src):
    """What `problem_spec_attachIdentity` predicts, transcribed from the Lean
    postcondition and evaluated on the source's two observed layers.

    `transferredEntry source.attr` is the source's own table entry where its table
    holds one and what a reader observes on it otherwise. The result holds that
    entry in its own table, and a reader of the result observes it directly, for
    each of the three attributes alike -- because the object handed back is the
    synthesised callable, which answers out of its own table and whose kind
    supplies nothing for any of the three on its own account."""
    entry = {n: overlay(src['ownEntry'][n], src['observed'][n]) for n in ATTRS}
    return {
        'observed': dict(entry),
        'ownEntry': dict(entry),
        '__wrapped__': True,
        'self_sufficient': True,
    }


class _Owner:
    """Stands in for the class whose method is being decorated."""


def _inject(obj, name, value):
    """Put an entry directly in the object's OWN attribute table, bypassing its
    slots. This is the state the repo's own decorator stack produces: the real
    routine's second pass writes exactly here, so a callable that has been through
    it carries table entries its slots do not answer with."""
    object.__getattribute__(obj, '__dict__')[name] = value


class _ReadRefused:
    """A callable whose kind answers for an identity attribute by refusing, while
    its own table may hold an entry for it -- the remaining reachable pair of layer
    states. Only the three modeled attributes are intercepted, so `__dict__`, the
    only other thing the routine reads, is untouched."""

    def __init__(self, refuse):
        self._refuse = frozenset(refuse)

    def __getattribute__(self, name):
        if name in ATTRS and name in object.__getattribute__(self, '_refuse'):
            raise AttributeError(name)
        return object.__getattribute__(self, name)

    def __call__(self, *a, **k):
        return None


def make_method(attrs, table=None):
    """A real callable standing in for `method`, holding the given attribute
    states: `ABSENT` (not held), None (held, containing nothing in particular),
    or a string (held, containing that text). `table` optionally puts entries
    DIRECTLY in the callable's own table, which is how a source whose two layers
    disagree is built.

    Where anything other than a plain string is requested, use a `partial` (which
    natively lacks all three attributes, and which accepts `setattr(x, attr,
    None)` on all three) so both non-string states are REAL; otherwise an UNBOUND
    function of one positional parameter -- which is what `method` actually is,
    and which is therefore NOT runnable without the instance."""
    if any(not isinstance(attrs.get(n, ABSENT), str) for n in ATTRS):
        base = functools.partial(lambda *a, **k: None)
        for n in ATTRS:
            v = attrs.get(n, ABSENT)
            if v is not ABSENT:
                setattr(base, n, v)     # v may be None: HELD, containing None
        for n, v in (table or {}).items():
            _inject(base, n, v)
        return base
    def method(self):
        return 'tests'
    for n in ATTRS:
        setattr(method, n, attrs[n])
    for n, v in (table or {}).items():
        _inject(method, n, v)
    return method


# --------------------------------------------------------------------------- #
# the repo's own decorator stack, as a source factory                          #
# --------------------------------------------------------------------------- #
# django/utils/decorators.py at the base commit builds the callable a second,
# outer decorator receives by running `_update_method_wrapper` on the inner
# wrapper and then `update_wrapper(_wrapper, method)`. The product is a callable
# whose slots answer with the ORIGINAL method's identity while its own table holds
# the decorator-side identity -- the two-layer disagreement, produced by the
# repo rather than by this file.
def _update_method_wrapper(_wrapper, decorator):
    @decorator
    def dummy(*args, **kwargs):
        pass
    functools.update_wrapper(_wrapper, dummy)


def _stack_source(decorators, method):
    def _wrapper(self, *args, **kwargs):
        return method.__get__(self, type(self))(*args, **kwargs)
    for dec in decorators:
        _update_method_wrapper(_wrapper, dec)
    functools.update_wrapper(_wrapper, method)
    return _wrapper


def src_stacked_method(rng):
    """A `method` that has itself already been through the repo's stack, so its
    own table disagrees with what a reader observes on it.

    The decorators handed to it return a wraps-dressed `partial` -- which is
    exactly the shape the gold line itself produces, and the shape a user
    decorator that simply passes its argument on produces once the gold line has
    run. That matters for the disagreement: the identity such a callable carries
    lives in its own TABLE, so when `_update_method_wrapper` runs
    `update_wrapper(_wrapper, dummy)` the whole-table merge plants the
    decorator-side entries in `_wrapper.__dict__`, while the later
    `update_wrapper(_wrapper, method)` writes `_wrapper`'s SLOTS with the original
    method's identity (a function's `__name__` is a data descriptor, so the slot
    is what a reader is answered from). The product answers with the original
    method's identity and holds the decorator's -- produced by the repo's own
    code, not by reaching into a table from here."""
    def partial_style(fn):
        # a decorator of the shape the gold construction introduces: identity
        # carried on a `partial`, i.e. in the object's own table
        return functools.wraps(fn)(functools.partial(fn))

    def outer(fn):
        @functools.wraps(fn)
        def inner(*a, **k):
            return fn(*a, **k)
        return inner

    def method(self):
        return 'tests'
    method.__name__ = rng.choice(['m', 'method', 'hello_world'])
    method.__qualname__ = rng.choice(['Outer.m', 'Test.method', 'C.hello_world'])
    method.__module__ = rng.choice(['__main__', 'tests'])
    decs = [partial_style] if rng.random() < 0.7 else [partial_style, outer]
    return _stack_source(decs, method)


def src_read_refused(rng):
    refuse = [n for n in ATTRS if rng.random() < 0.6] or [rng.choice(ATTRS)]
    obj = _ReadRefused(refuse)
    pool = [ABSENT, None, 'dummy', 'Outer.m', 'deco_patched', '']
    for n in ATTRS:
        v = rng.choice(pool)
        if v is not ABSENT:
            _inject(obj, n, v)
    return obj


def _synthesised(method):
    """The attribute-bare, self-sufficient callable the construction starts from:
    the instance is already bound into it, so it takes only the call's own
    arguments. Mirrors `partial(method.__get__(self, type(self)))`; for a carrier
    that is not a descriptor (the partial case) `partial(method)` is already
    argument-complete."""
    owner = _Owner()
    getter = getattr(method, '__get__', None)
    if getter is not None:
        return functools.partial(getter(owner, _Owner))
    return functools.partial(method)


def shadow(method):
    """R/I shadow of implementation_attachIdentity, with the A-reference op
    (identity copy) realised by the REAL stdlib callee:
        bound = partial(method.__get__(self, type(self)))  -- bareCallable
        update_wrapper(bound, method)   -- copyIdentity source bound (A: real callee)
        return bound
    """
    bound = _synthesised(method)                 # synthesised, name-bare
    functools.update_wrapper(bound, method)      # A-reference op via real callee
    return observe(bound)


def patched(method):
    """Independent reconstruction of the POST-patch bound_method construction:
    wraps(method)(partial(method.__get__(self, type(self))))."""
    owner = _Owner()
    getter = getattr(method, '__get__', None)
    inner = (functools.partial(getter(owner, _Owner)) if getter is not None
             else functools.partial(method))
    bound_method = functools.wraps(method)(inner)
    return observe(bound_method)


def rand_method_attrs(rng):
    # ABSENT and None are SEPARATE draws: a pool that used None for "absent"
    # could never construct a source HOLDING a contentless attribute, which is
    # exactly the state on which a two-state model and the real routine disagree.
    name_pool = [ABSENT, None, 'method', 'hello_world', 'view', 'm', '']
    mod_pool = [ABSENT, None, 'tests', '__main__', 'app.views', '']
    qual_pool = [ABSENT, None, 'Test.method', 'C.view', 'method', '']
    return {
        '__name__': rng.choice(name_pool),
        '__module__': rng.choice(mod_pool),
        '__qualname__': rng.choice(qual_pool),
    }


def rand_table(rng):
    """Entries put straight in the source's own table: absent for a third of the
    draws, so both the agreeing and the disagreeing layer states are reached."""
    if rng.random() < 0.34:
        return {}
    pool = [None, 'dummy', 'deco_patched', '_update_method_wrapper.<locals>.dummy',
            '', 'Outer.m']
    return {n: rng.choice(pool) for n in ATTRS if rng.random() < 0.7}


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        # the F2P case: a real method holding all three attributes
        ({'__name__': 'method', '__module__': 'tests', '__qualname__': 'Test.method'}, {}),
        ({'__name__': 'hello_world', '__module__': 'app', '__qualname__': 'C.hello_world'}, {}),
        # method not holding some attrs
        ({'__name__': 'm', '__module__': ABSENT, '__qualname__': ABSENT}, {}),
        ({n: ABSENT for n in ATTRS}, {}),
        # ---- the THIRD state on each facet in turn: HELD, containing nothing in
        # ---- particular. This is the input at which a two-state present/absent
        # ---- encoding parts company with the routine: collapsing the state onto
        # ---- "absent" predicts that the destination's entry stands (nothing at
        # ---- all on the freshly synthesised callable), while the routine really
        # ---- copies the held entry over, leaving one that contains None.
        ({'__name__': 'method', '__module__': None, '__qualname__': 'Test.method'}, {}),
        ({'__name__': None, '__module__': 'tests', '__qualname__': 'Test.method'}, {}),
        ({'__name__': 'method', '__module__': 'tests', '__qualname__': None}, {}),
        ({n: None for n in ATTRS}, {}),
        # mixed: one of each state
        ({'__name__': None, '__module__': ABSENT, '__qualname__': 'Test.method'}, {}),
        # ---- the source's OWN TABLE disagreeing with what a reader observes on
        # ---- it, which is what the repo's stack produces and the state at which
        # ---- the routine's second pass decides the answer.
        ({'__name__': 'm', '__module__': '__main__', '__qualname__': 'Outer.m'},
         {'__name__': 'dummy', '__module__': 'deco_patched',
          '__qualname__': '_update_method_wrapper.<locals>.dummy'}),
        ({'__name__': 'm', '__module__': '__main__', '__qualname__': 'Outer.m'},
         {'__name__': 'dummy'}),
        ({'__name__': 'm', '__module__': '__main__', '__qualname__': 'Outer.m'},
         {'__module__': None}),
        ({'__name__': 'm', '__module__': ABSENT, '__qualname__': 'Outer.m'},
         {'__module__': 'deco_patched'}),
        # a source whose table holds the delegation key: the routine writes that
        # link LAST, so the table entry must not be what survives
        ({'__name__': 'm', '__module__': 'tests', '__qualname__': 'Outer.m'},
         {'__wrapped__': 'bogus'}),
    ]
    cases = [make_method(a, t) for a, t in fixed]
    cases += [src_stacked_method(rng) for _ in range(60)]
    cases += [src_read_refused(rng) for _ in range(60)]
    for _ in range(N):
        r = rng.random()
        if r < 0.12:
            cases.append(src_stacked_method(rng))
        elif r < 0.2:
            cases.append(src_read_refused(rng))
        else:
            cases.append(make_method(rand_method_attrs(rng), rand_table(rng)))

    disagreements = 0
    spec_disagreements = 0
    examples = []
    spec_examples = []
    disagreeing_layers = 0
    # Sanity: on the F2P-shaped input the modeled facets must be NON-TRIVIAL --
    # the original is not runnable on its own while the constructed callable is.
    # Without this, both sides could agree on `self_sufficient` for the boring
    # reason that everything is self-sufficient, and the facet would test nothing.
    probe = make_method(fixed[0][0])
    if self_sufficient(probe):
        print("G-CONF FAIL: the modeled source is runnable without its instance; "
              "the usability facet would be vacuous")
        return 1
    if not patched(probe)['self_sufficient']:
        print("G-CONF FAIL: the post-patch construction is not runnable on its "
              "own; the usability facet is misobserved")
        return 1

    for method in cases:
        src = observe(method)
        if any(src['ownEntry'][n] is not ABSENT
               and src['ownEntry'][n] != src['observed'][n] for n in ATTRS):
            disagreeing_layers += 1
        got = shadow(method)
        want = patched(method)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((src, got, want))
        # leg (2): the POSTCONDITION against the real construction
        pred = spec_prediction(src)
        if pred != want:
            spec_disagreements += 1
            if len(spec_examples) < 10:
                spec_examples.append((src, pred, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, g, w in examples:
            print(f"  src={a}\n    shadow ={g}\n    patched={w}")
        return 1

    if spec_disagreements:
        print(f"G-CONF FAIL: the postcondition mispredicts the real post-patch "
              f"construction on {spec_disagreements} inputs")
        for a, p, w in spec_examples:
            print(f"  src={a}\n    spec   ={p}\n    patched={w}")
        return 1

    if not disagreeing_layers:
        # A sweep in which the source's two layers always agree cannot see the
        # routine's second pass, and would pass against a model that has only the
        # first. Refuse to report OK on such a sweep.
        print("G-CONF FAIL: no source had an own-table entry differing from what "
              "a reader observes, so the sweep never exercised the table pass")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements — impl shadow and "
          f"postcondition both match the post-patch construction at both "
          f"attribute layers ({disagreeing_layers} sources had an own-table entry "
          f"the reader does not observe) (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
