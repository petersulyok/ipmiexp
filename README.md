# ipmiexp
An IPMI explorer program.

### Features:
  - can show sensor data
  - can set sensor threshold
  - can set fan mode
  - can set zone level
  - can show events

 <img src="https://github.com/petersulyok/ipmiexp/raw/main/doc/ipmiexp.png" align="center" width="800">

## How to run?

```
git clone https://github.com/petersulyok/ipmiexp.git
cd ipmiexp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
ipmiexp 
```

## Further notes
- This program is using `ipmitool` 
- Must be executed with root privileges
- Default configuration file is stored at `~/.config/ipmiexp/setting.ini`
- You can exit from the program with pressing CTRL-Q
- The program is beta, not optimized, slowish... 