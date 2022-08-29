import random

import simulationConfig as config


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
    if config.ignoreRightyLeftyHandedness:
        rng = random.uniform(0, 1)
        return 0.5 > rng
    batter = battingTeam['batting-order'][orderSlot - 1]
    batter_hands = battingTeam['handedness'][batter]
    pitcher_hands = pitchingTeam['handedness'][currPitcher]
    # It's okay that right handed batters do "better" in this than LHB because they face the disadvantage of same-handed pitchers MORE often than LHB. It kinda makes sense.
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


def isError(pitchingTeam, inning, outs, gameNumber, outcome='in_play_out', processError=False):
    code = str(inning) + '.' + str(outs+1)
    if code in pitchingTeam['errors'] and outcome == 'in_play_out':
        err = pitchingTeam['errors'][code]
        if err['game'] == gameNumber:
            if processError:
                return pitchingTeam['errors'].pop(code, None)['name']
            return err['name']
    return False


def score(runs, logs, scored):
    if scored == 0:
        return runs, logs
    elif scored == 1:
        logs += "[ 1 run scored! ]\n"
    else:
        logs += "[ " + str(scored) + " runs scored!!! ]\n"
    return runs+scored, logs


def simBlendedInning(battingTeam, pitchingTeam, orderSlot, currPitcher, inning,
                     pitcherScore, batterScore, pitcherHome, gameNumber):
    if inning > 9:
        baseState = [0, 1, 0]
    else:
        baseState = [0, 0, 0]
    runs, outs, hits, errors = 0, 0, 0, 0
    logs = "\n"
    while outs < 3:
        prevOuts = outs
        coin = getCoinForMatchup(config.teamsInLeague, pitchingTeam, battingTeam, currPitcher, orderSlot)
        batter = battingTeam['batting-order'][orderSlot - 1]
        if coin == 'pitcher':
            team = pitchingTeam
            score_d = pitcherScore - batterScore - runs
            currPitcher, team, logs = decidePitchingChange(currPitcher, baseState, team, inning, score_d, pitcherHome, logs)
            outcome = team['pitching-results'][currPitcher].pop(0)
            # Discard a second outcome to compensate for "batter" at-bats
            team['pitching-results'][currPitcher].pop(0)
            logs += str(outs) + " out) " + currPitcher + " pitching (v " + batter.split(' ')[1] + "): " + outcome + "\n"
            if (outcome == "k"):
                outs += 1
            if (outcome == "in_play_out" and not isError(pitchingTeam, inning, outs, gameNumber)):
                outs += 1
                rng = random.uniform(0, 1)
                if (baseState[2] == 1 and outs < 3):
                    if (rng > 1.0 - config.sacrificeFlyToHomeRatio):
                        logs += "sacrifice runner scores\n"
                        runs, logs = score(runs, logs, 1)
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
            if (outcome == 'home run'):
                hits+=1
                runs, logs = score(runs, logs, 1 + baseState[0] + baseState[1] + baseState[2])
                baseState = [0, 0, 0]
            if (outcome == 'triple'):
                hits += 1
                runs, logs = score(runs, logs, baseState[0] + baseState[1] + baseState[2])
                baseState = [0, 0, 1]
            if (outcome == 'double'):
                hits += 1
                runs, logs = score(runs, logs, baseState[0] + baseState[1] + baseState[2])
                baseState = [0, 1, 0]
            if (outcome == 'single'):
                hits += 1
                runs, logs = score(runs, logs, baseState[1] + baseState[2])
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
                    runs, logs = score(runs, logs, 1)
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
            errorPlayer = isError(pitchingTeam, inning, prevOuts, gameNumber, outcome, True)
            if errorPlayer != False:
                errors += 1
                #logs += str(baseState) + "\n"
                logs += "An error is committed by " + errorPlayer + "! Everyone is safe and all runners advance.\n"
                runs, logs = score(runs, logs, baseState[2])
                secondToHomeOnErrorChance = config.secondToHomeOnErrorChance
                if prevOuts == 2:
                    secondToHomeOnErrorChance = config.secondToHomeOnErrorChanceTwoOuts
                rng = random.uniform(0, 1)
                if rng < secondToHomeOnErrorChance:
                    runs, logs = score(runs, logs, baseState[1])
                    if baseState[1] == 1:
                        logs += "The run scores from second on the error\n"
                    if rng < config.firstToThirdOnErrorChanceTwoOuts and prevOuts == 2:
                        if baseState[0] == 1:
                            logs += "Runner first to third on the costly two-out error\n"
                        baseState[2] = baseState[0]
                        baseState[1] = 0
                        baseState[0] = 1
                    else:
                        baseState[1] = baseState[0]
                        baseState[0] = 1
                else:
                    baseState[2] = baseState[1]
                    baseState[1] = baseState[0]
                    baseState[0] = 1
                #logs += str(baseState) + "\n"

        else:
            team = battingTeam
            outcome = offensiveOutcome(team, orderSlot)
            logs += str(outs) + " out) " + batter + " hitting (v " + currPitcher.split(' ')[1] + "): " + outcome + "\n"
            if (outcome == "k"):
                outs += 1
            if (outcome == "in_play_out" and not isError(pitchingTeam, inning, outs, gameNumber)):
                outs += 1
                rng = random.uniform(0, 1)
                if (baseState[2] == 1 and outs < 3):
                    if (rng > 1.0 - config.sacrificeFlyToHomeRatio):
                        logs += "sacrifice runner scores\n"
                        runs, logs = score(runs, logs, 1)
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
            if (outcome == 'home run'):
                hits += 1
                runs, logs = score(runs, logs, 1 + baseState[0] + baseState[1] + baseState[2])
                baseState = [0, 0, 0]
            if (outcome == 'triple'):
                hits += 1
                runs, logs = score(runs, logs, baseState[0] + baseState[1] + baseState[2])
                baseState = [0, 0, 1]
            if (outcome == 'double'):
                hits += 1
                runs, logs = score(runs, logs, baseState[0] + baseState[1] + baseState[2])
                baseState = [0, 1, 0]
            if (outcome == 'single'):
                hits += 1
                runs, logs = score(runs, logs, baseState[1] + baseState[2])
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
                    runs, logs = score(runs, logs, 1)
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
                if outcome == 'walk' or outcome == 'hbp' or outcome == "single":
                    chk_empty_base = 1
                elif outcome == "double":
                    chk_empty_base = 2
                else:
                    chk_empty_base = 3
                if out_stealing:
                    baseState[chk_empty_base - 1] = 0
                    outs += 1
                    logs += batter + " was picked off and is out\n"
                    # logs += baseState)
                elif baseState[chk_empty_base] == 0:
                    baseState[chk_empty_base] = 1
                    baseState[chk_empty_base - 1] = 0
                    logs += batter + " stole a base\n"
                    # logs += str(baseState)
                else:
                    logs += batter + " had a good jump but the next base was occupied\n"
            errorPlayer = isError(pitchingTeam, inning, prevOuts, gameNumber, outcome, True)
            if errorPlayer != False:
                errors += 1
                #logs += str(baseState) + "\n"
                logs += "An error is committed by " + errorPlayer + "! Everyone is safe and all runners advance.\n"
                runs, logs = score(runs, logs, baseState[2])
                secondToHomeOnErrorChance = config.secondToHomeOnErrorChance
                if prevOuts == 2:
                    secondToHomeOnErrorChance = config.secondToHomeOnErrorChanceTwoOuts
                rng = random.uniform(0, 1)
                if rng < secondToHomeOnErrorChance:
                    runs, logs = score(runs, logs, baseState[1])
                    if baseState[1] == 1:
                        logs += "The run scores from second on the error\n"
                    if rng < config.firstToThirdOnErrorChanceTwoOuts and prevOuts == 2:
                        if baseState[0] == 1:
                            logs += "Runner first to third on the costly two-out error\n"
                        baseState[2] = baseState[0]
                        baseState[1] = 0
                        baseState[0] = 1
                    else:
                        baseState[1] = baseState[0]
                        baseState[0] = 1
                else:
                    baseState[2] = baseState[1]
                    baseState[1] = baseState[0]
                    baseState[0] = 1
                #logs += str(baseState) + "\n"
        # Advance order slot even if a pitching outcome was chosen
        orderSlot += 1
        if (orderSlot > 9):
            orderSlot -= 9
    logs += battingTeam["team-name"] + " scored: " + str(runs) + "\n"
    return {"out": logs, "runs": runs, "orderSlot": orderSlot,
            "currPitcher": currPitcher, "hits": hits, "errors": errors}


