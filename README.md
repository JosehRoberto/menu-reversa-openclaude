# Menu de Comandos Reversa para OpenClaude

Bridge que expõe os **skills do framework Reversa** (instalados em `.agents/skills/` via `npx reversa install`) como **comandos slash** nativos do **OpenClaude** (`@gitlawb/openclaude`) — por exemplo `/reversa`, `/reversa-new`, `/reversa-forward`.

A partir da versão 1, a lógica deixou de ser um script shell embutido no README e passou a ser um **núcleo Python único e portátil** (`menu-reversa-openclaude.py`), com wrappers finos por sistema operacional. Isso torna a execução **determinística** em Linux, macOS e Windows.

> O Reversa é compatível com Agent Skills, mas o OpenClaude só descobre skills em diretórios específicos (`.openclaude/skills/` no projeto, e `~/.openclaude/skills/` no escopo do usuário). Como o Reversa instala em `.agents/skills/`, esses skills não aparecem por padrão. Este repositório entrega um script que cria **symlinks** (ou cópias, com `--copy`) de `.openclaude/skills/<name>` para `.agents/skills/<name>`, fazendo com que o OpenClaude carregue cada `SKILL.md` como um comando slash.

## Por que funciona

O binário do OpenClaude (validado em `@gitlawb/openclaude@0.26.0`):

1. chama `loadSkillsFromSkillsDir(<projeto>/.openclaude/skills, "projectSettings")` e `loadSkillsFromSkillsDir(~/.openclaude/skills, "userSettings")`;
2. em `findSkillMarkdownFiles`, segue **explicitamente symlinks de diretório**: `if(entry.isSymbolicLink()) try { if((await fs.stat(entryPath)).isDirectory()) childDirs.push(entryPath) }`;
3. carrega qualquer arquivo `SKILL.md` (case-insensitive) dentro da pasta;
4. no frontmatter, `user-invocable` **defaults to `true`** quando omitido (`userInvocable: definition.userInvocable ?? !0`) — então skills sem `user-invocable` no frontmatter (como os do Reversa) ainda viram slash command;
5. o nome do comando é derivado da pasta-mãe via `getSkillCommandName(filePath, basePath)`, então `.openclaude/skills/reversa/SKILL.md` expõe `/reversa`.

Como os `SKILL.md` do Reversa já têm `name` e `description` no frontmatter, **não é necessário gerar arquivos `.md` sintéticos** (ao contrário do bridge do OpenCode). Basta apresentar a pasta original em `.openclaude/skills/`.

## Pré-requisitos

- **Python 3** (não requer PyYAML).
- **Reversa instalado** no projeto (`npx reversa install`), de modo que `.agents/skills/reversa*/` exista.
- **OpenClaude** instalado (`npm i -g @gitlawb/openclaude`).
- **Bash** (Linux/macOS) ou **PowerShell** (Windows 10/11).
- **git** (para o fluxo via prompt ou clonagem).

> **Windows:** a criação de symlinks exige *Developer Mode* ou privilégios de administrador. Sem isso, use `--copy`.

## Instalação

### Opção A — via prompt (recomendada)

No projeto onde o Reversa já está instalado, abra o agente e cole:

```text
Instale os comandos Reversa no OpenClaude usando a versão fixada v1.0.0 do repositório https://github.com/JosehRoberto/menu-reversa-openclaude.

Procedimento:
1. Clone a versão fixada em uma pasta temporária do sistema:
   git clone --branch v1.0.0 --depth 1 https://github.com/JosehRoberto/menu-reversa-openclaude.git
2. Garanta Python 3 no ambiente atual.
3. Na raiz do meu projeto, execute o instalador não interativo:
   - Linux/macOS: bash <pasta-clonada>/bin/install.sh --yes
   - Windows: powershell -ExecutionPolicy Bypass -File <pasta-clonada>\bin\install.ps1 --yes
   (No Windows sem privilégio de symlink, acrescente --copy.)
4. Crie backup de qualquer link/arquivo existente antes de sobrescrever.
5. Ao final, informe o resumo (criados, atualizados, ignorados).
```

### Opção B — execução manual

