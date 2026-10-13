# RELAXED_LEAKAGE — sphinx-doc__sphinx-9461

Disposition: **KEEP with relaxed leakage** (per `RELAXED_LEAKAGE.md`).
`meta.json gates.G-LEAK.status = "relaxed"`.

## The problem_statement ↔ gold mismatch

The public `problem_statement` is framed **entirely as a discovery /
docstring-extraction symptom**. Its title and body:

> "Methods decorated with @classmethod and @property do not get documented."
>
> **EDIT:** "The problem seems to be that `type(BaseClass.baseclass_property)`
> returns `property`, thus sphinx can just lookup
> `BaseClass.baseclass_property.__doc__`. However,
> `type(BaseClass.baseclass_class_property)` returns the type of the returned
> object … So Sphinx doesn't really have a chance to extract the docstring."
>
> **Expected behavior:** "Methods that are decorated with both `@classmethod`
> and `@property` should be documented appropriately."

So the public issue is about a `@classmethod @property` method **not being
discovered / having its `__doc__` extracted at all** — a recognition problem,
diagnosed as `type(...)` returning the wrong type. The stated expectation is the
generic "should be documented appropriately."

The gold patch has THREE coupled hunks across three files:

1. **Recognition / docstring-extraction half** (`sphinx/util/inspect.py`,
   `sphinx/ext/autodoc/__init__.py`): `isclassmethod` gains an MRO-walking
   branch, `getdoc` gains a classmethod-property docstring-lookup branch, and
   `PropertyDocumenter.can_document_member` / `import_object` /
   `add_directive_header` learn to discover a `classmethod`-wrapped `property`
   and emit a new `:classmethod:` directive flag. **This half is what the PS
   describes** (discovery + `__doc__`), and it is NOT modeled (live descriptor /
   MRO introspection outside Velvet's fragment; documented unmodeled in
   `mapping.md §3.2`).

2. **Rendering half** (`sphinx/domains/python.py`,
   `PyProperty.get_signature_prefix`, the **modeled** site):

   ```python
   def get_signature_prefix(self, sig):
   -    prefix = ['property']
   -    if 'abstractmethod' in self.options:
   -        prefix.insert(0, 'abstract')
   +    prefix = []
   +    if 'abstractmethod' in self.options:
   +        prefix.append('abstract')
   +    if 'classmethod' in self.options:
   +        prefix.append('class')
   +    prefix.append('property')
       return ' '.join(prefix) + ' '
   ```
   plus a new `'classmethod': directives.flag` option.

The sole F2P test that observes the modeled site —
`tests/test_domain_py.py::test_pyproperty` — asserts the rendered prefix
`"class property "` (a `desc_annotation` node) and the new `:classmethod:`
option. A faithful spec of the modeled site MUST pin: when the second
(class-method) flag is set, the token `"class"` is emitted, in the canonical
order `abstract → class → property`, with `"property"` always trailing. That is
exactly the discriminator that fails the prepatch (which seeds `['property']`
and has no second-flag branch — silently dropping the `"class"` token).

## What leaks, and why it is unavoidable

A **faithful** spec must pin the rendering-half discriminator
(`secondFlag → "class" ∈ out`, the abstract→class→property order, trailing
`"property"`), because `test_pyproperty` asserts the rendered string
`"class property "` exactly. A spec built from the public issue's stated
expectation ("documented appropriately") cannot model this site at all — it
names neither the rendered prefix, nor the `"class"` token, nor the
`:classmethod:` directive flag, nor any ordering. Such a non-pinning spec would
admit the prepatch impl (drop the second flag) which verifies yet fails the F2P
`test_pyproperty` — i.e. it would violate G-EQ / `verify ⟹ correct`. So the
second-flag-`"class"`-token clause and the canonical order are **mandatory** for
faithfulness.

But the discriminating vocabulary of that rule is absent from the public text.
Token scan against `instance.json` (`problem_statement` + `hints_text`):

| token | in `problem_statement` | in `hints_text` |
|---|---|---|
| `prefix` | **0×** | **0×** |
| `signature` | **0×** | **0×** |
| `get_signature_prefix` | **0×** | **0×** |
| `:classmethod:` (the directive flag) | **0×** | **0×** |
| `render` | **0×** | **0×** |
| `order` (canonical ordering) | **0×** | **0×** |
| `class property` (the rendered annotation) | 1× — see note below | **0×** |

**Note on the lone `class property` hit.** The single occurrence in the
`problem_statement` is inside the **code-sample docstring** of the bug repro:

```python
class A:
    @classmethod
    @property
    def f(cls):
        """Some class property."""   # <- the lone "class property" substring
        return "property"
```

It is a free-text string literal in the user's demo, NOT a specification of the
rendered signature-prefix annotation. The PS never states that the rendered
prefix should read `"class property "`, never introduces a `:classmethod:`
directive flag, and never states a token ordering. (`property`/`class`/`abstract`
appear elsewhere only as the natural-language names of the `@property`,
`@classmethod` decorators and ordinary class definitions — not as prefix
tokens.)

