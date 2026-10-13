#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7440 (nagini).

SHADOW: the impl region of model.py (`register_term_name`), copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The impl body uses only plain Python lists at runtime, so no sequence shim is
needed on the shadow path. The @Pure helpers `fold_cp`/`casefold` (stated over
PSeq) copy over on top of a small immutable-tuple PSeq shim; the modeled
function's impl never calls them, so they are exercised only as an internal
cross-check on the boundary inputs (the shadow's output must differ from the
fold exactly on inputs carrying an upper-case ASCII letter, mirroring the
spec's contrast property). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
cross-reference key that `sphinx.domains.std.make_glossary_term` registers for
a glossary term via `StandardDomain.note_object('term', ...)`, observed as the
`name` component of the domain's `objects` store and re-read through
`get_objects()` (which re-emits the stored name unchanged; this is the same
observable the F2P test asserts on). The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable. For each generated term text a fresh StandardDomain is built over
a minimal environment stub, `make_glossary_term` is called with a single text
node carrying the term text, and the single registered 'term' key is read
back.

TYPE BRIDGE (mapping.md section 2): the model carries the term text as
`List[int]` of Unicode code points, `s[k] <-> ord(text[k])`. Each input string
is encoded to its code-point list, the shadow runs on the list, and the shadow
output is decoded back to a string for comparison with the real registered
key.

INPUT DOMAIN: the Requires is just list permission — any finite code-point
list. The oracle harness renders the term text through a docutils text node,
whose text rendering is the identity except for the NUL escape marker and
ill-formed lone surrogates; generation therefore avoids code point 0 and the
surrogate block (and the harness asserts the rendered text equals the input,
so any drift is a loud harness error, never a silent domain shrink). Everything
else is fair game: mixed-case ASCII, punctuation, whitespace, and non-ASCII
letters (including cased non-ASCII, where a case-folding behaviour would also
diverge from the identity).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz strings.
Pinned fuzz seed: 74400.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random).
"""
import json
import random
import sys

SEED = 74400
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


# --- pure region of model.py, copied verbatim (decorators dropped) -----------

def fold_cp(c):
    if 65 <= c and c <= 90:
        return c + 32
    return c


def casefold(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(fold_cp(s[0])) + casefold(s.drop(1))


# --- impl region of model.py, verbatim, contract calls stripped --------------

def register_term_name(termtext):
    # impl-start
    # Build the registration key character by character, copying each code point
    # of the term text unchanged. The loop invariant tracks that the prefix
    # emitted equals the prefix of the term text verbatim.
    result = []  # type: list
    i = 0
    while i < len(termtext):
        c = termtext[i]
        result = result + [c]
        i = i + 1
    return result
    # impl-end


# --- oracle: the patched repo behaviour ---------------------------------------

def make_env_and_domain(std_mod):
    """Minimal environment stub sufficient for StandardDomain + the modeled
    registration path: fresh per input so exactly one term key is observed."""
    from types import SimpleNamespace
    app = SimpleNamespace(registry=SimpleNamespace(enumerable_nodes={}))
    env = SimpleNamespace(domaindata={}, docname="index", all_docs={},
                          titles={}, temp_data={}, app=app)
    dom = std_mod.StandardDomain(env)
    env.get_domain = lambda name: dom
    return env, dom


def real_registered_key(std_mod, nodes_mod, termtext, serial):
    """The key the patched make_glossary_term registers for a term whose
    rendered text is `termtext`, read from the domain's objects store and
    cross-read through get_objects()."""
    env, dom = make_env_and_domain(std_mod)
    term = std_mod.make_glossary_term(
        env, [nodes_mod.Text(termtext)], None, "index.rst", 1,
        node_id="term-%d" % serial, document=None)
    # harness sanity: the text-node rendering must be the identity on the
    # generated domain, else the oracle input would silently drift
    assert term.astext() == termtext, (
        "harness drift: rendered term text %r != input %r"
        % (term.astext(), termtext))
    keys = [name for (objtype, name) in dom.objects.keys()
            if objtype == "term"]
    assert len(keys) == 1, "harness drift: expected exactly one term key, got %r" % keys
    got = [name for (name, _disp, typ, _doc, _lab, _prio) in dom.get_objects()
           if typ == "term"]
    assert got == keys, "harness drift: get_objects re-read %r != stored %r" % (got, keys)
    return keys[0]


# --- bridge + differential check ----------------------------------------------

def check_termtext(std_mod, nodes_mod, s, serial, cross_check_pure=False):
    """Encode `s` to code points, run the shadow, decode, and compare with the
    real registered key. Returns an error string on disagreement, else None."""
    cps = [ord(ch) for ch in s]              # Requires: a plain list of ints

    shadow_cps = register_term_name(cps)     # shadow (impl region)
    decoded = "".join(chr(c) for c in shadow_cps)

    real = real_registered_key(std_mod, nodes_mod, s, serial)  # oracle

    if decoded != real:
        return ("DISAGREEMENT\n  termtext=%r\n  codepoints=%r\n"
                "  shadow(decoded)=%r\n  real=%r"
                % (s, cps, decoded, real))
    if cross_check_pure:
        # internal consistency with the spec's contrast property: the shadow's
        # output differs from the pure-region fold exactly when the input
        # carries an upper-case ASCII letter (boundary inputs only; the oracle
        # comparison above is the verdict).
        has_upper = any(65 <= c <= 90 for c in cps)
        differs = ToSeq(shadow_cps) != casefold(ToSeq(cps))
        if differs != has_upper:
            return ("SHADOW SELF-INCONSISTENCY\n  termtext=%r\n"
                    "  has_upper=%s differs_from_fold=%s"
                    % (s, has_upper, differs))
    return None


def boundary_inputs():
    return [
        "",
        "term1", "term2", "TERM2",                 # the tested shapes
        "mysql", "MySQL",                          # case-differing pair
        "A", "Z", "a", "z", "0", " ", ":", "-", "_",
        "@", "[", "`", "{",                        # code points bracketing A..Z/a..z
        "ABCXYZ", "abcxyz", "AbCdEf",
        "HTTP", "Http", "http",
        "term with spaces", "Term With Spaces",
        "ls -l", "--option", "Option-Name",
        "Étude", "étude",                # cased non-ASCII letters
        "Über", "über",
        "Αβγ",                      # Greek upper+lower
        "中文",                            # uncased non-ASCII
        "tab\tand\nnewline",
        "A" * 64, "aA" * 32,
    ]


def rand_termtext(rng, max_len=24):
    n = rng.randint(0, max_len)
    out = []
    for _ in range(n):
        p = rng.random()
        if p < 0.45:
            out.append(chr(rng.randint(65, 90)))      # upper ASCII
        elif p < 0.75:
            out.append(chr(rng.randint(97, 122)))     # lower ASCII
        elif p < 0.90:
            out.append(chr(rng.randint(32, 126)))     # printable ASCII
        elif p < 0.97:
            out.append(chr(rng.randint(0xC0, 0x24F))) # Latin-1 sup / Latin ext (cased)
        else:
            # wider BMP, avoiding NUL and the surrogate block (harness domain)
            c = rng.randint(1, 0xFFFF)
            while 0xD800 <= c <= 0xDFFF:
                c = rng.randint(1, 0xFFFF)
            out.append(chr(c))
    return "".join(out)


def main():
    sys.path.insert(0, "/testbed")
    from sphinx.domains import std as std_mod   # REAL patched module
    from docutils import nodes as nodes_mod

    checked = 0
    serial = 0
    boundary = boundary_inputs()
    for s in boundary:
        err = check_termtext(std_mod, nodes_mod, s, serial, cross_check_pure=True)
        serial += 1
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_termtext(std_mod, nodes_mod, rand_termtext(rng), serial)
        serial += 1
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real registered term key on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