Clone a versão fixada e execute o wrapper **dentro da raiz do projeto onde o Reversa está instalado**:

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/JosehRoberto/menu-reversa-openclaude.git /tmp/menu-reversa-openclaude
```

**Linux / macOS:**

```bash
bash /tmp/menu-reversa-openclaude/bin/install.sh --yes
```

**Windows 10/11 (PowerShell):**

```powershell
powershell -ExecutionPolicy Bypass -File C:\caminho\menu-reversa-openclaude\bin\install.ps1 --yes
```

Reinicie o OpenClaude no projeto para ver `/reversa*`.

> O núcleo cria `.openclaude/skills/`, faz **backup** da pasta se já houver conteúdo e cria um symlink por skill `reversa*` (pulando links válidos e pedindo confirmação em conflitos).

## Sincronização (após `npx reversa update`)

Quando o Reversa adiciona/remove skills, sincronize (cria links novos, recalibra existentes e remove **órfãos** com confirmação):

**Linux / macOS:**

```bash
bash /tmp/menu-reversa-openclaude/bin/sync.sh --yes
```

**Windows 10/11 (PowerShell):**

```powershell
powershell -ExecutionPolicy Bypass -File C:\caminho\menu-reversa-openclaude\bin\sync.ps1 --yes
```

Ou use o núcleo direto, em qualquer sistema:

```bash
python3 menu-reversa-openclaude.py install --yes
python3 menu-reversa-openclaude.py sync --yes
```

## Arquitetura

| Arquivo | Papel |
|---|---|
| `menu-reversa-openclaude.py` | Núcleo único, portátil. Contém toda a lógica. Subcomandos `install` e `sync` |
| `bin/install.sh`, `bin/sync.sh` | Wrappers finos para Linux/macOS (bash 3.2+) |
| `bin/install.ps1`, `bin/sync.ps1` | Wrappers finos para Windows (PowerShell) |

Os wrappers apenas detectam o Python 3 (`python3` → `python` → `py -3`) e chamam o núcleo. Toda a lógica vive em `menu-reversa-openclaude.py`.

## Flags do `menu-reversa-openclaude.py`

| Flag | Descrição |
|---|---|
| `--yes` / `-y` | Não interativo: responde "sim" a todas as confirmações |
| `--dry-run` | Mostra o que seria feito, sem alterar arquivos |
| `--copy` | Copia os skills em vez de criar symlinks (Windows sem privilégio) |
| `--global` | Instala em `~/.openclaude/skills` (escopo de usuário) |
| `--skills-root DIR` | Raiz dos skills do Reversa (padrão: `.agents/skills`) |
| `--oc-skills-dir DIR` | Destino no OpenClaude (padrão: `.openclaude/skills`) |

## Variantes

### Skills globais (qualquer projeto)

Use `--global` para criar os links em `~/.openclaude/skills`, apontando (por caminho absoluto) para a cópia central do Reversa:

```bash
python3 menu-reversa-openclaude.py install --yes --global
```

### Fallback sem symlink (Windows sem suporte a symlinks)

Use `--copy`: copia cada skill em vez de linkar. A desvantagem é que `npx reversa update` não se reflete automaticamente — rode `sync` para recopiar.

```bash
python3 menu-reversa-openclaude.py install --yes --copy
```

## O que este repositório faz de diferente

- Cobre **`reversa-*`** (e o skill `reversa` sem sufixo, se existir). Skills sem esse prefixo (ex.: `impeccable`) são ignoradas.
- Cria **symlinks relativos determinísticos** (`../../.agents/skills/<name>`) no escopo do projeto, ou **absolutos** no escopo global.
- Faz **backup** da pasta `.openclaude/skills` (`.openclaude/skills.bak.<timestamp>`) antes de mexer, quando já há conteúdo.
- Pede confirmação antes de sobrescrever/criar/remover; em modo `--yes` age sem intervenção.
- Não cria `opencode.json`, `opencode.jsonc`, `settings.json` nem qualquer config do OpenClaude. Só cria links/cópias em `.openclaude/skills/`.
- Não modifica os `SKILL.md` originais do Reversa; no modo symlink, `npx reversa update` reflete automaticamente.
- Detecta **órfãos** (links cuja fonte sumiu) e remove com confirmação.

## Matriz de compatibilidade

| Plataforma | Wrapper | Requisitos | Symlink |
|---|---|---|---|
| Ubuntu / Debian / Fedora / Mint | `bin/*.sh` | bash, python3 | Nativo |
| macOS | `bin/*.sh` | python3 | Nativo |
| Windows 10/11 | `bin/*.ps1` | Python 3 | Requer Developer Mode/admin; senão `--copy` |

## Solução de problemas

### Windows: "symlink privilege not held" / OSError ao criar link

Sem *Developer Mode* nem admin, o Windows não permite symlinks. Use `--copy`:

```powershell
powershell -ExecutionPolicy Bypass -File C:\caminho\menu-reversa-openclaude\bin\install.ps1 --yes --copy
```

### Os comandos `/reversa*` não aparecem no OpenClaude

- Confirme que existem links/cópias em `.openclaude/skills/`.
- Reinicie o OpenClaude no projeto.
- Verifique se o `SKILL.md` original existe em `.agents/skills/reversa*/`.

### `ERRO: diretório '.agents/skills' não encontrado`

Você não está na raiz do projeto onde o Reversa foi instalado. Rode `npx reversa install` e execute o wrapper nessa pasta.

### `npx reversa update` adicionou skills mas os comandos não mudaram

Rode o `sync`. No modo `--copy`, é obrigatório para refletir novas versões.

## Notas e segurança

- **Não** cria configuração do OpenClaude; apenas links/cópias em `.openclaude/skills/`.
- Cria backup timestampado antes de sobrescrever a pasta `.openclaude/skills`.
- Pede confirmação explícita antes de sobrescrever/criar/remover.
- Não empacota nada como plugin Anthropic (`.claude-plugin/`).

## Compatibilidade

- OpenClaude `@gitlawb/openclaude@>=0.26.0` (mecanismo verificado: `findSkillMarkdownFiles` segue symlinks; `user-invocable` default `true`).
- Reversa instalado em `.agents/skills/reversa*` (qualquer versão com frontmatter `name`+`description`).

## Legado (script shell, v0)

A versão anterior baseada em script shell embutido no README continua disponível no histórico:

- README histórico: <https://github.com/JosehRoberto/menu-reversa-openclaude/blob/bb111ba/README.md>
- Prompt legado: `Execute o procedimento descrito em https://github.com/JosehRoberto/menu-reversa-openclaude/blob/bb111ba/README.md ...`

O fluxo legado exige Git Bash ou WSL no Windows e não é determinístico entre sistemas; prefira as opções A ou B acima.

## Licença

MIT
