# Requirements: PEP 484 type hints in pyreverse UML output

## Introduction

`pyreverse` generates UML diagrams from Python source. Today it ignores
PEP 484 parameter/attribute type annotations: a class attribute or method
parameter declared with a type hint (e.g. `a: str`) is rendered without its
type, and a hint combined with a `None` default (e.g. `a: str = None`) yields
no useful type information at all. The goal is for the diagram to display the
declared type of annotated attributes, method parameters, and method return
values, and to reflect an implicit-optional declaration (a typed target whose
default value is the `None` literal) as an `Optional[...]` type in the label.

The behavior lives in the `pyreverse` package: a new type-labelling capability
in `pylint/pyreverse/utils.py` (an annotation-resolution helper, an
annotation-to-text helper, and a type-inference helper), consumed by the
diagram builder (`pylint/pyreverse/inspector.py` — `Linker.visit_assignname`
and `Linker.handle_assignattr_type`), the type-name collector
(`pylint/pyreverse/diagrams.py` — `ClassDiagram.class_names`), and the DOT
renderer (`pylint/pyreverse/writer.py` — `DotWriter.get_values`). All existing
diagram output for unannotated code, and the existing visibility/relationship
behavior, must be preserved.

## Requirement 1: Resolve the declared annotation of an attribute or parameter

**User story:** As a developer generating a UML diagram, I want pyreverse to
locate the declared type annotation of a class attribute or `__init__`
parameter, so that the diagram can show the declared type.

**Acceptance criteria**

1. WHEN the annotation-resolution helper in `pylint/pyreverse/utils.py` is
   given an assignment-target node whose parent is an annotated assignment
   (astroid `AnnAssign`), THEN the helper SHALL use that parent's `annotation`
   expression as the target's annotation.
2. WHEN the helper is given an attribute-assignment node (astroid `AssignAttr`,
   e.g. the `self.x` target of `self.x = x` inside `__init__`) that is not
   itself part of an annotated assignment, THEN the helper SHALL resolve the
   annotation by matching the assigned parameter name against the enclosing
   `__init__` method's argument annotations, returning the annotation declared
   for the parameter of that name.
3. IF no annotation can be resolved for the given node, THEN the helper SHALL
   report the absence of an annotation (it SHALL NOT fabricate a type).
4. WHEN resolving the `__init__` parameter annotations and the expected
   argument/annotation structure is not present (attribute access fails),
   THEN the helper SHALL treat the annotation as absent rather than raising.

## Requirement 2: Render an annotation expression to a display label

**User story:** As a developer, I want each annotation expression converted to
a readable type string, so that both simple and parameterized types appear
correctly in the diagram.

**Acceptance criteria**

1. WHEN the annotation expression is a simple name reference (astroid `Name`,
   e.g. `str`), THEN the annotation-to-text helper SHALL produce the label
   equal to that name (e.g. `str`).
2. WHEN the annotation expression is a subscripted/parameterized type (astroid
   `Subscript`, e.g. `Optional[str]` or `List[int]`), THEN the helper SHALL
   produce the label equal to the source-text rendering of that expression
   (e.g. `Optional[str]`, `List[int]`).
3. IF the annotation expression is neither a simple name nor a subscripted
   type, THEN the helper SHALL produce an empty label.

## Requirement 3: Reflect an implicit-optional declaration as `Optional[...]`

**User story:** As a developer, I want a typed target whose default is `None`
to be shown as optional, so that the diagram honestly reflects that the value
may be absent.

**Acceptance criteria**

1. WHEN a target has a resolvable annotation AND the target's inferred default
   value is the `None` literal AND the annotation's base label does not already
   begin with `Optional`, THEN the produced label SHALL be the base label
   wrapped as `Optional[<base label>]`.
2. WHEN a target has a resolvable annotation AND its inferred default value is
   the `None` literal AND the base label already begins with `Optional`, THEN
   the produced label SHALL be the base label unchanged (it SHALL NOT be
   wrapped a second time).
3. WHEN a target has a resolvable annotation AND its default value is present
   and is not the `None` literal (or no default is declared), THEN the produced
   label SHALL be the base label unchanged (no `Optional` wrapping).
4. The system SHALL determine the base label for the wrapping decision using
   the annotation-to-text rendering of Requirement 2 (name for a simple name,
   source text for a subscripted type).
5. WHEN inferring the target's default value raises an inference error, THEN
   the wrapping decision SHALL proceed treating the default as not being the
   `None` literal (i.e. no `Optional` wrapping is forced by a failed
   inference).

The resulting label combinations that SHALL hold for an annotated assignment
target (`a: T = default`) and for an `__init__` parameter assigned to an
attribute (`x: T` with default) are:

6. WHEN the annotation is `str` and the default is the `None` literal, THEN the
   label SHALL be `Optional[str]`.
7. WHEN the annotation is `str` and the default is a present non-`None` value
   (e.g. a string literal), THEN the label SHALL be `str`.
8. WHEN the annotation is `Optional[str]` and the default is a present
   non-`None` value, THEN the label SHALL be `Optional[str]`.
