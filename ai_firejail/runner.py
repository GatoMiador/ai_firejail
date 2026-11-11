"""Monta e executa os comandos do firejail."""

import shlex
import shutil
import subprocess

from .profiles import profile_path

# Emuladores de terminal conhecidos e como passar um comando a eles.
_TERMINALS = [
    ("ptyxis", ["ptyxis", "--"]),           # terminal padrão do GNOME 47+
    ("kgx", ["kgx", "--"]),                  # GNOME Console
    ("gnome-terminal", ["gnome-terminal", "--"]),
    ("tilix", ["tilix", "-e"]),
    ("konsole", ["konsole", "-e"]),
    ("xfce4-terminal", ["xfce4-terminal", "-x"]),
    ("alacritty", ["alacritty", "-e"]),
    ("kitty", ["kitty"]),
    ("xterm", ["xterm", "-e"]),
]


def firejail_available() -> bool:
    return shutil.which("firejail") is not None


def detect_terminal(preferred: str | None = None) -> list[str] | None:
    """Retorna o prefixo de argv do terminal a usar, ou None."""
    if preferred and preferred.strip():
        parts = shlex.split(preferred)
        if parts and shutil.which(parts[0]):
            return parts
    for exe, argv in _TERMINALS:
        if shutil.which(exe):
            return list(argv)
    return None


def build_firejail_argv(profile_name: str, command: str,
                        extra_args: list[str] | None = None) -> list[str]:
    """argv do firejail: firejail --profile=<arq> [extras] -- <comando>."""
    argv = ["firejail", f"--profile={profile_path(profile_name)}"]
    if extra_args:
        argv += extra_args
    argv.append("--")
    argv += shlex.split(command)
    return argv


def run(profile_name: str, command: str, *, in_terminal: bool = False,
        terminal_pref: str | None = None,
        extra_args: list[str] | None = None,
        cwd: str | None = None) -> list[str]:
    """Executa o comando dentro do sandbox. Retorna o argv efetivamente usado.

    Levanta RuntimeError em caso de pré-condições não atendidas.
    """
    if not firejail_available():
        raise RuntimeError("O firejail não está instalado (apt install firejail).")
    if not command.strip():
        raise RuntimeError("Comando vazio.")

    fj_argv = build_firejail_argv(profile_name, command, extra_args)

    if in_terminal:
        term = detect_terminal(terminal_pref)
        if not term:
            raise RuntimeError("Nenhum emulador de terminal foi encontrado.")
        inner = " ".join(shlex.quote(a) for a in fj_argv)
        # Mantém o terminal aberto ao fim para o usuário ver a saída.
        bash_cmd = (
            f"{inner}; status=$?; echo; "
            f'echo "[AI_FIREJAIL] processo finalizado (código $status)"; '
            f'read -n1 -r -p "Pressione uma tecla para fechar..."'
        )
        argv = term + ["bash", "-lc", bash_cmd]
    else:
        argv = fj_argv

    subprocess.Popen(argv, cwd=cwd, start_new_session=True)
    return argv
