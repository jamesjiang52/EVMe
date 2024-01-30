import os
import sys
import re
import praw
from dotenv import dotenv_values
import src.parse
import src.speed
import src.offenses
import src.defenses
import src.optimize


secrets = dotenv_values(".env")

reddit = praw.Reddit(
    client_id=secrets["CLIENT_ID"],
    client_secret=secrets["CLIENT_SECRET"],
    password=secrets["PASSWORD"],
    username=secrets["USERNAME"],
    user_agent=secrets["USER_AGENT"]
)


def main():
    sub = reddit.subreddit("VGC")
    num_mons_re = re.compile(".*num\\\_mons:\s*(\d+).*", re.M | re.DOTALL)
    num_spreads_re = re.compile(".*num\\\_spreads:\s*(\d+).*", re.M | re.DOTALL)
    bias1_re = re.compile(".*bias1:\s*([a-zA-Z]+).*", re.M | re.DOTALL)
    bias2_re = re.compile(".*bias2:\s*([a-zA-Z]+).*", re.M | re.DOTALL)

    for comment in sub.stream.comments():
        if "/u/suggest-a-spread-bot" in comment.body:
            num_mons = 12
            num_spreads = 3
            bias1 = None
            bias2 = None
            print(comment.body)

            if "num\\_mons:" in comment.body:
                num_mons = int(re.match(num_mons_re, comment.body).group(1))

            if "num\\_spreads:" in comment.body:
                num_spreads = int(re.match(num_spreads_re, comment.body).group(1))

            if "bias1:" in comment.body:
                bias1 = re.match(bias1_re, comment.body).group(1)

            if "bias2:" in comment.body:
                bias2 = re.match(bias2_re, comment.body).group(1)

            meta_mons = src.parse.get_mons(
                "https://raw.githubusercontent.com/jamesjiang52/EVMe/main/data/moveset.txt",
                "https://raw.githubusercontent.com/jamesjiang52/EVMe/main/data/chaos.json",
                num_mons
            )

            print(num_mons, num_spreads, bias1, bias2)

            mon_data = src.parse.import_from_paste(comment.body)
            mon_name = mon_data["Name"]

            offensive_EVs = src.offenses.allocate_offensive_EVs(mon_name, mon_data, src.offenses.get_offensive_benchmarks(mon_name, mon_data, meta_mons))
            defensive_EVs = src.defenses.allocate_defensive_EVs(mon_name, mon_data, meta_mons)
            speed_EVs = src.speed.allocate_speed_EVs(mon_name, mon_data, src.speed.get_speed_benchmarks(meta_mons), tailwind=False)

            opt_EVs = src.optimize.optimize_EVs(mon_name, offensive_EVs, defensive_EVs, speed_EVs, num_spreads=num_spreads, bias1=bias1, bias2=bias2)
            EV_calcs = [src.parse.print_EV_calcs(mon_name, mon_data, *EVs[1], EVs[0], *EVs[2:], print_to_stdout=False) for EVs in opt_EVs]

            suggested_EVs_info = [[opt_EVs[i][0], opt_EVs[i][1][0], list(opt_EVs[i][1][1]), list(EV_calcs[i])] for i in range(len(opt_EVs))]
            reply = "Suggested spreads:\n\n---\n\n";

            for EVs_info in suggested_EVs_info:
                EV_list = EVs_info[2]
                reply += str(EV_list[0]) + " HP / " + str(EV_list[1]) + " Atk / " + str(EV_list[2]) + " Def / " + str(EV_list[3]) + " SpA / " + str(EV_list[4]) + " SpD / " + str(EV_list[5]) + " Spe\n\n"
                reply += EVs_info[1] + " Nature\n\n"
                reply += str(EVs_info[0]) + " Remaining EVs\n\n"

                for calc in EVs_info[3]:
                    if calc != "N/A":
                        reply += calc + "\n\n"

                reply += "\n\n---\n\n"

            comment.reply(reply + "^(Beep boop, I am a bot.)\n\n^(Want to see what I'm made of? Check out: ) [^GitHub ](https://github.com/jamesjiang52/EVMe)")


if __name__ == "__main__":
    main()
