# Playbook: DDoS
Trigger: alert_type = DDoS

ATT&CK mapping: T1498 (Network Denial of Service) - Impact (TA0040). Where the
traffic is a straightforward volumetric flood (not reflection/amplification), see
sub-technique T1498.001 (Direct Network Flood) specifically. Source: MITRE ATT&CK
Enterprise matrix, mitre/cti repo, MITRE's own Terms of Use license (verified
directly - not Apache 2.0). Attribution: "(c) 2026 The MITRE Corporation. This work
is reproduced and distributed with the permission of The MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
CDN/upstream provider or internal monitoring flags a traffic-volume spike far above
baseline, sourced from an unusually large or geographically dispersed set of IPs.

## Analysis
Confirm this is not a legitimate load event (marketing launch, viral traffic) before
treating it as an attack - check the traffic-source pattern (organic referrers vs.
uniform/scripted requests) and whether it targets a specific endpoint (e.g. login)
rather than the site broadly, which points toward an application-layer attack rather
than pure volumetric flood.

## Containment
Enable upstream scrubbing/CDN rerouting for the affected service; for
application-layer floods targeting a specific endpoint, add rate-limiting/CAPTCHA at
that endpoint specifically rather than only at the network edge.

## Eradication
Not typically applicable in the traditional malware-removal sense - "eradication"
here means confirming the flood source(s) are fully blocked/filtered, not just
mitigated in effect.

## Recovery
Monitor service health until traffic returns to baseline; close as Mitigated once
confirmed stable for 30 minutes.

## Lessons Learned
If this targeted a specific endpoint rather than the whole service, add permanent
rate-limiting there rather than relying on reactive scrubbing next time.
