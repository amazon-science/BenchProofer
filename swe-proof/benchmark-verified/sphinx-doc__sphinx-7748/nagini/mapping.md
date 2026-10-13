# mapping.md — sphinx-doc__sphinx-7748

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9988d5ce267bf0df4791770b469431b1fb00dcdd`, states the type
abstraction, and gives the provenance of the deep-model reference (there are no
consumed axioms).

Repo file under change: `sphinx/ext/autodoc/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `gather_signatures(cont, val)` | `DocstringSignatureMixin._find_signature` (`sphinx/ext/autodoc/__init__.py:1040`) together with `DocstringSignatureMixin.format_signature` (`:1084`) | the modeled changed behaviour: which / how many candidate signature lines are gathered from the top of a documentation block, and the ordered sequence they render to |
| `collected(cont, val)` *(deep model — A-reference)* | the post-patch `_find_signature` gathering loop (`:1043-1100` post-patch) + `format_signature` join (`:1119-1126` post-patch) | pure spec: the ordered sequence of collected signature values, validated == the real gathering by axiom_check.py (G-AX) |
| `run_len(cont)` *(deep model — A-reference)* | the number of signatures the post-patch loop records (`result` plus every entry appended to `self._signatures`) | pure spec: count of collected lines |
| `cont` (per-line continuation flag) | `line.endswith('\\')` test in the post-patch loop (`:1051` post-patch) | a line is *continued* (flag non-zero) iff it ends with the `\` line-continuation marker; controls the `if multiline: continue else: break` |
| `val` (per-line signature value) | the recorded `(args, retann)` / `"(%s) -> %s"` rendering of an accepted signature line | opaque integer token standing for the parsed signature description of a line |

The pre-patch repo behaviour the change replaces (for the refinement audit, not
referenced from the consumer spec view): `_find_signature` looked only at
`doclines[0]` of each docstring block (`:1053` pre-patch:
`match = py_ext_sig_re.match(doclines[0])`), recorded at most one signature,
and `break`-ed; `format_signature` returned just `super().format_signature(...)`
(`:1091` pre-patch) with no joined extra signatures.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a documentation block `doclines: List[str]` whose leading lines are candidate signature lines | two parallel `List[int]` streams `cont`, `val` indexed by line | for each accepted signature line `k`: `cont[k]` is non-zero ⇔ `doclines[k].endswith('\\')`; `val[k]` is a distinct token standing for that line's parsed `(args) -> retann` rendering |
| `line.endswith('\\')` → `multiline` flag | `cont[k] != 0` | the continuation marker is the only thing that decides `continue` (keep gathering) vs `break` (stop) after a recorded signature |
| recorded signature string `"(%s) -> %s" % (args, retann)` | `val[k]` (opaque int token) | the spec pins the COUNT and ORDER of collected signatures; the exact string content of each is an opaque token (its production from `args`/`retann` is unchanged by the patch and irrelevant to the discriminating behaviour) |
| `format_signature` join `"\n".join([sig] + self._signatures)` | the result `List[int]` (the ordered collected token sequence) | the join is order-preserving concatenation of the collected signatures; modeled as the ordered result list |

`str` indexing/iteration is banned in Nagini; the per-line structure that drives
the gathering (continuation flag, signature value) is therefore lifted to two
parallel `List[int]` streams, and the specification is phrased over `PSeq[int]`
via `ToSeq`.

### Modelled domain
The model's domain is a block of accepted signature lines (a clean run): every
modeled line is a line that matches the signature regex AND whose base name is
in `valid_names`. This is exactly the tested shape — the `class E` fixture is
two `__init__` signature lines, the first continued. The real loop additionally
*skips* (via `continue`) non-matching / wrong-name lines and *stops* (via
`break`) at an empty line; those interleavings do not change the collected
count/order for a clean run and are exercised by axiom_check.py's reimplemented
real algorithm rather than carried in the Nagini fragment.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `collected` / `run_len` deep model ↔ post-patch signature gathering
**Behaviour:** the post-patch `_find_signature` loop walks the lines of a
docstring block; for each accepted signature line it records the signature
(`result` for the first, `self._signatures.append(...)` for the rest) and then
`continue`s iff the line was continued (`multiline`, i.e. ended with `\`),
otherwise `break`s. `format_signature` joins `[sig] + self._signatures`. The net
effect — pinned by the model — is: **collect the values of every line from the
top up to and including the first terminating (non-continued) line.**

The changed gathering operation is modeled **deeply** by the `@Pure` folds
`run_len` and `collected` (front-recursive, one unfold per line) plus the
verified loop in `gather_signatures`; there is **no consumed `@ContractOnly`
axiom**. The deep model is instead validated equal to the real algorithm
out-of-band by axiom_check.py (G-AX), which reimplements the post-patch loop +
join using only the stdlib `re` module and the verbatim `py_ext_sig_re`
(`sphinx/ext/autodoc/__init__.py:55`):

```python
py_ext_sig_re = re.compile(r'''^ ([\w.]+::)?([\w.]+\.)?(\w+)\s*
    (?:\((.*)\)(?:\s*->\s*(.*))?)?$''', re.VERBOSE)
```

**Soundness check (G-AX):** `axiom_check.py` runs the reimplemented real
gathering on (a) the exhaustive set of clean runs of length 1..6 over all
continuation patterns, (b) 20000 randomized clean-run fuzz blocks, (c) the exact
F2P `class E` fixture (two `__init__` signatures, first continued → 2 collected),
and (d) the `class D` single-signature shape (→ 1 collected). For each it asserts
the model's `run_len` equals the number of signatures the real code renders AND
that the real collected signature at each position equals the rendering of that
same line (order-faithful, no count-only proxy). Exit 0 iff sound. It imports
only the standard library; nothing repo-specific.

## 4. Secondary change sites (no separate model — outside the F2P-tested behaviour)

The gold patch also contains two incidental hunks that the F2P tests do not
discriminate and that are not part of the modeled behaviour:

- `get_doc` (`:1074`): `lines = getattr(self, '_new_docstrings', None); if lines
  is not None: return lines` → `if self._new_docstrings is not None: return
  self._new_docstrings`. A refactor enabled by the new class attribute
  `_new_docstrings = None`; observationally identical (both return the cached
  docstrings when present, else fall through to `super().get_doc`).
- `SingledispatchFunctionDocumenter.format_signature` (`:1208` area): adds
  `documenter.objpath = [None]` so a synthesised function documenter has a
  non-empty `objpath` (the new `_find_signature` reads `self.objpath[-1]` up
  front; the pre-patch read it only inside the matched branch). A defensive
  guard against `IndexError` on the singledispatch path; the F2P tests
  (`test_autoclass_content_and_docstring_signature_init/both`) do not exercise
  singledispatch.

These are recorded in refinement.md as I (identical-effect refactor) / a guard
outside the modeled domain; neither changes the gathered-signature count/order
that `gather_signatures` pins.
