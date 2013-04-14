"""
Pull EBCD data from Raidbots.
"""

#from eventlet.green import urllib2
import ujson as json
#import datetime
import raidbots.common as common

BANNED_FIGHTS = ["Garajal_the_Spiritbinder", "Protectors_of_the_Endless"]
#fight name, mode(10N,25N,10H,25H), spec id
#Case matters
FIGHTDATA = "http://raidbots.com/json/ebcd/%s/%s/%s/"

NAME_MAP = {
    'Blade_Lord_Tayak': "Blade_Lord_Ta'yak",
    'Imperial_Vizier_Zorlok': "Imperial_Vizier_Zor'lok",
}


def get(spec_id, mode, fight_name):
    """
    Pull data for a specific fight, spec, and difficulty.
    """
    source = {
        'spec_id': str(spec_id),
        'mode': mode,
        'fight_name': fight_name,
    }
    if fight_name in NAME_MAP:
        fight_name = NAME_MAP[fight_name]
    fight_data = json.loads(common.HTTP.request(
        FIGHTDATA % (fight_name, mode, spec_id))[1])

    if len(fight_data) == 0:
        return {'source': source}

    output = {
        'source': source,
        'percent': {},
        'stddev': [],
    }
    for key in fight_data:
        raws = fight_data[key]
        if key == 'stddev':
            output['stddev'] = {}
            val = output['stddev']
        elif key in common.PERCENTILE_MAP:
            key = common.PERCENTILE_MAP[key]
            output['percent'][key] = {}
            val = output['percent'][key]
        else:
            key = int(key[1:])
            output['percent'][key] = {}
            val = output['percent'][key]

        for raw in raws:
            #TBD: Postprocessing?
            subkey = long(raw[0])/1000L/60L/60L/24L
            subvalue = raw[1]
            val[subkey] = subvalue

    return output
