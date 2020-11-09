# eventsService sample

![](https://github.com/MaksGS09/eventsService/blob/main/flow.png)

# Legend:
1. Web page sends POST request to the [endpoint](https://github.com/MaksGS09/eventsService/blob/main/eventsTracking/endpoint.py).
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
3. On the last step cron job starts [Spark application](https://github.com/MaksGS09/eventsService/blob/main/pyspark/analytics_agg.py) for batch processing each 3 hours. Spark job reads data from persistent storage, applys analytical aggregations to the data and saves data enriched with additional metrics to the analytics DB/cloud storage/etc. In this particular case - to the temporary storage in parquet format with overwriting existing data. So tools like Presto, AWS Athena, etc. can provide SQL-like access to the data.
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
