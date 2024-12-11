"""
The views module defines the Flask views (web pages) for the application.
Each view is a function that returns an HTML template to render in the browser.
"""

from collections import OrderedDict
from pathlib import Path

import flask
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Create a Flask Blueprint for the views
bp = flask.Blueprint("views", __name__)


@bp.route("/", methods=["GET"])
def index():
    """Serve the standard index page."""
    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    with open(instance_path / "date_of_last_nzgd_retrieval.txt", "r") as file:
        date_of_last_nzgd_retrieval = file.readline()

    # Load the Vs30 values from a Parquet file
    database_df = pd.read_parquet(
        instance_path / "website_database.parquet"
    ).reset_index()

    # Retrieve the available correlation options from the database dataframe to
    # populate the dropdowns in the user interface. Ignore None values.
    vs30_correlations = [
        x for x in database_df["vs30_correlation"].unique() if x is not None
    ]
    spt_vs_correlations = [
        x for x in database_df["spt_vs_correlation"].unique() if x is not None
    ]
    cpt_vs_correlations = [
        x for x in database_df["cpt_vs_correlation"].unique() if x is not None
    ]

    # Retrieve selected vs30 correlation. If no selection, default to "boore_2011"
    vs30_correlation = flask.request.args.get("vs30_correlation", default="boore_2011")

    # Retrieve selected spt_vs_correlation. If no selection, default to "brandenberg_2010"
    spt_vs_correlation = flask.request.args.get(
        "spt_vs_correlation", default="brandenberg_2010"
    )

    # Retrieve selected cpt_vs_correlation. If no selection, default to "andrus_2007_pleistocene".
    cpt_vs_correlation = flask.request.args.get(
        "cpt_vs_correlation", default="andrus_2007_pleistocene"
    )

    # Retrieve selected column to color by on the map. If no selection, default to "vs30".
    colour_by = flask.request.args.get("colour_by", default="vs30")

    # Retrieve selected column to plot as a histogram. If no selection, default to "vs30_log_residual".
    hist_by = flask.request.args.get(
        "hist_by",
        default="vs30_log_residual",  # Default value if no query parameter is provided
    )

    # Retrieve an optional custom query from request arguments
    query = flask.request.args.get("query", default=None)

    # Filter the dataframe for the selected vs30_correlation (applies to both CPT and SPT records)
    database_df = database_df[database_df["vs30_correlation"] == vs30_correlation]

    # Boolean masks for filtering the dataframe to only show the selected records on the map and histogram.
    # Assume spt_hammer_type is "Auto" for SPT records.
    spt_bool = (database_df["spt_vs_correlation"] == spt_vs_correlation) & (
        database_df["spt_hammer_type"] == "Auto"
    )
    cpt_bool = database_df["cpt_vs_correlation"] == cpt_vs_correlation

    # Filter the dataframe to only show the selected records on the map and histogram
    database_df = database_df[spt_bool | cpt_bool]

    # Apply custom query filtering if provided
    if query:
        database_df = database_df.query(query)

    # Calculate the center of the map for visualization
    centre_lat = database_df["latitude"].mean()
    centre_lon = database_df["longitude"].mean()

    ## Make map marker sizes proportional to the absolute value of the Vs30 log residual.
    ## Map marker size values cannot include nans, so replace nans with 0.0
    database_df["size"] = database_df["vs30_log_residual"].abs().fillna(0.0)
    marker_size_description_text = r"Marker size indicates the magnitude of the Vs30 log residual, given by \(\mathrm{|(\log(SPT_{Vs30}) - \log(Foster2019_{Vs30})|}\)"

    ## Make new columns of string values to display instead of the float values for Vs30 and log residual
    ## so that an explanation can be shown when the vs30 value or the log residual
    database_df["Vs30 (m/s)"] = database_df["vs30"]
    database_df["Vs30_log_resid"] = database_df["vs30_log_residual"]
    if vs30_correlation == "boore_2011":
        reason_text = "Unable to estimate as Boore et al. (2011) Vs to Vs30 correlation requires a depth of at least 5 m"
        min_required_depth = 5
    else:
        reason_text = "Unable to estimate as Boore et al. (2004) Vs to Vs30 correlation requires a depth of at least 10 m"
        min_required_depth = 10
    database_df.loc[database_df["max_depth"] < min_required_depth, "Vs30 (m/s)"] = (
        reason_text
    )
    database_df.loc[
        (database_df["max_depth"] >= min_required_depth)
        & (np.isnan(database_df["vs30"]) | (database_df["vs30"] == 0)),
        "Vs30 (m/s)",
    ] = "Vs30 calculation failed even though CPT depth is sufficient"
    database_df.loc[
        (database_df["max_depth"] >= min_required_depth)
        & ~(np.isnan(database_df["vs30"]) | (database_df["vs30"] == 0)),
        "Vs30 (m/s)",
    ] = database_df["vs30"].apply(lambda x: f"{x:.2f}")
    database_df.loc[(np.isnan(database_df["vs30_log_residual"])), "Vs30_log_resid"] = (
        "Unavailable as Vs30 could not be calculated"
    )
    database_df.loc[~(np.isnan(database_df["vs30_log_residual"])), "Vs30_log_resid"] = (
        database_df["vs30_log_residual"].apply(lambda x: f"{x:.2f}")
    )
    database_df["max_depth (m)"] = database_df["max_depth"]

    # Create an interactive scatter map using Plotly
    map = px.scatter_map(
        database_df,
        lat="latitude",  # Column specifying latitude
        lon="longitude",  # Column specifying longitude
        color=colour_by,  # Column specifying marker color
        hover_name=database_df["record_name"],
        zoom=5,
        size="size",  # Marker size
        center={"lat": centre_lat, "lon": centre_lon},  # Map center
        hover_data=OrderedDict(
            [  # Used to order the items in hover data (but lat and long are always first)
                ("max_depth (m)", ":.2f"),
                ("Vs30 (m/s)", True),
                ("Vs30_log_resid", True),
                ("size", False),
                ("vs30", False),
                ("vs30_log_residual", False),
            ]
        ),
    )

    # Create an interactive histogram using Plotly
    hist_plot = px.histogram(database_df, x=hist_by)
    hist_description_text = (
        f"Histogram of {hist_by}, showing {len(database_df)} records"
    )

    # If plotting the vs30_log_residual, add a note about the log residual calculation
    if hist_by == "vs30_log_residual":
        residual_description_text = r"Note: Vs30 residuals are given by \(\mathrm{\log(SPT_{Vs30}) - \log(Foster2019_{Vs30})} \)"
    else:
        residual_description_text = ""

    all_df_column_names = database_df.columns.tolist()
    col_names_to_exclude = [
        "index",
        "type",
        "link_to_pdf",
        "nzgd_url",
        "size",
        "total_depth",
        "original_reference",
        "error_from_data",
    ]
    col_names_to_display = [
        col_name
        for col_name in all_df_column_names
        if col_name not in col_names_to_exclude
    ]
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
        vs30_correlations=vs30_correlations,  # Pass all vs30_correlations for UI dropdown
        spt_vs_correlations=spt_vs_correlations,
        cpt_vs_correlations=cpt_vs_correlations,
        num_records=len(database_df),
        colour_by=colour_by,
        hist_by=hist_by,
        colour_variables=[
            ("vs30", "Inferred Vs30 from data"),
            ("type_number_code", "Type of record"),
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
        hist_plot=hist_plot.to_html(
            full_html=False,  # Embed only the necessary map HTML
            include_plotlyjs=False,  # Exclude Plotly.js library (assume it's loaded separately)
            default_height="85vh",  # Set the map height
        ),
        marker_size_description_text=marker_size_description_text,
        hist_description_text=hist_description_text,
        residual_description_text=residual_description_text,
        col_names_to_display=col_names_to_display_str,
    )


