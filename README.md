# Menu de Comandos Reversa para OpenClaude

Bridge que expõe os **skills do framework Reversa** (instalados em `.agents/skills/`
via `npx reversa install`) como **comandos slash** nativos do **OpenClaude**
(`@gitlawb/openclaude`) — por exemplo `/reversa`, `/reversa-new`, `/reversa-forward`.

> O Reversa é compatível com Agent Skills, mas o OpenClaude só descobre skills em
> diretórios específicos (`.openclaude/skills/` no projeto, e `~/.openclaude/skills/`
> no escopo do usuário). Como o Reversa instala em `.agents/skills/`, esses skills
> não aparecem por padrão. Este repo entrega um script bash que cria **symlinks**
> de `.openclaude/skills/<name>` para `.agents/skills/<name>`, fazendo com que o
> OpenClaude carregue cada `SKILL.md` como um comando slash.

## Por que funciona

O binário do OpenClaude (validado em `@gitlawb/openclaude@0.26.0`):

1. chama `loadSkillsFromSkillsDir(<projeto>/.openclaude/skills, "projectSettings")`
   e `loadSkillsFromSkillsDir(~/.openclaude/skills, "userSettings")`;
2. em `findSkillMarkdownFiles`, segue **explicitamente symlinks de diretório**:
   `if(entry.isSymbolicLink()) try { if((await fs.stat(entryPath)).isDirectory()) childDirs.push(entryPath) }`;
3. carrega qualquer arquivo `SKILL.md` (case-insensitive) dentro da pasta;
4. no frontmatter, `user-invocable` **defaults to `true`** quando omitido
   (`userInvocable: definition.userInvocable ?? !0`) — então skills sem
   `user-invocable` no frontmatter (como os do Reversa) ainda viram slash command;
5. o nome do comando é derivado da pasta-mãe via `getSkillCommandName(filePath, basePath)`,
   então `.openclaude/skills/reversa/SKILL.md` expõe `/reversa`.

Como os `SKILL.md` do Reversa já têm `name` e `description` no frontmatter,
**não é necessário gerar arquivos `.md` sintéticos** (ao contrário do bridge do
opencode). Basta apresentar a pasta original em `.openclaude/skills/`.

## Pré-requisitos

- `npx reversa install` já executado no projeto (de modo que `.agents/skills/reversa*/`
  exista).
- OpenClaude instalado (`npm i -g @gitlawb/openclaude`).
- Bash (Linux/macOS). No Windows, rode via Git Bash ou WSL — o agente traduz os
  comandos para PowerShell/zsh quando necessário.

## Instalação (primeira execução)

No projeto onde o Reversa já está instalado, abra o OpenClaude e cole:

> Execute o procedimento descrito em https://github.com/JosehRoberto/menu-reversa-openclaude para instalar os comandos do Reversa neste projeto.

O agente vai buscar este README e executar o **script de instalação segura** abaixo.

### Script de instalação segura (1ª execução)

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
AGENTS_SKILLS="$ROOT/.agents/skills"
OC_SKILLS="$ROOT/.openclaude/skills"

if [[ ! -d "$AGENTS_SKILLS" ]]; then
  echo "Aviso: $AGENTS_SKILLS não existe. Rode 'npx reversa install' primeiro."
  exit 1
fi

# Cria .openclaude/skills se não existir
mkdir -p "$OC_SKILLS"

# Backup se já houver links lá
if [[ -n "$(ls -A "$OC_SKILLS" 2>/dev/null)" ]]; then
  ts="$(date +%Y%m%d-%H%M%S)"
  backup="$ROOT/.openclaude/skills.bak.$ts"
  echo "Backup existente em $OC_SKILLS -> $backup"
  cp -a "$OC_SKILLS" "$backup"
fi

count=0
for src in "$AGENTS_SKILLS"/reversa*/; do
  [[ -d "$src" ]] || continue
  name="$(basename "$src")"
  target="../../.agents/skills/$name"
  link="$OC_SKILLS/$name"

  # Pula se já for um symlink válido apontando para o alvo certo
  if [[ -L "$link" && "$(readlink "$link")" == "$target" ]]; then
    echo "OK (existente): $name"
    continue
  fi

  # Se já existir (link quebrado, dir real, arquivo), pede confirmação
  if [[ -e "$link" || -L "$link" ]]; then
    echo "Conflito em $name:"
    ls -la "$link" || true
    read -r -p "Sobrescrever $link com symlink para $target? [y/N] " ok
    [[ "$ok" =~ ^[yY]$ ]] || { echo "Pulando $name"; continue; }
    rm -rf "$link"
  fi

  ln -s "$target" "$link"
  echo "Link criado: $link -> $target"
  count=$((count + 1))
