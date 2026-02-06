from src.synthpop_python_poc.synth import Synth
from src.synthpop_python_poc.cart_classifier import CartClassifier
from src.synthpop_python_poc.cart_regressor import CartRegressor

from src.synthpop_python_poc.metric import pairwise_spmse
from src.synthpop_python_poc.plotting import plot_spsme, plot_univariate_distributions

import pandas as pd
from pathlib import Path



###### DATA INLADEN EN VOORBEREIDEN

inkomstenperiode = pd.read_csv("data/LA_INKOMSTENPERIODE.csv", sep=";")
t1 = inkomstenperiode[inkomstenperiode['HIS_DAT_END'] == 99991231].drop(["HIS_DAT_END", "HIS_TS_END","INDRGLMARB", "INDAANVUITK", "INDPKINDNSTOUDWN", "INDJRURENNRM", "INDPUBAANONBEPTD", "INDSA43", "CAO", "LBTAB"], axis=1)
t2 = pd.read_csv("data/LA_IKV_PERSOON_HIS.csv", sep=";").drop(['HIS_DAT_END', 'HIS_TS_END', 'NAT'], axis=1)
t2['GESL'] = t2['GESL'].replace({1: "man", 2: "vrouw", 9: "niet gespecificeerd"})
t3 = pd.read_csv("data/LA_IKV_ADRES_HIS.csv", sep=";").drop(['HIS_DAT_END', 'HIS_TS_END'], axis=1)
t3['ADRESTYPE'] = t3['ADRESTYPE'].replace({0: "binnenlands adres", 1: "buitenlands adres", 2: "geen adres"})
t4 = pd.read_csv("data/LA_SECTORRISICOGROEP.csv", sep=";").drop(['HIS_DAT_END', 'HIS_TS_END'], axis=1)
 
tables = [t1, t2, t3, t4]
keys = ['IKV_ID', 'HIS_DAT_IN', 'HIS_TS_IN']

###### KOLOMMEN MET VEEL NAs ERUIT HALEN
print('Kolommen schoon maken')
excluded_columns = {}
tables_clean = []
for i, df in enumerate(tables):
    # drop kolommen met NAs
    na_pct = df.isna().mean()
    to_drop = na_pct[na_pct > 0.5].index.tolist()
    excluded_columns[i] = to_drop

    df_clean = df.drop(columns=to_drop)

    tables_clean.append(df_clean)
 

###### SYNTHESE PIPELINE (t1 & t2, t3, t4)
print('Synthese voor de eerste combinatie')
eerste_combinatie = pd.merge(tables_clean[0], tables_clean[1], on=keys, how='left')

eerste_synth = Synth(get_classiefier=CartClassifier.get_classifier,
                     get_regressor=CartRegressor.get_regressor
                    )

list_str_obj_cols = eerste_combinatie.columns[eerste_combinatie.dtypes == "object"].tolist()
for str_obj_col in list_str_obj_cols:
    eerste_combinatie[str_obj_col] = eerste_combinatie[str_obj_col].astype("category")

eerste_synth.fit(x= eerste_combinatie, targets=eerste_combinatie.columns.drop(keys))

eerste_syn_data = eerste_synth.generate(n_rows = eerste_combinatie.shape[0], x_syn = eerste_combinatie[keys])

t1_syn = eerste_syn_data[tables_clean[0].columns]
t2_syn = eerste_syn_data[tables_clean[1].columns]

results = [t1_syn, t2_syn]

####### Tweede synthese (t3)
print('Synthese voor tabel t3')

tweede_combinatie = pd.merge(eerste_syn_data, tables_clean[2], on=keys, how='left')

list_str_obj_cols = tweede_combinatie.columns[tweede_combinatie.dtypes == "object"].tolist()
for str_obj_col in list_str_obj_cols:
    tweede_combinatie[str_obj_col] = tweede_combinatie[str_obj_col].astype("category")

synth = Synth(get_classiefier=CartClassifier.get_classifier,
                        get_regressor=CartRegressor.get_regressor
                        )
synth.fit(x = tweede_combinatie, targets = tables_clean[2].columns.drop(keys))
tweede_synth_data = synth.generate(n_rows = tweede_combinatie.shape[0], x_syn = eerste_syn_data)

t3_syn = tweede_synth_data[tables_clean[2].columns]
results.append(t3_syn)

####### Derde synthese (t4)
print('Synthese voor tabel t4')

derde_combinatie = pd.merge(tweede_synth_data, tables_clean[3], on=keys, how='left')

list_str_obj_cols = derde_combinatie.columns[derde_combinatie.dtypes == "object"].tolist()
for str_obj_col in list_str_obj_cols:
    derde_combinatie[str_obj_col] = derde_combinatie[str_obj_col].astype("category")

synth = Synth(get_classiefier=CartClassifier.get_classifier,
                        get_regressor=CartRegressor.get_regressor
                        )
synth.fit(x = derde_combinatie, targets = tables_clean[3].columns.drop(keys))
derde_synth_data = synth.generate(n_rows = derde_combinatie.shape[0], x_syn = tweede_synth_data)

t4_syn = derde_synth_data[tables_clean[3].columns]
results.append(t4_syn)

####### SYN DATASETS OPSLAAN
Path("data").mkdir(exist_ok=True)
results[0].to_csv('data/INKOMSTENPERIODE_syn.csv', index=False)
results[1].to_csv('data/PERSOON_syn.csv', index=False)
results[2].to_csv('data/ADRES_syn.csv', index=False)
results[3].to_csv('data/SECTORRISICOGROEP_syn.csv', index=False)

print("Data gesynthetiseerd en opgeslagen")

####### S_pMSE berekenen

u = []
for i in range(4):
    utiliteit = pairwise_spmse(tables_clean[i], results[i])
    u.append(utiliteit)

