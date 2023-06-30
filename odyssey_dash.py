import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from streamlit_folium import folium_static
import numpy as np
import re
import folium
from folium import plugins
import altair as alt
import ast
from odyssey_func import *
import json
from geojson import Point, LineString, GeometryCollection, Feature, FeatureCollection
from shapely.geometry import shape

# Set basic page information
app_title = ':amphora: Odyssey'
app_subtitle = 'An exploratory tool for mythical journeys. For internal use by MigMag staff.'

# Visualizations
def display_map(authors, journ, agents, evid, places, range_min, range_max, hero_name, journ_name, dest_name, port_name, trav_type, author_name, journj, agentsj, evidj, mode_move, time_period, mob_word):
    latitude = 38
    longitude = 25

    errors = []
    # Create map and display it
    # Create map and display it
    odyssey_map = folium.Map(
        location=[latitude, longitude], 
        zoom_start=4, 
        tiles=None)
    # Add several basemap layers onto the blank space prepared above
    folium.TileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',
                     name='Carto DB - Dark',
                     attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>').add_to(odyssey_map)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
                     name='ESRI - World Shader Relief - Light',
                     attr='Tiles &copy; Esri &mdash; Source: Esri').add_to(odyssey_map)
    # This controls whether or not a text_display field is generated in the main function
    # If no journies have been selected in search boxes (see if statemenes below),
    # then that st field will be blank.
    # But if someone selects a journey, then the text and translation will be automatically
    # retrieved, formatted, and presented below the map
    text_display = False

    # This monitors whether searchbars have been modified and creates
    # sub-sets of the main df from those selections
    if journ_name:
        journ = journ[journ['Name'].isin(journ_name)]
        # This is the only place I will comment on this, but it is repeated below
        # We must reset the index religiously, or else the various search functions
        # Fail to work together. And index remnant must be dropped, as after two
        # layers, they get in the way of further column additions
        journ = journ.reset_index(drop=True)
        text_display = True
    if hero_name:
        rows = []
        for row, i in enumerate(journ['heroes']):
            if [ele for ele in i if(ele in hero_name)]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
        text_display = True
    if dest_name:
        journ = journ[journ['Place to'].isin(dest_name)]
        journ = journ.reset_index(drop=True)
        text_display = True
    if port_name:
        journ = journ[journ['Place From'].isin(port_name)]
        journ = journ.reset_index(drop=True)
        text_display = True
    if trav_type:
        rows = []
        for row, i in enumerate(journ['Traveller Types']):
            if [ele for ele in i if(ele in trav_type)]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
    if range_min > -1200 or range_max < 500:
        # Below is the filter portion of the process
        authors = authors[authors['Earliest'] > range_min] 
        authors = authors[authors['Latest'] < range_max]
        # now that we have a list of relevant authors, we must turn the process around
        # start from journeys, each of which points to a piece of evidence
        # from evidence, find authors, whittle down to unique authors
        # assign these to each journey --- compare the authors on journeys against your
        # authors df... remove journeys that don't have a relevant author
        # AND get rid of evidence in the text section that does not match the
        # date range
        rows = []
        for row, i in enumerate(journ['Authors']):
            if [ele for ele in i if(ele in list(authors['Name']))]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
    if author_name:
        authors = authors[authors['Name'].isin(author_name)]
        rows = []
        for row, i in enumerate(journ['Authors']):
            if [ele for ele in i if(ele in list(authors['Name']))]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
        text_display = True
    if mode_move:
        rows = []
        for row, i in enumerate(journ['Movement Type']):
            if [ele for ele in i if(ele in mode_move)]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
    if time_period:
        journ = journ[journ['Time Period'].isin(time_period)]
        journ = journ.reset_index(drop=True)

    if mob_word:
        rows = []
        for row, i in enumerate(journ['Mobility Words']):
            if [ele for ele in i if(ele in mob_word)]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
        text_display = True

    # We need exportable variables (export, author_export) to output from this function, while existing
    # variables (journ, authors) are needed internally for the function to work
    export = journ
    author_export = authors

    # These lists are used to set up the loops below
    j_names = list(journ['Name'])
    j_pf = list(journ['Place From - Object ID'])
    j_pt = list(journ['Place to - Object ID'])
    j_id = list(journ['Object ID'])

    # These empty lists are needed to house geojson objects that are to be converted to one big
    # feature group
    features = []
    line_features = []

    # Make markers and polygons for origins and destinations
    for i in list(set(j_pf + j_pt)):
        try:
            marker = geo_grabber(i)
            try: 
                marker = marker['geometries'][0]
            except:
                marker = marker
            marker = shape(marker)
        #    marker = marker.centroid
        #    marker = tuple((marker.coords[:])[0])
        #    label = places[places['Object ID']==i]['Name'].values[0]
            place_name = places[places['Object ID']==i]['Name'].values[0]
            feature = Feature(geometry=marker, properties={"Name": place_name})
            features.append(feature)
        except:
            continue

    # Make lines for journeys
    for name, object_id, pf_id, pt_id in zip(j_names, j_id, j_pf, j_pt):
        try:
            journey = journey_maker(name, pf_id, pt_id)
            journey_label = journey[0]
            pointa = journey[1]
            pointb = journey[2]
            # This uses shapely, not geojson-py, to find the centroid of polygons as line anchors
            # It can be used for points too---it just returns the point
            pointa_anchor = shape(pointa)
            pointa_anchor = pointa_anchor.centroid
            pointa_anchor = tuple((pointa_anchor.coords[:])[0])
            pointb_anchor = shape(pointb)
            pointb_anchor = pointb_anchor.centroid
            pointb_anchor = tuple((pointb_anchor.coords[:])[0])
            line = LineString([pointa_anchor, pointb_anchor])
            line_feature = Feature(geometry=line, properties={"Journey": journey[0]})
            line_features.append(line_feature)
        except:
            # The thought here is to maintain a list of truly impossible journeys as an error output
            errors.append(journey)
            continue
    markers = FeatureCollection(features)
    lines = FeatureCollection(line_features)
    style = lambda x: {
        'color' : 'white',
        'opacity' : '0.60',
        'weight' : '1',
        'radius' : '8',
        'fill' : 'True',
        'fillOpacity' : '0',
        'fillColor' : 'white'
            }
    highlight = lambda x: {
        'color' : 'white',
        'opacity' : '0.80',
        'weight' : '5',
        'fill' : 'True',
        'fillOpacity' : '0.3',
        'fillColor' : 'white'
            }
    folium.features.GeoJson(markers, 
                    style_function=style,
                    highlight_function=highlight,
                    name='Markers', 
                    overlay=True, 
                    control=True, 
                    show=True, 
                    smooth_factor=True, 
                    tooltip=folium.GeoJsonTooltip(fields=['Name']),
                    embed=True, 
                    popup=None, 
                    zoom_on_click=False, 
                    marker=folium.CircleMarker()).add_to(odyssey_map)
    folium.features.GeoJson(lines, 
                    style_function=style,
                    highlight_function=highlight,
                    name='Mythical Journeys', 
                    overlay=True, 
                    control=True, 
                    show=True, 
                    smooth_factor=True, 
                    tooltip=folium.GeoJsonTooltip(fields=['Journey']),
                    embed=True, 
                    popup=None, 
                    zoom_on_click=False, 
                    marker=folium.CircleMarker()).add_to(odyssey_map)

    return odyssey_map, export, journ, text_display, author_export, errors

