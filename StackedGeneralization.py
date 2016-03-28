"""

Purpose: This script tries to implement a technique called stacking/blending/stacked generalization.
The reason I have to make this a runnable script because I found that there isn't really any
readable code that demonstrates this technique. You may find the pseudocode in various papers but they
are all each kind of different.

Author: Eric Chio "log0" <im.ckieric@gmail.com>

======================================================================================================
Summary:

Just to test an implementation of stacking. Using a cross-validated random forest and SVMs, I was
only able to achieve an accuracy of about 88% (with 1000 trees and up). Using stacked generalization 
I have seen a maximum of 93.5% accuracy. It does take runs to find it out though. This uses only 
(10, 20, 10) trees for the three classifiers.

This code is heavily inspired from the code shared by Emanuele (https://github.com/emanuele) , but I
have cleaned it up to makeit available for easy download and execution.

======================================================================================================
Methodology:

Three classifiers (RandomForestRegressor, ExtraTreesRegressor and a GradientBoostingRegressor
are built to be stacked by a LogisticRegression in the end.

Some terminologies first, since everyone has their own, I'll define mine to be clear:
- DEV SET, this is to be split into the training and validation data. It will be cross-validated.
- TEST SET, this is the unseen data to validate the generalization error of our final classifier. This
set will never be used to train.

======================================================================================================
Log Output:

X_test.shape = (62L, 6L)
blend_train.shape = (247L, 3L)
blend_test.shape = (62L, 3L)
Training classifier [0]
Fold [0]
Fold [1]
Fold [2]
Fold [3]
Fold [4]
Training classifier [1]
Fold [0]
Fold [1]
Fold [2]
Fold [3]
Fold [4]
Training classifier [2]
Fold [0]
Fold [1]
Fold [2]
Fold [3]
Fold [4]
Y_dev.shape = 247
Accuracy = 0.935483870968


"""

import time

import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from SimpleNN import KerasNN
from utilities import make_folder
# from SimpleNN import KerasNN

np.random.seed(2016)

from sklearn.cross_validation import StratifiedKFold
from sklearn.linear_model import LinearRegression, BayesianRidge, ElasticNet, SGDRegressor
from sklearn import metrics
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.utils import shuffle
from configs import *
import xgboost as xgb
import pickle as pkl
import os
from scipy.stats.mstats import gmean, hmean

np.set_printoptions(formatter={'float_kind': float_formatter})


