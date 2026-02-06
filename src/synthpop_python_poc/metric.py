from rpy2 import robjects as ro
from rpy2.robjects.packages import importr
import pyreadr
from rpy2.robjects import pandas2ri
from itertools import combinations
import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype

def spmse_pair(obs_df: pd.DataFrame, syn_df: pd.DataFrame, var1: str, var2: str):
    """
    Compute S-pMSE for one pair of variables using frequency tables.
    """
    N = 2*len(obs_df) 

    # Calculate frequency tables
    f_obs = obs_df.groupby([var1, var2]).size().rename("obs")
    f_syn = syn_df.groupby([var1, var2]).size().rename("syn")

    freq = pd.concat([f_obs, f_syn], axis=1).fillna(0)

    freq["expected"] = (freq["obs"] + freq["syn"]) / 2
    freq["diff"] = freq["obs"] - freq["syn"]

    freq = freq.loc[freq["expected"] > 0]

    # Ratio statistic --> Voas-Wilkinson statistiek volgens synthpop-R
    ratio = np.sum((freq["diff"] ** 2) / freq["expected"])

    df = freq.shape[0]
    #pMSE = ratio * (0.5 ** 3) * (1 / N)
    S_pMSE = ratio / (df - 1) if df > 1 else np.nan

    return {"S_pMSE": S_pMSE}

def pairwise_spmse(obs_df: pd.DataFrame, syn_df: pd.DataFrame, max_groups: int = 25, na_label: str = "__NA__") -> pd.DataFrame:

    if not obs_df.columns.equals(syn_df.columns):
        raise ValueError("Observed and synthetic data must have identical columns")

    obs_prep = obs_df.copy()
    syn_prep = syn_df.copy()

    for col in obs_df.columns:
        # prepare bins for numeric columns
        if is_numeric_dtype(obs_df[col]):
            pooled = pd.concat([obs_df[col], syn_df[col]], axis=0)
            if pooled.nunique(dropna=True) > max_groups:
                bins = pd.qcut(pooled, q=max_groups, duplicates="drop").cat.categories

                obs_prep[col] = pd.cut(obs_df[col], bins=bins, include_lowest=True)
                syn_prep[col] = pd.cut(syn_df[col], bins=bins, include_lowest=True)

        # treat NA as a category
        obs_prep[col] = obs_prep[col].astype("object").fillna(na_label)
        syn_prep[col] = syn_prep[col].astype("object").fillna(na_label)


    results = []

    for var1, var2 in combinations(obs_prep.columns, 2):
        stats = spmse_pair(obs_prep, syn_prep, var1, var2)

        results.append({"var1": var1, "var2": var2, **stats})

    return pd.DataFrame(results)
