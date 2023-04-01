import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import numpy as np
import re
import folium
from folium import plugins
import altair as alt

# Set basics
app_title = 'Odyssey'
app_subtitle = 'An exploratory tool for mythical journeys'

# Visualizations
def display_map(journ, agents, evid, places, range_min, range_max, agent_name, journ_name):
    latitude = 38
    longitude = 25

    if agent_name:
        agents = agents[agents['Name'] == agent_name]
    if journ_name:
        journ = journ[journ['Name'] == journ_name]
    if range_min > -1200:
        agents = agents.dropna(subset=['Earliest date'])
        # This is needed because someone snuck a few "0-1" into this column and it causes an error
        agents['Earliest date'] = agents['Earliest date'].replace('0-1',1)
        agents['Earliest date'] = agents['Earliest date'].astype(int)
        agents = agents[agents['Earliest date'] > range_min]
    if range_max < 500 :
        agents = agents.dropna(subset=['Latest date'])
        agents['Latest date'] = agents['Latest date'].replace('0-1',1)
        agents['Latest date'] = agents['Latest date'].astype(int)
        agents = agents[agents['Latest date'] < range_max]

    # Create map and display it
    odyssey_map = folium.Map(
        location=[latitude, longitude], zoom_start=5, tiles='cartodbdark_matter'
    )

    # This is just a bespoke journey to show what this might look like
    path = [(39.9574327844, 26.2384586227),
       (37.7300345711, 22.7540710459)]
    folium.PolyLine(path,
                color='#FC6D73',
                weight=1,
                opacity=0.8,
                dash_array='5').add_to(odyssey_map)
    folium.CircleMarker(location=[39.9574327844, 26.2384586227],
                        fill=True,
                        fill_color='#A2FC6D',
                        fill_opacity=0.8,
                        opacity=1,
                        weight=0.3,
                        radius=3,
                        ).add_to(odyssey_map)
    folium.CircleMarker(location=[37.7300345711, 22.7540710459],
                        fill=True,
                        fill_color='#A2FC6D',
                        fill_opacity=0.8,
                        opacity=1,
                        weight=0.3,
                        radius=3,
                        ).add_to(odyssey_map)

#    st.write(agents.head(100))
#    st.write(journ.head(100))
    return odyssey_map



def main():
    # Load Data
    agents = pd.read_csv('agents.csv')
    journ = pd.read_csv('mythjour.csv')
    evid = pd.read_csv('textevid.csv')
    places = pd.read_csv('places.csv')

    # Create basic visual elements
    st.set_page_config(app_title)
    st.title(app_title)
    st.caption(app_subtitle)

    # Rather than construct paramenters for each independent search bar below, this function builds it, based on inputs from a list
# This is not working now, but is something to implement later.
# For now I just construct a couple of searches manually.
#    def search_builder(df, selector_title):
#    #    st.write(df, selector_title)
#        global_dict = {"agents" : agents, 
#                       "journ" : journ, 
#                       "evid" : evid, 
#                       "places" : places
#                      }
#        list_of = list(eval(df, global_dict)[eval(selector_title)].unique())
#        # PROBLEM IS IN ABOVE LINE
#        list_of = [x for x in list_of if str(x) != 'nan']
#        list_of.sort()
#        list_of = ['All'] + list_of
#        list_of_selector = st.sidebar.selectbox("Select" + selector_title (list_of))
#        list_of = list_of_selector
#        if list_of_selector == 'All':
#            list_of_selector = ''
#
#    search_list = [['agents','Type of Agent'], ['agents','Mythical Time Period']]

    # These are placeholders for filter selections. 
    # Categories for agents
    agent_name = ''
    agent_type = ''
    time_period = ''
    # Categories for journeys
    journ_name = ''
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

    # Create the date slider
    slider_range = st.sidebar.slider("Date Range", -1200, 500, (-1200,500))
    range_min = slider_range[0]
    range_max = slider_range[1]

    # Create an agent searchbar
    agent_list = list(agents['Name'].unique())
    agent_list = [x for x in agent_list if str(x) != 'nan']
    agent_list.sort()
    agent_list = ['All'] + agent_list
    agent_selector = st.sidebar.selectbox("Select Agent", (agent_list))
    agent_name = agent_selector
    if agent_selector == 'All':
        agent_name = ''

    # Create a journey searchbar
    journ_list = list(journ['Name'].unique())
    journ_list = [x for x in journ_list if str(x) != 'nan']
    journ_list.sort()
    journ_list = ['All'] + journ_list
    journ_selector = st.sidebar.multiselect("Select Journey", (journ_list))
    journ_name = journ_selector
    if journ_selector == 'All':
        journ_name = ''

    # Create an agent type searchbar
# This goes with the above placeholder. Uncomment this when the search constructor is done
#    for i in search_list:
#        search_builder(i[0],i[1])
#        #st.write(i[0])
    odyssey = display_map(journ, agents, evid, places, range_min, range_max, agent_name, journ_name)
    st_data = st_folium(odyssey, width=750, height=500)

    # The following generate a data dump button
    # When you are ready to complete this, docs are at: https://docs.streamlit.io/library/api-reference/widgets/st.download_button
    @st.cache
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(agents)
    st.download_button(
        label="Download data selection as CSV",
        data=csv,
        file_name='odyssey_export.csv',
        mime='text/csv',
    )
    # Display some data for testing

if __name__ == "__main__":
    main()
