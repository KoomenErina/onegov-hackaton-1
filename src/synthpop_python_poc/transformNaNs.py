from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.tree import DecisionTreeClassifier
import pandas as pd
import pyreadr
import numpy as np
from xgboost import XGBClassifier

from src.synthpop_python_poc.encoder import TotalCatEncoder

rng = np.random.default_rng()
class NaNTransformer(BaseEstimator,TransformerMixin):


    @staticmethod
    def get_NaNTransformer():
        return NaNTransformer()
        pass
    def __init__(self):
        super().__init__()
        # self.classifier = XGBClassifier(enable_categorical=True
        #                    #,n_estimators=1
        #                    ,max_leaves=0
        #                    ,min_child_weight=5
        #                    #,max_cat_threshold=1000
        #                    #,max_cat_onehot=0
        #                    ,tree_method="approx"
        #                    ,subsample=1.0
        #                    ,colsample_bytree=1.0
        #                    ,colsample_bylevel=1.0
        #                    ,colsample_bynode=1.0
        #                    ,grow_policy="lossguide")
        self.classifier = DecisionTreeClassifier(criterion = "gini"
                 , splitter = "best"
                 , max_depth = None
                # , min_samples_split = 2
                 , min_samples_leaf = 5
                 , min_weight_fraction_leaf = 0
                 , max_features = None
                 , random_state = None
                 , max_leaf_nodes = None
                 , min_impurity_decrease = 0
                 , class_weight = None
                 , ccp_alpha =  1e-08)
        self.y=None
        self.encoder = TotalCatEncoder()

    def fit(self,X,y):

        #df["y_is_nan"] = df[last_col].isna()
        x_tr = self.encoder.fit_transform(X,y)
        self.classifier = self.classifier.fit(pd.DataFrame(x_tr),y.isna())
        return self

    def transform(self,X):
        x_tr = self.encoder.transform(X)
        probs = self.classifier.predict_proba(x_tr)
        #print(probs)
        y_vals = self.classifier.classes_
        pred = [rng.choice(self.classifier.classes_,p=prob) for prob in probs]#[rng.choice(y_vals, p = prob) for prob in probs]#self.classifier.predict(X)
        return pred


class NaNToCategory(BaseEstimator,TransformerMixin):

    def __init__(self):
        super().__init__()

    def NaN_to_category(self,x:pd.Series)->pd.Series:
        x = x.cat.add_categories(["N.a.N"])
        is_na = x.isna()
        x[is_na] = "N.a.N"
        return x
    
    def category_to_NaN(self,x:pd.Series)->pd.Series:
        is_na = x=="N.a.N"
        x = x.copy()
        x[is_na]= None
        if "N.a.N" in x.cat.categories:
            x = x.cat.remove_categories(["N.a.N"])
        return x

    def fit(self,X,y):
        return self

    def transform(self,X):
        for idx_col,column in enumerate(X):
            if X[column].dtype == 'category':
                X[column] = self.NaN_to_category(X[column] )
        return X
    
    def inverse_transform(self,X):
        for idx_col,column in enumerate(X):
            if X[column].dtype == 'category':
                X[column] = self.category_to_NaN(X[column] )
        return X





# data = (pyreadr.read_r("SD2011.rda")['SD2011'])\
#     .select_dtypes(include=['category','float64'])
# print(data)
# tr = NaNToCategory()
# res = tr.inverse_transform(tr.transform(data))
# print(res["edu"].value_counts())


# x = data[["age"]]
# y = data[["mmarr"]]
# deimputer = NaNTransformer()

# deimputer.fit(x,y)
# print(deimputer.transform(x))
