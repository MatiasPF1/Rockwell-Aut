# Playbook: Suspicious Login
Trigger: alert_type = Suspicious Login

ATT&CK mapping: T1078 (Valid Accounts) - spans Initial Access (TA0001), Persistence
(TA0003), Privilege Escalation (TA0004), and Defense Evasion (TA0005), since a valid
but compromised account can be used at any of those stages; for the SSO/cloud-login
impossible-travel pattern specifically, sub-technique T1078.004 (Cloud Accounts)
applies. Source: MITRE ATT&CK Enterprise matrix, mitre/cti repo, MITRE's own Terms
of Use license (verified directly - not Apache 2.0). Attribution: "(c) 2026 The
MITRE Corporation. This work is reproduced and distributed with the permission of
The MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
Impossible-travel rule (same account, two logins, physically implausible elapsed
time) or a new-device/new-location flag never seen for this account before.

## Analysis
Confirm impossibility/implausibility of the pattern against known device/location
history - and check whether an MFA push was approved (MFA-fatigue attacks rely on
the user approving without noticing, which does not confirm legitimacy).

## Containment
Force an immediate password reset and re-authentication with MFA for the affected
account; revoke active sessions/tokens issued during the suspicious window.

## Eradication
Review the account's session activity between the two logins for any data access,
forwarding-rule changes, or config changes made by the attacker if the account was
compromised - remove any such changes.

## Recovery
Restore normal access once the account is confirmed clean; de-register any
unrecognized device involved.

## Lessons Learned
Close as Contained if no unauthorized activity occurred during the window; if MFA
fatigue was the vector, consider number-matching MFA instead of simple push
approval.
