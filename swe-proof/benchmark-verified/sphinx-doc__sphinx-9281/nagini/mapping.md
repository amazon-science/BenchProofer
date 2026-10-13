# mapping.md — sphinx-doc__sphinx-9281

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8ec06e9a1bd862cd713b9db748e039ccc7b3e15b`, states the type
abstraction, and gives the provenance of the deep-model reference (the only
modelled callee; no consumed axiom).

Repo file under change: `sphinx/util/inspect.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `describe(value)` | `object_description(object)` — `sphinx/util/inspect.py:433` (body 435-467) | the modeled changed function (textual description of an arbitrary value) |
| `Value` (fields `kind`, `class_name`, `member_name`, `category_text`, `fallback_text`) | the runtime `object` argument, projected onto the touched observables | minimal object carrying only the category tag and the text fragments the dispatch uses |
| `enum_rendering(class_name, member_name)` *(deep model — A-reference)* | the new branch body `"%s.%s" % (object.__class__.__name__, object.name)` (`sphinx/util/inspect.py:460-461` post-patch) | pure spec: the rendering of an enumerated-type member; deep model validated `== ClassName "." MemberName` by axiom_check.py (G-AX), NOT a consumed axiom |
| `dot()` | the literal `"."` in the `"%s.%s"` format string | pure spec: the single separator code point U+002E |

The pre-patch repo control flow the change touches (for the refinement audit,
not referenced from the consumer spec view): the dispatch chain `if dict … /
if set … / if frozenset … / try: repr(object)` (`inspect.py:435-467`). The
gold patch (a) turns the bare `if isinstance(object, set)` and
`if isinstance(object, frozenset)` into `elif` (joining the dispatch chain),
and (b) inserts a new `elif isinstance(object, enum.Enum): return "%s.%s" %
(object.__class__.__name__, object.name)` before the generic `repr` fallback.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `object` argument's *category* (which `isinstance` arm fires) | `value.kind: int` tag: 0=dict mapping, 1=set, 2=frozenset, 3=`enum.Enum` member, 4=anything else | `isinstance(object, dict)` ↔ `kind==0`; `set` ↔ 1; `frozenset` ↔ 2; `isinstance(object, enum.Enum)` ↔ 3; none of those ↔ 4. The arms are mutually exclusive in the patched `if/elif` chain. |
| `str` (the returned description; the class/member names; the fragment renderings) | `List[int]` of Unicode code points (Nagini bans `str` indexing) | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; `str` `+`/`%`-join ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `object.__class__.__name__` (an `enum.Enum` member's owning-type name) | `value.class_name: List[int]` | code points of the class name |
| `object.name` (an `enum.Enum` member's own name) | `value.member_name: List[int]` | code points of the member name |
| the rendering produced by the dict/set/frozenset arms | `value.category_text: List[int]` | opaque code-point sequence: these arms are UNCHANGED by this behaviour, so their exact rendering is carried as a given (the spec only requires the patched function reproduce it on those arms) |
| `repr(object)` with memory addresses stripped (the generic fallback) | `value.fallback_text: List[int]` | opaque code-point sequence: the unchanged generic fallback; this is also what an enumerated-type member would WRONGLY have rendered as pre-patch (the ugly value-revealing form) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

**Termination (total correctness):** the real `object_description` always
answers — copying/composing the finitely many code points of the relevant
fragments (`"%s.%s"` formatting, or reproducing an already-given rendering) is
a bounded computation. The spec carries `Requires(MustTerminate(2))` on
`describe` (consumed in each copy loop by an
`Invariant(MustTerminate(<remaining count>))` measure). Nagini is a
partial-correctness verifier by default, so without the obligation a diverging
implementation would satisfy every `Ensures` vacuously while sharing the spec.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `enum_rendering` deep model ↔ `"%s.%s" % (cls.__name__, member.name)` (A-reference)
**Callee / operation:** the new branch body the gold patch adds for a member
of an enumerated type:

```python
elif isinstance(object, enum.Enum):
    return "%s.%s" % (object.__class__.__name__, object.name)
```

The changed rendering operation is modelled **deeply** by the `@Pure` function
`enum_rendering` (with `dot`) in the `pure` region; there is **no `@ContractOnly`
axiom** the proof consumes. The deep model is instead validated equal to the
real behaviour out-of-band by axiom_check.py (G-AX): for a real `enum.Enum`
member `m`, `enum_rendering(ord*(m.__class__.__name__), ord*(m.name))` equals
the code points of `"%s.%s" % (m.__class__.__name__, m.name)`.

`enum.Enum` semantics relied on:
* `member.__class__.__name__` is the owning enumeration type's name;
* `member.name` is the member's own name (a `str`);
* `"%s.%s" % (a, b)` is `a + "." + b`.

These are stable across every supported CPython (3.6–3.12). Docs:
https://docs.python.org/3/library/enum.html#enum.Enum.name . The `enum` module
is already imported at `sphinx/util/inspect.py:13`, so the new branch needs no
new import.

The discriminating content of the change: an enumerated-type member renders as
`ClassName.MemberName` (e.g. `MyEnum.FOO`) rather than the default ugly repr
`<MyEnum.FOO: 1>` (the generic `repr` fallback, `value.fallback_text`). This is
exactly the single behaviour the F2P test
`tests/test_util_inspect.py::test_object_description_enum`
(`object_description(MyEnum.FOO) == "MyEnum.FOO"`) observes.

**Soundness check (G-AX):** `axiom_check.py` constructs real `enum.Enum`
classes — the issue's own `MyEnum`/`ValueA=10` example, string-valued members,
`IntEnum`, single-member, mixed/underscored names, plus 5000 randomized
freshly-built enumerations with 1–4 members each — evaluates the real
`"%s.%s" % (cls.__name__, member.name)` formatting, and asserts it equals the
deep model `enum_rendering` on the corresponding code-point sequences. It also
checks the gold rendering differs from the ugly default `repr` (the pre-patch
fall-through). It imports only the standard-library `enum` module (the very
module the patch dispatches on); nothing repo-specific. Exit 0 iff sound.

### 3.2 The dict/set/frozenset arms and the generic fallback
These arms are **unchanged** by this behaviour. The `if`→`elif` edit only joins
them into one dispatch chain; their rendering is identical to pre-patch. The
spec carries each arm's rendering as an opaque sequence (`category_text` for the
collection arms, `fallback_text` for the generic `repr` fallback) and only
requires the patched function reproduce it on the corresponding arm — so no
axiom about `sorted`, `repr`, or `", ".join` is needed or claimed.
