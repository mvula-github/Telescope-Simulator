# Re-run forecast creation without using caas_jupyter_tools display (to avoid import issues).
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression

months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
data = {
    "Month": months*3,
    "Year": [1]*12 + [2]*12 + [3]*12,
    "Demand": [
        500,480,520,550,580,450,420,430,700,750,780,650,
        520,500,540,560,590,460,430,440,720,770,800,670,
        510,495,530,555,585,455,425,435,710,760,790,660
    ]
}
df = pd.DataFrame(data)
df['MonthNum'] = list(range(1,13))*3
df['TimeIndex'] = np.arange(len(df)) + 1  # 1..36

# Simple seasonal method
month_means = df.groupby('Month')['Demand'].mean().reindex(months)
overall_month_mean = month_means.mean()
seasonal_index_simple = (month_means / overall_month_mean).rename('SeasonalIndex_Simple')
year_totals = df.groupby('Year')['Demand'].sum().reset_index()
X_year = year_totals[['Year']].values
y_tot = year_totals['Demand'].values
model_year = LinearRegression().fit(X_year, y_tot)
year4_total_pred = model_year.predict(np.array([[4]]))[0]
month_mean_year4 = year4_total_pred / 12.0
forecast_simple = (month_mean_year4 * seasonal_index_simple).rename('Forecast_Simple').round(1)

# MA multiplicative method
ts = df['Demand'].values
ma12 = pd.Series(ts).rolling(window=12, center=False).mean().values
ma12_centered = (pd.Series(ma12).rolling(window=2, center=False).mean().values)
df_ts = pd.DataFrame({
    'Demand': ts,
    'MA12': ma12,
    'MA12_centered': ma12_centered
})
df_ts['Month'] = df['Month'].values
df_ts['Year'] = df['Year'].values
df_ts['TimeIndex'] = df['TimeIndex']

df_ts['SeasonalRatio'] = df_ts['Demand'] / df_ts['MA12_centered']
valid = df_ts[np.isfinite(df_ts['SeasonalRatio'])]
seasonal_index_unadj = valid.groupby('Month')['SeasonalRatio'].mean().reindex(months)
seasonal_index = (seasonal_index_unadj / seasonal_index_unadj.mean()).rename('SeasonalIndex_MA')

df['SeasonalIndex_MA'] = df['Month'].map(seasonal_index)
df['Deseasonalized'] = df['Demand'] / df['SeasonalIndex_MA']

X_time = df[['TimeIndex']].values
y_des = df['Deseasonalized'].values
trend_model = LinearRegression().fit(X_time, y_des)
future_time = np.arange(37, 49).reshape(-1,1)
deseasonal_forecast = trend_model.predict(future_time)
seasonal_vals_future = seasonal_index.values
forecast_ma = (deseasonal_forecast * seasonal_vals_future).round(1)
forecast_ma_series = pd.Series(forecast_ma, index=months, name='Forecast_MA')

simple_table = pd.DataFrame({
    'Month': months,
    'MonthMean': month_means.values.round(1),
    'SeasonalIndex_Simple': seasonal_index_simple.values.round(4),
    'Forecast_Simple': forecast_simple.values
})

ma_table = pd.DataFrame({
    'Month': months,
    'SeasonalIndex_MA': seasonal_index.values.round(4),
    'Forecast_MA': forecast_ma_series.values
})

compare = pd.merge(simple_table[['Month','Forecast_Simple']], ma_table[['Month','Forecast_MA']], on='Month')
compare['Forecast_Simple'] = compare['Forecast_Simple'].astype(float)
compare['Forecast_MA'] = compare['Forecast_MA'].astype(float)
compare['Difference'] = (compare['Forecast_MA'] - compare['Forecast_Simple']).round(1)
total_simple = compare['Forecast_Simple'].sum()
total_ma = compare['Forecast_MA'].sum()

out_path = Path('/mnt/data/forecast_year4.xlsx')
with pd.ExcelWriter(out_path) as writer:
    simple_table.to_excel(writer, sheet_name='Simple_Seasonal', index=False)
    ma_table.to_excel(writer, sheet_name='MA_Seasonal', index=False)
    compare.to_excel(writer, sheet_name='Comparison', index=False)
    df.to_excel(writer, sheet_name='Input_3years', index=False)

# Output summary for the chat
result = {
    "compare_table": compare,
    "total_simple": float(total_simple),
    "total_ma": float(total_ma),
    "excel_path": out_path.as_posix(),
    "year4_total_pred_simple_method": float(year4_total_pred)
}
result

