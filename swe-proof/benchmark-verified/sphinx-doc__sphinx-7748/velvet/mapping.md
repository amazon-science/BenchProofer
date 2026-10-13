# mapping.md — sphinx-doc__sphinx-7748

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9988d5ce267bf0df4791770b469431b1fb00dcdd`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of every abstracted (unchanged) callee.

Repo file under change: `sphinx/ext/autodoc/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectSignatures (lines : List LineInfo)` | `DocstringSignatureMixin._find_signature` — `sphinx/ext/autodoc/__init__.py:1040` (the per-docstring line scan, body lines 1048-1071) | the modeled changed function: scan one docstring's lines, collect all signatures |
| `collectSigs (l : List LineInfo)` *(deep model)* | the changed control flow of the `for j, line in enumerate(doclines)` inner loop (post-patch lines 1054-1083 of `patch.diff`) | pure spec: the list of signatures collected from one docstring under the scan rules |
| `LineInfo` *(input abstraction — A-reference)* | the per-line classification computed by the **unchanged** callees `py_ext_sig_re.match`, `str.endswith`, `bool(line)`, and the `valid_names` membership test | the abstract carrier of one docstring line (see §2/§3) |
| `Sig` (args, retann) | the `(args, retann)` pair from `match.groups()` (`m.group(4)`, `m.group(5)`) | the extracted signature payload |

Repo constructs the change leaves UNCHANGED (refinement audit only, NOT in the
consumer spec view): the regex `py_ext_sig_re` (`__init__.py:55-62`); the
`valid_names` candidate list (`objpath[-1]`, `'__init__'`, the `__mro__` class
names — moved above the loop by the patch, semantically the same set);
`prepare_docstring`/`get_doc` (re-indentation of the tail); the outer
`for i, doclines in enumerate(docstrings)` loop (first docstring yielding a
signature wins — true pre- AND post-patch); and `format_signature`'s join of the
collected extras with newlines (§2, leg R5).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| one docstring = `List[str]` of lines (post `get_doc`/dedent) | `List LineInfo` | line `s` ↔ the `LineInfo` of §3; list order preserved; `len(doclines)` ↔ `lines.length` |
| the matched `(args, retann)` strings | `Sig` (two `String` fields) | `m.group(4)` ↔ `sig.args`, `m.group(5)` ↔ `sig.retann`; `None` group ↔ `""` (only read when `isSig`) |
| `_find_signature`'s `result` (first sig) + `self._signatures` (the rest) | `out : List Sig` | `result = out.head?`; `self._signatures = out.tail` rendered `"(args) -> retann"` |
| `format_signature` join `"\n".join([sig] + self._signatures)` | identity on `out` (omitted) | the newline join is a structural R/I transliteration of `out` to the rendered block; it changes no signature, only concatenates them — checked end-to-end by G-CONF |
| the outer `for i, doclines` docstring loop | identity (omitted) | unchanged pre/post: first docstring producing a signature wins; the discriminating behaviour is entirely within one docstring (collecting >1 sig), so the method models the inner scan |

`Sig` payloads are carried, never recomputed by the fold, so `String` (value
level) is the right carrier — the operation is not per-code-point.

## 3. `LineInfo` ↔ one docstring line (A-reference — checked by G-AX)

`LineInfo` abstracts the four facts the changed control flow reads about a single
line. Each fact is produced by an **unchanged** callee; none is the operation the
patch changes. The bridge `line_info(s, valid_names)` (axiom_check.py) is exactly
the per-iteration prefix of the post-patch loop body:

```python
def line_info(s, valid_names):
    blank = not s                                   # `if not line: break`
    if s.endswith('\\'):                            # continuation marker
        cont = True
        stripped = s.rstrip('\\').rstrip()
    else:
        cont = False
        stripped = s
    m = py_ext_sig_re.match(stripped)               # the UNCHANGED signature RE
    is_sig = bool(m) and (m.group(3) in valid_names)
    args   = m.group(4) if m else None
    retann = m.group(5) if m else None
    return blank, is_sig, cont, (args, retann)
```

Field correspondence:

| `LineInfo` field | repo expression | note |
|---|---|---|
| `blank : Bool` | `not line` | tested FIRST; true ⇒ stop scanning this docstring (`break`) |
| `cont : Bool` | `line.endswith('\\')` | true ⇒ keep collecting past this matched line (`multiline`/`continue`) |
| `isSig : Bool` | `bool(py_ext_sig_re.match(stripped)) and base in valid_names` | true ⇒ this line yields a signature; the strip happens BEFORE the match |
| `sig : Sig` | `(match.group(4), match.group(5))` | the `(args, retann)` payload; only read when `isSig` |

**Callee provenance.** `py_ext_sig_re` is a module-level `re.compile` constant
(`__init__.py:55-62`); the patch does not touch it. `valid_names` depends on the
documenter kind: for a class it is `[objpath[-1], '__init__', *mro names]`; for a
plain function `[objpath[-1]]`. The patch only HOISTS its construction above the
loop (the set is identical) and, in a separate hunk, sets `documenter.objpath =
[None]` for synthesised overload documenters so `objpath[-1]` is defined. G-AX
fuzzes both configurations.

**Soundness check (G-AX).** `axiom_check.py` runs the REAL `py_ext_sig_re` /
`str` methods inside `line_info` on boundary lines (blank, plain text, a bare
name, a full signature, a signature with a trailing `\`, an indented second
signature, return-annotation variants) plus randomised fuzz, in BOTH documenter
configurations (plain-function `valid_names` and class `valid_names` with mro
names), and asserts each `LineInfo` field independently recomputed from the real
callees equals the bridge. Imports only `re` and the repo regex source. Exit 0
iff the abstraction is faithful.

**Scope note — why G-AX checks only the bridge.** G-AX runs against the repo at
`base_commit` *without* the gold patch (the harness applies the patch only for
G-CONF, whose oracle is the patched repo). The bridge is patch-independent (the
regex, `str` methods and name-membership are unchanged callees — the patch only
moves `py_ext_sig_re`'s call site, not its definition), so it is exactly the
property G-AX can soundly audit unpatched. The end-to-end equivalence "deep model
`collectSigs` == the real *patched* `_find_signature`/`_signatures`" is a property
of the CHANGED function and is owned by **G-CONF** (§4), which applies the gold
patch and diffs the R/I shadow against the patched oracle on ≥10⁵ inputs.
Re-asserting it inside the unpatched G-AX would compare the correct model against
the pre-patch bug — a false negative, not a soundness signal.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7748`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `collectSigs` (the deep-model control flow) and the
`format_signature` join to Python over the real `str`/list types, derives each
`LineInfo` from the real callees via the §3 bridge, and compares the rendered
signature block to the REAL patched `DocstringSignatureMixin.format_signature`
applied at base_commit. There are no consumed axioms, so the A leg is empty; the
`LineInfo` bridge fidelity (A-reference) is the G-AX concern, the control-flow
fidelity (R/I) the G-CONF concern.
