#!/usr/bin/env python

import os
import numpy
import sys
import time

import fnmatch
from copy import deepcopy as copy
import re
import ROOT as r

r.gROOT.ProcessLine(".L $CMSSW_BASE/lib/$SCRAM_ARCH/libHiggsAnalysisCombinedLimit.so")
r.gROOT.ProcessLine(".L $CMSSW_BASE/lib/$SCRAM_ARCH/libdiphotonsUtils.so")
from optparse import OptionParser
from optparse import OptionGroup


from Queue import Queue
from threading import Thread, Semaphore
from multiprocessing import cpu_count

class Wrap:
    def __init__(self, func, args, queue):
        self.queue = queue
        self.func = func
        self.args = args
        
    def __call__(self):
        ret = self.func( *self.args )
        self.queue.put( ret  )

    
class Parallel:
    def __init__(self,ncpu):
        self.running = Queue(ncpu)
        self.returned = Queue()
        self.njobs = 0
  
    def run(self,cmd,args):
        wrap = Wrap( self, (cmd,args), self.returned )
        self.njobs += 1
        thread = Thread(None,wrap)
        thread.start()
        
    def __call__(self,cmd,args):
        if type(cmd) == str:
            print cmd
            for a in args:
                cmd += " %s " % a
            args = (cmd,)
            cmd = commands.getstatusoutput
        self.running.put((cmd,args))
        ret = cmd( *args ) 
        self.running.get()
        self.running.task_done()
        return ret

def getFilesFromDatacard(datacard):
    card = open(datacard,"r")
    files = set()
    for l in card.read().split("\n"):
        if l.startswith("shape"):
            toks = [t for t in l.split(" ") if t != "" ]
            files.add(toks[3])
    files = list(files)
    ret = files[0]
    for f in files[1:]:
        ret += ",%s" % f
    return ret

parser = OptionParser()
parser.add_option("-i","--infile",help="Signal Workspace")
parser.add_option("-d","--datfile",help="dat file")
parser.add_option("-s","--systdatfile",help="systematics dat file")
parser.add_option("--mhLow",default="120",help="mh Low")
parser.add_option("--mhHigh",default="130",help="mh High")
parser.add_option("--mh",default="750",help="mh")
parser.add_option("-k",default=None,help="with of signal")
parser.add_option("-q","--queue",help="Which batch queue")
parser.add_option("--runLocal",default=False,action="store_true",help="Run locally")
parser.add_option("--useMCBkgShape",default=False,action="store_true",help="Use MC rooHistPdf as bkg shape instead")
parser.add_option("--parametric",default=True,action="store_true",help="submit parameteric jobs")
parser.add_option("--batch",default="LSF",help="Which batch system to use (LSF,IC)")
parser.add_option("--changeIntLumi",default="1.")
parser.add_option("-o","--outfilename",default=None)
parser.add_option("-p","--outDir",default="./")
parser.add_option("--hadd",default=None)
parser.add_option("--grep",default=None)
parser.add_option("--deleteFailures",default=None)
parser.add_option("--resubmit",default=None)
parser.add_option("--makePlots",default=None)
parser.add_option("--pdfNameDict",default=None)
parser.add_option("--procs",default=None)
parser.add_option("-f","--flashggCats",default=None)
parser.add_option("--expected",type="int",default=None)
parser.add_option("--splitDatacard",default=None,help="Split thsi datacard by process")
parser.add_option("--justSplit",default=False,action="store_true",help="Split thsi datacard by process")
(opts,args) = parser.parse_args()

defaults = copy(opts)

print "INFO - queue ", opts.queue
def system(exec_line):
  #print "[INFO] defining exec_line"
  #if opts.verbose: print '\t', exec_line
  os.system(exec_line)

def writePreamble(sub_file,mu,cat,truthPdf,fitPdf,index):
  #print "[INFO] writing preamble"
  sub_file.write('#!/bin/bash\n')
  sub_file.write('touch %s.run\n'%os.path.abspath(sub_file.name))
  sub_file.write('cd %s\n'%os.getcwd())
  sub_file.write('eval `scramv1 runtime -sh`\n')
  #if (opts.batch == "IC" ) : sub_file.write('cd $TMPDIR\n')
  #sub_file.write('number=$RANDOM\n')
  #sub_file.write('mkdir -p scratch_$number\n')
  #sub_file.write('cd scratch_$number\n')
  sub_file.write('MU=%.2f \n'%mu)
  sub_file.write('MHhat=%d \n'%opts.mh)
  sub_file.write('NTOYS=500 \n')
  sub_file.write('PDF=%d \n'%truthPdf)
  sub_file.write('FITPDF=%d \n'%fitPdf)
  sub_file.write('EXTRAOPT="-L libdiphotonsUtils"\n')
  if (opts.batch == "IC"):
    sub_file.write('index=$SGE_TASK_ID\n')
  sub_file.write('TAG=%s \n'%cat)
  sub_file.write('JOBPATH=%s\n'%os.path.abspath(sub_file.name).split("sub")[0])
  #sub_file.write('PULLJOBPATH=%s\n'%os.path.abspath(sub_file.name).split("/sub")[0].replace("DeltaL","Pulls"))
  sub_file.write('cd $TMPDIR\n')
  sub_file.write('cp %s/biasStudyWS_k%s_m%d_%s.root biasStudyWS_%s.root \n'%(os.getcwd(),opts.k,int(opts.mh),cat,cat))
  sub_file.write('cp %s/biasStudyWS_k%s_m%d_%s_gen.root biasStudyWS_%s_gen.root \n'%(os.getcwd(),opts.k,int(opts.mh),cat,cat))
  name=None
  if (index=="Pulls"):
    name="biasStudyJobTemplatePulls.sh"
  else:
    name="biasStudyJobTemplate.sh"
  f= open(name)
  sub_file.write(f.read())
  f.close()

