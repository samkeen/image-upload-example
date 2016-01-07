Image Upload Demo App
=====================

This is a very simple app that can upload images on the User's behalf.

It is to be used to demonstrate building distributed computing systems.

*Demo purposes only, not production code ready by any means*

The strategy used by this app is:

1. Takes URL of image from user
2. Downloads the image locally, then uploads it to S3
3. Push Job to SQS (see branch: <<<>>>)

Usage
-----

``S3_BUCKET_NAME=<YOUR BUCKET NAME> python app.py``
