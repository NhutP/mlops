# train.py
import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

from model.train_hypertune.get_dataset import retrieve_training_data  # ← import data function

def setup():
    dist.init_process_group(backend="gloo", init_method="env://")

def cleanup():
    dist.destroy_process_group()

class LinearRegressionModel(nn.Module):
    def __init__(self, n_features):
        super().__init__()
        self.linear = nn.Linear(n_features, 1)

    def forward(self, x):
        return self.linear(x)

def main():
    setup()
    rank = dist.get_rank()
    print('-----------------------')
    print(rank)
    print('-----------------------')
    # 1. Get data
    df = retrieve_training_data().dropna()
    df = df.drop(['id', 'event_timestamp'], axis=1)
    X = df.drop(columns=["sales"]).values
    y = df["sales"].values.reshape(-1, 1)

    # 2. Preprocess
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    y = scaler.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)

    # 3. Model
    lr = float(os.getenv("LEARNING_RATE", 0.01))
    epochs = int(os.getenv("EPOCHS", 50))

    model = LinearRegressionModel(X_train.shape[1])
    model = DDP(model)

    criterion = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=lr)

    # 4. Training
    for epoch in range(epochs):
        print(epoch)
        model.train()
        optimizer.zero_grad()
        output = model(X_train)
        loss = criterion(output, y_train)
        loss.backward()
        optimizer.step()

        if rank == 0 and epoch % 10 == 0:
            print(f"Epoch {epoch}: train_loss={loss.item()}")

    # 5. Evaluation
    model.eval()
    with torch.no_grad():
      pred = model(X_test)
      mse = criterion(pred, y_test).item()

      # RMSPE computation
      eps = 1e-6  # avoid division by zero
      percentage_errors = ((y_test - pred) / (y_test + eps)) ** 2
      rmspe = torch.sqrt(percentage_errors.mean()).item()

    if rank == 0:
        print(f"Final MSE: {mse}")
        print(f"RMSPE={rmspe}")  # Katib watches this line

    cleanup()

if __name__ == "__main__":
    main()



# import os
# import torch
# import torch.nn as nn
# import torch.optim as optim
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler
# from sklearn.metrics import mean_squared_error

# from get_dataset import retrieve_training_data  # ← import data function

# class LinearRegressionModel(nn.Module):
#     def __init__(self, n_features):
#         super().__init__()
#         self.linear = nn.Linear(n_features, 1)

#     def forward(self, x):
#         return self.linear(x)

# def main():
#     # 1. Get data
#     df = retrieve_training_data().dropna()
#     df = df.drop(['id', 'event_timestamp'], axis=1)

#     X = df.drop(columns=["sales"]).values
#     y = df["sales"].values.reshape(-1, 1)

#     # 2. Preprocess
#     scaler = StandardScaler()
#     X = scaler.fit_transform(X)
#     y = scaler.fit_transform(y)
#     print('-------------------------')
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#     X_train = torch.tensor(X_train, dtype=torch.float32)
#     y_train = torch.tensor(y_train, dtype=torch.float32)
#     X_test = torch.tensor(X_test, dtype=torch.float32)
#     y_test = torch.tensor(y_test, dtype=torch.float32)

#     # 3. Model
#     lr = float(os.getenv("LEARNING_RATE", 0.01))
#     epochs = int(os.getenv("EPOCHS", 50))

#     model = LinearRegressionModel(X_train.shape[1])
#     criterion = nn.MSELoss()
#     optimizer = optim.SGD(model.parameters(), lr=lr)

#     # 4. Training
#     for epoch in range(epochs):
#         print(epoch)
#         model.train()
#         optimizer.zero_grad()
#         output = model(X_train)
#         loss = criterion(output, y_train)
#         loss.backward()
#         optimizer.step()

#         if epoch % 10 == 0:
#             print(f"Epoch {epoch}: train_loss={loss.item()}")

#     # 5. Evaluation
#     model.eval()
#     with torch.no_grad():
#         pred = model(X_test)
#         mse = criterion(pred, y_test).item()

#         # RMSPE computation
#         eps = 1e-6  # avoid division by zero
#         percentage_errors = ((y_test - pred) / (y_test + eps)) ** 2
#         rmspe = torch.sqrt(percentage_errors.mean()).item()

#     print(f"Final MSE: {mse}")
#     print(f"RMSPE={rmspe}")  # Katib watches this line

# if __name__ == "__main__":
#     main()