def run(X, Y, X_test=None):
    # The DEV SET will be used for all training and validation purposes
    # The TEST SET will never be used for training, it is the unseen set.

    Y = (Y - 1) / 2

    if X_test is None:
        dev_cutoff = int(len(Y) * TEST_CUTOFF)

        X, Y = shuffle(X, Y)

        X_dev = X[:dev_cutoff]
        Y_dev = Y[:dev_cutoff]
        X_test = X[dev_cutoff:]
        Y_test = Y[dev_cutoff:]
    else:
        X, Y = shuffle(X, Y)
        X_dev = X
        Y_dev = Y

    n_folds = configs['n_folds']  # Higher is better

    # Our level 0 classifiers
    clfs = [
        # ('KerasSimpleNN',KerasNN(nb_epoch=150, batch_size=100000)),
        ('BayesianRidge', BayesianRidge(alpha_1=1e-6, alpha_2=1e-6, verbose=not configs['silent'])),
        ('BayesianRidgeA0', BayesianRidge(alpha_1=1e0, alpha_2=1e-6, verbose=not configs['silent'])),

        ('LinearRegression', LinearRegression(n_jobs=NJOBS)),
        ('ElasticNetRegression', ElasticNet(alpha=0.2, l1_ratio=0.5)),
        # ('ElasticNetRegressionAX', ElasticNet(alpha=0.1, l1_ratio=0.1)),
        # ('ElasticNetRegressionAXB', ElasticNet(alpha=0.1, l1_ratio=0.9)),
        # ('SGDRegressor', SGDRegressor()),
        # ('SVRRegression', SVR(verbose=not configs['silent'])),
        # ('RandomForestRegressor', RandomForestRegressor(n_estimators=mConfig['rfr_n_trees'], n_jobs=NJOBS, verbose=not configs['silent'])),
        # ('ExtraTreesRegressor',
        #  ExtraTreesRegressor(n_estimators=mConfig['etr_n_trees'], n_jobs=NJOBS, verbose=not configs['silent'], max_features=99,
        #                      max_depth=7)),
        ('DecisionTreeRegressor', DecisionTreeRegressor(max_depth=6, max_features=99)),
        ('DecisionTreeRegressor5', DecisionTreeRegressor(max_depth=5, max_features=99)),
        ('DecisionTreeRegressor7', DecisionTreeRegressor(max_depth=7, max_features=99)),
        ('DecisionTreeRegressor4', DecisionTreeRegressor(max_depth=4, max_features=99)),
        ('DecisionTreeRegressor3', DecisionTreeRegressor(max_depth=3, max_features=99)),
        ('DecisionTreeRegressor2', DecisionTreeRegressor(max_depth=2, max_features=99)),
        ('DecisionTreeRegressor1', DecisionTreeRegressor(max_depth=1, max_features=99)),
        # Highly Correlated with other models
        # ('GradientBoostingRegressor', GradientBoostingRegressor(n_estimators=mConfig['gbr_n_trees'],
        #                                                         max_depth=9,
        #                                                         learning_rate=0.025,
        #                                                         max_features=85,
        #                                                         subsample=0.85,
        #                                                         verbose=not configs['silent'])),
        # TODO Try by changing other parameters
        ('XGBLinear', xgb.XGBRegressor(learning_rate=0.075,
                                       silent=configs['silent'],
                                       objective="reg:linear",
                                       nthread=NJOBS,
                                       gamma=0.55,
                                       min_child_weight=5,
                                       max_delta_step=1,
                                       subsample=0.65,
                                       colsample_bytree=0.9,
                                       colsample_bylevel=1,
                                       reg_alpha=0.5,
                                       reg_lambda=1,
                                       scale_pos_weight=1,
                                       base_score=0.5,
                                       seed=0,
                                       missing=None,
                                       n_estimators=mConfig['xgb_n_trees:linear'],
                                       max_depth=7
                                       )),
        ('XGBLogistic', xgb.XGBRegressor(learning_rate=0.075,
                                         silent=configs['silent'],
                                         objective="reg:logistic",
                                         nthread=NJOBS,
                                         gamma=0.55,
                                         min_child_weight=5,
                                         max_delta_step=1,
                                         subsample=0.65,
                                         colsample_bytree=0.9,
                                         colsample_bylevel=1,
                                         reg_alpha=0.5,
                                         reg_lambda=1,
                                         scale_pos_weight=1,
                                         base_score=0.5,
                                         seed=0,
                                         missing=None,
                                         n_estimators=mConfig['xgb_b_trees:logistic'],
                                         max_depth=7
                                         ))
    ]

    # Ready for cross validation
    skf = list(StratifiedKFold(Y_dev, n_folds=n_folds, shuffle=True))

    # Pre-allocate the data
    blend_train = np.zeros((X_dev.shape[0], len(clfs)))  # Number of training data x Number of classifiers
    blend_test = np.zeros((X_test.shape[0], len(clfs)))  # Number of testing data x Number of classifiers

    print('X_test.shape = %s' % (str(X_test.shape)))
    print('blend_train.shape = %s' % (str(blend_train.shape)))
    print('blend_test.shape = %s' % (str(blend_test.shape)))

    # For each classifier, we train the number of fold times (=len(skf))
    for j, (clf_name, clf) in enumerate(clfs):
        blend_test_j = np.zeros((X_test.shape[0], len(
            skf)))  # Number of testing data x Number of folds , we will take the mean of the predictions later
        if os.path.isfile('%s%s%s' % (FOLD_PATH, clf_name, 'Train.npy')) and os.path.isfile(
                        '%s%s%s' % (FOLD_PATH, clf_name, 'Test.npy')):
            print('Loading classifier [%s %s]' % (j, clf_name))
            blend_train[:, j] = np.load(FOLD_PATH + clf_name + 'Train.npy')
            blend_test[:, j] = np.load(FOLD_PATH + clf_name + 'Test.npy')
        else:
            print('Training classifier [%s %s]' % (j, clf_name))
            for i, (train_index, cv_index) in enumerate(skf):
                print('Fold [%s]' % (i))

                # This is the training and validation set
                X_train = X_dev[train_index]
                Y_train = Y_dev[train_index]
                X_cv = X_dev[cv_index]
                Y_cv = Y_dev[cv_index]

                clf.fit(X_train, Y_train)

                # This output will be the basis for our blended classifier to train against,
                # which is also the output of our classifiers
                blend_train[cv_index, j] = clf.predict(X_cv)
                blend_test_j[:, i] = clf.predict(X_test)
            # Take the mean of the predictions of the cross validation set
            blend_test[:, j] = blend_test_j.mean(1)
            if not DEBUG or 1:
                blend_train[:, j].dump(FOLD_PATH + clf_name + 'Train.npy')
                blend_test[:, j].dump(FOLD_PATH + clf_name + 'Test.npy')
    print('Y_dev.shape = %s' % Y_dev.shape)

    # Saving Model Data
    blend_train.dump(FOLD_PATH + 'BlendTrain_X.npy')
    Y_dev.dump(FOLD_PATH + 'BlendTrain_Y.npy')
    blend_test.dump(FOLD_PATH + 'BlendTest_X.npy')
    if 'Y_test' in locals(): Y_test.dump(FOLD_PATH + 'BlendTest_Y.npy')

    # Correlation Matrix
    print('\n---------- Correlation Matrix ----------')
    print(np.corrcoef(np.transpose(blend_train)))

    # TODO Try ridge regression
    # Start blending!
    bclf = LinearRegression(n_jobs=NJOBS)
    # bclf = xgb.XGBRegressor(learning_rate=0.075,
    #                         silent=False,
    #                         objective="reg:linear",
    #                         nthread=NJOBS,
    #                         gamma=0.55,
    #                         min_child_weight=5,
    #                         max_delta_step=1,
    #                         subsample=0.65,
    #                         colsample_bytree=0.9,
    #                         colsample_bylevel=1,
    #                         reg_alpha=0.5,
    #                         reg_lambda=1,
    #                         scale_pos_weight=1,
    #                         base_score=0.5,
    #                         seed=0,
    #                         missing=None,
    #                         n_estimators=100,
    #                         max_depth=7
    #                         )

    # score=cross_val_score(bclf, verbose=20, cv=2, X=blend_train, y=Y_dev)
    bclf.fit(blend_train, Y_dev)

    # Predict now
    Y_test_predict = bclf.predict(blend_test)

    # Y_test_predict = 2*Y_test_predict+1

    for i in range(len(Y_test_predict)):
        if Y_test_predict[i] < 0:
            Y_test_predict[i] = 0
        elif Y_test_predict[i] > 1:
            Y_test_predict[i] = 1

    if 'Y_test' in locals():
        print('\n---------- Test Accuracy ----------')
        for i, (clf_name, clf) in enumerate(clfs):
            score = metrics.mean_squared_error(blend_test[:, i] * 2 + 1, Y_test * 2 + 1)
            print('%s Accuracy = %s' % (clf_name, score ** 0.5))
        score = metrics.mean_squared_error(Y_test * 2 + 1, Y_test_predict * 2 + 1)
        print('Accuracy = %s' % (score ** 0.5))
    print('\n---------- Cross Validation Accuracy ----------')
    for i, (clf_name, clf) in enumerate(clfs):
        score = metrics.mean_squared_error(blend_train[:, i] * 2 + 1, Y_dev * 2 + 1)
        print('%s Accuracy = %s' % (clf_name, score ** 0.5))
    print('Weights = %s' % str(bclf.coef_))
    return Y_test_predict * 2 + 1


def run_tests(X_train, y_train):
    pass


# TODO Un-tune individual model
if __name__ == '__main__':
    dataset_name = 'svd50x3'
    model_name = '4fold_stacked_100estimators'
    FOLD_PATH = FOLD_PATH + model_name + '/'

    make_folder(FOLD_PATH)

    X_train = np.load('%s%s_train.npy' % (DATASET_PATH, dataset_name))
    X_test = np.load('%s%s_test.npy' % (DATASET_PATH, dataset_name))
    y_train = np.load('%sY_train.npy' % DATASET_PATH)
    id_test = np.load('%sid_test.npy' % DATASET_PATH)

    Y_test = run(X_train, y_train, X_test)
    pd.DataFrame({"id": id_test, "relevance": Y_test}).to_csv('submission/submission_stacked_%s.csv' % time.time(),
                                                              index=False)