def writePostamble(sub_file):

  sub_file.write('rm -f %s.run\n'%os.path.abspath(sub_file.name))
  #sub_file.write('rm -rf scratch_$number\n')
  sub_file.close()
  system('chmod +x %s'%os.path.abspath(sub_file.name))
  if opts.queue:
    system('rm -f %s.done'%os.path.abspath(sub_file.name))
    system('rm -f %s.*fail'%os.path.abspath(sub_file.name))
    system('rm -f %s.log'%os.path.abspath(sub_file.name))
    system('rm -f %s.err'%os.path.abspath(sub_file.name))
    if (opts.batch == "LSF") : system('bsub -q %s -o %s.log %s'%(opts.queue,os.path.abspath(sub_file.name),os.path.abspath(sub_file.name)))
    if (opts.batch == "IC") : 
      if (opts.parametric):
        system('qsub -q %s -o %s.log -e %s.err -t 1-10:1 %s'%(opts.queue,os.path.abspath(sub_file.name),os.path.abspath(sub_file.name),os.path.abspath(sub_file.name)))
        print "system(",'qsub -q %s -o %s.log -e %s.err %s '%(opts.queue,os.path.abspath(sub_file.name),os.path.abspath(sub_file.name),os.path.abspath(sub_file.name)),")"
      else:
        system('qsub -q %s -o %s.log -e %s.err %s'%(opts.queue,os.path.abspath(sub_file.name),os.path.abspath(sub_file.name),os.path.abspath(sub_file.name)))
  if opts.runLocal:
     system('bash %s'%os.path.abspath(sub_file.name))


#######################################
def update_progress(progress):
  barLength = 20 # Modify this to change the length of the progress bar
  status = ""
  if isinstance(progress, int):
    progress = float(progress)
  if not isinstance(progress, float):
      progress = 0
      status = "error: progress var must be float\r\n"
  if progress < 0:
        progress = 0
        status = "Halt...\r\n"
  if progress >= 1:
        progress = 1
        status = "Done...\r\n"
  block = int(round(barLength*progress))
  text = "\rProgress: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), round(progress*100,2), status)
  sys.stdout.write(text)
  sys.stdout.flush()

def trawlHadd():
  print "[INFO] trawling hadd"
  list_of_dirs=set()
  for root, dirs, files in os.walk(opts.hadd):
    for x in files:
      if 'higgsCombine' in x and '.root' in x:
        if (opts.grep==None) or (opts.grep in "%s/%s"%(root,x)):
          list_of_dirs.add(root)
      if 'mlfit' in x and '.root' in x: 
        if (opts.grep==None) or (opts.grep in "%s/%s"%(root,x)):
          #print "add dit ", root
          list_of_dirs.add(root)
  #for i in range (0,len(list_of_dirs)):
  #  interval = (imax+10)/100
  #  #print "i, max, interval" , i, imax, interval 
  #  if (i%interval==0):# update the bar
  #    time.sleep(0.1)
  #    #sys.stdout.write("-")
  #    #sys.stdout.flush()
  #update_progress(1)
  #sys.stdout.write("\n") 
  
  counter =0.
  imax= len(list_of_dirs)
  for dir in list_of_dirs:
    for root, dirs, files in os.walk(dir):
      list_of_files_DeltaL=''
      list_of_files_Pulls=''
      for file in fnmatch.filter(files,'higgsCombine*.root'):
        list_of_files_DeltaL += ' '+os.path.join(root,'%s'%file)
      for file in fnmatch.filter(files,'ml*.root'):
        list_of_files_Pulls += ' '+os.path.join(root,'%s'%file)
      #print root, ' -- ', len(list_of_files_DeltaL.split())
      exec_line = 'hadd -f %s/%s.merged.root%s > /dev/null'%(dir,os.path.basename(dir),list_of_files_DeltaL)
      #print root, ' -- ', len(list_of_files_Pulls.split())
      exec_line = 'hadd -f %s/%s.merged.root%s > /dev/null'%(dir,os.path.basename(dir),list_of_files_Pulls)
      update_progress(float(counter)/float(imax))
      counter =counter+1
      #if opts.verbose: print exec_line
      system(exec_line)
  update_progress(1)

