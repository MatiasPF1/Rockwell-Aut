# Playbook: Privilege Escalation
Trigger: alert_type = Privilege Escalation

ATT&CK mapping: this alert type covers three distinct scenarios, each with its own
technique - cited separately rather than forced into one ID:
  - Added to a privileged group (e.g. Domain Admins) outside change management:
    T1098.007 (Account Manipulation: Additional Local or Domain Groups) - Privilege Escalation (TA0004).
  - Local exploit used to obtain SYSTEM access: T1068 (Exploitation for Privilege
    Escalation) - Privilege Escalation (TA0004).
  - Unapproved sudo/root access granted on Linux/macOS: T1548.003 (Abuse Elevation
    Control Mechanism: Sudo and Sudo Caching) - Privilege Escalation (TA0004).
Source: MITRE ATT&CK Enterprise matrix, mitre/cti repo, MITRE's own Terms of Use
license (verified directly - not Apache 2.0; T1098's sub-technique list was checked
directly to find T1098.007 rather than guessed). Attribution: "(c) 2026 The MITRE
Corporation. This work is reproduced and distributed with the permission of The
MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
Group-membership change audit log (T1098.007), an EDR alert on a known local
privilege-escalation exploit pattern (T1068), or a sudoers/sudo-cache audit finding
(T1548.003) - three different log sources depending on which scenario this is.

## Analysis
Confirm whether the elevated access was granted through an approved change ticket.
If not, capture the process/command history that led to the escalation for
root-cause analysis, and check for any additional accounts/groups modified in the
same session.

## Containment
Revoke the unapproved elevated access immediately.

## Eradication
Check the account/host for lateral movement or additional persistence mechanisms
installed while elevated; if a local exploit was used (T1068), patch and reimage the
host so the same exploit can't be reused.

## Recovery
Restore the account to its correct, pre-escalation permission level; verify no
residual group memberships or sudo rules remain.

## Lessons Learned
Close as Remediated if access was correctly reverted and no further compromise
found; if this exposed a change-management gap (privileged group changes not
requiring approval), fix that gap, not just this instance.
