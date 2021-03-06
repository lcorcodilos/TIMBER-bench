import argparse, time
from TIMBER.Tools.Common import OpenJSON
from memory_profiler import memory_usage
from database import *
from benches import BenchNanoAODtools, BenchTIMBER

parser = argparse.ArgumentParser(description='Options to run a TIMBER benchmark.')
parser.add_argument('-f', '--framework', metavar='FRAMEWORK', 
                    dest='framework', choices=['TIMBER','NanoAODtools'],
                    default='TIMBER',
                    help='Framework workflow to run')
parser.add_argument('-i', '--db', metavar='DATABASE', 
                    dest='dbname', 
                    default='TIMBERbench.db',
                    help='SQLite database file to open')
parser.add_argument('inputs',nargs="*", help="Files to provide as input")
parser.add_argument('-s', '--setname', metavar='SET', 
                    dest='setname', required=False,
                    help='MC or data setname')
parser.add_argument('-y', '--year', metavar='YEAR', 
                    dest='year', required=False,
                    help='Processing year')
parser.add_argument('-t', '--tag', metavar='IN', 
                    dest='tag', required=False,
                    help='Identifying conditions to allow comparisons across frameworks')
parser.add_argument('-c', '--cut', metavar='IN', 
                    dest='cut', default='',
                    help='Cut string to apply (must be simple enough to pass both framworks)')
parser.add_argument('--kad', metavar='IN', 
                    dest='kad', default='',
                    help='"Keep and drop" file for NanoAOD-tools')
parser.add_argument('--payload', metavar='IN', 
                    dest='payload', default='',
                    help='Payload which bypasses other command line options')
parser.add_argument('--dry-run', action='store_true',
                    dest='dryrun', default=False,
                    help='Dry-run will not save to database')
args = parser.parse_args()

if args.payload != '':
    payload = OpenJSON(args.payload)
    for o in payload.keys():
        if hasattr(args,o):
            setattr(args,o,payload[o])

run_data = {
    "timestamp":GetTimeStamp(),
    "conditions":args.tag,
    "process_time":None,
    "process_maxmem":None,
    "rootfile":None
}

start_time = time.time()

if args.framework == "TIMBER":
    bench = BenchTIMBER(args.tag, args.setname, args.year,
                        args.inputs, cutstring=args.cut)
    mem_usage = memory_usage(bench.run_timber)
elif args.framework == "NanoAODtools":
    bench = BenchNanoAODtools(args.tag, args.setname, args.year,
                              args.inputs, cutstring=args.cut, kadfile=args.kad)
    mem_usage = memory_usage(bench.run_nanoaodtools)

run_data["process_time"] = time.time() - start_time
run_data["process_maxmem"] = max(mem_usage)
run_data["rootfile"] = bench.outfilename

print (run_data)
if not args.dryrun:
    db = BenchmarkDB(args.dbname)
    db.CreateTable(sql_create_bench_table.format(args.framework))
    db.CreateBenchmark(args.framework,run_data)
    db.connection.close()