# P2 adversarial audit — pytest-dev__pytest-7324

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression
ok = True
for word in ("True", "False", "None"):
    expr = Expression.compile(word)
    # matcher that says this identifier matches
    res_true = expr.evaluate(lambda k, w=word: k == w)
    res_false = expr.evaluate(lambda k: False)
    print(word, "match->", res_true, "nomatch->", res_false)
    if res_true is not True or res_false is not False:
        ok = False
if not ok:
    raise SystemExit(1)
print("R1: True/False/None resolve as ordinary identifiers")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression
seen = []
for word in ("True", "False", "None", "hello", "a.b-c[0]", "café"):
    keys = []
    def m(k, keys=keys):
        keys.append(k)
        return True
    Expression.compile(word).evaluate(m)
    print(repr(word), "-> matcher saw", [repr(x) for x in keys])
    if keys != [word]:
        raise SystemExit(1)
print("R2: matcher received exact identifier text")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression
for s in ("", "   ", "\t", "  \t "):
    r1 = Expression.compile(s).evaluate(lambda k: True)
    r2 = Expression.compile(s).evaluate(lambda k: False)
    print(repr(s), r1, r2)
    if r1 is not False or r2 is not False:
        raise SystemExit(1)
print("R3.1: empty/whitespace -> False")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression
def mk(trueset):
    return lambda k: k in trueset
cases = [
    ("a and b", {"a","b"}, True),
    ("a and b", {"a"}, False),
    ("a or b", {"b"}, True),
    ("not a", set(), True),
    ("not a", {"a"}, False),
    # precedence: not binds tighter than and; and tighter than or
    ("a or b and c", {"a"}, True),        # a or (b and c)
    ("a or b and c", {"b"}, False),       # (b and c) false, a false
    ("not a and b", {"b"}, True),         # (not a) and b
    ("not a and b", {"a","b"}, False),
    # parens override
    ("(a or b) and c", {"a","c"}, True),
    ("(a or b) and c", {"a"}, False),
]
for expr, ts, want in cases:
    got = Expression.compile(expr).evaluate(mk(ts))
    print(expr, ts, "->", got, "want", want)
    if got is not want:  # genuine bool identity
        raise SystemExit(1)
print("R3: boolean semantics/precedence/parens/genuine-bool")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression
m = lambda k: k in {"a","b","c"}
a = Expression.compile("a and b or c").evaluate(m)
b = Expression.compile("  a   and\tb   or  c  ").evaluate(m)
c = Expression.compile(" ( a and b ) or c ").evaluate(m)
print(a, b, c)
if not (a is True and b is True and c is True):
    raise SystemExit(1)
print("R3.4: whitespace ignored")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression, ParseError
idents = ["1234", "12.34", "café", "if", "else", "while",
          "notandor", "not_and_or", "1234and", "a:b+c-d.e[0]"]
for ident in idents:
    try:
        e = Expression.compile(ident)
    except ParseError as pe:
        print("REJECTED", repr(ident), pe)
        raise SystemExit(1)
    got = e.evaluate(lambda k, w=ident: k == w)
    print(repr(ident), "-> match", got)
    if got is not True:
        raise SystemExit(1)
print("R4: full identifier alphabet accepted & resolved")
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression, ParseError
illegal = ["/", "\\", "^", "*", "=", "&", "%", "$", "#", "@", "!", "~",
           "{", "}", '"', "'", "|", ";", "←"]
for ch in illegal:
    try:
        Expression.compile(ch)
    except ParseError as pe:
        print("illegal", repr(ch), "col", pe.column, "msg", pe.message)
        if pe.column != 1:
            raise SystemExit(1)
        continue
    print("NOT rejected", repr(ch)); raise SystemExit(1)

# malformed grammar
malformed = ["and", "a and", "a b", "(", ")", "()", "not", "a or or b"]
for s in malformed:
    try:
        Expression.compile(s)
    except ParseError as pe:
        print("malformed", repr(s), "col", pe.column, "msg", pe.message)
        continue
    print("NOT rejected malformed", repr(s)); raise SystemExit(1)
print("R5: illegal/malformed rejected with ParseError")
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
from _pytest.mark.expression import Expression, ParseError
# trailing token after complete expr -> "expected end of input; got ..."
try:
    Expression.compile("a b")
    raise SystemExit(1)
except ParseError as pe:
    print("trailing:", pe.column, repr(pe.message))
    if "expected end of input" not in pe.message:
        raise SystemExit(1)
# dangling operator -> "expected ...; got ..."
try:
    Expression.compile("a and")
    raise SystemExit(1)
except ParseError as pe:
    print("dangling:", pe.column, repr(pe.message))
    if "expected" not in pe.message or "got" not in pe.message:
        raise SystemExit(1)
print("R5.3: error wording preserved")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
from _pytest.mark.expression import Expression
ok = True
for word in ("True", "False", "None"):
    expr = Expression.compile(word)
    # matcher that says this identifier matches
    res_true = expr.evaluate(lambda k, w=word: k == w)
    res_false = expr.evaluate(lambda k: False)
    print(word, "match->", res_true, "nomatch->", res_false)
    if res_true is not True or res_false is not False:
        ok = False