def main():
    # Load Data
    agents = pd.read_csv('agents.csv')
    journ = pd.read_csv('mythjour.csv')
    evid = pd.read_csv('textevid.csv')
    places = pd.read_csv('places.csv')

    # if there is a nan in certain journ columns, it breaks things down the line
    journ = journ.dropna(subset=['Place From - Object ID', 'Place to - Object ID'])

    # Some of these rows are encoded as int or float in the nodegoat export
    # They should be strings
    agents['Object ID'] = agents['Object ID'].astype(str)
    journ['Object ID'] = journ['Object ID'].astype(str)
    journ['Place From - Object ID'] = journ['Place From - Object ID'].astype(int)
    journ['Place From - Object ID'] = journ['Place From - Object ID'].astype(str)
    journ['Place to - Object ID'] = journ['Place to - Object ID'].astype(str)
    # This is needed to make the Authors column readable as a list and not a literal
    journ['Authors'] = journ.Authors.apply(lambda x: ast.literal_eval(str(x)))
    evid['Object ID'] = evid['Object ID'].astype(str)
    places['Object ID'] = places['Object ID'].astype(str)

    # This imports four files that contain the substantive data as JSON
    # Right now these interface with the csv files that are custom exported.
    # The goal would be to create those simplified arrays from the JSON when the 
    # program starts up
    with open('agents.json', 'r') as f:
        agentsj = json.load(f)

    with open('places.json', 'r') as f:
        placesj = json.load(f)

    with open('journ.json', 'r') as f:
        journj = json.load(f)

    with open('evid.json', 'r') as f:
        evidj = json.load(f)


    # Create basic visual elements
    st.set_page_config('Odyssey (MigMag)', page_icon='amphora', layout='wide')
    st.title(app_title)
    st.caption(app_subtitle)
    st.markdown("""
            <style>
                .block-container {
                        padding-top: 1.5rem;
                        padding-bottom: 0rem;
                        padding-left: 1rem;
                        padding-right: 1rem;
                    }
                [data-testid=stSidebar] {
                    padding-left: 0rem;
                    }
            </style>
            """, unsafe_allow_html=True)

    # Some general use functions that are deployed in the map-making and graph-making functions.
    global hero_grabber
    def hero_grabber(journey_id):
        # First we need to scan the whole journj JSON file for our specific journey
        data = json_search(journj, journey_id)
        # The below is meant to drill down to data object 33543, which is typically where heroic participants
        # live in the JSON code. Once you find that, you can 
        results = json_search(data, '35543')
    #    hero_ids = results['object_definition_ref_object_id']
        hero_names = results['object_definition_value']
        return hero_names

    # geo_grabber is currently not capable of ingesting regions with polygon data
    # Right not when you run it in a loop, it just drops those entries
    global geo_grabber
