
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
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

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

Document Path:          /httptest/dir2
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   6.125 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      5200000 bytes
HTML transferred:       0 bytes
Requests per second:    8162.72 [#/sec] (mean)
Time per request:       12.251 [ms] (mean)
Time per request:       0.123 [ms] (mean, across all concurrent requests)
Transfer rate:          829.03 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   6.5      0    1024
Processing:     1   12   3.7     11      41
Waiting:        1   12   3.7     11      41
Total:          2   12   7.4     11    1033

Percentage of the requests served within a certain time (ms)
  50%     11
  66%     12
  75%     13
  80%     14
  90%     17
  95%     20
  98%     23
  99%     25
 100%   1033 (longest request)
```
