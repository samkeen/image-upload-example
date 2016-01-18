Work Queue Backed Image Upload Demo App
=====================

This is a very simple app that can upload images on the User's behalf.

It is to be used to demonstrate building distributed computing systems.
Planning to utilize it for a online course I am developing on Udemy.

The associated Worker App (Utilized AWS SQS), can be found at `here <https://github.com/samkeen/simple-image-worker-example>`_

*Demo purposes only, not production code ready by any means*

The strategy used by this app is:

1. Takes URL of image from user
2. Push Job to SQS

Advantages of using a Queue vs doing all work on the web app server

- File are never downloaded to local storage.  You do not need to manage this disk space per server.
- Short request times can be enforced. No need to support a multi-minute upload connection between a browser client
  and the server.
- If the server handling the request to process the image fails, work is not lost. It is still in the queue and can
  be handled by another server.
- **Specialization**: The web app server can be optimized to perform a single discrete purpose:
  *Respond to HTTP requests from a clients browser*.
  This simplifies configuration, securing, deployment and scaling of said web app servers.

Usage
-----

``WORK_QUEUE_NAME=<your SQS name> S3_BUCKET_NAME=<the S3 bucket for image storage> python app.py``
