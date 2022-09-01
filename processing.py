import random
from math import exp

import simulationConfig
import simulationConfig as config

def randomWalkOfWeeklyTotals(weekly_totals):
    outcomes = ['k', 'in_play_out', 'walk', 'hbp', 'single', 'double', 'triple', 'home run']
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
            on_base_stealable = ['walk', 'hbp', 'single', 'double']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+sb'
    for i in range(0, weekly_totals['cs']):
        valid = False
        while not valid:
            idx = random.randint(0, len(plateapps) -1)
            res = plateapps[idx]
            on_base_stealable = ['walk', 'hbp', 'single', 'double']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+cs'
    return plateapps


def trueRandomizePitchingTotals(weekly_totals):
    outcomes = ['k', 'in_play_out', 'walk', 'hbp', 'single', 'double', 'triple', 'home run']
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
            on_base_stealable = ['walk', 'single', 'double']
            if res in on_base_stealable:
                valid = True
                plateapps[idx] += '+wp'
    return plateapps


def filterPlayerPas(box_games, player):
    box_nm = player['boxscoreName']
    game_lines = []
    for box in box_games:
        if box['away']['team']['id'] == player['currentTeam']:
            for batter in box['awayBatters']:
                if box_nm in batter['namefield']:
                    game_lines.append(batter)
        if box['home']['team']['id'] == player['currentTeam']:
            for batter in box['homeBatters']:
                if box_nm in batter['namefield']:
                    game_lines.append(batter)
    weekly_totals = {
        'ab': 0, 'h': 0, 'doubles': 0, 'triples': 0, 'hr': 0,
        'sb': 0, 'cs': 0, 'bb': 0, 'k': 0, 'e': 0, 'hbp': 0
    }
    for game in game_lines:
        for attribute in game:
            if attribute in config.trackedBattingStats:
                weekly_totals[attribute] += int(game[attribute])
    weekly_totals['double'] = weekly_totals['doubles']
    weekly_totals['triple'] = weekly_totals['triples']
    weekly_totals['home run'] = weekly_totals['hr']
    weekly_totals['single'] = weekly_totals['h'] - weekly_totals['double'] - weekly_totals['triple'] - weekly_totals['home run']
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
    box_nm = player['boxscoreName']
    game_lines = []
    for box in box_games:
        if box['away']['team']['id'] == player['currentTeam']:
            for pitcher in box['awayPitchers']:
                if box_nm in pitcher['namefield']:
                    game_lines.append(pitcher)
        if box['home']['team']['id'] == player['currentTeam']:
            for pitcher in box['homePitchers']:
                if box_nm in pitcher['namefield']:
                    game_lines.append(pitcher)
    weekly_totals = {
        'ip': 0.0, 'h': 0, 'bb': 0, 'k': 0, 'hr': 0, 'wp': 0, 'e': 0, 'hbp': 0
    }
    for game in game_lines:
        for attribute in game:
            if attribute in config.trackedPitchingStats:
                weekly_totals[attribute] += float(game[attribute])
    ipart = int(weekly_totals['ip'])
    fpart = (weekly_totals['ip'] - int(weekly_totals['ip'])) * 10.0
    weekly_totals['out'] = int(fpart + ipart*3.0)
    hits_in_the_park = int(weekly_totals['h'] - weekly_totals['hr'])
    weekly_totals['single'] = 0
    weekly_totals['double'] = 0
    weekly_totals['triple'] = 0
    for i in range(0,hits_in_the_park):
        rng = random.uniform(0, 1)
        if rng < config.hitRatios[0]:
            weekly_totals['single'] += 1
        elif rng < config.hitRatios[1] + config.hitRatios[0]:
            weekly_totals['double'] += 1
        else:
            weekly_totals['triple'] += 1
    weekly_totals['ab'] = int(weekly_totals['h'] + weekly_totals['out'])
    weekly_totals['home run'] = int(weekly_totals['hr'])
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


def getOrderliness(n):
    #return 0.0205561 * exp(-0.150123 * float(n)) # Calculated values based on non-baseball array testing.
    return simulationConfig.fatigue * exp(-0.150123 * float(n)) #  Based on having a 5% OPS increase across a typical scramble of a 5-day pitching window (min 5 PA)


def fatigueBasedRandomizePitching(totals):
    pas = []
    totals['more_outs'] = 2 / 3 * totals['in_play_out']
    totals['in_play_out'] -= totals['more_outs']
    for outcome in ["k", "in_play_out", "bb", "more_outs", "single", "triple", "double", "home run"]:
        for _ in range(0, int(totals[outcome])):
            if outcome == 'more_outs':
                pas.append("in_play_out")
            else:
                pas.append(outcome)
    orderliness = getOrderliness(len(pas))
    pasOrder = range(len(pas))
    pasOrder = sorted(pasOrder, key=lambda i: random.gauss(i * orderliness, 1))
    pasFinal = []
    for pa in pasOrder:
        pasFinal.append(pas[pa])
    return pasFinal
