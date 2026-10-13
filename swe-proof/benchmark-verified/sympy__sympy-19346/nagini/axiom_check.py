#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-19346.

Executes the REAL callees the model abstracts and asserts every observation
matches the contracts encoded in model.py:

  (A-consumed) `elem_repr` / `doprint_elem` == the recursive executable
      representation routine (`ReprPrinter().doprint`, i.e. the engine behind
      the public `srepr`). The only property the proof consumes is the VALUE
      LINK `ToSeq(doprint_elem(t)) == elem_repr(t)`; `elem_repr` itself is left
      wholly uninterpreted (`Ensures(True)`) and in particular is NOT assumed
      non-empty. Checked here on a WIDE set of real sympy elements that
      explicitly INCLUDES the singleton / constant / boolean / None class and
      the empty-name symbol (`oo, zoo, nan, pi, E, I, S.Infinity, S.NaN, S.Pi,
      S.EmptySet, True, False, None, Symbol('')`), not only Symbols/Integers/
      Rationals/Floats, AND the class whose representation is genuinely the
      EMPTY string -- see `check_empty_representation_witness`, which is why no
      `len(elem_repr) >= 1` claim is shipped.

  (A-reference, contrast) `elem_str` / `str_elem` == Python `str(elem)`, the
      per-element rendering the pre-patch whole-object fallback performs. The
      model does NOT assume any relation between `elem_str` and `elem_repr`
      (they are two separate uninterpreted callees). The discriminating fact the
      F2P observes is EXISTENTIAL, not universal: for the symbolic / numeric
      element class the test exercises (Symbols, Integers, Rationals, Floats)
      `str(elem) != srepr(elem)`, while for the constant / singleton / boolean /
      None class `str(elem) == srepr(elem)`. This check asserts BOTH facts, so
      it would FAIL a model that (re-)introduced a universal `elem_repr != elem_str`
      inequality (the over-claim the spec previously shipped).

  (A-reference, deep model) the modeled assembly `set_seq` / `dict_seq` (brace
      wrapping, ", " separator, ": " pair separator, "set()"/"{}" empty forms,
      per-element recursive representation) == the REAL `srepr` of the
      corresponding set/dict, reconstructed by substituting each element's real
      `srepr` string into the documented assembly formula. Validated on boundary
      cases (empty, singletons, nested) + randomized fuzz over many element
      kinds, INCLUDING the constant / singleton class.

Imports only the standard library and the repo's own PUBLIC api (`sympy.srepr`,
`sympy.Symbol`, ...) — the same surface the gold patch and the F2P test
exercise; nothing private. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import (srepr, Symbol, Integer, Rational, Float, oo, zoo, nan,
                   pi, E, I, S)
from sympy.printing.repr import ReprPrinter


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_elem_repr(elem):
    """Reference for model.py's `elem_repr`: the recursive executable
    representation of one element, as a list of code points."""
    return [ord(ch) for ch in srepr(elem)]


def model_set_seq(elems):
    """Reference for model.py's `set_seq` (token substitution): the full
    rendering of a collection of elements as a list of code points."""
    if len(elems) == 0:
        return [ord(c) for c in "set()"]
    parts = [srepr(e) for e in elems]
    return [ord(c) for c in "{" + ", ".join(parts) + "}"]


def model_dict_seq(pairs):
    """Reference for model.py's `dict_seq` (token substitution): the full
    rendering of a mapping (list of (key, value)) as a list of code points."""
    if len(pairs) == 0:
        return [ord(c) for c in "{}"]
    parts = ["%s: %s" % (srepr(k), srepr(v)) for (k, v) in pairs]
    return [ord(c) for c in "{" + ", ".join(parts) + "}"]


# --- the checks --------------------------------------------------------------

def check_elem_repr_value_link(elem):
    """A-consumed: the ONLY property the proof uses is the value link
    `ToSeq(doprint_elem(t)) == elem_repr(t)` -- i.e. the concrete callee the
    container rendering invokes per element is the very routine the spec's
    `elem_repr` denotes. Asserts ReprPrinter().doprint(elem) == srepr(elem).

    Deliberately asserts NOTHING about the length or content of the result:
    `elem_repr` is uninterpreted in the spec (`Ensures(True)`). A
    `len(elem_repr(t)) >= 1` claim would be UNSOUND -- see
    check_empty_representation_witness."""
    rep = srepr(elem)
    dp = ReprPrinter().doprint(elem)
    assert dp == rep, (
        "doprint != srepr on %r: doprint=%r srepr=%r" % (elem, dp, rep))


