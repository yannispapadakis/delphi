#!/bin/bash

features_="sens,cont"
qoses_="1,2,3"
classes_="2,3"
models_="LR,SGD,PA,PER,RID,LDA,QDA,SVC,NSVC,LSVC,DT,KN,RN,NC,GP,GNB,RF,ET,AB,HGB,GB,MLP"

IFS=',' read -r -a features <<< "${features_}"
for feature in ${features[@]}; do
	IFS=',' read -r -a qoses <<< "${qoses_}"
	for qos in ${qoses[@]}; do
		IFS=',' read -r -a classes <<< "${classes_}"
		for class in ${classes[@]}; do
			core=$(($class * 5 + $qos))
			IFS=',' read -r -a models <<< "${models_}"
			for model in ${models[@]}; do
				./predictor.py test $feature 1.$qos $class $model s,p t
			done
		done
	done
done
