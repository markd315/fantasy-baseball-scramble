
from datetime import datetime
from datetime import timedelta
import random
import statsapi
import json
import statistics

trackedBattingStats = ['ab', 'h', 'doubles', 'triples', 'hr', 'sb', 'bb', 'k']
trackedPitchingStats = ['ip', 'h', 'bb', 'k', 'hr']
hitRatios = [0.771, 0.25, 0.019]# single double triple
# doubles rate from cubs 2021 season (788 non home runs) as the median doubles team
# triples stats from brewers 2021 season as a median triples team
# the hit ratios are only used for pitching simulations since we have detailed hit stats for batters

innings = 9

def randomWalkOfWeeklyTotals(weekly_totals):
    outcomes = ['k', 'in_play_out', 'walk', 'hbp', '1', '2', '3', '4']
    plateapps = []
    for outcome in outcomes:
        for i in range(0, int(weekly_totals[outcome])):
            plateapps.append(outcome)
    random.shuffle(plateapps)
    for i in range(0, weekly_totals['sb']):
        valid = False
        while not valid:
            idx = random.randint(0, len(plateapps) -1)
            res = plateapps[idx]
            on_base_stealable = ['walk', 'hbp', '1', '2']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+sb'
    for i in range(0, weekly_totals['cs']):
        valid = False
        while not valid:
            idx = random.randint(0, len(plateapps) -1)
            res = plateapps[idx]
            on_base_stealable = ['walk', 'hbp', '1', '2']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+cs'
    return plateapps


def randomWalkOfWeeklyPitchingTotals(weekly_totals):
    outcomes = ['k', 'in_play_out', 'walk', 'hbp', '1', '2', '3', '4']
    plateapps = []
    for outcome in outcomes:
        for i in range(0, int(weekly_totals[outcome])):
            plateapps.append(outcome)
    random.shuffle(plateapps)
    for i in range(0, weekly_totals['wp']):
        valid = False
        while not valid:
            idx = random.randint(0, len(plateapps) -1)
            res = plateapps[idx]
            on_base_stealable = ['walk', '1', '2']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+wp'
    return plateapps

def outcomeFromStats(team, orderSlot):
    idx = orderSlot - 1
    res_idx = team['batting-result-curr-idx'][idx]
    res = team['batting-results'][idx][int(res_idx)]
    length = len(team['batting-results'][idx])
    res_idx += 1
    if res_idx >= length:
        res_idx -= length
    team['batting-result-curr-idx'][idx] = res_idx
    return res

doublePlayRatioOnOutsWhenRunnerOnFirst = .17  # No source for this. Wild guess.
sacrificeBuntRatio = .07
productiveOutToThirdRatio = .10
sacrificeFlyToHomeRatio = .25
firstToThirdSingleRatio = .45

