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
GetBR = lambda x : norm.GetBR(float(x))
GetXsection = lambda x : norm.GetXsection(float(x))
GetProcXsection = lambda x,y : norm.GetXsection(x,y)

r.gROOT.SetBatch(1)
infileName=sys.argv[1]
f = r.TFile(infileName)
#outfile = r.TFile.Open(infileName.replace(".root","_reduced.root"),"RECREATE") 
#ws = f.Get("multipdf")
ws = f.Get("wtemplates")
ws.Print()
exit(1)
#outws = r.RooWorkspace("multipdf_reduced");
#data = ws.data("roohist_data_mass_UntaggedTag_2")
#dataReduced = data.emptyClone(data.GetName()+"_reduced",data.GetName()+"_reduced")
#random = r.TRandom3()
#random.Rndm()
#rArray=[]
#random.RndmArray(data.numEntries(),rArray)
#for i in range(0,data.numEntries()):
#  print "bin ", i, " data.get(i) " , data.get(i) , " data.weight() ", data.weight() 
#  dataReduced.add(data.get(i),int(data.weight()*0.1))
#  #if rArray[i] > 0.1:
#    #dataReduced.add(data.get(i),data.weight())
#print "Original Dataset"
#data.Print()
#print "Reduced  Dataset"
#dataReduced.Print()
##outws.r.RooWorkspace.import(dataReduced)
#getattr(outws,'import')(dataReduced)
#outfile.cd()
#outws.Write()
#outfile.Close()
#exit(1)
#print " NOW MULTIDIMFIT WS"
#ws.getSnapshot("MultiDimFit").Print("V")
#print " NOW CLEAN WS"

ws.Print("V")
#ws.obj("shapeBkg_bkg_ch1_EBEB").Print("V")
#print " current pdf index "

#print ws.obj("shapeBkg_bkg_ch1_EBEB").getCurrentIndex()
#print " NOW NORMAL WS"

#ws.Print("V")

exit(1)




# Global Setup, Modify with each Reload
systematics = ["TriggerWeight","MvaShift","MCScaleLowR9EB","MCScaleHighR9EB","MCScaleLowR9EE","MCScaleHighR9EE","MCSmearLowR9EBRho","MCSmearHighR9EBRho","MCSmearLowR9EERho","MCSmearHighR9EERho","MCSmearLowR9EBPhi","MCSmearHighR9EBPhi","MCSmearLowR9EEPhi","MCSmearHighR9EEPhi","FracRVWeight"] # These are the main contributions to eff*Acc
Masses = range(120,135,5) 
# -------------------------------------------------------------

procs=["ggh","vbf","wh","zh","tth"]
masses=[120.,125.,130.]
cats=["UntaggedTag_0","UntaggedTag_1","UntaggedTag_2","UntaggedTag_3","VBFTag_0","VBFTag_1","TTHLeptonicTag","TTHHadronicTag"]
sqrts = 13
extraFile=sys.argv[2]
lRRV = ws.var("IntLumi")
lumi = lRRV.getVal()
norm.Init(int(sqrts))


# Some helpful output
print "File - ", sys.argv[1]
print 'Processes found:  ' + str(procs)
print 'Masses found:     ' + str(masses)
print 'Categories found: ' + str(cats)


efficiency=r.TGraphAsymmErrors()
efficiencyPAS=r.TGraphAsymmErrors()
efficiencyE0=r.TGraphErrors()
#efficiencyTH1=r.TH1F("t","t",10,120,130)
central=r.TGraphAsymmErrors()
efficiencyup=r.TGraphAsymmErrors()
efficiencydn=r.TGraphAsymmErrors()
centralsmooth=r.TGraphAsymmErrors()

fitstring = "[0] + [1]*x + [2]*x*x"
cenfunc = r.TF1("cenfunc",fitstring,109.75,140.25)
upfunc = r.TF1("upfunc",fitstring,109.75,140.25)
dnfunc = r.TF1("dnfunc",fitstring,109.75,140.25)



