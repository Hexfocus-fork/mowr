import subprocess
from datetime import datetime
from hashlib import sha256, md5
import ssdeep
from bson.objectid import ObjectId, InvalidId
from flask import abort, current_app

class Analyser():
    def __init__(self, file=None, id=None):
        self.id = id
        self.file = file
        # Check if id is valid
        if id is not None:
            try:
                current_app.mongo.db.files.find_one_or_404({"_id": ObjectId(self.id)})
            except InvalidId:
                abort(404)

        # Get file path
        if self.file is None:
            sha256sum = current_app.mongo.db.files.find_one_or_404({"_id": ObjectId(self.id)})['sha256']
            self.file = self.getFilePath(sha256sum)

    @staticmethod
    def getFilePath(sha256sum):
        return '{0}/{1}'.format(current_app.config['UPLOAD_FOLDER'], sha256sum)

    def analyse(self):
        """ Returns the file _id """
        # Compute hashes
        with open(self.file, 'rb') as f:
            buf = f.read()
        sha256sum = sha256(buf).hexdigest()
        md5sum = md5(buf).hexdigest()
        ssdeephash = ssdeep.hash(buf)

        # Start the analysis
        # TODO yara bindings
        # TODO add tests
        analysis = subprocess.check_output(
                [current_app.config['PMF_BIN'], self.file]
                )
        # Format it (I could have called awk too)
        analysis = ' '.join([v for i, v in list(enumerate(analysis.split())) if i%2 == 0])

        # Store the result into the database
        if self.id is None:
            data = {"first_analysis": datetime.utcnow().ctime(),
                    "last_analysis": datetime.utcnow().ctime(),
                    "md5": md5sum,
                    "sha256": sha256sum,
                    "ssdeep": ssdeephash,
                    "pmf_analysis": analysis}
            id = current_app.mongo.db.files.insert_one(data).inserted_id
            self.id = id
        else:
            data = {"last_analysis": datetime.utcnow().ctime(),
                    "md5": md5sum,
                    "sha256": sha256sum,
                    "ssdeep": ssdeephash,
                    "pmf_analysis": analysis}
            current_app.mongo.db.files.update_one({"_id": ObjectId(self.id)}, {"$set": data})

        return self.id

    def getInfos(self):
        """ Get current analysis informations """
        return current_app.mongo.db.files.find_one_or_404({"_id": ObjectId(self.id)})
