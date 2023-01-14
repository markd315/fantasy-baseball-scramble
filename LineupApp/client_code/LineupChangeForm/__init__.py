import json

from anvil import DropDown, FlowPanel, Label, TextBox

from _template import LineupChangeTemplate
import anvil.server


class LineupChangeForm(LineupChangeTemplate):

    def __init__(self, **properties):
        self.init_components_base(**properties)
        self.show_lineup_page()
        self.addHandlers()

    def get_position(self, name):
        pos = 'UN'
        if self.pl_data is None:
            self.get_pl_data()
        for pl in self.pl_data:
            if pl['fullName'] == name:
                pos = pl['primaryPosition']['abbreviation']
        if pos == 'UN':  # We can try to query the server again
            players = json.loads(anvil.server.call('get_results', self.league_name.text, '', [name], 'MLB Player Data'))
            if len(players) > 0:
                self.pl_data.extend(players)
                for pl in self.pl_data:
                    if pl['fullName'] == name:
                        pos = pl['primaryPosition']['abbreviation']
        return pos

    def get_pl_data(self, full=False):
        if not full or self.pl_data is None:
            if self.pl_data is None:
                print("hitting server first time")
                roster_list = anvil.server.call('getRoster', self.league_name.text, self.team_abbv.text)
                if roster_list == "":  # user still typing name, maybe this makes it easy to bruteforce though
                    return
                self.pl_data = json.loads(anvil.server.call('get_results', self.league_name.text, '', roster_list, 'MLB Player Data'))
            return self.pl_data
        else:
            if len(self.pl_data) < 100:  # We have only retrieved this for lineup so far
                self.pl_data = json.loads(anvil.server.call('get_results', self.league_name.text, '', 0, 'MLB Player Data'))
                return self.pl_data
        return self.pl_data

    def error_check_positions(self, **event_args):
        used = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        friendly = ['DH', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']
        self.instr.text = self.txt_label[0]
        for idx, flowcomponent in enumerate(self.lineup.get_components()):
            label = flowcomponent.get_components()[0]
            dropdown = flowcomponent.get_components()[1]
            if str(dropdown.__class__) == "<class 'anvil.DropDown'>" and "Batting" in dropdown.placeholder:
                label.text = self.get_position(dropdown.selected_value)
                label.foreground = "#000000"
                if label.text == "TWP":
                    used[0] += 1
                for idx, match in enumerate(friendly):
                    if match == label.text:
                        used[idx] += 1
                    if used[idx] > 1:
                        label.foreground = "#ff0000"
        laterinstr = self.instr.text
        self.instr.text = ""
        for idx, elem in enumerate(used):
            if elem < 1:
                self.instr.text += "NEED A " + friendly[idx] + " IN LINEUP. "
            if elem > 1:
                self.instr.text += "TOO MANY " + friendly[idx] + " IN LINEUP. "
        self.instr.text += laterinstr

    def exec_add_player_slot(self, payload, player, labels, dds, idx, dd_items, key, list=True):
        player.remove_from_parent()
        old_label = labels[idx]
        player = FlowPanel(align="center")
        old_label.visible = True
        player.add_component(old_label)
        color = dds[idx].background
        pholder = dds[idx].placeholder

        if list == True:
            val = payload[key].pop(0)
        else:
            val = payload[key]
        dropdown_items = dd_items * 1
        if val not in dropdown_items:
            dropdown_items.append(val)

        dd_temp = DropDown(placeholder=pholder, width=240, background=color,
                           items=dropdown_items) # needs placeholder for some legacy code that detects textbox/dropdown vs label
        dd_temp.selected_value = val
        player.add_component(dd_temp)
        self.lineup.add_component(player)

    def exec_add_txt_slot(self, payload, player, labels, dds, idx, key, text=None):
        player.remove_from_parent()
        old_label = labels[idx]
        player = FlowPanel(align="center")
        old_label.visible = True
        player.add_component(old_label)
        pholder = dds[idx].placeholder

        final_text = payload[key] if text is None else text
        tb_temp = TextBox(placeholder=pholder, width=240, text=final_text) # needs placeholder for some legacy code that detects textbox/dropdown vs label
        player.add_component(tb_temp)
        self.lineup.add_component(player)

    def load_positions(self, **event_args):
        try:
            var = self.lineup_defined == None
        except Exception:
            self.define_lineup()
        json_str = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
        if json_str == "":  # user still typing name, maybe this makes it easy to bruteforce though
            return
        payload = json.loads(json_str)
        if self.team_abbv.text == "":  # May as well add this so the user doesn't need to type it.
            self.team_abbv.text = payload['abbv']
        self.base_json = payload
        self.get_bench()
        bench_raw = self.roster.text

        bench_list = bench_raw.split('    ')
        dd_items_p = []
        dd_items_b = []
        for pl in bench_list[:-1]:
            pos_player = pl.strip().split(": ")
            if pos_player[0].strip().upper() in ["P", "TWP"]:
                dd_items_p.append(pos_player[1])
            if pos_player[0].strip().upper() != "P":
                dd_items_b.append(pos_player[1])
        dd_items_p.append("")
        pitchers = self.get_pitchers()  # for pitchers and Shohei to be listed in multiple lineup slots.
        dd_items_p.extend(pitchers)
        dd_items_p = [*set(dd_items_p)]  # Remove dupes

        dd_items_b.append("")
        twp = self.get_twp()
        dd_items_b.extend(twp)
        dd_items_b = [*set(dd_items_b)]  # Remove dupes

        labels = []
        dds = []
        for player in self.lineup.get_components():
            comps = player.get_components()
            comps[0].visible = False
            comps[1].visible = False
            labels.append(comps[0])
            dds.append(comps[1])
            player.visible = False
            player.clear()
        self.lineup.clear()
        #self.lineup = FlowPanel(align="center")
        for idx, player in enumerate(self.direct_players):
            dropdown = dds[idx]
            if hasattr(dropdown, "placeholder") and payload is not None:
                if "Starter" in dropdown.placeholder and len(payload['starters']) > 0:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_p, 'starters')
                if "Bullpen" in dropdown.placeholder and len(payload['bullpen']) > 0:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_p, 'bullpen')
                if "Batting" in dropdown.placeholder and len(payload['batting-order']) > 0:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_b, 'batting-order')
                if "Closer" == dropdown.placeholder:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_p, 'closer', list=False)
                if "Fireman" in dropdown.placeholder:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_p, 'fireman', list=False)
                if "Pinch Hitter" in dropdown.placeholder:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_b, 'pinch-hitter', list=False)
                if "Pinch Runner" in dropdown.placeholder:
                    self.exec_add_player_slot(payload, player, labels, dds, idx, dd_items_b, 'pinch-runner', list=False)
                if "Save Bullpen Deficit" in dropdown.placeholder:
                    self.exec_add_txt_slot(payload, player, labels, dds, idx, 'blowout-deficit-by-inning')
                    dropdown.text = payload['blowout-deficit-by-inning']
                if "Closer Settings" in dropdown.placeholder:
                    res = "Home: " + str(payload['closer-min-lead-home']) + ":" + str(
                        payload["closer-max-lead-home"]) + ", Away: " + str(
                        payload['closer-min-lead-away']) + ":" + str(payload["closer-max-lead-away"])
                    self.exec_add_txt_slot(payload, player, labels, dds, idx, 'closer-min-lead-home', res)
        self.addComponent(self.lineup)
        self.ctl_lineup.add(self.lineup)
        self.ctl_all.add(self.lineup)
        payload = json.loads(json_str)
        for idx, flowcomponent in enumerate(self.lineup.get_components()):
            dropdown = flowcomponent.get_components()[1]
            label = flowcomponent.get_components()[0]
            if str(dropdown.__class__) == "<class 'anvil.DropDown'>" and payload is not None:
                if "Batting" in dropdown.placeholder and len(payload['batting-order']) > 0:
                    label.text = self.get_position(dropdown.selected_value)
        self.load_trades()

    def set_lineup_click(self, **event_args):
        self.error_check_positions()
        if "TOO MANY " in self.instr.text or "NEED A " in self.instr.text:  # Invalid, now the user will know
            return
        if self.league_name.text and self.team_name.text:
            self.base_json['starters'] = []
            self.base_json['bullpen'] = []
            self.base_json['batting-order'] = []
            for flowcomponent in self.lineup.get_components():
                dropdown = flowcomponent.get_components()[1]
                if str(dropdown.__class__) == "<class 'anvil.DropDown'>":
                    if "Starter" in dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['starters'].append(dropdown.selected_value)
                    if "Bullpen" in dropdown.placeholder and len(dropdown.selected_value) > 0:
                        try:
                            int(dropdown.placeholder[-1])  # To exclude Save Bullpen deficit
                            self.base_json['bullpen'].append(dropdown.selected_value)
                        except BaseException:
                            pass
                    if "Batting" in dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['batting-order'].append(dropdown.selected_value)
                    if "Closer" == dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['closer'] = dropdown.selected_value
                    if "Fireman" == dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['fireman'] = dropdown.selected_value
                    if "Fireman" == dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['fireman'] = dropdown.selected_value
                    if "Pinch Hitter" == dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['pinch-hitter'] = dropdown.selected_value
                    if "Pinch Runner" == dropdown.placeholder and len(dropdown.selected_value) > 0:
                        self.base_json['pinch-runner'] = dropdown.selected_value
                else:
                    textbox = dropdown
                    if "Save Bullpen Deficit" in textbox.placeholder and len(textbox.text) > 0:
                        self.base_json['blowout-deficit-by-inning'] = json.loads(textbox.text)
                    if "Closer Settings" in textbox.placeholder:
                        txt = textbox.text
                        txt = txt.replace("Home: ", "")
                        txt = txt.replace("Away: ", "")
                        setts = txt.split(", ")
                        self.base_json['closer-min-lead-home'] = int(setts[0].split(":")[0].strip())
                        self.base_json['closer-max-lead-home'] = int(setts[0].split(":")[1].strip())
                        self.base_json['closer-min-lead-away'] = int(setts[1].split(":")[0].strip())
                        self.base_json['closer-max-lead-away'] = int(setts[1].split(":")[1].strip())
            payload = json.dumps(self.base_json)
            anvil.server.call('set_lineup', self.league_name.text,
                              self.team_name.text, payload)
            self.load_positions()

    def clear_waiver_click(self, **event_args):
        anvil.server.call('clear_waiver_claims', self.league_name.text, self.team_name.text)
        self.show_add_drop_page()  # to refresh

    def add_waiver_click(self, **event_args):
        anvil.server.call('add_to_waiver_claims', self.league_name.text, self.team_name.text, self.player_name.text, self.player_name_dr.text)
        self.show_add_drop_page()  # to refresh

    def get_bench(self, **event_args):
        list, roster_size = anvil.server.call('get_bench', self.league_name.text, self.team_name.text)
        if list == "Your team hasn't started drafting yet, check current pick order by visiting Results > League Note":
            self.roster.text = list
            return
        txt = ""
        if roster_size < 0:
            self.clear_claims.visible = False
        else:
            if self.page_state == 'add-drop':
                self.clear_claims.visible = True
                self.add_claim.visible = True
            if roster_size >= 25:  # TODO find a way to import simulationConfig for this later lol
                self.add_claim.visible = False
        for elem in list:
            txt += self.get_position(elem.strip())
            txt += ": " + elem + "     "
        self.roster.text = txt

    def get_results_click(self, **event_args):
        if self.results_sel.selected_value == 'MLB Player Data':
            self.results_panel.get_components()[0].text = json.dumps(self.get_pl_data())
            return
        if self.results_sel.selected_value == 'Roster':
            self.results_panel.get_components()[0].text = anvil.server.call('getRoster', self.league_name.text, self.team_abbv.text)
            return
        results = anvil.server.call('get_results', self.league_name.text,
                                    self.team_abbv.text, self.league_week.text,
                                    self.results_sel.selected_value)
        self.results_panel.get_components()[0].text = results

    def send_chat_click(self, **event_args):
        anvil.server.call('send_chat', self.league_name.text, self.team_name.text, self.chat_msg.text)
        self.load_chat_click()

    def load_chat_click(self, **event_args):
        results = anvil.server.call('get_results', self.league_name.text, self.team_abbv.text, self.league_week.text, "Chat")
        self.chat_box.text = results

    def send_propose(self, **event_args):
        anvil.server.call('create_trade', self.league_name.text, self.team_name.text, self.propose_send.text, self.propose_rcv.text, self.trade_team_abbv.text.upper())
        self.propose_send.text = ""
        self.propose_rcv.text = ""
        self.trade_team_abbv.text = ""

    def send_accept(self, **event_args):
        anvil.server.call('approve_trade', self.league_name.text, self.team_name.text, self.trade_selector.selected_value)
        self.view_trade.text = ""
        self.load_trades()

    def send_reject(self, **event_args):
        anvil.server.call('delete_trade', self.league_name.text, self.team_name.text, self.trade_selector.selected_value)
        self.view_trade.text = ""
        self.load_trades()

    def load_trades(self, **event_args):
        self.json_trades = anvil.server.call('load_trades', self.league_name.text, self.team_name.text)
        self.trade_selector.items = self.json_trades.keys()
        if len(self.json_trades) > 0:
            for key, strn in self.json_trades.items():
                strn = "".join(strn)
                trade_obj = json.loads(strn)
                self.view_trade.text = "From: " + trade_obj['from'] + "\n"
                self.view_trade.text += "Receive:\n"
                for pl in trade_obj['receive']:
                    self.view_trade.text += pl + "\n"
                self.view_trade.text += "Send:\n"
                for pl in trade_obj['send']:
                    self.view_trade.text += pl + "\n"
                self.view_trade.text = self.view_trade.text[:-1]
                break

    def trade_selector_change(self, **event_args):
        strn = "".join(self.json_trades[self.trade_selector.selected_value])
        trade_obj = json.loads(strn)
        self.view_trade.text = "From: " + trade_obj['from'] + "\n"
        self.view_trade.text += "Receive:\n"
        for pl in trade_obj['receive']:
            self.view_trade.text += pl + "\n"
        self.view_trade.text += "Send:\n"
        for pl in trade_obj['send']:
            self.view_trade.text += pl + "\n"
        self.view_trade.text = self.view_trade.text[:-1]

    def check_pos_add_rm(self, **event_args):
        check_for = self.player_name.text
        found = False
        for player in self.get_pl_data(full=True):
            if player['fullName'].lower() == check_for.lower():
                if player['fullName'] == check_for:
                    rostered_team = anvil.server.call('get_rostered_team', self.league_name.text, check_for)
                    #print(rostered_team)
                    if rostered_team is not None and rostered_team != "":
                        self.add_drop_position.text = "Currently on team " + rostered_team
                    else:
                        self.add_drop_position.text = "Player Position: " + player['primaryPosition']['abbreviation']
                else:
                    self.add_drop_position.text = "Typo? Found similar player: " + str(player['fullName'])
                found = True
        if not found:
            self.add_drop_position.text = "Undefined Player"

    def get_pitchers(self):
        arr = []
        for pitcher in self.base_json['starters']:
            arr.append(pitcher)
        for pitcher in self.base_json['bullpen']:
            arr.append(pitcher)
        arr.append(self.base_json['fireman'])
        arr.append(self.base_json['closer'])
        batters = []
        batters.extend(self.base_json['batting-order'])
        batters.append(self.base_json['pinch-hitter'])
        batters.append(self.base_json['pinch-runner'])
        for batter in batters:
            pos = self.get_position(batter)
            if pos == "TWP":
                arr.append(batter)
        return arr

    def get_twp(self):
        arr = []
        for pitcher in self.base_json['starters']:
            arr.append(pitcher)
        for pitcher in self.base_json['bullpen']:
            arr.append(pitcher)
        for batter in self.base_json['batting-order']:
            arr.append(batter)
        arr.append(self.base_json['fireman'])
        arr.append(self.base_json['closer'])
        ret = []
        for pl in arr:
            pos = self.get_position(pl)
            if pos == "TWP" and pl not in self.base_json['batting-order']:
                ret.append(pl)
        return ret