def trawlResubmit():
  print "[INFO] trawling hadd"
  list_of_files=[]
  for root, dirs, files in os.walk(opts.resubmit):
    for x in files:
      if '.sh.run' in x: 
        print "adding", root+"/"+x.split(".fail")[0] 
        list_of_files.append(root+"/"+x.split(".fail")[0])
  for f in list_of_files:
    #print f
    f = f.replace(".run","")
    index = f.split("sub")[1].split(".")[0]
    if (index==""): continue
    #print "index is ", int(index)
    f0 = f.replace("sub%d"%int(index),"sub")
    #print "so, opening ",f0
    job0 = open(f0,"r")
    job = open(f,"w") 
    for line in job0.readlines():
      if "$SGE_TASK_ID" in line:
        job.write(line.replace("$SGE_TASK_ID","%d"%int(index)))
      elif "NTOYS=750" in line:
        job.write(line.replace("NTOYS=750","NTOYS=500"))
      else :
        job.write(line)
    print "resubmitting", job
    opts.parametric=False
    writePostamble(job)

def deleteFailures():
  print "[INFO] trawling hadd"
  list_of_files=[]
  for root, dirs, files in os.walk(opts.deleteFailures):
    for x in files:
      if '.sh.fail' in x: 
        print "adding", root+"/"+x.split(".fail")[0] 
        list_of_files.append(root+"/"+x.split(".fail")[0])
  for f in list_of_files:
    os.system("rm %s.fail*"%f)
    dir=f.split("/sub")[0]
    jobid=f.split("sub")[1].split(".sh")[0]
    os.system("rm %s/*job_%s.*"%(dir,jobid))
    print "delete *",f.split("sub")[1].split(".sh")[0],"* from ",f.split("/sub")[0]

def getAveragePullNew(f,muTrue,pdfTrue,pdfFit,tag):
  
  tf = r.TFile.Open(f)
  #f= f.split("/")[-1]
  ttree = tf.Get("tree_fit_sb")
  r.gStyle.SetOptStat(0)
  #tagName = f.split("_13TeV")[0]
  #mu = float(f.split("mu_")[1].split("_")[0])
  #pdf = int(f.split("pdf_")[1].split(".merged")[0])
  #print pullList
  
  r.gROOT.SetBatch(1)
  print 'ttree = tf.Get("tree_fit_sb")'
  c = r.TCanvas("c","c",500,500)
  #ttree.Draw("(mu-%f)/muHiErr>>htemp(10,-4,4)"%muTrue)
  print 'ttree.Draw("(mu-%f)/muHiErr>>htemp"'%muTrue,')'
  #ttree.Draw("(mu-%f)/muErr>>htemp"%muTrue)
  ttree.Draw("(mu-%f)/muHiErr>>htemp"%muTrue,"mu>-20 ")
  c.SaveAs("test.pdf")
  #exit(1)
  #ttree.Draw("(mu)/muErr>>htemp(10,-4,4)")
  htemp = r.gROOT.FindObject("htemp")
  print htemp.GetEntries()
  print "fitting"
  #htemp.Fit("gaus","")
  htemp.Fit("gaus","q")
  print htemp
  fit = htemp.GetFunction("gaus")
  print fit
  pullLists={}
  if not (htemp.GetEntries()) : return pullLists
  pull = fit.GetParameter(1)
  #pull = htemp.GetMean()
  print pull
  print " DEBUGXXX] file ", f, " mean is ",pull
  if not pdfFit in pullLists.keys(): pullLists[pdfFit]=None
  pullLists[pdfFit]=pull
  tf.Close()
  wf=open("log.txt","a")
  wf.write("%s %.2f \n"%(f,pull))
  wf.close()

  #for pdf in pullLists.keys():
  #  print " final average pull for tag ",tag, " pdf ", pdf
  #  pullLists[pdf]= (sum(pullLists[pdf]) / float(len(pullLists[pdf])))
  return pullLists

def getAveragePull(f,muTrue,pdfTrue,pdfFit,tag):
  
  tf = r.TFile.Open(f)
  #f= f.split("/")[-1]
  limit = tf.Get("limit")
  r.gStyle.SetOptStat(0)
  #tagName = f.split("_13TeV")[0]
  #mu = float(f.split("mu_")[1].split("_")[0])
  #pdf = int(f.split("pdf_")[1].split(".merged")[0])
  muTrue=1
  muArray ={}
  pdfArray ={}
  for ev in range(limit.GetEntries()):
   limit.GetEntry(ev)
   #uniqueRef=float((getattr(limit,"t_cpu")))
   #print uniqueRef
   uniqueRef="%d_%f_%f"%((getattr(limit,"iToy")),1000*(getattr(limit,"t_real")),1000*(getattr(limit,"t_cpu")))
   #print uniqueRef
   mu= (getattr(limit,"r"))
   pdf= (getattr(limit,"pdfindex_%s"%tag))
   if uniqueRef not in muArray.keys():
    muArray[uniqueRef]=[] 
    pdfArray[uniqueRef]=[] 
    muArray.get(uniqueRef).append(mu)
    pdfArray.get(uniqueRef).append(pdf)
   else:
    muArray.get(uniqueRef).append(mu)
    pdfArray.get(uniqueRef).append(pdf)
  
  pullLists={}
  print "printing contents"
  counter=0
  for k in muArray.keys() :
    if (len(muArray[k])!=3)  : continue
    #print counter, k
    muList =sorted((muArray[k]))
    pdfList =sorted((pdfArray[k]))
    mu =muList[1]
    print "mu List" ,muList
    pdf =pdfList[1]
    errLo = abs(mu -muList[0])
    errHi = abs(mu -muList[2])
    pull=0
    print "mu = ", mu ," + ", errHi, " - ", errLo
    if (muTrue < mu) :
      if (abs(errHi)< 10e-4) : continue
      pull = (muTrue -mu)/errHi
      #pull = (muTrue -mu)
      print "muTrue -mu ", muTrue -mu , " errHi ", errHi , " pull " ,pull
      if not pdf in pullLists.keys(): pullLists[pdf]=[]
      pullLists[pdf].append(pull)
    else:
      #if (abs(errLo)  < 10e-4): continue
      pull = (muTrue -mu)/errHi
      #pull = (muTrue -mu)
      if not pdf in pullLists.keys(): pullLists[pdf]=[]
      pullLists[pdf].append(pull)
  #print pullList
  for pdf in pullLists.keys():
    print " final average pull for tag ",tag, " pdf ", pdf
    pullLists[pdf]= (sum(pullLists[pdf]) / float(len(pullLists[pdf])))
  return pullLists

