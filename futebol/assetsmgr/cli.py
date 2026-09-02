from __future__ import annotations

import argparse
import sys

import django
from django.conf import settings


def _setup() -> None:
    if not settings.configured:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        django.setup()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Sincroniza clubes, jogadores e assets da Série A.')
    parser.add_argument('--teams', action='store_true')
    parser.add_argument('--players', action='store_true')
    parser.add_argument('--assets', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--missing', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force', action='store_true')
    return parser


def flags_from_args(args) -> dict:
    seletivos = args.teams or args.players or args.assets or args.validate or args.missing
    return {
        'teams': args.teams or not seletivos,
        'players': args.players or not seletivos,
        'assets': args.assets or args.missing or not seletivos,
        'validate': args.validate or not seletivos,
        'missing_only': args.missing,
        'dry_run': args.dry_run,
        'force': args.force,
    }


def main(argv: list[str] | None = None) -> int:
    _setup()
    from futebol.assetsmgr.pipeline import sincronizar

    args = build_parser().parse_args(argv)
    relatorio = sincronizar(**flags_from_args(args), stdout=sys.stdout)
    return 1 if relatorio.get('downloads', {}).get('failed') else 0


if __name__ == '__main__':
    raise SystemExit(main())
