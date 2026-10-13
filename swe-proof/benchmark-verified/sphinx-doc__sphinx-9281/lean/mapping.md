# mapping.md — sphinx-doc__sphinx-9281

## Symbol binding (file:line @ base_commit 8ec06e9a1bd862cd713b9db748e039ccc7b3e15b)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_describeValue` / `problem_spec_describeValue` / `correct_describeValue` | `object_description(object: Any) -> str` — the value→display-text routine | `sphinx/util/inspect.py:433-468` @ base_commit (the added branch lands at 460-462 post-patch) |
| `PyValue.enumMember className memberName` | a PLAIN `enum.Enum` member `object` — one that is not itself a `dict`/`set`/`frozenset` instance (i.e. not a container-mixin enum member), with `object.__class__.__name__` and `object.name` | the new `elif isinstance(object, enum.Enum)` branch (`inspect.py:460` post-patch), which such a value reaches because it fails every earlier `isinstance` guard |
| `PyValue.other _` | any other value: a non-enum value, OR an enum member that IS a `dict`/`set`/`frozenset` instance (container-mixin enum) and is therefore captured by an earlier branch of the `elif` chain before the enum branch is consulted | the `dict`/`set`/`frozenset` branches (`inspect.py:434-459`) and the fall-through to the `repr(object)` tail (`inspect.py:463-468`) |
| `legacyDescription obj` | the value **the POST-PATCH `object_description` produces for `object` when `object` itself does not take the new enum branch**: the `dict`/`set`/`frozenset` dedicated renderings — each of which joins `object_description(...)` of the values it holds, so the values it holds are rendered by the post-patch routine, the new enum branch included — plus the `repr`-based tail (`s = repr(object); s = memory_address_re.sub('', s); return s.replace('\n', ' ')`). For an `other`-kind value this IS `object_description(object)` post-patch (top-level dispatch never reaches the enum branch for such a value), so the `other` clause is TAUTOLOGICAL against the reference and cannot diverge from it. For an `enumMember`-kind value it is the `repr` tail — the display such a member gets when the new branch is not applied to it, which is also its pre-patch display (a plain enum member matches no container guard, so pre-patch it fell straight to the tail) | `inspect.py:434-468` read post-patch, with the top-level enum branch (`:460-462`) not taken |
| `className ++ "." ++ memberName` | `"%s.%s" % (object.__class__.__name__, object.name)` | `inspect.py:461` post-patch |

`memberName` binds to the TEXT `%s` formats from `object.name`, not to an
assertion that `object.name` is a `str`: for a canonical member that text is the
member's name; for a composite `Flag` value on an interpreter where `.name` is
absent, `%s` renders it as the text `None` and the model carries that text
(measured below). The model therefore makes no interpreter-version claim about
`.name`.

