
# app.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import requests
import json 

# Set page configuration
st.set_page_config(page_title="SF Airbnb Dashboard", layout="wide")
st.title("San Francisco Airbnb Listings Dashboard")

# Load and preprocess the data
dataframe = pd.read_csv("listings.csv")
dataframe['price'] = dataframe['price'].replace('[\$,]', '', regex=True).astype(float)
dataframe['estimated_revenue_l365d'] = pd.to_numeric(dataframe['estimated_revenue_l365d'], errors='coerce')
dataframe = dataframe.dropna(subset=['room_type', 'neighbourhood_cleansed', 'price', 'estimated_revenue_l365d'])

# Sidebar for filters
st.sidebar.title("Filters and Options")
st.sidebar.markdown("### Explore Airbnb Listings in SF!")

st.sidebar.header("Filter")

neighborhoods = ['All'] + sorted(dataframe['neighbourhood_cleansed'].unique())
selected_neighborhood = st.sidebar.selectbox("Select Neighborhood", neighborhoods)

selected_room = st.sidebar.selectbox("Select Room Type", dataframe['room_type'].unique())
price_range = st.sidebar.slider("Select Price Range", int(dataframe['price'].min()), int(dataframe['price'].max()), (50, 300))

filtered_df = dataframe.copy()
# if selected_neighborhood != 'All':
#     filtered_df = filtered_df[filtered_df['neighbourhood_cleansed'] == selected_neighborhood]
    
filtered_df = dataframe[(dataframe['room_type'] == selected_room) & 
                         (dataframe['price'].between(*price_range))]

if selected_neighborhood != 'All':
    filtered_df = filtered_df[filtered_df['neighbourhood_cleansed'] == selected_neighborhood]

# Column layout
col1, col2 = st.columns(2)

# 1st Bar chart = Average price by neighborhood
with col1:
    st.subheader("Average Price by Neighborhood")
    top_neighborhoods = filtered_df['neighbourhood_cleansed'].value_counts().nlargest(10).index
    df_top = filtered_df[filtered_df['neighbourhood_cleansed'].isin(top_neighborhoods)]

    bar = alt.Chart(df_top).mark_bar().encode(
        x=alt.X('neighbourhood_cleansed:N', sort='-y', title='Neighborhood'),
        y=alt.Y('mean(price):Q', title='Average Price ($)'),
        color=alt.Color('mean(price):Q', scale=alt.Scale(scheme='reds')),
        tooltip=['neighbourhood_cleansed', 'mean(price):Q', 'count():Q']
    ).properties(width=500, height=400)

    st.altair_chart(bar, use_container_width=True)

# 2nd Scatterplot = Availability vs Revenue
with col2:
    st.subheader("Availability vs Revenue")
    scatter1 = alt.Chart(filtered_df).mark_circle(opacity=0.5).encode(
        x=alt.X('availability_365:Q', title='Availability (Days)'),
        y=alt.Y('estimated_revenue_l365d:Q', title='Revenue ($)'),
        color=alt.Color('price:Q', scale=alt.Scale(scheme='viridis'), title='Price'),
        size=alt.Size('price:Q', scale=alt.Scale(range=[10, 200])),
        tooltip=['name', 'price', 'availability_365', 'estimated_revenue_l365d']
    ).properties(height=400)
    st.altair_chart(scatter1, use_container_width=True)

# 3rd Scatterplot = Reviews vs Revenue
st.subheader("Reviews vs Revenue")
scatter2 = alt.Chart(filtered_df).mark_circle(opacity=0.6).encode(
    x=alt.X('number_of_reviews:Q', title='Number of Reviews'),
    y=alt.Y('estimated_revenue_l365d:Q', title='Revenue ($)'),
    color=alt.Color('room_type:N'),
    size=alt.Size('price:Q', scale=alt.Scale(range=[10, 300])),
    tooltip=['name', 'price', 'number_of_reviews', 'estimated_revenue_l365d']
).properties(height=400)

st.altair_chart(scatter2, use_container_width=True)

# 4th Map of Listings Colored by Price
st.subheader("Map of Listings")
df_geo = filtered_df.dropna(subset=['latitude', 'longitude'])
df_geo = df_geo[df_geo['price'] < 1000] 

geojson_url = "https://gist.githubusercontent.com/cdolek/d08cac2fa3f6338d84ea/raw/ebe3d2a4eda405775a860d251974e1f08cbe4f48/SanFrancisco.Neighborhoods.json"
geojson_data = requests.get(geojson_url).json()

background = alt.Chart(alt.Data(values=geojson_data["features"])).mark_geoshape(
    fill='lightgray',
    stroke='white',
    fillOpacity=0.15
).project(
    type='identity'
).properties(width=600, height=600)

points = alt.Chart(df_geo).mark_circle(opacity=1).encode(
    longitude='longitude:Q',
    latitude='latitude:Q',
    color=alt.Color('price:Q', scale=alt.Scale(scheme='redyellowgreen'), title='Price ($)'),
    tooltip=['name:N', 'neighbourhood_cleansed:N', 'price:Q'],
    size=alt.Size('price:Q', scale=alt.Scale(range=[10, 300]))
).project(
    type='identity', reflectY=True
).properties(
    height=600,
    width=600,
    title='San Francisco Airbnb Listings'
)
map_chart = alt.layer(background, points).configure_view(stroke=None)

st.altair_chart(map_chart, use_container_width=True)