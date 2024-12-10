import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import requests
import numpy as np

import findspark
findspark.init()

spark_url = 'local'

from pyspark.pandas import SparkSession,read_csv
from pyspark.pandas import SQLContext

spark = SparkSession.builder\
        .master(spark_url)\
        .appName('Spark Tutorial')\
        .config('spark.ui.port', '4040')\
        .getOrCreate()

# Set page configuration
st.set_page_config(page_title="Global Carbon Research Distribution", layout="wide")

# Load and prepare data
# df = pd.read_csv("final_data.csv")

df = read_csv("final_data.csv")
cleaned_df = df.dropna(subset=['latitude'])

df = pd.read_csv("final_data.csv")


topic_colors = {
    'Study of Soil Carbon Emissions and Organic CH4 Levels in Forests': [255, 0, 0],
    'High-Performance Activated Carbon Materials for CO2 Adsorption and Energy Applications': [0, 255, 0],
    'Electronic Structure of N-Doped Carbon Molecular Bonds for Electrocatalytic Applications.': [0, 0, 255],
    'Hydrogen Fuel Combustion Emissions in Diesel Engines': [255, 255, 0],
    'Modeling Carbon Flame Flow Dynamics and Pressure Using Data Results': [255, 0, 255],
    'Climate Change and Energy Development: A Study of Carbon Emissions and Data Modeling': [0, 255, 255],
    'Rural Pulmonary Health Protection in CEE and CFC Regions with Skewed Household Outputs near Mangroves and TL': [128, 0, 128],
    'High-temperature properties of carbon fiber composites.': [255, 165, 0]
}

@st.cache_data
def load_country_boundaries():
    """Load country boundary data"""
    geojson_url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
    countries_geojson = requests.get(geojson_url).json()
    return countries_geojson


def get_color_scale(value, max_value):
    """Generate color scale with better visibility"""
    if pd.isna(value) or value == 0:
        return [255, 255, 255, 100]  # White for no papers
    
    # Calculate intensity (0-1)
    intensity = value / max_value
    
    # Return purple-blue gradient based on intensity
    if intensity < 0.33:
        return [171, 217, 233, 200]  # Light blue-ish (#ABD9E9)
    elif intensity < 0.66:
        return [44, 123, 182, 200]   # Medium blue (#2C7BB6)
    else:
        return [2, 56, 88, 200]      # Dark blue (#023858)

def create_scatter_layer(df, mono_color):
    if mono_color:
        return pdk.Layer(
            'ScatterplotLayer',
            df,
            get_position=['longitude', 'latitude'],
            get_color=[65, 105, 225, 160],  # Royal blue with transparency
            get_radius=50000,
            pickable=True
        )
    else:
        return pdk.Layer(
            'ScatterplotLayer',
            df,
            get_position=['longitude', 'latitude'],
            get_color='topic_color',  # Use topic color
            get_radius=50000,
            pickable=True
        )


def create_geojson_layer(df, geojson_data, selected_region, regions):
    # Filter countries based on selected region
    if selected_region != "All":
        region_countries = regions[selected_region]
        # Filter geojson features for selected region
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                feature for feature in geojson_data["features"]
                if feature["properties"]["name"] in region_countries
            ]
        }
        # Filter dataframe for selected region
        df = df[df['affiliation'].str.contains('|'.join(region_countries), case=False)]

    # Create layer with filtered data
    location_counts = df.groupby(['affiliation'])['title'].count().to_dict()
    max_count = max(location_counts.values()) if location_counts else 1
    
    for feature in geojson_data['features']:
        country_name = feature['properties']['name']
        country_papers = sum(count for affiliation, count in location_counts.items() 
                           if country_name.lower() in affiliation.lower())
        feature['properties']['paper_count'] = country_papers
        feature['properties']['fill_color'] = get_color_scale(country_papers, max_count)

    return pdk.Layer(
        'GeoJsonLayer',
        geojson_data,
        opacity=0.8,
        stroked=True,
        filled=True,
        extruded=False,
        wire_frame=True,
        get_fill_color='properties.fill_color',
        get_line_color=[180, 180, 180, 100],
        get_line_width=1,
        pickable=True
        
    )

