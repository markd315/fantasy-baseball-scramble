from anvil import *

class LineupChangeTemplate(HtmlPanel):

  def init_components(self, **properties):
    super().__init__()
    self.html = '@theme:standard-page.html'
    self.content_panel = GridPanel()
    self.add_component(self.content_panel)
    self.title_label = Label(text="Fantasy Lineup Setter")
    self.add_component(self.title_label, slot="title")
    self.card_1 = GridPanel(role="card")
    self.set_lineup_panel = FlowPanel(align="center")
    self.card_1.add_component(self.set_lineup_panel,
                              row="A", col_sm=2, width_sm=10)

    # Unique code for this SPA starts here
    self.league_name = TextBox(placeholder="League Name", width=400)
    self.team_name = TextBox(placeholder="Team Code", width=400)
    self.lineup_json = TextArea(placeholder="Team Lineup", width=500, height=700)
    self.get_lineup = Button(text="Get Current Lineup", role="primary-color")
    self.set_lineup = Button(text="Set Lineup", role="secondary-color")
    self.set_lineup_panel.add_component(self.league_name)
    self.set_lineup_panel.add_component(self.team_name)
    self.set_lineup_panel.add_component(self.lineup_json)
    self.set_lineup_panel.add_component(self.get_lineup)
    self.set_lineup_panel.add_component(self.set_lineup)
    self.content_panel.add_component(self.card_1, row="D", col_sm=2, width_sm=8)
