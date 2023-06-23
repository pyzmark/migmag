# This file has to be run either manually or on a schedule
# It does not interact with the other python files used by this app
# It outputs four (currently) JSON files from Nodegoat API queries
import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPDigestAuth
import json

# This will prompt the user to insert their NodeGoat token at command line
mytoken = input("Enter user token for NodeGoat: ")
bearer = 'Bearer '
my_headers = {'Authorization' : bearer + mytoken}


def apicall(datatype,objectid):
    url = 'https://nodegoat.io/project/3269'+'/data/type/'+datatype+'/object/'+objectid
    myResponse = requests.get(url, headers=my_headers)
    if(myResponse.ok):
        jData = json.loads(myResponse.content.decode('utf-8'))

    #    print("Code " + str(myResponse.status_code))
    #    print("The response contains {0} properties".format(len(jData)))
    #    print("\n")
    #    for key in jData:
    #        print(str(key) + " : " + str(jData[key]))
    else:
      # If response code is not ok (200), print the resulting http error code with description
        myResponse.raise_for_status()
    return jData

# nodegoat uses the category of "data types" to refer to high level data arrays that are
# in essence, the equivalent of separate spreadsheets for distinct kinds of conceptual objects
# the dictionary allows us to refer to these with name, not an assigned number
dt_dict = {
'agents' : '12174',
'journ' : '12173',
'evid' : '12189',
'places' : '12160',
'period' : '12188'
}

# This seems to work fine as a JSON dump. It produces four files, and is quick enough that you
# Can just run it every time you need to update the data (no need to keep an index and only update
# the files that you need, which would have probably been required in downloading individual JSON
# files)
for i in dt_dict:
    url = 'https://nodegoat.io/project/3269'+'/data/type/'+dt_dict[i]+'/object/'
    myResponse = requests.get(url, headers=my_headers)
    if(myResponse.ok):
        jData = json.loads(myResponse.content.decode('utf-8'))

    #    print("Code " + str(myResponse.status_code))
    #    print("The response contains {0} properties".format(len(jData)))
    #    print("\n")
    #    for key in jData:
    #        print(str(key) + " : " + str(jData[key]))
    else:
      # If response code is not ok (200), print the resulting http error code with description
        myResponse.raise_for_status()
    with open(i+'.json', 'w', encoding='utf-8') as f:
        json.dump(jData, f, ensure_ascii=False, indent=4)

# Next step is to turn these JSON dump files into skeletal CSVs that the mapping app can work from
# Generate csv equivalents from json files
# First, load the files we just generated above
with open('agents.json', 'r') as f:
  agentsj = json.load(f)

with open('places.json', 'r') as f:
  placesj = json.load(f)

with open('journ.json', 'r') as f:
  journj = json.load(f)

with open('evid.json', 'r') as f:
  evidj = json.load(f)

with open('period.json', 'r') as f:
  periodj = json.load(f)

### Produce a CSV for evidence
# Relies on the grabber function, which I put here
# The nodegoat JSON format is unorthodox (if not near senseless), in that it puts
# object values into the conceptual structure of the JSON object as keys
# So, Yağmapınar Höyük, a place, is object ID 14392930
# But 14392930 is also a dictionary key that precedes these values.
# So you get 
#{'objects': {'14392930': {'object': {'nodegoat_id': 'ngQX3I08cSHIcRnIaSJ8dfnNrRE', 'object_id': 14392930,...
# This renders the data structure unreplicable between JSON objects and any work with JSON has to be done with 
# node search. This is not a native JSON function, so I write a quick bit of code to drill into 
# nested dictionaries.

def json_search(data,target):
    for key, value in data.items():
        if isinstance(value, dict):
            json_search(value,target)
        if key == target:
            global final
            final = value
            break
    return final

# If you don't create the variable here, it break json_search() as this is called therein
final = ''

def grabber(json, object_id, data_type, string_value):
    data = json_search(json, object_id)
    if data_type:
        try:
            result = json_search(data, data_type)
            output = result[string_value]
        except:
            output = float('NaN')
    else:
        output = json_search(data, string_value)
    return output

