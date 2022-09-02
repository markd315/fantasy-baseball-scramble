from random import gauss

import numpy as np
import pandas as pd

import mlb_api
import processing
from inning import obp, slg, ops, ba
from mlb_api import getWeeklyBox

desired_width = 320
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)

pos_pl = ['walk', 'walk', 'hbp', 'k', 'in_play_out', 'in_play_out', "in_play_out", 'in_play_out', 'in_play_out', 'home run', 'double', 'single', 'single', 'single']

print(ba(pos_pl))
print(obp(pos_pl))
print(slg(pos_pl))

def cornerToCornerMath(n, orderliness, cycles):
    orig = list(range(n))
    occur = []
    for _ in range(0, n):
        arr = []
        for _ in range(0, n):
            arr.append(0.0)
        occur.append(arr)

    occur = np.array(occur)
    for _ in range(cycles):
        x = sorted(orig, key=lambda i: gauss(i * orderliness, 1))
        occur[orig, x] += 1.0

    occur *= np.array(100 / float(cycles))
    tlbr = (occur[0][0] + occur[n - 1][n - 1]) / 2.0
    trbl = (occur[0][n - 1] + occur[n - 1][0]) / 2.0
    cToCPercent = (tlbr / trbl * 100.0) - 100.0
    print(cToCPercent)

#cornerToCornerMath(10, 0.0036, 1000000)


box_games = getWeeklyBox(duration_days=5)
pitchers = mlb_api.playerQuery(pos="P")
res = {}
firstHalf, secondHalf = [], []
for i in range(0, 2000):
    for player in pitchers:
        totals = processing.filterPlayerPasDefensive(box_games, player)
        pasFinal = processing.fatigueBasedRandomizePitching(totals)
        if len(pasFinal) < 12:
            firstHalf.extend(pasFinal[:len(pasFinal) // 2])
            secondHalf.extend(pasFinal[len(pasFinal) // 2:])

print(obp(firstHalf))
print(obp(secondHalf))
print(slg(firstHalf))
print(slg(secondHalf))
print(ops(firstHalf))
print(ops(secondHalf))


# .790 for 2nd-3rd TTTO vs .750 for 1st-2nd. That's a 5% higher OPS in the "second half" of the sample we should be targeting.
# 0.6426425399072462
# 0.6773731338662972
# Are the outputs if we filter for min 5 PA, which is really close to what we wanted!
# If we filter for small sample size (max 12) to target bullpen pitchers instead, we get about a 7% deterioration, which is higher but I guess I can live with it. And maybe it makes sense that relievers have less general stamina


#4 and 6 is a 50% difference in corner to corner for n=20
#as I suspected, with a smaller array 19.5 and 20.7 is only a 5ish percent difference in corner to corner for n=5
#if I can find a way to hold the corner to corner change constant based on the orderliness by gathering some points and interpolating, maybe I can later find the expected increase in WHIP over facing batters again and do a pitch count / times thru order effect.
#let's say for now we want to create a 5% change in WHIP from the start to the end of a weekly dataset to model fatigue, since that may be achievable and about right.
#Corner to corner change should be strictly greater than this WHIP change due to the way good vs bad outcomes are distributed so shoot for 6-7%
# these effects are not even though. hr/9 tends to go up by as much as 25% from trip 1 to trip 3, wheras walks actually go DOWN 5%. K's go down 21%.
# maybe we can use an initial ordering of [k, bb, ipo, single, double, triple, hr] for the outcomes before applying this adjustment to account for that?

# n=2: 0.05 -> 5.99
# n=3: 0.024 -> 5.89
# n=5 : 0.01 -> 5.89
# n=10: 0.0036 -> 5.78
# n=18 : 0.0025 -> 5.74
# n=35:  0.00077 -> 5.70
# n=50 : 0.00048 -> 5.71
# n=99 : 0.00023 -> 5.38 use 0.00024
# best fit through points {2,0.05} {3,0.024} {5,0.01} {10,0.0036} {18,0.0025} {35,0.00071}  {50,0.00048} {99,0.00024}
# https://www.wolframalpha.com/input?i=exponential+fit+%7B2%2C0.05%7D+%7B3%2C0.024%7D+%7B5%2C0.01%7D+%7B10%2C0.0036%7D+%7B18%2C0.0025%7D+%7B35%2C0.00077%7D++%7B50%2C0.00048%7D+%7B99%2C0.00024%7D
# 0.169897 e^(-0.620642 x)