def makePlotsDeltaL():
  list_of_files=[]
  r.gROOT.SetBatch(1)
  for root, dirs, files in os.walk(opts.makePlots):
    for x in files:
      if 'merged.root' in x and "Delta" in x: 
        print "adding", root+"/"+x.split(".fail")[0] 
        list_of_files.append(root+"/"+x.split(".fail")[0])
  for f in list_of_files:
    print f
    tf = r.TFile.Open(f)
    f= f.split("/")[-1]
    limit = tf.Get("limit")
    r.gStyle.SetOptStat(0)
    tagName = f.split("_13TeV")[0]
    mu = float(f.split("mu_")[1].split("_")[0])
    pdf = int(f.split("pdf_")[1].split("_")[0])
    limit.Draw("2*deltaNLL>>htemp(50,0,10)","quantileExpected>0 && quantileExpected<1")
    limit.Draw("2*deltaNLL>>htempRF(50,0,10)","quantileExpected>0 && quantileExpected<1 &&  pdfindex_%s==%d"%(tagName,pdf))
    limit.Draw("2*deltaNLL>>htempWF(50,0,10)","quantileExpected>0 && quantileExpected<1 &&  pdfindex_%s!=%d"%(tagName,pdf))
    htemp = r.gROOT.FindObject("htemp")
    htempRF = r.gROOT.FindObject("htempRF")
    htempWF = r.gROOT.FindObject("htempWF")
    htemp.SetLineColor(r.kBlue)
    htemp.SetFillColor(r.kBlue)
    htemp.SetFillStyle(3003)
    htempWF.SetLineColor(r.kRed)
    htempWF.SetFillColor(r.kRed)
    htempWF.SetFillStyle(3002)
    htempRF.SetLineColor(r.kGreen)
    htempRF.SetFillColor(r.kGreen)
    htempRF.SetFillStyle(3001)
    chi2shape= r.TF1("chi2shape","[0]*x^(-1/2)*TMath::Exp(-x/2)", 0, 10)
    chi2shapeRF= r.TF1("chi2shapeRF","[0]*x^(-1/2)*TMath::Exp(-x/2)", 0, 10)
    chi2shapeWF= r.TF1("chi2shapeWF","[0]*x^(-1/2)*TMath::Exp(-x/2)", 0, 10)
    chi2shapeDummy= r.TF1("chi2shapeDummy","[0]*x^(-1/2)*TMath::Exp(-x/2)", 0, 10)
    chi2shape.SetLineColor(r.kBlue-1)
    chi2shapeRF.SetLineColor(r.kGreen-1)
    chi2shapeWF.SetLineColor(r.kRed-1)
    htemp.Fit(chi2shape)
    htempRF.Fit(chi2shapeRF)
    htempWF.Fit(chi2shapeWF)
    tleg = r.TLegend(0.1,0.5,0.9,0.9)
    tleg.SetFillColor(r.kWhite)
    tleg.AddEntry(htemp,"All Toys","f")
    tleg.AddEntry(htempRF,"Truth PDF chosen","f")
    tleg.AddEntry(htempWF,"Other PDF chosen","f")
    tleg.AddEntry(chi2shapeDummy,"Normalised #chi^{2} (n d.o.f=1)  shapes","l")

    c1 = r.TCanvas("c1","c1",500,500)
    c1.SetLogy()
    htemp.Draw()
    htempWF.Draw("same")
    htempRF.Draw("same")
    chi2shape.Draw("same")
    chi2shapeRF.Draw("same")
    chi2shapeWF.Draw("same")
    tleg.Draw("same")

    tlat = r.TLatex()
    tlat.SetNDC()
    tlat.DrawLatex(0.13,0.85,"%s X(%d GeV)"%(tagName,opts.mh))
    tlat.DrawLatex(0.13,0.8,"XS_{truth} = %d"%mu)
    #tlat.DrawLatex(0.13,0.73,"PDF_{truth} = %d"%pdf)
    #print opts.pdfNameDict[tagName]
    tlat.DrawLatex(0.13,0.73,"PDF_{truth} = %s"%opts.pdfNameDict[tagName][pdf])
    c1.SaveAs("biasStudyPlot_%s_mu_%.2f_pdf_%s.pdf"%(tagName,mu,opts.pdfNameDict[tagName][pdf]))
    c1.SaveAs("biasStudyPlot_%s_mu_%.2f_pdf_%s.png"%(tagName,mu,opts.pdfNameDict[tagName][pdf]))

