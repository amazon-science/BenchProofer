# Requirements: type-annotation name collection for `unused-import`

## Introduction

Pylint's variable checker tracks which imported names are actually used so it
can emit `unused-import` (`W0611`) for imports that are never referenced. A name
can be "used" solely inside a *type annotation*, including a type written as a
`# type:` comment (e.g. `X = ...  # type: abc.ABC`). To account for this,
`VariablesChecker` records, for each annotation it visits, the top-level
identifier names that the annotation refers to; those names are later treated as
"used" so the corresponding imports are not flagged.

The affected code lives in `pylint/checkers/variables.py`, in the
`VariablesChecker` helper `_store_type_annotation_node`, which walks a single
annotation expression node and appends the identifier names it refers to onto
the checker's running collection of annotation names (populated via
`_store_type_annotation_names` and the type-comment visit paths). The
downstream consumer compares imported names against that collection.

The defect (a follow-up to a prior related issue): when an annotation is a bare
dotted attribute access such as `abc.ABC` or `foo.Bar` (i.e. a qualified name,
not a plain identifier and not a subscripted/parametrized form), the walker
records **no** identifier at all. Consequently the qualifier module (`abc`,
`foo`) is never marked used, and `unused-import` is emitted as a false positive
even though the import is used in the annotation.

The goal: a dotted attribute annotation must contribute the identifier(s) at the
root of its qualifier, while every other annotation shape keeps its existing,
correct behavior.

## Requirement 1: Dotted attribute annotations record their qualifier

**User story:** As a developer who annotates values using qualified names in
type comments (e.g. `# type: abc.ABC`), I want the qualifier module to count as
used, so that a correct import is not wrongly reported as unused.

**Acceptance criteria**

1. WHEN `_store_type_annotation_node` processes an annotation node that is a
   member/attribute access (a dotted access of the form `<qualifier>.<attr>`),
   THEN the checker SHALL record the identifier name(s) contributed by the
   qualifier expression, and SHALL NOT record the trailing attribute label as an
   identifier in its own right.
2. WHEN the annotation is a single-level dotted access whose qualifier is a
   plain identifier (e.g. `abc.ABC`), THEN the checker SHALL record that
   qualifier identifier (`abc`) as a used annotation name.
3. WHEN the annotation is a multi-level dotted access (e.g. `a.b.c`), THEN the
   checker SHALL resolve through the nested qualifiers down to the root
   identifier and SHALL record that root identifier (`a`), and SHALL record no
   other identifier for the chain.
4. IF an import is referenced only inside such a dotted attribute annotation
   (including one written in a `# type:` comment), THEN the checker SHALL treat
   that import as used and SHALL NOT emit the `unused-import` (`W0611`) warning
   for it.

## Requirement 2: Existing annotation shapes keep their behavior

**User story:** As a pylint maintainer, I want the fix for dotted annotations to
leave the handling of plain names, subscripted forms, and non-name expressions
unchanged, so that no regression is introduced.

**Acceptance criteria**

1. WHEN the annotation is a plain identifier (a bare name such as `ABC`), THEN
   the checker SHALL record that identifier as a used annotation name.
2. WHEN the annotation is a parametrized/subscripted form (e.g. `Foo[Bar]`),
   THEN the checker SHALL record every identifier appearing anywhere inside the
   form, in left-to-right (pre-order) reading order — EXCEPT as specified in
   criterion 3.
3. WHEN the annotation is a parametrized/subscripted form whose head is a
   member access on the well-known standard typing namespace (i.e. the
   qualifier of the subscripted value is the identifier `typing`), THEN the
   checker SHALL record only the name of that typing namespace and SHALL record
   no further identifiers from that form.
4. WHEN the annotation is any other expression that refers to no identifier
   (e.g. a literal or ellipsis), THEN the checker SHALL record no identifier for
   it.
5. The checker SHALL preserve any names already collected before processing an
   annotation, appending newly contributed names to the end of the existing
   collection without reordering or dropping prior entries.
6. IF an import is referenced only inside a plain-name annotation, a subscripted
   annotation, or a `typing`-namespace parametrized annotation (each as above),
   THEN the checker SHALL continue to treat that import as used and SHALL NOT
   emit `unused-import` for it.

## Requirement 3: Preserve unrelated variable-checker diagnostics

**User story:** As a pylint user, I want the broader variable-checker behavior
to remain intact, so that the annotation fix does not disturb unrelated
warnings.

**Acceptance criteria**

1. The system SHALL continue to correctly emit and suppress unrelated
   variable-scope diagnostics (e.g. redefined-builtin handling, unused/unassigned
   globals, comprehension and lambda scoping, and import-as-underscore handling)
   exactly as before this change.
2. WHEN an imported name is genuinely never referenced — in code or in any type
   annotation — THEN the checker SHALL still emit `unused-import` for it.