# simnning stealbase and simoffensivegame based on https://github.com/markd315/baseball-softball-lineup-tester/blob/master/lineup.py
def simOffensiveInning(team, orderSlot, inning):
    if inning > 9:
        baseState = [0, 1, 0]
    else:
        baseState = [0, 0, 0]
    runs = 0
    outs = 0
    while outs < 3:
        player_nm = team['batting-order'][orderSlot - 1]
        outcome = outcomeFromStats(team, orderSlot)
        print("(outs: " + str(outs) + ") " + player_nm + " at-bat: " + outcome)
        if (outcome == "k"):
            outs += 1
        if (outcome == "in_play_out"):
            outs += 1
            rng = random.uniform(0, 1)
            if (baseState[2] == 1 and outs < 3):
                if (rng > 1.0 - sacrificeFlyToHomeRatio):
                    print("sacrifice runner scores")
                    runs += 1
                    baseState[2] = 0
            # don't reroll, if we can't score the run home we won't advance to third
            if (baseState[1] == 1 and baseState[2] == 0 and outs < 3):
                if (rng > 1.0 - productiveOutToThirdRatio):
                    print("sacrifice runner moved to 3rd")
                    baseState[2] = 1
                    baseState[1] = 0
            if (baseState[0] == 1 and outs < 3):
                if (rng < doublePlayRatioOnOutsWhenRunnerOnFirst):
                    print("double play (6-4-3/4-6-3)")
                    outs += 1
                    baseState[0] = 0
                elif (baseState[1] == 0 and rng > 1.0 - sacrificeBuntRatio):
                    print("sacrifice runner moved to 2nd")
                    baseState[1] = 1
                    baseState[0] = 0
                elif (baseState[2] == 0 and rng > 1.0 - sacrificeBuntRatio):
                    print("sacrifice both runners advance")
                    baseState[2] = 1
                    baseState[1] = 1
                    baseState[0] = 0
        stolen = False
        out_stealing = False
        if outcome.endswith("+sb"):
            stolen = True
            outcome = outcome[0:-3]
        if outcome.endswith("+cs"):
            stolen = True
            out_stealing = True
            outcome = outcome[0:-3]
        if (outcome == "4"):
            runs += 1 + baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 0]
        if (outcome == "3"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 1]
        if (outcome == "2"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 1, 0]
        if (outcome == "1"):
            runs += baseState[1] + baseState[2]
            baseState[2] = 0
            baseState[1] = 0
            if (baseState[0] == 1):
                rng = random.uniform(0, 1)
                if (rng > 1.0 - firstToThirdSingleRatio):
                    print("runner first to third")
                    baseState[2] = 1
                else:
                    baseState[1] = 1
            baseState[0] = 1
        if (outcome == "walk" or outcome == "hbp"):
            if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                runs += 1
            elif (baseState[0] == 1 and baseState[2] == 1):  # 13 loads it
                baseState[1] = 1
            elif (baseState[0] == 1 and baseState[1] == 1):  # 12 loads it
                baseState[2] = 1
            elif (baseState[1] == 1 and baseState[2] == 1):  # 23 loads it
                baseState[0] = 1
            elif (baseState[0] == 1):  # 1 pushed to second
                baseState[1] = 1
            else:  # first empty
                baseState[0] = 1
        if stolen or out_stealing:
            if outcome == 'walk' or outcome == 'hbp':
                outcome = 1
            chk_empty_base = int(outcome)
            if out_stealing:
                baseState[chk_empty_base - 1] = 0
                outs += 1
                print(player_nm + " was picked off and is out")
                print(baseState)
            elif baseState[chk_empty_base] == 0:
                baseState[chk_empty_base] = 1
                baseState[chk_empty_base - 1] = 0
                print(player_nm + " stole a base")
                print(baseState)
            else:
                print(player_nm + " had a good jump but the next base was occupied")
        orderSlot += 1
        if (orderSlot > 9):
            orderSlot -= 9
    print(team["team-name"] + " scored: " + str(runs/2.0))
    return {"orderSlot": orderSlot, "runs": runs}



def simOffensiveGame(team):
    runs = 0
    orderSlot = 1  # need scoped to game method
    for inn in range(0, innings):
        result = simOffensiveInning(team, orderSlot, inn)
        orderSlot = result["orderSlot"]
        runs += result["runs"]
    print("Game over, run count: " + str(runs))
    return runs



def filterPlayerPas(box_games, player):
    arr = []
    box_nm = player['boxscoreName']
    game_lines = []
    for box in box_games:
        if box['away']['team']['id'] == player['currentTeam']['id']:
            for batter in box['awayBatters']:
                if box_nm in batter['namefield']:
                    game_lines.append(batter)
        if box['home']['team']['id'] == player['currentTeam']['id']:
            for batter in box['homeBatters']:
                if box_nm in batter['namefield']:
                    game_lines.append(batter)
    weekly_totals = {
        'ab': 0, 'h': 0, 'doubles': 0, 'triples': 0, 'hr': 0,
        'sb': 0, 'cs': 0, 'bb': 0, 'k': 0, 'e': 0, 'hbp': 0
    }
    for game in game_lines:
        for attribute in game:
            if attribute in trackedBattingStats:
                weekly_totals[attribute] += int(game[attribute])
    weekly_totals['2'] = weekly_totals['doubles']
    weekly_totals['3'] = weekly_totals['triples']
    weekly_totals['4'] = weekly_totals['hr']
    weekly_totals['1'] = weekly_totals['h'] - weekly_totals['2'] - weekly_totals['3'] - weekly_totals['4']
    weekly_totals['out'] = weekly_totals['ab'] - weekly_totals['h']
    weekly_totals['pa'] = weekly_totals['ab'] + weekly_totals['bb']
    weekly_totals['in_play_out'] = weekly_totals['out'] - weekly_totals['k']
    weekly_totals['walk'] = weekly_totals['bb']
    weekly_totals['e'] = 0
    for box in box_games:
        for blame in box['errors-blame']:
            if blame in player['fullName']:
                weekly_totals['e'] += 1
        for hit in box['hbp']:
            if hit in player['fullName']:
                weekly_totals['hbp'] += 1
    return weekly_totals


