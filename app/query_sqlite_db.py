import pandas as pd
import sqlite3
import time
import numpy as np

def extract_data(selected_vs30_correlation: str,
                 selected_cpt_to_vs_correlation: str,
                 selected_spt_to_vs_correlation: str,
                 selected_hammer_type: str,
                 conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Extracts CPT and SPT data from the SQLite database based on the selected correlations and hammer type.

    Parameters
    ----------
    selected_vs30_correlation : str
        The selected Vs to Vs30 correlation name.
    selected_cpt_to_vs_correlation : str
        The selected CPT to Vs correlation name.
    selected_spt_to_vs_correlation : str
        The selected SPT to Vs correlation name.
    selected_hammer_type : str
        The selected hammer type name.
    conn : sqlite3.Connection
        The SQLite database connection.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the extracted data.
    """

    vs_to_vs30_correlation_df = pd.read_sql_query("SELECT * FROM vstovs30correlation", conn)
    cpt_to_vs_correlation_df = pd.read_sql_query("SELECT * FROM cpttovscorrelation", conn)
    spt_to_vs_correlation_df = pd.read_sql_query("SELECT * FROM spttovscorrelation", conn)
    hammer_type_df = pd.read_sql_query("SELECT * FROM spttovs30hammertype", conn)

    vs_to_vs30_correlation_id_value = int(vs_to_vs30_correlation_df[vs_to_vs30_correlation_df["name"] == selected_vs30_correlation]["vs_to_vs30_correlation_id"].values[0])
    cpt_to_vs_correlation_id_value = int(cpt_to_vs_correlation_df[cpt_to_vs_correlation_df["name"] == selected_cpt_to_vs_correlation]["cpt_to_vs_correlation_id"].values[0])
    spt_to_vs_correlation_id_value = int(spt_to_vs_correlation_df[spt_to_vs_correlation_df["name"] == selected_spt_to_vs_correlation]["correlation_id"].values[0])
    hammer_type_id_value = int(hammer_type_df[hammer_type_df["name"] == selected_hammer_type]["hammer_id"].values[0])

    # The SQLite query to extract the CPT data.
    # It takes too long to extract all pre-computed CPT Vs30s values from the SQLite database,
    # so we only extract the Vs30 values that were calculated with the selected Vs to Vs30 correlation
    # (identified by vs_to_vs30_correlation_id_value) and the selected CPT to Vs correlation
    # (identified by cpt_to_vs_correlation_id_value).
    # We first filter on the Vs to Vs30 correlation, as there are only two, so this halves the number of rows
    # to search through. We also only select certain columns as some like the vs30_id column are not needed, so only
    # waste time if they are selected. We also filter using the integer id values to save time by avoiding needing
    # to use SQLite JOIN operations with the tables that contain the string names of the correlations.
    # In testing, this query takes about 0.4 seconds to run. If this is too slow, write the required
    # data to a parquet file and read that instead, as reading from a parquet file was found to be 10x faster in testing.
    cpt_sql_query = f"""
    WITH filtered_data AS (
        SELECT cpt_id, nzgd_id, cpt_to_vs_correlation_id, vs_to_vs30_correlation_id, vs30, vs30_stddev
        FROM cptvs30estimates
        WHERE vs_to_vs30_correlation_id = {vs_to_vs30_correlation_id_value}  -- First filter
    ), second_filter AS (
        SELECT cpt_id, nzgd_id, cpt_to_vs_correlation_id, vs_to_vs30_correlation_id, vs30, vs30_stddev
        FROM filtered_data
        WHERE cpt_to_vs_correlation_id = {cpt_to_vs_correlation_id_value}   -- Second filter
    )
    SELECT 
        sf.cpt_id, sf.nzgd_id, sf.vs30, sf.vs30_stddev,
        n.type_prefix, n.original_reference, n.investigation_date, n.published_date,
        n.latitude, n.longitude, n.region_id, n.district_id, n.city_id,
        n.suburb_id, n.model_vs30_foster_2019, n.model_vs30_stddev_foster_2019,
        n.model_gwl_westerhoff_2019, cr.tip_net_area_ratio, cr.measured_gwl,
        cr.deepest_depth, cr.shallowest_depth,
        r.name AS region_name,
        d.name AS district_name,
        sub.name AS suburb_name,
        cty.name AS city_name
    FROM second_filter AS sf
    JOIN nzgdrecord AS n
        ON sf.nzgd_id = n.nzgd_id
    JOIN region AS r
        ON n.region_id = r.region_id
    JOIN district AS d
        ON n.district_id = d.district_id
    JOIN suburb AS sub
        ON n.suburb_id = sub.suburb_id
    JOIN city AS cty
        ON n.city_id = cty.city_id
    JOIN cptreport AS cr
        ON sf.cpt_id = cr.cpt_id;
    """

    # Extract the CPT data from the SQLite database and store it in a Pandas DataFrame.
    # Also get timing points (t1, t2) to assess performance.
    t1 = time.time()
    cpt_database_df = pd.read_sql_query(cpt_sql_query, conn)
    t2 = time.time()

    # Add columns needed for the web app
    cpt_database_df["record_name"] = cpt_database_df["type_prefix"].astype(str) + "_" + cpt_database_df["nzgd_id"].astype(str)
    cpt_database_df["vs30_residual"] = np.log(cpt_database_df["vs30"]) - np.log(cpt_database_df["model_vs30_foster_2019"])
    cpt_database_df["gwl_residual"] = cpt_database_df["measured_gwl"] - cpt_database_df["model_gwl_westerhoff_2019"]

    # The SQLite query to extract the SPT data.
    # There far fewer SPT Vs30 values than CPT Vs30 values, so this should be fast, regardless of the query structure.
    spt_sql_query = f"""
    WITH filtered_data AS (
        SELECT *
        FROM sptvs30estimates
        WHERE vs_to_vs30_correlation_id = {vs_to_vs30_correlation_id_value}  -- First filter
    ), second_filter AS (
        SELECT *
        FROM filtered_data
        WHERE spt_to_vs_correlation_id = {spt_to_vs_correlation_id_value}   -- Second filter
    ), third_filter AS (
        SELECT *
        FROM second_filter
        WHERE hammer_type_id = {hammer_type_id_value}   -- Second filter
    )
    SELECT 
        tf.spt_id, tf.vs30, tf.vs30_stddev,
        n.type_prefix, n.original_reference, n.investigation_date, n.published_date,
        n.latitude, n.longitude, n.model_vs30_foster_2019, n.model_vs30_stddev_foster_2019,
        n.model_gwl_westerhoff_2019, sr.measured_gwl, sr.efficiency, sr.borehole_diameter,
        r.name AS region_name,
        d.name AS district_name,
        sub.name AS suburb_name,
        cty.name AS city_name
    FROM third_filter AS tf
    JOIN nzgdrecord AS n
        ON tf.spt_id = n.nzgd_id
    JOIN sptreport AS sr
        ON tf.spt_id = sr.borehole_id
    JOIN region AS r
        ON n.region_id = r.region_id
    JOIN district AS d
        ON n.district_id = d.district_id
    JOIN suburb AS sub
        ON n.suburb_id = sub.suburb_id
    JOIN city AS cty
        ON n.city_id = cty.city_id;
    """

    # Extract the SPT data from the SQLite database and store it in a Pandas DataFrame.
    # Also get timing points (t3, t4) to assess performance.
    t3 = time.time()
    spt_database_df = pd.read_sql_query(spt_sql_query, conn)
    t4 = time.time()

    # Rename and add columns needed for the web app
    spt_database_df.rename(columns={"spt_id": "nzgd_id"}, inplace=True)
    spt_database_df["record_name"] = spt_database_df["type_prefix"].astype(str) + spt_database_df["nzgd_id"].astype(str)
    spt_database_df["vs30_residual"] = np.log(spt_database_df["vs30"]) - np.log(spt_database_df["model_vs30_foster_2019"])
    spt_database_df["gwl_residual"] = spt_database_df["measured_gwl"] - spt_database_df["model_gwl_westerhoff_2019"]

    print(f"Time to extract CPT Vs30s and metadata from SQLite: {t2 - t1:.2f} s")
    print(f"Time to extract SPT Vs30s and metadata from SQLite: {t4 - t3:.2f} s")

    # Concatenate the CPT and SPT dataframes so they can both be queried with one Pandas query.
    # Columns that are only relevant for CPTs will be NaN for rows for SPTs (and vice versa).
    database_df = pd.concat([cpt_database_df, spt_database_df], ignore_index=True)

    return database_df

