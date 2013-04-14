"""
Generate a nice static graph of raid guild performance based on
"""

import raidbots.player
import raidbots.ebcd
import bisect
import datetime
import sys
from numpy import average, percentile
from wow import guild

OUTPUT_TEMPLATE = u'''<!DOCTYPE HTML>
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>%s %s %s - HI KYAM</title>

        <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
        <script type="text/javascript">
var g;
$(function () {
    var chart;
    var DATES = ["%s"];
    $(document).ready(function() {
        chart = new Highcharts.Chart({
            chart: {
                renderTo: 'container',
                type: 'spline'
            },
            title: {
                text: '%s Performance (%s)'
            },
            subtitle: {
                text: 'Percentiles provided by Raidbots'
            },
            xAxis: {
                min: 0,
                max: DATES.length-1,
                //tickInterval: 1,
                //ordinal: false,
                labels: {
                                formatter: function() {
                                    v = DATES[this.value];
                                    try {
                                        return v.substring(5,10)+"<br/>"+v.substring(11);
                                    }
                                    catch(err) {
                                        return '';
                                    }
                                }
                            }
            },
            yAxis: {
                title: {
                    text: 'Spec Percentile (%%)'
                },
                min: 0,
                max: 100,
                plotBands: [{ from: 25, to: 50, color: '#D3F8D3' }, { from: 50, to: 75, color: '#C0CCF2' }, { from: 75, to: 95, color: '#F0B2E0' }, { from: 95, to: 100, color: '#FFD6AD' }]
            },
            tooltip: {
                formatter: function() {
                        return '<b>'+ this.series.name +'</b><br/>'+
                        DATES[this.x] +': '+ this.y +'%%';
                }
            },

            series: [%s]
        });
    });

});
        </script>
    </head>
    <body>
<script src="highcharts-2.3.3/js/highcharts.js"></script>
<script src="highcharts-2.3.3/js/modules/exporting.js"></script>

<div id="container" style="min-width: 400px; height: 400px; margin: 0 auto"></div>

    </body>
</html>
'''

SERIES_TEMPLATE = u'''{
    name: '%s',
    data: [%s],
    color: '%s',
    visible: %s
}'''

#Year, month, day, hour, percentile
DATA_TEMPLATE = u'''[Date.UTC(%s, %s, %s, %s), %s]'''
DATA_TEMPLATE = u'''[%s, %s]'''

KILL_ORDER = [u'Jinrokh_the_Breaker',
              u'Horridon',
              u'Council_of_Elders',
              u'Tortos',
              u'Megaera',
              u'Ji-Kun',
              u'Durumu_the_Forgotten',
              u'Primordius',
              u'Dark_Animus',
              u'Iron_Qon',
              u'Twin_Consorts',
              u'Lei_Shen',
              ]

#http://docs.python.org/library/bisect.html#searching-sorted-lists
def _interpolate(value, percentiles, percents):
    '''
    Return a linear interpolated percentile value based on:
        value - input value to get percentile for
        percentiles - list of percentile values to interpolate between
        percents - list of percents (same length as percentiles)
    '''
    if value in percentiles:
        return percents[percentiles.index(value)]
    if value < percentiles[0]:
        return 0
    if value > percentiles[-1]:
        return 100

    cur = bisect.bisect_right(percentiles, value)
    upper_p = percents[cur]
    upper_v = percentiles[cur]
    lower_p = percents[cur-1]
    lower_v = percentiles[cur-1]

    coef = ((value-lower_v)*100)/(upper_v-lower_v)

    return round(lower_p + (coef*(upper_p-lower_p))/100)

DPS_SPECS = set([102, 103, 201, 202, 301, 302, 303, 401, 402, 403, 503, 603,
                 701, 702, 703, 801, 802, 901, 902, 903, 1001, 1002, 1103])
TANK_SPECS = set([101, 203, 502, 1003, 1101])
HEAL_SPECS = set([204, 501, 601, 602, 803, 1102])
ALL_SPECS = DPS_SPECS.union(TANK_SPECS).union(HEAL_SPECS)

SPEC = {
    "DPS": DPS_SPECS,
    "TANK": TANK_SPECS,
    "HEAL": HEAL_SPECS,
    "ALL": ALL_SPECS,
}

THRESHOLD = {
    "ALL": 2,
    "DPS": 2,
    "HEAL": 2,
    "TANK": 2,
}

