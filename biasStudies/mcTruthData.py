#!/usr/bin/env python
# Simple script to make Effiency X Acceptance plot from Binned Baseline/Massfac analysis
# run with python makeEffAcc.py CMS-HGG.root
import ROOT as r
import sys
import re
import string
import random

r.gSystem.Load("Signal/lib/libSimultaneousSignalFit.so")
r.gSystem.Load("libHiggsAnalysisCombinedLimit")
r.gSystem.Load("libdiphotonsUtils")

r.gROOT.SetBatch(1)
infileName=sys.argv[1]
f = r.TFile(infileName)
outfile = r.TFile.Open(infileName.replace(".root","_mc_roohistpdf.root"),"RECREATE")

ws = f.Get("wtemplates")
#nBinsEBEE=(10010-230)
#nBinsEBEB=(10000-320)
nBinsEBEE=1000
nBinsEBEB=1000
binWidthEBEE=(10010-230)/nBinsEBEE
binWidthEBEB=(1000-320)/nBinsEBEB
nBins=nBinsEBEB
#ws.Print("V")
dataSets = ws.allData()
dsEBEE= []
dsEBEB= []
print "====================================="
print "available datasets"
print "====================================="
for data in dataSets:
  data.Print()
  if "mctruth_pp" not in data.GetName() : continue
  if "EBEE" in data.GetName() :
    dsEBEE.append(data)
  if "EBEB" in data.GetName() :
    dsEBEB.append(data)

#dataEBEB = ws.data("reduced_data_2D_EBEB")
#dataEBEE = ws.data("reduced_data_2D_EBEE")

print "====================================="
#targetN_EBEB =dataEBEB.sumEntries()
#targetN_EBEE =dataEBEE.sumEntries()
targetN_EBEB = 1470
targetN_EBEE = 801
print "====================================="
print "nEvents in EBEB = ",targetN_EBEB
print "nEvents in EBEE = ",targetN_EBEE
print "====================================="
print "selected datasets (EBEB):"
print dsEBEB
print "selected datasets (EBEE):"
print dsEBEE
print "====================================="

mggEBEB = r.RooRealVar("mggEBEB","mggEBEB",230,10010)
mggEBEE = r.RooRealVar("mggEBEE","mggEBEE",320,10000)
weight = r.RooRealVar("weight","weight",-100000,100000)
mass = ws.var("mass")
mass.setBins(nBinsEBEB)
mggEBEB.setBins(nBinsEBEB)
mggEBEE.setBins(nBinsEBEE)
frame = mass.frame()
#ds.plotOn(frame,r.RooFit.Binning(69))
colorList=[r.kBlack,r.kRed,r.kGreen,r.kBlue,r.kMagenta,r.kOrange,r.kGray,r.kViolet,r.kCyan,r.kYellow]

#counter= 0
#tl = r.TLegend(0.1,0.6,0.9,0.9)
#tl.SetNColumns(int(len(dsEBEB)/2))
#dummyhistos=[]
#binnedHistos=[]
#pdfHistos=[]
outws = r.RooWorkspace("roohistpdfs")

