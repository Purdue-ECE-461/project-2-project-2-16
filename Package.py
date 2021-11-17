from flask import Flask
from flask_restful import Resource, Api, reqparse
from ApplicationService import *
from flask_marshmallow import Marshmallow
from google.cloud import storage
#from your_orm import Model, Column, Integer, String, DateTime
import sys

app = Flask(__name__)
ma = Marshmallow(app)


@app.route("/package/<id>")
def getPackage(id):
        storageClient = storage.Client.from_service_account_json("./google-cloud-creds.json")
        bucketName = os.getenv("BUCKET_NAME")
        bucket = storageClient.bucket(bucketName)
        fileToCheck = bucket.blob(id + ".zip")
        
        if (fileToCheck.exists()):
            return {'metadata': {"Name": id + ".zip", "Version": "1.0.0", "ID": id}}, 200
        else:
            return {'metadata': "None"}, 400


#api.add_resource(Package, '/package/<id>')

if __name__ == '__main__':
    app.run(debug=True)


