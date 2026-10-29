# Playbook: Phishing
Trigger: alert_type = Phishing

ATT&CK mapping: T1566.002 (Phishing: Spearphishing Link) - Initial Access (TA0001).
Source: MITRE ATT&CK Enterprise matrix, mitre/cti repo. License: MITRE's own Terms
of Use (non-exclusive, royalty-free, attribution required) - verified directly, not
Apache 2.0 as sometimes assumed. Attribution: "(c) 2026 The MITRE Corporation. This
work is reproduced and distributed with the permission of The MITRE Corporation."

Phase structure below follows NIST SP 800-61 Rev 2 (2012) - a US government work,
public domain under 17 U.S.C. S 105. Rev 2 was withdrawn in April 2025 and replaced
by Rev 3, which maps incident response to NIST CSF 2.0 functions instead of a fixed
phase list - this playbook intentionally keeps the Rev 2-era phase structure since
that is what was requested, labeled accurately rather than presented as current
guidance.

## Detection
Email gateway/URL-reputation alert on an inbound link, or a user report of a
suspicious message. Look for the T1566.002 indicators ATT&CK documents: mismatched
sender/reply-to domains, lookalike/typosquatted domains, and URL-reputation or
sandboxing engines flagging the destination.

## Analysis
Confirm whether the link was clicked and whether credentials were entered on the
destination page (check email gateway click-tracking and, if available, proxy/DNS
logs for the flagged domain). Determine scope: search for the same sender/domain/
subject across all mailboxes, not just the reporting user's.

## Containment
Block the sender domain and the linked domain at the email gateway and web proxy/DNS
layer. If any user clicked through, isolate that user's session (force logout) while
the credential-compromise question in Analysis is resolved.

## Eradication
Quarantine or recall all matching messages org-wide. If credentials were entered,
treat the account as compromised for eradication purposes, not just containment.

## Recovery
Force a password reset and MFA re-enrollment for any user who entered credentials;
restore normal mail flow once the domain is blocked and matching messages are
cleared.

## Lessons Learned
Log whether this specific lure (sender pattern, domain, pretext) evaded existing
email-gateway rules, and if so, tighten the matching rule rather than relying on
user reporting alone next time.
