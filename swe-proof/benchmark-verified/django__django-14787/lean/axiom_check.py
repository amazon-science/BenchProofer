#!/usr/bin/env python3
"""G-AX — validate the deep-model A-reference for django__django-14787.

The modeled wrapper-construction step relies on the stdlib routine
`functools.wraps(method)(...)` (equivalently `functools.update_wrapper`) to copy
the original callable's identity onto the synthesised callable. That routine is
modeled DEEPLY in Solution.lean as `copyIdentity` / `IdentityAttr.transfer` (an
A-reference, not a consumed axiom). This check runs the REAL stdlib routine on
boundary + fuzzed inputs and asserts the deep model reproduces it
attribute-for-attribute, AT BOTH LAYERS.

THE ROUTINE'S STEPS, and which model leg stands for each. `update_wrapper` is
not one operation but four, in this order:

  1. for attr in `assigned` (WRAPPER_ASSIGNMENTS): `value = getattr(wrapped,
     attr)` guarded by `except AttributeError: pass`, then `setattr(wrapper,
     attr, value)`. Per-attribute, driven by whether the source ANSWERS for the
     attribute -- never by what the answer is.  ->  the `src.observed` leg of
     `IdentityAttr.transfer`.
  2. for attr in `updated` (WRAPPER_UPDATES = ('__dict__',)):
     `getattr(wrapper, attr).update(getattr(wrapped, attr, {}))`. One
     whole-container overlay of the source's OWN attribute table onto the
     wrapper's, key by key.  ->  the `src.ownEntry` leg of
     `IdentityAttr.transfer`.
  3. `wrapper.__wrapped__ = wrapped`, LAST of all, so the delegation link is a
     constant of the routine and cannot be overridden by anything the source's
     table happens to hold under that key.  ->  `wrapped := true`.
  4. `return wrapper` -- the object handed back is the WRAPPER, never the
     source.  ->  `selfSufficient := dst.selfSufficient`.

Steps 1 and 2 are two writes to the SAME storage whenever the destination reads
its attributes through its own table, which is the case for the synthesised
`functools.partial` the modeled construction always builds: step 1's `setattr`
lands in the partial's own table, and step 2 then overlays the source's table on
top of it. So step 2 is the LATER write and its entry is the one that survives.
That is why the model needs both legs and why their ORDER is part of the
contract; a model with only leg 1 agrees with the routine exactly on sources
whose two layers coincide and diverges on every source where they differ.

TWO-LAYER ATTRIBUTE CARRIER (Lean `IdentityAttr`). Each identity attribute of a
callable therefore has to be observed at two layers, which need not agree:

    observed  -- what `getattr(obj, attr)` answers (Lean `IdentityAttr.observed`)
    ownEntry  -- what `obj.__dict__` holds for it (Lean `IdentityAttr.ownEntry`)

A plain function answers for all three attributes out of type-level slots while
its own table holds none of them; a function whose table has been written into
directly answers from the SLOT (a data descriptor outranks the instance table)
while its table still holds the entry it hands on; an object whose kind answers
for an attribute by raising has NO observable value while its table may hold
one. All three shapes are built below out of real objects, and the disagreeing
ones are counted in the output so the sweep's coverage of that state is visible
rather than assumed.

THREE-STATE LAYERS (Lean `AttrSlot`). Each layer independently has THREE states,
because both step 1 (`except AttributeError`) and step 2 (a dict `update`) are
driven by PRESENCE, never by content:

    absent                 <-> AttrSlot.vacant
    present, value None    <-> AttrSlot.filled None
    present, value a str   <-> AttrSlot.filled (some s)

The middle state is load-bearing and a two-state present/absent encoding would
be UNFAITHFUL: a source holding `__module__ = None` satisfies the guard, so
`None` is copied VERBATIM onto the wrapper -- an entry is left there, holding
nothing in particular. A two-state model collapses that source onto "absent"
and so predicts that the DESTINATION's entry survives instead: no entry at all
on a freshly synthesised callable, or whatever text it already held on a preset
one. Both predictions are wrong, and the difference is visible at the wrapper's
own table as well as to a reader of it. The generators draw all three states
explicitly (see `ABSENT` vs `None` in the pools) rather than using `None` to
mean "absent".

MODELED SURFACE, and why the projection is exact. Three of the five
WRAPPER_ASSIGNMENTS attributes are modeled -- __name__, __module__, __qualname__
-- the ones that are genuinely ABSENT on a bare `partial` and PRESENT on a real
function or method (__name__ is the exact attribute whose absence causes the
issue's AttributeError; __doc__ is excluded because a `partial` carries it
natively, so the destination is never attribute-bare there, and __annotations__
because its value is a MAPPING rather than a text token, so it does not inhabit
the modeled content space and the issue's observable never reads it). The
projection onto three attributes is exact rather than approximate:
step 1 treats each attribute independently and step 2 is a key-wise dict
update, so the routine's effect on these three keys does not depend on the
others, and dropping the others changes nothing about what is claimed of these.

Modeled USABILITY surface (`selfSufficient` in the Lean model): whether the
callable can be run supplying only the arguments of the call itself, as opposed
to still expecting the object it belongs to to be handed in first. Probed
operationally -- call the object with the call's own arguments and see whether it
refuses for want of that leading argument -- because that refusal is precisely
the observable failure the issue reports.

Properties validated (the A-reference contract):
  (1) METADATA, BOTH LAYERS: model_copy_identity(observe(src), observe(dst)) ==
      observe(update_wrapper(dst, src)) on the three attributes at each of their
      two layers, plus the delegation flag, compared in the three-state encoding
      above.
  (2) USABILITY: the routine hands back the WRAPPER object itself and transfers
      identity only -- it never changes which arguments the wrapper needs. So the
      result's usability is the WRAPPER's, never the source's, which is exactly
      the model's `selfSufficient := dst.selfSufficient`. Checked two ways per
      input: `update_wrapper(dst, src) is dst`, and the wrapper's usability probe
      is unchanged across the call even when the source differs from it.
  (3) DESTINATION TRANSPARENCY, and the destination's OWN starting state: the
      model's `observed := entry.overlay dst.observed` leg is a claim about a
      destination that answers for an attribute out of its own table, and the
      modeled `bareCallable` further claims a freshly synthesised destination
      answers for NONE of the three attributes at either layer. Both are
      properties of the carrier the modeled construction always builds (a
      `functools.partial`), and both are checked once at startup on a real
      partial rather than assumed; every destination below is a partial.

exit 0 iff every input matches. stdlib-only.
"""
import functools
import random
import sys

