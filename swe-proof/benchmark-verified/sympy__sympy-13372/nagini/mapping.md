# mapping.md — sympy__sympy-13372

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 30379ea6e225e37833a764ac2da7b7fadf5fe374`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/core/evalf.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_evalf_result(re_kind, im_kind, prec)` | the fallback block of `evalf(x, prec, options)` — `sympy/core/evalf.py:1284` (the `except KeyError:` body, lines 1298-1310, ending at `r = re, im, reprec, imprec`) | the modeled changed function: classify the real and imaginary parts and assemble the precision components, deferring when a part is neither exact-zero nor a number |
| `re_kind` | the classification of `re` (the real part, `re, im = xe.as_real_imag()`): `0` ↔ `re == 0`; `1` ↔ `re.is_number`; `2` ↔ neither | per-part case tag |
| `im_kind` | the classification of `im` (the imaginary part): `0` ↔ `im == 0`; `1` ↔ `im.is_number`; `2` ↔ neither | per-part case tag |
| `prec` | the `prec` argument of `evalf` (the working precision passed to `_to_mpmath`) | working precision |
| `EvalfResult.reprec` | the local `reprec` (third component of `r = re, im, reprec, imprec`) | real-part precision component (`None` for exact zero, `prec` for a number) |
| `EvalfResult.imprec` | the local `imprec` (fourth component of `r`) | imaginary-part precision component |
| `part_precision(kind, prec)` | the `reprec`/`imprec` assignment in the `if/elif` chains (`None` for `== 0`, `prec` for `is_number`) | pure spec: the precision component a part's case yields |
| `EvalfDeferred` (exception) | `raise NotImplementedError` (the added `else` branches, and the surrounding `except`-driven fallback) | the deferral signal |

The pre-patch repo behaviour the change fixes (for the refinement audit): the
two `if re == 0 / elif re.is_number` and `if im == 0 / elif im.is_number`
chains have NO `else` branch, so when `re` (resp. `im`) is neither the exact
zero nor a number, `reprec` (resp. `imprec`) is never assigned, and the next
statement `r = re, im, reprec, imprec` reads the unset local — `UnboundLocalError:
local variable 'reprec' referenced before assignment`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a part `re`/`im` (a SymPy expression) and its three-way classification (`== 0`, `.is_number`, neither) | an integer case tag `re_kind`/`im_kind ∈ {0, 1, 2}` | `0` ↔ `part == 0` (the `if part == 0` branch); `1` ↔ `part.is_number` and `part != 0` (the `elif part.is_number` branch); `2` ↔ neither (the missing/added `else`). The three cases are mutually exclusive and exhaustive on the branch chain. |
| the local `reprec`/`imprec` (`None`, or `prec`, or unset) | `Optional[int]` (`None`, or `prec`) | absent precision ↔ `None`; numeric precision ↔ the integer `prec`. The pre-patch "unset" state has no representable value — that is exactly the bug, modeled as the result being assembled around an undefined component (a postcondition the prepatch cannot establish). |
| the result tuple `r = re, im, reprec, imprec` | the `EvalfResult` object carrying only the two TOUCHED precision components `reprec`, `imprec` | the bug and the fix concern only the precision components (`reprec`/`imprec`); the value components (`re`/`im`) are independently assigned in the same branches and are not the source of the unbound read. The minimal class carries only the touched fields (SPEC_GUIDE §2 rich-object rule). |
| `raise NotImplementedError` | `raise EvalfDeferred()` | a builtin exception in an `Exsures` crashes the Nagini translator (SPEC_GUIDE §2 / banned list), so the deferral is a user-defined exception. The discriminating observable is the *deferral* (an exception that the surrounding `except`/fallback handles) rather than the un-fixed `UnboundLocalError`; the stand-in preserves that the function defers instead of assembling a bad result. |

`str` is not involved; the carrier is integer case tags and `Optional[int]`
precision components.

## 3. Callee provenance

**No `@ContractOnly` axiom is consumed and no deep-model A-reference is
checked.** The fix is a pure control-flow / definedness change over data the
function already holds: it adds the `else: raise NotImplementedError` branch so
that a part which is neither the exact zero nor a number defers rather than
falling through to read an unset precision local. The per-part precision
selection (`None` for `== 0`, `prec` for `.is_number`) is concrete integer
control flow, modeled DIRECTLY by `part_precision` and the `if/elif/else`
chains — there is no unchanged opaque callee whose behaviour the proof depends
on.

The repo callees that the surrounding fallback invokes — `x._eval_evalf`,
`as_real_imag`, `expr == 0`, `expr.is_number`, `_to_mpmath` — are UNCHANGED by
the patch and are not part of the modeled behaviour: the bug is purely that the
classification chain lacked an `else`, leaving `reprec`/`imprec` unbound. The
model abstracts the *outcome* of the classification (`re_kind`/`im_kind`) and
pins the precision-component assignment plus the must-defer obligation, which
is the entirety of the changed delta. Hence `axiom_check.py` has no axiom to
fuzz; it instead validates the modeled three-way classification ↔ precision
mapping against the documented semantics (G-AX records SOUND with no consumed
axiom).
