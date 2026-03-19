#!/usr/bin/env python3
from pathlib import Path
import random
from zipfile import ZipFile

import torch
from huggingface_hub import hf_hub_download
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "ProsusAI/finbert"
OUTPUT_DIR = Path(__file__).resolve().parent / "models" / "finbert-finetuned"
MAX_LEN = 256
EPOCHS = 3
LEARNING_RATE = 2e-5
BATCH_SIZE = 16
WEIGHT_DECAY = 0.01
SEED = 42


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_phrasebank_rows():
    zip_path = hf_hub_download(
        repo_id="financial_phrasebank",
        filename="data/FinancialPhraseBank-v1.0.zip",
        repo_type="dataset",
    )
    rows = []
    with ZipFile(zip_path) as archive:
        raw_lines = (
            archive.read("FinancialPhraseBank-v1.0/Sentences_AllAgree.txt")
            .decode("latin1")
            .splitlines()
        )
    for line in raw_lines:
        sentence, label = line.rsplit("@", 1)
        rows.append({"sentence": sentence.strip(), "label": label.strip()})
    return rows


def tokenize_rows(rows, tokenizer):
    target_ids = {"positive": 0, "negative": 1, "neutral": 2}
    tokenized_rows = []
    for row in rows:
        encoded = tokenizer(
            row["sentence"],
            truncation=True,
            padding="max_length",
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        tokenized_rows.append(
            {
                "input_ids": encoded["input_ids"].squeeze(0),
                "attention_mask": encoded["attention_mask"].squeeze(0),
                "labels": torch.tensor(target_ids[row["label"]], dtype=torch.long),
            }
        )
    return tokenized_rows


def build_dataloaders(tokenizer):
    rows = load_phrasebank_rows()
    random.Random(SEED).shuffle(rows)
    split_idx = int(len(rows) * 0.8)
    train_rows = rows[:split_idx]
    test_rows = rows[split_idx:]

    train_dataset = tokenize_rows(train_rows, tokenizer)
    test_dataset = tokenize_rows(test_rows, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)
    return train_loader, test_loader


def evaluate(model, dataloader, device):
    model.eval()
    total = 0
    correct = 0
    with torch.no_grad():
        for batch in dataloader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            predictions = outputs.logits.argmax(dim=-1)
            total += batch["labels"].size(0)
            correct += (predictions == batch["labels"]).sum().item()
    return correct / total if total else 0.0


def train():
    set_seed(SEED)
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    print("device:", device)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)

    train_loader, test_loader = build_dataloaders(tokenizer)
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        avg_loss = running_loss / len(train_loader)
        accuracy = evaluate(model, test_loader, device)
        print(f"epoch={epoch + 1} loss={avg_loss:.4f} accuracy={accuracy:.4f}")

    final_accuracy = evaluate(model, test_loader, device)
    print(f"final_accuracy={final_accuracy:.4f}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"saved_model={OUTPUT_DIR}")


if __name__ == "__main__":
    train()
