export function checkText(text, policy) {
  const findings = [];
  if (text && text.trim().length < (policy.minChars || 0)) {
    findings.push(`below minChars ${policy.minChars}`);
  }
  for (const p of policy.blockedPlaceholders || []) {
    if (text && text.includes(p)) findings.push(`placeholder ${p}`);
  }
  return findings;
}
