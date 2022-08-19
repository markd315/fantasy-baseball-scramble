# fantasy-baseball-scramble
A fantasy baseball mode with real lineups and bullpen configurations that replays plate appearances from the week in random order to synthesize results.

### How to run
```commandline
pip install -r requirements.txt
python simulateLeagueWeek.py
```


![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/line_output.png)

![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/debug_output.png)

Both your batters and pitchers play a full simulated game against your opponent(s).

Actual plate appearances from the week for each batter or pitcher are selected in random order to compose this game.

Some assumptions are made about runner advancement, the likelihood of a double play, etc to facilitate scoring and making outs at the correct rates.

If your hitter steals a base during the week or is caught stealing, this modifier will be applied to the end of one of their plate appearances from the week in game.

Two way players must play as the DH if in the lineup.

# Pitching rules

Your starters will be selected in the order they are listed, be sure to make any changes to your weekly lineup before the week begins.

The starter (and any subsequent pitcher) will pitch until:

- They have become exhausted (no more real-life plate appearences remaining from the week).
- The game is in a high-leverage situation in the seventh inning or later (defined by your closer min/max lead settings and by having a runner in scoring position).
- The ninth inning or later is beginning and the closer settings apply.

Case 1: When any pitcher is exhausted, the first non-exhausted member of `bullpen` will enter the game, unless your team is getting blown out as defined by `blowout-deficit-by-inning`, in which case the order is reversed. If your team is behind by double this amount, a position player will pitch (badly) to help save your pitchers for another game.

Case 2: The `fireman` will enter the game unless the closer is already pitching.

Case 3: The closer will enter the game.

Exhaustion may vary slightly because of how the pitching and batting results are blended. For every pitcher PA result selected, two PA will be eliminated from the list to account for the fatigue experienced when a batter's PA result is selected.

# Tips:

Think about which teams your batters and pitchers are facing this week when constructing your lineup! Just like in any other fantasy sport, they are still playing against THEIR opponents, not YOUR opponent.

The first two batters in your order will get the most plate appearences. Try using high OBP players here.

Given that you choose high OBP players who can hit doubles or steal bases for the first two slots, the 3rd and 4th hitters will be most likely to bat with men on base. Try using power hitters here.

For aid in drafting, a file playersTeamsAndPositions.json is included and you can query it in code by importing `lineup_api`. See some examples of using it
```python
import lineup_api
shohei = lineup_api.scrapePlayerPositions(teamId=108, pos='TWP')[0]
judge = lineup_api.scrapePlayerPositions('Aaron Judge')[0]
metspitchers = lineup_api.scrapePlayerPositions(teamId=121, pos='P')
```

# Features to come:

Currently fielding errors are tracked but not implemented. Eventually, you will be punished defensively for having hitters who commit fielding errors in real life in your lineup, same with catcher interference, etc.

If your hitter gets on base in the seventh inning or later and your pinch runner has any CS or SB from the week, the hitter will be replaced by the pinch-runner and the CS or SB modifier will take place.

Same for pinch hitter maybe. But it seems hard to not make this pinch hitter thing OP. If it's just a second chance to steal/bat when the hitter does not succeed with no consequence, maybe that's too strong?

Ok so maybe implement PR straight up since they are specialists. For PH, look at the hitter being replaced. Add 3 past PA and 3 future PA to "see if they are hot" by taking the OPS. If the PH dataset has a higher OPS, make the substitution.

Allow a 4-player bench in case position players have 5 or fewer plate appearences from the week (errors are at least detected for this)

More balanced sample teams, LAQ and DVS are overpowered especially the batting orders. Maybe keep these as strong hitting teams but make their pitching weak.