# Requirements: Suppress headers/settings whose value is the null sentinel when merging session defaults with per-request settings

## Introduction

When a request is prepared, the client library combines two ordered
key/value mappings into a single effective mapping: the session-level
defaults and the per-request settings. This merge is performed by
`merge_setting(request_setting, session_setting, dict_class=OrderedDict)`
in `requests/sessions.py`, and it is the mechanism used to compute the
effective headers (and other dict-valued settings such as params and
proxies) for an outgoing request.

Users expect that assigning `None` to a key suppresses that key entirely —
so, per the documentation, a caller can prevent a default header from being
sent. Concretely, `session.headers['Accept-Encoding'] = None` should cause
`Accept-Encoding` to be omitted from the prepared request rather than being
transmitted with the literal string value `None`.

Before the fix, `merge_setting` only removed a key when the **per-request**
mapping mapped it to `None`; a `None` value coming from the **session
defaults** survived the merge and was later serialized as the header value
`"None"`. The goal is to guarantee that the effective mapping never carries
a null-valued entry, regardless of which of the two input mappings supplied
the `None`, while preserving all existing merge behavior (override
semantics, ordering, and the early-return/bypass branches).

## Requirement 1: The merged mapping never carries a null-valued entry

**User story:** As a developer who sets a default session header (or other
dict setting) to `None`, I want that key to be omitted from the effective
mapping, so that the header is not sent at all instead of being sent with a
bogus `None` value.

**Acceptance criteria**

1. WHEN both the per-request setting and the session setting are dictionary
   mappings and are merged, THEN `merge_setting` SHALL return a mapping in
   which no key has a value equal to the null sentinel (`None`).
2. IF the session-level mapping maps a key to `None` and the per-request
   mapping does not supply that key, THEN `merge_setting` SHALL omit that key
   from the returned mapping.
3. IF the per-request mapping maps a key to `None`, THEN `merge_setting` SHALL
   omit that key from the returned mapping, whether or not the session mapping
   provided a value for it.
4. WHEN a session default header value is set to the null sentinel and a
   request is prepared from that session, THEN the prepared request's headers
   SHALL NOT contain that header name.
5. The system SHALL treat the null sentinel as the value `None`, applying the
   suppression only to keys whose value is exactly `None` and never to keys
   whose value is an empty string, `0`, `False`, or any other non-`None`
   value.

## Requirement 2: Preserve override and merge semantics for non-null values

**User story:** As a developer relying on per-request overrides of session
defaults, I want the existing merge behavior to be unchanged for ordinary
values, so that only the `None`-suppression behavior is added.

**Acceptance criteria**

1. WHEN a key is present in both mappings with non-null values, THEN
   `merge_setting` SHALL use the per-request value for that key in the returned
   mapping.
2. WHEN a key is present only in the session mapping with a non-null value,
   THEN `merge_setting` SHALL retain that key and value in the returned mapping.
3. WHEN a key is present only in the per-request mapping with a non-null value,
   THEN `merge_setting` SHALL include that key and value in the returned
   mapping.
4. The system SHALL preserve the insertion ordering of the merged mapping:
   keys originating from the session defaults keep their relative position,
   an overriding per-request value keeps the existing key's position, and a
   new per-request key is appended after the session-derived keys.
5. The system SHALL return a newly constructed mapping containing exactly the
   surviving (non-null) merged entries, and SHALL leave the two input mappings
   unmodified. The returned mapping is a fresh object built during the merge
   rather than either input; its concrete container type is not guaranteed to
   match the `dict_class` argument once null-valued entries have been removed.

## Requirement 3: Preserve the early-return and non-mapping bypass branches

**User story:** As a maintainer, I want the existing short-circuit behavior of
`merge_setting` to remain intact, so that the null-suppression change does not
alter unrelated call paths.

**Acceptance criteria**

1. IF the session setting is `None`, THEN `merge_setting` SHALL return the
   per-request setting unchanged.
2. IF the per-request setting is `None`, THEN `merge_setting` SHALL return the
   session setting unchanged.
3. IF either operand is not a dictionary mapping (for example a scalar setting
   such as the TLS-verification flag), THEN `merge_setting` SHALL return the
   per-request setting unchanged without attempting to merge.
4. The system SHALL continue to apply null-suppression only in the branch where
   both operands are dictionary mappings.

## Requirement 4: Downstream request-preparation behavior remains correct

**User story:** As a user of the session request-preparation flow, I want the
merged settings to feed the prepared request correctly, so that ordinary
sessions, redirects, cookies, and authentication keep working.

**Acceptance criteria**

1. WHEN a request is prepared from a session with ordinary (non-`None`) default
   headers, THEN those headers SHALL appear in the prepared request unchanged.
2. WHEN preparing a request, THEN the session SHALL merge headers, query
   parameters, and other dict-valued settings using the same
   null-honoring merge behavior consistently.
3. The system SHALL keep existing session behaviors — cookie persistence across
   requests, redirect handling, and authentication header computation —
   functioning as before, unaffected by the null-suppression change.
