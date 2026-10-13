# mapping.md — pytest-dev__pytest-5262

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 58e6a09db49f34886ff13f3b7520dd0bcd7063cd`, states the type
abstraction, and records callee provenance.

Repo file under change: `src/_pytest/capture.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reported_mode(buffer_mode)` | the new `EncodedFile.mode` property — `src/_pytest/capture.py:445` (added immediately after the `name` property at `:445-448`, before `__getattr__` at `:450`) | the modeled changed function: the access mode the text wrapper advertises |
| `BINARY_MARKER` (== 98) | the literal `"b"` passed to `str.replace("b", "")` in the new property body | pure spec: the binary-mode marker code point |
| `without_marker(s)` *(deep model)* | `str.replace("b", "")` applied to the buffer's mode — `self.buffer.mode.replace("b", "")` | pure spec: the buffer mode with every binary marker deleted; the deep model of the changed string operation, validated `without_marker == str.replace("b","")` by axiom_check.py (G-AX). NOT a consumed axiom. |
| `kept(c)` | the per-character action of `str.replace("b", "")`: drop a `"b"`, keep anything else | pure spec: one code point's contribution |
| `marker_free(s)` | the property the F2P test observes: `"b" not in sys.stdout.mode` | pure spec: the sequence carries no binary marker |

The pre-patch repo state the change closes: there was **no** `mode` attribute on
`EncodedFile`, so `EncodedFile.mode` fell through `__getattr__`
(`src/_pytest/capture.py:450-451`) to `getattr(self.buffer, "mode")`, returning
the underlying binary buffer's mode verbatim (e.g. `"rb+"` from the
`safe_text_dupfile(f, mode="wb+")` duplication at `:566`), which still contains
the binary marker. `model_prepatch.py` reproduces that identity (mode reported
unchanged) and fails the postcondition.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the buffer's `.mode`, and the property's return value) | `List[int]` of Unicode code points | `s[k]` ↔ `mode[k] == ord(s[k])`; `len(s)` ↔ `len(mode)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]`; the marker `"b"` ↔ `98` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `self.buffer.mode` attribute read | the `buffer_mode` parameter | the wrapper reads the underlying buffer's mode; the property's only input is that string. Modeled as the (read-only) parameter `buffer_mode`. |
| `str.replace("b", "")` | the deep fold `without_marker` (§3) | per-code-point: `"b"`/98 deleted, every other character kept in order. `str.replace(old, new)` with a single-character `old` and empty `new` is exactly the deletion of every occurrence of `old`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. The changed operation, modeled deeply (no consumed axiom)

`str.replace("b", "")` is the **changed** operation, so it is NOT axiomatized —
it is modeled DEEPLY by the `@Pure` fold `without_marker` (with `kept`) in the
`pure` region, and validated equal to the real CPython `str.replace` out-of-band
by axiom_check.py (G-AX). For a single-character search string `old` and an
empty replacement, `s.replace(old, "")` removes every occurrence of `old` and
leaves all other characters in their original order — there is no overlapping or
substring subtlety, so the operation is exactly the per-code-point deletion:

  `kept(c) = empty if c == 98 ('b') else PSeq(c)`,
  `without_marker(s) = kept(s[0]) + without_marker(s.drop(1))`.

There are **no `@ContractOnly` axioms** in this bundle: the modeled function calls
no unchanged callee that Nagini cannot express (the only input is the buffer's
mode string, modeled as the parameter). G-AX therefore checks one A-reference
deep model (`without_marker == "".join-style str.replace("b","")`) and consumes
no axiom.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`s.replace("b", "")` on boundary inputs (all the file-mode strings CPython
produces — `"rb+"`, `"wb+"`, `"rb"`, `"wb"`, `"ab"`, `"xb"`, `"rb+"`,
`"r"`, `"w+"`, `""`, repeated/leading/trailing `b`s, `b` adjacent to other
letters) plus randomized fuzz over `{r,w,a,x,b,+,t, ...}`, and asserts the deep
model `without_marker` equals the real callee and that the real result is
`marker_free`. It imports only the Python standard string operation (`str`);
nothing repo-specific. Exit 0 iff sound.
