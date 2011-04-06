from utils import get_mongo_connection
con = get_mongo_connection()
DB = con.test
games = DB.games

from trueskill.trueskill import db_update_trueskill, SetParameters
SetParameters(gamma=0.0001)

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
                i = 2
                while open_name in openings:
                    # a cheap way to uniquify opening names.
                    # Silver+Silver2 means you are the second player to
                    # open Silver+Silver this game. *shrug*
                    if i == 2:
                        idx = openings.index(open_name)
                        openings[idx] = 'open1:' + ('+'.join(opening))
                    open_name = ('open%d:' % i) + ('+'.join(opening))
                    i += 1
                    dups = True
                openings.append(open_name)
                nturns = len(deck['turns'])
                if deck['resigned']:
                    vp = -1000
                else:
                    vp = deck['points']
                results.append((-vp, nturns))
                teams.append([open_name])
            if not dups:
                ranks = results_to_ranks(results)
                team_results = [
                    (team, [1.0], rank)
                    for team, rank in zip(teams, ranks)
                ]
                db_update_trueskill(team_results, collection)

