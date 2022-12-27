import datetime
import json
import os
from pathlib import Path

import pandas as pd

import simulationConfig


def commitNewRosters(league):
    pathpre = "leagues/" + league + "/team-lineups/"
    for p in Path(pathpre).glob('next_*'):
        with open(pathpre + p.name, 'r') as file_read:
            lines = file_read.readlines()
            file_read.close()
        committed_path = p.name.replace("next_", "")
        with open(pathpre + committed_path, 'w') as file_write:
            file_write.writelines(lines)
            file_write.close()

def get_rostered_team(league, player_nm):
    for p in Path("leagues/" + league + "/team-lineups/").glob('*.roster'):
        with open("leagues/" + league + "/team-lineups/" + p.name, "r") as roster_file:
            lines = roster_file.readlines()
            for idx, line in enumerate(lines):
                lines[idx] = line.strip()
            if player_nm in lines:
                roster_file.close()
                return p.name.replace(".roster", "")
            roster_file.close()
    return ""

def removeFromLineup(league, teamName, player):
    # Iterate through all files in the current directory
    for p in Path("leagues/" + league + "/team-lineups/").glob('*.json'):
        with open("leagues/" + league + "/team-lineups/" + p.name, "r") as file:
            data = json.load(file)

            # Check if the "team-name" property matches the team name parameter
            if data.get("team-name") == teamName:
                # Check if the "closer" property matches the player parameter
                if data.get("closer") == player:
                    # Set the "closer" property to an empty string
                    data["closer"] = ""

                # Check if the "pinch-hitter" property matches the player parameter
                if data.get("pinch-hitter") == player:
                    # Set the "pinch-hitter" property to an empty string
                    data["pinch-hitter"] = ""

                # Check if the "pinch-runner" property matches the player parameter
                if data.get("pinch-runner") == player:
                    # Set the "pinch-runner" property to an empty string
                    data["pinch-runner"] = ""

                # Check if the "fireman" property matches the player parameter
                if data.get("fireman") == player:
                    # Set the "fireman" property to an empty string
                    data["fireman"] = ""
                lst = data.get('batting-order')
                data['batting-order'] = [line.strip() for line in lst if player != line]
                lst = data.get('starters')
                data['starters'] = [line.strip() for line in lst if player != line]
                lst = data.get('bullpen')
                data['bullpen'] = [line.strip() for line in lst if player != line]
                # Open the file for writing and overwrite the JSON data
                file.close()
                with open("leagues/" + league + "/team-lineups/" + p.name, "w") as f:
                    f.write(json.dumps(data, indent=2, separators=(',', ': ')))


def processWaivers(league):
    df = pd.read_csv("leagues/" + league + "/standings.csv")
    # Sort the DataFrame by the "Year" and "Month" columns
    df = df.sort_values(by=["W", "RD"], ascending=[True, True])
    # Get the "Abbv" column as a Pandas Series in the sorted order
    waiverOrder = df["Abbv"].tolist()
    teamNames = df["Team"].tolist()
    waivers_file = "leagues/" + league + "/Waivers"
    # Open the waivers file for reading
    with open(waivers_file, "r") as f:
        # Read the lines of the file into a list
        lines = f.readlines()

    # Create a dictionary to store the claims for each team
    claims = {}
    for line in lines:
        # Split the line by space and get the team and claim
        team, add, drop = line.strip().split(":")
        if team not in claims:
            claims[team] = []
        claims[team].append(add + ":" + drop)

    # Process the claims in the order specified by the waiverOrder list
    for team in waiverOrder:
        if team in claims:
            cl = claims[team]
            for c in cl:
                # Get the add and drop players from the claim
                add, drop = c.split(":")
                rostered_team = get_rostered_team(league, add)
                if rostered_team != "":
                    continue
                rostered_team = get_rostered_team(league, drop)
                if rostered_team != team:
                    continue
                # Open the team's roster file for reading
                with open("leagues/" + league + f"/team-lineups/{team}.roster", "r") as f:
                    # Read the lines of the file into a list
                    roster = f.readlines()
                team_name = teamNames[waiverOrder.index(team)]
                removeFromLineup(league, team_name, drop)
                # Remove the player to drop from the roster
                roster = [line for line in roster if drop not in line]

                # Add the player to add to the roster and limit roster length appropriately
                roster.append(add)
                size = min(simulationConfig.maxRosterSize, len(roster))
                roster = roster[0:size]
                roster_done = []
                for line in roster:
                    line = line.strip() + "\n"
                    roster_done.append(line)
                roster = roster_done
                roster[-1] = roster[-1].strip()
                # Open the team's roster file for writing
                with open("leagues/" + league + f"/team-lineups/{team}.roster", "w") as f:
                    # Write the modified roster to the file
                    for line in roster:
                        f.write(line)
                    f.close()

    # Create a new, blank waivers file
    with open(waivers_file, "w") as f:
        f.close()


def addToWaiver(league, team, add, drop):
    waivers_file = "leagues/" + league + "/Waivers"
    # Open the waivers file for reading
    abbv = authenticateAndGetAbbv(league, team)
    if os.path.isfile(waivers_file):
        with open(waivers_file, "r") as f:
            # Read the lines of the file into a list
            lines = f.readlines()
    else:
        lines = []
    if len(lines) > 0:
        lines[-1] = lines[-1].strip() + "\n"
    lines.append(abbv + ":" + add + ":" + drop)
    with open(waivers_file, "w") as f:
        # Write the modified roster to the file
        for line in lines:
            f.write(line)
        f.close()


