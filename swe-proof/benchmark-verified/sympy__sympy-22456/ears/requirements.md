# Requirements: Argument invariance for the codegen AST string value

## Introduction

The symbolic code-generation abstract-syntax-tree module (`sympy.codegen.ast`)
provides a class representing an atomic string value — the `String` class in
`sympy/codegen/ast.py`. Every object in the core symbolic hierarchy is expected
to satisfy *argument invariance*: rebuilding the object by applying its own
reconstruction callable to its own positional argument sequence must reproduce
an object equal to the original, i.e. `obj.func(*obj.args)` equals `obj`.

Today `String` only supports the weaker keyword-based reconstruction
(`obj.func(**obj.kwargs())` equals `obj`) and does not satisfy the positional
`obj.func(*obj.args)` form that holds for every other core object. Because the
string value is *atomic* (its text is intrinsic data, not a positional child),
its positional argument sequence is empty, so reconstruction must succeed from
no positional arguments.

The goal is to make the `String` class a genuine atomic object that satisfies
positional argument invariance, while preserving all of its existing observable
behavior (text access, equality, keyword reconstruction, printing) and without
disturbing the behavior of the other AST node classes in the same module.

## Requirement 1: Positional argument invariance for the string value

**User story:** As a developer manipulating code-generation AST nodes, I want
the atomic string value to rebuild itself from its own positional arguments, so
that it obeys the same reconstruction contract as every other core object and
generic argument-based traversal/rebuilding code works on it.

**Acceptance criteria**

1. WHEN a string value is constructed from a text and its positional argument
   sequence is applied to its own reconstruction callable
   (`obj.func(*obj.args)`), THEN the module SHALL return an object that compares
   equal to the original string value.
2. The system SHALL expose the string value's positional argument sequence
   (`args`) as empty, because the value is atomic and carries its text as
   intrinsic data rather than as a positional child.
3. WHEN the string value's reconstruction callable is invoked with no positional
   arguments, THEN the module SHALL yield an object equal to the original string
   value.
4. The reconstructed object SHALL preserve the original text, so that the
   reconstructed value's text equals the original value's text.

## Requirement 2: Atomicity of the string value

**User story:** As a developer, I want the string value to identify itself as an
atomic object, so that traversal and simplification code treats it as a leaf
with no expression sub-structure.

**Acceptance criteria**

1. The system SHALL report the string value as atomic (its `is_Atom` indicator
   is true).
2. IF code inspects the positional children of the string value, THEN the module
   SHALL present the value as having no positional children.

## Requirement 3: Preserved keyword-based reconstruction

**User story:** As a developer relying on the previously supported keyword
reconstruction, I want it to keep working, so that existing code depending on it
is not broken by the move to positional invariance.

**Acceptance criteria**

1. WHEN the string value's keyword argument mapping is applied to its
   reconstruction callable (`obj.func(**obj.kwargs())`), THEN the module SHALL
   return an object equal to the original string value.
2. The system SHALL report the string value's keyword argument mapping as empty.

## Requirement 4: Preserved string-value identity, text access, and printing

**User story:** As a user of the string value, I want its text access,
equality, and textual rendering to be unchanged, so that only the reconstruction
contract improves and nothing else regresses.

**Acceptance criteria**

1. The system SHALL expose the original text through the value's text attribute.
2. WHEN two string values are constructed from equal text, THEN the module SHALL
   report them as equal.
3. WHEN a subclass of the string value is constructed from the same text as a
   base string value, THEN the module SHALL report the subclass instance as not
   equal to the base string value, WHILE still exposing the same text on both.
4. WHEN a string value is rendered as a plain string, THEN the module SHALL
   produce exactly its text with no surrounding decoration.
5. WHEN a string value is rendered in its representation form, THEN the module
   SHALL produce the class-name form wrapping the quoted text (e.g. the
   representation of a string value built from `foo` is `String('foo')`).

## Requirement 5: No regression for the other AST node classes

**User story:** As a maintainer of the code-generation AST module, I want the
non-atomic node classes to keep their existing behavior, so that making the
string value atomic does not perturb the rest of the module.

**Acceptance criteria**

1. The system SHALL keep positional argument invariance
   (`obj.func(*obj.args)` equals `obj`) for the other AST node classes that
   already satisfy it, including assignment, augmented-assignment, node, type,
   variable, pointer, declaration, code-block, control-flow, and
   function-related classes.
2. The system SHALL keep the existing construction, equality, attribute access,
   argument exposure, and printing/rendering behavior of those other AST node
   classes unchanged.
3. WHERE an AST node class embeds a string value as one of its arguments, THEN
   the module SHALL continue to construct, compare, and render that node
   correctly after the string value becomes atomic.
