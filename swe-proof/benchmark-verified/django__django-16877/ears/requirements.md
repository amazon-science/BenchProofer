# Requirements: `escapeseq` sequence-escaping template filter

## Introduction

Django's template filter library (`django/template/defaultfilters.py`) offers
per-element companions to some scalar filters. For example, the scalar `safe`
filter marks a single value as safe-for-HTML, and its companion `safeseq`
applies that same decision to every element of a sequence, returning a list.

There is currently no per-element companion to the scalar `escape` filter. The
`escape` filter marks a single value for HTML auto-escaping using Django's
conditional HTML escaper (`django.utils.html.conditional_escape`), which escapes
ordinary text but leaves content already marked safe-for-HTML untouched. When a
template author has autoescaping turned off and wants to escape every item of a
list before joining or otherwise combining them, no single filter expresses this.

The goal is to add a new sequence filter, `escapeseq`, registered in the default
template filter library, that is to `escape` what `safeseq` is to `safe`: it
applies the shared conditional HTML-escaping decision to each element of an
input sequence, individually, and returns the list of results. A typical usage
is `{{ some_list|escapeseq|join:"," }}` in a context where autoescaping is off.

## Requirement 1: Per-element escaping of a sequence

**User story:** As a template author, I want a filter that escapes each element
of a sequence individually, so that I can safely combine the escaped items (for
example with `join`) even when autoescaping is off.

**Acceptance criteria**

1. The system SHALL register a template filter named `escapeseq` in the default
   template filter library (`django/template/defaultfilters.py`) so that it is
   available to templates as `escapeseq`.
2. WHEN the `escapeseq` filter is applied to an input sequence, THEN the filter
   SHALL return a list containing exactly one result entry for each element of
   the input sequence, preserving the input order.
3. WHEN the `escapeseq` filter produces the entry for a given input element,
   THEN that entry SHALL be exactly the value produced by Django's conditional
   HTML escaper (`django.utils.html.conditional_escape`) applied to that element.
4. IF an input element is ordinary (not already marked safe-for-HTML), THEN the
   filter SHALL escape that element's HTML-significant characters in its result
   entry (for example, `&` becomes `&amp;`, `<` becomes `&lt;`, `>` becomes
   `&gt;`).
5. IF an input element is already marked safe-for-HTML, THEN the filter SHALL
   leave that element's text unchanged in its result entry (no additional
   escaping is applied).

## Requirement 2: Behavior independent of the autoescape state

**User story:** As a template author, I want `escapeseq` to escape its elements
regardless of the surrounding autoescape setting, so that it behaves
predictably both inside and outside an `{% autoescape off %}` block.

**Acceptance criteria**

1. WHEN the `escapeseq` filter is applied while template autoescaping is enabled,
   THEN the filter SHALL produce the same per-element results as when
   autoescaping is disabled.
2. WHILE template autoescaping is disabled, applying `escapeseq` to a sequence
   SHALL still escape each ordinary element and still leave each already-safe
   element unchanged.
3. The system SHALL register `escapeseq` such that its output is treated as
   already safe-for-HTML, so that downstream filters operating with autoescaping
   enabled do not escape the produced entries a second time.

## Requirement 3: Correct composition with `join`

**User story:** As a template author, I want `escapeseq` to chain correctly into
the `join` filter, so that `{{ some_list|escapeseq|join:sep }}` yields the
escaped items concatenated by the separator with no double-escaping.

**Acceptance criteria**

1. WHEN a sequence is passed through `escapeseq` and then through `join` with a
   separator, THEN the rendered output SHALL be the per-element escaped entries
   concatenated in order, separated by the given separator.
2. WHEN the escaped entries are joined, THEN each already-escaped entry SHALL
   appear in the output without being escaped again.
3. The system SHALL preserve the existing behavior of the `safe`, `safeseq`,
   and `escape` filters unchanged; adding `escapeseq` SHALL NOT alter the
   results those existing filters produce.
