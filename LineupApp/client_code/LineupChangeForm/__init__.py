import json

from _template import LineupChangeTemplate
import anvil.server


class LineupChangeForm(LineupChangeTemplate):

    def __init__(self, **properties):
        self.init_components_base(**properties)
        self.show_lineup_page()
        self.addHandlers()

    def get_position(self, name, pl_data):
        pos = 'UN'
        for pl in pl_data:
            if pl['fullName'] == name:
                pos = pl['primaryPosition']['abbreviation']
        return pos

    def get_pl_data(self):
        if self.pl_data == None:
            self.pl_data = anvil.server.call('get_results', self.league_name.text, '', 0, 'MLB Player Data')
        return self.pl_data


    def show_positions(self, **event_args):
        used = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        friendly = ['DH', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']
        self.instr.text = self.txt_label[0]
        for idx, flowcomponent in enumerate(self.lineup.get_components()):
            label = flowcomponent.get_components()[0]
            component = flowcomponent.get_components()[1]
            if "Batting" in component.placeholder:
                label.text = self.get_position(component.text, json.loads(self.get_pl_data()))
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


    def load_positions(self, **event_args):
        json_str = anvil.server.call('get_lineup', self.league_name.text,
                                 self.team_name.text)
        if json_str == "":  # user still typing name, maybe this makes it easy to bruteforce though
            return
        payload = json.loads(json_str)
        if self.team_abbv.text == "":  # May as well add this so the user doesn't need to type it.
            self.team_abbv.text = payload['abbv']
        self.base_json = payload
        for idx, flowcomponent in enumerate(self.lineup.get_components()):
            textbox = flowcomponent.get_components()[1]
            label = flowcomponent.get_components()[0]
            if hasattr(textbox, "placeholder"):
                if "Starter" in textbox.placeholder and len(payload['starters']) > 0:
                    textbox.text = payload['starters'].pop(0)
                if "Bullpen" in textbox.placeholder and len(payload['bullpen']) > 0:
                    textbox.text = payload['bullpen'].pop(0)
                if "Batting" in textbox.placeholder and len(payload['batting-order']) > 0:
                    textbox.text = payload['batting-order'].pop(0)
                    label.text = self.get_position(textbox.text, json.loads(self.get_pl_data()))
                if "Closer" == textbox.placeholder:
                    textbox.text = payload['closer']
                if "Fireman" in textbox.placeholder:
                    textbox.text = payload['fireman']
                if "Save Bullpen Deficit" in textbox.placeholder:
                    textbox.text = payload['blowout-deficit-by-inning']
                if "Closer Settings" in textbox.placeholder:
                    res = "Home: " + str(payload['closer-min-lead-home']) + ":" + str(payload["closer-max-lead-home"]) + ", Away: " + str(payload['closer-min-lead-away']) + ":" + str(payload["closer-max-lead-away"])
                    textbox.text = res
        self.get_bench_click()

    def set_lineup_click(self, **event_args):
        self.show_positions()
        if "TOO MANY " in self.instr.text or "NEED A " in self.instr.text:  # Invalid, now the user will know
            return
        if self.league_name.text and self.team_name.text:
            self.base_json['starters'] = []
            self.base_json['bullpen'] = []
            self.base_json['batting-order'] = []
            for flowcomponent in self.lineup.get_components():
                textbox = flowcomponent.get_components()[1]
                if hasattr(textbox, "placeholder"):
                    if "Starter" in textbox.placeholder and len(textbox.text) > 0:
                        self.base_json['starters'].append(textbox.text)
                    if "Bullpen" in textbox.placeholder and len(textbox.text) > 0:
                        try:
                            int(textbox.placeholder[-1])  # To exclude Save Bullpen deficit
                            self.base_json['bullpen'].append(textbox.text)
                        except BaseException:
                            pass
                    if "Batting" in textbox.placeholder and len(textbox.text) > 0:
                        self.base_json['batting-order'].append(textbox.text)
                    if "Closer" == textbox.placeholder and len(textbox.text) > 0:
                        self.base_json['closer'] = textbox.text
                    if "Fireman" == textbox.placeholder and len(textbox.text) > 0:
                        self.base_json['fireman'] = textbox.text
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

    def drop_player_click(self, **event_args):
        anvil.server.call('drop_player', self.league_name.text,
                          self.team_name.text, self.player_name.text)
        self.get_bench_click()

    def add_player_click(self, **event_args):
        anvil.server.call('add_player', self.league_name.text,
                          self.team_name.text, self.player_name.text)
        self.get_bench_click()

    def get_bench_click(self, **event_args):
        list = anvil.server.call('get_bench', self.league_name.text,
                                 self.team_name.text)
        txt = ""
        for elem in list:
            txt += self.get_position(elem.strip(), json.loads(self.get_pl_data()))
            txt += ": " + elem + "     "
        self.roster.text = txt

    def get_results_click(self, **event_args):
        if self.results_sel.selected_value == 'MLB Player Data':
            self.results_panel.get_components()[0].text = self.get_pl_data()
            return
        results = anvil.server.call('get_results', self.league_name.text,
                                    self.team_abbv.text, self.league_week.text,
                                    self.results_sel.selected_value)
        self.results_panel.get_components()[0].text = results

    def send_chat_click(self, **event_args):
        anvil.server.call('send_chat', self.league_name.text,
                          self.team_name.text, self.chat_msg.text)
        self.load_chat_click()

    def load_chat_click(self, **event_args):
        results = anvil.server.call('get_results', self.league_name.text,
                                    self.team_abbv.text, self.league_week.text,
                                    "Chat")
        self.chat_box.text = results
