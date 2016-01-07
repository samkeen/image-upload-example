from flask import Flask, render_template, request, url_for
import requests
import os
import hashlib
import boto3
from urllib.parse import urlparse, unquote


# ======= Excuse my procedural coding style ========
# I felt it better to keep this sample as simple as possible, working under
# the assumption that many of those exploring this file will not have
# Python as one of their primary languages.
# So rather than going full OO and requiring the reader to understand Python
# name spacing and packaging, I've kept it to a single, procedural file,
# one that can easily be refactored to a more appropriate style.

def get_s3_url():
    if 'S3_BUCKET_NAME' in os.environ:
        s3_bucket_url = os.environ['S3_BUCKET_NAME']
    else:
        raise Exception('No "S3_BUCKET_NAME" environment variable found')
    return s3_bucket_url


def parse_img_src_url(image_src_url):
    source_image_url = request.form['image_url']
    source_image_url_parts = urlparse(source_image_url)
    source_image_basename = os.path.basename(unquote(source_image_url_parts.path))
    image_name = '{0}-{1}'.format(hashlib.md5(source_image_url.encode('utf-8')).hexdigest(), source_image_basename)
    return {
        'img_src_url': source_image_url,
        'img_local_name': image_name
    }


def build_img_local_filepath(img_basename):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(this_dir, 'image_downloads', img_basename)


def write_img_to_file(source, destination):
    with open(destination, 'wb') as f:
        for chunk in source:
            f.write(chunk)


def put_img_to_s3(local_img_filepath, key_name):
    s3 = boto3.resource('s3')
    with open(local_img_filepath, 'rb') as image_bytes:
        # https://boto3.readthedocs.org/en/latest/reference/services/s3.html#S3.Client.put_object
        s3.Bucket(get_s3_url()).put_object(Key=key_name, Body=image_bytes)


app = Flask(__name__)
# check that s3_url is populated
get_s3_url()


@app.route('/images/')
def images():
    return render_template('images.html')


@app.route('/images/', methods=['POST'])
def image_form():
    try:
        parsed_img_src = parse_img_src_url(request.form['image_url'])
        local_img_filepath = build_img_local_filepath(parsed_img_src['img_local_name'])
        get_img_response = requests.get(parsed_img_src['img_src_url'], stream=True)
        if get_img_response.status_code == 200:
            write_img_to_file(get_img_response, local_img_filepath)
            put_img_to_s3(local_img_filepath, parsed_img_src['img_local_name'])
        else:
            # @todo meaningful error message
            pass

        return render_template('image_submitted.html', image_name=parsed_img_src['img_local_name'])
    except Exception as e:
        return render_template('error.html', error_message="OS error: {0}".format(e))


if __name__ == "__main__":
    app.run()
