# Nova ChatMix For Linux

## About

Some SteelSeries headsets have a feature called ChatMix where you can easily adjust game and chat audio volume on the headphones or dongle.

In previous SteelSeries headsets ChatMix was always a hardware feature. It worked by providing 2 sound devices to the host, 1 for general audio and the other for chat audio.

In newer generations of their headsets however, in particular the Arctis Nova Pro Wireless, this feature was taken out of the hardware itself, and made into a feature of their audio software called Sonar.

Sonar of course only works on Windows and requires a SteelSeries account.

Even though it is now a software feature, the hardware can still control it, but only when Sonar activated this feature on the base station. You can toggle between normal volume controls and ChatMix by pressing down on the volume dial on either the headset or base station.

I wanted to be able to use ChatMix on Linux, so I reverse engineered the communication between Sonar and the base station to control 2 virtual PipeWire sinks.

## Disclaimer

THIS PROJECT HAS NO ASSOCIATION TO STEELSERIES, NOR IS IT IN ANY WAY SUPPORTED BY THEM.   
I AM NOT RESPONSIBLE FOR BRICKED/BROKEN DEVICES NOR DO I GUARANTEE IT WILL WORK FOR YOU.   
USING ANYTHING IN THIS PROJECT _MIGHT_ VOID YOUR WARRANTY AND IS AT YOUR OWN RISK.   


## Setup & Installation

### Arch Linux

#### Install

On Arch, you can build & install via `yay`:   
```sh
sudo yay -S nova-chatmix
```

#### Enable Service

Once installed, run the following to enable the service and persist between boots:   
```sh
systemctl --user enable nova-chatmix --now
```

You then should see the Sonar icon on your base station and the `NovaChat` and `NovaGame` audio devices on your system.

Set your chat applications _(like Discord)_ to output audio to `NovaChat` and your system audio to output to `NovaGame`. The volume of each can be controlled independently on the system level, and the mix can be controlled with your headset or base station.


> [!NOTE]
> If you do not see the Sonar icon or the Nova* audio devices, you might need to run `sudo udevadm control --reload-rules` and then the `systemctl` command mentioned above again.

#### Uninstall

If you wish to ever uninstall this package, run the following:   
```sh
sudo pacman -R nova-chatmix
```


### Other Distros

Installation on other Linux distros is more complicated at the moment. This will be made simpler in the future. Feel free to submit a PR for other distros.

#### Prerequisites
The following dependencies need to be installed prior to setting this project up:

- Python 3
- python3-hidapi
- PipeWire
- pactl

On Fedora these can be installed with:

```sh
sudo dnf install pulseaudio-utils python3 python3-hidapi
```

On Debian based systems (like Ubuntu or Pop!_OS) these can be installed with:

```sh
sudo apt install pulseaudio-utils python3 python3-hid
```

#### Install

Clone this repo and cd into it

```sh
git clone https://git.dymstro.nl/Dymstro/nova-chatmix-linux.git
cd nova-chatmix-linux
```

To be able to run the script as a non-root user, some udev rules need to be applied. This will allow regular users to access the base station USB device. It also starts the script when it gets plugged in (only when the systemd service is also set up).

Copy `50-nova-pro-wireless.rules` to `/etc/udev/rules.d` and reload udev rules:

```sh
sudo cp 50-nova-pro-wireless.rules /etc/udev/rules.d/

sudo udevadm control --reload-rules
sudo udevadm trigger
```

If you want to run this script on startup you can add and enable the systemd service

```sh
## The systemd service expects the script in .local/bin
# Create the folder if it doesn't exist
mkdir -p /usr/bin/nova-chatmix
# Copy the script to the expected location
cp -i nova.py /usr/bin/nova-chatmix

# Create systemd user unit folder if it doesn't exist
mkdir -p ~/.config/systemd/user
# Install the service file
cp nova-chatmix.service ~/.config/systemd/user/
# Reload systemd configuration
systemctl --user daemon-reload
# Enable and start the service
systemctl --user enable nova-chatmix --now
```

#### One-Time Run

> [!IMPORTANT]
> You do not need to run this if you installed the systemd unit!

You can run the python script manually to use ChatMix.
This will create 2 virtual sound devices:

- NovaGame for game/general audio
- NovaChat for chat audio

`python nova.py`

This command does not generate any output, but the Sonar icon should now be visible on the base station.

To use ChatMix, select `NovaGame` as your main audio output, and select `NovaChat` as the output in your voice chat software of choice.

ChatMix should now work. You can toggle between volume and ChatMix by pressing the dial.

## Technical Details

I started by installing SteelSeries GG and Sonar in a Windows 11 VM and passing through the base station USB device. On the Linux host I used Wireshark to see what happened when I enabled Sonar.

This device uses USB HID events to both configure and receive data from the base station. I identified which ones enabled what features and tried activating these on Linux using the /dev/hidraw\* device. See `commands.sh` for more information.

I am on MCU firmware version `01.29.27` and DSP firmware version `00.03.82`.

### Protocol Description

See `nova.py` for a commented example implementation.

The controls and data output are on USB Interface 4 (`bInterfaceNumber=4`). This interface has 2 endpoint, 1 for sending data (`0x04`) and 1 for receiving data (`0x84`).

The HID Data messages are structured as follows:

- The first byte decides wether we are sending or receiving. `0x6` means we sent it, `0x7` means we received it from the base station
- The second byte specifies the parameter, eg. `73` (`0x49`) to enable ChatMix
- The next bytes contain the value for that parameter, some parameters use 1 byte, some use more.
- Because the message should be 64 bytes long, the unused bytes should all be `0`

These are the parameters I have found:
<br>
_(There are quite a few more parameters, like sidetone and other settings, I just haven't documented those yet.)_

| Option | Description        | Parameters                                       | Range | Notes                                                       |
| ------ | ------------------ | ------------------------------------------------ | ----- | ----------------------------------------------------------- |
| 73     | ChatMix State      | - Boolean: State                                 | 0-1   |
| 141    | Sonar Icon State   | - Boolean: State                                 | 0-1   | I think this only toggles the icon, but that could be wrong |
| 37     | Volume Attenuation | - Integer: Attenuation                           | 0-56  | 0=max<br>56=mute                                            |
| 69     | ChatMix Controls   | - Integer: Game Volume<br>- Integer: Chat Volume | 0-100 |
| 46     | EQ Preset          | - Integer: Preset                                | 0-18  | Preset 4 is the custom EQ profile                           |
| 49     | Custom EQ Controls | - Integer: EQ Bar<br>- Integer: Value            | 0-40  | On the base station the value ranges from -20 to 20         |

## License

This project is licensed under the Zero-Clause BSD license
