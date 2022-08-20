import random

import config


def offensiveOutcome(team, orderSlot):
    res_idx = int(team['batting-result-curr-idx'][orderSlot - 1])
    batterResults = team['batting-results'][orderSlot - 1]
    if res_idx >= len(batterResults):
        res_idx = 0  # Come back around to the top of the PA's
    res = batterResults[res_idx]
    res_idx += 1
    team['batting-result-curr-idx'][orderSlot - 1] = res_idx
    return res


def parseHandednessData(arr, batter, pitcher):
    #fmt: [LL, LHPvsR, RHPvsL, RR]
    if 'LHP' in pitcher:
        if 'RHB' in batter:
            return arr[1]
        else:
            return arr[0]
    else:  # RHP
        if 'LHB' in batter:
            return arr[2]
        else:
            return arr[3]


def getCoinForMatchup(teamsInLeague, pitchingTeam, battingTeam, currPitcher, orderSlot):
    batter = battingTeam['batting-order'][orderSlot - 1]
    batter_hands = battingTeam['handedness'][batter]
    pitcher_hands = pitchingTeam['handedness'][currPitcher]
    if teamsInLeague > 11:  # calibrated for 16 teams
        batterCoinPercent = parseHandednessData([0.0, .742, .508, .461], batter_hands, pitcher_hands)
    elif teamsInLeague > 6:  # calibrated for 8 teams
        batterCoinPercent = parseHandednessData([.196, .644, .505, .476], batter_hands, pitcher_hands)
    else:  # calibrated for 4 teams
        batterCoinPercent = parseHandednessData([.274, .607, .503, .483], batter_hands, pitcher_hands)
    rng = random.uniform(0, 1)
    if rng < batterCoinPercent:
        return 'batter'
    return 'pitcher'


