"""Janela de Preferências: comandos de IA, perfis do firejail e opções gerais."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from . import profiles as prof  # noqa: E402


class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, window, start_page: str | None = None):
        super().__init__(transient_for=window, modal=True)
        self.window = window
        self.config = window.config
        self.set_title("Preferências")
        self.set_search_enabled(False)
        self.set_default_size(680, 620)

        self.commands_page = self._build_commands_page()
        self.profiles_page = self._build_profiles_page()
        self.general_page = self._build_general_page()
        self.add(self.commands_page)
        self.add(self.profiles_page)
        self.add(self.general_page)

        self.reload_commands()
        self.reload_profiles()

        if start_page == "profiles":
            self.set_visible_page(self.profiles_page)
        elif start_page == "general":
            self.set_visible_page(self.general_page)

    # ===================================================================
    #  Página: Comandos
    # ===================================================================
    def _build_commands_page(self):
        page = Adw.PreferencesPage(title="Comandos", icon_name="utilities-terminal-symbolic")
        self.cmd_group = Adw.PreferencesGroup(
            title="Comandos de IA",
            description="Lista editável de comandos disponíveis na janela principal.",
        )
        add = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Novo comando")
        add.add_css_class("flat")
        add.connect("clicked", lambda *_: self._edit_command_dialog(None))
        self.cmd_group.set_header_suffix(add)
        page.add(self.cmd_group)
        self._cmd_rows = []
        return page

    def reload_commands(self):
        for row in self._cmd_rows:
            self.cmd_group.remove(row)
        self._cmd_rows = []

        commands = self.config.list_commands()
        if not commands:
            row = Adw.ActionRow(title="Nenhum comando", subtitle="Use + para adicionar")
            row.set_sensitive(False)
            self.cmd_group.add(row)
            self._cmd_rows.append(row)
            return

        total = len(commands)
        for i, cmd in enumerate(commands):
            subtitle = cmd.command
            if cmd.run_in_terminal:
                subtitle += "   ·   no terminal"
            row = Adw.ActionRow(title=cmd.name, subtitle=subtitle)

            up = self._icon_button("go-up-symbolic", "Subir")
            up.set_sensitive(i > 0)
            up.connect("clicked", self._move_command, cmd.id, -1)
            down = self._icon_button("go-down-symbolic", "Descer")
            down.set_sensitive(i < total - 1)
            down.connect("clicked", self._move_command, cmd.id, 1)
            edit = self._icon_button("document-edit-symbolic", "Editar")
            edit.connect("clicked", lambda _b, c=cmd: self._edit_command_dialog(c))
            delete = self._icon_button("user-trash-symbolic", "Excluir")
            delete.connect("clicked", lambda _b, c=cmd: self._delete_command(c))

            for b in (up, down, edit, delete):
                row.add_suffix(b)
            self.cmd_group.add(row)
            self._cmd_rows.append(row)

    def _move_command(self, _b, cmd_id, delta):
        self.config.move_command(cmd_id, delta)
        self.reload_commands()
        self.window.reload_commands()

    def _delete_command(self, cmd):
        dialog = Adw.MessageDialog(
            transient_for=self, modal=True,
            heading="Excluir comando?",
            body=f"“{cmd.name}” será removido da lista.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Excluir")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")

        def on_response(_d, response):
            if response == "delete":
                self.config.delete_command(cmd.id)
                self.reload_commands()
                self.window.reload_commands()
        dialog.connect("response", on_response)
        dialog.present()

    def _edit_command_dialog(self, cmd):
        is_new = cmd is None
        dialog = Adw.MessageDialog(
            transient_for=self, modal=True,
            heading="Novo comando" if is_new else "Editar comando")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("save", "Salvar")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")

        group = Adw.PreferencesGroup()
        name_row = Adw.EntryRow(title="Nome")
        cmd_row = Adw.EntryRow(title="Comando")
        term_row = Adw.SwitchRow(title="Executar no terminal",
                                 subtitle="Abre um emulador de terminal")
        if not is_new:
            name_row.set_text(cmd.name)
            cmd_row.set_text(cmd.command)
            term_row.set_active(cmd.run_in_terminal)
        group.add(name_row)
        group.add(cmd_row)
        group.add(term_row)
        dialog.set_extra_child(group)

        def on_response(_d, response):
            if response != "save":
                return
            name = name_row.get_text().strip()
            command = cmd_row.get_text().strip()
            term = term_row.get_active()
            if not name or not command:
                self.window.toast("Nome e comando são obrigatórios.")
                return
            if is_new:
                self.config.add_command(name, command, term)
            else:
                self.config.update_command(cmd.id, name=name, command=command,
                                           run_in_terminal=term)
            self.reload_commands()
            self.window.reload_commands()

        dialog.connect("response", on_response)
        dialog.present()

    # ===================================================================
    #  Página: Perfis
    # ===================================================================
    def _build_profiles_page(self):
        page = Adw.PreferencesPage(title="Perfis", icon_name="security-high-symbolic")
        self.prof_group = Adw.PreferencesGroup(
            title="Perfis do firejail",
            description="Arquivos .profile em texto puro no diretório de configuração.",
        )
        add = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Novo perfil")
        add.add_css_class("flat")
        add.connect("clicked", lambda *_: self._new_profile_dialog())
        self.prof_group.set_header_suffix(add)
        page.add(self.prof_group)
        self._prof_rows = []
        return page

    def reload_profiles(self):
        for row in self._prof_rows:
            self.prof_group.remove(row)
        self._prof_rows = []

        names = prof.list_profiles()
        if not names:
            prof.create_profile("default")
            names = ["default"]

        for name in names:
            dirs, _ = prof.read_profile(name)
            row = Adw.ActionRow(title=name,
                                subtitle=f"{len(dirs)} diretório(s)")

            edit = self._icon_button("document-edit-symbolic", "Editar opções/arquivo")
            edit.connect("clicked", lambda _b, n=name: self._edit_profile_dialog(n))
            rename = self._icon_button("document-properties-symbolic", "Renomear")
            rename.connect("clicked", lambda _b, n=name: self._rename_profile_dialog(n))
            delete = self._icon_button("user-trash-symbolic", "Excluir")
            delete.set_sensitive(len(names) > 1)
            delete.connect("clicked", lambda _b, n=name: self._delete_profile(n))

            for b in (edit, rename, delete):
                row.add_suffix(b)
            self.prof_group.add(row)
            self._prof_rows.append(row)

    def _new_profile_dialog(self):
        dialog = Adw.MessageDialog(transient_for=self, modal=True,
                                   heading="Novo perfil")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("create", "Criar")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")

        group = Adw.PreferencesGroup()
        name_row = Adw.EntryRow(title="Nome do perfil")
        group.add(name_row)
        dialog.set_extra_child(group)

        def on_response(_d, response):
            if response != "create":
                return
            name = _sanitize(name_row.get_text())
            if not name:
                self.window.toast("Nome inválido.")
                return
            if prof.exists(name):
                self.window.toast("Já existe um perfil com esse nome.")
                return
            prof.create_profile(name)
            self.reload_profiles()
            self.window.reload_profiles()
        dialog.connect("response", on_response)
        dialog.present()

    def _rename_profile_dialog(self, name):
        dialog = Adw.MessageDialog(transient_for=self, modal=True,
                                   heading=f"Renomear “{name}”")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("rename", "Renomear")
        dialog.set_response_appearance("rename", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("rename")

        group = Adw.PreferencesGroup()
        name_row = Adw.EntryRow(title="Novo nome")
        name_row.set_text(name)
        group.add(name_row)
        dialog.set_extra_child(group)

        def on_response(_d, response):
            if response != "rename":
                return
            new = _sanitize(name_row.get_text())
            if not new or new == name:
                return
            if prof.exists(new):
                self.window.toast("Já existe um perfil com esse nome.")
                return
            prof.rename_profile(name, new)
            if self.config.get_setting("active_profile") == name:
                self.config.set_setting("active_profile", new)
            self.reload_profiles()
            self.window.reload_profiles()
        dialog.connect("response", on_response)
        dialog.present()

    def _delete_profile(self, name):
        dialog = Adw.MessageDialog(
            transient_for=self, modal=True,
            heading="Excluir perfil?",
            body=f"O arquivo “{name}.profile” será removido permanentemente.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Excluir")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")

        def on_response(_d, response):
            if response != "delete":
                return
            prof.delete_profile(name)
            if self.config.get_setting("active_profile") == name:
                remaining = prof.list_profiles()
                if remaining:
                    self.config.set_setting("active_profile", remaining[0])
            self.reload_profiles()
            self.window.reload_profiles()
        dialog.connect("response", on_response)
        dialog.present()

    def _edit_profile_dialog(self, name):
        """Edita as opções extras do firejail (tudo exceto os diretórios)."""
        dirs, extras = prof.read_profile(name)
        dialog = Adw.MessageDialog(
            transient_for=self, modal=True,
            heading=f"Opções do firejail — {name}",
            body=("Os diretórios são gerenciados na janela principal. "
                  "Aqui você edita as demais opções do firejail "
                  "(ex.: caps.drop all, seccomp, net none, nodbus)."))
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("save", "Salvar")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")

        scroller = Gtk.ScrolledWindow(min_content_height=220, min_content_width=420,
                                      vexpand=True)
        scroller.add_css_class("card")
        textview = Gtk.TextView(monospace=True, top_margin=8, bottom_margin=8,
                                left_margin=8, right_margin=8,
                                wrap_mode=Gtk.WrapMode.WORD_CHAR)
        textview.get_buffer().set_text(extras)
        scroller.set_child(textview)
        dialog.set_extra_child(scroller)

        def on_response(_d, response):
            if response != "save":
                return
            buf = textview.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
            prof.write_profile(name, dirs, text)
            self.reload_profiles()
            self.window.reload_profiles()
        dialog.connect("response", on_response)
        dialog.present()

    # ===================================================================
    #  Página: Geral
    # ===================================================================
    def _build_general_page(self):
        page = Adw.PreferencesPage(title="Geral", icon_name="preferences-system-symbolic")

        group = Adw.PreferencesGroup(
            title="Execução",
            description="Opções aplicadas a todos os comandos.")

        self.term_row = Adw.EntryRow(title="Emulador de terminal")
        self.term_row.set_text(self.config.get_setting("terminal", "") or "")
        self.term_row.set_show_apply_button(True)
        self.term_row.connect(
            "apply",
            lambda r: self.config.set_setting("terminal", r.get_text().strip()))
        term_hint = Adw.ActionRow(
            title="Deixe em branco para detectar automaticamente",
            subtitle="Ex.: gnome-terminal, ptyxis, konsole, xterm")
        term_hint.set_sensitive(False)

        self.opts_row = Adw.EntryRow(title="Opções globais do firejail")
        self.opts_row.set_text(self.config.get_setting("global_options", "") or "")
        self.opts_row.set_show_apply_button(True)
        self.opts_row.connect(
            "apply",
            lambda r: self.config.set_setting("global_options", r.get_text().strip()))
        opts_hint = Adw.ActionRow(
            title="Aplicadas junto ao perfil em toda execução",
            subtitle="Ex.: --net=none --private-tmp")
        opts_hint.set_sensitive(False)

        group.add(self.term_row)
        group.add(term_hint)
        group.add(self.opts_row)
        group.add(opts_hint)
        page.add(group)
        return page

    # -- helper ----------------------------------------------------------
    @staticmethod
    def _icon_button(icon, tooltip):
        btn = Gtk.Button(icon_name=icon, valign=Gtk.Align.CENTER,
                         tooltip_text=tooltip)
        btn.add_css_class("flat")
        return btn


def _sanitize(name: str) -> str:
    """Nome de perfil seguro para nome de arquivo."""
    name = (name or "").strip()
    keep = "-_. "
    cleaned = "".join(c for c in name if c.isalnum() or c in keep).strip()
    return cleaned.replace("/", "").replace("..", "")
