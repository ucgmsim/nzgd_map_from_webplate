"""
This module provides a function to extract pre-computed Vs30 values for CPT and SPT from
a SQLite database based on the selected correlations and hammer type.
"""

import pandas as pd
import sqlite3
import time
import numpy as np


def all_vs30s_given_correlations(
    selected_vs30_correlation: str,
    selected_cpt_to_vs_correlation: str,
    selected_spt_to_vs_correlation: str,
    selected_hammer_type: str,
    conn: sqlite3.Connection,
) -> pd.DataFrame:
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

    vs_to_vs30_correlation_df = pd.read_sql_query(
        "SELECT * FROM vstovs30correlation", conn
    )
    cpt_to_vs_correlation_df = pd.read_sql_query(
        "SELECT * FROM cpttovscorrelation", conn
    )
    spt_to_vs_correlation_df = pd.read_sql_query(
        "SELECT * FROM spttovscorrelation", conn
    )
    hammer_type_df = pd.read_sql_query("SELECT * FROM spttovs30hammertype", conn)

    vs_to_vs30_correlation_id_value = int(
        vs_to_vs30_correlation_df[
            vs_to_vs30_correlation_df["name"] == selected_vs30_correlation
        ]["vs_to_vs30_correlation_id"].values[0]
    )
    cpt_to_vs_correlation_id_value = int(
        cpt_to_vs_correlation_df[
            cpt_to_vs_correlation_df["name"] == selected_cpt_to_vs_correlation
        ]["cpt_to_vs_correlation_id"].values[0]
    )
    spt_to_vs_correlation_id_value = int(
        spt_to_vs_correlation_df[
            spt_to_vs_correlation_df["name"] == selected_spt_to_vs_correlation
        ]["correlation_id"].values[0]
    )
    hammer_type_id_value = int(
        hammer_type_df[hammer_type_df["name"] == selected_hammer_type][
            "hammer_id"
        ].values[0]
    )

    # The SQLite query to extract the pre-computed Vs30 values.
    # It takes too long to extract all pre-computed CPT Vs30s values from the SQLite database,
    # so we only extract the Vs30 values that were calculated with the selected Vs to Vs30 correlation
    # (identified by vs_to_vs30_correlation_id_value) and the selected CPT to Vs correlation
    # (identified by cpt_to_vs_correlation_id_value).
    # We first filter on the Vs to Vs30 correlation, as there are only two, so this halves the number of rows
    # to search through. We also only select certain columns as some like the vs30_id column are not needed, so only
    # waste time if they are selected. We also filter using the integer id values, rather than the names as strings,
    # to save time by avoiding SQLite JOIN operations with the tables that contain the string names of the correlations.
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
        n.latitude, n.longitude, n.model_vs30_foster_2019, n.model_vs30_stddev_foster_2019,
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
    cpt_database_df["record_name"] = (
        cpt_database_df["type_prefix"].astype(str)
        + "_"
        + cpt_database_df["nzgd_id"].astype(str)
    )
    cpt_database_df["vs30_residual"] = np.log(cpt_database_df["vs30"]) - np.log(
        cpt_database_df["model_vs30_foster_2019"]
    )
    cpt_database_df["gwl_residual"] = (
        cpt_database_df["measured_gwl"] - cpt_database_df["model_gwl_westerhoff_2019"]
    )

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
    spt_partial_database_df = pd.read_sql_query(spt_sql_query, conn)
    t4 = time.time()

    spt_measurements_df = pd.read_sql_query("SELECT * FROM sptmeasurements", conn)
    # Use Pandas groupby to quickly calculate the shallowest and deepest depths for each borehole
    depth_stats_df = (
        spt_measurements_df.groupby("borehole_id")["depth"]
        .agg(shallowest_depth="min", deepest_depth="max")
        .reset_index()
    )

    spt_database_df = pd.merge(
        spt_partial_database_df,
        depth_stats_df,
        left_on="spt_id",
        right_on="borehole_id",
        how="left",
    )
    spt_database_df.drop(columns="borehole_id", inplace=True)

    # Rename and add columns needed for the web app
    spt_database_df.rename(columns={"spt_id": "nzgd_id"}, inplace=True)
    spt_database_df["record_name"] = spt_database_df["type_prefix"].astype(
        str
    ) + spt_database_df["nzgd_id"].astype(str)
    spt_database_df["vs30_residual"] = np.log(spt_database_df["vs30"]) - np.log(
        spt_database_df["model_vs30_foster_2019"]
    )
    spt_database_df["gwl_residual"] = (
        spt_database_df["measured_gwl"] - spt_database_df["model_gwl_westerhoff_2019"]
    )

    print(f"Time to extract CPT Vs30s and metadata from SQLite: {t2 - t1:.2f} s")
    print(f"Time to extract SPT Vs30s and metadata from SQLite: {t4 - t3:.2f} s")

    # Concatenate the CPT and SPT dataframes so they can both be queried with a single Pandas query.
    # Columns that are only relevant for CPTs will be NaN for rows for SPTs (and vice versa).
    database_df = pd.concat([cpt_database_df, spt_database_df], ignore_index=True)
    database_df["type_number_code"] = database_df["type_prefix"].map(
        {"CPT": 0, "SCPT": 1, "BH": 2}
    )

    # rename the columns to match the web app and add prefixes of cpt spt to columns that only
    # apply to one of the two types of data
    database_df.rename(
        columns={
            "tip_net_area_ratio": "cpt_tip_net_area_ratio",
            "region_name": "region",
            "district_name": "district",
            "suburb_name": "suburb",
            "city_name": "city",
            "efficiency": "spt_efficiency",
            "borehole_diameter": "spt_borehole_diameter",
        },
        inplace=True,
    )

    return database_df


