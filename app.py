import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# Page config
st.set_page_config(
    page_title="IMDB Movie Analytics",
    page_icon="🎬",
    layout="wide"
)

# Logo URLs
IMDB_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/IMDB_Logo_2016.svg/960px-IMDB_Logo_2016.svg.png"
SNAP_LOGO = "https://snapanalytics.co.uk/wp-content/uploads/2022/03/snap-analytics-Logo.png"

# Header with logos
header_col1, header_col2, header_col3 = st.columns([1, 3, 1])

with header_col1:
    st.image(IMDB_LOGO, width=120)

with header_col2:
    st.markdown(
        "<h1 style='text-align: center; margin-bottom: 0;'>Movie Analytics Dashboard</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #666; margin-top: 0;'>Exploring patterns in movie ratings, revenue, and genres</p>",
        unsafe_allow_html=True
    )

with header_col3:
    st.image(SNAP_LOGO, width=150)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("IMDB-Movie-Data.csv")
    df['Revenue (Millions)'] = pd.to_numeric(df['Revenue (Millions)'], errors='coerce')
    df['Metascore'] = pd.to_numeric(df['Metascore'], errors='coerce')
    return df

df = load_data()

# Sidebar branding and filters
st.sidebar.image(SNAP_LOGO, width=180)
st.sidebar.markdown("---")
st.sidebar.header("Filters")

# Year filter
year_range = st.sidebar.slider(
    "Year Range",
    min_value=int(df['Year'].min()),
    max_value=int(df['Year'].max()),
    value=(int(df['Year'].min()), int(df['Year'].max()))
)

# Rating filter
rating_range = st.sidebar.slider(
    "Rating Range",
    min_value=float(df['Rating'].min()),
    max_value=float(df['Rating'].max()),
    value=(float(df['Rating'].min()), float(df['Rating'].max()))
)

# Genre filter - extract unique genres
all_genres = []
for genres in df['Genre'].dropna():
    all_genres.extend([g.strip() for g in genres.split(',')])
unique_genres = sorted(set(all_genres))

selected_genres = st.sidebar.multiselect(
    "Select Genres",
    options=unique_genres,
    default=[]
)

# Apply filters
filtered_df = df[
    (df['Year'] >= year_range[0]) &
    (df['Year'] <= year_range[1]) &
    (df['Rating'] >= rating_range[0]) &
    (df['Rating'] <= rating_range[1])
]

if selected_genres:
    genre_mask = filtered_df['Genre'].apply(
        lambda x: any(g in str(x) for g in selected_genres)
    )
    filtered_df = filtered_df[genre_mask]

# KPI Metrics Row
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Movies", len(filtered_df))
with col2:
    st.metric("Avg Rating", f"{filtered_df['Rating'].mean():.2f}")
with col3:
    avg_revenue = filtered_df['Revenue (Millions)'].mean()
    st.metric("Avg Revenue", f"${avg_revenue:.1f}M" if pd.notna(avg_revenue) else "N/A")
with col4:
    st.metric("Avg Runtime", f"{filtered_df['Runtime (Minutes)'].mean():.0f} min")
with col5:
    avg_metascore = filtered_df['Metascore'].mean()
    st.metric("Avg Metascore", f"{avg_metascore:.0f}" if pd.notna(avg_metascore) else "N/A")

st.markdown("---")

# Row 1: Rating Distribution and Revenue by Year
col1, col2 = st.columns(2)

with col1:
    st.subheader("Rating Distribution")
    fig_rating = px.histogram(
        filtered_df,
        x='Rating',
        nbins=20,
        color_discrete_sequence=['#636EFA']
    )
    fig_rating.update_layout(
        xaxis_title="Rating",
        yaxis_title="Number of Movies",
        showlegend=False
    )
    st.plotly_chart(fig_rating, width="stretch")

