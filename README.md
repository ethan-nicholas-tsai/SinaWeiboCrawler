# SinaWeiboCrawler

A crawler collect data from Sina Weibo using none-official APIs

## 1. Installation

```
pip install -r requirements.txt
# install and configure your mongodb
```

## 2. Configuration

### a) Modification of Settings.py

```
# Necessary
DEFAULT_REQUEST_HEADERS = {
	'cookie': 'your cookie'
}
MONGO_URI = 'YOUR_IP:YOUR_PORT'
MONGO_DATABASE = 'YOUR_DBNAME'
MONGO_USER = 'YOUR_USERNAME'
MONGO_PASSWORD = 'YOUR_PASSWORD'
# Speed parameters
CONCURRENT_REQUESTS = 32  # Configure maximum concurrent requests performed by Scrapy 
DOWNLOAD_DELAY = 0.5  # Configure a delay for requests for the same website
DOWNLOAD_TIMEOUT = 3  # Configure a timeout for connection
RETRY_TIMES = 1  # Configure retry times for a request
# Crawl Target
## weibo.com
KEYWORD_LIST = ['#日常#'] # keywords to search the tweets
WEIBO_TYPE = 1 # Weibo type，0 for all，1 for origin
CONTAIN_TYPE = 0 # Weibo contain certain content，0 for all，1 for image，2 for video
REGION = ['全部'] # Region where the tweet is posted. '全部' for all, '北京' for Peking
START_DATE = '2014-01-01' # Lower bound of poting date range. (yyyy-mm-dd)
END_DATE = '2020-12-31' # Upper bound of poting date range. (yyyy-mm-dd)
START_TIME = '0' # Lower bound of poting time range. (0-24)
END_TIME = '6' # Upper bound of poting time range. (0-24)
```

### b) Modification of ProxyMiddleware

```
PROXY_POOL_URL = 'YOUR_PROXY_POOL_URL' # purchase a proxy pool yourself
```

## 3. Fields

### a) m.weibo.cn

#### user

```
# API for all information of user
https://m.weibo.cn/api/container/getIndex?containerid=100505{uid}
# API for profile of user
https://m.weibo.cn/api/container/getIndex?containerid=230283{uid}_-_INFO
```

| Ind  | Field Name in Response | Field Name in Code | Description                                                  |
| ---- | ---------------------- | ------------------ | ------------------------------------------------------------ |
| 1    | id                     | _id                | User id                                                      |
| 2    | screen_name            | screen_name        | User nickname                                                |
| 3    | statuses_count         | tweet_count        | The number of all tweets                                     |
| 4    | profile_image_url      | avatar             | Link of user avatar image                                    |
| 5    | cover_image_phone      | cover_image        | Link of user cover image                                     |
| 6    | description            | description        | User self-introduction                                       |
| 7    | follow_count           | follow_count       | The number of user followings                                |
| 8    | followers_count        | followers_count    | The number of user followers                                 |
| 9    | gender                 | gender             | User gender(`f` for female, `m` for male)                    |
| 10   | verified               | verified           | If user has passed certain verification of Sina Weibo        |
| 11   | verified_type          | verified_type      | User verification type, eg. Individual, Enterprise, Government, etc. |
| 12   | verified_reason        | verified_reason    | The reason why the user pass verification of Sina Weibo      |
| 13   | urank                  | urank              | Liveness of user on Sina Weibo（Bigger number represents for more user activities on Sina Weibo） |
| 14   | mbrank                 | mbrank             | Vip rank of user on Sina Weibo                               |

#### tweet

```
# API for crawling user tweets
https://m.weibo.cn/api/container/getIndex?containerid=107603{tid}&page={}
# API for detailed information of tweet (for long tweet or tweet containing more than 9 pictures)
https://m.weibo.cn/statuses/extend?id={tid}
```

| Ind  | Field Name in Code | Field Name in Response | Description                                                  |
| ---- | ------------------ | ---------------------- | ------------------------------------------------------------ |
| 1    | id                 | id                     | Tweet id（Primary key）                                      |
| 2    | user_id            | user_id                | User id（Foreign key）                                       |
| 3    | text               | text                   | Html of tweet                                                |
| 4    | pics               | pics                   | Links of pictures in the tweet content (delimited by comma)  |
| 5    | video_url          | page_info              | Link of video in the tweet                                   |
| 6    | created_at         | created_at             | The posting time of the tweet (weekday month day hour:minute:second timezone year) |
| 7    | source             | source                 | Use what kind of device to post the tweet or Under what supertopic the user post the tweet |
| 8    | attitudes_count    | attitudes_count        | The number of people favor the tweet                         |
| 9    | comments_count     | comments_count         | The number of comments                                       |
| 10   | reposts_count      | reposts_count          | Reposting times of the tweet                                 |
| 11   | location           | text                   | The current place of user when posting the tweet             |
| 12   | topics             | text                   | Topics of the tweet (classified by Sina Weibo, delimited by comma) |
| 13   | at_users           | text                   | Mention of users of Sina Weibo (delimited by comma)          |
| 14   | article_url        | text                   | Link of front page headline in the tweet                     |
| 15   | retweet            | retweeted_status       | Information of retweets                                      |

### b) weibo.com

#### meta

| Ind  | Field Name  | Description                                |
| ---- | ----------- | ------------------------------------------ |
| 1    | _id         | User id                                    |
| 2    | screen_name | User Nickname                              |
| 3    | orient_type | Type of user to be collected               |
| 4    | keyword     | Search keyword to filter content of tweets |