def makePlotsPulls():
  list_of_graphs={}
  wf=open("log.txt","w")
  wf.close()
  list_of_files=[]
  r.gROOT.SetBatch(1)
  for root, dirs, files in os.walk(opts.makePlots):
    for x in files:
      if 'merged.root' in x and "Pulls" in x: 
        if (opts.grep==None) or (opts.grep in "%s/%s"%(root,x)):
          print "adding", root+"/"+x.split(".fail")[0] 
          list_of_files.append(root+"/"+x.split(".fail")[0])
  for f in list_of_files:
    print f
    #tf = r.TFile.Open(f)
    fshort= f.split("/")[-1]
    #limit = tf.Get("limit")
    #r.gStyle.SetOptStat(0)
    tagName = fshort.split("_mu")[0].replace("_13TeV","")
    mu = float(fshort.split("mu_")[1].split("_")[0])
    mh = float(fshort.split("mh_")[1].split("_")[0])
    kval = (fshort.split("k_")[1].split("_")[0])
    truthPdf = int(fshort.split("truthPdf_")[1].split("_")[0])
    fitPdf = int(fshort.split("fitPdf_")[1].split("_")[0])
    label="%s_mX_%d_k_%s"%(tagName,mh,kval)
    #if tagName not in "UntaggedTag_2": continue
    #if mu!=1.: continue
    #print f,tagName,mu,pdf
    #pulls_by_fitted_pdf=getAveragePull(f,mu,,truthPdf,fitPdf,tagName)
    pulls_by_fitted_pdf = getAveragePullNew(f,mu,truthPdf,fitPdf,tagName)
    print pulls_by_fitted_pdf
    if not truthPdf in opts.pdfNameDict[tagName].keys(): continue 
    graphname= "%s_%s"%(label,opts.pdfNameDict[tagName][truthPdf])
    if "_750_" in graphname: graphname= graphname.replace("_750_","_0750_")
    if "_500_" in graphname: graphname= graphname.replace("_500_","_0500_")
    if not graphname in list_of_graphs: list_of_graphs[graphname]={}
    for fitPdf in pulls_by_fitted_pdf.keys():
      if not fitPdf in list_of_graphs[graphname]:list_of_graphs[graphname][fitPdf] =r.TGraphErrors()
      g =list_of_graphs[graphname][fitPdf]
      print "g.SetPoint( ",g.GetN(),mu, pulls_by_fitted_pdf[fitPdf],")"
      point = g.GetN()
      g.SetPoint(point ,mu, pulls_by_fitted_pdf[fitPdf])
      g.SetPointError( point, 1.25,0)
      print "setting point for graphname ", graphname , " fitPdf ", fitPdf , " mu ", mu, " pull ", pulls_by_fitted_pdf[fitPdf]

  print list_of_graphs
  colorList=[r.kBlack,r.kRed,r.kGreen,r.kBlue,r.kMagenta,r.kOrange,r.kGray,r.kViolet,r.kCyan,r.kYellow]
  
  mg_array={}
  tleg_array={}
  tlat_array={}
  mean_pulls_array={}
  print sorted(list_of_graphs.keys())
  for k in sorted(list_of_graphs.keys()):
    c1 = r.TCanvas("c1","c1",600,200)
    tag_graphs=list_of_graphs[k]
    mg = r.TMultiGraph()

    counter=0
    tleg = r.TLegend(0.1,0.7,0.9,0.9)
    tleg.SetNColumns(len(tag_graphs.keys()))
    tleg.SetHeader("Fit Function")
    tleg.SetFillColor(r.kWhite)
    for fitPdf in tag_graphs.keys():
      g =tag_graphs[fitPdf]
      g.SetMarkerColor(colorList[counter])
      g.SetMarkerSize(0.9)
      if not fitPdf in opts.pdfNameDict[k.split("_")[0]].keys(): continue 
      fitPdfString= opts.pdfNameDict[k.split("_")[0]][fitPdf]
      if (fitPdfString==k.rsplit("_",1)[1]):
        g.SetMarkerStyle(21)
      elif (fitPdf==-1):
        g.SetMarkerStyle(20)
      else:
        g.SetMarkerStyle(4)
      counter +=1
      mg.Add(g)
      mean = g.GetMean(2)
      print "LC DEBUG XXX mean of graph ",mean , " for ", k ," fitPdf ", opts.pdfNameDict[k.split("_")[0]][fitPdf]
      #if not "%_%"%(k,opts.pdfNameDict[k.split("_")[0]][fitPdf]) 
      tleg.AddEntry(g,opts.pdfNameDict[k.split("_")[0]][fitPdf],"p")
    mg.Draw("AP")
    mg.GetYaxis().SetRangeUser(-1.1,1.1)
    #mg.GetXaxis().SetLimits(-1.2,2.2)
    mg.GetXaxis().SetLimits(-7.51,17.6)
    #mg.GetXaxis().SetRangeUser(-1.2,2.2)
    mg.GetXaxis().SetRangeUser(-7.51,17.6)
    mg.GetXaxis().SetTitle("XS");
    mg.GetXaxis().SetTitleSize(0.055);
    mg.GetYaxis().SetTitle("<(XS - #hat{XS})/#sigma_{XS} > ");
    mg.GetYaxis().SetTitleSize(0.055);
    mg.Draw("AP")
    print " value of k = ", k
    print " value of k.rsplit(_)[0] = ", k.rsplit("_",1)[0]
    print " value of k = ", k
    mX = k.rsplit("_",1)[0].split("mX_")[1].split("_")[0] 
    label = k.rsplit("_",1)[0].replace("mX_%s"%mX,"")
    if not label  in mg_array.keys() : mg_array[label] = []
    if not label  in tleg_array.keys() : tleg_array[label] = []
    if not label  in tlat_array.keys() : tlat_array[label] = []
    tleg_array[label].append(tleg)
    tlat_array[label].append("m_{X} = %s"%mX) 
    #mg_array[k.rsplit("_",1)[0]].append(mg)
    mg_array[label].append(mg) 
    #line = r.TLine(-1.1,0,2.2,0)
    line = r.TLine(-7.5,0,17.5,0)
    line.SetLineStyle(r.kDashed)
    line.Draw()
    tleg.Draw()
    tlat = r.TLatex()
    tlat.SetNDC()
    tlat.SetTextSize(0.055)
    tlat.DrawLatex(0.15,0.9,'#bf{%s}'%k.rsplit("_",1)[0])
   # tlat.DrawLatex(0.15,0.79,"#bf{PDF_{truth} = %s}"%k.rsplit("_",1)[1])
    mg.SetTitle(k)
    #tlat.DrawLatex(0.13,0.73,"PDF_{truth} = %d"%pdf)
    #print opts.pdfNameDict[tagName]
    c1.SaveAs("pulls_test_%s.pdf"%k)
    c1.SaveAs("pulls_test_%s.png"%k)
  
  print mg_array
  for tag in mg_array.keys():
    r.gStyle.SetPadTopMargin(0.2)
    c2 = r.TCanvas("c2","c2",600, (len(mg_array[tag])+1)*200 )
    #c2.Divide(0,len(mg_array[tag]),0.01,0,r.kBlue)
    c2.Divide(0,len(mg_array[tag]),0.01,0.005)
    c2.cd(0)
    r.gPad.SetTopMargin(0.1)
    #c2.SetFrameBorderMode(0)
    #for mg_i in range(len(mg_array[tag])-1,-1,-1):
    for mg_i in range(0,len(mg_array[tag])):
      print mg_i
      c2.cd(mg_i+1)
      mg_array[tag][mg_i].Draw("AP")
      mg_array[tag][mg_i].GetYaxis().SetTitleOffset(0.35);
      mg_array[tag][mg_i].GetXaxis().SetTitleOffset(0.3);
      mg_array[tag][mg_i].GetYaxis().SetTitleSize(0.11);
      mg_array[tag][mg_i].GetYaxis().SetLabelSize(0.07);
      mg_array[tag][mg_i].GetXaxis().SetTitleSize(0.11);
      mg_array[tag][mg_i].GetXaxis().SetLabelSize(0.07);
      #line = r.TLine(-1.1,0,2.2,0)
      line = r.TLine(-7.5,0,17.5,0)
      line.SetLineStyle(r.kDashed)
      line.SetLineWidth(1)
      #line.Draw()
      #line.DrawLine(-1.1,0,2.2,0)
      line.DrawLine(-7.5,0,17.5,0)
      tlat = r.TLatex()
      tlat.SetNDC()
      tlat.SetTextSize(0.1)
      #tlat.DrawLatex(0.15,0.85,'#bf{%s}'%tag)
      #tlat.DrawLatex(0.15,0.79,"%s"%tlat_array[tag][mg_i])
      tlat.SetTextAngle(90)
      tlat.DrawLatex(0.94,0.1,"%s"%tlat_array[tag][mg_i])
      #tlat.Draw("")
      tleg_array[tag][mg_i].Draw("")
    c2.cd(1)
    tlat2= r.TLatex()
    tlat2.SetNDC()
    tlat2.SetTextSize(0.1)
    tlat2.DrawLatex(0.1,0.93,'#bf{%s}'%tag)
    #line = r.TLine(-1.1,0,2.2,0)
    #line.SetLineStyle(r.kDashed)
    #line.SetLineWidth(2)
    #line.Draw()
    #line.DrawLine(-1.1,0,2.2,0)
    c2.SaveAs("pulls_by_tag_%s.pdf"%tag)
    c2.SaveAs("pulls_by_tag_%s.png"%tag)
  


