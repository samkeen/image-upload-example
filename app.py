from flask import Flask, render_template, request, url_for
import requests
import os
import hashlib
import boto3

app = Flask(__name__)


@app.route('/images/')
def images():
    return render_template('images.html')


@app.route('/images/', methods=['POST'])
def image_form():
    # @todo validate S3 URL is well formed
    s3_bucket_url = os.environ['S3_URL']
    # @todo validate image URL is well formed
    source_image_url = request.form['image_url']
    this_dir = os.path.abspath(os.path.dirname(__file__))
    # @todo parse image name from URL
    image_name = hashlib.md5(source_image_url.encode('utf-8')).hexdigest()
    image_download_file = os.path.join(this_dir, 'image_downloads', image_name)
    # http://docs.python-requests.org/en/latest/_static/requests-sidebar.png
    image_request = requests.get(source_image_url, stream=True)
    if image_request.status_code == 200:
        with open(image_download_file, 'wb') as f:
            for chunk in image_request:
                f.write(chunk)
        # upload to S3
        s3 = boto3.resource('s3')
        with open(image_download_file, 'rb') as image_bytes:
            # https://boto3.readthedocs.org/en/latest/reference/services/s3.html#S3.Client.put_object
            s3.Bucket(s3_bucket_url).put_object(Key=image_name, Body=image_bytes)
    else:
        # @todo meaningful error message
        pass

    return render_template('image_submitted.html', image_url=source_image_url)


if __name__ == "__main__":
    app.run()
