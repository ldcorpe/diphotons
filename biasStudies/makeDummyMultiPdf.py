#!/usr/bin/env python
# Simple script to make Effiency X Acceptance plot from Binned Baseline/Massfac analysis
# run with python makeEffAcc.py CMS-HGG.root
import ROOT as r
import sys
import re
import string
import random

def getPhenoFunction(prefix,order, massvar,ws):
    params ={}
    if (order==0):
      #print "[WARNING] -- Pheno function must be at least order one" 
      return NULL
    
    dependents = r.RooArgList()
    dependents.add(massvar)

    sqrtS = 13000.
    var = "(@0/%f)"%sqrtS
    formula = ""
    for i in range(order):
      if (i > 0): formula += "+"
      formula += "@%d*TMath::Power(%s,@%d*TMath::Power(1-%s,@%d))"%(1+i*3,var,2+i*3,var,3+i*3)
      name1 =  ("%s_%d"%(prefix,1+i*3))
      name2 =  ("%s_%d"%(prefix,2+i*3))
      name3 =  ("%s_%d"%(prefix,3+i*3))

      params[name1] = r.RooRealVar(name1,name1,0.01,-0.1,0.1)
      params[name2] = r.RooRealVar(name2,name2,-3,-10,10)
      params[name3] = r.RooRealVar(name3,name3,7,-10,10)

      dependents.add(params[name1])
      dependents.add(params[name2])
      dependents.add(params[name3])
    
   # print "Pheno formula: ", formula 
    dependents.Print()
    pheno = r.RooGenericPdf(prefix,prefix,formula,dependents)
    getattr(ws,'import')(r.RooArgSet(pheno))
    getattr(ws,'import')(r.RooArgSet(dependents))
    print "THIS IS PHENO:"
    pheno.Print()
    print " THIS IS DENPENDENTS"
    dependents.Print()
    
    return dependents
  



r.gSystem.Load("Signal/lib/libSimultaneousSignalFit.so")
r.gSystem.Load("libHiggsAnalysisCombinedLimit")
r.gSystem.Load("libdiphotonsUtils")

r.gROOT.SetBatch(1)
infileName=sys.argv[1]
f = r.TFile(infileName)
outfile = r.TFile.Open("multipdf_all_ho_10.0.root","RECREATE")

ws = f.Get("wtemplates")
ws.Print()
#outws = ws.Clone()
#outws = r.RooWorkspace("wtemplates")
tags=["EBEB","EBEE"]
#for tag in tags:
#  mpdf= ws.obj("model_bkg_%s"%tag)
#  #print "MPDF (regular) for tag (start)", tag
#  #mpdf.Print()
#  catIndex= r.RooCategory("pdfindex_%s"%tag,"c")
#  #catIndex2= r.RooCategory("pdfindex_%s_LC"%tag,"c")
#  #catIndex= ws.obj("pdfindex_%s"%tag)
#  massVar = ws.obj("mgg%s"%tag)
#  savedPdfs = r.RooArgList()
#  for pdfIndex in range(mpdf.getNumPdfs()):
#     savedPdfs.add(mpdf.getPdf(pdfIndex))
#  #dependents  = getPhenoFunction("env_pdf_%d_13TeV_pheno1"%(tags.index(tag)),1,massVar,ws)
#  ###########GET PHENO FUNCYION #############
#  order=1
#  prefix="env_pdf_%d_13TeV_pheno1"%(tags.index(tag))
#  params ={}
#  #if (order==0):
#     #print "[WARNING] -- Pheno function must be at least order one" 
#     #return NULL
#    
#  dependents = r.RooArgList()
#  dependents.add(massVar)
#
#  sqrtS = 13000.
#  var = "(@0/%f)"%sqrtS
#  formula = ""
#  for i in range(order):
#      if (i > 0): formula += "+"
#      formula += "@%d*TMath::Power(%s,@%d*TMath::Power(1-%s,@%d))"%(1+i*3,var,2+i*3,var,3+i*3)
#      name1 =  ("%s_%d"%(prefix,1+i*3))
#      name2 =  ("%s_%d"%(prefix,2+i*3))
#      name3 =  ("%s_%d"%(prefix,3+i*3))
#
#      params[name1] = r.RooRealVar(name1,name1,0.01,-0.1,0.1)
#      params[name2] = r.RooRealVar(name2,name2,-3,-10,10)
#      params[name3] = r.RooRealVar(name3,name3,7,-10,10)
#
#      dependents.add(params[name1])
#      dependents.add(params[name2])
#      dependents.add(params[name3])
#    
#   # print "Pheno formula: ", formula 
#  dependents.Print()
#  pheno = r.RooGenericPdf(prefix,prefix,formula,dependents)
#  #getattr(ws,'import')(r.RooArgSet(pheno))
#  #getattr(ws,'import')(r.RooArgSet(dependents))
#  #print "THIS IS PHENO:"
#  #pheno.Print()
#  #print " THIS IS DENPENDENTS"
#  #dependents.Print()
#  #print " DEBUG allvars "
#  #ws.allVars().Print()
#  #print " DEBUG pheno:", dependents
#  #dependents.Print()
#  #pheno.Print()
#  #exit(1)
#  print "MPDF before"
#  mpdf.Print()
#  #getattr(ws,'import')(r.RooArgSet(pheno))
#  #mpdf.addExtraPdfs(catIndex, r.RooArgList(pheno))
#  print "MPDF after"
#  mpdf.Print()
#  #ws.im
#  #getattr(ws,'import')(pheno)
#  #savedPdfs.add(pheno)
#  #print "DEBUG 1 mpdf ", mpdf, " catIndex ", catIndex, " massvar ", massVar, " savedPdfs ", savedPdfs, " pheno ", pheno
#  print "MPDFnew b4"
#  #mpdfnew.Print()
#  savedPdfs.add(pheno)
#  mpdfnew = r.RooMultiPdf("model_bkg_%s_LC"%tag,"all pdfs",catIndex,r.RooArgList(savedPdfs))
#  getattr(ws,'import')(r.RooArgSet(mpdfnew))
#  print "MPDFnew after"
#  mpdfnew.Print()
#  #mpdfnew = r.RooMultiPdf("model_bkg_%s"%tag,"all pdfs",catIndex,savedPdfs)
#  #print "DEBUG 2"
#  #mpdfpheno= wspheno.obj("env_pdf_%d_13TeV_pheno1"%tags.index("%s"%tag))
#  #print "MPDF (regular) for tag (end) ", tag
#  #mpdf.Print()
#  #print "MPDFpheno for tag ", tag
#  #mpdfnew.Print()
#  #getattr(outws,'import')(mpdfnew)
#  #mpdf2=
#
##exit(1)
##print "AFTER IMPORT"
##tag ="EBEE"
##outws.obj("model_bkg_%s"%tag).Print()
##outws.obj("model_bkg_%s_"%tag).Print()
##outws.Print()
##exit(1)
#
model_bkg_EBEB_norm = ws.var("model_bkg_EBEB_norm")
model_bkg_EBEE_norm = ws.var("model_bkg_EBEE_norm")

#model_bkg_EBEB_norm.Print()
#model_bkg_EBEE_norm.Print()
model_bkg_EBEB_norm.setVal(4506.6)
model_bkg_EBEE_norm.setVal(2094.2)
#print "================================"
model_bkg_EBEB_norm.Print()
model_bkg_EBEE_norm.Print()
#outws = ws.Clone()
outfile.cd()
ws.Write()
outfile.Close()


exit(1)

