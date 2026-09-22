import os
import time
import random


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

BLACK = "\033[30m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GRAY = "\033[90m"


WIDTH = 72
MAX_UINT8 = 255
START_VALUE = 232
BASE_RISK = 1 / 16


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def hide_cursor():
    print("\033[?25l", end="")


def show_cursor():
    print("\033[?25h", end="")


def sleep(t):
    time.sleep(t)


def type_line(text, speed=0.008):
    for c in text:
        print(c, end="", flush=True)
        time.sleep(speed)
    print()


def bar(char="─", n=WIDTH):
    print(GRAY + char * n + RESET)


def glitch(text, cycles=3):
    chars = "!@#$%^&*?/\\|[]{}<>"
    for _ in range(cycles):
        fake = "".join(
            random.choice(chars) if random.random() < 0.18 else c
            for c in text
        )
        print(f"\r{RED}{fake}{RESET}", end="", flush=True)
        time.sleep(0.06)
    print("\r" + " " * WIDTH + "\r", end="")


def title():
    print(f"{CYAN}{BOLD}")
    print(" ██████╗ ██╗   ██╗███████╗██████╗ ███████╗██╗      ██████╗ ██╗    ██╗")
    print("██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔════╝██║     ██╔═══██╗██║    ██║")
    print("██║   ██║██║   ██║█████╗  ██████╔╝█████╗  ██║     ██║   ██║██║ █╗ ██║")
    print("██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗██╔══╝  ██║     ██║   ██║██║███╗██║")
    print("╚██████╔╝╚██████╔╝███████╗██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝")
    print("╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝  ")
    print()
    print(r"             R O U L E T T E")
    print(f"{RESET}")


def logo_small():
    print(f"{CYAN}{BOLD}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                         OVERFLOW ROULETTE                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")


class Game:
    def __init__(self):
        self.value = START_VALUE
        self.round = 1
        self.overflows = 0
        self.pushes = 0
        self.survived = 0
        self.best_chain = 0
        self.chain = 0
        self.game_over = False
        self.aborted = False
        self.log = []

    @property
    def risk(self):
        return min(BASE_RISK * (2 ** self.overflows), 1.0)

    @property
    def risk_percent(self):
        return self.risk * 100

    def add_log(self, text):
        self.log.append(text)
        if len(self.log) > 8:
            self.log.pop(0)


def value_meter(value):
    width = 42
    filled = int((value / 255) * width)
    filled = max(0, min(width, filled))

    if value >= 220:
        color = RED
    elif value >= 170:
        color = YELLOW
    else:
        color = CYAN

    return color + "█" * filled + GRAY + "░" * (width - filled) + RESET


def risk_meter(risk):
    width = 42
    filled = int(risk * width)
    filled = max(0, min(width, filled))

    if risk >= 0.5:
        color = RED
    elif risk >= 0.25:
        color = YELLOW
    elif risk >= 0.125:
        color = MAGENTA
    else:
        color = GREEN

    return color + "█" * filled + GRAY + "░" * (width - filled) + RESET


def risk_label(risk):
    if risk >= 1:
        return f"{RED}{BOLD}CERTAIN FAILURE{RESET}"
    if risk >= 0.5:
        return f"{RED}{BOLD}CRITICAL{RESET}"
    if risk >= 0.25:
        return f"{YELLOW}{BOLD}DANGEROUS{RESET}"
    if risk >= 0.125:
        return f"{MAGENTA}UNSTABLE{RESET}"
    return f"{GREEN}LOW{RESET}"


def status_screen(game):
    clear()
    logo_small()

    print()
    print(f"  ROUND              {WHITE}{game.round:03d}{RESET}")
    print(f"  INTEGER            {WHITE}{game.value:03d}{RESET} / 255")
    print(f"  OVERFLOWS          {MAGENTA}{BOLD}{game.overflows:03d}{RESET}")
    print(f"  SURVIVED           {GREEN}{game.survived:03d}{RESET}")
    print(f"  OVERFLOW CHAIN     {YELLOW}{game.chain:03d}{RESET}")
    print(f"  BEST CHAIN         {YELLOW}{game.best_chain:03d}{RESET}")

    print()
    print("  INTEGER PRESSURE")
    print(f"  [{value_meter(game.value)}]")

    print()
    print("  FAILURE PROBABILITY")
    print(f"  [{risk_meter(game.risk)}]")
    print(
        f"  {risk_label(game.risk)}"
        f"   {WHITE}{game.risk_percent:.2f}%{RESET}"
    )

    print()
    bar()

    print(f"  {GRAY}UINT8 MEMORY SPACE{RESET}")
    print(
        f"  {GRAY}000{RESET} "
        f"──────────────────────── "
        f"{YELLOW}255{RESET}"
    )
    print(
        f"  {GRAY}256 cannot be represented.{RESET}"
    )

    print()
    bar()

    if game.log:
        print(f"  {GRAY}SYSTEM LOG{RESET}")
        for item in game.log:
            print(f"  {item}")

    print()
    bar()


def intro():
    clear()
    title()

    bar()

    type_line(
        f"{WHITE}A game about the one number that should never exist.{RESET}",
        0.018
    )

    print()

    type_line(
        "You are controlling an unsigned 8-bit integer.",
        0.012
    )

    type_line(
        "It can represent exactly 256 states.",
        0.012
    )

    print()
    print(f"             {CYAN}000 → 001 → 002 → ... → 254 → 255{RESET}")
    print()
    print(f"                    {RED}{BOLD}256{RESET}")
    print(f"                    {RED}{BOLD}cannot be represented.{RESET}")

    print()

    type_line(
        "When the value crosses the boundary, it wraps around.",
        0.012
    )

    print()
    print(
        f"              {WHITE}255 + 1{RESET}"
        f"   {RED}→ OVERFLOW →{RESET}"
        f"   {CYAN}000{RESET}"
    )

    print()

    bar()

    print()
    print(f"{YELLOW}{BOLD}THE RULE{RESET}")
    print()

    print("Every overflow doubles the failure probability.")
    print()
    print(f"    0 overflows     {GREEN}  6.25%{RESET}")
    print(f"    1 overflow      {GREEN} 12.50%{RESET}")
    print(f"    2 overflows     {YELLOW} 25.00%{RESET}")
    print(f"    3 overflows     {RED} 50.00%{RESET}")
    print(f"    4 overflows     {RED}{BOLD}100.00%{RESET}")

    print()
    bar()

    print()
    print(f"{GRAY}There is no luck in the integer.{RESET}")
    print(f"{GRAY}Only consequences.{RESET}")

    print()
    input(f"{CYAN}Press ENTER to enter the machine...{RESET}")


def overflow_effect(old, amount, new, count):
    clear()

    print()
    print(f"{RED}{BOLD}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║                          O V E R F L O W                           ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    sleep(0.2)

    print()
    print(
        f"                    {WHITE}{old:03d}{RESET}"
        f"  +  "
        f"{YELLOW}{amount:02d}{RESET}"
    )

    sleep(0.35)

    print()
    print(f"                         {RED}{BOLD}255{RESET}")
    sleep(0.18)

    print(f"                         {RED}{BOLD}256{RESET}")
    sleep(0.18)

    print(f"                         {RED}{BOLD}257{RESET}")
    sleep(0.18)

    print()
    glitch("INTEGER BOUNDARY BREACHED", 5)

    print()
    print(
        f"                         {CYAN}{BOLD}{new:03d}{RESET}"
    )

    sleep(0.3)

    print()
    print(
        f"  {RED}{BOLD}"
        "██████████████████████████████████████████"
        f"{RESET}"
    )

    print()
    print(
        f"  {MAGENTA}{BOLD}"
        f"OVERFLOW #{count:02d}"
        f"{RESET}"
    )

    print()
    print(
        f"  FAILURE PROBABILITY → "
        f"{RED}{BOLD}{min(6.25 * (2 ** count), 100):.2f}%{RESET}"
    )

    print()
    bar()

    sleep(0.9)


def push_integer(game):
    old = game.value
    amount = random.randint(8, 31)

    raw = old + amount
    overflow = raw > MAX_UINT8
    new = raw % 256

    game.value = new
    game.pushes += 1

    if overflow:
        game.overflows += 1
        game.chain += 1
        game.best_chain = max(game.best_chain, game.chain)

        overflow_effect(
            old,
            amount,
            new,
            game.overflows
        )

        game.add_log(
            f"{RED}OVERFLOW #{game.overflows:02d}{RESET} "
            f"{old:03d} + {amount:02d} → {new:03d}"
        )

        game.add_log(
            f"{MAGENTA}RISK DOUBLED{RESET} "
            f"→ {game.risk_percent:.2f}%"
        )

    else:
        game.chain = 0

        game.add_log(
            f"{CYAN}PUSH{RESET} "
            f"{old:03d} + {amount:02d} → {new:03d}"
        )

    game.round += 1


def trigger_effect(game):
    clear()
    logo_small()

    print()
    print(f"{WHITE}{BOLD}")
    print("                         R I S K   T E S T")
    print(f"{RESET}")

    bar()

    print()
    print(f"  INTEGER       : {CYAN}{game.value:03d}{RESET}")
    print(f"  OVERFLOWS     : {MAGENTA}{game.overflows:03d}{RESET}")
    print(f"  CURRENT RISK  : {risk_label(game.risk)}")
    print(
        f"  PROBABILITY   : "
        f"{WHITE}{game.risk_percent:.2f}%{RESET}"
    )

    print()
    bar()

    print()
    print(f"               {DIM}THE MACHINE IS THINKING{RESET}")
    print()

    sequence = [
        "[          ]",
        "[█         ]",
        "[██        ]",
        "[████      ]",
        "[██████    ]",
        "[████████  ]",
        "[██████████]"
    ]

    for frame in sequence:
        print(f"\r                    {frame}", end="", flush=True)
        time.sleep(0.11)

    print()
    print()

    for _ in range(3):
        print(
            f"\r              {YELLOW}[ ? ]{RESET}",
            end="",
            flush=True
        )
        time.sleep(0.25)
        print(
            f"\r              {WHITE}[ ! ]{RESET}",
            end="",
            flush=True
        )
        time.sleep(0.18)

    print("\n")

    roll = random.random()

    if roll < game.risk:
        failure_effect(game)
    else:
        survival_effect(game)


def failure_effect(game):
    game.game_over = True

    clear()

    print(f"{RED}{BOLD}")
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║                      S Y S T E M   F A I L                        ║")
    print("║                                                                    ║")
    print("║                  INTEGER COLLAPSE DETECTED                        ║")
    print("║                                                                    ║")
    print("║                    255 ──→ 256 ──→ ???                            ║")
    print("║                              │                                     ║")
    print("║                              ▼                                     ║")
    print("║                            000                                     ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    sleep(0.5)

    glitch("INTEGER COLLAPSE", 8)

    print()
    print(f"       {RED}{BOLD}THE INTEGER HAS SPOKEN.{RESET}")

    print()
    print(
        f"       Final value      : {WHITE}{game.value:03d}{RESET}"
    )
    print(
        f"       Overflows        : {MAGENTA}{game.overflows:03d}{RESET}"
    )
    print(
        f"       Final risk       : {RED}{game.risk_percent:.2f}%{RESET}"
    )

    print()
    bar()

    sleep(1.2)


def survival_effect(game):
    game.survived += 1

    clear()

    print()
    print(f"{GREEN}{BOLD}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║                         S U R V I V E D                            ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    print()
    print(f"                     {GREEN}CLICK.{RESET}")
    print()

    sleep(0.3)

    print(
        f"                 {GREEN}{BOLD}"
        "THE MACHINE STAYED SILENT."
        f"{RESET}"
    )

    print()
    print(
        f"                 Survival #{game.survived}"
    )

    sleep(0.8)


def rules():
    clear()
    logo_small()

    print()

    print(f"{WHITE}{BOLD}CORE MECHANIC{RESET}")
    bar()

    print()
    print("The game uses an unsigned 8-bit integer model.")
    print()
    print("Valid values:")
    print()
    print("                 000 → 255")
    print()
    print("Anything beyond 255 wraps around to the beginning.")
    print()
    print("                 255 + 1 = 000")
    print()
    print("This is called an OVERFLOW.")

    print()
    bar()

    print()
    print(f"{WHITE}{BOLD}RISK ESCALATION{RESET}")
    bar()

    print()
    print("Every overflow doubles the failure probability.")
    print()

    rows = [
        ("0", "1 / 16", "6.25%"),
        ("1", "1 / 8", "12.50%"),
        ("2", "1 / 4", "25.00%"),
        ("3", "1 / 2", "50.00%"),
        ("4+", "1 / 1", "100.00%"),
    ]

    for overflow, fraction, percent in rows:
        print(
            f"  Overflow {overflow:<3}"
            f"  {fraction:<8}"
            f"  {percent}"
        )

    print()
    bar()

    print()
    print(f"{WHITE}{BOLD}THE CHOICE{RESET}")
    bar()

    print()
    print("Pushing increases the integer.")
    print("Eventually, it may overflow.")
    print()
    print("Overflow increases your risk.")
    print()
    print("Pulling the trigger tests your current risk.")
    print()
    print("You can always stop.")
    print()
    print("But stopping means the run ends.")
    print()
    print(f"{GRAY}The machine does not reward courage.")
    print(f"It only remembers what happened.{RESET}")

    print()
    input(f"{CYAN}Press ENTER to return...{RESET}")


def result_screen(game):
    clear()
    title()

    bar()

    if game.aborted:
        print()
        print(f"{YELLOW}{BOLD}RUN ABORTED{RESET}")
    else:
        print()
        print(f"{RED}{BOLD}RUN TERMINATED{RESET}")

    print()
    bar()

    print()
    print(f"  ROUNDS SURVIVED      {WHITE}{game.round - 1:03d}{RESET}")
    print(f"  INTEGER PUSHES       {WHITE}{game.pushes:03d}{RESET}")
    print(f"  OVERFLOWS            {MAGENTA}{game.overflows:03d}{RESET}")
    print(f"  BEST OVERFLOW CHAIN  {YELLOW}{game.best_chain:03d}{RESET}")
    print(f"  FINAL INTEGER        {CYAN}{game.value:03d}{RESET}")

    print()

    if game.overflows == 0:
        rank = "UNTOUCHED"
    elif game.overflows == 1:
        rank = "BOUNDARY TESTER"
    elif game.overflows == 2:
        rank = "OVERFLOWER"
    elif game.overflows == 3:
        rank = "SYSTEM BREAKER"
    elif game.overflows >= 4:
        rank = "INTEGER ABSOLUTE"
    else:
        rank = "UNKNOWN"

    print(f"  SYSTEM STATUS        {BOLD}{rank}{RESET}")

    print()
    bar()

    print()
    print(f"{GRAY}LAST SYSTEM EVENTS{RESET}")

    for item in game.log[-8:]:
        print(f"  {item}")

    print()
    bar()

    print()
    print(
        f"{DIM}"
        "255 was never the limit."
        "\n"
        "It was only the warning."
        f"{RESET}"
    )

    print()


def game_loop():
    game = Game()

    game.add_log(
        f"{GREEN}SYSTEM ONLINE{RESET} "
        f"UINT8 chamber initialized."
    )

    game.add_log(
        f"{CYAN}START VALUE{RESET} "
        f"{game.value:03d}"
    )

    while not game.game_over:

        status_screen(game)

        print()
        print(
            f"  {WHITE}[1]{RESET} PUSH INTEGER"
        )
        print(
            f"      Increase the value."
        )
        print()
        print(
            f"  {WHITE}[2]{RESET} TEST THE RISK"
        )
        print(
            f"      Pull the trigger."
        )
        print()
        print(
            f"  {WHITE}[3]{RESET} RULES"
        )
        print()
        print(
            f"  {WHITE}[4]{RESET} ABORT RUN"
        )

        print()
        bar()

        choice = input(
            f"\n{CYAN}OVERFLOW > {RESET}"
        ).strip()

        if choice == "1":
            push_integer(game)

        elif choice == "2":
            trigger_effect(game)

        elif choice == "3":
            rules()

        elif choice == "4":
            game.aborted = True
            game.game_over = True

        else:
            print(
                f"\n{RED}UNKNOWN COMMAND.{RESET}"
            )
            time.sleep(0.6)

    result_screen(game)

    while True:
        print()
        print(
            f"  {CYAN}[R]{RESET} RESTART"
            f"     {CYAN}[M]{RESET} MENU"
            f"     {CYAN}[Q]{RESET} QUIT"
        )

        choice = input(
            f"\n{CYAN}> {RESET}"
        ).strip().lower()

        if choice == "r":
            return "restart"

        if choice == "m":
            return "menu"

        if choice == "q":
            return "quit"


def main():
    hide_cursor()

    try:
        while True:
            clear()
            title()

            print(
                f"{GRAY}"
                "A terminal game where integer overflow becomes a matter "
                "of survival."
                f"{RESET}"
            )

            print()
            bar()

            print()
            print(f"  {CYAN}[1]{RESET} START GAME")
            print(f"  {CYAN}[2]{RESET} HOW IT WORKS")
            print(f"  {CYAN}[3]{RESET} QUIT")

            print()
            bar()

            choice = input(
                f"\n{CYAN}OVERFLOW ROULETTE > {RESET}"
            ).strip()

            if choice == "1":

                while True:
                    result = game_loop()

                    if result == "restart":
                        continue

                    if result == "menu":
                        break

                    if result == "quit":
                        return

            elif choice == "2":
                rules()

            elif choice == "3":
                return

            else:
                print(
                    f"\n{RED}INVALID INPUT.{RESET}"
                )
                time.sleep(0.6)

    except KeyboardInterrupt:
        pass

    finally:
        show_cursor()
        print(RESET)

if __name__ == "__main__":
    main()
