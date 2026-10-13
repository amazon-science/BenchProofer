# mapping.md — sphinx-doc__sphinx-9698

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f050a7775dfc9000f55d023d36d925a8d02ccfa8`, states the type
abstraction, and gives the provenance of the deep model (the changed operation
is modelled deeply; there is no consumed axiom).

Repo file under change: `sphinx/domains/python.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `get_member_index_text(methname, clsname, option)` | `PyMethod.get_index_text(self, modname, name_cls)` — `sphinx/domains/python.py:784` (the four-way role branch, body lines 795-803) | the modeled changed function (builds the member's index label) |
| `index_label(methname, clsname, option)` *(deep model — A-reference)* | the role branch's `_('<template>') % (methname, clsname)` substitution (`python.py:795-803`) | pure spec: the full label as a code-point sequence |
| `index_prefix(methname, option)` | the label up to and including the qualifier-group opening `' ('` | pure proof helper (class-name loop invariant) |
| `role_suffix(option)` | the role word + leading space + trailing `')'` in each template | pure spec: per-role suffix |
| `call_marker()` | the empty-call marker `()` literal in the callable-role templates | pure spec: `PSeq(40, 41)` |
| `group_open()` | the `' ('` literal beginning the qualifier group | pure spec: `PSeq(32, 40)` |
| `is_callable_role(option)` | the branch selection: the marker `()` is present for classmethod/staticmethod/plain-method and absent for the property role | pure spec: `option != 2` |

### The role selector ↔ `self.options`

`PyMethod.get_index_text` selects its template by inspecting `self.options`:

```python
if 'classmethod' in self.options:   return _('%s() (%s class method)')  % (methname, clsname)
elif 'property' in self.options:    return _('%s() (%s property)')      % (methname, clsname)  # base_commit (buggy), python.py:798-799
elif 'staticmethod' in self.options:return _('%s() (%s static method)') % (methname, clsname)
else:                               return _('%s() (%s method)')        % (methname, clsname)
```

The model collapses `self.options` to the integer `option`:

| `option` | `self.options` membership | role | template (post-patch) |
|---|---|---|---|
| 0 | none of the three | plain method | `'%s() (%s method)'` |
| 1 | `'classmethod'` | class method | `'%s() (%s class method)'` |
| 2 | `'property'` | **property (non-callable)** | `'%s (%s property)'` — **no `()`** (the fix) |
| 3 | `'staticmethod'` | static method | `'%s() (%s static method)'` |

The pre-patch property template is `'%s() (%s property)'` — it carries the
spurious `()` that the patch removes. `model_prepatch.py` reproduces that
(emits `()` for the property role too) and fails the spec (§ refinement.md).

The `name.rsplit('.', 1)` split into `(clsname, methname)` and the
`ValueError`/`modname` fallbacks (`python.py:786-794`) are upstream of and
unchanged by the fix; the model takes the already-split `methname` and
`clsname` as inputs (the carriers the tested branch consumes).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`methname`, `clsname`, the returned label) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `_(template)` gettext lookup (`python.py:796-803`) | identity on the template (omitted) | with no translation catalogue loaded (the test/build environment), `_(t)` returns `t` unchanged; the F2P test compares the literal English label. Modeled as the identity on the template code points. |
| `template % (methname, clsname)` substitution | sequence concatenation `methname ++ … ++ clsname ++ …` | the template has exactly two `%s` placeholders, filled by `methname` then `clsname`, with the surrounding literals (`()`, `' ('`, role word, `')'`) as constant code-point sequences |
| `self.options` (a `Dict[str, Any]`) | the integer selector `option ∈ {0,1,2,3}` | the four mutually-exclusive role branches (the directive sets at most one of `classmethod`/`property`/`staticmethod`; none ⇒ plain method) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

| the real `get_index_text` always returns (straight-line template splice; no loops, no recursion) | `Requires(MustTerminate(2))` + per-loop `Invariant(MustTerminate(len(...) - idx + 1))` measures | Nagini is a partial-correctness verifier by default; the obligation makes divergence a verification failure, matching the real operation's trivial totality. Without it, an implementation that loops forever before a wrong return satisfies the value postconditions vacuously while hanging the index build and the F2P test. |

## 3. Deep model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `index_label` deep model ↔ the patched label construction
**Real operation:** the patched member-role branch of `PyMethod.get_index_text`,
i.e. `_('<template>') % (methname, clsname)` with the post-patch templates of
§1. The changed string operation is modelled **deeply** by the `@Pure`
concatenation `index_label` (with `role_suffix`/`call_marker`/`group_open`/
`is_callable_role`) in the `pure` region; there is **no consumed `@ContractOnly`
axiom**. The deep model is validated equal to the real label out-of-band by
`axiom_check.py` (G-AX).

Why the `_()` and `%` steps are sound R-refinements: `_()` is gettext's
`gettext`, which returns its argument verbatim when no catalogue provides a
translation — the case in every test in the F2P/P2P set (no `.mo` files are
installed, the rendered label is the English template). `%`-substitution with
two positional `%s` and no width/precision/format flags is exactly the in-order
splice of the two name strings into the constant template — i.e. sequence
concatenation. Hence `index_label(methname, clsname, option)` equals
`_(template[option]) % (methname, clsname)` on code points.

The discriminating content of the change — the property role's label has **no
`()`** after the member name — lives in `is_callable_role(2) == False` (model)
⇔ the template becoming `'%s (%s property)'` (real). G-AX asserts
`index_label == real label` on boundary + fuzz names for all four roles, and
that the empty-call marker `()` follows the member name **exactly** for the
callable roles.

**Soundness check (G-AX):** `axiom_check.py` substitutes the post-patch
templates (the real oracle in the no-translation case) for a cartesian product
of 20 boundary member/class names × 4 roles (1600 cases) plus 20000 randomized
fuzz names, and asserts the deep model `index_label` equals the real label and
that the `()`-after-name discriminator matches `is_callable_role`. It also
drives the **real** `PyMethod.get_index_text` (when `sphinx` is importable):
in-container with `patch.diff` applied this validates all four roles directly;
on a pre-patch host it validates the three callable roles (unchanged by the
patch) and defers the property role to the patched run. It imports only the
standard library plus `sphinx` (best-effort); exit 0 iff sound.

## 4. No consumed axioms

The `axioms` region of `model.py` is empty (a comment). The only kind-A artefact
is the **A-reference** of §3.1 — the deep model validated against the real label
by G-AX — not a `@ContractOnly` the proof consumes. There is no `@ContractOnly`
in this bundle, hence no dead axiom.
