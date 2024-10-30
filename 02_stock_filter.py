import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

today = datetime.today().strftime('%Y_%m_%d')
roce_df = pd.read_csv("stock_financials/ROCE_Ratios_recent.csv")
roce_df.drop_duplicates(subset='ticker', inplace=True)

## Percential Ranking

rank_variable = '2024'
#roce_df['roce_rank'] = roce_df.groupby('Industry')[rank_variable].rank(method='dense', ascending=False)
roce_df['roce_rank'] = roce_df[rank_variable].rank(ascending=False)

## Regression

df = roce_df[[ '2014', '2015', '2016', '2017',
       '2018', '2019', '2020', '2021', '2022', '2023', '2014']]

def cal_coef(X,y):
    """Function to calculate coefficients or w or theta or b0 & b1"""
    coeffs = np.dot(np.linalg.inv(np.dot(X.T,X)),np.dot(X.T,y)) #
    
    #Similar way to calculate coeffs
    # coeffs = np.linalg.inv(X.T.dot(X)).dot(X.T).dot(y)
    return coeffs
  
def predict_normeq(new_x,coeffs):
    """Function to predict linear regression using normal equation"""
    
    new_y = np.dot(new_x, coeffs)
    return new_y
  

reg_results = {"ticker":[],
              "coef":[],
              "r_squared":[],
              "std":[]}

for i in roce_df['ticker']:
    df = roce_df[roce_df['ticker'] == i]
    df = df[['2014', '2015', '2016', '2017',
       '2018', '2019', '2020', '2021', '2022', '2023', '2024']]
    
    regression_df = df.transpose()
    regression_df.reset_index(inplace=True)
    regression_df.columns = ['year', 'roce']
    regression_df['year'] = regression_df['year'].astype(int)
    
    # Drop rows where ROCE is NA
    regression_df = regression_df.dropna(subset=['roce'])
    
    # Only proceed with regression if we have enough data points
    if len(regression_df) >= 2:  # Need at least 2 points for regression
        X = np.column_stack([np.ones(len(regression_df), dtype=np.float32), regression_df['year'].values])
        y = regression_df['roce']
        
    else:
        print(f"Insufficient data points for ticker {i} after removing NA values")

    coeffs = cal_coef(X,y) # b0-intercept, b1-slope
    slope = coeffs[1]
    normeq_preds = predict_normeq(X,coeffs)

    ## Model Evaluation
    SSE = sum((y-normeq_preds)**2) # Sum of squared error
    SST = sum((y-np.mean(y))**2) # Sum of squared total
    R_squared = 1-(SSE/SST) # R Square

    std = np.std(y)
    
    reg_results['ticker'].append(i)
    reg_results['coef'].append(slope)
    reg_results['r_squared'].append(R_squared)
    reg_results['std'].append(std)
    
reg_results = pd.DataFrame(reg_results)

#reg_results['coef'] = np.where(reg_results['r_squared'] < 0.15, 0, reg_results['coef'])
reg_results['coef_w'] = reg_results['coef'] * reg_results['r_squared']

reg_results['coef_rank'] = reg_results['coef_w'].rank(ascending=False)
reg_results['std_rank'] = reg_results['std'].rank(ascending=True)

roce_df = roce_df.merge(reg_results, left_on='ticker', right_on='ticker')

#long-term can build regression to find the best weights
roce_wt = 0.35
growth_wt = 0.65
std_wt = 0.0

roce_df['average_score'] = ((growth_wt *roce_df['coef_rank'] ) + 
                            (roce_wt * roce_df['roce_rank'] ) + 
                            (std_wt * roce_df['std_rank'])) / 3
roce_df['final_rank'] = roce_df['average_score'].rank(ascending=True)

roce_df.to_csv(f'stock_scores/stock_score_data_{today}.csv')
roce_df.to_csv(f'stock_scores/stock_score_data_recent.csv')