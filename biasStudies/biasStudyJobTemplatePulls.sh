MYLOG=$JOBPATH/mylog.$index.log
if (( $PDF>-1)); then
FREZZEPDF="--freezeNuisances pdfindex_${TAG},r"
SETPARAMS="--setPhysicsModelParameters pdfindex_${TAG}=${PDF},r=${MU} --expectSignal=${MU} "
else
FREZZEPDF="--freezeNuisances r"
SETPARAMS="--setPhysicsModelParameters r=${MU}  --expectSignal=${MU}"
fi

if (( $FITPDF>-1)); then
FREZZEFITPDF="--freezeNuisances pdfindex_${TAG}"
SETFITPDF="--setPhysicsModelParameters pdfindex_${TAG}=${FITPDF} "
fi

#echo
#echo "STEP 1 check for higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root"
#echo
#if [[ -e higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root ]] ; then
#echo " this file already exists":
#ls higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root
#else 
#echo "if ( combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} $FREZZEPDF $SETPARAMS -n  biasStudy1_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} --saveWorkspace --algo fixed >$MYLOG ) then"
#if ( combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} $FREZZEPDF $SETPARAMS -n  biasStudy1_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} --saveWorkspace -S0 --algo fixed $EXTRAOPT >$MYLOG ) then
#touch $JOBPATH/sub${index}.sh.run
#else 
#touch $JOBPATH/sub${index}.sh.fail.failed_to_make_fit_file
#exit 1
#fi
#fi

#echo
#echo "STEP 2"
#echo

#higgsCombinebiasStudy1_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.MultiDimFit.mH${MHhat}_${index}.root
#if [[ -e higgsCombinebiasStudy1_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.MultiDimFit.mH${MHhat}.root ]] ; then
#echo "fit file exists"
#else
#touch  $JOBPATH/sub${index}.sh.fail.no_fit_file
#exit 1
#fi

#echo " if ( combine higgsCombinebiasStudy1_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}.MultiDimFit.mH${MHhat}.root --snapshotName MultiDimFit -M GenerateOnly -m ${MHhat} --saveWorkspace --toysFrequentist --bypassFrequentistFit -t ${NTOYS}  $FREZZEPDF $SETPARAMS   -n biasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -s ${index} --saveToys >$MYLOG ) then"
#if ( combine higgsCombinebiasStudy1_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.MultiDimFit.mH${MHhat}.root --snapshotName MultiDimFit -M GenerateOnly -m ${MHhat} --saveWorkspace --toysFrequentist --bypassFrequentistFit -t ${NTOYS} $FREZZEPDF $SETPARAMS   -n biasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -s ${index} --saveToys  --setPhysicsModelParameterRanges r=-5,10 -S0 >$MYLOG ) then
### ##########################
if (( $PDF>-2)); then
# the below to be usd if you want to use the candidate pdfs as truth pdfs when doing this study
echo "if ( combine biasStudyWS_$TAG.root  --snapshotName MultiDimFit -M GenerateOnly -m ${MHhat} --saveWorkspace --toysFrequentist  -t ${NTOYS} --freezeNuisances pdfindex_${TAG},r  --setPhysicsModelParameters pdfindex_${TAG}=${PDF},r=${MU} -n biasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -s ${index} --saveToys  --setPhysicsModelParameterRanges r=-60,60  ) "then #$FREZZEPDF $SETPARAMS 
if ( combine biasStudyWS_$TAG.root  -M GenerateOnly -m ${MHhat} --saveWorkspace --toysFrequentist  -t ${NTOYS} -n biasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -s ${index} --saveToys  --setPhysicsModelParameterRanges r=-60,60 -S0 $EXTRAOPT $FREZZEPDF $SETPARAMS ) then   
touch $JOBPATH/sub${index}.sh.run
else 
touch  $JOBPATH/sub${index}.sh.fail.2
exit 1
fi
###############################
#the below to be used if you want some MC RooHistPdf to throw toys from instead of fittign candidate functiosn etc...

else

if ( combine biasStudyWS_${TAG}_gen.root  -M GenerateOnly -m ${MHhat} --saveWorkspace  -t ${NTOYS} -n biasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -s ${index} --saveToys  --setPhysicsModelParameterRanges r=-60,60 -S0 $EXTRAOPT $FREZZEPDF $SETPARAMS &> /dev/null ) then  
touch $JOBPATH/sub${index}.sh.run
else 
touch  $JOBPATH/sub${index}.sh.fail.2
exit 1
fi

fi

if [[ -e higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root ]] ; then
echo "fit file exists"
else
touch  $JOBPATH/sub${index}.sh.fail.no_toy_file
exit 1
fi


#echo "combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t ${NTOYS} --saveSpecifiedIndex pdfindex_${TAG} -n  biasStudy3_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}  --algo singles  "
#if ( combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t 10 --saveSpecifiedIndex pdfindex_${TAG} -n  biasStudy4_${TAG}_pdf_${PDF}_mu_${MU}_job_${index} --algo singles -P r --robustFit 1  --setPhysicsModelParameterRanges r=-5,5 >$MYLOG) then 
echo "combine biasStudyWS_$TAG.root -M MaxLikelihoodFit $SETFITPDF $FREZZEFITPDF --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t ${NTOYS} -n biasStudy3_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -m ${MHhat} -v 4  --setPhysicsModelParameterRanges r=-60,60 &> /dev/null "
if (combine biasStudyWS_$TAG.root -M MaxLikelihoodFit $SETFITPDF $FREZZEFITPDF --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t ${NTOYS} -n biasStudy3_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index} -m ${MHhat} -v 4  --setPhysicsModelParameterRanges r=-60,60 -S0 $EXTRAOPT --protectUnbinnedChannels  &> /dev/null ) then

touch  $JOBPATH/sub${index}.sh.run
else 
touch  $JOBPATH/sub${index}.sh.fail.4
exit 1
fi



mkdir -p archive
#mv higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root archive/higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root
#mv higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root  $JOBPATH/toys.${index}.root 
mv mlfitbiasStudy3_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.root $JOBPATH/.
mv higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root $JOBPATH/toys.${index}.root
rm higgsCombinebiasStudy3_${TAG}_pdf_${PDF}_pdfFit_${FITPDF}_mu_${MU}_job_${index}.MaxLikelihoodFit.mH*.root

rm  $JOBPATH/sub${index}.sh.run
touch  $JOBPATH/sub${index}.sh.done
