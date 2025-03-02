#!/usr/bin/env bash
# ipmitool emulation

# IPMI get fan mode (raw 0x30 0x45 0x00)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x45" && $4 = "0x00" ]] ; then
    r=$((1 + (RANDOM % 4)))
    echo "$r"
    exit 0
fi

# IPMI set fan mode (raw 0x30 0x45 0x01)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x45" && $4 = "0x01" ]] ; then
    exit 0
fi

# IPMI set fan level (raw 0x30 0x70 0x66 0x01)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x70" && $4 = "0x66" && $5 = "0x01" ]] ; then
    exit 0
fi


# IPMI get fan level (raw 0x30 0x70 0x66 0x00)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x70" && $4 = "0x66" && $5 = "0x00" ]] ; then
    if (( $6 < 8 )); then
        echo ${RANDOM:0:2}
    else
        echo "0"
    fi
    exit 0
fi

# IPMI read sensors.
if [[ $1 = "-v" && $2 = "sdr" ]] ; then
    curdir=$(dirname $0)
    cat "$curdir/ipmitool_sdr_v.txt"
    exit 0
fi


