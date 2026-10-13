# Requirements: Consistent default permissions for uploaded files

## Introduction

When a file is uploaded and written to disk by Django's filesystem-backed
storage (`django.core.files.storage.FileSystemStorage`, exposed as
`django.core.files.storage.default_storage`), the numeric permission mode
applied to the saved file is governed by the `FILE_UPLOAD_PERMISSIONS` setting
defined in `django/conf/global_settings.py`.

Historically this setting defaulted to `None`, meaning no explicit mode was
applied and the resulting permissions were operating-system dependent. Because
the default upload handlers buffer small uploads in memory but stream large
uploads through a temporary file, the final permissions of a saved file could
differ depending only on the uploaded file's size (e.g. `0o600` for files that
passed through a temporary file on some systems). This inconsistency is
surprising and undesirable.

The goal is to give newly uploaded files a predictable, consistent permission
mode by default, while preserving the ability to configure the mode explicitly
(including opting back into the operating-system-dependent behavior) both
project-wide via the setting and per storage instance via the constructor.
The affected surfaces are the global default in
`django/conf/global_settings.py` and the resolution of the
`file_permissions_mode` property in `FileSystemStorage`.

## Requirement 1: Predictable default file upload permission mode

**User story:** As a Django developer relying on default settings, I want
uploaded files to receive a consistent, well-defined permission mode
regardless of upload size, so that file permissions in my media directory are
predictable and not dependent on internal buffering behavior.

**Acceptance criteria**

1. The system SHALL define a concrete numeric default for the project-wide
   file upload permission setting equal to octal `0o644` (decimal `420`),
   rather than an absent/unset value.
2. WHEN a filesystem storage instance is created without an explicit
   per-instance file permission mode and the project-wide file upload
   permission setting has not been overridden, THEN the storage's effective
   `file_permissions_mode` SHALL resolve to `0o644`.
3. WHEN the default storage's `file_permissions_mode` is read under the default
   configuration, THEN it SHALL be exactly `0o644` and SHALL NOT be an
   absent/`None` value.

## Requirement 2: Explicit override of the file upload permission mode

**User story:** As a Django developer, I want to override the file upload
permission mode through configuration, so that I can control the exact
permissions applied to saved files or restore operating-system-dependent
behavior.

**Acceptance criteria**

1. WHEN the project-wide file upload permission setting is overridden to any
   concrete numeric mode, THEN the effective `file_permissions_mode` of a
   storage instance that has no per-instance override SHALL equal exactly that
   configured mode (and SHALL NOT fall back to the default of `0o644`).
2. WHEN a storage instance is constructed with an explicit per-instance file
   permission mode, THEN its effective `file_permissions_mode` SHALL equal that
   per-instance mode regardless of the project-wide setting's value.
3. IF the project-wide file upload permission setting is explicitly set to an
   absent/`None` value and no per-instance mode is supplied, THEN the effective
   `file_permissions_mode` SHALL be that absent value, preserving the ability
   to opt into operating-system-dependent behavior.
4. WHILE a saved file's resolved permission mode is a concrete numeric value,
   the storage SHALL apply that mode to the file when saving it; WHILE the
   resolved mode is absent, the storage SHALL NOT apply any explicit permission
   change.

## Requirement 3: Preserve existing directory-permission behavior

**User story:** As a Django developer, I want the change to affect only file
permissions, so that directory creation behavior and other override settings
are not silently altered.

**Acceptance criteria**

1. The system SHALL keep the project-wide directory permission setting
   (`FILE_UPLOAD_DIRECTORY_PERMISSIONS`) at its existing absent/`None` default,
   unchanged by this modification.
2. WHEN the directory permission setting is overridden to a concrete numeric
   mode, THEN the effective `directory_permissions_mode` of a storage instance
   without a per-instance directory override SHALL equal that configured mode.
