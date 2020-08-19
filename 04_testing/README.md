## Homework 4 - Scoring API with integration Tests and Storage

#### Запуск api  
```bash
python api.py [--port PORT --log PATH_TO_LOG]  
```
#### Написание запросов 
Приложение принимает ожидает на вход JSON-объект.  
##### Структура запроса:

```python
{
"account": "string",  
"login": "string",  
"method": "string",  
"token": "string",  
"arguments": {},  
}  
```
В приложении доступно два метода: "online_score" и "clients_interests", арггументы для которых передаются в поле arguments. Оба метода описаны в scoring.py
##### Информация по полям запроса:
| Field |  Type  |  Requirements  |
|:---:|:---:|:----:|
|  account  | string | optional, nullable 
|  login  | string | required, nullable 
|  method  | string | required, nullable 
|  login  | string | required, nullable 
|  arguments  | JSON-object | required, nullable 
##### Поля Arguments для запросов:  
##### online_score:  
| Field |  Type  |  Requirements  |  Description  |
|:---:|:---:|:----:|----|
| phone | string, int | optional, nullable | phone number, length=11, starting with 7 
| email | string | optional, nullable, | email, must contain "@" 
| first_name | string | optional, nullable | First name 
| last_name | string | optional, nullable | Last name 
| birthday | string | optional, nullable | Formatted "DD.MM.YYYY" birthday date 
| gender | int | optional, nullable | Gender id. Expected values: 0, 1, 2 

Для метода online_score необходима хотя бы 1 валидная пара данных: phone-email, first_name-last_name, birthday-gender 

##### clients_interests:  
| Field |  Type  |  Requirements  |  Description  |
|:---:|:---:|:----:|----|
|  client_ids  | Array[int] | required, not nullable | Client ids
|  date  | string | optional, nullable, | Formatted "DD.MM.YYYY" date

#### Примеры запросов и ответов
##### Запрос online_score: 
```bash
curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method":
"online_score", "token":
"55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd
"arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name":
"Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
```
##### Ответ online_score: 
{"code": 200, "response": {"score": 5.0}}
##### Запрос client_ids: 
```bash
curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method":
"clients_interests", "token":
"d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f240913860502
"arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
```
##### Ответ client_ids: 
{"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4":
["cinema", "geek"]}}

#### Ответ с ошибкой
В случае если запрос неверен, приложени вернет ответ с ошибкой:
{"code": CODE, "error": "<сообщение о том какое поле(я) невалидно(ы) и как именно>"}

#### Store  
Добавлен класс Store в store.py  
Класс представляет из себя обертку обертки для Redis для выполнения задания.    

#### Тестирование
В рамках задания было написано 3 теста: для тестирования полей, функционирования API и работы Store. Они находятся в папке
tests.  
Чтобы запустить их с красивым выводом необходимо запустить run_tests.py
