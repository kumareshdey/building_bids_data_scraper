from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from pymysql.err import MySQLError
from setup import log, MySQLConnection

app = FastAPI()

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
    sortOrder: str = Query('ASC')
):
    offset = (page - 1) * pageSize
    query = f"SELECT * FROM auction_data ORDER BY {sortField} {sortOrder} LIMIT %s, %s"

    try:
        with MySQLConnection() as cursor:
            cursor.execute(query, (offset, pageSize))
            results = cursor.fetchall()
            
            # Column names from the table
            column_names = [desc[0] for desc in cursor.description]
            
            # Convert tuples to dictionaries
            result_dicts = [dict(zip(column_names, row)) for row in results]

        return result_dicts
    except MySQLError as e:
        log.error("Error while querying MySQL", e)
        raise HTTPException(status_code=500, detail="Error while querying the database")

@app.get('/auctions/count')
def count_auctions():
    query = "SELECT COUNT(*) AS total_count FROM auction_data"
    
    try:
        with MySQLConnection() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            total_count = result['total_count']
        
        return {"total_count": total_count}
    except MySQLError as e:
        log.error("Error while counting auctions", e)
        raise HTTPException(status_code=500, detail="Error while counting auctions")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