with col2:
    st.subheader("Revenue Trends by Year")
    yearly_revenue = filtered_df.groupby('Year').agg({
        'Revenue (Millions)': 'mean',
        'Title': 'count'
    }).reset_index()
    yearly_revenue.columns = ['Year', 'Avg Revenue', 'Movie Count']

    fig_revenue = go.Figure()
    fig_revenue.add_trace(go.Bar(
        x=yearly_revenue['Year'],
        y=yearly_revenue['Avg Revenue'],
        name='Avg Revenue ($M)',
        marker_color='#00CC96'
    ))
    fig_revenue.add_trace(go.Scatter(
        x=yearly_revenue['Year'],
        y=yearly_revenue['Movie Count'],
        name='Movie Count',
        yaxis='y2',
        line=dict(color='#EF553B', width=3)
    ))
    fig_revenue.update_layout(
        yaxis=dict(title='Avg Revenue ($M)'),
        yaxis2=dict(title='Movie Count', overlaying='y', side='right'),
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_revenue, width="stretch")

# Row 2: Genre Analysis
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Genres by Movie Count")
    genre_counts = Counter()
    for genres in filtered_df['Genre'].dropna():
        for g in genres.split(','):
            genre_counts[g.strip()] += 1

    genre_df = pd.DataFrame(genre_counts.most_common(15), columns=['Genre', 'Count'])
    fig_genre = px.bar(
        genre_df,
        x='Count',
        y='Genre',
        orientation='h',
        color='Count',
        color_continuous_scale='Viridis'
    )
    fig_genre.update_layout(yaxis=dict(categoryorder='total ascending'), showlegend=False)
    st.plotly_chart(fig_genre, width="stretch")

with col2:
    st.subheader("Average Rating by Genre")
    genre_ratings = {}
    for _, row in filtered_df.iterrows():
        if pd.notna(row['Genre']):
            for g in row['Genre'].split(','):
                g = g.strip()
                if g not in genre_ratings:
                    genre_ratings[g] = []
                genre_ratings[g].append(row['Rating'])

    genre_rating_df = pd.DataFrame([
        {'Genre': g, 'Avg Rating': sum(r)/len(r), 'Count': len(r)}
        for g, r in genre_ratings.items()
    ])
    genre_rating_df = genre_rating_df[genre_rating_df['Count'] >= 5]
    genre_rating_df = genre_rating_df.sort_values('Avg Rating', ascending=False).head(15)

    fig_genre_rating = px.bar(
        genre_rating_df,
        x='Avg Rating',
        y='Genre',
        orientation='h',
        color='Avg Rating',
        color_continuous_scale='RdYlGn'
    )
    fig_genre_rating.update_layout(yaxis=dict(categoryorder='total ascending'), showlegend=False)
    st.plotly_chart(fig_genre_rating, width="stretch")

# Row 3: Runtime vs Rating Scatter and Director Analysis
col1, col2 = st.columns(2)

with col1:
    st.subheader("Runtime vs Rating (Revenue as Size)")
    scatter_df = filtered_df.dropna(subset=['Revenue (Millions)'])
    fig_scatter = px.scatter(
        scatter_df,
        x='Runtime (Minutes)',
        y='Rating',
        size='Revenue (Millions)',
        color='Year',
        hover_data=['Title', 'Director'],
        color_continuous_scale='Plasma'
    )
    fig_scatter.update_layout(
        xaxis_title="Runtime (Minutes)",
        yaxis_title="Rating"
    )
    st.plotly_chart(fig_scatter, width="stretch")

