# mapping.md — django__django-10880

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 838e432e3e5519c5383d12018e6c78f8ec7833c1`, states the type
abstraction, and gives the provenance of the deep-model reference.

Repo file under change: `django/db/models/aggregates.py`. Co-located render
mechanism: `django/db/models/expressions.py` (`Func.as_sql`, the template
substitution that turns the modifier value into the rendered SQL string).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_fragment(function, operands, distinct)` | the rendering of a set-reducing query function: the `distinct` value set in `Aggregate.as_sql` (`django/db/models/aggregates.py:70-71`) consumed by the inherited `Func.as_sql` template `'%(function)s(%(distinct)s%(expressions)s)'` (`django/db/models/expressions.py:621-622`, with the class template at `aggregates.py:17`) | the modeled changed behaviour (rendered SQL fragment) |
| `modifier(distinct)` *(deep model — A-reference)* | `extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''` (`aggregates.py:71` post-patch) | pure spec: the leading modifier value placed after `(`; the changed value |
| `fragment(function, operands, distinct)` *(deep model — A-reference)* | `template % data` in `Func.as_sql` (`expressions.py:621-622`) with the class template (`aggregates.py:17`) | pure spec: the whole rendered fragment; validated `fragment == template % data` by axiom_check.py (G-AX), NOT a consumed axiom |
| `kw_distinct()` | the keyword literal `DISTINCT` inside `'DISTINCT '` | pure spec: keyword as code points `[68,73,83,84,73,78,67,84]` |
| `sep()` | the trailing space inside `'DISTINCT '` | pure spec: the separator code point `32` (U+0020) — the entire content of the fix |
| `open_paren()` / `close_paren()` | the literal `(` / `)` in the template | pure spec: `[40]` / `[41]` |

The pre-patch repo value the change corrects (for the refinement audit, not
referenced from the consumer spec view): `extra_context['distinct'] =
'DISTINCT' if self.distinct else ''` (`aggregates.py:71`, the keyword without a
trailing separator).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`%(function)s` value, the function keyword) | `List[int]` of code points | `s[k]` ↔ `function[k] == ord(s[k])`; `len(s)` ↔ `len(function)`; `str` concat ↔ list `+` / `append`; `""` ↔ `[]` |
| `str` (`%(expressions)s` value, the already-compiled operand text e.g. `CASE WHEN ...`) | `List[int]` of code points (`operands`) | same as above; abstracts the operand text the compiler has already produced |
| `self.distinct` (`bool`) | `bool` (`distinct`) | identical |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Reference-callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `fragment` / `modifier` deep model ↔ the template percent-substitution
**Operation:** the printf-style substitution `template % data` performed by
`Func.as_sql` (`django/db/models/expressions.py:621-622`):

```python
data['expressions'] = data['field'] = arg_joiner.join(sql_parts)
return template % data, params
```

with the class template (`django/db/models/aggregates.py:17`):

```python
class Aggregate(Func):
    template = '%(function)s(%(distinct)s%(expressions)s)'
```

and the modifier value (`aggregates.py:70-71`, post-patch):

```python
def as_sql(self, compiler, connection, **extra_context):
    extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''
    ...
    return super().as_sql(compiler, connection, **extra_context)
```

Because the template is a fixed-order substitution of three named fields with
two literal parentheses, `template % data` is exactly the concatenation
`function + "(" + distinct + expressions + ")"`. With `distinct = 'DISTINCT '`
this is precisely `fragment`/`modifier` in model.py. There is **no consumed
axiom**; the deep model is validated equal to the real operation out-of-band:
axiom_check.py runs the REAL `template % data` (the Python `%`-operator, stdlib)
and asserts `fragment(function, operands, distinct) == template % data` on 56
boundary inputs (every function keyword × operand shape × both modes) plus
20000 randomized fuzz inputs in both modes, and asserts the separation
guarantee (when `distinct`, the code point after `DISTINCT` is the space).

**Flag/config dependency:** the soundness holds for the post-patch modifier
value `'DISTINCT '` and the `Aggregate` template `'%(function)s(%(distinct)s
%(expressions)s)'` (no space between `%(distinct)s` and `%(expressions)s` in
the template — the separator is supplied by the modifier value, which is the
fix). axiom_check.py pins exactly this template and value.

No stdlib library callee is consumed; `Func.as_sql`/`Aggregate.as_sql` is the
function under change (the very `as_sql` the patch edits), so it is modeled
deeply, never axiomatized. The `axioms` region of model.py is empty.