SEED = 14787
N = 120_000

# The three modeled WRAPPER_ASSIGNMENTS attributes.
ATTRS = ('__name__', '__module__', '__qualname__')


def self_sufficient(obj):
    """Whether `obj` can be run supplying only the arguments of the call itself.

    Probed operationally at the modeled call shape (no extra leading argument):
    a callable that still expects the object it belongs to be handed in first
    refuses with a TypeError naming a missing required positional argument --
    exactly the refusal the issue reports. Any other exception means the body
    ran, so the call shape was accepted and the object IS runnable on its own."""
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


# The sentinel for "this layer holds NOTHING at all", kept DISTINCT from the
# value None (which means "holds an entry containing nothing in particular").
# Using None for both is exactly the collapse that makes a two-state model
# unfaithful.
class _Absent:
    def __repr__(self):
        return 'ABSENT'


ABSENT = _Absent()


def overlay(src, dst):
    """Lean `AttrSlot.overlay`: `src` wins whenever it holds an entry -- content
    and all, including a None content -- and otherwise `dst`'s entry survives.
    Dispatch is on HELD-ness only, never on content."""
    return dst if src is ABSENT else src


def read_layer(obj, name):
    """What a reader of `name` on `obj` is answered with (Lean `observed`)."""
    try:
        return ('held', getattr(obj, name))
    except AttributeError:
        return ABSENT


def table_layer(obj, name):
    """What `obj`'s OWN attribute table holds for `name` (Lean `ownEntry`).

    This is the layer step 2 of the routine reads and writes, and it is the one
    a model built only out of `getattr` cannot see."""
    try:
        table = object.__getattribute__(obj, '__dict__')
    except AttributeError:
        return ABSENT
    if not isinstance(table, dict) or name not in table:
        return ABSENT
    return ('held', table[name])


def observe(obj):
    """The modeled surface of a callable: both layers of each attribute, the
    delegation flag, and the usability probe."""
    return {
        'observed': {n: read_layer(obj, n) for n in ATTRS},
        'ownEntry': {n: table_layer(obj, n) for n in ATTRS},
        'wrapped': hasattr(obj, '__wrapped__'),
        'self_sufficient': self_sufficient(obj),
    }


