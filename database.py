import sqlite3, glob, datetime
from sqlite3 import Error
from sqlite3.dbapi2 import Cursor

sql_create_bench_table = '''
CREATE TABLE IF NOT EXISTS {0}_benchmarks (
    id integer PRIMARY KEY,
    timestamp text NOT NULL,
    conditions text,
    process_time float,
    process_maxmem float,
    rootfile text
);
'''
update_str = '''
UPDATE {0}_benchmarks
SET
    timestamp = '{1}',
    process_time = {2},
    process_maxmem = {3}
WHERE conditions='{4}'
'''

def GetTimeStamp():
    return str(datetime.datetime.now().replace(microsecond=0))

def CreateConnection(db_file):
    '''Create a database connection to a SQLite database

    Args:
        db_file (str): Path to database file.

    Returns:
        sqlite3.Connection: Connection to the database.
    '''
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print("CreateConnection error %s"%e)
    
    return conn

class BenchmarkDB:
    def __init__(self,dbfile="TIMBERbench.db"):
        self.connection = CreateConnection(dbfile)
        if self.connection is not None:
            self.CreateTable(sql_create_bench_table.format("TIMBER"))

    def CreateTable(self,create_table_sql):
        '''Create a table from the create_table_sql statement

        Args:
            create_table_sql (str): SQL string to create table
        
        Returns:
            None
        '''
        try:
            sql_cursor = self.connection.cursor()
            sql_cursor.execute(create_table_sql)
        except Error as e:
            print("CreateTable error %s"%e)

    def CreateBenchmark(self,frameworkname,valdict):
        '''Create an benchmark entry for a given framework (TIMBER or other).
        Row entries are given by valdict (keys are columns).

        Args:
            frameworkname (str): Name of "framework" being benchmarked (ex. "TIMBER").
            valdict (dict): Dictionary of the entries for the SQL row.

        Returns:
            int: Last row id so that tables can be connected.
        '''

        columns = self.GetColumnNames(frameworkname)
        bench_entry = tuple([valdict[col] for col in columns])
        sql_cursor = self.connection.cursor()
        if checkTagExists(sql_cursor,frameworkname,valdict['conditions']):
            out = self.UpdateBenchmark(frameworkname,valdict) 
        else:
            sql_insert = '''INSERT INTO %s_benchmarks(%s) VALUES(%s)'''%(
                frameworkname,
                ','.join([col for col in columns]),
                ','.join(['?' for i in columns])
            )
            sql_cursor.execute(sql_insert,bench_entry)
            self.connection.commit()
            out = sql_cursor.lastrowid # used to connect tables
        return out

    def GetColumnNames(self,FWname):
        '''Get all column names in the current connection.

        Returns:
            list(str)
        '''
        try:
            sql_cursor = self.connection.cursor()
            query = sql_cursor.execute("SELECT * FROM %s_benchmarks"%FWname).description
        except Error as e:
            print ("GetColumNames error %s"%e)
        return [descrip[0] for descrip in query if 'id' not in descrip]

    def PrintTable(self,FWname):
        sql_cursor = self.connection.cursor()
    def UpdateBenchmark(self, FWname, valdict):
        '''Updates a benchmark entry in table FWname_benchmarks 
        for a certain tag.

        Args:
            FWname (str): Framework for table name.
            valdict (dict): Dictionary of entry values. Specifically needs the
                "conditions" and "timestamp" key/value pairs.

        Returns:
            int: Last row id so that tables can be connected.
        '''
        sql_cursor = self.connection.cursor()
        print (update_str.format(FWname, valdict['timestamp'], valdict['process_time'],valdict['process_maxmem'], valdict['conditions']))
        sql_cursor.execute(update_str.format(FWname, valdict['timestamp'], valdict['process_time'],valdict['process_maxmem'], valdict['conditions']))
        self.connection.commit()
        return sql_cursor.lastrowid

    def ReadBenchmark(self):
        pass

    def EditBenchmark(self):
        pass