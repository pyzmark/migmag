import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import numpy as np
import re
import folium
from folium import plugins
import altair as alt
import ast
from odyssey_func import *
import json
from geojson import Point, LineString, GeometryCollection, Feature, FeatureCollection

# Set basic page information
app_title = ':amphora: Odyssey'
app_subtitle = 'An exploratory tool for mythical journeys. For internal use by MigMag staff.'

# Visualizations
def display_map(journ, agents, evid, places, range_min, range_max, hero_name, journ_name, dest_name, port_name, trav_type, journj, agentsj, evidj):
    latitude = 38
    longitude = 25

    # Create map and display it
    # Create map and display it
    odyssey_map = folium.Map(
        location=[latitude, longitude], 
        zoom_start=4, 
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        )

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
        agents = agents[agents['Traveller Type'].isin(trav_type)]
        agents = agents.reset_index(drop=True)
        agent_list = agents['Name'].tolist()
        for row, i in enumerate(journ['heroes']):
            if [ele for ele in i if(ele in agent_list)]:
                rows.append(row)
        journ = journ.loc[rows]
        journ = journ.reset_index(drop=True)
    if range_min > -1200 or range_max < 500:
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

    export = journ


    def marker_maker(opacity, fill_opacity, weight, popup, journey_label, pointa_label, pointb_label):
            sign =  folium.map.FeatureGroup(show=True) 
            sign.add_child(
                folium.PolyLine(path,
                        color='white',
                        weight=weight,
                        opacity=opacity,
                        smooth_factor=True,
                        popup=popup,
                        tooltip=journey_label))
            sign.add_child(
                folium.CircleMarker(location=pointa,
                                fill=True,
                                color='white',
                                fill_opacity=fill_opacity,
                                smooth_factor=True,
                                opacity=opacity,
                                weight=weight,
                                radius=6,
                                tooltip=pointa_label
                                ))
            sign.add_child(
                folium.CircleMarker(location=pointb,
                                fill=True,
                                color='white',
                                fill_opacity=fill_opacity,
                                smooth_factor=True,
                                opacity=opacity,
                                weight=weight,
                                radius=6,
                                tooltip=pointb_label
                                ))
            odyssey_map.add_child(sign)

    j_names = list(journ['Name'])
    j_pf = list(journ['Place From - Object ID'])
    j_pt = list(journ['Place to - Object ID'])
    j_id = list(journ['Object ID'])

    for name, object_id, pf_id, pt_id in zip(j_names, j_id, j_pf, j_pt):
        journey = journey_maker(name, pf_id, pt_id)
        if isinstance(journey[1], list) and isinstance(journey[2], list):
            #print(journey, "YUP")
            pointa = [journey[1][1],journey[1][0]]
            pointb = [journey[2][1],journey[2][0]]
            pointa_label = places[places['Object ID']==pf_id]['Name'].values[0]
            pointb_label = places[places['Object ID']==pt_id]['Name'].values[0]
            heroes = hero_grabber(object_id)

            if heroes:
                heroes = heroes
            else:
                heroes = "No heroes listed"

            journey_label = journey[0]
            path = [(pointa[0],pointa[1]),(pointb[0],pointb[1])]
            html=f"""
                <h3>{journey_label}</h3><br>
                Starting point: <code>{pointa_label}</code><br>
                End point: <code>{pointb_label}</code><br>
                Heroes involved: <code>{heroes}</code><br>

                """
            test = folium.Html(html, script=True)
            popup = folium.Popup(test, max_width=265, max_height=400, parse_html=True)

            # Layer controls (opacity, fill_opacity, weight, popup, journey_label, pointa_label, pointb_label)
            # True layer
            marker_maker(0.9,0.5,0.3,None,None,None,None)
            # Highlight layer
            marker_maker(0,0,8,popup,journey_label,pointa_label,pointb_label)

        else:
            #print(journey, "NUP")
            continue

        journ['Object ID'] = journ['Object ID'].astype(str)
    return odyssey_map, export, journ, text_display

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

    # These are placeholders for filter selections. 
    # Categories for agents
    hero_name = ''
    agent_type = ''
    time_period = ''
    traveller_type = ''
    # Categories for journeys
    journ_name = ''
    dest_name = ''
    place_from = ''
    place_to = ''
    story_type = ''
    movement_mode = ''
    traveller_type = ''
    # Categories for evidence
    evid_name = ''
    evid_author = ''
    # Categories for places
    # This does not seem like a profitable search tab, so I leave this empty for now


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
    def geo_grabber(place_id):
        nodegoat = places[places['Object ID']==place_id]['nodegoat ID'].values[0]
        #data = apicall(dt_dict['places'],nodegoat)
        try:
            results = places[places['Object ID']==place_id]['[GPS Location] Geometry'].values[0]
            results = ast.literal_eval(results)
            return results['coordinates']
        except:
            #results = json_search(data, 'object_sub_location_geometry')
            results = 'No coords'
            return results

    global journey_maker
    def journey_maker(name, pf_id, pt_id):
        # We need to grab geo data from the places. The csv doesn't have that, so we need place ids
        # Then we need to query the API for them
        # Then grab geo data from JSON object
        # above geo_grabber does that
        pf_geo = geo_grabber(pf_id)
        pt_geo = geo_grabber(pt_id)
        return name, pf_geo, pt_geo

    global period_grabber
    def period_grabber(agent_id):
        data = json_search(agentsj, agent_id)
        # The below is meant to drill down to data object 33543, which is typically where heroic participants
        # live in the JSON code. Once you find that, you can 
        results = json_search(data, '35556')
    #    hero_ids = results['object_definition_ref_object_id']
        period = results['object_definition_value']
        return period

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

    # Get all of the information you need from JSON files here to put into the skeletal dfs
    # Starting with Traveller type

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
    hero_selector = st.sidebar.multiselect("Select Named Traveller(s)", (hero_list))
    hero_name = hero_selector
    if hero_selector == 'All':
        hero_name = ''

    def searchbar_maker(df, col, title):
        list_name = list(df[col].unique())
        list_name = [x for x in list_name if str(x) != 'nan']
        list_name.sort()
        list_name = ['All'] + list_name
        selector = st.sidebar.multiselect(title, (list_name))
        name = selector
        if selector == 'All':
            name = ''
        return name

    journ_name = searchbar_maker(journ, 'Name', 'Selection Journey by Name')
    dest_name = searchbar_maker(journ, 'Place to', "Select Destination")
    port_name = searchbar_maker(journ,'Place From', "Select Port of Origin")
    trav_type = searchbar_maker(agents, 'Traveller Type', 'Traveller Type')
    # we remove 'author' as an option, as this will not be relevant

    # Create a time period searchbar
    period_list = ''

    # Create the date slider
    slider_range = st.sidebar.slider("Author Date Range (Not Relevant to Heroes)", -1200, 500, (-1200,500))
    range_min = slider_range[0]
    range_max = slider_range[1]

    # Create the map. This has a number of other variables that come out of the
    # display_map function. This includes export, which is for the csv button at
    # the bottom of the page. modjourn is a modified journ df that comes out of
    # the map, once filters are applied. text_display is a y/n switch that
    # tells the program whether to generate text for the subsection of journeys
    odyssey_map, export, modjourn, text_display = display_map(journ, agents, evid, places, range_min, range_max, hero_name, journ_name, dest_name, port_name, trav_type, journj, agentsj, evidj)



    # This begins the mapping function
    #odyssey = display_map(journ, agents, evid, places, range_min, range_max, hero_name, journ_name, journj)
    st_data = st_folium(odyssey_map, width=950, height=450)

