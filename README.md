# Clash Royale Win/Loss Predictor with PyTorch

## Overview

This project trains a PyTorch model to predict whether a player using a 2.9 Balloon cycle deck will win or lose against a given opponent deck. The model only sees the opponent's deck, so it learns which matchups are favorable or unfavorable for Balloon cycle.

The tracked deck is: Musketeer, Skeletons, Giant Snowball, Bomb Tower, Balloon, Miner, Ice Golem, Barbarian Barrel.

## How it works

### 1. Data collection (`src/api/`)
- `cards.py` pulls the full card list from the official Clash Royale API and saves it to `assets/cards.json`.
- `battlelog_balloon.py` fetches the battle logs of a configured set of players (you plus other top players) and keeps only battles that:
  - are Path of Legend (ranked) matches,
  - were played with the exact Balloon cycle deck above,
  - were against an opponent using a different deck,
  - are not duplicates (identified by player tag + battle time).
- New battles are merged into a growing master log in `assets/`, so the dataset accumulates across runs. Copies are written to `exports/`, split into your own battles and everyone else's.

### 2. Encoding (`src/data/encode.py`)
Each card is assigned an index, and an opponent deck is turned into a multi-hot vector with a 1 for every card the opponent played. Evolutions are treated as separate cards from their base versions, so a card and its evolution each get their own slot.

### 3. Dataset and splits (`src/data/dataset.py`, `src/data/splits.py`)
- `BattlelogDataset` reads the exported battle log and produces `(opponent deck vector, label)` pairs. The label is 1 if the Balloon player took more crowns than the opponent, otherwise 0.
- `split_dataset` does a seeded random split into train, validation and test sets (currently 80% / 20% / 0%).

### 4. Model and training (`src/model/train.py`)
`winPredictor` is a small feed-forward network:

It is trained with binary cross-entropy and the Adam optimizer, plus an L1 penalty on the weights to reduce overfitting on the relatively small dataset. Training and validation loss and accuracy are printed each epoch.