def clearWaiverClaims(league, team):
    waivers_file = "leagues/" + league + "/Waivers"
    abbv = authenticateAndGetAbbv(league, team)
    if not os.path.isfile(waivers_file):
        return
    # Open the waivers file for reading
    with open(waivers_file, "r") as f:
        # Read the lines of the file into a list
        lines = f.readlines()
    final = []
    for line in lines:
        chk = line.split(":")[0]
        if chk != abbv:
            final.append(line)
    final[-1] = final[-1].strip()
    with open(waivers_file, "w") as f:
        # Write the modified roster to the file
        for line in final:
            f.write(line)
        f.close()


def getWaiverClaims(league, team):
    waivers_file = "leagues/" + league + "/Waivers"
    abbv = authenticateAndGetAbbv(league, team)
    if not os.path.isfile(waivers_file):
        return []
    # Open the waivers file for reading
    with open(waivers_file, "r") as f:
        # Read the lines of the file into a list
        lines = f.readlines()
    final = []
    for line in lines:
        chk = line.split(":")[0]
        if chk == abbv:
            final.append(line)
    return final


def getLineup(league, teamNm):
    try:
        with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json", "r") as lineup_file:
            lineup = json.load(lineup_file)
            lineup_file.close()
            return lineup
    except BaseException:  # the league is initializing
        print("init")
        with open("leagues/" + league + "/team-lineups/" + teamNm + ".json", "r") as preset_lineup_file:
            lineup = json.load(preset_lineup_file)
            with open("leagues/" + league + "/team-lineups/next_" + teamNm + ".json", "w") as lineup_file:
                lineup_file.write(json.dumps(lineup, indent=2, separators=(',', ': ')))
                lineup_file.close()
            preset_lineup_file.close()


def addPlayerValidated(league, abbv, player_add):
    any_roster = []
    for p in Path("leagues/" + league + "/team-lineups/").glob('*.roster'):
        with open("leagues/" + league + "/team-lineups/" + p.name, "r") as roster_file:
            roster = roster_file.readlines()
            for line in roster:
                any_roster.append(line.strip())
            roster_file.close()
            if abbv in p.name:
                our_roster = roster
    with open("leagues/" + league + "/team-lineups/" + abbv + ".roster", "w") as roster_file:
        if player_add not in any_roster and len(our_roster) < simulationConfig.maxRosterSize and len(our_roster) > 0:
            our_roster[len(our_roster) - 1] += "\n"
            our_roster.append(player_add)
        elif len(our_roster) == 0:
            our_roster = [player_add]
        roster_file.writelines(our_roster)
        roster_file.close()


def checkDraftOver(league):
    for p in Path("leagues/" + league + "/team-lineups/").glob('*.roster'):
        with open("leagues/" + league + "/team-lineups/" + p.name, "r") as roster_file:
            roster = roster_file.readlines()
            roster_file.close()
            if len(roster) < simulationConfig.maxRosterSize:
                return False
    with open("leagues/" + league + "/League_note", "w") as note_file:
        note_file.write("Draft complete! Time to set your lineups!")
        note_file.close()
    add_chat(league, "Draft Helper", "Draft Finalized!")
    return True


def checkDraftState(league, abbv, player_add):  # Returns if we are in a draft at all.
    with open("leagues/" + league + "/League_note", "r+") as note_file:
        note = note_file.readlines()
        if note[0].startswith("Drafting! Current pick order: "):
            pick_state_str = note[0].replace("Drafting! Current pick order: ", "")
            arr = json.loads(pick_state_str)
            if arr[0] == abbv:  # We have made our selection!
                addPlayerValidated(league, abbv, player_add)
                add_chat(league, "Draft Helper", str(abbv) + " drafted " + player_add)
                arr.append(arr.pop(0))
            if arr[0] == "snake":  # no additional logic for a non snake draft, just put the teams in the desired order and it will cycle.
                teams = arr[1:]
                arr = teams[::-1]  # Reverse order so same team picks again
                arr.append("snake")
            output = "Drafting! Current pick order: " + json.dumps(arr)
            note_file.close()
        else:
            return False
    if not checkDraftOver(league):
        with open("leagues/" + league + "/League_note", "r+") as note_file:
            note_file.write(output)
            note_file.close()
    return True


def add_chat(league, sender, msg):
    msg = msg.replace(">", "\\>")  # to avoid fake messages
    date_time_str = datetime.datetime.now().strftime("%m-%d %H:%M")
    with open("leagues/" + league + "/Chat", "a") as chat_file:
        toAdd = ">" + sender + " " + date_time_str + ": " + msg + "\n\n"
        chat_file.write(toAdd)
        chat_file.close()


def authenticateAndGetAbbv(league, teamNm):
    with open("leagues/" + league + "/team-lineups/" + teamNm + ".json", "r") as lineup_file:
        lineup = json.load(lineup_file)
        abbv = lineup['abbv']
        lineup_file.close()
        return abbv