def filterPlayerPasDefensive(box_games, player):
    arr = []
    box_nm = player['boxscoreName']
    game_lines = []
    for box in box_games:
        if box['away']['team']['id'] == player['currentTeam']['id']:
            for pitcher in box['awayPitchers']:
                if box_nm in pitcher['namefield']:
                    game_lines.append(pitcher)
        if box['home']['team']['id'] == player['currentTeam']['id']:
            for pitcher in box['homePitchers']:
                if box_nm in pitcher['namefield']:
                    game_lines.append(pitcher)
    weekly_totals = {
        'ip': 0.0, 'h': 0, 'bb': 0, 'k': 0, 'hr': 0, 'wp': 0, 'e': 0, 'hbp': 0
    }
    for game in game_lines:
        for attribute in game:
            if attribute in trackedPitchingStats:
                weekly_totals[attribute] += float(game[attribute])
    ipart = int(weekly_totals['ip'])
    fpart = (weekly_totals['ip'] - int(weekly_totals['ip'])) * 10.0
    weekly_totals['out'] = int(fpart + ipart*3.0)
    hits_in_the_park = int(weekly_totals['h'] - weekly_totals['hr'])
    weekly_totals['1'] = 0
    weekly_totals['2'] = 0
    weekly_totals['3'] = 0
    for i in range(0,hits_in_the_park):
        rng = random.uniform(0, 1)
        if rng < hitRatios[0]:
            weekly_totals['1'] += 1
        elif rng < hitRatios[1] + hitRatios[0]:
            weekly_totals['2'] += 1
        else:
            weekly_totals['3'] += 1
    weekly_totals['ab'] = int(weekly_totals['h'] + weekly_totals['out'])
    weekly_totals['4'] = int(weekly_totals['hr'])
    weekly_totals['pa'] = int(weekly_totals['ab'] + weekly_totals['bb'])
    weekly_totals['in_play_out'] = int(weekly_totals['out'] - weekly_totals['k'])
    weekly_totals['walk'] = int(weekly_totals['bb'])
    weekly_totals['e'] = 0
    for box in box_games:
        for blame in box['errors-blame']:
            if blame in player['fullName']:
                weekly_totals['e'] += 1
        for hit in box['hbp_pitcher']:
            if hit in player['fullName']:
                weekly_totals['hbp'] += 1
    return weekly_totals


