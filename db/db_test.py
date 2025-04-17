import sqlite3
import json
import uuid

conn = sqlite3.connect("neurosketch.db")
cursor = conn.cursor()


query = """
INSERT INTO sessions (id, title, canvas)
VALUES (?, ?, ?)
"""

session_id = str(uuid.uuid4())

user_id = "67119570-4772-4d63-92b2-326dffd95907"
title = "Drawing Some Random Shapes"

canvas_data = {
    "shapes": [
        {
            "type": "rectangle",
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 50,
        }]
}
canvas = json.dumps(canvas_data)

cursor.execute(query, (session_id, title, canvas))


participant_query = """
INSERT INTO session_participants (id,user_id)
VALUES (?, ?)
"""

cursor.execute(participant_query, (session_id, user_id))

conn.commit()