innings = 9
trackedBattingStats = ['ab', 'h', 'doubles', 'triples', 'hr', 'sb', 'bb', 'k']
trackedPitchingStats = ['ip', 'h', 'bb', 'k', 'hr']
# doubles rate from cubs 2021 season (788 non home runs) as the median doubles team
# triples stats from brewers 2021 season as a median triples team
# the hit ratios are only used for pitching simulations since we have detailed hit stats for batters
hitRatios = [0.771, 0.25, 0.019]# single double triple
doublePlayRatioOnOutsWhenRunnerOnFirst = .17  # No source for these. Wild guesses
sacrificeBuntRatio = .07
productiveOutToThirdRatio = .10
sacrificeFlyToHomeRatio = .25
firstToThirdSingleRatio = .45
