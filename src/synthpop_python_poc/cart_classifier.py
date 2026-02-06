from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import OrdinalEncoder,FunctionTransformer
from sklearn.compose import make_column_selector as selector
import pandas as pd
import numpy as np

from src.synthpop_python_poc.encoder import TotalCatEncoder
from src.synthpop_python_poc.transformNaNs import NaNToCategory, NaNTransformer

rng = np.random.default_rng()
class CartClassifier(DecisionTreeClassifier):

    @staticmethod
    def get_classifier():

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", TotalCatEncoder(), selector(dtype_include="category")),
                ("non-cat", FunctionTransformer(func=lambda x:x, inverse_func=lambda x:x), selector(dtype_exclude="category")),
                ]
            )
        
        pipeline = Pipeline(steps=[("preprocessor",preprocessor),
                                   ("synth",CartClassifier())]
                                   )
        return CartClassifier()#pipeline

    def __init__(self, *, criterion = "gini"
                 , splitter = "best"
                 , max_depth = None
                 #, min_samples_split = 2
                 , min_samples_leaf = 5
                 , min_weight_fraction_leaf = 0
                 , max_features = None
                 , random_state = None
                 , max_leaf_nodes = None
                 , min_impurity_decrease = 0
                 , class_weight = None
                 , ccp_alpha =  1e-08
                 ,nan_transformer = NaNToCategory()
                 ,encoder = TotalCatEncoder()):
        super().__init__(criterion=criterion, splitter=splitter, max_depth=max_depth, min_samples_leaf=min_samples_leaf, min_weight_fraction_leaf=min_weight_fraction_leaf, max_features=max_features, random_state=random_state, max_leaf_nodes=max_leaf_nodes, min_impurity_decrease=min_impurity_decrease, class_weight=class_weight, ccp_alpha=ccp_alpha)
        self.x_orig=None
        self.y=None
        self.nan_transformer = nan_transformer
        self.encoder = TotalCatEncoder()
    

    def fit(self,X, y,**kwargs):
        X = pd.DataFrame(X)
        y = self.nan_transformer.NaN_to_category(y)
        self.encoder = self.encoder.fit(X,y)
 
        self.x_orig=self.encoder.transform(X)
        self.y=y

        return super().fit(self.x_orig,self.y)
    
    def transform(self,x_syn, check_input=True):
        x_syn = self.encoder.transform(x_syn)
        probs = self.predict_proba(x_syn)
        #Sampelen uit classes_ is erg belangrijk, ivm volg orde van factor levels.
        pred_y_vals = pd.DataFrame([rng.choice(self.classes_, p = prob) for prob in probs],columns=[self.y.name]).astype('category')

        return self.nan_transformer.inverse_transform(pred_y_vals)