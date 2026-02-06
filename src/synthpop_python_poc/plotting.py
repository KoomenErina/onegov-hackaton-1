import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

def plot_spsme(df, save_path = None):
    """
    Parameters
    -----------
    df : pandas.DataFrame
        DataFrame met kolommen ['var1', 'var2', 'S_pMSE']
    save_path : string
    """

    variables = sorted(set(df['var1']).union(df['var2']))

    mat = pd.DataFrame(
        data=np.nan,
        index=variables,
        columns=variables
    )

    for _, row in df.iterrows():
        v1, v2, val = row['var1'], row['var2'], row['S_pMSE']
        mat.loc[v1, v2] = val
        mat.loc[v2, v1] = val

    data = mat.values

    bounds = [0, 3, 10, 30, 100, np.nanmax(data[np.isfinite(data)]) + 1]
    colors = ['darkgreen', 'lightgreen', 'yellow', 'orange', 'red']
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, cmap.N)

    plt.figure(figsize=(8, 5))
    im = plt.imshow(data, cmap=cmap, norm=norm)
    plt.xticks(range(len(variables)), variables, rotation=90)
    plt.yticks(range(len(variables)), variables)
    
    cbar = plt.colorbar(im, ticks=[1.5, 6.5, 20, 65, 110])
    cbar.ax.set_yticklabels(['0-3', '3-10', '10-30', '30-100', '>100'])
    cbar.set_label('S_pMSE')

    plt.title('Heatmap S_pSME')
    plt.tight_layout()
    plt.show()


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os

sns.set_style(style="whitegrid")
def plot_univariate_distributions(obs_df, syn_df, target_folder=None):
    for col in obs_df.columns:
        nan_orig = obs_df[col].isna().sum()
        nan_syn = syn_df[col].isna().sum()

        plt.figure(figsize=(8, 5))

        if pd.api.types.is_numeric_dtype(obs_df[col]):
            combined_data = pd.concat([obs_df[col], syn_df[col]])
            if pd.api.types.is_integer_dtype(combined_data):
                bins = np.arange(combined_data.min() - 0.5, combined_data.max() + 1.5, 1)
            else:
                bins = np.histogram_bin_edges(combined_data.dropna(), bins='auto')

            sns.histplot(obs_df[col], bins=bins, label="Original", stat="density", alpha=0.5)
            sns.histplot(syn_df[col], bins=bins, label="Synthetic", stat="density", alpha=0.5)
            plt.xlabel(col)
            plt.ylabel("Density")
        else:
            orig_counts = (
                obs_df[col]
                .value_counts(normalize=True)
                .rename("Original")
            )

            synth_counts = (
                syn_df[col]
                .value_counts(normalize=True)
                .rename("Synthetic")
            )

            plot_df = pd.concat([orig_counts, synth_counts], axis=1).fillna(0)

            plot_df.plot(
                kind="bar",
                ax=plt.gca(),
                alpha=0.8
            )

            plt.xticks(rotation=45)
            plt.xlabel(col)
            plt.ylabel("Density")
            
        plt.title(f"Univariate distribution: {col}")
        plt.figtext(0.5, 0, f"NaNs - Original: {nan_orig} | Synthetic: {nan_syn}", ha="center", fontsize = 8)
        plt.legend()
        plt.tight_layout()

        if target_folder is not None:
            os.makedirs(target_folder, exist_ok=True)
            file_path = os.path.join(target_folder, f"{col}.png")
            plt.savefig(file_path, dpi=300, bbox_inches="tight")

        plt.show()