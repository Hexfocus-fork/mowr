import hashlib

import magic
import zipfile
from flask import flash

from mowr.models.sample import Sample
from mowr.analyzers.analyser import Analyser

MAX_SIZE = 1024*1024*15


class Legit(object):
    def __init__(self, path, analyse_type):
        self.path = path
        self.analyse_type = analyse_type or 'PHP'

    def analyse(self):
        mimetype = magic.from_file(self.path, mime=True)
        if mimetype != b'application/zip' or not zipfile.is_zipfile(self.path):
            flash('The file you sent is not a valid zip file.', 'warning')
            return False

        myfile = zipfile.ZipFile(self.path)
        size = 0
        file_list = []
        for compressed_file in myfile.infolist():
            size += compressed_file.file_size
            if self.analyse_type.lower() in compressed_file.filename.lower():
                file_list.append(compressed_file)

        if size > MAX_SIZE:
            flash('The size of the archive content is too big !', 'warning')
            return False

        for compressed_file in file_list:
            buf = myfile.read(compressed_file.filename)
            sha256 = hashlib.sha256(buf).hexdigest()
            filename = list(reversed(compressed_file.filename.split('/')))[0]
            with open(Sample.get_file_path(sha256), 'wb') as f:
                f.write(buf)
            analyser = Analyser(sha256=sha256, name=filename, type=self.analyse_type)
            analyser.analyse()

        return True