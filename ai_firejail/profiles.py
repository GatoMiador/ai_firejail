"""Gerência dos arquivos .profile do firejail (texto puro).

Cada perfil é um arquivo ``<nome>.profile`` em ``profiles_dir()`` que pode ser
passado diretamente ao firejail com ``--profile=<arquivo>``.

Estrutura gerada:

    # AI_FIREJAIL managed profile: <nome>
    whitelist /caminho/um          <- diretórios permitidos (ordem = prioridade)
    whitelist /caminho/dois
    # --- opções extras do firejail (editáveis nas preferências) ---
    caps.drop all                  <- qualquer outra opção do firejail
    seccomp

As linhas ``whitelist`` são gerenciadas pelo painel principal; o restante é a
área de "opções extras", editável nas preferências.
"""

import os

from .paths import profiles_dir

_HEADER = "# AI_FIREJAIL managed profile"
_SEP = "# --- opções extras do firejail (editáveis nas preferências) ---"
_WL = "whitelist "


def profile_path(name: str) -> str:
    return os.path.join(profiles_dir(), f"{name}.profile")


def list_profiles() -> list[str]:
    names = [
        f[:-len(".profile")]
        for f in os.listdir(profiles_dir())
        if f.endswith(".profile")
    ]
    return sorted(names, key=str.lower)


def exists(name: str) -> bool:
    return os.path.exists(profile_path(name))


def read_profile(name: str) -> tuple[list[str], str]:
    """Retorna (lista_de_diretórios, texto_das_opções_extras)."""
    path = profile_path(name)
    directories: list[str] = []
    extras: list[str] = []
    if not os.path.exists(path):
        return directories, ""
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if stripped.startswith(_WL):
                directories.append(stripped[len(_WL):].strip())
            elif stripped == "" or stripped == _SEP or stripped.startswith(_HEADER):
                continue
            else:
                extras.append(line)
    return directories, "\n".join(extras)


def write_profile(name: str, directories: list[str], extras_text: str = ""):
    """Grava o arquivo .profile preservando a ordem dos diretórios."""
    lines = [f"{_HEADER}: {name}", ""]
    for directory in directories:
        directory = directory.strip()
        if directory:
            lines.append(f"{_WL}{directory}")
    lines.append("")
    lines.append(_SEP)
    extras = extras_text.strip("\n")
    if extras.strip():
        lines.append(extras)
    content = "\n".join(lines).rstrip("\n") + "\n"
    with open(profile_path(name), "w", encoding="utf-8") as fh:
        fh.write(content)


def create_profile(name: str):
    if not exists(name):
        write_profile(name, [], "")


def delete_profile(name: str):
    path = profile_path(name)
    if os.path.exists(path):
        os.remove(path)


def rename_profile(old: str, new: str):
    if exists(old) and not exists(new):
        os.rename(profile_path(old), profile_path(new))


def raw_text(name: str) -> str:
    path = profile_path(name)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()
