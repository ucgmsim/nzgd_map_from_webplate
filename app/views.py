from pathlib import Path

import flask
import numpy as np
import pandas as pd
import plotly.express as px

from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Create a Flask Blueprint for the views
bp = flask.Blueprint("views", __name__)


@bp.route("/spt/<record_name>", methods=["GET"])
def spt_record(record_name: str) -> str:
    """
    Render the SPT record page for a given record name.

    Parameters
    ----------
    record_name : str
        The name of the record to display.

    Returns
    -------
    str
        The rendered HTML template for the SPT record page.
    """

    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    vs30_df_all_records = pd.read_parquet(instance_path / "website_database.parquet").reset_index()
    record_details_df = vs30_df_all_records[
        vs30_df_all_records["record_name"] == record_name
    ]

    record_details_df["estimate_number"] = np.arange(1, len(record_details_df) + 1)

    all_spt_df = pd.read_parquet(instance_path / "extracted_spt_data.parquet").reset_index()

    all_spt_df["record_name"] = "BH_" + all_spt_df["NZGD_ID"].astype(str)

    spt_df = all_spt_df[all_spt_df["record_name"] == record_name]
    spt_df = spt_df.rename(columns={"N": "Number of blows", "Depth": "Depth (m)"})
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

    spt_plot = px.line(spt_df, x="Number of blows", y="Depth (m)", line_shape="vhv")
    # Invert the y-axis
    spt_plot.update_layout(yaxis=dict(autorange="reversed"))

    return flask.render_template(
        "views/spt_record.html",
        record_details=record_details_df.to_dict(
            orient="records"
        ),  # Pass DataFrame as list of dictionaries)
        spt_data=spt_df.to_dict(orient="records"),
        spt_plot=spt_plot.to_html())


@bp.route("/cpt/<record_name>", methods=["GET"])
def cpt_record(record_name: str) -> str:
    """
    Render the SPT record page for a given record name.

    Parameters
    ----------
    record_name : str
        The name of the record to display.

    Returns
    -------
    str
        The rendered HTML template for the SPT record page.
    """

    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    vs30_df_all_records = pd.read_parquet(instance_path / "website_database.parquet").reset_index()
    record_details_df = vs30_df_all_records[
        vs30_df_all_records["record_name"] == record_name
    ]

    record_details_df["estimate_number"] = np.arange(1, len(record_details_df) + 1)

    cpt_df = pd.read_parquet(instance_path / "extracted_cpt_and_scpt_data.parquet", filters=[("record_name", "==", record_name)]).reset_index()
    cpt_df = cpt_df.sort_values(by="Depth")

# 'Depth', 'qc', 'fs', 'u'
    fig = make_subplots(rows=1, cols=3)

    fig.add_trace(go.Scatter(x=cpt_df["qc"], y=cpt_df["Depth"]), row=1, col=1)
    fig.add_trace(go.Scatter(x=cpt_df["fs"], y=cpt_df["Depth"]), row=1, col=2)
    fig.add_trace(go.Scatter(x=cpt_df["u"], y=cpt_df["Depth"]), row=1, col=3)

    # fig.update_yaxes(autorange="reversed", row=1, col=1)
    # fig.update_yaxes(autorange="reversed", row=1, col=2)
    # fig.update_yaxes(autorange="reversed", row=1, col=3)

    fig.update_yaxes(title_text="Depth (m)", autorange="reversed", row=1, col=1)
    fig.update_yaxes(title_text="Depth (m)", autorange="reversed", row=1, col=2)
    fig.update_yaxes(title_text="Depth (m)", autorange="reversed", row=1, col=3)

    fig.update_xaxes(title_text=r"Cone resistance, qc (Mpa)", row=1, col=1)
    fig.update_xaxes(title_text="Sleeve friction, fs (Mpa)", row=1, col=2)
    fig.update_xaxes(title_text="Pore pressure, u2 (Mpa)", row=1, col=3)

    return flask.render_template(
        "views/cpt_record.html",
        record_details=record_details_df.to_dict(
            orient="records"
        ),  # Pass DataFrame as list of dictionaries)
        cpt_plot=fig.to_html()
)


