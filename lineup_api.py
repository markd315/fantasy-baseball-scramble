from datetime import datetime
from datetime import timedelta
import statsapi
import json

import processing


def loadLineup(team_name, box_games):
    with open("team-lineups/" + team_name + ".json", "r") as json_file:
        team = json.load(json_file)
        team['batting-results'] = []
        team['batting-result-curr-idx'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        team['pitching-results'] = {}
        positions_filled = [1, 0, 0, 0, 0, 0, 0, 0, 0] # ignore 0 slot and pitcher slot 1
        for idx, player in enumerate(team['batting-order']):
            player = statsapi.lookup_player(player)[0]
            if player['fullName'] != team['designated-hitter']:
                code = player['primaryPosition']['code']
                if code == 'Y':
                    raise(BaseException(player['fullName'] + " must be the designated hitter s they are a TWP"))
                if int(code) > 9:
                    raise (BaseException(player['fullName'] + " must be the designated hitter s they are primarily a DH"))
            if player['primaryPosition']['code'] != 'Y' and player['fullName'] != team['designated-hitter']:
                #print(player)
                positions_filled[int(player['primaryPosition']['code']) - 1] += 1

            totals = processing.filterPlayerPas(box_games, player)
            pas = processing.randomWalkOfWeeklyTotals(totals)
            team['batting-results'].append(pas)
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
        pitchers = team['starters']
        pitchers.extend(team['bullpen'])
        pitchers.append(team['closer'])
        pitchers.append(team['long-reliever'])
        pitchers.append(team['fireman'])
        for player in pitchers:
            # print(player)
            player = statsapi.lookup_player(player)
            totals = processing.filterPlayerPasDefensive(box_games, player[0])
            pas = processing.randomWalkOfWeeklyPitchingTotals(totals)
            name = player[0]["fullName"]
            team['pitching-results'][name] = pas
        return team


def scrapePlayerPositions(name=None, teamId=None, pos=None):  #  note: this will take a bit to complete.
    try:
        with open("playersTeamsAndPositions.json", "r") as json_file:
            pass
    except FileNotFoundError:
        with open("playersTeamsAndPositions.json", "w") as json_file:
            players = statsapi.lookup_player(lookup_value="")
            write_players = []
            for pl_full in players:
                pl = {"fullName": pl_full["fullName"],
                    "currentTeam": pl_full["currentTeam"]["id"],
                    "primaryPosition": pl_full['primaryPosition']
                      }
                write_players.append(pl)
            json_file.write(json.dumps(write_players))
            json_file.close()
    with open("playersTeamsAndPositions.json", "r") as json_file:
        data = json.load(json_file)
        if name != None:
            data = [a for a in data if a['fullName'] == name]
        if teamId != None:
            data = [a for a in data if a['currentTeam'] == int(teamId)]
        if pos != None:
            data = [a for a in data if a['primaryPosition']['abbreviation'] == str(pos)]
        return data


def getWeeklyBox(endtime=datetime.now() - timedelta(days=0.5),
                 duration_days=6):  # To rule out games in progress
    # TODO revert test
    end_date = endtime.strftime("%Y-%m-%d")
    begin = endtime - timedelta(
        days=duration_days)  # 6 day lookback instead of 7 to prevent double starts?
    st_date = begin.strftime("%Y-%m-%d")
    games = statsapi.schedule(start_date=st_date, end_date=end_date,
                              team="",
                              opponent="", sportId=1, game_id=None)
    box_games = []
    for game in games:
        try:
            with open("cached-box-scores/" + str(game['game_id']) + ".json",
                      "r") as json_file:
                # print(str(game['game_id']))
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
                if play["result"]["event"] == "Hit By Pitch" and play["result"]["eventType"] == "hit_by_pitch":
                    box['hbp'].append(play["matchup"]["batter"]["fullName"])
                    box['hbp_pitcher'].append(
                        play["matchup"]["pitcher"]["fullName"])
                if play["result"]["event"].startswith("Caught Stealing") and \
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
                        player = statsapi.lookup_player(
                            fn + " " + ln.strip(".,"))
                        box['cs'].append(player[0]['fullName'])
                        fn = desc[catcher_index + 1]
                        ln = desc[catcher_index + 2]
                        player = statsapi.lookup_player(
                            fn + " " + ln.strip(".,"))
                        box['cs_catcher'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled caught stealing")
                if play["result"]["event"] == "Catcher Interference" and \
                        play["result"]["eventType"] == "catcher_interf":
                    box['errors-detail'].append(play)
                    desc = play["result"]["description"].split(" ")
                    byIndex = desc.index("by")
                    try:
                        # by [player]
                        fn = desc[byIndex + 1]
                        ln = desc[byIndex + 2]
                        player = statsapi.lookup_player(
                            fn + " " + ln.strip(".,"))
                        box['errors-blame'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled fielding error")
                        box['errors-blame'].append("Unknown")
                if play["result"]["event"] == "Field Error" and play["result"][
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
                        player = statsapi.lookup_player(
                            fn + " " + ln.strip(".,"))
                        box['errors-blame'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled fielding error")
                        box['errors-blame'].append("Unknown")
            f.write(json.dumps(box))
            f.close()
            box_games.append(box)
    return box_games
