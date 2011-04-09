from utils import get_mongo_connection
con = get_mongo_connection()
DB = con.test
games = DB.games

from trueskill.trueskill import db_update_trueskill, get_skill, get_stdev

def results_to_ranks(results):
    sorted_results = sorted(results)
    return [sorted_results.index(r) for r in results]

def run_trueskill_players():
    collection = DB.trueskill_players
    collection.remove()
    collection.ensure_index('name')
    for game in games.find():
        if len(game['decks']) >= 2:
            players = []
            results = []
            for deck in game['decks']:
                nturns = len(deck['turns'])
                if deck['resigned']:
                    vp = -1000
                else:
                    vp = deck['points']
                results.append((-vp, nturns))
                players.append(deck['name'])
            ranks = results_to_ranks(results)
            team_results = [
                ([player], [1.0], rank)
                for player, rank in zip(players, ranks)
            ]
            db_update_trueskill(team_results, collection)

def run_trueskill_openings():
    collection = DB.trueskill_openings
    player_collection = DB.trueskill_players
    player_collection.remove()
    player_collection.ensure_index('name')
    player_collection.ensure_index('mu')
    player_collection.ensure_index('floor')
    player_collection.ensure_index('ceil')
    collection.remove()
    collection.ensure_index('name')
    collection.ensure_index('mu')
    collection.ensure_index('floor')
    collection.ensure_index('ceil')
    for game in games.find():
        if len(game['decks']) >= 2 and len(game['decks'][1]['turns']) >= 5:
            teams = []
            results = []
            openings = []
            dups = False
            for deck in game['decks']:
                opening = deck['turns'][0].get('buys', []) +\
                          deck['turns'][1].get('buys', [])
                opening.sort()
                open_name = 'open:'+ ('+'.join(opening))
                if open_name in openings:
                    dups = True
                openings.append(open_name)
                nturns = len(deck['turns'])
                if deck['resigned']:
                    vp = -1000
                else:
                    vp = deck['points']
                results.append((-vp, nturns))
                player_name = deck['name']
                player_info = {
                    'name': player_name,
                    'mu': get_skill(player_name, player_collection),
                    'sigma': get_stdev(player_name, player_collection)
                }

                teams.append([open_name, player_info])
            ranks = results_to_ranks(results)
            if not dups:
                team_results = [
                    (team, [0.5, 0.5], rank)
                    for team, rank in zip(teams, ranks)
                ]
                db_update_trueskill(team_results, collection)
            player_results = [
                ([team[1]], [1.0], rank)
                for team, rank in zip(teams, ranks)
            ]
            db_update_trueskill(player_results, player_collection)

def update_plays():
    DB.trueskill_openings.ensure_index('cards')
    for opening in DB.trueskill_openings.find():
        key = opening['name']
        cards = key[5:].split('+')
        if cards == ['']:
            cards = []
        print cards
        DB.trueskill_openings.update(
            {'name': key},
            {'$set': {'cards': cards}}
        )

