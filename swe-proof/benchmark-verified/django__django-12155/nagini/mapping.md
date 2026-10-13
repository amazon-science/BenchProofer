# mapping.md — django__django-12155

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e8fcdaad5c428878d0a5d6ba820d957013f75595`, states the type
abstraction, and gives the provenance of the A-reference callee (its source +
the exact behaviour the deep model is validated against).

Repo files under change: `django/contrib/admindocs/utils.py`,
`django/contrib/admindocs/views.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `dedent_block(eff)` | the docstring-indentation normalisation that `parse_docstring` applies to its argument: `django/contrib/admindocs/utils.py:46` (`docstring = trim_docstring(docstring)`, pre-patch) → `docstring = cleandoc(docstring)` (post-patch) | the modeled changed operation (uniform docstring de-indentation) |
| `min_indent_from(eff, k)` *(deep model — A-reference)* | the common-indentation measurement: pre-patch `min(... for line in lines if line.lstrip())` over ALL lines (`utils.py:37`); post-patch the PEP 257 measurement over the lines AFTER the first, performed inside `inspect.cleandoc` | pure spec: smallest leading-whitespace amount among the non-blank lines from index `k` on |
| `remove_margin(s, margin)` *(deep model — A-reference)* | the per-line removal `line[indent:]` (pre-patch `utils.py:38`) / `lines[i][margin:]` (post-patch, inside `inspect.cleandoc`) | pure spec: remove `margin` leading-whitespace units from each subsequent line |
| `first_line(x)` | `lines[0].lstrip()` (pre-patch `utils.py:38`) / `lines[0] = lines[0].lstrip()` (post-patch, inside `inspect.cleandoc`) | pure spec: a non-blank first line is moved flush-left, a blank first line stays blank |
| `dedented(s)` *(deep model — A-reference)* | the whole normalised block: `inspect.cleandoc(docstring)` (`utils.py:34` post-patch; CPython stdlib `Lib/inspect.py`) | pure spec: the per-line indentation transform of the entire block; the deep model validated `dedented == inspect.cleandoc` (per-line indent profile) by axiom_check.py (G-AX), NOT consumed as an axiom |
| `clamp_margin(m)` / `NO_AMOUNT()` | the `min(...)` fold's identity / "no body line" case — pre-patch `trim_docstring` cannot face an empty fold because the first line guarantees a member; `inspect.cleandoc` uses `margin = sys.maxsize` and only removes when `margin < sys.maxsize` | pure spec: the amount actually removed, 0 when no non-blank line follows the first. The marker is **negative** (`NO_AMOUNT() == -1`), not large: `sys.maxsize` is what a fixed-width C-level index can carry, whereas the carrier's `int` is unbounded, so a *large* marker would be a reachable leading-whitespace amount and a body line at exactly that indentation would be read as "there was no body line". A count of characters is never negative, so the sign separates "nothing measured" from every amount. |

The second change site (`django/contrib/admindocs/views.py:259`) replaces
`utils.parse_rst(utils.trim_docstring(verbose), ...)` with
`utils.parse_rst(cleandoc(verbose), ...)` — the SAME normalisation swap applied
to the model-method docstring path. It is the identical operation under spec
(the de-indentation `dedent_block` models), so it needs no separate modeled
function; see refinement.md §B.

The pre-patch repo symbol the change removes (for the refinement audit, not
referenced from the consumer spec view): the helper `trim_docstring`
(`utils.py:27-39`), whose `indent = min(... for line in lines if line.lstrip())`
(`utils.py:37`) ranges over the FIRST line as well — the bug. `parse_docstring`
also gains an early `return '', '', {}` for a falsy docstring (`utils.py`,
post-patch), preserving the old `trim_docstring` short-circuit on empty input;
this is an unchanged guard outside the modeled indentation transform.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a docstring `str` | a `List[int]` `eff`, one entry per line | line `k` ↔ `eff[k]`: a non-blank line maps to its leading-whitespace count `len(line) - len(line.lstrip())` (`>= 0`); a blank (empty / whitespace-only) line maps to the blank marker `-1` |
| `docstring.expandtabs().split('\n')` (the line split, identical pre- and post-patch) | the per-line summary `eff` | `expandtabs` is the unchanged preprocessing both `trim_docstring` and `cleandoc` perform before measuring indentation; the split-on-`'\n'` line list is summarised entry-wise into `eff` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(eff)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror the per-line list operations |
| the normalised output `str` | a `List[int]` of the OUTPUT per-line leading-whitespace amounts | each output line's leading-whitespace count (or `-1` blank); the FAIL_TO_PASS observable — whether the body line is flush-left — is exactly this amount on the body line |

