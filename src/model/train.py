import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from data.encode import load_card_index_dict
from data.dataset import BattlelogDataset
from data.splits import split_dataset
from api.battlelog_balloon import getData
from pathlib import Path


class winPredictor(nn.Module):
    def __init__(self, n_cards: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(n_cards, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.network(x)

def accuracy(predictions, labels):
    predictions = (predictions > 0.5).float()
    correct = (predictions == labels).float()

    return correct.mean().item()

def main():
    getData()

    card_index_dict, n_cards = load_card_index_dict()

    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    dataset = BattlelogDataset(BASE_DIR / "exports/battlelog_balloon.json", card_index_dict, n_cards)
    print(f"dataset size: {len(dataset)}")
    train_set, val_set, test_set = split_dataset(dataset)

    train_loader = DataLoader(train_set, batch_size=36, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=36)
    test_loader = DataLoader(test_set, batch_size=36)



    model = winPredictor(n_cards)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    l1_lambda = 0.0001

    #training loop
    epochs = 10
    for epoch in range(epochs):
        model.train()
        train_losses = []
        train_acc = []

        for xb, yb in train_loader:
            predictions = model(xb)
            loss = criterion(predictions, yb.unsqueeze(1))
            l1_norm = sum(p.abs().sum() for p in model.parameters())
            loss += l1_lambda * l1_norm

            acc = accuracy(predictions, yb.unsqueeze(1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())
            train_acc.append(acc)

        model.eval()
        val_losses = []
        val_acc = []

        with torch.no_grad():
            for xb, yb in val_loader:
                predictions = model(xb)
                loss = criterion(predictions, yb.unsqueeze(1))
                acc = accuracy(predictions, yb.unsqueeze(1))
                val_losses.append(loss.item())
                val_acc.append(acc)

        print(f"Epoch {epoch+1}/{epochs}  "
              f"Train Loss: {sum(train_losses)/len(train_losses):.4f}  "
              f"Train Acc:  {sum(train_acc)/len(train_acc):.4f}  "
              f"Val Loss:   {sum(val_losses)/len(val_losses):.4f}  "
              f"Val Acc:    {sum(val_acc)/len(val_acc):.4f}")

if __name__ == "__main__":
    main()