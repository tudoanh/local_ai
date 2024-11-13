from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
import sqlite_vec


class DatabaseWrapper(SQLiteDatabaseWrapper):
    def get_new_connection(self, conn_params):
        conn = super().get_new_connection(conn_params)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn
