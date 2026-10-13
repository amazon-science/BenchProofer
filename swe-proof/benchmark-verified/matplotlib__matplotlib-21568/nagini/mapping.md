# mapping.md — matplotlib__matplotlib-21568

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f0632c0fc7339f68e992ed63ae4cfac76cd41aad`, states the type
abstraction, and gives the provenance of the kind-A reference the deep model is
validated against.

Repo file under change: `lib/matplotlib/dates.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `protect_codepoints(text)` | `_wrap_in_tex(text)` — `lib/matplotlib/dates.py:592` (changed body lines 597-598) | the modeled changed function; the verified function captures the per-code-point protection substitution that `_wrap_in_tex` performs on its tick-label text |
| `protect(c)` | the per-character protection `.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')` chain (`lib/matplotlib/dates.py:597-599` post-patch) | pure spec: protected expansion of one code point |
| `protected_seq(s)` *(deep model — A-reference)* | the whole-string protection performed by the `.replace` chain inside `_wrap_in_tex` (the changed operation) | pure spec: protection of a sequence; the deep model of the changed substitution, validated `protected_seq == real protection` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `tok_dash` / `tok_colon` / `tok_space` | the literal protection tokens `{-}` `{:}` `\;` | pure spec: protection tokens as code-point sequences |

The pre-patch repo behaviour the change extends (for the refinement audit, not
referenced from the consumer spec view): the old body protected only the hyphen
(`ret_text.replace('-', '{-}')`, `lib/matplotlib/dates.py:598` @ base_commit),
leaving the colon and the space unprotected.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `text` argument of `_wrap_in_tex`, and its return) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the unchanged regex wrapping `re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text)` (`dates.py:594`) | framing, omitted from the verified function (I/R) | the regex acts only on `[a-zA-Z]` runs and introduces only the framing characters `} $ \ m a t h d e f a u l t {`, none of which is `-` `:` ` `; so the protection substitution acts on exactly the protected code points of the original `text`. Modeled as framing applied around the protection (refinement.md A1-A2). |
| the unchanged `'$\\mathdefault{' + … + '}$'` wrap and `.replace('$\\mathdefault{}$', '')` empty-fragment removal (`dates.py:599-600` post-patch) | framing, omitted (I/R) | this wrap/strip only adds/removes the fixed framing string and never touches `-` `:` ` `; observationally inert with respect to the protection delta. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `protected_seq` deep model ↔ the changed protection in `_wrap_in_tex` (A-reference)
**Operation:** the per-code-point protection chain
`.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')` inside
`_wrap_in_tex` (gold post-patch). This is the operation UNDER specification, so
it is modeled **deeply** by the `@Pure` fold `protected_seq` (with `protect`) in
the `pure` region; there is **no `@ContractOnly` axiom** the proof consumes. The
deep model is instead validated equal to the real changed operation out-of-band
by axiom_check.py (G-AX). Gold source (`lib/matplotlib/dates.py`, post-patch):

```python
def _wrap_in_tex(text):
    p = r'([a-zA-Z]+)'
    ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)
    # Braces ensure symbols are not spaced like binary operators.
    ret_text = ret_text.replace('-', '{-}').replace(':', '{:}')
    # To not concatenate space between numbers.
    ret_text = ret_text.replace(' ', r'\;')
    ret_text = '$\\mathdefault{' + ret_text + '}$'
    ret_text = ret_text.replace('$\\mathdefault{}$', '')
    return ret_text
```

The three `.replace` calls operate on disjoint targets (`-`, `:`, ` `), and each
replacement output (`{-}`, `{:}`, `\;`) contains none of the other two targets,
so the chain is exactly the **per-code-point substitution**

  `- → {-}`, `: → {:}`, ` ` → `\;`, else identity,

which is what `protected_seq` / `protect` encode (the `\;` token is the two code
points `\\`=92, `;`=59). G-AX asserts `protected_seq(s) == real protection(s)`
on 26 boundary + 20000 fuzz inputs and additionally that the gold `_wrap_in_tex`
equals the unchanged framing applied around the deep model on 37 boundary +
5000 fuzz labels — confirming the protection is the only behavioural delta.

The colon `:` → `{:}` and the space ` ` → `\;` are the two behavioural changes
the F2P tests observe (`delta2`/`delta3` of `test_date_formatter_usetex`,
`t_delta2`/`t_delta3` of `test_concise_formatter_usetex`); the pre-patch body
protected only `-` and left `:`/` ` bare. Docs / source:
https://github.com/matplotlib/matplotlib/blob/v3.5.0/lib/matplotlib/dates.py
(`_wrap_in_tex`); Python `str.replace` is the standard library.

**No A-consumed axiom.** The proof depends on no `@ContractOnly` callee; the
only kind-A relationship is the A-reference above.
