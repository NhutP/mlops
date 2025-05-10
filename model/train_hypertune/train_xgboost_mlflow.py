import os
import socket
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from datetime import datetime

from model.train_hypertune.get_dataset import retrieve_training_data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def main():
    rank = int(os.getenv("OMPI_COMM_WORLD_RANK", "0"))
    world_size = int(os.getenv("DMLC_NUM_WORKER", "1"))
    role = os.getenv("DMLC_ROLE", "worker")
    host = socket.gethostname()

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")  # UTC timestamp
    print(f"[{host} | Rank {rank}] Starting at {timestamp} with role: {role}, world size: {world_size}")

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

    # 3. Hyperparameters
    lr = float(os.getenv("LEARNING_RATE", "0.1"))
    max_depth = int(os.getenv("MAX_DEPTH", "6"))
    num_round = int(os.getenv("NUM_ROUND", "50"))
    
    params = {
        "objective": "reg:squarederror",
        "eta": lr,
        "max_depth": max_depth,
        "tree_method": "hist"
    }

    # 4. Train
    bst = xgb.train(params=params, dtrain=dtrain, num_boost_round=num_round)

    # 5. Evaluation and MLflow logging (only done in rank 0)
    if rank == 0:
        preds = bst.predict(dtest)
        rmspe = np.sqrt(np.mean(((y_test - preds) / (y_test + 1e-6)) ** 2))
        print(f"RMSPE={rmspe:.3f}", flush=True)

        # Set up MLflow
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
        mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "xgboost-mlflow"))

        run_name = f"xgboost-{timestamp}"

        with mlflow.start_run(run_name=run_name):
            mlflow.log_param("learning_rate", lr)
            mlflow.log_param("max_depth", max_depth)
            mlflow.log_param("num_round", num_round)

            mlflow.log_metric("RMSPE", rmspe)

            mlflow.set_tags({
                "host": host,
                "rank": rank,
                "timestamp": timestamp
            })

            os.makedirs("/output", exist_ok=True)
            local_model_path = f"/output/xgboost_model_{timestamp}.bst"
            # bst.save_model(local_model_path)

            mlflow.xgboost.log_model(bst, artifact_path=f"model_{timestamp}")
            mlflow.log_dict(params, f"params_{timestamp}.json")

if __name__ == "__main__":
    main()