PLAYER_CACHE = {}


def get_player_data(name, realm, region):
    '''Cache data on a given player.'''
    if region not in PLAYER_CACHE:
        PLAYER_CACHE[region] = {}
    rcache = PLAYER_CACHE[region]

    if realm not in rcache:
        rcache[realm] = {}
    ecache = rcache[realm]

    if name not in ecache:
        ecache[name] = raidbots.player.get(name, realm, region)['data']

    return ecache[name]


FIGHT_CACHE = {}


def get_fight_data(spec, mode, name):
    '''Cache fight data for a given fightspec.'''
    if spec not in FIGHT_CACHE:
        FIGHT_CACHE[spec] = {}
    scache = FIGHT_CACHE[spec]

    if mode not in scache:
        scache[mode] = {}
    mcache = scache[mode]

    if name not in mcache:
        mcache[name] = raidbots.ebcd.get(spec, mode, name)

    return mcache[name]


def get_performance_graph(player, realm, region, mode, source_specs):
    data = get_player_data(player, realm, region)
    if len(data) == 0:
        return {}
    specs = data.keys()
    raids = {}
    for spec in specs:
        if int(spec) not in source_specs:
            print >> sys.stderr, "[INFO] %s is filtered" % spec
            continue

        if 'active' not in data[spec]:
            print >> sys.stderr, "[INFO] %s is not an active spec" % spec
            continue

        if mode not in data[spec]['active']:
            print >> sys.stderr, \
                "[INFO] No active parses for %d in mode %s" % (int(spec), mode)
            continue

        fights = data[spec]['active'][mode]

        fight_names = fights.keys()

        fight_data = {}

        if spec not in raids:
            raids[spec] = {}

        for name in fight_names:
            fight_data[name] = get_fight_data(spec, mode, name)

        for name in fight_names:
            if name not in KILL_ORDER:
                print >> sys.stderr, \
                    "[INFO] %s not a boss we're actively tracking" % name
                continue
            if isinstance(fights[name], basestring):
                print >> sys.stderr, "[BEFORE] %s" % fights[name]
                fights[name] = [fights[name][x] for x in fights[name][x]]
                print >> sys.stderr, "[AFTER] %s" % fights[name]
            for kill in fights[name]:
                date = long(kill['date'])/1000L
                #print >> sys.stderr, player, name, long(kill['date'])
                if date not in raids:
                    raids[spec][date] = [None for x in KILL_ORDER]
                dps = kill['value']

                if 'percent' not in fight_data[name]:
                    continue
                percents = sorted(fight_data[name]['percent'].keys())
                #Somewhat guaranteed to be sorted here
                percentiles = {}
                tdate = (date/24L/60L/60L)
                for per in percents:
                    pdate = fight_data[name]['percent'][per]
                    percentiles[per] = \
                        pdate[tdate] if tdate in pdate else \
                        pdate[min(pdate.keys(), key=lambda k: abs(k-tdate))]

                percents = sorted(percentiles.keys())
                percentiles = [percentiles[per] for per in percents]

                try:
                    raids[spec][date][KILL_ORDER.index(name)] = \
                        _interpolate(dps, percentiles, percents)
                except:
                    print >> sys.stderr, "[FATAL] Unable to handle %s %s %s" % \
                        (spec, date, name)
                    raise
    return raids


MODES = ['10N', '25N', '25H', '10H']


def get_points(raider, realm, region, source_specs):
    '''Get the graph points for a given player.'''
    raids = [get_performance_graph(raider, realm, region, mode, source_specs)
             for mode in MODES]

    points = []
    for raid in raids:
        for spec in raid.keys():
            for date in sorted(raid[spec].keys()):
                sdate = datetime.datetime.fromtimestamp(date)
                for i in range(len(raid[spec][date])):
                    hour = i
                    percent = raid[spec][date][i]
                    if percent is not None:
                        points.append((
                            datetime.datetime(sdate.year, sdate.month,
                                              sdate.day, hour),
                            percent,
                            spec
                        ))
    points.sort(key=lambda x: x[0])
    return points

