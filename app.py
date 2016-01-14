from flask import Flask, render_template, request, url_for, redirect
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

def get_images_bucket_name():
    """
    Retrieves the name of the S3 image storage bucket from the environment

    :return: The AWS name of the bucket
    """
    if 'S3_BUCKET_NAME' in os.environ:
        s3_bucket_name = os.environ['S3_BUCKET_NAME'].strip()
    else:
        raise Exception('No "S3_BUCKET_NAME" environment variable found')
    return s3_bucket_name


def parse_img_src_url(image_src_url):
    """
    Normalizes the source image URL and also produces a local image name derived from said URL.

    :param image_src_url:
    :return: Dictionary of img_src_url: <image's source URL>, img_local_name: <Local image filename>
    """
    image_src_url = image_src_url.strip()
    source_image_url_parts = urlparse(image_src_url)
    source_image_basename = os.path.basename(unquote(source_image_url_parts.path))
    image_name = '{0}-{1}'.format(hashlib.md5(image_src_url.encode('utf-8')).hexdigest(), source_image_basename)
    return {
        'img_src_url': image_src_url,
        'img_local_name': image_name
    }


def build_img_local_filepath(img_basename):
    """
    Construct the full path to store the local image at.

    :param img_basename:
    :return: Full path to local directory to store image within.
    """
    this_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(this_dir, 'image_downloads', img_basename)


def write_img_to_file(source, destination):
    """
    Writes Image to local file system

    :param source: The Requests response for the Image
    :param destination: The full file path to store the Image on the local file system
    :return: void
    """
    with open(destination, 'wb') as f:
        for chunk in source:
            f.write(chunk)


def put_img_to_s3(local_img_filepath, key_name):
    """
    Uploads the image to the Images Storage S3 bucket

    :param local_img_filepath:
    :param key_name:
    :return: Returns the full S3 HTTP url to the S3 Object.
    """
    s3 = boto3.resource('s3')
    with open(local_img_filepath, 'rb') as image_bytes:
        # https://boto3.readthedocs.org/en/latest/reference/services/s3.html#S3.Client.put_object
        s3_bucket_name = get_images_bucket_name()
        s3.Bucket(s3_bucket_name).put_object(Key=key_name, Body=image_bytes, ACL='public-read')
        bucket_location = boto3.client('s3').get_bucket_location(Bucket=s3_bucket_name)
        return "https://s3-{0}.amazonaws.com/{1}/{2}".format(bucket_location['LocationConstraint'],
                                                             s3_bucket_name,
                                                             key_name)


app = Flask(__name__)
# check that s3 bucket name was defined on startup
get_images_bucket_name()


@app.route('/images/')
def images():
    """
    Renders the Upload Image form
    """
    return render_template('images.html')


@app.route('/images/', methods=['POST'])
def image_form():
    """
    Accepts POST'd image source URL.
     - pulls the image down and stores it locally
     - pushes the image up to S3
    """
    try:
        parsed_img_src = parse_img_src_url(request.form['image_url'])
        local_img_filepath = build_img_local_filepath(parsed_img_src['img_local_name'])
        get_img_response = requests.get(parsed_img_src['img_src_url'], stream=True)
        if get_img_response.status_code == 200:
            write_img_to_file(get_img_response, local_img_filepath)
            s3_img_url = put_img_to_s3(local_img_filepath, parsed_img_src['img_local_name'])
        else:
            return render_template('error.html', error_message="Error retrieving image. Response code: {0} {1}"
                                   .format(get_img_response.status_code, get_img_response.reason))

        os.remove(local_img_filepath)
        return redirect(url_for('uploaded_image',
                                name=parsed_img_src['img_local_name'],
                                source=parsed_img_src['img_src_url'],
                                destination=s3_img_url))
    except Exception as e:
        return render_template('error.html', error_message="Error Message: {0}".format(e))


@app.route('/uploaded_image/', methods=['GET'])
def uploaded_image():
    """
    Show information about an uploaded Image
    """
    return render_template('uploaded_image.html',
                           image_name=request.args.get('name', ''),
                           source_url=request.args.get('source', ''),
                           destination_url=request.args.get('destination', ''))


if __name__ == "__main__":
    flask_host = os.environ['FLASK_HOST'].strip() if 'FLASK_HOST' in os.environ else '127.0.0.1'
    flask_port = os.environ['FLASK_PORT'].strip() if 'FLASK_PORT' in os.environ else 5000
    app.run(host=flask_host, port=flask_port)