def executePitchingChange(team, logs, currPitcher, newPitcher):
    logs += currPitcher + " takes a seat. " + newPitcher + " has been warming up and enters the game.\n"
    if newPitcher != 'Position Player':
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
        if is_blowout:
            iter_order = team['bullpen'][-2::-1]  # reverse bullpen order and ignore position player
            iter_order.append(team['bullpen'][-1])  # add position player back in as a last resort
            for pitcher in iter_order:
                if len(results[pitcher]) > 1 and pitcher not in team['burned-pitchers']:
                    currPitcher, logs = executePitchingChange(team, logs, currPitcher, pitcher)
                    break
        else:
            for pitcher in team['bullpen']:
                if len(results[pitcher]) > 1 and pitcher not in team['burned-pitchers']:
                    currPitcher, logs = executePitchingChange(team, logs, currPitcher, pitcher)
                    break
    #if currPitcher not in team['burned-pitchers'] and currPitcher != 'Position Player':  # shouldnt happen
        #team['burned-pitchers'].append(currPitcher)
    return currPitcher, team, logs


def ops(dataset):
    ab = 0
    slg = 0
    pa = 0
    ob = 1
    # todo remove +cs +sb
    for app in dataset:
        if app in ['single', 'double', 'triple', 'home run']:
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