The `hints_text` is a short thread (a "Wow, I'll take a look" reply plus a
metaclass work-around recipe); it contains **none** of the rendering
discriminator. The rendered-prefix tokens, the `:classmethod:` flag, and the
canonical token order live ONLY in the gold diff and the hidden `test_patch`.

Therefore any faithful spec of the modeled rendering site necessarily reveals a
behavior the public task text does not contain — the leak is in the **behavior
itself** (the second-flag `"class"` token + canonical order + trailing
`"property"`), not in narration that round-1 de-narration could remove. Round 1
correctly stripped the diagnosis prose and the symbol-echoing identifiers
(`signaturePrefixTokens`→`assembleModifierTokens`,
`modifierPrefix`→`annotationTokens`; removed "prefix"/"signature"/"rendered"
vocabulary and the "subsumed/conflated/not ignored" narration), and the
re-audit confirmed that work was done — yet leakage persisted because the
disclosure is the *behavioral discriminator*, and no `problem_statement`-derivable
reformulation models the gold rendering fix. This is precisely the condition
`RELAXED_LEAKAGE.md` accepts.

## Why this is the rendering half, not the PS's recognition half

The PS-described behavior (discover a `@classmethod @property`; extract its
`__doc__`) is the **recognition half** — the two unmodeled introspection files.
Modeling that half is what is genuinely PS-grounded, but it is reflection over
live class objects / the descriptor protocol / `getmro` / `__dict__` /
`__func__`, outside Velvet's expressible fragment, and would be unsound to
axiomatize (changed functions, SPEC_GUIDE directive 7). So the only
cleanly-expressible F2P-relevant site is the **rendering half** — and the
rendering half is exactly the part of the gold the PS does not raise. The bundle
models the expressible site and discloses (`mapping.md §3.2`, `refinement.md`)
that the recognition co-changes are unmodeled but shipped verbatim in
`patch.diff` so all three F2P tests resolve (G-RESOLVE). This is the standard
multi-site honesty pattern (precedent: sphinx-7590, sphinx-10673,
sphinx-8265 RELAXED).

## Requirements check (RELAXED_LEAKAGE.md §29)

1. **Core is sound.** G-VERIFY pass (`Solution.lean` exit 0, 3s); G-DIFF fail —
   the prepatch (seed `["property"]`, only the first flag prepends, no
   second-flag branch) fails on exactly `ensures_2`
   (`secondFlag = true → "class" ∈ out`) and `ensures_3`
   (`out = annotationTokens firstFlag secondFlag`) — the dropped class-method
   token, the actual gold bug — re-verified this round (unsolved goals on both
   the `firstFlag` and `¬firstFlag` cases of the `secondFlag` clauses). G-EQ
   sound + tight (exact-equality pin to the fully-concrete pure function
   `annotationTokens`; 7 wrong impls all `same_spec=True` and rejected for the
   right clauses; structurally-different correct positive control verifies; no
   ungrounded oracle — `annotationTokens` is a spelled-out `if/then/else ++`
   string-list computation over the two boolean inputs, not an opaque answer
   key, directive 8); G-AX vacuous (no axioms / `sorry` / `admit` / `Classical`;
   the only library op is the unchanged `' '.join + ' '`, an R/I identity);
   G-CONF runs an all-R/I shadow and agrees with the REAL patched
   `PyProperty.get_signature_prefix` over the 4 flag combos × 10⁵ fuzz, 0
   disagreements (seed 9461); **G-RESOLVE**: `patch.diff` == gold verbatim,
   harness resolves all three F2P.
2. **The leak is genuinely unavoidable**, established above: the rendering
   discriminator (`prefix`/`signature`/`get_signature_prefix`/`:classmethod:`/
   `render`/`order` all 0× in PS AND 0× in `hints_text`; the lone `class property`
   hit is a code-sample docstring, not a prefix spec) is present only in
   gold / `test_patch`. The PS's framing is the orthogonal recognition /
   docstring-extraction symptom, modeled by the unmodeled introspection half.
3. **Documented in-bundle** (this file); `meta.json gates.G-LEAK.status =
   "relaxed"` points here. The mechanical lexical G-LEAK screen still passes (the
   spec view names no patched path/symbol — `get_signature_prefix`, `PyProperty`,
   `classmethod`, `self.options`, the files — and uses only generic identifiers
   `annotationTokens`, `assembleModifierTokens`, `firstFlag`, `secondFlag`); the
   leak is semantic, as the policy expects.

## Scope of what is disclosed

The spec view discloses: an ordered list of optional annotation tokens built
from two independent boolean flags — the first contributes `"abstract"`, the
second contributes `"class"`, with an always-present trailing `"property"`, in
the fixed order abstract → class → property. Nothing about the patched files,
the `get_signature_prefix` / `PyProperty` / `PropertyDocumenter` / `isclassmethod`
/ `getdoc` symbols, the `self.options` dict-membership mechanism, the
`:classmethod:` directive flag, the descriptor/MRO introspection, or the
three-file multi-site refactor is named in the spec view.
