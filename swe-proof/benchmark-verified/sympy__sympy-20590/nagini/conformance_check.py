#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20590 (nagini).

SHADOW
------
The impl regions of `model.py`, copied VERBATIM below with only the contract
calls deleted (`Requires`/`Ensures`/`Exsures` live outside the regions;
`Assert(...)` lines inside the two `core_expression_*` regions are the proof
scaffolding that is stripped).  Nothing is restructured, renamed or
"simplified" — the proof-scaffolding locals `empty`/`one`/`two` are kept even
though they are dead once the `Assert`s are gone, precisely so the shadow is
the region and not a paraphrase of it.  Copied over:

  * `all_closed_layout` / `instance_admits_namespace` — the `@Pure` helpers the
    impl regions call (pure-start/pure-end), contracts stripped;
  * `AttributeBindingRefused` — the exception the impl raises;
  * `bind_undeclared_attribute`, `trait_pins_closed_layout`,
    `core_expression_instance_admits_namespace`,
    `core_expression_bind_undeclared_attribute` — the four impl regions.

A minimal `PSeq`/`ToSeq` shim (tuple subclass with `len`/`[]`/`drop`/`take`/
`+`/`==`) realizes the immutable Nagini sequence the front-recursive fold
recurses on.  There is NO `@ContractOnly` callee in this bundle (meta.json
`axioms: []`, mapping.md §3): the `__slots__`/`__dict__` rule is modelled
DEEPLY, so the whole impl region is executable shadow and nothing is assumed.

ORACLE — the real patched repo, called, not reimplemented
---------------------------------------------------------
The gate applies `patch.diff` (adds `__slots__ = ()` to `Printable`,
`sympy/core/_print_helpers.py:8`) to /testbed before this script runs, and
PYTHONPATH=/testbed makes the patched package importable.  The modelled
behaviour is a property of the *patched class hierarchy*, so the oracle is that
hierarchy itself, observed through the real CPython interpreter.  Four legs, in
increasing distance from the F2P and decreasing directness:

  L1  PINNED F2P SHAPE — the real `sympy.core.basic.Basic` (`basic.py:28`) and
      the real `sympy.core._print_helpers.Printable` (`_print_helpers.py:8`),
      the two symbols mapping.md §1 names.  `trait_pins_closed_layout()` is
      diffed against `Printable`'s ACTUAL post-patch slot declaration;
      `core_expression_instance_admits_namespace()` against the F2P's
      `hasattr(Basic(), '__dict__')`; `core_expression_bind_undeclared_attribute()`
      against the F2P's `with raises(AttributeError): b1.x = 1`.  This leg is
      the F2P assertion itself, run against the model's own entry points.
      It also diffs the model's padded chain `PSeq(True, True, trait)` against
      the faithful 2-entry chain `PSeq(True, trait)` **and** against the real
      `Basic` MRO — mapping.md §2's "the extra leading True is inert padding"
      claim is thereby tested, not taken on trust.

  L2  EVERY real class in the patched sympy package, layout observation.  We
      invert the type bridge on each class (its real MRO, `object` excluded, ->
      the `PSeq[bool]` of closed-layout flags) and diff
      `instance_admits_namespace(flags)` against `cls.__dictoffset__ != 0` —
      the C-level fact "this class's instance layout carries a per-instance
      namespace", which is exactly what the model's predicate denotes.  1469
      real classes, of which ~1354 have an OPEN chain: this is where the real
      repository exercises the model's open-namespace branch, which no
      F2P-adjacent class can.

  L3  Real classes again, BEHAVIOURAL observation: build an instance and diff
      the shadow against the real `hasattr(inst, '__dict__')` and the real
      outcome of binding an undeclared attribute name.  Restricted to classes
      that do not override the attribute protocol (see DOMAIN below).

  L4  SYNTHETIC chains over the real interpreter, to reach >= 1e5 and to force
      every branch.  A flag chain is realized as a real linear class chain
      (`type(name, (base,), {'__slots__': ()})` iff the flag is True, else a
      body omitting `__slots__`), the leaf is instantiated, and the shadow is
      diffed against the same two real observations.  L2/L3 alone cannot cover
      the impl's `return True` branch *behaviourally* — every real sympy class
      with an open chain also overrides `__getattr__`/`__setattr__`, so its
      `hasattr`/assignment outcome is not a layout observation.  L4 supplies
      real-interpreter witnesses for that branch, so the shadow's
      `raise` branch and its `return True` branch are both taken.

