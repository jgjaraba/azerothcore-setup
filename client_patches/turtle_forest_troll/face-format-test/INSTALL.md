# Single face-format A/B test

This is a full replacement candidate for the owned patch-S v2, NOT an overlay
to load together with it. Only male Troll Skin24's FaceLower/FaceUpper differ.
The top-level RGBA pixels are identical; serialization changes to BLP2 palette.
Other skin faces remain unchanged and may still show the reported error.

1. Verify SHA256SUMS in this directory. Fully exit WoW.
2. Back up your current owned Data/patch-S.MPQ OUTSIDE Data. Baseline expected:
   d63ecb0e583a77f4283dde8f39e253d4dee5694f6978ae5326d1120e164165a9
3. Copy this candidate Data/patch-S.MPQ to that SAME client path. Keep T/Z and
   locale patches unchanged. Do not install another S alongside it or rename it
   to a higher-priority test archive. No SQL or server restart is necessary.
4. Select a male Troll of an ordinary class, the first additional v2 tone after
   the six Forest tones (purple body, source100 / internal Skin24). Any normal
   Face0..4 references this same pair. Choose an ORIGINAL tusk/facial option,
   not new face paint that could conceal the underlying face.
5. Compare exactly that selection before/after: does the face regain detail and
   match the purple body, or remain green/untextured? A screenshot is useful.
6. Fully exit WoW and restore your backed-up v2 S to revert this experiment.

Do not roll back the server, remove hairstyles/features, or replace with v1.
This artifact is an experiment, not an accepted repair of all v2 skins.
