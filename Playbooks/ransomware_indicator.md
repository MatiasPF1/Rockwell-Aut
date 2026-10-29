# Playbook: Ransomware Indicator
Trigger: alert_type = Ransomware Indicator

ATT&CK mapping: T1486 (Data Encrypted for Impact) - Impact (TA0040), for the
end-state this alert type warns of. The specific precursor behavior this alert type
is built around - shadow-copy deletion via vssadmin/wmic immediately before mass
file changes - maps precisely to T1490 (Inhibit System Recovery) - Impact (TA0040);
this is the exact, verified technique (confirmed directly against the current
attack.mitre.org page, which documents "vssadmin.exe delete shadows /all /quiet" as
the canonical example, used by WannaCry, BlackCat, Conti, LockBit and others).
Source: MITRE ATT&CK Enterprise matrix, mitre/cti repo, MITRE's own Terms of Use
license (verified directly - not Apache 2.0). Attribution: "(c) 2026 The MITRE
Corporation. This work is reproduced and distributed with the permission of The
MITRE Corporation."

Phase structure follows NIST SP 800-61 Rev 2 (2012, public domain, withdrawn April
2025).

## Detection
EDR/behavioral rule flags shadow-copy deletion (T1490) or mass file-rename/
encryption activity across shares (T1486) - T1490 firing FIRST, before mass changes
begin, is the highest-value early-warning signal this alert type is designed to
catch.

## Analysis
Determine blast radius immediately: which hosts/shares show the same pattern. This
is time-critical - ransomware spreads faster than most other alert types on this
list, so Analysis and Containment often happen in parallel rather than sequentially.

## Containment
Isolate the affected host(s) from the network immediately - do not power off (this
destroys memory forensics and can trigger some ransomware's "wipe on shutdown"
behavior). If shadow-copy deletion is still in progress, disable/kill that process
first.

## Eradication
Identify and disable the responsible process; confirm no other host on the same
subnet is still executing the same pattern before considering eradication complete.

## Recovery
Restore affected files from the most recent clean backup once the host is confirmed
contained - verify backup integrity before restoring, since some ransomware
campaigns specifically target backup infrastructure first.

## Lessons Learned
Treat every T1490 (shadow-copy deletion) sighting as a major-incident trigger going
forward, even in isolation - waiting for confirmed encryption before escalating
costs valuable containment time.
