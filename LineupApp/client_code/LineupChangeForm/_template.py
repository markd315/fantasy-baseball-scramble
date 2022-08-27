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
        self.link_results = Link(text="Results")
        self.link_chat = Link(text="Chat")
        self.navbar.add_component(self.link_lineup, slot="nav-right")
        self.navbar.add_component(self.link_add, slot="nav-right")
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
            items=["Standings", "Line scores", "Team totals", "1", "2", "3",
                   "4", "5", "League note", "MLB Player Data"])
        self.player_name = TextBox(placeholder="Player Name")
        self.chat_msg = TextBox(placeholder="Say hi here!")
        self.league_week = TextBox(placeholder="Week", width=45)
        self.get_results = Button(text="Get Results",
                                  role="primary-color")
        self.get_lineup = Button(text="Show Current Positions",
                                 role="primary-color")
        self.set_lineup = Button(text="Set Lineup", role="secondary-color")
        self.get_roster = Button(text="Get Current Bench",
                                 role="primary-color")
        self.drop_lineup = Button(text="Drop Player", role="secondary-color", background='#ff0000')
        self.add_lineup = Button(text="Add Player", role="secondary-color", background='#40ff00')
        self.send_chat = Button(text="Send Msg", role="secondary-color")
        self.load_chat = Button(text="Load Chat", role="primary-color")
        self.team_abbv = TextBox(placeholder="Team", width=80)
        self.roster = TextArea(placeholder="Bench", width=350, height=100)
        self.results = TextArea(placeholder="Results", width=500, height=800,
                                font="Courier")
        self.base_json = None
        self.chat_box = TextArea(placeholder="Click button to load chat", width=350,
                                    height=700)
        self.txt_label = [
            "For the starters, lineup, and bullpen, order will affect the simulation! You must have exactly one player from each position in the lineup and only one DH/TWP. Request \"MLB Player Data\" from the results page to validate your players primary positions. Your team code is the credential for managing your roster and lineup and anyone who has it can submit changes on your behalf so keep it hidden. The closer can only enter the game in the 9th inning or later, and the fireman will be used in a 7th+ inning situations where there are runners on base in a close game.",
            "To add a new player, they cannot be on any other fantasy roster, and you must currently have <=24 players on your roster. To drop a player, they must first not appear anywhere in your lineup (ie be showing on your bench). Other teams will be able to add them immediately. Use the fullname matching a player in the \"MLB Player Data\" if you want to be able to include the player in your lineup. If the player is not visible in the lineup (like for a recent minor league callup) notify the league manager to invalidate the player name cache",
            "Put in the *abbreviation* of the team whose results you want to view on this page, not the full team code that you use on the other pages. Standings, League Note, and MLB Player Data are global settings that do not require a team or week specified."
        ]
        self.instr = Label(text=self.txt_label[0])
        self.lineup = FlowPanel(align="center")
        for i in range(1,6):
            self.lineup.add_component(Label(text="S" +str(i), width=20))
            self.lineup.add_component(TextBox(placeholder="Starter " + str(i), width=310, background='#c6ffb3'))
        for i in range(1,6):
            self.lineup.add_component(Label(text="R" + str(i), width=20))
            self.lineup.add_component(TextBox(placeholder="Bullpen " + str(i), width=310, background='#b3d9ff'))
        self.lineup.add_component(Label(text="FI"), width=20)
        self.lineup.add_component(TextBox(placeholder="Fireman", width=310, background='#ccffff'))
        self.lineup.add_component(Label(text="CL"), width=20)
        self.lineup.add_component(TextBox(placeholder="Closer", width=310, background='#6666ff'))
        for i in range(1,10):
            self.lineup.add_component(Label(text="B" + str(i), width=20))
            self.lineup.add_component(TextBox(placeholder="Batting order " + str(i), width=310, background='#ffd9b3'))

        self.lineup.add_component(Label(text="Reverse bullpen order (when losing by <=N runs in the indexed inning)", width=310))
        self.lineup.add_component(TextBox(placeholder="Save Bullpen Deficit", width=310))
        self.lineup.add_component(Label(text="Closer enters game when lead is between (min):(max) runs", width=310))
        self.lineup.add_component(TextBox(placeholder="Closer Settings"))
        # Pages
        self.ctl_lineup = {self.league_name, self.team_name, self.lineup,
                           self.get_lineup, self.set_lineup, self.instr}
        self.ctl_add_drop = {self.league_name, self.team_name, self.get_roster,
                        self.add_lineup, self.drop_lineup, self.roster, self.player_name, self.instr}
        self.ctl_results = {self.league_name, self.league_week,
                            self.get_results, self.results, self.team_abbv, self.results_sel, self.instr}
        self.ctl_chat = {self.league_name, self.team_name, self.chat_box, self.chat_msg, self.send_chat, self.load_chat}
        self.ctl_all = self.ctl_lineup.union(self.ctl_add_drop.union(self.ctl_results.union(self.ctl_chat)))

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
        self.addComponent(self.add_lineup)
        self.addComponent(self.drop_lineup)
        self.addComponent(self.roster)
        self.addComponent(self.results)
        self.addComponent(self.lineup)
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
        if self.league_name.text != "" and self.team_name.text != "":
            self.load_positions()

    def show_add_drop_page(self, **properties):
        self.showAll(self.ctl_add_drop)
        self.instr.text = self.txt_label[1]
        if self.league_name.text != "" and self.team_name.text != "":
            self.get_bench_click()

    def show_results_page(self, **properties):
        self.showAll(self.ctl_results)
        self.instr.text = self.txt_label[2]

    def show_chat_page(self, **properties):
        self.showAll(self.ctl_chat)
        self.load_chat_click()

    def addHandlers(self):
        if hasattr(self, "team_name"):
            self.team_name.set_event_handler('change', self.load_positions)
        if hasattr(self, "set_lineup"):
            self.set_lineup.set_event_handler('click', self.set_lineup_click)
        if hasattr(self, "get_lineup"):
            self.get_lineup.set_event_handler('click', self.show_positions_click)
        if hasattr(self, "get_roster"):
            self.get_roster.set_event_handler('click', self.get_bench_click)
        if hasattr(self, "add_lineup"):
            self.add_lineup.set_event_handler('click', self.add_player_click)
        if hasattr(self, "drop_lineup"):
            self.drop_lineup.set_event_handler('click', self.drop_player_click)
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
            self.link_add.set_event_handler('click', self.show_add_drop_page)
        if hasattr(self, "link_results"):
            self.link_results.set_event_handler('click', self.show_results_page)
        if hasattr(self, "link_chat"):
            self.link_chat.set_event_handler('click', self.show_chat_page)
