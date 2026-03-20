#!/usr/bin/env python3
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "training_features.csv"
MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODEL_DIR / "xgboost_signal_model.joblib"

FEATURE_COLUMNS = [
    "price_delta_1d",
    "price_delta_5d",
    "rsi_14",
    "ma_cross",
    "price_vs_ma20",
    "volume_spike_zscore",
    "sentiment_news",
    "sentiment_social",
    "sentiment_divergence",
]

LABEL_TO_INT = {"SELL": 0, "HOLD": 1, "BUY": 2}
INT_TO_LABEL = {value: key for key, value in LABEL_TO_INT.items()}

PARAM_GRID = [
    {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.05},
    {"n_estimators": 100, "max_depth": 4, "learning_rate": 0.05},
    {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05},
    {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.1},
]


def load_dataset():
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = df.sort_values(["date", "ticker"]).reset_index(drop=True)
    df = df.dropna(subset=FEATURE_COLUMNS + ["label"])
    return df


def make_model(params):
    return XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=1,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        **params,
    )


def compute_sample_weights(labels):
    counts = labels.value_counts().to_dict()
    total = len(labels)
    num_classes = len(counts)
    class_weights = {
        class_id: total / (num_classes * count)
        for class_id, count in counts.items()
    }
    return labels.map(class_weights), class_weights


def walk_forward_splits(unique_dates, n_splits=5):
    total_dates = len(unique_dates)
    if total_dates < n_splits + 1:
        raise ValueError("Not enough unique dates for walk-forward splits")

    fold_size = total_dates // (n_splits + 1)
    if fold_size == 0:
        raise ValueError("Fold size is zero; dataset is too small")

    splits = []
    for fold in range(1, n_splits + 1):
        train_end = fold * fold_size
        test_end = min((fold + 1) * fold_size, total_dates)
        train_dates = unique_dates[:train_end]
        test_dates = unique_dates[train_end:test_end]
        if len(test_dates) == 0:
            continue
        splits.append((train_dates, test_dates))
    return splits


def directional_accuracy(y_true, y_pred):
    directional_mask = y_true != LABEL_TO_INT["HOLD"]
    if directional_mask.sum() == 0:
        return 0.0
    return accuracy_score(y_true[directional_mask], y_pred[directional_mask])


def evaluate_params(df, params):
    unique_dates = sorted(df["date"].dt.strftime("%Y-%m-%d").unique())
    splits = walk_forward_splits(unique_dates, n_splits=5)
    fold_metrics = []

    for train_dates, test_dates in splits:
        train_mask = df["date"].dt.strftime("%Y-%m-%d").isin(train_dates)
        test_mask = df["date"].dt.strftime("%Y-%m-%d").isin(test_dates)

        train_df = df.loc[train_mask]
        test_df = df.loc[test_mask]

        X_train = train_df[FEATURE_COLUMNS]
        y_train = train_df["label"].map(LABEL_TO_INT)
        X_test = test_df[FEATURE_COLUMNS]
        y_test = test_df["label"].map(LABEL_TO_INT)
        sample_weight, class_weights = compute_sample_weights(y_train)

        model = make_model(params)
        model.fit(X_train, y_train, sample_weight=sample_weight)
        predictions = model.predict(X_test)

        baseline_prediction = [LABEL_TO_INT["HOLD"]] * len(y_test)
        fold_metrics.append(
            {
                "accuracy": accuracy_score(y_test, predictions),
                "baseline_accuracy": accuracy_score(y_test, baseline_prediction),
                "directional_accuracy": directional_accuracy(y_test.to_numpy(), predictions),
                "class_weights": class_weights,
            }
        )

    mean_accuracy = sum(item["accuracy"] for item in fold_metrics) / len(fold_metrics)
    mean_baseline = sum(item["baseline_accuracy"] for item in fold_metrics) / len(fold_metrics)
    mean_directional = sum(item["directional_accuracy"] for item in fold_metrics) / len(fold_metrics)
    return {
        "params": params,
        "fold_metrics": fold_metrics,
        "mean_accuracy": mean_accuracy,
        "mean_baseline_accuracy": mean_baseline,
        "mean_directional_accuracy": mean_directional,
    }


def train_final_model(df, params):
    X = df[FEATURE_COLUMNS]
    y = df["label"].map(LABEL_TO_INT)
    sample_weight, class_weights = compute_sample_weights(y)
    model = make_model(params)
    model.fit(X, y, sample_weight=sample_weight)
    return model, class_weights


def main():
    df = load_dataset()
    print(f"training rows={len(df)}")
    print(f"date range={df['date'].min().date()} to {df['date'].max().date()}")

    results = [evaluate_params(df, params) for params in PARAM_GRID]
    best_result = max(results, key=lambda item: item["mean_accuracy"])

    print("walk_forward_results")
    for result in results:
        print(
            "params="
            f"{result['params']} "
            f"mean_accuracy={result['mean_accuracy']:.4f} "
            f"baseline_accuracy={result['mean_baseline_accuracy']:.4f} "
            f"directional_accuracy={result['mean_directional_accuracy']:.4f}"
        )

    final_model, class_weights = train_final_model(df, best_result["params"])
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "feature_columns": FEATURE_COLUMNS,
            "label_to_int": LABEL_TO_INT,
            "int_to_label": INT_TO_LABEL,
            "best_params": best_result["params"],
            "class_weights": class_weights,
            "metrics": {
                "walk_forward_accuracy": best_result["mean_accuracy"],
                "walk_forward_baseline_accuracy": best_result["mean_baseline_accuracy"],
                "walk_forward_directional_accuracy": best_result["mean_directional_accuracy"],
            },
        },
        MODEL_PATH,
    )

    print(f"best_params={best_result['params']}")
    print(f"best_walk_forward_accuracy={best_result['mean_accuracy']:.4f}")
    print(f"best_walk_forward_baseline_accuracy={best_result['mean_baseline_accuracy']:.4f}")
    print(f"best_walk_forward_directional_accuracy={best_result['mean_directional_accuracy']:.4f}")
    print(f"class_weights={class_weights}")
    print(f"saved_model={MODEL_PATH}")


if __name__ == "__main__":
    main()