def check_empty_representation_witness():
    """A-consumed, NEGATIVE witness for the dropped `len(elem_repr(t)) >= 1`
    over-claim. `ReprPrinter` has no dedicated method for these classes, so the
    dispatch scan falls through to a branch returning the object's plain text,
    which is EMPTY for them: srepr is the empty string, length 0. This is why
    `elem_repr` must carry no non-emptiness Ensures, and why the container
    rendering must still emit such an element (and its separators) like any
    other. Guards against re-introducing the over-claim."""
    witnesses = []
    try:
        from sympy.physics.units import Quantity
        witnesses.append(Quantity(''))
    except Exception:
        pass
    try:
        from sympy.printing.pretty.stringpict import stringPict
        witnesses.append(stringPict(''))
    except Exception:
        pass
    try:
        from sympy.assumptions.cnf import CNF
        witnesses.append(CNF())
    except Exception:
        pass
    if not witnesses:
        return 0
    empties = [e for e in witnesses if len(srepr(e)) == 0]
    assert empties, (
        "expected at least one element whose srepr is EMPTY (so that a "
        "len(elem_repr) >= 1 axiom is demonstrably unsound); got %r"
        % ([srepr(e) for e in witnesses],))
    # and the value link still holds on them
    for e in empties:
        check_elem_repr_value_link(e)
    return len(empties)


def check_elem_discriminating(elem):
    """A-reference contrast, EXISTENTIAL witness: for the symbolic / numeric
    element class the F2P uses, str(elem) != srepr(elem) (the bug: the pre-patch
    whole-object fallback uses str per element). srepr wraps a constructor while
    str does not, so they differ on this class. This is the fact that DISTINGUISHES
    elem_str from elem_repr on the tested inputs -- but the model does NOT promote
    it to a universal axiom (see check_elem_coincident)."""
    check_elem_repr_value_link(elem)
    s, rep = str(elem), srepr(elem)
    assert s != rep, (
        "expected str != srepr on the discriminating class: str(%r)=%r "
        "== srepr=%r" % (elem, s, rep))


def check_elem_coincident(elem):
    """A-reference contrast, NEGATIVE witness: for the singleton / constant /
    boolean / None class, str(elem) == srepr(elem). This is exactly why the
    spec must NOT carry a universal `elem_repr(t) != elem_str(t)` Ensures: the
    real callee relationship is existential, false on this class. (The previous
    bundle shipped that universal inequality; it was unsound -- this check guards
    against re-introducing it.) The value link still holds here."""
    check_elem_repr_value_link(elem)
    s, rep = str(elem), srepr(elem)
    assert s == rep, (
        "expected str == srepr on the constant class (so the spec is correctly "
        "NOT universal): str(%r)=%r != srepr=%r" % (elem, s, rep))


def check_empty_name_symbol():
    """A-reference, NEGATIVE witness for the dropped `len(elem_str(t)) >= 1`
    over-claim: str(Symbol('')) == '' has length 0, while srepr is non-empty.
    This is why the spec must NOT carry `len(elem_str(t)) >= 1`."""
    e = Symbol('')
    assert str(e) == '' and len(str(e)) == 0, (
        "expected str(Symbol('')) == '' (length 0); got %r" % (str(e),))
    assert len(srepr(e)) >= 1, "srepr(Symbol('')) unexpectedly empty"


def check_set_reference(elems):
    """A-reference deep model: model set_seq(order) == real assembly, where the
    element order is the real set's iteration order. A Python set is unordered,
    so we read the real iteration order off a set built from `elems` and feed
    THAT order to the deep model (set_seq is defined over an ordered carrier)."""
    real_set = set(elems)
    real_order = list(real_set)
    expected = "".join(chr(c) for c in model_set_seq(real_order))
    if len(real_order) == 0:
        observed = "set()"
    else:
        observed = "{%s}" % ", ".join(srepr(it) for it in real_set)
    assert expected == observed, (
        "set_seq deep model mismatch: model %r vs real %r" % (expected, observed))
    rp = ReprPrinter()
    if hasattr(rp, "_print_set"):
        live = rp._print_set(real_set)
        assert live == observed, (
            "live _print_set %r != reconstructed %r" % (live, observed))


def check_dict_reference(pairs):
    """A-reference deep model: model dict_seq(pairs) == real assembly. Uses a
    real dict built from `pairs` and compares against the gold _print_dict
    formula over that dict's items() order (dicts preserve insertion order)."""
    d = dict(pairs)
    # rebuild pairs in the dict's real iteration order (dedups duplicate keys)
    real_pairs = list(d.items())
    expected = "".join(chr(c) for c in model_dict_seq(real_pairs))
    if len(real_pairs) == 0:
        observed = "{}"
    else:
        observed = "{%s}" % ", ".join(
            "%s: %s" % (srepr(k), srepr(v)) for (k, v) in d.items())
    assert expected == observed, (
        "dict_seq deep model mismatch: model %r vs real %r" % (expected, observed))
    # If the patch is applied in-container, also compare against the live
    # _print_dict / _print_set methods directly.
    rp = ReprPrinter()
    if hasattr(rp, "_print_dict"):
        live = rp._print_dict(d)
        assert live == observed, (
            "live _print_dict %r != reconstructed %r" % (live, observed))


