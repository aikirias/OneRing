"""Spark ML training pipeline orchestrated from Airflow."""
from __future__ import annotations

import os
from datetime import datetime

import mlflow
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from mlflow.tracking import MlflowClient
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

FEATURE_COLUMNS = [
    "total_transactions",
    "total_spend",
    "avg_transaction_value",
    "spend_last_30d",
]
TARGET_COLUMN = "churned"


def _create_spark_session(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.master("local[*]")
        .appName(app_name)
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )


def _prepare_dataset(spark: SparkSession, data_path: str):
    df = spark.read.csv(data_path, header=True, inferSchema=True)
    assembler = VectorAssembler(inputCols=FEATURE_COLUMNS, outputCol="features")
    transformed = assembler.transform(df)
    dataset = transformed.select(col("features"), col(TARGET_COLUMN).alias("label"))
    return dataset.randomSplit([0.8, 0.2], seed=42)


def run_hyperopt_training(data_path: str, experiment_name: str, model_name: str) -> str:
    spark = _create_spark_session("ChurnTraining")
    train_df, test_df = _prepare_dataset(spark, data_path)
    evaluator = BinaryClassificationEvaluator(metricName="areaUnderROC")

    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    mlflow.set_experiment(experiment_name)
    mlflow.spark.autolog(log_models=False)

    def objective(params):
        with mlflow.start_run(nested=True) as run:
            lr = LogisticRegression(
                featuresCol="features",
                labelCol="label",
                maxIter=int(params["max_iter"]),
                regParam=float(params["reg_param"]),
                elasticNetParam=float(params["elastic_net"]),
            )
            model = lr.fit(train_df)
            predictions = model.transform(test_df)
            auc = evaluator.evaluate(predictions)
            mlflow.log_metric("auc", auc)
            mlflow.log_params(
                {
                    "max_iter": int(params["max_iter"]),
                    "reg_param": float(params["reg_param"]),
                    "elastic_net": float(params["elastic_net"]),
                }
            )
            mlflow.spark.log_model(model, artifact_path="model")
            return {"loss": -auc, "status": STATUS_OK, "run_id": run.info.run_id}

    search_space = {
        "max_iter": hp.quniform("max_iter", 20, 150, 10),
        "reg_param": hp.loguniform("reg_param", -4, 0),
        "elastic_net": hp.uniform("elastic_net", 0.0, 1.0),
    }

    trials = Trials()
    best = fmin(fn=objective, space=search_space, algo=tpe.suggest, max_evals=20, trials=trials)
    best_trial = min(trials.results, key=lambda r: r["loss"])
    best_run_id = best_trial.get("run_id")

    with mlflow.start_run(run_name="best_model") as best_run:
        lr = LogisticRegression(
            featuresCol="features",
            labelCol="label",
            maxIter=int(best["max_iter"]),
            regParam=float(best["reg_param"]),
            elasticNetParam=float(best["elastic_net"]),
        )
        model = lr.fit(train_df)
        predictions = model.transform(test_df)
        auc = evaluator.evaluate(predictions)
        mlflow.log_metric("auc", auc)
        mlflow.log_params(
            {
                "max_iter": int(best["max_iter"]),
                "reg_param": float(best["reg_param"]),
                "elastic_net": float(best["elastic_net"]),
            }
        )
        mlflow.spark.log_model(model, artifact_path="model")
        model_uri = f"runs:/{best_run.info.run_id}/model"
        registered_model = mlflow.register_model(model_uri, model_name)

    client = MlflowClient()
    client.transition_model_version_stage(
        name=model_name,
        version=registered_model.version,
        stage="Staging",
        archive_existing_versions=True,
    )
    spark.stop()
    return best_run_id or ""


def main():
    data_path = os.environ.get("FEAST_REFERENCE_DATA_PATH", "/opt/airflow/storage/data/ml")
    csv_path = os.path.join(data_path, "customer_transactions.csv")
    experiment_name = "customer_churn_experiment"
    model_name = os.environ.get("MLFLOW_MODEL_NAME", "oner_churn_model")
    run_id = run_hyperopt_training(csv_path, experiment_name, model_name)
    print(f"Training completed. Best run id: {run_id}")


if __name__ == "__main__":
    main()
