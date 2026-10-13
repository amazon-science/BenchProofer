# refinement.md — sphinx-doc__sphinx-7748

Every op in `implementation_collectSignatures` mapped to its `patch.diff`
counterpart. Tags: **R** (type-only refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

This bundle has **no A-consumed** axiom. It declares ONE `opaque` callee,
`matchSig` (the unchanged extended-signature regex matcher), used **identically**
in the spec helper `scanDoc` and in `implementation_collectSignatures`, so it is
an **A-reference** that cancels (the proof consumes no property of it). Every
other row is R or I. `meta.json conf_skip = false` (the impl region is NOT
all-A-tagged — the loop control flow and signature collection are R/I).

## What the patch does (the two coordinated edits modeled here)

`_find_signature` (gold hunk 1) changes the inner loop over docstrings from
inspecting only `doclines[0]` and keeping a single `result` to a nested
`for j, line in enumerate(doclines)` that:
- `break`s on the first empty line,
- strips a trailing-backslash continuation marker (`multiline`),
- matches `py_ext_sig_re` and checks `base in valid_names`,
- records the first hit as `result` and each subsequent hit into
  `self._signatures`,
- `continue`s after a continuation line and `break`s after a non-continuation
  line,
- and stops the outer loop once `result` is set.

`format_signature` (gold hunk 3) then returns `"\n".join([sig] + self._signatures)`
when `self._signatures` is non-empty, i.e. the primary signature followed by the
collected continuations — exactly the ordered list this bundle returns.

The Lean impl fuses these two sites into the single observable: the ordered list
of collected signatures (`result :: signatures`).

## implementation_collectSignatures  ↔  `_find_signature` + `format_signature`

patch.diff hunk 1 (core), reproduced abridged:
```python
        result = None
        for i, doclines in enumerate(docstrings):
            for j, line in enumerate(doclines):
                if not line:
                    break
                if line.endswith('\\'):
                    multiline = True
                    line = line.rstrip('\\').rstrip()
                else:
                    multiline = False
                match = py_ext_sig_re.match(line)
                if not match:
                    continue
                exmod, path, base, args, retann = match.groups()
                if base not in valid_names:
                    continue
                ...
                if result is None:
                    result = args, retann
                else:
                    self._signatures.append("(%s) -> %s" % (args, retann))
                if multiline:
                    continue
                else:
                    break
            if result:
                break
```

| Lean op | patch.diff op | tag | note |
|---|---|---|---|
| `docstrings : List (List String)` parameter | `docstrings = self.get_doc()` | R | `List[List[str]]` ↔ `List (List String)`, per-block/per-line identity |
| `validNames : List String` parameter | `valid_names` list | R | `List[str]` ↔ `List String`; the patch hoists its computation out of the loop but does not change its value — taken as a given input |
| `let mut result : Option Sig := none` | `result = None` | I | the primary-signature accumulator |
| `let mut signatures : List Sig := []` | `self._signatures = []` | I | the continuation-signature accumulator |
| `for doclines in docstrings do` | `for i, doclines in enumerate(docstrings):` | I | outer block scan (index `i` unused — only used post-patch to re-prep the description text, not the signature output) |
| `for line0 in doclines do` | `for j, line in enumerate(doclines):` | I | inner line scan (the NEW inner loop the fix introduces; pre-patch only line 0 was read) |
| `if line0.isEmpty then break` | `if not line: break` | R/I | empty-line terminator; Python falsy-empty `str` ↔ `String.isEmpty` |
| `let multiline := line0.endsWith "\\"` | `multiline = line.endswith('\\')` | R | trailing-backslash test; `str.endswith('\\')` ↔ `String.endsWith _ "\\"` |
| `let line := if multiline then stripContinuation line0 else line0` | `line = line.rstrip('\\').rstrip()` (when multiline) | R | strip trailing `\` then trailing whitespace; modeled deeply by `stripContinuation` (`List Char`), whose whitespace class `isPyWhitespace` enumerates EXACTLY the `str.isspace()` codepoints (0x9–0xD, 0x1C–0x1F, 0x20, 0x85, 0xA0, 0x1680, 0x2000–0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000) — Lean's built-in `Char.isWhitespace` is only {' ','\t','\r','\n'} and was an earlier unfaithful choice (G-PANEL-2 counterexample: `"E(a)\x0c\\"`) |
| `match matchSig line with \| none => continue` | `match = py_ext_sig_re.match(line); if not match: continue` | A-reference | the UNCHANGED regex matcher; `.match → None` ↔ `matchSig → none`; identical in spec/impl, cancels |
| `\| some m => if validNames.contains m.base` | `base not in valid_names: continue` | R | `base in valid_names` ↔ `validNames.contains m.base` |
| `if result.isNone then result := some ⟨m.args, m.retann⟩` | `if result is None: result = args, retann` | I | first signature → primary |
| `else signatures := signatures ++ [⟨m.args, m.retann⟩]` | `else: self._signatures.append("(%s) -> %s" % (args, retann))` | R | subsequent signatures appended in order; the `"(%s) -> %s"` rendering is value-level formatting of the same (args,retann) pair |
| `if multiline then continue else break` | `if multiline: continue else: break` | I | continuation keeps scanning; a terminal signature ends the block scan |
| `if result.isSome then break` (outer) | `if result: break` | I | first block that yields a signature wins |
| `match result with \| none => return [] \| some r => return r :: signatures` | `format_signature`: `"\n".join([sig] + self._signatures)` (or `sig` alone) | R | the ordered collected-signature list; the join is value-level rendering |

## Frame discipline (SPEC_GUIDE §0.5)

`problem_spec_collectSignatures docstrings validNames result := result =
collectSpec validNames docstrings` pins the ENTIRE result by full structural
equality to an input-grounded expression: its length, the order of its entries,
and each entry's `args`/`retann` are all determined by the input `docstrings`
and `validNames`. No output component is left unconstrained; there is no
ungrounded oracle (directive 8) — `collectSpec`/`scanDoc` are concrete recursive
functions over the actual input lists, whose only opaque leaf is `matchSig`,
which the impl invokes IDENTICALLY (so the spec is dischargeable only by
performing the same scan). The discriminating clauses a wrong impl violates:
- the continuation case `s :: scanDoc …` (a backslash-continued run must yield
  ALL its signatures in order, not just the first); and
- the strip step (`stripContinuation`) — a primary signature taken from a
  continued line must have its trailing `\` + whitespace removed.

## G-DIFF: one failing prepatch per independently-fixed behavior

`Solution_prepatch.lean` carries the PRE-FIX skeleton: only `doclines[0]` of each
block is inspected (no inner line loop), no continuation handling, and at most a
single signature is returned (`[r]`). On the F2P input — a block whose leading
run is a backslash-continued pair of signature lines (class `E`'s two-line
`__init__` docstring) — the spec requires the full ordered list of TWO
signatures (the first with its continuation marker stripped), whereas the
prepatch returns one signature carrying the raw unstripped line. The equality in
`problem_spec` is therefore unprovable; the carried proof cannot close
(G-DIFF/G-PANEL). The PASS_TO_PASS cases (single-line `D(foo, bar, baz)`, etc.)
flow identically through both impls: a single non-continuation signature on line
0 gives `[⟨"foo, bar, baz", ""⟩]` either way.

## G-CONF

`conformance_check.py` transliterates the R/I impl into Python (`shadow`) and
differential-tests it against an in-process replica of the patched
`_find_signature` + `format_signature` collection behavior, with `matchSig`
(`py_ext_sig_re.match`) stubbed IDENTICALLY on both legs (the A-reference
cancels), over hand-picked edge cases (single signature, two-signature
continuation run, run terminated by a non-continuation line, name-mismatch
skips, empty-line terminator, first-block-wins, no-match→empty) plus ≥1e5 fuzzed
block lists.
