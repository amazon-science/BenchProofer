# Requirements: correct trailing-punctuation trimming in `urlize`

## Introduction

Django's template/text helper `urlize()` (in `django/utils/html.py`) turns
bare URLs and email addresses in a block of text into HTML anchor tags. Before
building a link, it strips leading and trailing punctuation from each candidate
word so that ordinary sentence punctuation stays outside the generated `<a>`
tag. The trailing-punctuation stripping happens in the internal
`trim_punctuation` helper, which — because encoded HTML entities such as
`&lt;` contain a `;` that is itself in the trailing-punctuation set — first
runs the candidate through `html.unescape` before deciding how much to strip.

The affected behavior: when the candidate word contains one or more HTML
character-reference entities (for example `&lt;`, `&gt;`, `&amp;`) that decode
to a shorter string than the original text, the amount of trailing punctuation
detected on the *decoded* string was applied using length arithmetic based on
the decoded string, then sliced against the *original* (still-encoded) text.
Because the decoded and original strings have different lengths, the split
between the linked portion (`middle`) and the trailing punctuation (`trail`)
landed at the wrong index, so characters belonging to the linked text were
duplicated into, or lost from, the trailing remainder.

Concretely, for the input shown in the issue:

    urlize('Search for google.com/?q=1&lt! and see.')

the expected result keeps the whole encoded token inside the link and moves
only the true trailing punctuation (`!`) out:

    'Search for <a href="http://google.com/?q=1%3C">google.com/?q=1&lt</a>! and see.'

The goal is to make the trailing-punctuation split depend on the *number of
trailing punctuation characters actually found on the decoded string*, applied
directly to the original text, so that the linked text and trailing remainder
are always partitioned correctly regardless of how many entities the candidate
contains — while preserving all previously correct `urlize` behavior and its
guard against pathological (catastrophic-backtracking) inputs.

## Requirement 1: Correct split point when trailing punctuation is detected via the decoded string

**User story:** As a developer using `urlize` to linkify user-supplied text, I
want candidate words that contain HTML-encoded entities followed by trailing
punctuation to be split correctly, so that the generated link text is intact
and only genuine trailing punctuation is placed after the closing tag.

**Acceptance criteria**

1. WHEN `trim_punctuation` decodes the current candidate (via `html.unescape`)
   and finds that the decoded form ends in one or more characters from the
   trailing-punctuation set (`.,:;!`), THEN the helper SHALL determine the
   count of trailing punctuation characters as the difference between the
   length of the decoded candidate and the length of the decoded candidate
   after its trailing punctuation characters are removed.
2. WHEN a positive count of trailing punctuation characters is determined,
   THEN the helper SHALL move exactly that many characters from the END of the
   ORIGINAL (still-encoded) candidate text into the trailing remainder, in
   their original order, prepended to any punctuation already accumulated in
   the trailing remainder.
3. WHEN a positive count of trailing punctuation characters is determined,
   THEN the helper SHALL retain as the linked candidate the ORIGINAL
   (still-encoded) candidate text with exactly that many characters removed
   from its end.
4. WHEN the candidate contains one or more encoded entities that decode to a
   shorter string than the original text and the candidate ends in trailing
   punctuation, THEN the count of characters moved to the trailing remainder
   SHALL equal the number of punctuation characters actually present at the
   end (as measured on the decoded string) and SHALL NOT be inflated or
   reduced by the length difference between the encoded and decoded forms.
5. IF the decoded candidate does not end in any trailing punctuation character,
   THEN the helper SHALL leave the linked candidate and the trailing remainder
   unchanged by this step.
6. WHEN linkifying the text `Search for google.com/?q=1&lt! and see.`, THEN
   `urlize` SHALL produce `Search for <a href="http://google.com/?q=1%3C">google.com/?q=1&lt</a>! and see.`, in which the encoded entity remains inside the anchor's visible text and only the exclamation mark is emitted after the closing tag.

## Requirement 2: Preserve existing trailing-punctuation and linkification behavior

**User story:** As a maintainer, I want the fix to change only the mis-split
case, so that all previously correct linkification of URLs, emails, wrapping
punctuation, and plain trailing punctuation continues to behave as before.

**Acceptance criteria**

1. The system SHALL continue to strip trailing punctuation characters from the
   set `.,:;!` from candidate words that contain no shortening entities exactly
   as before, placing that punctuation after the generated link.
2. WHEN a candidate has no encoded entities and ends in trailing punctuation
   (for example a URL followed by `!`), THEN `urlize` SHALL keep the URL inside
   the anchor and emit the trailing punctuation after the closing tag,
   unchanged from prior behavior.
3. The system SHALL continue to apply the trailing-punctuation trimming
   repeatedly, together with the existing wrapping-punctuation trimming, until
   the candidate stabilizes, so that entities (whose textual form ends in `;`)
   are not broken by removing their terminating semicolon.
4. The system SHALL continue to unescape the candidate only to MEASURE trailing
   punctuation, while all slicing that produces the linked text and trailing
   remainder operates on the original (still-encoded) candidate text.

## Requirement 3: No regression on unchanged or degenerate inputs

**User story:** As a user linkifying arbitrary text, I want inputs that should
not be turned into links, and pathological inputs, to be handled safely and
returned unchanged, so that `urlize` remains robust and does not hang.

**Acceptance criteria**

1. WHEN `urlize` is given a value that contains no linkifiable URL or email
   address, THEN it SHALL return that value unchanged.
2. WHEN `urlize` is given an input consisting of a very long run of the same
   trailing-punctuation character appended to text (a catastrophic-input
   stress case), THEN it SHALL return the input unchanged and SHALL complete in
   linear time without pathological slowdown.
3. WHEN `urlize` is given an input consisting of a very long run of repeated
   `@`-containing text (an email-detection stress case), THEN it SHALL return
   the input unchanged and SHALL complete without pathological slowdown.
4. IF a candidate word looks like an incomplete or invalid email address (for
   example one that begins or ends with `@`, contains more than one `@`, or
   whose domain part is empty or begins with a dot), THEN `urlize` SHALL NOT
   turn it into a link and SHALL return it unchanged.
5. The system SHALL preserve the existing behavior of all other `django.utils.html`
   helpers (escaping, conditional escaping, JavaScript escaping, tag stripping,
   linebreak handling, and URL quoting), making no observable change to them.
