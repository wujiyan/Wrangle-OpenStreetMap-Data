##get part of the osm data in order to test the code.
import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import copy
import csv

OSM_FILE = "C:/data analyst/pj3/project/nashville_tennessee.osm"  # Replace this with your osm file
SAMPLE_FILE = "C:/data analyst/pj3/project/sample.osm"

k = 20 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')

  
##This part is to see the structure of xml data
    def count_tags(filename):
    tag_dict1 = {}    #top level
    tag_dict2 = {}    #second level
    tag_dict3 = {}    #third level
    ele_list = []
    tree = ET.ElementTree(file=filename)
    root = tree.getroot()
#if tag has not been counted, append it to the list and set the number to zero
    if root.tag not in ele_list:
        ele_list.append(root.tag)
        tag_dict1[root.tag] = 1
#if tag has been counted ,simply plus one
    else:
        tag_dict1[root.tag] +=1
    for root_1 in root:
        if root_1.tag not in ele_list:
            ele_list.append(root_1.tag)
            tag_dict2[root_1.tag] = 1
        else:
            tag_dict2[root_1.tag] += 1
        for root_2 in root_1:
            if root_2.tag not in ele_list:
                ele_list.append(root_2.tag)
                tag_dict3[root_2.tag] = 1
            else:
                tag_dict3[root_2.tag] += 1
    
    tag_level = [tag_dict1,tag_dict2,tag_dict3]
                            
    return tag_level

##the sample osm file and original file that I would use
filename = "C:/data analyst/pj3/project/sample.osm"
filename2 = "C:/data analyst/pj3/project/nashville_tennessee.osm"
#See the number of each tag at each structure level
tags = (count_tags(filename2))
pprint.pprint(tags[0])
pprint.pprint(tags[1])
pprint.pprint(tags[2])

##count the number of string type
lower = re.compile(r'^([a-z]|_|[0-9])*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_|[0-9])*$')
upper = re.compile(r'^([A-Z]|_)*$')    #strings with only capital
upper_colon = re.compile(r'^([a-z]|_)*:([A-Z]|[a-z]|_|[0-9])*$')    #strings with colon and capital after the colon
def key_type(element, keys):
    if element.tag == "tag":
        for tags in element.iter("tag"):
            m = tags.attrib["k"]
            if re.search(lower,m):
                keys["lower"] += 1
            elif re.search(lower_colon,m):
                keys["lower_colon"] += 1
            elif re.search(upper,m):
                keys["upper"] += 1
            elif re.search(upper_colon,m):
                keys["upper_colon"] += 1
            else:
                keys["other"] += 1
        
    return keys
keys = {"lower": 0, "lower_colon": 0, "upper": 0, "upper_colon": 0,"other": 0}
for __, element in ET.iterparse(filename2):
    keys = key_type(element,keys)
pprint.pprint(keys)

##function to creat string type list
def key_type_list(element, keys):
    if element.tag == "tag":
        for tags in element.iter("tag"):
            m = tags.attrib["k"]
            if re.search(lower,m):
                keys["lower"].add(m)
            elif re.search(lower_colon,m):
                keys["lower_colon"].add(m)
            elif re.search(upper,m):
                keys["upper"].append(m)
            elif re.search(upper_colon,m):
                keys["upper_colon"].append(m)
            else:
                keys["other"].append(m)
        
    return keys
keys = {"lower": set(), "lower_colon": set(), "upper": [],"upper_colon": [],"other": []}
for __, element in ET.iterparse(filename2):
    keys = key_type_list(element,keys)

##street name adjustment
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
#expected normal street name list
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Way","Pike","Circle","Cove","Highway","Terrace"]
#those abbreviated street type need to be fixed. 
mapping = { "st": "Street",
            "St.": "Street",
            "St": "Street",
            "St.":"Street",
            "Rd": "Road",
            "Ave": "Avenue",
            "Dr": "Drive",
            "Crt": "Court",
            "Pk": "Park",
            "pike": "Pike",
            "Pky": "Parkway",
            "Ct": "Court",
            "Blvd": "Boulevard",
            "Ln": "Lane",
            "Pkwy":"Parkway",
            "ave": "Avenue",
            "avenue":"Avenue",
            "Hwy":"Highway"
            }

