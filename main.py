
from bids_scraper import fetch_bids_data
from setup import MySQLConnection, log

urls = ["https://www.bid4assets.com/philaforeclosures",
        "https://www.bid4assets.com/SchuylkillSheriffSales",
        "https://www.bid4assets.com/chestercopasheriffsales",
        "https://www.bid4assets.com/MontcoPASheriff"
]


def save_bids_data(df, cursor: MySQLConnection):
    log.info("Saving data to the database.")
    with MySQLConnection() as cursor:
        create_table_query = """
            CREATE TABLE IF NOT EXISTS auction_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                auction_id VARCHAR(255) UNIQUE,
                address TEXT,
                current_bid TEXT,
                debt FLOAT
                date DATE
            );
        """

        insert_query = """
            INSERT INTO auction_data (auction_id, address, current_bid, debt, date)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(create_table_query)
        log.info("Created auction_data table if it didn't exist.")

        for _, row in df.iterrows():
            try:
                cursor.execute(insert_query, tuple(row))
            except Exception as e:
                log.error(f"Error inserting data: {e}")

    log.info("Data saving complete.")
    return True

for url in urls:
    try:
        df = fetch_bids_data(url)
        if not df.empty:
            with MySQLConnection() as cursor:
                save_bids_data(df, cursor)
    except Exception as e:
        log.error(f"An error occurred while processing {url}: {e}")