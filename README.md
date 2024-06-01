# Arctis Nova Pro Wireless ChatMix on Linux

### In this document

1. [About this project](#about-this-project)
2. [Disclaimer](#disclaimer)
3. [My Findings](#my-findings)
4. [Usage](#usage)
5. [What's Next](#whats-next)
6. [License](#license)

## About this project

Some SteelSeries headsets have a feature called ChatMix where you can easily adjust game and chat audio volume on the headphones or dongle.

In previous SteelSeries headsets ChatMix was always a hardware feature. It worked by providing 2 sound devices to the host, 1 for general audio and the other for chat audio.

In newer generations of their headsets however, in particular the Arctis Nova Pro Wireless, this feature was taken out of the hardware itself, and made into a feature of their audio software called Sonar.

Sonar of course only works on Windows (and requires a SteelSeries account!), so everyone using other platforms were shit out of luck, even though these headphones are far from cheap.

Even though it is now a software feature, the hardware can still control it, but only when Sonar activated this feature on the base station. You can toggle between normal volume controls and ChatMix by pressing down on the volume dial on either the headset or base station.

I used ChatMix a lot on my previous SteelSeries headset, and I want to be able to use it on this one, so I started looking into how I can control 2 virtual PipeWire sinks with the ChatMix controls. This project is the result.

## Disclaimer

THIS PROJECT HAS NO ASSOCIATION TO STEELSERIES, NOR IS IT IN ANY WAY SUPPORTED BY THEM.

I AM NOT RESPONSIBLE FOR BRICKED/BROKEN DEVICES NOR DO I GUARANTEE IT WILL WORK FOR YOU.

USING ANYTHING IN THIS PROJECT *MIGHT* VOID YOUR WARRANTY AND IS AT YOUR OWN RISK

I started this project knowing nothing about USB (I still don't), so I might be overcomplicating everything. The scripts I created were quickly thrown together and don't really integrate with anything. I might try to improve this later, but I also might not, as it does work for me in it's current state.

## My findings

I started by installing SteelSeries GG and Sonar in a Windows 11 VM and passing through the base station USB device. On the (Linux) host I used Wireshark to see what happened when I enabled Sonar.

This device uses USB HID events to both configure and receive data from the base station. I identified which ones enabled what features and tried activating these on Linux using the /dev/hidraw* device. See `commands.sh` for more information.

I am on MCU firmware version `01.29.27` and DSP firmware version `00.03.82`.

### Protocol description

Again, I don't really know anything about USB, so I could be wrong about a lot of this, but this is the protocol as I understand it

See `nova.py` for a commented example implementation.

The controls and data output are on USB Interface 4 (`bInterfaceNumber=4`). This interface has 2 endpoint, 1 for sending data (`0x04`) and 1 for receiving data (`0x84`).

The HID Data messages are structured as follows:

- The first byte decides wether we are sending or receiving. `0x6` means we sent it, `0x7` means we received it from the base station
- The second byte specifies the parameter, eg. `73` (`0x49`) to enable ChatMix
- The next bytes contain the value for that parameter, some parameters use 1 byte, some use more.
- Because the message should be 64 bytes long, the unused bytes should all be `0`

These are the parameters I have found:
<br>
*(There are quite a few more parameters, like sidetone and other settings, I just haven't documented those yet.)*

| Option | Description | Parameters | Range | Notes |
| ------ | ----------- | ---------- | ----- | ----- |
| 73 | ChatMix State | - Boolean: State | 0-1 |
| 141 | Sonar Icon State | - Boolean: State | 0-1 | I think this only toggles the icon, but that could be wrong
| 37 | Volume Attenuation | - Integer: Attenuation | 0-56 | 0=max<br>56=mute |
| 69 | ChatMix Controls | - Integer: Game Volume<br>- Integer: Chat Volume | 0-100 |
| 46 | EQ Preset | - Integer: Preset | 0-18 | Preset 4 is the custom EQ profile
| 49 | Custom EQ Controls | - Integer: EQ Bar<br>- Integer: Value | 0-40 | On the base station the value ranges from -20 to 20

## Usage
For this project I created a simple Python program to both enable the controls and use them to control 2 virtual sound devices.

### Dependencies
- Python 3 (I used 3.12, it may or may not work on older versions)
- PyUSB
- PipeWire
- pactl

On Fedora (assuming PipeWire is already setup) these can be installed with:
```
sudo dnf install pulseaudio-utils python3 python3-pyusb
```
### Install

Clone this repo and cd into it
```
git clone https://git.dymstro.nl/Dymstro/nova-chatmix-linux.git
cd nova-chatmix-linux
```

To be able to run the script as a non-root user, some udev rules need to be applied. This will allow regular users to access the base station USB device.

Copy `50-nova-pro-wireless.rules` to `/etc/udev/rules.d` and reload udev rules:
```
sudo cp 50-nova-pro-wireless.rules /etc/udev/rules.d/

sudo udevadm control --reload-rules
sudo udevadm trigger
```

Check if your audio device matches the one on line 49 of `nova.py`
```
pactl list sinks short
# The output should look something like this:
# 47      alsa_output.pci-0000_0c_00.4.iec958-stereo      PipeWire        s32le 2ch 48000Hz       SUSPENDED
# 77      alsa_output.pci-0000_0a_00.1.hdmi-stereo        PipeWire        s32le 2ch 48000Hz       SUSPENDED
# 92      alsa_output.usb-SteelSeries_Arctis_Nova_Pro_Wireless-00.iec958-stereo   PipeWire        s24le 2ch 48000Hz       RUNNING
```

In `nova.py`:
```
## Lines 48-50
# PW_ORIGINAL_SINK = (
#     "alsa_output.usb-SteelSeries_Arctis_Nova_Pro_Wireless-00.7.iec958-stereo" # Edit this line if needed
# )
```

If you want to run this script on startup you can add and enable the systemd service
```
## The systemd service expects the script in .local/bin
# Create the folder if it doesn't exist
mkdir -p ~/.local/bin
# Copy the script to the expected location
cp -i nova.py ~/.local/bin

# Create systemd user unit folder if it doesn't exist
mkdir -p ~/.config/systemd/user
# Install the service file
cp nova-chatmix.service ~/.config/systemd/user/
# Reload systemd configuration
systemctl --user daemon-reload
# Enable and start the service
systemctl --user enable nova-chatmix --now
```

### Run

You can now run the python script to use ChatMix. 
This will create 2 virtual sound devices:
- NovaGame for game/general audio
- NovaChat for chat audio

```
# You do not need to run this if you installed the systemd unit!
python nova.py
```

This command does not generate any output, but the Sonar icon should now be visible on the base station.

To use ChatMix select NovaGame as your main audio output, and select NovaChat as the output in your voice chat software of choice.


ChatMix should now work. You can toggle between volume and ChatMix by pressing the dial.

### Use as a library

You should also be able to use nova.py as a library.
<br>
Example:

```
from nova import NovaProWireless

nova = NovaProWireless()
nova.enable_sonar_icon()
nova.enable_chatmix()

# Output all received messages
nova.print_output(True)
```

## What's Next

Currently none of this is very polished, it should work, but that's about it. ~~I would like to make this a bit more integrated, so that it just works without having to run the python script every time.~~ I added a systemd service to automate starting the script.

There are also some other projects that try to make headset features work on linux, for example [HeadsetControl](https://github.com/Sapd/HeadsetControl). I might want to try and get some of this implemented in there.

I also want to figure out if this could be something that happens by default in PipeWire (or somewhere else). So that users of the headset don't need anything beside what already comes with their distribution.

While I'd like to do these things, I don't yet know if I will. Even in the current state of the project, it does work for me, so while I'd like for this to be a temporary solution, it might just stay like this.

If anyone else wants to work on these things, please do, I'd love to see it.

## License

This project is licensed under the Zero-Clause BSD license