def cpt_measurements_for_one_nzgd(
    selected_nzgd_id: int, conn: sqlite3.Connection
) -> pd.DataFrame:
    """
    Extracts CPT measurements from the SQLite database for a given NZGD ID.
    Note that multiple CPT investigations (with different cpt_ids) can be returned,
    as some NZGD records contain multiple CPT investigations.

    Parameters
    ----------
    selected_nzgd_id : int
        The selected CPT ID.
    conn : sqlite3.Connection
        The SQLite database connection.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the CPT measurements and metadata as columns.
    """

    query = f"""SELECT 
    cptmeasurements.depth,
    cptmeasurements.qc,
    cptmeasurements.fs,
    cptmeasurements.u2,
    cptmeasurements.cpt_id,
    cptreport.nzgd_id
    FROM cptmeasurements
    JOIN cptreport ON cptmeasurements.cpt_id = cptreport.cpt_id
    WHERE cptreport.nzgd_id = {selected_nzgd_id};"""

    t1 = time.time()
    cpt_measurements_df = pd.read_sql_query(query, conn)
    t2 = time.time()

    print(
        f"Time to extract CPT measurements for cpt_id={selected_nzgd_id} from SQLite: {t2 - t1:.2f} s"
    )

    return cpt_measurements_df


def cpt_vs30s_for_one_nzgd_id(
    selected_nzgd_id: int, conn: sqlite3.Connection
) -> pd.DataFrame:
    """
    Extracts Vs30 values for a given CPT ID from the SQLite database.
    Note that multiple CPT investigations (with different cpt_ids) can be returned,
    as some NZGD records contain multiple CPT investigations.

    Parameters
    ----------
    selected_nzgd_id : int
        The selected NZGD ID.
    conn : sqlite3.Connection
        The SQLite database connection.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the Vs30 values and related metadata.
    """

    query = f"""SELECT 
    cptvs30estimates.cpt_id,
    cptvs30estimates.nzgd_id,
    cptvs30estimates.vs30,
    cptvs30estimates.vs30_stddev, 
    cptreport.cpt_file,
    cptreport.tip_net_area_ratio,
    cptreport.measured_gwl,
    cptreport.deepest_depth,
    cptreport.shallowest_depth,   
    cpttovscorrelation.name AS cpt_to_vs_correlation,
    vstovs30correlation.name AS vs_to_vs30_correlation,
    nzgdrecord.type_prefix,    
    nzgdrecord.original_reference,
    nzgdrecord.investigation_date,
    nzgdrecord.published_date,
    nzgdrecord.latitude,
    nzgdrecord.longitude,
    nzgdrecord.model_vs30_foster_2019,
    nzgdrecord.model_vs30_stddev_foster_2019,
    nzgdrecord.model_gwl_westerhoff_2019,
    region.name AS region,
    district.name AS district,
    city.name AS city,
    suburb.name AS suburb
    FROM cptvs30estimates
    JOIN cpttovscorrelation 
      ON cptvs30estimates.cpt_to_vs_correlation_id = cpttovscorrelation.cpt_to_vs_correlation_id
    JOIN vstovs30correlation 
      ON cptvs30estimates.vs_to_vs30_correlation_id = vstovs30correlation.vs_to_vs30_correlation_id
    JOIN cptreport
      ON cptvs30estimates.cpt_id = cptreport.cpt_id
    JOIN nzgdrecord
      ON cptvs30estimates.nzgd_id = nzgdrecord.nzgd_id
    JOIN region
        ON nzgdrecord.region_id = region.region_id
    JOIN district
        ON nzgdrecord.district_id = district.district_id
    JOIN suburb
        ON nzgdrecord.suburb_id = suburb.suburb_id
    JOIN city
        ON nzgdrecord.city_id = city.city_id
    WHERE cptvs30estimates.nzgd_id = {selected_nzgd_id};"""

    t1 = time.time()
    vs30_df = pd.read_sql_query(query, conn)

    # Add columns needed for the web app
    vs30_df["record_name"] = (
        vs30_df["type_prefix"].astype(str) + "_" + vs30_df["nzgd_id"].astype(str)
    )
    vs30_df["vs30_residual"] = np.log(vs30_df["vs30"]) - np.log(
        vs30_df["model_vs30_foster_2019"]
    )
    vs30_df["gwl_residual"] = (
        vs30_df["measured_gwl"] - vs30_df["model_gwl_westerhoff_2019"]
    )

    # rename the columns to match the web app and add prefixes of cpt spt to columns that only
    # apply to one of the two types of data
    vs30_df.rename(
        columns={
            "tip_net_area_ratio": "cpt_tip_net_area_ratio",
            "efficiency": "spt_efficiency",
            "borehole_diameter": "spt_borehole_diameter",
        },
        inplace=True,
    )

    t2 = time.time()

    print(
        f"Time to extract Vs30s for nzgd_id={selected_nzgd_id} from SQLite: {t2 - t1:.2f} s"
    )

    return vs30_df