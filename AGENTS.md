# Claire personal website

This directory is the canonical workspace for Claire's personal website.

- Web source, assets, build output, and standalone `claire.html` live at the root.
- The current Blender source is `models/modern-v03/claire-modern-v03.blend`.
- Current design and interaction documents live in `docs/handoff`.
- Before animation or interaction work, read `skills/emil-design-eng/SKILL.md`. Apply immediate feedback, interruptible springs, restrained overshoot, and reduced-motion behavior.
- Preserve `models/archives`, `models/modern-v02`, `inherited-v02`, and original validation evidence; archive verification relies on their original file hashes.
- Preserve user-provided music files. Do not invent songs, biography details, or projects.
- Build with `npm run build`; this refreshes both the maintained web build and the offline standalone HTML.
- Test against the server running from this directory. Set `CLAIRE_BASE_URL` if an older preview still occupies the default port.
