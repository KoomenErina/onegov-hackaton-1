import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA, MiniBatchSparsePCA, SparsePCA

def single_target_transform(df:pd.DataFrame,time_column,target_columns,entity_id):

    
    print(matrix)


class TimeSeriesToTable(BaseEstimator,TransformerMixin):

    def __init__(self,time_column,target_columns,entity_id):
        super().__init__()
        self.time_column = time_column
        self.target_column = target_columns
        self.entity_id = entity_id
        self.transformer = PCA().set_output(transform="pandas")


    def fit(self, X):
        
        print(X.value_counts())
        matrix = X.pivot(index=self.time_column,columns=self.entity_id,values=self.target_column).fillna(0)
        self.time_ = matrix.index
        print("time_ = ")
        print(self.time_)
        print("input matrix:")
        print(matrix) #51 tijdstippen, 395 individuen.
        self.index = matrix.index

        print(f"shape of input matrix:{matrix.shape}")
        self.transformer = self.transformer.fit(matrix)

        print("components:")
        print(self.transformer.components_)
        print(f"component shape:{self.transformer.components_.shape}")

    def transform(self,X):
        matrix = X.pivot(index=self.time_column,columns=self.entity_id,values=self.target_column).fillna(0)
        print(matrix)
        return self.transformer.transform(matrix)
    
    def inverse_transform(self,y):
        matrix = self.transformer.inverse_transform(y)

        print("matrix after inverse transform:")
        print(matrix)
  
        matrix[self.time_column] = self.time_

        print("matrix before melt:")
        print(matrix)
        matrix.reset_index(drop=True)
        result = matrix.melt(id_vars=self.time_column,var_name=self.entity_id,value_name=self.target_column)
        #result[self.time_column] = self.time_
        #result =  pd.Series(self.transformer.components_[0], index=self.index)#pd.DataFrame(matrix,index=self.index)#pd.melt(matrix,id_vars=self.entity_id)
        return result