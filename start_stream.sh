#/bin/bash
export PYSPARK_PYTHON=python3.8
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 ~/PycharmProjects/eventsService/pyspark/stream.py