def model_copy_identity(src, dst):
    """Python mirror of Lean `copyIdentity` / `IdentityAttr.transfer`.

    Per attribute, the two passes of the real routine in their real order: the
    entry placed from what a reader observes on the source, then the source's own
    table entry laid over that -- both writing the destination's table, so the
    table entry is the one that survives. What the result is then observed to
    hold is that entry laid over whatever the destination already answered with.
    The delegation flag is the routine's own constant, and the usability of the
    object handed back is the destination's."""
    observed, own = {}, {}
    for name in ATTRS:
        entry = overlay(src['ownEntry'][name],
                        overlay(src['observed'][name], dst['ownEntry'][name]))
        own[name] = entry
        observed[name] = overlay(entry, dst['observed'][name])
    return {'observed': observed, 'ownEntry': own, 'wrapped': True,
            'self_sufficient': dst['self_sufficient']}


# --------------------------------------------------------------------------- #
# real carriers for every reachable pair of layer states                       #
# --------------------------------------------------------------------------- #
# Values drawn for a layer. ABSENT and None are SEPARATE draws: the pool must
# reach the held-but-None state, or the module leg is never exercised where a
# two-state model breaks.
POOL = [ABSENT, None, 'method', 'tests', 'T.method', '', 'x', 'mod.sub',
        'hello_world', 'dummy', 'deco_patched',
        '_update_method_wrapper.<locals>.dummy']
# Values a FUNCTION's slots accept: `f.__name__ = None` raises TypeError, so a
# function's observed layer is always held and always text (its module slot does
# accept None, and does so natively).
TEXT_POOL = [v for v in POOL if isinstance(v, str)]


def _inject(obj, name, value):
    """Put an entry in the object's OWN table directly, bypassing the slots.

    This is the state the decorator stack itself produces: the real routine's
    step 2 writes exactly here, so a callable that has been through it carries
    table entries that its own slots do not answer with."""
    object.__getattribute__(obj, '__dict__')[name] = value


def src_plain_function(rng):
    """A plain function: answers for all three attributes out of its slots, own
    table empty. The commonest original there is, and the F2P's shape."""
    def f(*a, **k):
        return None
    f.__name__ = rng.choice(TEXT_POOL)
    f.__qualname__ = rng.choice(TEXT_POOL)
    m = rng.choice(POOL)
    if m is not ABSENT:
        f.__module__ = m          # a function's module slot does accept None
    return f


def src_table_shadowed_function(rng):
    """A function whose own table DISAGREES with its slots: the slots still
    answer (a data descriptor outranks the instance table) while the table holds
    the entries it hands on. What `_update_method_wrapper` leaves behind, and the
    class a model built only out of `getattr` cannot express."""
    f = src_plain_function(rng)
    names = [n for n in ATTRS if rng.random() < 0.75] or [rng.choice(ATTRS)]
    for n in names:
        v = rng.choice(POOL)
        if v is not ABSENT:
            _inject(f, n, v)
    if rng.random() < 0.2:
        # the routine writes the delegation link LAST, so a source whose table
        # holds that key must not be able to override it
        _inject(f, '__wrapped__', 'bogus')
    return f


def src_partial(rng):
    """A `functools.partial` used as the SOURCE: it holds no slots for these
    attributes, so what a reader observes is exactly what its own table holds and
    the two layers agree by construction. The carrier for the agreeing-layers
    shape at every mixture of the three states, and also the shape a source takes
    when two of these constructions stack."""
    p = functools.partial(lambda *a, **k: None)
    for n in ATTRS:
        v = rng.choice(POOL)
        if v is not ABSENT:
            setattr(p, n, v)      # lands in the partial's own table
    return p


def src_method_wrapper(rng):
    """A real bound method-wrapper: it answers for __name__ and __qualname__ out
    of its kind and genuinely does NOT hold __module__ (verified:
    hasattr(object().__str__, '__module__') is False), and it has NO own attribute
    table at all -- `object.__getattribute__(mw, '__dict__')` itself raises. So it
    is the carrier for the one state no `partial` and no function can reach: the
    source of step 2's `getattr(wrapped, '__dict__', {})` DEFAULT branch, where
    the whole-table merge has no table to merge and every ownEntry layer is absent
    for that reason rather than by choice of key."""
    return object().__str__


