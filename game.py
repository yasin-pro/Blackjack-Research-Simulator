# blackjack/game.py

import time
from models import Player, Dealer, Hand
from deck import Deck
from strategy import should_split, hybrid_decision
from ui import refresh_ui


class BlackjackSimulator:
    def __init__(
        self,
        num_players,
        direction,
        decks,
        delay=1,
        cut_card_ratio=0.50,
        monte_carlo_simulations=3000,
        ask_shuffle_each_round=True
    ):
        self.players = [Player(f"P{i + 1}") for i in range(num_players)]
        self.dealer = Dealer()
        self.deck = Deck(decks, cut_card_ratio=cut_card_ratio)

        self.direction = direction
        self.delay = delay

        self.total_cards = decks * 52
        self.cut_card_ratio = cut_card_ratio
        self.monte_carlo_simulations = monte_carlo_simulations
        self.ask_shuffle_each_round = ask_shuffle_each_round

        self.current_action = "Initializing..."
        self.stats = {"win": 0, "lose": 0, "push": 0}
        self.last_analysis = {}
        self.round_number = 0

        self.dealer_revealed = False

    def ask_yes_no(self, question, default="n"):
        suffix = " [y/N]: " if default.lower() == "n" else " [Y/n]: "
        ans = input(question + suffix).strip().lower()

        if not ans:
            ans = default.lower()

        return ans in ["y", "yes"]

    def calculate_bust_prob(self, hand):
        if hand.value() >= 21:
            return 0.0

        unknown_cards = self.deck.get_unknown_cards()

        if not unknown_cards:
            return 0.0

        bad = 0

        for card in unknown_cards:
            tmp = Hand(cards=list(hand.cards))
            tmp.add_card(card)

            if tmp.value() > 21:
                bad += 1

        return bad / len(unknown_cards) * 100


    def shoe_advantage_state(self):
        if self.last_analysis and "shoe_state" in self.last_analysis:
            return self.last_analysis["shoe_state"]

        tc = self.deck.true_count()

        if tc >= 4:
            return "🔥 EXTREME PLAYER ADVANTAGE"
        if tc >= 2:
            return "⭐ PLAYER ADVANTAGE"
        if tc <= -2:
            return "⚠️ DEALER ADVANTAGE"
        return "Neutral"

    def reset_round(self):
        for p in self.players:
            p.hands = [Hand()]

        self.dealer.hand = Hand()
        self.last_analysis = {}
        self.dealer_revealed = False

    def force_shuffle(self, reason):
        self.current_action = f"Shuffling Shoe... Reason: {reason}"
        refresh_ui(self, hide_dealer=not self.dealer_revealed)
        time.sleep(1)

        self.deck.reset_and_shuffle()

        self.current_action = "Shuffle complete."
        refresh_ui(self, hide_dealer=not self.dealer_revealed)
        time.sleep(1)

    def check_manual_shuffle_before_round(self):
        if not self.ask_shuffle_each_round:
            return

        refresh_ui(self, hide_dealer=not self.dealer_revealed)

        do_shuffle = self.ask_yes_no(
            f"Round {self.round_number}: Dealer manual shuffle before round?",
            default="n"
        )

        if do_shuffle:
            self.force_shuffle("manual dealer shuffle before round")

    def check_cut_card_shuffle(self):
        if self.deck.needs_cut_card_prompt():
            self.deck.cut_card_prompted = True

            refresh_ui(self, hide_dealer=not self.dealer_revealed)

            do_shuffle = self.ask_yes_no(
                f"Cut card reached at {self.deck.usage_percent():.1f}%. Shuffle now?",
                default="y"
            )

            if do_shuffle:
                self.force_shuffle("cut card reached")
            else:
                self.deck.cut_card_declined = True
                self.current_action = "Cut card declined. Continuing until shoe is exhausted."
                refresh_ui(self, hide_dealer=not self.dealer_revealed)
                time.sleep(1)

    def ensure_cards_available(self, min_cards_needed=15):
        if self.deck.full_shoe_exhausted():
            self.force_shuffle("shoe exhausted")
            return

        if len(self.deck.cards) < min_cards_needed:
            self.force_shuffle("not enough cards to safely start next round")

    def deal_initial(self):
        order = self.players if self.direction == "right" else list(reversed(self.players))

        for p in order:
            p.hands[0].add_card(self.deck.draw())
            self.current_action = f"Dealing first card to {p.name}"
            refresh_ui(self, hide_dealer=True)
            time.sleep(self.delay)

        self.dealer.hand.add_card(self.deck.draw())
        self.current_action = "Dealing dealer up-card"
        refresh_ui(self, hide_dealer=True)
        time.sleep(self.delay)

        for p in order:
            p.hands[0].add_card(self.deck.draw())
            self.current_action = f"Dealing second card to {p.name}"
            refresh_ui(self, hide_dealer=True)
            time.sleep(self.delay)

        self.dealer.hand.add_card(self.deck.draw(visible=False))
        self.current_action = "Dealing dealer hole-card"
        refresh_ui(self, hide_dealer=True)
        time.sleep(self.delay)


    def play_player_turns(self):
        order = self.players if self.direction == "right" else list(reversed(self.players))
        dealer_up = self.dealer.hand.cards[0]

        for p in order:
            h_idx = 0

            while h_idx < len(p.hands):
                hand = p.hands[h_idx]

                if hand.status in ["BUST", "STAND", "STAND (SPLIT)", "BLACKJACK"]:
                    h_idx += 1
                    continue

                if hand.is_blackjack():
                    hand.status = "BLACKJACK"
                    refresh_ui(self, hide_dealer=True)
                    time.sleep(self.delay)
                    h_idx += 1
                    continue

                hand.status = "PLAYING"

                if should_split(hand, dealer_up, "hybrid"):
                    self.current_action = f"{p.name}-{h_idx + 1} SPLITS"

                    first_card = hand.cards.pop()
                    new_hand = Hand(cards=[first_card], is_split_hand=True)

                    p.hands.append(new_hand)

                    hand.is_split_hand = True
                    hand.add_card(self.deck.draw())
                    new_hand.add_card(self.deck.draw())

                    hand.status = "STAND (SPLIT)"
                    new_hand.status = "STAND (SPLIT)"

                    refresh_ui(self, hide_dealer=True)
                    time.sleep(self.delay)

                    h_idx += 1
                    continue

                while hand.status == "PLAYING":
                    if not self.deck.cards:
                        self.force_shuffle("shoe exhausted during player turn")

                    tc = self.deck.true_count()

                    analysis = hybrid_decision(
                        hand=hand,
                        dealer_up_card=dealer_up,
                        deck=self.deck,
                        true_count=tc,
                        simulations=self.monte_carlo_simulations
                    )

                    self.last_analysis = analysis

                    self.current_action = (
                        f"{p.name}-{h_idx + 1}: "
                        f"Bust if Hit {analysis['bust_if_hit']:.1f}%, "
                        f"Dealer Bust {analysis['dealer_bust']:.1f}%, "
                        f"EV Hit {analysis['ev_hit']:+.3f}, "
                        f"EV Stand {analysis['ev_stand']:+.3f}, "
                        f"Edge {analysis['player_edge']:+.2f}%, "
                        f"Bet {analysis['bet_multiplier']}x, "
                        f"Final {analysis['final_move'].upper()}"
                    )

                    refresh_ui(self, hide_dealer=True)
                    time.sleep(self.delay)

                    move = analysis["final_move"]

                    if move == "stand":
                        hand.status = "STAND"

                    elif move == "hit":
                        hand.add_card(self.deck.draw())

                        if hand.value() > 21:
                            hand.status = "BUST"

                    else:
                        hand.status = "STAND"


                    refresh_ui(self, hide_dealer=True)
                    time.sleep(self.delay)

                h_idx += 1

    def dealer_turn(self):
        self.dealer_revealed = True

        if len(self.dealer.hand.cards) > 1:
            self.deck.reveal_card(self.dealer.hand.cards[1])

        self.current_action = "Dealer reveals hole card"
        refresh_ui(self, hide_dealer=False)
        time.sleep(self.delay)

        # Dealer stands on soft 17 (S17 rule)
        while self.dealer.hand.value() < 17:
            if not self.deck.cards:
                self.force_shuffle("shoe exhausted during dealer turn")

            self.dealer.hand.add_card(self.deck.draw())
            self.current_action = "Dealer hits"
            refresh_ui(self, hide_dealer=False)
            time.sleep(self.delay)

        self.current_action = "Dealer stands"
        refresh_ui(self, hide_dealer=False)
        time.sleep(self.delay)


    def show_results(self):
        self.dealer_revealed = True
        d_val = self.dealer.hand.value()

        print("\n--- ROUND RESULTS ---")
        print(f"Dealer: {self.dealer.hand.visible_cards()} -> {d_val}")

        for p in self.players:
            for i, h in enumerate(p.hands):
                p_val = h.value()

                if h.is_blackjack() and not self.dealer.hand.is_blackjack():
                    h.result = "WIN"
                elif self.dealer.hand.is_blackjack() and not h.is_blackjack():
                    h.result = "LOSE"
                elif p_val > 21:
                    h.result = "LOSE"
                elif d_val > 21:
                    h.result = "WIN"
                elif p_val > d_val:
                    h.result = "WIN"
                elif p_val < d_val:
                    h.result = "LOSE"
                else:
                    h.result = "PUSH"

                self.stats[h.result.lower()] += 1

                mark = " (S)" if h.is_split_hand else ""
                print(f"{p.name}-{i + 1}{mark}: {h.result} ({p_val} vs {d_val})")

        print(f"Global Stats: {self.stats}")

    def play_round(self):
        self.round_number += 1
        self.current_action = f"Round {self.round_number}"

        self.reset_round()

        self.check_manual_shuffle_before_round()
        self.check_cut_card_shuffle()
        self.ensure_cards_available(min_cards_needed=max(15, len(self.players) * 8 + 8))

        self.deal_initial()
        self.play_player_turns()
        self.dealer_turn()
        self.show_results()


    def start(self):
        self.deck.shuffle()

        while True:
            self.play_round()

            self.current_action = "Waiting 5 seconds before next round..."
            refresh_ui(self, hide_dealer=False)
            time.sleep(5)