@bp.route("/spt/<record_name>", methods=["GET"])
def spt_record(record_name: str):
    """
    Render the details page for a given SPT record.

    Parameters
    ----------
    record_name : str
        The name of the record to display.

    Returns
    -------
    The rendered HTML template for the SPT record page.
    """

    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    vs30_df_all_records = pd.read_parquet(
        instance_path / "website_database.parquet"
    ).reset_index()
    record_details_df = vs30_df_all_records[
        vs30_df_all_records["record_name"] == record_name
    ]

    record_details_df["estimate_number"] = np.arange(1, len(record_details_df) + 1)

    all_spt_df = pd.read_parquet(
        instance_path / "extracted_spt_data.parquet"
    ).reset_index()

    all_spt_df["record_name"] = "BH_" + all_spt_df["NZGD_ID"].astype(str)

    spt_df = all_spt_df[all_spt_df["record_name"] == record_name]
    spt_df = spt_df.rename(columns={"N": "Number of blows", "Depth": "Depth (m)"})
    soil_types_as_str = []
    for soil_type in spt_df["Soil Type"]:

        if len(soil_type) > 0:
            combined_soil_str = " + ".join(soil_type)
            soil_types_as_str.append(combined_soil_str)

        else:
            soil_types_as_str.append(None)

    spt_df["soil_types_as_str"] = soil_types_as_str

    # Plot the SPT data. line_shape is set to "vhv" to create a step plot with the correct orientation for vertical depth.
    spt_plot = px.line(spt_df, x="Number of blows", y="Depth (m)", line_shape="vhv")
    # Invert the y-axis
    spt_plot.update_layout(yaxis=dict(autorange="reversed"))

    return flask.render_template(
        "views/spt_record.html",
        record_details=record_details_df.to_dict(
            orient="records"
        ),  # Pass DataFrame as list of dictionaries
        spt_data=spt_df.to_dict(orient="records"),
        spt_plot=spt_plot.to_html(),
    )


