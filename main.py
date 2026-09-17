from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import MetaHIAEngine
from kernel2 import Node, NodeRef, OBSERVATION


def demo_engine() -> dict:
    observations = (
        Node('obs1', OBSERVATION, (NodeRef('PERE_DE'), NodeRef('Alice'), NodeRef('Bob'))),
        Node('obs2', OBSERVATION, (NodeRef('MERE_DE'), NodeRef('Alice'), NodeRef('Claire'))),
        Node('obs3', OBSERVATION, (NodeRef('FRERE_DE'), NodeRef('Bob'), NodeRef('Claire'))),
    )
    return MetaHIAEngine(observations).summary()


def main() -> None:
    parser = argparse.ArgumentParser(description='MetaHIA clean-core runner')
    parser.add_argument('--demo', action='store_true', help='run the structured-input demo')
    parser.add_argument('--output', type=Path, default=None, help='write JSON result to file')
    args = parser.parse_args()
    if not args.demo:
        parser.error('current release accepts structured observations; use --demo')
    result = demo_engine()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        args.output.write_text(payload + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