with col2:
    st.subheader("Top Directors by Average Rating")
    director_stats = filtered_df.groupby('Director').agg({
        'Rating': 'mean',
        'Title': 'count',
        'Revenue (Millions)': 'mean'
    }).reset_index()
    director_stats.columns = ['Director', 'Avg Rating', 'Movie Count', 'Avg Revenue']
    director_stats = director_stats[director_stats['Movie Count'] >= 2]
    director_stats = director_stats.sort_values('Avg Rating', ascending=False).head(10)

    fig_director = px.bar(
        director_stats,
        x='Avg Rating',
        y='Director',
        orientation='h',
        color='Movie Count',
        hover_data=['Avg Revenue'],
        color_continuous_scale='Blues'
    )
    fig_director.update_layout(yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(fig_director, width="stretch")

# Row 4: Rating vs Metascore and Revenue Distribution
col1, col2 = st.columns(2)

with col1:
    st.subheader("IMDB Rating vs Metascore")
    metascore_df = filtered_df.dropna(subset=['Metascore'])
    fig_meta = px.scatter(
        metascore_df,
        x='Metascore',
        y='Rating',
        color='Year',
        hover_data=['Title'],
        trendline='ols',
        color_continuous_scale='Turbo'
    )
    fig_meta.update_layout(
        xaxis_title="Metascore (Critics)",
        yaxis_title="IMDB Rating (Audience)"
    )
    st.plotly_chart(fig_meta, width="stretch")

with col2:
    st.subheader("Revenue Distribution")
    revenue_df = filtered_df.dropna(subset=['Revenue (Millions)'])
    fig_revenue_dist = px.box(
        revenue_df,
        y='Revenue (Millions)',
        color_discrete_sequence=['#AB63FA']
    )
    fig_revenue_dist.update_layout(yaxis_title="Revenue (Millions $)")
    st.plotly_chart(fig_revenue_dist, width="stretch")

# Row 5: Top Movies Tables
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Highest Rated Movies")
    top_rated = filtered_df.nlargest(10, 'Rating')[['Title', 'Year', 'Rating', 'Director', 'Genre']]
    st.dataframe(top_rated, width="stretch", hide_index=True)

with col2:
    st.subheader("Top 10 Highest Grossing Movies")
    top_revenue = filtered_df.dropna(subset=['Revenue (Millions)']).nlargest(10, 'Revenue (Millions)')
    top_revenue = top_revenue[['Title', 'Year', 'Revenue (Millions)', 'Rating', 'Genre']]
    top_revenue['Revenue (Millions)'] = top_revenue['Revenue (Millions)'].apply(lambda x: f"${x:.1f}M")
    st.dataframe(top_revenue, width="stretch", hide_index=True)

# Genre Revenue Heatmap
st.markdown("---")
st.subheader("Genre Performance Matrix")

# Build genre stats
genre_stats = {}
for _, row in filtered_df.iterrows():
    if pd.notna(row['Genre']):
        for g in row['Genre'].split(','):
            g = g.strip()
            if g not in genre_stats:
                genre_stats[g] = {'ratings': [], 'revenues': [], 'votes': []}
            genre_stats[g]['ratings'].append(row['Rating'])
            if pd.notna(row['Revenue (Millions)']):
                genre_stats[g]['revenues'].append(row['Revenue (Millions)'])
            genre_stats[g]['votes'].append(row['Votes'])

genre_matrix = pd.DataFrame([
    {
        'Genre': g,
        'Avg Rating': sum(v['ratings'])/len(v['ratings']),
        'Avg Revenue ($M)': sum(v['revenues'])/len(v['revenues']) if v['revenues'] else 0,
        'Avg Votes': sum(v['votes'])/len(v['votes']),
        'Movie Count': len(v['ratings'])
    }
    for g, v in genre_stats.items()
])
genre_matrix = genre_matrix[genre_matrix['Movie Count'] >= 5]
genre_matrix = genre_matrix.sort_values('Movie Count', ascending=False).head(15)

fig_matrix = px.scatter(
    genre_matrix,
    x='Avg Revenue ($M)',
    y='Avg Rating',
    size='Movie Count',
    color='Avg Votes',
    text='Genre',
    color_continuous_scale='Reds'
)
fig_matrix.update_traces(textposition='top center')
fig_matrix.update_layout(height=500)
st.plotly_chart(fig_matrix, width="stretch")

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
            <p style='margin-bottom: 5px;'>Dashboard built by <strong>Snap Analytics</strong> for <strong>IMDb</strong></p>
            <p style='margin-top: 0;'>Data source: IMDB Movie Dataset | Powered by Streamlit & Plotly</p>
        </div>
        """,
        unsafe_allow_html=True
    )
