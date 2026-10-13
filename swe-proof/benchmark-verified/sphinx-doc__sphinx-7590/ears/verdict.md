# P2 adversarial audit — sphinx-doc__sphinx-7590

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_recognize.py`, `probe_2_mangle.py`, `probe_3_std_suffix_precedence.py`, `probe_4_string_char_udl.py`, `probe_5_regression.py`, `probe_6_no_ident_unchanged.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_recognize.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_recognize.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2 + POSITIVE CONTROL: a UDL (base literal + suffix identifier)
parses successfully as one user-defined literal, no parse error from an
unconsumed suffix. Fails at base (parser aborts on the trailing identifier)."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse_full_literal(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed suffix: %r" % p.definition[p.pos:])
    return ast


ok = True
for t in ["5_udl", "6.62607015e-34q_J", "1q_s"]:
    try:
        ast = parse_full_literal(t)
        cls = type(ast).__name__
        print("parsed %r -> %s" % (t, cls))
        if cls != "ASTUserDefinedLiteral":
            print("  FAIL: expected ASTUserDefinedLiteral, got %s" % cls)
            ok = False
    except Exception as e:
        print("parsed %r -> ERROR %s: %s" % (t, type(e).__name__, e))
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2_mangle.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2/2.4: mangled id of a UDL is clL_Zli<id(ident)>E<id(base)>E,
with id(ident) = 'St' for 'std' else <len><text>, and id(base) = the base
literal's own id. Checks the two worked examples plus the St rule."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def litid(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed: %r" % p.definition[p.pos:])
    return ast.get_id(cpp._max_id)


cases = {
    "5_udl": "clL_Zli4_udlEL5EE",
    "6.62607015e-34q_J": "clL_Zli3q_JEL6.62607015e-34EE",
    "1q_s": "clL_Zli3q_sEL1EE",
    "5std": "clL_ZliStEL5EE",   # Req 2.2: suffix 'std' -> St
}
ok = True
for t, exp in cases.items():
    try:
        got = litid(t)
    except Exception as e:
        got = "ERROR %s: %s" % (type(e).__name__, e)
    print("id(%r) = %s (expected %s)" % (t, got, exp))
    if got != exp:
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3_std_suffix_precedence.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.2/3.3: a standard numeric suffix (terminated at a word boundary)
is consumed as part of a plain numeric literal (id L<text>E), NOT a UDL. But
5lll (no word boundary ending a standard suffix) is a UDL with ident 'lll'."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed: %r" % p.definition[p.pos:])
    return type(ast).__name__, ast.get_id(cpp._max_id)


# standard-suffixed numeric literals: plain ASTNumberLiteral with id L<text>E
plain = {
    "5l": "L5lE",
    "5ul": "L5ulE",
    "5L": "L5LE",
    "5ull": "L5ullE",
    "5LL": "L5LLE",
    "5.0f": "L5.0fE",
    "5.0L": "L5.0LE",
}
# 5lll: standard suffix does not end at boundary -> UDL with ident 'lll'
udl = {"5lll": "clL_Zli3lllEL5EE"}

ok = True
for t, exp in plain.items():
    try:
        cls, got = parse(t)
    except Exception as e:
        cls, got = "ERR", "%s: %s" % (type(e).__name__, e)
    print("%r -> %s id=%s (expect ASTNumberLiteral %s)" % (t, cls, got, exp))
    if cls != "ASTNumberLiteral" or got != exp:
        ok = False