def loadLineup(team_name, box_games):
    with open("team-lineups/" + team_name + ".json", "r") as json_file:
        team = json.load(json_file)
        team['batting-results'] = []
        team['batting-result-curr-idx'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        team['pitching-results'] = {}
        for idx, player in enumerate(team['batting-order']):
            player = statsapi.lookup_player(player)
            totals = filterPlayerPas(box_games, player[0])
            pas = randomWalkOfWeeklyTotals(totals)
            team['batting-results'].append(pas)
        pitchers = team['starters']
        pitchers.extend(team['bullpen'])
        pitchers.append(team['closer'])
        pitchers.append(team['long-reliever'])
        pitchers.append(team['fireman'])
        for player in pitchers:
            #print(player)
            player = statsapi.lookup_player(player)
            totals = filterPlayerPasDefensive(box_games, player[0])
            pas = randomWalkOfWeeklyPitchingTotals(totals)
            name = player[0]["fullName"]
            team['pitching-results'][name] = pas
        return team


def getWeeklyBox():
    now = datetime(year=2022, month=8, day=16, hour=20, minute=0, second=0)
    # TODO revert test
    #now = datetime.now()
    yesterday = now - timedelta(days=0.5) # To rule out games in progress
    end_date = yesterday.strftime("%Y-%m-%d")
    begin = yesterday - timedelta(days=5) # 5 day lookback instead of 7 to prevent double starts?
    st_date = begin.strftime("%Y-%m-%d")
    games = statsapi.schedule(start_date=st_date, end_date=end_date,
                              team="",
                              opponent="", sportId=1, game_id=None)
    box_games = []
    for game in games:
        try:
            with open("cached-box-scores/" + str(game['game_id']) + ".json",
                      "r") as json_file:
                #print(str(game['game_id']))
                game = json.load(json_file)
                box_games.append(game)
        except FileNotFoundError: # Hit the API
            box = statsapi.boxscore_data(game['game_id'])
            f = open("cached-box-scores/" + str(game['game_id']) + ".json", "w")
            box['errors-detail'] = []
            box['errors-blame'] = []
            box['hbp'] = []
            box['hbp_pitcher'] = []
            box['catcher_interference'] = []
            box['cs'] = []
            box['cs_catcher'] = [] # apparently, may be a pitcher.
            pbp = statsapi.get("game_playByPlay",
                               {"gamePk": str(game['game_id'])})
            for play in pbp['allPlays']:
                if play["result"]["event"] == "Hit By Pitch" and play["result"]["eventType"] == "hit_by_pitch":
                    box['hbp'].append(play["matchup"]["batter"]["fullName"])
                    box['hbp_pitcher'].append(play["matchup"]["pitcher"]["fullName"])
                if play["result"]["event"].startswith("Caught Stealing") and play["result"]["eventType"].startswith("caught_stealing"):
                    desc = play["result"]["description"].split(" ")
                    try:
                        catcherIndex = desc.index("catcher")
                    except ValueError:
                        catcherIndex = desc.index("pitcher")
                    try:
                        # by [player]
                        fn = desc[0]
                        ln = desc[1]
                        player = statsapi.lookup_player(fn + " " + ln.strip(".,"))
                        box['cs'].append(player[0]['fullName'])
                        fn = desc[catcherIndex + 1]
                        ln = desc[catcherIndex +2]
                        player = statsapi.lookup_player(
                            fn + " " + ln.strip(".,"))
                        box['cs_catcher'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled caught stealing")
                if play["result"]["event"] == "Catcher Interference" and play["result"]["eventType"] == "catcher_interf":
                    box['errors-detail'].append(play)
                    desc = play["result"]["description"].split(" ")
                    byIndex = desc.index("by")
                    try:
                        # by [player]
                        fn = desc[byIndex + 1]
                        ln = desc[byIndex + 2]
                        player = statsapi.lookup_player(fn + " " + ln.strip(".,"))
                        box['errors-blame'].append(player[0]['fullName'])
                    except Exception as e:
                        print("unhandled fielding error")
                        box['errors-blame'].append("Unknown")
                if play["result"]["event"] == "Field Error" and play["result"]["eventType"] == "field_error":
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


def headToHeadGame(home, away, starterIdx):
    home_score = 0
    away_score = 0
    orderSlotHome = 1
    orderSlotAway = 1
    currHomePitcher = home['starters'][starterIdx]
    currAwayPitcher = away['starters'][starterIdx]
    home['burned-pitchers'] = [currHomePitcher]
    away['burned-pitchers'] = [currAwayPitcher]
    for i in range(1, 10):
        result = simOffensiveInning(away, orderSlotAway, i)
        orderSlotAway = result["orderSlot"]
        away_score += result["runs"]

        result = simOffensiveInning(home, orderSlotHome, i)
        orderSlotHome = result["orderSlot"]
        home_score += result["runs"]

        result = simDefensiveInning(home, currHomePitcher, i, home_score, away_score, True)
        currHomePitcher = result["currPitcher"]
        away_score += result["runs"]

        result = simDefensiveInning(away, currAwayPitcher, i, away_score, home_score, True)
        currAwayPitcher = result["currPitcher"]
        home_score += result["runs"]
        print("End %d, %s: %5.1f, %s: %5.1f\n" % (i, away['team-name'], away_score/2.0, home['team-name'], home_score/2.0))
    i=9

    while away_score + 1.0 >= home_score and home_score + 1.0 >= away_score: # Experimenting with needing to win by "two" runs or a whole run.
        i += 1
        result = simOffensiveInning(home, orderSlotHome, i)
        orderSlotHome = result["orderSlot"]
        home_score += result["runs"]

        result = simOffensiveInning(away, orderSlotAway, i)
        orderSlotAway = result["orderSlot"]
        away_score += result["runs"]
        print("Mid %d, %s: %5.1f, %s: %5.1f\n" % (i, away['team-name'], away_score / 2.0, home['team-name'], home_score / 2.0))

        result = simDefensiveInning(home, currHomePitcher, i, home_score, away_score, True)
        currHomePitcher = result["currPitcher"]
        away_score += result["runs"]

        result = simDefensiveInning(home, currHomePitcher, i, away_score, home_score, True)
        currAwayPitcher = result["currPitcher"]
        home_score += result["runs"]

        print("End %d, %s: %5.1f, %s: %5.1f\n" % (i, away['team-name'], away_score / 2.0, home['team-name'], home_score / 2.0))


def simDefensiveInning(team, currPitcher, inning, our_score, their_score, isHome):
    baseState = [0, 0, 0]
    runs = 0
    outs = 0
    while outs < 3:
        bullpenIdx = 0
        score_d = our_score - their_score - runs
        while len(team['pitching-results'][currPitcher]) < 1:
            currPitcher = decidePitchingChange(baseState, team, inning, bullpenIdx, score_d)
            team['burned-pitchers'].append(currPitcher)
            bullpenIdx += 1
        if inning >= 7:
            if inning >= 9 and team['closer'] not in team['burned-pitchers']:
                if (isHome and score_d <= team["closer-max-lead-home"] and score_d >= team["closer-min-lead-home"]) or (not isHome and score_d >= -1 * away["closer-max-lead-away"] and score_d <= -1 * away["closer-min-lead-away"]):
                    currPitcher = team['closer']
                    team['burned-pitchers'].append(currPitcher)
            elif team['fireman'] not in team['burned-pitchers'] and baseState[1] + baseState[2] > 0:
                if (isHome and score_d <= team["closer-max-lead-home"] and score_d >= team["closer-min-lead-home"]) or (not isHome and score_d >= -1 * away["closer-max-lead-away"] and score_d <= -1 * away["closer-min-lead-away"]):
                    currPitcher = team['fireman']
                    team['burned-pitchers'].append(currPitcher)

        outcome = team['pitching-results'][currPitcher].pop(0)
        print("(outs: " + str(outs) + ") " + currPitcher + " pitching: " + outcome)
        if (outcome == "k"):
            outs += 1
        if (outcome == "in_play_out"):
            outs += 1
            rng = random.uniform(0, 1)
            if (baseState[2] == 1 and outs < 3):
                if (rng > 1.0 - sacrificeFlyToHomeRatio):
                    print("sacrifice runner scores")
                    runs += 1
                    baseState[2] = 0
            # don't reroll, if we can't score the run home we won't advance to third
            if (baseState[1] == 1 and baseState[2] == 0 and outs < 3):
                if (rng > 1.0 - productiveOutToThirdRatio):
                    print("sacrifice runner moved to 3rd")
                    baseState[2] = 1
                    baseState[1] = 0
            if (baseState[0] == 1 and outs < 3):
                if (rng < doublePlayRatioOnOutsWhenRunnerOnFirst):
                    print("double play (6-4-3/4-6-3)")
                    outs += 1
                    baseState[0] = 0
                elif (baseState[1] == 0 and rng > 1.0 - sacrificeBuntRatio):
                    print("sacrifice runner moved to 2nd")
                    baseState[1] = 1
                    baseState[0] = 0
                elif (baseState[2] == 0 and rng > 1.0 - sacrificeBuntRatio):
                    print("sacrifice both runners advance")
                    baseState[2] = 1
                    baseState[1] = 1
                    baseState[0] = 0
        out_stealing = False
        if outcome.endswith("+cs"):
            out_stealing = True
            outcome = outcome[0:-3]
            print("Runner picked off by " + currPitcher)
        if (outcome == "4"):
            runs += 1 + baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 0]
        if (outcome == "3"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 1]
        if (outcome == "2"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 1, 0]
        if (outcome == "1"):
            runs += baseState[1] + baseState[2]
            baseState[2] = 0
            baseState[1] = 0
            if (baseState[0] == 1):
                rng = random.uniform(0, 1)
                if (rng > 1.0 - firstToThirdSingleRatio):
                    print("runner first to third")
                    baseState[2] = 1
                else:
                    baseState[1] = 1
            baseState[0] = 1
        if (outcome == "walk" or outcome == "hbp"):
            if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                runs += 1
            elif (baseState[0] == 1 and baseState[2] == 1):  # 13 loads it
                baseState[1] = 1
            elif (baseState[0] == 1 and baseState[1] == 1):  # 12 loads it
                baseState[2] = 1
            elif (baseState[1] == 1 and baseState[2] == 1):  # 23 loads it
                baseState[0] = 1
            elif (baseState[0] == 1):  # 1 pushed to second
                baseState[1] = 1
            else:  # first empty
                baseState[0] = 1
        if out_stealing:
            if outcome == 'walk' or outcome == 'hbp':
                outcome = 1
                baseState[int(outcome) - 1] = 0
                outs += 1
                print("Runner picked off by " + currPitcher)
    print(team["team-name"] + " conceded " + str(runs/2.0) + " runs")
    return {"currPitcher": currPitcher, "runs": runs}


def decidePitchingChange(baseState, team, inning, idx, scoreDiff):
    # todo long reliever
    return team['bullpen'][idx]


def offenseCalibrationOutput(team):
    histogram = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0]
    runs = []
    for i in range(1, 500):
        res = simOffensiveGame(team)
        histogram[res] += 1
        runs.append(res)
    print("mean: " + str(statistics.mean(runs)))
    print("median: " + str(statistics.median(runs)))
    print("mode: " + str(statistics.mode(runs)))
    print(histogram)

box_games = getWeeklyBox()
away = loadLineup("liverpool-ale-quaffers", box_games)
home = loadLineup("new-york-bankers", box_games)
#offenseCalibrationOutput(away)


headToHeadGame(home, away, 0)