done

echo "Concluído. $count symlink(s) criados. Reinicie o OpenClaude no projeto para ver /reversa*."
```

## Sincronização (após `npx reversa update`)

Quando o Reversa adiciona/remove skills, rode o prompt:

> Sincronize os comandos do Reversa com https://github.com/JosehRoberto/menu-reversa-openclaude

O agente executa o script de sincronização: cria symlinks novos, recalibra
existentes, e detecta **órfãos** (links em `.openclaude/skills/` cuja fonte em
`.agents/skills/` sumiu) pedindo confirmação antes de remover.

### Script de sincronização

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
AGENTS_SKILLS="$ROOT/.agents/skills"
OC_SKILLS="$ROOT/.openclaude/skills"

mkdir -p "$OC_SKILLS"

created=0; updated=0; removed=0

# 1) Cria/atualiza symlinks para cada skill atual
for src in "$AGENTS_SKILLS"/reversa*/; do
  [[ -d "$src" ]] || continue
  name="$(basename "$src")"
  target="../../.agents/skills/$name"
  link="$OC_SKILLS/$name"

  if [[ -L "$link" && "$(readlink "$link")" == "$target" ]]; then
    continue
  fi

  if [[ -e "$link" || -L "$link" ]]; then
    echo "Atualizar: $name (era $(readlink "$link" 2>/dev/null || echo 'não-symlink'))"
    read -r -p "Recriar $link -> $target? [y/N] " ok
    [[ "$ok" =~ ^[yY]$ ]] || { echo "Pulado $name"; continue; }
    rm -rf "$link"
    ln -s "$target" "$link"
    updated=$((updated + 1))
  else
    ln -s "$target" "$link"
    echo "Criado: $name"
    created=$((created + 1))
  fi
done

# 2) Detecta órfãos: symlinks em .openclaude/skills cuja fonte sumiu
if [[ -n "$(ls -A "$OC_SKILLS" 2>/dev/null)" ]]; then
  for link in "$OC_SKILLS"/*; do
    [[ -L "$link" ]] || continue
    name="$(basename "$link")"
    if [[ ! -d "$AGENTS_SKILLS/$name" ]]; then
      echo "Órfão: $name (fonte .agents/skills/$name não existe mais)"
      read -r -p "Remover $link? [y/N] " ok
      if [[ "$ok" =~ ^[yY]$ ]]; then
        rm -f "$link"
        removed=$((removed + 1))
      fi
    fi
  done
fi

echo "Sync concluído: $created criado(s), $updated atualizado(s), $removed órfão(s) removido(s)."
```

## Variantes

### Skills globais (qualquer projeto)
Para ter `/reversa*` em todos os projetos, crie os symlinks em `~/.openclaude/skills/`
apontando para uma cópia do Reversa central (ex.: `~/reversa/.agents/skills/<name>`).
Mude `OC_SKILLS="$HOME/.openclaude/skills"` e ajuste o `target` para o caminho
absoluto da fonte.

### Fallback sem symlink (Windows sem suporte a symlinks)
Use **cópia recursiva** em vez de link. Substitua o `ln -s "$target" "$link"` por:

```bash
cp -a "$src" "$link"
```

A desvantagem é que `npx reversa update` não reflete automaticamente — será
necessário rodar o script de sync para recopiar.

## Notas e segurança

- **Não** cria `opencode.json`, `opencode.jsonc`, `settings.json` nem qualquer
  config do OpenClaude. Só cria symlinks em `.openclaude/skills/`.
- Cria backup timestampado antes de sobrescrever qualquer symlink pré-existente.
- Pede confirmação explícita antes de sobrescrever/criar/remover.
- Não modifica os `SKILL.md` originais do Reversa; o symlink aponta para o mesmo
  arquivo, então `npx reversa update` reflete automaticamente.
- Não empacota nada como plugin Anthropic (`.claude-plugin/`), pois seria overkill
  para skills já residentes na árvore do projeto.
- Scripts em bash. O agente adapta para PowerShell/zsh/Git Bash conforme o SO.

## Compatibilidade

- OpenClaude `@gitlawb/openclaude@>=0.26.0` (mecanismo verificado: `findSkillMarkdownFiles`
  segue symlinks; `user-invocable` default `true`).
- Reversa instalado em `.agents/skills/reversa*` (qualquer versão com frontmatter
  `name`+`description`).

## Licença

MIT
