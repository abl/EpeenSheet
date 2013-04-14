"""
Common includes for raidbot work.
"""

PERCENTILE_MAP = {
    'max': 100,
    'min': 0,
    'median': 50,
}

if "HTTP" not in vars():
    import httplib2
    HTTP = httplib2.Http(cache=".cache")
