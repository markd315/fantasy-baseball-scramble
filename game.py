import statistics
import simulationConfig as config
import inning


def headToHeadGame(home, away, starterIdx, awayStarterIdx=None):
    if awayStarterIdx == None:
        awayStarterIdx = starterIdx
    long_output = ""
    home_score = 0
    away_score = 0
    orderSlotHome = 1
    orderSlotAway = 1
    currHomePitcher = home['starters'][starterIdx]
    currAwayPitcher = away['starters'][awayStarterIdx]
    home['burned-pitchers'] = [currHomePitcher]
    away['burned-pitchers'] = [currAwayPitcher]
    if len(home['pitching-results'][currHomePitcher]) == 0:
        if len(home['pitching-results'][home['starters'][4]]) != 0:
            long_output += "The scheduled starter " + currHomePitcher + " was unavailable for this game. " + home['starters'][4] + " takes the mound.\n"
            currHomePitcher = home['starters'][4]
            home['burned-pitchers'].append(currHomePitcher)
        else:
            long_output += "The scheduled and backup starters " + currHomePitcher + ", " + home['starters'][4] + " were both unavailable for this game. " + " Bullpen day.\n"
            home['burned-pitchers'].append(home['starters'][4])
            currHomePitcher = home['bullpen'][0]
            home['burned-pitchers'].append(currHomePitcher)
    if len(away['pitching-results'][currAwayPitcher]) == 0:
        if len(away['pitching-results'][away['starters'][4]]) > 0:
            long_output += "The scheduled starter " + currAwayPitcher + " was unavailable for this game. " + away['starters'][4] + " takes the mound.\n"
            currAwayPitcher = away['starters'][4]
            away['burned-pitchers'].append(currAwayPitcher)
        else:
            long_output += "The scheduled and backup starters " + currAwayPitcher + ", " + away['starters'][4] + " were both unavailable for this game. " + " Bullpen day.\n"
            away['burned-pitchers'].append(away['starters'][4])
            currAwayPitcher = away['bullpen'][0]
            away['burned-pitchers'].append(currAwayPitcher)
    line_score = [["Inning / Total"],
                  [away['team-name']],
                  [home['team-name']]
                  ]  # header, aw_off, hm_off, aw_def, aw_def
    away_hits, home_hits, away_errors, home_errors = 0, 0, 0, 0
    for i in range(1, 10):
        line_score[0].append(str(i))
        result = inning.simBlendedInning(away, home, orderSlotAway, currHomePitcher, i, away_score, home_score, True, starterIdx)
        orderSlotAway, currHomePitcher = result["orderSlot"], result['currPitcher']
        long_output += result["out"]
        line_score[1].append(result["runs"])
        away_score += result["runs"]
        away_hits += result['hits']
        home_errors += result['errors']

        if i < 9 or home_score <= away_score:
            result = inning.simBlendedInning(home, away, orderSlotHome, currAwayPitcher, i, away_score, home_score, False, starterIdx)
            orderSlotHome, currAwayPitcher = result["orderSlot"], result['currPitcher']
            long_output += result["out"]
            line_score[2].append(result["runs"])
            home_score += result["runs"]
            home_hits += result['hits']
            away_errors += result['errors']
        else:
            line_score[2].append("-")
        long_output += "End %d, %s: %d, %s: %d\n" % (i, away['team-name'], away_score, home['team-name'], home_score) + "\n"
    i=9
    while away_score == home_score:
        i += 1
        line_score[0].append(str(i))
        result = inning.simBlendedInning(away, home, orderSlotAway, currHomePitcher, i, away_score, home_score, True, starterIdx)
        orderSlotAway, currPitcher = result["orderSlot"], result['currPitcher']
        long_output += result["out"]
        line_score[1].append(result["runs"])
        away_score += result["runs"]
        away_hits += result['hits']
        home_errors += result['errors']

        if home_score > away_score:
            long_output += "Skipping the bottom of the inning: the ballgame is over!"
        else:
            long_output += "Mid %d, %s: %d, %s: %d\n" % (i, away['team-name'], away_score, home['team-name'], home_score)

        result = inning.simBlendedInning(home, away, orderSlotHome, currAwayPitcher, i, away_score, home_score, False, starterIdx)
        orderSlotHome, currPitcher = result["orderSlot"], result['currPitcher']
        long_output += result["out"]
        line_score[2].append(result["runs"])
        home_score += result["runs"]
        home_hits += result['hits']
        away_errors += result['errors']

        long_output += "End %d, %s: %d, %s: %d\n" % (i, away['team-name'], away_score, home['team-name'], home_score) + "\n"
    line_score[0].extend(["~R~", "H", "E"])
    hits = [away_hits, home_hits]
    errs = [away_errors, home_errors]
    for idx, arr in enumerate(line_score[1:]):
        sum=0
        for num in arr[1:]:
            try:
                sum += int(num)
            except BaseException:
                pass
        line_score[idx + 1].append(str(sum))
        line_score[idx+1].append(str(hits[idx]))
        line_score[idx + 1].append(str(errs[idx]))
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


def simulateAndLogGame(home, away, starter_idx, league, week, away_starter_idx=None):
    winner, line_score, long_output = headToHeadGame(home, away, starter_idx, awayStarterIdx=away_starter_idx)
    shortname = away['abbv'] + "@" + home['abbv'] + "-wk" + str(week) + "-" + str(starter_idx + 1)
    with open("leagues/" + league + "/debug_output/" + shortname, "w") as f:
        f.write(long_output)
        f.close()
    print(winner + " win!")
    return winner, line_score
