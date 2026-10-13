#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7748 (nagini).

SHADOW: the impl region of model.py (`gather_signatures`), copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The body uses only plain Python lists, so no sequence shim is needed on the
shadow path; the @Pure helpers `run_len`/`collected` (stated over PSeq) copy
over on top of a small immutable-tuple PSeq shim and are exercised as an
internal cross-check on the boundary inputs only. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
`sphinx.ext.autodoc.DocstringSignatureMixin._find_signature` together with
`format_signature`. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable. For
each generated input a minimal probe documenter (a DocstringSignatureMixin
subclass with just the attributes the mixin reads: objpath, directive
settings, get_doc returning the block) runs the real gathering loop; the
observable is the ordered collected signature sequence
`[rendering(result)] + self._signatures`, which is exactly the content
`format_signature` joins in order. On the boundary inputs the join itself is
additionally exercised end-to-end through the real `format_signature` (with a
stub base-class renderer standing in for the unchanged upstream formatting of
the FIRST signature) and its line order compared against the primary
observable.

TYPE BRIDGE (mapping.md section 2 / "Modelled domain"): the model's domain is
a clean run — a documentation block whose lines are all accepted signature
lines (regex-matching, base name valid). The block is lifted to two parallel
List[int] streams: cont[k] non-zero iff line k carries over to the next
(trailing continuation marker), val[k] an opaque token for line k's parsed
signature (here the index k). Generated lines embed known args/retann tokens,
so decoding token k back to that line's expected "(args) -> retann" rendering
is exact; the decoded shadow output is compared element-for-element with the
real collected sequence (order-faithful, no count-only proxy). Interleavings
outside the clean run (empty lines, non-matching prose, wrong names) are
outside the modeled domain and are covered by axiom_check.py's oracle.

INPUT DOMAIN: Requires is list permission + equal lengths + non-empty; every
non-empty pair of aligned streams is admissible. Generation: exhaustive over
block lengths 1..10 x all 2^L continuation patterns, the F2P-shaped fixtures
(two-line run with the leading line continued -> 2 collected; one-line run
-> 1 collected), plus 100000 fuzz blocks with randomized lengths, flags, and
args/retann token content.

