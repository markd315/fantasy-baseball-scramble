import simulationConfig
import simulationConfig as config

leagueWeek = config.leagueWeek
maxRegularSeasonWeeks = config.maxRegularSeasonWeeks  # TODO this isn't a true cap yet, we will always play at least one full round robin.

import numpy as np

import os
import random
from pathlib import Path

from tabulate import tabulate

import game
import mlb_api
from itertools import permutations
import pandas as pd

def commitNewRosters(league):
    pathpre = "leagues/" + league + "/team-lineups/"
    for p in Path(pathpre).glob('next_*'):
        lines = []
        with open(pathpre + p.name, 'r') as file_read:
            lines = file_read.readlines()
            file_read.close()
        committed_path = p.name.replace("next_", "")
        with open(pathpre + committed_path, 'w') as file_write:
            file_write.writelines(lines)
            file_write.close()


def add_line_score_to_standings(league, home, away, line_score):
    rhe = []
    for line in line_score[1:]:
        toAdd = []
        for elem in line[-3:]:
            toAdd.append(int(elem))
        rhe.append(toAdd)
    # reading the csv file
    df = pd.read_csv("leagues/" + league + "/standings.csv")
    home_row = int(np.where(df["Team"] == home['team-name'])[0].min())
    away_row = int(np.where(df["Team"] == away['team-name'])[0].min())
    if rhe[0][0] > rhe[1][0]:  # away win
        df.loc[away_row, 'W'] += 1
        df.loc[home_row, 'L'] += 1
    else:
        df.loc[home_row, 'W'] += 1
        df.loc[away_row, 'L'] += 1
    # writing into the file
    rd_away = rhe[0][0] - rhe[1][0]
    df.loc[home_row, 'RD'] -= rd_away
    df.loc[away_row, 'RD'] += rd_away
    df.loc[home_row, 'RA'] += rhe[0][0]
    df.loc[away_row, 'RA'] += rhe[1][0]
    iter = [away_row, home_row]
    for idx, rows in enumerate(iter):
        df.loc[iter[idx], 'R'] += rhe[idx][0]
        df.loc[iter[idx], 'H'] += rhe[idx][1]
        df.loc[iter[idx], 'E'] += rhe[idx][2]
    df = df.sort_values(ascending=False, by=['W', 'RD', 'R', 'H'])
    df.to_csv("leagues/" + league + "/standings.csv", index=False)
    with open("leagues/" + league + "/Standings", "w") as file:
        file.write(tabulate(df, headers='keys', showindex=False))

def writeLineScores(league, line_scores, home, away, week):
    shortname = away['abbv'] + "@" + home['abbv'] + "wk" + str(week)
    with open("leagues/" + league + "/debug_output/" + shortname + ".line", "w") as f:
        f.write(line_scores)
        f.close()


def multiGameSeries(home, away, games, league, week):
    h = home['team-name']
    a = away['team-name']
    count = {h: 0, a: 0}
    for team in [home, away]:
        for error in team['errors']:
            team['errors'][error]['game'] = random.randint(0, games-1)
    line_scores = ""
    for starter in range(0, games):
        winner, line_score = game.simulateAndLogGame(home, away, starter, league, week)
        add_line_score_to_standings(league, home, away, line_score)
        count[winner] += 1
        line_scores += tabulate(line_score) + "\n\n"
    writeLineScores(league, line_scores, home, away, week)
    if (count[h] > count[a]):
        outcome = h + " win the series "
    elif (count[a] > count[h]):
        outcome = a + " win the series "
    else:
        outcome = h + " and " + a + " tie the series "
    print(outcome + str(count[h]) + " games to " + str(count[a]))


def extendScheduleToDesiredLength(weeks, maxRegularSeasonWeeks):
    # first convert tuple to list screw tuples
    for week in weeks:
        for idx, game in enumerate(week):
            week[idx] = list(game)
    finalWeeks = []
    for week in weeks:
        newWk = []
        for gm in week:
            newWk.append(gm.copy())
        finalWeeks.append(newWk)
    remainingLen = maxRegularSeasonWeeks - len(weeks)
    while remainingLen >= len(weeks):
        # flip all the home and away
        flippedWeeks = []
        for idx, week in enumerate(weeks):
            flippedWeeks.append([])
            for idy, gm in enumerate(week):
                tmp = gm[0]
                gm[0] = gm[1]
                gm[1] = tmp
                flippedWeeks[len(flippedWeeks) - 1].append(gm)
        for week in weeks:
            newWk = []
            for gm in week:
                newWk.append(gm.copy())
            finalWeeks.append(newWk)
        remainingLen -= len(weeks)
    return finalWeeks


