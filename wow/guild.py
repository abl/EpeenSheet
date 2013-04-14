from eventlet.green import urllib2
import ujson as json

API_ROOT="http://us.battle.net/api/wow"
GUILD_API = "/guild/%s/%s?fields=%s"

MEMBERS = "members"
ACHIEVEMENTS = "achievements"
NEWS = "news"
CHALLENGE = "challenge"

VALID_FIELDS = set([MEMBERS, ACHIEVEMENTS, NEWS, CHALLENGE])

def _is_string(var):
    c = var.__class__
    return c is unicode or c is str

def _wrap_arr(var):
    if _is_string(var):
        return [var]
    else:
        return var

def get(guild, realm, fields=[]):
    fields = _wrap_arr(fields)
    fields = [field for field in fields if field in VALID_FIELDS]
    
    guild = urllib2.quote(guild)
    realm = urllib2.quote(realm)
    data = json.load(urllib2.urlopen(API_ROOT + GUILD_API % (realm, guild, ",".join(fields))))
    
    return data