def get_view_state(selected_region):
    """Adjust map view based on selected region"""
    views = {
        "Asia": {"latitude": 30, "longitude": 100, "zoom": 2},
        "Europe": {"latitude": 50, "longitude": 10, "zoom": 3},
        "North America": {"latitude": 40, "longitude": -100, "zoom": 2},
        "South America": {"latitude": -15, "longitude": -60, "zoom": 2},
        "Africa": {"latitude": 0, "longitude": 20, "zoom": 2},
        "Oceania": {"latitude": -25, "longitude": 135, "zoom": 3},
        "All": {"latitude": 20, "longitude": 0, "zoom": 1}
    }
    view = views.get(selected_region, views["All"])
    return pdk.ViewState(
        latitude=view["latitude"],
        longitude=view["longitude"],
        zoom=view["zoom"],
        pitch=0
    )

def analyze_topics(df):
    """Analyze research topics from titles and abstracts"""
    # Combine title and abstract
    text = ' '.join(df['title'].astype(str) + ' ' + df['abstract'].astype(str))
    
    # Simple word frequency analysis
    common_words = ["the", "and", "of", "in", "to", "a", "for", "on", "with"]
    words = text.lower().split()
    word_freq = pd.Series(words).value_counts()
    word_freq = word_freq[~word_freq.index.isin(common_words)]
    
    return word_freq.head(10)

