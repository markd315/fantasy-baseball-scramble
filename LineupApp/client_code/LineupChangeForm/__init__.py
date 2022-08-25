from _template import LineupChangeTemplate
import anvil.server


class LineupChangeForm(LineupChangeTemplate):

  def __init__(self, **properties):
    self.init_components_base(**properties)
    self.show_lineup_page()
    self.addHandlers()

  
  def get_lineup_click(self, **event_args):
    json = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
    self.lineup_json.text = json


  def set_lineup_click(self, **event_args):
    if self.league_name.text and self.team_name.text:
      anvil.server.call('set_lineup', self.league_name.text, self.team_name.text, self.lineup_json.text)

  def drop_lineup_click(self, **event_args):
    anvil.server.call('drop_player', self.league_name.text, self.team_name.text, self.player_name.text)

  def add_lineup_click(self, **event_args):
    anvil.server.call('add_player', self.league_name.text, self.team_name.text, self.player_name.text)

  def get_roster_click(self, **event_args):
    list = anvil.server.call('get_roster', self.league_name.text, self.team_name.text)
    self.roster.text = list