for t, exp in udl.items():
    try:
        cls, got = parse(t)
    except Exception as e:
        cls, got = "ERR", "%s: %s" % (type(e).__name__, e)
    print("%r -> %s id=%s (expect ASTUserDefinedLiteral %s)" % (t, cls, got, exp))
    if cls != "ASTUserDefinedLiteral" or got != exp:
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4_string_char_udl.py` → holds on the patched tree (good)

```python
"""Req 5.1/5.2: UDL after string and character literals. "abc"_udl mangles to
clL_Zli4_udlELA3_KcEE; 'a'_udl mangles to clL_Zli4_udlEc97E (base = char id)."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed: %r" % p.definition[p.pos:])
    return type(ast).__name__, ast.get_id(cpp._max_id)


cases = {
    '"abc"_udl': "clL_Zli4_udlELA3_KcEE",
    "'a'_udl": "clL_Zli4_udlEc97E",
}
ok = True
for t, exp in cases.items():
    try:
        cls, got = parse(t)
    except Exception as e:
        cls, got = "ERR", "%s: %s" % (type(e).__name__, e)
    print("%r -> %s id=%s (expect ASTUserDefinedLiteral %s)" % (t, cls, got, exp))
    if cls != "ASTUserDefinedLiteral" or got != exp:
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5_regression.py` → holds on the patched tree (good)

```python
"""Req 4 (regression) + Req 1.4/3.4: plain literals keep their existing ids;
non-suffix-like trailing letters still form a UDL (uludl); a bare number is
left unchanged when no identifier follows."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed: %r" % p.definition[p.pos:])
    return type(ast).__name__, ast.get_id(cpp._max_id)


