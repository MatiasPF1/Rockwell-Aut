# Playbook: Insider Threat / Data Exfiltration
Trigger: alert_type = Insider Threat

ATT&CK mapping: T1052.001 (Exfiltration Over Physical Medium: Exfiltration over USB) - Exfiltration (TA0010), for the removable-media pattern this alert type is built
around. Where the pattern is instead unusual access to data outside a user's normal
job function (no physical medium involved), there is no single precise ATT&CK
technique - ATT&CK models adversary tradecraft, not user-behavior/role-based
anomalies, so this part of the analysis leans on UEBA-style reasoning rather than a
technique ID. Source: MITRE ATT&CK Enterprise matrix, mitre/cti repo, MITRE's own
Terms of Use license (verified directly - not Apache 2.0). Attribution: "(c) 2026 The
MITRE Corporation. This work is reproduced and distributed with the permission of The
MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
DLP or endpoint policy flags data movement to removable media, or a UEBA-style rule
flags access/volume outside a user's normal pattern.

## Analysis
Confirm data volume, destination, and business justification with the user's manager
before assuming malicious intent - this alert type has a real false-positive rate
against legitimate but unusual work (e.g. an approved offboarding data handoff).

## Containment
If unjustified, suspend the user's access pending investigation. Do not tip off the
user prematurely if deliberate intent is suspected, since that risks destruction of
evidence.

## Eradication
Not typically applicable unless the removable media/destination can be recovered and
the copied data confirmed deleted - coordinate with Legal on this, since eradication
here often means legal/administrative action, not a technical fix.

## Recovery
Restore the user's access once cleared, or proceed to HR/Legal-led offboarding if
substantiated - preserve forensic evidence (do not wipe the device) throughout.

## Lessons Learned
Document chain of custody for all evidence collected; if this was a policy gap
(e.g. removable media should have been disabled for this role), close that gap.
