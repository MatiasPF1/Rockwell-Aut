"""Regenerate knowledge/playbook_index.md: `python -m soc_agent.index`."""

from . import config
from .playbooks import build_index, validate_step_rules


def main() -> None:
    config.PLAYBOOK_INDEX.parent.mkdir(parents=True, exist_ok=True)
    config.PLAYBOOK_INDEX.write_text(build_index())
    print(f"Wrote {config.rel(config.PLAYBOOK_INDEX)}")
    for problem in validate_step_rules():
        print(f"WARNING: {problem}")


if __name__ == "__main__":
    main()
