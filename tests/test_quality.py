from soc_agent.data import get_alert
from soc_agent.llm import MockLLM
from soc_agent.models import Alert, Investigation
from soc_agent.quality import check_against_investigation, check_alert


def codes(flags):
    return {f.code for f in flags}


def test_user_and_device_mismatch():
    # ALT-1001: description names WKS-9711 but affected_device is WKS-3702.
    assert "DEVICE_MISMATCH" in codes(check_alert(get_alert("ALT-1001")))
    # ALT-1003: description names jdoe59 but affected_user is jdoe19.
    assert "USER_MISMATCH" in codes(check_alert(get_alert("ALT-1003")))


def test_clean_alert_has_no_entity_flags():
    alert = Alert(alert_id="X-1", timestamp="2026-05-20T02:07:00Z", severity="High", source_system="EDR-Endpoint01",
                  affected_user="jdoe1", affected_device="WKS-1000",
                  description="EDR detected regsvr32.exe executing from /tmp on WKS-1000 used by jdoe1.")
    assert check_alert(alert) == []


def _inv(**overrides) -> Investigation:
    base = dict(
        incident_type="Ransomware Indicator", classification_rationale="", assessed_severity="Critical",
        severity_rationale="", recommended_action="isolate", action_rationale="", next_actions=[], steps=[],
        evidence_gaps=[], related_incident_ids=[], model_confidence=80, is_novel=False, playbook_proposal=None,
    )
    return Investigation(**{**base, **overrides})


def test_severity_conflict_and_source_mismatch():
    # ALT-1051: ransomware behaviour, reported Low, from Cloud WAF.
    alert = get_alert("ALT-1051")
    flags = check_against_investigation(alert, [], _inv())
    assert {"SEVERITY_CONFLICT", "SOURCE_MISMATCH"} <= codes(flags)


def test_mock_llm_is_labelled():
    assert MockLLM.name == "mock"
