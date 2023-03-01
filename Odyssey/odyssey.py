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
def display_map(journ, agents, evid, places, range_min, range_max):
    latitude = 38
    longitude = 25


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
    journey_name = ''
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
    slider_range = st.sidebar.slider("Date Range", -1200, -500, (-1200,-500))
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
        agent_selector = ''

    # Create a journey searchbar
    journ_list = list(journ['Name'].unique())
    journ_list = [x for x in journ_list if str(x) != 'nan']
    journ_list.sort()
    journ_list = ['All'] + journ_list
    journ_selector = st.sidebar.selectbox("Select Journey", (journ_list))
    journ_name = journ_selector
    if journ_selector == 'All':
        journ_selector = ''

    # Create an agent type searchbar
# This goes with the above placeholder. Uncomment this when the search constructor is done
#    for i in search_list:
#        search_builder(i[0],i[1])
#        #st.write(i[0])

    # Display some data for testing
    st.write(journ.head(100))

if __name__ == "__main__":
    main()
