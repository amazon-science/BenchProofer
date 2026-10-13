# refinement.md — matplotlib__matplotlib-21568

The operation-by-operation correspondence between `model.py`'s implementation
(the `protect_codepoints` impl region and the deep `protected_seq` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (split into **A-consumed** — proof uses the axiom's `Ensures` — and
**A-reference** — a deep model validated == the real callee/operation by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The math-mode tick-label neutralisation — `_wrap_in_tex()` (`lib/matplotlib/dates.py:592`)

Gold hunk:
```
     p = r'([a-zA-Z]+)'
     ret_text = re.sub(p, r'}$\1$\\mathdefault{', text)

-    # Braces ensure dashes are not spaced like binary operators.
-    ret_text = '$\\mathdefault{'+ret_text.replace('-', '{-}')+'}$'
+    # Braces ensure symbols are not spaced like binary operators.
+    ret_text = ret_text.replace('-', '{-}').replace(':', '{:}')
+    # To not concatenate space between numbers.
+    ret_text = ret_text.replace(' ', r'\;')
+    ret_text = '$\\mathdefault{' + ret_text + '}$'
     ret_text = ret_text.replace('$\\mathdefault{}$', '')
     return ret_text
```

| # | model.py impl op (`protect_codepoints`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `text: List[int]` | `text: str` argument of `_wrap_in_tex` | R | `str` ↔ `List[int]` of code points (mapping.md §2). |
| A2 | (no node) | `re.sub(r'([a-zA-Z]+)', r'}$\1$\mathdefault{', text)` regex wrapping | I (framing) | UNCHANGED between pre/post patch (identical line). The regex acts only on `[a-zA-Z]` runs and introduces only the framing characters `} $ \ m a t h d e f a u l t {`, none of which is `-` `:` ` `. So the protection substitution that follows acts on exactly the protected code points of `text`; the verified function operates over that protected-code-point alphabet directly (mapping.md §2). Confirmed by G-AX end-to-end (deep model + this framing == gold). |
| A3 | the result is `protected_seq(ToSeq(text))`, i.e. the per-code-point substitution `- → {-}`, `: → {:}`, ` ` → `\;`, else identity, computed by the backward fold over `text` | `ret_text.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')` | A-reference | the changed string operation is modeled **deeply**: `protected_seq` (the spelled-out per-code-point fold in the `pure` region) and the verified loop in `protect_codepoints` ARE the substitution. There is no consumed `@ContractOnly` axiom — the proof never depends on one. The deep model is validated **== the real changed operation** out-of-band: G-AX (axiom_check.py) runs the gold `.replace` chain on boundary+fuzz and asserts `real protection == protected_seq`. The three `.replace` targets are disjoint and no replacement output contains another target, so the chain is exactly the per-code-point map `protected_seq` encodes (mapping.md §3.1). |
| A4 | `result` returned (a `List[int]`) | `'$\\mathdefault{' + ret_text + '}$'` then `.replace('$\\mathdefault{}$', '')` then `return` | I (framing) | the wrap and empty-fragment removal are UNCHANGED framing (the wrap line merely moved after the protection; both pre- and post-patch wrap then strip). They add/remove only the fixed framing string and never touch `-` `:` ` `, so they are observationally inert with respect to the protection delta the spec pins. Confirmed by G-AX end-to-end. |

The discriminating content of the change — protecting `:` (U+003A) → `{:}` and
` ` (U+0020) → `\;` in addition to the already-protected `-` — lives in
`protect(58) == tok_colon()` and `protect(32) == tok_space()` (model) ⇔ the
`.replace(':', '{:}')` and `.replace(' ', r'\;')` steps added by the patch
(real). The pre-patch body protected only `-`; `model_prepatch.py` reproduces
that (the colon/space branch is dropped, both pass through as identity) and
**fails** the postcondition `ToSeq(Result()) == protected_seq(ToSeq(text))`,
which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the protection substitution — is modeled **deeply** (the spelled-out
per-code-point fold `protected_seq` consumed in `protect_codepoints`, step A3,
an **A-reference**), not hidden behind an axiom about the function under change.
There is **no A-consumed axiom**: the proof is self-contained over the
`List[int]`/`PSeq[int]` theory. The only kind-A relationship is the A-reference
(A3) that G-AX validates the deep model against. The unchanged regex wrapping
(A2) and the `$\mathdefault{...}$` framing + empty-fragment removal (A4) are I
framing, confirmed observationally inert by the G-AX end-to-end check.

## C. verify(model) ⇒ resolved

`protect_codepoints` verifies only if its output equals the exact per-code-point
protection with `: → {:}` and ` ` → `\;` (A3, the postcondition
`ToSeq(Result()) == protected_seq(ToSeq(text))` plus the three `protect(·)`
token clauses). By R (`str` ↔ `List[int]`) and the I framing (A2 regex, A4
wrap/strip, both unchanged), the verified protection equals the gold
`_wrap_in_tex`'s changed `.replace` chain on the tested labels; by G-AX the deep
model `protected_seq` equals the real changed operation (A-reference) and the
deep model under the unchanged framing reproduces the gold `_wrap_in_tex` exactly
on F2P-shaped labels. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited deep-model
reference — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: deep-model/operation soundness (G-AX, here the
A-reference) and refinement fidelity (this document, G-EQ).