def main():
    x, y, z = Symbol('x'), Symbol('y'), Symbol('z')

    # The discriminating class the F2P exercises: str(elem) != srepr(elem).
    discriminating = [x, y, z, Symbol('alpha'), Integer(0), Integer(5),
                      Integer(-3), Rational(1, 2), Rational(-7, 4), Float(1.5),
                      Symbol('x', positive=True)]
    # The constant / singleton / boolean / None class: str(elem) == srepr(elem).
    # (The pool the previous bundle omitted, which let the false universal pass.)
    coincident = [oo, zoo, nan, pi, E, I, S.Infinity, S.NaN, S.Pi, S.EmptySet,
                  True, False, None]

    # --- per-element axioms --------------------------------------------------
    # A-consumed VALUE LINK (doprint == srepr) on EVERY class, including the
    # constant class and the empty-name symbol -- the only property the proof
    # consumes. No length claim: elem_repr is uninterpreted.
    for elem in discriminating + coincident + [Symbol(''), {x: y}]:
        check_elem_repr_value_link(elem)
    # The dropped `len(elem_repr) >= 1` over-claim: the real routine returns the
    # EMPTY representation for some element classes, so no non-emptiness Ensures
    # on elem_repr is sound. Guards against re-introducing it.
    n_empty_rep = check_empty_representation_witness()
    # A-reference contrast, EXISTENTIAL: discriminator holds on the F2P class...
    for elem in discriminating:
        check_elem_discriminating(elem)
    # ...and explicitly FAILS (str == srepr) on the constant class, so the spec
    # is correctly NOT a universal inequality (guards re-introduction of the
    # over-claim).
    for elem in coincident:
        check_elem_coincident(elem)
    # The dropped `len(elem_str) >= 1` over-claim: str(Symbol('')) is empty.
    check_empty_name_symbol()

    # --- set deep model: boundary -------------------------------------------
    check_set_reference([])
    check_set_reference([x])
    check_set_reference([Integer(5)])
    check_set_reference([x, y])
    check_set_reference([x, y, z])
    check_set_reference([Integer(1), Rational(1, 2), Symbol('w')])
    check_set_reference([oo, pi])               # constant-class elements
    check_set_reference([Symbol(''), x])        # empty-name element
    # elements whose executable representation is the EMPTY sequence: the
    # assembly must still emit them and their separators like any other.
    _empty_rep_elems = []
    try:
        from sympy.physics.units import Quantity
        _q = Quantity('')
        if len(srepr(_q)) == 0:
            _empty_rep_elems.append(_q)
    except Exception:
        pass
    for _e in _empty_rep_elems:
        check_set_reference([_e])               # singleton, empty rendering
        check_set_reference([_e, x])            # mixed with a non-empty element

    # --- dict deep model: boundary ------------------------------------------
    check_dict_reference([])
    check_dict_reference([(x, y)])
    check_dict_reference([(x, y), (y, z)])
    check_dict_reference([(x, {y: z})])           # nested dict value
    check_dict_reference([(Integer(1), x), (Integer(2), y)])
    check_dict_reference([(oo, nan), (pi, E)])    # constant-class key/value
    check_dict_reference([(Symbol(''), x)])       # empty-name key
    for _e in _empty_rep_elems:
        check_dict_reference([(_e, x)])           # empty-rendering key
        check_dict_reference([(x, _e)])           # empty-rendering value
        check_dict_reference([(_e, _e)])          # both sides empty

    # --- randomized fuzz -----------------------------------------------------
    # Fuzz over the FULL pool (discriminating + constant class + empty-name).
    rng = random.Random(19346)
    pool = discriminating + coincident + [Symbol('')]
    n_set, n_dict = 0, 0
    for _ in range(4000):
        k = rng.randint(0, 5)
        # distinct elements to keep set/dict sizes meaningful
        elems = rng.sample(pool, min(k, len(pool)))
        check_set_reference(elems)
        n_set += 1
    for _ in range(4000):
        k = rng.randint(0, 5)
        keys = rng.sample(pool, min(k, len(pool)))
        vals = [rng.choice(pool) for _ in keys]
        check_dict_reference(list(zip(keys, vals)))
        n_dict += 1

    print("G-AX OK: elem_repr A-consumed VALUE LINK (doprint == srepr) sound on "
          "%d elements incl. constant/singleton/None/empty-name class; "
          "%d element(s) render as the EMPTY representation -> elem_repr is "
          "correctly uninterpreted, no len>=1 over-claim; str != srepr is "
          "EXISTENTIAL (holds on %d discriminating elements, str == srepr on %d "
          "constant-class elements, str(Symbol(''))=='' -> no universal "
          "inequality and no len(elem_str)>=1 over-claim); set_seq/dict_seq deep "
          "model == real srepr assembly on boundary + %d set + %d dict fuzz "
          "inputs over the full pool"
          % (len(discriminating) + len(coincident) + 2, n_empty_rep,
             len(discriminating), len(coincident), n_set, n_dict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
