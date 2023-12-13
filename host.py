import os
import sys
import json
import struct
import src.parse
import src.speed
import src.offenses
import src.defenses
import src.optimize


def send_message(message):
    message_json = {"text": message}
    message_json = json.dumps(message_json).encode("utf-8")
    length = struct.pack("@I", len(message_json))

    sys.stdout.buffer.write(length)
    sys.stdout.buffer.write(message_json)
    sys.stdout.buffer.flush()


def get_message():
    length = sys.stdin.buffer.read(4)
    if len(length) == 0:
        sys.exit(0)

    length = struct.unpack("@I", length)[0]
    message = sys.stdin.buffer.read(length).decode("utf-8")
    
    return json.loads(message)["text"]


def main():
    message = get_message()
    
    meta_mons = src.parse.get_mons(message["moveset_url"], message["chaos_url"], int(message["num_mons"]))
    
    mon_data = src.parse.import_from_paste(message["mon_data"])
    mon_name = mon_data["Name"]

    offensive_EVs = src.offenses.allocate_offensive_EVs(mon_name, mon_data, src.offenses.get_offensive_benchmarks(mon_name, mon_data, meta_mons))
    defensive_EVs = src.defenses.allocate_defensive_EVs(mon_name, mon_data, meta_mons)
    speed_EVs = src.speed.allocate_speed_EVs(mon_name, mon_data, src.speed.get_speed_benchmarks(meta_mons), tailwind=False)
    
    opt_EVs = src.optimize.optimize_EVs(mon_name, offensive_EVs, defensive_EVs, speed_EVs, num_spreads=int(message["num_spreads"]), bias1=message["bias1"], bias2=message["bias2"])
    EV_calcs = [src.parse.print_EV_calcs(mon_name, mon_data, *EVs[1], EVs[0], *EVs[2:], print_to_stdout=False) for EVs in opt_EVs]
    
    message = [[opt_EVs[i][0], opt_EVs[i][1][0], list(opt_EVs[i][1][1]), list(EV_calcs[i])] for i in range(len(opt_EVs))]
    send_message(message)


if __name__ == "__main__":
    main()
