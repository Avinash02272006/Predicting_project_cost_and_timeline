import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from math import sqrt

# -----------------------------
# Sample Dataset (Realistic Values)
# Columns: [complexity (1-5), team_size, num_features]
# Targets: [total_cost (₹), timeline_weeks]
# Complexity: 1 = very simple, 5 = very complex
# -----------------------------

X = np.array([
    [1, 1, 2],    # Very simple solo project
    [1, 2, 3],    # Simple small team
    [2, 2, 5],    # Slightly more complex
    [2, 3, 6],
    [3, 3, 8],
    [3, 4, 10],
    [4, 4, 12],
    [4, 5, 15],
    [5, 5, 18],   # Complex medium team
    [5, 6, 20],   # Large complex project
], dtype=float)

# Realistic cost (in INR) and timeline (weeks)
y = np.array([
    [20000, 2],
    [35000, 3],
    [50000, 4],
    [65000, 5],
    [90000, 6],
    [120000, 8],
    [160000, 10],
    [210000, 12],
    [280000, 16],
    [350000, 20]
], dtype=float)

# -----------------------------
# Split Data
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# -----------------------------
# Train RandomForest Model
# -----------------------------
model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

# -----------------------------
# Evaluate Model
# -----------------------------
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = sqrt(mean_squared_error(y_test, y_pred))
print(f"✅ Model trained | MAE: ₹{mae:.2f} | RMSE: ₹{rmse:.2f}")

# -----------------------------
# Save Model
# -----------------------------
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_file = os.path.join(model_dir, "project_model.joblib")
joblib.dump(model, model_file)
print(f"✅ Model saved at {model_file}")
