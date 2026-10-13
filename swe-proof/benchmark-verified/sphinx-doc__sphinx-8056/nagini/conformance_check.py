#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8056 (nagini).

SHADOW: the impl region of model.py's ``emitted_names``, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped and PSeq
realized as an immutable tuple shim. The three @Pure @ContractOnly callees
(``num_commas`` / ``split_on_comma`` / ``trim``) are axiomatized stand-ins for
UNCHANGED Python built-ins (mapping.md section 3), so per the contract they
call the REAL callees here: ``str.count(',')`` / ``str.split(',')`` /
``str.strip()`` over the code-point carrier.

ORACLE: the REAL patched repo method the model models per mapping.md —
``sphinx.ext.napoleon.docstring.GoogleDocstring._consume_fields`` (its
per-field body, as reached with the per-comma expansion flag). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. The model's boundary places the field tuple
production (``_consume_field``) and the section-break scan OUTSIDE the modeled
region — they are unchanged upstream producers whose output is the model's
INPUT — so the oracle instantiates a real GoogleDocstring and replaces exactly
those producers with a queue of prepared (name, type, desc) fields, then calls
the real ``_consume_fields`` method itself. Everything inside the modeled
region executes for real.

Type bridge (mapping.md section 2): the name run is carried as List[int] of
Unicode code points (``name[k] == ord(_name[k])``); the emitted-name sequence
is PSeq[PSeq[int]] and is lowered back to a list of str for comparison. The
type / description of a field are summarized by their truthiness
(``type_nonempty`` / ``desc_nonempty``) and ride along verbatim across every
emitted entry, so the oracle ALSO asserts each emitted tuple carries the
input's type/desc objects unchanged.

Input domain: Requires demands only a readable name list — every str-shaped
name satisfies it. Fields are fed in batches so the real method's consume loop
runs across many fields per call; each field counts as one compared input.

>= 1e5 Requires-satisfying inputs: boundary cases x all 8 flag combos + fuzz.
Pinned fuzz seed: 8056.

Exit 0 iff zero disagreements; on a disagreement the offending field, the
shadow output and the real output are printed and the exit code is 1.
stdlib only.
"""
import json
import random
import sys

SEED = 8056
N_FUZZ = 100_000
BATCH = 50


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
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

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


def pseq_to_str(s):
    return "".join(chr(s[k]) for k in range(len(s)))


def str_to_pseq(s):
    return PSeq._wrap(ord(c) for c in s)


# --- @ContractOnly callees realized by the REAL built-ins they stand in for --

def num_commas(s):
    return pseq_to_str(s).count(",")


def split_on_comma(s):
    return PSeq._wrap(str_to_pseq(p) for p in pseq_to_str(s).split(","))


def trim(s):
    return str_to_pseq(pseq_to_str(s).strip())


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def emitted_names(name, multiple, type_nonempty, desc_nonempty):
    result = PSeq(ToSeq(name)).take(0)  # type: PSeq
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq
        n = num_commas(ToSeq(name)) + 1
        i = 0
        while i < n:
            piece = trim(parts[i])  # type: PSeq
            old_result = result  # type: PSeq
            result = result + PSeq(piece)
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
        return result
    # impl-end (verbatim copy ends here)


def shadow_names(name_str, multiple, type_nonempty, desc_nonempty):
    """Run the shadow on one field; lower the emitted PSeq[PSeq[int]] to
    a list of str via the mapping.md bijection."""
    out = emitted_names([ord(c) for c in name_str], multiple,
                        type_nonempty, desc_nonempty)
    return [pseq_to_str(out[k]) for k in range(len(out))]


# --- oracle: the real patched consumer method --------------------------------

def make_real_consumer():
    """Build a callable (fields, multiple) -> emitted tuples that drives the
    REAL patched _consume_fields method. Only the unchanged upstream field
    producers (outside the modeled region) are replaced by a queue."""
    from sphinx.ext.napoleon import Config
    from sphinx.ext.napoleon.docstring import GoogleDocstring

    doc = GoogleDocstring("", Config())
    queue = []
    doc._consume_field = lambda parse_type=True, prefer_type=False: queue.pop(0)
    doc._is_section_break = lambda: not queue
    doc._consume_empty = lambda: None

    def consume(fields, multiple):
        queue[:] = list(fields)
        return doc._consume_fields(multiple=multiple)

    return consume


def check_batch(consume, batch, multiple):
    """batch: list of (name_str, type_obj, desc_obj). Returns an error string
    on any disagreement, else None. One compared input per field."""
    expected = []
    for (name_str, type_obj, desc_obj) in batch:
        names = shadow_names(name_str, multiple, bool(type_obj), bool(desc_obj))
        expected.extend((n, type_obj, desc_obj) for n in names)

    real = consume([(n, t, d) for (n, t, d) in batch], multiple)
    real = [tuple(f) for f in real]

    if real == expected:
        return None
    # localize: re-run field by field for a precise report
    for (name_str, type_obj, desc_obj) in batch:
        names = shadow_names(name_str, multiple, bool(type_obj), bool(desc_obj))
        exp1 = [(n, type_obj, desc_obj) for n in names]
        real1 = [tuple(f) for f in consume([(name_str, type_obj, desc_obj)],
                                           multiple)]
        if real1 != exp1:
            return ("DISAGREEMENT\n  name=%r multiple=%r type=%r desc=%r\n"
                    "  shadow=%r\n  real=%r"
                    % (name_str, multiple, type_obj, desc_obj, exp1, real1))
    return ("DISAGREEMENT (batch-level only)\n  multiple=%r batch=%r\n"
            "  shadow=%r\n  real=%r" % (multiple, batch, expected, real))


BOUNDARY_NAMES = [
    "", ",", ",,", " , ", "x1, x2", "x1,x2", "x1, x2, x3",
    " x ", "  ", "a ,b, c ", "x,", ",y", " a , b , c ",
    r"\*args, \*\*kwargs", "x1, x2, optional", "no_comma",
    "  spaced  name  ", "\tx1,\ty2\n", "x1 , x2 , x3",
]


def rand_name(rng):
    alphabet = list("ab x1y2,*\\_") + [" ", ",", "\t", "\n"]
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))


def main():
    consume = make_real_consumer()
    checked = 0

    # F2P-shaped sanity anchor first: multi-name run under both flag values.
    for m in (True, False):
        err = check_batch(consume, [("x1, x2", "array_like", ["d"])], m)
        if err:
            print(err)
            return 1
        checked += 1

    # boundary names x all (multiple, type_nonempty, desc_nonempty) combos
    for name in BOUNDARY_NAMES:
        for m in (True, False):
            for t in ("int", ""):
                for d in (["line one", "line two"], []):
                    err = check_batch(consume, [(name, t, d)], m)
                    if err:
                        print(err)
                        return 1
                    checked += 1

    # fuzz: batches of BATCH fields per real consume-loop call
    rng = random.Random(SEED)
    remaining = N_FUZZ
    while remaining > 0:
        k = min(BATCH, remaining)
        m = rng.choice((True, False))
        batch = []
        for _ in range(k):
            t = rng.choice(("T", ""))
            d = rng.choice((["desc"], []))
            batch.append((rand_name(rng), t, d))
        err = check_batch(consume, batch, m)
        if err:
            print(err)
            return 1
        checked += k
        remaining -= k

    print("G-CONF OK: shadow impl == real patched consumer on %d field inputs "
          "(%d boundary combos + %d fuzz, seed %d)."
          % (checked, checked - N_FUZZ, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
