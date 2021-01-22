# SGX-crawler
A crawler that automatically download Singapore Exchange Time and Sales Historical Data.

The data is downloaded by 2 methods:
- GET request: GET request is prefered as it does not require using browser. Furthermore, the website only offer the data for the past 5 market days; therefore, older can only be download by sending GET request with specific id for the older date.
- Selenium: this is only used for the data of the past 5 market days and if the GET request method does not work.

The crawler will download the data from the date the user request until the latest market day. For the usage, please refer to
```
python crawler.py --help
```