`str` indexing/iteration is banned in Nagini, so a line is summarised by the
single number the indentation transform depends on (its leading-whitespace
count, or the blank marker). The non-whitespace CONTENT of a line is invariant
under both `trim_docstring` and `cleandoc`'s indentation steps (they only add/
remove leading whitespace and strip trailing whitespace/blank lines), so it is
not part of the carrier; the F2P test observes the leading-whitespace amount.

## 3. Callee provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `dedented` deep model ↔ `inspect.cleandoc` (A-reference)
**Callee:** CPython `inspect.cleandoc(doc)` — the canonical PEP 257 docstring
de-indentation, stable across every supported 3.x (the algorithm is unchanged
since it was introduced). Source (`Lib/inspect.py`):

```python
def cleandoc(doc):
    try:
        lines = doc.expandtabs().split('\n')
    except UnicodeError:
        return None
    else:
        # Find minimum indentation of any non-blank lines after first line.
        margin = sys.maxsize
        for line in lines[1:]:
            content = len(line.lstrip())
            if content:
                indent = len(line) - content
                margin = min(margin, indent)
        if lines:
            lines[0] = lines[0].lstrip()
        if margin < sys.maxsize:
            for i in range(1, len(lines)): lines[i] = lines[i][margin:]
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
        return '\n'.join(lines)
```

The changed operation is the **indentation measurement and removal**, modelled
**deeply** by the `@Pure` functions in the `pure` region; there is **no
`@ContractOnly` axiom** the proof consumes. The deep model is validated equal
to the real callee out-of-band by axiom_check.py (G-AX), at the index level the
model decides:

  * `margin = min over the NON-BLANK lines AFTER the first` ↔ `min_indent_from(s, 1)`,
    the empty fold reported as `NO_AMOUNT()` and turned into "remove nothing" by
    `clamp_margin` — the counterpart of `cleandoc`'s `margin = sys.maxsize` /
    `if margin < sys.maxsize`, encoded by SIGN rather than by magnitude because
    the carrier's `int` is unbounded and any magnitude is a reachable amount;
  * `lines[0] = lines[0].lstrip()` ↔ `first_line(s[0])` (non-blank → 0, blank → −1);
  * `lines[i] = lines[i][margin:]` for `i >= 1` ↔ `remove_margin(s.drop(1), margin)`
    (a non-blank line loses `margin`; a blank line stays blank).

`cleandoc`'s trailing/leading **blank-line stripping** (`while lines.pop()`) is
an unchanged post-step ORTHOGONAL to the indentation measurement that is the
bug; the deep model (and the G-AX comparison) is taken at the per-line indent
profile BEFORE that stripping, so the comparison is not masked by it.

**Flag/configuration dependency:** none — `cleandoc` takes a single argument
and the per-line transform has no options. (For contrast, the pre-patch
`trim_docstring` is not a stdlib callee; it is the buggy code being replaced,
and its measurement `min(... for line in lines if line.lstrip())` ranges over
the first line too — `min_indent_from(s, 0)` — which is the prepatch skeleton.)

**Soundness check (G-AX):** `axiom_check.py` runs the real `inspect.cleandoc`
on 13 boundary docstrings (empty, single line, the FAIL_TO_PASS shape, the
blank-first-line Django docstring style, tab-indented, all-blank, mixed) plus
40 000 randomized fuzz docstrings, and asserts that its per-line leading-
whitespace profile equals the deep model `dedented` of the input summary at
each index (no value-membership double-mask). It additionally pins the
FAIL_TO_PASS discriminator: on `"firstline\n\n    second line"` the fixed
measurement (over `lines[1:]`) gives margin 4 and flushes the body line, while
the pre-patch measurement (over all lines) gives margin 0 and would leave it
indented — the two MUST differ, and the real `cleandoc` MUST match the fixed
deep model. It imports only the standard-library `inspect` module (the very
module the gold patch calls); nothing repo-specific. Exit 0 iff sound.
