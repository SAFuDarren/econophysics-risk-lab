"""Validation-selected, training-only preprocessing for paired observation views."""

from itertools import product
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.kernel_ridge import KernelRidge


class CenteredRegressor:
    def __init__(self, estimator, specification):
        self.estimator = estimator
        self.specification = specification

    def fit(self, x, y):
        self.mean = float(np.mean(y))
        if self.estimator is not None:
            self.estimator.fit(x, y-self.mean)
        return self

    def predict(self, x):
        return np.full(len(x), self.mean) if self.estimator is None else self.estimator.predict(x)+self.mean


def candidate_specs(method, dimension, config):
    if method == 'Dummy':
        return [{}]
    if method == 'Ridge':
        return [{'alpha':a} for a in config['ridge_alpha']]
    return [{'alpha':a, 'gamma':g/dimension} for a,g in product(config['rbf_alpha'],config['rbf_gamma_multipliers'])]


def make_regressor(method, specification):
    if method == 'Dummy':
        return CenteredRegressor(None, specification)
    estimator = Ridge(alpha=specification['alpha'],fit_intercept=False) if method == 'Ridge' else KernelRidge(kernel='rbf',**specification)
    pipeline = Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                         ('scale',StandardScaler()),('regress',estimator)])
    return CenteredRegressor(pipeline,specification)


def select_regressor(method, x_train, y_train, x_val, y_val, config):
    records, fitted = [], []
    for spec in candidate_specs(method,x_train.shape[1],config):
        model = make_regressor(method,spec).fit(x_train,y_train)
        loss = float(np.mean(np.abs(model.predict(x_val)-y_val)))
        records.append({'specification':spec,'validation_mae':loss})
        fitted.append(model)
    index = min(range(len(records)),key=lambda i: records[i]['validation_mae'])
    return fitted[index], records, index
