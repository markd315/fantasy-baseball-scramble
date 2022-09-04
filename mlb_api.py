import random
from datetime import datetime
from datetime import timedelta
import statsapi
import json
import processing
import simulationConfig


def validateOnRoster(player, roster):
    if player['fullName'] not in roster:
        raise(BaseException(player['fullName'] + " is in the lineup but not on their roster."))


def handedness(player):
    person_data = statsapi.player_stat_data(player['id'], group='hitting')
    handedness = []
    if person_data['bat_side'] == 'Left' or person_data['bat_side'] == 'Switch':
        handedness.append("LHB")
    if person_data['bat_side'] == 'Right' or person_data['bat_side'] == 'Switch':
        handedness.append("RHB")
    if person_data['pitch_hand'] == 'Left':
        handedness.append("LHP")
    if person_data['pitch_hand'] == 'Right':
        handedness.append("RHP")
    return handedness


def fillErrors(player, box_games):
    errs = []
    for game in box_games:
        for err in game['errors-blame']:
            if err in player['fullName']:
                inn = str(random.randint(1, 9)) + "."
                inn += str(random.randint(1, 3))
                errs.append({'inning': inn, 'name': player['fullName']})
    return errs


def getOffense(team):
    offense = []
    offense.extend(team['batting-order'])
    if team['pinch-hitter'] != '':
        offense.append(team['pinch-hitter'])
    if team['pinch-runner'] != '':
        offense.append(team['pinch-runner'])
    return offense


def getPitchers(team):
    pitchers = []
    pitchers.extend(team['starters'])
    pitchers.extend(team['bullpen'])
    pitchers.append(team['closer'])
    pitchers.append(team['fireman'])
    return pitchers


def getAndValidateLineup(team, roster):
    ret = getPitchers(team)
    ret.extend(getOffense(team))
    for pl in ret:
        #print(pl)
        if pl != "":
            player = playerQuery(pl)[0]
            validateOnRoster(player, roster)
    return ret

