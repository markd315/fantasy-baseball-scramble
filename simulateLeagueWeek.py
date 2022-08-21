import os
import random
from datetime import datetime

from tabulate import tabulate

import game
import lineup_api
from itertools import permutations


box_games = lineup_api.getWeeklyBox(
    datetime(year=2022, month=8, day=16, hour=20, minute=0, second=0)
)

leagueWeek = 0


def multiGameSeries(home, away, games, league):
    h = home['team-name']
    a = away['team-name']
    count = {h: 0, a: 0}
    for team in [home, away]:
        for error in team['errors']:
            team['errors'][error]['game'] = random.randint(0, games-1)
    line_scores = ""
    for starter in range(0, games):
        winner, line_score = game.simulateAndLogGame(home, away, starter, league)
        count[winner] += 1
        line_scores += tabulate(line_score) + "\n\n"
    runtime = datetime.now().strftime("%m-%d")
    shortname = runtime + "-" + away['abbv'] + "@" + home['abbv']
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
    lineups = os.listdir("leagues/" + league + "/team-lineups")
    for file in os.listdir("leagues/" + league + "/team-lineups"):
        if str(file).endswith(".json"):
            team_nm = str(file)[:-5]
            teams.append(lineup_api.loadLineup(league, team_nm, box_games, leagueWeek))
    if len(teams) % 2 != 0:
        teams.append({'team-name': 'Bye'})
    perms = [n for n in permutations(teams, 2)]
    if len(teams) <= 4:
        perms.extend(perms)
        if len(teams) <= 2:
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
    week = weeks[leagueWeek]
    for gm in week:
        print(gm[1]['team-name'] + "@" + gm[0]['team-name'])
        if gm[0]['team-name'] != 'Bye' and gm[1]['team-name'] != 'Bye':
            multiGameSeries(gm[0], gm[1], 4, league)

# game.offenseCalibrationOutput(away)
print("fin")
