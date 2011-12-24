import BeautifulSoup
import re
import string
import textwrap
import urllib2

def url(name):
    """Get the data url for a card."""
    url_prefix = 'http://ww2.wizards.com/gatherer/CardDetails.aspx?name='
    return url_prefix + name.replace(' ', '%20')

def _scrape(soup, title):
    """Scrape a BeautifulSoup for the value div of the div with id=title."""
    scrape = soup.find('div', id=title)
    if not scrape:
        return None
    value = scrape.find('div', attrs={'class': 'value'})
    return value.text.encode('ascii', 'replace')

def _scrape_raw(soup, title):
    """Scrape a BeautifulSoup for the value div of the div with id=title."""
    scrape = soup.find('div', id=title)
    if not scrape:
        return None
    value = scrape.find('div', attrs={'class': 'value'})
    return value

def _scrape_cost(soup):
    """Scrapte mana cost as a list."""
    value = _scrape_raw(soup, scrapeid_mana)
    if not value:
        return None
    imgs = value.findAll('img')
    l = [_alt_to_id(t['alt']) for t in imgs]
    return ''.join(l)

def _scrape_pt(soup):
    """Scrape power / toughness."""
    content = _scrape(soup, scrapeid_pt)
    m = re.search('(\d+)\D+(\d+)', content)
    return (m.group(1), m.group(2))

def _scrape_text(soup, title):
    """Scrape card text."""
    value = _scrape_raw(soup, title)
    if not value:
        return None
    boxes = value.findAll('div', attrs={'class': 'cardtextbox'})
    retl = [_replace_scrape_imgs(str(l)) for l in boxes]
    return string.join(retl, sep='\n')

def _replace_scrape_imgs(s):
    """Replace imgs in a scrape string with the ascii representation."""
    tmp = re.sub('<.*?>', '', re.sub('<img.*?alt="(.*?)".*?>', '|\\1|', s))
    return ''.join(_conv_all_alt(string.split(tmp, '|')))

def _conv_all_alt(l):
    """Converts all alt types to symbols."""
    r = []
    for s in l:
        if s in _alt_to_sym:
            r.append(_alt_to_sym[s])
        else:
            r.append(s)
    return r

def _alt_to_id(mana):
    """Converts a mana type from alt name to symbol. Ignores ints."""
    if re.match('\d+$', mana):
        return str(int(mana))
    else:
        if mana not in _alt_to_sym:
            return '?'
        else:
            return _alt_to_sym[mana]

# Gatherer scrape alt tags.
_alt_to_sym = {'Green': '{G}', 'Red': '{R}', 'Black': '{B}', 'Blue': '{U}',
               'White': '{W}', 'Variable Colorless': '{X}', 'Tap': '{T}',
               'None': 'None'}
# Gatherer scrape div ids.
scrapeid_name = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_nameRow'
scrapeid_mana = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_manaRow'
scrapeid_cmc = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_cmcRow'
scrapeid_type = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_typeRow'
scrapeid_text = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_textRow'
scrapeid_flvr = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_flavorRow'
scrapeid_pt = 'ctl00_ctl00_ctl00_MainContent_SubContent_SubContent_ptRow'


class Card:
    """A MtG card."""
    def __init__(self, name):
        self.name = name
        self.cost = []
        self.convertedCost = None
        self.types = None
        self.text = None
        self.flavor = None
        self.power = None
        self.toughness = None
        self.loaded = False

    def load(self):
        """Attempts to load the card from gatherer.wizards.com."""
        response = urllib2.urlopen(url(self.name))
        html = response.read()
        soup = BeautifulSoup.BeautifulSoup(html)
        # Scrape data.
        name = _scrape(soup, scrapeid_name)
        if not name or self.name.lower() != name.lower():
            return
        self.name = name
        self.cost = _scrape_cost(soup)
        self.convertedCost = _scrape(soup, scrapeid_cmc)
        types = _scrape(soup, scrapeid_type).split('?')
        self.types = types[0].split()
        if (len(types) > 1):
            self.subtypes = types[1].split()
        else:
            self.subtypes = []
        self.text = _scrape_text(soup, scrapeid_text)
        self.flavor = _scrape(soup, scrapeid_flvr)
        if self.isCreature():
            self.power, self.toughness = _scrape_pt(soup)
        self.loaded = True

    def isCreature(self):
        """Return True if card is of type Creature."""
        return 'Creature' in self.types

    def __str__(self):
        ret = self.name + '\n' +\
              'cost: '.ljust(10) + str(self.cost) +\
              ' (' + str(self.convertedCost) + ')'
        if len(self.types):
            ret += '\n' + 'types:'.ljust(10)
        for t in self.types:
            ret += t + ' '
        if len(self.subtypes):
            ret += '\n' + 'subtypes:'.ljust(10)
        for t in self.subtypes:
            ret += t + ' '
        if self.isCreature():
              ret += '\n' + 'P/T:'.ljust(10) + str(self.power) +\
                     ' / ' + str(self.toughness)
        if self.text:
            ret += '\n'
            for l in string.split(str(self.text), '\n'):
                ret += '\n' + textwrap.fill(l, 50)
        if self.flavor:
            ret += '\n'
            for l in string.split(str(self.flavor), '\n'):
                ret += '\n"' + textwrap.fill(l, 50).replace('?', '\n-') + '"'
        return ret
