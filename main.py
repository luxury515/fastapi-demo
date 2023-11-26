from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import aiomysql

app = FastAPI()

# MySQL Configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'db': 'fastapi_db',
}


async def get_db():
    # Use the 'with' statement for better resource management
    async with aiomysql.create_pool(**DATABASE_CONFIG) as pool:
        async with pool.acquire() as connection:
            async with connection.cursor() as cursor:
                yield cursor
                # Commit changes to the database
                await connection.commit()


class Item(BaseModel):
    name: str
    description: str = None

@app.get("/items/", response_model=List[Item])
async def list_items(db: aiomysql.Connection = Depends(get_db)):
    query = "SELECT name, description FROM items"
    await db.execute(query)
    results = await db.fetchall()

    items = [{"name": result[0], "description": result[1]} for result in results]
    return items

@app.post("/items/", response_model=Item)
async def create_item(item: Item, db: aiomysql.Connection = Depends(get_db)):
    query = "INSERT INTO items (name, description) VALUES (%s, %s)"
    values = (item.name, item.description)
    
    try:
        await db.execute(query, values)
    except Exception as e:
        # Log the error for debugging
        print(f"Error inserting data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return item


@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int, db: aiomysql.Connection = Depends(get_db)):
    query = "SELECT name, description FROM items WHERE id = %s"
    await db.execute(query, (item_id,))
    result = await db.fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"name": result[0], "description": result[1]}


@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item, db: aiomysql.Connection = Depends(get_db)):
    query = "UPDATE items SET name = %s, description = %s WHERE id = %s"
    values = (item.name, item.description, item_id)

    try:
        await db.execute(query, values)
    except Exception as e:
        print(f"Error updating data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return item


@app.delete("/items/{item_id}", response_model=dict)
async def delete_item(item_id: int, db: aiomysql.Connection = Depends(get_db)):
    query = "DELETE FROM items WHERE id = %s"
    
    try:
        await db.execute(query, (item_id,))
    except Exception as e:
        print(f"Error deleting data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"message": "Item deleted"}