# blackjack/strategy.py

import copy
import random
from models import Hand


def dealer_up_value(card):
    if card.rank in ["J", "Q", "K"]:
        return 10
    if card.rank == "A":
        return 11
    return int(card.rank)


def compare_result(player_value, dealer_value):
    """
    Return EV unit:
      win  = +1
      lose = -1
      push = 0
    """
    if player_value > 21:
        return -1

    if dealer_value > 21:
        return 1

    if player_value > dealer_value:
        return 1

    if player_value < dealer_value:
        return -1

    return 0


def basic_strategy_move(hand, dealer_up_card):
    val = hand.value()
    d_val = dealer_up_value(dealer_up_card)
    soft = hand.is_soft()

    # Soft hands
    if soft:
        if val >= 19:
            return "stand"
        if val == 18:
            return "stand" if d_val in [2, 7, 8] else "hit"
        return "hit"

    # Hard hands
    if val >= 17:
        return "stand"

    if 13 <= val <= 16:
        return "stand" if 2 <= d_val <= 6 else "hit"

    if val == 12:
        return "stand" if d_val in [4, 5, 6] else "hit"

    return "hit"


def should_split(hand, dealer_up_card, strategy_name="hybrid"):
    if len(hand.cards) != 2:
        return False

    if hand.cards[0].rank != hand.cards[1].rank:
        return False

    if strategy_name == "random":
        return random.choice([True, False])

    rank = hand.cards[0].rank
    d_val = dealer_up_value(dealer_up_card)

    if rank in ["A", "8"]:
        return True

    if rank in ["10", "J", "Q", "K"]:
        return False

    if rank in ["4", "5"]:
        return False

    if rank in ["2", "3", "7"] and 2 <= d_val <= 7:
        return True

    if rank == "6" and 2 <= d_val <= 6:
        return True

    if rank == "9" and d_val in [2, 3, 4, 5, 6, 8, 9]:
        return True

    return False


def illustrious18_move(hand, dealer_up_card, true_count):
    val = hand.value()
    d_val = dealer_up_value(dealer_up_card)

    if val == 16 and d_val == 10 and true_count >= 0:
        return "stand"

    if val == 15 and d_val == 10 and true_count >= 4:
        return "stand"

    if val == 12 and d_val == 3 and true_count >= 2:
        return "stand"

    if val == 12 and d_val == 2 and true_count >= 3:
        return "stand"

    if val == 13 and d_val == 2 and true_count >= -1:
        return "stand"

    if val == 13 and d_val == 3 and true_count >= -2:
        return "stand"

    if val == 12 and d_val == 4 and true_count < 0:
        return "hit"

    if val == 12 and d_val == 5 and true_count < -2:
        return "hit"

    if val == 12 and d_val == 6 and true_count < -1:
        return "hit"

    return basic_strategy_move(hand, dealer_up_card)


def would_bust_if_hit(hand, card):
    tmp = copy.deepcopy(hand)
    tmp.add_card(card)
    return tmp.value() > 21


def dealer_play_from_upcard_and_hole(dealer_up_card, hole_card, cards):
    dealer_hand = Hand(cards=[dealer_up_card, hole_card])

    while dealer_hand.value() < 17 and cards:
        dealer_hand.add_card(cards.pop())

    return dealer_hand.value()


def simulate_player_after_hit(player_hand, dealer_up_card, cards):
    hand = copy.deepcopy(player_hand)

    if not cards:
        return hand.value()

    hand.add_card(cards.pop())

    if hand.value() > 21:
        return hand.value()

    while cards:
        if hand.value() >= 17:
            break

        move = basic_strategy_move(hand, dealer_up_card)

        if move == "stand":
            break

        hand.add_card(cards.pop())

        if hand.value() > 21:
            break

    return hand.value()


def calculate_bust_if_hit(hand, deck_cards):
    if not deck_cards:
        return 0.0

    busts = 0

    for card in deck_cards:
        if would_bust_if_hit(hand, card):
            busts += 1

    return busts / len(deck_cards) * 100


