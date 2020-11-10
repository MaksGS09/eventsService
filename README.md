# eventsService sample

![](https://github.com/MaksGS09/eventsService/blob/main/flow.png)

# Legend:
1. Web page sends POST request to the [endpoint](https://github.com/MaksGS09/eventsService/blob/main/eventsTracking/main.py).
Service takes payload in json from request and asynchronous writes data to the kafka topic `events`.

2. On other hand the [Spark Structured Streaming application](https://github.com/MaksGS09/eventsService/blob/main/pyspark/stream.py) consumes data from kafka topic `events` and each 1 minute saves data to the persistent storage in parquet format with next schema:
```
root
 |-- event_time: timestamp (nullable = true)
 |-- user_id: integer (nullable = true)
 |-- app_name: string (nullable = true)
 |-- event_action: string (nullable = true)
 |-- event_category: string (nullable = true)
 |-- event_value: integer (nullable = true)
 |-- u_count: long (nullable = true)
 |-- u_mp_ea: string (nullable = true)
```
sample data from this step:
```
+--------------------------+-------+---------+------------+--------------+-----------+
|event_time                |user_id|app_name |event_action|event_category|event_value|
+--------------------------+-------+---------+------------+--------------+-----------+
|2020-11-09 08:51:30.128801|1      |product_3|scroll      |category_3    |12         |
|2020-11-09 08:51:30.180028|1      |product_1|scroll      |category_2    |null       |
|2020-11-09 08:51:30.396411|3      |product_1|button_click|category_2    |null       |
|2020-11-09 08:51:30.63611 |4      |product_2|page_view   |category_2    |12         |
|2020-11-09 08:51:32.144393|2      |product_2|scroll      |category_2    |37         |
|2020-11-09 08:51:32.196655|2      |product_2|button_click|category_3    |null       |
|2020-11-09 08:51:32.416766|3      |product_1|scroll      |category_1    |12         |
|2020-11-09 08:51:32.656561|4      |product_1|button_click|category_1    |null       |
|2020-11-09 08:51:34.164493|2      |product_3|button_click|category_3    |54         |
|2020-11-09 08:51:34.216541|3      |product_1|button_click|category_2    |null       |
|2020-11-09 08:51:34.436065|6      |product_1|button_click|category_1    |12         |
|2020-11-09 08:51:34.67622 |5      |product_3|null        |category_2    |null       |
|2020-11-09 08:51:36.18165 |6      |product_3|scroll      |category_1    |54         |
|2020-11-09 08:51:36.236815|6      |product_1|button_click|category_2    |54         |
|2020-11-09 08:51:36.451145|2      |product_1|button_click|category_3    |null       |
|2020-11-09 08:51:36.696168|2      |product_3|button_click|category_1    |5          |
+--------------------------+-------+---------+------------+--------------+-----------+
```
3. On the last step cron job starts [Spark application](https://github.com/MaksGS09/eventsService/blob/main/pyspark/analytics_agg.py) for batch processing each 3 hours. Spark job reads data from persistent storage, applies analytical aggregations to the data and saves data enriched with additional metrics to the analytics DB/cloud storage/etc. In this particular case - to the temporary storage in parquet format with overwriting existing data. So tools like Presto, AWS Athena, etc. can provide SQL-like access to this data.
data schema:
```
root
 |-- event_time: timestamp (nullable = true)
 |-- user_id: integer (nullable = true)
 |-- app_name: string (nullable = true)
 |-- event_action: string (nullable = true)
 |-- event_category: string (nullable = true)
 |-- event_value: integer (nullable = true)
 |-- u_count: long (nullable = true)
 |-- u_mp_ea: string (nullable = true)
```
final data sample:
```
+--------------------------+-------+---------+------------+--------------+-----------+-------+------------+
|event_time                |user_id|app_name |event_action|event_category|event_value|u_count|u_mp_ea     |
+--------------------------+-------+---------+------------+--------------+-----------+-------+------------+
|2020-11-09 14:48:13.697496|5      |product_1|button_click|category_1    |37         |1640   |scroll      |
|2020-11-09 14:48:13.698427|1      |product_2|button_click|category_1    |37         |1630   |page_view   |
|2020-11-09 14:48:13.698702|2      |product_3|page_view   |category_1    |37         |1707   |scroll      |
|2020-11-09 14:48:13.703538|5      |product_1|null        |category_3    |null       |1640   |scroll      |
|2020-11-09 14:48:13.704694|3      |product_3|scroll      |category_1    |12         |1689   |button_click|
|2020-11-09 14:48:13.704972|4      |product_3|null        |category_1    |54         |1686   |button_click|
|2020-11-09 14:48:13.712363|3      |product_2|page_view   |category_3    |12         |1689   |button_click|
|2020-11-09 14:48:13.712613|2      |product_3|scroll      |category_1    |12         |1707   |scroll      |
|2020-11-09 14:48:13.71284 |1      |product_1|null        |category_2    |5          |1630   |page_view   |
|2020-11-09 14:48:13.713048|1      |product_3|null        |category_3    |54         |1630   |page_view   |
|2020-11-09 14:48:13.713293|3      |product_1|null        |category_2    |37         |1689   |button_click|
|2020-11-09 14:48:13.713483|6      |product_1|null        |category_2    |null       |1648   |scroll      |
|2020-11-09 14:48:13.715946|3      |product_2|page_view   |category_1    |54         |1689   |button_click|
|2020-11-09 14:48:13.716643|3      |product_2|page_view   |category_3    |8          |1689   |button_click|
|2020-11-09 14:48:13.716947|1      |product_3|button_click|category_2    |5          |1630   |page_view   |
|2020-11-09 14:48:13.717216|3      |product_3|scroll      |category_2    |12         |1689   |button_click|
|2020-11-09 14:48:13.727331|6      |product_1|scroll      |category_1    |8          |1648   |scroll      |
|2020-11-09 14:48:13.72747 |5      |product_2|page_view   |category_3    |8          |1640   |scroll      |
|2020-11-09 14:48:13.727602|1      |product_1|page_view   |category_3    |12         |1630   |page_view   |
|2020-11-09 14:48:13.727726|1      |product_3|button_click|category_2    |37         |1630   |page_view   |
|2020-11-09 14:48:13.727848|5      |product_1|button_click|category_1    |8          |1640   |scroll      |
|2020-11-09 14:48:13.727969|4      |product_2|button_click|category_3    |37         |1686   |button_click|
+--------------------------+-------+---------+------------+--------------+-----------+-------+------------+
```

# To start this flow locally you need to do the next steps:
Sure that you have installed:
 - Python (in our case we use python 3.8);
 - Kafka client (if no, install it by this [guide](https://kafka.apache.org/quickstart));
 - Spark (install [guide](https://github.com/MaksGS09/eventsService/wiki/Install-Apache-Spark));
 - Clone project https://github.com/MaksGS09/eventsService via IDE or git command.
 - Setup your environment using Pipenv.
 - Start Kafka environment as defined [here](https://kafka.apache.org/quickstart). 
 - Create kafka topic `events`:
 ```commandline
bin/kafka-topics.sh --create --topic events --bootstrap-server localhost:9092
```
Now you can start the flow:
NOTE: In our case the project cloned to the ~/PycharmProjects directory. If you have cloned the project to a different folder, make sure you are using the correct path in all commands.
- start the POST API [endpoint](https://github.com/MaksGS09/eventsService/blob/main/eventsTracking/main.py)
- start the streaming job:
```commandline
/bin/bash ~/PycharmProjects/eventsService/start_stream.sh
```
- start the [fake_requests.py](https://github.com/MaksGS09/eventsService/blob/main/eventsTracking/fake_requests.py) to simulate requests to the POST API endpoint.
- after few minutes you can trigger the  [analytics_agg.py](https://github.com/MaksGS09/eventsService/blob/main/pyspark/analytics_agg.py) to get the analytical aggregation.
- and finally check the final dataset:
```commandline
/bin/bash ~/PycharmProjects/eventsService/start_check.sh
```
Since we defined in the [fake_requests.py](https://github.com/MaksGS09/eventsService/blob/main/eventsTracking/fake_requests.py) 10000 requests, you can see in the output stats for the same number of rows:
```commandline
+--------------------------+-------+---------+------------+--------------+-----------+-------+------------+
|event_time                |user_id|app_name |event_action|event_category|event_value|u_count|u_mp_ea     |
+--------------------------+-------+---------+------------+--------------+-----------+-------+------------+
|2020-11-09 14:48:13.697496|5      |product_1|button_click|category_1    |37         |1640   |scroll      |
|2020-11-09 14:48:13.698427|1      |product_2|button_click|category_1    |37         |1630   |page_view   |
|2020-11-09 14:48:13.698702|2      |product_3|page_view   |category_1    |37         |1707   |scroll      |
|2020-11-09 14:48:13.703538|5      |product_1|null        |category_3    |null       |1640   |scroll      |
|2020-11-09 14:48:13.704694|3      |product_3|scroll      |category_1    |12         |1689   |button_click|
|2020-11-09 14:48:13.704972|4      |product_3|null        |category_1    |54         |1686   |button_click|
|2020-11-09 14:48:13.705203|3      |product_3|page_view   |category_3    |37         |1689   |button_click|
|2020-11-09 14:48:13.70576 |6      |product_3|null        |category_3    |null       |1648   |scroll      |
|2020-11-09 14:48:13.707245|4      |product_2|page_view   |category_3    |54         |1686   |button_click|
|2020-11-09 14:48:13.709066|3      |product_2|page_view   |category_2    |5          |1689   |button_click|
|2020-11-09 14:48:13.709388|2      |product_3|page_view   |category_2    |12         |1707   |scroll      |
|2020-11-09 14:48:13.709623|3      |product_3|page_view   |category_2    |8          |1689   |button_click|
|2020-11-09 14:48:13.709831|4      |product_1|page_view   |category_3    |8          |1686   |button_click|
|2020-11-09 14:48:13.711974|5      |product_2|button_click|category_3    |37         |1640   |scroll      |
|2020-11-09 14:48:13.712363|3      |product_2|page_view   |category_3    |12         |1689   |button_click|
|2020-11-09 14:48:13.712613|2      |product_3|scroll      |category_1    |12         |1707   |scroll      |
|2020-11-09 14:48:13.71284 |1      |product_1|null        |category_2    |5          |1630   |page_view   |
|2020-11-09 14:48:13.713048|1      |product_3|null        |category_3    |54         |1630   |page_view   |
|2020-11-09 14:48:13.713293|3      |product_1|null        |category_2    |37         |1689   |button_click|
|2020-11-09 14:48:13.713483|6      |product_1|null        |category_2    |null       |1648   |scroll      |
|2020-11-09 14:48:13.715946|3      |product_2|page_view   |category_1    |54         |1689   |button_click|
|2020-11-09 14:48:13.716643|3      |product_2|page_view   |category_3    |8          |1689   |button_click|
|2020-11-09 14:48:13.716947|1      |product_3|button_click|category_2    |5          |1630   |page_view   |
|2020-11-09 14:48:13.717216|3      |product_3|scroll      |category_2    |12         |1689   |button_click|
|2020-11-09 14:48:13.717431|3      |product_3|scroll      |category_2    |null       |1689   |button_click|
|2020-11-09 14:48:13.719048|5      |product_2|scroll      |category_2    |8          |1640   |scroll      |
|2020-11-09 14:48:13.719951|5      |product_1|scroll      |category_3    |54         |1640   |scroll      |
|2020-11-09 14:48:13.720205|5      |product_2|scroll      |category_3    |12         |1640   |scroll      |
|2020-11-09 14:48:13.720414|3      |product_2|page_view   |category_2    |8          |1689   |button_click|
|2020-11-09 14:48:13.720613|2      |product_2|button_click|category_3    |54         |1707   |scroll      |
|2020-11-09 14:48:13.722861|6      |product_2|scroll      |category_2    |12         |1648   |scroll      |
|2020-11-09 14:48:13.72304 |5      |product_3|scroll      |category_2    |12         |1640   |scroll      |
|2020-11-09 14:48:13.723176|4      |product_3|page_view   |category_1    |8          |1686   |button_click|
|2020-11-09 14:48:13.723321|6      |product_3|null        |category_2    |8          |1648   |scroll      |
|2020-11-09 14:48:13.723482|4      |product_2|page_view   |category_2    |54         |1686   |button_click|
|2020-11-09 14:48:13.723611|5      |product_2|scroll      |category_3    |8          |1640   |scroll      |
|2020-11-09 14:48:13.724905|5      |product_1|null        |category_2    |null       |1640   |scroll      |
|2020-11-09 14:48:13.725073|6      |product_2|button_click|category_1    |null       |1648   |scroll      |
|2020-11-09 14:48:13.725204|4      |product_2|null        |category_2    |37         |1686   |button_click|
|2020-11-09 14:48:13.725399|4      |product_3|page_view   |category_3    |37         |1686   |button_click|
|2020-11-09 14:48:13.72553 |5      |product_1|page_view   |category_1    |54         |1640   |scroll      |
|2020-11-09 14:48:13.725654|2      |product_2|null        |category_1    |5          |1707   |scroll      |
|2020-11-09 14:48:13.725783|2      |product_1|button_click|category_2    |37         |1707   |scroll      |
|2020-11-09 14:48:13.725901|1      |product_3|null        |category_2    |12         |1630   |page_view   |
|2020-11-09 14:48:13.727331|6      |product_1|scroll      |category_1    |8          |1648   |scroll      |
|2020-11-09 14:48:13.72747 |5      |product_2|page_view   |category_3    |8          |1640   |scroll      |
|2020-11-09 14:48:13.727602|1      |product_1|page_view   |category_3    |12         |1630   |page_view   |
|2020-11-09 14:48:13.727726|1      |product_3|button_click|category_2    |37         |1630   |page_view   |
|2020-11-09 14:48:13.727848|5      |product_1|button_click|category_1    |8          |1640   |scroll      |
|2020-11-09 14:48:13.727969|4      |product_2|button_click|category_3    |37         |1686   |button_click|
+--------------------------+-------+---------+------------+--------------+-----------+-------+------------+
only showing top 50 rows

-------------------------------------------------------------

......
20/11/10 16:58:32 INFO DAGScheduler: ResultStage 3 (count at NativeMethodAccessorImpl.java:0) finished in 0.040 s
20/11/10 16:58:32 INFO DAGScheduler: Job 2 is finished. Cancelling potential speculative or zombie tasks for this job
20/11/10 16:58:32 INFO TaskSchedulerImpl: Killing all running tasks in stage 3: Stage finished
20/11/10 16:58:32 INFO DAGScheduler: Job 2 finished: count at NativeMethodAccessorImpl.java:0, took 0.128761 s

Rows in the result dataset: 10000
-------------------------------------------------------------
root
 |-- event_time: timestamp (nullable = true)
 |-- user_id: integer (nullable = true)
 |-- app_name: string (nullable = true)
 |-- event_action: string (nullable = true)
 |-- event_category: string (nullable = true)
 |-- event_value: integer (nullable = true)
 |-- u_count: long (nullable = true)
 |-- u_mp_ea: string (nullable = true)

```
