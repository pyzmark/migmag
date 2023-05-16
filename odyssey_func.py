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
        try:
            if isinstance(value, dict):
                json_search(value,target)
            if key == target:
                global final
                final = value
                break
        except:
            final = float(NaN)
    return final
# This is needed for the json_search() function. Variable has to be present before
# the function is used.
final = ''


