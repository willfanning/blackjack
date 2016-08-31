import random
import time
from collections import OrderedDict
from tabulate import tabulate


class Card:
    def __init__(self, value, rank, suit):
        self.value = value
        self.rank = rank
        self.suit = suit
        self.title = rank + ' ' + suit

    def __str__(self):
        return '{} {}'.format(self.rank, self.suit)


class Deck:
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    SUITS = ["\u2764", "\u2666", "\u2660", "\u2663"]
    VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
    NUM_DECKS = 6

    @classmethod
    def new_deck(cls):
        """Create one shuffled deck per game, pop off cards as needed"""
        deck = []
        for suit in Deck.SUITS:
            for value, rank in zip(Deck.VALUES, Deck.RANKS):
                deck.append(Card(value, rank, suit))
        deck *= Deck.NUM_DECKS
        random.shuffle(deck)
        return deck


class Hand:
    def __init__(self):
        self.cards = []
        self.total = 0
        self.hand_bet = 0
        self.payout = 0
        self.insurance = 0
        self.result = ''
        self.is_resolved = False
        self.is_insured = False
        self.split = False
        self.stand = False
        self.surrender = False
        self.bust = False
        self.blackjack = False

    def check_bust(self):
        if self.total > 21:
            self.bust = True
            self.is_resolved = True

    def update(self):
        """Recalculate hand total, soften aces, check for bust"""
        self.total = 0
        for card in self.cards:
            self.total += card.value
        for card in self.cards:
            if self.total > 21 and card.value == 11:
                card.value = 1
                self.total -= 10
        self.check_bust()

    def ace_up(self):
        return self.cards[1].value == 11

    def has_blackjack(self):
        self.update()
        if self.total == 21:
            self.blackjack = True
            self.is_resolved = True
            return True
        else:
            return False

    def action_state(self):
        """Additional actions available to a player based on their holdings
        If hand not resolved, hit and stand always available. Return int:
            0 - none, hand resolved
            1 - split, surrender, double
            2 - surrender, double
            3 - (prev. split) re-split, double
            4 - (prev. split) double
            5 - none

            Note extra consideration for [A, A] hands as update() alters A value,
            but hand can still be split
            """
        if self.total == 21:
            if len(self.cards) == 2:
                print("Blackjack!")
                self.blackjack = True
                self.is_resolved = True
                return 0
            else:
                print("Twenty-one!")
                self.is_resolved = True
                return 0
        if len(self.cards) == 2:
            if not self.split:
                if self.cards[0].rank == 'A' and self.cards[1].rank == 'A':
                    return 1
                if self.cards[0].value == self.cards[1].value:
                    return 1
                else:
                    return 2
            else:
                if self.cards[0].rank == 'A' and self.cards[1].rank == 'A':
                    return 3
                if self.cards[0].value == self.cards[1].value:
                    return 3
                else:
                    return 4
        else:
            return 5

    def card_list(self):
        """Print out formatted hand for game use"""
        self.update()
        time.sleep(0.5)
        print()
        for i, card in enumerate(self.cards):
            print('Card {}: {}'.format((i+1), card))
        print('-------------')
        print('Total:', self.total)
        if self.bust:
            print('     (BUST)')

    def hit(self, deck):
        card = deck.pop()
        self.cards.append(card)
        time.sleep(0.33)
        self.update()
        print()
        print('--> []')


class Player:
    def __init__(self, name, bankroll):
        self.hands = []
        self.name = name.upper()
        self.bankroll = bankroll
        self.bet = 0
        self.change_bet = True


