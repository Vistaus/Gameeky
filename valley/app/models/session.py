from gi.repository import GObject, GLib, Gtk

from ...client.game.service import Service as Client
from ...client.game.scene import Scene as SceneModel
from ...client.game.stats import Stats as StatsModel
from ...client.input.keyboard import Keyboard
from ...client.graphics.entity import EntityRegistry as EntityGraphicsRegistry
from ...client.sound.scene import Scene as SceneSound
from ...client.sound.entity import EntityRegistry as EntitySoundRegistry

from ...common.utils import get_data_path
from ...common.scanner import Scanner, Description
from ...common.definitions import TILES_X, TILES_Y

from ...server.game.service import Service as Server
from ...server.game.entity import EntityRegistry as EntityGameRegistry


class Session(GObject.GObject):
    __gsignals__ = {
        "initializing": (GObject.SignalFlags.RUN_LAST, None, ()),
        "started": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(
        self,
        scene: str,
        clients: int,
        address: str,
        session_port: int,
        messages_port: int,
        scene_port: int,
        stats_port: int,
        host: bool,
        window: Gtk.Window,
    ) -> None:
        super().__init__()

        self._scene = scene
        self._clients = clients
        self._address = address
        self._session_port = session_port
        self._messages_port = messages_port
        self._scene_port = scene_port
        self._stats_port = stats_port
        self._host = host

        self._window = window

        self._context = GLib.MainContext.default()

    def _setup_client(self) -> None:
        self._client = Client(
            address=self._address,
            session_port=self._session_port,
            messages_port=self._messages_port,
            scene_port=self._scene_port,
            stats_port=self._stats_port,
            context=self._context,
        )

        self._scene_model = SceneModel(
            width=TILES_X,
            height=TILES_Y,
            service=self._client,
        )

        self._stats_model = StatsModel(
            service=self._client,
        )

        self._input = Keyboard(
            widget=self._window,
            service=self._client,
        )

        self._sound = SceneSound(
            model=self._scene_model,
        )

        self._client.register()

    def _setup_server(self) -> None:
        self._server = Server(
            scene=self._scene,
            clients=self._clients,
            session_port=self._session_port,
            messages_port=self._messages_port,
            scene_port=self._scene_port,
            stats_port=self._stats_port,
            context=self._context,
        )

    def _setup_scanner(self) -> None:
        self._scanner = Scanner(path=get_data_path("entities"))
        self._scanner.connect("found", self.__on_scanner_found)
        self._scanner.connect("done", self.__on_scanner_done)
        self._scanner.scan()

    def __on_scanner_found(self, scanner: Scanner, description: Description) -> None:
        EntityGraphicsRegistry.register(description)
        EntitySoundRegistry.register(description)

        if self._host is True:
            EntityGameRegistry.register(description)

    def __on_scanner_done(self, scanner: Scanner) -> None:
        if self._host is True:
            self._setup_server()

        self._setup_client()
        self.emit("started")

    def create(self) -> None:
        self._setup_scanner()
        self.emit("initializing")

    def shutdown(self) -> None:
        self._client.unregister()

        if self._host is True:
            self._server.shutdown()

    @property
    def scene(self) -> SceneModel:
        return self._scene_model

    @property
    def stats(self) -> StatsModel:
        return self._stats_model