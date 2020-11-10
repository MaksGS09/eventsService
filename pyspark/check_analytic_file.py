from pyspark.sql import SparkSession


if __name__ == '__main__':
    spark = SparkSession = (SparkSession.builder.master('local[2]').appName('check').getOrCreate())
    check = spark.read.parquet('/tmp/analytic_events/*.parquet').cache()
    check.show(50, False)
    print('-------------------------------------------------------------')
    print("Rows in the result dataset: {}".format(check.count()))
    print('-------------------------------------------------------------')
    check.printSchema()
