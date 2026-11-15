#!/usr/bin/env python3
"""Expoe os skills do Reversa como comandos slash no OpenClaude.

Nucleo unico, portatil (Linux, macOS e Windows) e nao interativo por padrao,
substituindo os scripts Bash embutidos no README.

O OpenClaude descobre skills em .openclaude/skills/ (projeto) e ~/.openclaude/skills/
(usuario). Como o Reversa instala em .agents/skills/, este script cria symlinks
(ou copias, com --copy) de .openclaude/skills/<name> para os skills reversa*.

Subcomandos:
  install   Primeira execucao: cria os links a partir de .agents/skills.
  sync      Sincronizacao: cria/atualiza links e remove orfaos com confirmacao.

Exemplos:
  python3 menu-reversa-openclaude.py install --yes
  python3 menu-reversa-openclaude.py sync --yes
  python3 menu-reversa-openclaude.py install --yes --copy
  python3 menu-reversa-openclaude.py install --yes --global
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_SKILLS_ROOT = ".agents/skills"
DEFAULT_OC_SKILLS_DIR = ".openclaude/skills"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="menu-reversa-openclaude.py",
        description="Expoe os skills do Reversa como comandos slash no OpenClaude.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("install", "Primeira execucao: cria os links/symlinks no OpenClaude."),
        ("sync", "Sincronizacao dos links, com deteccao de orfaos."),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("-y", "--yes", action="store_true",
                       help="Nao interativo: responde 'sim' a todas as confirmacoes.")
        p.add_argument("--dry-run", action="store_true",
                       help="Mostra o que seria feito sem alterar arquivos.")
        p.add_argument("--copy", action="store_true",
                       help="Copia os skills em vez de criar symlinks (use no Windows sem privilegio).")
        p.add_argument("--global", dest="global_scope", action="store_true",
                       help="Instala em ~/.openclaude/skills (escopo de usuario) em vez do projeto.")
        p.add_argument("--skills-root", default=DEFAULT_SKILLS_ROOT,
                       help=f"Raiz dos skills do Reversa (padrao: {DEFAULT_SKILLS_ROOT}).")
        p.add_argument("--oc-skills-dir", default=None,
                       help=f"Destino no OpenClaude (padrao: {DEFAULT_OC_SKILLS_DIR}; com --global: ~/.openclaude/skills).")

    return parser


def make_confirmer(auto_yes: bool):
    def confirm(prompt: str) -> bool:
        if auto_yes:
            print(f"{prompt} [y/N]: y (--yes)")
            return True
        try:
            response = input(f"{prompt} [y/N]: ")
        except EOFError:
            response = ""
        return response.strip().lower() in ("y", "yes", "s", "sim")

    return confirm


def find_skill_dirs(root: Path):
    names = set()
    for path in root.glob("reversa-*"):
        if path.is_dir():
            names.add(path.name)
    if (root / "reversa").is_dir():
        names.add("reversa")
    return sorted(names)


def dirs_equal(a: Path, b: Path) -> bool:
    if not b.is_dir() or b.is_symlink():
        return False
    a_files = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    b_files = sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    if a_files != b_files:
        return False
    for rel in a_files:
        if (a / rel).read_bytes() != (b / rel).read_bytes():
            return False
    return True


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


class Runner:
    def __init__(self, args):
        self.args = args
        self.skills_root = Path(args.skills_root)
        self.global_scope = args.global_scope
        if args.oc_skills_dir:
            self.oc_dir = Path(args.oc_skills_dir)
        elif self.global_scope:
            self.oc_dir = Path.home() / ".openclaude" / "skills"
        else:
            self.oc_dir = Path(DEFAULT_OC_SKILLS_DIR)
        self.copy = args.copy
        self.dry_run = args.dry_run
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.confirm = make_confirmer(args.yes)
        self.created = 0
        self.updated = 0
        self.removed = 0
        self.skipped = 0

    def target_for(self, src: Path) -> str:
        if self.global_scope:
            return str(src.resolve())
        return os.path.relpath(src.resolve(), self.oc_dir.resolve())

    def link_is_current(self, src: Path, link: Path, target: str) -> bool:
        if self.copy:
            return dirs_equal(src, link)
        return link.is_symlink() and os.readlink(link) == target

    @staticmethod
    def link_exists(link: Path) -> bool:
        return link.is_symlink() or link.exists()

    def create_link(self, src: Path, link: Path, target: str) -> None:
        if self.dry_run:
            kind = "copia" if self.copy else "symlink"
            print(f"[dry-run] Criaria {kind}: {link} -> {target}")
            return
        self.oc_dir.mkdir(parents=True, exist_ok=True)
        if self.copy:
            shutil.copytree(src, link)
        else:
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError) as exc:
                print(f"ERRO ao criar symlink {link}: {exc}")
                print("Use --copy para copiar os skills em vez de linkar.")
                raise SystemExit(1)

    def backup_existing(self) -> None:
        if not self.oc_dir.is_dir():
            return
        try:
            entries = list(self.oc_dir.iterdir())
        except OSError:
            return
        if not entries:
            return
        backup = self.oc_dir.parent / f"{self.oc_dir.name}.bak.{self.timestamp}"
        if self.dry_run:
            print(f"[dry-run] Backup: {self.oc_dir} -> {backup}")
            return
        shutil.copytree(self.oc_dir, backup, symlinks=True)
        print(f"Backup existente em {self.oc_dir} -> {backup}")

    def check_skills_root(self) -> bool:
        if not self.skills_root.is_dir():
            print(f"ERRO: diretório '{self.skills_root}' não encontrado.")
            print("Rode 'npx reversa install' primeiro.")
            return False
        return True

    def ensure_links(self, verbose_ok: bool) -> None:
        for name in find_skill_dirs(self.skills_root):
            src = self.skills_root / name
            link = self.oc_dir / name
            target = self.target_for(src)

            if self.link_is_current(src, link, target):
                if verbose_ok:
                    print(f"OK (existente): {name}")
                    self.skipped += 1
                continue

            if self.link_exists(link):
                print()
                print(f"Conflito em {name}: {link} já existe.")
                if self.confirm(f"Deseja sobrescrever {link} mantendo backup?"):
                    if not self.dry_run:
                        remove_path(link)
                    self.create_link(src, link, target)
                    print(f"Atualizado: {name}")
                    self.updated += 1
                else:
                    print(f"Mantido sem alteração: {name}")
                    self.skipped += 1
            else:
                self.create_link(src, link, target)
                print(f"Criado: {name}")
                self.created += 1

    def process_orphans(self) -> None:
        if not self.oc_dir.is_dir():
            return
        for entry in sorted(self.oc_dir.iterdir()):
            if not entry.is_symlink():
                continue
            name = entry.name
            if (self.skills_root / name).is_dir():
                continue
            print()
            print(f"Órfão detectado: {name} (fonte {self.skills_root / name} não existe mais)")
            if self.confirm(f"Deseja remover {entry}?"):
                if self.dry_run:
                    print(f"[dry-run] Removeria: {entry}")
                else:
                    entry.unlink()
                print(f"Removido: {name}")
                self.removed += 1
            else:
                print(f"Preservado: {name}")
                self.skipped += 1


def run_install(args) -> int:
    runner = Runner(args)
    print("==> Instalação segura dos comandos Reversa no OpenClaude")
    print()

    if not runner.check_skills_root():
        return 1

    if not runner.dry_run:
        runner.oc_dir.mkdir(parents=True, exist_ok=True)
    runner.backup_existing()

    if not runner.confirm(f"Deseja criar os comandos Reversa no OpenClaude em '{runner.oc_dir}'?"):
        print("Operação cancelada pelo usuário.")
        return 0

    print(f"Diretório de skills: {runner.skills_root}")
    print(f"Diretório do OpenClaude: {runner.oc_dir}")
    print()

    runner.ensure_links(verbose_ok=True)

    print()
    print("Resumo:")
    print(f" - Criados: {runner.created}")
    print(f" - Atualizados: {runner.updated}")
    print(f" - Ignorados: {runner.skipped}")
    print()
    print("Concluído com segurança.")
    print("Reinicie o OpenClaude no projeto para ver /reversa*.")
    return 0


def run_sync(args) -> int:
    runner = Runner(args)
    print("==> Sincronização segura dos comandos Reversa no OpenClaude")
    print()

    if not runner.check_skills_root():
        return 1

    if not runner.dry_run:
        runner.oc_dir.mkdir(parents=True, exist_ok=True)

    runner.ensure_links(verbose_ok=False)
    runner.process_orphans()

    print()
    print("Resumo:")
    print(f" - Criados: {runner.created}")
    print(f" - Atualizados: {runner.updated}")
    print(f" - Removidos: {runner.removed}")
    print(f" - Ignorados: {runner.skipped}")
    print()
    print("Sincronização concluída com segurança.")
    print("Reinicie o OpenClaude no projeto para refletir as mudanças.")
    return 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    if args.command == "install":
        return run_install(args)
    if args.command == "sync":
        return run_sync(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
