"""Janela principal do AI_FIREJAIL."""

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from . import APP_TITLE  # noqa: E402
from . import profiles as prof  # noqa: E402
from . import runner  # noqa: E402

_INVALID = Gtk.INVALID_LIST_POSITION


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = self.get_application()
        self.config = self.app.config

        self.directories: list[str] = []
        self.extras: str = ""
        self._dir_rows: list[Gtk.Widget] = []
        self._cmd_rows: list[Gtk.Widget] = []

        self.set_title(APP_TITLE)
        self.set_default_size(760, 680)

        self.toasts = Adw.ToastOverlay()
        toolbar = Adw.ToolbarView()
        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)

        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        menu = Gio.Menu()
        menu.append("Preferências", "app.preferences")
        menu.append("Sobre o AI_FIREJAIL", "app.about")
        menu.append("Sair", "app.quit")
        menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic",
                                  menu_model=menu, primary=True)
        header.pack_end(menu_btn)

        self.page = Adw.PreferencesPage()
        toolbar.set_content(self.page)

        self._build_profile_group()
        self._build_directories_group()
        self._build_commands_group()

        self.reload_profiles()
        self.reload_commands()

    # -- construção dos grupos ------------------------------------------
    def _build_profile_group(self):
        group = Adw.PreferencesGroup(title="Perfil")
        self.profile_combo = Adw.ComboRow(
            title="Perfil ativo",
            subtitle="Conjunto de diretórios e opções do firejail",
        )
        manage = Gtk.Button(icon_name="document-edit-symbolic",
                            valign=Gtk.Align.CENTER, tooltip_text="Gerenciar perfis")
        manage.add_css_class("flat")
        manage.connect("clicked", lambda *_: self.app.show_preferences("profiles"))
        self.profile_combo.add_suffix(manage)
        self._profile_handler = self.profile_combo.connect(
            "notify::selected", self.on_profile_changed)
        group.add(self.profile_combo)
        self.page.add(group)

    def _build_directories_group(self):
        self.dir_group = Adw.PreferencesGroup(
            title="Diretórios Permitidos",
            description="Liberados dentro do sandbox. A ordem define a prioridade.",
        )
        add_btn = Gtk.Button(icon_name="list-add-symbolic",
                            tooltip_text="Adicionar diretório")
        add_btn.add_css_class("flat")
        add_btn.connect("clicked", self.on_add_directory)
        self.dir_group.set_header_suffix(add_btn)
        self.page.add(self.dir_group)

    def _build_commands_group(self):
        self.cmd_group = Adw.PreferencesGroup(
            title="Comandos de IA",
            description="Escolha o comando e execute no sandbox do perfil ativo.",
        )
        edit_btn = Gtk.Button(icon_name="document-edit-symbolic",
                             tooltip_text="Editar lista de comandos")
        edit_btn.add_css_class("flat")
        edit_btn.connect("clicked", lambda *_: self.app.show_preferences("commands"))
        self.cmd_group.set_header_suffix(edit_btn)
        self.page.add(self.cmd_group)

    # -- utilidades ------------------------------------------------------
    def toast(self, text: str):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))

    def current_profile(self) -> str | None:
        model = self.profile_combo.get_model()
        idx = self.profile_combo.get_selected()
        if model is None or idx == _INVALID:
            return None
        return model.get_string(idx)

    # -- perfis ----------------------------------------------------------
    def reload_profiles(self):
        names = prof.list_profiles()
        if not names:
            prof.create_profile("default")
            names = ["default"]

        active = self.config.get_setting("active_profile", names[0])
        if active not in names:
            active = names[0]

        model = Gtk.StringList.new(names)
        self.profile_combo.handler_block(self._profile_handler)
        self.profile_combo.set_model(model)
        self.profile_combo.set_selected(names.index(active))
        self.profile_combo.handler_unblock(self._profile_handler)

        self.config.set_setting("active_profile", active)
        self.reload_directories()

    def on_profile_changed(self, *_):
        name = self.current_profile()
        if name:
            self.config.set_setting("active_profile", name)
            self.reload_directories()

    # -- diretórios ------------------------------------------------------
    def reload_directories(self):
        for row in self._dir_rows:
            self.dir_group.remove(row)
        self._dir_rows = []

        name = self.current_profile()
        if not name:
            self._add_dir_placeholder("Nenhum perfil selecionado")
            return

        self.directories, self.extras = prof.read_profile(name)
        if not self.directories:
            self._add_dir_placeholder("Nenhum diretório",
                                      "Use o botão + para adicionar")
            return

        count = len(self.directories)
        for i, directory in enumerate(self.directories):
            title = os.path.basename(directory.rstrip("/")) or directory
            row = Adw.ActionRow(title=title, subtitle=directory)

            up = self._icon_button("go-up-symbolic", "Subir prioridade")
            up.set_sensitive(i > 0)
            up.connect("clicked", self.on_move_directory, i, -1)
            down = self._icon_button("go-down-symbolic", "Descer prioridade")
            down.set_sensitive(i < count - 1)
            down.connect("clicked", self.on_move_directory, i, 1)
            remove = self._icon_button("user-trash-symbolic", "Remover")
            remove.connect("clicked", self.on_remove_directory, i)

            row.add_suffix(up)
            row.add_suffix(down)
            row.add_suffix(remove)
            self.dir_group.add(row)
            self._dir_rows.append(row)

    def _add_dir_placeholder(self, title, subtitle=""):
        row = Adw.ActionRow(title=title, subtitle=subtitle)
        row.set_sensitive(False)
        self.dir_group.add(row)
        self._dir_rows.append(row)

    @staticmethod
    def _icon_button(icon, tooltip):
        btn = Gtk.Button(icon_name=icon, valign=Gtk.Align.CENTER,
                         tooltip_text=tooltip)
        btn.add_css_class("flat")
        return btn

    def save_directories(self):
        name = self.current_profile()
        if name:
            prof.write_profile(name, self.directories, self.extras)

    def on_add_directory(self, *_):
        dialog = Gtk.FileDialog(title="Escolha um diretório para liberar")
        dialog.select_folder(self, None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except Exception:
            return
        path = folder.get_path()
        if not path:
            return
        if path in self.directories:
            self.toast("Esse diretório já está na lista.")
            return
        self.directories.append(path)
        self.save_directories()
        self.reload_directories()

    def on_move_directory(self, _button, index, delta):
        new = index + delta
        if new < 0 or new >= len(self.directories):
            return
        self.directories[index], self.directories[new] = (
            self.directories[new], self.directories[index])
        self.save_directories()
        self.reload_directories()

    def on_remove_directory(self, _button, index):
        if 0 <= index < len(self.directories):
            del self.directories[index]
            self.save_directories()
            self.reload_directories()

    # -- comandos --------------------------------------------------------
    def reload_commands(self):
        for row in self._cmd_rows:
            self.cmd_group.remove(row)
        self._cmd_rows = []

        commands = self.config.list_commands()
        if not commands:
            row = Adw.ActionRow(title="Nenhum comando configurado",
                                subtitle="Adicione em Preferências → Comandos")
            row.set_sensitive(False)
            self.cmd_group.add(row)
            self._cmd_rows.append(row)
            return

        for cmd in commands:
            row = Adw.ActionRow(title=cmd.name, subtitle=cmd.command)

            term_label = Gtk.Label(label="Terminal", valign=Gtk.Align.CENTER)
            term_label.add_css_class("dim-label")
            term_switch = Gtk.Switch(valign=Gtk.Align.CENTER,
                                     active=cmd.run_in_terminal,
                                     tooltip_text="Executar dentro de um terminal")
            term_switch.connect("state-set", self.on_terminal_toggled, cmd.id)

            run = Gtk.Button(valign=Gtk.Align.CENTER, tooltip_text="Executar no sandbox")
            run.set_child(Adw.ButtonContent(icon_name="media-playback-start-symbolic",
                                            label="Executar"))
            run.add_css_class("suggested-action")
            run.connect("clicked", self.on_run_command, cmd.id)

            row.add_suffix(term_label)
            row.add_suffix(term_switch)
            row.add_suffix(run)
            row.set_activatable_widget(run)
            self.cmd_group.add(row)
            self._cmd_rows.append(row)

    def on_terminal_toggled(self, _switch, state, cmd_id):
        self.config.update_command(cmd_id, run_in_terminal=state)
        return False  # deixa o Switch atualizar o estado visual

    def on_run_command(self, _button, cmd_id):
        name = self.current_profile()
        if not name:
            self.toast("Selecione um perfil primeiro.")
            return
        cmd = next((c for c in self.config.list_commands() if c.id == cmd_id), None)
        if cmd is None:
            return
        terminal_pref = self.config.get_setting("terminal", "") or None
        global_opts = self.config.get_setting("global_options", "")
        extra_args = global_opts.split() if global_opts.strip() else None
        try:
            runner.run(name, cmd.command,
                       in_terminal=cmd.run_in_terminal,
                       terminal_pref=terminal_pref,
                       extra_args=extra_args)
            self.toast(f"Executando “{cmd.name}” no perfil “{name}”.")
        except Exception as exc:
            self._error_dialog("Não foi possível executar", str(exc))

    def _error_dialog(self, heading, body):
        dialog = Adw.MessageDialog(transient_for=self, modal=True,
                                   heading=heading, body=body)
        dialog.add_response("ok", "Fechar")
        dialog.present()
