# Requirements: Optional element id for `json_script`

## Introduction

Django exposes a helper, `json_script`, in two places:

- `django.utils.html.json_script(value, element_id)` — a Python function that
  JSON-encodes `value`, escapes the HTML/XML special characters in the result,
  and wraps the encoded body in a `<script type="application/json">` element.
- the `json_script` template filter in `django.template.defaultfilters`, which
  is a thin wrapper delegating to the utility function above.

Historically both required an `element_id`, which was always rendered as the
`id` attribute of the emitted `<script>` element. There are legitimate
use-cases (for example, embedding the script inside a `<template>` element)
where no identifier is needed and the `id` attribute is undesirable.

The goal is to make the identifier **optional** in both the utility function
and the template filter, so callers may omit it and receive a `<script>`
element with no `id` attribute, while every previously supported behavior
(including the JSON encoding and HTML-escaping) is preserved unchanged.

## Requirement 1: Identifier is optional in the utility function

**User story:** As a Django developer, I want to call
`django.utils.html.json_script` without supplying an identifier, so that I can
produce a JSON script element that carries no `id` attribute.

**Acceptance criteria**

1. The system SHALL allow `django.utils.html.json_script` to be called with the
   value as the only positional argument (the identifier argument being
   optional).
2. WHEN `json_script` is called without an identifier (or with an empty/absent
   identifier), THEN the function SHALL return a `<script type="application/json">`
   element that contains the encoded JSON body and carries **no** `id`
   attribute.
3. WHEN `json_script` is called with a non-empty identifier, THEN the function
   SHALL return a `<script>` element whose `id` attribute is set to that
   identifier and whose `type` attribute is `application/json`, containing the
   encoded JSON body.
4. The system SHALL, in both cases, produce the same JSON-encoded and
   HTML/XML-escaped body it produced before this change (see Requirement 3).
5. The system SHALL return the result as an output marked safe for direct
   inclusion in HTML.

## Requirement 2: Identifier is optional in the template filter

**User story:** As a template author, I want to apply the `json_script` filter
without an argument, so that I can render a JSON script element with no `id`.

**Acceptance criteria**

1. The system SHALL allow the `json_script` template filter to be applied to a
   value without providing the identifier argument.
2. WHEN the `json_script` filter is applied to a value with no argument, THEN
   the rendered output SHALL be a `<script type="application/json">` element
   containing the value's encoded JSON body and carrying **no** `id` attribute.
3. WHEN the `json_script` filter is applied with an identifier argument, THEN
   the rendered output SHALL be a `<script>` element carrying that identifier as
   its `id` attribute, matching the utility function's with-identifier output.
4. The filter's output SHALL match the output of the underlying utility function
   for the same value and identifier.

## Requirement 3: Preserve existing encoding, escaping, and structure

**User story:** As a maintainer, I want the encoding and escaping behavior to
stay exactly as before, so that existing callers and their output are
unaffected.

**Acceptance criteria**

1. The system SHALL continue to JSON-encode `value` using Django's JSON encoder
   (the same encoder used before this change), including its handling of types
   such as dates and Decimals.
2. The system SHALL continue to escape the HTML/XML special characters `<`,
   `>`, and `&` in the encoded JSON body as their unicode escape sequences, so
   the body is safe to embed inside the script element.
3. WHEN a non-empty identifier is supplied, THEN the emitted `id` attribute
   value SHALL be escaped in the same way substituted arguments were previously
   escaped when formatting the element.
4. The system SHALL keep the element's opening tag, `type="application/json"`
   attribute, encoded body, and closing `</script>` tag structure identical to
   the prior behavior for the with-identifier case.
5. The system SHALL leave the observable behavior of all other HTML utility
   functions in the module (escaping, `format_html`, `conditional_escape`,
   `strip_tags`, `urlize`, and the html-safe helpers) unchanged.
