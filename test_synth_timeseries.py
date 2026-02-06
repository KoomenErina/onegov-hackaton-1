import pandas as pd

from synthpop_python_poc.cart_classifier import CartClassifier
from synthpop_python_poc.cart_regressor import CartRegressor
from synthpop_python_poc.synth import Synth
from synthpop_python_poc.transform_timeseries import TimeSeriesToTable
import seaborn as sns
import matplotlib.pyplot as plt

df_full = pd.read_csv("data/LA_INKOMSTENOPGAVE.csv",sep=";")
target = "LNLBPH"
entity_id = "IKV_ID"
time_variable = "DATUMAANVANG"

df = df_full[[entity_id, target,time_variable]][1:1000]


print(df)
# sns.lineplot(df[1:1000],x=time_variable,y=target,legend=False)
# plt.show()

tr =TimeSeriesToTable(time_column=time_variable,entity_id=entity_id,target_columns=target)
tr.fit(df)

tabular = tr.transform(df)

# test = tr.inverse_transform(tabular)
# print(test)
# print(tabular)
synth = Synth(get_classiefier=CartClassifier.get_classifier,get_regressor=CartRegressor.get_regressor)
synth.fit(tabular,targets=tabular.columns)


syn_data = synth.generate(tabular.shape[0])

result = tr.inverse_transform(syn_data)
print(result)
# print(f"expected rows: {tabular.shape}")

df["synthetic"] = False
result["synthetic"] = True

combined = pd.concat([df.reset_index(drop=True),result.reset_index(drop=True)],axis=0,ignore_index=True)
print(combined)
sns.lineplot(combined,x=time_variable,y=target,legend=True,hue="synthetic")
plt.show()