9. WHEN the annotation is `Optional[str]` and the default is the `None`
   literal, THEN the label SHALL be `Optional[str]` (no double wrapping).
10. WHEN the annotation is `str` and no default is declared, THEN the label
    SHALL be `str`.
11. WHEN the annotation is `Optional[str]` and no default is declared, THEN the
    label SHALL be `Optional[str]`.

## Requirement 4: Type inference with annotation preference and safe fallback

**User story:** As a maintainer, I want the type recorded for a name or
attribute to prefer its declared annotation and otherwise fall back to
astroid inference, without crashing on uninferable nodes, so that diagram type
collection is robust.

**Acceptance criteria**

1. WHEN the type-inference helper in `pylint/pyreverse/utils.py` is asked for a
   node's type AND an annotation is resolvable for that node, THEN it SHALL
   return a set containing exactly that resolved annotation node.
2. WHEN no annotation is resolvable for the node, THEN the helper SHALL return
   the set of astroid-inferred types obtained from the node's `infer()`
   results.
3. WHEN no annotation is resolvable for the node AND calling the node's
   `infer()` raises an astroid inference error, THEN the helper SHALL return an
   empty set.
4. WHILE recording types in `Linker.visit_assignname`
   (`pylint/pyreverse/inspector.py`), the linker SHALL merge the type-inference
   helper's result for the name into the frame's `locals_type` entry for that
   name (union with any previously recorded types), instead of calling astroid
   `infer()` directly.
5. WHILE recording types in `Linker.handle_assignattr_type`
   (`pylint/pyreverse/inspector.py`), the linker SHALL merge the type-inference
   helper's result for the attribute node into the parent's
   `instance_attrs_type` entry for that attribute name (union with any
   previously recorded types), instead of calling astroid `infer()` directly.

## Requirement 5: Include annotation type nodes when collecting related class names

**User story:** As a developer, I want annotation-derived types to participate
in the diagram's set of known classes, so that types stored as annotation
nodes are not dropped.

**Acceptance criteria**

1. WHEN `ClassDiagram.class_names` (`pylint/pyreverse/diagrams.py`) iterates
   over a collection of type nodes, THEN a node that is a simple name reference
   (astroid `Name`) or a subscripted type (astroid `Subscript`) SHALL be
   eligible for inclusion in the returned names on the same terms as a class
   definition node.
2. WHEN such a node is eligible AND it exposes a `name` attribute AND it is not
   already present in the diagram, THEN its `name` SHALL be added to the
   returned list of class names.
3. The system SHALL continue to include class-definition (astroid `ClassDef`)
   nodes that expose a `name` and are not already present, exactly as before.

## Requirement 6: Render types in the DOT class label

**User story:** As a developer, I want the DOT output to show attribute types,
parameter types, and method return types, so that the rendered UML conveys the
declared type information.

**Acceptance criteria**

1. WHEN `DotWriter.get_values` (`pylint/pyreverse/writer.py`) renders a class
   record label and detailed (non-`only_classnames`) output is requested, THEN
   for each method parameter that has a resolvable annotation the parameter
   SHALL be rendered as `<parameter name>: <type label>`, using the
   annotation-to-text rendering of Requirement 2.
2. WHEN a method parameter has no annotation, THEN it SHALL be rendered as its
   bare parameter name, with no colon or type.
3. WHEN a method has a return annotation, THEN the method entry SHALL be
   suffixed with `: <return type label>` after its parameter list.
4. WHEN a method has no return annotation, THEN no return-type suffix SHALL be
   added.
5. The system SHALL continue to exclude the implicit `self` parameter from the
   rendered parameter list.
6. The system SHALL preserve the existing record-label structure: the class
   title, the attribute section, and the method section separated by the same
   delimiters as before, and SHALL keep rendering exception classes with the
   red-fontcolor record style.

## Requirement 7: Preserve existing pyreverse behavior (regression protection)

**User story:** As a maintainer, I want all previously-correct pyreverse output
and helpers to keep working unchanged, so that adding type-hint support
introduces no regressions.

**Acceptance criteria**

1. The `get_visibility` helper in `pylint/pyreverse/utils.py` SHALL continue to
   classify a name as `special` for dunder-style names, `private` for
   names with a double leading underscore (not dunder), `protected` for a
   single leading underscore, and `public` otherwise.
2. WHEN a project containing unannotated attributes and methods is rendered to
   DOT, THEN the generated class diagram SHALL match the previously-expected
   output: unannotated attributes shown with their inferred type where one
   exists (e.g. `attr : str`), and unannotated method parameters rendered as
   bare names (e.g. `set_value(value)`).
3. WHEN a project is rendered to DOT, THEN the generated package diagram SHALL
   match the previously-expected output (module boxes and their import
   relationships), unaffected by the type-labelling changes.
4. The system SHALL preserve existing class relationship extraction
   (inheritance, association, and interface/implements edges) in the generated
   diagrams.
5. The public helpers of `pylint/pyreverse/utils.py` used by the tests SHALL
   remain importable from that module (the type-inference helper, the
   annotation-resolution helper, and `get_visibility`).
