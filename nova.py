#!/usr/bin/python3

# Licensed under the 0BSD

from signal import SIGINT, SIGTERM, signal
from subprocess import Popen, check_output

from hid import device
from hid import enumerate as hidenumerate

CMD_PACTL = "pactl"
CMD_PWLOOPBACK = "pw-loopback"


class ChatMix:
    # Create virtual pipewire sinks
    def __init__(self, output_sink: str, main_sink: str, chat_sink: str):
        self.main_sink = main_sink
        self.chat_sink = chat_sink
        self.main_sink_process = self._create_virtual_sink(main_sink, output_sink)
        self.chat_sink_process = self._create_virtual_sink(chat_sink, output_sink)

    def set_main_volume(self, volume: int):
        self._set_volume(self.main_sink, volume)

    def set_chat_volume(self, volume: int):
        self._set_volume(self.chat_sink, volume)

    def set_volumes(self, main_volume: int, chat_volume: int):
        self.set_main_volume(main_volume)
        self.set_chat_volume(chat_volume)

    def close(self):
        self.main_sink_process.terminate()
        self.chat_sink_process.terminate()

    def _create_virtual_sink(self, name: str, output_sink: str) -> Popen:
        return Popen(
            [
                CMD_PWLOOPBACK,
                "-P",
                output_sink,
                "--capture-props=media.class=Audio/Sink",
                "-n",
                name,
            ]
        )

    def _set_volume(self, sink: str, volume: int):
        Popen([CMD_PACTL, "set-sink-volume", f"input.{sink}", f"{volume}%"])


