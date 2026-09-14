"""Preprocessing pipeline construction (fit on training set only)."""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(numeric, categorical):
    num_pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    cat_pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, numeric),
            ("cat", cat_pipe, categorical),
        ],
        remainder="drop",
    )


def feature_names_out(pre, columns):
    return list(pre.get_feature_names_out())


def transform_to_frame(pre, X):
    arr = pre.transform(X)
    names = pre.get_feature_names_out()
    return pd.DataFrame(
        arr.toarray() if hasattr(arr, "toarray") else arr, columns=names, index=X.index
    )
