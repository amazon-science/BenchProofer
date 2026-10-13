# refinement.md — django__django-12155

The operation-by-operation correspondence between `model.py`'s implementation
(the `dedent_block` impl region plus the deep `dedented` model in the `pure`
region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The de-indentation site — `parse_docstring` (`utils.py`)

Gold hunk (`django/contrib/admindocs/utils.py`): the helper `trim_docstring`
(`utils.py:27-39`) is deleted, and `parse_docstring` switches its
normalisation to `inspect.cleandoc` with an early empty-input return:
```
-def trim_docstring(docstring):
-    ...
-    indent = min(len(line) - len(line.lstrip()) for line in lines if line.lstrip())
-    trimmed = [lines[0].lstrip()] + [line[indent:].rstrip() for line in lines[1:]]
-    return "\n".join(trimmed).strip()
-
 def parse_docstring(docstring):
-    docstring = trim_docstring(docstring)
+    if not docstring:
+        return '', '', {}
+    docstring = cleandoc(docstring)
     parts = re.split(r'\n{2,}', docstring)
     ...
```

| # | model.py impl op (`dedent_block` / `dedented`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `eff: List[int]` (one entry per line: leading-whitespace count, or `-1` for blank) | `docstring: str`, split via `docstring.expandtabs().split('\n')` | R | `str` ↔ per-line summary `List[int]` (mapping.md §2). `expandtabs` + line split is the unchanged preprocessing shared by `trim_docstring` and `cleandoc`. |
| A2 | `margin = clamp_margin(min_indent_from(ToSeq(eff), 1))` — min leading-whitespace over the non-blank lines AFTER the first | the common-indentation measurement of `cleandoc`: `margin = min(indent for line in lines[1:] if content)` with the `sys.maxsize` sentinel | A-reference | the changed measurement is modeled **deeply** (`min_indent_from` over `s.drop(1)` ⇔ `lines[1:]`, with `clamp_margin`/`NO_AMOUNT()` ⇔ `margin`/`sys.maxsize` — the empty fold is marked by SIGN, not by magnitude: `sys.maxsize` is unreachable for a real line only because it bounds a C-level index, while the carrier's `int` is unbounded, so a large marker would alias a body line at that indentation and leave it unmoved). No consumed axiom; G-AX asserts `dedented == cleandoc`'s per-line profile (mapping.md §3.1). The pre-patch measured over ALL lines (`min_indent_from(.., 0)` ⇔ `min(... for line in lines ...)`), which the prepatch reproduces and which **fails** the spec. |
| A3 | `first_line(eff[0])` — non-blank first line → 0, blank first line → −1 | `lines[0] = lines[0].lstrip()` | A-reference (I under R) | `lstrip()` of a non-blank line zeroes its indent; of a blank line leaves it blank. The deep model encodes exactly this; identical pre- and post-patch (both lstrip line 0). |
| A4 | `remove_margin(ToSeq(eff).drop(1), margin)` — each subsequent line loses `margin` leading-whitespace units (blank stays blank) | `lines[i] = lines[i][margin:]` for `i >= 1` | A-reference | the per-line removal modeled deeply; `remove_margin` ⇔ the slice `[margin:]` on the per-line leading whitespace (mapping.md §3.1). G-AX-validated. |
| A5 | `result` (`List[int]` of output per-line indent amounts) returned | `'\n'.join(lines)` (after blank-line stripping) | R | the output `str`'s per-line leading-whitespace profile is the carrier; the trailing/leading blank-line stripping (`while lines.pop()`) is an unchanged post-step orthogonal to the indentation transform that is the bug, so it is outside the carrier (mapping.md §3.1). The F2P observable is the body line's leading-whitespace amount, which A5 carries. |

The discriminating content of the change — measuring the common indentation
over the lines AFTER the first (`min_indent_from(s, 1)`) rather than over ALL
lines (`min_indent_from(s, 0)`) — lives in step A2. The pre-patch
`trim_docstring` used `min(... for line in lines if line.lstrip())` over every
line, so when the first line begins at column zero the measured amount is zero
and the body is left indented (the docutils "default-role: no content
permitted" error). `model_prepatch.py` reproduces exactly that
(`min_indent_from(ToSeq(eff), 0)`) and **fails** the postcondition
`ToSeq(Result()) == dedented(ToSeq(eff))` — the spec sensing the bug (G-DIFF).

## B. The model-method docstring site — `views.py:259`

Gold hunk (`django/contrib/admindocs/views.py`):
```
- utils.parse_rst(utils.trim_docstring(verbose), 'model', _('model:') + opts.model_name)
+ utils.parse_rst(cleandoc(verbose), 'model', _('model:') + opts.model_name)
```

This is the SAME normalisation swap (`trim_docstring(x)` → `cleandoc(x)`)
applied to the model-method docstring before `parse_rst`. It is the identical
operation `dedent_block` models (the de-indentation transform), so it needs no
separate modeled function: the verified property of the transform (A2–A4)
transfers to this call site verbatim under the same R/A-reference map. No
second `model_prepatch` is required, because the fixed behaviour is the same
de-indentation; its soundness is the same A-reference (`cleandoc`, G-AX), and
site A's prepatch already exercises the discriminating margin measurement both
sites share.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the common-indentation measurement (and the per-line removal it
feeds) — is modeled **deeply** (`min_indent_from` / `remove_margin` /
`first_line` / `dedented` in the `pure` region, consumed by `dedent_block`,
steps A2–A4), not hidden behind an axiom about the function under change. There
is **no consumed `@ContractOnly` axiom** at all (the `axioms` region is empty).
The only callee the new code invokes that is not itself changed —
`inspect.cleandoc` — is precisely the deep model's **A-reference**: G-AX
(axiom_check.py) validates `dedented == inspect.cleandoc`'s per-line indent
profile rather than the proof consuming any contract for it.

## D. verify(model) ⇒ resolved

`dedent_block` verifies only if its output equals `dedented(ToSeq(eff))` —
i.e. the body de-indented by the common amount measured over the lines AFTER
the first (A2), the first line flushed/kept-blank (A3), each body line slid
left by that amount (A4). By R (str ↔ per-line `List[int]`; `expandtabs`/split
and the blank-line post-strip are unchanged) the verified transform equals
`cleandoc(docstring)` on the tested inputs; by G-AX the deep model `dedented`
equals the real `inspect.cleandoc` per-line profile (A-reference) on 13
boundary + 40 000 fuzz docstrings, including the FAIL_TO_PASS shape where it
diverges from the pre-patch measurement. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited A-reference callee — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
