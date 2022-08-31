import simulationConfig as config

leagueWeek = config.leagueWeek
maxRegularSeasonWeeks = config.maxRegularSeasonWeeks  # TODO this isn't a true cap yet, we will always play at least one full round robin.

import numpy as np

import os
import random
from datetime import datetime
from pathlib import Path

from tabulate import tabulate

import game
import mlb_api
from itertools import permutations
import pandas as pd


box_games = mlb_api.getWeeklyBox(
    datetime.now()
)


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


def add_line_score_to_standings(home, away, line_score):
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
        add_line_score_to_standings(home, away, line_score)
        count[winner] += 1
        line_scores += tabulate(line_score) + "\n\n"
    shortname = away['abbv'] + "@" + home['abbv'] + "wk" + str(week)
    with open("leagues/" + league + "/debug_output/" + shortname + ".line", "w") as f:
        f.write(line_scores)
        f.close()
    if (count[h] > count[a]):
        outcome = h + " win the series "
    elif (count[a] > count[h]):
        outcome = a + " win the series "
    else:
        outcome = h + " and " + a + " tie the series "
    print(outcome + str(count[h]) + " games to " + str(count[a]))


for league in os.listdir("leagues"):
    teams = []
    league = str(league)
    with open("leagues/" + league + "/League_note", "r") as league_note:
        out = league_note.read()
        if out.startswith("Drafting! Current pick order"):
            continue
    lineups = os.listdir("leagues/" + league + "/team-lineups")
    for file in os.listdir("leagues/" + league + "/team-lineups"):
        if str(file).endswith(".json") and not str(file).startswith("next_"):
            team_nm = str(file)[:-5]
            teams.append(mlb_api.loadLineup(league, team_nm, box_games, leagueWeek))
    if len(teams) % 2 != 0:
        teams.append({'team-name': 'Bye'})
    perms = [n for n in permutations(teams, 2)]
    if len(teams) <= 4 and maxRegularSeasonWeeks > 4 * (len(teams) - 1):
        perms.extend(perms)
        if len(teams) <= 2 and maxRegularSeasonWeeks > 8 * (len(teams) - 1):
            perms.extend(perms)
    print("League " + league + " week " + str(leagueWeek) + ":")
    targetWeeks = 0
    for perm in perms:
        if(teams[0]['team-name'] == perm[0]['team-name'] or teams[0]['team-name'] == perm[1]['team-name']):
            targetWeeks += 1
    weeks = []
    for idx in range(0, targetWeeks):
        weeks.append([])
    for perm in perms:
        for idx, week in enumerate(weeks):
            teamAlreadyPlaying = False
            for gm in week:
                if gm[0] in perm or gm[1] in perm:
                    teamAlreadyPlaying = True
                    break
            if not teamAlreadyPlaying:
                week.append(perm)
                gamePlaced = True
                break
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
    if leagueWeek < len(weeks) -1:
        week = weeks[leagueWeek]
    else:
        continue
    for gm in week:
        print(gm[1]['team-name'] + "@" + gm[0]['team-name'])
        if gm[0]['team-name'] != 'Bye' and gm[1]['team-name'] != 'Bye':
            multiGameSeries(gm[0], gm[1], 4, league, leagueWeek)
    commitNewRosters(league)

# game.offenseCalibrationOutput(away)
print("fin")
