"""ents.pty
Convert SGML character entities into Unicode

Function taken from:
http://stackoverflow.com/questions/1197981/convert-html-entities-to-ascii-in-python/1582036#1582036

Thanks agazso!
"""
import re
import htmlentitydefs


def convert(s):
    """Take an input string s, find all things that look like SGML character
    entities, and replace them with the Unicode equivalent.

    Function is from:
http://stackoverflow.com/questions/1197981/convert-html-entities-to-ascii-in-python/1582036#1582036

    """
    matches = re.findall("&#\d+;", s)
    if len(matches) > 0:
        hits = set(matches)
        for hit in hits:
            name = hit[2:-1]
            try:
                entnum = int(name)
                s = s.replace(hit, unichr(entnum))
            except ValueError:
                pass
    matches = re.findall("&\w+;", s)
    hits = set(matches)
    amp = "&"
    if amp in hits:
        hits.remove(amp)
    for hit in hits:
        name = hit[1:-1]
        if name in htmlentitydefs.name2codepoint:
            s = s.replace(hit,
                          unichr(htmlentitydefs.name2codepoint[name]))
    s = s.replace(amp, "&")
    return s
