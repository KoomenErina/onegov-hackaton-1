from sklearn import tree
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder,FunctionTransformer
from sklearn.compose import make_column_selector as selector

from src.synthpop_python_poc.encoder import TotalCatEncoder
from src.synthpop_python_poc.transformNaNs import NaNTransformer
import numpy as np


class CartRegressor(tree.DecisionTreeRegressor):
    def __init__(self, *
                 , criterion = "squared_error"
                 , splitter = "best"
                 , max_depth = None
                 , min_samples_split = 2
                 , min_samples_leaf = 5
                 , min_weight_fraction_leaf = 0
                 , max_features = None
                 , random_state = None
                 , max_leaf_nodes = None
                 , min_impurity_decrease = 0
                 , ccp_alpha = 1e-08
                 , get_nan_transformer = NaNTransformer.get_NaNTransformer):
        super().__init__(criterion=criterion, splitter=splitter, max_depth=max_depth, min_samples_split=min_samples_split, min_samples_leaf=min_samples_leaf, min_weight_fraction_leaf=min_weight_fraction_leaf, max_features=max_features, random_state=random_state, max_leaf_nodes=max_leaf_nodes, min_impurity_decrease=min_impurity_decrease, ccp_alpha=ccp_alpha)
        self.x_orig=None
        self.y = None
        self.nan_transformer = None
        self.get_nan_transformer = get_nan_transformer()
        self.encoder = TotalCatEncoder()


    @staticmethod
    def get_regressor():

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", TotalCatEncoder(), selector(dtype_include="category")),
                ("non-cat", FunctionTransformer(func=lambda x:x, inverse_func=lambda x:x), selector(dtype_exclude="category")),
                ]
            )
        
        pipeline = Pipeline(steps=[("preprocessor",preprocessor),
                                   ("synth",CartRegressor())]
                                   )
        return CartRegressor()

    def fit(self,X, y,**kwargs):
            l1 = len(X.index)
            self.nan_transformer = self.get_nan_transformer.fit(X,y)
            l2 = len(X.index)

            if l1 != l2:
                 print("stop")
            not_na = y.notna()
            self.encoder = self.encoder.fit(X,y)
            

            before = len(X[not_na].index)
            self.x_orig=self.encoder.transform(X[not_na])
            after = len(self.x_orig.index)
            if before != after:
                 print("stop")
            self.y=y[not_na]

            
            return super().fit(self.x_orig,self.y)
    
    def transform(self,x_syn, check_input=True):
        nan_mask = self.nan_transformer.transform(x_syn)
        not_na_mask = [not b for b in nan_mask]

        x_syn_enc = self.encoder.transform(x_syn[not_na_mask])

        nodes_orig = pd.DataFrame(self.apply(self.x_orig))
        df = pd.concat([nodes_orig,self.y.reset_index(drop=True)],axis=1,ignore_index=True).rename(columns={0:"nodes_orig",1:"y"})
        #Concat neemt de index van een series mee, ook als je ignore_index=True doet.
        #Het gevolg hiervan is dat je meer rijen in df hebt dan in nodes_orig en self.y (die even veel rijen hebben).
        # Daar het gevolg van is dat er NaN waarden geproduceert worden. 
        # Deze NaNs komen met name voor waar NaNs gefilted zijn. Zo lijkt het alsof er NaNs voorspeld worden zonder NaNTransformer.

        #pd.concat([nodes_orig,self.y],axis=1).rename(columns={0:"nodes_orig",1:"y"})
        nodes_group = df.groupby('nodes_orig')#.value_counts(normalize=True)
        probs_map = {n:g.rename(columns={1:"y"}) for n,g in nodes_group}

        nodes_pred = self.apply(x_syn_enc)
        y_pred = [probs_map[int(n)].sample().to_numpy()[:,1] for n in nodes_pred ]
        result = pd.DataFrame(columns=[self.y.name],index=x_syn.index)
        idx_not_na = np.where(not_na_mask)[0]
        result.iloc[idx_not_na]=y_pred

        return result
    