# (text, expected class, expected id)
cases = [
    ("5", "ASTNumberLiteral", "L5E"),          # Req 4.2 plain int
    ("3.14", "ASTNumberLiteral", "L3.14E"),    # Req 4.2 plain float
    ('"abc"', "ASTStringLiteral", "LA3_KcE"),  # Req 4.4 string
    ("'a'", "ASTCharLiteral", "c97"),          # Req 4.3 char
    (r"L'\n'", "ASTCharLiteral", "w10"),        # Req 4.3 wide char
    ("nullptr", "ASTPointerLiteral", "LDnE"),  # Req 4.5 keyword literal
    ("true", "ASTBooleanLiteral", "L1E"),      # Req 4.5
    ("false", "ASTBooleanLiteral", "L0E"),     # Req 4.5
    # Req 3.4 / 1.1: suffix-like-but-not-standard -> UDL
    ("42uludl", "ASTUserDefinedLiteral", "clL_Zli5uludlEL42EE"),
]
ok = True
for t, ecls, eid in cases:
    try:
        cls, got = parse(t)
    except Exception as e:
        cls, got = "ERR", "%s: %s" % (type(e).__name__, e)
    print("%r -> %s id=%s (expect %s %s)" % (t, cls, got, ecls, eid))
    if cls != ecls or got != eid:
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6_no_ident_unchanged.py` → holds on the patched tree (good)

```python
"""Req 1.4 + 3.3: if the characters after a base literal do NOT form a valid
identifier, the base literal is left unchanged (not wrapped as a UDL). We parse
just the literal and check the parser stops right after the base literal."""
from sphinx.domains import cpp
from sphinx.config import Config


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse_lit_only(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    return type(ast).__name__, ast.get_id(cpp._max_id), p.definition[p.pos:]


# (text, expected class, expected id, expected remaining unconsumed tail)
cases = [
    ("5+3", "ASTNumberLiteral", "L5E", "+3"),    # '+' is not an identifier
    ("5 _udl", "ASTNumberLiteral", "L5E", " _udl"),  # whitespace intervenes
    ("5)", "ASTNumberLiteral", "L5E", ")"),
]
ok = True
for t, ecls, eid, etail in cases:
    try:
        cls, got, tail = parse_lit_only(t)
    except Exception as e:
        cls, got, tail = "ERR", "%s: %s" % (type(e).__name__, e), ""
    print("%r -> %s id=%s tail=%r (expect %s %s tail=%r)"
          % (t, cls, got, tail, ecls, eid, etail))
    if cls != ecls or got != eid or tail != etail:
        ok = False

import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_recognize.py`

```python
"""Req 1.1/1.2 + POSITIVE CONTROL: a UDL (base literal + suffix identifier)
parses successfully as one user-defined literal, no parse error from an
unconsumed suffix. Fails at base (parser aborts on the trailing identifier)."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse_full_literal(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed suffix: %r" % p.definition[p.pos:])
    return ast


ok = True
for t in ["5_udl", "6.62607015e-34q_J", "1q_s"]:
    try:
        ast = parse_full_literal(t)
        cls = type(ast).__name__
        print("parsed %r -> %s" % (t, cls))
        if cls != "ASTUserDefinedLiteral":
            print("  FAIL: expected ASTUserDefinedLiteral, got %s" % cls)
            ok = False
    except Exception as e:
        print("parsed %r -> ERROR %s: %s" % (t, type(e).__name__, e))
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7590: C++ domain user-defined-literal (UDL) support in DefinitionParser._parse_literal / cfamily.py.

All probes exercise the parser directly via cpp.DefinitionParser(text,...)._parse_literal() and compare get_id(cpp._max_id). Harness confirmed working (sphinx 3.1.0 image).

### PROBES (all HOLD on gold-patched tree, exit 0):
- probe_1_recognize.py (Req 1.1/1.2, POSITIVE CONTROL): 5_udl / 6.62607015e-34q_J / 1q_s parse as one ASTUserDefinedLiteral, no 'Expected end of definition'/unconsumed-suffix error. HOLDS patched; FAILS at base (base raises DefinitionError 'unconsumed suffix _udl'). prepatch_reproduced=true.
- probe_2_mangle.py (Req 2.1/2.2/2.4): id = clL_Zli<id(ident)>E<id(base)>E; 5_udl->clL_Zli4_udlEL5EE, 6.62607015e-34q_J->clL_Zli3q_JEL6.62607015e-34EE, 1q_s->clL_Zli3q_sEL1EE, and St rule 5std->clL_ZliStEL5EE. HOLDS patched; FAILS at base.
- probe_3_std_suffix_precedence.py (Req 3.1/3.2/3.3): 5l/5ul/5L/5ull/5LL/5.0f/5.0L stay plain ASTNumberLiteral id L<text>E; 5lll (standard suffix not ending at word boundary) -> UDL ident 'lll' clL_Zli3lllEL5EE. HOLDS patched.
- probe_4_string_char_udl.py (Req 5.1/5.2): "abc"_udl->clL_Zli4_udlELA3_KcEE, 'a'_udl->clL_Zli4_udlEc97E. HOLDS patched; FAILS at base.
- probe_5_regression.py (Req 4.2/4.3/4.4/4.5 + 3.4): plain 5,3.14,"abc",'a',L'\n'(w10),nullptr,true,false keep existing ids; 42uludl->clL_Zli5uludlEL42EE. HOLDS patched.
- probe_6_no_ident_unchanged.py (Req 1.4/3.3): when no valid identifier follows (5+3, '5 _udl' with whitespace, 5)) base literal left unchanged as ASTNumberLiteral L5E with correct unconsumed tail. HOLDS patched.

WEAK CANDIDATE (patches.naive_swallow_ident_into_numeric, weak.diff): the lazy fix a weak reading of Req 1.2 permits — just swallow trailing identifier chars into the numeric literal's text so parsing no longer errors, but produce a plain ASTNumberLiteral (no ASTUserDefinedLiteral, wrong mangling, no string/char handling). Applies cleanly at base. REJECTED by the suite: probe_1 (5_udl -> ASTNumberLiteral not UDL, exit1), probe_2 (id L5_udlE != clL_Zli4_udlEL5EE, exit1), probe_4 ("abc"_udl still raises unconsumed-suffix error, exit1). This demonstrates the suite discriminates a requirement-plausible wrong fix from the gold behavior.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, the positive control discriminates (fails at base, holds patched, re-confirmed by probes 2 and 4 also failing at base), and >=1 wrong-fix candidate is exercised and REJECTED. No requirement mandates a behavior the gold patch lacks.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_recognize.py`, `probe_2_mangle.py`, `probe_3_std_suffix_precedence.py`, `probe_4_string_char_udl.py`, `probe_5_regression.py`, `probe_6_no_ident_unchanged.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_recognize.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_recognize.py` → holds on the patched tree (good)

Attack 2 — `probe_2_mangle.py` → holds on the patched tree (good)

Attack 3 — `probe_3_std_suffix_precedence.py` → holds on the patched tree (good)

Attack 4 — `probe_4_string_char_udl.py` → holds on the patched tree (good)

Attack 5 — `probe_5_regression.py` → holds on the patched tree (good)

Attack 6 — `probe_6_no_ident_unchanged.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_recognize.py`

```python
"""Req 1.1/1.2 + POSITIVE CONTROL: a UDL (base literal + suffix identifier)
parses successfully as one user-defined literal, no parse error from an
unconsumed suffix. Fails at base (parser aborts on the trailing identifier)."""
from sphinx.domains import cpp
from sphinx.config import Config
from sphinx.util.cfamily import DefinitionError


def cfg():
    c = Config({}, {})
    for n in ('cpp_id_attributes', 'cpp_paren_attributes'):
        c.add(n, [], 'env', ())
    return c


def parse_full_literal(text):
    p = cpp.DefinitionParser(text, location=("t", 1), config=cfg())
    p.skip_ws()
    ast = p._parse_literal()
    p.skip_ws()
    if not p.eof:
        raise DefinitionError("unconsumed suffix: %r" % p.definition[p.pos:])
    return ast


ok = True
for t in ["5_udl", "6.62607015e-34q_J", "1q_s"]:
    try:
        ast = parse_full_literal(t)
        cls = type(ast).__name__
        print("parsed %r -> %s" % (t, cls))
        if cls != "ASTUserDefinedLiteral":
            print("  FAIL: expected ASTUserDefinedLiteral, got %s" % cls)
            ok = False
    except Exception as e:
        print("parsed %r -> ERROR %s: %s" % (t, type(e).__name__, e))
        ok = False

import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-7590: C++ domain user-defined-literal (UDL) support in DefinitionParser._parse_literal / cfamily.py.

All probes exercise the parser directly via cpp.DefinitionParser(text,...)._parse_literal() and compare get_id(cpp._max_id). Harness confirmed working (sphinx 3.1.0 image).

### PROBES (all HOLD on gold-patched tree, exit 0):
- probe_1_recognize.py (Req 1.1/1.2, POSITIVE CONTROL): 5_udl / 6.62607015e-34q_J / 1q_s parse as one ASTUserDefinedLiteral, no 'Expected end of definition'/unconsumed-suffix error. HOLDS patched; FAILS at base (base raises DefinitionError 'unconsumed suffix _udl'). prepatch_reproduced=true.
- probe_2_mangle.py (Req 2.1/2.2/2.4): id = clL_Zli<id(ident)>E<id(base)>E; 5_udl->clL_Zli4_udlEL5EE, 6.62607015e-34q_J->clL_Zli3q_JEL6.62607015e-34EE, 1q_s->clL_Zli3q_sEL1EE, and St rule 5std->clL_ZliStEL5EE. HOLDS patched; FAILS at base.
- probe_3_std_suffix_precedence.py (Req 3.1/3.2/3.3): 5l/5ul/5L/5ull/5LL/5.0f/5.0L stay plain ASTNumberLiteral id L<text>E; 5lll (standard suffix not ending at word boundary) -> UDL ident 'lll' clL_Zli3lllEL5EE. HOLDS patched.
- probe_4_string_char_udl.py (Req 5.1/5.2): "abc"_udl->clL_Zli4_udlELA3_KcEE, 'a'_udl->clL_Zli4_udlEc97E. HOLDS patched; FAILS at base.
- probe_5_regression.py (Req 4.2/4.3/4.4/4.5 + 3.4): plain 5,3.14,"abc",'a',L'\n'(w10),nullptr,true,false keep existing ids; 42uludl->clL_Zli5uludlEL42EE. HOLDS patched.
- probe_6_no_ident_unchanged.py (Req 1.4/3.3): when no valid identifier follows (5+3, '5 _udl' with whitespace, 5)) base literal left unchanged as ASTNumberLiteral L5E with correct unconsumed tail. HOLDS patched.

WEAK CANDIDATE (patches.naive_swallow_ident_into_numeric, weak.diff): the lazy fix a weak reading of Req 1.2 permits — just swallow trailing identifier chars into the numeric literal's text so parsing no longer errors, but produce a plain ASTNumberLiteral (no ASTUserDefinedLiteral, wrong mangling, no string/char handling). Applies cleanly at base. REJECTED by the suite: probe_1 (5_udl -> ASTNumberLiteral not UDL, exit1), probe_2 (id L5_udlE != clL_Zli4_udlEL5EE, exit1), probe_4 ("abc"_udl still raises unconsumed-suffix error, exit1). This demonstrates the suite discriminates a requirement-plausible wrong fix from the gold behavior.

Verdict SOUND: >=5 distinct probes all hold on the patched tree, the positive control discriminates (fails at base, holds patched, re-confirmed by probes 2 and 4 also failing at base), and >=1 wrong-fix candidate is exercised and REJECTED. No requirement mandates a behavior the gold patch lacks.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior (UDL recognition + Itanium-style call mangling clL_Zli...E...E across float/int/string/char) rather than a narrow branch or helper. Boundary is correct: it covers the full literal-parsing surface the patch touches (float-before-int ordering, std-suffix vs UDL disambiguation via word boundary, all four base-literal kinds). All numeric/string/char id worked examples in the requirements reproduce exactly on the patched tree. Verified via nl_attack probe on the gold-patched instance image; no requirement mandates behavior the code lacks, forbids behavior it has, or invents behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes UDL support behaviorally and localizes the change to legitimate public modules/functions (sphinx/domains/cpp.py:_parse_literal, sphinx/util/cfamily.py, sphinx/domains/c.py). Checked for semantic leaks the mechanical screen misses:

1. No test path/function/class names or parametrization ids: the hidden test is tests/test_domain_cpp.py::test_expressions with parametrized lists decimalFloats/hexFloats/charPrefixAndIds/chars — none of these names or the file path appear.

2. No fix-invented identifiers leaked: the gold introduces ASTUserDefinedLiteral, udl_identifier_re, float_literal_suffix_re, integers_literal_suffix_re, and description mode 'udl'. The document never names any of these; it describes them purely functionally (e.g. 'a user-defined-literal suffix identifier', 'standard numeric suffix', a 'udl' description-mode is never mentioned).

3. No verbatim test or gold code quoted.

4. Example manglings that coincide with test expectations (e.g. `_udl`->`4_udl`, `<i>uludl`->`clL_Zli5uludlEL<i>EE`, `"abc"_udl`->`clL_Zli4_udlELA3_KcEE`, and the issue's `6.62607015e-34q_J`->`clL_Zli3q_JEL6.62607015e-34EE`) are the DETERMINISTIC output of the mangling algorithm the document itself fully specifies in Requirement 2 (clL_Zli + suffix-id + E + base-id + E; suffix-id = |ident| followed by text, or St for std). Any correct implementation produces these; they are illustrative derivations of the stated rule, not transmissions of the hidden cases. The issue example 6.62607015e-34q_J is already public in the problem_statement.

5. The document does NOT reproduce the test parametrization: the big enumerations (decimalFloats/hexFloats lists, the char-prefix x escape-sequence matrix, char ids like c97/w10/Di127820) are given only as one or two illustrative examples of pre-existing behavior (Req 4), not as an exhaustive case list mirroring the test loops. The `5lll`->UDL vs `5l`->suffix distinction and `<i>uludl` are behavioral consequences of the word-boundary rule stated in Req 3, describable from the algorithm without seeing the tests.

The document translates what the tests verify into described behavior — the legitimate purpose — rather than reconstructing the tests. No leakage.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