# This function builds the markdown text evidence below the map.
# it relies on text_evidence, set in the odyssey_map function, to be true
    def text_maker(journeys):
        # Set header for all texts
        total_text = """## Textual Evidence

        """
        # There was a problem with multiple instances of the same journey
        # producing multiple text sections
        # The list below fixes that, as each journey is checked against the list
        journey_names = []
        for i in journeys:
            journey_name = grabber(journj, i, None, 'object_name')
            if journey_name not in journey_names:
                # We are stapling several sections together
                # total_text > sub_total_text > markdown
                #              sub_total_text > markdown
                #                             > markdown
                sub_total_text = f"""
-------
### {journey_name}
            
            """
                # Some problems with failures when JSON querying something that doesn't exist
                # So the check helps
                try:
                    evidence = grabber(journj, i, '35524', 'object_definition_ref_object_id')
                    for number, y in enumerate(evidence):
                        author = grabber(evidj, str(y), '35557', 'object_definition_value')
                        title = grabber(evidj, str(y), '36999', 'object_definition_value')
                        greek = grabber(evidj, str(y), '37023', 'object_definition_value')
                        english = grabber(evidj, str(y), '37024', 'object_definition_value')
                        number2 = str(number+1)
                        if len(greek) > 5:
                            markdown = f"""

#### {number2}. {author} - {title}
{english}


*{greek}*

                        """
                        else:
                            markdown = """

#### No text available for this journey

                        """
                        sub_total_text = ' '.join((sub_total_text, markdown))
                    total_text = ' '.join((total_text,sub_total_text))
                    journey_names.append(journey_name)
                except:
                    #number = number-1
                    journey_names.append(journey_name)
                    continue
            else:
                continue
        return total_text

    if text_display:
        markdown = text_maker(list(modjourn['Object ID']))
        st.markdown(markdown)
    

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
