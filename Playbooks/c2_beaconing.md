# Playbook: C2 Beaconing
Trigger: alert_type = C2 Beaconing

ATT&CK mapping: T1071 (Application Layer Protocol) - Command and Control (TA0011)
for periodic outbound connections generally; where domain-generation-algorithm
domains are involved specifically, T1568.002 (Dynamic Resolution: Domain Generation
Algorithms) - Command and Control (TA0011) applies (confirmed directly against the
current attack.mitre.org page). Source: MITRE ATT&CK Enterprise matrix, mitre/cti
repo, MITRE's own Terms of Use license (verified directly - not Apache 2.0).
Attribution: "(c) 2026 The MITRE Corporation. This work is reproduced and
distributed with the permission of The MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
Network sensor flags periodic outbound connections with regular beacon-interval
timing (T1071), or DNS requests to a newly-registered/algorithmically-generated
domain (T1568.002 DGA pattern).

## Analysis
Identify the initiating process and any dropped payloads or scheduled tasks that
establish persistence; check other hosts for connections to the same domain/IP or a
matching beacon-interval pattern, which would indicate lateral spread.

## Containment
Block the destination domain/IP at the firewall/DNS layer; isolate the beaconing
host from the network via EDR while preserving it for forensic capture (do not wipe
before capturing).

## Eradication
Remove the beaconing process and any persistence mechanism it installed; for
DGA-based C2, block the DGA pattern via threat-intel feed rather than only the
currently-observed domain, since new domains will register on the same algorithm.

## Recovery
Reimage the host once forensics are captured; close as Contained only after
confirming no other host still beacons to the same destination or matching pattern.

## Lessons Learned
If egress filtering would have caught this sooner (non-standard port, unapproved
destination), tighten egress rules rather than relying solely on beacon-pattern
detection next time.