class GameState:
    def __init__(self):
        self.players = []
        self.hand_number = 1
        self.dealer = None

    def run_game(self):
        """Play through one hand around the table"""
        self.place_bets()

        deck = Deck.new_deck()
        self.deal_cards(deck)

        if self.dealer.ace_up():
            self.offer_insurance()
            self.check_hole_card()

        self.resolve_players(deck)
        self.resolve_dealer(deck)
        self.table()

        print(' - NEW HAND - ')
        print()
        self.hand_number += 1

        self.new_game_options()

    def place_bets(self):
        for player in self.players:
            if player.change_bet:
                player.bet = 0
                print(player.name)
                print('Place your bet (Min. ${!s} / Max. ${!s}):'.format(Game.min_bet, player.bankroll))
                while not player.bet >= Game.min_bet and player.bet <= player.bankroll:
                    bet = float(input('>>> $'))
                    if bet < Game.min_bet:
                        print('BET NOT ACCEPTED')
                        print('Min. bet $', Game.min_bet)
                        print('Place your bet:')
                        continue
                    if bet > player.bankroll:
                        print('BET NOT ACCEPTED')
                        print('Max. bet $', player.bankroll)
                        print('Place your bet:')
                        continue
                    else:
                        player.bet = bet
            player.bankroll -= player.bet
            print()

    def deal_cards(self, deck):
        for player in self.players:
            hand = Hand()
            hand.hit(deck)
            hand.hit(deck)
            player.hands.append(hand)
        self.dealer = Hand()
        self.dealer.hit(deck)
        self.dealer.hit(deck)

    def offer_insurance(self):
        for player in self.players:
            hand = player.hands[0]
            self.tableau(player)
            hand.card_list()
            print()
            if player.bankroll < player.bet * 0.5:
                print('Not enough $ to buy insurance')
                continue
            if hand.has_blackjack():
                print('You have blackjack!')
                print('Take even money? Enter [Y]es or [N]o:')
                while True:
                    even_money = input('>>> ').upper()
                    if even_money == 'Y':
                        hand.is_insured = True
                        print('Even money taken')
                        break
                    elif even_money == 'N':
                        print('No insurance')
                        break
                    else:
                        continue
            else:
                print('Insurance? Enter [Y]es or [N]o:')
                while True:
                    insurance = input('>>> ').upper()
                    if insurance == 'Y':
                        hand.is_insured = True
                        hand.insurance = player.bet / 2
                        player.bankroll -= hand.insurance
                        print('Insurance bought: $', hand.insurance)
                        break
                    elif insurance == 'N':
                        print('No insurance')
                        break
                    else:
                        continue

    def check_hole_card(self):
        print()
        print('Dealer checking hole card...')
        time.sleep(1)
        if self.dealer.has_blackjack():
            print()
            print('Dealer reveals blackjack')
            self.dealer.card_list()
            for player in self.players:
                player.hands[0].is_resolved = True
        else:
            pass

    def tableau(self, player):
        print()
        print('{0}:   [Hand #{1!s}]'.format(player.name, self.hand_number))
        print('Bankroll: $' + str(player.bankroll))
        print('Bet: $' + str(player.bet))
        print('[Dealer shows {!s}]'.format(self.dealer.cards[1]))

    def resolve_players(self, deck):
        for player in self.players:
            for hand in player.hands:
                hand.hand_bet = player.bet
                if self.dealer.blackjack:
                    return
                self.resolve_player_hand(player, hand, deck)

    def resolve_player_hand(self, player, hand, deck):
        self.tableau(player)
        while not hand.is_resolved:
            hand.card_list()
            print()
            options = self.build_options(player, hand, deck)
            if not options:
                break
            self.select_option(options)
            continue

        if hand.stand or hand.surrender or hand.total == 21:
            print('------------------------')
            time.sleep(0.5)
        else:
            hand.card_list()
            print('------------------------')
            time.sleep(0.5)

    def build_options(self, player, hand, deck):
        options = OrderedDict()
        state = hand.action_state()

        if state == 0:
            return

        options['H'] = {'desc': '[H]it', 'method': hand.hit, 'params': [deck]}
        options['S'] = {'desc': '[S]tand', 'method': self.stand, 'params': [hand]}

        if state < 5:
            options['D'] = {'desc': '[D]ouble',
                            'method': self.double_down,
                            'params': [player, hand, deck]}
        if state in [1, 3]:
            options['SP'] = {'desc': '[SP]lit',
                             'method': self.split,
                             'params': [player, hand, deck]}
        if state < 3:
            options['SU'] = {'desc': '[SU]rrender',
                             'method': self.surrender,
                             'params': [player, hand, deck]}

        return options

    def select_option(self, options):
        prompt = 'Select: {}'.format(', '.join(o['desc'] for o in options.values()))
        print(prompt)
        action = ''
        while True:
            action = input('>>> ').upper()
            if action not in options:
                continue
            else:
                break

        return options[action]['method'](*options[action]['params'])

    def surrender(self, hand):
        hand.is_resolved = True
        hand.surrender = True
        print()
        print('Surrender')

    def stand(self, hand):
        hand.is_resolved = True
        hand.stand = True
        print()
        print('Stand on', hand.total)

    def double_down(self, player, hand, deck):
        print()
        if hand.hand_bet > player.bankroll:
            print('Not enough $ to double down')
            print('Enter a different action')
            return
        print('Double down')
        hand.stand = True
        hand.is_resolved = True
        player.bankroll -= player.bet
        hand.hand_bet *= 2
        hand.hit(deck)
        hand.card_list()

    def split(self, player, hand, deck):
        print()
        if hand.hand_bet > player.bankroll:
            print('Not enough $ to split')
            print('Enter a different action')
            return
        if hand.cards[0].rank == 'A' and hand.cards[1].rank == 'A':
            hand.cards[0].value = 11
            hand.cards[1].value = 11
        player.bankroll -= player.bet
        new_hand = Hand()
        hand.split = True
        new_hand.split = True
        split_card = hand.cards.pop()
        print('--> ' + split_card.title + ' to new hand')
        new_hand.cards.append(split_card)
        hand.hit(deck)
        new_hand.hit(deck)
        player.hands.append(new_hand)
        print()
        print('Split')
        self.tableau(player)

    def need_not_resolve(self):
        if self.dealer.blackjack:
            return True
        player_out = 0
        player_hands = 0
        for player in self.players:
            for hand in player.hands:
                player_hands += 1
                if hand.bust or hand.surrender or hand.blackjack:
                    player_out += 1
        if player_out == player_hands:
            return True
        else:
            return False

    def resolve_dealer(self, deck):
        print()
        if self.need_not_resolve():
            return
        print('Resolving Dealer Hand:')
        while not self.dealer.is_resolved:
            if self.dealer.total < 17:
                self.dealer.card_list()
                self.dealer.hit(deck)
                continue
            elif self.dealer.total == 17:
                if self.dealer.cards[0].value == 11 or self.dealer.cards[1].value == 11:
                    self.dealer.card_list()
                    self.dealer.hit(deck)
                    continue
                else:
                    break
            elif 17 < self.dealer.total <= 21:
                break

        self.dealer.card_list()
        print('------------------------')
        print()
        time.sleep(0.5)

    def hand_result(self, player, hand):
        if hand.bust:
            hand.result = 'BUST'

        elif hand.surrender:
            hand.result = 'SURR.'
            hand.payout = hand.hand_bet * 0.5
            player.bankroll += hand.payout

        elif self.dealer.bust:
            hand.result = 'WIN'
            hand.payout = hand.hand_bet
            player.bankroll += hand.hand_bet + hand.payout

        elif self.dealer.blackjack:
            if not hand.blackjack and not hand.is_insured:
                hand.result = 'LOSS'
            elif not hand.blackjack and hand.is_insured:
                hand.result = 'INSUR.'
                hand.payout = hand.insurance * 2
                player.bankroll += hand.payout + hand.insurance
            elif hand.blackjack and hand.is_insured:
                hand.result = 'EVEN$'
                hand.payout = hand.hand_bet
                player.bankroll = hand.hand_bet + hand.payout
            elif hand.blackjack and not hand.is_insured:
                hand.result = 'PUSH'
                player.bankroll += hand.hand_bet

        elif hand.blackjack:
            hand.result = 'WIN-BJ'
            hand.payout = hand.hand_bet * 1.5
            player.bankroll += hand.hand_bet + hand.payout

        elif hand.total > self.dealer.total:
            hand.result = 'WIN'
            hand.payout = hand.hand_bet
            player.bankroll += hand.hand_bet + hand.payout

        elif self.dealer.total == hand.total:
            hand.result = 'PUSH'
            player.bankroll += hand.hand_bet

        else:
            hand.result = 'LOSS'

    def table(self):
        table = []
        headers = ['PLAYER', 'TOTAL', 'RESULT', 'BET', 'PAYOUT', 'BANKROLL']
        for player in self.players:
            for hand in player.hands:
                self.hand_result(player, hand)
                table.append([player.name, hand.total, hand.result,
                              hand.hand_bet, hand.payout, player.bankroll])
        print(tabulate(table, headers=headers, numalign='center',
                       stralign='center', floatfmt='0.2f'))
        print()

    def new_game_options(self):
        self.dealer = None
        for player in self.players[:]:
            player.hands.clear()
            if player.bankroll < Game.min_bet:
                print(player.name + ':')
                print('Not enough $ to continue. Better luck next time.')
                print()
                self.players.remove(player)
                break
            print(player.name + ':')
            print('[R]ebet, [C]hange bet, or [Q]uit:')
            while True:
                action = input('>>> ').upper()
                if action == 'R' and player.bet > player.bankroll:
                    action = 'C'
                    print('Bet too large for current bankroll.')
                if action == 'R':
                    player.change_bet = False
                    print('Rebet')
                    break
                if action == 'C':
                    player.change_bet = True
                    print('Change bet')
                    break
                if action == 'Q':
                    self.players.remove(player)
                    print('Goodbye')
                    break
            print()


