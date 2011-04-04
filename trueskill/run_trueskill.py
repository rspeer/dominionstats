import pymongo
con = pymongo.Connection()
DB = con.test
games = DB.games

from trueskill import db_update_trueskill

def results_to_ranks(results):
    sorted_results = sorted(results)
    return [sorted_results.index(r) for r in results]

def run_trueskill_players():
    collection = DB.trueskill_players
    for game in games.find():
        if len(game['decks'] >= 2):
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

