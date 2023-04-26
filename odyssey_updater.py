# This file has to be run either manually or on a schedule
# It does not interact with the other python files used by this app
# It outputs four (currently) JSON files from Nodegoat API queries
import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPDigestAuth
import json

# Any public use of this app will need this to be encrypted somehow or passed in using another method
# this is template for use in other parts of the code: it will usually need to be adapted in some way
my_headers = {'Authorization' : 'Bearer z6aanT57RX5mrf7ApyCIrgizQSYaM2cXztiTgoTpbQJO7FKyP'}

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
