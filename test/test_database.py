from database import BenchmarkDB, GetTimeStamp, sql_create_bench_table, checkTagExists

class TestBenchmarkDB():
    @classmethod
    def setup_class(cls):
        cls.db = BenchmarkDB("testClass.db")
        cls.db.CreateTable(sql_create_bench_table.format("NanoAODtools"))
    def test_checkTagExistsFalse(self):
        assert not checkTagExists(self.db.connection.cursor(),'TIMBER','nonexistent_tag')
    def test_GetColumnName(self):
        print (self.db.GetColumnNames("TIMBER"))
        assert True
    def test_CreateBenchmark(self):
        attr = {
            "timestamp":GetTimeStamp(),
            "conditions":"test_CreateBenchmark",
            "process_time":100,
            "process_maxmem":100,
            "rootfile":"benchmark_out/test_CreateBenchmark.root"
        }
        self.db.CreateBenchmark("TIMBER",attr)
        self.db.CreateBenchmark("NanoAODtools",attr)
        assert True
    def test_PrintTable(self):
        self.db.PrintTable("TIMBER")
        self.db.PrintBenchmark("NanoAODtools","test_CreateBenchmark")
        assert True
    def test_checkTagExistsTrue(self):
        assert checkTagExists(self.db.connection.cursor(),'TIMBER','test_CreateBenchmark')
    def test_UpdateBenchmark(self):
        indict = {
            "timestamp":GetTimeStamp(),
            "conditions":"test_CreateBenchmark",
            "process_time":105,
            "process_maxmem":105,
        }
        self.db.UpdateBenchmark("TIMBER",indict)
        assert 105 in self.db.ReadBenchmark("TIMBER","test_CreateBenchmark")
    def test_EraseBenchmark(self):
        self.db.EraseBenchmark("TIMBER","test_CreateBenchmark")
        assert self.db.ReadBenchmark("TIMBER","test_CreateBenchmark") == None
 