if not ok:
    raise SystemExit(1)
print("R1: True/False/None resolve as ordinary identifiers")
```

Prepatch bug re-encoded as an attack: `True`.

8 distinct probes covering R1 (True/False/None resolve as ordinary identifiers, positive control), R2 (matcher receives EXACT identifier text incl. True/unicode/punctuation), R3.1 (empty/whitespace->False), R3.2/3.3/3.6 (boolean semantics, precedence not>and>or, parens override, genuine bool), R3.4 (whitespace ignored), R4 (identifier alphabet: digits, unicode, python keywords if/else/while, embedded-operator substrings notandor/1234and, punctuation set), R5.1/5.2/5.3 (18 illegal punctuation chars + ← rejected with ParseError col=1; malformed grammar rejected; error wording 'expected end of input; got ...' and 'expected ...; got ...' preserved). All 8 HOLD on the gold-patched tree.

Positive control (probe_1) FAILS at base with 'ValueError: Name node can't be used with True constant' and HOLDS patched -> discriminates. Weak candidate (weak.diff: adds IDENT_PREFIX in not_expr but does NOT strip it in MatcherAdapter.__getitem__ -- a partial/lazy fix that satisfies R1's no-crash guarantee only) is REJECTED by probes 1,2,4,6: the matcher then sees mangled key '$True', every identifier matches nothing, violating R2.1/R2.4 and R3/R4 resolution. Suite discriminates wrong implementations; requirements are faithful and not too weak.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
from _pytest.mark.expression import Expression
ok = True
for word in ("True", "False", "None"):
    expr = Expression.compile(word)
    # matcher that says this identifier matches
    res_true = expr.evaluate(lambda k, w=word: k == w)
    res_false = expr.evaluate(lambda k: False)
    print(word, "match->", res_true, "nomatch->", res_false)
    if res_true is not True or res_false is not False:
        ok = False
if not ok:
    raise SystemExit(1)
print("R1: True/False/None resolve as ordinary identifiers")
```

Prepatch bug re-encoded as an attack: `True`.

8 distinct probes covering R1 (True/False/None resolve as ordinary identifiers, positive control), R2 (matcher receives EXACT identifier text incl. True/unicode/punctuation), R3.1 (empty/whitespace->False), R3.2/3.3/3.6 (boolean semantics, precedence not>and>or, parens override, genuine bool), R3.4 (whitespace ignored), R4 (identifier alphabet: digits, unicode, python keywords if/else/while, embedded-operator substrings notandor/1234and, punctuation set), R5.1/5.2/5.3 (18 illegal punctuation chars + ← rejected with ParseError col=1; malformed grammar rejected; error wording 'expected end of input; got ...' and 'expected ...; got ...' preserved). All 8 HOLD on the gold-patched tree.

Positive control (probe_1) FAILS at base with 'ValueError: Name node can't be used with True constant' and HOLDS patched -> discriminates. Weak candidate (weak.diff: adds IDENT_PREFIX in not_expr but does NOT strip it in MatcherAdapter.__getitem__ -- a partial/lazy fix that satisfies R1's no-crash guarantee only) is REJECTED by probes 1,2,4,6: the matcher then sees mangled key '$True', every identifier matches nothing, violating R2.1/R2.4 and R3/R4 resolution. Suite discriminates wrong implementations; requirements are faithful and not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verdict only. Confirmed base-vs-patched discriminator is the crash/prefix behavior (issue: debug-build assertion abort on compile('False')). Note: meta.json records G-PANEL-3=fail for test-leakage (R5.1 reproduces test_invalid_idents' punctuation list, R4.3-4 reproduce test_valid_idents ids) — that is a leakage concern outside this faithfulness gate and does not affect the FAITHFUL verdict here.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The FAIL_TO_PASS behavior (identifiers spelled True/False/None must not crash) is fully public via problem_statement, which quotes the CPython assertion naming None/True/False and the Expression.compile('False') reproducer. The gold patch's invented identifier IDENT_PREFIX = '$' is NOT leaked: Req 2 crit 4 describes the encode/decode mechanism generically ('an internal AST encoding ... to avoid colliding with Python reserved words ... reverse that encoding') without naming '$' or IDENT_PREFIX. Naming expression.py, not_expr, MatcherAdapter.__getitem__, and the empty-expression branch is legitimate localization. Req 4's enumeration (digits/decimal, unicode word chars, keywords if/else/while, embedded operator substrings) overlaps the PASS_TO_PASS test_valid_idents parametrization, but these are all derivable from the identifier-alphabet regex in the source (\w,:,+,-,.,[,]) — describing the accepted grammar is behavioral spec, not test transmission. No test file paths, function/class names, parametrization ids, or verbatim test/gold lines appear. The only genuinely hidden test-patch change (adding 'None' to test_valid_idents params) is already covered by the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
