'''
Pull player data from raidbots.
'''

import ujson as json
import sys
import raidbots.common as common

DEFAULT_REGION = 'us'
DEFAULT_REALM = 'perenolde'
#region(us,eu), realm, player
#all lowercase
PLAYERDATA = "http://raidbots.com/json/playerdata/%s/%s/%s"


def get(player, realm=DEFAULT_REALM, region=DEFAULT_REGION):
    '''
    Pull a specific player's performance statistics from raidbots.
    '''
    player = player.lower()
    realm = realm.lower()
    region = region.lower()
    uri = PLAYERDATA % (region, realm, player.encode('utf-8'))
    print >> sys.stderr, "[INFO] Fetching %s" % repr(uri)
    data = json.loads(common.HTTP.request(uri)[1])

    return data
