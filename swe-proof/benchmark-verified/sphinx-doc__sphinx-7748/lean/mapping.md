# mapping.md — sphinx-doc__sphinx-7748

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 9988d5ce267bf0df4791770b469431b1fb00dcdd
- changed file: `sphinx/ext/autodoc/__init__.py` (one mixin, two coordinated methods)
- spec_provenance: cold

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_collectSignatures` / `problem_spec_collectSignatures` / `correct_collectSignatures` | the signature-reading logic of `DocstringSignatureMixin` — `_find_signature` (the `result` it returns) together with `format_signature` (the `[sig] + self._signatures` join) | `sphinx/ext/autodoc/__init__.py:1041-1066` (`_find_signature`) and `:1085-1094` (`format_signature`) |
| `matchSig` (opaque callee) | `py_ext_sig_re.match(line)` and its `.groups()` (`base`, `args`, `retann`) | regex defined `:55-62`; called `:1053` |
| `validNames` (input) | the `valid_names` candidate list (`self.objpath[-1]`, `'__init__'`, the `__mro__` class names) | computed `:1044-1048` (post-patch: hoisted above the loop) |

## What the fix changes (modeled behavior)

The mixin reads object signatures from the leading text of a docstring. The
text is a list of *docstrings* (each a list of lines). Historically only the
**very first line** of each docstring was inspected, and at most **one**
signature was ever picked up.

The fix makes the reader:
1. scan **every** leading line of a docstring (stopping at the first empty
   line), not just line 0;
2. support a **line-continuation** convention — a candidate line ending in a
   backslash means "another signature follows on the next line" (the trailing
   backslash and trailing whitespace are stripped before matching);
3. **collect all** matching signatures in order (the first becomes the primary
   signature, each subsequent one is appended), instead of keeping only the
   first;
4. across the list of docstrings, use the first docstring that yields at least
   one signature (then stop).

A signature line is recognised by an unchanged extended-signature regular
expression (`matchSig`); a recognised line counts only when its parsed *thing
name* (`base`) is one of the object's candidate names (`validNames`).

## Lean ↔ Python type bijection (used by G-CONF, G-AX)

| Python | Lean | bijection |
|---|---|---|
| one docstring line, `str` value-level | `String` | value identity |
| one docstring (`List[str]`) | `List String` | per-line, in order |
| `docstrings : List[List[str]]` (from `get_doc()`) | `List (List String)` | per-docstring, in order |
| `valid_names : List[str]` | `validNames : List String` | per-name, in order |
| `py_ext_sig_re.match(line)` → `None` / `(exmod,path,base,args,retann)` | `matchSig : String → Option SigMatch` (`base`,`args`,`retann`) | the regex's match result; `exmod`/`path` are irrelevant to the modeled behavior and are not carried |
| `line.endswith('\\')` | `String.endsWith line "\\"` | trailing-backslash test |
| `line.rstrip('\\').rstrip()` | `stripContinuation` (drop trailing `\`, then trailing whitespace per `isPyWhitespace` — the exact `str.isspace()` codepoint set, NOT Lean's narrower `Char.isWhitespace`) | per-char |
| the collected signature list (`result` then `self._signatures`) | `List Sig` (`args`,`retann`), head = primary | order-preserving |

`args`/`retann` are carried as the raw matched substrings (`retann` is optional,
mirroring the regex's optional return-annotation group). The downstream string
formatting (`"(%s) -> %s"`, and `super().format_signature`) is value-level
rendering of these same fields and is not part of the modeled collection
behavior.

## Callee provenance / flag deps

- `matchSig` (`py_ext_sig_re.match`) is an **UNCHANGED** callee. It is declared
  `opaque matchSig : String → Option SigMatch` so it can appear in the
  executable impl. It is used **identically** in the spec helper (`scanLines`)
  and in `implementation_collectSignatures`, so it **cancels** in the
  correctness argument: the proof consumes **no** property of it. It is an
  **A-reference** (no consumed axiom). Nothing for G-AX to validate (skip stub).
- `validNames` is an input. The patch hoists its computation out of the loop but
  does not change its value (it was recomputed identically each iteration
  before). Its construction (`objpath`, `__init__`, `__mro__`) is not modeled —
  it is an unchanged input to the collection behavior.
- The `self.objpath = [None]` line added in `format_signature` of the
  singledispatch overload branch (hunk 4) only affects how `validNames` is built
  for module-level singledispatch functions; it is not exercised by the modeled
  collection behavior (which takes `validNames` as a given) and not covered by
  the F2P tests. Not modeled.
- The `get_doc` change (hunk 2: `getattr(self,'_new_docstrings',None)` →
  `self._new_docstrings`, with a class-level `None` default) is a refactor with
  identical behavior; the `_new_docstrings`/`prepare_docstring` body re-prep is a
  side effect on the *description* text, not on the signature output, and is not
  asserted by the F2P slice. Not modeled.

## G-CONF fuzz seed
`SEED = 7748` (pinned in conformance_check.py).
