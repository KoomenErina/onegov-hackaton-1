import pandas as pd

class Sampler:
    def __init__(self):
        self.x = None
        pass

    def fit(self,x):
        self.x = x
        return self

    def predict_sample(self,n_rows):
        return pd.DataFrame(self.x.sample(n=n_rows
                      ,replace=True#Het is een kleine dataset (150 regels) Sampelen met replacement geeft al een relatief grote synthese fout.
                      ,ignore_index=True#door ignore_index=True voorkomen we dat er een index kolom onstaat. Een index kolom zit het predicten in de weg.
                      ))


