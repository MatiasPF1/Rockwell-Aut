# Playbook: Web Application Attack
Trigger: alert_type = Web Application Attack

ATT&CK mapping: T1190 (Exploit Public-Facing Application) - Initial Access (TA0001).
Note this is the same top-level technique as vulnerability.md's Vulnerability alert
type - ATT&CK's technique catalog models the adversary's action (exploiting a
public-facing app), not the specific vulnerability class (SQLi/XSS/directory
traversal are OWASP/CWE categories, not separate ATT&CK sub-techniques), so the same
ID is the honest answer for both rather than forcing an artificial distinction. The
practical difference here is that this alert type reflects an attempt actually
observed against the application (via WAF/app logs), not just an unpatched exposure.
Source: MITRE ATT&CK Enterprise matrix, mitre/cti repo, MITRE's own Terms of Use
license (verified directly - not Apache 2.0). Attribution: "(c) 2026 The MITRE
Corporation. This work is reproduced and distributed with the permission of The
MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
WAF or application log flags a known attack pattern (SQL injection, XSS probe,
directory traversal) against a specific endpoint.

## Analysis
Confirm from WAF/app logs whether the payload was blocked or reached the
application layer. If it reached the app, check for evidence of successful
exploitation: unexpected DB queries, new files written, or error traces leaking
data.

## Containment
Add the source IP to the WAF blocklist and tighten the matching rule if it's a known
attack class; if the app itself is confirmed exploitable, restrict access (e.g.
VPN-only) while a fix is prepared.

## Eradication
Patch or add a virtual patch for the underlying vulnerability if the application
code is confirmed exploitable.

## Recovery
Restore normal access once the patch/virtual patch is verified; invalidate any
sessions or data affected by a confirmed successful exploitation.

## Lessons Learned
Close as Blocked if the WAF stopped it with no evidence of compromise; if it reached
the app, treat the underlying code defect as the real root cause, not just this one
attack attempt.
