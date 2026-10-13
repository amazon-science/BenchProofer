# mapping.md — sphinx-doc__sphinx-11445

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 71db08c05197545944949d5aa76cd340e7143627`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep model.

Repo file under change: `sphinx/util/rst.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `countLeadingMetadataLines (content : List (List Char))` | the leading-line counting loop at the top of `prepend_prolog(content, prolog)` — `sphinx/util/rst.py:78` (loop body lines 82–86), which computes the local `pos` | the modeled changed function: how many leading lines are counted as field/meta lines before the prolog is inserted |
| `isMetadataLine` *(deep model — A-reference)* | the per-line classifier `FIELD_NAME_RE.match(line)` where `FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])` (post-patch); pre-patch it was `docinfo_re = re.compile(':\\w+:.*?')` | pure spec: whether one line is recognised as a field/meta marker. Deeply models the **post-patch** classifier (the strict docutils field-marker grammar), validated `isMetadataLine == FIELD_NAME_RE.match` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `metaScan` | the forward scan implementing the body of the `field_marker` regex `:(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)` | helper of the deep model |
| `leadingMetadata (content : List (List Char))` | the value `pos` would hold after the `for line in content … else: break` loop | pure spec: length of the leading run of metadata lines; front-recursive (the fold pattern, plan §5.4) |

The pre-patch repo symbol the change replaces (refinement audit only, not in the
consumer spec view): `docinfo_re = re.compile(':\\w+:.*?')` (`rst.py:28`),
matched at `rst.py:83` in the loop. Its loose grammar wrongly accepts a leading
cross-reference role marker such as `:mod:` `` `foo` `` and therefore over-counts
the leading run; that is the bug under repair.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `StringList content` (a list of source lines) | `List (List Char)` | `content` (list of `str`) ↔ a `List` of `List Char`; `len(content)` ↔ `content.length`; the *i*-th line ↔ `content[i]!` |
| a single source line `line : str` | `List Char` | `line` ↔ `line.toList`; `len(line)` ↔ `l.length`; per-code-point indexing is total/sound on `List Char` |
| a single character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact. The classifier only distinguishes the four literals `':'`, `'\\'`, `` '`' ``, `' '` from "any other character", so the bijection is exact for the grammar |
| local `pos : int` (leading count) | `Nat` | `pos` ↔ the returned `Nat`; non-negative by construction |

`prepend_prolog` mutates `content` in place and returns `None`; only the leading
**count** `pos` (where the prolog is inserted) is the changed, observable
quantity. The insertion arithmetic (`content.insert(...)`, the `<generated>` /
`<rst_prolog>` markers, the post-patch defensive `lineno = 0` init) is unchanged
by the classifier swap and carries no field-marker behaviour — it is an I leg
(refinement.md §C) and is not part of the modeled function.

## 3. Deep-model provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `isMetadataLine` deep model ↔ `FIELD_NAME_RE.match` (A-reference)
**Callee:** `re.compile(Body.patterns['field_marker']).match(line)`, where
`Body` is `docutils.parsers.rst.states.Body`. The changed classifier is modeled
**deeply** by `isMetadataLine` (with `metaScan`) in the `pure` region; there is
**no consumed axiom**. The real pattern (docutils 0.17.1, the interpreter in this
instance image) is:

```python
Body.patterns['field_marker'] == r':(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)'
```

`re.match` anchors at the start of the line. The pattern reads:
* `:` — a leading colon;
* `(?![: ])` — not immediately followed by `:` or space (so the field name is
  non-empty and does not start with a space). Modeled by `isMetadataLine`'s
  guard `a = ':' && b ≠ ':' && b ≠ ' '`;
* `([^:\\] | \\. | :(?!([ `]|$)))*` — the field-name body: any non-`:`,
  non-`\` char; or a backslash escape `\\.` (the next char is consumed); or a
  `:` that is **not** followed by space / backtick / end (an internal colon).
  Modeled by `metaScan`'s recursion: ordinary char advances (`metaScan cs c`),
  `\\` consumes the next char (`metaScan ds (cs.headD ' ')`), an internal `:`
  followed by neither space nor backtick continues, a `:` followed by `` ` ``
  fails the marker;
* `(?<! ):( +|$)` — a closing `:` preceded by a non-space, followed by one or
  more spaces or end-of-line. Modeled by `metaScan`'s `c = ':'` case:
  `decide (prev ≠ ' ')` when the next char is a space or the colon is last.

The `prev` argument threads the immediately-preceding character so the negative
lookbehind `(?<! )` is faithfully enforced; the `` ` `` guard makes a `:`
immediately followed by a backtick non-terminating, so an inline cross-reference
role marker (`:role:` `` ` `` …) is **rejected** — exactly the discriminator the
issue turns on.

**Flag/config dependency:** none. `field_marker` is a fixed module-level pattern;
`re.match` uses no flags here. `Body.patterns` is built once at class-definition
time and is identical across docutils 0.17–0.20 (the versions Sphinx 7.1 admits).

**Soundness check (G-AX):** `axiom_check.py` compiles the **real**
`Body.patterns['field_marker']` and asserts `isMetadataLine(line) ==
(FIELD_NAME_RE.match(line) is not None)` on a boundary battery (role markers,
field names, escapes, internal colons, trailing-space variants, the literal
F2P-test lines) plus ≥100 000 randomized fuzz lines drawn from the
grammar-relevant alphabet (`: \ ` ``` ` ``` space, word chars, dot, digits).
Imports only stdlib `re` + `docutils` (the same module the gold patch calls).
Exit 0 iff every observation agrees.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11445`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`isMetadataLine`/`metaScan` (the A-reference deep model) and the counting `while`
loop to Python, and compares the count against the **real patched**
`prepend_prolog` (imported from the repo at base_commit with `patch.diff`
applied): it builds a `StringList`, runs `prepend_prolog`, and recovers the
insertion offset `pos` from `xitems()`. Zero disagreements over ≥10⁵ inputs ⇒
exit 0.
