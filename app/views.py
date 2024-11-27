from pathlib import Path

import flask
import pandas as pd
import plotly.express as px

# Create a Flask Blueprint for the views
bp = flask.Blueprint("views", __name__)

@bp.route('/spt/<record_name>', methods=['GET'])
def spt_record(record_name: int) -> str:
    return ''


@bp.route("/", methods=["GET"])
def index() -> str:
    """Serve the standard index page."""
    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    # Load intensity measures data from a Parquet file
    df = pd.read_parquet(instance_path / "spt_vs30.parquet").reset_index()

    # Extract unique intensity measures for UI dropdown or selection
    intensity_measures = df["spt_vs_correlation_and_vs30_correlation"].unique()

    # Retrieve selected intensity measure or default to "PGA"
    im = flask.request.args.get(
        "intensity_measure",
        default="brandenberg_2010_boore_2011",  # Default value if no query parameter is provided
    )
    colour_by = flask.request.args.get(
        "colour_by",
        default="vs30_from_data",  # Default value if no query parameter is provided
    )
    # Retrieve an optional custom query from request arguments
    query = flask.request.args.get("query", default=None)

    # Filter the dataframe for the selected spt_vs_correlation_and_vs30_correlation
    df = df[df["spt_vs_correlation_and_vs30_correlation"] == im]

    # Apply custom query filtering if provided
    print(df[df['record_name'] == 'BH_16467'])
    if query:
        df = df.query(query)
    print(df[df['record_name'] == 'BH_16467'])

    # Calculate the center of the map for visualization
    centre_lat = df["latitude"].mean()
    centre_lon = df["longitude"].mean()

    # Add a constant size column for consistent marker sizes in the map
    df["size"] = 0.5

    # Create an interactive scatter map using Plotly
    im_map = px.scatter_map(
        df,
        lat="latitude",  # Column specifying latitude
        lon="longitude",  # Column specifying longitude
        color=colour_by,  # Column specifying marker color
        hover_name=df["record_name"],
        zoom=5,  # What to display when hovering over a marker
        hover_data={
            "vs30_from_data": ":.2f",  # Format numerical values in scientific notation
            "vs30_std_from_data": ":.2f",
            "min_depth": ":.2f",
            "max_depth": ":.2f",
            "depth_span": ":.2f",
            "num_depth_levels": ":.1f",
            "size": False,  # Exclude size from hover data
        },
        size="size",  # Marker size
        center={"lat": centre_lat, "lon": centre_lon},  # Map center
    )

    # Render the map and data in an HTML template
    return flask.render_template(
        "views/index.html",
        map=im_map.to_html(
            full_html=False,  # Embed only the necessary map HTML
            include_plotlyjs=False,  # Exclude Plotly.js library (assume it's loaded separately)
            default_height="85vh",  # Set the map height
        ),
        selected_im=im,  # Pass the selected intensity measure for the template
        query=query,  # Pass the query back for persistence in UI
        intensity_measures=intensity_measures,  # Pass all intensity measures for UI dropdown
        colour_by=colour_by,
        colour_variables=[
            ("vs30", "vs30"),
            ("vs30_std", "Vs30 Standard Deviation"),
            ("min_depth", "Minimum Depth"),
            ("max_depth", "Maximum Depth"),
            ("depth_span", "Depth Span"),
            ("num_depth_levels", "Number of Depth Levels"),
        ],
    )


@bp.route("/validate", methods=["GET"])
def validate():
    query = flask.request.args.get("query", None)
    if not query:
        return ""

    # Create a dummy dataframe to ensure the column names are present
    dummy_df = pd.DataFrame(
        columns=['record_name', 'type', 'original_reference', 'investigation_date',
       'total_depth', 'published_date', 'latitude', 'longitude', 'nzgd_url',
       'region', 'district', 'city', 'suburb', 'foster_2019_vs30',
       'foster_2019_vs30_std', 'error_from_data', 'vs30_from_data',
       'vs30_std_from_data', 'spt_vs_correlation', 'vs30_correlation',
       'used_soil_info', 'hammer_type', 'borehole_diameter', 'min_depth',
       'max_depth', 'depth_span', 'num_depth_levels',
       'spt_vs_correlation_and_vs30_correlation',
       'log_vs30_from_data_minus_log_vs30_from_foster_2019']
    )
    try:
        dummy_df.query(query)
    except (
        ValueError,
        SyntaxError,
        UnboundLocalError,
        pd.errors.UndefinedVariableError,
    ) as e:
        return flask.render_template("error.html", error=e)
    return ""