def getWeeklySchedule(league, box_games):
    teams = []
    for file in os.listdir("leagues/" + league + "/team-lineups"):
        if str(file).endswith(".json") and not str(file).startswith("next_"):
            team_nm = str(file)[:-5]
            teams.append(mlb_api.loadLineup(league, team_nm, box_games, leagueWeek))
    if len(teams) % 2 != 0:
        if len(teams) == 5: #  Stripe it so there is 1 4-game series and 3 2-game series each week: everyone plays!
            weeks = [
                ['2@1', '543'],
                ['4@3', '152'],
                ['1@5', '324'],
                ['3@2', '415'],
                ['5@3', '214'],
                ['4@5', '231'],
                ['3@1', '542'],
                ['2@4', '153'],
                ['1@4', '325'],
                ['5@2', '431'],
            ]
            retWeeks = []
            for week in weeks:
                tri_matchup = week.pop(1)
                week.append(tri_matchup[0] + '@' + tri_matchup[1])
                week.append(tri_matchup[1] + '@' + tri_matchup[2])
                week.append(tri_matchup[0] + '@' + tri_matchup[2])
                retWeeks.append([
                    [teams[int(week[0][0]) - 1], teams[int(week[0][2]) - 1]],
                    [teams[int(week[1][0]) - 1], teams[int(week[1][2]) - 1]],
                    [teams[int(week[2][0]) - 1], teams[int(week[2][2]) - 1]],
                    [teams[int(week[3][0]) - 1], teams[int(week[3][2]) - 1]],
                ])
            return retWeeks
        else:
            teams.append({'team-name': 'Bye'})
    perms = [n for n in permutations(teams, 2)]
    if len(teams) <= 4 and maxRegularSeasonWeeks > 4 * (len(teams) - 1):
        perms.extend(perms)
        if len(teams) <= 2 and maxRegularSeasonWeeks > 8 * (len(teams) - 1):
            perms.extend(perms)
    print("League " + league + " week " + str(leagueWeek) + ":")
    """ Create a schedule for the players in the list and return it https://gist.github.com/ih84ds/be485a92f334c293ce4f1c84bfba54c9"""
    weeks = []
    if len(teams) % 2 == 1: teams = teams + [None]
    # manipulate map (array of indexes for list) instead of list itself
    # this takes advantage of even/odd indexes to determine home vs. away
    n = len(teams)
    map = list(range(n))
    mid = n // 2
    for i in range(n - 1):
        l1 = map[:mid]
        l2 = map[mid:]
        l2.reverse()
        round = []
        for j in range(mid):
            t1 = teams[l1[j]]
            t2 = teams[l2[j]]
            if j == 0 and i % 2 == 1:
                # flip the first match only, every other round
                # (this is because the first match always involves the last player in the list)
                round.append((t2, t1))
            else:
                round.append((t1, t2))
        weeks.append(round)
        # rotate list by n/2, leaving last element at the end
        map = map[mid:-1] + map[:mid] + map[-1:]
    weeks = extendScheduleToDesiredLength(weeks, maxRegularSeasonWeeks)
    try:
        with open("leagues/" + league + "/scheduleSeed.txt", 'r') as seedFile:
            seed = seedFile.readlines()[0]
            random.Random(int(seed)).shuffle(weeks)
            seedFile.close()
    except FileNotFoundError:
        rng = random.randint(0, 9999999)
        random.Random(rng).shuffle(weeks)
        with open("leagues/" + league + "/scheduleSeed.txt", 'w') as seedFile:
            seedFile.write(str(rng))
            seedFile.close()
    weeks = weeks[0:simulationConfig.maxRegularSeasonWeeks]
    return weeks
