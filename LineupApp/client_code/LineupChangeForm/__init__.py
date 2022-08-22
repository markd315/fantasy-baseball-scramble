from _template import LineupChangeTemplate
import anvil.server


class LineupChangeForm(LineupChangeTemplate):

  def __init__(self, **properties):
    self.init_components(**properties)
    self.set_lineup.set_event_handler('click', self.set_lineup_click)
    #self.lineup_json.set_event_handler('pressed_enter', self.set_lineup_click)  # only works for textBox I guess?
    self.set_lineup.set_event_handler('click', self.set_lineup_click)
    self.get_lineup.set_event_handler('click', self.get_lineup_click)

  
  def get_lineup_click(self, **event_args):
    json = anvil.server.call('get_lineup', self.league_name.text, self.team_name.text)
    self.lineup_json.text = json


  def set_lineup_click(self, **event_args):
    if self.league_name.text and self.team_name.text:
      anvil.server.call('set_lineup', self.league_name.text, self.team_name.text, self.lineup_json.text)





