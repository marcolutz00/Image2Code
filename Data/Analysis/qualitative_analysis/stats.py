from scipy.stats import pearsonr, spearmanr

def correlation(df, groupby_col, x_col, y_col):
    # groupby_col = "model", x_col = "amount_nodes", y_col = "amount_landmark_violations"
    for name, values in df.groupby(groupby_col):
        pearson_correlation, pearson_p = pearsonr(values[x_col], values[y_col])
        spearman_correlation, spearman_p = spearmanr(values[x_col], values[y_col])

        print(f"{name}  Pearson correlation ={pearson_correlation} with p={pearson_p} and Spearman correlation ={spearman_correlation} with p= {spearman_p}")


def get_all_violations(accessibility_data, issue_name, full_output=False):
    """
    Get the amount of landmark violations
    """
    violations = 0
    for issue in accessibility_data.get("automatic", []):
        if issue_name:
            if issue.get("name") == issue_name:
                return issue if full_output else issue.get("amount_nodes_failed", 0)
        else: 
            violations += issue.get("amount_nodes_failed", 0)
    return [] if full_output else violations