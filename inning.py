import random

import config

def offensiveOutcome(team, orderSlot):
    idx = orderSlot - 1
    res_idx = team['batting-result-curr-idx'][idx]
    res = team['batting-results'][idx][int(res_idx)]
    length = len(team['batting-results'][idx])
    res_idx += 1
    if res_idx >= length:
        res_idx -= length
    team['batting-result-curr-idx'][idx] = res_idx
    return res

# simnning stealbase and simoffensivegame based on https://github.com/markd315/baseball-softball-lineup-tester/blob/master/lineup.py
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
        logs += "(outs: " + str(outs) + ") " + player_nm + " at-bat: " + outcome + "\n"
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
                elif (baseState[1] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                    logs += "sacrifice runner moved to 2nd\n"
                    baseState[1] = 1
                    baseState[0] = 0
                elif (baseState[2] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
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
                #logs += baseState)
            elif baseState[chk_empty_base] == 0:
                baseState[chk_empty_base] = 1
                baseState[chk_empty_base - 1] = 0
                logs += player_nm + " stole a base\n"
                #logs += str(baseState)
            else:
                logs += player_nm + " had a good jump but the next base was occupied\n"
                orderSlot += 1
        if (orderSlot > 9):
            orderSlot -= 9
    logs += team["team-name"] + " scored: " + str(runs/2.0)
    return {"orderSlot": orderSlot, "runs": runs, "out": logs}

def simDefensiveInning(team, currPitcher, inning, our_score, their_score, isHome):
    baseState = [0, 0, 0]
    runs = 0
    outs = 0
    logs = ""
    while outs < 3:
        bullpenIdx = 0
        score_d = our_score - their_score - runs
        while len(team['pitching-results'][currPitcher]) < 1:
            old = currPitcher
            currPitcher = decidePitchingChange(baseState, team, inning, bullpenIdx, score_d)
            logs += old + " is exhausted and being replaced on the mound by " + currPitcher + ". Some respectful clapping surfaces from the crowd in recognition of the effort.\n"
            team['burned-pitchers'].append(currPitcher)
            bullpenIdx += 1
            if inning >= 7:
                if inning >= 9 and team['closer'] not in team['burned-pitchers']:
                    if (isHome and score_d <= team["closer-max-lead-home"] and score_d >= team["closer-min-lead-home"]) or (not isHome and score_d >= -1 * team["closer-max-lead-away"] and score_d <= -1 * team["closer-min-lead-away"]):
                        logs += currPitcher + " takes a seat. Crunch time means " + team['closer'] + " time.\n"
                        currPitcher = team['closer']
                        team['burned-pitchers'].append(currPitcher)

                elif team['fireman'] not in team['burned-pitchers'] and baseState[1] + baseState[2] > 0:
                    if (isHome and score_d <= team["closer-max-lead-home"] and score_d >= team["closer-min-lead-home"]) or (not isHome and score_d >= -1 * team["closer-max-lead-away"] and score_d <= -1 * team["closer-min-lead-away"]):
                        logs += currPitcher + " is sweating and the manager makes a call to the pen, luckily " + team['fireman'] + " was already warming up.\n"
                        currPitcher = team['fireman']
                        team['burned-pitchers'].append(currPitcher)

        outcome = team['pitching-results'][currPitcher].pop(0)
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
                elif (baseState[1] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
                    logs += "sacrifice runner moved to 2nd\n"
                    baseState[1] = 1
                    baseState[0] = 0
                elif (baseState[2] == 0 and rng > 1.0 - config.sacrificeBuntRatio):
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
    logs += team["team-name"] + " conceded " + str(runs/2.0) + " runs\n"
    return {"currPitcher": currPitcher, "runs": runs, "out": logs}


def decidePitchingChange(baseState, team, inning, idx, scoreDiff):
    # todo long reliever
    return team['bullpen'][idx]