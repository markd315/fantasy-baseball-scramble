import json
from pathlib import Path

import anvil.server
import mlb_api


def add_chat(league, sender, msg):
    msg = msg.replace(">", "\\>")  # to avoid fake messages
    with open("leagues/" + league + "/Chat", "a") as chat_file:
        toAdd = ">" + sender + ": " + msg + "\n\n"
        chat_file.write(toAdd)
        chat_file.close()

def authenticateAndGetAbbv(league, teamNm):
    with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json",
              "r") as lineup_file:
        lineup = json.load(lineup_file)
        abbv = lineup['abbv']
        lineup_file.close()
        return abbv

def getLineup(league, teamNm):
    with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json",
              "r") as lineup_file:
        lineup = json.load(lineup_file)
        abbv = lineup['abbv']
        lineup_file.close()
        return lineup

def getRoster(league, abbv):
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster",
              "r") as roster_file:
        roster = roster_file.readlines()
        for idx, line in enumerate(roster):
            roster[idx] = line.strip()
        return roster

@anvil.server.http_endpoint('/league/:league/:teamNm/lineup', methods=["POST"], authenticate_users=False)
def post_lineup(league, teamNm, **q):
    set_lineup(league, teamNm, json.dumps(anvil.server.request.body_json))


@anvil.server.callable
def get_bench(league, teamNm):
    abbv = authenticateAndGetAbbv(league, teamNm)
    lineup = getLineup(league, teamNm)
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster",
              "r") as roster_file:
        roster = roster_file.readlines()
        for idx, line in enumerate(roster):
            roster[idx] = line.strip()
        starting_lineup = mlb_api.getAndValidateLineup(lineup, roster)
        bench = []
        for line in roster:
            if line not in starting_lineup:
                bench.append(line)
    return bench

@anvil.server.callable
def get_lineup(league, teamNm):
    try:
        with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json", "r") as lineup_file:
            ptl_lineup = json.load(lineup_file)
            return json.dumps(ptl_lineup, indent=2, separators=(',', ': '))
    except BaseException:
        return ""


@anvil.server.callable
def set_lineup(league, teamNm, lineup):
    lineup = json.loads(lineup)
    with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json",
              "r") as lineup_file:
        old_lineup = json.load(lineup_file)
        if old_lineup['team-name'] != lineup['team-name'] or old_lineup[
            'abbv'] != lineup['abbv']:
            raise BaseException("Invalid access attempt")
        else:
            abbv = old_lineup['abbv']
        lineup_file.close()
    roster = getRoster(league, abbv)
    mlb_api.getAndValidateLineup(lineup, roster)
    with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json",
              "w") as lineup_file:
        lineup_file.write(json.dumps(lineup, indent=2, separators=(',', ': ')))
        lineup_file.close()
    return {}

@anvil.server.callable
def drop_player(league, teamNm, player_drop):
    abbv = authenticateAndGetAbbv(league, teamNm)
    lineup = getLineup(league, teamNm)
    roster = getRoster(league, abbv)
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster",
              "w") as roster_file:
        starters = mlb_api.getAndValidateLineup(lineup, roster)
        if player_drop in roster and player_drop not in starters:
            roster.remove(player_drop)
        for idx, line in enumerate(roster):
            roster[idx] = line+'\n'
        roster[len(roster) - 1] = roster[len(roster) - 1].strip()
        roster_file.writelines(roster)
        roster_file.close()
        add_chat(league, "Waiver Drop", str(abbv) + " released " + player_drop)
    return {}


@anvil.server.callable
def add_player(league, teamNm, player_add):
    any_roster = []
    abbv = authenticateAndGetAbbv(league, teamNm)
    for p in Path("leagues/" + league + "/team-lineups/").glob('*.roster'):
        with open("leagues/" + league + "/team-lineups/" + p.name, "r") as roster_file:
            roster = roster_file.readlines()
            for line in roster:
                any_roster.append(line.strip())
            roster_file.close()
            if abbv in p.name:
                our_roster = roster
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster",
              "w") as roster_file:
        if player_add not in any_roster and len(our_roster) < 25:
            our_roster[len(our_roster) - 1] += "\n"
            our_roster.append(player_add)
        roster_file.writelines(our_roster)
        roster_file.close()
    add_chat(league, "Waiver Add", str(abbv) + " added " + player_add)
    return {}


@anvil.server.callable
def get_results(league, teamAbbv, week, selector):
    out_path = "leagues/" + league + "/debug_output/"
    if selector == "Team totals":
        name = teamAbbv + "_wk" + str(week) + "_totals.json"
        with open(out_path + name,
                  "r") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    elif selector == "Standings":
        with open("leagues/" + league + "/Standings", "r") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    elif selector == "League note":
        with open("leagues/" + league + "/League_note", "r") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    elif selector == "Chat":
        with open("leagues/" + league + "/Chat", "r") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    elif selector == "MLB Player Data":
        with open("playersTeamsAndPositions.json", "r", encoding="utf-8") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    else:  # game int or line score
        if selector == "Line scores":
            suffix = "wk" + str(week) + ".line"
        else:
            suffix = "-wk" + str(week) + "-" + str(selector)
        for p in Path(out_path).glob('*'):
            if p.name.endswith(suffix) and teamAbbv in p.name:
                with open(out_path + p.name, "r") as results_file:
                    ret = results_file.read()
                    results_file.close()
                    return ret

@anvil.server.callable
def send_chat(league, teamNm, msg):
    abbv = authenticateAndGetAbbv(league, teamNm)
    add_chat(league, abbv, msg)