def getPdfNameDict(tags):
  pdfNameDict={} 
  f="multipdf_all_ho.root"
  tf = r.TFile.Open(f)
  #f= f.split("/")[-1]
  w = tf.Get("wtemplates")
  for tag in tags:
   mpdf= w.obj("model_bkg_%s"%tag)
   mpdf.Print()
   nPdfs = mpdf.getNumPdfs()
   #pdfNameDict[tag]=[]
   pdfNameDict[tag]={}
   for i in range (0,nPdfs):
     print "pdf ",i, " name " ,mpdf.getPdf(i).GetName()
     #pdfNameDict[tag].append(mpdf.getPdf(i).GetName().split("_")[-1])
     pdfNameDict[tag][i]=mpdf.getPdf(i).GetName().split("_")[-1]
   #pdfNameDict[tag].append(mpdf.getPdf(i).GetName().split("_")[-1])
   pdfNameDict[tag][-1]="envelope"
  return  pdfNameDict

def makeSplittedDatacards(datacard):
  path="./"
  if "/" in datacard:
    path = datacard.rsplit("/",1)[0]
    datacard = datacard.rsplit("/",1)[1] 

  print "path =" ,path
  print "datacard =" ,datacard
  system('cp %s/* .'%(path))

  f = open(datacard)
  allCats = set()
  for line in f.readlines():
   if line.startswith('bin'):
    for el in line.split()[1:]:
       allCats.add(el)
  f.close()
  print ' [INFO] -->Found these categories in card: ', allCats
  veto = ""
  for cat in allCats:
    veto="ch1_"+cat
    splitCardName = 'datacard%s.txt'%cat
    system('combineCards.py --ic="%s" %s > %s'%(veto,datacard,splitCardName))
    print ('combineCards.py --ic="%s" %s > %s'%(veto,datacard,splitCardName))
    card = open('%s'%(splitCardName),'r')
    newCard = open('tempcard.txt','w')
    newCard_gen = open('tempcard_gen.txt','w') # this one is for the case where toys are generated from a fixed RooHistPdf
    for line in card.readlines():
       if 'discrete' in line:
         if cat in line: 
          newCard.write(line.replace("750","%s"%opts.mh))
          # no need to add the "discrete" to the newCard_gen
       else: 
        newline =line.replace("750","%s"%opts.mh)
        newline_gen =line.replace("750","%s"%opts.mh)
        if opts.useMCBkgShape : 
          if "shapes" in line and "bkg" in line :
            newline_gen = newline.replace("multipdf_all_ho.root wtemplates:model_bkg_%s"%cat,"mctruth_7415v2_v5_mc_roohistpdf.root roohistpdfs:pdf_reduced_mctruth_pp_cic2_%s_binned"%cat)
          if "rate" in line :
            if cat=="EBEE" : newline_gen = "rate  1.000   569\n"
            if cat=="EBEB" : newline_gen = "rate  1.000   1218\n"
          if "shapes" in line and "data_obs" in line :
            newline_gen = newline.replace("multipdf_all_ho.root wtemplates:data_%s"%cat,"mctruth_7415v2_v5_mc_roohistpdf.root roohistpdfs:reduced_mctruth_pp_cic2_%s_binned"%cat)
            #newline = newline.replace("multipdf_all_ho.root wtemplates:data_%s"%cat,"mctruth_7415v2_v5_mc_roohistpdf.root roohistpdfs:reduced_mctruth_pp_cic2_%s_binned"%cat)
        newCard.write(newline)
        newCard_gen.write(newline_gen)
    card.close()
    newCard.close()
    newCard_gen.close()
    system('mv %s %s'%(newCard.name,card.name))
    system('mv %s %s'%(newCard_gen.name,card.name.replace(".txt","_gen.txt")))
    print "new datacard done ", card.name
    print "new datacard done ", card.name.replace(".txt","_gen.txt")
    print 'text2workspace.py %s  -o biasStudyWS_k%s_m%d_%s.root -L libdiphotonsUtils'%(card.name,opts.k, int(opts.mh), cat)
    system('text2workspace.py %s  -o biasStudyWS_k%s_m%d_%s.root -L libdiphotonsUtils'%(card.name,opts.k, int(opts.mh), cat))
    print 'text2workspace.py %s  -o biasStudyWS_k%s_m%d_%s_gen.root -L libdiphotonsUtils'%(card.name.replace(".txt","_gen.txt"),opts.k, int(opts.mh), cat)
    system('text2workspace.py %s  -o biasStudyWS_k%s_m%d_%s_gen.root -L libdiphotonsUtils'%(card.name.replace(".txt","_gen.txt"),opts.k, int(opts.mh), cat))
    print "new datacard done ", card.name, " aka  biasStudyWS_k%s_m%d_%s.root"%(opts.k, int(opts.mh),cat)
    print "new gen datacard done ", card.name.replace(".txt","_gen.txt"), " aka  biasStudyWS_k%s_m%d_%s_gen.root"%(opts.k, int(opts.mh),cat)