@bp.route("/", methods=["GET"])
def index() -> str:
    """Serve the standard index page."""
    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    with open(instance_path / "date_of_last_nzgd_retrieval.txt", "r") as file:
        date_of_last_nzgd_retrieval = file.readline()

    # Load the Vs30 values from a Parquet file
    df = pd.read_parquet(instance_path / "website_database.parquet").reset_index()
    ## hammer_type has three options ("Auto", "Safety", "Standard") but we only need to use one for the map


    # vs30_correlations for UI dropdown or selection
    vs30_correlations = df["vs30_correlation"].unique()
    spt_vs_correlations = df["spt_vs_correlation"].unique()
    cpt_vs_correlations = df["cpt_vs_correlation"].unique()

    # Retrieve selected vs30 correlation or default to "boore_2011"
    vs30_correlation = flask.request.args.get(
        "vs30_correlation",
        default="boore_2011",  # Default value if no query parameter is provided
    )

    # Retrieve selected spt_vs_correlation or default to "boore_2011"
    spt_vs_correlation = flask.request.args.get(
        "spt_vs_correlation",
        default="brandenberg_2010",  # Default value if no query parameter is provided
    )

    # Retrieve selected cpt_vs_correlation or default to "boore_2011"
    cpt_vs_correlation = flask.request.args.get(
        "cpt_vs_correlation",
        default="andrus_2007_pleistocene",  # Default value if no query parameter is provided
    )

    colour_by = flask.request.args.get(
        "colour_by",
        default="vs30",  # Default value if no query parameter is provided
    )
    # Retrieve an optional custom query from request arguments
    query = flask.request.args.get("query", default=None)

    # Filter the dataframe for the selected spt_vs_correlation_and_vs30_correlation
    df = df[df["vs30_correlation"] == vs30_correlation]

    spt_bool = (df["spt_vs_correlation"] == spt_vs_correlation) & (df["spt_hammer_type"] == "Auto")
    cpt_bool = df["cpt_vs_correlation"] == cpt_vs_correlation

    df = df[spt_bool | cpt_bool]

    # Apply custom query filtering if provided
    if query:
        df = df.query(query)

    # Calculate the center of the map for visualization
    centre_lat = df["latitude"].mean()
    centre_lon = df["longitude"].mean()

    ## Maker size values cannot include nans, so replace nans with 0.0
    df["size"] = df["vs30_log_residual"].abs().fillna(0.0)

    # Define the shapes for each type
    borehole_shape = "circle"
    cpt_shape = "square"
    scpt_shape = "diamond"

    # Add the new column "shape" based on the conditions
    df["shape"] = df["type"].map({
        "Borehole": borehole_shape,
        "CPT": cpt_shape,
        "SCPT": scpt_shape
    })

    num_records = len(df)

    marker_size_description_text = r"Marker size indicates the magnitude of the Vs30 log residual, given by \(\mathrm{|(\log(SPT_{Vs30}) - \log(Foster2019_{Vs30})|}\)"

    # Create an interactive scatter map using Plotly
    map = px.scatter_map(
        df,
        lat="latitude",  # Column specifying latitude
        lon="longitude",  # Column specifying longitude
        color=colour_by,  # Column specifying marker color
        hover_name=df["record_name"],
        zoom=5,
        size="size",  # Marker size
        center={"lat": centre_lat, "lon": centre_lon},  # Map center
        hover_data={
            "vs30": ":.2f",
            "max_depth": ":.2f",
            "vs30_log_residual": ":.2f",
            "size": False,  # Exclude size from hover data
        }
    )

    log_resid_hist = px.histogram(df, x="vs30_log_residual")
    hist_description_text = r"Distribution of Vs30 residuals, given by \(\mathrm{\log(SPT_{Vs30}) - \log(Foster2019_{Vs30})} \)"

    all_df_column_names = df.columns.tolist()
    col_names_to_exclude = ["index", "type", "link_to_pdf", "nzgd_url","size", "total_depth", "original_reference",
                            "error_from_data"]
    col_names_to_display = [col_name for col_name in all_df_column_names if col_name not in col_names_to_exclude]
    col_names_to_display_str = ", ".join(col_names_to_display)

    # Render the map and data in an HTML template
    return flask.render_template(
        "views/index.html",
        date_of_last_nzgd_retrieval=date_of_last_nzgd_retrieval,
        map=map.to_html(
            full_html=False,  # Embed only the necessary map HTML
            include_plotlyjs=False,  # Exclude Plotly.js library (assume it's loaded separately)
            default_height="85vh",  # Set the map height
        ),
        selected_vs30_correlation=vs30_correlation,  # Pass the selected vs30_correlation for the template
        selected_spt_vs_correlation=spt_vs_correlation,
        selected_cpt_vs_correlation=cpt_vs_correlation,
        query=query,  # Pass the query back for persistence in UI
        vs30_correlations=vs30_correlations, # Pass all vs30_correlations for UI dropdown
        spt_vs_correlations=spt_vs_correlations,
        cpt_vs_correlations=cpt_vs_correlations,
        num_records = num_records,
        colour_by=colour_by,
        colour_variables=[
            ("vs30", "Inferred Vs30 from data"),
            ("type_number_code","Type of record"),
            ("vs30_log_residual", "log residual with Foster et al. (2019)"),
            ("max_depth", "Maximum Depth"),
            ("vs30_std", "Vs30 standard deviation inferred from data"),
            ("foster_2019_vs30", "Vs30 from Foster et al. (2019)"),
            (
                "foster_2019_vs30_std",
                "Vs30 standard deviation from Foster et al. (2019)",
            ),
            ("min_depth", "Minimum Depth"),
            ("num_depth_levels", "Number of Depth Levels"),
            ("depth_span", "Depth Span"),
        ],
        log_resid_hist=log_resid_hist.to_html(
            full_html=False,  # Embed only the necessary map HTML
            include_plotlyjs=False,  # Exclude Plotly.js library (assume it's loaded separately)
            default_height="85vh",  # Set the map height
        ),
        marker_size_description_text=marker_size_description_text,
        hist_description_text=hist_description_text,
        col_names_to_display = col_names_to_display_str)


@bp.route("/validate", methods=["GET"])
def validate():
    query = flask.request.args.get("query", None)
    if not query:
        return ""

    # Create a dummy dataframe to ensure the column names are present
    dummy_df = pd.DataFrame(
        columns=['record_name', 'type', 'original_reference', 'investigation_date',
       'total_depth', 'published_date', 'latitude', 'longitude', 'region',
       'district', 'city', 'suburb', 'foster_2019_vs30',
       'foster_2019_vs30_std', 'raw_file_links', 'processed_file_links',
       'record_type', 'processing_error', 'max_depth', 'min_depth',
       'depth_span', 'num_depth_levels', 'vs30', 'vs30_std',
       'vs30_correlation', 'cpt_vs_correlation', 'spt_vs_correlation',
       'spt_used_soil_info', 'spt_hammer_type', 'spt_borehole_diameter',
       'vs30_log_residual']
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
