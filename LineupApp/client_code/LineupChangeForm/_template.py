import datetime

import anvil
from anvil import *


class LineupChangeTemplate(HtmlPanel):

    def init_components_base(self, **properties):
        super().__init__()
        self.clear()
        self.html = '@theme:standard-page.html'
        self.content_panel = GridPanel()
        self.add_component(self.content_panel)
        self.title_label = Label(text="MLB Fantasy", font_size=24)
        self.add_component(self.title_label, slot="title")

        # Navbar
        self.navbar = FlowPanel(align="right")
        self.link_lineup = Link(text="Set lineup", font_size=16)
        self.link_add = Link(text="Add/Drop", font_size=16)
        self.link_results = Link(text="League", font_size=16)
        self.link_trade = Link(text="Trade", font_size=16)
        self.link_chat = Link(text="Chat", font_size=16)
        self.navbar.add_component(self.link_lineup, slot="nav-right")
        self.navbar.add_component(self.link_add, slot="nav-right")
        self.navbar.add_component(self.link_results, slot="nav-right")
        self.navbar.add_component(self.link_trade, slot="nav-right")
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
                                   text="c1league")
        self.team_name = TextBox(placeholder="Team Code")
        self.results_sel = DropDown(
            items=["Standings", "Line scores", "Schedule", "Team totals", "League note", "Roster", "Game 1", "Game 2", "Game 3",
                   "Game 4", "Game 5", "MLB Player Data"])
        self.player_name = TextBox(placeholder="Add Player Name")
        self.player_name_dr = TextBox(placeholder="Drop Player Name")
        self.chat_msg = TextBox(placeholder="Say hi here!")
        self.league_week = TextBox(placeholder="Week", width=45)
        self.get_results = Button(text="Get Results",
                                  role="primary-color")
        self.set_lineup = Button(text="Set Lineup", role="secondary-color")
        self.clear_claims = Button(text="Clear Weekly Claims", role="secondary-color", background='#ff0000')
        self.add_claim = Button(text="Submit Claim", role="secondary-color", background='#40ff00')
        self.add_drop_position = Label(text="Undefined Player")
        self.send_chat = Button(text="Send Msg", role="secondary-color")
        self.team_abbv = TextBox(placeholder="Team", width=80)
        self.roster = TextArea(placeholder="Bench", width=300, height=100)
        self.results_panel = FlowPanel()
        self.results_panel.add_component(TextArea(placeholder="Results", height=600, width=375, font="Courier"))
        self.add_panel = FlowPanel()
        self.add_panel.add_component(self.add_drop_position)
        self.add_panel.add_component(self.player_name)
        self.add_panel.add_component(self.player_name_dr)
        self.base_json = None
        self.pl_data = None
        self.chat_box = TextArea(placeholder="Click button to load chat", width=350,
                                 height=700)
        # Trades
        self.propose_send = TextArea(placeholder="Send Players", width=145, height=300)
        self.propose_rcv = TextArea(placeholder="Receive Players", width=145, height=300)
        self.trade_team_abbv = TextBox(placeholder="Trade With", width=78)
        self.propose = Button(text="Propose Trade", role="secondary-color")
        self.propose_panel = FlowPanel()
        self.propose_panel.add_component(self.propose_send)
        self.propose_panel.add_component(self.propose_rcv)
        self.propose_panel.add_component(self.trade_team_abbv)
        self.propose_panel.add_component(self.propose)
        self.view_trade = TextArea(placeholder="Proposed Trade", width=145, height=300)
        self.trade_selector = DropDown()
        self.accept = Button(text="Accept Trade", role="secondary-color", background='#40ff00')
        self.reject = Button(text="Reject Trade", role="secondary-color", background='#ff0000')
        self.accept_panel = FlowPanel()
        self.accept_panel.add_component(self.view_trade)
        self.accept_panel.add_component(self.trade_selector)
        self.accept_panel.add_component(self.accept)
        self.accept_panel.add_component(self.reject)
        self.json_trades = {}
        self.dd_items = []

        self.txt_label = [
            "^ That's your bench. Order of players will affect the simulation results. You must have exactly one player from each position in the lineup and only one DH/TWP. Errors with positions will display at the start of these instructions. Your team code is the credential for managing your roster and lineup and anyone who has it can submit changes on your behalf so keep it hidden. The closer can only enter the game in the 9th inning or later, and the fireman will be used in a 7th+ inning situations where there are runners on base in a close game.",
            "Transactions until Thursday EST midnight will be processed as waiver claims, executing at that time. After that, all transactions until Sunday are instant. You can add or drop the blank player name \"\" to open up or fill a roster spot. Waiver claims are processed in reverse order of standings, and in order for any claim to succeed: 1. the added player must not be on any roster, 2. the dropped player must still be on your roster. Your lineup will not automatically update after a waiver claim or add/drop processes, you have to set it manually before Sunday. You can roster minor league players in the hope that they are called up to play games, but must ask for the player data to be updated to include these players in your lineup.",
            "Put in the *abbreviation* of the team whose results you want to view on this page, not the full team code that you use on the other pages. Standings, League Note, and MLB Player Data are global outputs that do not require a team or week specified.",
            "All times in the chat are UTC. Chat subject to moderation, keep it safe for work.",
            "Propose trades using the top part of the form. Put each player name on a separate line and ensure correct spelling/capitalization. Accept trades from other players using the bottom part of the form. Highlight a trade using the dropdown, then accept or reject it as desired."
        ]
        self.instr = Label(text=self.txt_label[0], font_size=18)
        self.page_state = 'lineup'
        # Pages
        self.ctl_lineup = {self.league_name, self.team_name, self.set_lineup, self.roster, self.instr}
        self.ctl_add_drop = {self.league_name, self.team_name, self.add_claim, self.clear_claims, self.roster, self.add_panel, self.instr}
        self.ctl_results = {self.league_name, self.league_week,
                            self.get_results, self.team_abbv, self.results_sel, self.results_panel, self.instr}
        self.ctl_chat = {self.league_name, self.team_name, self.chat_msg, self.send_chat, self.chat_box, self.instr}
        self.ctl_trade = {self.league_name, self.team_name, self.propose_panel, self.accept_panel, self.instr}
        self.ctl_all = self.ctl_lineup.union(self.ctl_add_drop.union(self.ctl_results.union(self.ctl_chat.union(self.ctl_trade))))
        self.ctl_all.remove(self.instr)
        self.ctl_all.add(self.instr)  # hacky since set is unordered but I always want instructions at the bottom despite appearing in multiple places
        # Add
        for component in self.ctl_all:
            self.addComponent(component)

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
        self.page_state = 'lineup'
        self.showAll(self.ctl_lineup)
        self.instr.text = self.txt_label[0]
        self.roster.placeholder = "Bench"
        if self.league_name.text != "" and self.team_name.text != "":
            self.get_bench()

    def show_add_drop_page(self, **properties):
        self.page_state = 'add-drop'
        self.showAll(self.ctl_add_drop)
        self.instr.text = self.txt_label[1]
        claims = anvil.server.call('get_waiver_claims', self.league_name.text, self.team_name.text)
        self.roster.placeholder = "Existing claims show here"
        self.roster.text = ""
        waiver_period = isWaiverPeriod()
        if waiver_period:
            self.add_claim.text = "Submit Claim"
            self.clear_claims.visible = True
        else:
            self.add_claim.text = "Add/Drop (immediate)"
            self.clear_claims.visible = False
        if claims is not None and len(claims) > 0:
            for claim in claims:
                self.roster.text += claim + "\n"

    def show_results_page(self, **properties):
        self.page_state = 'results'
        self.showAll(self.ctl_results)
        self.instr.text = self.txt_label[2]

    def show_chat_page(self, **properties):
        self.page_state = 'chat'
        self.showAll(self.ctl_chat)
        self.instr.text = self.txt_label[3]
        self.load_chat_click()

    def show_trade_page(self, **properties):
        self.page_state = 'trade'
        self.showAll(self.ctl_trade)
        self.instr.text = self.txt_label[4]
        self.load_trades()

    def hex_from_base(self, base, idx):
        inc = 11
        h = base.lstrip('#')
        codes = list(int(h[i:i + 2], 16) for i in (0, 2, 4))
        for c_idx, component in enumerate(codes):
            for i in range(0, idx):
                if codes[c_idx] < 255 - inc:
                    codes[c_idx] += inc
                else:
                    codes[c_idx] = 255
        return "#" + str(hex(codes[0]))[-2:] + str(hex(codes[1]))[-2:] + str(hex(codes[2]))[-2:]

    def define_lineup(self):
        self.lineup = FlowPanel(align="center")
        self.direct_players = []
        for i in range(1, 6):
            player = FlowPanel(align="center")
            player.add_component(Label(text="S" + str(i), width=20))
            color = self.hex_from_base('#b6efa3', i)
            component_tmp = DropDown(placeholder="Starter " + str(i), width=240, background=color, items=['A', 'B'])
            player.add_component(component_tmp)
            self.lineup.add_component(player)
            self.direct_players.append(player)
        for i in range(1, 8):
            player = FlowPanel(align="center")
            player.add_component(Label(text="R" + str(i), width=20))
            color = self.hex_from_base('#a3c9ef', i)
            player.add_component(DropDown(placeholder="Bullpen " + str(i), width=240, background=color))
            self.lineup.add_component(player)
            self.direct_players.append(player)
        player = FlowPanel(align="center")
        player.add_component(Label(text="FI"), width=20)
        player.add_component(DropDown(placeholder="Fireman", width=240, background='#64fff0'))
        self.lineup.add_component(player)
        self.direct_players.append(player)
        player = FlowPanel(align="center")
        player.add_component(Label(text="CL"), width=20)
        player.add_component(DropDown(placeholder="Closer", width=240, background='#afafff'))
        self.lineup.add_component(player)
        self.direct_players.append(player)
        for i in range(1, 10):
            player = FlowPanel(align="center")
            player.add_component(Label(text="B" + str(i), width=20))
            color = self.hex_from_base('#bf9973', i)
            player.add_component(DropDown(placeholder="Batting order " + str(i), width=240, background=color))
            self.lineup.add_component(player)
            self.direct_players.append(player)
        ph = FlowPanel(align="center")
        ph.add_component(Label(text="PH"), width=20)
        ph.add_component(DropDown(placeholder="Pinch Hitter", width=240, background='#ffafca'))
        self.lineup.add_component(ph)
        self.direct_players.append(ph)
        pr = FlowPanel(align="center")
        pr.add_component(Label(text="PR"), width=20)
        pr.add_component(DropDown(placeholder="Pinch Runner", width=240, background='#fff63d'))
        self.lineup.add_component(pr)
        self.direct_players.append(pr)
        config = FlowPanel(align="center")
        config.add_component(Label(text="Reverse bullpen order (when losing by <=N runs in the indexed inning)", width=310))
        config.add_component(TextBox(placeholder="Save Bullpen Deficit", width=310))
        self.lineup.add_component(config)
        self.direct_players.append(config)
        config = FlowPanel(align="center")
        config.add_component(Label(text="Closer enters game when lead is between (min):(max) runs", width=310))
        config.add_component(TextBox(placeholder="Closer Settings"))
        self.lineup.add_component(config)
        self.direct_players.append(config)
        self.lineup_defined = True

    def addHandlers(self):
        if hasattr(self, "team_name"):
            self.team_name.set_event_handler('change', self.load_positions)
        if hasattr(self, "league_name"):
            self.league_name.set_event_handler('change', self.load_positions)
        if hasattr(self, "player_name"):
            self.player_name.set_event_handler('change', self.check_pos_add_rm)
        if hasattr(self, "trade_selector"):
            self.trade_selector.set_event_handler('change', self.trade_selector_change)
        if hasattr(self, "set_lineup"):
            self.set_lineup.set_event_handler('click', self.set_lineup_click)
        #if hasattr(self, "lineup"):
            #for flowcomponent in self.lineup.get_components():
                #textbox = flowcomponent.get_components()[1]
                #textbox.set_event_handler('change', self.show_positions)
        if hasattr(self, "add_claim"):
            self.add_claim.set_event_handler('click', self.add_waiver_click)
        if hasattr(self, "clear_claims"):
            self.clear_claims.set_event_handler('click', self.clear_waiver_click)
        if hasattr(self, "get_results"):
            self.get_results.set_event_handler('click', self.get_results_click)
        if hasattr(self, "send_chat"):
            self.send_chat.set_event_handler('click', self.send_chat_click)
        if hasattr(self, "send_chat"):
            self.send_chat.set_event_handler('click', self.send_chat_click)
        if hasattr(self, "propose"):
            self.propose.set_event_handler('click', self.send_propose)
        if hasattr(self, "accept"):
            self.accept.set_event_handler('click', self.send_accept)
        if hasattr(self, "reject"):
            self.reject.set_event_handler('click', self.send_reject)
        # Links
        if hasattr(self, "link_lineup"):
            self.link_lineup.set_event_handler('click', self.show_lineup_page)
        if hasattr(self, "link_add"):
            self.link_add.set_event_handler('click', self.show_add_drop_page)
        if hasattr(self, "link_results"):
            self.link_results.set_event_handler('click', self.show_results_page)
        if hasattr(self, "link_chat"):
            self.link_chat.set_event_handler('click', self.show_chat_page)
        if hasattr(self, "link_trade"):
            self.link_trade.set_event_handler('click', self.show_trade_page)


def isWaiverPeriod():  # Has antipattern dupe in scheduling.py for server access
    now = datetime.datetime.now()
    if now.weekday() == 6:  # Sunday
        return True
    elif now.weekday() == 0:  # Monday
        return True
    elif now.weekday() == 1:  # Tuesday
        return True
    elif now.weekday() == 2:  # Wednesday
        return True
    else:
        return False  # Thursday Friday or Saturday