DOMAIN (mapping.md §2's carrier, inverted; no branch is routed around)
----------------------------------------------------------------------
The model's `Requires` is only `MustTerminate(n)` — every finite `PSeq[bool]`
is in the domain, so L4 is unrestricted and its exhaustive part is complete.
Two restrictions apply to the REAL-class legs, and both are about what the
observation means, not about which answers come out:

  * L2/L3 skip classes whose MRO contains a non-heap (C/static) type.
    `__slots__` is a heap-type mechanism; a static extension type's layout is
    not governed by any `__slots__` declaration, so the bridge's flag has no
    denotation there.  (201 of 1670 classes, chiefly `Exception` subclasses.)
  * L3 additionally skips classes where some MRO entry defines
    `__getattr__`/`__getattribute__`/`__dict__` (for the `hasattr` observation)
    or `__setattr__` (for the binding observation).  Such a class answers
    `hasattr(inst, '__dict__')` from a custom lookup hook rather than from its
    instance layout, so the observation stops being the one the model models.
    This is a restriction on the ORACLE's validity, not on the model: the one
    real class where the two diverge (`sympy.deprecated.class_registry.
    ClassRegistry`, which defines `__getattr__`) is NOT dropped — it is still
    checked by L2 against `__dictoffset__`, where the model is right and
    `hasattr` was simply reading the hook.  Every skip is counted and printed.

INPUTS — 108_191 synthetic + every real class; pinned seed 20590
----------------------------------------------------------------
L4's chain space is exhaustively ENUMERATED for every length 0..12 (all
2**13 - 1 = 8191 chains — a complete decision of that sub-space, stronger than
sampling it), then fuzzed with 100_000 further chains of length 0..14 over the
same space to reach the count.  Boundary chains (empty, singleton of each
flag, the gold `[T,T,T]` and prepatch `[T,T,F]` shapes, the faithful `[T,T]`,
a single open layer at every position) are covered by the enumeration and are
also asserted explicitly.  Seed pinned as `SEED` below and recorded in
mapping.md § G-CONF.

