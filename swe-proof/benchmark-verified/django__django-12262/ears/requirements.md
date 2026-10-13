# Requirements: Keyword-only arguments in custom template tags

## Introduction

Django's template tag helpers `simple_tag` and `inclusion_tag` (registered via
`django.template.library.Library`) parse the arguments written in a template
`{% ... %}` block through the shared helper
`django.template.library.parse_bits`. This helper receives the tag callable's
signature — its positional parameters, its variadic markers, its defaults, and
critically the set of *keyword-only* parameters together with which of those
have default values — and turns the raw template bits into positional args and
keyword args, raising `TemplateSyntaxError` on any misuse.

The helper mishandles keyword-only parameters. A tag function such as
`def f(*, greeting='hello')` declares a keyword-only parameter that carries a
default. When a template supplies that argument by keyword, `parse_bits`
incorrectly treats it as unrecognized and rejects the whole tag. In addition,
when any keyword-only argument is supplied more than once, the helper reports
the wrong diagnostic — it claims the argument is unexpected rather than
reporting a duplicate value.

The goal is to make `parse_bits` recognize every declared keyword-only
parameter (whether or not it has a default) as an acceptable keyword argument,
so that keyword-only arguments with defaults can be overridden from a template,
and so that duplicated keyword arguments produce the correct diagnostic — while
preserving all existing acceptance and rejection behavior. The behavior must be
identical for both `simple_tag` and `inclusion_tag`, since they share this code
path.

## Requirement 1: Accept keyword-only arguments that have defaults

**User story:** As a template author, I want to pass a value for a tag's
keyword-only argument that has a default, so that I can override the default
from within a template.

**Acceptance criteria**

1. WHEN a custom `simple_tag` or `inclusion_tag` whose function declares a
   keyword-only parameter with a default value is invoked from a template and a
   value for that parameter is supplied using keyword syntax
   (`name=value`), THEN `parse_bits` SHALL accept the argument without raising
   `TemplateSyntaxError`.
2. WHEN such a keyword-only argument is accepted, THEN the tag SHALL render
   using the value supplied in the template rather than the parameter's
   declared default.
3. IF a keyword-only argument with a default is NOT supplied in the template,
   THEN the tag SHALL render using the parameter's declared default value and
   SHALL NOT raise an error.
4. The system SHALL treat a declared keyword-only parameter as a permitted
   keyword argument regardless of whether that parameter has a default value.

## Requirement 2: Correct diagnostic when a keyword argument is supplied twice

**User story:** As a template author, I want a clear error when I accidentally
supply the same keyword argument more than once, so that I can identify the
real mistake.

**Acceptance criteria**

1. WHEN the same keyword argument name is supplied more than once for a custom
   `simple_tag` or `inclusion_tag`, THEN `parse_bits` SHALL raise
   `TemplateSyntaxError` reporting that the tag received multiple values for
   that keyword argument, naming the tag and the argument.
2. The reported message SHALL take the form
   `'<tag>' received multiple values for keyword argument '<name>'`.
3. WHEN a keyword-only parameter (whether or not it declares a default) is the
   argument supplied twice, THEN the raised message SHALL be the
   multiple-values diagnostic of criterion 2 and SHALL NOT be an
   unexpected-keyword-argument diagnostic.
4. The duplicate-value detection SHALL apply equally to positional parameters
   supplied by keyword name and to keyword-only parameters.

## Requirement 3: Preserve rejection of genuinely unexpected keyword arguments

**User story:** As a tag author, I want callers to still be rejected when they
pass an argument my tag does not declare, so that typos and misuse are caught.

**Acceptance criteria**

1. IF a keyword argument is supplied whose name is neither a declared
   positional parameter, nor a declared keyword-only parameter, and the tag
   function does not accept arbitrary keyword arguments (no `**kwargs`), THEN
   `parse_bits` SHALL raise `TemplateSyntaxError` reporting that the tag
   received an unexpected keyword argument, naming the tag and the argument.
2. The reported message SHALL take the form
   `'<tag>' received unexpected keyword argument '<name>'`.
3. WHEN the tag function accepts arbitrary keyword arguments (`**kwargs`), THEN
   a keyword argument whose name is not otherwise declared SHALL be accepted
   and collected rather than rejected.

## Requirement 4: Preserve reporting of missing required arguments

**User story:** As a tag author, I want callers to be told when they omit a
required argument, so that incomplete invocations are reported clearly.

**Acceptance criteria**

1. IF, after parsing all supplied bits, one or more required positional
   parameters or required keyword-only parameters (a keyword-only parameter
   without a default) have not received a value, THEN `parse_bits` SHALL raise
   `TemplateSyntaxError` reporting that the tag did not receive value(s) for
   those argument(s), naming the tag and listing the missing argument names.
2. WHEN a keyword-only parameter that has no default is omitted from the
   template, THEN the tag SHALL be reported as missing that argument.
3. WHEN a keyword-only parameter that has a default is omitted, THEN it SHALL
   NOT be reported as missing.

## Requirement 5: Preserve existing positional and ordering behavior

**User story:** As a template author, I want all previously valid tag
invocations to keep working exactly as before, so that this change does not
regress existing templates.

**Acceptance criteria**

1. The system SHALL continue to raise `TemplateSyntaxError` reporting too many
   positional arguments WHEN more positional values are supplied than the tag
   accepts and the function declares no variadic positional parameter.
2. The system SHALL continue to raise `TemplateSyntaxError` reporting that a
   positional argument was received after a keyword argument WHEN a positional
   value follows a keyword argument in the template.
3. WHEN a positional parameter is supplied by its keyword name, THEN
   `parse_bits` SHALL accept it and SHALL count that parameter as filled.
4. The parsing behavior described in Requirements 1–5 SHALL be identical for
   tags registered with `simple_tag` and tags registered with `inclusion_tag`.