@bp.route("/cpt/<record_name>", methods=["GET"])
def cpt_record(record_name: str):
    """
    Render the details page for a given CPT record.

    Parameters
    ----------
    record_name : str
        The name of the record to display.

    Returns
    -------
    The rendered HTML template for the CPT record page.
    """

    # Access the instance folder for application-specific data
    instance_path = Path(flask.current_app.instance_path)

    vs30_df_all_records = pd.read_parquet(
        instance_path / "website_database.parquet"
    ).reset_index()
    record_details_df = vs30_df_all_records[
        vs30_df_all_records["record_name"] == record_name
    ]

    ## Only show Vs30 values for correlations that could be used given the depth of the record
    max_depth_for_record = record_details_df["max_depth"].unique()[0]

    if max_depth_for_record < 5:
        vs30_correlation_explanation_text = (
            f"Unable to estimate a Vs30 value from {record_name} as it has a maximum depth "
            f"of {max_depth_for_record} m, while depths of at least 10 m and 5 m are required for "
            "the Boore et al. (2004) and Boore et al. (2011) Vs to Vs30 correlations, respectively."
        )
        show_vs30_values = False

    elif 5 <= max_depth_for_record < 10:
        vs30_correlation_explanation_text = (
            f"{record_name} has a maximum depth of {max_depth_for_record} m so only the Boore et al. (2011) "
            "Vs to Vs30 correlation can be used as it requires a depth of at least 5 m, while the "
            "Boore et al. (2004) correlation requires a depth of at least 10 m."
        )
        show_vs30_values = True
        record_details_df = record_details_df[
            record_details_df["vs30_correlation"] == "boore_2011"
        ]

    else:
        vs30_correlation_explanation_text = (
            f"{record_name} has a maximum depth of {max_depth_for_record} m so both the Boore et al. (2004) "
            "and Boore et al. (2011) Vs to Vs30 correlations can be used, as they require depths of at least "
            "10 m and 5 m, respectively."
        )
        show_vs30_values = True

    record_details_df["estimate_number"] = np.arange(1, len(record_details_df) + 1)

    # Only load the CPT data for the selected record
    cpt_df = pd.read_parquet(
        instance_path / "extracted_cpt_and_scpt_data.parquet",
        filters=[("record_name", "==", record_name)],
    ).reset_index()
    cpt_df = cpt_df.sort_values(by="Depth")

    # Plot the CPT data as a subplot with 1 row and 3 columns
    fig = make_subplots(rows=1, cols=3)

    fig.add_trace(go.Scatter(x=cpt_df["qc"], y=cpt_df["Depth"]), row=1, col=1)
    fig.add_trace(go.Scatter(x=cpt_df["fs"], y=cpt_df["Depth"]), row=1, col=2)
    fig.add_trace(go.Scatter(x=cpt_df["u"], y=cpt_df["Depth"]), row=1, col=3)

    fig.update_yaxes(title_text="Depth (m)", autorange="reversed", row=1, col=1)
    fig.update_yaxes(title_text="Depth (m)", autorange="reversed", row=1, col=2)
    fig.update_yaxes(title_text="Depth (m)", autorange="reversed", row=1, col=3)

    fig.update_xaxes(title_text=r"Cone resistance, qc (Mpa)", row=1, col=1)
    fig.update_xaxes(title_text="Sleeve friction, fs (Mpa)", row=1, col=2)
    fig.update_xaxes(title_text="Pore pressure, u2 (Mpa)", row=1, col=3)

    fig.update_layout(showlegend=False)

    return flask.render_template(
        "views/cpt_record.html",
        record_details=record_details_df.to_dict(
            orient="records"
        ),  # Pass DataFrame as list of dictionaries
        cpt_plot=fig.to_html(),
        vs30_correlation_explanation_text=vs30_correlation_explanation_text,
        show_vs30_values=show_vs30_values,
    )


@bp.route("/validate", methods=["GET"])
def validate():
    """
    Validate a query string against a dummy DataFrame.
    """
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
            "region",
            "district",
            "city",
            "suburb",
            "foster_2019_vs30",
            "foster_2019_vs30_std",
            "raw_file_links",
            "processed_file_links",
            "record_type",
            "processing_error",
            "max_depth",
            "min_depth",
            "depth_span",
            "num_depth_levels",
            "vs30",
            "vs30_std",
            "vs30_correlation",
            "cpt_vs_correlation",
            "spt_vs_correlation",
            "spt_used_soil_info",
            "spt_hammer_type",
            "spt_borehole_diameter",
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