for point,M in enumerate(Masses):
  printLine = "Signal M%3.1f: "%M
  Sum = 0
  dataVector= []
  for i in cats:
    if int(M)==M:
      suffix = '_%d_13TeV_%s'%(int(M),i)
      histos = getSigHistos(ws, procs, suffix)

      #integrals = { proc : h.Integral() for (proc, h) in histos.iteritems()}
      integrals = { proc : h.sumEntries() for (proc, h) in histos.iteritems()}
      print "integralsf for M ",M ," ", integrals

      procLine = 'cat %s, mH=%3.1f:'%(i, M)
      for proc in procs:
        integral = integrals[proc]
        procLine += '   %s %.5f'% (proc, integral )

      hs = [ h for (proc, h) in histos.iteritems() ]
      for (proc,h) in histos.iteritems():
        dataVector.append(h)
      h=hs[0].emptyClone("dummy dataset"+str(id_generator()))
      
      for j in hs:
        h.Print()
        h.append(j)
        h.Print()
    
    Sum += h.sumEntries()
    printLine+="%3.5f "%h.sumEntries()
  printLine+="tot=%3.5f"%Sum
  
  xsecs = [ GetProcXsection(M,proc)*adHocFactors[proc] for proc in procs ]
  sm = GetBR(M) * sum(xsecs)
  
  effAcc = 100*Sum/(sm*lumi) # calculate Efficiency at mH
  centralsmooth.SetPoint(point,M,effAcc)
  central.SetPoint(point,M,effAcc)
  efficiency.SetPoint(point,M,effAcc)
  efficiencyE0.SetPoint(point,M,effAcc)
  #efficiencyTH1.Fill(M,effAcc)
  sigmaUp = 0
  sigmaDown = 0
  sigmaNom = 0
  for s in systematics:
    syssumup=0
    syssumnom=0
    syssumdn=0
    for cat in cats:
      for proc in procs:
         if int(M)==M:
          [hup,hnom,hdn]=getSystHisto(proc,cat,s,M,ws)
          #print
          #print "syst " , s , " cat ", cat ,", proc ", proc, "hup.sumEntries() ", hup.sumEntries()
          #hup.Print()
          #print "syst " , s , " cat ", cat ,", proc ", proc, "hnom.sumEntries() ", hnom.sumEntries() 
          #hnom.Print()
          #print "syst " , s , " cat ", cat ,", proc ", proc, "hdn.sumEntries() ", hdn.sumEntries()      
          #hdn.Print()
          #print
          syssumup+=hup.sumEntries()
          syssumnom+=hnom.sumEntries()
          syssumdn+=hdn.sumEntries()


    # We make 3-sigma templates so need to scale back by 1/3
    #print "total event yield for systematic ", s ," UP at mh=",M," is " ,syssumup
    #print "total event yield for systematic ", s ," NOM at mh=",M," is " ,syssumnom
    #print "total event yield for systematic ", s ," DN at mh=",M," is " ,syssumdn
    #delUp+=abs(syssumup-Sum)
    #delDown+=abs(syssumdn-Sum)
    xplus= max(syssumup,syssumdn,syssumnom) -syssumnom
    xminus= min(syssumup,syssumdn,syssumnom) -syssumnom
    sigmaUp += xplus*xplus
    sigmaDown += xminus*xminus
    #print "total event yield for systematic ", s ," xUp ", xplus, "xDown", xminus, " sigmaUp ", sigmaUp**0.5 , " sigmaDown ", sigmaDown**0.5
  


  sigmaUp=100*(sigmaUp**0.5)/(sm*lumi)
  sigmaDown=100*(sigmaDown**0.5)/(sm*lumi)
  efficiencyup.SetPoint(point,M,sigmaUp)
  efficiencydn.SetPoint(point,M,sigmaDown)
  centralsmooth.SetPointError(point,0,0,0,0)
  
  print "Setting error of pt ", point , " to [",sigmaDown,",",sigmaUp,"]"
  efficiency.SetPointError(point,0,0,sigmaDown,sigmaUp)
  efficiencyPAS.SetPointError(point,0,0,sigmaDown,sigmaUp)
  #efficiency.SetPointError(point,0,0,sigma_ea,sigma_ea)

  print printLine

