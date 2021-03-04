from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import * 
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *#UncertaintiesFactorized import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetRecalib import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *

from TIMBER.Analyzer import analyzer, Calibration
from TIMBER.Tools.Common import GetJMETag
import glob, os

class Bench(object):
    def __init__(self,tag,setname,year,filenames,cutstring=''):
        self.setname = setname
        self.isMC = False if 'data' in setname else True
        self.year = year
        self.cutstring = cutstring
        self.tag = tag
        self.filenames = filenames

        if not self.isMC: self.period = setname.split('data')[1][0]
        else: self.period = False

class BenchNanoAODtools(Bench):
    def __init__(self,tag,setname,year,filenames,cutstring='',kadfile='nanoaodtools_keep.txt'): # year = 201*
        # possible cutstring
        #"(FatJet_pt[0]>350)&&(FatJet_pt[1]>350)&&(FatJet_eta[0]<2.5)&&(FatJet_eta[1]<2.5)"
        super(BenchNanoAODtools,self).__init__(tag,setname,year,filenames,cutstring='')
        self.kadfile = kadfile

        self.jesUncertainty = "Total"
        self.redojec = True
        self.jettype = "AK8PFPuppi"
        self.corrector = createJMECorrector(
                            self.isMC, self.year, self.period,
                            self.jesUncertainty, self.redojec, self.jettype)

        if not self.isMC:
            self.mymodules = [self.corrector()]
        else:
            if self.year == '16':
                self.mymodules =  [self.corrector(),puAutoWeight_2016(),PrefCorr_2016()]
            elif self.year == '17':
                self.mymodules = [self.corrector(),puAutoWeight_2017(),PrefCorr_2017()]
            elif self.year == '18':
                self.mymodules = [self.corrector(),puAutoWeight_2018()]

        self.new_list = []
        for l in filenames:
            if '/store/user' not in l:
                full_path = 'root://cms-xrd-global.cern.ch/'+l
            else:
                full_path = l
            self.new_list.append(full_path)

    def run_nanoaodtools(self):
        output_dir = 'benchmark_out/'
        hadded_file = 'NanoAODtools_'+self.tag+'.root'
        # Postprocessor
        if len(self.new_list) > 1:
            p=PostProcessor(output_dir,self.new_list,
                        self.cutstring,
                        branchsel=self.kad_file,
                        outputbranchsel=self.kad_file,
                        modules=self.mymodules,
                        provenance=True,haddFileName=hadded_file)
            out = output_dir+hadded_file
        else:
            p=PostProcessor(output_dir,self.new_list,
                        self.cutstring,
                        branchsel=self.kad_file,
                        outputbranchsel=self.kad_file,
                        modules=self.mymodules,
                        provenance=True)
            out = output_dir+self.new_list[0]

        p.run()
        return out

class BenchTIMBER(Bench):
    def __init__(self,tag,setname,year,filenames,cutstring=''):
        super(BenchTIMBER,self).__init__(tag,setname,year,filenames,cutstring='')

        jes = Calibration("JES","TIMBER/Framework/src/JES_weight.cc",
                [GetJMETag("JES",str(year),"MC"),"AK8PFPuppi","","true"], corrtype="Calibration")
        jer = Calibration("JER","TIMBER/Framework/src/JER_weight.cc",
                [GetJMETag("JER",str(year),"MC"),"AK8PFPuppi"], corrtype="Calibration")
        jms = Calibration("JMS","TIMBER/Framework/src/JES_weight.cc",
                [], corrtype="Calibration")
        jmr = Calibration("JMR","TIMBER/Framework/src/JMR_weight.cc",
                [str(year)], corrtype="Calibration")
        
        self.a = analyzer(self.filenames)
        if cutstring != '':
            self.a.Cut("cutstring",cutstring)
        a.CalibrateVar(["FatJet_pt","FatJet_msoftdrop"],jes,evalArgs={"jets":"FatJets","rho":"fixedGridRhoFastjetAll"})
        a.CalibrateVar(["FatJet_pt","FatJet_msoftdrop"],jer,evalArgs={"jets":"FatJets","genJets":"GenJets"})
        a.CalibrateVar(["FatJet_msoftdrop"],jms,evalArgs={"nJets":"nFatJet"})
        a.CalibrateVar(["FatJet_msoftdrop"],jmr,evalArgs={"jets":"FatJets","genJets":"GenJets"})
    
    def run_timber(self):
        a.Snapshot('all','TIMBER_'+self.tag+'.root',"Events")
        