import os
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from get_dataset import retrieve_training_data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def main():
    # 1. Load dataset
    df = retrieve_training_data().dropna()
    df = df.drop(["id", "event_timestamp"], axis=1)
    X = df.drop(columns=["sales"]).values
    y = df["sales"].values

    # 2. Preprocess
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    # 3. Load hyperparameters from environment
    lr = float(os.getenv("LEARNING_RATE", "0.1"))
    max_depth = int(os.getenv("MAX_DEPTH", "6"))
    num_round = int(os.getenv("NUM_ROUND", "50"))
    model_version = os.getenv("MODEL_VERSION", "unspecified")
    final_model = os.getenv("FINAL_MODEL", "no").lower()  # should be 'yes' to trigger MLflow

    # print(f"Using hyperparameters: learning_rate={lr}, max_depth={max_depth}, num_round={num_round}, model_version={model_version}, FinalModel={final_model}")

    params = {
        "objective": "reg:squarederror",
        "eta": lr,
        "max_depth": max_depth,
        "tree_method": "hist"
    }

    # 4. Train
    bst = xgb.train(params=params, dtrain=dtrain, num_boost_round=num_round)

    # 5. Evaluate
    preds = bst.predict(dtest)
    rmspe = np.sqrt(np.mean(((y_test - preds) / (y_test + 1e-6)) ** 2))
    print(f"RMSPE={rmspe:.3f}", flush=True)

    if final_model == "yes":
        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow.default.svc.cluster.local:8585")
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        
        mlflow_experiment = os.getenv("MLFLOW_EXP", 'xgboost')
        mlflow.set_experiment(mlflow_experiment)
        
        # 6. MLflow tracking
        with mlflow.start_run():
            mlflow.log_param("learning_rate", lr)
            mlflow.log_param("max_depth", max_depth)
            mlflow.log_param("num_round", num_round)
            mlflow.log_param("model_version", model_version)
            mlflow.set_tag("model_version", model_version)
            mlflow.log_metric("rmspe", rmspe)
            mlflow.xgboost.log_model(bst, artifact_path=f"models/{model_version}")
    else:
        print("FinalModel != 'yes'; skipping MLflow logging.")


if __name__ == "__main__":
    main()