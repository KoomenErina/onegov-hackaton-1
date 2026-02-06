import pyreadr
from sklearn import tree
from src.synthpop_python_poc.sampler import Sampler
import pandas as pd
from pandas.api.types import is_numeric_dtype
from src.synthpop_python_poc.transformNaNs import NaNTransformer
from src.synthpop_python_poc.cart_classifier import CartClassifier
from src.synthpop_python_poc.cart_regressor import CartRegressor

class Synth:
    
    def __init__(self,get_classiefier=tree.DecisionTreeClassifier, get_regressor=tree.DecisionTreeRegressor, get_Nan = NaNTransformer.get_NaNTransformer ):
        self.get_classifier = get_classiefier
        self.get_regressor = get_regressor
        self.get_nan_transformer = get_Nan
        self.models={}

    def fit(self,x:pd.DataFrame,targets):
        """
        X: volledige tabel, inclusief features en targets.
        targets: list of columns to be synthesised.
        """ 
        self.targets_ = targets
        for idx_col,column in enumerate(x):
            if column not in targets:
                continue
            if idx_col == 0:
                sam = Sampler()
                sam.fit(x[column])
                self.models[column]= sam
                continue
            features = x.iloc[:,0:idx_col]

            print(f"features for {column} ----- {features.columns}")
            target = x[column]
            if is_numeric_dtype(x[column]):
                estimator = self.get_regressor()
                #self.models[column] = self.regressor.fit(features,target)
            else:
                estimator = self.get_classifier()
                print(f"CAT={column}-----------------------------------------------------------")
                #self.models[column] = self.classifier.fit(features,target)

            self.models[column] = estimator.fit(features,target)

    def generate(self,n_rows = None, x_syn = None):
        
        if x_syn is not None:
            result = x_syn
        else:
            print('generation of first column')
            first_column = next(iter(self.models))
            result = self.models[first_column].predict_sample(n_rows)
        for idx_col,(column,model) in enumerate(self.models.items()):
            if idx_col == 0 and x_syn is None:
                continue
            print(f"generating column: {column} with synthesised features {result.columns}")
            new_column = model.transform(result)
            result = pd.concat([result,new_column],axis=1)
        return result

