# Playbook: Data Exfiltration
Trigger: alert_type = Data Exfiltration

ATT&CK mapping: T1567.002 (Exfiltration Over Web Service: Exfiltration to Cloud
Storage) - Exfiltration (TA0010), for the "uploaded to external cloud storage/
personal email" pattern this alert type is built around. Source: MITRE ATT&CK
Enterprise matrix, mitre/cti repo, MITRE's own Terms of Use license (verified
directly - not Apache 2.0). Attribution: "(c) 2026 The MITRE Corporation. This work
is reproduced and distributed with the permission of The MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
DLP or proxy/CASB rule flags an outbound transfer to an external cloud-storage
domain or personal email account, especially one matching sensitive-data patterns
(PII, financials, source code).

## Analysis
Identify the destination and confirm it is not a sanctioned business service (a
personal Dropbox/Gmail account vs. an approved corporate cloud tenant materially
changes the response). Determine what data left: file names/types and volume.

## Containment
Block the outbound channel at the proxy/CASB; suspend the source account's outbound
access pending review. Do not tip off the user if insider intent is suspected (see
insider_threat.md for the closely related decision tree).

## Eradication
Request a takedown from the destination cloud provider if the data was confirmed
sensitive and the transfer unauthorized.

## Recovery
Restore normal access once cleared, or hand off to HR/Legal-led process if
substantiated - preserve proxy/DLP logs and the affected endpoint's file-access
history as evidence throughout.

## Lessons Learned
Escalate to Legal/Privacy if regulated data (PII, PCI, PHI) was confirmed involved;
otherwise close as Contained once the channel is blocked, and note whether this
destination category (personal cloud storage) needs a standing block rather than
per-incident handling.
