MYLOG=$JOBPATH/mylog.$index.log
if (( $PDF>-1)); then
FREZZEPDF="--freezeNuisances pdfindex_${TAG}"
SETPDF="--setPhysicsModelParameters pdfindex_${TAG}=${PDF} "
else
FREZZEPDF="--freezeNuisances pdfindex_${TAG}"
fi

if (( $FITPDF>-1)); then
FREZZEFITPDF="--freezeNuisances pdfindex_${TAG}"
SETFITPDF="--setPhysicsModelParameters pdfindex_${TAG}=${PDF} "
else
FREZZEFITPDF="--freezeNuisances pdfindex_${TAG}"
fi

echo
echo "STEP 1 check for higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root"
echo
if [[ -e higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root ]] ; then
echo " this file already exists":
ls higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root
else 
echo "execute: combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} $FREZZEPDF $SETPDF -n  biasStudy1 --saveWorkspace"
if ( combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} $FREZZEPDF $SETPDF -n  biasStudy1_${TAG}_pdf_${PDF} --saveWorkspace >$MYLOG ) then
touch $JOBPATH/sub${index}.sh.run
else 
touch $JOBPATH/sub${index}.sh.fail.1
exit 1
fi
fi

echo
echo "STEP 2"
echo

cp higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}.root higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}_${index}.root
echo " combine higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}_${index}.root --snapshotName MultiDimFit -M GenerateOnly -m ${MHhat} --saveWorkspace --toysFrequentist --bypassFrequentistFit -t ${NTOYS} --expectSignal=${MU} $FREZZEPDF $SETPDF  -n biasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index} -s ${index} --saveToys"
if ( combine higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}_${index}.root --snapshotName MultiDimFit -M GenerateOnly -m ${MHhat} --saveWorkspace --toysFrequentist --bypassFrequentistFit -t ${NTOYS} --expectSignal=${MU} $FREZZEPDF $SETPDF   -n biasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index} -s ${index} --saveToys >$MYLOG ) then
touch $JOBPATH/sub${index}.sh.run
else 
touch  $JOBPATH/sub${index}.sh.fail.2
exit 1
fi
rm higgsCombinebiasStudy1_${TAG}_pdf_${PDF}.MultiDimFit.mH${MHhat}_${index}.root

echo
echo "STEP 3"
echo

echo "combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t ${NTOYS} --saveSpecifiedIndex pdfindex_${TAG} -n  biasStudy3_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}  --algo fixed  -P r --setPhysicsModelParameters r=${MU}"
if ( combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t ${NTOYS} --saveSpecifiedIndex pdfindex_${TAG} -n  biasStudy3_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}   --algo fixed  -P r --setPhysicsModelParameters r=${MU} --setPhysicsModelParameterRanges r=-5,10  $FREZZEFITPDF $SETFITPDF   > /dev/null/ ) then
touch  $JOBPATH/sub${index}.sh.run
else
touch  $JOBPATH/sub${index}.sh.fail.3
exit 1
fi
mv higgsCombinebiasStudy3_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.MultiDimFit.mH${MHhat}.123456.root $JOBPATH/. 

#echo
#echo "STEP 4"
#echo

#echo "combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t ${NTOYS} --saveSpecifiedIndex pdfindex_${TAG} -n  biasStudy3_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}  --algo singles  "
#if ( combine biasStudyWS_$TAG.root -M MultiDimFit -m ${MHhat} --toysFile higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root -t 10 --saveSpecifiedIndex pdfindex_${TAG} -n  biasStudy4_${TAG}_pdf_${PDF}_mu_${MU}_job_${index} --algo singles -P r --robustFit 1  --setPhysicsModelParameterRanges r=-5,5 >$MYLOG) then
#touch  $JOBPATH/sub${index}.sh.run
#else 
#touch  $JOBPATH/sub${index}.sh.fail.4
#exit 1
#fi


mkdir -p archive
mv higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root archive/higgsCombinebiasStudy2_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.GenerateOnly.mH${MHhat}.${index}.root
mv higgsCombinebiasStudy4_${TAG}_pdf_${PDF}_mu_${MU}_job_${index}.MultiDimFit.mH${MHhat}.123456.root $PULLJOBPATH/. 

rm  $JOBPATH/sub${index}.sh.run
touch  $JOBPATH/sub${index}.sh.done