def src_owner_method(rng):
    """A callable that still expects the object it belongs to to be handed in
    first -- a plain unbound function of one positional parameter, which is what
    the original `method` is. Not runnable on its own, which is the usability
    state the modeled construction must not propagate."""
    def owner_method(self):
        return None
    owner_method.__name__ = rng.choice(TEXT_POOL)
    owner_method.__qualname__ = rng.choice(TEXT_POOL)
    m = rng.choice(POOL)
    if m is not ABSENT:
        owner_method.__module__ = m
    if rng.random() < 0.5:
        for n in ATTRS:
            v = rng.choice(POOL)
            if v is not ABSENT:
                _inject(owner_method, n, v)
    return owner_method


class _ReadRefused:
    """A callable whose KIND answers for an identity attribute by refusing, while
    its own table may still hold an entry for it.

    That is the remaining reachable pair of layer states (nothing observable,
    an entry held), and it is a state the real routine handles by skipping the
    attribute in step 1 and still copying it in step 2. Only the three modeled
    attributes are intercepted, so the object is an ordinary one in every other
    respect -- in particular `getattr(obj, '__dict__')`, the only other thing the
    routine reads, is untouched."""

    def __init__(self, refuse):
        self._refuse = frozenset(refuse)

    def __getattribute__(self, name):
        if name in ATTRS and name in object.__getattribute__(self, '_refuse'):
            raise AttributeError(name)
        return object.__getattribute__(self, name)

    def __call__(self, *a, **k):
        return None


def src_read_refused(rng):
    """A source with nothing observable for some attributes and table entries for
    them anyway."""
    refuse = [n for n in ATTRS if rng.random() < 0.6] or [rng.choice(ATTRS)]
    obj = _ReadRefused(refuse)
    for n in ATTRS:
        v = rng.choice(POOL)
        if v is not ABSENT:
            _inject(obj, n, v)
    return obj


SOURCES = (src_plain_function, src_table_shadowed_function, src_partial,
           src_method_wrapper, src_owner_method, src_read_refused)


def dst_bare_partial(rng):
    """The modeled `bareCallable`: a freshly synthesised `partial`, own table
    empty and its kind answering for none of the three attributes, so nothing is
    held at either layer. This is the destination the real construction always
    builds, and the pre-fix `bound_method` exactly."""
    return functools.partial(lambda *a, **k: None)


def dst_preset_partial(rng):
    """A synthesised callable that already holds some entries of its own, so the
    destination's layers are exercised rather than only the empty case."""
    p = functools.partial(lambda *a, **k: None)
    for n in ATTRS:
        v = rng.choice(POOL)
        if v is not ABSENT:
            setattr(p, n, v)
    return p


def dst_owner_partial(rng):
    """A synthesised callable that is NOT runnable on its own (its underlying
    function still wants a leading argument). The model says the result's
    usability is the destination's, so this is the destination that separates
    `selfSufficient := dst.selfSufficient` from the constant `true`."""
    p = functools.partial(lambda self, *a, **k: None)
    if rng.random() < 0.5:
        for n in ATTRS:
            v = rng.choice(POOL)
            if v is not ABSENT:
                setattr(p, n, v)
    return p


DESTINATIONS = (dst_bare_partial, dst_preset_partial, dst_owner_partial)


def _state(layer):
    if layer is ABSENT:
        return 'absent'
    return 'none' if layer[1] is None else 'text'


