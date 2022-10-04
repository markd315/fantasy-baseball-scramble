from tabulate import tabulate

import game
import simulationConfig as config

leagueWeek = config.leagueWeek
maxRegularSeasonWeeks = config.maxRegularSeasonWeeks  # TODO this isn't a true cap yet, we will always play at least one full round robin.
import os
from datetime import datetime
import mlb_api
import scheduling


box_games = mlb_api.getWeeklyBox(
    datetime.now()
)


for league in os.listdir("leagues"):
    teams = []
    league = str(league)
    with open("leagues/" + league + "/League_note", "r") as league_note:
        out = league_note.read()
        if out.startswith("Drafting! Current pick order"):
            continue
    weeks = scheduling.getWeeklySchedule(league, box_games)
    lineups = os.listdir("leagues/" + league + "/team-lineups")
    if leagueWeek < len(weeks):
        week = weeks[leagueWeek]
    else:
        continue
    if len(weeks) == 10:
        scheduling.multiGameSeries(week[0][0], week[0][1], 4, league, leagueWeek)  # Striping games to follow.

        gm, line_scores = week[1], ""
        _, line_score = game.simulateAndLogGame(gm[0], gm[1], 0, league, leagueWeek)
        scheduling.add_line_score_to_standings(league, gm[0], gm[1], line_score)
        line_scores += tabulate(line_score) + "\n\n"
        _, line_score = game.simulateAndLogGame(gm[0], gm[1], 1, league, leagueWeek)
        scheduling.add_line_score_to_standings(league, gm[0], gm[1], line_score)
        line_scores += tabulate(line_score) + "\n\n"
        scheduling.writeLineScores(league, line_scores, gm[0], gm[1], leagueWeek)

        gm, line_scores = week[2], ""
        _, line_score = game.simulateAndLogGame(gm[0], gm[1], 0, league, leagueWeek, away_starter_idx=2)
        scheduling.add_line_score_to_standings(league, gm[0], gm[1], line_score)
        line_scores += tabulate(line_score) + "\n\n"
        _, line_score = game.simulateAndLogGame(gm[0], gm[1], 1, league, leagueWeek, away_starter_idx=3)
        scheduling.add_line_score_to_standings(league, gm[0], gm[1], line_score)
        line_scores += tabulate(line_score) + "\n\n"
        scheduling.writeLineScores(league, line_scores, gm[0], gm[1], leagueWeek)

        gm, line_scores = week[3], ""
        _, line_score = game.simulateAndLogGame(gm[0], gm[1], 2, league, leagueWeek)
        scheduling.add_line_score_to_standings(league, gm[0], gm[1], line_score)
        line_scores += tabulate(line_score) + "\n\n"
        _, line_score = game.simulateAndLogGame(gm[0], gm[1], 3, league, leagueWeek)
        scheduling.add_line_score_to_standings(league, gm[0], gm[1], line_score)
        line_scores += tabulate(line_score) + "\n\n"
        scheduling.writeLineScores(league, line_scores, gm[0], gm[1], leagueWeek)

        scheduling.commitNewRosters(league)
    else:
        for gm in week:
            print(gm[1]['team-name'] + "@" + gm[0]['team-name'])
            if gm[0]['team-name'] != 'Bye' and gm[1]['team-name'] != 'Bye':
                scheduling.multiGameSeries(gm[0], gm[1], 4, league, leagueWeek)
        scheduling.commitNewRosters(league)

# game.offenseCalibrationOutput(away)
print("fin")
