from flask import Flask, render_template, request, url_for, redirect
from urllib.parse import urlparse, unquote
import os, hashlib, boto3, json


# ======= Excuse my procedural coding style ========
# I felt it better to keep this sample as simple as possible, working under the assumption that many of those
# exploring this file may not have Python as one of their primary languages.
#
# So rather than going full Object Oriented and requiring the reader to understand Python name spacing and
# packaging, and Object model,  I've kept it to a single, procedural file, one that can easily be refactored to a
# more appropriate style by the reader.

def get_required_env_var(var_name):
    """Retrieves an env var's value from the environment, RuntimeError if not found

    :param var_name:
    :return: String ENV var's value
    """
    if var_name in os.environ:
        value = os.environ[var_name].strip()
    else:
        raise RuntimeError('No "{}" environment variable found'.format(var_name))
    return value


def get_unique_local_img_name(image_src_url):
    """Uses the 'filename' from the URL + an MD5 hash of the entire URL to create a unique local name to use for
    the image file.

    :param image_src_url:
    :return: str "{MD5 hash of src URL}-{file name of segemnt of src URL}"
    """
    source_image_url_parts = urlparse(image_src_url)
    source_image_basename = os.path.basename(unquote(source_image_url_parts.path))
    return '{0}-{1}'.format(hashlib.md5(image_src_url.encode('utf-8')).hexdigest(), source_image_basename)


def put_work_to_queue(local_img_name, img_src_url):
    """Send the Message to the SQS work queue

    :param str local_img_name:
    :param str img_src_url:
    :return: str The SQS message id
    """
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=get_required_env_var('WORK_QUEUE_NAME'))
    message_body = json.dumps({"img_src_url": img_src_url, "img_local_name": local_img_name}, indent=2)
    response = queue.send_message(MessageBody=message_body)

    return response.get('MessageId')


def get_s3_base_url(s3_bucket_name):
    """returns the URL for an S3 bucket

    :param str s3_bucket_name:
    :return: str full URL to the bucket
    """
    bucket_location = boto3.client('s3').get_bucket_location(Bucket=s3_bucket_name)
    return "https://s3-{0}.amazonaws.com/{1}".format(bucket_location['LocationConstraint'],
                                                     s3_bucket_name)


# This app uses the Flask web framework. For documentation see: http://flask.pocoo.org/
app = Flask(__name__)
# check that the expected ENV vars are in place on startup of the server
get_required_env_var('S3_BUCKET_NAME')
get_required_env_var('WORK_QUEUE_NAME')


@app.route('/images')
def images():
    return render_template('images.html')


@app.route('/images', methods=['POST'])
def image_form():
    try:
        img_src_url = request.form['image_url'].strip()
        img_local_name = get_unique_local_img_name(img_src_url)
        work_receipt = put_work_to_queue(img_local_name, img_src_url)
        target_s3_base_url = get_s3_base_url(get_required_env_var('S3_BUCKET_NAME'))
        return redirect(url_for('request_received',
                                name=img_local_name,
                                source=img_src_url,
                                dest_base_url=target_s3_base_url,
                                dest_img_name=img_local_name))
    except Exception as e:
        return render_template('error.html', error_message="Error Message: {0}".format(e))


@app.route('/request_received', methods=['GET'])
def request_received():
    return render_template('request_received.html',
                           image_name=request.args.get('name', ''),
                           src_url=request.args.get('source', ''),
                           dest_base_url=request.args.get('dest_base_url', ''),
                           dest_img_name=request.args.get('dest_img_name', ''))


if __name__ == "__main__":
    flask_host = os.environ['FLASK_HOST'].strip() if 'FLASK_HOST' in os.environ else '127.0.0.1'
    flask_port = int(os.environ['FLASK_PORT'].strip()) if 'FLASK_PORT' in os.environ else 5000
    app.run(host=flask_host, port=flask_port)
