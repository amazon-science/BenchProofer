# Requirements: Correct and efficient multi-word admin changelist search

## Introduction

The Django admin changelist supports free-text search over a model's configured
`search_fields`. The search term entered by an administrator is split into
individual words, and each word is matched against the search fields using the
per-field lookup operators (`icontains` by default, or `istartswith` / `iexact`
/ `search` when a field name is prefixed with `^`, `=`, `@`).

The affected code is `ModelAdmin.get_search_results` in
`django/contrib/admin/options.py`. Its job is to narrow the supplied queryset so
that it retains only the model instances that satisfy the whole search term, and
to report whether the narrowed result may contain duplicate rows.

Two problems exist in the current behavior when one or more search fields span a
**multi-valued relation** (for example a reverse foreign key or many-to-many,
such as `child__name`):

1. **Correctness.** The current implementation applies a separate queryset
   filter for each word of the search term. When a search field spans a
   multi-valued relation, each such filter introduces its own join, so different
   words may be satisfied by *different* related rows. This over-matches: an
   instance is retained even when no single related row matches all the words.
2. **Performance.** Because each word produces its own filter (and therefore its
   own join), a search term with many words produces many joins and can make the
   changelist query prohibitively slow.

The goal is to narrow the queryset with a **single combined filter** so that,
for each multi-valued relation traversed by the search fields, all words that
are matched through that relation must be satisfied by **one and the same**
related row (collapsing the per-word joins into a single join per relation),
while words that can be satisfied by the instance's own field values or by a
*different* relation are still combined independently. This is done without
changing any other observable output of the function.

## Requirement 1: Words matched through one multi-valued relation must share a single related row

**User story:** As an administrator searching a changelist across a multi-valued
relation, I want an instance returned only when the words I matched through that
relation are all satisfied by one and the same related row, so that results are
not falsely inflated by combining unrelated rows of the same relation.

**Acceptance criteria**
1. WHEN a search term is non-empty and search fields are configured, THEN
   `get_search_results` SHALL retain an instance in the narrowed queryset if and
   only if, treating every word's per-field OR condition as one combined
   AND-of-all-words condition applied in a single filtering step, the instance
   satisfies that combined condition — with the consequence that, for any single
   multi-valued relation traversed only via that relation's configured search
   fields, the words satisfied through it must all be satisfied by the same
   related row.
2. WHEN every configured search field spans the same multi-valued relation, and
   two search words are each individually matched through that relation but no
   single related row matches both words together, THEN `get_search_results`
   SHALL exclude that instance from the narrowed queryset.
3. WHEN a single related row of a multi-valued relation matches every word that
   is matched through that relation, THEN `get_search_results` SHALL retain that
   instance in the narrowed queryset.
4. WHEN a word can be satisfied by the instance's own single-valued field values
   (or by a relation other than the one under consideration), THEN that word
   SHALL be allowed to contribute to retention independently of which related
   row of a multi-valued relation satisfies the other words; the same-related-row
   constraint SHALL bind only those words that are matched through the same
   multi-valued relation.
5. The system SHALL evaluate each word against the configured search fields
   using the OR combination across those fields (so a word matches when it
   satisfies at least one configured field), and SHALL combine the per-word
   matches with AND within a single combined filter (so all words must be
   satisfied together, and words matched through the same multi-valued relation
   must be satisfied by the same related row).

## Requirement 2: The narrowing is a single combined filter (bounded joins)

**User story:** As an administrator entering a search term with many words, I
want the changelist query to remain efficient, so that searching does not stall.

**Acceptance criteria**
1. WHEN a search term contains multiple words and a search field spans a
   multi-valued relation, THEN `get_search_results` SHALL narrow the queryset
   with a single combined filter so that the number of joins introduced for that
   relation does not grow with the number of search words.
2. WHEN the search term consists of many repetitions of the same word over a
   single multi-valued search field, THEN the resulting query SHALL introduce
   exactly one join for that relation, and SHALL retain an instance when one
   related row matches the repeated word.
3. The system SHALL produce a narrowed queryset whose retained instances are
   determined solely by the combined all-words condition of Requirement 1,
   independent of the order in which the words are processed.

## Requirement 3: Preserve unchanged search behaviors

**User story:** As a maintainer, I want existing search semantics preserved, so
that only the multi-valued over-matching and join explosion are fixed.

**Acceptance criteria**
1. WHEN the search term is empty or no search fields are configured, THEN
   `get_search_results` SHALL return the supplied queryset unchanged.
2. WHEN a word in the search term is wrapped in matching single or double quotes,
   THEN `get_search_results` SHALL treat the unescaped literal inside the quotes
   as the word to match.
3. The system SHALL continue to honor the search-field prefixes that select the
   lookup operator: `^` for starts-with, `=` for exact, `@` for full-text
   search, and no prefix for case-insensitive contains, and SHALL continue to
   follow relation paths expressed with the lookup separator.
4. The system SHALL preserve the ordering and identity of retained instances
   relative to the supplied queryset, keeping each qualifying instance and not
   introducing instances that do not satisfy the search.

## Requirement 4: Report duplicate possibility unchanged

**User story:** As a caller of `get_search_results`, I want the duplicate-results
indicator to keep its meaning, so that downstream de-duplication decisions are
unaffected by this fix.

**Acceptance criteria**
1. The system SHALL return, alongside the narrowed queryset, a boolean
   indicating whether the results may contain duplicates.
2. WHEN any configured search field spawns duplicate rows (as determined for the
   configured search fields on the model), THEN `get_search_results` SHALL report
   that the results may contain duplicates.
3. WHEN no configured search field spawns duplicate rows, THEN
   `get_search_results` SHALL report that the results may contain duplicates only
   if some other factor already required it; this indicator's value SHALL NOT be
   altered by the change to how per-word matching is combined.

## Requirement 5: Non-relational single-valued searches unaffected

**User story:** As an administrator searching on ordinary (non-multi-valued)
fields, I want multi-word search to keep working as before, so that the fix does
not regress common searches.

**Acceptance criteria**
1. WHEN all search fields reference single-valued attributes of the instance and
   the search term has multiple words, THEN `get_search_results` SHALL retain an
   instance if and only if the instance satisfies every word (each word under the
   OR across the configured fields).
2. WHEN a multi-word search cannot be satisfied by a single instance's own field
   values, THEN `get_search_results` SHALL exclude that instance.
