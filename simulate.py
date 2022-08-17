from datetime import datetime
import game
import lineup_api

box_games = lineup_api.getWeeklyBox(
    datetime(year=2022, month=8, day=16, hour=20, minute=0, second=0)
)
away = lineup_api.loadLineup("liverpool-ale-quaffers", box_games)
home = lineup_api.loadLineup("new-york-bankers", box_games)
#game.offenseCalibrationOutput(away)


winner, line_score = game.headToHeadGame(home, away, 0)
print(winner)
print(line_score)
print("fin")
