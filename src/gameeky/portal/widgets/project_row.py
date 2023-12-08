from gi.repository import Gtk, Adw, GObject

from ...common.scanner import Description


@Gtk.Template(resource_path="/dev/tchx84/gameeky/portal/widgets/project_row.ui")
class ProjectRow(Adw.ActionRow):
    __gtype_name__ = "ProjectRow"

    __gsignals__ = {
        "edited": (GObject.SignalFlags.RUN_LAST, None, ()),
        "removed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    @Gtk.Template.Callback("on_edit_clicked")
    def __on_edit_clicked(self, button: Gtk.Button) -> None:
        self.emit("edited")

    @Gtk.Template.Callback("on_remove_clicked")
    def __on_remove_clicked(self, button: Gtk.Button) -> None:
        self.emit("removed")

    @property
    def description(self) -> Description:
        return Description(
            name=self.props.title,
            description=self.props.subtitle,
        )

    @description.setter
    def description(self, description: Description) -> None:
        self.props.title = description.name
        self.props.subtitle = description.description