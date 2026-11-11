"""Camada de configuração em SQLite.

Guarda:
  * ``settings``  -> pares chave/valor (perfil ativo, terminal, opções globais…)
  * ``commands``  -> lista de comandos de IA (nome, comando, rodar no terminal,
                     posição para ordenação).

Os diretórios permitidos NÃO ficam aqui: eles são gravados como texto puro nos
arquivos .profile do firejail (ver :mod:`ai_firejail.profiles`).
"""

import sqlite3
from dataclasses import dataclass

from .paths import db_path


@dataclass
class Command:
    id: int
    name: str
    command: str
    run_in_terminal: bool
    position: int


_DEFAULT_COMMANDS = [
    # (nome, comando, rodar_no_terminal)
    ("Shell (bash)", "bash", True),
    ("Python", "python3", True),
    ("Jupyter Lab", "jupyter lab", False),
]


class Config:
    """Acesso ao banco de configurações."""

    def __init__(self, path: str | None = None):
        self.path = path or db_path()
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()
        self._seed()

    # -- esquema ---------------------------------------------------------
    def _init_schema(self):
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS commands (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                command         TEXT NOT NULL,
                run_in_terminal INTEGER NOT NULL DEFAULT 0,
                position        INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def _seed(self):
        """Cria comandos de exemplo apenas na primeira execução."""
        if self.get_setting("seeded") == "1":
            return
        for name, command, term in _DEFAULT_COMMANDS:
            self.add_command(name, command, term)
        self.set_setting("seeded", "1")

    # -- settings --------------------------------------------------------
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        self._conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()

    # -- comandos --------------------------------------------------------
    def list_commands(self) -> list[Command]:
        rows = self._conn.execute(
            "SELECT * FROM commands ORDER BY position, id"
        ).fetchall()
        return [
            Command(r["id"], r["name"], r["command"],
                    bool(r["run_in_terminal"]), r["position"])
            for r in rows
        ]

    def add_command(self, name: str, command: str,
                    run_in_terminal: bool = False) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS p FROM commands"
        ).fetchone()
        pos = row["p"]
        cur = self._conn.execute(
            "INSERT INTO commands(name, command, run_in_terminal, position) "
            "VALUES(?, ?, ?, ?)",
            (name, command, int(run_in_terminal), pos),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_command(self, cmd_id: int, *, name: str | None = None,
                       command: str | None = None,
                       run_in_terminal: bool | None = None):
        fields, values = [], []
        if name is not None:
            fields.append("name = ?"); values.append(name)
        if command is not None:
            fields.append("command = ?"); values.append(command)
        if run_in_terminal is not None:
            fields.append("run_in_terminal = ?"); values.append(int(run_in_terminal))
        if not fields:
            return
        values.append(cmd_id)
        self._conn.execute(
            f"UPDATE commands SET {', '.join(fields)} WHERE id = ?", values
        )
        self._conn.commit()

    def delete_command(self, cmd_id: int):
        self._conn.execute("DELETE FROM commands WHERE id = ?", (cmd_id,))
        self._conn.commit()

    def move_command(self, cmd_id: int, delta: int):
        """Move um comando para cima (delta=-1) ou para baixo (delta=+1)."""
        cmds = self.list_commands()
        idx = next((i for i, c in enumerate(cmds) if c.id == cmd_id), None)
        if idx is None:
            return
        new = idx + delta
        if new < 0 or new >= len(cmds):
            return
        cmds[idx], cmds[new] = cmds[new], cmds[idx]
        for pos, c in enumerate(cmds):
            self._conn.execute(
                "UPDATE commands SET position = ? WHERE id = ?", (pos, c.id)
            )
        self._conn.commit()
