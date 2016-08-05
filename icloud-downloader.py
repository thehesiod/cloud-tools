#!/usr/bin/env python3
from pyicloud import PyiCloudService
import os.path
import multiprocessing.pool
import traceback
import argparse


def download_photo(photo, photo_path):
    try:
        print('Downloading', photo_path)
        download = photo.download()

        data = download.raw.read()
        assert len(data) == photo.size

        with open(photo_path, 'wb') as opened_file:
            opened_file.write(data)
        print('Downloaded', photo_path)
    except:
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)

        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='Download All Photos from iCloud')
    parser.add_argument('-apple_id', required=True, help="Your AppleID (password must be in KeyChain")
    parser.add_argument('-password', required=True)  # TODO switch to using keyring
    parser.add_argument('-folder', required=True, help='Path to Download Photos To')
    app_args = parser.parse_args()

    app_args.folder = os.path.expanduser(app_args.folder)

    with multiprocessing.pool.ThreadPool(10) as pool:
        api = PyiCloudService(app_args.apple_id, app_args.password)
        photos = list(api.photos.all)

        file_dups = dict()
        for photo in photos:
            if photo.filename not in file_dups:
                file_dups[photo.filename] = 1
            else:
                file_dups[photo.filename] += 1

        file_dups = {fname: count for fname, count in file_dups.items() if count > 1}

        for photo in photos:
            fname = photo.filename

            if fname in file_dups:
                assert file_dups[fname] > 0
                file_dups[fname] -= 1

                if file_dups[fname] > 0:
                    name, ext = fname.rsplit('.', 1)
                    fname = '{}-{}.{}'.format(name, file_dups[fname], ext)

            photo_path = os.path.join(app_args.folder, fname)
            if os.path.exists(photo_path) and os.path.getsize(photo_path) == photo.size:
                continue

            r = pool.apply_async(download_photo, [photo, photo_path])

        pool.close()
        pool.join()

if __name__ == '__main__':
    main()