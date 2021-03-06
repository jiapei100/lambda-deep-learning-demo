import os
import sys
from six.moves import urllib
import tarfile

def download_and_extract(data_file, data_url, create_parent_folder=True):
  data_dirname = os.path.dirname(data_file)
  print("Can not find " + data_file +
        ", download it now.")
  if not os.path.isdir(data_dirname):
    os.makedirs(data_dirname)

  if create_parent_folder:
    untar_dirname = data_dirname
  else:
    untar_dirname = os.path.abspath(os.path.join(data_dirname, os.pardir))

  download_tar_name = os.path.join("/tmp", os.path.basename(data_url))

  def _progress(count, block_size, total_size):
    sys.stdout.write('\r>> Downloading to %s %.1f%%' % (
        download_tar_name, 100.0 * count * block_size / total_size))
    sys.stdout.flush()

  local_tar_name, _ = urllib.request.urlretrieve(data_url,
                                                 download_tar_name,
                                                 _progress)

  print("\nExtracting dataset to " + data_dirname)
  tarfile.open(local_tar_name, 'r:gz').extractall(untar_dirname)