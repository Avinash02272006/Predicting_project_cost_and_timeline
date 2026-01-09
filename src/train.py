
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report

def train_models():
    """
    Master Training Script.
    Trains:
    1. Timeline Delay Model (Regressor)
    2. Cost Overrun Model (Regressor)
    3. Improvement Suggestion Model (Classifier)
    """
    data_path = 'data/it_projects.csv'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run data_gen.py first.")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # --- Features & Targets ---
    X = df.drop(columns=['actual_delay_days', 'cost_overrun_percent', 'primary_recommendation'])
    y_delay = df['actual_delay_days']
    y_cost = df['cost_overrun_percent']
    y_suggestion = df['primary_recommendation']
    
    # --- Preprocessing Pipelines ---
    categorical_features = ['project_type']
    numeric_features = ['complexity_score', 'number_of_developers', 'team_experience_rating', 
                        'dependency_delay_days', 'resource_availability_ratio', 
                        'labour_cost_index', 'historical_delay_days']
    text_features = 'project_description'
    
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
    
    # --- 1. Train Delay Model (Regressor) ---
    print("\n--- Training Timeline Delay Model ---")
    delay_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_delay, test_size=0.2, random_state=42)
    delay_model.fit(X_train, y_train)
    
    y_pred = delay_model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"Delay Model RMSE: {rmse:.2f} Days")
    print(f"Delay Model R2: {r2_score(y_test, y_pred):.2f}")
    
    # --- 2. Train Cost Model (Regressor) ---
    print("\n--- Training Cost Overrun Model ---")
    cost_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cost, test_size=0.2, random_state=42)
    cost_model.fit(X_train_c, y_train_c)
    
    y_pred_c = cost_model.predict(X_test_c)
    rmse_c = np.sqrt(mean_squared_error(y_test_c, y_pred_c))
    print(f"Cost Model RMSE: {rmse_c:.2f}%")
    print(f"Cost Model R2: {r2_score(y_test_c, y_pred_c):.2f}")
    
    # --- 3. Train Suggestion Model (Classifier) ---
    print("\n--- Training Smart Suggestion Model ---")
    suggestion_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X, y_suggestion, test_size=0.2, random_state=42)
    suggestion_model.fit(X_train_s, y_train_s)
    
    y_pred_s = suggestion_model.predict(X_test_s)
    acc = accuracy_score(y_test_s, y_pred_s)
    print(f"Suggestion Model Accuracy: {acc:.2f}")
    print("Classification Report Sample:")
    print(classification_report(y_test_s, y_pred_s)) # Simple print
    
    # --- Save All ---
    os.makedirs('models', exist_ok=True)
    joblib.dump(delay_model, 'models/delay_model.pkl')
    joblib.dump(cost_model, 'models/cost_model.pkl')
    joblib.dump(suggestion_model, 'models/suggestion_model.pkl')
    
    print("\n✅ All models saved to /models")

if __name__ == "__main__":
    train_models()
