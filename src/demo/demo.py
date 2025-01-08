import random

from ollama import chat
from ollama import ChatResponse
from textual import work
from textual.app import App, ComposeResult
from textual.message import Message
from textual.widgets import Footer, Header, Button, Label, RichLog, Markdown, OptionList, LoadingIndicator
from textual.containers import Grid, HorizontalGroup, VerticalScroll
from textual.reactive import reactive

import re
import sys
sys.path.append("../")

from constants import Types
from main import genetic_algorithm

dungeon = genetic_algorithm()
und_dungeon = dungeon.to_undirected()

class TopLeftPanel(HorizontalGroup):
    keys = reactive(0)
    health = reactive(20)
    rupees = reactive(0)
    map_found = reactive(False)

    def compose(self):
        yield VerticalScroll(
            Label(f"🗝  0"),
            Label(f"❤  20"),
            Label(f"💎 0"),
            Label(f"🗺  False"),
            Button("Show map >", id="show-map", variant="primary", disabled=True),
        classes="panel", id="statistics")

    async def update_statistics(self, keys, health, rupees, map_found):
        container = self.query_one(VerticalScroll)
        await container.remove_children(selector='*')

        await container.mount(
            Label(f"🗝  {keys}"),
            Label(f"❤  {health}"),
            Label(f"💎 {rupees}"),
            Label(f"🗺  {'yes' if map_found else 'no'}"),
            Button("Show map >", id="show-map", variant="primary", disabled=not map_found)
        )

    def on_button_pressed(self, event):
        self.open_map()

    @work(thread=True)
    def open_map(self):
        dungeon.print()

    def on_mount(self):
        container = self.query_one(VerticalScroll)
        container.border_title = "Statistics"

    async def watch_keys(self, new_keys):
        await self.update_statistics(new_keys, self.health, self.rupees, self.map_found)

    async def watch_health(self, new_health):
        await self.update_statistics(self.keys, new_health, self.rupees, self.map_found)

    async def watch_rupees(self, new_rupees):
        await self.update_statistics(self.keys, self.health, new_rupees, self.map_found)

    async def watch_map_found(self, new_map_found):
        await self.update_statistics(self.keys, self.health, self.rupees, new_map_found)

class TopRightPanel(HorizontalGroup):
    class PickedActionMessage(Message):
        def __init__(self, pick):
            self.pick = pick
            super().__init__()

    doing = reactive("main")
    choices = reactive([])

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label("Waiting for narrative..."),
            classes="panel", id="actions_panel")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "Actions"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if self.doing == "action":
            option_list = self.query_one(OptionList)

            self.post_message(TopRightPanel.PickedActionMessage(option_list.highlighted))

    async def watch_doing(self, new_doing):
        container = self.query_one(VerticalScroll)
        await container.remove_children(selector='*')

        if new_doing == "action":
            await container.mount(
                Label("What path do you want to take?"),
                OptionList(*self.choices, id="actions"),
                Button("Pick >", id="confirm", variant="success")
            )
        else:
            await container.mount(Label("Waiting for narrative..."))

class BottomLeftPanel(HorizontalGroup):
    class AnswerMessage(Message):
        def __init__(self, answer):
            self.answer = answer
            super().__init__()

    class UpdateUIMessage(Message):
        def __init__(self, thinking, answer):
            self.thinking = thinking
            self.answer = answer
            super().__init__()

    messages_until_now = []

    doing = reactive("main")
    llm_query = reactive("")

    thinking = reactive(False)
    answer = reactive("Waiting for an input...")

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Markdown(self.answer, classes="textual_output", id="llm_output"),
        classes="panel", id="narrative")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "Narrative"

    def on_bottom_left_panel_update_uimessage(self, message: UpdateUIMessage) -> None:
        container = self.query_one(VerticalScroll)
        container.remove_children(selector='*')

        if message.thinking:
            container.mount(LoadingIndicator())
        else:
            container.mount(Markdown(message.answer, classes="textual_output", id="llm_output"))

    @work(thread=True)
    def send_llm_message(self, message):
        self.thinking = True

        self.post_message(self.UpdateUIMessage(self.thinking, self.answer))

        self.messages_until_now.append({
            'role': 'user',
            'content': message,
        })

        response: ChatResponse = chat(model='llama3.2', messages=self.messages_until_now)

        self.messages_until_now.append({
            'role': 'assistant',
            'content': response['message']['content']
        })

        self.answer = "\n".join(response['message']['content'].splitlines()[:-2])

        self.thinking = False

        self.post_message(self.UpdateUIMessage(self.thinking, self.answer))

        self.post_message(self.AnswerMessage(response['message']['content']))

    def watch_llm_query(self, new_llm_query):
        if self.doing == "llm":
            self.send_llm_message(new_llm_query)

