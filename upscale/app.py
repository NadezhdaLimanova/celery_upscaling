import os

from flask import Flask
from flask import request
from celery import Celery, Task
from flask.views import MethodView
from flask import jsonify
from celery.result import AsyncResult
import cv2
from cv2 import dnn_superres


app_name = "upscale"
app = Flask(app_name)

app.config['UPLOAD_FOLDER'] = 'files'
celery = Celery(
    app_name,
    backend='redis://localhost:6379/1',
    broker='redis://localhost:6379/2',
    broker_connection_retry_on_startup=True
)
celery.conf.update(app.config)

class ContextTask(Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


Task = ContextTask


@celery.task(name='upscale.upscale')
def upscale(input_path: str, output_path: str, model_path: str = 'EDSR_x2.pb') -> None:
    """
    :param input_path: путь к изображению для апскейла
    :param output_path:  путь к выходному файлу
    :param model_path: путь к ИИ модели
    :return:
    """

    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    image = cv2.imread(input_path)
    result = scaler.upsample(image)
    cv2.imwrite(output_path, result)


class Upscale(MethodView):

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        return jsonify({'status': task.status})

    def post(self):
        image_orig, image_output = self.save_image()
        task = upscale.delay(image_orig, image_output)
        return jsonify({'task_id': task.id, 'task_status': task.status})

    def save_image(self):
        image = request.files.get('image')
        extension, name = image.filename.split('.')[-1], image.filename.split('.')[0]
        image_orig = os.path.join('files', f'{name}.{extension}')
        image_output = os.path.join('files', f'{name}_upscaled.{extension}')
        image.save(image_orig)
        image.save(image_output)
        return image_orig, image_output


upscale_view = Upscale.as_view('upscale')
app.add_url_rule('/upscale/<string:task_id>', view_func=upscale_view, methods=['GET'])
app.add_url_rule('/upscale/', view_func=upscale_view, methods=['POST'])


if __name__ == '__main__':
    app.run()
