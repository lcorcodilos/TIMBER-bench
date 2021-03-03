from database import BenchmarkDB, CreateConnection, GetTimeStamp, sql_create_bench_table

class TestBenchmarkDB():
    @classmethod
    def setup_class(cls):
        cls.db = BenchmarkDB("testClass.db")
        cls.db.CreateTable(sql_create_bench_table.format("NanoAODtools"))
    def test_GetColumnName(self):
        print (self.db.GetColumnNames("TIMBER"))
        assert True
    def test_CreateBenchmark(self):
        attr = {
            "timestamp":GetTimeStamp(),
            "conditions":"test_CreateBenchmark",
            "process_time":100,
            "process_maxmem":100,
        }
        self.db.CreateBenchmark("TIMBER",attr)
        self.db.CreateBenchmark("NanoAODtools",attr)
        assert True

    def test_PrintTable(self):
        self.db.PrintTable("TIMBER")
        self.db.PrintTable("NanoAODtools")
        assert True