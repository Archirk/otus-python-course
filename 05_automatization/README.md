
## Homework 5 - Basic HTTP Server

#### Описание
Простой HTTP сервер принимающий HEAD и GET запросы и обрабатывающий их в соответствии с ТЗ и приложенными тестами.  
Сервер основан на preforked архитектуре. На выбранном порте создаются воркеры, слушающие запросы, а затем на каждый запрос создаются треды для их обработки.  
#### Запуск сервера
```bash
python3 httpd.py -r DOCUMENT_ROOT -w WORKERS_NUMBER -c MAX_CONNECTIONS --host HOST --port PORT --log PATH_TO_LOG  
```
Вместо неуказанных переменных будут взяты переменные по умолчанию указанные в config.py
#### Запуск тестов
После запуска сервера можно запустить unit-тесты:
```bash
python3 httptest.py
```
##### Нагрузочное тестирование:
Поскольку по условию задания и входным данным, при обращении к корневой директории будет возвращена ошибка 404, нагрузочный тест проводился на страницу, которая возвращает ответ 200. В данном случае http://localhost:8080/httptest/dir2/ , а количество воркеров для теста было **6**
```bash
ab -n 50000 -с 100 -r http://localhost:8080/httptest/dir2/
```
##### Результаты тестирования
```
Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        OTUS_ChirkovServer
Server Hostname:        localhost
Server Port:            8080

Document Path:          /httptest/dir2/
Document Length:        34 bytes

Concurrency Level:      100
Time taken for tests:   4.158 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      8800000 bytes
HTML transferred:       1700000 bytes
Requests per second:    12024.43 [#/sec] (mean)
Time per request:       8.316 [ms] (mean)
Time per request:       0.083 [ms] (mean, across all concurrent requests)
Transfer rate:          2066.70 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.2      0       6
Processing:     1    8   1.1      8      22
Waiting:        1    8   1.1      8      22
Total:          2    8   1.1      8      22

Percentage of the requests served within a certain time (ms)
  50%      8
  66%      8
  75%      9
  80%      9
  90%     10
  95%     10
  98%     11
  99%     12
 100%     22 (longest request)
```
