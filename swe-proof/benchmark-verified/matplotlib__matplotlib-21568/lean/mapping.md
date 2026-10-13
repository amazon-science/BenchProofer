# mapping.md — matplotlib__matplotlib-21568

## Symbol binding (file:line @ base_commit f0632c0fc7)
Modeled function: the math-mode label helper `_wrap_in_tex(text)`,
`lib/matplotlib/dates.py:594-601`. It is called by the date tick formatters
(`DateFormatter`, `ConciseDateFormatter`) when `usetex` is in effect, to turn a
strftime-rendered tick label into a `$\mathdefault{…}$` math fragment. The gold
patch changes the symbol-escaping step: in addition to bracing hyphens it now
braces colons (`:`↦`{:}`) and rewrites spaces (` `↦`\;`).

Lean modeled function name: `texLabel` / `implementation_texLabel` (neutral — it
names the *behavior* "render a label as a math-mode fragment", not the patched
symbol; see G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `texLabel` / `implementation_texLabel` | `_wrap_in_tex`, `dates.py:594-601` |
| `text : List Char` | parameter `text : str` |
| `bracketLetterRuns` | `re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text)`, `dates.py:596` |
| `escapeMathSym` / `escapeMathSyms` | `.replace('-','{-}').replace(':','{:}').replace(' ', r'\;')`, `dates.py:599-601` (post) |
| outer wrap | `'$\\mathdefault{' + ret_text + '}$'`, `dates.py:601` (post) |
| `dropToken '$' "\\mathdefault{}$"` | `.replace('$\\mathdefault{}$', '')`, `dates.py:602` |
| result | the returned `str` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `text : str` (a sequence of code points) | `text : List Char` |
| per-code-point operations (`re.sub` over `[a-zA-Z]`, `str.replace` of single chars, prefix-token deletion) | `List Char` operations (total, sound; mapping.md §note) |
| `str` result | `List Char` (`String.mk` recovers the `str`; G-CONF compares as the joined string) |
| `re` ASCII class `[a-zA-Z]` | `Char.isAlpha` (verified: true exactly on ASCII `A-Z`/`a-z`, false on digits, `-`, `:`, space, and non-ASCII letters) |

### String modeling note
The transform is entirely per-code-point (regex over an ASCII class, single-char
`str.replace`s, a literal-token deletion). `List Char` is the faithful, total
model (SPEC_GUIDE §2). G-CONF bridges I/O by `"".join` on the shadow's char list
vs the oracle's `str`; both sides are byte-for-byte strings.

## Callee provenance + flag deps
- **A-reference (op 1):** `re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text)`
  is an UNCHANGED standard-library callee that the patch keeps verbatim. It is
  modeled DEEPLY as `bracketLetterRuns` (not axiomatized). `axiom_check.py`
  validates the model `== re.sub` over boundary + 2·10^5 fuzz inputs. The regex
  group `[a-zA-Z]+` is greedy and matches maximal ASCII-letter runs; the model's
  `takeWhile Char.isAlpha` / `dropWhile Char.isAlpha` reproduce this exactly.
- **No A-consumed axiom.** The proof discharges `result = texLabel text` by
  reduction of the loop to the `escapeMathSyms` fold (front-recursive fold +
  accumulator loop, PROOF_PLAYBOOK Route B); no callee contract is assumed.
- **Flag dependency:** `_wrap_in_tex` is only invoked when `usetex` is set
  (`DateFormatter.__call__` / `ConciseDateFormatter` under `text.usetex`). The
  modeled value is the pure string transform; the `usetex` gate selects *whether*
  it runs, not *what* it computes, so it is not a parameter of the model. The
  FAIL_TO_PASS tests set `text.usetex=True` (and `style.use("default")`).
- **`str.replace` chaining (op 2):** the three single-character replaces
  `-`,`:`,` ` have pairwise-distinct single-char sources, and no source char
  occurs inside any replacement string's *source position*, so the chain equals
  one left-to-right per-character map — soundly modeled as the `escapeMathSym`
  loop. (Order-independence verified by G-CONF.)

## G-LEAK
The problem_statement (the public issue) speaks only of "spacing for a datetime
axis when using usetex" being "unclear"/"unfair" — it does NOT name
`_wrap_in_tex`, `re.sub`, `mathdefault`, `replace`, or the `{-}`/`{:}`/`\;`
tokens. The hints_text (NOT public) contains the monkey-patch with
`_wrap_in_tex`/`{:}`/`\;`, but G-LEAK is judged against problem_statement only.
The spec view therefore uses neutral behavioral vocabulary ("math-default
group", "thin-space command", "braced") and the modeled identifier `texLabel`
shares no patched def name (`_wrap_in_tex` strips to `wrapintex`) as a substring.
The mathdefault/`{-}`/`{:}`/`\;` literals appear ONLY as the concrete output the
behavior must produce (describing behavior, not the edit).

## Pinned G-CONF / G-AX fuzz seed
`21568`.
