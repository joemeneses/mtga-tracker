import pprint

from models.game import Game, Player
import util


def parse_jsonrpc_blob(blob):
    pass


def parse_get_decklists(blob):
    """ CHECK """
    for deck in blob["Deck.GetDeckLists"]:
        util.process_deck(deck)


def parse_event_joinqueue(blob):
    import app.mtga_app as mtga_app
    # method = 'Event.JoinQueue'
    """ CHECK """
    params = blob['params']
    deckId = params['deckId']
    return mtga_app.mtga_watch_app.player_decks[deckId].generate_library()


def parse_game_state_message(message):
    import app.mtga_app as mtga_app
    if 'zones' in message.keys():
        for zone in message['zones']:
            parse_zone(zone)
    if 'gameObjects' in message.keys():
        game_objects = message['gameObjects']
        for object in game_objects:
            card_id = object['grpId']
            instance_id = object['instanceId']
            owner = object['controllerSeatId']
            zone = object['zoneId']
            with mtga_app.mtga_watch_app.game_lock:
                player, zone = mtga_app.mtga_watch_app.game.get_owner_zone_tup(zone)
                if player:
                    assert isinstance(player, Player)
                    # I guess let's assume zone exists?
                    player.put_instance_id_in_zone(instance_id, zone)
                    zone.match_game_id_to_card(instance_id, card_id)


def parse_zone(zone_blob):
    import app.mtga_app as mtga_app
    trackable_zones = ["ZoneType_Hand", "ZoneType_Library"]
    zone_type = zone_blob["type"]
    if zone_type not in trackable_zones:
        return
    with mtga_app.mtga_watch_app.game_lock:
        zone_id = zone_blob["zoneId"]
        owner_seat = zone_blob["ownerSeatId"]
        player, zone = mtga_app.mtga_watch_app.game.get_owner_zone_tup(zone_id)
        if not player:
            player = mtga_app.mtga_watch_app.game.get_player_in_seat(owner_seat)
            zone = player.get_zone_by_name(zone_type)
            zone.zone_id = zone_id
        if 'objectInstanceIds' in zone_blob:
            for instance_id in zone_blob['objectInstanceIds']:
                player.put_instance_id_in_zone(instance_id, zone)
            cards_to_remove_from_zone = []
            for card in zone.cards:
                if card.game_id not in zone_blob['objectInstanceIds']:
                    cards_to_remove_from_zone.append(card)
            for card in cards_to_remove_from_zone:
                zone.cards.remove(card)


def parse_accept_hand(blob):
    import app.mtga_app as mtga_app
    client_message = blob['clientToGreMessage']
    response = client_message['mulliganResp']['decision']
    if response == "MulliganOption_AcceptHand":
        with mtga_app.mtga_watch_app.game_lock:
            mtga_app.mtga_watch_app.game.hero.deck.transfer_cards_to(mtga_app.mtga_watch_app.game.temp["my_mulligan"],
                                                                     mtga_app.mtga_watch_app.game.hero.hand)


def parse_gameroomstatechangedevent(blob):
    import app.mtga_app as mtga_app
    temp_players = {
        1: {},
        2: {}
    }
    game_room_info = blob["matchGameRoomStateChangedEvent"]["gameRoomInfo"]
    game_room_players = game_room_info["players"]

    for player in game_room_players:
        temp_players[player["systemSeatId"]]["player_id"] = player["userId"]

    game_room_config = game_room_info["gameRoomConfig"]

    reserved_players = game_room_config["reservedPlayers"]
    for player in reserved_players:
        temp_players[player["systemSeatId"]]["name"] = player["playerName"]

    match_config = game_room_config["matchConfig"]
    if "teams" in match_config:
        teams = match_config["teams"]
        for team in teams:
            players = team["players"]
            for player in players:
                player_seat = player["systemSeatId"]
                temp_players[player_seat]["deck"] = util.card_ids_to_card_list(player["deckCards"])
    for player_idx in [1,2]:
        if "deck" not in temp_players[player_idx]:
            temp_players[player_idx]["deck"] = []
    player1 = Player(temp_players[1]["name"], temp_players[1]["player_id"], 1, temp_players[1]["deck"])
    player2 = Player(temp_players[2]["name"], temp_players[2]["player_id"], 2, temp_players[2]["deck"])
    with mtga_app.mtga_watch_app.game_lock:
        if mtga_app.mtga_watch_app.player_id == player1.player_id:
            hero = player1
            opponent = player2
        else:
            hero = player2
            opponent = player1
        mtga_app.mtga_watch_app.game = Game(hero, opponent)  # TODO: figure out how to pick the hero


""" simple map: take keys of a dict, and keep digging until you find a callable

# I already realized this won't work, but let's just track stuff here til we have a better solution"""
# log_handler_map = {
#     ["matchGameRoomStateChangedEvent"]: parse_gameroomstatechangedevent,
# }

