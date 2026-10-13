# mapping.md — sphinx-doc__sphinx-8621

## Symbol binding (base_commit 21698c14461d27933864d73e6fba568a154e83b3)

| Lean symbol | Python source | file:line @ base_commit |
|---|---|---|
| modeled behavior `tokenizeKeystrokes` | `KeyboardTransform.pattern` split of `node[-1].astext()` inside `KeyboardTransform.run` | `sphinx/builders/html/transforms.py:40` (the `pattern` regex) and `:45` (`self.pattern.split(...)`) |

The gold patch changes exactly one line — the class attribute

```python
pattern = re.compile(r'(-|\+|\^|\s+)')                 # pre-patch (buggy)
pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')      # post-patch (fix)
```

`KeyboardTransform.run` (`:42`–`:59`) then does `parts = self.pattern.split(text)`
and, **iff `len(parts) != 1`**, rebuilds the node: even-indexed `parts` become
`<kbd>` child literals and odd-indexed `parts` become `nodes.Text` separators.
The ONLY thing the patch changes is which list `self.pattern.split(text)` returns;
the node-rebuilding loop is unchanged. So the modeled behavior is the **return
value of `pattern.split(text)`** — the token list — and that is what
`problem_spec_tokenizeKeystrokes` pins. The downstream `len(parts)==1 → continue`
short-circuit and the even/odd node assignment are a deterministic, unchanged
function of that token list, hence not part of the modeled behavior.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Python | Lean | bridge |
|---|---|---|
| `text : str` (the keystroke spec `node[-1].astext()`) | `text : List Char` | `list(text)` ↔ `text.toList`; per-code-point (SPEC_GUIDE §2 `str`, per-code-point op) |
| `parts : list[str]` (= `re.split(pattern, text)`) | `result : List (List Char)` | element-wise `''.join(token)` ↔ `String.mk token`; outer list order preserved |
| `re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')` post-patch behavior | `specSplit : List Char → List (List Char)` (the `step`/`finalize` fold) | the deferred single-pass tokenizer; validated == `re.split` by `conformance_check.py` |
| separator alphabet `-`, `+`, `^` | `isSepChar` | `c in '-+^'` ↔ `isSepChar c` |
| `\s` single-char class | `isWsChar` | see **newline note** below |

### Newline note (modeled domain — the one subtlety)

Python `\s` matches `\n`, but the post-patch lookbehind/lookahead `(?<=.)`/`(?=.)`
use the default `.`, which does **NOT** match `\n`. So in the real regex a `\n`
never participates in a lookaround boundary, and a `\n` inside a `\s+` run breaks
the greedy `.`-anchored match in ways that depend on `\n` position. Modeling that
faithfully would add no value: a `:kbd:` keystroke specification
(`node[-1].astext()` of an inline literal) is a single inline text line and
**never contains a line break** — every FAIL_TO_PASS / PASS_TO_PASS input is
newline-free, and in practice the only whitespace it ever contains is the space
character.

`isWsChar` models exactly the set `{' ', '\t', '\r', '\v'=\x0b, '\f'=\x0c}` — i.e.
ASCII `\s` minus `\n` minus the four C0 separator controls FS/GS/RS/US
(`\x1c`–`\x1f`). Two precise points (the G-CONF fuzzer draws from this exact set,
so the validated bijection is internally consistent):

* Python `\s` is **Unicode-aware** (it also matches e.g. `U+00A0` NBSP); the
  modeled domain excludes non-ASCII whitespace.
* ASCII `\s` additionally includes `\x1c`–`\x1f`; the modeled domain excludes
  those C0 controls.

So the bijection `specSplit ↔ re.split` is asserted over the **modeled domain**:
strings whose characters are non-`\n`, and whose whitespace characters are among
`{space, \t, \r, \v, \f}`. This strictly contains every keystroke spec the role
can produce. `conformance_check.py` fuzzes exactly this domain and `mapping.md`
records it as the modeled domain. (This is a domain restriction on the conformance
oracle, NOT a precondition weakening of the Lean theorem: `implementation_…` is
definitionally `specSplit`, so `correct_…` holds for all inputs; the restriction
governs only where `specSplit` is claimed to mirror Python `re.split`.)

## Callee provenance / flag deps

No unchanged callee is consumed as an axiom. `re.Pattern.split` is the standard
library splitter whose *changed* configuration (the regex pattern) is modeled
DEEPLY by the `step`/`finalize` fold (SPEC_GUIDE §3 — the changed op is modeled,
never axiomatized), and validated against the real `re.split` by G-CONF. There is
no flag-dependent callee.

## G-CONF fuzz seed

Pinned seed: **8621** (also in `conformance_check.py`).
