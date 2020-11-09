import os
import argparse
import traceback
import datetime as dt
import pyspark.sql.functions as F
from pyspark.sql.types import *
from pyspark.sql import SparkSession
from pyspark.sql.window import Window

# define schema for the output data
schema = StructType([
    StructField('event_time', TimestampType(), True),
    StructField('user_id', IntegerType(), False),
    StructField('app_name', StringType(), False),
    StructField('event_action', StringType(), True),
    StructField('event_category', StringType(), False),
    StructField('event_value', IntegerType(), True),
    StructField('u_count', IntegerType(), False),
    StructField('u_mp_ea', StringType(), False)
])


class AnalyticsPipeline(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.appname = 'analytic_events'
        self.spark: SparkSession = (SparkSession.builder.master('local[2]').appName(self.appname).getOrCreate())
        self.logger = self._config_logging()

    def _config_logging(self):
        logger = self.spark._jvm.org.apache.log4j.LogManager.getLogger(self.appname)
        logger.info("{} spark app logger initialized......".format(self.appname))
        return logger

    def process(self):
        try:
            self.job()
        except Exception as ex:
            self.logger.info("Error encountered: {}".format(str(ex)))
            self.logger.info(str(traceback.format_exc()))

    def job(self):
        # read source data and cache it for reuse
        data = self.spark.read.parquet(os.path.join(self.source_dir, '*/*.parquet')
                                       ).cache()
        # calculate count of events by user for last 3 hours
        events_by_usr = data.filter(
            (F.col('event_time').cast('long') - F.lit(self.processing_tmstmp).cast('long')) / 3600 <= 3
        ).groupBy('user_id'
                  ).agg(F.count(F.col('event_time')).alias('u_count')
                        ).select('user_id',
                                 'u_count')
        # calculate most popular event per user
        mp_event_by_usr = data.groupBy('user_id',
                                       'event_action'
                                       ).agg(F.count(F.col('event_action')).alias('event_count')
                                             ).withColumn('rank',
                                                          F.row_number()
                                                          .over(Window.partitionBy('user_id')
                                                                .orderBy(F.desc('event_count'))
                                                                )
                                                          ).filter(F.col('rank') == 1
                                                                   ).select('user_id',
                                                                            F.col('event_action').alias('u_mp_ea')
                                                                            )
        # join data to the final dataframe
        result = data.join(events_by_usr, on='user_id', how='left'
                           ).join(mp_event_by_usr, on='user_id', how='left'
                                  ).select(*schema.fieldNames())
        # write final dataframe to the destination
        # in this particular case we write data to some directory in the `parquet` format
        # by the way, we can set here any datasource
        result.repartition(1).write.parquet(path=self.target_dir,
                                            mode='overwrite',
                                            compression='snappy')


def pipeline_options():
    parser = argparse.ArgumentParser(description='Events_streaming')
    parser.add_argument('--processing_tmstmp', action="store", dest="processing_tmstmp",
                        default=dt.datetime.utcnow(),
                        help="processing_tmstmp: timestamp to process data",
                        required=False)
    parser.add_argument('--source_dir', action="store", dest="source_dir",
                        default="/tmp/consumed_events",
                        help="source_dir: path for input source data",
                        required=False)
    parser.add_argument('--checkpoint_dir', action="store", dest="checkpoint_dir",
                        default="/tmp/checkpoint",
                        help="checkpoint_dir: path to set checkpoint for streaming app",
                        required=False)
    parser.add_argument('--target_dir', action="store", dest="target_dir",
                        default="/tmp/analytic_events",
                        help="target_dir: path for output aggregated data",
                        required=False)
    args = parser.parse_args()
    options = vars(args)
    return options


def main():
    # parse args from command line
    options = pipeline_options()
    # create pipeline instance and start data processing
    pipeline = AnalyticsPipeline(**options)
    pipeline.process()


if __name__ == '__main__':
    main()