for data in dsEBEB+dsEBEE:
  massVar=None
  if "EBEB" in data.GetName():
    mass.setRange(230,10010)
    mass.setBins(nBinsEBEB)
    nBins=nBinsEBEB
    binWidth=binWidthEBEB
    massVar=mggEBEB
    targetN = targetN_EBEB
    minBin=0
    maxBin=1600
  if "EBEE" in data.GetName():
    mass.setRange(320,10000)
    mass.setBins(nBinsEBEE)
    binWidth=binWidthEBEE
    nBins=nBinsEBEE
    massVar=mggEBEE
    targetN = targetN_EBEE
  if massVar==None :
    print " why is massVAr == None ? something is wrong. exit"
    exit(1)
 
  #h=r.TH1F("dummy%d"%counter,"dummy%d"%counter,10,0,1)
  
  print "-----------------------------------"
  print "considering ",data.GetName()
  data.Print()
  print "-----------------------------------"
  #dbinned = r.RooDataHist(data.GetName()+"_binned",data.GetName()+"_binned",r.RooArgSet(mass))
  th1f0 = r.TH1F("th1f0","th1f0",nBins,mass.getMin(), mass.getMax())
  for i in range(0,data.numEntries()):
    data.get(i)
    mass.setVal(data.get(i).getRealValue("mass"))
    #dbinned.add(r.RooArgSet(mass),data.weight())
    th1f0.Fill(mass.getVal(),data.weight())
  print "-----------------------------------"
  epsilon = 100000 
  for i in range(0,th1f0.GetNbinsX()):
   if(th1f0.GetBinContent(i) < epsilon):
        th1f0.SetBinError(i, 0);
  dbinned = r.RooDataHist(data.GetName()+"_binned",data.GetName()+"_binned",r.RooArgList(mass),th1f0)
  for i in range(0,dbinned.numEntries()):
    nTH1F = th1f0.GetBinContent(i+1)
    dbinned.get(i)
    nRDH= dbinned.weight()
    if not (nTH1F-nRDH == 0) : print "compare bin ",i," nTH1F= ", nTH1F, ", nRDH=",nRDH, " difference = ", nTH1F-nRDH
    print "bin error for bin ", i ," " ,th1f0.GetBinError(i)
  print data.GetName() , " BINNED CLONE"
  #data.binnedClone().Print()
  dbinned.Print("V")
  print "TH1F " , th1f0.GetNbinsX() , " bins between ", th1f0.GetBinLowEdge(1), " and ", th1f0.GetBinLowEdge(dbinned.numEntries())+th1f0.GetBinWidth(0)
  print "-----------------------------------"
  #dbinned.plotOn(frame,r.RooFit.MarkerColor(colorList[counter]),r.RooFit.MarkerSize(1),r.RooFit.Binning(69))
  #binnedHistos.append(dbinned)
  frame = massVar.frame(r.RooFit.Range(0,4500))
  frame0 = mass.frame(r.RooFit.Range(0,4500))
  dbinnedNormalised = r.RooDataHist(dbinned.GetName(),dbinned.GetName(),r.RooArgSet(massVar))
  factor =targetN/dbinned.sumEntries() 
  th1f = r.TH1F("th1f","th1f",nBins,mass.getMin(), mass.getMax())
  for i in range(0,dbinned.numEntries()):
    massVar.setVal(dbinned.get(i).getRealValue("mass"))
    if (dbinned.weight()>0):
      w0 = dbinned.weight()*(factor)
    else: 
      w0 = 0.0001
    weight.setVal(w0*(factor))
    print "evt ", i, " weight  ", dbinned.weight(), " factor ", factor , " final weight=", weight.getVal()
    dbinnedNormalised.add(r.RooArgSet(massVar),weight.getVal())
    th1f.Fill(massVar.getVal(),weight.getVal())
  for i in range(0,th1f.GetNbinsX()):
   if(th1f.GetBinContent(i) < epsilon):
        th1f.SetBinError(i, 0);
   
   #float epsilon = 0.5; 
   #  for(int i = 1; i <= dbinnedNormalised.numEntries(); ++i)
   #      if(dbinnedNormalised->GetBinContent(i) < epsilon)
   #            dbinnedNormalised->SetBinError(i, 0);
  print "-----------------------------------"
  print "rewieghted clone"
  dbinnedNormalised.Print()
  print "-----------------------------------"
    
    
  rooHistPdf=r.RooHistPdf("pdf_%s"% dbinned.GetName(),"pdf_%s"% dbinned.GetTitle(),r.RooArgSet(massVar),dbinnedNormalised)
  print "-----------------------------------"
  print 'Roohist pdf version'
  #pdfHistos.append(rooHistPdf)
  rooHistPdf.Print()
  for i in range(0,10010):
    massVar.setVal(float(i))
    #getattr(rooHistPdf,'evaluate')()
    val = rooHistPdf.getVal()
    if (val>-1) : print " for mass ", massVar.getVal(), " pdf value is ", val
  #h.SetMarkerColor(colorList[counter])
  print "-----------------------------------"
  #h.SetMarkerStyle(20)
  #h.SetMarkerSize(1)
  #dummyhistos.append(h)
  #tl.AddEntry(h,data.GetName(),"p")
  c1 = r.TCanvas("c1","c1",300,300)
  print "plotting frame1"
  data.plotOn(frame0,r.RooFit.MarkerColor(colorList[0]),r.RooFit.MarkerSize(0.5),r.RooFit.Binning(nBins))
  #dbinned.plotOn(frame0,r.RooFit.MarkerColor(colorList[1]),r.RooFit.MarkerSize(0.5),r.RooFit.Binning(nBins))
  print "plotting frame1"

  #data.plotOn(frame,r.RooFit.MarkerSize(0.5),r.RooFit.DataError(r.RooAbsData.SumW2))
  #dbinnedNormalised.plotOn(frame,r.RooFit.MarkerColor(colorList[2]),r.RooFit.MarkerSize(0.5),r.RooFit.DataError(r.RooAbsData.SumW2))
  rooHistPdf.plotOn(frame,r.RooFit.LineColor(colorList[3]))
  c1.SetLogy()
  frame.Draw()
  #th1f.Draw("same *")
  c1.SaveAs("test_%s.pdf"%data.GetName())
  c1.SaveAs("test_%s.png"%data.GetName())
  c1.Clear()
  frame0.Draw()
  th1f0.Draw("same *")
  c1.SaveAs("test_0_%s.pdf"%data.GetName())
  c1.SaveAs("test_0_%s.png"%data.GetName())
  #outws.import(rooHistPdf)
  getattr(outws,'import')(rooHistPdf)
  getattr(outws,'import')(dbinnedNormalised)
  #counter =counter+1

#c1 = r.TCanvas("c1","c1",300,300)
#c1.SetLogy()
#frame.Draw()
#tl.Draw()
#c1.SaveAs("test.pdf")







outfile.cd()
outws.Write()
outfile.Close()


exit(1)

  