#muValues = [0.,1.,2.]
#muValues = [-1.0,-0.75,-0.5,-0.25,0.,0.25,0.5,0.75,1.,1.25,1.5,1.75,2.]
#muValues = [-1.0,-0.5,0.,0.5,1.,1.5,2.]
#muValues = [-1.0,0.0,1.0,2.]
#muValues = [-0.75,-0.5,-0.25,0.25,0.5,0.75,1.25,1.5,1.75]
#muValues = [-1.0,-0.5,-0.25,0.0,0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0]
#muValues = [0.25,0.5,0.75,1.0,1.25,1.5,1.75,2]
muValues = [-5,0,5,10,15]
#muValues = [-5,-2.5,0,2.5,5,7.5,10,12.5,15]
#muValues = [-5,-2.5,0,2.5,5,7.5,10,12.5,15]
#muValues = [5]
#muValues = [2]
#muValues = [0.25,0.5,1.0,1.5,2]
#muValues = [-]
#catValues = ["UntaggedTag_0","UntaggedTag_1","UntaggedTag_2","UntaggedTag_3","VBFTag_0","VBFTag_1","TTHLeptonicTag","TTHHadronicTag"]
catValues = ["EBEB","EBEE"]


if opts.splitDatacard:
  makeSplittedDatacards(opts.splitDatacard)
  exit(1)

