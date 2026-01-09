
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

def train_models():
    """
    Trains models for Timeline Delay and Cost Overrun using IT Project Data with NLP features.
    """
    data_path = 'data/it_projects.csv'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run data_gen.py first.")
        return

    df = pd.read_csv(data_path)
    
    # Features & Targets
    # Drop targets and non-predictive columns if any
    X = df.drop(columns=['actual_delay_days', 'cost_overrun_percent'])
    y_delay = df['actual_delay_days']
    y_cost = df['cost_overrun_percent']
    
    # Preprocessing
    categorical_features = ['project_type']
    numeric_features = ['complexity_score', 'number_of_developers', 'team_experience_rating', 
                        'dependency_delay_days', 'resource_availability_ratio', 
                        'labour_cost_index', 'historical_delay_days']
    text_features = 'project_description' # Single text column
    
    # 1. Text Pipeline (TF-IDF)
    text_transformer = Pipeline(steps=[
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=100))
    ])

    # 2. Categorical Pipeline
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    # 3. Numeric Pipeline
    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('txt', text_transformer, text_features),
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # --- Train Timeline Delay Model ---
    print("Training Timeline Delay Model with NLP...")
    delay_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_delay, test_size=0.2, random_state=42)
    delay_model.fit(X_train, y_train)
    
    y_pred = delay_model.predict(X_test)
    rmse_delay = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"Delay Model RMSE: {rmse_delay:.2f}")
    print(f"Delay Model R2: {r2_score(y_test, y_pred):.2f}")
    
    # --- Train Cost Overrun Model ---
    print("\nTraining Cost Overrun Model with NLP...")
    cost_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    X_train_cost, X_test_cost, y_train_cost, y_test_cost = train_test_split(X, y_cost, test_size=0.2, random_state=42)
    cost_model.fit(X_train_cost, y_train_cost)
    
    y_pred_cost = cost_model.predict(X_test_cost)
    rmse_cost = np.sqrt(mean_squared_error(y_test_cost, y_pred_cost))
    print(f"Cost Model RMSE: {rmse_cost:.2f}")
    print(f"Cost Model R2: {r2_score(y_test_cost, y_pred_cost):.2f}")
    
    # Save Artifacts
    os.makedirs('models', exist_ok=True)
    joblib.dump(delay_model, 'models/delay_model.pkl')
    joblib.dump(cost_model, 'models/cost_model.pkl')
    
    print("\nModels saved to models/delay_model.pkl and models/cost_model.pkl")

if __name__ == "__main__":
    train_models()
