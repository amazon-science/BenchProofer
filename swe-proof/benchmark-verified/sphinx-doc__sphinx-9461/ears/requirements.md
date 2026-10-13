# Requirements: Support documenting attributes decorated with both `@classmethod` and `@property`

## Introduction

Since Python 3.9, a class attribute may be defined by stacking the
`@classmethod` and `@property` decorators, producing a read-only, class-level
computed attribute:

```python
class A:
    @classmethod
    @property
    def f(cls):
        """Some class property."""
        return "property"
```

Sphinx's Python documentation support does not recognize such attributes.
Ordinary `@property` attributes are documented, but a `@classmethod`-wrapped
`@property` is skipped entirely (its docstring, type, and modifier are lost),
because the attribute no longer inspects as a plain `property` object.

This bundle specifies the behavior needed so that these class-level properties
are documented like ordinary properties, but additionally marked as
class-level. The affected areas are:

- The Python domain property directive `PyProperty`
  (`sphinx/domains/python.py`), which renders the signature prefix and accepts
  option flags for a property description.
- The autodoc property documenter `PropertyDocumenter`
  (`sphinx/ext/autodoc/__init__.py`), which discovers property members of a
  class and emits their directive header (options, type, docstring).
- The inspection helpers `isclassmethod` and `getdoc`
  (`sphinx/util/inspect.py`), which classify objects and retrieve docstrings.

Behavior is described in terms of the reStructuredText the documenter emits and
the document tree the directive produces; nothing here prescribes how the code
is edited.

## Requirement 1: Class-level flag on the property directive

**User story:** As a documentation author, I want to mark a `py:property`
directive as class-level, so that the rendered description shows it is a
class-level property.

**Acceptance criteria**

1. The system SHALL accept, on the Python property directive (`py:property` /
   `PyProperty`), a boolean flag option that marks the property as class-level,
   in addition to the existing abstract-method flag option and the existing
   type option.
2. WHEN the class-level flag option is present on a property directive, THEN
   the system SHALL prepend the word `class` to the rendered signature prefix so
   that the prefix reads `class property ` (the word `class`, a single space,
   the word `property`, and a single trailing space).
3. WHEN the abstract-method flag option is present on a property directive,
   THEN the system SHALL include the word `abstract` in the rendered signature
   prefix.
4. WHEN both the abstract-method flag option and the class-level flag option
   are present on a property directive, THEN the system SHALL render the
   signature prefix as `abstract class property ` — the word `abstract`, then
   the word `class`, then the word `property`, each separated by a single space,
   with a single trailing space.
5. IF neither the abstract-method flag option nor the class-level flag option
   is present, THEN the system SHALL render the signature prefix as `property `
   (the word `property` followed by a single trailing space).
6. The system SHALL keep the type option behavior for property directives: WHEN
   a type option value is supplied, THEN the rendered signature SHALL include a
   type annotation of the form `: <value>` for that property.

## Requirement 2: Property directive index and cross-reference registration are preserved

**User story:** As a documentation reader, I want class-level properties to be
indexed and cross-referenceable exactly like ordinary properties, so that links
and the index keep working.

**Acceptance criteria**

1. The system SHALL produce, for each documented property (including a
   class-level one), an index entry describing it as a property of its
   containing class, in the same textual form used for an ordinary property
   (the attribute name, followed by the containing class name qualified as a
   property).
2. The system SHALL register each documented property (including a class-level
   one) in the Python domain's object inventory under its fully qualified
   `Class.attribute` name, recorded with the `property` object type and marked
   as non-anonymous, so that it can be resolved as a cross-reference target.
3. The system SHALL continue to register and index ordinary (non-class-level)
   properties unchanged when the class-level flag option is absent.

## Requirement 3: Autodoc discovers class-level property members

**User story:** As a package author using autodoc, I want autodoc to document a
class attribute defined with stacked `@classmethod` and `@property` decorators,
so that it is not silently omitted from the generated documentation.

**Acceptance criteria**

1. WHEN autodoc examines a member of a documented class, THEN the property
   documenter SHALL claim responsibility for that member if the member is an
   ordinary property, and additionally if the member is a class attribute whose
   underlying object in the class dictionary is a class method that wraps a
   property.
2. WHILE the member being documented is a class attribute whose class-dictionary
   entry is a class method wrapping a property, the system SHALL resolve the
   member to the wrapped property object so that its type and documentation can
   be extracted like an ordinary property.
3. IF a member is neither an ordinary property nor a class method wrapping a
   property, THEN the property documenter SHALL NOT claim responsibility for it.
4. The system SHALL continue to claim and document ordinary property members of
   a class exactly as before, and SHALL only treat members of classes (not of
   modules) as properties.

## Requirement 4: Autodoc marks class-level properties and emits their type and docstring

**User story:** As a package author, I want a documented class-level property to
be rendered with a class-level marker plus its type and docstring, so that
readers see it is class-level and see its details.

**Acceptance criteria**

1. WHEN autodoc generates the directive header for a member it determined to be
   a class-level property (a class method wrapping a property), THEN the system
   SHALL emit the class-level flag option line for that property directive.
2. WHEN autodoc generates the directive header for an ordinary property that is
   not class-level, THEN the system SHALL NOT emit the class-level flag option
   line.
3. WHEN autodoc generates the directive header for a property whose getter has a
   return type annotation and type-hint output is enabled, THEN the system SHALL
   emit a type option line carrying that return type, for both ordinary and
   class-level properties.
4. WHEN autodoc documents a property whose underlying function carries a
   docstring, THEN the system SHALL emit that docstring as the content of the
   property, for both ordinary and class-level properties.
5. WHEN the documented property is abstract, THEN the system SHALL emit the
   abstract-method flag option line, and this behavior SHALL be unchanged by the
   introduction of the class-level marker.

## Requirement 5: Inspection helpers recognize class methods and their docstrings

**User story:** As a maintainer of the inspection utilities, I want the helper
that classifies class methods and the helper that fetches docstrings to handle
class-level properties, so that class-level property documentation resolves
correctly.

**Acceptance criteria**

1. The system SHALL classify an object as a class method when it is a class
   method object, or when it is a bound method bound to a class.
2. WHEN the class-method classifier is given a containing class and an attribute
   name in addition to an object, THEN it SHALL also report the object as a
   class method if that attribute name resolves, anywhere in the class's method
   resolution order, to a class method defined in the class dictionary.
3. WHEN the docstring helper is given an object together with a containing class
   and an attribute name, and the attribute is determined to be a class method,
   THEN the system SHALL return the docstring of the underlying wrapped function
   found via the class's method resolution order.
4. The system SHALL preserve the existing docstring-resolution behavior for
   ordinary objects, partial functions, and inherited docstrings when the
   class/name-based class-method path does not apply.
5. WHEN autodoc resolves the docstring for a class member, THEN it SHALL pass
   the containing object and the member name to the docstring helper so that a
   class-level property's docstring is found.
