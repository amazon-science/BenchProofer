# Requirements: keep message level tags consistent when settings change at runtime

## Introduction

The Django messages framework labels each message with a display "tag" derived
from its numeric level. This mapping is computed by
`django.contrib.messages.utils.get_level_tags()`, which merges the built-in
`django.contrib.messages.constants.DEFAULT_TAGS` with the project's
`MESSAGE_TAGS` setting (the override values taking precedence). For performance,
the result is cached once at import time in the module-level constant
`LEVEL_TAGS` inside `django.contrib.messages.storage.base`, and the
`Message.level_tag` property reads from that cached constant.

The defect: when `MESSAGE_TAGS` is changed at runtime — for example while
running tests that temporarily override settings — the cached `LEVEL_TAGS`
constant is never refreshed. As a result `Message.level_tag` keeps returning
values based on the stale mapping (or an empty string for levels only present in
the new configuration), diverging from the active `MESSAGE_TAGS` setting.

The goal is to make the cached level→tag mapping stay consistent with the
current settings: whenever the `MESSAGE_TAGS` setting changes, the cached
mapping must be recomputed from the current defaults and the current override,
while changes to any other setting must leave the cached mapping untouched. The
affected code is the messages application configuration
(`django.contrib.messages.apps.MessagesConfig`), which must subscribe to
Django's runtime setting-change notification, together with the cached
`LEVEL_TAGS` constant in `django.contrib.messages.storage.base`.

## Requirement 1: Refresh the cached level→tag mapping when MESSAGE_TAGS changes

**User story:** As a developer overriding `MESSAGE_TAGS` at runtime (e.g. in a
test), I want the messages framework's cached level→tag mapping to reflect my
override, so that message tags are computed from the current configuration
rather than a stale snapshot.

**Acceptance criteria**

1. WHEN Django emits a setting-changed notification reporting that the
   `MESSAGE_TAGS` setting has changed, THEN the messages framework SHALL
   recompute the cached level→tag mapping (`LEVEL_TAGS` in
   `django.contrib.messages.storage.base`) from the current configuration.
2. The recomputed cached mapping SHALL equal the result of merging the built-in
   default level→tag pairs with the current `MESSAGE_TAGS` override, where an
   override value replaces the default for any level present in both.
3. The recomputed cached mapping SHALL include an entry for every level present
   in the current defaults and for every level present in the current
   `MESSAGE_TAGS` override, including custom numeric levels that are not among
   the built-in defaults.
4. WHEN the `MESSAGE_TAGS` override supplies an empty string as the tag for a
   level, THEN the recomputed cached mapping SHALL map that level to the empty
   string (rather than falling back to a default tag).
5. WHEN a level's tag has been refreshed in the cached mapping, THEN reading
   `Message.level_tag` for a message at that level SHALL return the tag value
   from the current configuration.
6. IF the current `MESSAGE_TAGS` override supplies tag values for every level
   that has a built-in default, THEN the recomputed cached mapping SHALL equal
   the `MESSAGE_TAGS` override exactly.

## Requirement 2: Leave the cached mapping unchanged for unrelated setting changes

**User story:** As a developer changing settings other than `MESSAGE_TAGS`, I
want the cached level→tag mapping to remain stable, so that unrelated
configuration changes do not disturb message tagging.

**Acceptance criteria**

1. WHEN Django emits a setting-changed notification for any setting other than
   `MESSAGE_TAGS`, THEN the messages framework SHALL leave the cached level→tag
   mapping exactly as it was, performing no recomputation.
2. IF no setting-changed notification for `MESSAGE_TAGS` has occurred, THEN the
   cached level→tag mapping SHALL retain the value it had when it was last
   computed.

## Requirement 3: Subscribe to setting changes during messages app startup

**User story:** As a Django project using the messages framework, I want the
mapping-refresh behavior to be active automatically, so that runtime setting
overrides are honored without any additional wiring.

**Acceptance criteria**

1. WHEN the messages application configuration
   (`django.contrib.messages.apps.MessagesConfig`) completes its startup
   initialization, THEN it SHALL register a handler on Django's setting-changed
   signal so that subsequent `MESSAGE_TAGS` changes trigger the recomputation
   described in Requirement 1.
2. The system SHALL perform this registration without requiring any change to
   project code beyond having the messages application installed.

## Requirement 4: Preserve existing tag-lookup and message-equality behavior

**User story:** As a maintainer, I want the pre-existing behavior of message tag
lookup and message equality to be preserved, so that the fix introduces no
regressions.

**Acceptance criteria**

1. The `Message.level_tag` property SHALL return the tag mapped to the message's
   level in the current cached mapping, and SHALL return the empty string when
   the message's level is absent from that mapping.
2. The system SHALL keep computing the initial cached level→tag mapping at
   import time as the merge of the built-in defaults with the configured
   `MESSAGE_TAGS`, so that before any runtime change the mapping already
   reflects the configured overrides.
3. IF two `Message` instances have the same level and the same message content,
   THEN they SHALL compare as equal, regardless of their extra tags.
4. IF two `Message` instances differ in level or in message content, THEN they
   SHALL compare as not equal.
