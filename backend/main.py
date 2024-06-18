
from datetime import datetime
import os
import pandas as pd
from bids_scraper import fetch_bids_data, scrape_bids_data
from credentials import DOWNLOAD_PATH
from zillow_scraper import zillow_crawler
from setup import MySQLConnection, log

urls = ["https://www.bid4assets.com/chestercopasheriffsales",
        "https://www.bid4assets.com/MontcoPASheriff",
        "https://www.bid4assets.com/berkscountysheriffsales",
        "https://www.bid4assets.com/philataxsales",
        "https://www.bid4assets.com/philaforeclosures"
]

def delete_files(directory, file_pattern=None):
    """
    Deletes files in the specified directory. If a file pattern is provided, only files
    matching the pattern will be deleted. If no pattern is provided, all files in the
    directory will be deleted.
    
    Parameters:
    directory (str): The path to the directory where files will be deleted.
    file_pattern (str, optional): A pattern to match files to be deleted. Defaults to None.
    """
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if file_pattern is None or file_pattern in filename:
                    os.remove(file_path)
                    log.info(f"Deleted file: {file_path}")
    except Exception as e:
        log.error(f"Error deleting files: {e}")

def save_bids_data(df):
    log.info(f"Saving data to the database. Total entries {len(df)}")
    with MySQLConnection() as cursor:
        insert_query = """
            INSERT INTO auction_data (
                auction_id, bid, bid_open_date, bid_closing_date, debt, address, 
                crawl_date, city, state, county, remark, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                bid = VALUES(bid),
                bid_open_date = VALUES(bid_open_date),
                bid_closing_date = VALUES(bid_closing_date),
                debt = VALUES(debt),
                address = VALUES(address),
                crawl_date = VALUES(crawl_date),
                city = VALUES(city),
                state = VALUES(state),
                county = VALUES(county),
                remark = VALUES(remark),
                created_at = COALESCE(created_at, VALUES(created_at));  -- Keep the old value if exists, otherwise use the new value
        """

        for _, row in df.iterrows():
            try:
                cursor.execute(insert_query, (
                    row['id'], row['bid'], row['bid_open_date'], row['bid_closing_date'], 
                    row.get('debt'), row['address'], row['crawl_date'], row['city'], 
                    row['state'], row['county'], row['remark'], datetime.now()
                ))
            except Exception as e:
                log.error(f"Error inserting data: {e}")
    log.info("Data saving complete.")

if __name__ == "__main__":
    for url in urls:
        try:
            df = scrape_bids_data(url)
            if not df.empty:
                save_bids_data(df)
        except Exception as e:
            log.error(f"An error occurred while processing {url}: {e}")
    zillow_crawler()
    delete_files(DOWNLOAD_PATH, '.xlsx')  # delete files after all urls have been processed