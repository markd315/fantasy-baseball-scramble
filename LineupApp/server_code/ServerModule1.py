import json

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

# This is a server module. It runs on the server, rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
import mlb_api
import jsbeautifier


@anvil.server.http_endpoint('/league/:league/:teamNm/lineup', methods=["POST"], authenticate_users=False)
def post_lineup(league, teamNm, **q):
    set_lineup(league, teamNm, json.dumps(anvil.server.request.body_json))


@anvil.server.callable
def get_lineup(league, teamNm):
    with open("leagues/" + league + "/team-lineups/" + teamNm + ".json",
              "r") as lineup_file:
        ptl_lineup = json.load(lineup_file)
        return json.dumps(ptl_lineup, indent=2, separators=(',', ': '))
    return ""


@anvil.server.callable
def set_lineup(league, teamNm, lineup):
    lineup = json.loads(lineup)
    with open("leagues/" + league + "/team-lineups/" + teamNm + ".json",
              "r") as lineup_file:
        old_lineup = json.load(lineup_file)
        if old_lineup['team-name'] != lineup['team-name'] or old_lineup[
            'abbv'] != lineup['abbv']:
            raise BaseException("Invalid access attempt")
        else:
            abbv = old_lineup['abbv']
        lineup_file.close()
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster",
              "r") as roster_file:
        roster = roster_file.readlines()
        for idx, line in enumerate(roster):
            roster[idx] = line.strip()
    mlb_api.getAndValidateTeam(lineup, roster)
    with open("leagues/" + league + "/team-lineups/" + teamNm + ".json",
              "w") as lineup_file:
        lineup_file.write(json.dumps(lineup, indent=2, separators=(',', ': ')))
        lineup_file.close()
    return {}


@anvil.server.callable
def update_task(task, complete):
  if app_tables.tasks.has_row(task):
	  task.update(complete=complete)


@anvil.server.callable
def delete_task(task):
  if app_tables.tasks.has_row(task):
	  task.delete()