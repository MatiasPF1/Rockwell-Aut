from soc_agent.data import load_csv_alerts, load_incidents
from soc_agent.playbooks import L1_PHASES, build_index, load_playbooks, playbooks_by_type, validate_step_rules
from soc_agent.retrieval import PlaceholderRetriever


def test_every_incident_type_has_a_playbook():
    types = {i.alert_type for i in load_incidents()}
    assert types == set(playbooks_by_type())


def test_playbooks_have_l1_sections():
    for book in load_playbooks().values():
        for phase in L1_PHASES:
            assert book.sections.get(phase), f"{book.slug} missing {phase}"


def test_step_overlay_matches_playbook_text():
    assert validate_step_rules() == []


def test_index_lists_every_playbook():
    index = build_index()
    for slug in load_playbooks():
        assert f"`{slug}`" in index


def test_retriever_contract():
    incidents = load_incidents()
    retriever = PlaceholderRetriever()
    for alert in load_csv_alerts()[:40]:
        matches = retriever.retrieve(alert, incidents, 3)
        assert len(matches) <= 3
        assert all(0 <= m.score <= 1 for m in matches)
        assert [m.score for m in matches] == sorted((m.score for m in matches), reverse=True)
