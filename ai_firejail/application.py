"""Ponto de entrada da aplicação AI_FIREJAIL."""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from . import APP_ID, APP_TITLE, __version__  # noqa: E402
from .config import Config  # noqa: E402
from .preferences import PreferencesWindow  # noqa: E402
from .window import MainWindow  # noqa: E402


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.config = Config()
        self.window: MainWindow | None = None

        self._add_action("preferences", lambda *_: self.show_preferences(),
                         accels=["<primary>comma"])
        self._add_action("about", lambda *_: self.show_about())
        self._add_action("quit", lambda *_: self.quit(), accels=["<primary>q"])

    def _add_action(self, name, callback, accels=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if accels:
            self.set_accels_for_action(f"app.{name}", accels)

    def do_activate(self):
        if self.window is None:
            self.window = MainWindow(application=self)
        self.window.present()

    def show_preferences(self, page: str | None = None):
        if self.window is None:
            return
        prefs = PreferencesWindow(self.window, start_page=page)
        prefs.present()

    def show_about(self):
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name=APP_TITLE,
            application_icon=APP_ID,
            version=__version__,
            developer_name="AI_FIREJAIL",
            license_type=Gtk.License.GPL_3_0,
            comments=("Wrapper GTK4 para o firejail voltado à execução "
                      "de algoritmos de IA em sandbox."),
            website="https://github.com/aifirejail/ai_firejail",
        )
        about.present()


def main() -> int:
    app = Application()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
