#!/usr/bin/python

import collections

PRIMATIVES = [dict, str, int, list, float, unicode]

def ToPrimative(val):
    if hasattr(val, 'ToPrimativeObject'):
        return val.ToPrimativeObject()
    assert type(val) in PRIMATIVES, val
    return val

class PrimativeConversion:
    def ToPrimativeObject(self):
        ret = {}
        for k, v in self.__dict__.iteritems():
            ret[k] = ToPrimative(v)
        return ret

    def FromPrimativeObject(self, obj):
        # Get rid of _id because it's something that mongo injects into our
        # objects, and it's not really natural to the objects themselves.
        obj_keys_except_id = set(obj.keys()) - set(['_id'])
        unicoded_keys = set(map(unicode, self.__dict__.keys()))
        assert unicoded_keys == obj_keys_except_id, (
            '%s != %s' % (str(unicoded_keys),  str(obj_keys_except_id)))
        for k in obj_keys_except_id:
            if hasattr(self.__dict__[k], 'FromPrimativeObject'):
                self.__dict__[k].FromPrimativeObject(obj[k])
            else:
                assert type(obj[k]) in PRIMATIVES, obj[k]
                self.__dict__[k] = obj[k]

class ConvertibleDefaultDict(PrimativeConversion):
    def __init__(self, value_type, key_type = str):
        self.value_type = value_type
        self.key_type = key_type
        self.backing_dict = collections.defaultdict(value_type)

    def __getattr__(self, key):
        return getattr(self.backing_dict, key)

    def ToPrimativeObject(self):
        ret = {}
        for key, val in self.backing_dict.iteritems():
            if type(key) == unicode:
                key = key.encode('utf-8')
            else:
                key = str(key)
            ret[key] = ToPrimative(val)
        return ret

    def FromPrimativeObject(self, obj):
        for k, v in obj.iteritems():
            if k == '_id': continue
            val = self.value_type()
            if hasattr(val, 'FromPrimativeObject'):
                val.FromPrimativeObject(v)
            else: 
                val = v
            self.backing_dict[self.key_type(k)] = val

    def __eq__(self, obj):
        return self.backing_dict == obj.backing_dict



# TODO: Get rid of this class, it really conflates two concepts, 
# IncrementalScanning and persistent objects.  It would be cleaner to have
# them separate, and the IncrementalScanner already exists.
class PersistentIncrementalWrapper:
    # wrapped_obj must have a max_game_id field
    def __init__(self, wrapped_obj, obj_id, persistent_collection):
        self.wrapped_obj = wrapped_obj
        self.obj_id = obj_id
        self.persistent_collection = persistent_collection
        self.max_game_id = ''
        prim_obj = self.persistent_collection.find_one({'_id': obj_id})
        if prim_obj:
            self.wrapped_obj.FromPrimativeObject(prim_obj)
            # is this + '1' neccessary?
            self.max_game_id = self.wrapped_obj.max_game_id + '1'

    def Scan(self, scan_collection, scan_query, ):
        if not '_id' in scan_query:
            scan_query['_id'] = {}
        scan_query['_id']['$gt'] = max(self.max_game_id, 
                                       scan_query['_id'].get('$gt'))
        for item in scan_collection.find(scan_query):
            self.max_game_id = max(item['_id'], self.max_game_id)
            yield item

    def Save(self):
        self.wrapped_obj.max_game_id = self.max_game_id
        prim_obj = self.wrapped_obj.ToPrimativeObject()
        prim_obj['_id'] = self.obj_id
        prim_obj['max_game_id'] = self.max_game_id
        self.persistent_collection.save(prim_obj, safe = True)

if __name__ == '__main__':
    import pymongo
    c = pymongo.Connection()
    db = c.test
    coll = db.prim
    prim_a['_id'] = ''
    coll.save(prim_a, safe='true')

    a_from_db = list(coll.find())[0]
    new_a = A()
    new_a.FromPrimativeObject(a_from_db)
    assert new_a.foo == a.foo
    assert new_a.bar == a.bar

