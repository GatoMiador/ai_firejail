"""Localização dos arquivos de configuração.

Segue as diretrizes do GNOME/XDG: usa ``$XDG_CONFIG_HOME`` (por padrão
``~/.config``) e cria o subdiretório ``ai_firejail``. O banco SQLite guarda as
configurações; os perfis ficam como texto puro em ``profiles/``.
"""

import os

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib  # noqa: E402

from . import APP_NAME  # noqa: E402


def config_dir() -> str:
    """Diretório base de configuração (~/.config/ai_firejail)."""
    path = os.path.join(GLib.get_user_config_dir(), APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def profiles_dir() -> str:
    """Diretório onde ficam os arquivos .profile do firejail (texto puro)."""
    path = os.path.join(config_dir(), "profiles")
    os.makedirs(path, exist_ok=True)
    return path


def db_path() -> str:
    """Caminho do banco SQLite de configurações."""
    return os.path.join(config_dir(), "config.db")
