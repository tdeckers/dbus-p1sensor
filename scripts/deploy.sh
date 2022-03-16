#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rsync -av -e ssh --exclude 'venv' --exclude 'ext' --exclude '.vscode' --exclude '.git*' ${SCRIPT_DIR}/.. root@192.168.2.16:/data/etc/dbus-p1sensor