class NovaProWireless:
    # USB IDs
    VID = 0x1038
    PID = 0x12E0

    # bInterfaceNumber
    INTERFACE = 0x4

    # HID Message length
    MSGLEN = 63

    # Message read timeout
    READ_TIMEOUT = 1000

    # First byte controls data direction.
    TX = 0x6  # To base station.
    RX = 0x7  # From base station.

    # Second Byte
    # This is a very limited list of options, you can control way more. I just haven't implemented those options (yet)
    ## As far as I know, this only controls the icon.
    OPT_SONAR_ICON = 0x8D
    ## Enabling this option enables the ability to switch between volume and ChatMix.
    OPT_CHATMIX_ENABLE = 0x49
    ## Volume controls, 1 byte
    OPT_VOLUME = 0x25
    ## ChatMix controls, 2 bytes show and control game and chat volume.
    OPT_CHATMIX = 0x45
    ## EQ controls, 2 bytes show and control which band and what value.
    OPT_EQ = 0x31
    ## EQ preset controls, 1 byte sets and shows enabled preset. Preset 4 is the custom preset required for OPT_EQ.
    OPT_EQ_PRESET = 0x2E

    # PipeWire Names
    ## String used to automatically select output sink
    PW_OUTPUT_SINK_AUTODETECT = "SteelSeries_Arctis_Nova_Pro_Wireless"
    ## Names of virtual sound devices
    PW_GAME_SINK = "NovaGame"
    PW_CHAT_SINK = "NovaChat"

    # Keeps track of enabled features for when close() is called
    CHATMIX_CONTROLS_ENABLED = False
    SONAR_ICON_ENABLED = False

    # Stops processes when program exits
    CLOSE = False

    # Device not found error string
    ERR_NOTFOUND = "Device not found"

    # Selects correct device, and makes sure we can control it
    def __init__(self, output_sink=None):
        # Find HID device path
        devpath = None
        for hiddev in hidenumerate(self.VID, self.PID):
            if hiddev["interface_number"] == self.INTERFACE:
                devpath = hiddev["path"]
                break
        if not devpath:
            raise DeviceNotFoundException

        # Try to automatically detect output sink, this is skipped if output_sink is given
        if not output_sink:
            sinks = (
                check_output([CMD_PACTL, "list", "sinks", "short"]).decode().split("\n")
            )
            for sink in sinks[:-1]:
                sink_name = sink.split("\t")[1]
                if self.PW_OUTPUT_SINK_AUTODETECT in sink_name:
                    output_sink = sink_name

        self.dev = device()
        self.dev.open_path(devpath)
        self.dev.set_nonblocking(True)
        self.output_sink = output_sink

    # Enables/Disables chatmix controls
    def set_chatmix_controls(self, state: bool):
        assert self.dev, self.ERR_NOTFOUND
        self.dev.write(
            self._create_msgdata((self.TX, self.OPT_CHATMIX_ENABLE, int(state))),
        )
        self.CHATMIX_CONTROLS_ENABLED = state

    # Enables/Disables Sonar Icon
    def set_sonar_icon(self, state: bool):
        assert self.dev, self.ERR_NOTFOUND
        self.dev.write(
            self._create_msgdata((self.TX, self.OPT_SONAR_ICON, int(state))),
        )
        self.SONAR_ICON_ENABLED = state

    # Sets Volume
    def set_volume(self, attenuation: int):
        assert self.dev, self.ERR_NOTFOUND
        self.dev.write(
            self._create_msgdata((self.TX, self.OPT_VOLUME, attenuation)),
        )

    # Sets EQ preset
    def set_eq_preset(self, preset: int):
        assert self.dev, self.ERR_NOTFOUND
        self.dev.write(
            self._create_msgdata((self.TX, self.OPT_EQ_PRESET, preset)),
        )

    # ChatMix implementation
    # Continuously read from base station and ignore everything but ChatMix messages (OPT_CHATMIX)
    def chatmix_volume_control(self, chatmix: ChatMix):
        assert self.dev, self.ERR_NOTFOUND
        while not self.CLOSE:
            try:
                msg = self.dev.read(self.MSGLEN, self.READ_TIMEOUT)
                if not msg or msg[1] is not self.OPT_CHATMIX:
                    continue

                # 4th and 5th byte contain ChatMix data
                gamevol = msg[2]
                chatvol = msg[3]

                # Actually change volume. Everytime you turn the dial, both volumes are set to the correct level
                chatmix.set_volumes(gamevol, chatvol)
            except OSError:
                print("Device was probably disconnected, exiting.")
                self.CLOSE = True
        # Remove virtual sinks on exit
        chatmix.close()

    # Prints output from base station. `debug` argument enables raw output.
    def print_output(self, debug: bool = False):
        assert self.dev
        while not self.CLOSE:
            msg = self.dev.read(self.MSGLEN, self.READ_TIMEOUT)
            if debug:
                print(msg)
            match msg[1]:
                case self.OPT_VOLUME:
                    print(f"Volume: -{msg[2]}")
                case self.OPT_CHATMIX:
                    print(f"Game Volume: {msg[2]} - Chat Volume: {msg[3]}")
                case self.OPT_EQ:
                    print(f"EQ: Bar: {msg[2]} - Value: {(msg[3] - 20) / 2}")
                case self.OPT_EQ_PRESET:
                    print(f"EQ Preset: {msg[2]}")
                case _:
                    print("Unknown Message")

    # Terminates processes and disables features
    def close(self, signum, frame):
        self.CLOSE = True
        if self.CHATMIX_CONTROLS_ENABLED:
            self.set_chatmix_controls(False)
        if self.SONAR_ICON_ENABLED:
            self.set_sonar_icon(False)

    # Takes a tuple of ints and turns it into bytes with the correct length padded with zeroes
    def _create_msgdata(self, data: tuple[int, ...]) -> bytes:
        return bytes(data).ljust(self.MSGLEN, b"\0")


class DeviceNotFoundException(Exception):
    pass


# When run directly, just start the ChatMix implementation. (And activate the icon, just for fun)
if __name__ == "__main__":
    try:
        nova = NovaProWireless()
        nova.set_sonar_icon(state=True)
        nova.set_chatmix_controls(state=True)

        signal(SIGINT, nova.close)
        signal(SIGTERM, nova.close)

        assert nova.output_sink, "Output sink not set"
        chatmix = ChatMix(
            output_sink=nova.output_sink,
            main_sink=nova.PW_GAME_SINK,
            chat_sink=nova.PW_CHAT_SINK,
        )

        nova.chatmix_volume_control(chatmix=chatmix)
    except DeviceNotFoundException:
        print("Device not found, exiting.")