##update street type according to the mapping list
def update_streettype (street_type):
    if street_type in mapping.keys():
        street_type = mapping[street_type]    
    return street_type

##extract street type. 
def extract_streettype (street_name):
    strings = re.split(" |, ",street_name)      #split them by the first colon
    strings = list(reversed(strings))  #reverse them so that we can use the first word as street type in some cases
    for w in range(len(strings)):
        if strings[w] in expected or strings[w] in ["Ave","Dr","St.","St","Hwy.","Hwy"]: 
            street_type = strings[w]     #if street type is in expected list or in mapping key list, just select it as the type
            break
        else:
            street_type = strings[0]          #otherwise, extract the first word
    street_type = update_streettype(street_type)       
    return street_type

#update original string with newly updated words
def update_string(street_name):
    strings = re.split(" |, ",street_name)
    new_string = ""
    for w in range(len(strings)):
        if strings[w] in mapping.keys():
            k = strings[w]
            strings[w] = mapping[k]
        new_string = new_string + " " + strings[w]
        new_string2 = new_string[1:]     #delete the first space
    return new_string2

#create street type list for further use, with original type, updated type and id in it.
files = open(filename2, "r")
street_types = defaultdict(set)
street_type_completed = []
for event, ele in ET.iterparse(files, events = ("start",)):
    if ele.tag in ["node","way"]:
        for tags in ele.iter("tag"):
            if tags.attrib["k"] == "addr:street":
                streets = {}
                street_name = tags.attrib['v']
                street_type = extract_streettype(street_name)
                streets['type'] = street_type
                streets['original_name'] = street_name
                street_name2 = update_string(street_name)
                street_types[street_type].add(street_name2)
                streets['updated_name'] = street_name2
                streets['id'] = ele.attrib["id"]
                street_type_completed .append(copy.copy(streets))
