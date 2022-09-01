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
    lineups = os.listdir("leagues/" + league + "/team-lineups")
    weeks = scheduling.getWeeklySchedule(league, box_games)
    if leagueWeek < len(weeks) - 1:
        week = weeks[leagueWeek]
    else:
        continue
    for gm in week:
        print(gm[1]['team-name'] + "@" + gm[0]['team-name'])
        if gm[0]['team-name'] != 'Bye' and gm[1]['team-name'] != 'Bye':
            scheduling.multiGameSeries(gm[0], gm[1], 4, league, leagueWeek)
    scheduling.commitNewRosters(league)

# game.offenseCalibrationOutput(away)
print("fin")