Exit 0 iff zero disagreements.  On disagreement the input chain and both sides'
outputs are printed and the exit status is 1.  stdlib + the repo under test.
"""
import contextlib
import importlib
import json
import pkgutil
import random
import sys
import warnings

SEED = 20590            # pinned; recorded in mapping.md § G-CONF
MAX_ENUM_LEN = 12       # exhaustive over all chains of length 0..12 (8191)
N_FUZZ = 100_000        # + fuzz over the same space
MAX_FUZZ_LEN = 14

Py_TPFLAGS_HEAPTYPE = 1 << 9


# =============================================================================
# PSeq shim — the immutable Nagini sequence the pure fold recurses on.
# =============================================================================

class PSeq(tuple):
    """Immutable sequence: len / [] / drop / take / + / ==."""

    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    def drop(self, n):
        return ToSeq(tuple.__getitem__(self, slice(n, None)))

    def take(self, n):
        return ToSeq(tuple.__getitem__(self, slice(None, n)))

    def __add__(self, other):
        return ToSeq(tuple(self) + tuple(other))


def ToSeq(items):
    """Materialize a PSeq from any iterable (Nagini's ToSeq)."""
    return PSeq(*tuple(items))


# =============================================================================
# SHADOW — model.py, contracts stripped, otherwise verbatim.
# =============================================================================

class AttributeBindingRefused(Exception):
    """Signals that binding an undeclared attribute name was refused because the
    instance carries no open namespace. Stands in for the `AttributeError` the
    runtime raises (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# --- pure-start .. pure-end (the @Pure helpers), contracts stripped ----------

def all_closed_layout(chain):
    """True iff EVERY type in the chain pins a closed instance layout. Front-
    recursive over the chain so one unfold is available per step: the head must
    pin a closed layout and so must the tail."""
    if len(chain) == 0:
        return True
    return chain[0] and all_closed_layout(chain.drop(1))


def instance_admits_namespace(chain):
    """True iff an instance built from this chain carries an open per-instance
    namespace: that happens iff at least one type leaves its layout open, i.e.
    iff NOT every type pins a closed layout."""
    return not all_closed_layout(chain)


# --- impl-start .. impl-end of `bind_undeclared_attribute` -------------------

def bind_undeclared_attribute(chain):
    if all_closed_layout(chain):
        raise AttributeBindingRefused()
    return True


# --- impl-start .. impl-end of `trait_pins_closed_layout` -------------------

def trait_pins_closed_layout():
    return True


# --- impl-start .. impl-end of `core_expression_instance_admits_namespace` ---
# (`Assert(...)` proof scaffolding stripped; the locals it constrained are kept
#  verbatim rather than dead-code-eliminated.)

def core_expression_instance_admits_namespace():
    # The chain of the core expression type (root excluded): the type itself and
    # its other contributing types pin closed layouts; the remaining contributing
    # type pins a closed layout iff trait_pins_closed_layout() says so.
    trait = trait_pins_closed_layout()
    chain = PSeq(True, True, trait)
    empty = PSeq()
    one = PSeq(trait)
    two = PSeq(True, trait)
    return instance_admits_namespace(chain)


# --- impl-start .. impl-end of `core_expression_bind_undeclared_attribute` ---

def core_expression_bind_undeclared_attribute():
    trait = trait_pins_closed_layout()
    chain = PSeq(True, True, trait)
    empty = PSeq()
    one = PSeq(trait)
    two = PSeq(True, trait)
    return bind_undeclared_attribute(chain)


# =============================================================================
# TYPE BRIDGE (mapping.md §2, inverted)
# =============================================================================

def declares_closed_layout(cls):
    """The bridge, forward direction: does this class pin a closed instance
    layout?  True iff it declares `__slots__` in its OWN body and that
    declaration does not itself re-open the namespace by listing `__dict__`.
    (mapping.md §2: "a class declares __slots__" -> flag True; "a class omits
    __slots__ (contributes a per-instance __dict__)" -> flag False.)"""
    if '__slots__' not in cls.__dict__:
        return False
    slots = cls.__dict__['__slots__']
    if isinstance(slots, str):
        slots = (slots,)
    try:
        names = tuple(slots)
    except TypeError:
        return True
    return '__dict__' not in names


def mro_chain(cls):
    """The real MRO with the universal root excluded (mapping.md §2: "a class's
    MRO (excluding object)" -> `chain: PSeq[bool]`, one flag per class)."""
    return [c for c in cls.__mro__ if c is not object]


def flags_of(cls):
    """The bridge, inverted: a real class -> the model's `PSeq[bool]` carrier."""
    return ToSeq([declares_closed_layout(c) for c in mro_chain(cls)])


def build_chain_class(chain):
    """The bridge, other direction: a `PSeq[bool]` -> a real class chain whose
    non-root classes carry exactly those closed-layout flags.  `chain[0]` is the
    most-derived class (the model's chain head), so build base-first.  Returns
    the leaf class, which is the one to instantiate."""
    cls = object
    for i in range(len(chain) - 1, -1, -1):
        body = {'__slots__': ()} if chain[i] else {}
        cls = type('L%d' % i, (cls,), body)
    return cls


# =============================================================================
# ORACLE — real observations through the real (patched) interpreter
# =============================================================================

def real_layout_admits_namespace(cls):
    """The C-level layout fact: does an instance of this class carry a
    per-instance namespace slot?  This is `instance_admits_namespace`'s
    denotation, read straight off the real type object."""
    return cls.__dictoffset__ != 0


def real_hasattr_dict(inst):
    """The F2P's own observation: `hasattr(b1, '__dict__')`."""
    return hasattr(inst, '__dict__')


def real_bind_undeclared(inst):
    """The F2P's own observation: `with raises(AttributeError): b1.x = 1`.
    Returns True if the binding was REFUSED with an AttributeError, False if it
    was absorbed."""
    try:
        inst.sbu_undeclared_probe_name = 1
    except AttributeError:
        return True
    return False


def shadow_bind_refused(chain):
    """The shadow's binding outcome, as a refusal flag: the impl raises
    `AttributeBindingRefused` (standing in for `AttributeError`) or returns
    True."""
    try:
        got = bind_undeclared_attribute(chain)
    except AttributeBindingRefused:
        return True
    if got is not True:
        raise AssertionError("shadow returned %r, not True" % (got,))
    return False


def all_heap(cls):
    """Every class in the chain is a Python-level (heap) type, so that the
    bridge's `__slots__` flag has a denotation for each of them."""
    return all(c.__flags__ & Py_TPFLAGS_HEAPTYPE for c in mro_chain(cls))


ATTR_LOOKUP_HOOKS = ('__getattr__', '__getattribute__', '__dict__')


def overrides_lookup(cls):
    return any(h in c.__dict__ for c in mro_chain(cls) for h in ATTR_LOOKUP_HOOKS)


def overrides_setattr(cls):
    return any('__setattr__' in c.__dict__ for c in mro_chain(cls))


# =============================================================================
# disagreement reporting
# =============================================================================

class Disagreement(Exception):
    pass


def fail(leg, what, inp, shadow, real):
    raise Disagreement(
        "DISAGREEMENT [%s] %s\n"
        "  input : %s\n"
        "  shadow: %r\n"
        "  real  : %r" % (leg, what, inp, shadow, real))


def diff_observations(leg, chain, inp_desc, real_ns, real_refused):
    """Diff both modelled observations for one chain.  `real_ns`/`real_refused`
    are None when that observation is not available for this input."""
    if real_ns is not None:
        s_ns = instance_admits_namespace(chain)
        if s_ns != real_ns:
            fail(leg, "instance_admits_namespace != real open-namespace "
                      "observation", inp_desc, s_ns, real_ns)
    if real_refused is not None:
        s_rf = shadow_bind_refused(chain)
        if s_rf != real_refused:
            fail(leg, "bind_undeclared_attribute refusal != real "
                      "undeclared-binding outcome", inp_desc, s_rf, real_refused)


# =============================================================================
# L1 — the pinned F2P shape: the real Basic / Printable
# =============================================================================

def leg1_pinned_shape(stats):
    from sympy.core.basic import Basic
    from sympy.core._print_helpers import Printable

    # (a) trait_pins_closed_layout() vs Printable's ACTUAL slot declaration.
    #     mapping.md §2: `Printable`, slot declaration -> trait_pins_closed_layout().
    shadow_trait = trait_pins_closed_layout()
    real_trait = declares_closed_layout(Printable)
    if shadow_trait != real_trait:
        fail("L1", "trait_pins_closed_layout() != Printable's real slot "
                   "declaration", "sympy.core._print_helpers.Printable "
             "(__slots__ in class body: %r)"
             % ('__slots__' in Printable.__dict__,), shadow_trait, real_trait)
    stats['l1'] += 1

    # (b) the model's chain vs the REAL MRO of Basic (mapping.md §2 + the D4
    #     padding note).  The real chain is [Basic, Printable]; the model uses
    #     PSeq(True, True, trait).  Check the padding is genuinely inert by
    #     diffing all three against the real interpreter.
    real_chain = flags_of(Basic)
    real_names = [c.__name__ for c in mro_chain(Basic)]
    model_chain = PSeq(True, True, trait_pins_closed_layout())
    faithful_chain = PSeq(True, trait_pins_closed_layout())
    if tuple(real_chain) != tuple(faithful_chain):
        fail("L1", "the faithful 2-entry model chain != Basic's real MRO flags",
             "Basic MRO (object excluded) = %r" % (real_names,),
             tuple(faithful_chain), tuple(real_chain))
    stats['l1'] += 1
    for name, ch in (("model padded chain", model_chain),
                     ("faithful 2-entry chain", faithful_chain),
                     ("real Basic MRO flags", real_chain)):
        diff_observations("L1", ch,
                          "%s = %r (Basic MRO %r)" % (name, tuple(ch), real_names),
                          real_layout_admits_namespace(Basic),
                          None)
        stats['l1'] += 1

    # (c) the F2P assertions themselves, against the model's entry points.
    b1 = Basic()
    real_ns = real_hasattr_dict(b1)            # F2P: assert not hasattr(b1,'__dict__')
    shadow_ns = core_expression_instance_admits_namespace()
    if shadow_ns != real_ns:
        fail("L1", "core_expression_instance_admits_namespace() != real "
                   "hasattr(Basic(), '__dict__')",
             "sympy.core.basic.Basic() (MRO %r)" % (real_names,),
             shadow_ns, real_ns)
    stats['l1'] += 1

    real_refused = real_bind_undeclared(Basic())   # F2P: raises(AttributeError)
    try:
        got = core_expression_bind_undeclared_attribute()
        shadow_refused = False
        shadow_out = got
    except AttributeBindingRefused:
        shadow_refused = True
        shadow_out = 'AttributeBindingRefused'
    if shadow_refused != real_refused:
        fail("L1", "core_expression_bind_undeclared_attribute() != real "
                   "`Basic().x = 1` outcome",
             "sympy.core.basic.Basic() (MRO %r)" % (real_names,),
             shadow_out, 'AttributeError' if real_refused else 'stored')
    stats['l1'] += 1
    return real_ns, real_refused


# =============================================================================
# L2 / L3 — every real class in the patched sympy package
# =============================================================================

def collect_sympy_classes():
    """Every class reachable from the patched sympy package's modules.  sympy
    prints banners / deprecation warnings on import; keep stdout clean so the
    gate's last-line read is ours."""
    import sympy
    found = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stdout(sys.stderr):
            for m in pkgutil.walk_packages(sympy.__path__, 'sympy.'):
                if '.tests' in m.name or 'benchmarks' in m.name:
                    continue
                try:
                    mod = importlib.import_module(m.name)
                except Exception:
                    continue
                for v in vars(mod).values():
                    if isinstance(v, type):
                        found[v] = True
    return list(found)


def leg23_real_classes(classes, stats):
    for cls in classes:
        if not all_heap(cls):
            stats['skip_nonheap'] += 1
            continue
        chain = flags_of(cls)
        names = [c.__name__ for c in mro_chain(cls)]
        desc = "%s.%s  MRO(object excluded)=%r flags=%r" % (
            cls.__module__, cls.__name__, names, tuple(chain))

        # L2: the layout fact, available for every eligible class.
        diff_observations("L2", chain, desc,
                          real_layout_admits_namespace(cls), None)
        stats['l2'] += 1
        if instance_admits_namespace(chain):
            stats['l2_open'] += 1
        else:
            stats['l2_closed'] += 1

        # L3: the behavioural observations, where they denote the layout.
        want_ns = not overrides_lookup(cls)
        want_bind = want_ns and not overrides_setattr(cls)
        if not want_ns:
            stats['skip_lookup_override'] += 1
            continue
        try:
            inst = object.__new__(cls)
        except Exception:
            stats['skip_uninstantiable'] += 1
            continue
        real_ns = real_hasattr_dict(inst)
        real_refused = None
        if want_bind:
            try:
                real_refused = real_bind_undeclared(object.__new__(cls))
            except Exception:
                real_refused = None
        else:
            stats['skip_setattr_override'] += 1
        diff_observations("L3", chain, desc, real_ns, real_refused)
        stats['l3'] += 1
        if real_refused is not None:
            stats['l3_bind'] += 1


# =============================================================================
# L4 — synthetic chains over the real interpreter
# =============================================================================

def check_synthetic(chain, stats, leg="L4"):
    leaf = build_chain_class(chain)
    inst = leaf()
    real_ns = real_hasattr_dict(inst)
    real_refused = real_bind_undeclared(leaf())
    # The layout fact must agree with the behavioural observation on these
    # freshly built classes (no hooks); if it does not, the oracle itself is
    # not the one we think it is, so report rather than silently prefer one.
    real_layout = real_layout_admits_namespace(leaf)
    if real_layout != real_ns:
        fail(leg, "oracle internally inconsistent: __dictoffset__ vs hasattr",
             "chain=%r" % (tuple(chain),), real_layout, real_ns)
    diff_observations(leg, chain, "synthetic chain=%r" % (tuple(chain),),
                      real_ns, real_refused)
    stats['l4'] += 1
    if real_refused:
        stats['l4_refused'] += 1
    else:
        stats['l4_stored'] += 1


def enumerate_chains(max_len):
    """Every bool chain of length 0..max_len — the model's domain restricted to
    those lengths, decided EXHAUSTIVELY (2**(max_len+1) - 1 chains)."""
    for n in range(max_len + 1):
        for bits in range(1 << n):
            yield ToSeq([bool((bits >> i) & 1) for i in range(n)])


def boundary_chains():
    """Explicit boundary shapes (also inside the enumeration; asserted here so
    each named case is visibly exercised)."""
    out = [
        PSeq(),                          # empty chain -> all closed, no namespace
        PSeq(True),                      # singleton closed
        PSeq(False),                     # singleton open
        PSeq(True, True),                # the faithful gold Basic chain
        PSeq(True, False),               # the BUG shape (Basic closed, trait open)
        PSeq(False, True),
        PSeq(True, True, True),          # the model's gold padded chain
        PSeq(True, True, False),         # the model's prepatch padded chain
    ]
    # a single open layer at every position of a length-6 chain: the fold must
    # find it wherever it is.
    for i in range(6):
        out.append(ToSeq([j != i for j in range(6)]))
    out.append(ToSeq([True] * 10))
    out.append(ToSeq([False] * 10))
    return out


# =============================================================================

def main():
    stats = dict(l1=0, l2=0, l2_open=0, l2_closed=0, l3=0, l3_bind=0,
                 l4=0, l4_refused=0, l4_stored=0, boundary=0,
                 enumerated=0, fuzzed=0, skip_nonheap=0,
                 skip_lookup_override=0, skip_setattr_override=0,
                 skip_uninstantiable=0)
    try:
        # L1 — the pinned F2P shape (real Basic / real Printable).
        f2p_ns, f2p_refused = leg1_pinned_shape(stats)

        # L2 / L3 — every real class in the patched package.
        classes = collect_sympy_classes()
        leg23_real_classes(classes, stats)

        # L4 — boundary, then the exhaustive enumeration, then fuzz.
        for chain in boundary_chains():
            check_synthetic(chain, stats)
            stats['boundary'] += 1
        for chain in enumerate_chains(MAX_ENUM_LEN):
            check_synthetic(chain, stats)
            stats['enumerated'] += 1
        rng = random.Random(SEED)
        for _ in range(N_FUZZ):
            n = rng.randint(0, MAX_FUZZ_LEN)
            # bias towards all-closed so the refusal branch is well populated
            # at longer lengths too, without excluding any chain.
            p = 0.5 if rng.random() < 0.5 else 0.95
            check_synthetic(ToSeq([rng.random() < p for _ in range(n)]),
                            stats)
            stats['fuzzed'] += 1
    except Disagreement as exc:
        print(str(exc))
        print(json.dumps({"checked": sum(stats[k] for k in
                                         ('l1', 'l2', 'l3', 'l4')),
                          "disagreements": 1, "seed": SEED,
                          "shadow": "direct (contract-stripped impl regions)"}))
        return 1

    checked = stats['l1'] + stats['l2'] + stats['l3'] + stats['l4']
    if stats['l4_refused'] == 0 or stats['l4_stored'] == 0:
        print("G-CONF FAIL: input generation did not take both impl branches "
              "(refused=%d stored=%d)" % (stats['l4_refused'],
                                          stats['l4_stored']))
        return 1
    if checked < 100_000:
        print("G-CONF FAIL: only %d inputs checked, need >= 1e5" % checked)
        return 1

    print("G-CONF OK: contract-stripped impl regions of model.py agree with the "
          "real patched sympy on %d inputs — %d pinned F2P observations (real "
          "Basic/Printable: hasattr(Basic(),'__dict__')=%r, undeclared binding "
          "refused=%r), %d real classes by layout (%d open-chain / %d closed-"
          "chain), %d real classes behaviourally (%d incl. undeclared binding), "
          "%d synthetic chains over the real interpreter (%d boundary + %d "
          "exhaustive over all lengths 0..%d + %d fuzz, seed %d; %d refused / "
          "%d stored). Skipped as outside the bridge's denotation: %d non-heap "
          "MRO, %d lookup-hook override, %d setattr override, %d "
          "uninstantiable. 0 disagreements."
          % (checked, stats['l1'], f2p_ns, f2p_refused,
             stats['l2'], stats['l2_open'], stats['l2_closed'],
             stats['l3'], stats['l3_bind'],
             stats['l4'], stats['boundary'], stats['enumerated'],
             MAX_ENUM_LEN, stats['fuzzed'], SEED,
             stats['l4_refused'], stats['l4_stored'],
             stats['skip_nonheap'], stats['skip_lookup_override'],
             stats['skip_setattr_override'], stats['skip_uninstantiable']))
    print(json.dumps({
        "checked": checked,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl regions of model.py; no "
                  "@ContractOnly callee — the __slots__/__dict__ rule is "
                  "modelled deeply)",
        "oracle": "real patched sympy: sympy.core.basic.Basic / "
                  "sympy.core._print_helpers.Printable and every class in the "
                  "package, observed via __dictoffset__, hasattr(inst, "
                  "'__dict__') and real undeclared-attribute binding",
        "legs": {"pinned_f2p": stats['l1'], "real_class_layout": stats['l2'],
                 "real_class_behaviour": stats['l3'],
                 "synthetic_chains": stats['l4']},
        "branches": {"refused": stats['l4_refused'],
                     "stored": stats['l4_stored']},
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
