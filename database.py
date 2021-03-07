import sqlite3, glob, datetime
from sqlite3 import Error
from sqlite3.dbapi2 import Cursor
import pandas as pd

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
    process_maxmem = {3},
    rootfile = '{4}'
WHERE conditions='{5}'
'''

def GetTimeStamp():
    '''Return a string timestamp (date and time to the second).

    Returns:
        str: Timestamp
    '''
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

def checkTagExists(cursor,FWname,tag):
    '''Check that an entry with the given tag/conditions exists
    in the table associated with FWname.

    Args:
        cursor (SQLite cursor): Associated with the connection to the database.
        FWname (str): Framework name associated with the table we want.
        tag (str): Tag/conditions.

    Returns:
        bool: Whether there's an entry for the given tag/conditions.
    '''
    select_str = "SELECT id FROM {0}_benchmarks WHERE conditions='{1}'"
    cursor.execute(select_str.format(FWname,tag))
    if len(cursor.fetchall()) > 0:
        return True
    else:
        return False

class BenchmarkDB:
    '''Class to organize access to the database storing benchmarking information.
    '''
    def __init__(self,dbfile="TIMBERbench.db"):
        '''Initializer

        Args:
            dbfile (str, optional): Database name. Defaults to "TIMBERbench.db".
                Will be created if it does not exist. Will be opened otherwise.
                Delete it via the CLI to start over.
        '''
        self.connection = CreateConnection(dbfile)
        if self.connection is not None:
            self.CreateTable(sql_create_bench_table.format("TIMBER"))

    def CreateTable(self,create_table_sql):
        '''Create a table from the create_table_sql statement.

        Args:
            create_table_sql (str): SQL string to create table.
        
        Returns:
            None
        '''
        try:
            sql_cursor = self.connection.cursor()
            sql_cursor.execute(create_table_sql)
        except Error as e:
            print("CreateTable error %s"%e)

    def CreateBenchmark(self,frameworkname,valdict):
        '''Create a benchmark entry for a given framework (TIMBER or other).
        Row entries are given by valdict (keys are columns). Will instead UpdateBenchmark
        if entry with tag already exists.

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
        '''Print the table for a given framework (FWname).

        Args:
            FWname (str): Framework name.
        '''
        print (pd.read_sql_query("SELECT * FROM %s_benchmarks"%FWname,self.connection))

    def PrintBenchmark(self, FWname, tag):
        '''Print a benchmark for a specific framework and tag.

        Args:
            FWname (str): Framework name.
            tag (str): Tag/conditions.
        '''
        print (pd.read_sql_query("SELECT * FROM %s_benchmarks WHERE conditions='%s'"%(FWname,tag),self.connection))

    def ReadBenchmark(self,FWname, tag):
        '''Return a specific benchmark.

        Args:
            FWname (str): Framework name.
            tag (str): Tag/conditions.

        Returns:
            [type]: [description]
        '''
        sql_cursor = self.connection.cursor()
        sql_cursor.execute("SELECT * FROM {0}_benchmarks WHERE conditions='{1}'".format(FWname,tag))
        out = sql_cursor.fetchone()
        return out

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
        sql_cursor.execute(update_str.format(FWname, valdict['timestamp'], valdict['process_time'],valdict['process_maxmem'],valdict['rootfile'], valdict['conditions']))
        self.connection.commit()
        return sql_cursor.lastrowid
        
    def EraseBenchmark(self, FWname, tag):
        '''Erase a benchmark entry in table FWname_benchmarks 
        for a certain tag.

        Args:
            FWname (str): Framework name.
            tag (str): Tag/conditions.
        '''
        erase_str = "DELETE FROM {0}_benchmarks WHERE conditions='{1}'"
        sql_cursor = self.connection.cursor()
        sql_cursor.execute(erase_str.format(FWname,tag))
        self.connection.commit()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Options to modify a TIMBERbench database.')
    parser.add_argument('mode',nargs="*", help="Mode to run. Possibilities are `print` and `erase`.")
    parser.add_argument('-i', '--db', metavar='DATABASE', 
                        dest='dbname', 
                        default='TIMBERbench.db',
                        help='SQLite database file to open')
    parser.add_argument('-f', '--framework', metavar='FRAMEWORK', 
                    dest='framework', choices=['TIMBER','NanoAODtools'],
                    default='TIMBER',
                    help='Framework workflow to run')
    parser.add_argument('-t', '--tag', metavar='IN', 
                    dest='tag', default=None,
                    help='Identifying conditions to allow comparisons across frameworks')
    args = parser.parse_args()

    possible_modes = ['print']

    if len(args.mode) == 0: raise ValueError('No mode provided. Available modes are %s'%(''.join(possible_modes)))
    elif len(args.mode) > 1: print ('WARNING: Multiple modes specified (). Only the first is taken ().'%(''.join(args.mode),args.mode[0]))
    mode = args.mode[0]
    if mode not in possible_modes: raise ValueError('Provided mode (%s) not accepted. Available modes are %s'(mode,''.join(possible_modes)))

    db = BenchmarkDB(args.dbname)

    if mode == 'print':
        if args.tag == None:
            db.PrintTable(args.framework)
        else:
            db.PrintBenchmark(args.framework,args.tag)
    elif mode == 'erase':
        db.EraseBenchmark(args.framework,args.tag)