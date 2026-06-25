# blackjack/deck.py

import random
from models import Card


class Deck:
    SUITS = ["♠", "♥", "♦", "♣"]
    RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    def __init__(self, num_decks=1, cut_card_ratio=0.50):
        self.num_decks = num_decks
        self.cut_card_ratio = cut_card_ratio

        self.cards = []
        self.dealt_cards = []
        self.known_cards = []
        self.hidden_cards = []

        self.cut_card_prompted = False
        self.cut_card_declined = False

        self.build_shoe()

    def build_shoe(self):
        self.cards = []

        for _ in range(self.num_decks):
            for suit in self.SUITS:
                for rank in self.RANKS:
                    self.cards.append(Card(rank, suit))

        self.dealt_cards = []
        self.known_cards = []
        self.hidden_cards = []

        self.cut_card_prompted = False
        self.cut_card_declined = False

    def shuffle(self):
        random.shuffle(self.cards)

    def reset_and_shuffle(self):
        self.build_shoe()
        self.shuffle()

    def draw(self, visible=True):
        if not self.cards:
            raise ValueError("Shoe empty")

        card = self.cards.pop(0)
        self.dealt_cards.append(card)

        if visible:
            self.register_known_card(card)
        else:
            self.hidden_cards.append(card)

        return card

    def register_known_card(self, card):
        self.known_cards.append(card)

    def reveal_card(self, card):
        if card in self.hidden_cards:
            self.hidden_cards.remove(card)
            self.register_known_card(card)

    def get_unknown_cards(self):
        return list(self.cards) + list(self.hidden_cards)

    def counts(self):
        return len(self.dealt_cards), len(self.cards)

    def running_count(self):
        return sum(card.hi_lo_value() for card in self.known_cards)

    def decks_remaining(self):
        return max(len(self.cards), 1) / 52

    def true_count(self):
        decks_left = self.decks_remaining()
        return self.running_count() / decks_left

    def rounded_true_count(self):
        return int(self.true_count())

    def total_cards(self):
        return self.num_decks * 52

    def penetration(self):
        return len(self.dealt_cards) / self.total_cards()

    def usage_percent(self):
        return self.penetration() * 100

    def cut_card_reached(self):
        return self.penetration() >= self.cut_card_ratio

    def needs_cut_card_prompt(self):
        return (
            self.cut_card_reached()
            and not self.cut_card_prompted
            and not self.cut_card_declined
        )

    def full_shoe_exhausted(self):
        return len(self.cards) == 0
