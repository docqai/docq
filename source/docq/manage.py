

def upload(file, space):
    raise NotImplementedError


def download(file, space):
    raise NotImplementedError


def delete(files, space):
    raise NotImplementedError


def show(space):
    return list(map(lambda x: (x, f"This is document {str(x)}"), range(1, 5)))
