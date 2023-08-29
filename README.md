# fantasy-baseball-scramble
A fantasy baseball mode with real lineups and bullpen configurations that replays plate appearances from the week in random order to synthesize results.

### How to run the simulation
```commandline
pip install -r requirements.txt
python simulateLeagueWeek.py
```

### How to run the lineup server
```commandline
anvil-app-server --app LineupApp
```


![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/line_output.png)

![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/debug_output.png)

There is even a cool webapp which can run in a docker container and allows you to set your lineups, obtain results etc during league operation. Be sure to change the origin setting in the Dockerfile if you host it somewhere else.

![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/set_lineup.png)
![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/add_drop.png)
![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/standings.png)
![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/web_output.png)

It even works okay on mobile! Mostly.
![Example output](https://raw.githubusercontent.com/markd315/fantasy-baseball-scramble/master/img/mobile.png)


Both your batters and pitchers play full simulated games against your opponent(s).

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
import mlb_api

shohei = mlb_api.playerQuery(teamId=108, pos='TWP')[0]
judge = mlb_api.playerQuery('Aaron Judge')[0]
metspitchers = mlb_api.playerQuery(teamId=121, pos='P')
```

# Features to come:
add email to the team files and be capable of sending notifications, especially "your turn in the async draft!" type ones.

7 day weeks to prevent excessive lineup micromanagement.

Initialize new leagues with HTTP endpoint and a secret key with the team names, codes, etc

If your hitter gets on base in the seventh inning or later and your pinch runner has any CS or SB from the week, the hitter will be replaced by the pinch-runner and the CS or SB modifier will take place.

Same for pinch hitter maybe. But it seems hard to not make this pinch hitter thing OP. If it's just a second chance to steal/bat when the hitter does not succeed with no consequence, maybe that's too strong?
Ok so maybe implement PR straight up since they are specialists. For PH, look at the hitter being replaced. Add 3 past PA and 3 future PA to "see if they are hot" by taking the OPS. If the PH dataset has a higher OPS, make the substitution.

Troubleshoot any issues with substitutions using the live league backups.

Expanded roster option? 30 may make more sense than 25. Make it a config option.

Per league simulation variables instead of globally configured ones. Make config.py invoke functions that get the league specific ones.

Walkoff wins check this part to see if it works

Injured list manage from Bench page, will also require change to data model to allow restrictions on readding player so that you cannot recall them for 10-15 days (or certain number of weeks) after adding.
"injuredList" [
    {
        "fullName": "[fn]"
        "placedOnILTimestamp": ""
    }
]

Setup server cron job for weekly runs.

Manager position as an optional fun thing, they can challenge wrong calls (put "it was a close play" sometimes in the output and have the wrong value) and get ejected for arguing balls and strikes.
Need a datasource if I were to do this. https://www.baseball-reference.com/managers/showabu99.shtml has it but season-level only so weekly comparisons to a baseline would be needed as well as the scraper. lots of work tbh for little benefit.

Webapp ideas for quality of life:
Social login instead of team-code?
Eventually... more info provided on draft page, injury designations for players in lineup page, etc.


# SSL
You must reconfigure the SSL Dockerfile command if you are deploying this somewhere else

# Local docker commands to build image (pipeline in git actions should do this now)
```commandline
docker build -t 720291373173.dkr.ecr.us-east-1.amazonaws.com/fantasy-baseball-prod:latest .
docker push 720291373173.dkr.ecr.us-east-1.amazonaws.com/fantasy-baseball-prod:latest
```

# Docker commands for admin
Saves containerid for anything below.
```commandline

Note: not working yet in set-eid.sh
sudo su -
cd /home/ec2-user

eid=$(docker ps --filter name=fantasy-mlb-dev | tail -n 1 | awk '{print $1;}')
eid=$(docker ps --filter name=fantasy-mlb-prod | tail -n 1 | awk '{print $1;}')
```

Takes a league backup to the vm
```commandline
docker cp $eid:/apps/leagues /home/ec2-user/backups/leagues_backup$(date +'%d-%m-%Y-%H-%M')
```

Restores a league backup
```commandline
docker exec -it $eid rm -rf /apps/leagues
sudo cp /home/ec2-user/backups/leagues_backup04-09-2022-04-52 /home/ec2-user/backups/leagues -r
sudo chown -R root leagues
sudo chmod -R 777 leagues
sudo docker cp /home/ec2-user/backups/leagues/ $eid:/apps
```

Updates the league week prior to an execution
```bash
sudo docker cp $eid:/apps/config.py config.py
sudo cp config.py config.py.backup
sudo echo 'leagueWeek = 0'> config.py
sudo cat config.py.backup |tail -n+2>> config.py
sudo docker cp config.py $eid:/apps/config.py
```

Runs the league week, publishing results logs etc
```commandline
sudo docker exec -it $eid python simulateLeagueWeek.py
```

To lock in rosters (normally a week will already do this)
```commandline
sudo docker exec -it $eid python commitNewRosters.py
```

For any further debugging
```commandline
sudo docker exec -it $eid /bin/sh
```


### some math on handedness

Handedness advantage with pitchers and batters. We want to keep the principle of rolling to determine the outcome in place while favoring R/L and L/R batters.
Needs a factor proportional to number of teams for this too. 30 teams would nullify the handedness advantage since avg pitcher and batter would be same as league avg,
but less (8 for example) means the best 25% of lineups are competing day to day. Instead of .708 league avg OPS, we can look at how the top .25 of that pool would do.

There are more righty PA's (3500) than lefty PA's in any given year, so it makes sense that we need to punish LHB vs LHP more than RHB vs RHP to arrive at the right numbers (see data this intuition was right)
https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1,3&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=mlb&statgroup=2&startDate=2022-3-1&endDate=2022-11-1&players=&filter=&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=10,1&pg=0

example. in a 8 team league, having "your" outcome selected instead of the typical pitchers outcome confers a 15% advantage. Double that for the advantage against a "fantasy pitcher"s outcome (30%)
We can manipulate the odds of the coin flip based on handedness, and arrive at the right OPS for the matchup through some algebra.

solve the equations
x+y=1, .815x+.601y=.739 for example (8 team, LHP vs RHB)

Luckily, all of the 4 platoon splits seem to be almost within the bounds of what we can construct by manipulating these coin tosses a little bit. Even the 16 team league gives us a range of .772 to .644 which we can just use .644 for.

Full league
            HL          HR
   PL      .643        .739
   PR      .709        .703
   OVR(batter - pitcher)     .708

in the table the solved results are (batter coin %) rest is pitcher coin %

16 team league
            HL               HR
   PL     .737(0.0)          .849(.742)
   PR     .796(.508)          .776(.461)
   OVR(+18%) .772-.644


8 team league
             HL           HR
   PL       .788(.196)         .928(.644)
   PR       .861(.505)          .818(.476)
   OVR(+30%) .815-.601

4 team league
             HL           HR
   PL       .837(.274)         .982(.607)
   PR       .918(.503)         .851(.483)
   OVR(+40%) .852-.564


### Cookbook for serving an Anvil app from a public Linux server
If you have a fresh, internet-accessible Linux server running Ubuntu or Rasbian, and an Anvil app ready to serve, the following sequence of commands will set up and serve your app:

With some custom setup because the embedded postgres was not working on my ubuntu 20.04 instances in GCP
```
$ sudo su
\# apt update
\# apt install openjdk-8-jdk python3.7 virtualenv
\# echo 'net.ipv4.ip_unprivileged_port_start=0' > /etc/sysctl.d/50-unprivileged-ports.conf
\# sysctl --system
\# exit
virtualenv -p python3 venv
. venv/bin/activate
source env/bin/activate
git clone this repo
cd into this repo
pip install anvil-app-server
sudo chmod 0700 .anvil-data/db
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql.service
sudo -u postgres createdb my_database
anvil-app-server --app LineupApp --auto-migrate --config-file LineupApp/anvil.yaml
```

don't think this part is needed anymore
```commandline
sudo -u postgres createuser --interactive
alice
sudo -u postgres createdb alice
```