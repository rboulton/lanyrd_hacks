# List conferences for a given user.

from lxml import etree, cssselect
import hashlib
import os
import re
import sys
import urllib, urllib2

baseurl = "http://lanyrd.com"
cachedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

userlist_name_re = re.compile('^([^(]+)\\(')
name_from_href_re = re.compile('^/people/([^/]+)')

def cachereq(url):
    h = hashlib.md5(url).hexdigest()
    dir = os.path.join(cachedir, h[0:2], h[0:4])
    if not os.path.exists(dir):
        os.makedirs(dir)
    cachefile = os.path.join(dir, h)
    if os.path.exists(cachefile):
        # FIXME - check not too old
        return open(cachefile).read()

    fd = urllib2.urlopen(url)
    data = fd.read()
    fd.close()
    fd = open(cachefile, "w")
    fd.write(data)
    fd.close()
    return data

def parse_confs(data):
    html = etree.HTML(data)
    url_sel = cssselect.CSSSelector('.url')
    summary_sel = cssselect.CSSSelector('.summary')
    loc_sel = cssselect.CSSSelector('.location')
    dtstart_sel = cssselect.CSSSelector('.dtstart')
    dtend_sel = cssselect.CSSSelector('.dtend')
    confs = []
    for e in cssselect.CSSSelector('li.vevent')(html):
        url = url_sel(e)[0].get('href')
        summary = etree.tostring(summary_sel(e)[0], method="text").strip()
        loc = etree.tostring(loc_sel(e)[0], method="text").strip()
        dtstart = dtstart_sel(e)
        if len(dtstart) > 0: dtstart = dtstart[0].get('title')
        else: dtstart = None
        dtend = dtend_sel(e)
        if len(dtend) > 0: dtend = dtend[0].get('title')
        else: dtend = None
        confs.append([url, summary, loc, dtstart, dtend])
    return confs

def parse_conf(data):
    html = etree.HTML(data)

    people = {}

    for e in cssselect.CSSSelector('ul.user-list')(html):
        p = e.getprevious()
        mo = userlist_name_re.match(p.text)
        if not mo: continue
        type = mo.groups(1)[0].strip().lower()
        type = {'attendees': 'a', 'tracked by': 't'}.get(type, type)
        l = people.setdefault(type, [])
        for e in cssselect.CSSSelector('li')(e):
            a = cssselect.CSSSelector('a')(e)
            if len(a) == 0: continue
            a = a[0]
            href = a.get('href')
            mo = name_from_href_re.match(href)
            name = mo.groups(1)[0]
            l.append((name, href, a.get('title')))
    return people

def get_conf(confurl):
    data = cachereq(baseurl + confurl)
    conf = parse_conf(data)
    return conf

def list_confs(user):
    data = cachereq(baseurl + "/people/" + user + "/")
    confs = parse_confs(data)
    return confs

def meetings(user):
    """Get a list of the conferences a user has been too, and a list of all the
    users attending each of those conferences.

    """
    confs = list_confs(user)
    for (url, summary, loc, dtstart, dtend) in confs:
        conf = get_conf(url)
        yield (url, summary, loc, dtstart, dtend, conf.get('a', ()))

if __name__ == '__main__':
    print list(meetings(sys.argv[1]))
