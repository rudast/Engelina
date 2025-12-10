from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
#Jinja2 - шаблонизатор HTML

app = FastAPI()
#бэк фреймворк, API и обработка запросов

# Подключаем папку static/ для CSS, картинок и т.п.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем папку с шаблонами
templates = Jinja2Templates(directory="templates")


# Простой health-check, чтобы проверить, что сервер жив
@app.get("/api/health")
async def health():
    return {"status": "ok"}
    #возврат чистого json. (формально передаем мы словарь, но FastAPI автоматически сериализует в json)


@app.get("/", response_class=HTMLResponse)
#это- эндпоинт = адрес, по которому сервер выполняет функцию
#когда пользователь переходит через / (т.е. открывает главную страницу) то вызвать эту функцию + формат HTML заместо json
async def index(request: Request):
#request - объект запроса. в данном случае обозначает открытие html
#асинхронная функция - выполняется параллельно
    return templates.TemplateResponse(
        "index.html",
        #возвращает HTML главной страницы
        {
            "request": request,
            #Jinja2 требует прописывать реквест
            "result": None,
            "text": ""
        }
    )


@app.post("/check", response_class=HTMLResponse)
#post - передача данных на сервер
#это тоже эндпоинт
#кнопка check будет вести на новый url
#так-то при новом url если написано без javascript страница обновляется каждый раз
async def check_text(request: Request, text: str = Form(...)):
    #функция - обработчик эндпоинта
    #принимает текст введенный пользователем в форму (не JSON)
    #ПОЗЖЕ ТУТ БУДЕТ НАСТОЯЩАЯ ОБРАБОТКА
    result = {
        "corrected_text": text,
        "explanation": "Пока логики нет, просто возвращаем твой текст 🙂",
        "errors": []
    }
    #этот резалт - заглушка. тут будет json от воркера
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result,
            "text": text
        }
    )

class CheckRequest(BaseModel):
    user_id: int | None = None
    text: str
    level: str | None = None
#модель входящего json

class CheckResponse(BaseModel):
    corrected_text: str
    explanation: str
    errors: list  # потом можно уточнить тип: list[dict]
#модель того что бэк шлет фронту

@app.post("/api/check", response_model=CheckResponse)
async def api_check(payload: CheckRequest):
    #payload автоматически меняет json на удобный для питона формат
    #это JSON API, которое будет звать AI worker
    #пока здесь заглушка - просто возвращаем текст как есть


    # здесь позже будет вызов AI worker

    return CheckResponse(
        corrected_text=payload.text,
        explanation="AI ещё не подключен: это заглушка, просто возвращаем твой текст 🙂",
        errors=[]
    )