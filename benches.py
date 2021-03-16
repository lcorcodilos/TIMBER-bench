from memory_profiler import profile
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import * 
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *#UncertaintiesFactorized import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetRecalib import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *

from TIMBER.Analyzer import analyzer, Calibration
from TIMBER.Tools.Common import GetJMETag
import glob, os, subprocess

PrefCorr_2016 = lambda : PrefCorr(jetroot='L1prefiring_jetpt_2016BtoH.root',
                            jetmapname='L1prefiring_jetpt_2016BtoH',
                            photonroot='L1prefiring_photonpt_2016BtoH.root',
                            photonmapname='L1prefiring_photonpt_2016BtoH')
PrefCorr_2017 = lambda : PrefCorr()

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
    def __init__(self,tag,setname,year,filenames,cutstring='',kadfile='keep_all.txt'): # year = 201*
        # possible cutstring
        #"(FatJet_pt[0]>350)&&(FatJet_pt[1]>350)&&(FatJet_eta[0]<2.5)&&(FatJet_eta[1]<2.5)"
        super(BenchNanoAODtools,self).__init__(tag,setname,year,filenames,cutstring='')
        self.kad_file = kadfile
        self.filenames = filenames
        self.jesUncertainty = "Total"
        self.jettype = "AK8PFPuppi"
        self.corrector = createJMECorrector(
                            self.isMC, self.year, self.period,
                            self.jesUncertainty, self.jettype,applySmearing=True)

        self.mymodules = [self.corrector()]
        # if not self.isMC:
        #     self.mymodules = [self.corrector()]
        # else:
        #     if self.year == '2016':
        #         self.mymodules =  [self.corrector(),puAutoWeight_2016(),PrefCorr_2016()]
        #     elif self.year == '2017':
        #         self.mymodules = [self.corrector(),puAutoWeight_2017(),PrefCorr_2017()]
        #     elif self.year == '2018':
        #         self.mymodules = [self.corrector(),puAutoWeight_2018()]

    def run_nanoaodtools(self):
        output_dir = 'benchmark_out/'
        hadded_file = 'NanoAODtools_'+self.tag+'.root'
        # Postprocessor
        # if len(self.filenames) > 1:
        p=PostProcessor(output_dir,self.filenames,
                    self.cutstring,
                    branchsel="keep_all.txt",
                    outputbranchsel=self.kad_file,
                    modules=self.mymodules,
                    provenance=True,haddFileName=hadded_file)
        
        self.outfilename = output_dir+hadded_file
        subprocess.call(["mv %s %s"%(hadded_file,self.outfilename)],shell=True)
        # else:
        #     p=PostProcessor(output_dir,self.filenames,
        #                 self.cutstring,
        #                 branchsel="keep_all.txt",
        #                 outputbranchsel=self.kad_file,
        #                 modules=self.mymodules,
        #                 provenance=True)
        #     self.outfilename = output_dir+self.filenames[0]

        p.run()

class BenchTIMBER(Bench):
    def __init__(self,tag,setname,year,filenames,cutstring=''):
        super(BenchTIMBER,self).__init__(tag,setname,year,filenames,cutstring='')

        jes = Calibration("JES","TIMBER/Framework/include/JES_weight.h",
                [GetJMETag("JES",str(year),"MC"),"AK8PFPuppi","","true"], corrtype="Calibration")
        jer = Calibration("JER","TIMBER/Framework/include/JER_weight.h",
                [GetJMETag("JER",str(year),"MC"),"AK8PFPuppi"], corrtype="Calibration")
        jms = Calibration("JMS","TIMBER/Framework/include/JMS_weight.h",
                [str(year)], corrtype="Calibration")
        jmr = Calibration("JMR","TIMBER/Framework/include/JMR_weight.h",
                [str(year)], corrtype="Calibration")
        
        self.a = analyzer(self.filenames)
        if cutstring != '':
            self.a.Cut("cutstring",cutstring)
        calibdict = {"FatJet_pt":[jes,jer],"FatJet_mass":[jes,jer,jms,jmr]}
        evalargs = {
            jes: {"jets":"FatJets","rho":"fixedGridRhoFastjetAll"},
            jer: {"jets":"FatJets","genJets":"GenJetAK8s"},
            jms: {"nJets":"nFatJet"},
            jmr: {"jets":"FatJets","genJets":"GenJetAK8s"}
        }
        self.a.CalibrateVars(calibdict,evalargs,"CalibratedFatJet")

        self.outfilename = 'benchmark_out/TIMBER_'+self.tag+'.root'
    
    def run_timber(self):
        self.a.Snapshot(['nCalibratedFatJet','CalibratedFatJet_.*','J.*_(nom|up|down)'],self.outfilename,"Events")
        print ('Finished snapshot')
        