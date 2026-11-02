#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { checkText } from "./lib/artifact-policy.mjs";
const policy = JSON.parse(fs.readFileSync(path.join(process.cwd(), ".claude/hooks/artifact-policy.json"), "utf8"));
const staged = process.env.STAGED_FILES;
if (!staged) process.exit(0);
let fail = false;
for (const f of staged.split("\n").filter(Boolean)) {
  if (!f.endsWith(".md")) continue;
  if (!policy.canonicalDocPrefixes.some((p) => f.startsWith(p)) && !f.includes("docs/sprint")) continue;
  const text = fs.readFileSync(f, "utf8");
  const findings = checkText(text, policy);
  if (findings.length) {
    console.error(f, findings.join("; "));
    fail = true;
  }
}
process.exit(fail ? 1 : 0);
