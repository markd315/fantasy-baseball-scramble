from _template import LineupChangeTemplate
import anvil.server


class LineupChangeForm(LineupChangeTemplate):

  def __init__(self, **properties):
    self.init_components_lineup(**properties)
    self.set_lineup.set_event_handler('click', self.set_lineup_click)
    #self.lineup_json.set_event_handler('pressed_enter', self.set_lineup_click)  # only works for textBox I guess?
    self.set_lineup.set_event_handler('click', self.set_lineup_click)
    self.get_lineup.set_event_handler('click', self.get_lineup_click)
    self.get_roster.set_event_handler('click', self.get_roster_click)
    self.add_lineup.set_event_handler('click', self.add_lineup_click)
    self.drop_lineup.set_event_handler('click', self.drop_lineup_click)

    self.link_lineup.set_event_handler('click', self.init_components_lineup)
    self.link_add.set_event_handler('click', self.init_components_add)
    self.link_drop.set_event_handler('click', self.init_components_drop)

  
  def get_lineup_click(self, **event_args):
    json = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
    self.lineup_json.text = json


  def set_lineup_click(self, **event_args):
    if self.league_name.text and self.team_name.text:
      anvil.server.call('set_lineup', self.league_name.text, self.team_name.text, self.lineup_json.text)

  def drop_lineup_click(self, **event_args):
    json = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
    self.lineup_json.text = json

  def add_lineup_click(self, **event_args):
    json = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
    self.lineup_json.text = json

  def get_roster_click(self, **event_args):
    list = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
    self.roster.text = list