from flask import Flask
from flask_restful import Resource, Api, reqparse
from ApplicationService import *
from google.cloud import storage

class Package(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument('id', required=True)
        args = parser.parse_args() # parse args into dictionary

        storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
        bucketName = os.getenv("BUCKET_NAME")
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(args['id'] + ".zip")
        if (fileToCheck.exists()):
            return {'metadata': {"Name": args["id"], "Version": "1.0.0", "ID": args["id"]}}, 200
        else:
            return {'metadata': "None"}, 400

    def put(self):
        



