import argparse
import traceback
import pyspark.sql.functions as F
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import *


# define schema for data
schema = StructType([
    StructField('event_time', TimestampType(), True),
    StructField('user_id', IntegerType(), False),
    StructField('app_name', StringType(), False),
    StructField('event_action', StringType(), True),
    StructField('event_category', StringType(), False),
    StructField('event_value', IntegerType(), True)
])


class StreamingPipeline(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.appname = 'kafka_events_consumer'
        self.spark = self._create_session()
        self.logger = self._config_logging()
        self.stream = self._stream()

    def _create_session(self) -> SparkSession:
        spark = (SparkSession.builder
                 .master('local[2]')
                 .appName(self.appname)
                 .getOrCreate())
        return spark

    def _config_logging(self):
        logger = self.spark._jvm.org.apache.log4j.LogManager.getLogger(self.appname)
        logger.info("{} spark app logger initialized......".format(self.appname))
        return logger

    def _stream(self) -> DataFrame:
        # define input stream
        try:
            stream = self.spark.readStream\
                .format('kafka')\
                .option("kafka.bootstrap.servers", self.broker_list)\
                .option("subscribe", self.kafka_topic)\
                .load()
        except:
            raise ConnectionError("Kafka error: Connection refused: \
                                    broker_list={} topic={}".format(self.broker_list, self.kafka_topic))
        return stream

    def process(self) -> None:
        try:
            self.job()
        except Exception as ex:
            print("--> Opps! Is seems an Error!!!", ex)
            self.logger.info("Error encountered: {}".format(str(ex)))
            self.logger.info(str(traceback.format_exc()))

    def job(self) -> None:
        # define transformations for input data stream and write structured data on parquet format
        query = self.stream \
            .select(F.col('value').cast('string').alias('json')) \
            .select(F.from_json('json', schema).alias('data')) \
            .select('data.*')\
            .withColumn('event_date', F.to_date('event_time')) \
            .writeStream \
            .trigger(processingTime='1 minute') \
            .outputMode("append")\
            .partitionBy('event_date')\
            .option("checkpointLocation", self.checkpoint_dir) \
            .option("startingOffsets", "earliest") \
            .option("truncate", "false") \
            .format("parquet")\
            .option("path", self.target_dir) \
            .start()
        query.awaitTermination()


def pipeline_options():
    parser = argparse.ArgumentParser(description='Events_streaming')
    parser.add_argument('--broker_list', action="store", dest="broker_list",
                        default="localhost:9092",
                        help="kafka brokers",
                        required=False)
    parser.add_argument('--kafka_topic', action="store", dest="kafka_topic",
                        default="events",
                        help="set kafka topic name to consume messages",
                        required=False)
    parser.add_argument('--checkpoint_dir', action="store", dest="checkpoint_dir",
                        default="/tmp/checkpoint",
                        help="checkpoint_dir: directory to set checkpoint for streaming app",
                        required=False)
    parser.add_argument('--target_dir', action="store", dest="target_dir",
                        default="/tmp/consumed_events",
                        help="target_dir: directory to save output data",
                        required=False)
    args = parser.parse_args()
    options = vars(args)
    return options


def main():
    # parse args from command line
    options = pipeline_options()
    # create pipeline instance and start stream processing
    pipeline = StreamingPipeline(**options)
    pipeline.process()


if __name__ == '__main__':
    main()
