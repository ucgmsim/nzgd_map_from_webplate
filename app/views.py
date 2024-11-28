from pathlib import Path

import flask
import pandas as pd
import plotly.express as px

# Create a Flask Blueprint for the views
bp = flask.Blueprint("views", __name__)


@bp.route("/spt/<record_name>", methods=["GET"])
def spt_record(record_name: int) -> str:

    link_to_pdf_prefix = Path("https://quakecoresoft.canterbury.ac.nz")
    link_to_extracted_spt_data = link_to_pdf_prefix / "processed" / "spt" / "extracted_spt_data.parquet"

    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)
    # Load intensity measures data from a Parquet file

    vs30_df = pd.read_parquet(instance_path / "spt_vs30.parquet").reset_index()

    all_spt_df = pd.read_parquet(instance_path / "out.parquet").reset_index()

    all_spt_df["record_name"] = "BH_" + all_spt_df["NZGD_ID"].astype(str)

    spt_df = all_spt_df[all_spt_df["record_name"] == record_name]
    spt_df = spt_df.rename(columns={'N': 'Number of blows', 'Depth': 'Depth (m)'})
    soil_types_as_str = []
    for soil_type in spt_df["Soil Type"]:

        if len(soil_type) > 0:
            combined_soil_str = ""
            for soil_str in soil_type:
                combined_soil_str += soil_str + " + "

            ## Remove the last "and" from the string
            combined_soil_str = combined_soil_str.strip(" + ")
            soil_types_as_str.append(combined_soil_str)

        else:
            soil_types_as_str.append(None)

    spt_df["soil_types_as_str"] = soil_types_as_str

    spt_plot = px.line(
        spt_df,
        x="Number of blows",
        y="Depth (m)")
    # Invert the y-axis
    spt_plot.update_layout(yaxis=dict(autorange='reversed'))

    return flask.render_template(
        "views/spt_record.html",
    record_name=record_name,
    spt_plot = spt_plot.to_html(),
    nzgd_url=vs30_df[vs30_df["record_name"] == record_name]["nzgd_url"].values[0],
    spt_data=spt_df.to_dict(orient='records'), # Pass DataFrame as list of dictionaries
    link_to_pdf = link_to_pdf_prefix / vs30_df[vs30_df["record_name"] == record_name]["link_to_pdf"].values[0],
    link_to_extracted_spt_data = link_to_extracted_spt_data)


@bp.route("/", methods=["GET"])
def index() -> str:
    """Serve the standard index page."""
    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    # Load intensity measures data from a Parquet file
    df = pd.read_parquet(instance_path / "spt_vs30.parquet").reset_index()

    # Correlations for UI dropdown or selection
    correlations = df["spt_vs_correlation_and_vs30_correlation"].unique()

    # Retrieve selected intensity measure or default to "PGA"
    correlation = flask.request.args.get(
        "correlation",
        default="brandenberg_2010_boore_2011",  # Default value if no query parameter is provided
    )
    colour_by = flask.request.args.get(
        "colour_by",
        default="vs30_from_data",  # Default value if no query parameter is provided
    )
    # Retrieve an optional custom query from request arguments
    query = flask.request.args.get("query", default=None)

    # Filter the dataframe for the selected spt_vs_correlation_and_vs30_correlation
    df = df[df["spt_vs_correlation_and_vs30_correlation"] == correlation]

    # Apply custom query filtering if provided
    if query:
        df = df.query(query)

    # Calculate the center of the map for visualization
    centre_lat = df["latitude"].mean()
    centre_lon = df["longitude"].mean()

    # Add a constant size column for consistent marker sizes in the map
    df["size"] = 0.5

    # Create an interactive scatter map using Plotly
    map = px.scatter_map(
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
        map=map.to_html(
            full_html=False,  # Embed only the necessary map HTML
            include_plotlyjs=False,  # Exclude Plotly.js library (assume it's loaded separately)
            default_height="85vh",  # Set the map height
        ),
        selected_correlation=correlation,  # Pass the selected correlation for the template
        query=query,  # Pass the query back for persistence in UI
        correlations=correlations,  # Pass all correlations for UI dropdown
        colour_by=colour_by,
        colour_variables=[
            ("vs30_from_data", "vs30 from data"),
            ("vs30_std_from_data", "Vs30 standard deviation from data"),
            ("vs30_log_residual", "log residual with Foster et al. (2019)"),
            ("max_depth", "Maximum Depth"),
            ("foster_2019_vs30", "Vs30 from Foster et al. (2019)"),
            ("foster_2019_vs30_std", "Vs30 standard deviation from Foster et al. (2019)"),
            ("min_depth", "Minimum Depth"),
            ("num_depth_levels", "Number of Depth Levels"),
            ("depth_span", "Depth Span")
        ],
    )


@bp.route("/validate", methods=["GET"])
def validate():
    query = flask.request.args.get("query", None)
    if not query:
        return ""

    # Create a dummy dataframe to ensure the column names are present
    dummy_df = pd.DataFrame(
        columns=[
            "record_name",
            "type",
            "original_reference",
            "investigation_date",
            "total_depth",
            "published_date",
            "latitude",
            "longitude",
            "nzgd_url",
            "region",
            "district",
            "city",
            "suburb",
            "foster_2019_vs30",
            "foster_2019_vs30_std",
            "error_from_data",
            "vs30_from_data",
            "vs30_std_from_data",
            "spt_vs_correlation",
            "vs30_correlation",
            "used_soil_info",
            "hammer_type",
            "borehole_diameter",
            "min_depth",
            "max_depth",
            "depth_span",
            "num_depth_levels",
            "spt_vs_correlation_and_vs30_correlation",
            "vs30_log_residual",
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