#    def geo_grabber(place_id):
#        try:
#            results = places[places['Object ID']==place_id]['[GPS Location] Geometry'].values[0]
#            results = ast.literal_eval(results)
#            return results['coordinates']
#        except:
#            #results = json_search(data, 'object_sub_location_geometry')
#            results = 'No coords'
#            return results
    def geo_grabber(place_id):
        results = places[places['Object ID']==place_id]['[GPS Location] Geometry'].values[0]
        try:
            if 'coordinates' in results:
                results = ast.literal_eval(results)
                return results
            elif 'coordinates' not in results:
                results = 'There is a problem. Probably the place referred to here is missing a sub-object.'
                return results
        except:
            results = 'There is a problem. Not quite sure what...'
            return results
            st.write(results)

    global journey_maker
    def journey_maker(name, pf_id, pt_id):
        # We need to grab geo data from the places. The csv doesn't have that, so we need place ids
        # Then we need to query the API for them
        # Then grab geo data from JSON object
        # above geo_grabber does that
        pf_geo = geo_grabber(pf_id)
        pt_geo = geo_grabber(pt_id)
        return name, pf_geo, pt_geo

    # This is a proposed "universal grabber" that would replace all of the above. It would be more efficient, but not as human-readable. I may implement it, meaning reworking function-calls that are basically isomorphic. But for now, diffing a hero grabber from a period grabber isn't terrible.
    global grabber
    def grabber(json, object_id, data_type, string_value):
        try:
            data = json_search(json, object_id)
            if data_type:
                result = json_search(data, data_type)
                output = result[string_value]
            else:
                output = json_search(data, string_value)
        except:
            output = float('NaN')
        return output    

    # We need to separate out the authors from travellers, should be done here and passed into map function
    authors = agents
    # This is needed because someone snuck a few "0-1" into this column and it causes an error
    authors['Earliest'] = authors['Object ID'].map(lambda x: grabber(agentsj, x, '35536', 'object_definition_value'))
    authors['Latest'] = authors['Object ID'].map(lambda x : grabber(agentsj, x, '35537', 'object_definition_value'))
    authors = authors.dropna(subset=['Earliest','Latest'])
    authors['Earliest'] = authors['Earliest'].replace('0-1',1)
    authors['Latest'] = authors['Latest'].replace('0-1',1)
    authors['Earliest'] = authors['Earliest'].astype(int)
    authors['Latest'] = authors['Latest'].astype(int)
    # We need a dictionary for authors/object_ids. We do this here, before filtering authors down
    all_authors_names = list(authors['Name'])
    all_authors_id = list(authors['Object ID'])
    all_authors = dict(zip(all_authors_names,all_authors_id))

    # This is needed for the searchbars with a scroll
    tooltip = "Certain filters do not generate text on their own (so you won't see it below the map), because they are sufficiently general that they produce an :red[overwhelming amount of it.] Use filters marked :memo: if you wish to generate texts below the map."

    def searchbar_maker(df, col, title, tooltip):
        list_name = list(df[col].unique())
        list_name = [x for x in list_name if str(x) != 'nan']
        list_name.sort()
        list_name = ['All'] + list_name
        selector = st.sidebar.multiselect(title, (list_name), help=tooltip)
        name = selector
        if selector == 'All':
            name = ''
        return name

    # We need to make a list of MigMag study regions to add to the list of places
    region = list(set(places['Region'].dropna()))
    regions = ['Region: ' + s for s in region]

    # Implementing regional search meant the generic searchbox below was not longer workable
    # I preserve it here for reference. Same goes for port_name
    #dest_name = searchbar_maker(journ, 'Place to', 'Place Established or Destination   :memo:', tooltip)
    dest_list = list(journ['Place to'].unique())
    dest_list = [x for x in dest_list if str(x) != 'nan']
    dest_list = dest_list + regions
    dest_list.sort()
    dest_list = ['All'] + dest_list
    dest_name = st.sidebar.multiselect('Place Established or Destination    :memo:', dest_list, help=tooltip)
    if dest_name == 'All':
        dest_name = ''
    subregions = [i for i in dest_name if 'Region: ' in i]
    additional_cities = []
    for i in subregions:
        region_name = i.replace('Region: ','')
        regional_cities = places[places['Region']==region_name]
        regional_cities = list(regional_cities['Name'])
        additional_cities.extend(regional_cities)
    dest_name = dest_name + additional_cities
    dest_name = [i for i in dest_name if not ('Region: ' in i)]
    dest_name = list(set(dest_name))
    
    #port_name = searchbar_maker(journ,'Place From', 'Select Port of Origin   :memo:', tooltip)
    port_list = list(journ['Place From'].unique())
    port_list = [x for x in port_list if str(x) != 'nan']
    port_list = port_list + regions
    port_list.sort()
    port_list = ['All'] + port_list
    port_name = st.sidebar.multiselect('Place of Origin    :memo:', port_list, help=tooltip)
    if port_name == 'All':
        port_name = ''
    subregions = [i for i in port_name if 'Region: ' in i]
    additional_cities = []
    for i in subregions:
        region_name = i.replace('Region: ','')
        regional_cities = places[places['Region']==region_name]
        regional_cities = list(regional_cities['Name'])
        additional_cities.extend(regional_cities)
    port_name = port_name + additional_cities
    port_name = [i for i in port_name if not ('Region: ' in i)]
    port_name = list(set(port_name))
    
    # Make a list of movement types for searchbar. This requires same method as above bcs it is list of lists
    move_list = []
    journ['Movement Type'] = journ['Movement Type'].apply(lambda x: ast.literal_eval(str(x)))
    for i in journ['Movement Type']:
        for y in i:
            move_list.append(y)
    move_list = list(set(move_list))
    move_list.sort()
    mode_move = st.sidebar.multiselect("Type of Movement", (move_list))

    # Create an agent searchbar
    journ['heroes'] = journ['Object ID'].apply(hero_grabber)
    hero_list = []
    for i in journ['heroes']:
        for y in i:
            hero_list.append(y)
    hero_list = list(set(hero_list))
    hero_list = [x for x in hero_list if str(x) != 'nan']
    hero_list.sort()
    hero_list = ['All'] + hero_list
    hero_selector = st.sidebar.multiselect("Select Named Traveller(s)   :memo:", (hero_list), help=tooltip)
    hero_name = hero_selector
    if hero_selector == 'All':
        hero_name = ''

    time_period = searchbar_maker(journ, 'Time Period', 'Mythical Time Period (Travellers)', None)

    # We need to make a list of traveller types to feed to the traveller type searchbar
    traveller_types = []
    journ['Traveller Types'] = journ['Traveller Types'].apply(lambda x: ast.literal_eval(str(x)))
    for i in journ['Traveller Types']:
        for y in i:
            traveller_types.append(y)
    traveller_types = list(set(traveller_types))
    trav_type = st.sidebar.multiselect("Traveller Type", (traveller_types))

    journ_name = searchbar_maker(journ, 'Name', 'Journey Name', tooltip)

    # Make a list of words of mobility
    mob_word_list = []
    journ['Mobility Words'] = journ['Mobility Words'].apply(lambda x: ast.literal_eval(str(x)))
    for i in journ['Mobility Words']:
        for y in i:
            mob_word_list.append(y)
    mob_word_list = list(set(mob_word_list))
    mob_word_list.sort()
    mob_word = st.sidebar.multiselect('Mobility Vocabulary', (mob_word_list))


    author_name = searchbar_maker(authors, 'Name', 'Author(s) of Evidence   :memo:', tooltip)
    #from_region = searchbar_maker(places, 'Region', 'From Region')
    #to_region = searchbar_maker(places, 'Region', 'To Region')
    # we remove 'author' as an option, as this will not be relevant

    # Create the date slider
    slider_range = st.sidebar.slider('Author Date Range', -1200, 500, (-1200,500))
    range_min = slider_range[0]
    range_max = slider_range[1]

    # Create the map. This has a number of other variables that come out of the
    # display_map function. This includes export, which is for the csv button at
    # the bottom of the page. modjourn is a modified journ df that comes out of
    # the map, once filters are applied. text_display is a y/n switch that
    # tells the program whether to generate text for the subsection of journeys
    odyssey_map, export, modjourn, text_display, author_export, errors = display_map(authors, journ, agents, evid, places, range_min, range_max, hero_name, journ_name, dest_name, port_name, trav_type, author_name, journj, agentsj, evidj, mode_move, time_period, mob_word)


    folium.LayerControl().add_to(odyssey_map)
    # This begins the mapping function
