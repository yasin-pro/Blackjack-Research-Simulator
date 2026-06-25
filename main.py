# blackjack/main.py

from game import BlackjackSimulator


def get_direction():
    direction = input("Direction (right/left): ").strip().lower()
    if direction not in ["right", "left"]:
        return "right"
    return direction


def get_float(prompt, default):
    value = input(prompt).strip()
    if not value:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def get_int(prompt, default):
    value = input(prompt).strip()
    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_yes_no(prompt, default=True):
    suffix = " [Y/n]: " if default else " [y/N]: "
    ans = input(prompt + suffix).strip().lower()

    if not ans:
        return default

    return ans in ["y", "yes"]


if __name__ == "__main__":
    print("Blackjack Research Simulator Setup")
    print("-" * 50)

    players = get_int("Number of players: ", 1)
    decks = get_int("Number of decks: ", 6)
    direction = get_direction()

    delay = get_float("Delay seconds, default 1: ", 1.0)

    cut_percent = get_float("Cut card percent, default 50: ", 50.0)
    cut_card_ratio = cut_percent / 100

    monte_carlo_simulations = get_int(
        "Monte Carlo simulations per decision, default 3000: ",
        3000
    )

    ask_shuffle_each_round = get_yes_no(
        "Ask dealer manual shuffle before each round?",
        True
    )

    sim = BlackjackSimulator(
        num_players=players,
        direction=direction,
        decks=decks,
        delay=delay,
        cut_card_ratio=cut_card_ratio,
        monte_carlo_simulations=monte_carlo_simulations,
        ask_shuffle_each_round=ask_shuffle_each_round
    )

    sim.start()