class Game:
    min_bet = 5

    def __init__(self):
        print()
        print('House rules:')
        print()
        print('- The game is played using six decks,')
        print('    which are reshuffled after each hand.')
        print('- Dealer hits on soft 17')
        print('- Blackjack pays 3 : 2')
        print('- Insurance pays 2 : 1')
        print('- A split ace and ten-value card does not make Blackjack')
        print('- Surrender any first two cards')
        print()

    def new_game(self):
        g = GameState()
        print('Welcome to Blackjack!')
        print()
        print('Enter [B] to begin:')
        while True:
            enter_b = input('>>> ').upper()
            if enter_b == 'B':
                break
            else:
                continue
        print()
        print('Enter the number of players:')
        num_players = 0
        while True:
            num_players = int(input('>>> '))
            if num_players > 0:
                break
            else:
                continue
        print()
        for i in range(num_players):
            print('Player', (i + 1))
            print('Enter name:')
            name = input('>>> ')
            print('Enter bankroll (Min. ${!s}):'.format(self.min_bet))
            bankroll = float(input('>>> $'))
            print()
            g.players.append(Player(name, bankroll))
        return g

if __name__ == '__main__':
    g = Game()
    gs = g.new_game()
    while len(gs.players) > 0:
        gs.run_game()
    print('Thanks for playing')