class BottomRightPanel(HorizontalGroup):
    path = reactive([])
    explored_key_rooms = reactive([])

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            RichLog(highlight=True, markup=True, classes="textual_output"),
        classes="panel", id="logs")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "History"

    def watch_path(self, old_path, new_path) -> None:
        if len(new_path) > 0:
            log = self.query_one(RichLog)

            attachment = ""

            if und_dungeon.nodes[new_path[-1]]['type'] == Types.START:
                attachment = " Adventure begins!"
            elif und_dungeon.nodes[new_path[-1]]['type'] == Types.FINISH:
                attachment = " You won!"
            elif und_dungeon.nodes[new_path[-1]]['type'] == Types.KEY and new_path[-1] not in self.explored_key_rooms:
                attachment = " You found a key."

            log.write(f"You are in Room {new_path[-1]}.{attachment}")

class DemoZeldagen(App):
    doing = reactive("main")
    llm_query = reactive("")
    choices = reactive([])

    path = reactive([0])
    keys = reactive(0)
    health = reactive(20)
    rupees = reactive(0)
    map_found = reactive(False)

    explored_key_rooms = reactive([])
    unlocked_edges = reactive([])

    CSS_PATH = "demo_styles.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def construct_choices(self):
        choices = []

        for node in und_dungeon.neighbors(self.path[-1]):
            if und_dungeon.edges[self.path[-1], node]['locked']:
                if (self.path[-1], node) in self.unlocked_edges:
                    choices.append(f"Room {node} (unlocked)")
                else:
                    choices.append(f"Room {node} (locked)")
            else:
                choices.append(f"Room {node}")

        return choices

    def construct_llm_prompt(self):
        return f"""
        We are exploring a Zelda-like dungeon.
        You'll have to describe me each room I'm in.
        
        Rooms can be of four types: initial room (always room 0), final room (always room 9), key room (where I find treasures containing keys), normal room (where I find enemies and treasures that are not keys, such as rupees).
        
        I will tell you each time what room I'm in, what rooms I can reach from here, and how much health I have (out of a max of 20).
        You'll give me a brief narrative description of the room, in Zelda style: you can use enemies and concepts of the Zelda saga.
        The description has to be in a simple language, and not be too dark, it has to match the Zelda dungeon atmosphere.
        
        I will tell you the rooms I already explored before, so if I return to them adjust the description accordingly.
        If you notice I'm at a dead end and can only return back to the room I came from, tell so.
        
        When I find a key room, you'll have to describe how I found the key. Keys are not rare artifacts or magical, just simple keys.
        
        In normal rooms, I can find rupees, hearts or enemies. When I enter a normal room for the first time, you'll have to describe what I found.
        If it's an enemy, you'll have to describe very briefly my fight (use classical Link weapons, like sword, bow and bombs). Keep in mind I can't find boss enemies in normal rooms, only simple or elite enemies. Do not repeat the same enemies too often.
        If it's rupees or hearts, you'll have to describe that I found them.
        All fights and discoveries must be self-contained in one message, do not wait for my reply because each message I send will only be movement to a new room.
        
        Then, at the end of your message, you'll have to tell me exactly how much health I lost and how much rupees I gained. Remember that I can't go over 20 health (it's the maximum).
        It has to be at the very end of your message, as the last two lines. You'll have to write a string, "health" or "rupee", then a space, and then the value I lost or gained as a single integer.
        
        For example:
        "
        Brief description
        
        health -5
        rupees 0
        "
        
        You'll have to be exact about the format of the last two lines. Don't write like this: "20/20", instead write just an integer "2", "-4", etc.
        "health" or "rupees" have to be written exactly like that, do not add any punctuation or capitalization. The order is important, you must write the "health" line before the "rupees" line.
        If I didn't lose health or gain rupees, you can just write "health 0" or "rupees 0".
        
        Do not add notes, questions or anything else after the last two lines.
        
        When I reach the final room (room 9), there will be a boss fight. Again you will tell me how much health I lost, and I will win if I didn't die in the boss fight.
        I will lose if my health goes below 0. If I died and got a game over, add it to the narrative too.
        
        Remember: you don't have to tell me how much health I have NOW. You only have to tell me how much health I gained or lost in the last room.
        Also, don't tell me I've found keys when I'm not in a key room.
        
        My prompt will follow.
        
        ------------------
        
        Now, I am in room {self.path[-1]}, and it is a {und_dungeon.nodes[self.path[-1]]['type']} room.
        {"I have never explored this room." if self.path[-1] in self.path[:-1] else "I have already explored this room before."}
        I see doors to rooms: {[n for n in und_dungeon.neighbors(self.path[-1])]}.
        I have {self.health} hearts.
        """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Grid(
        TopLeftPanel().data_bind(keys=DemoZeldagen.keys, health=DemoZeldagen.health, rupees=DemoZeldagen.rupees, map_found=DemoZeldagen.map_found),
               TopRightPanel().data_bind(doing=DemoZeldagen.doing, choices=DemoZeldagen.choices),
               BottomLeftPanel().data_bind(doing=DemoZeldagen.doing, llm_query=DemoZeldagen.llm_query),
               BottomRightPanel().data_bind(path=DemoZeldagen.path, explored_key_rooms=DemoZeldagen.explored_key_rooms),
           classes="main")
        yield Footer()

    def on_bottom_left_panel_answer_message(self, message: BottomLeftPanel.AnswerMessage) -> None:
        print("Received", message.answer)

        health_line = message.answer.splitlines()[-2]
        rupees_line = message.answer.splitlines()[-1]

        health_value = int(health_line.split(" ")[-1])
        rupees_value = int(rupees_line.split(" ")[-1])

        self.health += int(health_value)
        if self.health > 20:
            self.health = 20

        self.rupees += int(rupees_value)

        if self.health <= 0:
            self.notify("You died.", title="Game over!", severity="error")
            self.doing = "finished"
            return

        if und_dungeon.nodes[self.path[-1]]['type'] == Types.FINISH:
            self.notify("You reached the final room and beat the boss! Congratulations.", title="You won!", severity="information")
            self.doing = "finished"
            return

        self.choices = self.construct_choices()
        self.mutate_reactive(DemoZeldagen.choices)
        self.doing = "action"

    def on_top_right_panel_picked_action_message(self, message: TopRightPanel.PickedActionMessage) -> None:
        room_to_go = int(re.sub('[^-\d]', '', self.choices[message.pick]))

        if und_dungeon.edges[self.path[-1], room_to_go]['locked']:
            if (self.path[-1], room_to_go) not in self.unlocked_edges:
                if self.keys > 0:
                    self.keys -= 1
                    self.unlocked_edges.append((self.path[-1], room_to_go))
                    self.unlocked_edges.append((room_to_go, self.path[-1]))
                else:
                    self.notify("The door is locked, and you don't have any key.", title="Stop!", severity="error")
                    return

        self.path.append(room_to_go)
        self.mutate_reactive(DemoZeldagen.path)

        if und_dungeon.nodes[room_to_go]['type'] == Types.KEY:
            if room_to_go not in self.explored_key_rooms:
                self.keys += 1
                self.explored_key_rooms.append(room_to_go)
        elif und_dungeon.nodes[room_to_go]['type'] == Types.NORMAL:
            if random.randint(0, 100) < 25 and not self.map_found:
                self.notify("You found the map of the dungeon!", severity="information")
                self.map_found = True

        self.doing = "llm"
        self.llm_query = self.construct_llm_prompt()

    def on_ready(self):
        self.doing = "llm"
        self.llm_query = self.construct_llm_prompt()

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")

if __name__ == "__main__":
    app = DemoZeldagen()
    app.run()