>= 1e5 Requires-satisfying inputs: 2046 exhaustive + fixtures + 100000 fuzz.
Pinned fuzz seed: 774801.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random).
"""
import json
import random
import sys
from types import SimpleNamespace

SEED = 774801
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

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


# --- pure region of model.py, copied verbatim (contract calls stripped) ------

def run_len(cont):
    if len(cont) == 0:
        return 0
    if cont[0] != 0:
        return 1 + run_len(cont.drop(1))
    return 1


def collected(cont, val):
    if len(cont) == 0 or len(val) == 0:
        return PSeq(0).take(0)
    if cont[0] != 0:
        return PSeq(val[0]) + collected(cont.drop(1), val.drop(1))
    return PSeq(val[0])


# --- impl region of model.py, verbatim, contract calls stripped --------------

def gather_signatures(cont, val):
    # impl-start
    result = []  # type: list
    n = len(cont)
    i = 0
    while True:
        c = cont[i]
        v = val[i]
        result = result + [v]
        if c == 0 or i == n - 1:
            # the run ends here — either this line terminates it (not open) or
            # it is the last line of the block (no further line to spill onto).
            break
        i = i + 1
    return result
    # impl-end


# --- oracle: the patched repo behaviour ---------------------------------------

class _RenderBase:
    """Stub for the unchanged upstream renderer of the FIRST signature: the
    mixin's format_signature delegates the first signature's text to super();
    the stub renders the (args, retann) pair the same way subsequent entries
    are rendered, so line order through the real join is observable."""

    def format_signature(self, **kwargs):
        return "(%s) -> %s" % (self.args, self.retann)


_probe_cls_cache = {}


def _probe_class(autodoc_mod):
    if "cls" not in _probe_cls_cache:
        class _Probe(autodoc_mod.DocstringSignatureMixin, _RenderBase):
            def __init__(self, doclines, name):
                self._doclines = list(doclines)
                self.objpath = [name]
                self.args = None
                self.retann = None
                self.directive = SimpleNamespace(
                    state=SimpleNamespace(
                        document=SimpleNamespace(
                            settings=SimpleNamespace(tab_width=8))))
                self.env = SimpleNamespace(
                    config=SimpleNamespace(autodoc_docstring_signature=True))

            def get_doc(self, encoding=None, ignore=None):
                return [list(self._doclines)]

        _probe_cls_cache["cls"] = _Probe
    return _probe_cls_cache["cls"]


def real_collected(autodoc_mod, lines, name):
    """Ordered collected signature sequence the REAL patched gathering
    produces for one documentation block: the first recorded signature's
    rendering followed by the subsequently recorded ones, in order — exactly
    the content the real format_signature joins."""
    probe = _probe_class(autodoc_mod)(lines, name)
    result = probe._find_signature()
    if result is None:
        return []
    first = "(%s) -> %s" % (result[0], result[1])
    return [first] + list(probe._signatures)


def real_joined(autodoc_mod, lines, name):
    """Secondary observable: the real format_signature end-to-end (gathering
    + join), split back into its ordered lines."""
    probe = _probe_class(autodoc_mod)(lines, name)
    return probe.format_signature().split("\n")


# --- input construction + differential check ----------------------------------

NAME = "probe_fn"


def make_line(args, retann, continued):
    """One accepted signature line with known parse tokens. `retann` may be
    None (no return annotation on the line); the recorded rendering is then
    the string 'None', matching '%s' formatting of the parse group."""
    if retann is None:
        line = "%s(%s)" % (NAME, args)
    else:
        line = "%s(%s) -> %s" % (NAME, args, retann)
    if continued:
        line = line + " \\"
    return line


def check_case(autodoc_mod, cont, args_list, retann_list,
               cross_check_pure=False, check_join=False):
    """Build the real block for (cont, args, retann), run the shadow on the
    model streams, decode, and compare with the real collected sequence.
    Returns an error string on disagreement, else None."""
    n = len(cont)
    val = list(range(n))                       # opaque tokens: line indices
    lines = [make_line(args_list[k], retann_list[k], cont[k] != 0)
             for k in range(n)]
    expected = ["(%s) -> %s" % (args_list[k], retann_list[k])
                for k in range(n)]             # token k -> line k's rendering

    shadow_tokens = gather_signatures(list(cont), val)   # shadow (impl region)
    decoded = [expected[t] for t in shadow_tokens]

    real = real_collected(autodoc_mod, lines, NAME)      # oracle (patched repo)

    if decoded != real:
        return ("DISAGREEMENT\n  lines=%r\n  cont=%r\n  shadow tokens=%r\n"
                "  shadow(decoded)=%r\n  real=%r"
                % (lines, cont, shadow_tokens, decoded, real))
    if cross_check_pure:
        # internal consistency: the impl region computes the pure folds
        # (boundary inputs only; the oracle comparison above is the verdict).
        if ToSeq(shadow_tokens) != collected(ToSeq(cont), ToSeq(val)):
            return ("SHADOW SELF-INCONSISTENCY (collected)\n  cont=%r\n"
                    "  impl=%r" % (cont, shadow_tokens))
        if len(shadow_tokens) != run_len(ToSeq(cont)):
            return ("SHADOW SELF-INCONSISTENCY (run_len)\n  cont=%r\n"
                    "  impl len=%d run_len=%d"
                    % (cont, len(shadow_tokens), run_len(ToSeq(cont))))
    if check_join:
        # the real join, end-to-end: same ordered lines as the primary
        # observable (first rendering comes from the stub base renderer,
        # which renders the recorded pair the same way).
        joined = real_joined(autodoc_mod, lines, NAME)
        if joined != real:
            return ("JOIN DRIFT\n  lines=%r\n  collected=%r\n  joined=%r"
                    % (lines, real, joined))
    return None


def fixed_tokens(n):
    return (["arg%d: int" % k for k in range(n)], ["None"] * n)


ARG_POOL = ["", "x", "foo: int, bar: int", "a, b, c", "s: str = 'd'",
            "items: List[int]", "k: int = 0, *rest", "u, v: Dict[str, int]"]
RET_POOL = [None, "None", "int", "str", "List[int]", "Foo.Bar", "'E'"]


def main():
    sys.path.insert(0, "/testbed")
    from sphinx.ext import autodoc as autodoc_mod  # REAL patched module

    checked = 0

    # --- exhaustive boundary: block lengths 1..10, every continuation mask ---
    for n in range(1, 11):
        args_list, retann_list = fixed_tokens(n)
        for mask in range(2 ** n):
            cont = [1 if (mask >> k) & 1 else 0 for k in range(n)]
            err = check_case(autodoc_mod, cont, args_list, retann_list,
                             cross_check_pure=True, check_join=True)
            if err:
                print(err)
                return 1
            checked += 1

    # --- F2P-shaped fixtures ---------------------------------------------------
    # two-line run, leading line continued -> BOTH signatures collected
    err = check_case(autodoc_mod, [1, 0],
                     ["foo: int, bar: int, baz: int",
                      "foo: str, bar: str, baz: str"],
                     ["None", "None"],
                     cross_check_pure=True, check_join=True)
    if err:
        print(err)
        return 1
    checked += 1
    # one-line run -> exactly one signature
    err = check_case(autodoc_mod, [0], ["foo, bar, baz"], [None],
                     cross_check_pure=True, check_join=True)
    if err:
        print(err)
        return 1
    checked += 1

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(1, 25)
        cont = [1 if rng.random() < 0.6 else 0 for _ in range(n)]
        args_list = [rng.choice(ARG_POOL) if rng.random() < 0.7
                     else "p%d" % rng.randint(0, 999) for _ in range(n)]
        retann_list = [rng.choice(RET_POOL) for _ in range(n)]
        err = check_case(autodoc_mod, cont, args_list, retann_list)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real collected signature sequence on "
          "%d inputs (2046 exhaustive + 2 fixtures + %d fuzz, seed %d)."
          % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
