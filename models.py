# blackjack/models.py

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def blackjack_value(self):
        if self.rank in ["J", "Q", "K"]:
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)

    def hi_lo_value(self):
        if self.rank in ["2", "3", "4", "5", "6"]:
            return 1
        if self.rank in ["7", "8", "9"]:
            return 0
        return -1


@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)
    status: str = "WAITING"
    result: str = ""
    is_split_hand: bool = False

    def add_card(self, card: Card):
        self.cards.append(card)

    def value(self):
        total = sum(c.blackjack_value() for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")

        while total > 21 and aces:
            total -= 10
            aces -= 1

        return total

    def is_soft(self):
        total = sum(c.blackjack_value() for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")

        while total > 21 and aces:
            total -= 10
            aces -= 1

        return aces > 0

    def is_blackjack(self):
        return len(self.cards) == 2 and self.value() == 21 and not self.is_split_hand

    def visible_cards(self, hide_last=False):
        if not self.cards:
            return "[]"

        if hide_last and len(self.cards) > 1:
            return "[" + str(self.cards[0]) + ", HIDDEN]"

        return "[" + ", ".join(str(c) for c in self.cards) + "]"


@dataclass
class Player:
    name: str
    hands: List[Hand] = field(default_factory=lambda: [Hand()])


@dataclass
class Dealer:
    name: str = "Dealer"
    hand: Hand = field(default_factory=Hand)
