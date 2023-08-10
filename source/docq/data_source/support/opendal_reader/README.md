# OpenDAL Loader

This loader parses any file via [OpenDAL](https://github.com/apache/incubator-opendal).

All files are temporarily downloaded locally and subsequently parsed. Hence, you may also specify a custom `file_extractor`, relying on any of the loaders in this library (or your own)!

## Usage

`OpendalReader` can read data from any supported storage services including `s3`, `azblob`, `gcs` and so on.

```python
loader = OpendalReader(
    scheme="s3",
    bucket='bucket',
    path='path/to/data/',
)
documents = loader.load_data()
```

We also provide `Opendal[S3|Gcs|Azblob]Reader` for convenience.

## License

Some files in this folder have a different license and copyright indicated at the top.