def simBlendedInning(battingTeam, pitchingTeam, orderSlot, currPitcher, inning,
                     pitcherScore, batterScore, pitcherHome):
    if inning > 9:
        baseState = [0, 1, 0]
    else:
        baseState = [0, 0, 0]
    runs = 0
    outs = 0
    logs = "\n"
    while outs < 3:
        coin = getCoinForMatchup(config.teamsInLeague, pitchingTeam, battingTeam, currPitcher, orderSlot)
        if coin == 'pitcher':
            team = pitchingTeam
            score_d = pitcherScore - batterScore - runs
            currPitcher, team, logs = decidePitchingChange(currPitcher, baseState, team, inning, score_d, pitcherHome, logs)
            outcome = team['pitching-results'][currPitcher].pop(0)
            # Discard a second outcome to compensate for "batter" at-bats
            team['pitching-results'][currPitcher].pop(0)
            logs += "(outs: " + str(outs) + ") " + currPitcher + " pitching: " + outcome + "\n"
            if (outcome == "k"):
                outs += 1
            if (outcome == "in_play_out"):
                outs += 1
                rng = random.uniform(0, 1)
                if (baseState[2] == 1 and outs < 3):
                    if (rng > 1.0 - config.sacrificeFlyToHomeRatio):
                        logs += "sacrifice runner scores\n"
                        runs += 1
                        baseState[2] = 0
                # don't reroll, if we can't score the run home we won't advance to third
                if (baseState[1] == 1 and baseState[2] == 0 and outs < 3):
                    if (rng > 1.0 - config.productiveOutToThirdRatio):
                        logs += "sacrifice runner moved to 3rd\n"
                        baseState[2] = 1
                        baseState[1] = 0
                if (baseState[0] == 1 and outs < 3):
                    if (rng < config.doublePlayRatioOnOutsWhenRunnerOnFirst):
                        logs += "double play (6-4-3/4-6-3)\n"
                        outs += 1
                        baseState[0] = 0
                    elif (baseState[
                              1] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                        logs += "sacrifice runner moved to 2nd\n"
                        baseState[1] = 1
                        baseState[0] = 0
                    elif (baseState[
                              2] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                        logs += "sacrifice both runners advance\n"
                        baseState[2] = 1
                        baseState[1] = 1
                        baseState[0] = 0
            out_stealing = False
            if outcome.endswith("+cs"):
                out_stealing = True
                outcome = outcome[0:-3]
                logs += "Runner picked off by " + currPitcher + "\n"
            if (outcome == "4"):
                runs += 1 + baseState[0] + baseState[1] + baseState[2]
                baseState = [0, 0, 0]
            if (outcome == "3"):
                runs += baseState[0] + baseState[1] + baseState[2]
                baseState = [0, 0, 1]
            if (outcome == "2"):
                runs += baseState[0] + baseState[1] + baseState[2]
                baseState = [0, 1, 0]
            if (outcome == "1"):
                runs += baseState[1] + baseState[2]
                baseState[2] = 0
                baseState[1] = 0
                if (baseState[0] == 1):
                    rng = random.uniform(0, 1)
                    if (rng > 1.0 - config.firstToThirdSingleRatio):
                        logs += "runner first to third\n"
                        baseState[2] = 1
                    else:
                        baseState[1] = 1
                baseState[0] = 1
            if (outcome == "walk" or outcome == "hbp"):
                if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                    runs += 1
                elif (baseState[0] == 1 and baseState[2] == 1):  # 13 loads it
                    baseState[1] = 1
                elif (baseState[0] == 1 and baseState[1] == 1):  # 12 loads it
                    baseState[2] = 1
                elif (baseState[1] == 1 and baseState[2] == 1):  # 23 loads it
                    baseState[0] = 1
                elif (baseState[0] == 1):  # 1 pushed to second
                    baseState[1] = 1
                else:  # first empty
                    baseState[0] = 1
            if out_stealing:
                if outcome == 'walk' or outcome == 'hbp':
                    outcome = 1
                    baseState[int(outcome) - 1] = 0
                    outs += 1
                    logs += "Runner picked off by " + currPitcher + "\n"
        else:
            team = battingTeam
            player_nm = team['batting-order'][orderSlot - 1]
            outcome = offensiveOutcome(team, orderSlot)
            logs += "(outs: " + str(
                outs) + ") " + player_nm + " at-bat: " + outcome + "\n"
            if (outcome == "k"):
                outs += 1
            if (outcome == "in_play_out"):
                outs += 1
                rng = random.uniform(0, 1)
                if (baseState[2] == 1 and outs < 3):
                    if (rng > 1.0 - config.sacrificeFlyToHomeRatio):
                        logs += "sacrifice runner scores\n"
                        runs += 1
                        baseState[2] = 0
                # don't reroll, if we can't score the run home we won't advance to third
                if (baseState[1] == 1 and baseState[2] == 0 and outs < 3):
                    if (rng > 1.0 - config.productiveOutToThirdRatio):
                        logs += "sacrifice runner moved to 3rd\n"
                        baseState[2] = 1
                        baseState[1] = 0
                if (baseState[0] == 1 and outs < 3):
                    if (rng < config.doublePlayRatioOnOutsWhenRunnerOnFirst):
                        logs += "double play (6-4-3/4-6-3)\n"
                        outs += 1
                        baseState[0] = 0
                    elif (baseState[
                              1] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                        logs += "sacrifice runner moved to 2nd\n"
                        baseState[1] = 1
                        baseState[0] = 0
                    elif (baseState[
                              2] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                        logs += "sacrifice both runners advance\n"
                        baseState[2] = 1
                        baseState[1] = 1
                        baseState[0] = 0
            stolen = False
            out_stealing = False
            if outcome.endswith("+sb"):
                stolen = True
                outcome = outcome[0:-3]
            if outcome.endswith("+cs"):
                stolen = True
                out_stealing = True
                outcome = outcome[0:-3]
            if (outcome == "4"):
                runs += 1 + baseState[0] + baseState[1] + baseState[2]
                baseState = [0, 0, 0]
            if (outcome == "3"):
                runs += baseState[0] + baseState[1] + baseState[2]
                baseState = [0, 0, 1]
            if (outcome == "2"):
                runs += baseState[0] + baseState[1] + baseState[2]
                baseState = [0, 1, 0]
            if (outcome == "1"):
                runs += baseState[1] + baseState[2]
                baseState[2] = 0
                baseState[1] = 0
                if (baseState[0] == 1):
                    rng = random.uniform(0, 1)
                    if (rng > 1.0 - config.firstToThirdSingleRatio):
                        logs += "runner first to third\n"
                        baseState[2] = 1
                    else:
                        baseState[1] = 1
                baseState[0] = 1
            if (outcome == "walk" or outcome == "hbp"):
                if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                    runs += 1
                elif (baseState[0] == 1 and baseState[2] == 1):  # 13 loads it
                    baseState[1] = 1
                elif (baseState[0] == 1 and baseState[1] == 1):  # 12 loads it
                    baseState[2] = 1
                elif (baseState[1] == 1 and baseState[2] == 1):  # 23 loads it
                    baseState[0] = 1
                elif (baseState[0] == 1):  # 1 pushed to second
                    baseState[1] = 1
                else:  # first empty
                    baseState[0] = 1
            if stolen or out_stealing:
                if outcome == 'walk' or outcome == 'hbp':
                    outcome = 1
                chk_empty_base = int(outcome)
                if out_stealing:
                    baseState[chk_empty_base - 1] = 0
                    outs += 1
                    logs += player_nm + " was picked off and is out\n"
                    # logs += baseState)
                elif baseState[chk_empty_base] == 0:
                    baseState[chk_empty_base] = 1
                    baseState[chk_empty_base - 1] = 0
                    logs += player_nm + " stole a base\n"
                    # logs += str(baseState)
                else:
                    logs += player_nm + " had a good jump but the next base was occupied\n"
        # Advance order slot even if a pitching outcome was chosen
        orderSlot += 1
        if (orderSlot > 9):
            orderSlot -= 9
    logs += battingTeam["team-name"] + " scored: " + str(runs) + "\n"
    return {"out": logs, "runs": runs, "orderSlot": orderSlot,
            "currPitcher": currPitcher}


def executePitchingChange(team, logs, currPitcher, newPitcher):
    logs += currPitcher + " takes a seat. " + newPitcher + " has been warming up and enters the game.\n"
    team['burned-pitchers'].append(newPitcher)
    return newPitcher, logs


def scoreIsClose(team, score_d, pitcherHome):
    return pitcherHome and team["closer-max-lead-home"] >= score_d >= team["closer-min-lead-home"] or (not pitcherHome and -1 * team["closer-max-lead-away"] <= score_d <= -1 * team["closer-min-lead-away"])


def decidePitchingChange(currPitcher, baseState, team, inning, score_d, pitcherHome, logs):
    results = team['pitching-results']
    if inning >= 7:
        closer, fireman = team['closer'], team['fireman']
        cl_pitches, fm_pitches = len(results[closer]) > 1, len(results[fireman]) > 1
        score_close = scoreIsClose(team, score_d, pitcherHome)
        if inning >= 9 and closer not in team['burned-pitchers'] and score_close and cl_pitches:
            currPitcher, logs = executePitchingChange(team, logs, currPitcher, closer)
        elif fireman not in team['burned-pitchers'] and baseState[1] + baseState[2] > 0 and score_close:
            currPitcher, logs = executePitchingChange(team, logs, currPitcher, fireman)
    inning = inning if inning <= 9 else 9
    score_blowout = team['blowout-deficit-by-inning'][inning - 1]
    is_blowout = score_d * -1 > score_blowout
    double_blowout = score_d * -1 > score_blowout * 2
    if double_blowout:
        currPitcher, logs = executePitchingChange(team, logs, currPitcher, 'Position Player')
    while len(results[currPitcher]) < 2:  #We still need to substitute SOMEONE who can pitch
        if is_blowout:  # reverse bullpen order
            for pitcher in team['bullpen'][:-1:-1]:  # reverse order and ignore position player
                if len(results[pitcher]) > 1 and pitcher not in team['burned-pitchers']:
                    currPitcher, logs = executePitchingChange(team, logs, currPitcher, pitcher)
                    break
        else:
            for pitcher in team['bullpen']:
                if len(results[pitcher]) > 1 and pitcher not in team['burned-pitchers']:
                    currPitcher, logs = executePitchingChange(team, logs, currPitcher, pitcher)
                    break
    if currPitcher not in team['burned-pitchers']:  # shouldnt happen
        team['burned-pitchers'].append(currPitcher)
    return currPitcher, team, logs


def ops(dataset):
    ab = 0
    slg = 0
    pa = 0
    ob = 1
    # todo remove +cs +sb
    for app in dataset:
        if app in ["1", "2", "3", "4"]:
            slg += int(app)
            ab += 1
            ob += 1
        if app in ["in_place_out", "k"]:
            ab += 1
        if app in ["walk", "hbp"]:
            pa += 1
            ob += 1
    pa += ab
    obp = float(ob) / pa
    slgp = float(slg) / ab
    return obp + slgp


def simOffensiveInning(team, orderSlot, inning):
    if inning > 9:
        baseState = [0, 1, 0]
    else:
        baseState = [0, 0, 0]
    runs = 0
    outs = 0
    logs = "\n"
    while outs < 3:
        player_nm = team['batting-order'][orderSlot - 1]
        outcome = offensiveOutcome(team, orderSlot)
        logs += "(outs: " + str(
            outs) + ") " + player_nm + " at-bat: " + outcome + "\n"
        if (outcome == "k"):
            outs += 1
        if (outcome == "in_play_out"):
            outs += 1
            rng = random.uniform(0, 1)
            if (baseState[2] == 1 and outs < 3):
                if (rng > 1.0 - config.sacrificeFlyToHomeRatio):
                    logs += "sacrifice runner scores\n"
                    runs += 1
                    baseState[2] = 0
            # don't reroll, if we can't score the run home we won't advance to third
            if (baseState[1] == 1 and baseState[2] == 0 and outs < 3):
                if (rng > 1.0 - config.productiveOutToThirdRatio):
                    logs += "sacrifice runner moved to 3rd\n"
                    baseState[2] = 1
                    baseState[1] = 0
            if (baseState[0] == 1 and outs < 3):
                if (rng < config.doublePlayRatioOnOutsWhenRunnerOnFirst):
                    logs += "double play (6-4-3/4-6-3)\n"
                    outs += 1
                    baseState[0] = 0
                elif (baseState[
                          1] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                    logs += "sacrifice runner moved to 2nd\n"
                    baseState[1] = 1
                    baseState[0] = 0
                elif (baseState[
                          2] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                    logs += "sacrifice both runners advance\n"
                    baseState[2] = 1
                    baseState[1] = 1
                    baseState[0] = 0
        stolen = False
        out_stealing = False
        if outcome.endswith("+sb"):
            stolen = True
            outcome = outcome[0:-3]
        if outcome.endswith("+cs"):
            stolen = True
            out_stealing = True
            outcome = outcome[0:-3]
        if (outcome == "4"):
            runs += 1 + baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 0]
        if (outcome == "3"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 1]
        if (outcome == "2"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 1, 0]
        if (outcome == "1"):
            runs += baseState[1] + baseState[2]
            baseState[2] = 0
            baseState[1] = 0
            if (baseState[0] == 1):
                rng = random.uniform(0, 1)
                if (rng > 1.0 - config.firstToThirdSingleRatio):
                    logs += "runner first to third\n"
                    baseState[2] = 1
                else:
                    baseState[1] = 1
            baseState[0] = 1
        if (outcome == "walk" or outcome == "hbp"):
            if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                runs += 1
            elif (baseState[0] == 1 and baseState[2] == 1):  # 13 loads it
                baseState[1] = 1
            elif (baseState[0] == 1 and baseState[1] == 1):  # 12 loads it
                baseState[2] = 1
            elif (baseState[1] == 1 and baseState[2] == 1):  # 23 loads it
                baseState[0] = 1
            elif (baseState[0] == 1):  # 1 pushed to second
                baseState[1] = 1
            else:  # first empty
                baseState[0] = 1
        if stolen or out_stealing:
            if outcome == 'walk' or outcome == 'hbp':
                outcome = 1
            chk_empty_base = int(outcome)
            if out_stealing:
                baseState[chk_empty_base - 1] = 0
                outs += 1
                logs += player_nm + " was picked off and is out\n"
                # logs += baseState)
            elif baseState[chk_empty_base] == 0:
                baseState[chk_empty_base] = 1
                baseState[chk_empty_base - 1] = 0
                logs += player_nm + " stole a base\n"
                # logs += str(baseState)
            else:
                logs += player_nm + " had a good jump but the next base was occupied\n"
                orderSlot += 1
        if (orderSlot > 9):
            orderSlot -= 9
    logs += team["team-name"] + " scored: " + str(runs / 2.0)
    return {"orderSlot": orderSlot, "runs": runs, "out": logs}


def simDefensiveInning(team, currPitcher, inning, our_score, their_score,
                       isHome):
    baseState = [0, 0, 0]
    runs = 0
    outs = 0
    logs = ""
    while outs < 3:
        bullpenIdx = 0
        score_d = our_score - their_score - runs
        while len(team['pitching-results'][currPitcher]) < 1:
            old = currPitcher
            currPitcher, team, logs = decidePitchingChange(baseState, team, inning,
                                               bullpenIdx, score_d)
            logs += old + " is exhausted and being replaced on the mound by " + currPitcher + ". Some respectful clapping surfaces from the crowd in recognition of the effort.\n"
            team['burned-pitchers'].append(currPitcher)
            bullpenIdx += 1
            if inning >= 7:
                if inning >= 9 and team['closer'] not in team[
                    'burned-pitchers']:
                    if (isHome and score_d <= team[
                        "closer-max-lead-home"] and score_d >= team[
                            "closer-min-lead-home"]) or (
                            not isHome and score_d >= -1 * team[
                        "closer-max-lead-away"] and score_d <= -1 * team[
                                "closer-min-lead-away"]):
                        logs += currPitcher + " takes a seat. Crunch time means " + \
                                team['closer'] + " time.\n"
                        currPitcher = team['closer']
                        team['burned-pitchers'].append(currPitcher)

                elif team['fireman'] not in team['burned-pitchers'] and \
                        baseState[1] + baseState[2] > 0:
                    if (isHome and score_d <= team[
                        "closer-max-lead-home"] and score_d >= team[
                            "closer-min-lead-home"]) or (
                            not isHome and score_d >= -1 * team[
                        "closer-max-lead-away"] and score_d <= -1 * team[
                                "closer-min-lead-away"]):
                        logs += currPitcher + " is sweating and the manager makes a call to the pen, luckily " + \
                                team['fireman'] + " was already warming up.\n"
                        currPitcher = team['fireman']
                        team['burned-pitchers'].append(currPitcher)

        outcome = team['pitching-results'][currPitcher].pop(0)
        logs += "(outs: " + str(
            outs) + ") " + currPitcher + " pitching: " + outcome + "\n"
        if (outcome == "k"):
            outs += 1
        if (outcome == "in_play_out"):
            outs += 1
            rng = random.uniform(0, 1)
            if (baseState[2] == 1 and outs < 3):
                if (rng > 1.0 - config.sacrificeFlyToHomeRatio):
                    logs += "sacrifice runner scores\n"
                    runs += 1
                    baseState[2] = 0
            # don't reroll, if we can't score the run home we won't advance to third
            if (baseState[1] == 1 and baseState[2] == 0 and outs < 3):
                if (rng > 1.0 - config.productiveOutToThirdRatio):
                    logs += "sacrifice runner moved to 3rd\n"
                    baseState[2] = 1
                    baseState[1] = 0
            if (baseState[0] == 1 and outs < 3):
                if (rng < config.doublePlayRatioOnOutsWhenRunnerOnFirst):
                    logs += "double play (6-4-3/4-6-3)\n"
                    outs += 1
                    baseState[0] = 0
                elif (baseState[
                          1] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                    logs += "sacrifice runner moved to 2nd\n"
                    baseState[1] = 1
                    baseState[0] = 0
                elif (baseState[
                          2] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                    logs += "sacrifice both runners advance\n"
                    baseState[2] = 1
                    baseState[1] = 1
                    baseState[0] = 0
        out_stealing = False
        if outcome.endswith("+cs"):
            out_stealing = True
            outcome = outcome[0:-3]
            logs += "Runner picked off by " + currPitcher + "\n"
        if (outcome == "4"):
            runs += 1 + baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 0]
        if (outcome == "3"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 0, 1]
        if (outcome == "2"):
            runs += baseState[0] + baseState[1] + baseState[2]
            baseState = [0, 1, 0]
        if (outcome == "1"):
            runs += baseState[1] + baseState[2]
            baseState[2] = 0
            baseState[1] = 0
            if (baseState[0] == 1):
                rng = random.uniform(0, 1)
                if (rng > 1.0 - config.firstToThirdSingleRatio):
                    logs += "runner first to third\n"
                    baseState[2] = 1
                else:
                    baseState[1] = 1
            baseState[0] = 1
        if (outcome == "walk" or outcome == "hbp"):
            if (baseState[0] + baseState[1] + baseState[2] == 3):  # ld
                runs += 1
            elif (baseState[0] == 1 and baseState[2] == 1):  # 13 loads it
                baseState[1] = 1
            elif (baseState[0] == 1 and baseState[1] == 1):  # 12 loads it
                baseState[2] = 1
            elif (baseState[1] == 1 and baseState[2] == 1):  # 23 loads it
                baseState[0] = 1
            elif (baseState[0] == 1):  # 1 pushed to second
                baseState[1] = 1
            else:  # first empty
                baseState[0] = 1
        if out_stealing:
            if outcome == 'walk' or outcome == 'hbp':
                outcome = 1
                baseState[int(outcome) - 1] = 0
                outs += 1
                logs += "Runner picked off by " + currPitcher + "\n"
    logs += team["team-name"] + " conceded " + str(runs / 2.0) + " runs\n"
    return {"currPitcher": currPitcher, "runs": runs, "out": logs}
