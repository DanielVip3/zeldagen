from ollama import chat
from ollama import ChatResponse
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button, Label, RichLog, Markdown, OptionList
from textual.containers import Grid, HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from constants import Types
from main import genetic_algorithm

dungeon = genetic_algorithm()
dungeon.print()

und_dungeon = dungeon.to_undirected()

# top-top-left: title, then down a button to generate a dungeon and a select for difficulty
# top-left: statistics (keys, health, rupees, map etc.) + button to view graph enabled only if has a map
# top-right: room choice picker
# bottom-left: ai description
# bottom-right: history (with colors for damage etc.)

messages_until_now = []
def send(message):
    messages_until_now.append({
        'role': 'user',
        'content': message,
    })

    response: ChatResponse = chat(model='llama3.2', messages=messages_until_now)

    messages_until_now.append({
        'role': 'assistant',
        'content': response['message']['content']
    })

    return response['message']['content']

class TopLeftPanel(HorizontalGroup):
    keys = reactive(0, recompose=True)
    health = reactive(20, recompose=True)
    rupees = reactive(0, recompose=True)
    map_found = reactive(False, recompose=True)

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label(f"Keys: {self.keys}"),
            Label(f"Health: {self.health}"),
            Label(f"Rupees: {self.rupees}"),
            Label(f"Map: {self.map_found}"),
        classes="panel statistics")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "Statistics"

class TopRightPanel(HorizontalGroup):
    pick = None
    choices = reactive(["Room 3", "Room 6"], recompose=True)

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label("What action do you want to take?"),
            OptionList(*self.choices),
            Button(">", id="confirm", variant="success"),
        classes="panel")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "Actions"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        option_list = self.query_one(OptionList)
        self.pick = option_list.highlighted

class BottomLeftPanel(HorizontalGroup):
    text = "This is a test output from the LLM."

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Markdown(self.text, classes="textual_output"),
        classes="panel")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "Narrative"

class BottomRightPanel(HorizontalGroup):
    text = "You are in Room 0."

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            RichLog(highlight=True, markup=True, classes="textual_output"),
        classes="panel")

    def on_mount(self) -> None:
        container = self.query_one(VerticalScroll)
        container.border_title = "History"

    def on_ready(self):
        log = self.query_one(RichLog)

        log.write(self.text)

class Box(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Button("Start", id="start", variant="success")

class DemoZeldagen(App):
    CSS_PATH = "demo_styles.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Grid(TopLeftPanel(), TopRightPanel(), BottomLeftPanel(), BottomRightPanel(), classes="main")
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = ("textual-dark" if self.theme == "textual-light" else "textual-light")

if __name__ == "__main__":
    app = DemoZeldagen()
    app.run()