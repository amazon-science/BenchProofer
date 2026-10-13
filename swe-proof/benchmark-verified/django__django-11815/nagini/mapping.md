# mapping.md — django__django-11815

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e02f67ef2d03d48128e7a118bf75f0418e24e8ac`, states the type
abstraction, and gives the provenance of each deep-model reference (callee
source + the exact behaviour the deep model is validated against).

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `serialize_member(module, class_name, identifier, payload)` | `EnumSerializer.serialize(self)` — `django/db/migrations/serializer.py:120` (body lines 121-125) | the modeled changed function (the enum-member serializer) |
| `rendered(module, class_name, identifier)` *(deep model — A-reference)* | the post-patch format string `'%s.%s[%r]' % (module, enum_class.__name__, self.value.name)` (`serializer.py:121-124` post-patch) | pure spec: the rendered fragment, keyed by the stable identifier |
| `quoted(tok)` *(deep model — A-reference)* | the `%r` conversion applied to `self.value.name` inside that format string (CPython `repr` of a simple identifier `str`) | pure spec: a plain identifier token wrapped in single quotes |
| `import_line(module)` *(deep model — A-reference)* | the lone import `'import %s' % module` of the post-patch `{'import %s' % module}` import set (`serializer.py:124` post-patch) | pure spec: the one accompanying import statement |
| `Requires(MustTerminate(2))` | the real `serialize()` body — a single straight-line format expression that always returns (no loop/recursion) | total-correctness obligation: the modeled function must terminate. Closes the partial-correctness hole (a same-spec impl that diverges before returning would otherwise verify vacuously while its faithful patch hangs the F2P tests; found by the P2 audit) |
| `plain_token_char(c)` + `Requires(Forall(... plain_token_char(identifier[k])))` | the domain of `self.value.name`: an enum member name is a class attribute name, always matching `[A-Za-z_][A-Za-z0-9_]*` | domain-scoping precondition: the modeled slice covers exactly the identifiers on which the `quoted` deep model equals the real `%r` rendering (CPython `repr` of such a string is the bare single-quote wrap — no escaping, no delimiter switch). Names outside this alphabet (a quote/backslash in the name, reachable only via the enum functional API, never via a class-body declaration) are outside the precondition, so the spec makes no claim about them. Added after a P2 audit exhibited the divergence `repr("a'b") != "'" + "a'b" + "'"` on such an out-of-alphabet name |

The four `serialize_member` parameters bind to the data the real method reads
from `self.value` (the enum member) and `self.value.__class__`:

| model.py parameter | real source (`EnumSerializer.serialize`) |
|---|---|
| `module` | `enum_class.__module__` where `enum_class = self.value.__class__` |
| `class_name` | `enum_class.__name__` |
| `identifier` | `self.value.name` — the enum member's **stable** declared name |
| `payload` | a renderable form of `self.value.value` — the member's **mutable** payload (the pre-patch code serialized this via `serializer_factory(self.value.value).serialize()`); supplied to the model only to witness that the post-patch output does NOT depend on it |

The pre-patch repo expressions the change removes (for the refinement audit,
not referenced from the consumer spec view): the body line
`v_string, v_imports = serializer_factory(self.value.value).serialize()`
(`serializer.py:123`), the import union `{'import %s' % module, *v_imports}`
(`serializer.py:124`), and the by-payload return
`"%s.%s(%s)" % (module, enum_class.__name__, v_string)` (`serializer.py:125`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`module`, `enum_class.__name__`, `self.value.name`, and the rendered fragment) | `List[int]` of Unicode code points | `s[k]` ↔ `cps[k] == ord(s[k])`; `len(s)` ↔ `len(cps)`; `str` concatenation / `%`-splice of whole strings ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`len`/`[i]` mirror `str` `+`/`len`/index |
| the method's return value, a 2-tuple `(string, imports)` | `Tuple[List[int], List[int]]` — `(fragment, import_line)` | the `string` first element refines as the `str`↔`List[int]` row above; the `imports` set is a one-element set `{'import %s' % module}`, refined as its single member rendered to code points (`Result()[1]`). The set wrapper is the identity on its single element for the F2P comparison (`assertSerializedResultEqual` compares `(string, {'import module'})` exactly). |
| the `%r` conversion of the member name (`'%s.%s[%r]'`) | `quoted`: wrap in U+0027 | sound because an enum member name is always a valid Python identifier (letters/digits/underscore, never a leading digit, no quote/backslash/control char), whose `repr` is exactly the single-quoted form (mapping.md §3.1; G-AX). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The whole rendering is the
function under change, so it is modelled **deeply** (spelled out in the `pure`
region and the verified impl), and its equality to the real post-patch
serializer output is validated out-of-band by `axiom_check.py` (G-AX). Three
A-references:

### 3.1 `quoted` ↔ `repr` of a simple identifier name (A-reference)
**Callee:** CPython `repr(str)` via the `%r` conversion. The gold patch renders
the member name with `'%s.%s[%r]' % (..., self.value.name)`. An enum member
name is, by the language rules for class attribute names, always a valid Python
identifier: it matches `[A-Za-z_][A-Za-z0-9_]*`, contains no single quote,
backslash, or control character, and is non-empty. For such a string CPython's
`repr` chooses single-quote delimiters and performs no escaping, so
`repr(name) == "'" + name + "'"` — exactly what `quoted` encodes
(`PSeq(39) + tok + PSeq(39)`). Docs: the F2P targets observe
`['A']`, `['B']`, `['DOTALL']`. G-AX asserts `quoted(name) == repr(name)` over
the real F2P member names plus 20 000 randomized valid-identifier names.

### 3.2 `rendered` ↔ the post-patch format string (A-reference)
**Callee:** the gold-patch f-string
`'%s.%s[%r]' % (module, enum_class.__name__, self.value.name)`. With
`%r(name) == "'name'"` (§3.1) this is exactly
`module ++ "." ++ class_name ++ "[" ++ "'identifier'" ++ "]"`, which is what
`rendered` encodes. G-AX reconstructs the real post-patch
`EnumSerializer.serialize` formatting and asserts the deep model reproduces the
string code point for code point, over the real F2P enums (TextEnum, BinaryEnum,
IntEnum, `re.RegexFlag`) and synthesised enums over the fuzz identifier names.

### 3.3 `import_line` ↔ the post-patch import (A-reference)
**Callee:** the post-patch import set `{'import %s' % module}` — a singleton.
`import_line` encodes its single element as `"import " ++ module`
(`PSeq(105,109,112,111,114,116,32) + module`). The post-patch code drops the
pre-patch `*v_imports` (the imports the payload serialization contributed),
so the set is exactly the module import. G-AX asserts the real post-patch
import set has exactly one element equal to `import_line(module)`.

**Soundness check (G-AX):** `axiom_check.py` reconstructs the gold-patch
post-patch formatting (the two f-strings) and runs CPython `repr` on real enum
member names, asserting `quoted`/`rendered`/`import_line` reproduce the real
string and import code point for code point over the real F2P enums + 20 000
fuzz identifier names + synthesised enums. It imports only the standard library
(`enum`, `re`, `keyword`, `random`); nothing repo-specific. Exit 0 iff sound.

## 4. F2P coverage note

Both FAIL_TO_PASS tests exercise this single changed function:
`test_serialize_enums` (TextEnum/BinaryEnum/IntEnum, directly and inside
`models.CharField`/`IntegerField` choices+default) and
`test_serialize_class_based_validators` (`re.RegexValidator(..., flags=re.S)`,
whose `re.RegexFlag(16)` is an `enum.IntFlag` routed through
`EnumSerializer` because `enum.Enum` is the registered base — observed as
`re.RegexFlag['DOTALL']`). Both observe the name-keyed `Class['NAME']` form and
the singleton `{'import module'}` import set.
