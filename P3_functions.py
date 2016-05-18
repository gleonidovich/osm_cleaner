import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import re
import codecs
import json

OSMFILE = "washdc.osm"

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Alley","Avenue", "Bend", "Bottom", "Boulevard", "Bridge", 
            "Bypass", "Cape", "Causeway", "Center", "Circle", "Common", 
            "Corner",  "Court", "Crossing", "Crossroad", "Curve", "Drive", 
            "Expressway", "Flat", "Fort", "Freeway", "Garden", "Gateway",  
            "Harbor", "Heights", "Highway", "Hill", "Hills", "Junction", 
            "Landing", "Lane", "Loop", "Mall", "Manor", "Motorway", "Overlook", 
            "Overpass", "Park", "Parkway", "Passage", "Pike", "Place", "Plaza", 
            "Point", "Port", "Ridge", "Road", "Route", "Row", "Run", "Spring", 
            "Springs", "Square", "Station", "Street", "Terrace", "Throughway", 
            "Trail", "Tunnel", "Turnpike", "Union", "View", "Way"]

direction = ["North", "South", "East", "West","Northeast", "Northwest", "Southeast", "Southwest"]

direction_map = { "n.": "North", "n": "North", "N.": "North", "N": "North",
                  "s.": "South", "s": "South", "S.": "South", "S": "South",
                  "w.": "West", "w": "West", "W.": "West", "W": "West",
                  "e.": "East", "e": "East", "E.": "East", "E": "East",
                  "n.w.": "Northwest", "nw": "Northwest", "N.W.": "Northwest", "NW": "Northwest",
                  "n.e.": "Northeast", "ne": "Northeast", "N.E.": "Northeast", "NE": "Northeast",
                  "s.w.": "Southwest", "sw": "Southwest", "S.W.": "Southwest", "SW": "Southwest",
                  "s.e.": "Southeast", "se": "Southeast", "S.E.": "Southeast", "SE": "Southeast" }

mapping = { "ave": "Avenue",
            "avenue": "Avenue",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd": "Boulevard",
            "Ct": "Court",
            "Ct.": "Court",
            "drive": "Drive",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Hwy": "Highway",
            "Hwy.": "Highway",
            "Ln": "Lane",
            "Ln.": "Lane",
            "pike": "Pike",
            "Pkwy": "Parkway",
            "Pky": "Parkway",
            "Plz": "Plaza",
            "rd": "Road",
            "road": "Road",
            "Rd": "Road",
            "Rd.": "Road",
            "st": "Street",
            "St": "Street",
            "St.": "Street" }

def audit_street_type(street_types, street_name):
    '''Audit a string against a set of street types.

    This function determines whether the ending of a given street name 
    is within an expected set of street types.
    '''

    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    '''Check if element is a street name.'''
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile):
    '''Audit an OSM file for unexpected street names.

    This function parses through each lines of an OSM data file 
    to determine whether the street name in each "node" or "way" 
    is properly formatted. Any unexpected results are stored in 
    a defaultdict object with the unexpected ending at the key 
    and the full street names as value(s).
    '''
    osm_file = open(osmfile, "r", encoding="utf8")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

# check whether the street type needs to be fixed
def check_street_type(street_name):
    '''Finds the street type of the argument.

    This function checks the ending of a street name to determine if
    it is an expected street type, an abbreviation, or neither, and 
    the starting position of the last word.

    Returns:
    return1 == True if it is a valid street type
    return2 == True if the street type needs fixing
    return3 is the starting position of the street type in the name
    '''
    m = street_type_re.search(street_name.strip())
    if m:
        street_type = m.group()
        return street_type in expected, street_type in mapping.keys(), m.start()
    else:
        return False, False, 0

def check_if_direction(street_name):
    '''Finds the direction of the argument.

    This function checks the ending of a street name to determine if
    it is an expected ordinal direction, an abbreviated direction, or 
    neither, and the starting position of the last word.

    Returns:
    return1 == True if it is a valid direction
    return2 == True if the direction needs fixing
    return3 is the starting position of the direction in the name
    '''
    m = street_type_re.search(street_name.strip())
    if m:
        street_type = m.group()
        return street_type in direction, street_type in direction_map.keys(), m.start()
    else:
        return False, False, 0

def update_name(name, mapping, direction_map):
    '''Update a street name to desired formatting.

    This function takes a street name argument and updates the 
    street type and direction based on a set of expected values. 
    The method for updating is to split the string and then
    reconstruct it after editing.

    Returns:
    Updated street name
    '''
    # check first to see if a direction is at the end of the name
    check1, check2, index = check_if_direction(name)
    direct = ""
    if check1:
        # split the direction from the name if there is one
        direct = name[index:]
        name = name[:index]
    if check2:
        temp = name[index:]
        # fix the direction based on the abbreviation mapping
        for i in direction_map:
            if i == temp:
                direct = direction_map[i]
                name = name[:index]
    
    check1, check2, index = check_street_type(name)
    street_suffix = ""
    if check1:
        # if there is nothing else wrong with the street name
        # concatenate the name and direction (or empty string) back together
        direct = direct.strip()
        name = name.strip()
        return ("%s %s" % (name, direct)).strip().title()
    if check2:
        temp = name[index:].strip()
        # fix the street type if it was not properly formatted
        for i in mapping:
            if i == temp:
                street_suffix = mapping[i]
                name = name[:index]
    
    direct = direct.strip()
    street_suffix = street_suffix.strip()
    name = name.strip()
    # return the formatted string after all checks
    # using .strip() to get rid of any surrounding spaces throughout
    return ("%s %s %s" % (name, street_suffix, direct)).strip().title()

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

def shape_element(element):
    '''Creates a JSON object from a XML element.

    This function formats an XML element with a "node" or "way" 
    tag into a JSON object.

    Returns:
    JSON style dictionary object
    '''
    node = {}
    if element.tag == "node" or element.tag == "way" :
        
        created = {}
        pos = {}
        for i in element.attrib.keys():
            if i in CREATED:
                created[i] = element.get(i)
            elif (i == 'lat' or i == 'lon'):
                pos[i] = float(element.get(i))
            else:
                node[i] = element.get(i)
        
        node['created'] = created
        if len(pos) == 2:
            node['pos'] = [pos['lat'], pos['lon']]
        
        nds = []
        for n in element.findall('nd'):
            nds.append(n.get('ref'))
        if len(nds) > 0:
            node['node_refs'] = nds
        
        address = {}
        for t in element.findall('tag'):
            if re.search(problemchars, t.get('k')):
                pass # ignore any element with special characters
            elif re.search(r'\w+:\w+:\w+', t.get('k')):
                pass # ignore any element with multiple colon characters
            elif 'addr' in t.get('k'):
                address[t.get('k')[5:]] = t.get('v')
            else:
                if re.search(r'\w+:\w+', t.get('k')):
                    name = re.search(r':\w+', t.get('k'))
                    node[name.group(0)[1:]] = t.get('v')
                else:
                    node[t.get('k')] = t.get('v')
        if len(address) > 0:
            if 'street' in address:
                name = address['street']
                # pass all streets through the updating module
                address['street'] = update_name(name, mapping, direction_map)
            node['address'] = address
        if 'type' in node:
            # avoid an issue with 'type' being overriden
            node['place_type'] = node['type']
        node['type'] = element.tag
        return node
    else:
        return None

def process_map(file_in, pretty = False):
    '''Converts an OSM file into a JSON file.'''
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

process_map(OSMFILE)                