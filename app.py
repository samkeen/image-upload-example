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
    # @todo validate S3 URL is well formed
    if 'S3_URL' in os.environ:
        s3_bucket_url = os.environ['S3_URL']
    else:
        raise Exception('No "S3_URL" environment variable found')
    return s3_bucket_url


def parse_img_src_url(image_src_url):
    # @todo validate image URL is well formed
    source_image_url = request.form['image_url']
    source_image_url_parts = urlparse(source_image_url)
    source_image_basename = os.path.basename(unquote(source_image_url_parts.path))
    image_name = '{0}-{1}'.format(hashlib.md5(source_image_url.encode('utf-8')).hexdigest(), source_image_basename)
    return {
        'img_src_url': source_image_url,
        'img_local_name': image_name
    }


app = Flask(__name__)
# check that s3_url is populated
get_s3_url()


@app.route('/images/')
def images():
    return render_template('images.html')


@app.route('/images/', methods=['POST'])
def image_form():
    s3_bucket_url = get_s3_url()
    parsed_img_src = parse_img_src_url(request.form['image_url'])
    this_dir = os.path.abspath(os.path.dirname(__file__))
    image_download_file = os.path.join(this_dir, 'image_downloads', parsed_img_src['img_local_name'])
    image_request = requests.get(parsed_img_src['img_src_url'], stream=True)
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

    return render_template('image_submitted.html', image_name=parsed_img_src['img_local_name'])


if __name__ == "__main__":
    app.run()