The modeled behaviour is the new dedicated rendering of a plain `enum.Enum`
member in `object_description` — the only rendering the patch ADDS, and the only
behaviour the FAIL_TO_PASS test (`test_object_description_enum`) observes. It is
NOT the only text the patch changes: because the container branches join
`object_description(...)` of the values they hold, the new display also reaches
any `dict`/`set`/`frozenset` that holds a plain enum member, at any depth. That
propagation is carried whole inside `legacyDescription` (whose denotation above
is the post-patch routine's own output) rather than pinned clause-by-clause —
a deliberate granularity boundary, stated in refinement.md and measured below.

### What the patch does (post-patch `object_description`)

```python
def object_description(object: Any) -> str:
    if isinstance(object, dict):
        ...            # return "{...}"  (sorted items)  — unchanged
    elif isinstance(object, set):
        ...            # return "{...}"  (sorted values) — unchanged
    elif isinstance(object, frozenset):
        ...            # return "frozenset({...})"        — unchanged
    elif isinstance(object, enum.Enum):                  # <-- ADDED
        return "%s.%s" % (object.__class__.__name__, object.name)
    try:
        s = repr(object)                                 # general-purpose tail — unchanged
    except Exception as exc:
        raise ValueError from exc
    s = memory_address_re.sub('', s)
    return s.replace('\n', ' ')
```

Two things change in the diff:

1. **The added `enum.Enum` branch** — an enum member is rendered as
   `f"{object.__class__.__name__}.{object.name}"`, i.e. `Class.Member`, instead
   of falling through to `repr(object)` (which for an enum yields the ugly
   `<Class.Member: value>`). This is the observable fix.
2. **`if` → `elif`** on the `set` and `frozenset` branches, which lets the new
   enum branch hang off the chain. Note that the kinds are NOT pairwise
   disjoint in Python: an enum class may mix in `dict`/`set`/`frozenset`
   (e.g. `class FZ(frozenset, enum.Enum)`), and such a member satisfies BOTH
   `isinstance(object, frozenset)` and `isinstance(object, enum.Enum)`. Because
   the container branches PRECEDE the enum branch in the `elif` chain, a
   container-mixin enum member is rendered by its container branch and never
   reaches the new enum branch — including when its container branch FALLS
   THROUGH (unsortable values), where the `elif` chain skips the enum test
   altogether and the value lands on the `repr` tail (measured below:
   `UNSORT.Y`). Only a **plain** enum member (one failing all the earlier
   container guards) receives the new `Class.Member` display.

   What is NOT true of a container-mixin enum member is that its DISPLAY TEXT is
   the same as pre-patch: its container branch joins `object_description(...)` of
   the values it holds, so if it holds plain enum members the text changes with
   the patch (measured below: `FZE.X`). The invariant the model rests on is the
   dispatch one — such a member is displayed by its container rendering, not by
   the new branch — and `legacyDescription` denotes that container rendering as
   the POST-PATCH routine computes it, so the model asserts nothing about
   pre-patch text for `other`-kind values.

### Lean modeling

- `PyValue` is the value being rendered, modeled at exactly the granularity the
  fix distinguishes: a **plain enum member** (`enumMember className memberName`,
  carrying the two string components the new branch reads —
  `object.__class__.__name__` and `object.name`; "plain" = not itself a
  `dict`/`set`/`frozenset` instance, so it reaches the new branch) versus **any
  other value** (`other tag`, an opaque value identified by a `Nat` tag). The
  `other` kind covers non-enum values AND container-mixin enum members: the
  dict/set/frozenset branches precede the enum branch in the `elif` chain and
  capture a container-mixin enum member before the enum test is consulted, so
  such a member is displayed by its container rendering rather than by the new
  branch.
- `legacyDescription : PyValue → String` (`opaque`) is the display the POST-PATCH
  routine produces for a value that does not itself take the new enum branch:
  the dedicated dict/set/frozenset renderings (each joining the post-patch
  display of every value it holds) plus the `repr` + memory-address scrub +
  newline-flattening tail. For an `other`-kind value that is exactly
  `object_description(object)` as shipped, which is why the `other` clause is
  tautological against the reference — it pins the result to the routine's own
  output and so cannot be over-strong. The proof consumes **no** property of it:
  for the `other` kind the spec pins the result to `legacyDescription obj` by
  definition, and for the `enumMember` kind the spec does not mention it. It is
  therefore a bare `opaque` carrier with no `_prop` axiom. It is defined on every
  `PyValue` (including plain enum members) so that the prepatch impl — which
  applies it unconditionally — is well-typed; on a plain enum member its value is
  the `repr` tail, which is both "the display with the new branch not applied"
  and (for such a member specifically) its real pre-patch display.
- **Disclosed granularity boundary.** The model's carrier distinguishes exactly
  the TOP-LEVEL dispatch decision. The same dispatch also runs on the values a
  container holds (the container branches join `object_description(...)` of their
  elements), and the patch changes those inner displays too; `PyValue.other`'s
  `Nat` tag cannot express "a container that holds a plain enum member", so that
  propagation is not pinned clause-by-clause — it is carried inside
  `legacyDescription`'s denotation. Consequences, stated plainly: (i) the spec
  makes no false claim, because the carrier denotes the post-patch output; (ii)
  the spec does not FORCE the propagation, so an implementation that produced the
  new display only at top level would still satisfy it. (ii) does not weaken
  `verify ⟹ resolved`: `test_object_description_enum` observes the top-level case
  only, and no test in `tests/test_util_inspect.py` renders a container holding
  an enum member, so the propagation is unobserved by the harness. It is recorded
  here rather than left implicit because an undisclosed asymmetry is a defect
  even when it is harmless.
- **Totality vs the routine's partiality (unchanged paths).** The spec is total:
  it relates every `PyValue` to a `String`. The real routine is not total on
  `other`-kind inputs — a `repr` that raises is re-raised as
  `raise ValueError from exc`, and the `set`/`frozenset` branches catch only
  `TypeError` from `sorted(...)`, so an element whose comparison raises anything
  else propagates out. None of those paths is touched by the patch and all of
  them sit inside `legacyDescription`, which asserts no text; `PyValue.other`'s
  `Nat` is an identity tag for a value that HAS a display, not a claim that every
  Python object has one. The model therefore contradicts no reference behaviour,
  but it does not model the raising paths either — stated here for the same
  reason as the granularity boundary above.
- `className ++ "." ++ memberName` is `"%s.%s" % (cls_name, member_name)`:
  string concatenation of the class name, a literal `"."`, and the member name.
  This is total and assumes nothing about the strings (any class/member name,
  including ones containing dots or empty strings, maps identically).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `object` is a plain `enum.Enum` member (not a `dict`/`set`/`frozenset` instance) with `object.__class__.__name__ == C` and `"%s" % object.name == M` | `PyValue.enumMember C M` | string identity on the two components. |
| `object` is any other value — non-enum, or a container-mixin enum member (display = the container branch that captures it) | `PyValue.other tag` | identified by an opaque `Nat` tag; its display is `legacyDescription`. |
| `"%s.%s" % (C, M)` | `C ++ "." ++ M` | identical concatenation. |
| `object_description(object)` for an `object` that does not take the new enum branch (container rendering or `repr` tail, post-patch) | `legacyDescription obj` | opaque equality only. |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The fix's behaviour — render an
  enum member as `Class.Member`, otherwise defer to the existing routine — is
  modeled DEEPLY: the enum branch is spelled out as the concatenation
  `className ++ "." ++ memberName`, and the non-enum branch is the opaque
  `legacyDescription`. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed op, so there is no consumed axiom. `legacyDescription` carries no
  `_prop` axiom (the proof consumes no property of it — for `other` it appears
  verbatim on both sides of the spec equation, for `enumMember` it is absent),
  so it is neither A-consumed nor A-reference. **G-AX skips.**
- `repr`, `memory_address_re.sub`, `str.replace` (the general-purpose tail) are
  **unchanged** by the patch; they are folded into the opaque
  `legacyDescription`. Their omission constrains no free output component — the
  spec pins the `other` result to `legacyDescription obj` (frame discipline,
  SPEC_GUIDE §0.5), and the patch changes none of them.
- `object.__class__.__name__` / `object.name` are unchanged attribute reads on
  the enum member; they are modeled directly as the `className` / `memberName`
  components of `enumMember`.
- **No flag dependency.** The branch is selected purely by the value's kind
  (the `isinstance` chain); there is no configuration flag. G-CONF fuzzes both
  kinds (plain enum members and other values).
- **`if`→`elif` and the container branches** (see above): the container branches'
  own CODE is untouched by the patch, and because they precede the enum branch a
  container-mixin enum member is displayed by its container branch rather than by
  the new one. Their TEXT is not invariant, though: they join
  `object_description(...)` of the values they hold, so a container holding a
  plain enum member renders differently after the patch. They are represented
  within the `other` kind, whose display is `legacyDescription` — the post-patch
  routine's own output for the value — so no pre-patch text is asserted for them
  (see "Disclosed granularity boundary" above).

## G-CONF fuzz seed

Pinned LCG seed: **9281** (see `conformance_check.py` `SEED`). Corpus: randomized
`PyValue`s — plain enum members with random class/member names (including empty
strings, names containing dots, unicode-ish ascii) and other values with
random tags — each rendered by the R/I shadow of `implementation_describeValue`
and diffed against an in-process replica of the POST-PATCH `object_description`
kind-dispatch (plain-enum branch = `f"{cls}.{name}"`, else the routine's own
display for the value, modeled by the SAME `legacyDescription` stand-in on both
legs) over ≥1e5 inputs. Hand-picked edge cases pin: the F2P `MyEnum.FOO` case,
empty class/member names, names containing `.`, and an `other`-kind value
(fall-through — covering non-enum values and container-mixin enum members).
Because the stand-in is applied on both legs, G-CONF refutes the enum-branch
text and the kind dispatch only; it is blind to the content of the `other` leg
by construction, which is the same boundary the spec draws.

## Measured reference behaviour (post-patch worktree)

Reference built from the frozen mirror, not from an installed sphinx:

```
git -C repos/sphinx-doc_sphinx.git worktree add --detach $WT 8ec06e9a1bd862cd713b9db748e039ccc7b3e15b
git -C $WT apply benchmark-verified/sphinx-doc__sphinx-9281/patch.diff   # 5 insertions(+), 2 deletions(-)
```
`object_description` extracted VERBATIM from both trees with
`ast.get_source_segment` (base file md5 `75cbe4695ab80deb32340fd2b8cb5b78`,
identical to `git show <base>:sphinx/util/inspect.py`) and exec'd with the real
`enum` module and the real `memory_address_re`; CPython 3.10.20.

| input | BASE (no enum branch) | POST-PATCH (reference) | model |
|---|---|---|---|
| `MyEnum.FOO` | `'<MyEnum.FOO: 1>'` | `'MyEnum.FOO'` | `enumMember "MyEnum" "FOO"` → `"MyEnum.FOO"` ✔ |
| `SE.S` (`str` mixin enum) | `"<SE.S: 'hello'>"` | `'SE.S'` | `enumMember "SE" "S"` ✔ (mixing in a non-container type does not change the dispatch) |
| `Perm.R` (canonical `Flag`) | `'<Perm.R: 1>'` | `'Perm.R'` | `enumMember "Perm" "R"` ✔ |
| `Perm.R\|Perm.W` (composite `Flag`, `.name is None` on 3.10) | `'<Perm.W\|R: 3>'` | `'Perm.None'` | `enumMember "Perm" "None"` ✔ (`memberName` is the `%s` text) |
| `{'a': MyEnum.FOO}` | `"{'a': <MyEnum.FOO: 1>}"` | `"{'a': MyEnum.FOO}"` | `other` → `legacyDescription obj` = the post-patch dict rendering ✔ (this input FALSIFIED the earlier "unchanged pre-existing rendering" denotation) |
| `{IE.A, IE.B}` | `'{<IE.A: 1>, <IE.B: 2>}'` | `'{IE.A, IE.B}'` | `other` ✔ |
| `frozenset({IE.A, IE.B})` | `'frozenset({<IE.A: 1>, <IE.B: 2>})'` | `'frozenset({IE.A, IE.B})'` | `other` ✔ |
| `{'k': {'inner': MyEnum.BAR}}` | `"{'k': {'inner': <MyEnum.BAR: 2>}}"` | `"{'k': {'inner': MyEnum.BAR}}"` | `other` ✔ (propagation is depth-unbounded) |
| `FZE.X = frozenset({IE.A, IE.B})` (`frozenset`+`Enum` mixin) | `'frozenset({<IE.A: 1>, <IE.B: 2>})'` | `'frozenset({IE.A, IE.B})'` | `other` ✔ (container branch captures it; its text still moves, because the branch joins its elements' displays) |
| `UNSORT.Y = frozenset({1, 'a'})` (unsortable mixin) | `"<UNSORT.Y: frozenset({1, 'a'})>"` | same | `other` ✔ (`elif` chain: the frozenset branch matches, sorting raises, the enum test is skipped, `repr` tail) |
| `[MyEnum.FOO]` | `'[<MyEnum.FOO: 1>]'` | same | `other` ✔ (`list` has no branch, so no element recursion) |
| `(MyEnum.FOO,)`, `{'a': 1}`, `frozenset({'p','q'})` | unchanged | same | `other` ✔ |

Every row agrees with the shipped spec under the denotations above. The two rows
that read `DIVERGES` against the OLD denotation of `legacyDescription` ("the
unchanged pre-existing rendering") are the ones the container recursion moves;
they are now covered by the post-patch denotation, and the fact that the model
does not separately FORCE that propagation is the disclosed boundary above.