#    import streamlit.components.v1 as components
#    iframe = odyssey_map._repr_html_()
#    components.html(iframe, width=950, height=500)
    st.data = st_folium(odyssey_map, width=950, height=500)

    if errors:
        with st.expander(":skull: Error 01: Journey(s) missing geographic information on at least one place in Nodegoat", expanded=False):
            st.write('Below are a series of "lists" (produced by the program\'s code, so they are barely human legible\). The point is that each list (starting with #0) has three sub-elements. #0 is the name of the journey. #1 is an origin point. #2 is a destination. The most likely source of error is a missing value in #1 or #2, and this will be indicated by the phrase "There is a problem. Probably the place referred to here is missing a sub-object.". This should be fixed in Nodegoat by filling in geographic information on either the origin point or destination of the journey in question.')
            st.write(errors)
# This function builds the markdown text evidence below the map.
# it relies on text_evidence, set in the odyssey_map function, to be true
    if text_display:
        header = """## Textual Evidence

        """
        st.write(header)
        journey_names = []
        for i in list(modjourn['Object ID']):
            journey_name = grabber(journj, i, None, 'object_name')
            if journey_name not in journey_names:
                journey_names.append(journey_name)
                journey_header = f"""
#### {journey_name}
"""
                st.markdown(journey_header)
                try:
                    evidence = grabber(journj, str(i), '35524', 'object_definition_ref_object_id')
                    for number, y in enumerate(evidence):
                        author = str(grabber(evidj, str(y), '35557', 'object_definition_value'))
                        title = str(grabber(evidj, str(y), '36999', 'object_definition_value'))
                        greek = str(grabber(evidj, str(y), '37023', 'object_definition_value'))
                        english = str(grabber(evidj, str(y), '37024', 'object_definition_value'))
                        number2 = str(number+1)
                        mobnloc = grabber(evidj, str(y), '47295', 'object_definition_value')
                        mobvloc = grabber(evidj, str(y), '47292', 'object_definition_value')
                        mobwloc = mobnloc + mobvloc
                        if mob_word:
                            if author in list(author_export['Name']) and [ele for ele in mobwloc if(ele in mob_word)]:
                                expander_header = f"""{number2}. {author} - {title}"""
                                with st.expander(expander_header):
                                    markdown = f"""

{english}

{greek}

_This text contains the following Words of Mobility: {mobwloc}_
                                    """
                                    st.write(markdown)
                            else:
                                continue
                        else:
                            if author in list(author_export['Name']):
                                expander_header = f"""{number2}. {author} - {title}"""
                                with st.expander(expander_header):
                                    markdown = f"""

{english}

{greek}

_This text contains the following Words of Mobility: {mobwloc}_
                                    """
                                    st.write(markdown)
                            else:
                                continue
                except:
                    st.write("Something isn't working!")


    # The following generate a data dump button
    # When you are ready to complete this, docs are at: https://docs.streamlit.io/library/api-reference/widgets/st.download_button
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(export)
    st.download_button(
        label="Download data selection as CSV",
        data=csv,
        file_name='odyssey_export.csv',
        mime='text/csv',
    )
    # Display some data for testing

if __name__ == "__main__":
    main()
