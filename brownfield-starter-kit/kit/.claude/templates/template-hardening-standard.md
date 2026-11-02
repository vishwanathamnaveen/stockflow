# Template hardening (Claude kit)

- No placeholder `{TODO}` in shipped templates.
- Use `{{variable}}` only where a command explicitly renders the template.
- Kit commands reference `.claude/templates/<name>.md` — keep paths consistent with command contracts.
- SAST packs, handoff logs, and issue-log templates are **not** shipped in this kit.
