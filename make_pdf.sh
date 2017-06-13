#!/usr/bin/env bash
#
# Copyright © 2017 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

# Setup

#Bash should terminate in case a command or chain of command finishes with a non-zero exit status.
#Terminate the script in case an uninitialized variable is accessed.
#See: https://github.com/azet/community_bash_style_guide#style-conventions
set -e
set -u

# TODO remove DEBUGGING
# set -x

# Read Only variables

# readonly PROG_DIR=$(readlink -m $(dirname $0))
# readonly PROGNAME="$( cd "$( dirname "BASH_SOURCE[0]" )" && pwd )"

cleanup() {
    # put cleanup needs here
    exit 0
}

readonly FILE=$1
readonly IMAGE=$2
readonly LICENSE=$3
readonly TEMPLATE=$4
readonly OUTPUT=$5

main() {
    local BASENAME=$(basename "${FILE}")
    local PDFNAME="${BASENAME%.md}.pdf"
    local TEXNAME="${BASENAME%.md}.tex"
    pandoc -f markdown  -t latex --template=${TEMPLATE} \
           "${FILE}" \
        | sed 's/\\subsection/\\subsection*/g' \
        | sed "s@\[PROFILE_PHOTO\]@${IMAGE}@g" \
        | sed "s@\[PHOTO_LICENSE\]@${LICENSE}@g" \
              > ${OUTPUT}/"${TEXNAME}"
    lualatex --interaction=batchmode --output-directory=${OUTPUT} "${TEXNAME}"
    #lualatex --output-directory=latex latex/"${TEXNAME}"
    #mv latex/"${PDFNAME}" final/"${PDFNAME}"
}

trap 'cleanup' EXIT

main
