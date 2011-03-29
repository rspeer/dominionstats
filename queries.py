import pymongo

if __name__ == '__main__':
    c = pymongo.Connection()
    db = c.test
    games = db.games
    ct = 0
    print games.find({'players': 'rrenaud'})
    for g in games.find({'players': 'rrenaud'}).min({'_id': 'game-2011'}):
        print g['_id']
    #print games.find({'turns.plays': ["Fishing Village"]}).count()
    #print games.find({'turns': { 
        # $elemMatch: {'plays': 'Fishing Village'} 
        #          }
        #          }).count()
                     
