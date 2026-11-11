# AI_FIREJAIL

Interface gráfica **GTK4 / libadwaita** para o [firejail](https://firejail.wordpress.com/),
pensada para executar **algoritmos de IA** dentro de um sandbox. Você escolhe
quais diretórios ficam visíveis para o processo, organiza-os por prioridade e
dispara comandos de IA — no terminal ou não — a partir de **perfis**
reutilizáveis gravados como arquivos `.profile` do firejail.

![Categoria](https://img.shields.io/badge/GTK-4-blue) ![libadwaita](https://img.shields.io/badge/libadwaita-1.x-purple) ![Python](https://img.shields.io/badge/python-3.10%2B-green) ![Licença](https://img.shields.io/badge/licen%C3%A7a-GPL--3.0-orange)

---

## Recursos

- **Painel de diretórios permitidos** com botões de **adicionar**, **remover** e
  **alterar a prioridade** (ordem = ordem das regras `whitelist` no firejail).
- **Lista de comandos de IA**, cada um com uma chave que define se ele roda
  **dentro de um terminal** ou não. A lista é **editável nas preferências**
  (adicionar, editar, excluir e reordenar).
- **Perfis** selecionáveis: cada perfil é um conjunto de diretórios + opções do
  firejail, gravado como **texto puro** em um arquivo `.profile`.
- **Preferências** para gerenciar perfis (criar, renomear, excluir) e **editar
  as opções extras do firejail** de cada perfil (ex.: `caps.drop all`,
  `seccomp`, `net none`, `nodbus`).
- Configurações em **SQLite**; perfis em **texto puro**.
- Diretório de configuração conforme as diretrizes do GNOME/XDG:
  **`~/.config/ai_firejail`**.
- **Pacote Debian** para Pop!\_OS 24.04 (base Ubuntu *noble*).

---

## Como funciona

```
Janela principal                       Disco (~/.config/ai_firejail)
┌───────────────────────────┐
│ Perfil ativo:  [ default ▾]│         config.db            (SQLite)
│                            │           ├─ settings        (perfil ativo, terminal, opções globais)
│ Diretórios Permitidos   [+]│           └─ commands        (lista de comandos de IA)
│  ▸ /home/você/projeto  ↑↓🗑 │
│  ▸ /home/você/dados    ↑↓🗑 │         profiles/
│                            │           ├─ default.profile (texto puro p/ o firejail)
│ Comandos de IA          [✎]│           └─ ...
│  ▸ Python   [Terminal ▣] ▶ │
│  ▸ Jupyter  [Terminal ▢] ▶ │
└───────────────────────────┘
```

Ao clicar em **Executar**, o AI_FIREJAIL monta e dispara:

```
firejail --profile=~/.config/ai_firejail/profiles/<perfil>.profile [opções globais] -- <comando>
```

Se o comando estiver marcado como **Terminal**, ele é aberto dentro de um
emulador de terminal (detectado automaticamente, ou definido nas preferências).

Exemplo de arquivo de perfil gerado (`profiles/default.profile`):

```
# AI_FIREJAIL managed profile: default

whitelist /home/você/projeto
whitelist /home/você/dados

# --- opções extras do firejail (editáveis nas preferências) ---
caps.drop all
seccomp
net none
```

> As linhas `whitelist` são gerenciadas pelo painel principal; o restante é a
> área de "opções extras", editável em **Preferências → Perfis → Editar**.
> O arquivo é compatível com `firejail --profile=`, podendo ser usado também
> fora da interface.

---

## Dependências de execução

- `firejail`
- `python3` (3.10+)
- `python3-gi` (PyGObject)
- `gir1.2-gtk-4.0`
- `gir1.2-adw-1` (libadwaita)

No Pop!\_OS / Ubuntu 24.04:

```bash
sudo apt install firejail python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

---

## Executar a partir do código-fonte

```bash
cd ai_firejail
python3 -m ai_firejail
```

---

## Instalação como pacote Debian (Pop!_OS 24.04)

1. Instale as ferramentas e dependências de compilação:

   ```bash
   sudo apt install build-essential debhelper dh-python python3-all python3-setuptools devscripts
   ```

2. Gere o pacote a partir da raiz do projeto:

   ```bash
   dpkg-buildpackage -us -uc -b
   ```

   (ou `debuild -us -uc -b`). O arquivo `.deb` é criado no diretório acima
   (`../ai-firejail_0.1.0_all.deb`).

3. Instale:

   ```bash
   sudo apt install ../ai-firejail_0.1.0_all.deb
   ```

4. Abra pelo menu de aplicativos (**AI_FIREJAIL**) ou pelo terminal:

   ```bash
   ai-firejail
   ```

Para remover:

```bash
sudo apt remove ai-firejail
```

---

## Estrutura do projeto

```
ai_firejail/
├── ai_firejail/            # pacote Python
│   ├── application.py       # Adw.Application + ações (preferências, sobre, sair)
│   ├── window.py            # janela principal (perfil, diretórios, comandos)
│   ├── preferences.py       # preferências (comandos, perfis, geral)
│   ├── config.py            # configurações em SQLite
│   ├── profiles.py          # leitura/escrita dos arquivos .profile do firejail
│   ├── runner.py            # montagem e execução do comando firejail
│   └── paths.py             # localização XDG/GNOME dos arquivos
├── data/                    # .desktop, metainfo e ícone
├── debian/                  # empacotamento Debian/Ubuntu
├── pyproject.toml
└── README.md
```

---

## Onde ficam as configurações

| O quê                 | Onde                                                   | Formato    |
|-----------------------|--------------------------------------------------------|------------|
| Comandos de IA        | `~/.config/ai_firejail/config.db`                      | SQLite     |
| Perfil ativo, terminal, opções globais | `~/.config/ai_firejail/config.db`     | SQLite     |
| Perfis (diretórios + opções) | `~/.config/ai_firejail/profiles/*.profile`      | texto puro |

(O caminho respeita `$XDG_CONFIG_HOME`; `~/.config` é o padrão.)

---

## Licença

GPL-3.0-or-later. Veja o arquivo [LICENSE](LICENSE).
