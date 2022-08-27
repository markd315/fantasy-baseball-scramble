leagueWeek = 0
maxRegularSeasonWeeks = 16
innings = 9
trackedBattingStats = ['ab', 'h', 'doubles', 'triples', 'hr', 'sb', 'bb', 'k']
trackedPitchingStats = ['ip', 'h', 'bb', 'k', 'hr']
# doubles rate from cubs 2021 season (788 non home runs) as the median doubles team
# triples stats from brewers 2021 season as a median triples team
# the hit ratios are only used for pitching simulations since we have detailed hit stats for batters
hitRatios = [0.771, 0.25, 0.019]  # single double triple. only used for the pitching half of the simulation since batters have total bases in their hit results from the api
doublePlayRatioOnOutsWhenRunnerOnFirst = .17  # No source for these. Wild guesses
sacrificeBuntRatio = .07
productiveOutToThirdRatio = .10
sacrificeFlyToHomeRatio = .25
firstToThirdSingleRatio = .45
teamsInLeague = 4
secondToHomeOnErrorChance = 0.15
secondToHomeOnErrorChanceTwoOuts = 0.50
firstToThirdOnErrorChanceTwoOuts = 0.25  # subset of previous setting
ignoreRightyLeftyHandedness = False
injuredListRestrictedWeeks = 3
