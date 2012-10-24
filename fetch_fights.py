from eventlet.green import urllib2
import ujson as json
import datetime

DEFAULT_REGION = 'us'
DEFAULT_REALM  = 'perenolde'
#region(us,eu), realm, player
#all lowercase
PLAYERDATA = "http://raidbots.com/json/playerdata/%s/%s/%s"

BANNED_FIGHTS = ["Garajal_the_Spiritbinder"]
#fight name, mode(10N,25N,10H,25H), spec id
#Case matters
FIGHTDATA = "http://raidbots.com/json/ebcd/%s/%s/%s/"

def get_player(player, realm=DEFAULT_REALM, region=DEFAULT_REGION):
    player = player.lower()
    realm = realm.lower()
    region = region.lower()
    return json.load(urllib2.urlopen(PLAYERDATA % (region, realm, player)))

PERCENTILE_MAP = {
    'max' : 100,
    'min' : 0,
    'median' : 50,
}

def get_fight(spec_id, mode, fight_name):
    source = {
        'spec_id'   : spec_id,
        'mode'      : mode,
        'fight_name': fight_name,
    }
    fight_data = json.load(urllib2.urlopen(FIGHTDATA % (fight_name, mode, spec_id)))

    if len(fight_data) == 0:
        return {'source':source}
    
    output = {
        'source' : source,
        'percent' : {},
        'stddev' : [],
    }
    for k in fight_data:
        raw = fight_data[k]
        if k == 'stddev':
            output['stddev'] = {}
            o = output['stddev']
        elif k in PERCENTILE_MAP:
            k = PERCENTILE_MAP[k]
            output['percent'][k] = {}
            o = output['percent'][k]
        else:
            k = int(k[1:])
            output['percent'][k] = {}
            o = output['percent'][k]
        
        
        
        for x in raw:
            r = long(x[0])
            v = x[1]
            o[r] = v
    return output