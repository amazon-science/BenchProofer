#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8621 (nagini).

SHADOW: the impl regions of model.py (`split_keystrokes`,
`keystroke_is_atomic`), copied verbatim below with the contract calls
(Requires/Ensures/Invariant/Assert and the type-comment annotations) stripped.
The @Pure helpers the impl calls (is_sep / is_space / empty_seq / single_part /
emit_sep) copy over as plain functions.  PSeq is shimmed as an immutable tuple
subclass supporting the operations the impl uses: PSeq(x) one-element
construction, `+` concatenation, `take`/`drop`, `len`, indexing; ToSeq
materialises a List[int] as a PSeq.  There are no @ContractOnly callees in
this bundle.

ORACLE: the REAL repo symbol the model models per mapping.md — the class
attribute `pattern` of `sphinx.builders.html.transforms.KeyboardTransform`
(the compound-key splitting pattern) applied via `.split(text)`, and the
single-part decision `len(parts) == 1` derived from it.  The gate applies the
diff to /testbed before this script runs and sets PYTHONPATH=/testbed; this
script never applies any diff itself.  The pattern object is imported from
the repo, not re-stated here.

Type bridge (mapping.md section 2):
  str keystroke text          <-> List[int] of code points (text[k] == ord(s[k]))
  pattern.split -> List[str]  <-> PSeq[PSeq[int]] part sequence (k-th substring
                                  <-> k-th inner sequence, joined back via chr)
  len(parts) == 1             <-> keystroke_is_atomic(text) result

