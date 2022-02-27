#!/bin/bash
cd "$(dirname "$0")"

autopep8 ../blelog ../BLELog.py ../config.py ../plot.py ../char_decoders.py -r -i --global-config ../setup.cfg
echo "Formatted all python files..."
