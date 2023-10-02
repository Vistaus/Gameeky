from gi.repository import Gio, GLib, GObject


class Client(GObject.GObject):
    __gtype_name__ = "UDPClient"

    __gsignals__ = {
        "received": (GObject.SignalFlags.RUN_LAST, None, (object, object)),
    }

    MAX_BYTES = 2048

    def __init__(self, address, port, context):
        super().__init__()

        self._address = Gio.InetSocketAddress.new_from_string(address, port)

        self._socket = Gio.Socket.new(
            Gio.SocketFamily.IPV4, Gio.SocketType.DATAGRAM, Gio.SocketProtocol.UDP
        )
        self._socket.connect(self._address)

        self._input_stream = Gio.UnixInputStream.new(self._socket.get_fd(), False)

        self._source = self._socket.create_source(GLib.IOCondition.IN, None)
        self._source.set_callback(self.__received_data_cb)
        self._source.attach(context)

    def __received_data_cb(self, source):
        # XXX replace with .receive_from() when fixed
        size, address, messages, flags = self._socket.receive_message(
            [], Gio.SocketMsgFlags.PEEK, None
        )
        raw = self._input_stream.read_bytes(self.MAX_BYTES, None)

        self.emit("received", address, raw.get_data())

        return GLib.SOURCE_CONTINUE

    def send(self, data):
        self._socket.send(data)
