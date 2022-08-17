import statistics
from datetime import datetime

from tabulate import tabulate

import config
import inning


def headToHeadGame(home, away, starterIdx):
    long_output = ""
    home_score = 0
    away_score = 0
    orderSlotHome = 1
    orderSlotAway = 1
    currHomePitcher = home['starters'][starterIdx]
    currAwayPitcher = away['starters'][starterIdx]
    home['burned-pitchers'] = [currHomePitcher]
    away['burned-pitchers'] = [currAwayPitcher]
    line_score = [["Inning / Total"],
                  [away['team-name'] + ' Batting'],
                  [home['team-name'] + ' Batting'],
                  ['vs. ' + home['team-name'] + ' pitchers'],
                  ['vs. ' + away['team-name'] + ' pitchers'],
                  [away['team-name']],
                  [home['team-name']]
                  ] # header, aw_off, hm_off, aw_def, aw_def
    for i in range(1, 10):
        line_score[0].append(str(i))
        result = inning.simOffensiveInning(away, orderSlotAway, i)
        orderSlotAway, score = result["orderSlot"], result["runs"]
        long_output += result["out"]
        line_score[1].append(score)
        away_score += score

        result = inning.simOffensiveInning(home, orderSlotHome, i)
        orderSlotHome, score = result["orderSlot"], result["runs"]
        long_output += result["out"]
        line_score[2].append(score)
        home_score += score

        result = inning.simDefensiveInning(home, currHomePitcher, i, home_score, away_score, True)
        currHomePitcher, score = result["currPitcher"], result["runs"]
        long_output += result["out"]
        line_score[3].append(score)
        away_score += score

        result = inning.simDefensiveInning(away, currAwayPitcher, i, away_score, home_score, True)
        currAwayPitcher, score = result["currPitcher"], result["runs"]
        long_output += result["out"]
        line_score[4].append(score)
        home_score += score
        long_output += "End %d, %s: %5.1f, %s: %5.1f\n" % (i, away['team-name'], away_score/2.0, home['team-name'], home_score/2.0) + "\n"
        line_score[5].append(str(float( line_score[1][i] + line_score[3][i] ) / 2.0))
        line_score[6].append(str(float( line_score[2][i] + line_score[4][i] ) / 2.0))
    i=9

    while away_score + 1.0 >= home_score and home_score + 1.0 >= away_score: # Experimenting with needing to win by "two" runs or a whole run.
        i += 1
        line_score[0].append(str(i))
        result = inning.simOffensiveInning(away, orderSlotAway, i)
        orderSlotAway, score = result["orderSlot"], result["runs"]
        long_output += result["out"]
        line_score[1].append(score)
        away_score += score

        result = inning.simOffensiveInning(home, orderSlotHome, i)
        orderSlotHome, score = result["orderSlot"], result["runs"]
        long_output += result["out"]
        line_score[2].append(score)
        home_score += score

        long_output += "Mid %d, %s: %5.1f, %s: %5.1f\n" % (i, away['team-name'], away_score/2.0, home['team-name'], home_score/2.0)

        result = inning.simDefensiveInning(home, currHomePitcher, i, home_score, away_score, True)
        currHomePitcher, score = result["currPitcher"], result["runs"]
        long_output += result["out"]
        line_score[3].append(score)
        away_score += score
        if home_score > away_score + 0.5:
            long_output+= "Skipping the bottom of the inning: the ballgame is over!"

        result = inning.simDefensiveInning(away, currAwayPitcher, i, away_score, home_score, True)
        currAwayPitcher, score = result["currPitcher"], result["runs"]
        long_output += result["out"]
        line_score[4].append(score)
        home_score += score

        long_output += "End %d, %s: %5.1f, %s: %5.1f\n" % (i, away['team-name'], away_score/2.0, home['team-name'], home_score/2.0) + "\n"
        line_score[5].append( str(float(line_score[1][i] + line_score[3][i]) / 2.0) )
        line_score[6].append( str(float(line_score[2][i] + line_score[4][i]) / 2.0) )
    line_score[0].append("T")
    for idx, arr in enumerate(line_score[1:5]):
        line_score[idx+1].append(sum(arr[1:]))
    line_score[5].append(str(away_score/2.0))
    line_score[6].append(str(home_score/2.0))
    winner = home['team-name'] if home_score > away_score else away['team-name']
    return winner, line_score, long_output


def simOffensiveGame(team):
    runs = 0
    orderSlot = 1  # need scoped to game method
    for inn in range(0, config.innings):
        result = inning.simOffensiveInning(team, orderSlot, inn)
        orderSlot = result["orderSlot"]
        runs += result["runs"]
    print("Game over, run count: " + str(runs))
    return runs

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


def simulateAndLogGame(home, away, starter_idx):
    runtime = datetime.now()
    runtime = runtime.strftime("%m-%d")
    winner, line_score, long_output = headToHeadGame(home, away, starter_idx)
    shortname = runtime + "-" + away['abbv'] + "@" + home['abbv'] + "-" + str(starter_idx + 1)
    with open("line_output/" + shortname, "w") as f:
        f.write(tabulate(line_score))
        f.close()
    with open("debug_output/" + shortname, "w") as f:
        f.write(long_output)
        f.close()
    print(winner + " win!")
    return winner
