import argparse, random
from database import *
from collections import OrderedDict
import ROOT, sys
import pprint

pp = pprint.PrettyPrinter(indent=4)

def RandRange(minval,maxval,minskip,maxskip):
    out = []
    toadd = minval
    while toadd < maxval:
        out.append(toadd)
        r = random.randint(minskip,maxskip)
        toadd += r
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Options to run a TIMBER benchmark.')
    parser.add_argument('-f', '--frameworks', metavar='FRAMEWORK', 
                        dest='frameworks',
                        default='TIMBER,NanoAODtools',
                        help='Comma-separated list of frameworks to compare (different tables in database')
    parser.add_argument('-t', '--tag', metavar='IN', 
                        dest='tag', required=True,
                        help='Identifying conditions to allow comparisons across frameworks')
    parser.add_argument('-i', '--db', metavar='DATABASE', 
                        dest='dbname', 
                        default='TIMBERbench.db',
                        help='SQLite database file to open')
    args = parser.parse_args()

    db = BenchmarkDB(args.dbname)
    info = OrderedDict()
    colnames = ['id']+db.GetColumnNames(args.frameworks.split(',')[0])
    for c in colnames:
        info[c] = {}
    for f in args.frameworks.split(','):
        # print (db.ReadBenchmark(f,args.tag))
        entryvals = zip(colnames,db.ReadBenchmark(f,args.tag))
        for entryval in entryvals:
            info[entryval[0]][f] = entryval[1]
    
    inputs = {}
    for frame in info['rootfile'].keys():
        inputs[frame] = {}
        inputs[frame]["file"] = ROOT.TFile.Open(info['rootfile'][frame])
        inputs[frame]["tree"] = inputs[frame]["file"].Get("Events")
        inputs[frame]["nentries"] = inputs[frame]["tree"].GetEntries()

    nentries = 0
    for iframe in range(0,len(inputs.keys())):
        if iframe == 0:
            nentries = inputs[frame]["nentries"]
        else:
            if inputs[frame]["tree"].GetEntries() != nentries:
                raise ValueError('Nentries do not match (%s vs %s)'%(nentries,inputs[frame]["tree"].GetEntries()))
    
    randrange = RandRange(1,nentries,1,10)
    fout = ROOT.TFile('benchmark_out/Comparing_%s.root'%args.tag,'RECREATE')

    vars_to_comp = {
        "pt":{"TIMBER":"CalibratedFatJet_pt","NanoAODtools":"FatJet_pt_nom"},
        "mass":{"TIMBER":"CalibratedFatJet_mass","NanoAODtools":"FatJet_mass_nom"},
        "JES":{"TIMBER":"JES_nom","NanoAODtools":"FatJet_corr_JEC"},
        "pt_JESUp":{"TIMBER":"CalibratedFatJet_pt_JES__up","NanoAODtools":"FatJet_pt_jesTotalUp"},
        "pt_JESDown":{"TIMBER":"CalibratedFatJet_pt_JES__down","NanoAODtools":"FatJet_pt_jesTotalDown"},
        "pt_JERUp":{"TIMBER":"CalibratedFatJet_pt_JER__up","NanoAODtools":"FatJet_pt_jerUp"},
        "pt_JERDown":{"TIMBER":"CalibratedFatJet_pt_JER__down","NanoAODtools":"FatJet_pt_jerDown"},
        "mass_JESUp":{"TIMBER":"CalibratedFatJet_mass_JES__up","NanoAODtools":"FatJet_mass_jesTotalUp"},
        "mass_JESDown":{"TIMBER":"CalibratedFatJet_mass_JES__down","NanoAODtools":"FatJet_mass_jesTotalDown"},
        "mass_JERUp":{"TIMBER":"CalibratedFatJet_mass_JER__up","NanoAODtools":"FatJet_mass_jerUp"},
        "mass_JERDown":{"TIMBER":"CalibratedFatJet_mass_JER__down","NanoAODtools":"FatJet_mass_jerDown"},
        "mass_JMRUp":{"TIMBER":"CalibratedFatJet_mass_JMR__up","NanoAODtools":"FatJet_mass_jmrUp"},
        "mass_JMRDown":{"TIMBER":"CalibratedFatJet_mass_JMR__down","NanoAODtools":"FatJet_mass_jmrDown"},
        "mass_JMSUp":{"TIMBER":"CalibratedFatJet_mass_JMS__up","NanoAODtools":"FatJet_mass_jmsUp"},
        "mass_JMSDown":{"TIMBER":"CalibratedFatJet_mass_JMS__down","NanoAODtools":"FatJet_mass_jmsDown"},
        "JER":{"TIMBER":"JER_nom","NanoAODtools":"FatJet_corr_JER"},
        "JMS":{"TIMBER":"JMS_nom","NanoAODtools":"FatJet_corr_JMS"},
        "JMR":{"TIMBER":"JMR_nom","NanoAODtools":"FatJet_corr_JMR"}
    }

    for v in vars_to_comp.keys():
        # if 'JE' not in v and 'JM' not in v:
        vars_to_comp[v]["hist"] = ROOT.TH1F('%s_comp'%v,'TIMBER - NanoAODtools',200,-0.5,0.5)
        # else: vars_to_comp[v]["hist"] = ROOT.TH2F('%s_comp'%v,'TIMBER - NanoAODtools',200,-,0.6,200,0,400)
        vars_to_comp[v]["hist"].GetXaxis().SetTitle(v)

    for i,ientry in enumerate(randrange):
        sys.stdout.write("%i / %i ... \r" % (i,len(randrange)))
        sys.stdout.flush()
        for frame in inputs.keys():
            inputs[frame]['tree'].GetEntry(ientry)
            # if 'TIMBER' in frame:
            #     # inputs[frame]["FatJetColl"] = Collection(inputs[frame]["event"], "FatJet")
            #     inputs[frame]["FatJetColl"] = Collection(inputs[frame]["event"], "CalibratedFatJet", "nCalibratedFatJet")
            # else:
            #     inputs[frame]["FatJetColl"] = Collection(inputs[frame]["event"], "FatJet")

        if inputs['TIMBER']['tree'].nCalibratedFatJet > 0:
            for v in vars_to_comp.keys():
                timberval = getattr(inputs['TIMBER']['tree'],"%s"%vars_to_comp[v]["TIMBER"])[0]
                nanoval = getattr(inputs['NanoAODtools']['tree'],"%s"%vars_to_comp[v]["NanoAODtools"])[0]
                vars_to_comp[v]['hist'].Fill((timberval-nanoval)/nanoval)
    fout.cd()
    for v in vars_to_comp.keys():
        vars_to_comp[v]['hist'].Write()
    fout.Close()