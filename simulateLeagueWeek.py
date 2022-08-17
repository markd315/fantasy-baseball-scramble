from datetime import datetime
import game
import lineup_api

box_games = lineup_api.getWeeklyBox(
    datetime(year=2022, month=8, day=16, hour=20, minute=0, second=0)
)

away = lineup_api.loadLineup("liverpool-ale-quaffers", box_games)
home = lineup_api.loadLineup("new-york-bankers", box_games)
away2 = lineup_api.loadLineup("denver-stoners", box_games)
home2 = lineup_api.loadLineup("canada-hosers", box_games)


# game.offenseCalibrationOutput(away)


def multiGameSeries(home, away, games):
    h = home['team-name']
    a = away['team-name']
    count = {h: 0, a: 0}
    for starter in range(0, games):
        winner = game.simulateAndLogGame(home, away, starter)
        count[winner] += 1

    if (count[h] > count[a]):
        outcome = h + " win the series "
    elif (count[a] > count[h]):
        outcome = a + " win the series "
    else:
        outcome = h + " and " + a + " tie the series "
    print(outcome + str(count[h]) + " games to " + str(count[a]))


multiGameSeries(home, away, 4)
multiGameSeries(home2, away2, 3)
print("fin")
