import datetime
import json
import os
from pathlib import Path

import anvil.server

import mlb_api
import notify_mail
import rosters
import scheduling
from rosters import getLineup, addPlayerValidated, checkDraftState, add_chat, authenticateAndGetAbbv


@anvil.server.callable
def getRoster(league, abbv):
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster", "r") as roster_file:
        roster = roster_file.readlines()
        for idx, line in enumerate(roster):
            roster[idx] = line.strip()
        return roster


@anvil.server.http_endpoint('/league/:league/:teamNm/lineup', methods=["POST"], authenticate_users=False)
def post_lineup(league, teamNm, **q):
    league = league.lower()
    set_lineup(league, teamNm, json.dumps(anvil.server.request.body_json))


@anvil.server.callable
def get_bench(league, teamNm):
    league = league.lower()
    abbv = authenticateAndGetAbbv(league, teamNm)
    lineup = getLineup(league, teamNm)
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster", "r") as roster_file:
        roster = roster_file.readlines()
        if len(roster) == 0:
            return "Your team hasn't started drafting yet, check current pick order by visiting Results > League Note"
        for idx, line in enumerate(roster):
            if line == "" or line == None:
                return "Your team hasn't started drafting yet, check current pick order by visiting Results > League Note"
            roster[idx] = line.strip()
        starting_lineup = mlb_api.getAndValidateLineup(lineup, roster)
        bench = []
        for line in roster:
            if line not in starting_lineup:
                bench.append(line)
    return bench, len(roster)

@anvil.server.callable
def get_lineup(league, teamNm):
    league = league.lower()
    try:
        ptl_lineup = getLineup(league, teamNm)
        return json.dumps(ptl_lineup, indent=2, separators=(',', ': '))
    except BaseException:
        return ""


@anvil.server.callable
def set_lineup(league, teamNm, lineup):
    league = league.lower()
    lineup = json.loads(lineup)
    with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json","r") as lineup_file:
        old_lineup = json.load(lineup_file)
        if old_lineup['team-name'] != lineup['team-name'] or old_lineup['abbv'] != lineup['abbv']:
            raise BaseException("Invalid access attempt")
        else:
            abbv = old_lineup['abbv']
        lineup_file.close()
    roster = getRoster(league, abbv)
    mlb_api.getAndValidateLineup(lineup, roster)
    with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json","w") as lineup_file:
        lineup_file.write(json.dumps(lineup, indent=2, separators=(',', ': ')))
        lineup_file.close()
    return {}


@anvil.server.callable
def drop_player(league, teamNm, player_drop):
    league = league.lower()
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
def get_rostered_team(league, player_nm, **q):
    rosters.get_rostered_team(league, player_nm)



@anvil.server.callable
def add_player(league, teamNm, player_add):
    if "\n" in player_add:
        return {}
    league = league.lower()
    abbv = authenticateAndGetAbbv(league, teamNm)
    if checkDraftState(league, abbv, player_add):
        return {}
    else:
        addPlayerValidated(league, abbv, player_add)
        add_chat(league, "Waiver Add", str(abbv) + " added " + player_add)
    return {}


@anvil.server.callable
def get_results(league, teamAbbv, week, selector):
    league = league.lower()
    out_path = "leagues/" + league + "/debug_output/"
    if selector == "Team totals":
        if week == "":
            return "Need to enter a `week` to get this result pane."
        if teamAbbv == "":
            return "This is a team-specific result. Enter the abbreviation for the team whose results you want."
        name = teamAbbv + "_wk" + str(week) + "_totals.json"
        with open(out_path + name,
                  "r") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    elif selector == "Standings":
        try:
            notify_mail.sendMail("markd315@gmail.com", "Standings were checked at " + str(datetime.datetime.now()), "Server Activity")
        except BaseException as exc1:
            print(exc1)
            pass
        with open("leagues/" + league + "/Standings", "r") as results_file:
            ret = results_file.read()
            results_file.close()
            return ret
    elif selector == "Schedule":
        weeks = scheduling.getWeeklySchedule(league, [])
        out = ""
        for idx, week in enumerate(weeks):
            out += "Week " + str(idx) + ":\n"
            for idx, gm in enumerate(week):
                if gm[0]['team-name'] != 'Bye' and gm[1]['team-name'] != 'Bye':
                    if len(weeks) == 10:  # Must be a 5 man league
                        if idx == 0:
                            out += gm[1]['team-name'] + "@" + gm[0]['team-name'] + " (4 games)\n"
                        else:
                            out += gm[1]['team-name'] + "@" + gm[0]['team-name'] + " (2 games)\n"
                        continue
                    out += gm[1]['team-name'] + "@" + gm[0]['team-name'] + "\n"
                else:
                    out += (gm[0]['team-name'] + gm[1]['team-name']).replace("Bye", "") + " Bye Week\n"
            out += "\n"
        return out
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
        try:
            if week == "" or int(week) > -1:
                print("getting the whole thing from server")
                with open("playersTeamsAndPositions.json", "r", encoding="utf-8") as results_file:
                    obj = json.load(results_file)
                    return json.dumps(obj)
            raise Exception("we received an array as input")
        except BaseException:  # Intended that we get this from parsing the weeks param if it's an array, hacky but saves us time
            playersQueried = week
            ret = []
            for name in playersQueried:
                ret.extend(mlb_api.playerQuery(name))
            return json.dumps(ret)
    else:  # game int or line score
        if week == "":
            return "Need to enter a `week` to get this result pane."
        if teamAbbv == "":
            return "This is a team-specific result. Enter the abbreviation for the team whose results you want."
        if selector == "Line scores":
            suffix = "wk" + str(week) + ".line"
        else:
            suffix = "-wk" + str(week) + "-" + str(selector.replace("Game ", ""))
        ret = ""
        for p in Path(out_path).glob('*'):
            if p.name.endswith(suffix) and teamAbbv in p.name:
                with open(out_path + p.name, "r") as results_file:
                    ret += results_file.read()
                    results_file.close()
        return ret

