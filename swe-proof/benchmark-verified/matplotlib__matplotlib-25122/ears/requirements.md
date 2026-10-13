# Requirements: Correct window-loss compensation in the spectral helper

## Introduction

Matplotlib's spectral routines in `lib/matplotlib/mlab.py` (the shared engine
`_spectral_helper`, and its public consumers `psd`, `csd`, `magnitude_spectrum`,
`angle_spectrum`, `phase_spectrum`, `specgram`, and `cohere`) multiply each data
segment by an analysis *window* before taking its Fourier transform. Because the
window attenuates the signal, the resulting spectrum must be divided by a
*window-correction factor* built from the window's own samples so that the lost
energy/amplitude is compensated.

The correction factor is currently computed from the **magnitudes** of the window
samples (each sample's absolute value is taken before summing). This is wrong for
any window that contains negative samples — for example a flat-top window, whose
side lobes dip below zero. For such windows the sum of magnitudes differs from the
arithmetic (signed) sum, so the spectrum is scaled by the wrong factor. For windows
whose samples are all non-negative (e.g. Hanning, rectangular/`window_none`) the two
sums coincide, so those results must be unchanged.

The goal is to make every window-correction factor use the **signed** total of the
window samples (and the signed total of their squares), matching the reference
definition used by comparable signal-processing libraries, while leaving all other
spectral behavior intact.

## Requirement 1: Signed window sum for amplitude-style spectra

**User story:** As a user computing a magnitude or complex spectrum with a window
that has negative samples, I want the window-loss compensation to use the true
(signed) sum of the window samples, so that the returned spectrum is correctly
scaled.

**Acceptance criteria**

1. WHEN a magnitude spectrum is computed for a data segment weighted by a window,
   THEN `_spectral_helper` SHALL divide the magnitude result by the arithmetic
   (signed) sum of the window samples, not by the sum of their absolute values.
2. WHEN a complex spectrum is computed for a data segment weighted by a window,
   THEN `_spectral_helper` SHALL divide the complex result by the arithmetic
   (signed) sum of the window samples, not by the sum of their absolute values.
3. IF the window contains one or more negative samples, THEN the amplitude-style
   correction factor SHALL be the signed sum (which may be smaller in magnitude
   than, or differ in sign from, the sum of the sample magnitudes).
4. The window-correction factor for amplitude-style spectra SHALL be a pure
   function of the window samples only (independent of the sampling frequency and
   of the density flag).

## Requirement 2: Signed window sums for power-style (PSD) spectra

**User story:** As a user computing a power spectral density (or cross-spectral
density) with a window that has negative samples, I want the power normalization to
use the signed window sums, so that density and per-segment power results are
correct.

**Acceptance criteria**

1. WHEN a power-style spectrum is computed WITH scaling by frequency (a density),
   THEN `_spectral_helper` SHALL divide the result by the sum of the squared window
   samples computed from the signed samples, not from their absolute values.
2. WHEN a power-style spectrum is computed WITHOUT scaling by frequency (power
   preserved per segment), THEN `_spectral_helper` SHALL divide the result by the
   square of the arithmetic (signed) sum of the window samples, not by the square of
   the sum of their absolute values.
3. IF the window contains negative samples, THEN for the same input signal the
   density result and the non-frequency-scaled result SHALL remain related only by
   the sampling-frequency factor and the ratio between the squared-sample sum and
   the squared signed sum — i.e. the frequency-scaled power spectrum multiplied by
   the squared signed window sum SHALL equal the density spectrum multiplied by the
   sampling frequency and by the sum of the squared window samples (up to numerical
   tolerance).
4. The power-style correction SHALL apply after the one-sided scaling factor and,
   when requested, the division by the sampling frequency, and SHALL leave the DC
   (and, for an even number of frequencies, the Nyquist) component treated exactly
   as before.

## Requirement 3: Unchanged behavior for non-negative windows and other modes

**User story:** As an existing user relying on the current spectral results, I want
outputs to stay identical wherever the window has no negative samples and for
spectrum modes that never applied a window correction, so that the fix does not
regress established behavior.

**Acceptance criteria**

1. IF every window sample is non-negative, THEN all spectral results (`psd`, `csd`,
   `magnitude_spectrum`, `complex` spectrum, `specgram`, `cohere`, and the windowed
   variants) SHALL be identical to the results produced before the change, because
   the signed sum and the sum of magnitudes coincide.
2. WHEN an angle or phase spectrum is computed, THEN `_spectral_helper` SHALL apply
   no window-correction factor to the result (the phase is unaffected by window
   scaling).
3. The system SHALL preserve the existing one-sided normalization: for a one-sided
   spectrum the non-DC, non-Nyquist frequency components SHALL continue to be scaled
   by the same one-sided factor as before.
4. The system SHALL preserve the existing segmentation, detrending, zero-padding,
   frequency-axis construction, and the requirement that the window length match the
   segment length; only the window-correction factor SHALL change.
5. WHEN a window is supplied as a callable rather than an array, THEN it SHALL be
   evaluated to obtain the window samples, and the correction factor SHALL be
   computed from those samples using the signed sums defined above.
