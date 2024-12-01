import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def display_table(rank_metric, embedding_type, checkpoint_name, show_percentage=True):
    # Reading the data
    df_cscs = pd.read_csv(f"outs/cscs_scores_OR/cscs_scores_{embedding_type}_{checkpoint_name}.csv")
    # delete part after _ in the name
    df_cscs['name'] = df_cscs['name'].str.split('_').str[0]
    df_cscs['rank_by_sc'] = df_cscs['sc_per'].rank(ascending=False)
    df_cscs['rank_by_gr'] = df_cscs['gr_per'].rank(ascending=False)
    df_cscs['rank_by_N'] = df_cscs['N'].rank(ascending=False) # N is the number of mutations with ng < gr and nc < sc
    df_cscs['rank_by_cscs_per'] = df_cscs['cscs_per'].rank(ascending=False)
    df_cscs['rank_by_scgr'] = df_cscs["rank_by_sc"] + df_cscs["rank_by_gr"]


    # Prepare data for the merged table
    top_k_values = [100, 500, 1000]

    row_data = []
    for k in top_k_values:
        #df_topk = df_cscs.sort_values(by=rank_metric, ascending=(True if "gr" in rank_metric else False)).head(k)
        df_topk = df_cscs.sort_values(by=rank_metric, ascending=True).head(k)
        # Count the number of each source in the top-K
        eris_count = df_topk[df_topk['name'] == 'eris'].shape[0]
        new_count = df_topk[df_topk['name'] == 'new'].shape[0]
        gpt_count = df_topk[df_topk['name'] == 'gpt'].shape[0]

        if show_percentage:
            eris_count = eris_count / k * 100
            new_count = new_count / k * 100
            gpt_count = gpt_count / k * 100
            row_data.extend([f'{eris_count:.1f}', f'{new_count:.1f}', f'{gpt_count:.1f}'])
        else:
            row_data.extend([eris_count, new_count, gpt_count])

    # Create multi-level columns
    columns = pd.MultiIndex.from_product(
        [[f'Top-{k}' for k in top_k_values], ['Eris', 'New', 'GPT']],
        names=['Top-K', 'Source']
    )

    # Create the DataFrame with multi-level columns
    merged_table = pd.DataFrame([row_data], columns=columns)

    print(f"\nEmbedding type: {embedding_type}, Checkpoint: {checkpoint_name}, Rank metric: {rank_metric}")
    print(merged_table)
    return merged_table

wt_table_cov   = display_table(rank_metric='rank_by_scgr', embedding_type='wt', checkpoint_name='cov', show_percentage=True)
avg_table_cov  = display_table(rank_metric='rank_by_scgr', embedding_type='avg', checkpoint_name='cov', show_percentage=True)
wt_table_omic  = display_table(rank_metric='rank_by_scgr', embedding_type='wt', checkpoint_name='omic', show_percentage=True)
avg_table_omic = display_table(rank_metric='rank_by_scgr', embedding_type='avg', checkpoint_name='omic', show_percentage=True)


print("\n")
row_name_wt_cov  = "BiLSTM (\\texttt{{WT}}) &"
row_name_avg_cov = "BiLSTM (\\texttt{{AVG}}) &"
row_name_wt_omic = "BiLSTM$^+$ (\\texttt{{WT}}) &"
row_name_avg_omic= "BiLSTM$^+$ (\\texttt{{AVG}}) &"

# print rows of each table. add & between cell values
print("Percentages for Eris:")
selected_indices = [0,3,6]
print(row_name_wt_cov.format(), '\% & '.join(map(str, [wt_table_cov.values[0][j] for j in selected_indices])) + "\% \\\\")
print(row_name_avg_cov.format(), '\% & '.join(map(str, [avg_table_cov.values[0][j] for j in selected_indices])) + "\% \\\\")
print(row_name_wt_omic.format(), '\% & '.join(map(str, [wt_table_omic.values[0][j] for j in selected_indices])) + "\% \\\\")
print(row_name_avg_omic.format(), '\% & '.join(map(str, [avg_table_omic.values[0][j] for j in selected_indices])) + "\% \\\\")



# # make name uppercase
# df_cscs_avg['name'] = df_cscs_avg['name'].str.upper()
# df_cscs_wt['name'] = df_cscs_wt['name'].str.upper()

# # Plotting the boxplots
# plt.figure(figsize=(10, 5))

# ax3 = plt.subplot(1, 2, 1)
# df_cscs_wt.boxplot(column=METRIC, by='name', ax=ax3)
# plt.title(f'{METRIC.upper()} based on WT')
# plt.suptitle('')
# plt.xlabel('')
# plt.ylabel('')



# # Plot boxplots for CSCS
# ax4 = plt.subplot(1, 2, 2)
# df_cscs_avg.boxplot(column=METRIC, by='name', ax=ax4)
# plt.title(f'{METRIC.upper()} based on AVG')
# plt.suptitle('')
# plt.xlabel('')
# plt.ylabel('')

# # Font size settings
# font_size = 16
# plt.rc('font', size=font_size)
# plt.rc('axes', titlesize=font_size)
# plt.rc('axes', labelsize=font_size)
# plt.rc('xtick', labelsize=font_size)
# plt.rc('ytick', labelsize=font_size)
# plt.rc('legend', fontsize=font_size)
# plt.rc('figure', titlesize=font_size)

# plt.tight_layout(rect=[0, 0.03, 1, 1.03])
# fig_file_name = f"outs/cscs_{checkpoint_name}_{METRIC}.pdf"
# plt.savefig(fig_file_name)
# plt.show()