if (opts.k and opts.mh):
  opts.splitDatacard="datacards/k%s/datacard_full_analysis_spring15_7415v2_sync_v5_cic2_default_shapes_grav_%s_750.txt"%(opts.k,opts.k)
  makeSplittedDatacards(opts.splitDatacard)
  if (opts.justSplit) : exit(1)


opts.pdfNameDict = getPdfNameDict(catValues)

if opts.hadd:
  trawlHadd()
  exit(1)

if opts.resubmit:
  trawlResubmit()
  exit(1)

if opts.makePlots:
  #makePlotsDeltaL()
  makePlotsPulls()
  exit(1)

if opts.deleteFailures:
  deleteFailures()
  exit(1)

opts.mh = int(opts.mh)

system('mkdir -p biasStudyJobs')
for mu in muValues:
  for cat in catValues:
    pdfValues=opts.pdfNameDict[cat].keys()
    #pdfValues=[-1,4]
    for truthPdf in [-1]:
    #for truthPdf in [4]:
      for fitPdf in pdfValues:
        counter=0
        system('mkdir -p biasStudyJobs/%s_mu_%.2f_mh_%d_k_%s_truthPdf_%d_fitPdf_%d_Pulls'%(cat,mu,opts.mh,opts.k,truthPdf,fitPdf))
        #system('rm biasStudyJobs/%s_mu_%d_pdf_%d/sub*'%(cat,mu,pdf))
        if (opts.batch == "IC"):
           #submit paramtetric 
           file = open('%s/biasStudyJobs/%s_mu_%.2f_mh_%d_k_%s_truthPdf_%d_fitPdf_%d_Pulls/sub.sh'%(opts.outDir,cat,mu,opts.mh,opts.k,truthPdf,fitPdf),'w')
           print " making", ('%s/biasStudyJobs/%s_mu_%.2f_mh_%d_k_%s_truthPdf_%d_fitPdf_%d_Pulls/sub.sh'%(opts.outDir,cat,mu,opts.mh,opts.k,truthPdf,fitPdf),'w')
           writePreamble(file,mu,cat,truthPdf,fitPdf,"Pulls")
           writePostamble(file)
'''
for mu in muValues:
  for cat in catValues:
    for pdf in pdfValues:
        counter=0
        system('mkdir -p biasStudyJobs/%s_mu_%.2f_mh_%d_pdf_%d_DeltaL'%(cat,mu,opts.mh,pdf))
        #system('mkdir -p biasStudyJobs/%s_mu_%.2f_mh_%d_pdf_%d_Pulls'%(cat,mu,opts.mh,pdf))
        #system('rm biasStudyJobs/%s_mu_%.2f_pdf_%d/sub*'%(cat,mu,pdf))
        if (opts.batch == "IC"):
           #submit paramtetric 
           file = open('%s/biasStudyJobs/%s_mu_%.2f_mh_%d_pdf_%d_DeltaL/sub.sh'%(opts.outDir,cat,mu,opts.mh,pdf),'w')
           print "making file  biasStudyJobs/%s_mu_%.2f_mh_%d_pdf_%d_DeltaL/sub.sh"%(cat,mu,opts.mh,pdf)
           writePreamble(file,mu,cat,pdf,-999,"DeltaL")
           writePostamble(file)
        else :
          for counter in range(0,20):
           file = open('%s/biasStudyJobs/%s_mu_%.2f_mh_%d_pdf_%d_DeltaL/sub%d.sh'%(opts.outDir,cat,mu,opts.mh,pdf,counter),'w')
           print "making file  biasStudyJobs/%s_mu_%.2f_mh_%d_pdf_%d_DeltaL/sub%d.sh"%(cat,mu,opts.mh,pdf,counter)
           writePreamble(file,mu,cat,pdf,-999,"DeltaL")
           #print exec_line
           writePostamble(file)
           counter =  counter+1
'''
  
  
  

