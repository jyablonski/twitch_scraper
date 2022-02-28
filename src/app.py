from datetime import datetime, date, timedelta
from itertools import islice
import logging
import os

import pandas as pd
from sqlalchemy import exc, create_engine
import twitch

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
    handlers=[logging.FileHandler("logs/example.log"), logging.StreamHandler()],
)

logging.info("STARTING TWITCH SCRAPE Version: 0.0.8")

client = twitch.TwitchHelix(client_id=os.environ.get("client_id"),
                            client_secret=os.environ.get("client_secret"),
                            scopes=[twitch.constants.OAUTH_SCOPE_ANALYTICS_READ_EXTENSIONS])
client.get_oauth()

def sql_connection(rds_schema):
    """
    SQL Connection function connecting to my postgres db with schema = nba_source where initial data in ELT lands
    Args:
        None
    Returns:
        SQL Connection variable to schema: nba_source in my PostgreSQL DB
    """
    RDS_USER = os.environ.get("RDS_USER")
    RDS_PW = os.environ.get("RDS_PW")
    RDS_IP = os.environ.get("IP")
    RDS_DB = os.environ.get("RDS_DB")
    try:
        connection = create_engine(
            f"postgresql+psycopg2://{RDS_USER}:{RDS_PW}@{RDS_IP}:5432/{RDS_DB}",
            connect_args={"options": f"-csearch_path={rds_schema}"},
            # defining schema to connect to
            echo=False,
        )
        logging.info(f"SQL Connection to {RDS_IP} with user {RDS_USER} and schema: {rds_schema} Successful")
        return connection
    except exc.SQLAlchemyError as e:
        logging.error(f"SQL Connection to schema: {rds_schema} Failed, Error: {e}")
        return e

def write_to_sql(con, data, table_type):
    """
    SQL Table function to write a Pandas DataFrame in {data}_source format
    Args:
        data: The Pandas DataFrame to store in SQL
        table_type: Whether the table should replace or append to an existing SQL Table under that name
    Returns:
        Writes the Pandas DataFrame to a Table in Snowflake in the {nba_source} Schema we connected to.
    """
    try:
        data_name = [k for k, v in globals().items() if v is data][0]
        # ^ this disgusting monstrosity is to get the name of the -fucking- dataframe lmfao
        if len(data) == 0:
            logging.info(f"{data_name} is empty, not writing to SQL")
        else:
            data.to_sql(
                con=con,
                name=f"{data_name}_source",
                index=False,
                if_exists=table_type,
            )
            logging.info(f"Writing {len(data)} rows from {data_name}_source to SQL")
    except BaseException as error:
        logging.error(f"SQL Write Script Failed, {error}")
        return error

def twitch_scrape(channel_count: int) -> pd.DataFrame:
    """
    Scraper Function which uses the Twitch Helix API to grab current Live Streaming Data

    Args:
        channel_count (int): The number of top channels you want to scrape
    
    Returns
        Pandas DataFrame of top channels
    """
    try:
        streams = client.get_streams(page_size=100) # get max amount of data at 1 time
        stream_list = []
        for stream in islice(streams, 0, channel_count):
            stream_list.append(stream)

        df = pd.DataFrame.from_records(stream_list)
        df['scrape_ts'] = datetime.now()
        
        logging.info(f"Twitch Scrape Successful, returning top {channel_count} channels at {datetime.now()}")
        return(df)
    except BaseException as e:
        logging.error(f"Error Occurred, {e}")
        return e

twitch_data = twitch_scrape(1000)

conn = sql_connection(os.environ.get("RDS_SCHEMA"))
write_to_sql(conn, twitch_data, "append")

logging.info("FINISHED TWITCH SCRAPE Version: 0.0.8")