@anvil.server.callable
def send_chat(league, teamNm, msg):
    league = league.lower()
    abbv = authenticateAndGetAbbv(league, teamNm)
    add_chat(league, abbv, msg)


@anvil.server.callable
def load_trades(league, teamNm):
    league = league.lower()
    trades = {}
    for p in Path("leagues/" + league + "/team-lineups/trades").glob('*.json'):
        if p.name.startswith(teamNm + "-trade"):
            with open("leagues/" + league + "/team-lineups/trades/" + p.name, "r") as trade_file:
                lines = trade_file.readlines()
                code = p.name.replace(teamNm + "-trade", "").replace(".json", "")
                trades[code] = lines
                trade_file.close()
    return trades


@anvil.server.callable
def create_trade(league, teamNm, propose_send, propose_get, trade_team):
    league = league.lower()
    abbv = authenticateAndGetAbbv(league, teamNm)
    other_team_teamcode = None
    for p in Path("leagues/" + league + "/team-lineups").glob('*.json'):
        if not p.name.startswith("next_"):
            with open("leagues/" + league + "/team-lineups/" + p.name, "r") as lineup_file:
                json_obj = json.load(lineup_file)
                if json_obj['abbv'] == trade_team:
                    other_team_teamcode = p.name.replace(".json", "")
    if other_team_teamcode == None:
        return
    highest_number = 1
    trade_files = Path("leagues/" + league + "/team-lineups/trades").glob('*.json')
    found = True
    while found:
        found = False
        for p in trade_files:
            if p.name == other_team_teamcode + "-trade" + str(highest_number) + ".json":
                highest_number+=1
                found=True
                break
    full_file = other_team_teamcode + "-trade" + str(highest_number) + ".json"
    with open("leagues/" + league + "/team-lineups/trades/" + full_file, "w") as trade_file:
        trade = {}
        trade['from'] = abbv
        rcv, lose = [], []
        for line in propose_get.split("\n"):
            rcv.append(line.strip())
        for line in propose_send.split("\n"):
            lose.append(line.strip())
        trade['receive'] = lose
        trade['send'] = rcv
        trade_file.write(json.dumps(trade))
        trade_file.close()
    return {}


@anvil.server.callable
def delete_trade(league, teamNm, trade_code):
    league = league.lower()
    try:
        fn = "leagues/" + league + "/team-lineups/trades/" + teamNm + "-trade" + str(trade_code) + ".json"
        print(fn)
        os.remove(fn)
    except:
        pass


@anvil.server.callable
def approve_trade(league, teamNm, trade_code):
    league = league.lower()
    abbv = authenticateAndGetAbbv(league, teamNm)
    with open("leagues/" + league + "/team-lineups/trades/" + teamNm + "-trade" + str(trade_code) + ".json", "r") as trade_file:
        trade = json.load(trade_file)
    approving_roster = getRoster(league, abbv)
    requesting_roster = getRoster(league, trade['from'])
    for player in trade['send']:
        if player not in approving_roster:
            return
    for player in trade['receive']:
        if player not in requesting_roster:
            return
    if len(approving_roster) + len(trade['receive']) - len(trade['send']) > 25 or len(requesting_roster) + len(trade['send']) - len(trade['receive']) > 25:
        return
    msg = str(abbv) + " and " + trade['from'] + " exchange players:\n"
    for pl in trade['receive']:
        approving_roster.append(pl)
        requesting_roster.remove(pl)
        msg += pl + "\n"
    msg += "for:\n"
    for pl in trade['send']:
        approving_roster.remove(pl)
        requesting_roster.append(pl)
        msg += pl + "\n"
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster", "w") as roster_file:
        out = ""
        for pl in approving_roster:
            out += pl + "\n"
        out = out[:-1]
        roster_file.write(out)
        roster_file.close()
    with open("leagues/" + league + "/team-lineups/" + trade['from'] + ".roster", "w") as roster_file:
        out = ""
        for pl in requesting_roster:
            out += pl + "\n"
        out = out[:-1]
        roster_file.write(out)
        roster_file.close()
    delete_trade(league, teamNm, trade_code)
    add_chat(league, "Trade Executed", msg)


@anvil.server.callable
def clear_waiver_claims(league, team):
    rosters.clearWaiverClaims(league, team)


@anvil.server.callable
def add_to_waiver_claims(league, team, add, drop):
    if scheduling.isWaiverPeriod():
        rosters.addToWaiver(league, team, add, drop)
    else:
        rostered_team = rosters.get_rostered_team(league, add)
        if rostered_team != "":  # Not processing if adding a rostered player
            return
        if drop != "":
            rosters.removeFromLineup(league, team, drop)
            drop_player(league, team, drop)
        add_player(league, team, add)


@anvil.server.callable
def get_waiver_claims(league, team):
    return rosters.getWaiverClaims(league, team)
