import sqlite3


class LocalDatabase():
    def __init__(self, db_name):
        try:
            self.con = sqlite3.connect(db_name)
        except Exception as e:
            print(e)
            print("Data is not persistent until the database is created.")

        self.cur = self.con.cursor()

    def insert_event(self, time, dev_id, dev_info, priority, description):
        event = (time, dev_id, dev_info, priority, description)
        self.cur.execute("INSERT into eventdata values (?,?,?,?,?);", event)
        self.con.commit()

    def shutdown(self):
        self.con.close()
