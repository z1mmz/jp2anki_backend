from flask import Flask,request,send_file
from flask_cors import CORS, cross_origin
import jp2anki
from celery import Celery, Task
from celery import shared_task
from celery.result import AsyncResult
import redis
import pickle



r = redis.Redis()

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://127.0.0.1",
        result_backend="redis://127.0.0.1",
        task_ignore_result=True,
    ),
)
celery_app = celery_init_app(app)


cors = CORS(app)
app.config['CORS_HEADERS'] = ['Content-Type',"Authorization",'Access-Control-Allow-Origin']
app.config['CORS_EXPOSE_HEADERS'] = ['Content-Disposition','Access-Control-Allow-Origin']
celery_app = celery_init_app(app)

@shared_task(ignore_result=False)
def anki_task(rj):
    title = rj["title"]
    file = jp2anki.jankify(title=title,text=rj["text"])
    return {"title":title + ".apkg","data":file}

app.route('/download/<fpath>')
@cross_origin()
def download(fpath):
    return send_file(fpath, as_attachment=True )


@app.route("/result/<id>")
@cross_origin()
def task_result(id: str) -> dict[str, object]:
    result = anki_task.AsyncResult(str(id))
    ready = result.ready()
    return {
        "ready": ready,
        "successful": result.successful() if ready else None,
        "value": result.get() if ready else None,
    }
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/ankify",methods=['POST'])
@cross_origin()
def ankify():
    rj = request.get_json()
    result = anki_task.delay(rj)
    return {"result_id": result.id}