Input domain = the model's Requires: every code point printable ASCII
(32..126).  >= 1e5 Requires-satisfying inputs: structured boundary cases
(each separator alone / doubled / adjacent pairs, leading and trailing
separators, blank runs, the compound-key shapes) plus 100000 fuzz strings
drawn from the whole domain with a bias toward the branch characters.
Pinned fuzz seed: 86210.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1.  stdlib only (random; no hypothesis needed).
"""
import json
import random
import sys

SEED = 86210
N_FUZZ = 100_000


# --- PSeq shim: plain immutable sequence with the operations the impl uses ---

class PSeq(tuple):
    """Pure-sequence shim: PSeq(x) is the one-element sequence [x]; `+`
    concatenates; take/drop slice; len/indexing as usual."""

    def __new__(cls, *elems):
        return tuple.__new__(cls, elems)

    @classmethod
    def _of(cls, iterable):
        return tuple.__new__(cls, tuple(iterable))

    def __add__(self, other):
        return PSeq._of(tuple.__add__(self, tuple(other)))

    def take(self, n):
        return PSeq._of(tuple(self)[:n])

    def drop(self, n):
        return PSeq._of(tuple(self)[n:])


def ToSeq(lst):
    """Materialise a List[int] as a PSeq[int] (the spec-level view)."""
    return PSeq._of(lst)


# --- @Pure helpers from model.py, contracts stripped -------------------------

def is_sep(c):
    # a single compound-key separator character: '-' (45), '+' (43) or '^' (94)
    return c == 45 or c == 43 or c == 94


def is_space(c):
    # the only blank-space code point in the modelled printable-ASCII domain
    return c == 32


def in_domain(c):
    # the modelled domain: printable ASCII, code points 32..126
    return 32 <= c and c <= 126


def empty_seq():
    return PSeq(0).take(0)


def single_part(p):
    return PSeq(p)


def emit_sep(c):
    return single_part(empty_seq()) + single_part(PSeq(c))


# --- impl region of split_keystrokes, verbatim, contracts/asserts stripped ---

def split_keystrokes(text):
    result = single_part(empty_seq())
    i = len(text)
    while i > 0:
        i = i - 1
        c = text[i]
        if i == len(text) - 1:
            result = single_part(PSeq(c) + result[0]) + result.drop(1)
        else:
            if (i > 0) and is_sep(c):
                result = emit_sep(c) + result
            elif (i > 0) and is_space(c):
                if i + 2 <= len(text) - 1 and is_space(text[i + 1]):
                    result = single_part(empty_seq()) + single_part(PSeq(c) + result[1]) + result.drop(2)
                else:
                    result = emit_sep(c) + result
            else:
                result = single_part(PSeq(c) + result[0]) + result.drop(1)
    return result


# --- impl region of keystroke_is_atomic, verbatim, contracts stripped --------

def keystroke_is_atomic(text):
    parts = split_keystrokes(text)
    return len(parts) == 1


# --- bridge: str <-> List[int] code points, PSeq parts <-> list of substrings

def shadow_split(text_str):
    cps = [ord(ch) for ch in text_str]
    parts = split_keystrokes(cps)
    return [''.join(chr(c) for c in p) for p in parts]


def shadow_atomic(text_str):
    return keystroke_is_atomic([ord(ch) for ch in text_str])


def check_one(pattern, text):
    """Diff the shadow against the real splitting pattern on one text.
    Returns an error string on disagreement, else None."""
    assert all(in_domain(ord(ch)) for ch in text), \
        "input outside the Requires domain: %r" % (text,)
    real_parts = pattern.split(text)      # real repo callee (patched /testbed)
    real_atomic = (len(real_parts) == 1)  # real single-part decision
    sh_parts = shadow_split(text)
    sh_atomic = shadow_atomic(text)
    if sh_parts != real_parts:
        return ("DISAGREEMENT (split)\n  input=%r\n  shadow=%r\n  real=%r"
                % (text, sh_parts, real_parts))
    if sh_atomic != real_atomic:
        return ("DISAGREEMENT (atomic)\n  input=%r\n  shadow=%r\n  real=%r"
                % (text, sh_atomic, real_atomic))
    return None


def boundary_cases():
    seps = ['-', '+', '^']
    space = [' ']
    cases = [""]
    cases += seps + space                                # each alone
    cases += [c + c for c in seps + space]               # doubled
    cases += [a + b for a in seps + space for b in seps + space]  # adjacent
    cases += [
        "Shift-+", "Alt+^", "Control+X", "Control-x", "space",
        "-x", "x-", "+a", "a+", "^z", "z^",
        " x", "x ", " x ", "a b", "a  b", "a   b", "  a", "a  ",
        "a- b", "a -b", "a - b", "a-  -b", "-  -", "  -  ",
        "a-+b", "a-b-c", "Ctrl-Alt-Del", "X", "ab",
        "----", "+-^", "^-+", "a^^b", "Shift-^-+",
        "M-x  M-s", "x x x", "ab  cd  ef",
    ]
    return cases


def main():
    # REAL repo symbol (the module the model models, per mapping.md); the
    # splitting pattern is taken from the patched checkout, not re-stated here.
    from sphinx.builders.html.transforms import KeyboardTransform
    pattern = KeyboardTransform.pattern

    checked = 0

    boundary = boundary_cases()
    for t in boundary:
        err = check_one(pattern, t)
        if err:
            print(err)
            return 1
        checked += 1

    # Fuzz over the whole Requires domain (printable ASCII 32..126), biased
    # toward the separator/space branch characters and ordinary letters so
    # every branch of the impl loop (including blank-run merging) is hit.
    rng = random.Random(SEED)
    common = [ord(c) for c in
              ['-', '+', '^', ' ',
               'a', 'B', 'Z', '3', '9', 'x', 'S', 'h', 'i', 'f', 't',
               'C', 'o', 'n', 'r', 'l', 'A', 'M', 's', 'X']]
    for _ in range(N_FUZZ):
        n = rng.randint(0, 14)
        cps = []
        for _ in range(n):
            if rng.random() < 0.55:
                cps.append(rng.choice(common))
            else:
                cps.append(rng.randint(32, 126))
        t = "".join(chr(c) for c in cps)
        err = check_one(pattern, t)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real keystroke splitting on %d inputs "
          "(%d boundary + %d fuzz, seed %d); part sequences and the "
          "single-part decision agree everywhere."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
