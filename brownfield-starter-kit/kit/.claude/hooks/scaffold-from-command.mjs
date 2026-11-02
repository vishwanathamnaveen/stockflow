#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
const prompt = process.env.CURSOR_PROMPT || "";
const root = process.cwd();
const m = prompt.match(/sprint\s*(\d+)/i);
const sprint = process.env.SPRINT_NUMBER || (m ? m[1] : null);
function ensure(p) {
  fs.mkdirSync(p, { recursive: true });
  const gk = path.join(p, ".gitkeep");
  if (!fs.existsSync(gk)) fs.writeFileSync(gk, "");
}
const KIT_COMMANDS =
  "generate-brd|propose-architecture|plan-sprint|generate-ui-design|implement-api|implement-ui|expand-test-coverage|run-tests|run-eval|close-eval-gaps|review-changes|application-summary|build-context|implement-change";
if (new RegExp(`\\/(${KIT_COMMANDS})`).test(prompt)) {
  if (sprint) {
    ensure(path.join(root, `docs/sprint${sprint}`));
    ensure(path.join(root, `docs/sprint${sprint}/userstory`));
  }
  ensure(path.join(root, "artifacts/audit"));
  ensure(path.join(root, "artifacts/changes"));
  ensure(path.join(root, "docs/harness"));
}
