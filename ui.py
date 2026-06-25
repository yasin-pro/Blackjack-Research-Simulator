# blackjack/ui.py

import os


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def format_card_lines(cards, per_line=20):
    if not cards:
        return ["[]"]

    card_texts = [str(card) for card in cards]
    lines = []

    for i in range(0, len(card_texts), per_line):
        chunk = card_texts[i:i + per_line]
        lines.append("[" + ", ".join(chunk) + "]")

    return lines


def refresh_ui(game, hide_dealer=True):
    clear_console()

    dealt, remaining = game.deck.counts()
    usage = round(game.deck.usage_percent(), 2)

    running_count = game.deck.running_count()
    decks_remaining = round(game.deck.decks_remaining(), 2)
    true_count = round(game.deck.true_count(), 2)
    rounded_tc = game.deck.rounded_true_count()

    shoe_state = game.shoe_advantage_state()

    print("=" * 110)
    print("BLACKJACK RESEARCH SIMULATOR")
    print("=" * 110)

    print(f"Round           : {game.round_number}")
    print(f"Direction       : {game.direction}")
    print(f"Decks           : {game.deck.num_decks}")
    print(f"Action          : {game.current_action}")

    print("-" * 110)
    print("COUNTING / SHOE")

    print(f"Running Count   : {running_count}")
    print(f"True Count      : {true_count}")
    print(f"Rounded TC      : {rounded_tc}")
    print(f"Decks Remaining : {decks_remaining}")
    print(f"Cards Used      : {dealt}")
    print(f"Cards Remaining : {remaining}")
    print(f"Penetration     : {usage:.2f}%")
    print(f"Cut Card        : {game.cut_card_ratio * 100:.0f}%")

    if game.deck.cut_card_reached():
        print("Cut Status      : CUT CARD REACHED")
    else:
        print("Cut Status      : Before cut card")

    if game.deck.cut_card_declined:
        print("Cut Decision    : Declined, continue until shoe exhaustion")
    elif game.deck.cut_card_prompted:
        print("Cut Decision    : Prompted")
    else:
        print("Cut Decision    : Not prompted yet")

    print("-" * 110)
    print("REAL ADVANTAGE METER")

    if game.last_analysis:
        a = game.last_analysis

        print(f"Player Edge     : {a['player_edge']:+.2f}%")
        print(f"House Edge      : {a['house_edge']:+.2f}%")
        print(f"Bet Multiplier  : {a['bet_multiplier']}x")
        print(f"Shoe State      : {a['shoe_state']}")
        print(f"Optimal Status  : {a['shoe_state']}")
    else:
        print("Player Edge     : waiting...")
        print("House Edge      : waiting...")
        print("Bet Multiplier  : waiting...")
        print(f"Shoe State      : {shoe_state}")
        print(f"Optimal Status  : {shoe_state}")

    print("-" * 110)
    print("PLAYERS")

    for player in game.players:
        for i, hand in enumerate(player.hands):
            val = hand.value()
            prob = game.calculate_bust_prob(hand) if hand.status == "PLAYING" else 0.0
            split_mark = " (S)" if hand.is_split_hand else ""

            print(
                f"{player.name}-{i + 1}{split_mark:4} "
                f"{hand.visible_cards():30} "
                f"-> {val:<2} "
                f"{hand.status:14} "
                f"[Bust Prob: {prob:.1f}%]"
            )

    print()
    print("-" * 110)
    print("DEALER")

    if hide_dealer:
        print(f"Dealer          : {game.dealer.hand.visible_cards(hide_last=True)} -> ?")
    else:
        print(f"Dealer          : {game.dealer.hand.visible_cards()} -> {game.dealer.hand.value()}")

    print("-" * 110)
    print("DECISION ENGINE")

    if game.last_analysis:
        a = game.last_analysis

        print(f"Bust if Hit        : {a['bust_if_hit']:.1f}%")
        print(f"Dealer Bust        : {a['dealer_bust']:.1f}%")

        print(f"EV Hit             : {a['ev_hit']:+.4f}")
        print(f"EV Stand           : {a['ev_stand']:+.4f}")
        print(f"EV Double          : {a['ev_double']:+.4f}")

        print(f"Hit Win Rate       : {a['win_rate_hit']:.1f}%")
        print(f"Hit Lose Rate      : {a['lose_rate_hit']:.1f}%")
        print(f"Hit Push Rate      : {a['push_rate_hit']:.1f}%")

        print(f"Stand Win Rate     : {a['win_rate_stand']:.1f}%")
        print(f"Stand Lose Rate    : {a['lose_rate_stand']:.1f}%")
        print(f"Stand Push Rate    : {a['push_rate_stand']:.1f}%")

        print(f"Basic Move         : {a['basic_move'].upper()}")
        print(f"Composition Move   : {a['composition_move'].upper()}")
        print(f"Illustrious Move   : {a['illustrious_move'].upper()}")
        print(f"Monte Carlo Best   : {a['mc_move'].upper()}")
        print(f"Final Decision     : {a['final_move'].upper()}")
        print(f"Confidence         : {a['confidence']:.1f}%")
        print(f"Reason             : {a['reason']}")
    else:
        print("Waiting for analysis...")

    print("-" * 110)
    print("SESSION STATS")

    total_resolved = game.stats["win"] + game.stats["lose"] + game.stats["push"]

    print(f"Stats Win       : {game.stats['win']}")
    print(f"Stats Lose      : {game.stats['lose']}")
    print(f"Stats Push      : {game.stats['push']}")

    if total_resolved > 0:
        print(f"Win Rate        : {game.stats['win'] / total_resolved * 100:.2f}%")
        print(f"Lose Rate       : {game.stats['lose'] / total_resolved * 100:.2f}%")
        print(f"Push Rate       : {game.stats['push'] / total_resolved * 100:.2f}%")
    else:
        print("Win Rate        : 0.00%")
        print("Lose Rate       : 0.00%")
        print("Push Rate       : 0.00%")

    print("-" * 110)
    print("DEALT CARDS LOG")

    for line in format_card_lines(game.deck.dealt_cards):
        print(line)

    print("=" * 110)
