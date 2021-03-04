import argparse, time
from memory_profiler import memory_usage
from database import *
from benches import BenchNanoAODtools, BenchTIMBER

parser = argparse.ArgumentParser(description='Options to run a TIMBER benchmark.')
parser.add_argument('-f', '--framework', metavar='FRAMEWORK', 
                    dest='framework', choices=['TIMBER','NanoAODtools'],
                    default='TIMBER',
                    help='Framework workflow to run')
parser.add_argument('inputs',nargs="*", help="Files to provide as input")
parser.add_argument('-s', '--setname', metavar='SET', 
                    dest='setname', required=True,
                    help='MC or data setname')
parser.add_argument('-y', '--year', metavar='YEAR', 
                    dest='year', required=True,
                    help='Processing year')
parser.add_argument('-t', '--tag', metavar='IN', 
                    dest='tag', required=True,
                    help='Identifying conditions to allow comparisons across frameworks')
parser.add_argument('-c', '--cut', metavar='IN', 
                    dest='cut', default='',
                    help='Cut string to apply (must be simple enough to pass both framworks)')

args = parser.parse_args()

run_data = {
    "timestamp":GetTimeStamp(),
    "conditions":args.tag,
    "process_time":None,
    "process_maxmem":None,
}

start_time = time.time()

# do stuff..
if args.framework == "TIMBER":
    bench = BenchTIMBER(args.tag, args.setname, args.year,
                        args.inputs, cutstring=args.cut)
    mem_usage = memory_usage(bench.run_timber(), interval=1) # 1 sec intervals

elif args.framework == "NanoAODtools":
    bench = BenchNanoAODtools(args.tag, args.setname, args.year,
                              args.inputs, cutstring=args.cut)
    mem_usage = memory_usage(bench.run_nanoaodtools(), interval=1)

run_data["process_time"] = time.time() - start_time
run_data["process_maxmem"] = max(mem_usage)

print (run_data)
# db = BenchmarkDB()
# db.CreateTable(sql_create_bench_table.format(args.framework))
# db.CreateBenchmark("TIMBER",run_data)
# db.connection.close()