### Start with places
placeslist = []
data = json_search(placesj, 'data')
for i in data['objects']:
    placeslist.append(i)

# Build df
places = pd.DataFrame(columns=['nodegoat ID', 
                                  'Object ID', 
                                  'Name',
                               'Region',
                               '[GPS Location] Geometry'])
# Fill df
for i in placeslist:
    object_id = i
    nodegoat_id = grabber(placesj, i, None, 'nodegoat_id')
    name = grabber(placesj, i, None, 'object_name')
    geometry = grabber(placesj, i, None, 'object_sub_location_geometry')
    region = grabber(placesj, i, '37737', 'object_definition_value')
    # Apparently this too can be multiple...
    new_row = [nodegoat_id, object_id, name, region, geometry]
    places.loc[len(places)] = new_row

### Get a list of periods from JSON
periodlist = []
data = json_search(periodj, 'data')
for i in data['objects']:
    periodlist.append(i)

# Build df
periods = pd.DataFrame(columns=['nodegoat ID', 
                                  'Object ID', 
                                  'Name'])
# Fill df
for i in periodlist:
    object_id = i
    nodegoat_id = grabber(periodj, i, None, 'nodegoat_id')
    name = grabber(periodj, i, None, 'object_name')
    # Apparently this too can be multiple...
    new_row = [nodegoat_id, object_id, name]
    periods.loc[len(periods)] = new_row

### Get a list of agents from JSON
agentlist = []
data = json_search(agentsj, 'data')
for i in data['objects']:
    agentlist.append(i)

# Build df
agents = pd.DataFrame(columns=['nodegoat ID', 
                                  'Object ID', 
                                  'Name',
                               'Traveller Type'])
# Fill df
for i in agentlist:
    object_id = i
    nodegoat_id = grabber(agentsj, i, None, 'nodegoat_id')
    name = grabber(agentsj, i, None, 'object_name')
    travtype = grabber(agentsj, i, '35520', 'object_definition_value')
    # Apparently this too can be multiple...
    new_row = [nodegoat_id, object_id, name, travtype]
    agents.loc[len(agents)] = new_row

# Get a list of evidence from JSON
evidlist = []
data = json_search(evidj, 'data')
for i in data['objects']:
    evidlist.append(i)

# Build df
evid = pd.DataFrame(columns=['nodegoat ID', 
                                  'Object ID', 
                                  'Name',
                             'Mobility Word'
                             ])
# Fill df
for i in evidlist:
    object_id = i
    nodegoat_id = grabber(evidj, i, None, 'nodegoat_id')
    name = grabber(evidj, i, None, 'object_name')
    mobn = grabber(evidj, i, '47295', 'object_definition_value')
    mobv = grabber(evidj, i, '47292', 'object_definition_value')
    mobw = mobn + mobv
    # Apparently this too can be multiple...
    new_row = [nodegoat_id, object_id, name, mobw]
    evid.loc[len(evid)] = new_row

### Get a list of journeys
journeys = []
data = json_search(journj, 'data')
for i in data['objects']:
    journeys.append(i)

journ = pd.DataFrame(columns=['nodegoat ID', 
                                  'Object ID', 
                                  'Name', 
                                  'Place From', 
                                  'Place From - Object ID', 
                                  'Place to', 
                                  'Place to - Object ID',
                                  'Traveller Types',
                                  'Movement Type',
                              'Time Period'])

