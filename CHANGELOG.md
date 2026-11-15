# Changelog

> Convenção: skill `changelog-convention`.
> Ordem **cronológica decrescente**; **não** misturar séries de numeração sem a nota + divisor.

## [Unreleased]

## [1.0.0] - 2026-11-15

### v1.0 (15/11/2026) — Núcleo Python determinístico e multiplataforma (bridge OpenClaude)

- **Adicionado:** `menu-reversa-openclaude.py` — núcleo único, portátil (Linux/macOS/Windows) e não interativo, com subcomandos `install` e `sync`. Substitui os scripts shell embutidos no README.
- **Adicionado:** flags `--yes`, `--dry-run`, `--copy`, `--global`, `--skills-root`, `--oc-skills-dir`.
- **Adicionado:** fallback `--copy` (copia os skills em vez de symlink), necessário no Windows sem Developer Mode/admin.
- **Adicionado:** variante `--global` para `~/.openclaude/skills` (alvos absolutos).
- **Adicionado:** wrappers finos `bin/install.sh` e `bin/sync.sh` (Linux/macOS) e `bin/install.ps1` e `bin/sync.ps1` (Windows 10/11).
- **Adicionado:** testes em `tests/test_menu_reversa_openclaude.py` (13 testes), incluindo symlink, cópia, conflito, órfãos, escopo global, determinismo e wrapper bash.
- **Alterado:** README reescrito para fluxo determinístico (versão fixada + execução não interativa), preservando a seção "Por que funciona" (internos do OpenClaude) e com troubleshooting de symlink no Windows.
- **Nota:** diferente dos menus do OpenCode, este repositório **não** gera arquivos `.md` nem usa PyYAML; expõe os skills do Reversa ao OpenClaude via symlinks (ou cópias).
- **Arquivos:** `menu-reversa-openclaude.py`, `bin/*`, `tests/test_menu_reversa_openclaude.py`, `README.md`.
- **Testes:** +13. Suíte em **13**.

---

> **Nota de versionamento.** O `[1.0.0]` (nov/2026) inaugura a **série atual** do projeto `menu-reversa-openclaude`, baseada no núcleo Python. O bloco abaixo — `[0.x]`, com data **até 2026-11-15** — é o **histórico legado** da numeração anterior, baseada em script shell embutido no README.

## Histórico legado (pré-v1 — até 2026-11-15)

## [0.1.0] - 2026-11-15

### v0.1 (15/11/2026) — Bridge com scripts shell embutidos no README

- **Adicionado:** README com scripts Bash (instalação e sincronização) que criam symlinks de `.openclaude/skills/` para `.agents/skills/reversa*` (commit `bb111ba`).
- **Arquivos:** `README.md`.
- **Testes:** 0.

---

## Legenda

- **Adicionado** — novas funcionalidades
- **Alterado** — mudanças em funcionalidades existentes
- **Corrigido** — correções de bugs
- **Removido** — funcionalidades removidas
- **Segurança** — correções de vulnerabilidades
- **Obsoleto** — funcionalidades marcadas para remoção futura
