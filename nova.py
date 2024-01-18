#!/usr/bin/python3

# Licensed under the EUPL

import subprocess

from usb.core import find, USBTimeoutError


class NovaProWireless:
    # USB IDs
    VID = 0x1038
    PID = 0x12E0

    # bInterfaceNumber
    INTERFACE = 0x4

    # bEndpointAddress
    ENDPOINT_TX = 0x4  # EP 4 OUT
    ENDPOINT_RX = 0x84  # EP 4 IN

    MSGLEN = 64  # Total USB packet is 128 bytes, data is last 64 bytes.

    # First byte controls data direction.
    TX = 0x6  # To base station.
    RX = 0x7  # From base station.

    # Second Byte
    # This is a very limited list of options, you can control way more. I just haven't implemented those options (yet)
    ## As far as I know, this only controls the icon.
    OPT_SONAR_ICON = 141
    ## Enabling this options enables the ability to switch between volume and ChatMix.
    OPT_CHATMIX_ENABLE = 73
    ## Volume controls, 1 byte
    OPT_VOLUME = 37
    ## ChatMix controls, 2 bytes show and control game and chat volume.
    OPT_CHATMIX = 69
    ## EQ controls, 2 bytes show and control which band and what value.
    OPT_EQ = 49
    ## EQ preset controls, 1 byte sets and shows enabled preset. Preset 4 is the custom preset required for OPT_EQ.
    OPT_EQ_PRESET = 46

    # PipeWire Names
    ## Name of digital sink.
    ## PipeWire docs recommend the analog sink, but I've had better results with the digital one. Probably not actually, but whatever.
    PW_ORIGINAL_SINK = (
        "alsa_output.usb-SteelSeries_Arctis_Nova_Pro_Wireless-00.7.iec958-stereo"
    )
    ## Names of virtual sound devices
    PW_GAME_SINK = "NovaGame"
    PW_CHAT_SINK = "NovaChat"

    # Selects correct device, and makes sure we can control it
    def __init__(self):
        self.dev = find(idVendor=self.VID, idProduct=self.PID)
        if self.dev is None:
            raise ValueError("Device not found")
        if self.dev.is_kernel_driver_active(self.INTERFACE):
            self.dev.detach_kernel_driver(self.INTERFACE)

    # Takes a tuple of ints and turns it into bytes with the correct length padded with zeroes
    def _create_msgdata(self, data: tuple[int]) -> bytes:
        return bytes(data).ljust(self.MSGLEN, b"0")

    # Enables chatmix
    def enable_chatmix(self):
        self.dev.write(
            self.ENDPOINT_TX,
            self._create_msgdata((self.TX, self.OPT_CHATMIX_ENABLE, 1)),
        )

    # Enables Sonar Icon
    def enable_sonar_icon(self):
        self.dev.write(
            self.ENDPOINT_TX, self._create_msgdata((self.TX, self.OPT_SONAR_ICON, 1))
        )

    # Sets Volume
    def set_volume(self, attenuation: int):
        self.dev.write(
            self.ENDPOINT_TX,
            self._create_msgdata((self.TX, self.OPT_VOLUME, attenuation)),
        )

    # Sets EQ preset
    def set_eq_preset(self, preset: int):
        self.dev.write(
            self.ENDPOINT_TX,
            self._create_msgdata((self.TX, self.OPT_EQ_PRESET, preset)),
        )

    # Create virtual pipewire loopback sinks, and redirect them to the real headset sink
    def _enable_virtual_sinks(self):
        cmd = [
            "pw-loopback",
            "-P",
            self.PW_ORIGINAL_SINK,
            "--capture-props=media.class=Audio/Sink",
            "-n",
        ]
        subprocess.Popen(cmd + [self.PW_GAME_SINK])
        subprocess.Popen(cmd + [self.PW_CHAT_SINK])

    # ChatMix implementation
    # Continuously read from base station and ignore everything but ChatMix messages (OPT_CHATMIX)
    # The .read method times out and returns an error. This error is catched and basically ignored. Timeout can be configured, but not turned off (I think).
    def chatmix(self):
        self._enable_virtual_sinks()
        while True:
            try:
                msg = self.dev.read(self.ENDPOINT_RX, self.MSGLEN)
                if msg[1] != self.OPT_CHATMIX:
                    continue

                # 4th and 5th byte contain ChatMix data
                gamevol = msg[2]
                chatvol = msg[3]

                # Set Volume using PulseAudio tools. Can be done with pure pipewire tools, but I didn't feel like it
                cmd = ["pactl", "set-sink-volume"]

                # Actually change volume. Everytime you turn the dial, both volumes are set to the correct level
                subprocess.Popen(cmd + [f"input.{self.PW_GAME_SINK}", f"{gamevol}%"])
                subprocess.Popen(cmd + [f"input.{self.PW_CHAT_SINK}", f"{chatvol}%"])
            # Ignore timeout.
            except USBTimeoutError:
                continue

    # Prints output from base station. `debug` argument enables raw output.
    def print_output(self, debug: bool = False):
        while True:
            try:
                msg = self.dev.read(self.ENDPOINT_RX, self.MSGLEN)
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
            except USBTimeoutError:
                continue


# When run directly, just start the ChatMix implementation. (And activate the icon, just for fun)
if __name__ == "__main__":
    nova = NovaProWireless()
    nova.enable_sonar_icon()
    nova.enable_chatmix()
    nova.chatmix()
