# Playbook: Brute Force / Credential Attack
Trigger: alert_type = Brute Force

ATT&CK mapping: T1110 (Brute Force) - Credential Access (TA0006). Where the pattern
is many accounts each tried a few times rather than one account tried many times,
see sub-technique T1110.003 (Password Spraying) specifically. Source: MITRE ATT&CK
Enterprise matrix, mitre/cti repo, MITRE's own Terms of Use license (verified
directly - not Apache 2.0). Attribution: "(c) 2026 The MITRE Corporation. This work
is reproduced and distributed with the permission of The MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
Authentication-log threshold alert: repeated failed logins for one account from one
source (T1110 classic pattern) or a low-and-slow spread of failed attempts across
many accounts from one or few sources (T1110.003 password-spray pattern) - the two
need different detection logic, since a per-account threshold alone misses spraying.

## Analysis
Determine which pattern this is (single-account brute force vs. spray) and whether
any attempt succeeded. Review the targeted account(s)' recent successful logins for
signs the attacker eventually got in.

## Containment
Block the source IP(s) at the perimeter firewall/VPN gateway. For a spray pattern,
consider a temporary global lockout-threshold tightening rather than only blocking
the observed source, since spray sources often rotate.

## Eradication
If any login succeeded, treat the account as compromised: force a password reset and
review for any changes made during the compromised session (mail rules, new MFA
devices registered, etc.).

## Recovery
Enroll the targeted account(s) in MFA if not already enrolled; restore normal login
availability once the source is blocked and no successful compromise is confirmed.

## Lessons Learned
Close as Contained if no successful login from the attacking source is found;
otherwise document how the attempt bypassed existing lockout thresholds and adjust
them.
