## Migration Guide

- Old code (read-only): `src/playweight`
- New module: `src_new/rpa/browser`
- Steps:
  1. Keep old modules intact (no edits).
  2. Wrap old runner usage behind `BrowserService` where needed.
  3. Gradually move scene-specific actions to typed services.
- Backward compatibility: provide adapter layers if existing callers need old signatures.