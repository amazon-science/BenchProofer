# Requirements: robust lower-bound sanitisation for logarithmic image normalisation

## Introduction

When an image is drawn with a logarithmic colour normalisation (a `LogNorm`
instance passed as the `norm` of an image created via `imshow`), matplotlib
resamples the image data and, in doing so, re-derives the effective lower and
upper bounds of the data range that are temporarily assigned to the norm before
the norm is applied. This sanitisation happens in the image-drawing path,
specifically in the internal `_make_image` routine of
`lib/matplotlib/image.py` (reached through `AxesImage.make_image` /
`draw`).

A logarithmic scale cannot represent a lower bound that is zero or negative,
because the logarithm of a non-positive number is not finite. When the
re-derived lower bound handed to the norm is zero or negative, the transform of
that bound is non-finite and `LogNorm.__call__` (in
`lib/matplotlib/colors.py`) raises `ValueError("Invalid vmin or vmax")`,
aborting the draw.

The existing guard only replaced the lower bound when it was strictly negative,
and used the maximum of the original value and a small positive floor. This
left a gap: a re-derived lower bound of exactly zero (and, for the intended
semantics, any non-positive value) could still be forwarded to the logarithmic
transform, producing the non-finite transform and the fatal error. The goal is
to sanitise the lower bound so that a logarithmic normalisation always receives
a strictly positive lower bound, while leaving all other cases untouched.

The small positive floor value is the smallest representable positive
difference for the data's working floating-point type (i.e. the machine epsilon
of that dtype, `numpy.finfo(<dtype>).eps`).

## Requirement 1: Sanitise a non-positive lower bound for logarithmic normalisation

**User story:** As a user drawing an image whose data spans a huge range and
whose colour mapping uses a logarithmic scale, I want the image to render
without error even when the effective lower bound of the resampled data is zero
or negative, so that a valid figure is produced instead of a crash.

**Acceptance criteria**

1. WHEN an image is drawn whose normalisation is a logarithmic normalisation
   (`LogNorm`) AND the lower value of the re-derived data range that is about
   to be assigned to the norm is less than or equal to zero, THEN the
   image-drawing routine SHALL replace that lower value with the small positive
   floor value (the machine epsilon of the working floating-point dtype) before
   the norm is applied.
2. WHEN the lower value is replaced under criterion 1, THEN the replacement
   value SHALL be exactly the machine-epsilon floor and SHALL NOT depend on the
   original non-positive lower value.
3. IF the normalisation is a logarithmic normalisation AND the lower value of
   the re-derived data range is zero, THEN the image-drawing routine SHALL treat
   it as a non-positive bound and replace it with the positive floor value.
4. WHEN an image is drawn with a logarithmic normalisation and data that mixes
   non-positive entries with entries of very large magnitude, THEN the draw
   SHALL complete without raising `ValueError("Invalid vmin or vmax")`.
5. The system SHALL always leave the upper value of the re-derived data range
   unchanged when performing this sanitisation.

## Requirement 2: Preserve the lower bound when sanitisation is not required

**User story:** As a user drawing images with linear normalisations or with
logarithmic normalisations whose lower bound is already valid, I want the
existing rendering behaviour to be unchanged, so that no colours or value
mappings shift because of the sanitisation logic.

**Acceptance criteria**

1. IF the normalisation is a logarithmic normalisation AND the lower value of
   the re-derived data range is strictly positive, THEN the image-drawing
   routine SHALL leave that lower value unchanged.
2. IF the normalisation is NOT a logarithmic normalisation, THEN the
   image-drawing routine SHALL leave the lower value of the re-derived data
   range unchanged regardless of its sign.
3. The system SHALL apply the lower-bound replacement only to logarithmic
   normalisations, so that images using a linear normalisation continue to map
   values to colours exactly as before.

## Requirement 3: Preserve existing image-rendering behaviour

**User story:** As a maintainer, I want all previously-working image drawing,
resampling, interpolation, masking, and colour-mapping behaviour to remain
intact, so that this fix does not regress unrelated functionality.

**Acceptance criteria**

1. WHEN an image is drawn with a logarithmic normalisation whose data and
   bounds are already fully valid (all positive), THEN the routine SHALL produce
   the same rendered output as before this change.
2. The system SHALL keep producing correct output for images drawn with linear
   normalisation, including data containing values below the normalisation's
   lower bound (which are mapped through the colormap's under-range colour).
3. The system SHALL preserve all existing resampling, interpolation, masking,
   and alpha-handling behaviour of the image-drawing routine unchanged.
4. WHEN an empty image is drawn with either a linear or a logarithmic
   normalisation, THEN the routine SHALL continue to behave as it did before
   this change.
