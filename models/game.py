import models.set as set
from models.card import GameCard


class Player(object):
    def __init__(self, player_name, player_id, seat, deck_cards=None):
        self.player_name = player_name
        self.player_id = player_id
        self.seat = seat

        self.library = set.Library("{}'s hand".format(self.player_name), deck_cards)
        self.hand = set.Zone("{}'s hand".format(self.player_name))
        self.graveyard = set.Zone("{}'s graveyard".format(self.player_name))
        self.exile = set.Zone("{}'s exile".format(self.player_name))
        self.unknown = set.Zone("{}'s unknown zones".format(self.player_name))

        self.all_zones = [self.library, self.hand, self.graveyard, self.exile, self.unknown]

    def get_zone_by_name(self, name):
        if name == "ZoneType_Hand":
            return self.hand
        elif name == "ZoneType_Library":
            return self.library

    def get_location_of_instance(self, instance_id):
        for zone in self.all_zones:
            for card in zone.cards:
                if card.game_id == instance_id:
                    return card, zone
        return None, None

    def put_instance_id_in_zone(self, instance_id, zone):
        card, current_zone = self.get_location_of_instance(instance_id)
        if current_zone:
            current_zone.transfer_card_to(card, zone)
        else:
            unknown_card = GameCard("unknown", -1, -1, -1, instance_id)
            zone.cards.append(unknown_card)


class Game(object):
    def __init__(self, hero, opponent):
        self.hero = hero
        assert isinstance(self.hero, Player)
        self.opponent = opponent
        assert isinstance(self.opponent, Player)

        self.identified_game_objects = {}
        self.temp = {}

    def get_owner_zone_tup(self, zone_id):
        hero_zones = [self.hero.library, self.hero.hand, self.hero.graveyard, self.hero.exile, self.hero.unknown]
        opponent_zones = [self.opponent.library, self.opponent.hand, self.opponent.graveyard, self.opponent.exile,
                          self.opponent.unknown]
        owner_zones = [(self.hero, hero_zones),
                       (self.opponent, opponent_zones)]
        for owner_zone in owner_zones:
            for zone in owner_zone[1]:
                if zone.zone_id == zone_id:
                    return owner_zone[0], zone
        return None, None

    def get_player_in_seat(self, seat_id):
        if self.hero.seat == seat_id:
            return self.hero
        elif self.opponent.seat == seat_id:
            return self.opponent
        else:
            print("NOTHING TO RETURN OH NO")