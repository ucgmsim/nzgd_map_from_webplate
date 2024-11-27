from pathlib import Path

import flask
import pandas as pd
import plotly.express as px

# Create a Flask Blueprint for the views
bp = flask.Blueprint("views", __name__)

@bp.route("/", methods=["GET"])
def index() -> str:
    """Serve the standard index page."""
    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    # Load intensity measures data from a Parquet file
    df = (
        pd.read_parquet(instance_path / "intensity_measures.parquet")
        .reset_index()  # Ensure a clean index for later operations
        .set_index(["station"])  # Set 'station' as the index for easier merging
    )

    # Extract unique intensity measures for UI dropdown or selection
    intensity_measures = df["intensity_measure"].unique()

    # Retrieve selected intensity measure or default to "PGA"
    im = flask.request.args.get(
        "intensity_measure",
        default="PGA",  # Default value if no query parameter is provided
    )

    # Retrieve an optional custom query from request arguments
    query = flask.request.args.get("query", default=None)

    # Filter the dataframe for the selected intensity measure
    df = df[df["intensity_measure"] == im]

    # Load station location data from a text file
    locations = pd.read_csv(
        instance_path / "stations.ll",
        sep=r"\s+",  # Handle whitespace-delimited file
        header=None,  # File does not have a header row
        names=["longitude", "latitude", "station"],  # Assign column names
    ).set_index("station")  # Set 'station' as index for merging

    # Join location data with intensity measure data
    df = df.join(locations)

    # Apply custom query filtering if provided
    if query:
        df = df.query(query)

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
        color="rotd50",  # Column specifying marker color
        hover_name=df.index,  # What to display when hovering over a marker
        hover_data={
            "rotd50": ":.2e",  # Format numerical values in scientific notation
            "rotd100": ":.2e",
            "000": ":.2e",
            "090": ":.2e",
            "ver": ":.2e",
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
    )


@bp.route("/validate", methods=["GET"])
def validate():
    query = flask.request.args.get("query", None)
    if not query:
        return ""

    # Create a dummy dataframe to ensure the column names are present
    dummy_df = pd.DataFrame(
        columns=[
            "station",
            "latitude",
            "longitude",
            "000",
            "090",
            "ver",
            "geom",
            "rotd50",
            "rotd100",
        ]
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