def loadLineup(league, team_name, box_games, weekNumber):
    with open("leagues/" + league + "/team-lineups/" + team_name + ".json", "r") as json_file:
        team = json.load(json_file)
        roster = []
        with open("leagues/" + league + "/team-lineups/" + team['abbv'] + ".roster", "r") as roster_file:
            roster = roster_file.readlines()
            for idx, line in enumerate(roster):
                roster[idx] = line.strip()
        team['batting-results'] = []
        team['batting-result-curr-idx'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        team['pitching-results'] = {}
        team['handedness'] = {}
        team['errors'] = {}
        positions_filled = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # ignore 0 slot and pitcher slot 1
        offense = getOffense(team)
        batterTotals = {}
        for idx, player in enumerate(offense):
            player = playerQuery(player)[0]
            team['handedness'][player['fullName']] = player['handedness']
            validateOnRoster(player, roster)
            code = player['primaryPosition']['code']
            if code == 'Y' or str(code) == "10":
                code = 1  # DH, TWP bats in pitcher spot
            code = int(code)
            positions_filled[code - 1] += 1
            totals = processing.filterPlayerPas(box_games, player)
            batterTotals[player['fullName'] + '_b'] = totals
            pas = processing.randomWalkOfWeeklyTotals(totals)
            if len(pas) < 5:
                print("Small sample for " + player['fullName'])
                #raise(BaseException("Not enough data for player " + player['fullName'] + " must be replaced by bench"))
            team['batting-results'].append(pas)
            errs = fillErrors(player, box_games)
            for err in errs:
                team['errors'][err['inning']] = {'game': 0, 'name': err['name']}
        # validate positions
        for idx, pos in enumerate(positions_filled):
            err = False
            if pos == 0:
                err = True
                print("position " + str(idx+1) + " not filled in " + team_name)
            if pos > 1:
                print("too many of position " + str(idx + 1) + " in " + team_name)
                err = True
            if err:
                print(positions_filled)
        if err:
            raise(BaseException("Invalid lineups found in teams playing this week"))
        pitchers = getPitchers(team)
        pitcherTotals = {}
        for player in pitchers:
            if player == '':
                continue
            player = playerQuery(player)[0]
            team['handedness'][player['fullName']] = player['handedness']
            # Commenting this out because there could be trades drops etc, validate elsewhere.
            # validateOnRoster(player, roster)
            totals = processing.filterPlayerPasDefensive(box_games, player)
            pitcherTotals[player['fullName'] + '_p'] = totals
            if simulationConfig.fatigueEnabled:
                pas = processing.fatigueBasedRandomizePitching(totals)
            else:
                pas = processing.trueRandomizePitchingTotals(totals)
            name = player["fullName"]
            team['pitching-results'][name] = pas
        team['bullpen'].append('Position Player')
        seq = ['walk', 'walk', 'hbp', 'in_play_out', "in_play_out", 'in_play_out', 'in_play_out', 'home run', 'double', 'single', 'single', 'single', 'k']
        team['pitching-results']['Position Player'] = []
        team['handedness']['Position Player'] = ['RHP', "RHB"]
        for i in range(0, 100):  #5*100 outs, almost 18 whole games of outs is plenty
            team['pitching-results']['Position Player'].extend(seq)
        random.shuffle(team['pitching-results']['Position Player'])
        playerTotals = {}
        for pl in batterTotals:
            for k, v in batterTotals[pl].items():
                if 'bat_' + k not in playerTotals:
                    playerTotals['bat_' + k] = 0
                playerTotals['bat_' + k] += v
        for pl in pitcherTotals:
            for k, v in pitcherTotals[pl].items():
                if 'pit_' + k not in playerTotals:
                    playerTotals['pit_' + k] = 0
                if k == 'ip':
                    ipart = int(v) + int(playerTotals['pit_' + k])
                    fpart = v - int(v) + playerTotals['pit_' + k] - int(playerTotals['pit_' + k])
                    fpart = round(fpart, 1)
                    if fpart > 0.3:
                        ipart += 1
                        fpart -= 0.3
                    playerTotals['pit_' + k] = round(float(ipart+fpart), 1)
                else:
                    playerTotals['pit_' + k] += v
        for pl in batterTotals:
            playerTotals[pl] = batterTotals[pl]
        for pl in pitcherTotals:
            playerTotals[pl] = pitcherTotals[pl]
        playerTotals['errors'] = team['errors']
        fileName = team['abbv'] + "_wk" + str(weekNumber) + "_totals.json"
        with open("leagues/" + league + "/debug_output/" + fileName, "w") as json_file:
            json_file.write(json.dumps(playerTotals, indent=2, separators=(',', ': ')))
        return team


def playerQuery(name=None, teamId=None, pos=None):  #  note: this will take a bit to complete.
    try:
        with open("playersTeamsAndPositions.json", "r", encoding='utf8') as json_file:
            data = json.load(json_file)
            if name != None:
                data = [a for a in data if a['fullName'] == name]
            if teamId != None:
                data = [a for a in data if a['currentTeam'] == int(teamId)]
            if pos != None:
                data = [a for a in data if
                        a['primaryPosition']['abbreviation'] == str(pos)]
            return data
    except FileNotFoundError:
        with open("playersTeamsAndPositions.json", "w") as json_file:
            players = statsapi.lookup_player(lookup_value="")
            write_players = []
            for pl_full in players:
                pl = {
                    "fullName": pl_full["fullName"],
                    "boxscoreName": pl_full['boxscoreName'],
                    "currentTeam": pl_full["currentTeam"]["id"],
                    "primaryPosition": pl_full['primaryPosition'],
                    "handedness": handedness(pl_full)
                }
                write_players.append(pl)
            json_file.write(json.dumps(write_players))
            json_file.close()
        return playerQuery(name, teamId, pos)


def getWeeklyBox(endtime=datetime.now(), duration_days=5):  # subtract timedelta to rule out games in progress
    end_date = endtime.strftime("%Y-%m-%d")
    begin = endtime - timedelta(days=duration_days)  #5 day lookback instead of 7 to prevent double starts?
    st_date = begin.strftime("%Y-%m-%d")
    games = statsapi.schedule(start_date=st_date, end_date=end_date, team="", opponent="", sportId=1, game_id=None)
    box_games = []
    for game in games:
        try:
            with open("cached-box-scores/" + str(game['game_id']) + ".json", "r") as json_file:
                game = json.load(json_file)
                box_games.append(game)
        except FileNotFoundError:  # Hit the API
            box = statsapi.boxscore_data(game['game_id'])
            f = open("cached-box-scores/" + str(game['game_id']) + ".json", "w")
            box['errors-detail'] = []
            box['errors-blame'] = []
            box['hbp'] = []
            box['hbp_pitcher'] = []
            box['catcher_interference'] = []
            box['cs'] = []
            box['cs_catcher'] = []  # apparently, may be a pitcher.
            pbp = statsapi.get("game_playByPlay",
                               {"gamePk": str(game['game_id'])})
            for play in pbp['allPlays']:
                if "event" in play["result"] and play["result"]["event"] == "Hit By Pitch" and play["result"]["eventType"] == "hit_by_pitch":
                    box['hbp'].append(play["matchup"]["batter"]["fullName"])
                    box['hbp_pitcher'].append(
                        play["matchup"]["pitcher"]["fullName"])
                if "event" in play["result"] and play["result"]["event"].startswith("Caught Stealing") and \
                        play["result"]["eventType"].startswith(
                            "caught_stealing"):
                    desc = play["result"]["description"].split(" ")
                    try:
                        catcher_index = desc.index("catcher")
                    except ValueError:
                        catcher_index = desc.index("pitcher")
                    try:
                        # by [player]
                        fn = desc[0]
                        ln = desc[1]
                        player = playerQuery(fn + " " + ln.strip(".,"))
                        box['cs'].append(player[0]['fullName'])
                        fn = desc[catcher_index + 1]
                        ln = desc[catcher_index + 2]
                        player = playerQuery(fn + " " + ln.strip(".,"))
                        box['cs_catcher'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled caught stealing")
                if "event" in play["result"] and play["result"]["event"] == "Catcher Interference" and \
                        play["result"]["eventType"] == "catcher_interf":
                    box['errors-detail'].append(play)
                    desc = play["result"]["description"].split(" ")
                    byIndex = desc.index("by")
                    try:
                        # by [player]
                        fn = desc[byIndex + 1]
                        ln = desc[byIndex + 2]
                        player = playerQuery(fn + " " + ln.strip(".,"))
                        box['errors-blame'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled fielding error")
                        box['errors-blame'].append("Unknown")
                if "event" in play["result"] and play["result"]["event"] == "Field Error" and play["result"][
                    "eventType"] == "field_error":
                    box['errors-detail'].append(play)
                    desc = play["result"]["description"].split(" ")
                    byIndex = desc.index("by")
                    try:
                        # by [position] [player]
                        if desc[byIndex + 2] == "baseman" or desc[byIndex + 2] == "fielder":
                            fn = desc[byIndex + 3]
                            ln = desc[byIndex + 4]
                        else:
                            fn = desc[byIndex + 2]
                            ln = desc[byIndex + 3]
                        player = playerQuery(fn + " " + ln.strip(".,"))
                        box['errors-blame'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled fielding error")
                        box['errors-blame'].append("Unknown")
            f.write(json.dumps(box))
            f.close()
            box_games.append(box)
    return box_games