# Fill df. This was the most complicated one as the last four columns might
# have multiple entries in lists. These have to be disentangled as separate rows
for i in journeys:
    object_id = i
    nodegoat_id = grabber(journj, i, None, 'nodegoat_id')
    name = grabber(journj, i, None, 'object_name')
    traveller_types = grabber(journj, i, '35542', 'object_definition_value')
    mode_move = grabber(journj, i, '35518', 'object_definition_value')
    time_period = grabber(journj, i, '35555', 'object_definition_value')
    # Apparently this too can be multiple...
    
    place_from = grabber(journj, i, '35546', 'object_definition_value')
    place_from_id = grabber(journj, i, '35546', 'object_definition_ref_object_id')      
    # This can be a list, you will have to build in something to take this into account
    place_to = grabber(journj, i, '35547', 'object_definition_value')
    place_to_id = grabber(journj, i, '35547', 'object_definition_ref_object_id')
    if len(place_from) > 1:
        for i in range(len(place_from)):
            new_row = [nodegoat_id, object_id, name, place_from[i], place_from_id[i], place_to, place_to_id, traveller_types, mode_move, time_period]
            journ.loc[len(journ)] = new_row
    if len(place_to) > 1:
        for i in range(len(place_to)):
            new_row = [nodegoat_id, object_id, name, place_from, place_from_id, place_to[i], place_to_id[i], traveller_types, mode_move, time_period]
            journ.loc[len(journ)] = new_row
    else:
        new_row = [nodegoat_id, object_id, name, place_from, place_from_id, place_to, place_to_id, traveller_types, mode_move, time_period]
        journ.loc[len(journ)] = new_row

# This is required in order to get rid of remaining multi-item lists
# After this code, all that is left is single-item lists
def cull_list(column):
    for row, i in enumerate(column):
        indexdrop = []
        if isinstance(i, list) and len(i) > 1:
            indexdrop.append(row)
        #journtest = journtest.drop([journtest.index[row]], )
            #print(i, "Dropped")
        journ.drop(indexdrop , inplace=True)

cull_list(journ['Place From'])
cull_list(journ['Place to'])

# This is a nice method of de-listing lists in these columns.
# It runs into problems in the object_id columns because, unlike
# the two below (which are strings and which are compatible with the unlist function)
# when it hits an integer it fails
unlist = lambda lisst : ''.join(str(e) for e in lisst)
journ['Place From'] = journ['Place From'].apply(unlist)
journ['Place to'] = journ['Place to'].apply(unlist)

# Handling ints required for loops (to incorp conditionals)
# Doing that required getting rid of nans and resetting the index
# (otherwise the enumerated loop gets out of sync)
journ = journ.replace('', np.NaN)
journ = journ.dropna(subset=['Place From', 'Place to'])
journ = journ.reset_index()

# And here we run the code to separate things out
for row, i in enumerate(journ['Place From - Object ID']):
    if isinstance(i, list) and i:
        journ['Place From - Object ID'].loc[row] = ''.join(str(e) for e in i)
    elif not i:
        journ['Place From - Object ID'].loc[row] = ''
    else:
        continue

for row, i in enumerate(journ['Place to - Object ID']):
    if isinstance(i, list) and i:
        journ['Place to - Object ID'].loc[row] = ''.join(str(e) for e in i)
    elif not i:
        journ['Place to - Object ID'].loc[row] = ''
    else:
        continue

# Resetting the index created a column called "index". We drop it
journ = journ.drop(columns=['index'])

# We want to assign authors to all journeys
# the list-set-list format at the start is to weed out doubled journeys (like Ionian migration)
all_passages = []
for i in journ['Object ID']:
    passage_list = grabber(journj, str(i), '35524', 'object_definition_ref_object_id')
    authors_in_this_journey = []
    for i in passage_list:
        authors_in_this_journey.append(grabber(evidj, str(i), '35557', 'object_definition_value'))
    authors_in_this_journey = list(set(authors_in_this_journey))
    all_passages.append(authors_in_this_journey)
journ['Authors'] = all_passages

# Assign words of mobility here
all_words = []
for i in journ['Object ID']:
    passage_list = grabber(journj, str(i), '35524', 'object_definition_ref_object_id')
    words_in_this_journey = []
    for i in passage_list:
        words_in_this_journey.extend(grabber(evidj, str(i), '47292', 'object_definition_value'))
        words_in_this_journey.extend(grabber(evidj, str(i), '47295', 'object_definition_value'))
    words_in_this_journey = list(set(words_in_this_journey))
    all_words.append(words_in_this_journey)
journ['Mobility Words'] = all_words

journ.to_csv('mythjour.csv', index=False)
evid.to_csv('textevid.csv', index=False)
places.to_csv('places.csv', index=False)
periods.to_csv('period.csv', index=False)
agents.to_csv('agents.csv', index=False)
