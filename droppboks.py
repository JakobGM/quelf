import dropbox

from config import Config

conf = Config()

dbx = dropbox.Dropbox(conf['dropbox']['access_token'])


class File:
    def __init__(self, file_path: str) -> None:
        self.path = 'data/' + file_path

        dbx.files_download_to_file(
            download_path=self.path,
            path='/' + file_path,
        )

    def read(self):
        with open(self.path) as file:
            return file.read()

