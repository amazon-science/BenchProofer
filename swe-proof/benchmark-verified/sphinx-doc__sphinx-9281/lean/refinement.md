# refinement.md — sphinx-doc__sphinx-9281

Operation-by-operation correspondence between `implementation_describeValue`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `object_description`
kind-dispatch). Tags: **R** type refinement, **A-consumed** proof uses an axiom,
**A-reference** deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if let .enumMember className memberName := obj then …` | the value fails the preceding `dict`/`set`/`frozenset` guards and satisfies `elif isinstance(object, enum.Enum):` — i.e. it is a PLAIN enum member, selecting the enum-member branch | R |
| 2 | `return className ++ "." ++ memberName` | `return "%s.%s" % (object.__class__.__name__, object.name)` | R |
| 3 | `return legacyDescription obj` (fall-through) | the display the POST-PATCH routine gives a value that does not take the new enum branch: the dedicated `dict`/`set`/`frozenset` branches (which also capture container-mixin enum members, and which join `object_description(...)` of the values they hold) plus the general-purpose tail `s = repr(object); s = memory_address_re.sub('', s); return s.replace('\n', ' ')` | R |

Notes:

- **Every step is R — no A, no I-needing-axiom.** The changed op (the new enum
  branch) is modeled DEEPLY: the displayed text is spelled out as the
  concatenation `className ++ "." ++ memberName`, which is exactly
  `"%s.%s" % (cls_name, member_name)`. SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op, so there is no consumed axiom.
- **op 1 (R).** "fails the dict/set/frozenset guards AND satisfies
  `isinstance(object, enum.Enum)`" ↔ the `PyValue.enumMember` constructor. The
  Lean `PyValue` type is the type-only refinement of "a Python value, viewed at
  the granularity the fix distinguishes": PLAIN enum member (not a container-
  mixin) vs. anything else (non-enum values and container-mixin enum members,
  which the preceding container branches capture before the enum test runs).
  The kind test is total in both languages.
- **op 2 (R).** Python `%`-formatting `"%s.%s" % (C, M)` ↔ Lean
  `C ++ "." ++ M`. For `str` arguments `%s` is identity, so the formatted result
  is the concatenation of `C`, `"."`, `M` — byte-identical to the Lean
  `String.append`. No assumption on the contents (dots, empties, etc.) is made.
- **op 3 (R).** The `other`-kind fall-through is modeled by the opaque
  `legacyDescription obj`, whose denotation is **the display the POST-PATCH
  routine produces for a value that does not itself take the new enum branch**:
  the dedicated `dict`/`set`/`frozenset` branches plus the `repr` +
  memory-address scrub + newline-flatten tail. For an `other`-kind value that is
  literally `object_description(object)` as shipped, so the clause is
  tautological against the reference and cannot be over-strong. It is NOT "the
  pre-patch rendering": the container branches join `object_description(...)` of
  the values they hold, so a container holding a plain enum member renders
  differently after the patch, and asserting pre-patch text here would falsify
  the spec on `{'a': MyEnum.FOO}` (measured — mapping.md "Measured reference
  behaviour"). Modeling it as an opaque `String`-valued function of the value is
  the weakest faithful model — the spec quantifies over all values and pins the
  `other` result to exactly `legacyDescription obj`, so a verifying impl must
  return precisely that routine's output for an `other`-kind value (it cannot
  echo the enum branch). It carries **no `_prop` axiom**: for `other` it appears
  verbatim on both sides of the spec equation and for `enumMember` it is absent,
  so the proof consumes no property of it — NOT an A-reference, NOT A-consumed.
  **G-AX skips.**
- **`if`→`elif` and container-mixin enums.** The diff also converts the
  `set`/`frozenset` `if`s into an `elif` chain so the new branch can hang off
  it. The kinds are NOT pairwise disjoint: an enum class can mix in `dict`/
  `set`/`frozenset` (e.g. `class FZ(frozenset, enum.Enum)`), whose members
  satisfy both `isinstance` tests. Because the container branches PRECEDE the
  enum branch, such a member is rendered by its container branch and never by
  the new one — including when that branch falls through on unsortable values,
  where the `elif` chain skips the enum test entirely and the value lands on the
  `repr` tail (measured: `UNSORT.Y`, unchanged text). The model draws the
  boundary exactly there: only PLAIN enum members are `PyValue.enumMember`;
  container-mixin enum members are `PyValue.other`, displayed by
  `legacyDescription`.
- **DISCLOSED ASYMMETRY — the propagation through the container branches is
  carried, not pinned.** An earlier revision of this file claimed "no
  changed-but-inexpressible op exists". That was wrong, and the correction is
  recorded rather than quietly dropped. The container branches join
  `object_description(...)` of the values they hold, so the patch's new display
  also reaches every `dict`/`set`/`frozenset` holding a plain enum member, at any
  depth (measured: `{'a': MyEnum.FOO}` → `"{'a': MyEnum.FOO}"` post-patch vs
  `"{'a': <MyEnum.FOO: 1>}"` at base; `FZE.X`; `{'k': {'inner': MyEnum.BAR}}`).
  `PyValue.other`'s `Nat` tag cannot express "a container holding a plain enum
  member", so op 3 carries that text inside `legacyDescription` (denoted
  post-patch) instead of pinning it. Two consequences, both stated for the
  record: the spec asserts nothing false — its `other` clause equals the shipped
  routine's own output on every `other`-kind value; and the spec does not FORCE
  the propagation, so an implementation that produced the new display only at
  top level would still verify. The second does not weaken `verify ⟹ resolved`:
  the F2P test `test_object_description_enum` observes only
  `object_description(MyEnum.FOO) == "MyEnum.FOO"`, and no test in
  `tests/test_util_inspect.py` renders a container holding an enum member, so a
  patch that changes only the top-level display still resolves. Pinning the
  propagation would require the carrier to become a recursive value tree
  (`mapping (List (PyValue × PyValue))` / `setLike (List PyValue)` /
  `frozenLike (List PyValue)` with a mutually-recursive render, sortable
  containers only, unsortable ones staying `other`); that is the strictly
  stronger model, and it is deliberately NOT what this bundle ships, because the
  two-arm carrier is the granularity the graded behaviour is observed at.
- **The fix itself** is op 1+2 collectively: pre-patch, there is no enum branch,
  so a plain enum member falls through to `legacyDescription` (the ugly
  `<Class.Member: value>` `repr`). The prepatch impl returns
  `legacyDescription obj` unconditionally — modeled by `Solution_prepatch.lean`,
  whose `correct_describeValue` is unprovable on the discriminating clause: for
  `.enumMember C M` the spec demands `result = C ++ "." ++ M`, but the prepatch
  impl yields `legacyDescription (.enumMember C M)`, which is not definitionally
  (nor provably, since `legacyDescription` is opaque/unconstrained) equal to the
  qualified name. Note the prepatch variant models the ABSENCE OF THE TOP-LEVEL
  dedicated treatment, which is the modeled granularity: on a plain enum member
  `legacyDescription` is the `repr` tail, i.e. exactly that member's real
  pre-patch display (no container guard matches it), which is what makes the
  discriminating clause fail. It does not additionally re-derive the pre-patch
  text of a container holding an enum member — that text is inside the carrier,
  per the disclosed asymmetry above.
- **G-CONF** mechanically refutes the R legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the post-patch
  `object_description` kind-dispatch over ≥1e5 fuzzed inputs
  (`conformance_check.py`, seed 9281), with `legacyDescription` modeled by the
  SAME deterministic stand-in on both legs (so any disagreement can only come
  from the enum-branch text, never the opaque tail).
