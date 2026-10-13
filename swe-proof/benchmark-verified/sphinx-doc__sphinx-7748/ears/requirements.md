# Requirements: docstring-signature extraction for overloaded callables

## Introduction

Sphinx's autodoc extension can read a callable's signature from the first
line(s) of its docstring when the `autodoc_docstring_signature` configuration
value is enabled. This is the mechanism used, for example, when C/C++ wrappers
(such as SWIG-generated bindings) cannot expose an introspectable Python
signature and instead embed the signature text at the top of the docstring.

By convention, when a wrapped callable is *overloaded*, each overload's
signature is written on its own line at the very start of the docstring. The
existing behavior only recognises the **first** such line and discards the
rest, so overloaded callables lose all but one signature in the generated
documentation.

The goal is to make the docstring-signature feature collect **every** signature
offered at the start of the docstring (in order) and render all of them, while
preserving the existing single-signature behavior and all related
configuration semantics.

Affected code lives in `sphinx/ext/autodoc/__init__.py`: the signature-from-
docstring behavior shared by `FunctionDocumenter` and `MethodDocumenter` (the
`DocstringSignatureMixin`), the class documenter that reuses it
(`ClassDocumenter`), and the module-level documenter that renders grouped /
overloaded module functions.

## Requirement 1: Collect every leading signature from a docstring

**User story:** As a documentation author for an overloaded callable, I want
autodoc to pick up all of the signatures listed at the top of the docstring, so
that every overload appears in the generated documentation instead of only the
first.

**Acceptance criteria**

1. WHEN `autodoc_docstring_signature` is enabled and a documented callable's
   signature is not already known by other means, THEN autodoc SHALL attempt to
   read the callable's signature(s) from the leading lines of its docstring.
2. WHEN the leading lines of the docstring contain more than one recognised
   signature line, THEN autodoc SHALL collect all of them, preserving their
   order of appearance, with the first recognised signature treated as the
   primary signature and each later recognised signature retained as an
   additional signature.
3. WHEN more than one signature is collected, THEN the rendered signature of
   the object SHALL include every collected signature, each on its own line and
   in the order collected, so that all of them appear in the object's
   documentation header.
4. The system SHALL preserve, for each collected signature, both its argument
   list and its return annotation exactly as they appear in the docstring line.

## Requirement 2: Backslash continuation determines when to keep reading

**User story:** As a documentation author, I want a clear, explicit marker for
"another signature follows", so that autodoc knows to keep reading additional
signature lines rather than treating the second line as body text.

**Acceptance criteria**

1. IF a recognised signature line ends with a trailing backslash, THEN autodoc
   SHALL treat it as a continuation, meaning at least one further signature line
   follows, and SHALL continue reading the next line for another signature.
2. WHEN a signature line ends with a trailing backslash, THEN autodoc SHALL
   remove that trailing backslash together with any whitespace preceding it
   before attempting to recognise the signature on that line, so that the
   continuation marker does not corrupt the parsed signature.
3. IF a recognised signature line does NOT end with a trailing backslash, THEN
   autodoc SHALL treat it as the final signature of that run and SHALL stop
   reading further lines from that docstring for signatures.
4. WHEN a signature has already been collected and a subsequent line is a
   non-continuation recognised signature, THEN autodoc SHALL include that final
   signature and then stop, so the last overload is not dropped.

## Requirement 3: Line scanning boundaries within a docstring block

**User story:** As a documentation author, I want signature extraction to look
only at the true leading signature lines, so that ordinary prose in the
docstring body is never mistaken for a signature.

**Acceptance criteria**

1. WHEN scanning the lines of a docstring block for signatures, THEN autodoc
   SHALL read lines from top to bottom and SHALL stop scanning that block at the
   first empty line encountered.
2. IF a line does not match the signature form, THEN autodoc SHALL skip that
   line without stopping the scan and without collecting a signature from it.
3. IF a line matches the signature form but its leading name is not one of the
   object's candidate names, THEN autodoc SHALL skip that line without stopping
   the scan and without collecting a signature from it.
4. The system SHALL consider, as candidate names for the leading name, the
   object's own final path name; and, when the object being documented is a
   class, additionally the name `__init__` and the names of the classes in the
   object's method-resolution order.

## Requirement 4: A single docstring supplies the whole result

**User story:** As a documentation author whose object exposes several docstring
blocks, I want the signatures taken from one coherent place, so that the result
is predictable.

**Acceptance criteria**

1. WHEN more than one docstring block is available for an object, THEN autodoc
   SHALL use the first block whose leading lines yield at least one signature as
   the source of the entire result, and SHALL ignore later blocks for signature
   purposes.
2. IF no docstring block yields any recognised signature, THEN autodoc SHALL
   leave the object's signature unchanged from what other mechanisms would
   produce, collecting no signatures from the docstring.

## Requirement 5: Consumed signature lines are stripped from the rendered docstring

**User story:** As a documentation reader, I do not want the raw signature lines
to appear twice, so that the signature shows in the header only and not also as
body text.

**Acceptance criteria**

1. WHEN autodoc collects one or more signatures from the leading lines of a
   docstring block, THEN it SHALL remove those consumed leading lines from the
   docstring body that is subsequently rendered, retaining only the remaining
   description text.
2. WHILE the docstring-signature feature is active for an object, the rendered
   description SHALL reflect the stripped docstring (the leading signature lines
   removed) rather than the original docstring.

## Requirement 6: Preserve existing single-signature and configuration behavior

**User story:** As an existing Sphinx user, I want the current behavior to keep
working unchanged, so that this enhancement introduces no regressions.

**Acceptance criteria**

1. WHEN a docstring begins with exactly one recognised signature line (no
   continuation marker), THEN autodoc SHALL behave exactly as before: it SHALL
   adopt that single signature and strip only that one leading line.
2. IF a signature is already explicitly provided for an object, THEN autodoc
   SHALL NOT override it with a signature read from the docstring.
3. IF `autodoc_docstring_signature` is disabled, THEN autodoc SHALL NOT read any
   signature from the docstring and SHALL NOT strip any leading lines from it.
4. The system SHALL keep the interaction with the `autoclass_content` setting
   intact: for a class documented with content mode that excludes the
   constructor, the class SHALL be rendered with an empty argument list; for
   content modes that include the constructor, the class SHALL be rendered with
   the signature(s) read from the constructor's docstring.
5. The system SHALL keep unrelated autodoc behaviors intact, including
   inherited-docstring handling, type-hint presentation modes, and the default
   member-option handling, so that enabling multi-signature collection does not
   alter their output.

## Requirement 7: Rendering grouped or overloaded module-level functions stays robust

**User story:** As a user documenting grouped or overloaded module-level
functions, I want signature formatting to succeed without errors, so that the
enhancement does not break rendering of those functions.

**Acceptance criteria**

1. WHEN autodoc formats the signature of a member callable while rendering a
   group of overloaded module-level functions, THEN it SHALL do so without
   raising an error caused by the callable lacking an object path.
2. The system SHALL continue to render the combined signatures of grouped
   module-level functions correctly, preserving the previously supported
   output.
