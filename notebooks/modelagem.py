"""Peças de modelagem compartilhadas pelos notebooks 03 e 04.

Tudo que aprende com os dados (limites de winsorização, mediana para
imputação, média e desvio da padronização, média por UF do baseline) é
ajustado em `fit`, ou seja, só com os dados de treino de cada dobra.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class Winsorizador(BaseEstimator, TransformerMixin):
    """Limita cada coluna aos quantis aprendidos no treino (ignora ausentes)."""

    def __init__(self, inferior=0.01, superior=0.99):
        self.inferior = inferior
        self.superior = superior

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.limite_inf_ = np.nanquantile(X, self.inferior, axis=0)
        self.limite_sup_ = np.nanquantile(X, self.superior, axis=0)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        return np.clip(X, self.limite_inf_, self.limite_sup_)

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features, dtype=object)


class BaselineMediaUF(BaseEstimator, RegressorMixin):
    """Prevê o IDEB médio da UF no treino (média geral para UF não vista)."""

    def __init__(self, coluna_uf='sigla_uf'):
        self.coluna_uf = coluna_uf

    def fit(self, X, y):
        y = pd.Series(np.asarray(y, dtype=float), index=X.index)
        self.media_uf_ = y.groupby(X[self.coluna_uf]).mean().to_dict()
        self.media_geral_ = float(y.mean())
        return self

    def predict(self, X):
        return X[self.coluna_uf].map(self.media_uf_).fillna(self.media_geral_).to_numpy()


def montar_preprocessador(numericas, categoricas):
    """Winsorização p1/p99 -> imputação pela mediana -> padronização; one-hot nas categóricas."""
    numerico = Pipeline([
        ('winsor', Winsorizador(0.01, 0.99)),
        ('imputacao', SimpleImputer(strategy='median')),
        ('escala', StandardScaler()),
    ])
    categorico = OneHotEncoder(drop='first', handle_unknown='ignore', sparse_output=False)
    return ColumnTransformer(
        [('num', numerico, list(numericas)), ('cat', categorico, list(categoricas))],
        verbose_feature_names_out=False,
    )


def metricas(y_real, y_previsto):
    y_real = np.asarray(y_real, dtype=float)
    y_previsto = np.asarray(y_previsto, dtype=float)
    return {
        'RMSE': mean_squared_error(y_real, y_previsto) ** 0.5,
        'MAE': mean_absolute_error(y_real, y_previsto),
        'R²': r2_score(y_real, y_previsto),
        'Viés (previsto − real)': float(np.mean(y_previsto - y_real)),
    }
