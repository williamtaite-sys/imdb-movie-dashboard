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

# Sidebar branding
st.sidebar.image(SNAP_LOGO, width=180)
st.sidebar.markdown("---")

# Create tabs
tab_dashboard, tab_self_service = st.tabs(["Dashboard", "Self-Service Analytics"])

# =============================================================================
# TAB 1: DASHBOARD
# =============================================================================
with tab_dashboard:
    # Sidebar filters for Dashboard tab
    st.sidebar.header("Dashboard Filters")

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

# =============================================================================
# TAB 2: SELF-SERVICE ANALYTICS
# =============================================================================
with tab_self_service:
    st.subheader("Build Your Own Analysis")
    st.markdown("Select columns, apply filters, and aggregate data to create custom reports.")

    # Define column types for smart filtering
    numeric_cols = ['Year', 'Runtime (Minutes)', 'Rating', 'Votes', 'Revenue (Millions)', 'Metascore']
    text_cols = ['Title', 'Genre', 'Description', 'Director', 'Actors']
    all_cols = df.columns.tolist()

    # Layout: Config on left, Results on right
    config_col, results_col = st.columns([1, 2])

    with config_col:
        st.markdown("### 1. Select Columns")
        selected_columns = st.multiselect(
            "Choose columns to display",
            options=all_cols,
            default=['Title', 'Year', 'Rating', 'Revenue (Millions)'],
            help="Select which columns to include in your output"
        )

        st.markdown("---")
        st.markdown("### 2. Filter Data")

        # Dynamic filter builder
        ss_filtered_df = df.copy()

        # Year filter
        with st.expander("Year Filter", expanded=False):
            year_min, year_max = int(df['Year'].min()), int(df['Year'].max())
            ss_year_range = st.slider(
                "Select year range",
                min_value=year_min,
                max_value=year_max,
                value=(year_min, year_max),
                key="ss_year"
            )
            ss_filtered_df = ss_filtered_df[
                (ss_filtered_df['Year'] >= ss_year_range[0]) &
                (ss_filtered_df['Year'] <= ss_year_range[1])
            ]

        # Rating filter
        with st.expander("Rating Filter", expanded=False):
            rating_min, rating_max = float(df['Rating'].min()), float(df['Rating'].max())
            ss_rating_range = st.slider(
                "Select rating range",
                min_value=rating_min,
                max_value=rating_max,
                value=(rating_min, rating_max),
                key="ss_rating"
            )
            ss_filtered_df = ss_filtered_df[
                (ss_filtered_df['Rating'] >= ss_rating_range[0]) &
                (ss_filtered_df['Rating'] <= ss_rating_range[1])
            ]

        # Runtime filter
        with st.expander("Runtime Filter", expanded=False):
            runtime_min, runtime_max = int(df['Runtime (Minutes)'].min()), int(df['Runtime (Minutes)'].max())
            ss_runtime_range = st.slider(
                "Select runtime range (minutes)",
                min_value=runtime_min,
                max_value=runtime_max,
                value=(runtime_min, runtime_max),
                key="ss_runtime"
            )
            ss_filtered_df = ss_filtered_df[
                (ss_filtered_df['Runtime (Minutes)'] >= ss_runtime_range[0]) &
                (ss_filtered_df['Runtime (Minutes)'] <= ss_runtime_range[1])
            ]

        # Revenue filter
        with st.expander("Revenue Filter", expanded=False):
            rev_df = df['Revenue (Millions)'].dropna()
            if len(rev_df) > 0:
                rev_min, rev_max = float(rev_df.min()), float(rev_df.max())
                ss_rev_range = st.slider(
                    "Select revenue range ($M)",
                    min_value=rev_min,
                    max_value=rev_max,
                    value=(rev_min, rev_max),
                    key="ss_revenue"
                )
                include_null_revenue = st.checkbox("Include movies with no revenue data", value=True, key="ss_rev_null")
                if include_null_revenue:
                    ss_filtered_df = ss_filtered_df[
                        (ss_filtered_df['Revenue (Millions)'].isna()) |
                        ((ss_filtered_df['Revenue (Millions)'] >= ss_rev_range[0]) &
                         (ss_filtered_df['Revenue (Millions)'] <= ss_rev_range[1]))
                    ]
                else:
                    ss_filtered_df = ss_filtered_df[
                        (ss_filtered_df['Revenue (Millions)'] >= ss_rev_range[0]) &
                        (ss_filtered_df['Revenue (Millions)'] <= ss_rev_range[1])
                    ]

        # Director filter
        with st.expander("Director Filter", expanded=False):
            unique_directors = sorted(df['Director'].dropna().unique().tolist())
            selected_directors = st.multiselect(
                "Select directors",
                options=unique_directors,
                default=[],
                key="ss_directors"
            )
            if selected_directors:
                ss_filtered_df = ss_filtered_df[ss_filtered_df['Director'].isin(selected_directors)]

        # Text search filter
        with st.expander("Text Search", expanded=False):
            search_column = st.selectbox(
                "Search in column",
                options=['Title', 'Description', 'Actors', 'Genre'],
                key="ss_search_col"
            )
            search_text = st.text_input("Search text (case-insensitive)", key="ss_search_text")
            if search_text:
                ss_filtered_df = ss_filtered_df[
                    ss_filtered_df[search_column].astype(str).str.lower().str.contains(search_text.lower(), na=False)
                ]

        st.markdown("---")
        st.markdown("### 3. Aggregate Data (Optional)")

        enable_aggregation = st.checkbox("Enable aggregation", value=False)

        if enable_aggregation:
            group_by_cols = st.multiselect(
                "Group by columns",
                options=['Year', 'Director', 'Genre'],
                default=['Year'],
                key="ss_groupby"
            )

            agg_col = st.selectbox(
                "Column to aggregate",
                options=numeric_cols,
                index=2,  # Rating
                key="ss_agg_col"
            )

            agg_func = st.selectbox(
                "Aggregation function",
                options=['mean', 'sum', 'count', 'min', 'max', 'median', 'std'],
                index=0,
                key="ss_agg_func"
            )

        st.markdown("---")
        st.markdown("### 4. Sort & Limit")

        if selected_columns:
            sort_col = st.selectbox(
                "Sort by",
                options=selected_columns,
                index=0,
                key="ss_sort"
            )
            sort_order = st.radio(
                "Sort order",
                options=["Descending", "Ascending"],
                horizontal=True,
                key="ss_sort_order"
            )

        limit_rows = st.number_input(
            "Limit rows (0 = no limit)",
            min_value=0,
            max_value=1000,
            value=100,
            key="ss_limit"
        )

    with results_col:
        st.markdown("### Results")

        # Build output dataframe
        if enable_aggregation and group_by_cols:
            # Handle Genre specially since it's comma-separated
            if 'Genre' in group_by_cols:
                # Explode genres into separate rows
                temp_df = ss_filtered_df.copy()
                temp_df['Genre'] = temp_df['Genre'].str.split(',')
                temp_df = temp_df.explode('Genre')
                temp_df['Genre'] = temp_df['Genre'].str.strip()

                agg_dict = {agg_col: agg_func}
                output_df = temp_df.groupby(group_by_cols, as_index=False).agg(agg_dict)
                output_df.columns = group_by_cols + [f"{agg_func.title()}({agg_col})"]
            else:
                agg_dict = {agg_col: agg_func}
                output_df = ss_filtered_df.groupby(group_by_cols, as_index=False).agg(agg_dict)
                output_df.columns = group_by_cols + [f"{agg_func.title()}({agg_col})"]
        else:
            # No aggregation - just select columns
            if selected_columns:
                output_df = ss_filtered_df[selected_columns].copy()
            else:
                output_df = ss_filtered_df.copy()

        # Apply sorting
        if selected_columns and not output_df.empty:
            sort_ascending = sort_order == "Ascending"
            if enable_aggregation and group_by_cols:
                # Sort by aggregated column
                agg_col_name = f"{agg_func.title()}({agg_col})"
                if agg_col_name in output_df.columns:
                    output_df = output_df.sort_values(agg_col_name, ascending=sort_ascending)
            elif sort_col in output_df.columns:
                output_df = output_df.sort_values(sort_col, ascending=sort_ascending)

        # Apply limit
        if limit_rows > 0:
            output_df = output_df.head(limit_rows)

        # Display metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total Rows", len(output_df))
        with metric_col2:
            st.metric("Total Columns", len(output_df.columns))
        with metric_col3:
            st.metric("Filtered From", f"{len(ss_filtered_df)} movies")

        # Display the data
        st.dataframe(output_df, width="stretch", hide_index=True, height=400)

        # Download button
        csv = output_df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="custom_analysis.csv",
            mime="text/csv"
        )

        # Quick visualization
        st.markdown("---")
        st.markdown("### Quick Visualization")

        if not output_df.empty and len(output_df.columns) >= 2:
            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                chart_type = st.selectbox(
                    "Chart type",
                    options=["Bar", "Line", "Scatter", "None"],
                    key="ss_chart_type"
                )

            if chart_type != "None":
                numeric_output_cols = output_df.select_dtypes(include=['number']).columns.tolist()
                all_output_cols = output_df.columns.tolist()

                with viz_col2:
                    x_col = st.selectbox("X-axis", options=all_output_cols, key="ss_x")

                viz_col3, viz_col4 = st.columns(2)
                with viz_col3:
                    y_col = st.selectbox("Y-axis", options=numeric_output_cols if numeric_output_cols else all_output_cols, key="ss_y")
                with viz_col4:
                    color_col = st.selectbox("Color by (optional)", options=["None"] + all_output_cols, key="ss_color")

                color_param = None if color_col == "None" else color_col

                if chart_type == "Bar":
                    fig = px.bar(output_df.head(50), x=x_col, y=y_col, color=color_param)
                elif chart_type == "Line":
                    fig = px.line(output_df, x=x_col, y=y_col, color=color_param)
                elif chart_type == "Scatter":
                    fig = px.scatter(output_df, x=x_col, y=y_col, color=color_param)

                st.plotly_chart(fig, width="stretch")

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
