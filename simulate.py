
from datetime import datetime
from datetime import timedelta
import random
import statsapi
import json

trackedBattingStats = ['ab', 'h', 'doubles', 'triples', 'hr', 'sb', 'bb', 'k']


def getWeeklyBox():
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    current_time = yesterday.strftime("%Y-%m-%d")
    begin = yesterday - timedelta(days=7)
    st_time = begin.strftime("%Y-%m-%d")
    games = statsapi.schedule(start_date=st_time, end_date=current_time,
                              team="",
                              opponent="", sportId=1, game_id=None)
    box_games = []

    for game in games:
        try:
            with open("cached-box-scores/" + str(game['game_id']) + ".json",
                      "r") as json_file:
                box_games.append(json.load(json_file))
        except FileNotFoundError:
            box = statsapi.boxscore_data(game['game_id'])
            f = open("cached-box-scores/" + str(game['game_id']) + ".json", "w")
            f.write(json.dumps(box))
            f.close()
            box_games.append(box)
    return box_games


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
        'sb': 0, 'bb': 0, 'k': 0
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
    return weekly_totals


innings = 9

def randomWalkOfWeeklyTotals(weekly_totals):
    outcomes = ['k', 'in_play_out', 'walk', '1', '2', '3', '4']
    plateapps = []
    for outcome in outcomes:
        for i in range(0, weekly_totals[outcome]):
            plateapps.append(outcome)
    random.shuffle(plateapps)
    for i in range(0, weekly_totals['sb']):
        valid = False
        while not valid:
            idx = random.randint(0, len(plateapps) -1)
            res = plateapps[idx]
            on_base_stealable = ['walk', '1', '2']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+sb'
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

# simnning stealbase and simoffensivegame based on https://github.com/markd315/baseball-softball-lineup-tester/blob/master/lineup.py
def simInning(team, orderSlot):
    lineup = team['batting-results']
    baseState = [0, 0, 0]
    runs = 0
    outs = 0
    while outs < 3:
        # TODO caught stealing
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
                    rng = random.uniform(0, 1)
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
        if outcome.endswith("+sb"):
            stolen = True
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
            baseState[1] = baseState[0]  # first to second
            baseState[2] = 0
            baseState[0] = 1
        if (outcome == "walk"):
            if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                runs += 1
            elif (baseState[0] == 1 and baseState[2] == 1):  # 13
                baseState[1] = 1
            elif (baseState[0] == 1 and baseState[1] == 1):  # 12
                baseState[2] = 1
            elif (baseState[1] == 1 and baseState[2] == 1):  # 23
                baseState[0] = 1
            elif (baseState[1] == 1):  # 1
                baseState[1] = 1
            else:  # first empty
                baseState[0] = 1
        if stolen:
            if outcome == 'walk':
                outcome = 1
            chk_empty_base = int(outcome)
            if baseState[chk_empty_base] == 0:
                baseState[chk_empty_base] = 1
                baseState[chk_empty_base - 1] = 0
                print(player_nm + " stole a base")
            else:
                print(player_nm + " had a good jump but the next base was occupied")
        orderSlot += 1
        if (orderSlot > 9):
            orderSlot -= 9
    print("Scored " + str(runs))
    return {"orderSlot": orderSlot, "runs": runs}


def simOffensiveGame(team):
    runs = 0
    orderSlot = 1  # need scoped to game method
    for inn in range(0, innings):
        result = simInning(team, orderSlot)
        orderSlot = result["orderSlot"]
        runs += result["runs"]
    print("Game over, run count: " + str(runs))
    return runs


def loadLineup(team_name, box_games):
    with open("team-lineups/" + team_name + ".json", "r") as json_file:
        team = json.load(json_file)
        team['batting-results'] = []
        team['batting-result-curr-idx'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for idx, player in enumerate(team['batting-order']):
            player = statsapi.lookup_player(player)
            totals = filterPlayerPas(box_games, player[0])
            pas = randomWalkOfWeeklyTotals(totals)
            team['batting-results'].append(pas)
        return team

# player = statsapi.lookup_player('Shohei Ohtani')
box_games = getWeeklyBox()
lineup = loadLineup("liverpool-ale-quaffers", box_games)
simOffensiveGame(lineup)