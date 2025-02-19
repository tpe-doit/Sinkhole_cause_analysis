"""
This module demonstrates a workflow for time series data analysis using XGBoost regression.
It includes data preprocessing, model training, evaluation, and visualization.

Functions:
- time_series_data_etl: Loads and transforms time series data.
- split_time_series_data: Splits time series data into training, validation, and test sets.
- train_xgb_regressor: Trains an XGBoost regressor model.
- evaluate_model_performance: Evaluates the performance of the trained model on test data.
- plot_feature_importance: Plots feature importance based on the trained model.
- plot_actual_vs_predicted: Plots actual vs predicted sinkhole count for visual analysis.

Usage:
To run the module, execute the `main()` function which orchestrates the entire workflow.
"""
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor, plot_importance

class TrainTimeSeries:
    def __init__(
            self, 
            download_folder="data/raw_data", 
            export_folder="data/preprocessed_data", 
            output_folder="output/time_series"
        ):
        self.download_folder = download_folder
        self.export_folder = export_folder
        self.output_folder = output_folder

    # Load and transform time series data
    def time_series_data_etl(self, file_name="time_series_table_M.csv", trans_col=None):
        """
        Load and transform time series data from a CSV file.

        Parameters:
        - file_name: The name of the CSV file (default: "time_series_table_M.csv").
        - trans_col: List of columns to be transformed to numeric (default: list of specific columns).

        Returns:
        - merged_df: The transformed DataFrame.
        """
        if trans_col is None:
            trans_col = ['sinkhole_count', 'MeanTideLevel', 'MeanHighWaterLevel',
                        'MeanLowWaterLevel', 'earthquake_count', 'total_rain', 'tide_range']
        
        # Construct the full path to the CSV file
        merged_df_path = os.path.join(self.export_folder, file_name)
        
        # Load the CSV file into a DataFrame
        merged_df = pd.read_csv(merged_df_path)
        
        # Check if 'sinkhole_count' column is present
        if 'sinkhole_count' not in merged_df.columns:
            print("Without Sinkhole count column")

            trans_col = ['MeanTideLevel', 'MeanHighWaterLevel', 'MeanLowWaterLevel', 
                        'earthquake_count', 'total_rain', 'tide_range']
            # Convert the 'index' column to datetime
            merged_df['index'] = pd.to_datetime(merged_df['index'])
            
            # Convert specified columns to numeric, handling errors by coercing them to NaN
            for col in trans_col:
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        else:
            # Convert the 'index' column to datetime
            merged_df['index'] = pd.to_datetime(merged_df['index'])
            
            # Convert specified columns to numeric, handling errors by coercing them to NaN
            for col in trans_col:
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        
        return merged_df


    # Rename columns
    def rename_time_series_data(self, merged_df, rename_dict=None):
        """
        Rename columns of time series data from a CSV file.

        Parameters:
        - trans_col: List of columns to be transformed to numeric (default: list of specific columns).
        - rename_dict: Dictionary to rename columns (default: None).

        Returns:
        - merged_df: The transformed and renamed DataFrame.
        """
        
        if rename_dict is None:
            rename_dict = {
                'MeanTideLevel': 'Mean Tide Level', 
                'MeanHighWaterLevel': 'Mean High Water Level',
                'MeanLowWaterLevel': 'Mean Low Water Level', 
                'earthquake_count': 'Earthquake Count', 
                'total_rain': 'Total Rainfall',
                'river_level_baoqiao': 'River Level Baoqiao', 
                'river_level_wanfu': 'River Level Wanfu', 
                'river_level_mean': 'Mean River Level',
                'ugwater_level_bt1': 'Ground Water Level BT1', 
                'ugwater_level_bt2': 'Ground Water Level BT2', 
                'ugwater_level_ntu1': 'Ground Water Level NTU1',
                'ugwater_level_ntu2': 'Ground Water Level NTU2', 
                'ugwater_level_sunn': 'Ground Water Level Sunn', 
                'ugwater_level_dq': 'Ground Water Level DQ',
                'ugwater_level_dh': 'Ground Water Level DH', 
                'ugwater_level_xs': 'Ground Water Level XS', 
                'ugwater_level_qn': 'Ground Water Level QN',
                'ugwater_level_mean': 'Mean Ground Water Level', 
                'tide_range': 'Tide Range',
            }
        
        # Rename columns
        merged_df = merged_df.rename(columns=rename_dict)
        
        return merged_df
    
    # Split time series data
    def split_time_series_data(
            self, 
            merged_df, 
            target_column='sinkhole_count', 
            train_ratio=0.64, 
            val_ratio=0.16
        ):
        """
        Split the time series data into training, validation, and test sets.

        Parameters:
        - merged_df: The DataFrame containing the time series data.
        - target_column: The name of the target column (default: 'sinkhole_count').
        - train_ratio: The ratio of the training set size to the entire data (default: 0.64).
        - val_ratio: The ratio of the validation set size to the entire data (default: 0.16).

        Returns:
        - X_train: Training features.
        - y_train: Training target.
        - X_val: Validation features.
        - y_val: Validation target.
        - X_test: Test features.
        - y_test: Test target.
        """
        # Calculate the number of samples for each set
        train_num = round(len(merged_df) * train_ratio)
        val_num = round(len(merged_df) * (train_ratio + val_ratio))
        test_num = len(merged_df)

        # Split the data
        X_train = merged_df[:train_num].copy()
        X_train.reset_index(drop=True, inplace=True)

        X_val = merged_df[train_num:val_num].copy()
        X_val.reset_index(drop=True, inplace=True)

        X_test = merged_df[val_num:test_num].copy()
        X_test.reset_index(drop=True, inplace=True)

        y_train = merged_df[target_column][:train_num]
        y_train.reset_index(drop=True, inplace=True)

        y_val = merged_df[target_column][train_num:val_num]
        y_val.reset_index(drop=True, inplace=True)

        y_test = merged_df[target_column][val_num:test_num]
        y_test.reset_index(drop=True, inplace=True)

        # Drop the target and index columns from features
        X_train = X_train.drop(columns=['index', target_column])
        X_val = X_val.drop(columns=['index', target_column])
        X_test = X_test.drop(columns=['index', target_column])

        return X_train, y_train, X_val, y_val, X_test, y_test

    # Train an XGBoost model
    def train_xgb_regressor(
            self, X_train, y_train, X_val, y_val, 
            n_estimators=1000, 
            learning_rate=0.01, 
            enable_categorical=True, 
            seed=42
        ):
        """
        Train an XGBRegressor model with the given training and validation data.

        Parameters:
        - X_train: Training features.
        - y_train: Training target.
        - X_val: Validation features.
        - y_val: Validation target.
        - n_estimators: Number of trees in the model (default: 1000).
        - learning_rate: Learning rate (default: 0.01).
        - enable_categorical: Whether to enable categorical data handling (default: True).
        - seed: Random seed (default: 42).

        Returns:
        - reg: The trained XGBRegressor model.
        """
        # Create the model
        reg = XGBRegressor(n_estimators=n_estimators, 
                        learning_rate=learning_rate, 
                        enable_categorical=enable_categorical, 
                        seed=seed)
        
        # Fit the model
        reg.fit(X_train, y_train, 
                eval_set=[(X_train, y_train), (X_val, y_val)], 
                verbose=False)
        
        return reg

    # Evaluate model performance
    def evaluate_model_performance(self, reg, X_test, y_test):
        """
        Evaluate the performance of a trained model on the test set.

        Parameters:
        - reg: The trained regression model.
        - X_test: Test features.
        - y_test: Test target.

        Returns:
        - rmse: Root Mean Squared Error.
        - mae: Mean Absolute Error.
        - r_squared: R-squared score.
        """
        # Predict the target values for the test set
        y_pred = reg.predict(X_test)
        
        # Calculate performance metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r_squared = r2_score(y_test, y_pred)
        
        # Print the performance metrics
        print(f"RMSE: {rmse}")
        print(f'MAE: {mae}')
        print(f'R^2: {r_squared}')
        
        return rmse, mae, r_squared

    # Plot feature importance
    def plot_feature_importance(self, reg, save_fig=False, fig_path='feature_importance.png'):
        """
        Plot feature importance for the sinkhole count model.

        Parameters:
        - reg: The trained regression model.
        - save_fig: Whether to save the feature importance plot (default: False).
        - fig_path: Path to save the figure (default: 'feature_importance.png').

        Returns:
        - fig: The matplotlib figure object.
        - ax: The matplotlib axes object.
        """
        # Plot feature importance
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.rcParams['font.size'] = 16
        _ = plot_importance(
            reg, 
            ax=ax,
            importance_type='weight', 
            height=0.75, 
            color='#D84F4F', 
            grid=False, 
            title='',
            xlabel='Feature importance (F score)', 
            ylabel='',
            max_num_features=10, 
            values_format='{v:.0f}', 
            show_values=False
        )
        
        # Save the feature importance plot if requested
        if save_fig:
            os.makedirs(self.output_folder, exist_ok=True)  # Create output folder if it doesn't exist
            path = os.path.join(self.output_folder, fig_path)
            plt.savefig(path, bbox_inches='tight')
        plt.show()
        
        return fig, ax

    # Create output folder
    def create_output_folder(self):
        """
        Create the output folder if it does not exist.
        """
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        else:
            print("Output folder exists.")

    def plot_actual_vs_predicted(
            self, 
            merged_df, 
            reg, 
            X_test, 
            plot_title='', 
            save_fig=False, 
            fig_path='plot_actual_vs_predicted.png'
        ):
        """
        Plot actual vs predicted sinkhole count.

        Parameters:
        - merged_df: The DataFrame containing the time series data.
        - reg: The trained regression model.
        - X_test: Test features.
        - plot_title: Title of the plot (default: '').
        - save_fig: Whether to save the plot (default: False).
        - fig_path: Path to save the plot (default: 'plot_actual_vs_predicted.png').

        Returns:
        - None
        """
        # Reset index
        merged_df.reset_index(inplace=True)
        merged_df.set_index('index', inplace=True)

        # Split training and test datasets
        df_train = merged_df[:38].copy()
        df_test = merged_df[38:].copy()

        # Predict sinkhole count
        df_test = df_test.copy()  # Avoid SettingWithCopyWarning
        df_test['sinkhole_prediction'] = reg.predict(X_test)

        # Concatenate training and test datasets
        df_all = pd.concat([df_train, df_test], sort=False)

        # Plot actual vs predicted sinkhole count
        plt.figure(figsize=(15, 5))
        plt.plot(df_all.index, df_all['sinkhole_count'], label='Actual Sinkhole Count')
        plt.plot(df_all.index, df_all['sinkhole_prediction'], label='Predicted Sinkhole Count')
        plt.title('Actual vs Predicted Sinkhole Count' if not plot_title else plot_title)
        plt.xlabel('Index')
        plt.ylabel('Sinkhole Count')
        plt.legend()
        plt.grid(True)
        
        # Save the figure
        if save_fig:
            self.create_output_folder()
            path = os.path.join(self.output_folder, fig_path)
            plt.savefig(path)
        
        plt.show()

    def run(self):
        # Load and transform time series data
        merged_df = self.time_series_data_etl(file_name="time_series_table_M.csv", trans_col=None)
        
        # Rename columns
        merged_df = self.rename_time_series_data(merged_df, rename_dict=None)

        if 'sinkhole_count' not in merged_df.columns:
            print("====Without Sinkhole count column, skip model training.====")
            return None
        
        else:
            # Split the time series data
            X_train, y_train, X_val, y_val, X_test, y_test = self.split_time_series_data(merged_df)

            # Train an XGBoost model
            reg = self.train_xgb_regressor(X_train, y_train, X_val, y_val)

            # Evaluate the model performance
            self.evaluate_model_performance(reg, X_test, y_test)

            # Create output folder
            self.create_output_folder()

            # Plot feature importance
            self.plot_feature_importance(reg, save_fig=True)

            # Plot actual vs predicted sinkhole count
            self.plot_actual_vs_predicted(merged_df, reg, X_test, save_fig=True)

if __name__ == '__main__':
    START_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'Data Preprocessing Start at {START_TIME}!\n')

    # Initialize the TrainTimeSeries class
    train_time_series = TrainTimeSeries()

    # Run the main function
    train_time_series.run()

    END_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'\nData Preprocessing Finished at {END_TIME}!')