CLASS_COLORS = {
    "death knight": "#C41F3B",
    "druid": "#FF7D0A",
    "hunter": "#ABD473",
    "mage": "#69CCF0",
    "monk": "#00FF96",
    "paladin": "#F58CBA",
    "priest": "#EEEEEE",
    "rogue": "#FFF569",
    "shaman": "#0070DE",
    "warlock": "#9482C9",
    "warrior": "#C79C6E",
}

ORDINAL_CLASSES = [None, "warrior", "paladin", "hunter", "rogue", "priest",
                   "death knight", "shaman", "mage", "warlock", "monk", "druid"]


def get_fight(fight):
    '''
    Return the name of the fight.
    '''
    return KILL_ORDER[fight.hour]


def generate():
    source_specs = ALL_SPECS
    sname = "ALL"
    gname = "Crisis Management"
    if len(sys.argv) > 1:
        sname = sys.argv[1].upper()
        source_specs = SPEC[sname]
        if len(sys.argv) > 2:
            gname = sys.argv[2]
    series = []
    #, u'M\xeenlock', u'Ric\xebz'
    members = guild.get(gname, "Perenolde", "members")['members']
    print >> sys.stderr, "[INFO] Got %d members" % len(members)
    raiders = [(x['character']['name'], x['character']['class'])
               for x in members
               if x['character']['level'] == 90 and x['rank'] <= 6]
    print >> sys.stderr, "[INFO] Got %d raiders" % len(raiders)
    points = {}
    dates = set()
    for raider in raiders:
        raider_name = raider[0]
        points[raider_name] = pstat = \
            get_points(raider_name, 'perenolde', 'us', source_specs)
        for raid_player in pstat:
            dates.add(raid_player[0])

    dates = sorted(list(dates))
    raider_series = {}
    attendance = [0 for x in dates]

    for raider in raiders:
        #raider_name = raider[0]
        pstat = [(dates.index(x[0]), x[1], x[2]) for x in points[raider[0]]]
        for raid_player in pstat:
            attendance[raid_player[0]] += 1

    real_dates = [date for date in dates
                  if attendance[dates.index(date)] >= THRESHOLD[sname]]

    raid_data = [[] for x in real_dates]
    for raider in raiders:
        raider_series[raider[0]] = rseries = []
        pstat = [(real_dates.index(x[0]), x[1])
                 for x in points[raider[0]] if x[0] in real_dates]
        for raid_player in sorted(pstat, key=lambda r: r[0]):
            if raid_player[0] >= 0:
                rseries.append(DATA_TEMPLATE % raid_player)
                raid_data[raid_player[0]].append(raid_player[1])

    for raider in sorted(raiders, key=lambda r: r[0]):
        print >> sys.stderr, "[INFO] Processing %s" % raider[0]
        rseries = raider_series[raider[0]]
        if len(rseries) > 0:
            series.append(SERIES_TEMPLATE % (raider[0], u','.join(rseries),
                          CLASS_COLORS[ORDINAL_CLASSES[raider[1]]], "false"))
        else:
            print >> sys.stderr, "[INFO] %s has no parses of this type." % \
                raider[0]

    stats = [('min', "#FF0000", "true"),
             ('p25', "#00FF00", "true"),
             ('median', "#0000FF", "true"),
             ('average', "#000000", "false"),
             ('p75', "#00FF00", "true"),
             ('max', "#FF0000", "true")]

    statistics = {}
    for stat in stats:
        statistics[stat[0]] = []
    for i in range(len(real_dates)):
        date = real_dates[i]
        data = raid_data[i]
        statistics["max"].append(DATA_TEMPLATE % (i, max(data)))
        statistics["min"].append(DATA_TEMPLATE % (i, min(data)))
        statistics["average"].append(DATA_TEMPLATE % (i, average(data)))
        statistics["p25"].append(DATA_TEMPLATE % (i, percentile(data, 25)))
        statistics["p75"].append(DATA_TEMPLATE % (i, percentile(data, 75)))
        statistics["median"].append(DATA_TEMPLATE % (i, percentile(data, 50)))

    for k in stats:
        series.append(SERIES_TEMPLATE %
                      (k[0], u','.join(statistics[k[0]]), k[1], k[2]))

    print OUTPUT_TEMPLATE % (gname, sname, str(datetime.datetime.now())[:10],
                             "\",\"".join([str(x)[:10] +
                                           " (%s)" % get_fight(x)
                                           for x in real_dates]),
                             gname, sname, u','.join(series))

if __name__ == "__main__":
    generate()
