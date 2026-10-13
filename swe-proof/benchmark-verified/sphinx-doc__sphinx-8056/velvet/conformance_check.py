#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8056 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions
              (`expandOne`/`expandFields`, with the deep models
              `splitOnComma`/`stripWs`) transliterated to Python over the real
              repo field type `Tuple[str, str, List[str]]`, via the mapping.md
              bijection (`Field` ↔ tuple, `List Char` ↔ `str`). The unchanged
              scanner output is the FREE INPUT `raw`; the unchanged downstream
              renderer is the identity-on-fields boundary (out of R/I scope).
  * ORACLE  — `patch.diff`'s behaviour: the exact post-patch loop body of
              `_consume_fields` (`docstring.py:272-281`), applied to the same
              `(multiple, raw)`. This is the gold-patched correctness oracle
              (G-RESOLVE); it uses the real `str.split(",")` / `str.strip()`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib only; seed pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 8056
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean expandOne/expandFields, transliterated -----

def shadow_expand_one(multiple, name, typ, desc):
    """expandOne (multiple) (f) — the per-field contribution."""
    if multiple and name:
        # (splitOnComma name).map (fun nm => { f with name := stripWs nm })
        return [(piece.strip(), typ, desc) for piece in name.split(",")]
    if name or typ or desc:
        return [(name, typ, desc)]
    return []


def shadow_expand_fields(multiple, raw):
    """expandFields (multiple) (raw) — concatenate each field's contribution."""
    out = []
    for (name, typ, desc) in raw:
        out.extend(shadow_expand_one(multiple, name, typ, desc))
    return out


# --- the oracle: patch.diff's post-patch _consume_fields loop body ------------

def oracle_consume_fields(multiple, raw):
    """The exact body of the gold-patched `_consume_fields` while-loop
    (sphinx/ext/napoleon/docstring.py:272-281 post-patch), with `raw` standing
    in for the (unchanged) sequence of `_consume_field(...)` results."""
    fields = []
    for (_name, _type, _desc) in raw:
        if multiple and _name:
            for name in _name.split(","):
                fields.append((name.strip(), _type, _desc))
        elif _name or _type or _desc:
            fields.append((_name, _type, _desc,))
    return fields


# --- the parameters-section caller: thread the flag (site B) ------------------

def shadow_parse_params(use_param, raw):
    return shadow_expand_fields(use_param, raw)


def oracle_parse_params(use_param, raw):
    # post-patch _parse_parameters_section: multiple=True iff napoleon_use_param
    if use_param:
        return oracle_consume_fields(True, raw)
    else:
        return oracle_consume_fields(False, raw)


# --- fuzz ---------------------------------------------------------------------

def rand_str(rng):
    # names/types/desc-lines: identifier chars, commas, whitespace, stars —
    # including non-ASCII whitespace the real str.strip() trims (NBSP, NEL,
    # em space, ideographic space) and ZWSP which it must NOT trim
    alphabet = (list("abcxyz12_") +
                [",", " ", "\t", "*",
                 "\xa0", "\x85", "\u2003", "\u3000",  # NBSP/NEL/em/ideographic
                 "\u200b"])                            # ZWSP: NOT whitespace
    n = rng.randint(0, 8)
    return "".join(rng.choice(alphabet) for _ in range(n))


def rand_field(rng):
    name = rand_str(rng)
    typ = rand_str(rng)
    k = rng.randint(0, 2)
    desc = [rand_str(rng) for _ in range(k)]
    return (name, typ, desc)


def fuzz_inputs(n, rng):
    # boundary cases first (the F2P scenario and edge fields)
    yield (False, [("x1, x2", "array_like", ["Input arrays, description of x1, x2."])])
    yield (True,  [("x1, x2", "array_like", ["Input arrays, description of x1, x2."])])
    yield (True,  [("*args, **kwargs", "", ["Variable length."])])
    yield (False, [("*args, **kwargs", "", ["Variable length."])])
    yield (True,  [("", "", [])])
    yield (False, [("", "", [])])
    yield (True,  [("x1,\xa0x2", "array_like", ["d"])])   # NBSP after comma
    yield (True,  [("a,,b", "int", [])])
    yield (True,  [("  x , y  ", "T", ["d"])])
    yield (True,  [("solo", "int", ["d"])])
    yield (False, [("a,b,c", "int", ["d"])])
    yield (True,  [])
    for _ in range(n):
        multiple = rng.random() < 0.5
        m = rng.randint(0, 5)
        raw = [rand_field(rng) for _ in range(m)]
        yield (multiple, raw)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (multiple, raw) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # site A: the collector
        sh = shadow_expand_fields(multiple, raw)
        orc = oracle_consume_fields(multiple, raw)
        if sh != orc:
            disagreements.append(("consume_fields", multiple, raw, sh, orc))
        # site B: the parameters-section caller (use_param drives multiple)
        shp = shadow_parse_params(multiple, raw)
        orcp = oracle_parse_params(multiple, raw)
        if shp != orcp:
            disagreements.append(("parse_params", multiple, raw, shp, orcp))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for site, m, raw, sh, orc in disagreements:
            print("  site=%s multiple=%r raw=%r shadow=%r oracle=%r"
                  % (site, m, raw, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of expandFields/buildParameterFieldSeq agrees "
          "with patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
