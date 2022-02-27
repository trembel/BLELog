# BLELog

Philipp Schilk, 2022
PBL, ETH Zuerich
---

A (hopefully) robust BLE Datalogger, that receives, decodes, stores and displays characteristic data.

Based on the [bleak](https://github.com/hbldh/bleak) cross-platform Bluetooth backend.

# Installation:

BLELog works under Linux and Windows, but is much more stable under Linux (due to driver/backend differences).
If *at all* possible, use Linux. 

__WSL will not work.__

MacOS is not yet supported. While technically possible, it would require major work as device addresses are handled
differently.

Tested under Python 3.9.7.

Other (especially later) versions will likely work, but are not guaranteed.

## Linux:

First, clone this repository.

All dependencies can be installed via `pip` and are listed in `requirements.txt`.

I suggest setting up a virtual environment to run this script. 

To do so, run:

```bash
# Create a new venv:
python -m venv env

# Activate it:
source env/bin/activate

# Install dependencies:
pip install -r requirements.txt

```

You can always deactivate and activate this venv as follows:

```bash
# Deactivate the currently active venv:
deactivate

# Activate the venv:
source env/bin/activate
```

To run `BLELog`, execute `BLELog.py` with your venv active:
```bash
python BLELog.py
```

## Windows:

First, clone this repository.

All dependencies can be installed via `pip` and are listed in `requirements.txt`, with additional
windows-only requirements in `requirements_windows.txt`:

I suggest setting up a virtual environment to run this script. 

To do so, run:

```cmd
# Create a new venv:
python -m venv env

# Activate it:
env\Scripts\activate

# Install dependencies:
pip install -r requirements.txt

# Install additional windows-only dependencies:
pip install -r requirements_windows.txt
```

You can always deactivate and activate this venv as follows:

```cmd
# Deactivate the currently active venv:
deactivate

# Activate the venv:
env\Scripts\activate
```

To run `BLELog`, execute `BLELog.py` with your venv active:
```cmd
python BLELog.py
```

# Configuration:

To use BLELog, you will have to adapt some basic settings to your application.

Modify the following three files:

## config.py

Contains all connection parameters, including:

    - Device addresses and aliases
    - Characteristic information
    - Connection parameters

Read the included comments for more details.

## char_decoders.py:

Contains the functions used to decode characteristics data.

Read the included comments and look at the example implementations.

## plot.py:

Contains the live-plot setup. 

Read the included comments and look at the example implementations.

# Troubleshooting:

#### BLELog frozen/stuck after trying to close:
BLELog may take a short moment to fully terminate after the 'CTRL-C' shortcut
is pressed. It takes some time to gracefully shut down all connections, to avoid
any future connection problems.

Pressing 'CTRL-C' three times will panic-abort BLELog. This might leave
your Bluetooth connections or file I/O in an undefined state.

#### "Failed to open file" errors:
Make sure the folder you set `log2csv_folder_name` to in `config.py` exists.

#### Strange '?' symbols in output:
Either switch to a different terminal with unicode support, or enable the 
pure-ascii TUI with `plain_ascii_tui` in `config.py`.

#### Plot is not showing any data:
If the live-plot is not updating but data is arriving, you most likely have
to adapt `plot.py` for your setup. Is the device-address in `plot.py` set
correctly?

#### Any other kind of strange terminal/TUI behaviour:
While the default CURSES tui contains much more information, it sometimes
does not play nice with certain terminal emulators on some platforms. 

Using a different terminal emulator (for example Terminal vs cmd.exe 
in windows) often fixes the problem.

If the TUI seems to 'flicker', reducing the update rate (`curse_tui_interva` in
`config.py`) can help.

As a last resort, you can always fall back on the plain console TUI. 
(`tui_mode=TUI_Mode.CONSOLE` in `config.py`). It contains much less information,
but is much more compatible.

The console TUI does not support the 'g' shortcut to open the live 
data display. The `plotter_open_by_default` toggle in `config.py` can be
used if the plot is needed.


