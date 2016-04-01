import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import re
import codecs
import json

def count_tags(filename):
        tags = {}
        for event, elem in ET.iterparse(filename):
            if elem.tag in tags:
                tags[elem.tag] = tags[elem.tag] + 1
            else:
                tags[elem.tag] = 1
            elem.clear()
        
        return tags

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    if element.tag == "tag":
        k = element.attrib['k']
        if lower.match(k):
            keys['lower'] = keys['lower'] + 1
        elif lower_colon.search(k):
            keys['lower_colon'] = keys['lower_colon'] + 1
        elif problemchars.search(k):
            keys['problemchars'] = keys['problemchars'] + 1
        else:
            keys['other'] = keys['other'] + 1
        
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

def get_user(element):
    return element.attrib['uid']


def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if 'uid' in element.attrib:
            users.add(get_user(element))

    return users

OSMFILE = "example.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road"
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name, mapping):

    for i in mapping:
        if i in name:
            name = name.replace(i, mapping[i])
            return name

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        
        created = {}
        for i in CREATED:
            created[i] = element.attrib[i]
        
        node['id'] = element.attrib['id']
        node['type'] = element.tag
        node['created'] = created
        
        if 'visible' in element.attrib:
            node['visible'] = element.attrib['visible']
        
        if element.tag == 'node':
            node['pos'] = [element.attrib['lon'], element.attrib['lat']]
        if element.tag == 'way':
            nds = []
            for nd in element.iter("nd"):
                nds.append(nd.attrib['ref'])
            node['node_refs'] = nds
        
        address = {}
        for tag in element.iter("tag"):
            if 'addr:' in tag.attrib['k']:
                if ":" not in tag.attrib['k'][5:]:
                    address[tag.attrib['k'][5:]] = tag.attrib['v']
        finding = element.find('tag')
        if finding is None:
            pass
        else:
            node['address'] = address
        
        print(node)
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data