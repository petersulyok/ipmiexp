#!/usr/bin/env bash
#
#   ipmitool_emu.sh (C) 2025, Peter Sulyok
#   This script will emulate the most important commands of `ipmitool`. It will persist fan mode and
#   zone level information in the system temporary directory (e.g. /tmp/ipmiexp/...)
#

# Check the program temporary directory and create it if needed.
tmp_dir=$(dirname "$(mktemp -u)")/ipmiexp
if [ ! -d "$tmp_dir" ]; then
    mkdir -p $tmp_dir
    echo "1" >$tmp_dir/fan_mode
    echo "64" >$tmp_dir/zone0
    echo "64" >$tmp_dir/zone1
    echo "64" >$tmp_dir/zone2
    echo "64" >$tmp_dir/zone3
    echo "64" >$tmp_dir/zone4
    echo "64" >$tmp_dir/zone5
    echo "64" >$tmp_dir/zone6
    echo "64" >$tmp_dir/zone7
fi

# IPMI get fan mode (raw 0x30 0x45 0x00)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x45" && $4 = "0x00" ]] ; then
    file=$tmp_dir/fan_mode
    if [ -f "$file" ]; then
        r=$(<"$file")
    else
        r=$((1 + (RANDOM % 4)))
    fi
    echo "$r"
    exit 0
fi

# IPMI set fan mode (raw 0x30 0x45 0x01 mode)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x45" && $4 = "0x01" ]] ; then
    file=$tmp_dir/fan_mode
    echo "$5" > "$file"
    case "$5" in
        "0")
            # Standard mode: level 50% in all zones.
            for i in $(seq 0 7); do
                echo "32" > "$tmp_dir/zone$i"
            done
            ;;
        "1")
            # Full mode: level 100% in all zones.
            for i in $(seq 0 7); do
                echo "64" > "$tmp_dir/zone$i"
            done
            ;;
        "2")
            # Optimal mode: level 30% in all zones.
            for i in $(seq 0 7); do
                echo "1e" > "$tmp_dir/zone$i"
            done
            ;;
        "3")
            # Randomly this mode will generate an error.
            if [[ $(($RANDOM % 2)) -eq 1 ]]; then
                >&2 echo "Unable to send RAW command (channel=0x0 netfn=0x30 lun=0x0 cmd=0x45 rsp=0xcc): Invalid data field in request"
                exit 1
            fi
            # PUE mode: level 30% in all zones.
            for i in $(seq 0 7); do
                echo "1e" > "$tmp_dir/zone$i"
            done
            ;;
        "4")
            # Heavy IO mode: CPU zone 30%, HD zone 75%.
            echo "1e" > "$tmp_dir/zone0"
            echo "4b" > "$tmp_dir/zone1"
            echo "1" > "$tmp_dir/zone2"
            echo "1" > "$tmp_dir/zone3"
            echo "1" > "$tmp_dir/zone4"
            echo "1" > "$tmp_dir/zone5"
            echo "1" > "$tmp_dir/zone6"
            echo "1" > "$tmp_dir/zone7"
            ;;
    esac
    exit 0
fi

# IPMI set fan level (raw 0x30 0x70 0x66 0x01 zone level)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x70" && $4 = "0x66" && $5 = "0x01" ]] ; then
    file=$tmp_dir/zone$6
    printf "%x" "$7" > "$file"
    exit 0
fi

# IPMI get fan level (raw 0x30 0x70 0x66 0x00 zone)
if [[ $1 = "raw" && $2 = "0x30" && $3 = "0x70" && $4 = "0x66" && $5 = "0x00" ]] ; then
    if (( $6 < 8 )); then
        file=$tmp_dir/zone$6
        if [ -f "$file" ]; then
            r=$(<"$file")
        else
            r=$(printf "%x" "$((1 + (RANDOM % 100)))")
        fi
        echo "$r"
    else
        echo "00"
    fi
    exit 0
fi

# IPMI read sensors.
if [[ $1 = "-v" && $2 = "sdr" ]] ; then
    curdir=$(dirname "$0")
    cat "$curdir/ipmitool_v_sdr_2500.txt"
    exit 0
fi

# IPMI read events.
if [[ $1 = "sel" && $2 = "elist" ]] ; then
    curdir=$(dirname "$0")
    cat "$curdir/ipmitool_sel_elist.txt"
    exit 0
fi

# IPMI set sensor threshold.
if [[ $1 = "sensor" && $2 = "thresh" ]] ; then
    exit 0
fi

# IPMI bmc info command.
if [[ $1 = "bmc" && $2 = "info" ]] ; then
    cat <<EOF
Device ID                 : 32
Device Revision           : 1
Firmware Revision         : 1.74
IPMI Version              : 2.0
Manufacturer ID           : 10876
Manufacturer Name         : Super Micro Computer Inc.
Product ID                : 6929 (0x1b11)
Product Name              : X11SCH-LN4F
Device Available          : yes
Provides Device SDRs      : no
Additional Device Support :
    Sensor Device
    SDR Repository Device
    SEL Device
    FRU Inventory Device
    IPMB Event Receiver
    IPMB Event Generator
    Chassis Device
Aux Firmware Rev Info     : 
    0x19
    0x01
    0x00
    0x00
EOF
    exit 0
fi


# IPMI bmc reset command.
if [[ $1 = "bmc" && $2 = "reset" ]] ; then
    exit 0
fi

# Unknown command.
exit 1

# End.
