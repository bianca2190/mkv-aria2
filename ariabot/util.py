import os
from urllib.parse import urlparse

def hum_convert(value):
    units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s", "PB/s"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value /= size

def byte2Readable(size):
    """
    Fungsi ini mengonversi ukuran dalam byte menjadi format yang lebih mudah dibaca.
    """

    def strofsize(integer, remainder, level):
        if integer >= 1024:
            remainder = integer % 1024
            integer //= 1024
            level += 1
            return strofsize(integer, remainder, level)
        else:
            return integer, remainder, level

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    integer, remainder, level = strofsize(size, 0, 0)
    if level + 1 > len(units):
        level = -1
    return '{}.{:>03d}{}'.format(integer, remainder, units[level])

def progress(total_length, completed_length):
    if total_length != 0:
        return '{:.2f}%'.format(completed_length / total_length * 100)
    else:
        return "0%"

def getFileName(task):
    if task.__contains__('bittorrent'):
        if task['bittorrent'].__contains__('info'):
            # Untuk unduhan BT
            return task['bittorrent']['info']['name']
        # Untuk informasi dasar BT
        return task['files'][0]['path']
    filename = task['files'][0]['path'].split('/')[-1]
    if filename == '':
        pa = urlparse(task['files'][0]['uris'][0]['uri'])
        filename = os.path.basename(pa.path)
    return filename

def split_list(datas, n, row: bool = True):
    """
    Fungsi ini membagi daftar satu dimensi menjadi daftar dua dimensi,
    tergantung pada nilai N yang diberikan.
    """
    length = len(datas)
    size = length / n + 1 if length % n else length / n
    _datas = []
    if not row:
        size, n = n, size
    for i in range(int(size)):
        start = int(i * n)
        end = int((i + 1) * n)
        _datas.append(datas[start:end])
    return _datas

def format_name(string):
    """
    Fungsi ini memformat nama file untuk tampilan yang lebih baik.
    """
    head = end = ''
    middle = string
    if ':' in string:
        head, middle = string.split(':', 1)
    if '.' in middle:
        middle, end = middle.rsplit('.', 1)
    length = 15 - len(head + end) - 3
    middle = middle[:((length + 1) // 2)] + '~' + middle[-(length - (length + 1) // 2):]
    info = f"{head}:" if head else ""
    info += middle
    info += f".{end}" if end else ""
    return info

def format_lists(lst):
    """
    Fungsi ini mengubah daftar angka yang berurutan menjadi rentang angka yang diformat.
    """
    result = []
    start = None
    for i, num in enumerate(lst):
        num = int(num)
        if start is None:
            start = num
        if i + 1 == len(lst) or int(lst[i + 1]) != num + 1:
            if start == num:
                result.append(str(start))
            else:
                result.append(f"{start}~{num}")
            start = None
    return ", ".join(result)

def flatten_list(nested_list):
    """
    Fungsi ini melakukan flatten (penggabungan) dari daftar bersarang menjadi daftar satu dimensi.
    """
    flattened_list = []
    stack = [nested_list]

    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(current[::-1])
        else:
            flattened_list.append(current)

    return flattened_list
