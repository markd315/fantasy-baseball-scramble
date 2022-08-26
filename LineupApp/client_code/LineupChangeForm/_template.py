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

        # Sidebar
        self.navbar = FlowPanel(align="right")
        self.link_lineup = Link(text="Set lineup")
        self.link_add = Link(text="Roster add")
        self.link_drop = Link(text="Roster drop")
        self.link_results = Link(text="Results")
        self.link_chat = Link(text="Chat")
        self.navbar.add_component(self.link_lineup, slot="nav-right")
        self.navbar.add_component(self.link_add, slot="nav-right")
        self.navbar.add_component(self.link_drop, slot="nav-right")
        self.navbar.add_component(self.link_results, slot="nav-right")
        self.navbar.add_component(self.link_chat, slot="nav-right")
        self.add_component(self.navbar, slot='nav-right')

        self.card_1 = GridPanel(role="card")
        self.main_content = FlowPanel(align="center")
        self.card_1.add_component(self.main_content,
                                  row="A", col_sm=2, width_sm=10)
        self.content_panel.add_component(self.card_1, row="D", col_sm=2,
                                         width_sm=8)

        # Parts
        self.league_name = TextBox(placeholder="League Name",
                                   text="livetestleague")
        self.team_name = TextBox(placeholder="Team Code")
        self.results_sel = DropDown(
            items=["Line scores", "Team totals", "Standings", "1", "2", "3",
                   "4", "5", "League note", "MLB Player Data"])
        self.player_name = TextBox(placeholder="Player Name")
        self.chat_msg = TextBox(placeholder="Say hi here!")
        self.league_week = TextBox(placeholder="Week", width=45)
        self.get_results = Button(text="Get Results",
                                  role="primary-color")
        self.get_lineup = Button(text="Get Current Lineup",
                                 role="primary-color")
        self.set_lineup = Button(text="Set Lineup", role="secondary-color")
        self.get_roster = Button(text="Get Current Roster",
                                 role="primary-color")
        self.drop_lineup = Button(text="Drop Player", role="secondary-color")
        self.add_lineup = Button(text="Add Player", role="secondary-color")
        self.send_chat = Button(text="Send Msg", role="secondary-color")
        self.load_chat = Button(text="Load Chat", role="primary-color")
        self.team_abbv = TextBox(placeholder="Team", width=80)
        self.roster = TextArea(placeholder="Roster", width=350, height=700)
        self.results = TextArea(placeholder="Results", width=350, height=700,
                                font="Courier")
        self.lineup_json = TextArea(placeholder="Team Lineup", width=350, height=700)
        self.chat_box = TextArea(placeholder="Click button to load chat", width=350,
                                    height=700)
        self.txt_label = [
            "You must submit your adjusted lineup in the JSON format. I suggest putting in your team code and then getting the current JSON first, then making small changes before submitting to avoid mistakes. For the starters, lineup, and bullpen arrays, order will affect the simulation! You must have one player from each position in the lineup and only one DH. Request \"MLB Player Data\" from the results page to validate your players primary positions. Your team code is the credential for managing your roster and lineup. Anyone who has it can submit changes on your behalf so keep it hidden.",
            "The closer can only enter the game in the 9th inning or later. "
            "To add a new player, they cannot be on any other fantasy roster, and you must currently have <=24 players on your roster. Use the fullname matching a player in the \"MLB Player Data\" if you want to be able to include the player in your lineup. For callups after August 20th, notify the league manager to have the player cache invalidated.",
            "To drop a player, they must first not appear anywhere in your lineup. Other teams will be able to add them immediately.",
            "Put in the abbreviation of the team whose results you want to view on this page, not the full team code that you use on the other pages. Standings, League Note, and MLB Player Data are global settings that do not require a team or week specified."
        ]
        self.instr = Label(text=self.txt_label[0])
        self.lineup = FlowPanel(align="center")
        self.main_content.add_component(self.lineup)
        for i in range(1,6):
            self.lineup.add_component(TextBox(placeholder="Starter " + str(i)))
        for i in range(1,7):
            self.lineup.add_component(TextBox(placeholder="Bullpen " + str(i)))
        for i in range(1,10):
            self.lineup.add_component(TextBox(placeholder="Batting order " + str(i)))
        self.lineup.add_component(TextBox(placeholder="Closer"))
        self.lineup.add_component(TextBox(placeholder="Fireman"))
        self.lineup.add_component(TextBox(placeholder="Blowout Pitcher Settings"))
        self.lineup.add_component(TextBox(placeholder="Use Closer Settings"))
        #print(self.lineup.children)
        # Pages
        self.ctl_lineup = {self.league_name, self.team_name, self.lineup,
                           self.get_lineup, self.set_lineup, self.instr}
        self.ctl_add = {self.league_name, self.team_name, self.get_roster,
                        self.add_lineup, self.roster, self.player_name, self.instr}
        self.ctl_drop = {self.league_name, self.team_name, self.get_roster,
                         self.drop_lineup, self.roster, self.player_name, self.instr}
        self.ctl_results = {self.league_name, self.league_week,
                            self.get_results, self.results, self.team_abbv, self.results_sel, self.instr}
        self.ctl_chat = {self.league_name, self.team_name, self.chat_box, self.chat_msg, self.send_chat, self.load_chat}
        self.ctl_all = self.ctl_lineup.union(
            self.ctl_add.union(self.ctl_drop.union(self.ctl_results.union(self.ctl_chat))))


        # Add
        self.addComponent(self.league_name)
        self.addComponent(self.team_name)
        self.addComponent(self.player_name)
        self.addComponent(self.league_week)
        self.addComponent(self.results_sel)
        self.addComponent(self.team_abbv)
        self.addComponent(self.get_results)
        self.addComponent(self.get_lineup)
        self.addComponent(self.set_lineup)
        self.addComponent(self.get_roster)
        self.addComponent(self.drop_lineup)
        self.addComponent(self.add_lineup)
        self.addComponent(self.roster)
        self.addComponent(self.results)
        self.addComponent(self.lineup_json)
        self.addComponent(self.instr)
        self.addComponent(self.chat_box)
        self.addComponent(self.chat_msg)
        self.addComponent(self.load_chat)
        self.addComponent(self.send_chat)

    def showAll(self, components):
        for component in self.ctl_all:
            component.visible = False
        for component in components:
            component.visible = True

    def addComponent(self, component):
        try:
            component.remove_from_parent()
        except BaseException:
            pass
        component.visible = True
        self.main_content.add_component(component)

    def show_lineup_page(self, **properties):
        self.showAll(self.ctl_lineup)
        self.instr.text = self.txt_label[0]

    def show_add_page(self, **properties):
        self.showAll(self.ctl_add)
        self.instr.text = self.txt_label[1]

    def show_drop_page(self, **properties):
        self.showAll(self.ctl_drop)
        self.instr.text = self.txt_label[2]

    def show_results_page(self, **properties):
        self.showAll(self.ctl_results)
        self.instr.text = self.txt_label[3]

    def show_chat_page(self, **properties):
        self.showAll(self.ctl_chat)

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
        if hasattr(self, "get_results"):
            self.get_results.set_event_handler('click', self.get_results_click)
        if hasattr(self, "send_chat"):
            self.send_chat.set_event_handler('click', self.send_chat_click)
        if hasattr(self, "load_chat"):
            self.load_chat.set_event_handler('click', self.load_chat_click)
        # Links
        if hasattr(self, "link_lineup"):
            self.link_lineup.set_event_handler('click', self.show_lineup_page)
        if hasattr(self, "link_add"):
            self.link_add.set_event_handler('click', self.show_add_page)
        if hasattr(self, "link_drop"):
            self.link_drop.set_event_handler('click', self.show_drop_page)
        if hasattr(self, "link_results"):
            self.link_results.set_event_handler('click', self.show_results_page)
        if hasattr(self, "link_chat"):
            self.link_chat.set_event_handler('click', self.show_chat_page)
