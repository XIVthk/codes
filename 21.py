#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random as r
from dataclasses import dataclass
import re

CARDS = {"2S": 2, "3S": 3, "4S": 4, "5S": 5, "6S": 6, "7S": 7, "8S": 8, "9S": 9, "10S": 10, "JS": 10, "QS": 10, "KS": 10, "AS": (1, 11),
         "2H": 2, "3H": 3, "4H": 4, "5H": 5, "6H": 6, "7H": 7, "8H": 8, "9H": 9, "10H": 10, "JH": 10, "QH": 10, "KH": 10, "AH": (1, 11),
         "2D": 2, "3D": 3, "4D": 4, "5D": 5, "6D": 6, "7D": 7, "8D": 8, "9D": 9, "10D": 10, "JD": 10, "QD": 10, "KD": 10, "AD": (1, 11),
         "2C": 2, "3C": 3, "4C": 4, "5C": 5, "6C": 6, "7C": 7, "8C": 8, "9C": 9, "10C": 10, "JC": 10, "QC": 10, "KC": 10, "AC": (1, 11)}

class StopDealing(Exception):
    pass

@dataclass
class Card:
    suit: str
    value: str
    point: int | tuple[int, int]

class Cardpool:
    def __init__(self, cards: dict[str, int | tuple[int, int]]):
        self.cards = list(cards.keys())
        self.shuffle()

    def shuffle(self):
        r.shuffle(self.cards)

    def deal(self) -> Card:
        if not self.cards:
            raise StopDealing("No more cards to deal.")
        rc = self.cards.pop(0)
        suit = rc[-1]
        value = rc[:-1]
        point = CARDS[rc]
        return Card(suit=suit, value=value, point=point)
    
    def __len__(self):
        return len(self.cards)
    
    def reset(self):
        self.__init__(CARDS)


class Hand:
    def __init__(self, cp: Cardpool):
        self.STAND = False
        self.handcards: list[Card] = []
        self.cardpool = cp
        self.total = 0
        self.BUST = False
    
    def deal(self):
        try:
            self.handcards.append(self.cardpool.deal())
        except StopDealing:
            self.cardpool.reset()
            self.handcards.append(self.cardpool.deal())
        self.check()

    def reset(self):
        self.handcards = []
        try:
            self.handcards.append(self.cardpool.deal())
            self.handcards.append(self.cardpool.deal())
        except StopDealing:
            self.handcards = []
            self.cardpool.reset()
            self.handcards.append(self.cardpool.deal())
            self.handcards.append(self.cardpool.deal())
        self.check()
    
    def check(self):
        self.total = sum(card.point if isinstance(card.point, int) else max(card.point) for card in self.handcards)
        total = self.total
        aces = [i for i, card in enumerate(self.handcards) if isinstance(card.point, tuple)]
        for i in aces:
            if total <= 21:
                break
            # Turn Ace from 11 to 1
            card = self.handcards[i]
            self.handcards[i] = Card(card.suit, card.value, 1)
            total -= 10
        self.total = total
        if total > 21:
            self.BUST = True
    
    def double_down(self):
        self.deal()
        self.STAND = True
    
    def stand(self):
        self.STAND = True
    
    def get_total(self):
        self.check()
        return self.total
    
    def get_handcards(self):
        suits = {
            "S": "♠",
            "H": "♥",
            "D": "♦",
            "C": "♣"
        }
        hdc = ""
        for card in self.handcards:
            hdc += f"   - {suits[card.suit]} {card.value} ({card.point}) \n"
        return hdc
    
    def get_status(self):
        return "Stand" if self.STAND else "Bust" if self.BUST else "Playing"


class AIHand(Hand):
    def __init__(self, cp: Cardpool):
        super().__init__(cp)
    
    def check(self):
        self.total = sum(card.point if isinstance(card.point, int) else max(card.point) for card in self.handcards)
        total = self.total
        aces = [i for i, card in enumerate(self.handcards) if isinstance(card.point, tuple)]
        for i in aces:
            if total <= 21:
                break
            # Turn Ace from 11 to 1
            card = self.handcards[i]
            self.handcards[i] = Card(card.suit, card.value, 1)
            total -= 10
        self.total = total
        if total > 21:
            # AI will never bust, it will just stand if total exceeds 21
            self.STAND = True

    def decide(self):
        # Simple AI strategy: hit if total is less than 17, otherwise stand
        if self.get_total() < 17:
            self.deal()
        else:
            self.stand()
    
    def get_handcards(self):
        suits = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
        desc = ["   - Hidden Card"]
        for card in self.handcards[1:]:
            desc.append(f"   - {suits[card.suit]} {card.value} ({card.point})")
        return "\n".join(desc) + "\n"

    def get_final_handcards(self):  
        suits = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
        rtn = []
        for card in self.handcards:
            rtn.append(f"   - {suits[card.suit]} {card.value} ({card.point})")
        return "\n".join(rtn) + "\n"

class GameStart:
    def __init__(self, cp: Cardpool, hand: Hand, aih: AIHand):
        self.running = True
        self.cp = cp
        self.hand = hand
        self.aih = aih
        self.hand.reset()
        self.aih.reset()
        self.t = 1
        self.doubled = False
        self.turn()
    
    def turn(self, nohint: bool = False):
        if not nohint:
            print(f"Turn {self.t}")
            print("=" * 30)
            print(f"({self.hand.get_status()})Your hand: Total = {self.hand.get_total()}\n{self.hand.get_handcards()}")
            print(f"({self.aih.get_status()})AI's hand: Total = ?\n{self.aih.get_handcards()}")
        if self.hand.STAND and self.aih.STAND:
            self.end()
            return 
        if not self.hand.STAND:
            inp = "Choose an action: (H)it, (S)tand:"
            if self.t == 1:
                inp += "\b, (D)ouble Down:"
            action = input(inp).strip().upper()
            if action == "H":
                self.hand.deal()
            elif action == "S":
                self.hand.stand()
            elif action == "D":
                if self.t == 1:
                    self.hand.double_down()
                    self.doubled = True
                else:
                    print("Cannot double down.")
                    self.turn(True)
            else:
                print("Invalid action. Please choose H, S, or D.")
                self.turn(True)
        if not self.aih.STAND:
            self.aih.decide()
        if self.hand.BUST:
            print("You busted, Waiting for AI to finish...")
            self.hand.stand()
        self.t += 1
        self.turn()
    
    def end(self):
        print("=" * 30)
        print(f"Final Your hand: Total = {self.hand.get_total()}\n{self.hand.get_handcards()}{'   - Bust' if self.hand.get_total() > 21 else '   - Doubled' if self.doubled else ''}")
        print(f"Final AI hand: Total = {self.aih.get_total()}\n{self.aih.get_final_handcards()}{'   - Bust' if self.aih.get_total() > 21 else ''}")
        if self.hand.get_total() > 21 and not self.aih.get_total() > 21:
            print("You bust! AI wins.")
        elif self.aih.get_total() > 21 and not self.hand.get_total() > 21:
            print("AI busts! You win.")
        elif self.hand.get_total() > 21 and self.aih.get_total() > 21:
            print("Both bust! It's a tie.")
        elif self.hand.get_total() > self.aih.get_total():
            print("You win!")
        elif self.aih.get_total() > self.hand.get_total():
            print("AI wins!")
        else:
            print("It's a tie!")
        
if __name__ == "__main__":
    cp = Cardpool(CARDS)
    hand = Hand(cp)
    aih = AIHand(cp)
    game = GameStart(cp, hand, aih)