pprint.pprint(street_types["Avenue"]

##function to clean postcode
import re
pc_type2 = re.compile(r'\d{5}')
pc_type3 = re.compile(r'\D\D\ \d{5}\Z')
def update_postcode(code):
    if pc_type2.match(code):      #if post code begins with 5 digit number, just extract the first 5-digit number
        codes = re.search(r'\d{5}',code)
        new_code = codes.group()
    elif pc_type3.match(code):     #if post code is like type 3, just trim the 5 digit code.
        codes = re.search(r'\d(5)',code,re.M|re.I)
        new_code = codes.group()
    else:    #otherwise, make it null.
        new_code = ""
    return new_code

##create list to store the postcode and updated ones.
pc_type = re.compile(r'\d{5}$')
files = open(filename2, "r")
pc_types = defaultdict(list)
pc_type_n = []
for event, ele in ET.iterparse(files, events = ("start",)):
    if ele.tag in ["node","way"]:
        for tags in ele.iter("tag"):
            if tags.attrib["k"] == "addr:postcode":       #extract tags with postcode
                pc_value = {}
                value = str(tags.attrib["v"])
                if pc_type.match(value):
                    pc_value["original_code"] = tags.attrib["v"]
                    pc_value["updated_code"] = tags.attrib["v"]
                    pc_types["code"].append(value)
                    pc_value['id'] = ele.attrib['id']
                    pc_type_n.append(pc_value)
                else:
                    u = tags.attrib["v"]
                    pc_value["original_code"] = u
                    v = update_postcode(u)
                    pc_value["updated_code"] = v
                    pc_types["others"].append(v)
                    pc_value['id'] = ele.attrib['id']
                    pc_type_n.append(pc_value)
pprint.pprint(pc_types["others"])

#redefine the new lower colon format. Capital and lowercase are include after the colon
LOWER_COLON = re.compile(r'^([a-z]|_)*:([a-z]|_|[0-9]|[A-Z])*$')

#keys in each table
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['value', 'type', 'id', 'key','uid']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['value', 'type', 'id', 'key','uid']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

node_attribs = []
way_attribs = []
node_tags = []
way_nodes = []
way_tags = []
id_list = []
id_list1 = []
id_list2 = []
files = open(filename2, "r")
for event, ele in ET.iterparse(files, events = ("start",)):
    if ele.tag == "node":      #collect node data
        node_attrib = {}
        for attrib in ele.attrib:
            if attrib in NODE_FIELDS:
                node_attrib[attrib] = (ele.attrib[attrib])
        node_attribs.append(node_attrib)
                
        for child in ele:     #collect node_tags data
            if LOWER_COLON.match(child.attrib["k"]):    #if there is a colon in it
                if ele.attrib["id"] not in id_list1:
                    id_list1.append(ele.attrib["id"]) 
                    f = 0
                    node_tag={}
                    node_tag["type"]=child.attrib["k"].split(":",1)[0]      #extract the word before the colon as type
                    node_tag["key"]=child.attrib["k"].split(":",1)[1]      #extract the word after the first colon as the key
                    node_tag["id"]=ele.attrib["id"]                      #extract id as primary key
                    node_tag["value"]=child.attrib["v"]
                    node_tag["uid"] = f                                 #set uid as joint primary key
                    node_tags.append(copy.copy(node_tag))
                else:
                    node_tag = {}
                    f = f + 1                                         # uid would add one if it appears again
                    node_tag["type"]=child.attrib["k"].split(":",1)[0]
                    node_tag["key"]=child.attrib["k"].split(":",1)[1]
                    node_tag["id"]=ele.attrib["id"]
                    node_tag["value"]=child.attrib["v"]
                    node_tag["uid"] = f
                    node_tags.append(copy.copy(node_tag))
            else: #if there is no colon in it
                if ele.attrib["id"] not in id_list1:
                    id_list1.append(ele.attrib["id"])
                    f = 0
                    node_tag={}
                    node_tag["type"]="regular"      # type would be regular 
                    node_tag["key"]=child.attrib["k"]    #key remain the same
                    node_tag["id"]=ele.attrib["id"]
                    node_tag["value"]=child.attrib["v"]
                    node_tag["uid"] = f
                    node_tags.append(copy.copy(node_tag))
                else:
                    node_tag = {}
                    f = f + 1
                    node_tag["type"]="regular"
                    node_tag["key"]=child.attrib["k"]
                    node_tag["id"]=ele.attrib["id"]
                    node_tag["value"]=child.attrib["v"]
                    node_tag["uid"] = f
                    node_tags.append(copy.copy(node_tag))
    elif ele.tag == "way":
        way_attrib = {}
        for attrib in ele.attrib:                 #collect way data
            if attrib in WAY_FIELDS:
                way_attrib[attrib] = ele.attrib[attrib]
        way_attribs.append(way_attrib)
        for child in ele: 
            if child.tag == "nd":             #collect way_nodes data
                if ele.attrib["id"] not in id_list:
                    way_node = {}
                    i = 0
                    id_list.append(ele.attrib["id"])
                    way_node["id"] = ele.attrib["id"]
                    way_node["node_id"] = child.attrib["ref"]
                    way_node["position"] = i
                    way_nodes.append(copy.copy(way_node))
                else:
                    way_node = {}
                    i = i + 1
                    way_node["id"]=ele.attrib["id"]
                    way_node["node_id"]=child.attrib["ref"]
                    way_node["position"]=i
                    way_nodes.append(copy.copy(way_node))
            if child.tag == "tag":           #collect way_tags data
                if LOWER_COLON.match(child.attrib["k"]):           #if there is colon
                    if ele.attrib["id"] not in id_list2:
                        h = 0
                        way_tag = {}
                        id_list2.append(ele.attrib["id"])
                        way_tag["type"]=child.attrib["k"].split(":",1)[0]
                        way_tag["key"]=child.attrib["k"].split(":",1)[1]
                        way_tag["id"]=ele.attrib["id"]
                        way_tag["value"]=child.attrib["v"]
                        way_tag["uid"]=h
                        way_tags.append(copy.copy(way_tag))
                    else:
                        way_tag = {}
                        h = h + 1
                        way_tag["type"] = child .attrib["k"].split(":",1)[0]
                        way_tag["key"] = child.attrib["k"].split(":",1)[1]
                        way_tag["id"] = ele.attrib["id"]
                        way_tag["value"] = child.attrib["v"]
                        way_tag["uid"] = h
                        way_tags.append(copy.copy(way_tag))
                else:                              #if there is not colon
                    if ele.attrib["id"] not in id_list2:
                        h = 0
                        way_tag = {}
                        id_list2.append(ele.attrib["id"])
                        way_tag["type"]="regular"
                        way_tag["key"]=child.attrib["k"]
                        way_tag["id"]=ele.attrib["id"]
                        way_tag["value"]=child.attrib["v"]
                        way_tag["uid"]=h
                        way_tags.append(copy.copy(way_tag))
                    else:
                        way_tag = {}
                        h = h + 1
                        way_tag["type"] = "regular"
                        way_tag["key"] = child.attrib["k"]
                        way_tag["id"] = ele.attrib["id"]
                        way_tag["value"] = child.attrib["v"]
                        way_tag["uid"] = h
                        way_tags.append(copy.copy(way_tag))

##export tables into csv file locally
#local file path
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"
STREET_TYPE_PATH = "street_type.csv"
PC_TYPE_PATH = "postcode.csv"

#define table keys for street type and postcode type
STREET_TYPE_FIELDS = ["type","id","updated_name","original_name"]
PC_TYPE_FIELDS = ['updated_code', 'original_code', 'id']

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
#open paths and write down data
with open(NODES_PATH, 'w') as nodes_file, \
    open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
    open(WAYS_PATH, 'w') as ways_file, \
    open(WAY_NODES_PATH, 'w') as way_nodes_file, \
    open(WAY_TAGS_PATH, 'w') as way_tags_file,\
    open(STREET_TYPE_PATH,"w") as street_type_file,\
    open(PC_TYPE_PATH,'w') as pc_type_file:
        
        nodes_files = UnicodeDictWriter(nodes_file,NODE_FIELDS)
        nodes_tags_files = UnicodeDictWriter(nodes_tags_file,NODE_TAGS_FIELDS)
        ways_files = UnicodeDictWriter(ways_file,WAY_FIELDS)
        way_nodes_files = UnicodeDictWriter(way_nodes_file,WAY_NODES_FIELDS)
        way_tags_files = UnicodeDictWriter(way_tags_file,WAY_TAGS_FIELDS)
        street_type_files = csv.DictWriter(street_type_file,STREET_TYPE_FIELDS)
        pc_type_files = csv.DictWriter(pc_type_file,PC_TYPE_FIELDS)
        
        #headers
        nodes_files.writeheader()
        nodes_tags_files.writeheader()
        ways_files.writeheader()
        way_nodes_files.writeheader()
        way_tags_files.writeheader()
        street_type_files.writeheader()
        pc_type_files.writeheader()
        #write down tables
        nodes_files.writerows(node_attribs)
        nodes_tags_files.writerows(node_tags)
        ways_files.writerows(way_attribs)
        way_nodes_files.writerows(way_nodes)
        way_tags_files.writerows(way_tags)
        street_type_files.writerows(street_type_completed)
        pc_type_files.writerows(pc_type_n)

##example sql code. All sql queries were done in sqlite3

#this query extract the top 10 popular post codes
import sqlite3

# Fetch records from either openstreetmap.db
db = sqlite3.connect("openstreetmap.db")
c = db.cursor()
QUERY = "SELECT updated_code, count(*) as num\
         FROM postcode\
         GROUP BY updated_code\
         ORDER BY num DESC\
         LIMIT 10"
c.execute(QUERY)
rows = c.fetchall()

import pandas as pd    
df = pd.DataFrame(rows)
print df

db.close()
