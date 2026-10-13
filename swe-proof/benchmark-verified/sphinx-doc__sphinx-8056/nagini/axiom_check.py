#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8056.

The model axiomatizes three UNCHANGED stdlib string operations the consumer
calls and checks them against the REAL Python callees on boundary + fuzz
inputs:

  num_commas(s)      stands in for ``s.count(',')``; the axiom only claims
                     ``num_commas(s) >= 0`` and ``num_commas('') == 0``.
  split_on_comma(s)  stands in for ``s.split(',')``; the axiom only claims
                     ``len(split_on_comma(s)) == num_commas(s) + 1``.
  trim(s)            stands in for ``s.strip()``; the documented (weak)
                     behaviour is "leading/trailing whitespace removed, interior
                     content preserved".

The check asserts that the REAL callees SATISFY each axiom's Ensures (soundness
direction: the real behaviour is no weaker than the contract the proof relies
on), and that the COMPOSED observable the model's postcondition demands -- under
the per-comma expansion, ``num_commas(name)+1`` emitted names, the k-th being
``trim(split_on_comma(name)[k])`` -- equals the gold patch's real computation
``[piece.strip() for piece in name.split(',')]``.

Imports nothing repo-specific: ``str.split`` / ``str.strip`` / ``str.count``
are Python built-ins -- the exact operations the gold patch calls. Exit 0 iff
every obligation holds.
"""
import random
import sys


# --- axiom soundness against the real callees --------------------------------

def check_num_commas(s):
    """num_commas axiom: Result() >= 0; '' -> 0 (real: str.count(','))."""
    real = s.count(",")
    assert real >= 0, "count(',') negative on %r" % (s,)
    if s == "":
        assert real == 0, "count(',') on empty string is %r" % (real,)


def check_split_len(s):
    """split_on_comma axiom: len(split) == num_commas + 1 (real str.split)."""
    parts = s.split(",")
    assert len(parts) == s.count(",") + 1, (
        "split_on_comma length axiom unsound on %r: split gave %d runs, "
        "axiom requires count+1 == %d" % (s, len(parts), s.count(",") + 1))


def check_trim(s):
    """trim axiom: leading/trailing whitespace removed, interior preserved
    (real str.strip()). We verify the *documented* properties the axiom states:
      * trim(s) is a contiguous interior slice of s (a suffix of a prefix);
      * its endpoints are non-whitespace (or it is empty);
      * stripping is idempotent.
    These are exactly what str.strip() guarantees."""
    t = s.strip()
    # idempotent
    assert t.strip() == t, "strip not idempotent on %r" % (s,)
    # t is an interior substring of s preserving order/content
    assert t in s, "strip result %r not a substring of %r" % (t, s)
    if t:
        assert not t[0].isspace() and not t[-1].isspace(), (
            "strip left surrounding whitespace on %r -> %r" % (s, t))
        # interior preserved: s with leading+trailing whitespace removed == t
        assert s.lstrip().rstrip() == t


# --- the composed observable == the gold patch's real computation ------------

def model_emitted_names(name, multiple, type_nonempty, desc_nonempty):
    """Reference implementation of model.py's emitted_names, computed with the
    REAL stdlib callees the axioms stand in for."""
    if multiple and len(name) > 0:
        # one entry per comma-separated run, each trimmed -- the gold patch's
        # ``for n in _name.split(','): fields.append((n.strip(), ...))``.
        return [piece.strip() for piece in name.split(",")]
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            return [name]            # single verbatim entry
        return []                    # entirely-empty field dropped


def gold_consume(name, multiple, type_nonempty, desc_nonempty):
    """The gold patch's _consume_fields per-field behaviour, transcribed
    directly from sphinx/ext/napoleon/docstring.py @ patched commit:

        if multiple and _name:
            for n in _name.split(','):
                fields.append((n.strip(), _type, _desc))
        elif _name or _type or _desc:
            fields.append((_name, _type, _desc))
    """
    fields = []
    if multiple and name:
        for n in name.split(","):
            fields.append(n.strip())
    elif name or type_nonempty or desc_nonempty:
        fields.append(name)
    return fields


def check_composed(name, multiple, type_nonempty, desc_nonempty):
    model = model_emitted_names(name, multiple, type_nonempty, desc_nonempty)
    gold = gold_consume(name, multiple, type_nonempty, desc_nonempty)
    assert model == gold, (
        "model emitted_names != gold _consume_fields on "
        "name=%r multiple=%r type=%r desc=%r: model=%r gold=%r"
        % (name, multiple, type_nonempty, desc_nonempty, model, gold))
    # also re-assert the model.py postcondition clauses directly
    if multiple and len(name) > 0:
        assert len(model) == name.count(",") + 1, (
            "count clause violated on %r: %d != %d"
            % (name, len(model), name.count(",") + 1))
        parts = name.split(",")
        for k in range(len(model)):
            assert model[k] == parts[k].strip(), (
                "content clause violated at %d on %r" % (k, name))
    else:
        assert len(model) <= 1
        expect_one = (len(name) > 0 or type_nonempty or desc_nonempty)
        assert (len(model) == 1) == expect_one
        if len(model) == 1:
            assert model[0] == name


def main():
    # F2P discriminator (test_multiple_parameters): "x1, x2" -> ["x1", "x2"]
    assert model_emitted_names("x1, x2", True, False, True) == ["x1", "x2"], \
        "F2P multi-name expansion broken"
    assert model_emitted_names("x1, x2", False, False, True) == ["x1, x2"], \
        "F2P non-expansion (single verbatim field) broken"

    boundary = [
        "", ",", ",,", "x1, x2", "x1,x2", "x1, x2, x3",
        " x ", "  ", " , ", "a ,b, c ", "x,", ",y", " a , b , c ",
        "*args, **kwargs", "\\*args, \\*\\*kwargs", "x1, x2, optional",
        "no_comma", "  spaced  name  ", "\tx1,\ty2\n",
    ]
    flags = [(m, t, d) for m in (True, False) for t in (True, False)
             for d in (True, False)]

    for s in boundary:
        check_num_commas(s)
        check_split_len(s)
        check_trim(s)
        for (m, t, d) in flags:
            check_composed(s, m, t, d)

    rng = random.Random(8056)
    alphabet = list("ab x1y2,*\\_") + [" ", ",", "\t", "\n", ""]
    for _ in range(30000):
        n = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_num_commas(s)
        check_split_len(s)
        check_trim(s)
        m = rng.choice((True, False))
        t = rng.choice((True, False))
        d = rng.choice((True, False))
        check_composed(s, m, t, d)

    print("G-AX OK: num_commas/split_on_comma/trim axioms sound vs real "
          "str.count/str.split/str.strip; composed emitted_names == gold "
          "_consume_fields on %d boundary + 30000 fuzz inputs x flag combos"
          % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