def main():
    st.title("Global Carbon Research Distribution")
    st.write("Visualization of carbon research papers by location")
    regions = {
        "Asia": ["China", "Japan", "India", "South Korea", "Taiwan", "Vietnam", "Thailand", "Indonesia", "Malaysia", "Philippines", "Singapore", "Cambodia", "Myanmar", "Laos", "Bangladesh", "Sri Lanka", "Nepal", "Mongolia"], 
        "Europe": ["Germany", "UK", "France", "Italy", "Spain", "Netherlands", "Belgium", "Switzerland", "Austria", "Sweden", "Norway", "Denmark", "Finland", "Ireland", "Portugal", "Greece", "Poland", "Czech Republic", "Hungary", "Romania", "Bulgaria", "Croatia", "Serbia", "Ukraine", "Belarus", "Lithuania", "Latvia", "Estonia"],
        "North America": ["United States", "Canada", "Mexico", "Costa Rica", "Panama", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Belize"],
        "South America": ["Brazil", "Argentina", "Chile", "Colombia", "Peru", "Venezuela", "Ecuador", "Bolivia", "Paraguay", "Uruguay", "Guyana", "Suriname"],
        "Africa": ["South Africa", "Egypt", "Nigeria", "Kenya", "Morocco", "Tunisia", "Algeria", "Ethiopia", "Ghana", "Cameroon", "Uganda", "Tanzania", "Rwanda", "Senegal", "Zimbabwe", "Zambia", "Angola", "Mozambique", "Ivory Coast", "Madagascar"],
        "Oceania": ["Australia", "New Zealand", "Papua New Guinea", "Fiji", "Solomon Islands", "Vanuatu", "New Caledonia", "French Polynesia", "Samoa", "Tonga"]
    }
    
    # Sidebar controls
    # Add search bar
    search_query = st.text_input("Search by assigned topic")
    # Filter data based on search query
    if search_query:
        search_words = search_query.split()
        filtered_df = cleaned_df[cleaned_df.apply(lambda row: any(word.lower() in str(row['assigned_Topic']).lower() or word.lower() in str(row['title']).lower() for word in search_words), axis=1)]
    else:
        filtered_df = cleaned_df
    st.sidebar.header("Region Filter")
    selected_region = st.sidebar.selectbox(
        "Select Region",
        ["All"] + list(regions.keys())
    )

    st.sidebar.header("Display Options")
    view_type = st.sidebar.radio(
        "Select View Type",
        ["Countries", "Points"],
        index=0
    )
    

    # Load country boundaries
    countries_geojson = load_country_boundaries()

    if selected_region != "All":
            region_countries = regions[selected_region]
            filtered_df = filtered_df[filtered_df['affiliation'].str.contains('|'.join(region_countries), case=False)]


    # Create appropriate layer based on selection
    mono_color = False
    if view_type == "Points":
        filtered_df['topic_color'] = filtered_df['assigned_Topic'].map(topic_colors)
        mono_color = st.checkbox("Use mono-color scatter plot", value=False)
        layer = create_scatter_layer(filtered_df,mono_color)
        tooltip = {
            "html": "<b>Affiliation:</b> {affiliation}<br/>"
                   "<b>Title:</b> {title}<br/>"
                   "<b>Year:</b> {year}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }
        
        st.write("Research Topic Color Scale:")
        legend_col1, legend_col2, legend_col3, legend_col4, legend_col5, legend_col6, legend_col7, legend_col8 = st.columns(8)

        
    else:
        layer = create_geojson_layer(filtered_df, countries_geojson, selected_region, regions)
        tooltip = {
            "html": "<b>{properties.name}</b><br/>"
                   "Papers: {properties.paper_count}",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }

    # Get appropriate view state
    view_state = get_view_state(selected_region)

    # Create deck
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/light-v9',
        tooltip=tooltip
    )

    st.pydeck_chart(deck)

    if view_type == "Points" and not mono_color:
        
        st.write("Research Topic Color Scale:")
        legend_col1, legend_col2, legend_col3, legend_col4, legend_col5, legend_col6, legend_col7, legend_col8 = st.columns(8)

        with legend_col1:
            st.color_picker("Study of Soil Carbon", "#FF0000", disabled=True)
        with legend_col2:
            st.color_picker("High-Performance Activated Carbon", "#00FF00", disabled=True)
        with legend_col3:  
            st.color_picker("Electronic Structure of N-Doped Carbon", "#0000FF", disabled=True)
        with legend_col4:
            st.color_picker("Hydrogen Fuel Combustion", "#FFFF00", disabled=True) 
        with legend_col5:
            st.color_picker("Modeling Carbon Flame Flow", "#FF00FF", disabled=True)
        with legend_col6:  
            st.color_picker("Climate Change and Energy", "#00FFFF", disabled=True)
        with legend_col7:
            st.color_picker("Rural Pulmonary Health Protection", "#800080", disabled=True)
        with legend_col8:
            st.color_picker("High-temperature properties", "#FFA500", disabled=True)

    if view_type == "Countries":
        st.write("Paper Count Scale:")
        legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
        with legend_col1:
            st.color_picker("No Papers", "#FFFFFF", disabled=True)
        with legend_col2:
            st.color_picker("Low", "#ABD9E9", disabled=True)
        with legend_col3:
            st.color_picker("Medium", "#2C7BB6", disabled=True)
        with legend_col4:
            st.color_picker("High", "#023858", disabled=True)

    st.header("Research Statistics")

    total_papers = len(filtered_df)
    total_affiliations = len(filtered_df['affiliation'].unique())
    year_range = f"{filtered_df['year'].min()} - {filtered_df['year'].max()}"
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
   
    with stat_col1:
        st.metric("Total Research Papers", total_papers)
    with stat_col2:
        st.metric("Number of Affiliations", total_affiliations)
    with stat_col3:
        st.metric("Year Range", year_range)
    # Count research by affiliation
    research_counts = filtered_df.groupby('affiliation').size().reset_index(name='count')
    research_details = filtered_df[['title', 'affiliation', 'year']]

    # Merge counts with details
    research_with_counts = pd.merge(research_details, research_counts, on='affiliation')

    st.header("Research Topics Distribution")


    ana_col1,ana_col2 = st.columns(2)
    with ana_col1:
        # Count and sort topics
        topic_distribution = filtered_df['assigned_Topic'].value_counts().reset_index()
        topic_distribution.columns = ['Topic', 'Number of Papers']

        # Display sorted table
        st.dataframe(
        topic_distribution,
        hide_index=True,
        width=800,
        height=400
        )

    with ana_col2:
        # Add pie chart for topics
        topic_dist = filtered_df['assigned_Topic'].value_counts().head(5)
        pie_chart = alt.Chart(topic_dist.reset_index()).mark_arc().encode(
            theta='count',
            color='assigned_Topic',
            tooltip=['assigned_Topic', 'count']
        ).properties(title='Top 5 Research Topics')
        st.altair_chart(pie_chart)


    # Add time series analysis
    st.header("Research Trends")
    yearly_papers = filtered_df.groupby('year')['title'].count()
    trend_chart = alt.Chart(yearly_papers.reset_index()).mark_line().encode(
        x='year:O',
        y='title:Q',
        tooltip=['year', 'title']
    ).properties(title='Papers Published by Year', height=300)
    st.altair_chart(trend_chart, use_container_width=True)

    # Add collaboration analysis
    collaborations = filtered_df.groupby(['affiliation']).agg({
        'title': 'count',
        'assigned_Topic': lambda x: len(x.unique())
    }).sort_values('title', ascending=False).head(5)

    st.header("Top Research Institutions")
    st.dataframe(collaborations.rename(columns={
        'title': 'Number of Papers',
        'assigned_Topic': 'Unique Topics'
    }))

    
if __name__ == "__main__":
    main()