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

    def show_positions_click(self, **event_args):
        json_str = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
        payload = json.loads(json_str)
        self.load_positions()  # Separate for later when use the button to refresh positions only.
        pl_data = json.loads(anvil.server.call('get_results', self.league_name.text, payload['abbv'], 0, 'MLB Player Data'))
        for idx, component in enumerate(self.lineup.get_components()):
            if hasattr(component, "placeholder"):
                if "Batting" in component.placeholder:
                    label = self.lineup.get_components()[idx - 1]
                    label.text = self.get_position(component.text, pl_data)


    def load_positions(self, **event_args):
        json_str = anvil.server.call('get_lineup', self.league_name.text,
                                 self.team_name.text)
        if json_str == "":  # user still typing name, maybe this makes it easy to bruteforce though
            return
        payload = json.loads(json_str)
        if self.team_abbv.text == "": # May as well add this so the user doesn't need to type it.
            self.team_abbv.text = payload['abbv']
        self.base_json = payload
        pl_data = json.loads(anvil.server.call('get_results', self.league_name.text, payload['abbv'], 0, 'MLB Player Data'))
        for idx, component in enumerate(self.lineup.get_components()):
            if hasattr(component, "placeholder"):
                if "Starter" in component.placeholder and len(payload['starters']) > 0:
                    component.text = payload['starters'].pop(0)
                if "Bullpen" in component.placeholder and len(payload['bullpen']) > 0:
                    component.text = payload['bullpen'].pop(0)
                if "Batting" in component.placeholder and len(payload['batting-order']) > 0:
                    component.text = payload['batting-order'].pop(0)
                    label = self.lineup.get_components()[idx - 1]
                    label.text = self.get_position(component.text, pl_data)
                if "Closer" == component.placeholder:
                    component.text = payload['closer']
                if "Fireman" in component.placeholder:
                    component.text = payload['fireman']
                if "Save Bullpen Deficit" in component.placeholder:
                    component.text = payload['blowout-deficit-by-inning']
                if "Closer Settings" in component.placeholder:
                    res = "Home: " + str(payload['closer-min-lead-home']) + ":" + str(payload["closer-max-lead-home"]) + ", Away: " + str(payload['closer-min-lead-away']) + ":" + str(payload["closer-max-lead-away"])
                    component.text = res

    def set_lineup_click(self, **event_args):
        if self.league_name.text and self.team_name.text:
            self.base_json['starters'] = []
            self.base_json['bullpen'] = []
            self.base_json['batting-order'] = []
            for component in self.lineup.get_components():
                if hasattr(component, "placeholder"):
                    if "Starter" in component.placeholder and len(component.text) > 0:
                        self.base_json['starters'].append(component.text)
                    if "Bullpen" in component.placeholder and len(component.text) > 0:
                        try:
                            int(component.placeholder[-1])  # To exclude Save Bullpen deficit
                            self.base_json['bullpen'].append(component.text)
                        except BaseException:
                            pass
                    if "Batting" in component.placeholder and len(component.text) > 0:
                        self.base_json['batting-order'].append(component.text)
                    if "Closer" == component.placeholder and len(component.text) > 0:
                        self.base_json['closer'] = component.text
                    if "Fireman" == component.placeholder and len(component.text) > 0:
                        self.base_json['fireman'] = component.text
                    if "Save Bullpen Deficit" in component.placeholder and len(component.text) > 0:
                        self.base_json['blowout-deficit-by-inning'] = json.loads(component.text)
                    if "Closer Settings" in component.placeholder:
                        txt = component.text
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
        self.roster.text = list

    def get_results_click(self, **event_args):
        results = anvil.server.call('get_results', self.league_name.text,
                                    self.team_abbv.text, self.league_week.text,
                                    self.results_sel.selected_value)
        self.results.text = results

    def send_chat_click(self, **event_args):
        anvil.server.call('send_chat', self.league_name.text,
                          self.team_name.text, self.chat_msg.text)
        self.load_chat_click()

    def load_chat_click(self, **event_args):
        results = anvil.server.call('get_results', self.league_name.text,
                                    self.team_abbv.text, self.league_week.text,
                                    "Chat")
        self.chat_box.text = results