def monte_carlo_evaluate_advanced(
    hand,
    dealer_up_card,
    deck_cards,
    simulations=3000
):

    if not deck_cards:
        return {
            "bust_if_hit": 0.0,
            "dealer_bust": 0.0,
            "ev_hit": 0.0,
            "ev_stand": 0.0,
            "ev_double": 0.0,
            "mc_move": "stand",
            "confidence": 0.0,
            "win_rate_hit": 0.0,
            "lose_rate_hit": 0.0,
            "push_rate_hit": 0.0,
            "win_rate_stand": 0.0,
            "lose_rate_stand": 0.0,
            "push_rate_stand": 0.0,
        }

    bust_if_hit = calculate_bust_if_hit(hand, deck_cards)

    hit_results = []
    stand_results = []
    double_results = []

    dealer_bust_count = 0

    hit_win = hit_lose = hit_push = 0
    stand_win = stand_lose = stand_push = 0

    current_value = hand.value()

    for _ in range(simulations):
        # ------------------------------
        # STAND branch
        # ------------------------------
        cards_stand = deck_cards.copy()
        random.shuffle(cards_stand)

        if not cards_stand:
            stand_results.append(0)
        else:
            hole_card = cards_stand.pop()
            dealer_value = dealer_play_from_upcard_and_hole(
                dealer_up_card,
                hole_card,
                cards_stand
            )

            if dealer_value > 21:
                dealer_bust_count += 1

            result = compare_result(current_value, dealer_value)
            stand_results.append(result)

            if result == 1:
                stand_win += 1
            elif result == -1:
                stand_lose += 1
            else:
                stand_push += 1

        # ------------------------------
        # HIT branch
        # ------------------------------
        cards_hit = deck_cards.copy()
        random.shuffle(cards_hit)

        if not cards_hit:
            hit_results.append(0)
        else:
            hole_card = cards_hit.pop()

            player_value_after_hit = simulate_player_after_hit(
                hand,
                dealer_up_card,
                cards_hit
            )

            if player_value_after_hit > 21:
                result = -1
            else:
                dealer_value = dealer_play_from_upcard_and_hole(
                    dealer_up_card,
                    hole_card,
                    cards_hit
                )
                result = compare_result(player_value_after_hit, dealer_value)

            hit_results.append(result)

            if result == 1:
                hit_win += 1
            elif result == -1:
                hit_lose += 1
            else:
                hit_push += 1


        # ------------------------------
        # DOUBLE branch
        # ------------------------------
        cards_double = deck_cards.copy()
        random.shuffle(cards_double)

        double_hand = copy.deepcopy(hand)

        if not cards_double:
            double_results.append(0)
        else:
            hole_card = cards_double.pop()

            if cards_double:
                double_hand.add_card(cards_double.pop())

            if double_hand.value() > 21:
                double_results.append(-2)
            else:
                dealer_value = dealer_play_from_upcard_and_hole(
                    dealer_up_card,
                    hole_card,
                    cards_double
                )
                double_results.append(2 * compare_result(double_hand.value(), dealer_value))


    ev_hit = sum(hit_results) / len(hit_results) if hit_results else 0.0
    ev_stand = sum(stand_results) / len(stand_results) if stand_results else 0.0
    ev_double = sum(double_results) / len(double_results) if double_results else 0.0

    dealer_bust = dealer_bust_count / simulations * 100

    mc_move = "hit" if ev_hit > ev_stand else "stand"

    ev_diff = abs(ev_hit - ev_stand)
    confidence = min(99.0, 50.0 + ev_diff * 120)

    return {
        "bust_if_hit": round(bust_if_hit, 2),
        "dealer_bust": round(dealer_bust, 2),

        "ev_hit": round(ev_hit, 4),
        "ev_stand": round(ev_stand, 4),
        "ev_double": round(ev_double, 4),

        "mc_move": mc_move,
        "confidence": round(confidence, 2),

        "win_rate_hit": round(hit_win / simulations * 100, 2),
        "lose_rate_hit": round(hit_lose / simulations * 100, 2),
        "push_rate_hit": round(hit_push / simulations * 100, 2),

        "win_rate_stand": round(stand_win / simulations * 100, 2),
        "lose_rate_stand": round(stand_lose / simulations * 100, 2),
        "push_rate_stand": round(stand_push / simulations * 100, 2),
    }


def estimate_player_edge(true_count, ev_hit, ev_stand):

    base_house_edge = -0.50  
    count_edge = true_count * 0.50

    best_ev = max(ev_hit, ev_stand)

    ev_component = best_ev * 2.0

    player_edge = base_house_edge + count_edge + ev_component
    house_edge = -player_edge

    return round(player_edge, 2), round(house_edge, 2)


def bet_multiplier_from_edge(player_edge, true_count):
    if player_edge >= 3.0 or true_count >= 5:
        return 8
    if player_edge >= 2.0 or true_count >= 4:
        return 6
    if player_edge >= 1.0 or true_count >= 3:
        return 4
    if player_edge >= 0.3 or true_count >= 2:
        return 2
    return 1


def shoe_state_from_edge(player_edge, true_count):
    if true_count >= 5 or player_edge >= 3.0:
        return "EXTREME PLAYER ADVANTAGE"
    if true_count >= 3 or player_edge >= 1.0:
        return "STRONG PLAYER ADVANTAGE"
    if true_count >= 2 or player_edge >= 0.3:
        return "SLIGHT PLAYER ADVANTAGE"
    if true_count <= -2 or player_edge <= -1.5:
        return "DEALER ADVANTAGE"
    return "Neutral"


def hybrid_decision(hand, dealer_up_card, deck, true_count, simulations=3000):
    analysis = monte_carlo_evaluate_advanced(
        hand=hand,
        dealer_up_card=dealer_up_card,
        deck_cards=deck.get_unknown_cards(),
        simulations=simulations
    )

    basic_move = basic_strategy_move(hand, dealer_up_card)
    illustrious_move = illustrious18_move(hand, dealer_up_card, true_count)
    composition_move = analysis["mc_move"]

    final_move = basic_move
    reason = "basic_strategy"

    ev_gap = abs(analysis["ev_hit"] - analysis["ev_stand"])

    if analysis["confidence"] >= 62 and ev_gap >= 0.025:
        final_move = composition_move
        reason = "composition_monte_carlo_ev"

    if true_count >= 2:
        final_move = illustrious_move
        reason = "illustrious_true_count_deviation"

    if analysis["confidence"] >= 78 and ev_gap >= 0.04:
        final_move = composition_move
        reason = "high_confidence_monte_carlo_override"

    player_edge, house_edge = estimate_player_edge(
        true_count=true_count,
        ev_hit=analysis["ev_hit"],
        ev_stand=analysis["ev_stand"]
    )

    bet_multiplier = bet_multiplier_from_edge(player_edge, true_count)
    shoe_state = shoe_state_from_edge(player_edge, true_count)

    analysis.update({
        "basic_move": basic_move,
        "composition_move": composition_move,
        "illustrious_move": illustrious_move,
        "final_move": final_move,
        "reason": reason,

        "player_edge": player_edge,
        "house_edge": house_edge,
        "bet_multiplier": bet_multiplier,
        "shoe_state": shoe_state,
    })

    return analysis
