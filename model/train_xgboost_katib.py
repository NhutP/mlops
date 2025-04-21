# train.py
import os
import socket
import numpy as np
import xgboost as xgb
from get_dataset import retrieve_training_data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def main():
    # Retrieve environment variables set by DMLC launcher / trainer
    
    # rank = int(os.getenv("RANK", "0"))
    rank = int(os.getenv("OMPI_COMM_WORLD_RANK", "0"))
    world_size = int(os.getenv("DMLC_NUM_WORKER", "1"))
    role = os.getenv("DMLC_ROLE", "worker")
    host = socket.gethostname()
    print(f"#####@@@@@ [{host} | Rank {rank}] Starting with role: {role}, world size: {world_size}")

    # 1. Load dataset (same in all workers)
    df = retrieve_training_data().dropna()
    df = df.drop(["id", "event_timestamp"], axis=1)  # optional
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

    # 4. Train (XGBoost will use Rabit for gradient sync)
    bst = xgb.train(params=params, dtrain=dtrain, num_boost_round=num_round)


    if rank == 0:
        preds = bst.predict(dtest)
        rmspe = np.sqrt(np.mean(((y_test - preds) / (y_test + 1e-6)) ** 2))
        # Print with rounding to 3 decimal places
        print(f"RMSPE={rmspe:.3f}", flush=True)
        


if __name__ == "__main__":
    main()