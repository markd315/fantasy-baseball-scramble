from anvil import *

class LineupChangeTemplate(HtmlPanel):

  def init_components_base(self, **properties):
    super().__init__()
    self.clear()
    self.html = '@theme:standard-page.html'
    self.content_panel = GridPanel()
    self.add_component(self.content_panel)
    self.title_label = Label(text="Fantasy Lineup Setter")
    self.add_component(self.title_label, slot="title")
    self.card_1 = GridPanel(role="card")
    self.main_content = FlowPanel(align="center")
    self.card_1.add_component(self.main_content,
                              row="A", col_sm=2, width_sm=10)
    self.content_panel.add_component(self.card_1, row="D", col_sm=2, width_sm=8)

    # Sidebar
    self.link_lineup = Link(text="Set Lineup")
    self.link_add = Link(text="Add to roster")
    self.link_drop = Link(text="Drop from roster")

    # Parts
    self.league_name = TextBox(placeholder="League Name", width=400,
                               text="livetestleague")
    self.team_name = TextBox(placeholder="Team Code", width=400)
    self.lineup_json = TextArea(placeholder="Team Lineup", width=500,
                                height=700)
    self.get_lineup = Button(text="Get Current Lineup", role="primary-color")
    self.set_lineup = Button(text="Set Lineup", role="secondary-color")
    self.get_roster = Button(text="Get Current Roster", role="primary-color")
    self.drop_lineup = Button(text="Drop Player", role="secondary-color")
    self.add_lineup = Button(text="Add Player", role="secondary-color")
    self.roster = TextArea(placeholder="Roster", width=500,
                           height=700)
    self.player_name = TextBox(placeholder="Player Name", width=400)

    # Rest of sidebar
    self.col = ColumnPanel()
    self.sidebar = FlowPanel(align="left")
    self.sidebar.add_component(self.col)
    self.col.add_component(self.link_lineup, slot="sidebar")
    self.col.add_component(self.link_add, slot="sidebar")
    self.col.add_component(self.link_drop, slot="sidebar")
    self.add_component(self.sidebar)

  def addComponent(self, component):
    try:
      component.remove_from_parent()
    except BaseException:
      pass
    self.main_content.add_component(component)


  def show_lineup_page(self, **properties):
    self.addComponent(self.league_name)
    self.addComponent(self.team_name)
    self.addComponent(self.lineup_json)
    self.addComponent(self.get_lineup)
    self.addComponent(self.set_lineup)
    #self.content_panel.add_component(self.card_1, row="D", col_sm=2, width_sm=8)


  def show_add_page(self, **properties):
    self.addComponent(self.league_name)
    self.addComponent(self.team_name)
    self.addComponent(self.player_name)
    self.addComponent(self.roster)
    self.addComponent(self.get_roster)
    self.addComponent(self.add_lineup)
    #self.content_panel.add_component(self.card_1, row="D", col_sm=2, width_sm=8)

  def show_drop_page(self, **properties):
    self.addComponent(self.league_name)
    self.addComponent(self.team_name)
    self.addComponent(self.player_name)
    self.addComponent(self.roster)
    self.addComponent(self.get_roster)
    self.addComponent(self.drop_lineup)
    #self.content_panel.add_component(self.card_1, row="D", col_sm=2, width_sm=8)

  def addHandlers(self):
    if hasattr(self, "set_lineup"):
      self.set_lineup.set_event_handler('click', self.set_lineup_click)
    if hasattr(self, "get_lineup"):
      self.get_lineup.set_event_handler('click', self.get_lineup_click)
    if hasattr(self, "get_roster"):
      self.get_roster.set_event_handler('click', self.get_roster_click)
    if hasattr(self, "add_lineup"):
      self.add_lineup.set_event_handler('click', self.add_lineup_click)
    if hasattr(self, "drop_lineup"):
      self.drop_lineup.set_event_handler('click', self.drop_lineup_click)

    if hasattr(self, "link_lineup"):
      self.link_lineup.set_event_handler('click', self.show_lineup_page)
    if hasattr(self, "link_add"):
      self.link_add.set_event_handler('click', self.show_add_page)
    if hasattr(self, "link_drop"):
      self.link_drop.set_event_handler('click', self.show_drop_page)