#centralsmooth.Fit(cenfunc,"R,0,EX0","")
#efficiencyup.Fit(upfunc,"R,0,EX0","")
#efficiencydn.Fit(dnfunc,"R,0,EX0","")

#for point,M in enumerate(Masses):
#  central.SetPoint(point,M,cenfunc.Eval(M))
#  efficiency.SetPoint(point,M,cenfunc.Eval(M))

leg=r.TLegend(0.40,0.16,0.89,0.42)
leg.SetFillColor(0)
leg.SetBorderSize(0)
#leg.AddEntry(central,"Higgs Signal #varepsilon #times Acc","L")
#leg.AddEntry(efficiency,"#pm 1 #sigma syst. error","F")
#leg.AddEntry(efficiencyPAS,"#pm 1 #sigma syst. error","F")

mytext = r.TLatex()
mytext.SetTextSize(0.05)
mytext.SetNDC()

listy = []

MG=r.TMultiGraph()
can =None
can = r.TCanvas("c","c",600,600)
can.SetTicks(1,1)
if ("root" in extraFile):
  print "got graph!"
  _file0 = r.TFile(extraFile)
  graph=r.TGraph(_file0.Get("effAccGraph"))
  graph.SetLineColor(r.kBlack)
if (graph!=None): 
  print "drawing graph"
  point =0
  for i in range (0,graph.GetN()): 
    graph.GetY()[i] *= 100
    if (graph.GetX()[i] == 120) or (graph.GetX()[i] ==125) or (graph.GetX()[i]==130):
      efficiencyPAS.SetPoint(point,graph.GetX()[i],graph.GetY()[i])
      point =point+1
  #graph.Draw("same")
else :
  print "not drawing graph"
efficiency.SetFillColor(r.kOrange)
efficiencyPAS.SetFillColor(r.kOrange)
efficiency.SetLineWidth(2)
efficiencyPAS.SetLineWidth(2)
central.SetLineWidth(2)
#central.SetMarkerSize(2)
central.SetMarkerColor(r.kBlack)
central.SetMarkerStyle(22)
#MG.Add(efficiency)
MG.Add(efficiencyPAS)
#MG.Add(central)
MG.Add(graph)
leg.AddEntry(graph,"Signal model #varepsilon #times #alpha","l")
leg.AddEntry(efficiencyPAS,"#pm 1 #sigma syst. error","F")
MG.Draw("APL3")
MG.GetXaxis().SetTitle("m_{H} (GeV)")
MG.GetXaxis().SetTitleSize(0.055)
MG.GetXaxis().SetTitleOffset(0.7)
MG.GetXaxis().SetRangeUser(120.1,129.9)
#MG.GetXaxis().SetRangeUser(120.0,130)
MG.GetYaxis().SetTitle("Efficiency #times Acceptance (%)")
MG.GetYaxis().SetRangeUser(37.1,42.9)
MG.GetYaxis().SetTitleSize(0.055)
MG.GetYaxis().SetTitleOffset(0.7)
mytext.DrawLatex(0.1,0.92,"#scale[1.15]{CMS} #bf{#it{Simulation Preliminary}}") #for some reason the bf is reversed??
mytext.DrawLatex(0.75,0.92,"#bf{13#scale[1.1]{ }TeV}")
mytext.DrawLatex(0.129+0.03,0.82,"#bf{H#rightarrow#gamma#gamma}")
can.Update()
can.RedrawAxis()
leg.Draw("same")
print "Int Lumi from workspace ", lumi
#raw_input("Looks OK?")

can.Update()
print "Saving plot as effAcc_vs_mass.pdf"
can.SaveAs("effAcc_vs_mass.C")
can.SaveAs("effAcc_vs_mass.pdf")
can.SaveAs("effAcc_vs_mass.png")
can.SaveAs("effAcc_vs_mass.root")

 
#(r.TVirtualFitter.GetFitter()).GetConfidenceIntervals(efficiencyE0)

#can2 = r.TCanvas()
#efficiencyE0.Draw("E0")
#can2.SaveAs("effAcc_vs_mass_E0.pdf")
  