def check_destination_transparency():
    """Two carrier facts the model states about the destination, checked on a real
    `functools.partial` instead of assumed.

    (a) `bareCallable` says a freshly synthesised destination holds NOTHING for
        any of the three attributes, at EITHER layer -- no entry in its own table
        and nothing a reader of it is answered with. That is the whole content of
        the pre-fix defect, so if the carrier answered for one of them anyway the
        model would be claiming an absence the real object does not have.
    (b) The `observed := entry.overlay dst.observed` leg says the destination
        answers for an attribute out of its OWN table once that table holds an
        entry -- i.e. it is table-transparent, with no slot of its own to win
        over the merged entry.

    Both are claimed of the `partial` the modeled construction builds IN THE
    INTERPRETER THIS FILE RUNS IN, which is the instance image's (conda `testbed`
    env, CPython 3.9.20) -- the interpreter the instance's own tests run under and
    the one G-AX executes this check in. They are re-measured on a real object
    every run rather than assumed, so an interpreter where they do NOT hold fails
    the gate instead of silently certifying a model the carrier does not match.
    Fact (a) is interpreter-dependent: from CPython 3.10 on, a static C type's
    `__module__` is recorded in the type's own dict and so lands on the instance
    lookup path, making `getattr(partial(f), '__module__')` answer `'functools'`;
    through 3.9 that read raises. A FAIL naming `__module__` therefore means this
    file was run on a 3.10+ interpreter rather than in the instance image, and is
    NOT evidence that the model is over-strong -- re-run it in the image before
    concluding anything about the model. See mapping.md, "Environment of
    record"."""
    p = functools.partial(lambda *a, **k: None)
    problems = []
    for n in ATTRS:
        if read_layer(p, n) is not ABSENT:
            problems.append(f"a fresh partial answers for {n}")
        if table_layer(p, n) is not ABSENT:
            problems.append(f"a fresh partial's own table holds {n}")
    for n in ATTRS:
        _inject(p, n, 'through')
        if read_layer(p, n) != ('held', 'through'):
            problems.append(f"a partial does not answer {n} out of its own table")
    return problems


def main() -> int:
    rng = random.Random(SEED)

    problems = check_destination_transparency()
    if problems:
        print("G-AX FAIL: the destination carrier is not what the model assumes: "
              + "; ".join(problems)
              + f" [interpreter {sys.version.split()[0]}; the reference one is the"
                " instance image's CPython 3.9.20 -- a 3.10+ interpreter answers"
                " 'functools' for a fresh partial's __module__ and fails here by"
                " design, see mapping.md 'Environment of record']")
        return 1

    # Boundary pairs, built as (source factory, destination factory) so every
    # one is a real object rather than a requested attribute set.
    fixed = []
    for s in SOURCES:
        for d in DESTINATIONS:
            fixed.append((s, d))
    cases = list(fixed)
    cases += [(rng.choice(SOURCES), rng.choice(DESTINATIONS))
              for _ in range(N)]

    mismatches = 0
    examples = []
    pairs = {n: set() for n in ATTRS}
    disagreeing = 0
    for src_factory, dst_factory in cases:
        src = src_factory(rng)
        dst = dst_factory(rng)
        src_obs = observe(src)
        dst_obs = observe(dst)
        for n in ATTRS:
            pairs[n].add((_state(src_obs['observed'][n]),
                          _state(src_obs['ownEntry'][n])))
        if any(src_obs['ownEntry'][n] is not ABSENT
               and src_obs['ownEntry'][n] != src_obs['observed'][n]
               for n in ATTRS):
            disagreeing += 1
        model = model_copy_identity(src_obs, dst_obs)
        returned = functools.update_wrapper(dst, src)   # == wraps(src)(dst)
        real = observe(returned)
        # the routine hands back the WRAPPER, never the source -- the structural
        # half of the usability contract
        identity_ok = returned is dst
        if model != real or not identity_ok:
            mismatches += 1
            if len(examples) < 10:
                examples.append((src_factory.__name__, dst_factory.__name__,
                                 src_obs, dst_obs, model, real, identity_ok))

    if mismatches:
        print(f"G-AX FAIL: deep model diverges from functools.update_wrapper on "
              f"{mismatches} inputs")
        for sname, dname, so, do, m, r, ident in examples:
            print(f"  src={sname} {so}\n  dst={dname} {do}\n"
                  f"    model={m}\n    real ={r}\n    returns_wrapper={ident}")
        return 1

    if not disagreeing:
        # A sweep in which the two layers always agree cannot see the second
        # pass at all, and would have passed against a model that has only the
        # first. Refuse to report OK on such a sweep.
        print("G-AX FAIL: no input had an own-table entry disagreeing with what "
              "a reader observes, so the sweep never exercised the table pass")
        return 1

    reached = ", ".join(f"{n}: {len(pairs[n])}" for n in ATTRS)
    print(f"G-AX OK: copyIdentity == functools.update_wrapper on {len(cases)} "
          f"inputs at BOTH layers ({disagreeing} of them with an own-table entry "
          f"the reader does not observe; layer-state pairs reached — {reached}) "
          f"(seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
