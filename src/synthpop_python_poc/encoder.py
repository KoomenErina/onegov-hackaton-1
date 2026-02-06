from rpy2 import robjects as ro
import pyreadr
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import numpy as np


ro.r('''
     source("src\\\\synthpop_python_poc\\\\encode.R")
''')
encode_func = ro.r['enc']
def encode_column(x,y):
    
    with (ro.default_converter + pandas2ri.converter).context():
        result = encode_func(x,y)
    return result

class CatEncoder(BaseEstimator,TransformerMixin):
    def __init__(self):
        super().__init__()
        self.encoding = None
        self.var_name = ""

    def fit(self,X,y):
        print(f"encoding x={X.name} with y = {y.name}")

        if len(X.cat.categories)== 1:
            self.encoding = pd.DataFrame({"feature_level":[X.cat.categories[0]],
                                          "encoding":[1]})
            self.var_name = X.name
            return self
        if y.dtype == 'category':
            observed = y.cat.remove_unused_categories()
            if len(observed.cat.categories)== 1:
                self.encoding = pd.DataFrame({"feature_level":[X.cat.categories[0]],
                                            "encoding":[1]})
                self.var_name = X.name
                return self
        with (ro.default_converter + pandas2ri.converter).context():
            encoding_table = encode_func(X,y)

        self.encoding=encoding_table
        self.var_name = X.name
        return self

    def transform(self,X:pd.Series):
        print(f"encoding transformatie x={X.name}")

        is_na = X.isna()
        not_na = X.notna()
        empty_row = pd.DataFrame([{c:None for c in self.encoding.columns}]).drop('feature_level',axis=1)
        
        before = len(X.index)
        t = {f:self.encoding[self.encoding["feature_level"]==f].drop('feature_level',axis=1).reset_index(drop=True) for f in self.encoding["feature_level"]}
        t[np.nan] = empty_row

        l = [t[v] if v in t else empty_row for v in X]
        result = pd.concat(l,ignore_index=True)

        after = len(result.index)
        if before != after:
            print("stop")

        return result

class TotalCatEncoder(BaseEstimator,TransformerMixin):
    def __init__(self):
        super().__init__()
        self.column_encoders = {}

    def fit(self,X:pd.DataFrame,y):

        for col in X.columns:
            if X[col].dtype == 'category':
                not_na = X[col].notna()
                self.column_encoders[col] = CatEncoder().fit(X[col][not_na],y[not_na])
                
        return self
    
    def transform(self,X:pd.DataFrame):
        before = len(X.index)
        result = pd.concat([self.column_encoders[col].transform(X[col]).reset_index(drop=True)  if X[col].dtype== 'category' else pd.DataFrame(X[col]).reset_index(drop=True) for col in X.columns],axis=1, ignore_index=True)
        after = len(result.index)
        if before != after:
            print("stop")
        return result

