# The MIT License

# Copyright (c) Jerry Liu

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Opendal file and directory reader.

A loader that fetches a file or iterates through a directory on AWS S3 or other compatible service.

"""
import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from llama_index import download_loader
from llama_index.readers.base import BaseReader
from llama_index.readers.schema.base import Document


class OpendalReader(BaseReader):
    """General reader for any opendal operator."""

    def __init__(
        self,
        scheme: str,
        path: str = "/",
        file_extractor: Optional[Dict[str, Union[str, BaseReader]]] = None,
        **kwargs: Optional[dict[str, any]],
    ) -> None:
        """Initialize opendal operator, along with credentials if needed.

        Args:
            scheme (str): the scheme of the service
            path (str): the path of the data. If none is provided,
                this loader will iterate through the entire bucket. If path is endswith `/`, this loader will iterate through the entire dir. Otherwise, this loader will load the file.
            file_extractor (Optional[Dict[str, BaseReader]]): A mapping of file
                extension to a BaseReader class that specifies how to convert that file
                to text. See `SimpleDirectoryReader` for more details.
            **kwargs (Optional dict[str, any]): Additional arguments to pass to the `opendal.AsyncOperator` constructor. These are the scheme (object store) specific options.
        """
        import opendal

        super().__init__()

        self.path = path
        self.file_extractor = file_extractor

        self.op = opendal.AsyncOperator(scheme, **kwargs)

    def load_data(self) -> List[Document]:
        """Load file(s) from OpenDAL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            if not self.path.endswith("/"):
                asyncio.run(download_file_from_opendal(self.op, temp_dir, self.path))
            else:
                asyncio.run(download_dir_from_opendal(self.op, temp_dir, self.path))

            try:
                from llama_hub.utils import import_loader

                SimpleDirectoryReader = import_loader("SimpleDirectoryReader")
            except ImportError:
                SimpleDirectoryReader = download_loader("SimpleDirectoryReader")
            loader = SimpleDirectoryReader(temp_dir, file_extractor=self.file_extractor)

            return loader.load_data()


async def download_file_from_opendal(op: Any, temp_dir: str, path: str) -> str:
    """Download file from OpenDAL."""
    import opendal

    op = cast(opendal.AsyncOperator, op)

    suffix = Path(path).suffix
    filepath = f"{temp_dir}/{next(tempfile._get_candidate_names())}{suffix}"

    async with op.open_reader(path) as r:
        with open(filepath, "wb") as w:
            w.write(await r.read())

    return filepath


async def download_dir_from_opendal(op: Any, temp_dir: str, dir_: str) -> str:
    """Download directory from opendal."""
    import opendal

    op = cast(opendal.AsyncOperator, op)
    async for obj in await op.scan(dir_):
        await download_file_from_opendal(op, temp_dir, obj.path)
