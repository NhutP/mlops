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

    print(f"Using hyperparameters: learning_rate={lr}, max_depth={max_depth}, num_round={num_round}, model_version={model_version}")

    params = {
        "objective": "reg:squarederror",
        "eta": lr,
        "max_depth": max_depth,
        "tree_method": "hist"
    }

    # 4. Start MLflow run
    with mlflow.start_run():
        # Log hyperparameters
        mlflow.log_param("learning_rate", lr)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("num_round", num_round)
        mlflow.log_param("model_version", model_version)

        # Optional: log model version as a tag too
        mlflow.set_tag("model_version", model_version)

        # 5. Train
        bst = xgb.train(params=params, dtrain=dtrain, num_boost_round=num_round)

        # 6. Evaluate
        preds = bst.predict(dtest)
        rmspe = np.sqrt(np.mean(((y_test - preds) / (y_test + 1e-6)) ** 2))
        print(f"RMSPE={rmspe:.3f}", flush=True)

        # Log metric
        mlflow.log_metric("rmspe", rmspe)

        # 7. Log model artifact
        mlflow.xgboost.log_model(bst, artifact_path="model")


if __name__ == "__main__":
    main()


# import os
# import numpy as np
# import xgboost as xgb
# # from model.train_hypertune.get_dataset import retrieve_training_data
# from get_dataset import retrieve_training_data
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler

# def main():
#     # 1. Load dataset
#     df = retrieve_training_data().dropna()
#     df = df.drop(["id", "event_timestamp"], axis=1)  # optional
#     X = df.drop(columns=["sales"]).values
#     y = df["sales"].values

#     # 2. Preprocess
#     scaler = StandardScaler()
#     X = scaler.fit_transform(X)
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#     dtrain = xgb.DMatrix(X_train, label=y_train)
#     dtest = xgb.DMatrix(X_test, label=y_test)

#     # 3. Load hyperparameters from environment variables
#     lr = float(os.getenv("LEARNING_RATE", "0.1"))
#     max_depth = int(os.getenv("MAX_DEPTH", "6"))
#     num_round = int(os.getenv("NUM_ROUND", "50"))

#     print(f"Using hyperparameters: learning_rate={lr}, max_depth={max_depth}, num_round={num_round}")

#     params = {
#         "objective": "reg:squarederror",
#         "eta": lr,
#         "max_depth": max_depth,
#         "tree_method": "hist"
#     }

#     # 4. Train model
#     bst = xgb.train(params=params, dtrain=dtrain, num_boost_round=num_round)

#     # 5. Evaluate
#     preds = bst.predict(dtest)
#     rmspe = np.sqrt(np.mean(((y_test - preds) / (y_test + 1e-6)) ** 2))
#     print(f"RMSPE={rmspe:.3f}", flush=True)


# if __name__ == "__main__":
#     main()
